import json, math, os
from pathlib import Path
from PySide6.QtCore import QObject, Property, QSettings, Signal, Slot
from flight_alerts import DEFAULT_THRESHOLDS, validate_threshold, validate_thresholds
from home_dashboard import home_dashboard
import station_settings
from station_settings import validate_station_settings

DATA = Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'FPV-Uhyliant'
DATA.mkdir(parents=True, exist_ok=True)


class HomeDashboard(QObject):
    changed = Signal()

    def __init__(self, devices):
        super().__init__()
        self._devices = devices
        self._controller = None
        self._model = home_dashboard(devices.items, devices.streams)
        devices.changed.connect(self.refresh)
        devices.streamsChanged.connect(self.refresh)
        devices.discoveryChanged.connect(self.refresh)

    def setController(self, controller):
        """Include an observed RC controller in the Home next action."""
        self._controller = controller
        controller.changed.connect(self.refresh)
        self.refresh()

    def refresh(self):
        controller = self._controller.evidence() if self._controller is not None else None
        self._model = home_dashboard(self._devices.items, self._devices.streams, controller)
        self.changed.emit()

    @Property(str, notify=changed)
    def health(self):
        return self._model["health"]

    @Property(str, notify=changed)
    def title(self):
        return self._model["title"]

    @Property(str, notify=changed)
    def summary(self):
        return self._model["summary"]

    @Property(int, notify=changed)
    def deviceCount(self):
        return self._model["deviceCount"]

    @Property(int, notify=changed)
    def verifiedCount(self):
        return self._model["verifiedCount"]

    @Property(int, notify=changed)
    def pendingCount(self):
        return self._model["pendingCount"]

    @Property(int, notify=changed)
    def warningCount(self):
        return self._model["warningCount"]

    @Property('QVariantMap', notify=changed)
    def nextAction(self):
        return dict(self._model["nextAction"])


class Station(QObject):
    changed = Signal()
    notice = Signal(str)
    osdSettingsSaved = Signal()
    OSD_ENABLED_KEY = "osd/station-enabled"
    OSD_OPACITY_KEY = "osd/station-opacity"
    OSD_SCALE_KEY = "osd/station-scale"
    OSD_POSITION_KEY = "osd/station-position"
    OSD_ELEMENTS_KEY = "osd/station-elements"
    OSD_ELEMENT_VISIBILITY_KEY = "osd/station-element-visibility"
    OSD_ELEMENT_NAMES = station_settings.ELEMENT_NAMES
    OSD_POSITIONS = station_settings.POSITIONS
    OSD_DEFAULT_ELEMENT_VISIBILITY = station_settings.DEFAULT_ELEMENT_VISIBILITY
    OSD_DEFAULT_OPACITY = station_settings.DEFAULT_OPACITY
    OSD_DEFAULT_SCALE = station_settings.DEFAULT_SCALE
    OSD_DEFAULT_POSITION = station_settings.DEFAULT_POSITION
    ALERT_THRESHOLDS_KEY = "alerts/thresholds"

    def __init__(self, settings=None):
        super().__init__()
        self._settings = settings or QSettings("FPV-Uhyliant", "FPV-Uhyliant")
        self._menu = False
        self._video = False
        self._osd = 'station'
        self._osd_enabled = self._read_osd_enabled()
        self._edit = False
        self._opacity = self._read_osd_number(self.OSD_OPACITY_KEY, self.OSD_DEFAULT_OPACITY, 0, 1)
        self._scale = self._read_osd_number(self.OSD_SCALE_KEY, self.OSD_DEFAULT_SCALE, 0.85, 1.3)
        self._position = self._read_osd_position()
        self._elements = self._read_osd_elements()
        self._element_visibility = self._read_osd_element_visibility()
        self._osd_settings_error = ""
        self._alert_thresholds = self._read_alert_thresholds()
        self._armed = False
        self._recording = False
        self._streaming = False

    def _read_alert_thresholds(self):
        try:
            stored = json.loads(str(self._settings.value(self.ALERT_THRESHOLDS_KEY, "{}")))
        except (TypeError, ValueError):
            stored = {}
        return validate_thresholds(stored)

    def exportSettings(self):
        """All station settings that belong in a vehicle preset."""
        return {
            "osd": {
                "enabled": self._osd_enabled,
                "opacity": self._opacity,
                "scale": self._scale,
                "position": self._position,
                "elements": {name: list(value) for name, value in self._elements.items()},
                "elementVisibility": dict(self._element_visibility),
            },
            "alerts": dict(self._alert_thresholds),
        }

    def applySettings(self, settings):
        """Validate and apply a complete settings set (all or nothing), then persist it."""
        try:
            value = validate_station_settings(settings)
        except ValueError:
            return False
        osd = value["osd"]
        self._osd_enabled = osd["enabled"]
        self._opacity = osd["opacity"]
        self._scale = osd["scale"]
        self._position = osd["position"]
        self._elements = {name: list(pos) for name, pos in osd["elements"].items()}
        self._element_visibility = dict(osd["elementVisibility"])
        self._alert_thresholds = dict(value["alerts"])
        self._settings.setValue(self.OSD_ENABLED_KEY, self._osd_enabled)
        self._settings.setValue(self.OSD_OPACITY_KEY, self._opacity)
        self._settings.setValue(self.OSD_SCALE_KEY, self._scale)
        self._settings.setValue(self.OSD_POSITION_KEY, self._position)
        self._settings.setValue(self.OSD_ELEMENTS_KEY, json.dumps(self._elements))
        self._settings.setValue(self.OSD_ELEMENT_VISIBILITY_KEY, json.dumps(self._element_visibility))
        self._settings.setValue(self.ALERT_THRESHOLDS_KEY, json.dumps(self._alert_thresholds, sort_keys=True))
        saved = self._save_osd_settings()
        if saved:
            self.osdSettingsSaved.emit()
        self.changed.emit()
        return saved

    @Property("QVariantMap", notify=changed)
    def alertThresholds(self):
        return dict(self._alert_thresholds)

    @Slot(str, float, result=bool)
    def setAlertThreshold(self, name, value):
        """Validate, apply and persist one alert threshold with the other station settings."""
        try:
            normalized = validate_threshold(name, value)
        except ValueError:
            return False
        self._alert_thresholds[name] = normalized
        self._settings.setValue(self.ALERT_THRESHOLDS_KEY, json.dumps(self._alert_thresholds, sort_keys=True))
        saved = self._save_osd_settings()
        self.changed.emit()
        return saved

    @Slot(result=bool)
    def resetAlertThresholds(self):
        self._alert_thresholds = dict(DEFAULT_THRESHOLDS)
        self._settings.setValue(self.ALERT_THRESHOLDS_KEY, "{}")
        saved = self._save_osd_settings()
        self.changed.emit()
        return saved

    def _read_osd_enabled(self):
        value = self._settings.value(self.OSD_ENABLED_KEY, True)
        return str(value).strip().lower() not in ("0", "false", "no", "off")

    def _read_osd_number(self, key, default, minimum, maximum):
        try:
            value = float(self._settings.value(key, default))
        except (TypeError, ValueError):
            return default
        if not math.isfinite(value):
            return default
        return max(minimum, min(maximum, value))

    def _read_osd_position(self):
        value = str(self._settings.value(self.OSD_POSITION_KEY, self.OSD_DEFAULT_POSITION))
        return value if value in self.OSD_POSITIONS else self.OSD_DEFAULT_POSITION

    def _read_osd_elements(self):
        try:
            values = json.loads(str(self._settings.value(self.OSD_ELEMENTS_KEY, "{}")))
        except (ValueError, TypeError):
            return {}
        if not isinstance(values, dict):
            return {}
        return {
            key: value
            for key, value in values.items()
            if key in self.OSD_ELEMENT_NAMES
            and isinstance(value, list)
            and len(value) == 2
            and all(type(n) is int and 0 <= n <= 100 for n in value)
        }

    def _read_osd_element_visibility(self):
        values = dict(self.OSD_DEFAULT_ELEMENT_VISIBILITY)
        try:
            saved = json.loads(str(self._settings.value(self.OSD_ELEMENT_VISIBILITY_KEY, "{}")))
        except (ValueError, TypeError):
            return values
        if isinstance(saved, dict):
            values.update(
                {key: value for key, value in saved.items() if key in self.OSD_ELEMENT_NAMES and type(value) is bool}
            )
        return values

    @Property(bool, notify=changed)
    def menuOpen(self):
        return self._menu

    @Property(bool, notify=changed)
    def videoRunning(self):
        return self._video

    @Property(str, notify=changed)
    def osdSource(self):
        return self._osd

    @Property(bool, notify=changed)
    def osdEnabled(self):
        return self._osd_enabled

    @Property(bool, notify=changed)
    def osdEdit(self):
        return self._edit

    @Property(float, notify=changed)
    def osdOpacity(self):
        return self._opacity

    @Property(float, notify=changed)
    def osdScale(self):
        return self._scale

    @Property(str, notify=changed)
    def osdPosition(self):
        return self._position

    @Property('QVariantMap', notify=changed)
    def osdElements(self):
        return dict(self._elements)

    @Property('QVariantMap', notify=changed)
    def osdEnabledElements(self):
        return dict(self._element_visibility)

    @Property(str, notify=changed)
    def osdSettingsError(self):
        return self._osd_settings_error

    def exportOsdSnapshot(self):
        return {
            'enabled': self._osd_enabled,
            'opacity': self._opacity,
            'scale': self._scale,
            'position': self._position,
        }

    @Slot()
    def toggleMenu(self):
        self._menu = not self._menu
        self.changed.emit()

    @Slot()
    def toggleVideo(self):
        self._video = not self._video
        self.changed.emit()

    @Slot(str)
    def setOSDSource(self, v):
        self._osd = v
        self.changed.emit()

    @Slot(bool)
    def setOSDEnabled(self, value):
        enabled = bool(value)
        if enabled == self._osd_enabled:
            return
        self._osd_enabled = enabled
        self._settings.setValue(self.OSD_ENABLED_KEY, enabled)
        if self._save_osd_settings():
            self.osdSettingsSaved.emit()
        self.changed.emit()

    @Slot(bool)
    def setOSDEdit(self, v):
        self._edit = v
        self.changed.emit()

    @Slot(float, float, result=bool)
    def setOSDStyle(self, o, s):
        if not math.isfinite(o) or not math.isfinite(s) or not 0 <= o <= 1 or not 0.85 <= s <= 1.3:
            return False
        self._opacity = o
        self._scale = s
        self._settings.setValue(self.OSD_OPACITY_KEY, o)
        self._settings.setValue(self.OSD_SCALE_KEY, s)
        saved = self._save_osd_settings()
        if saved:
            self.osdSettingsSaved.emit()
        self.changed.emit()
        return saved

    @Slot(str, result=bool)
    def setOSDPosition(self, value):
        if value not in self.OSD_POSITIONS:
            return False
        self._position = value
        self._settings.setValue(self.OSD_POSITION_KEY, value)
        saved = self._save_osd_settings()
        if saved:
            self.osdSettingsSaved.emit()
        self.changed.emit()
        return saved

    @Slot(str, int, int, result=bool)
    def setOSDElementPosition(self, name, x, y):
        if name not in self.OSD_ELEMENT_NAMES or not 0 <= x <= 100 or not 0 <= y <= 100:
            return False
        self._elements[name] = [x, y]
        self._settings.setValue(self.OSD_ELEMENTS_KEY, json.dumps(self._elements))
        saved = self._save_osd_settings()
        if saved:
            self.osdSettingsSaved.emit()
        self.changed.emit()
        return saved

    @Slot(str, bool, result=bool)
    def setOSDElementEnabled(self, name, enabled):
        if name not in self.OSD_ELEMENT_NAMES:
            return False
        value = bool(enabled)
        if self._element_visibility.get(name) == value:
            return True
        self._element_visibility[name] = value
        self._settings.setValue(self.OSD_ELEMENT_VISIBILITY_KEY, json.dumps(self._element_visibility))
        saved = self._save_osd_settings()
        if saved:
            self.osdSettingsSaved.emit()
        self.changed.emit()
        return saved

    @Slot()
    def resetOSDStyle(self):
        self._opacity = self.OSD_DEFAULT_OPACITY
        self._scale = self.OSD_DEFAULT_SCALE
        self._position = self.OSD_DEFAULT_POSITION
        self._elements = {}
        self._element_visibility = dict(self.OSD_DEFAULT_ELEMENT_VISIBILITY)
        self._settings.setValue(self.OSD_OPACITY_KEY, self._opacity)
        self._settings.setValue(self.OSD_SCALE_KEY, self._scale)
        self._settings.setValue(self.OSD_POSITION_KEY, self._position)
        self._settings.setValue(self.OSD_ELEMENTS_KEY, "{}")
        self._settings.setValue(self.OSD_ELEMENT_VISIBILITY_KEY, json.dumps(self._element_visibility))
        if self._save_osd_settings():
            self.osdSettingsSaved.emit()
        self.changed.emit()

    def _save_osd_settings(self):
        self._settings.sync()
        self._osd_settings_error = (
            "Не вдалося зберегти налаштування OSD. Перевірте доступ до папки даних."
            if self._settings.status() != QSettings.NoError
            else ""
        )
        return self._osd_settings_error == ""

    def setRecordingActive(self, active):
        self._recording = bool(active)

    @Slot(str)
    def action(self, v):
        self.notice.emit(v)

    def canInstallUpdate(self):
        r = []
        if self._armed:
            r.append('автопілот озброєний')
        if self._recording:
            r.append('активний запис')
        if self._streaming:
            r.append('активна трансляція')
        return (not r, 'Неможливо оновити: ' + ', '.join(r) if r else '')
