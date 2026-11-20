import argparse,json,os,sys,time
from pathlib import Path
def signal_ok(t):
 if not t:return
 d=Path(os.environ.get('LOCALAPPDATA',Path.home()))/'FPV-Uhyliant';d.mkdir(parents=True,exist_ok=True);tmp=d/'startup-ok.tmp';dst=d/'startup-ok.json';tmp.write_text(json.dumps({'status':'ok','token':t,'version':'2.0.1'}));os.replace(tmp,dst)
def main():
 a=argparse.ArgumentParser(add_help=False);a.add_argument('--self-test',action='store_true');a.add_argument('--install-root');a.add_argument('--startup-token');x,_=a.parse_known_args();here=Path(__file__).resolve().parent
 if x.self_test:print(json.dumps({'status':'ok','version':'2.0.1'}));return 0
 from PySide6.QtCore import QUrl,QTimer
 from PySide6.QtGui import QGuiApplication
 from PySide6.QtQml import QQmlApplicationEngine
 from PySide6.QtQuickControls2 import QQuickStyle
 from backend import Station
 from updater_engine import Updater
 app=QGuiApplication(sys.argv);QQuickStyle.setStyle('Basic');e=QQmlApplicationEngine();s=Station();u=Updater(x.install_root,s.canInstallUpdate);e.rootContext().setContextProperty('station',s);e.rootContext().setContextProperty('updater',u);e.load(QUrl.fromLocalFile(str(here/'Main.qml')))
 if not e.rootObjects():return 1
 QTimer.singleShot(1200,lambda:signal_ok(x.startup_token));return app.exec()
if __name__=='__main__':raise SystemExit(main())

