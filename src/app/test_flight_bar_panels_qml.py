"""Flight bar: one link block, one flight-controller block, the rest in the menu; hardware and Starlink panels."""

import os
import subprocess
import sys
from pathlib import Path

SCRIPT = r"""
import sys
from pathlib import Path
from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine

app = QGuiApplication(sys.argv)

class Obj(QObject):
    changed = Signal()
    def __init__(self, **values):
        super().__init__()
        self._v = values

def make(cls_name, fields, slots=None):
    attrs = {'changed': Signal()}
    for name, kind in fields.items():
        attrs[name] = Property(kind, (lambda n: lambda self: self._v[n])(name), notify=attrs['changed'])
    for name, (args, result, fn) in (slots or {}).items():
        fn.__name__ = name  # the slot is registered under the function's name
        attrs[name] = Slot(*args, result=result)(fn)
    attrs['__init__'] = lambda self, **v: (QObject.__init__(self), setattr(self, '_v', v))[0]
    return type(cls_name, (QObject,), attrs)

Devices = make('Devices', {'activeId': str, 'activeName': str})
refreshed = []
Connections = make('Connections', {'selected': 'QVariantMap', 'statuses': 'QVariantMap', 'cameraFacts': 'QVariantMap',
                                   'types': 'QVariantList', 'zerotierText': str, 'zerotierState': str},
                   {'addressFor': ((str, str), str, lambda self, d, k: '2001:db8::10'),
                    'refresh': ((), None, lambda self: refreshed.append(1))})
Link = make('Link', {'history': 'QVariantList', 'fps': int, 'lost': bool, 'lostSeconds': int, 'frameSize': str})
Dvr = make('Dvr', {'recording': bool, 'canStart': bool, 'elapsedText': str, 'freeSpaceText': str, 'lowSpace': bool},
           {'toggle': ((), None, lambda self: None)})
Ctl = make('Ctl', {'health': str, 'summary': str})
Dish = make('Dish', {'available': bool, 'status': 'QVariantMap', 'reason': str, 'lastOutageCause': str}, {'poll': ((), None, lambda self: polled.append(1))})
polled = []
VP = make('VP', {'busy': bool}, {'stepBitrate': ((int,), bool, lambda self, d: steps.append(d) or True)})
steps = []
Doctor = make('Doctor', {'details': 'QVariantMap', 'text': str, 'level': str})
Station = make('Station', {'osdEnabled': bool}, {'setOSDEnabled': ((bool,), None, lambda self, v: None)})

types = [{'key': 'local', 'label': 'Локальна мережа'}, {'key': 'starlink', 'label': 'Starlink IPv6'}]
statuses = {'c1': {'local': {'state': 'available', 'latencyMs': 3, 'label': '3 мс'},
                   'starlink': {'state': 'available', 'latencyMs': 58, 'label': '58 мс'}}}
engine = QQmlEngine()
ctx = engine.rootContext()
props = dict(
    devicesModel=Devices(activeId='c1', activeName='Квадрик'),
    connectionsRuntime=Connections(selected={'c1': 'local'}, statuses=statuses,
                                   cameraFacts={'c1': {'summary': 'OpenIPC fpv', 'starlinkFromCamera': True, 'video': {'codec': 'h265', 'size': '1920x1080', 'fps': 60, 'bitrateKbps': 4096, 'gopS': 1}}},
                                   types=types, zerotierText='', zerotierState='ok'),
    linkMonitor=Link(history=[30, 30, 0, 12, 30], fps=30, lost=False, lostSeconds=0, frameSize='1280×720'),
    dvrRuntime=Dvr(recording=False, canStart=True, elapsedText='', freeSpaceText='вільно 3,1 ГБ', lowSpace=False),
    controllerRuntime=Ctl(health='ready', summary='Пульт готовий'),
    station=Station(osdEnabled=True),
    videoPresets=VP(busy=False),
    starlinkDish=Dish(available=True, status={'stateText': 'на зв’язку', 'latencyMs': 42, 'dropPct': 0.5, 'obstructedPct': 3.1, 'currentlyObstructed': False, 'downMbps': 85.3, 'upMbps': 12.4, 'alerts': ['антена перегріта, швидкість знижена']}, reason='', lastOutageCause='перешкода в небі (дерева, будівлі, корпус дрона)'),
    linkDoctor=Doctor(details={'internet': False, 'hasStream': True, 'lossPct': 2.5, 'jitterMs': 4.2, 'kbps': 3200, 'codec': 'H.265', 'keyframeS': 1.0}, text='', level='ok'),
)
for name, obj in props.items():
    ctx.setContextProperty(name, obj)

keep = []
def load(name, **init):
    component = QQmlComponent(engine, QUrl.fromLocalFile(str(Path(name).resolve())))
    item = component.createWithInitialProperties(init) if init else component.create()
    assert item is not None, [e.toString() for e in component.errors()]
    QQmlEngine.setObjectOwnership(item, QQmlEngine.CppOwnership)
    keep.append((component, item))
    return item

def child(item, name):
    found = item.findChild(QObject, name)
    assert found is not None, name
    return found

bar = load('FlightBar.qml', linkKind='starlink', linkKindLabel='Starlink IPv6', linkStatus=statuses['c1']['starlink'],
           linkHistory=[30, 0, 30], linkFps=30, video={'state': 'playing'},
           telemetry={'connected': True, 'batteryVoltage': 16.42, 'freshness': {}})
bar.setProperty('width', 1366)
app.processEvents()
link = child(bar, 'flightBarLink')
assert link.property('caption') == 'Зв’язок · Starlink IPv6' and link.property('value') == '58 мс · 30 к/с'
assert child(bar, 'flightBarFc').property('value') == 'АКБ 16,4 В'
assert bar.findChild(QObject, 'flightBarWindows') is None, 'the streams live in the side panel'

child(bar, 'flightBarBitrateDown').clicked.emit()
child(bar, 'flightBarBitrateUp').clicked.emit()
assert steps == [-1, 1], steps
for gone in ('flightBarPreflight', 'flightBarOsd', 'flightBarVideo', 'flightBarStarlink', 'flightBarHardware'):
    assert bar.findChild(QObject, gone) is None, gone + ' moved to the menu'
assert not child(bar, 'flightBarLowSpace').property('visible'), 'free space only when it runs low'
props['dvrRuntime']._v['lowSpace'] = True
props['dvrRuntime'].changed.emit()
app.processEvents()
assert child(bar, 'flightBarLowSpace').property('visible')
opened = []
bar.openHardware.connect(lambda: opened.append('hardware'))
link.clicked.emit()
child(bar, 'flightBarFc').clicked.emit()
assert opened == ['hardware', 'hardware'], opened
bar.setProperty('linkLost', True)
bar.setProperty('linkLostSeconds', 4)
app.processEvents()
assert link.property('value') == 'немає відео 4 с'
assert child(bar, 'flightMenuToggle').property('text') == '☰ Меню'
bar.setProperty('width', 1000)
app.processEvents()
assert child(bar, 'flightMenuToggle').property('text') == '☰', 'narrow screen: icons only'
bar.setProperty('simulation', True)
app.processEvents()
assert link.property('value') == 'симуляція' and child(bar, 'flightBarFc').property('value') == 'Польотник: штучні дані'
assert not child(bar, 'dvrToggle').property('visible')

hw = load('HardwarePanel.qml', video={'streamId': 's1', 'state': 'playing', 'width': 1280, 'height': 720},
          telemetry={'connected': True, 'batteryVoltage': 16.4, 'satellites': 12})
app.processEvents()
def value_texts(item):
    texts = [o.property('text') for o in item.findChildren(QObject)]
    return [t for t in texts if isinstance(t, str) and t]
texts = value_texts(hw)
assert 'H.265 · 1280×720 · 30 к/с · 3,2 Мбіт/с' in texts, texts
assert 'повний кадр кожні 1 с · у камері задано: 1920×1080, 60 к/с, 4,1 Мбіт/с, повний кадр кожні 1 с' in texts, texts
assert 'затримка 3 мс' in texts, texts
assert 'дані надходять · АКБ 16.4 В · супутників 12' in texts, texts
assert 'Пульт готовий' in texts and 'OpenIPC fpv' in texts, texts
assert not child(hw, 'hardwareZeroTier').property('visible'), 'ZeroTier line only for a ZeroTier connection'
assert not child(hw, 'hardwareInternet').property('visible'), 'a local flight does not need the internet'
assert 'втрачено 2,5% пакетів · нерівність 4 мс · 3,2 Мбіт/с' in texts, texts

props['connectionsRuntime']._v['selected'] = {'c1': 'starlink'}
props['connectionsRuntime'].changed.emit()
app.processEvents()
assert child(hw, 'hardwareInternet').property('visible')
assert 'немає · перевірте роутер або провайдера' in value_texts(hw)
props['connectionsRuntime']._v['selected'] = {'c1': 'static'}
props['connectionsRuntime']._v['statuses'] = {'c1': {'static': {'state': 'available', 'latencyMs': None, 'label': 'камера надсилає'}}}
props['connectionsRuntime'].changed.emit()
app.processEvents()
assert 'камера надсилає' in value_texts(hw), 'a static IP has no latency to show'
props['connectionsRuntime']._v['selected'] = {'c1': 'starlink'}
props['connectionsRuntime']._v['statuses'] = statuses
props['connectionsRuntime'].changed.emit()
sl = load('StarlinkPanel.qml')
app.processEvents()
assert child(sl, 'starlinkState').property('text') == 'Зв’язок є · затримка 58 мс'
assert child(sl, 'starlinkAddress').property('text') == '2001:db8::10 — зчитано з камери'
child(sl, 'starlinkCheckNow').clicked.emit()
assert refreshed == [1]
assert polled == [1], 'the dish is asked too'
assert child(sl, 'starlinkDishState').property('text') == 'на зв’язку · затримка до мережі Starlink 42 мс · втрати 0,5%'
assert child(sl, 'starlinkDishAlerts').property('text') == 'Увага: антена перегріта, швидкість знижена'
assert child(sl, 'starlinkLastOutage').property('text') == 'Останній обрив: перешкода в небі (дерева, будівлі, корпус дрона)'
props['connectionsRuntime']._v['statuses'] = {'c1': {'starlink': {'state': 'unconfigured', 'latencyMs': None, 'label': 'вказати адресу'}}}
props['connectionsRuntime'].changed.emit()
app.processEvents()
assert child(sl, 'starlinkState').property('text') == 'Адресу камери в Starlink ще не отримано'
print('ok')
"""


def test_flight_bar_link_graph_and_panels():
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen", QT_QUICK_BACKEND="software")
    result = subprocess.run(
        [sys.executable, "-c", SCRIPT],
        cwd=Path(__file__).resolve().parent,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "ok" in result.stdout
