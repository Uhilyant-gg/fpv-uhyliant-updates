import argparse,json,os,sys,time,traceback
from pathlib import Path
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
def load_main_qml(engine,here,smoke,QUrl):
 path=here/'Main.qml'
 if not smoke:engine.load(QUrl.fromLocalFile(str(path)));return
 source=path.read_text(encoding='utf-8')
 replacements={
  'AudioOutput{id:audioOut;muted:true}':'QtObject{id:audioOut;property bool muted:true}',
  'MediaPlayer{id:player;videoOutput:videoOut;audioOutput:audioOut;onPlayingChanged:{if(playing){videoRecovery.stop();videoRecoveryCount=0;videoRuntime.markPlaying()}else if(videoRuntime.state==="playing"){videoRuntime.markStalled("Основний RTSP несподівано зупинився");videoRecovery.restart()}}onErrorOccurred:function(error,errorString){videoRuntime.playbackError(errorString);if(videoRuntime.streamId!=="")videoRecovery.restart()}}':'QtObject{id:player;property url source:"";readonly property int playbackState:0;function stop(){} function play(){}}',
  'MediaPlayer{id:secondaryPlayer;videoOutput:secondaryVideoOut;onPlayingChanged:{if(playing){secondaryRecovery.stop();secondaryRecoveryCount=0;secondaryVideoRuntime.markPlaying()}else if(pipEnabled&&secondaryVideoRuntime.state==="playing"){secondaryVideoRuntime.markStalled("Додатковий RTSP несподівано зупинився");secondaryRecovery.restart()}}onErrorOccurred:function(error,errorString){secondaryVideoRuntime.playbackError(errorString);if(pipEnabled&&secondaryVideoRuntime.streamId!=="")secondaryRecovery.restart()}}':'QtObject{id:secondaryPlayer;property url source:"";readonly property int playbackState:0;function stop(){} function play(){}}',
  'VideoOutput{id:videoOut;anchors.fill:parent;fillMode:VideoOutput.PreserveAspectFit}':'Item{id:videoOut;anchors.fill:parent}',
  'VideoOutput{id:secondaryVideoOut;anchors.fill:parent;fillMode:VideoOutput.PreserveAspectFit}':'Item{id:secondaryVideoOut;anchors.fill:parent}',
 }
 for production,headless in replacements.items():
  if source.count(production)!=1:raise RuntimeError('QML smoke multimedia boundary is out of sync with Main.qml')
  source=source.replace(production,headless)
 engine.loadData(source.encode('utf-8'),QUrl.fromLocalFile(str(here)+os.sep))
def main():
 a=argparse.ArgumentParser(add_help=False);a.add_argument('--self-test',action='store_true');a.add_argument('--mavlink-self-test',action='store_true');a.add_argument('--smoke-test',action='store_true');a.add_argument('--smoke-marker');a.add_argument('--install-root');a.add_argument('--startup-token');x,_=a.parse_known_args();here=Path(__file__).resolve().parent
 if x.self_test:print(json.dumps({'status':'ok','version':VERSION}));return 0
 from PySide6.QtCore import QUrl,QTimer,qInstallMessageHandler
 from PySide6.QtGui import QGuiApplication,QIcon
 from PySide6.QtQml import QQmlApplicationEngine
 from PySide6.QtQuickControls2 import QQuickStyle
 from backend import Station
 from devices_routeaware import Devices
 from updater_engine import Updater
 from video import VideoWorkspaceRuntime
 from stream_workspace import StreamWorkspace
 from firmware_center import FirmwareCenter
 from firmware_executor import FirmwareExecutor
 from firmware_update_session import FirmwareUpdateSession
 from camera_credentials import CameraCredentials
 from camera_presets import CameraPresets
 from camera_preset_executor import CameraPresetExecutor
 from link_diagnostics import LinkDiagnostics
 from station_backup import StationBackup
 from pairing import JsonMetadataStore,PairingRegistry
 from mavlink_runtime import MavlinkRuntime
 from msp_runtime import MspRuntime
 from crsf_runtime import CrsfRuntime
 from serial_telemetry import MspSerialTransport,CrsfSerialTransport
 from telemetry_provider import CrsfProvider,MavlinkProvider,MspProvider,TelemetryRouter
 from vehicle import VehicleRuntime
 DATA.mkdir(parents=True,exist_ok=True);qtlog=DATA/'qt-startup.log'
 def qt_message(kind,context,message):
  line=f'{time.strftime("%Y-%m-%d %H:%M:%S")} {int(kind)} {message}'
  try:
   with qtlog.open('a',encoding='utf-8') as f:f.write(line+'\n')
  except Exception:pass
  print(line,file=sys.stderr,flush=True)
 qInstallMessageHandler(qt_message);app=QGuiApplication(sys.argv);app.setApplicationName('FPV-Uhyliant');app.setApplicationVersion(VERSION)
 m=MavlinkRuntime();msp=MspRuntime();crsf=CrsfRuntime();msp_serial=MspSerialTransport(msp);crsf_serial=CrsfSerialTransport(crsf)
 if x.mavlink_self_test:QTimer.singleShot(350,app.quit);rc=app.exec();m.shutdown();msp_serial.stop();crsf_serial.stop();print(json.dumps({'status':'ok','backend':'mavlink','telemetry':'not simulated'}));return rc
 icon=here/'fpv-uhyliant.ico'
 if icon.exists():app.setWindowIcon(QIcon(str(icon)))
 QQuickStyle.setStyle('Basic');e=QQmlApplicationEngine();s=Station();d=Devices();video=VideoWorkspaceRuntime(d);v=video.primary;secondary=video.secondary;streams=StreamWorkspace(d);fw=FirmwareCenter(d);fwexec=FirmwareExecutor(fw);fwsession=FirmwareUpdateSession(fwexec,d);credentials=CameraCredentials();presets=CameraPresets(d);presetexec=CameraPresetExecutor(presets);links=LinkDiagnostics();backup=StationBackup(d);pairing=PairingRegistry(metadata_store=JsonMetadataStore(DATA/'pairing-trust.json'));telemetry=TelemetryRouter([MavlinkProvider(m),MspProvider(msp),CrsfProvider(crsf)]);vehicle=VehicleRuntime(telemetry,v);u=Updater(x.install_root,s.canInstallUpdate)
 d.streamsChanged.connect(streams.autoSelect);streams.autoSelect();pairing.reconcile();ctx=e.rootContext()
 for name,obj in [('station',s),('devicesModel',d),('videoRuntime',v),('secondaryVideoRuntime',secondary),('videoWorkspaceRuntime',video),('streamWorkspace',streams),('firmwareCenter',fw),('firmwareExecutor',fwexec),('firmwareUpdateSession',fwsession),('cameraCredentials',credentials),('cameraPresets',presets),('cameraPresetExecutor',presetexec),('linkDiagnostics',links),('stationBackup',backup),('pairingRegistry',pairing),('mavlinkRuntime',m),('mspSerial',msp_serial),('crsfSerial',crsf_serial),('telemetryRuntime',telemetry),('vehicleRuntime',vehicle),('updater',u)]:ctx.setContextProperty(name,obj)
 ctx.setContextProperty('appWindowTitle',WINDOW_TITLE);load_main_qml(e,here,x.smoke_test,QUrl)
 def shutdown():credentials.clear();video.stopAll();links.clear();pairing.clearPending();m.shutdown();msp_serial.stop();crsf_serial.stop()
 if not e.rootObjects():shutdown();raise RuntimeError('QML root object failed to load')
 app.aboutToQuit.connect(shutdown);root=e.rootObjects()[0];QTimer.singleShot(0,root.showMaximized)
 if x.smoke_test:
  marker=x.smoke_marker or str(DATA/'smoke-test-ok.json');signal_smoke(marker);QTimer.singleShot(1500,lambda:os._exit(0))
 else:QTimer.singleShot(1200,lambda:signal_ok(x.startup_token))
 return app.exec()
if __name__=='__main__':
 try:raise SystemExit(main())
 except SystemExit:raise
 except BaseException:log_startup();raise
