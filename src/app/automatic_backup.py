"""Installation-bound encrypted local snapshots for reversible device changes."""

import json
import os
import secrets
import time
import uuid
from pathlib import Path

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from pairing import SecretStoreUnavailable
from snapshot_validation import validate_snapshot
from station_backup import _b64, _json, _unb64

SCHEMA = 'fpv-uhyliant-automatic-backup'
ERROR = 'Не вдалося створити або перевірити автоматичну копію. Зміни не застосовано. Перевірте доступ до диска та захищеного сховища Windows.'
MISSING_KEY = 'Ключ автоматичних копій недоступний. Старі копії неможливо відновити без нього; новий ключ автоматично не створюється.'
INVALID_STATE = 'Поточні дані пристроїв або OSD не пройшли перевірку копії. Зміни не застосовано.'


def valid_devices(devices):
    if (
        not isinstance(devices, dict)
        or devices.get('videoProfiles') != []
        or not isinstance(devices.get('streams'), list)
    ):
        return False
    streams = devices['streams']
    if any(not isinstance(s, dict) or 'video_profile_id' in s for s in streams):
        return False
    return validate_snapshot({**devices, 'streams': [{**s, 'video_profile_id': None} for s in streams]})


def valid_osd(value):
    if not isinstance(value, dict) or set(value) != {'enabled', 'opacity', 'scale', 'position'}:
        return False
    if not isinstance(value['enabled'], bool):
        return False
    for key, low, high in (('opacity', 0.25, 0.8), ('scale', 0.85, 1.3)):
        v = value[key]
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not low <= v <= high:
            return False
    return value['position'] in ('top-left', 'top-right', 'bottom-left', 'bottom-right')


class AutomaticBackup:
    def __init__(self, path, store, devices, station):
        self.path = Path(path)
        self.store = store
        self.devices = devices
        self.station = station
        self.error = ''

    def _identity_and_key(self, create):
        marker = self.path / 'installation-id'
        if marker.exists():
            identity = marker.read_text(encoding='ascii').strip()
            if len(identity) != 32 or uuid.UUID(hex=identity).hex != identity:
                raise ValueError('invalid installation identity')
            key = self.store.get('backup/' + identity)
            if key is None:
                self.error = MISSING_KEY
                raise SecretStoreUnavailable('automatic backup key missing')
            if len(key) != 32:
                raise ValueError('invalid automatic backup key')
            return identity, key
        if not create:
            raise FileNotFoundError('installation identity missing')
        self.path.mkdir(parents=True, exist_ok=True)
        if any(self.path.glob('snapshot-*.fub')):
            raise ValueError('snapshots exist without installation identity')
        identity = uuid.uuid4().hex
        key = secrets.token_bytes(32)
        self.store.put('backup/' + identity, key)
        if self.store.get('backup/' + identity) != key:
            raise SecretStoreUnavailable('automatic backup key verification failed')
        try:
            with marker.open('x', encoding='ascii') as f:
                f.write(identity)
                f.flush()
                os.fsync(f.fileno())
        except FileExistsError:
            self.store.delete('backup/' + identity)
            return self._identity_and_key(False)
        return identity, key

    def _payload(self):
        return {'devices': self.devices.exportSnapshot(), 'osd': self.station.exportOsdSnapshot()}

    def _valid(self, payload):
        return (
            isinstance(payload, dict)
            and set(payload) == {'devices', 'osd'}
            and valid_devices(payload['devices'])
            and self.devices.validateSnapshot(payload['devices'])
            and valid_osd(payload['osd'])
        )

    def _read(self, path, identity, key):
        wrapper = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(wrapper, dict) or set(wrapper) != {
            'schema',
            'version',
            'installationId',
            'nonce',
            'ciphertext',
        }:
            raise ValueError('invalid snapshot')
        header = {k: wrapper[k] for k in ('schema', 'version', 'installationId', 'nonce')}
        if header['schema'] != SCHEMA or header['version'] != 1 or header['installationId'] != identity:
            raise ValueError('incompatible snapshot')
        nonce = _unb64(header['nonce'])
        if len(nonce) != 12:
            raise ValueError('invalid nonce')
        payload = json.loads(AESGCM(key).decrypt(nonce, _unb64(wrapper['ciphertext']), _json(header)).decode('utf-8'))
        if not self._valid(payload):
            raise ValueError('invalid snapshot payload')
        return payload

    def create(self):
        self.error = ''
        try:
            payload = self._payload()
            if not self._valid(payload):
                self.error = INVALID_STATE
                raise ValueError('invalid live snapshot')
            identity, key = self._identity_and_key(True)
            header = {
                'schema': SCHEMA,
                'version': 1,
                'installationId': identity,
                'nonce': _b64(secrets.token_bytes(12)),
            }
            wrapper = {
                **header,
                'ciphertext': _b64(AESGCM(key).encrypt(_unb64(header['nonce']), _json(payload), _json(header))),
            }
            path = self.path / ('snapshot-%020d-%s.fub' % (time.time_ns(), uuid.uuid4().hex))
            with path.open('x', encoding='utf-8') as f:
                json.dump(wrapper, f, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            if self._read(path, identity, key) != payload:
                raise ValueError('snapshot verification failed')
            pointer = self.path / ('latest-' + uuid.uuid4().hex + '.tmp')
            with pointer.open('x', encoding='ascii') as f:
                f.write(path.name)
                f.flush()
                os.fsync(f.fileno())
            os.replace(pointer, self.path / 'latest')
            return True
        except (OSError, SecretStoreUnavailable, ValueError, TypeError, KeyError, InvalidTag, UnicodeError):
            self.error = self.error or ERROR
            return False

    def latest(self):
        self.error = ''
        try:
            identity, key = self._identity_and_key(False)
            name = (self.path / 'latest').read_text(encoding='ascii')
            if not name.startswith('snapshot-') or not name.endswith('.fub') or Path(name).name != name:
                raise ValueError('invalid snapshot reference')
            return self._read(self.path / name, identity, key)
        except (OSError, SecretStoreUnavailable, ValueError, TypeError, KeyError, InvalidTag, UnicodeError):
            self.error = self.error or 'Не вдалося перевірити останню автоматичну копію. Поточні дані не змінено.'
            return None
