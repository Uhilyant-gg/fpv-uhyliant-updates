"""Fail-closed OpenIPC firmware catalog, selection binding and verified download boundary."""

import hashlib, json, os, tempfile, urllib.error, urllib.request
from copy import deepcopy
from pathlib import Path
from urllib.parse import urlparse
from PySide6.QtCore import QObject, Property, Signal, Slot

OFFICIAL_MANIFEST_URL = ''.join(('https://', 'openipc.github.io', '/firmware/manifest.json'))
OFFICIAL_DOWNLOAD_HOSTS = ('openipc.org', 'openipc.github.io')
MAX_MANIFEST_BYTES = 4 * 1024 * 1024
MAX_FIRMWARE_BYTES = 64 * 1024 * 1024
NETWORK_TIMEOUT = 15


def _text(value):
    return str(value).strip() if isinstance(value, (str, int)) else ''


def _sha(value):
    value = _text(value).lower()
    return value if len(value) == 64 and all(c in '0123456789abcdef' for c in value) else ''


def _official_url(value):
    try:
        p = urlparse(_text(value))
        return (
            p.scheme == 'https'
            and p.hostname in OFFICIAL_DOWNLOAD_HOSTS
            and not p.username
            and not p.password
            and bool(p.path)
        )
    except ValueError:
        return False


def _entries(payload):
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []
    for key in ('firmwares', 'builds', 'images', 'artifacts'):
        if isinstance(payload.get(key), list):
            return payload[key]
    return []


def _field(item, *names):
    for name in names:
        value = item.get(name) if isinstance(item, dict) else None
        if value not in (None, ''):
            return value
    return ''


def parse_catalog(raw):
    if isinstance(raw, str):
        raw = raw.encode('utf-8')
    if not isinstance(raw, (bytes, bytearray)) or not raw or len(raw) > MAX_MANIFEST_BYTES:
        return []
    try:
        payload = json.loads(bytes(raw).decode('utf-8'))
    except (UnicodeError, json.JSONDecodeError):
        return []
    result = []
    for item in _entries(payload):
        if not isinstance(item, dict):
            continue
        platform = _text(_field(item, 'platform', 'soc', 'chip')).lower()
        sensor = _text(_field(item, 'sensor')).lower()
        variant = _text(_field(item, 'variant', 'flavor')).lower()
        channel = _text(_field(item, 'channel'))
        build = _text(_field(item, 'build', 'version', 'release'))
        url = _text(_field(item, 'url', 'download', 'download_url'))
        sha = _sha(_field(item, 'sha256', 'sha'))
        try:
            size = int(_field(item, 'size', 'bytes') or 0)
        except (TypeError, ValueError):
            size = 0
        if (
            platform
            and sensor
            and variant
            and channel
            and build
            and _official_url(url)
            and sha
            and 0 < size <= MAX_FIRMWARE_BYTES
        ):
            result.append(
                {
                    'platform': platform,
                    'sensor': sensor,
                    'variant': variant,
                    'channel': channel,
                    'build': build,
                    'url': url,
                    'sha256': sha,
                    'size': size,
                }
            )
    return result


def resolve(catalog, platform, sensor, channel='', build='', variant=''):
    platform = _text(platform).lower()
    sensor = _text(sensor).lower()
    channel = _text(channel)
    build = _text(build)
    variant = _text(variant).lower()
    if not platform or not sensor:
        return {'ready': False, 'reason': 'Платформу або сенсор не підтверджено'}
    matches = [x for x in catalog if x.get('platform') == platform and x.get('sensor') == sensor]
    if channel:
        matches = [x for x in matches if x.get('channel') == channel]
    if build:
        matches = [x for x in matches if x.get('build') == build]
    if variant:
        matches = [x for x in matches if x.get('variant') == variant]
    variants = sorted({x.get('variant', '') for x in matches if x.get('variant')})
    if not variant and len(variants) > 1:
        return {'ready': False, 'reason': 'Варіант прошивки потрібно вибрати явно', 'variants': variants}
    builds = sorted({x.get('build', '') for x in matches if x.get('build')})
    if not build and len(builds) > 1:
        return {'ready': False, 'reason': 'Збірку прошивки потрібно вибрати явно', 'builds': builds}
    if len(matches) != 1:
        return {'ready': False, 'reason': 'Не знайдено однозначно сумісний образ'}
    return {'ready': True, 'artifact': dict(matches[0])}


def verify_download(path, artifact):
    if not isinstance(artifact, dict):
        return False
    expected = _sha(artifact.get('sha256'))
    try:
        expected_size = int(artifact.get('size'))
    except (TypeError, ValueError):
        return False
    if not expected or expected_size <= 0 or expected_size > MAX_FIRMWARE_BYTES:
        return False
    p = Path(path)
    h = hashlib.sha256()
    size = 0
    try:
        with p.open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                size += len(chunk)
                if size > expected_size:
                    return False
                h.update(chunk)
    except OSError:
        return False
    return size == expected_size and h.hexdigest() == expected


def _read_response(response, limit):
    final = response.geturl()
    if not _official_url(final):
        raise ValueError('redirected outside official OpenIPC hosts')
    declared = response.headers.get('Content-Length')
    if declared:
        try:
            declared_size = int(declared)
        except ValueError as exc:
            raise ValueError('invalid response size') from exc
        if declared_size < 0 or declared_size > limit:
            raise ValueError('response is too large')
    data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError('response is too large')
    return data


class OpenIPCFirmwareAcquisition(QObject):
    changed = Signal()

    def __init__(self, firmware_center, cache_dir, opener=None):
        super().__init__()
        self.center = firmware_center
        self.cache = Path(cache_dir)
        self.opener = opener or urllib.request.urlopen
        self._catalog = []
        self._generation = 0
        self._status = {'state': 'idle', 'reason': '', 'count': 0, 'selection': {}}

    @Property('QVariantMap', notify=changed)
    def status(self):
        return deepcopy(self._status)

    @Property('QVariantList', notify=changed)
    def catalog(self):
        return deepcopy(self._catalog)

    @Property('QStringList', notify=changed)
    def channels(self):
        return sorted({x['channel'] for x in self._catalog})

    @Slot(str, str, str, result='QStringList')
    def variants(self, platform, sensor, channel):
        return sorted(
            {
                x['variant']
                for x in self._catalog
                if x['platform'] == _text(platform).lower()
                and x['sensor'] == _text(sensor).lower()
                and (not channel or x['channel'] == channel)
            }
        )

    @Slot(str, str, str, str, result='QStringList')
    def builds(self, platform, sensor, channel, variant):
        return sorted(
            {
                x['build']
                for x in self._catalog
                if x['platform'] == _text(platform).lower()
                and x['sensor'] == _text(sensor).lower()
                and (not channel or x['channel'] == channel)
                and (not variant or x['variant'] == _text(variant).lower())
            }
        )

    def _set(self, state, reason='', selection=None, **extra):
        if selection is None:
            selection = {}
        self._status = {
            'state': state,
            'reason': reason,
            'count': len(self._catalog),
            'selection': deepcopy(selection),
            **extra,
        }
        self.changed.emit()

    def _device_snapshot(self, device_id):
        device = next((d for d in self.center.devices.items if d.get('id') == device_id), None)
        identity = (device or {}).get('openipcIdentity') or {}
        if not device or identity.get('verified') is not True:
            return None
        platform = _text(identity.get('platform')).lower()
        sensor = _text(identity.get('sensor')).lower()
        host = _text(device.get('host'))
        if not platform or not sensor or not host:
            return None
        return {'deviceId': device_id, 'host': host, 'platform': platform, 'sensor': sensor}

    def _selection_current(self, selection):
        return (
            isinstance(selection, dict)
            and selection.get('catalogGeneration') == self._generation
            and self._device_snapshot(selection.get('deviceId', '')) == selection.get('device')
            and selection.get('artifact') in self._catalog
        )

    @Slot(result=bool)
    def refresh(self):
        self._generation += 1
        self._catalog = []
        self._set('loading')
        try:
            request = urllib.request.Request(
                OFFICIAL_MANIFEST_URL,
                headers={'Accept': 'application/json', 'User-Agent': 'FPV-Uhyliant/firmware-acquisition'},
            )
            with self.opener(request, timeout=NETWORK_TIMEOUT) as response:
                raw = _read_response(response, MAX_MANIFEST_BYTES)
            catalog = parse_catalog(raw)
            if not catalog:
                raise ValueError('Каталог OpenIPC не містить придатних образів')
        except (OSError, urllib.error.URLError, ValueError, TypeError) as exc:
            self._set('error', str(exc))
            return False
        self._catalog = catalog
        self._set('ready')
        return True

    @Slot(str, str, str, str, result='QVariantMap')
    def selectForDevice(self, device_id, channel, build, variant):
        device = self._device_snapshot(device_id)
        if not device:
            result = {'ready': False, 'reason': 'Пристрій або підтверджену апаратну ідентичність втрачено'}
            self._status = {**self._status, 'selection': result}
            self.changed.emit()
            return result
        result = resolve(self._catalog, device['platform'], device['sensor'], channel, build, variant)
        if result.get('ready'):
            result = {
                **result,
                'deviceId': device_id,
                'device': device,
                'catalogGeneration': self._generation,
                'source': 'official-openipc-catalog',
            }
        self._status = {**self._status, 'selection': deepcopy(result)}
        self.changed.emit()
        return result

    @Slot(str, result='QVariantMap')
    def selectRecommendedForDevice(self, device_id):
        device = self._device_snapshot(device_id)
        if not device:
            result = {'ready': False, 'reason': 'Спочатку виберіть підтверджену OpenIPC-камеру'}
            self._status = {**self._status, 'selection': result}
            self.changed.emit()
            return result
        result = resolve(self._catalog, device['platform'], device['sensor'])
        if result.get('ready'):
            result = {
                **result,
                'deviceId': device_id,
                'device': device,
                'catalogGeneration': self._generation,
                'source': 'official-openipc-catalog',
                'recommended': True,
            }
        self._status = {**self._status, 'selection': deepcopy(result)}
        self.changed.emit()
        return result

    @Slot(str, result=bool)
    def prepareRecommended(self, device_id):
        if not self.refresh():
            return False
        selection = self.selectRecommendedForDevice(device_id)
        if not selection.get('ready'):
            return False
        return self.downloadSelected(device_id)

    @Slot(str, result=bool)
    def downloadSelected(self, device_id):
        selection = deepcopy(self._status.get('selection') or {})
        if selection.get('deviceId') != device_id or not self._selection_current(selection):
            self._set('stale', 'Вибір прошивки застарів; повторіть перевірку сумісності', selection=selection)
            return False
        artifact = selection['artifact']
        expected = _sha(artifact.get('sha256'))
        try:
            size = int(artifact.get('size'))
        except (TypeError, ValueError):
            size = 0
        if not _official_url(artifact.get('url')) or not expected or size <= 0 or size > MAX_FIRMWARE_BYTES:
            self._set('error', 'Невалідні метадані прошивки', selection=selection)
            return False
        self._set('downloading', selection=selection)
        try:
            self.cache.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            self._set('error', 'Не вдалося підготувати кеш прошивки: ' + str(exc), selection=selection)
            return False
        target = self.cache / ('openipc-' + expected[:16] + '.tgz')
        if target.is_file() and verify_download(target, artifact):
            if self._selection_current(selection) and self.center.verifyImage(str(target), expected):
                selection['path'] = str(target)
                self._set('verified', selection=selection)
                return True
            self._set('stale', 'Ідентичність пристрою змінилася під час перевірки кешу', selection=selection)
            return False
        try:
            target.unlink(missing_ok=True)
        except OSError:
            pass
        try:
            fd, tmp = tempfile.mkstemp(prefix='openipc-', suffix='.part', dir=self.cache)
            os.close(fd)
        except OSError as exc:
            self._set('error', 'Не вдалося створити тимчасовий файл прошивки: ' + str(exc), selection=selection)
            return False
        try:
            request = urllib.request.Request(
                artifact['url'],
                headers={'Accept': 'application/octet-stream', 'User-Agent': 'FPV-Uhyliant/firmware-acquisition'},
            )
            with self.opener(request, timeout=NETWORK_TIMEOUT) as response:
                data = _read_response(response, size)
            Path(tmp).write_bytes(data)
            if not verify_download(tmp, artifact):
                raise ValueError('SHA-256 або розмір завантаження не збігається')
            if not self._selection_current(selection):
                raise ValueError('Ідентичність пристрою або каталог змінилися під час завантаження')
            os.replace(tmp, target)
            if not self.center.verifyImage(str(target), expected):
                raise ValueError('Центр прошивки відхилив завантажений образ')
        except (OSError, urllib.error.URLError, ValueError, TypeError) as exc:
            try:
                Path(tmp).unlink(missing_ok=True)
            except OSError:
                pass
            self._set('error', str(exc), selection=selection)
            return False
        selection['path'] = str(target)
        self._set('verified', selection=selection)
        return True

    @Slot()
    def reset(self):
        self._generation += 1
        self._catalog = []
        self._set('idle')
