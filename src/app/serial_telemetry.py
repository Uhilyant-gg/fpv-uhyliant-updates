"""Serial transports for read-only MSP polling and passive CRSF telemetry."""

from PySide6.QtCore import QObject, Property, QSettings, QTimer, Signal, Slot
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo
from msp_runtime import READ_ONLY_COMMANDS, build_request


class SerialTelemetryTransport(QObject):
    changed = Signal()

    def __init__(self, runtime, settings_prefix, protocol, baud=115200, poll_commands=()):
        super().__init__()
        self.runtime = runtime
        self.protocol = protocol
        self.settings_prefix = settings_prefix
        settings = QSettings("FPV-Uhyliant", "FPV-Uhyliant")
        self._port_name = str(settings.value(f"{settings_prefix}/port", ""))
        self._baud = int(settings.value(f"{settings_prefix}/baud", baud))
        self._enabled = str(settings.value(f"{settings_prefix}/enabled", "false")).lower() not in ("0", "false")
        self._error = ""
        self._serial = QSerialPort(self)
        self._serial.readyRead.connect(self._read)
        self._serial.errorOccurred.connect(self._serial_error)
        self._poll_commands = tuple(poll_commands)
        self._poll_index = 0
        self._poll = QTimer(self)
        self._poll.setInterval(250)
        self._poll.timeout.connect(self._poll_once)
        if self._enabled and self._port_name:
            self.start()

    @Property(str, notify=changed)
    def portName(self):
        return self._port_name

    @Property(int, notify=changed)
    def baud(self):
        return self._baud

    @Property(bool, notify=changed)
    def enabled(self):
        return self._enabled

    @Property(bool, notify=changed)
    def running(self):
        return self._serial.isOpen()

    @Property(str, notify=changed)
    def error(self):
        return self._error

    @Property("QStringList", notify=changed)
    def ports(self):
        return [port.portName() for port in QSerialPortInfo.availablePorts()]

    @Slot()
    def refreshPorts(self):
        self.changed.emit()

    @Slot(str, int, bool)
    def configure(self, port_name, baud, enabled):
        self.stop()
        self._port_name = port_name.strip()
        self._baud = max(1200, min(int(baud), 4000000))
        self._enabled = bool(enabled)
        settings = QSettings("FPV-Uhyliant", "FPV-Uhyliant")
        settings.setValue(f"{self.settings_prefix}/port", self._port_name)
        settings.setValue(f"{self.settings_prefix}/baud", self._baud)
        settings.setValue(f"{self.settings_prefix}/enabled", self._enabled)
        self._error = ""
        if self._enabled and self._port_name:
            self.start()
        self.changed.emit()

    @Slot(result=bool)
    def start(self):
        if self._serial.isOpen():
            return True
        if not self._port_name:
            self._error = f"{self.protocol}: serial port не вибрано"
            self.changed.emit()
            return False
        self._serial.setPortName(self._port_name)
        self._serial.setBaudRate(self._baud)
        if not self._serial.open(QSerialPort.ReadWrite if self._poll_commands else QSerialPort.ReadOnly):
            self._error = f"{self.protocol}: {self._serial.errorString()}"
            self.changed.emit()
            return False
        self._error = ""
        if self._poll_commands:
            self._poll.start()
        self.changed.emit()
        return True

    @Slot()
    def stop(self):
        self._poll.stop()
        if self._serial.isOpen():
            self._serial.close()
        self.changed.emit()

    def _read(self):
        data = bytes(self._serial.readAll())
        if data:
            self.runtime.feed(data)

    def _serial_error(self, error):
        if error != QSerialPort.NoError and self._serial.isOpen():
            self._error = f"{self.protocol}: {self._serial.errorString()}"
            self.changed.emit()

    def _poll_once(self):
        if not self._serial.isOpen() or not self._poll_commands:
            return
        command = self._poll_commands[self._poll_index % len(self._poll_commands)]
        self._poll_index += 1
        self._serial.write(build_request(command))


class MspSerialTransport(SerialTelemetryTransport):
    def __init__(self, runtime):
        super().__init__(runtime, "msp", "MSP", 115200, READ_ONLY_COMMANDS)


class CrsfSerialTransport(SerialTelemetryTransport):
    def __init__(self, runtime):
        super().__init__(runtime, "crsf", "CRSF", 420000, ())
