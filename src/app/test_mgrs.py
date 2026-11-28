import pytest

import mgrs
from map_marks import MapMarksRuntime


@pytest.mark.parametrize(
    "lat,lon,expected",
    [
        (50.4501, 30.5234, "36U UA 24182 91607"),
        (38.8977, -77.0365, "18S UJ 23394 07395"),
        (-33.86, 151.21, "56H LH 34416 51925"),
        (60.0, 5.0, "32V KM 76979 58157"),
    ],
)
def test_to_mgrs_and_back_within_a_metre(lat, lon, expected):
    assert mgrs.to_mgrs(lat, lon) == expected
    back = mgrs.from_mgrs(expected)
    assert abs(back[0] - lat) < 2e-5 and abs(back[1] - lon) < 2e-5


def test_written_in_any_spacing_and_precision():
    a = mgrs.from_mgrs("36uua2418291607")
    b = mgrs.from_mgrs("36U UA 241 916")
    assert abs(a[0] - b[0]) < 0.01 and abs(a[1] - b[1]) < 0.01
    for bad in ("", "hello", "36U UA 123", "61U UA 1 1", "36U IA 1 1"):
        with pytest.raises(ValueError):
            mgrs.from_mgrs(bad)


def test_marks_are_added_named_kept_and_removed(tmp_path):
    rt = MapMarksRuntime(tmp_path / "marks.json")
    assert rt.addMgrs("36U UA 24182 91607", "")
    assert rt.addAt(50.46, 30.53)
    assert not rt.addMgrs("ерунда", "")
    assert "Не схоже на координати MGRS" in rt.message
    assert [m["name"] for m in rt.marks] == ["1", "2"]
    assert rt.marks[1]["mgrs"] == mgrs.to_mgrs(50.46, 30.53)
    again = MapMarksRuntime(tmp_path / "marks.json")
    assert [m["name"] for m in again.marks] == ["1", "2"]
    again.remove(0)
    assert again.addAt(50.0, 30.0) and [m["name"] for m in again.marks] == ["2", "1"]
    assert again.mgrsOf(50.4501, 30.5234) == "36U UA 24182 91607"
