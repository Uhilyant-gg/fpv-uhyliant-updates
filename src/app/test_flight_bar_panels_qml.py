"""Flight bar: link graph, Starlink button only on a Starlink connection, hardware and Starlink panels."""

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
Link = make('Link', {'history': 'QVariantList', 'fps': int, 'lost': bool, 'lostSeconds': int})
Dvr = make('Dvr', {'recording': bool, 'canStart': bool, 'elapsedText': str, 'freeSpaceText': str},
           {'toggle': ((), None, lambda self: None)})
Ctl = make('Ctl', {'health': str, 'summary': str})
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
                                   cameraFacts={'c1': {'summary': 'OpenIPC fpv', 'starlinkFromCamera': True}},
                                   types=types, zerotierText='', zerotierState='ok'),
    linkMonitor=Link(history=[30, 30, 0, 12, 30], fps=30, lost=False, lostSeconds=0),
    dvrRuntime=Dvr(recording=False, canStart=True, elapsedText='', freeSpaceText='вільно 58 ГБ'),
    controllerRuntime=Ctl(health='ready', summary='Пульт готовий'),
    station=Station(osdEnabled=True),
    linkDoctor=Doctor(details={'internet': False, 'hasStream': True, 'lossPct': 2.5, 'jitterMs': 4.2, 'kbps': 3200}, text='', level='ok'),
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

bar = load('FlightBar.qml', linkKind='local', linkKindLabel='Локальна мережа', linkStatus=statuses['c1']['local'],
           linkHistory=[30, 0, 30])
app.processEvents()
assert not child(bar, 'flightBarStarlink').property('visible'), 'no Starlink button on a local connection'
assert child(bar, 'flightBarHardware').property('visible')
assert child(bar, 'flightBarGraph').property('visible')
opened = []
bar.openHardware.connect(lambda: opened.append('hardware'))
bar.openStarlink.connect(lambda: opened.append('starlink'))
child(bar, 'flightBarHardware').clicked.emit()
bar.setProperty('linkKind', 'starlink')
app.processEvents()
assert child(bar, 'flightBarStarlink').property('visible'), 'Starlink button on a Starlink connection'
child(bar, 'flightBarStarlink').clicked.emit()
child(bar, 'flightBarGraph').clicked.emit()
assert opened == ['hardware', 'starlink', 'starlink'], opened
bar.setProperty('simulation', True)
app.processEvents()
assert not child(bar, 'flightBarHardware').property('visible') and not child(bar, 'flightBarGraph').property('visible')

hw = load('HardwarePanel.qml', video={'streamId': 's1', 'state': 'playing', 'width': 1280, 'height': 720},
          telemetry={'connected': True, 'batteryVoltage': 16.4, 'satellites': 12})
app.processEvents()
def value_texts(item):
    texts = [o.property('text') for o in item.findChildren(QObject)]
    return [t for t in texts if isinstance(t, str) and t]
texts = value_texts(hw)
assert '1280×720 · 30 к/с' in texts, texts
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
