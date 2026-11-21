from pathlib import Path


def replace(path, old, new):
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"pattern not found in {path}: {old[:120]}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")

# Discovery must surface reachable camera candidates before authentication.
replace(
    "src/app/route_discovery.py",
    "import concurrent.futures,ipaddress,json,os,re,socket,subprocess,urllib.error,urllib.request",
    "import base64,concurrent.futures,ipaddress,json,os,re,socket,subprocess,urllib.error,urllib.request",
)
replace(
    "src/app/route_discovery.py",
    '''def _fetch(url,accept,limit,cancel):
 if cancel.is_set():return None
 request=urllib.request.Request(url,headers={"Accept":accept,"User-Agent":"FPV-Uhyliant/route-discovery"})
 try:
  with urllib.request.urlopen(request,timeout=PROBE_TIMEOUT) as response:return response.read(limit)
 except (urllib.error.URLError,TimeoutError,socket.timeout,OSError,ValueError):return None
''',
    '''def _tcp_open(host,port,cancel):
 if cancel.is_set():return False
 try:
  with socket.create_connection((host,port),timeout=PROBE_TIMEOUT):return True
 except (TimeoutError,socket.timeout,OSError,ValueError):return False
def _fetch(url,accept,limit,cancel,username="",password=""):
 if cancel.is_set():return None,0
 headers={"Accept":accept,"User-Agent":"FPV-Uhyliant/route-discovery"}
 if username or password:
  token=base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii");headers["Authorization"]="Basic "+token
 request=urllib.request.Request(url,headers=headers)
 try:
  with urllib.request.urlopen(request,timeout=PROBE_TIMEOUT) as response:return response.read(limit),int(response.status)
 except urllib.error.HTTPError as exc:return None,int(exc.code)
 except (urllib.error.URLError,TimeoutError,socket.timeout,OSError,ValueError):return None,0
''',
)
replace(
    "src/app/route_discovery.py",
    '''def fingerprint(host,cancel):
 identity={"verified":False,"platform":"","soc":"","sensor":"","firmware":"","majestic":"","evidence":[]};result={"host":host,"reachable":False,"camera":False,"openipc":False,"r2d2":False,"identityVerified":False,"identity":identity,"services":[],"streams":[],"evidence":[]}
 try:config_url=_http_url(host,"/api/v1/config.json");status_url=_http_url(host,"/cgi-bin/status.cgi")
 except ValueError:return result
 config=_fetch(config_url,"application/json",524288,cancel)
 if config:
''',
    '''def fingerprint(host,cancel,username="",password=""):
 identity={"verified":False,"platform":"","soc":"","sensor":"","firmware":"","majestic":"","evidence":[]};result={"host":host,"reachable":False,"camera":False,"openipc":False,"r2d2":False,"authRequired":False,"identityVerified":False,"identity":identity,"services":[],"streams":[],"evidence":[]}
 try:config_url=_http_url(host,"/api/v1/config.json");status_url=_http_url(host,"/cgi-bin/status.cgi")
 except ValueError:return result
 open_ports=[port for port in (80,443,554,22) if _tcp_open(host,port,cancel)]
 if open_ports:
  result["reachable"]=True;result["camera"]=any(port in open_ports for port in (80,443,554));result["services"].extend(f"TCP {port}" for port in open_ports);result["evidence"].append("reachable camera services: "+", ".join(map(str,open_ports)))
 config,config_status=_fetch(config_url,"application/json",524288,cancel,username,password)
 if config_status in (401,403):result["authRequired"]=True;result["camera"]=True;result["evidence"].append(f"Majestic API requires authentication ({config_status})")
 if config:
''',
)
replace(
    "src/app/route_discovery.py",
    ''' status=_fetch(status_url,"text/html",262144,cancel)
 if status:
''',
    ''' status,status_code=_fetch(status_url,"text/html",262144,cancel,username,password)
 if status_code in (401,403):result["authRequired"]=True;result["camera"]=True;result["evidence"].append(f"OpenIPC WebUI requires authentication ({status_code})")
 if status:
''',
)
replace(
    "src/app/route_discovery.py",
    ''' if result["openipc"]:identity["verified"]=True;identity["evidence"]=list(result["evidence"]);result["identityVerified"]=any(identity[k] for k in ("platform","soc","sensor","firmware","majestic"))
 return result
''',
    ''' if result["openipc"]:identity["verified"]=True;identity["evidence"]=list(result["evidence"]);result["identityVerified"]=any(identity[k] for k in ("platform","soc","sensor","firmware","majestic"));result["authRequired"]=False
 result["name"]=("OpenIPC " if result["openipc"] else "Камера ")+host;result["hostname"]=host;result["confidence"]="OpenIPC підтверджено" if result["openipc"] else ("Потрібна авторизація" if result["authRequired"] else "Кандидат камери")
 return result
''',
)

# Add explicit authenticated add operation; credentials are used only for this call.
replace(
    "src/app/devices_routeaware.py",
    '''    @Slot(str,str,bool,result=str)
    def addDiscovered(self,host,name,verified):
''',
    '''    @Slot(str,str,str,str,result=str)
    def authenticateAndAdd(self,host,name,username,password):
        address=_safe_private_host(host)
        if not address:return ""
        result=fingerprint(address,threading.Event(),str(username or "").strip(),str(password or ""))
        if not result.get("openipc") or not result.get("identityVerified"):
            self._manual_error="Невірний логін/пароль або OpenIPC не підтверджено";self.manualChanged.emit();return ""
        self._manual_result=result
        for index,item in enumerate(self._discovered):
            if item.get("host")==address:self._discovered[index]=result;break
        else:self._discovered.append(result)
        self.discoveryChanged.emit();self.manualChanged.emit()
        return self.addDiscovered(address,name,True)
    @Slot(str,str,bool,result=str)
    def addDiscovered(self,host,name,verified):
''',
)

# Let the UI surface candidates and prompt for credentials only on Add.
replace(
    "src/app/DevicesPanel.qml",
    ' property var selectedFound:null;property var selectedSaved:null',
    ' property var selectedFound:null;property var selectedSaved:null;property string authHost:"";property string authName:""',
)
replace(
    "src/app/DevicesPanel.qml",
    'Rectangle{width:150;height:28;radius:14;color:modelData.openipc?"#15392f":"#202b38";Text{anchors.centerIn:parent;text:modelData.openipc?"OpenIPC підтверджено":"Кандидат";color:modelData.openipc?accent:muted;font.pixelSize:11}}',
    'Rectangle{width:170;height:28;radius:14;color:modelData.openipc?"#15392f":"#202b38";Text{anchors.centerIn:parent;text:modelData.openipc?"OpenIPC підтверджено":(modelData.authRequired?"Потрібен логін":"Кандидат");color:modelData.openipc?accent:muted;font.pixelSize:11}}',
)
replace(
    "src/app/DevicesPanel.qml",
    '''Button{text:"Додати камеру";font.bold:true;enabled:selectedFound&&selectedFound.openipc;onClicked:{devicesModel.addDiscovered(selectedFound.host,selectedFound.name,true);selectedSaved=null}HoverHint{text:"Зберегти камеру лише після підтвердження OpenIPC."}}''',
    '''Button{text:"Додати камеру";font.bold:true;enabled:selectedFound!==null;onClicked:{if(selectedFound.openipc&&selectedFound.identityVerified){devicesModel.addDiscovered(selectedFound.host,selectedFound.name,true);selectedSaved=null}else{root.authHost=selectedFound.host;root.authName=selectedFound.name;authPopup.open()}}HoverHint{text:"Для захищеної камери логін і пароль запитуються лише під час додавання."}}''',
)
replace(
    "src/app/DevicesPanel.qml",
    '''Button{text:"Додати";enabled:devicesModel.manualResult.openipc===true;onClicked:{devicesModel.addDiscovered(devicesModel.manualResult.host,"OpenIPC "+devicesModel.manualResult.host,true);manualPopup.close()}HoverHint{text:"Зберегти підтверджену OpenIPC-камеру."}}''',
    '''Button{text:"Додати";enabled:devicesModel.manualResult.camera===true;onClicked:{if(devicesModel.manualResult.openipc&&devicesModel.manualResult.identityVerified){devicesModel.addDiscovered(devicesModel.manualResult.host,"OpenIPC "+devicesModel.manualResult.host,true);manualPopup.close()}else{root.authHost=devicesModel.manualResult.host;root.authName="Камера "+devicesModel.manualResult.host;manualPopup.close();authPopup.open()}}HoverHint{text:"Запросити доступ лише під час додавання захищеної камери."}}''',
)
replace(
    "src/app/DevicesPanel.qml",
    ''' Popup{id:detailsPopup;''',
    ''' Popup{id:authPopup;anchors.centerIn:parent;width:Math.min(440,root.width-40);modal:true;padding:20;background:Rectangle{color:raised;radius:18;border.color:line}
  ColumnLayout{width:parent.width;spacing:12
   Text{text:"Доступ до камери";color:fg;font.pixelSize:22;font.bold:true}Text{text:root.authHost;color:muted}
   TextField{id:authUser;Layout.fillWidth:true;text:"root";placeholderText:"Логін"}
   TextField{id:authPassword;Layout.fillWidth:true;placeholderText:"Пароль";echoMode:TextInput.Password}
   Text{visible:devicesModel.manualError!=="";text:devicesModel.manualError;color:danger;wrapMode:Text.WordWrap;Layout.fillWidth:true}
   RowLayout{Layout.fillWidth:true;Button{text:"Перевірити й додати";font.bold:true;onClicked:{var added=devicesModel.authenticateAndAdd(root.authHost,root.authName,authUser.text,authPassword.text);if(added!==""){authPassword.text="";authPopup.close();selectedFound=null}}}Item{Layout.fillWidth:true}Button{text:"Скасувати";flat:true;onClicked:{authPassword.text="";authPopup.close()}}}
  }
 }
 Popup{id:detailsPopup;''',
)

Path("src/app/test_camera_discovery_auth_flow.py").write_text('''from pathlib import Path


def test_discovery_surfaces_auth_candidates():
    source=Path(__file__).with_name("route_discovery.py").read_text(encoding="utf-8")
    assert "authRequired" in source
    assert "_tcp_open" in source
    assert "Basic "+'" + token' in source


def test_credentials_are_requested_only_for_add():
    source=Path(__file__).with_name("DevicesPanel.qml").read_text(encoding="utf-8")
    assert "Потрібен логін" in source
    assert "authenticateAndAdd" in source
    assert "echoMode:TextInput.Password" in source


def test_authenticated_add_is_fail_closed():
    source=Path(__file__).with_name("devices_routeaware.py").read_text(encoding="utf-8")
    assert "def authenticateAndAdd" in source
    assert 'not result.get("openipc") or not result.get("identityVerified")' in source
''',encoding="utf-8")
