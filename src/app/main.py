import argparse,json,os,sys,traceback
from pathlib import Path
from version import VERSION, WINDOW_TITLE

DATA=Path(os.environ.get('LOCALAPPDATA',Path.home()))/'FPV-Uhyliant'
def signal_ok(t):
 if not t:return
 DATA.mkdir(parents=True,exist_ok=True);tmp=DATA/'startup-ok.tmp';dst=DATA/'startup-ok.json';tmp.write_text(json.dumps({'status':'ok','token':t,'version':VERSION}),encoding='utf-8');os.replace(tmp,dst)
def log_startup():
 DATA.mkdir(parents=True,exist_ok=True)
 try:(DATA/'startup.log').write_text(traceback.format_exc(),encoding='utf-8')
 except Exception:pass
def main():
 a=argparse.ArgumentParser(add_help=False);a.add_argument('--self-test',action='store_true');a.add_argument('--smoke-test',action='store_true');a.add_argument('--install-root');a.add_argument('--startup-token');x,_=a.parse_known_args();here=Path(__file__).resolve().parent
 if x.self_test:print(json.dumps({'status':'ok','version':VERSION}));return 0
 from PySide6.QtCore import QUrl,QTimer
 from PySide6.QtGui import QGuiApplication,QIcon
 from PySide6.QtQml import QQmlApplicationEngine
 from PySide6.QtQuickControls2 import QQuickStyle
 from PySide6 import QtMultimedia
 from backend import Station
 from devices import Devices
 from updater_engine import Updater
 from video import VideoRuntime
 app=QGuiApplication(sys.argv);app.setApplicationName('FPV-Uhyliant');app.setApplicationVersion(VERSION)
 icon=here/'fpv-uhyliant.ico'
 if icon.exists():app.setWindowIcon(QIcon(str(icon)))
 QQuickStyle.setStyle('Basic');e=QQmlApplicationEngine();s=Station();d=Devices();v=VideoRuntime(d);u=Updater(x.install_root,s.canInstallUpdate);e.rootContext().setContextProperty('station',s);e.rootContext().setContextProperty('devicesModel',d);e.rootContext().setContextProperty('videoRuntime',v);e.rootContext().setContextProperty('updater',u);e.rootContext().setContextProperty('appWindowTitle',WINDOW_TITLE);e.load(QUrl.fromLocalFile(str(here/'Main.qml')))
 if not e.rootObjects():raise RuntimeError('QML root object failed to load')
 root=e.rootObjects()[0];QTimer.singleShot(0,root.showMaximized)
 if x.smoke_test:QTimer.singleShot(1500,app.quit)
 else:QTimer.singleShot(1200,lambda:signal_ok(x.startup_token))
 return app.exec()
if __name__=='__main__':
 try:raise SystemExit(main())
 except SystemExit:raise
 except BaseException:
  log_startup();raise
