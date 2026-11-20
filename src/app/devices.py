import json, os, uuid
from pathlib import Path
from PySide6.QtCore import QObject, Property, Signal, Slot

DATA = Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'FPV-Uhyliant'
DB = DATA / 'devices.json'

class Devices(QObject):
    changed = Signal()
    notice = Signal(str)

    def __init__(self):
        super().__init__()
        DATA.mkdir(parents=True, exist_ok=True)
        self._items = []
        self._active_id = ''
        self._load()

    def _load(self):
        try:
            raw = json.loads(DB.read_text(encoding='utf-8')) if DB.exists() else {}
            self._items = raw.get('devices', []) if isinstance(raw, dict) else []
            self._active_id = raw.get('activeDeviceId', '') if isinstance(raw, dict) else ''
            if self._active_id and not any(x.get('id') == self._active_id for x in self._items):
                self._active_id = ''
        except (OSError, ValueError, TypeError):
            self._items = []
            self._active_id = ''

    def _save(self):
        tmp = DB.with_suffix('.tmp')
        tmp.write_text(json.dumps({'schema': 1, 'activeDeviceId': self._active_id, 'devices': self._items}, ensure_ascii=False, indent=2), encoding='utf-8')
        os.replace(tmp, DB)

    def _public(self, item):
        return {
            'id': item.get('id', ''),
            'name': item.get('name', ''),
            'type': item.get('type', ''),
            'host': item.get('host', ''),
            'port': item.get('port', 0),
            'connection': item.get('connection', ''),
            'notes': item.get('notes', ''),
            'active': item.get('id') == self._active_id,
        }

    @Property('QVariantList', notify=changed)
    def items(self):
        return [self._public(x) for x in self._items]

    @Property(int, notify=changed)
    def count(self):
        return len(self._items)

    @Property(str, notify=changed)
    def activeId(self):
        return self._active_id

    @Property(str, notify=changed)
    def activeName(self):
        for item in self._items:
            if item.get('id') == self._active_id:
                return item.get('name', '')
        return ''

    @Property(str, notify=changed)
    def activeSummary(self):
        for item in self._items:
            if item.get('id') == self._active_id:
                host = item.get('host', '')
                return f"{item.get('type', '')} · {host}" if host else item.get('type', '')
        return ''

    @Slot(str, str, str, int, str, str, result=str)
    def addDevice(self, name, device_type, host, port, connection, notes):
        name = name.strip()
        host = host.strip()
        if not name:
            self.notice.emit('Вкажіть назву пристрою')
            return ''
        if device_type not in ('Камера OpenIPC', 'Політний контролер', 'Борт'):
            self.notice.emit('Невідомий тип пристрою')
            return ''
        if connection not in ('Мережа', 'Serial/COM', 'Комбінований'):
            self.notice.emit('Невідомий тип підключення')
            return ''
        device_id = uuid.uuid4().hex
        self._items.append({'id': device_id, 'name': name, 'type': device_type, 'host': host, 'port': max(0, min(int(port), 65535)), 'connection': connection, 'notes': notes.strip()})
        if not self._active_id:
            self._active_id = device_id
        self._save(); self.changed.emit(); self.notice.emit('Пристрій збережено')
        return device_id

    @Slot(str)
    def setActive(self, device_id):
        if any(x.get('id') == device_id for x in self._items):
            self._active_id = device_id
            self._save(); self.changed.emit()

    @Slot(str)
    def removeDevice(self, device_id):
        before = len(self._items)
        self._items = [x for x in self._items if x.get('id') != device_id]
        if len(self._items) == before:
            return
        if self._active_id == device_id:
            self._active_id = self._items[0]['id'] if self._items else ''
        self._save(); self.changed.emit(); self.notice.emit('Пристрій видалено')
