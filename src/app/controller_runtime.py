"""Qt bridge for RC controller onboarding: status, live inputs and the setup wizard.

Polling only runs while the controller panel is open, so an idle station does
not touch the joystick API. All state shown to the operator comes from a fresh
observation; a saved profile never makes the controller "ready" on its own.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Property, QObject, QTimer, Signal, Slot

from controller_mapping import MappingWizard
from controller_onboarding import ControllerOnboarding

POLL_INTERVAL_MS = 50

_SUMMARIES = {
    "controller-observed-inputs-and-restored": "Пульт підключено, налаштування відновлено.",
    "controller-profile-unavailable": "Пульт підключено. Налаштуйте його один раз — далі він відновлюватиметься сам.",
    "controller-not-observed": "Пульт не знайдено. Підключіть його через USB у режимі джойстика.",
    "controller-input-unavailable": "Пульт видно, але він не передає сигнали стіків. Увімкніть режим джойстика на пульті.",
    "controller-source-unavailable": "Пульти недоступні на цьому комп'ютері.",
    "controller-source-failed": "Не вдалося прочитати пульт. Перепідключіть його.",
    "controller-identity-ambiguous": "Підключено два однакові пульти. Залиште один, щоб уникнути плутанини.",
    "controller-identity-unavailable": "Не вдалося визначити пульт. Перепідключіть його.",
    "controller-selection-required": "Підключено кілька пультів. Залиште один для налаштування.",
    "controller-input-outside-calibration": "Стіки виходять за межі налаштування. Налаштуйте пульт повторно.",
    "controller-input-invalid": "Пульт передає некоректні значення. Перепідключіть його.",
    "controller-profile-store-invalid": "Збережені налаштування пульта пошкоджено. Налаштуйте пульт повторно.",
    "controller-profile-store-write-failed": "Не вдалося зберегти налаштування пульта. Перевірте доступ до диска.",
    "controller-observation-stale": "Дані пульта застаріли. Перепідключіть його.",
    "controller-calibration-in-progress": "Налаштування пульта триває.",
}

_STEP_ERRORS = {
    "controller-mapping-no-movement": "Рух не помічено. Відхиліть стік до упору й утримуйте.",
    "controller-mapping-ambiguous-movement": "Рухається кілька каналів одночасно. Рухайте лише один стік.",
    "controller-mapping-channel-reused": "Цей канал уже призначено іншій осі. Рухайте інший стік.",
    "controller-calibration-samples-insufficient": "Покрутіть стіки ще трохи, потім натисніть «Готово».",
    "controller-calibration-range-invalid": "Діапазон стіка замалий. Покрутіть стіки до упору.",
    "controller-calibration-center-invalid": "Центр стіка поза діапазоном. Почніть налаштування заново.",
    "controller-calibration-interrupted": "Пульт від'єднано під час налаштування. Почніть заново.",
    "controller-input-invalid": "Пульт передає некоректні значення.",
}


def human_summary(reason_code: str) -> str:
    return _SUMMARIES.get(reason_code, "Стан пульта невідомий.")


def human_step_error(reason_code: str) -> str:
    return _STEP_ERRORS.get(reason_code, "Крок не вдався. Спробуйте ще раз.")


class ControllerRuntime(QObject):
    changed = Signal()

    def __init__(self, onboarding: ControllerOnboarding, interval_ms: int = POLL_INTERVAL_MS):
        super().__init__()
        self.onboarding = onboarding
        self._state: dict[str, Any] = {"health": "unknown", "reasonCode": "controller-not-observed", "controller": None}
        self._channels: list[float] = []
        self._wizard: MappingWizard | None = None
        self._step_error = ""
        self._active = False
        self._timer = QTimer(self)
        self._timer.setInterval(interval_ms)
        self._timer.timeout.connect(self._tick)

    # -- polling --------------------------------------------------------------
    def _tick(self):
        if self._wizard is not None:
            result = self.onboarding.sample()
            if not result.get("calibration", {}).get("active"):
                self._abort_wizard(result.get("reasonCode", "controller-calibration-interrupted"), result)
                return
            self._channels = list(result.get("channels") or [])
            self._wizard.observe(self._channels)
            self.changed.emit()
            return
        self._apply(self.onboarding.refresh())

    def _apply(self, state: dict[str, Any]):
        self._state = state
        self.changed.emit()

    def _abort_wizard(self, reason: str, state: dict[str, Any] | None = None):
        self._wizard = None
        self._step_error = human_step_error(reason)
        if state is not None:
            self._state = state
        self.changed.emit()

    # -- QML API ----------------------------------------------------------------
    @Slot()
    def activate(self):
        self._active = True
        self._timer.start()
        self._tick()

    @Slot()
    def deactivate(self):
        self._active = False
        self._timer.stop()
        if self._wizard is not None:
            self.cancelWizard()

    @Slot()
    def startWizard(self):
        self._step_error = ""
        result = self.onboarding.begin_calibration()
        if not result.get("calibration", {}).get("active"):
            self._abort_wizard(result.get("reasonCode", "controller-not-observed"), result)
            return
        self._wizard = MappingWizard()
        if not self._timer.isActive():
            self._timer.start()
        self._tick()

    @Slot()
    def nextStep(self):
        if self._wizard is None:
            return
        try:
            self._wizard.advance(self._channels)
        except ValueError as exc:
            self._step_error = human_step_error(str(exc))
            self.changed.emit()
            return
        self._step_error = ""
        if self._wizard.done:
            mapping = dict(self._wizard.mapping)
            self._wizard = None
            result = self.onboarding.finish_calibration(mapping)
            if not result.get("restored"):
                self._step_error = human_step_error(result.get("reasonCode", ""))
            self._apply(result)
            return
        self.changed.emit()

    @Slot()
    def cancelWizard(self):
        self._wizard = None
        self._step_error = ""
        self._apply(self.onboarding.cancel_calibration())

    @Slot()
    def forgetProfile(self):
        controller = self._state.get("controller") or {}
        if controller.get("id"):
            self._apply(self.onboarding.forget_profile(controller["id"]))

    # -- properties -------------------------------------------------------------
    @Property(str, notify=changed)
    def health(self):
        return "attention" if self._wizard is not None else self._state.get("health", "unknown")

    @Property(str, notify=changed)
    def summary(self):
        if self._wizard is not None:
            return human_summary("controller-calibration-in-progress")
        return human_summary(self._state.get("reasonCode", ""))

    @Property(str, notify=changed)
    def controllerName(self):
        controller = self._state.get("controller") or {}
        return controller.get("name") or ""

    @Property(bool, notify=changed)
    def restored(self):
        return bool(self._state.get("restored"))

    @Property(bool, notify=changed)
    def canConfigure(self):
        return self._wizard is None and "calibrate-controller" in (self._state.get("safeActions") or [])

    @Property(bool, notify=changed)
    def canForget(self):
        return self._wizard is None and bool(self._state.get("restored"))

    @Property("QVariantMap", notify=changed)
    def controls(self):
        return dict(self._state.get("controls") or {}) if self._state.get("restored") else {}

    @Property("QVariantList", notify=changed)
    def channels(self):
        return list(self._channels)

    @Property(bool, notify=changed)
    def wizardActive(self):
        return self._wizard is not None

    @Property(str, notify=changed)
    def wizardStep(self):
        return self._wizard.step if self._wizard is not None else ""

    @Property(str, notify=changed)
    def wizardPrompt(self):
        return self._wizard.prompt if self._wizard is not None else ""

    @Property(str, notify=changed)
    def stepError(self):
        return self._step_error

    @Property(bool, notify=changed)
    def active(self):
        return self._active
