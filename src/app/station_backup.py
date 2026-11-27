"""Encrypted, versioned station backups with explicit transactional restore."""

import base64, json, os, secrets
from pathlib import Path
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from PySide6.QtCore import QObject, Property, Signal, Slot

from settings_presets import PresetError, validate_state
from station_settings import validate_station_settings

SCHEMA = 'fpv-uhyliant-station-backup'
VERSION = 4
# Version 3 files (devices only) remain importable; version 4 adds presets and station settings.
SUPPORTED_VERSIONS = (3, 4)
KDF = 'scrypt'
CIPHER = 'aes-256-gcm'
N = 16384
R = 8
P = 1


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')


def _b64(value):
    return base64.b64encode(value).decode('ascii')


def _unb64(value):
    return base64.b64decode(value.encode('ascii'), validate=True)


def _derive(password, salt):
    return Scrypt(salt=salt, length=32, n=N, r=R, p=P).derive(password.encode('utf-8'))


def _aad(header):
    return _json(header)


def _seal(payload, password):
    salt = secrets.token_bytes(16)
    nonce = secrets.token_bytes(12)
    header = {
        'schema': SCHEMA,
        'version': VERSION,
        'kdf': KDF,
        'cipher': CIPHER,
        'scrypt': {'n': N, 'r': R, 'p': P},
        'salt': _b64(salt),
        'nonce': _b64(nonce),
    }
    cipher = AESGCM(_derive(password, salt)).encrypt(nonce, _json(payload), _aad(header))
    return {**header, 'ciphertext': _b64(cipher)}


def _open(wrapper, password):
    if (
        not isinstance(wrapper, dict)
        or wrapper.get('schema') != SCHEMA
        or wrapper.get('version') not in SUPPORTED_VERSIONS
        or wrapper.get('kdf') != KDF
        or wrapper.get('cipher') != CIPHER
        or wrapper.get('scrypt') != {'n': N, 'r': R, 'p': P}
    ):
        raise ValueError('unsupported backup envelope')
    header = {k: wrapper[k] for k in ('schema', 'version', 'kdf', 'cipher', 'scrypt', 'salt', 'nonce')}
    salt, nonce, cipher = _unb64(header['salt']), _unb64(header['nonce']), _unb64(wrapper['ciphertext'])
    if len(salt) != 16 or len(nonce) != 12:
        raise ValueError('invalid backup parameters')
    plain = AESGCM(_derive(password, salt)).decrypt(nonce, cipher, _aad(header))
    return json.loads(plain.decode('utf-8'))


class StationBackup(QObject):
    changed = Signal()
    automaticFailure = Signal(str)
    restored = Signal()

    def __init__(self, devices, automatic=None, station=None, presets=None):
        super().__init__()
        self.devices = devices
        self.automatic = automatic
        self.station = station
        self.presets = presets
        self._result = {'ready': False, 'reason': 'Резервну копію ще не створено.', 'manifest': {}}
        self._pending = None
        if automatic is not None:
            devices.setBackupGuard(self._protect_change)

    def _protect_change(self):
        if self.automatic.create():
            return True
        self.automaticFailure.emit(self.automatic.error)
        return False

    @Property('QVariantMap', notify=changed)
    def result(self):
        return dict(self._result)

    def _payload(self):
        payload = {'schema': SCHEMA, 'version': VERSION, 'devices': self.devices.exportSnapshot()}
        if self.station is not None:
            payload['stationSettings'] = self.station.exportSettings()
        if self.presets is not None:
            payload['presets'] = self.presets.load()
        return payload

    def _pending_from(self, payload):
        """Validate every part of a decrypted payload before anything is restored."""
        if payload.get('schema') != SCHEMA or payload.get('version') not in SUPPORTED_VERSIONS:
            return None
        if not self.devices.validateSnapshot(payload.get('devices')):
            return None
        pending = {'devices': payload['devices'], 'settings': None, 'presets': None}
        try:
            if 'stationSettings' in payload:
                pending['settings'] = validate_station_settings(payload['stationSettings'])
            if 'presets' in payload:
                pending['presets'] = validate_state(payload['presets'])
        except (ValueError, PresetError):
            return None
        return pending

    def _set(self, ready, reason, manifest=None):
        self._result = {'ready': bool(ready), 'reason': reason, 'manifest': dict(manifest or {})}
        self.changed.emit()

    @Slot(str, str, result=bool)
    def exportEncrypted(self, path, password):
        if len(password) < 8:
            self._set(False, 'Пароль має містити щонайменше 8 символів.')
            return False
        try:
            target = Path(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            wrapper = _seal(self._payload(), password)
            temp = target.with_suffix(target.suffix + '.tmp')
            temp.write_text(json.dumps(wrapper, ensure_ascii=False, indent=2), encoding='utf-8')
            os.replace(temp, target)
            self._set(
                True,
                'Створено зашифровану резервну копію.',
                {'schema': SCHEMA, 'version': VERSION, 'encrypted': True, 'cipher': CIPHER},
            )
            return True
        except (OSError, TypeError, ValueError, PresetError):
            self._set(
                False,
                'Не вдалося створити резервну копію. Перевірте доступ до вибраної папки та наявність вільного місця.',
            )
            return False

    @Slot(str, str, result='QVariantMap')
    def inspectEncryptedImport(self, path, password):
        self._pending = None
        try:
            payload = _open(json.loads(Path(path).read_text(encoding='utf-8')), password)
            pending = self._pending_from(payload)
            if pending is None:
                self._set(False, 'Не вдалося перевірити резервну копію. Перевірте пароль, файл і його сумісність.')
                return {}
            self._pending = pending
            plan = {
                'schema': SCHEMA,
                'version': payload['version'],
                'encrypted': True,
                'cipher': CIPHER,
                'deviceCount': len(pending['devices']['devices']),
                'presetCount': len(pending['presets']['presets']) if pending['presets'] is not None else 0,
                'includesSettings': pending['settings'] is not None,
                'execution': 'explicit-confirmation-required',
            }
            self._set(True, 'Копію перевірено. Поточні дані не змінено.', plan)
            return dict(plan)
        except (OSError, TypeError, ValueError, KeyError, json.JSONDecodeError, InvalidTag):
            self._set(False, 'Не вдалося перевірити резервну копію. Перевірте пароль, файл і його сумісність.')
            return {}

    @Slot(result='QVariantMap')
    def inspectAutomatic(self):
        self._pending = None
        if self.automatic is None:
            self._set(False, 'Автоматичні резервні копії недоступні.')
            return {}
        payload = self.automatic.latest()
        if payload is None:
            self.automaticFailure.emit(self.automatic.error)
            self._set(False, self.automatic.error)
            return {}
        self._pending = {'devices': payload['devices'], 'settings': None, 'presets': None}
        plan = {
            'schema': SCHEMA,
            'version': VERSION,
            'encrypted': True,
            'deviceCount': len(payload['devices']['devices']),
            'execution': 'explicit-confirmation-required',
            'automatic': True,
        }
        self._set(True, 'Копію перевірено. Поточні дані не змінено.', plan)
        return dict(plan)

    @Slot(bool, result=bool)
    def restoreInspected(self, confirmed):
        if not confirmed or self._pending is None:
            self._set(False, 'Для відновлення підтвердьте перевірену резервну копію.')
            return False
        pending = self._pending
        self._pending = None
        if not self.devices.restoreSnapshot(pending['devices']):
            self._set(
                False,
                (
                    self.automatic.error
                    if self.automatic and self.automatic.error
                    else 'Не вдалося відновити копію. Поточні дані не змінено.'
                ),
            )
            return False
        try:
            if pending['presets'] is not None and self.presets is not None:
                self.presets.replace_state(pending['presets'])
        except (OSError, PresetError):
            self._set(False, 'Пристрої відновлено, але не вдалося відновити пресети. Перевірте доступ до папки даних.')
            self.restored.emit()
            return False
        if (
            pending['settings'] is not None
            and self.station is not None
            and not self.station.applySettings(pending['settings'])
        ):
            self._set(False, 'Пристрої та пресети відновлено, але не вдалося застосувати налаштування станції.')
            self.restored.emit()
            return False
        restored_presets = pending['presets'] is not None and self.presets is not None
        self._set(
            True,
            'Пристрої, відеопотоки, пресети та налаштування відновлено.'
            if restored_presets
            else 'Пристрої та відеопотоки відновлено.',
            {'schema': SCHEMA, 'version': VERSION, 'restored': True},
        )
        self.restored.emit()
        return True

    @Slot()
    def cancelRestore(self):
        self._pending = None
        self._set(False, 'Відновлення скасовано.')
