"""Archive: a camera leaves the home screen and use, then is restored or deleted."""

import gc

import pytest

import devices as devices_module
from devices_routeaware import Devices
from snapshot_validation import validate_snapshot


@pytest.fixture
def devices(tmp_path, monkeypatch):
    monkeypatch.setattr(devices_module, "DATA", tmp_path)
    monkeypatch.setattr(devices_module, "DB", tmp_path / "station.db")
    model = Devices()
    yield model
    del model
    gc.collect()


def add(model, name, host):
    return model.addDevice(name, "OpenIPC", host, 80, "Network", "")


def test_archive_hides_restore_returns(devices):
    first = add(devices, "Квадрик", "192.168.1.10")
    second = add(devices, "Крило", "192.168.1.11")
    devices.setActive(first)
    events = []
    devices.changed.connect(lambda: events.append("changed"))

    assert devices.archiveDevice(first)
    assert events
    assert [d["id"] for d in devices.homeItems] == [second]
    assert [d["id"] for d in devices.archivedItems] == [first]
    assert devices.archivedItems[0]["archivedAt"] > 0
    assert devices.activeName == "", "archiving the active camera releases it"
    devices.setActive(first)
    assert devices.activeName == "", "an archived camera cannot become active"
    assert not devices.archiveDevice(first), "already archived"

    assert devices.restoreDevice(first)
    assert {d["id"] for d in devices.homeItems} == {first, second}
    assert devices.archivedItems == []
    assert not devices.restoreDevice(first), "not archived any more"


def test_archive_survives_reload(devices, tmp_path):
    did = add(devices, "Квадрик", "192.168.1.10")
    devices.archiveDevice(did)
    reloaded = Devices()
    assert [d["id"] for d in reloaded.archivedItems] == [did]
    assert reloaded.homeItems == []


def test_archived_camera_can_be_deleted(devices):
    did = add(devices, "Квадрик", "192.168.1.10")
    devices.archiveDevice(did)
    devices.removeDevice(did)
    assert devices.items == []
    assert devices.archivedItems == []


def test_unknown_camera_is_rejected(devices):
    assert not devices.archiveDevice("nope")
    assert not devices.restoreDevice("nope")


def test_snapshot_keeps_archive_and_old_snapshots_still_restore(devices):
    first = add(devices, "Квадрик", "192.168.1.10")
    second = add(devices, "Крило", "192.168.1.11")
    devices.archiveDevice(first)
    snapshot = devices.exportSnapshot()
    assert snapshot["archivedDeviceIds"] == [first]
    assert devices.validateSnapshot(snapshot)
    assert validate_snapshot(snapshot)

    devices.restoreDevice(first)
    assert devices.restoreSnapshot(snapshot)
    assert [d["id"] for d in devices.archivedItems] == [first]
    assert [d["id"] for d in devices.homeItems] == [second]

    old = {k: v for k, v in snapshot.items() if k != "archivedDeviceIds"}
    assert devices.validateSnapshot(old) and validate_snapshot(old)
    assert devices.restoreSnapshot(old)
    assert devices.archivedItems == []


@pytest.mark.parametrize("bad", [["missing"], "c1", [1]])
def test_snapshot_rejects_bad_archive_lists(devices, bad):
    add(devices, "Квадрик", "192.168.1.10")
    snapshot = dict(devices.exportSnapshot(), archivedDeviceIds=bad)
    assert not devices.validateSnapshot(snapshot)
    assert not validate_snapshot(snapshot)


def test_active_camera_cannot_be_archived_in_a_snapshot(devices):
    did = add(devices, "Квадрик", "192.168.1.10")
    devices.setActive(did)
    snapshot = dict(devices.exportSnapshot(), archivedDeviceIds=[did])
    assert not validate_snapshot(snapshot)
