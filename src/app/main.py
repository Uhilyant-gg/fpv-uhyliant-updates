import argparse,json,os,sys,time,traceback
from pathlib import Path
PROCESS_STARTED_AT=time.monotonic()
from version import VERSION, WINDOW_TITLE
DATA=Path(os.environ.get('LOCALAPPDATA',Path.home()))/'FPV-Uhyliant'
def write_json_atomic(path,payload):path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(payload),encoding='utf-8');os.replace(tmp,path)
def signal_ok(t):
 if t:write_json_atomic(DATA/'startup-ok.json',{'status':'ok','token':t,'version':VERSION})
def signal_smoke(path):write_json_atomic(Path(path),{'status':'ok','version':VERSION,'pid':os.getpid(),'timestamp':int(time.time())})
def log_startup():
 DATA.mkdir(parents=True,exist_ok=True)
 try:(DATA/'startup.log').write_text(traceback.format_exc(),encoding='utf-8')
 except Exception:pass
def compile_qml_smoke(here):
 from PySide6.QtQml import QQmlComponent,QQmlEngine
 engine=QQmlEngine();errors=[]
 for path in sorted(here.glob('*.qml')):
  component=QQmlComponent(engine);component.loadUrl(path.as_uri())
  if component.isError():errors.extend(f'{path.name}: {error.toString()}' for error in component.errors())
 if errors:raise RuntimeError('QML smoke compile failed:\n'+'\n'.join(errors))
def main():
 a=argparse.ArgumentParser(add_help=False);a.add_argument('--self-test',action='store_true');a.add_argument('--mavlink-self-test',action='store_true');a.add_argument('--smoke-test',action='store_true');a.add_argument('--smoke-marker');a.add_argument('--install-root');a.add_argument('--startup-token');a.add_argument('--startup-diagnostics',action='store_true');a.add_argument('--startup-marker');a.add_argument('--acceptance-report',action='store_true');x,_=a.parse_known_args();here=Path(__file__).resolve().parent
 from startup_harness import StartupHarness,default_path,read_startup_acceptance,run_import_probes,run_qt_probe
 harness=StartupHarness(x.startup_marker or default_path(DATA),VERSION,PROCESS_STARTED_AT)
 if x.acceptance_report:
  report=read_startup_acceptance(harness.path)
  print(json.dumps(report,ensure_ascii=False,separators=(',',':')))
  return 0 if report['status']=='accepted' else 1
 harness.mark('main-entry');harness.mark('launch',detail={'phase':'process-started'})
 if x.self_test:harness.mark('self-test');print(json.dumps({'status':'ok','version':VERSION}));return 0
 if x.startup_diagnostics:
  try:run_import_probes(harness);return run_qt_probe(harness,sys.argv)
  except BaseException as exc:harness.failed('startup-diagnostics',exc);raise
 if x.smoke_test:
  harness.mark('smoke-qtcore-begin');from PySide6.QtCore import QCoreApplication
  harness.mark('smoke-qtcore-complete');app=QCoreApplication(sys.argv);compile_qml_smoke(here);signal_smoke(x.smoke_marker or str(DATA/'smoke-test-ok.json'));harness.mark('smoke-complete');return 0
 harness.mark('qt-imports-begin')
 from PySide6.QtCore import QUrl,QTimer
 from PySide6.QtGui import QGuiApplication,QIcon
 from PySide6.QtQml import QQmlApplicationEngine
 from PySide6.QtQuickControls2 import QQuickStyle
 harness.mark('qt-imports-complete');harness.mark('application-imports-begin')
 from backend import Station, HomeDashboard
 from devices_routeaware import Devices
 from updater_engine import Updater
 from video import VideoWorkspaceRuntime
 from stream_workspace import StreamWorkspace
 from firmware_center import FirmwareCenter
 from firmware_executor import FirmwareExecutor
 from firmware_update_session import FirmwareUpdateSession
 from openipc_firmware_acquisition import OpenIPCFirmwareAcquisition
 from camera_credentials import CameraCredentials
 from camera_presets import CameraPresets
 from camera_preset_executor import CameraPresetExecutor
 from link_diagnostics import LinkDiagnostics
 from diagnostic_events import DiagnosticEvents
 from timeline_runtime import TimelineRuntime
 from display_runtime import DisplayRuntime
 from diagnostics_runtime import DiagnosticsRuntime
 from hardware_e2e_runtime import HardwareE2ERuntime
 from station_backup import StationBackup
 from pairing import JsonMetadataStore,PairingRegistry
 from mavlink_runtime import MavlinkRuntime
 from msp_runtime import MspRuntime
 from crsf_runtime import CrsfRuntime
 from serial_telemetry import MspSerialTransport,CrsfSerialTransport
 from telemetry_provider import CrsfProvider,MavlinkProvider,MspProvider,TelemetryRouter
 from vehicle import VehicleRuntime
 harness.mark('application-imports-complete');DATA.mkdir(parents=True,exist_ok=True);qtlog=DATA/'qt-startup.log'
 def qt_message(kind,context,message):
  line=f'{time.strftime("%Y-%m-%d %H:%M:%S")} {int(kind)} {message}'
  try:
   with qtlog.open('a',encoding='utf-8') as f:f.write(line+'\n')
  except Exception:pass
  print(line,file=sys.stderr,flush=True)
 harness.mark('qgui-application-begin');app=QGuiApplication(sys.argv);app.setApplicationName('FPV-Uhyliant');app.setApplicationVersion(VERSION);harness.mark('qgui-application-complete')
 harness.mark('protocol-runtimes-begin');m=MavlinkRuntime(auto_start=False);msp=MspRuntime();crsf=CrsfRuntime();msp_serial=MspSerialTransport(msp);crsf_serial=CrsfSerialTransport(crsf);harness.mark('protocol-runtimes-complete')
 if x.mavlink_self_test:QTimer.singleShot(0,m.start);QTimer.singleShot(350,app.quit);rc=app.exec();m.shutdown();msp_serial.stop();crsf_serial.stop();print(json.dumps({'status':'ok','backend':'mavlink','telemetry':'not simulated'}));return rc
 icon=here/'fpv-uhyliant.ico'
 if icon.exists():app.setWindowIcon(QIcon(str(icon)))
 harness.mark('application-objects-begin');QQuickStyle.setStyle('Basic');e=QQmlApplicationEngine();s=Station();d=Devices();harness.mark('restore',detail={'savedDevices':d.count});home=HomeDashboard(d);video=VideoWorkspaceRuntime(d);v=video.primary;secondary=video.secondary;streams=StreamWorkspace(d);fw=FirmwareCenter(d);acquisition=OpenIPCFirmwareAcquisition(fw,DATA/'firmware-cache');fwexec=FirmwareExecutor(fw);credentials=CameraCredentials();presets=CameraPresets(d);presetexec=CameraPresetExecutor(presets);links=LinkDiagnostics();backup=StationBackup(d);pairing=PairingRegistry(metadata_store=JsonMetadataStore(DATA/'pairing-trust.json'));telemetry=TelemetryRouter([MavlinkProvider(m),MspProvider(msp),CrsfProvider(crsf)]);vehicle=VehicleRuntime(telemetry,v);u=Updater(x.install_root,s.canInstallUpdate);diag_events=DiagnosticEvents();timeline=TimelineRuntime();fwsession=FirmwareUpdateSession(fwexec,d,events=diag_events);diag=DiagnosticsRuntime(VERSION,d,links,telemetry,u,diag_events,DATA,video);hardware_e2e=HardwareE2ERuntime(d,diag,credentials,fw,fwsession);display_runtime=DisplayRuntime(app);app._runtime_refs=(e,s,d,home,video,v,secondary,streams,fw,acquisition,fwexec,fwsession,credentials,presets,presetexec,links,backup,pairing,telemetry,vehicle,u,diag_events,timeline,diag,hardware_e2e,m,msp,crsf,msp_serial,crsf_serial,display_runtime);harness.mark('application-objects-complete')
 d.streamsChanged.connect(streams.autoSelect);streams.autoSelect();pairing.reconcile();ctx=e.rootContext()
 for name,obj in [('station',s),('homeDashboard',home),('devicesModel',d),('videoRuntime',v),('secondaryVideoRuntime',secondary),('videoWorkspaceRuntime',video),('streamWorkspace',streams),('firmwareCenter',fw),('firmwareAcquisition',acquisition),('firmwareExecutor',fwexec),('firmwareUpdateSession',fwsession),('cameraCredentials',credentials),('cameraPresets',presets),('cameraPresetExecutor',presetexec),('linkDiagnostics',links),('stationBackup',backup),('pairingRegistry',pairing),('mavlinkRuntime',m),('mspSerial',msp_serial),('crsfSerial',crsf_serial),('telemetryRuntime',telemetry),('vehicleRuntime',vehicle),('timelineRuntime',timeline),('displayRuntime',display_runtime),('updater',u),('diagnosticsRuntime',diag),('hardwareE2ERuntime',hardware_e2e)]:ctx.setContextProperty(name,obj)
 ctx.setContextProperty('appWindowTitle',WINDOW_TITLE);harness.mark('qml-load-begin');e.load(QUrl.fromLocalFile(str(here/'Main.qml')));harness.mark('qml-load-complete')
 def shutdown():hardware_e2e.reset();credentials.clear();video.stopAll();links.clear();pairing.clearPending();m.shutdown();msp_serial.stop();crsf_serial.stop()
 if not e.rootObjects():harness.mark('launch','error',{'reasonCode':'qml-root-not-created'});shutdown();raise RuntimeError('QML root object failed to load')
 app.aboutToQuit.connect(shutdown);root=e.rootObjects()[0]
 def start_discovery():
  try:
   d.discoverOpenIPC();harness.mark('discovery',detail={'started':True,'savedDevices':d.count})
  except Exception as exc:harness.failed('discovery',exc)
 def show_home():
  root.showMaximized();app.processEvents();visible=root.isVisible();harness.mark('window-visible','ok' if visible else 'error',{'windowVisible':visible});start_discovery()
  harness.mark('health',detail={'health':home.health,'summary':home.summary});harness.mark('devices',detail={'devices':[{'type':item.get('type','')} for item in d.items],'verifiedCount':home.verifiedCount})
  action_available=bool(home.nextAction.get('available'));harness.mark('next-action','ok' if action_available else 'error',{'available':action_available,'action':home.nextAction.get('action')})
 QTimer.singleShot(0,show_home);QTimer.singleShot(0,m.start);QTimer.singleShot(1200,lambda:signal_ok(x.startup_token));QTimer.singleShot(1200,lambda:harness.mark('startup-ready'));harness.mark('event-loop-begin')
 return app.exec()
if __name__=='__main__':
 try:raise SystemExit(main())
 except SystemExit:raise
 except BaseException:log_startup();raise
