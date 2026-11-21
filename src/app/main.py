import argparse,json,os,sys,time,traceback
from pathlib import Path
from version import VERSION, WINDOW_TITLE

DATA=Path(os.environ.get('LOCALAPPDATA',Path.home()))/'FPV-Uhyliant'
def write_json_atomic(path,payload):
 path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(payload),encoding='utf-8');os.replace(tmp,path)
def signal_ok(t):
 if t:write_json_atomic(DATA/'startup-ok.json',{'status':'ok','token':t,'version':VERSION})
def signal_smoke(path):write_json_atomic(Path(path),{'status':'ok','version':VERSION,'pid':os.getpid(),'timestamp':int(time.time())})
def log_startup():
 DATA.mkdir(parents=True,exist_ok=True)
 try:(DATA/'startup.log').write_text(traceback.format_exc(),encoding='utf-8')
 except Exception:pass
def main():
 a=argparse.ArgumentParser(add_help=False);a.add_argument('--self-test',action='store_true');a.add_argument('--mavlink-self-test',action='store_true');a.add_argument('--smoke-test',action='store_true');a.add_argument('--smoke-marker');a.add_argument('--install-root');a.add_argument('--startup-token');x,_=a.parse_known_args();here=Path(__file__).resolve().parent
 if x.self_test:print(json.dumps({'status':'ok','version':VERSION}));return 0
 from PySide6.QtCore import QUrl,QTimer,qInstallMessageHandler
 from PySide6.QtGui import QGuiApplication,QIcon
 from PySide6.QtQml import QQmlApplicationEngine
 from PySide6.QtQuickControls2 import QQuickStyle
 from PySide6 import QtMultimedia
 DATA.mkdir(parents=True,exist_ok=True);qtlog=DATA/'qt-startup.log'
 def qt_message(kind,context,message):
  line=f'{time.strftime("%Y-%m-%d %H:%M:%S")} {int(kind)} {message}'
  try:
   with qtlog.open('a',encoding='utf-8') as f:f.write(line+'\n')
  except Exception:pass
  # Keep Qt/QML diagnostics visible in GitHub Actions and terminal runs.
  print(line,file=sys.stderr,flush=True)
 qInstallMessageHandler(qt_message)
 from backend import Station
 from devices import Devices
 from updater_engine import Updater
 from video import VideoRuntime
 from mavlink_runtime import MavlinkRuntime
 from telemetry_provider import MavlinkProvider
 from vehicle import VehicleRuntime
 app=QGuiApplication(sys.argv);app.setApplicationName('FPV-Uhyliant');app.setApplicationVersion(VERSION)
 m=MavlinkRuntime()
 if x.mavlink_self_test:
  QTimer.singleShot(350,app.quit);rc=app.exec();m.shutdown();print(json.dumps({'status':'ok','backend':'mavlink','telemetry':'not simulated'}));return rc
 icon=here/'fpv-uhyliant.ico'
 if icon.exists():app.setWindowIcon(QIcon(str(icon)))
 QQuickStyle.setStyle('Basic');e=QQmlApplicationEngine();s=Station();d=Devices();v=VideoRuntime(d);telemetry=MavlinkProvider(m);vehicle=VehicleRuntime(telemetry,v);u=Updater(x.install_root,s.canInstallUpdate);e.rootContext().setContextProperty('station',s);e.rootContext().setContextProperty('devicesModel',d);e.rootContext().setContextProperty('videoRuntime',v);e.rootContext().setContextProperty('mavlinkRuntime',m);e.rootContext().setContextProperty('vehicleRuntime',vehicle);e.rootContext().setContextProperty('updater',u);e.rootContext().setContextProperty('appWindowTitle',WINDOW_TITLE);e.load(QUrl.fromLocalFile(str(here/'Main.qml')))
 if not e.rootObjects():
  try:
   tail='\n'.join(qtlog.read_text(encoding='utf-8',errors='replace').splitlines()[-80:])
  except Exception:tail='Qt startup log unavailable'
  raise RuntimeError('QML root object failed to load\n'+tail)
 app.aboutToQuit.connect(m.shutdown);root=e.rootObjects()[0];QTimer.singleShot(0,root.showMaximized)
 if x.smoke_test:
  marker=x.smoke_marker or str(DATA/'smoke-test-ok.json');signal_smoke(marker);QTimer.singleShot(1500,lambda:os._exit(0))
 else:QTimer.singleShot(1200,lambda:signal_ok(x.startup_token))
 return app.exec()
if __name__=='__main__':
 try:raise SystemExit(main())
 except SystemExit:raise
 except BaseException:log_startup();raise
