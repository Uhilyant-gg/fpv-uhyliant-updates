"""E8 controller onboarding: detect -> restore saved profile -> or guided calibration.

Composes local discovery, the durable non-secret profile store, calibration and
identity-bound restore. Every decision uses a fresh local observation; a saved
profile alone never makes the controller ready. Output uses the unified health
vocabulary with at most the normal-workflow safe actions the NBA engine accepts.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Mapping, Sequence

from controller_discovery import DEFAULT_MAX_AGE_SECONDS, discover_controllers, is_fresh, select_controller
from controller_profile import calibrate_controller
from controller_profile_store import ControllerProfileStoreInvalid
from controller_restore import controller_restore

MAX_CALIBRATION_SAMPLES = 4096


def _actions_for(health: str, reason: str) -> list[str]:
    if health == "ready":
        return []
    if reason in {"controller-not-observed", "controller-input-unavailable"}:
        return ["connect-controller"]
    if reason in {
        "controller-profile-unavailable",
        "controller-input-outside-calibration",
        "controller-profile-invalid",
    }:
        return ["calibrate-controller"]
    return ["diagnose"]


def _public(controller: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(controller, Mapping):
        return None
    return {"id": controller.get("id"), "name": controller.get("name"), "transport": controller.get("transport")}


class ControllerOnboarding:
    def __init__(
        self,
        source: Any,
        store: Any,
        clock: Callable[[], float] | None = None,
        max_age: float = DEFAULT_MAX_AGE_SECONDS,
    ):
        self.source = source
        self.store = store
        self.clock = clock or time.monotonic
        self.max_age = max_age
        self._calibration: dict[str, Any] | None = None

    # -- evidence -----------------------------------------------------------------
    def _saved(self) -> tuple[dict[str, dict[str, Any]], str | None]:
        if self.store is None:
            return {}, "controller-profile-store-unavailable"
        try:
            return self.store.load(), None
        except ControllerProfileStoreInvalid as exc:
            return {}, str(exc)

    def _observe(self, saved_ids: Sequence[str]) -> dict[str, Any]:
        return select_controller(discover_controllers(self.source, self.clock), saved_ids)

    def _result(self, health: str, reason: str, controller=None, **extra) -> dict[str, Any]:
        result = {
            "health": health,
            "reasonCode": reason,
            "controller": _public(controller),
            "restored": False,
            "safeActions": _actions_for(health, reason),
            "calibration": self.calibration_status(),
        }
        result.update(extra)
        return result

    def refresh(self) -> dict[str, Any]:
        """Observe now and report whether the controller is usable with a restored profile."""
        saved, store_error = self._saved()
        selection = self._observe(list(saved))
        controller = selection.get("controller")
        if controller is None:
            extra = {"candidates": selection["candidates"]} if "candidates" in selection else {}
            return self._result(selection["health"], selection["reasonCode"], **extra)
        if not is_fresh(controller, self.clock(), self.max_age):
            return self._result("unknown", "controller-observation-stale", controller)
        if store_error is not None:
            return self._result("problem", store_error, controller)
        restore = controller_restore(saved.get(controller["id"]), controller)
        result = self._result(restore["health"], restore["reasonCode"], controller)
        result["restored"] = restore["restored"]
        if restore["restored"]:
            result["controls"] = restore["controls"]
        return result

    # -- guided calibration -----------------------------------------------------
    def calibration_status(self) -> dict[str, Any]:
        if self._calibration is None:
            return {"active": False, "samples": 0, "controllerId": None}
        return {
            "active": True,
            "samples": len(self._calibration["samples"]),
            "controllerId": self._calibration["controllerId"],
        }

    def begin_calibration(self) -> dict[str, Any]:
        saved, _ = self._saved()
        selection = self._observe(list(saved))
        controller = selection.get("controller")
        if controller is None:
            self._calibration = None
            return self._result(selection["health"], selection["reasonCode"])
        if not controller.get("connected") or not is_fresh(controller, self.clock(), self.max_age):
            self._calibration = None
            return self._result("unknown", "controller-input-unavailable", controller)
        self._calibration = {
            "controllerId": controller["id"],
            "name": controller.get("name"),
            "channelCount": len(controller["channels"]),
            "samples": [list(controller["channels"])],
        }
        return self._result("attention", "controller-calibration-in-progress", controller)

    def sample(self) -> dict[str, Any]:
        """Capture one fresh frame from the controller being calibrated."""
        if self._calibration is None:
            return self._result("attention", "controller-calibration-not-started")
        selection = self._observe([self._calibration["controllerId"]])
        controller = selection.get("controller")
        if controller is None or controller.get("id") != self._calibration["controllerId"]:
            self._calibration = None
            return self._result("unknown", "controller-calibration-interrupted")
        channels = controller.get("channels")
        if (
            not controller.get("connected")
            or not is_fresh(controller, self.clock(), self.max_age)
            or len(channels) != self._calibration["channelCount"]
        ):
            self._calibration = None
            return self._result("unknown", "controller-calibration-interrupted", controller)
        if len(self._calibration["samples"]) < MAX_CALIBRATION_SAMPLES:
            self._calibration["samples"].append(list(channels))
        return self._result("attention", "controller-calibration-in-progress", controller, channels=list(channels))

    def cancel_calibration(self) -> dict[str, Any]:
        self._calibration = None
        return self.refresh()

    def finish_calibration(self, mapping: Mapping[str, Any]) -> dict[str, Any]:
        """Build, persist and immediately re-verify the profile against a fresh frame."""
        session = self._calibration
        if session is None:
            return self._result("attention", "controller-calibration-not-started")
        try:
            profile = calibrate_controller(session["controllerId"], session["samples"], mapping)
        except ValueError as exc:
            return self._result(
                "attention", str(exc), {"id": session["controllerId"], "name": session["name"], "transport": "usb-hid"}
            )
        if self.store is None:
            return self._result("problem", "controller-profile-store-unavailable")
        try:
            self.store.save_profile(session["controllerId"], session["name"], profile)
        except (ControllerProfileStoreInvalid, OSError) as exc:
            reason = (
                str(exc) if isinstance(exc, ControllerProfileStoreInvalid) else "controller-profile-store-write-failed"
            )
            return self._result("problem", reason)
        self._calibration = None
        return self.refresh()

    def forget_profile(self, controller_id: str) -> dict[str, Any]:
        if self.store is not None:
            try:
                self.store.forget(controller_id)
            except (ControllerProfileStoreInvalid, OSError):
                return self._result("problem", "controller-profile-store-invalid")
        return self.refresh()
