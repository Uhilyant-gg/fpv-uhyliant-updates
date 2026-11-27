import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import QtMultimedia
ApplicationWindow {
 id:w;visible:true;visibility:Window.Maximized;minimumWidth:1024;minimumHeight:640;color:"#050a12";title:appWindowTitle
 property color fg:"#f4f7fb";property color sub:"#b7c8da";property color line:"#4a6078";property color green:"#27d59a";property color blue:"#2387ff";property color amber:"#ffb84d";property color red:"#ff6678"
 font.family: "Segoe UI"
 font.pixelSize: 14
 palette.window: "#0d1725"; palette.windowText: "#f4f7fb"; palette.text: "#f4f7fb"; palette.buttonText: "#f4f7fb"; palette.button: "#253b52"; palette.base: "#152638"; palette.highlight: "#2679d9"; palette.highlightedText: "white"; palette.placeholderText: "#b7c8da"
 property bool simulation: false
 property int simulationTick: 0
 property var simulatedTelemetry: ({connected:true, provider:"MAVLink", armed:false, flightMode:"STABILIZE", batteryVoltage:15.8 + 0.1 * Math.sin(simulationTick / 12), batteryRemaining:82, gpsFix:3, satellites:12, altitude:124 + Math.round(4 * Math.sin(simulationTick / 5)), groundSpeed:12.4 + Math.sin(simulationTick / 4), heading:(348 + simulationTick) % 360, roll:12 * Math.sin(simulationTick / 7), pitch:7 * Math.sin(simulationTick / 9), yaw:(348 + simulationTick) % 360, homeDistance:86 + Math.round(10 * Math.sin(simulationTick / 8))})
 property var simulatedVideo: ({streamId:"simulation",state:"playing"})
 Timer { interval: 1000; repeat: true; running: w.simulation; onTriggered: w.simulationTick++ }
 property bool connected:devicesModel.activeName!=="";property bool serviceMode:false;property bool primaryDetached:false;property bool secondaryDetached:false;property int selectedDisplayIndex:0;property string displayMoveMessage:"";property string displayFallbackNotice:"";property string selectedStreamId:streamWorkspace.state.primaryId||"";property string secondaryStreamId:streamWorkspace.state.secondaryId||"";readonly property bool pipEnabled:videoWorkspaceRuntime.pipEnabled;property var t:telemetryRuntime.telemetry;property var vd:videoRuntime.diagnostics;property var sd:secondaryVideoRuntime.diagnostics;property var ext:linkDiagnostics.externalNavigation;property var net:linkDiagnostics.network;property int videoRecoveryCount:0;property int secondaryRecoveryCount:0
 function val(v,suffix,digits){return v===undefined||v===null?"--":Number(v).toFixed(digits===undefined?0:digits)+(suffix||"")}
 function stateUa(value){if(value===undefined||value===null||value==="")return "недоступно";var states={"idle":"очікування","stopped":"зупинено","checking":"перевірка","ready":"готово","playing":"відтворення","reconnecting":"перепідключення","stalled":"зупинка потоку","error":"помилка","blocked":"заблоковано","executing":"виконання","installing":"встановлення","reboot-pending":"очікується перезапуск","verified":"перевірено","hardware-validation-pending":"очікується перевірка на обладнанні","applied-pending-verification":"застосовано, очікується перевірка","unavailable":"недоступно","unknown":"ще не визначено","connected":"підключено","disconnected":"відключено","stale":"дані давно не оновлювалися","degraded":"працює нестабільно","attention":"потребує уваги","traffic-no-heartbeat":"є передавання без підтвердження зв’язку","ok":"справно"};return states[value]||"потрібна перевірка"}
 function stopPrimary(){videoRecovery.stop();player.stop();player.source="";videoRuntime.stop();videoRecoveryCount=0}
 function stopSecondary(){secondaryRecovery.stop();secondaryPlayer.stop();secondaryPlayer.source="";secondaryVideoRuntime.stop();secondaryRecoveryCount=0}
 function setPip(enabled){var requested=enabled&&streamWorkspace.state.pipAvailable;videoWorkspaceRuntime.setPipEnabled(requested);if(!requested)stopSecondary();else startSecondary()}
 function connectDevice(id){var item=null;for(var i=0;i<devicesModel.items.length;i++){if(devicesModel.items[i].id===id){item=devicesModel.items[i];break}}if(!item||item.onboardingState!=="ready")return;serviceMode=false;stopPrimary();setPip(false);devicesModel.setActive(id);timelineRuntime.recordEvent("camera-selected");streamWorkspace.autoSelect();if(devicesModel.activeName!==""&&streamWorkspace.state.primaryId!=="")startSelected()}
 function disconnectDevice(){serviceMode=false;primaryDetached=false;secondaryDetached=false;stopPrimary();setPip(false);videoWorkspaceRuntime.stopAll();devicesModel.clearActive();streamWorkspace.autoSelect()}
 function enterServiceMode(){serviceMode=true;stopPrimary();setPip(false)}
 function openFirmwareFor(deviceId){devices.close();firmwarePopup.open();Qt.callLater(function(){if(firmwarePanelLoader.item)firmwarePanelLoader.item.selectDevice(deviceId)})}
 function openOsdSettings(){if(!osdSettingsLoader.active){osdSettingsLoader.active=true;Qt.callLater(openOsdSettings);return}osdSettingsLoader.item.editingAllowed=w.simulation||t.armed!==true;osdSettingsPopup.open()}
 function startSelected(){stopPrimary();if(connected&&selectedStreamId!==""&&videoWorkspaceRuntime.preparePrimary(selectedStreamId)){player.source=videoRuntime.url;player.play()}if(pipEnabled)startSecondary()}
 function startSecondary(){stopSecondary();if(pipEnabled&&connected&&secondaryStreamId!==""&&videoWorkspaceRuntime.prepareSecondary(secondaryStreamId)){secondaryPlayer.source=secondaryVideoRuntime.url;secondaryPlayer.play()}}
 function rebuildPlayback(){var wasPlaying=player.playbackState===MediaPlayer.PlayingState||videoRuntime.streamId!=="";var keepPip=pipEnabled&&streamWorkspace.state.pipAvailable;stopPrimary();stopSecondary();if(wasPlaying)startSelected();if(keepPip&&streamWorkspace.state.pipAvailable){videoWorkspaceRuntime.setPipEnabled(true);startSecondary()}}
 function recoverPrimary(){if(!connected||videoRuntime.url==="")return;if(videoRecoveryCount>=5){videoRuntime.markStalled("Не вдалося автоматично відновити основний відеопотік.");return}videoRecoveryCount++;player.stop();if(videoRuntime.reconnect()){player.source="";player.source=videoRuntime.url;player.play()}else videoRecovery.start()}
 function recoverSecondary(){if(!pipEnabled||secondaryVideoRuntime.url==="")return;if(secondaryRecoveryCount>=5){secondaryVideoRuntime.markStalled("Не вдалося автоматично відновити додатковий відеопотік.");return}secondaryRecoveryCount++;secondaryPlayer.stop();if(secondaryVideoRuntime.reconnect()){secondaryPlayer.source="";secondaryPlayer.source=secondaryVideoRuntime.url;secondaryPlayer.play()}else secondaryRecovery.start()}
 onPipEnabledChanged:if(!pipEnabled){secondaryDetached=false;secondaryRecovery.stop();secondaryPlayer.stop();secondaryPlayer.source="";secondaryRecoveryCount=0}
 MediaPlayer{id:player;videoOutput:primaryDetached?detachedPrimaryVideoOut:videoOut;onPlayingChanged:{timelineRuntime.observe("primary-video",playing?"playing":"stopped");if(playing){videoRecovery.stop();videoRecoveryCount=0;videoRuntime.markPlaying()}else if(videoRuntime.state==="playing"){videoRuntime.markStalled("Основний відеопотік несподівано зупинився.");videoRecovery.restart()}}onErrorOccurred:function(error,errorString){videoRuntime.playbackError(errorString);if(videoRuntime.streamId!=="")videoRecovery.restart()}}
 property bool dvrVideoAvailable: !simulation && connected && player.playbackState === MediaPlayer.PlayingState
 onDvrVideoAvailableChanged: dvrRuntime.setVideoAvailable(dvrVideoAvailable)
 onConnectedChanged: if (!connected) dvrRuntime.stop()
 function attachDvrSink(){dvrRuntime.setVideoSink(player.videoOutput ? player.videoOutput.videoSink : null)}
 Connections{target:player;function onVideoOutputChanged(){w.attachDvrSink()}}
 property string dvrCameraName: devicesModel.activeName
 onDvrCameraNameChanged: dvrRuntime.setCameraName(dvrCameraName)
 Connections{target:dvrRuntime;function onStatusChanged(){if(dvrRuntime.status!==""){dvrNotice.text=dvrRuntime.status;dvrNoticeTimer.restart()}}}
 Component.onCompleted: {attachDvrSink();dvrRuntime.setCameraName(devicesModel.activeName);dvrRuntime.setVideoAvailable(dvrVideoAvailable)}
 Timer{id:dvrNoticeTimer;interval:6000;onTriggered:dvrNotice.text=""}
 MediaPlayer{id:secondaryPlayer;videoOutput:secondaryDetached?detachedSecondaryVideoOut:secondaryVideoOut;onPlayingChanged:{timelineRuntime.observe("secondary-video",playing?"playing":"stopped");if(playing){secondaryRecovery.stop();secondaryRecoveryCount=0;secondaryVideoRuntime.markPlaying()}else if(pipEnabled&&secondaryVideoRuntime.state==="playing"){secondaryVideoRuntime.markStalled("Додатковий відеопотік несподівано зупинився.");secondaryRecovery.restart()}}onErrorOccurred:function(error,errorString){secondaryVideoRuntime.playbackError(errorString);if(pipEnabled&&secondaryVideoRuntime.streamId!=="")secondaryRecovery.restart()}}
 Connections{target:telemetryRuntime;function onChanged(){timelineRuntime.observe("telemetry",t.connected===true?"connected":(t.connected===false?"lost":"unknown"));if(osdSettingsPopup.visible&&!w.simulation&&osdSettingsLoader.item)osdSettingsLoader.item.editingAllowed=t.armed!==true}}
 Connections{target:devicesModel;function onDiscoveryChanged(){timelineRuntime.observe("discovery",devicesModel.scanning?"scanning":(devicesModel.discoveryStage==="Готово"?"completed":(devicesModel.discoveryStage==="Скасовано"?"cancelled":(devicesModel.discoveryStage==="Помилка"?"failed":"unknown"))))}}
 Connections{target:devicesModel;function onDeviceAdded(){timelineRuntime.recordEvent("device-added")}function onDeviceUpdated(){timelineRuntime.recordEvent("device-updated")}function onDeviceRemoved(){timelineRuntime.recordEvent("device-removed")}function onDeviceListRestored(){timelineRuntime.recordEvent("device-list-restored")}function onFirmwarePreparationRequested(deviceId){w.openFirmwareFor(deviceId)}}
 Connections{target:station;function onOsdSettingsSaved(){osdSettingsTimelineTimer.restart()}}
 Connections{target:stationBackup;function onAutomaticFailure(message){backupFailureText.text=message;backupFailurePopup.open()}}
 Connections{target:updater;function onChanged(){timelineRuntime.observe("update",updater.updateState)}}
 Connections{target:firmwareUpdateSession;function onChanged(){var result=firmwareUpdateSession.result;timelineRuntime.observe("camera-firmware",result.state);if(result.state==="verified"&&result.transaction.deviceId&&result.verification.ok===true)devicesModel.completeFirmwareOnboarding(result.transaction.deviceId,result.verification)}}
 Connections{target:linkDiagnostics;function onChanged(){timelineRuntime.observe("network",net.state==="ready"?"ready":(net.state==="degraded"?"degraded":(net.state==="error"||net.state==="stale"?"lost":"unknown")));timelineRuntime.observe("navigation",ext.state==="ready"?"ready":(ext.state==="degraded"?"degraded":(ext.state==="error"||ext.state==="stale"?"lost":"unknown")))}}
 Connections{target:displayRuntime;function onChanged(){if(w.selectedDisplayIndex>=displayRuntime.displays.length)w.selectedDisplayIndex=0}function onWindowReturnedToWorkspace(window){if(window===primaryStreamWindow||window===secondaryStreamWindow){if(window===primaryStreamWindow)w.primaryDetached=false;else w.secondaryDetached=false;w.displayFallbackNotice="Екран від’єднано. Відеопотік повернуто до основного робочого простору.";displayFallbackTimer.restart()}}}
 Timer{id:displayFallbackTimer;interval:6000;repeat:false;onTriggered:w.displayFallbackNotice=""}
 Timer{id:osdSettingsTimelineTimer;interval:1200;repeat:false;onTriggered:timelineRuntime.recordEvent("station-osd-settings-saved")}
 Timer{id:videoRecovery;interval:2000;repeat:false;onTriggered:recoverPrimary()} Timer{id:secondaryRecovery;interval:2000;repeat:false;onTriggered:recoverSecondary()}
 Window{id:primaryStreamWindow;visible:connected&&!serviceMode&&primaryDetached;x:w.x+40;y:w.y+40;width:Math.min(960,w.width);height:Math.min(540,w.height);title:"Основний відеопотік · "+devicesModel.activeName;color:"black";onClosing:primaryDetached=false;onVisibleChanged:if(visible)displayRuntime.trackWindow(primaryStreamWindow)
  VideoOutput{id:detachedPrimaryVideoOut;anchors.fill:parent;fillMode:VideoOutput.PreserveAspectFit}
  OsdOverlay{anchors.fill:parent;anchors.margins:12;visible:station.osdEnabled;positions:station.osdElements;enabledElements:station.osdEnabledElements;corner:station.osdPosition;opacityValue:station.osdOpacity;scaleFactor:station.osdScale;telemetry:t;video:vd}
 }
 Window{id:secondaryStreamWindow;visible:connected&&!serviceMode&&secondaryDetached;x:w.x+80;y:w.y+80;width:Math.min(960,w.width);height:Math.min(540,w.height);title:"Додатковий відеопотік · "+devicesModel.activeName;color:"black";onClosing:secondaryDetached=false;onVisibleChanged:if(visible)displayRuntime.trackWindow(secondaryStreamWindow)
  VideoOutput{id:detachedSecondaryVideoOut;anchors.fill:parent;fillMode:VideoOutput.PreserveAspectFit}
  OsdOverlay{anchors.fill:parent;anchors.margins:12;visible:station.osdEnabled;positions:station.osdElements;enabledElements:station.osdEnabledElements;corner:station.osdPosition;opacityValue:station.osdOpacity;scaleFactor:station.osdScale;telemetry:t;video:sd}
 }
 property bool flightBarHidden: false
 Shortcut{sequence:"F10";enabled:pages.currentIndex===1;onActivated:w.flightBarHidden=!w.flightBarHidden}
 Shortcut{sequence:"F9";enabled:connected&&!serviceMode&&!simulation;onActivated:dvrRuntime.toggle()}
 Shortcut{sequence:"F2";enabled:connected&&!serviceMode&&!simulation;onActivated:startSelected()} Shortcut{sequence:"F11";onActivated:w.visibility=w.visibility===Window.FullScreen?Window.Maximized:Window.FullScreen}
 StackLayout{id:pages;objectName:"mainPages";currentIndex:simulation?1:(!connected?0:(serviceMode?2:1));anchors.fill:parent
  HomePanel{onOpenFirmwareFor:function(deviceId){openFirmwareFor(deviceId)};onOpenPreflightFor:function(deviceId){devicesModel.setActive(deviceId);streamWorkspace.autoSelect();preflightPopup.open()};onOpenStationSettings:openStationSettings("");onOpenVehicleSettings:openVehicleSettings("");onOpenService:openService("");onOpenPresets:openVehicleSettings("presets");onOpenRecording:openStationSettings("recording");onOpenController:openStationSettings("controller");onOpenSimulation:simulation=true;onOpenDevices:devices.open();onOpenFirmware:openService("firmware");onOpenUpdate:updatePopup.open();onOpenDiagnostics:openService("diagnostics");onOpenPreflight:preflightPopup.open();onOpenTimeline:openService("timeline");onOpenOsdSettings:openVehicleSettings("osd");onOpenBackup:openStationSettings("backup");onConnectDevice:function(deviceId){connectDevice(deviceId)};onRunNextAction:function(action){if(action==="calibrate-controller"){openStationSettings("controller")}else if(action==="diagnose"){openService("diagnostics")}else if(action==="review-firmware"){openService("firmware")}else if(action==="find-camera"){devices.open()}else if(action==="show-video"||action==="connect-camera"){var activeId="";for(var i=0;i<devicesModel.items.length;i++){if(devicesModel.items[i].active&&devicesModel.items[i].onboardingState==="ready"){activeId=devicesModel.items[i].id;break}}if(activeId===""){activeId=devicesModel.homeItems.length>0?devicesModel.homeItems[0].id:""}if(activeId!=="")connectDevice(activeId);else devices.open()}else{devices.open()}}}
  Item {
   objectName: "flightPage"
   FlightBar {
    id: flightBar
    objectName: "flightBar"
    visible: !w.flightBarHidden
    anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top
    height: visible ? implicitHeight : 0
    simulation: w.simulation
    telemetry: w.simulation ? w.simulatedTelemetry : t
    video: w.simulation ? ({}) : videoRuntime.diagnostics
    cameraName: devicesModel.activeName
    presetName: presetsRuntime.activeName
    pipEnabled: w.pipEnabled
    onOpenVehicle: openVehicleSettings("presets")
    onOpenStreams: streamsPopup.open()
    onOpenDiagnostics: openService("diagnostics")
    onOpenPreflight: preflightPopup.open()
    onOpenMenu: flightMenu.open()
    onHideRequested: w.flightBarHidden = true
    onLeaveFlight: { if (w.simulation) w.simulation = false; else disconnectDevice() }
   }
   Item {
   id: flightArea
   objectName: "flightVideoArea"
   anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom
   anchors.top: flightBar.visible ? flightBar.bottom : parent.top
   clip: true
   Rectangle { anchors.fill: parent; visible: !w.simulation; color: "black" }
   VideoOutput { id:videoOut; objectName:"mainFlightVideoOutput"; anchors.fill:parent; visible:!w.simulation; fillMode:VideoOutput.PreserveAspectFit }
   Item {
    id: simulationWorld
    objectName: "simulationWorld"
    anchors.fill: parent
    visible: w.simulation
    clip: true
    Rectangle { anchors.fill: parent; color: "#4b8db8" }
    Item {
     width: parent.width * 1.7
     height: parent.height * 2
     x: (parent.width - width) / 2
     y: (parent.height - height) / 2 + w.simulatedTelemetry.pitch * 2.4
     rotation: -w.simulatedTelemetry.roll
     Rectangle { anchors.left:parent.left; anchors.right:parent.right; anchors.top:parent.top; height:parent.height/2; color:"#4b8db8" }
     Rectangle { anchors.left:parent.left; anchors.right:parent.right; anchors.bottom:parent.bottom; height:parent.height/2; color:"#526a4a" }
     Rectangle { anchors.left:parent.left; anchors.right:parent.right; anchors.verticalCenter:parent.verticalCenter; height:3; color:"#b9c9b0" }
     Repeater {
      model: 10
      Rectangle {
       required property int index
       width: simulationWorld.width * 0.13
       height: simulationWorld.height * 0.025
       radius: height / 2
       color: "#657b4c"
       x: ((index * simulationWorld.width * 0.21 + w.simulationTick * 7) % (simulationWorld.width * 1.8)) - width
       y: height + simulationWorld.height * (0.62 + (index % 4) * 0.09)
      }
     }
    }
   }
   Rectangle {
    objectName: "flightAlertBanner"
    visible: flightAlerts.active && !w.simulation
    z: 25
    anchors.top: parent.top
    anchors.horizontalCenter: parent.horizontalCenter
    anchors.topMargin: 16
    width: Math.min(parent.width - 32, flightAlertText.implicitWidth + 40)
    height: 48
    radius: 10
    color: flightAlerts.level === "critical" ? "#e6b3263a" : "#e6a8730f"
    border.color: flightAlerts.level === "critical" ? red : amber
    Text { id: flightAlertText; anchors.centerIn: parent; text: flightAlerts.text; color: "white"; font.pixelSize: 18; font.bold: true }
   }
   Rectangle { visible:w.displayFallbackNotice!==""&&!w.simulation; z:20; anchors.top:parent.top; anchors.horizontalCenter:parent.horizontalCenter; anchors.topMargin:16; width:Math.min(parent.width-32,620); height:48; radius:10; color:"#e60b1522"; border.color:amber; Text{anchors.fill:parent;anchors.margins:10;text:w.displayFallbackNotice;color:fg;horizontalAlignment:Text.AlignHCenter;verticalAlignment:Text.AlignVCenter;wrapMode:Text.WordWrap} }
   Column { visible:!w.simulation&&player.playbackState!==MediaPlayer.PlayingState&&!primaryDetached; anchors.centerIn:parent; spacing:8; Text{text:stateUa(videoRuntime.state);color:fg;font.pixelSize:20;font.bold:true} Text{text:videoRuntime.error;color:red;visible:text!==""} Button{text:"Запустити відео";enabled:selectedStreamId!=="";onClicked:startSelected()} }
   Column { visible:!w.simulation&&primaryDetached; anchors.centerIn:parent; spacing:8; Text{text:"Основний потік відкрито в окремому вікні";color:fg;font.pixelSize:18} Button{text:"Повернути до основного екрана";onClicked:primaryDetached=false} }
   Rectangle { visible:!w.simulation&&pipEnabled&&streamWorkspace.state.pipAvailable&&!secondaryDetached; z:5; width:Math.min(parent.width*0.32,480); height:width*9/16; anchors.right:parent.right; anchors.top:parent.top; anchors.margins:12; color:"black"; border.color:secondaryVideoRuntime.state==="playing"?green:amber; border.width:2; radius:8; clip:true; VideoOutput{id:secondaryVideoOut;anchors.fill:parent;fillMode:VideoOutput.PreserveAspectFit} Text{anchors.centerIn:parent;visible:secondaryPlayer.playbackState!==MediaPlayer.PlayingState;text:stateUa(secondaryVideoRuntime.state);color:fg;font.bold:true} }
   OsdOverlay {
    objectName: "flightOsdOverlay"
    anchors.fill:parent; anchors.margins:12
    visible:station.osdEnabled&&(w.simulation||!primaryDetached)
    positions:station.osdElements; enabledElements:station.osdEnabledElements; corner:station.osdPosition
    opacityValue:station.osdOpacity; scaleFactor:station.osdScale
    telemetry:w.simulation?w.simulatedTelemetry:t
    video:w.simulation?w.simulatedVideo:vd
   }
   Rectangle {
    visible: w.simulation
    z: 20
    anchors.top: parent.top
    anchors.horizontalCenter: parent.horizontalCenter
    anchors.topMargin: 14
    width: simulationStatus.implicitWidth + 18
    height: 42
    radius: 10
    color: "#e60b1522"
    border.color: amber
    RowLayout {
     id: simulationStatus
     anchors.centerIn: parent
     spacing: 10
     Text { text:"СИМУЛЯЦІЯ ДРОНА · штучні дані"; color:fg; font.bold:true }
    }
   }
   Button {
    objectName: "flightBarShow"
    visible: w.flightBarHidden
    z: 30
    anchors.right: parent.right; anchors.top: parent.top; anchors.margins: 8
    text: "▾ Панель"
    opacity: hovered ? 1 : 0.55
    onClicked: w.flightBarHidden = false
    HoverHint { text: "Показати панель (F10)." }
   }
   Rectangle {
    objectName: "dvrNotice"
    visible: dvrNotice.text !== "" && !w.simulation
    z: 22
    anchors.bottom: parent.bottom
    anchors.horizontalCenter: parent.horizontalCenter
    anchors.bottomMargin: 24
    width: Math.min(parent.width - 32, dvrNotice.implicitWidth + 32)
    height: dvrNotice.implicitHeight + 20
    radius: 10
    color: "#e60b1522"
    border.color: dvrRuntime.statusLevel === "error" ? red : green
    Text { id: dvrNotice; anchors.centerIn: parent; width: Math.min(implicitWidth, parent.parent.width - 64); text: ""; color: fg; wrapMode: Text.WordWrap; horizontalAlignment: Text.AlignHCenter }
   }
   }
  }
  Item{ColumnLayout{anchors.fill:parent;anchors.margins:20;spacing:10;RowLayout{Layout.fillWidth:true;ColumnLayout{Text{text:"СЕРВІСНИЙ РЕЖИМ";color:fg;font.pixelSize:24;font.bold:true}Text{text:devicesModel.activeName;color:sub}}Item{Layout.fillWidth:true}Button{text:"Налаштувати OSD";onClicked:openOsdSettings()}Button{text:"FPV";enabled:selectedStreamId!=="";onClicked:{serviceMode=false;startSelected()}}}Rectangle{Layout.fillWidth:true;Layout.fillHeight:true;radius:12;color:"#0b1420";border.color:line;ColumnLayout{anchors.fill:parent;anchors.margins:14;Text{text:"Поточний стан системи";color:fg;font.bold:true}Text{text:"Дані польоту: "+stateUa(t.health);color:sub}Text{text:"Зовнішня навігація: "+stateUa(ext.state);color:sub}Text{text:"Мережеве з’єднання: "+stateUa(net.state);color:sub}Item{Layout.fillHeight:true}}}Button{text:"Відключити пристрій";onClicked:disconnectDevice()}}}
 }
 Popup {
  id: flightMenu
  objectName: "flightMenu"
  x: w.width - width - 12
  y: flightBar.visible ? flightBar.height + 6 : 12
  width: Math.min(360, w.width - 24)
  height: Math.min(640, w.height - 24)
  padding: 0
  background: Rectangle { color: "#f20a1420"; border.color: "#71879c"; radius: 12 }
  contentItem: ScrollView {
   id: flightMenuScroll
   clip: true
   contentWidth: availableWidth
   ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
   ColumnLayout {
    objectName: "flightMenuContent"
    width: flightMenuScroll.availableWidth
    spacing: 5
    Text {
     text: w.simulation ? "СИМУЛЯЦІЯ ДРОНА" : (devicesModel.activeName || "МЕНЮ ПОЛЬОТНОГО ЕКРАНА")
     color: fg
     font.pixelSize: 17
     font.bold: true
     Layout.fillWidth: true
     Layout.leftMargin: 14
     Layout.rightMargin: 14
     Layout.topMargin: 14
     Layout.bottomMargin: 4
     elide: Text.ElideRight
    }
    Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: "#627489" }
    Text {
     text: "ВІДЕО ТА OSD"
     color: sub
     font.pixelSize: 12
     font.bold: true
     Layout.fillWidth: true
     Layout.leftMargin: 14
     Layout.topMargin: 5
    }
    Switch {
     text: "Додавати OSD станції поверх відео"
     font.pixelSize: 15
     Layout.fillWidth: true
     Layout.leftMargin: 8
     checked: station.osdEnabled
     onToggled: station.setOSDEnabled(checked)
    }
    Text {
     text: "Відео камери залишається без змін. Якщо її OSD вбудоване в зображення, прибрати його тут неможливо."
     color: sub
     wrapMode: Text.WordWrap
     Layout.fillWidth: true
     Layout.leftMargin: 14
     Layout.rightMargin: 14
     font.pixelSize: 12
    }
    Button {
     text: "Налаштувати розташування OSD"
     objectName: "flightMenuOsdSettings"
     font.pixelSize: 14
     Layout.fillWidth: true
     Layout.preferredHeight: 44
     onClicked: { flightMenu.close(); openOsdSettings() }
     background: Rectangle { radius: 8; color: parent.hovered ? "#40566e" : "#18233342"; border.color: parent.hovered ? "#7897b5" : "#435b72" }
    }
    Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: "#627489" }
    Text {
     text: "ЗАПИС ВІДЕО"
     color: sub
     font.pixelSize: 12
     font.bold: true
     Layout.fillWidth: true
     Layout.leftMargin: 14
     Layout.topMargin: 5
    }
    Button {
     objectName: "flightMenuRecordingSettings"
     text: "Папка для записів"
     font.pixelSize: 14
     Layout.fillWidth: true
     Layout.preferredHeight: 44
     onClicked: { flightMenu.close(); openStationSettings("recording") }
     background: Rectangle { radius: 8; color: parent.hovered ? "#40566e" : "#18233342"; border.color: parent.hovered ? "#7897b5" : "#435b72" }
    }
    Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: "#627489" }
    Text {
     text: "ВІКНА ТА ПОТОКИ"
     color: sub
     font.pixelSize: 12
     font.bold: true
     Layout.fillWidth: true
     Layout.leftMargin: 14
     Layout.topMargin: 5
    }
    Button {
     text: primaryDetached ? "Повернути основне відео" : "Відкрити основне відео окремо"
     font.pixelSize: 14
     Layout.fillWidth: true
     Layout.preferredHeight: 46
     enabled: !w.simulation && (primaryDetached || player.playbackState === MediaPlayer.PlayingState)
     onClicked: { primaryDetached = !primaryDetached; flightMenu.close() }
     background: Rectangle { radius: 8; color: parent.hovered ? "#40566e" : "#18233342"; border.color: parent.hovered ? "#7897b5" : "#435b72" }
    }
    Button {
     text: secondaryDetached ? "Повернути додаткове відео" : "Відкрити додаткове відео окремо"
     font.pixelSize: 14
     Layout.fillWidth: true
     Layout.preferredHeight: 46
     enabled: !w.simulation && (secondaryDetached || secondaryPlayer.playbackState === MediaPlayer.PlayingState)
     onClicked: { secondaryDetached = !secondaryDetached; flightMenu.close() }
     background: Rectangle { radius: 8; color: parent.hovered ? "#40566e" : "#18233342"; border.color: parent.hovered ? "#7897b5" : "#435b72" }
    }
    Button {
     text: "Вибрати відеопотоки"
     enabled: !w.simulation
     font.pixelSize: 14
     Layout.fillWidth: true
     Layout.preferredHeight: 46
     onClicked: { flightMenu.close(); streamsPopup.open() }
     background: Rectangle { radius: 8; color: parent.hovered ? "#40566e" : "#18233342"; border.color: parent.hovered ? "#7897b5" : "#435b72" }
    }
    Text {
     text: "Від’єднання екрана поверне відео сюди."
     color: sub
     wrapMode: Text.WordWrap
     Layout.fillWidth: true
     Layout.leftMargin: 14
     Layout.rightMargin: 14
     font.pixelSize: 12
    }
    Text {
     visible: w.simulation
     text: "Симуляція не підключається до реального обладнання. Інструменти пристроїв і оновлення недоступні."
     color: amber
     wrapMode: Text.WordWrap
     Layout.fillWidth: true
     Layout.leftMargin: 14
     Layout.rightMargin: 14
     font.pixelSize: 12
    }
    Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: "#627489" }
    Text {
     text: "ІНСТРУМЕНТИ СТАНЦІЇ"
     color: sub
     font.pixelSize: 12
     font.bold: true
     Layout.fillWidth: true
     Layout.leftMargin: 14
     Layout.topMargin: 5
    }
    Button {
     text: "Пристрої"; font.pixelSize: 15; Layout.fillWidth: true; Layout.preferredHeight: 46
     objectName: "flightMenuDevices"
     enabled: !w.simulation
     onClicked: { flightMenu.close(); devices.open() }
     background: Rectangle { radius: 8; color: parent.hovered ? "#40566e" : "#18233342"; border.color: parent.hovered ? "#7897b5" : "#435b72" }
    }
    Button {
     text: "Дрони і пресети"; font.pixelSize: 15; Layout.fillWidth: true; Layout.preferredHeight: 46
     objectName: "flightMenuPresets"
     onClicked: { flightMenu.close(); openVehicleSettings("presets") }
     background: Rectangle { radius: 8; color: parent.hovered ? "#40566e" : "#18233342"; border.color: parent.hovered ? "#7897b5" : "#435b72" }
    }
    Button {
     text: "Налаштування станції"; font.pixelSize: 15; Layout.fillWidth: true; Layout.preferredHeight: 46
     objectName: "flightMenuController"
     onClicked: { flightMenu.close(); openStationSettings("") }
     background: Rectangle { radius: 8; color: parent.hovered ? "#40566e" : "#18233342"; border.color: parent.hovered ? "#7897b5" : "#435b72" }
    }
    Button {
     text: "Обслуговування"; font.pixelSize: 15; Layout.fillWidth: true; Layout.preferredHeight: 46
     objectName: "flightMenuService"
     enabled: !w.simulation
     onClicked: { flightMenu.close(); openService("") }
     background: Rectangle { radius: 8; color: parent.hovered ? "#40566e" : "#18233342"; border.color: parent.hovered ? "#7897b5" : "#435b72" }
    }
    Button {
     text: "Перейти до сервісного режиму"; font.pixelSize: 14; Layout.fillWidth: true; Layout.preferredHeight: 46
     enabled: !w.simulation
     onClicked: { flightMenu.close(); enterServiceMode() }
     background: Rectangle { radius: 8; color: parent.hovered ? "#40566e" : "#18233342"; border.color: parent.hovered ? "#7897b5" : "#435b72" }
    }
    Button {
     text: "Hardware E2E"; font.pixelSize: 14; Layout.fillWidth: true; Layout.preferredHeight: 46
     enabled: !w.simulation
     onClicked: { flightMenu.close(); hardwareE2EPopup.open() }
     background: Rectangle { radius: 8; color: parent.hovered ? "#40566e" : "#18233342"; border.color: parent.hovered ? "#7897b5" : "#435b72" }
    }
    Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: "#627489" }
    Button {
     text: "Відключити камеру"
     font.pixelSize: 15
     Layout.fillWidth: true
     Layout.preferredHeight: 48
     enabled: !w.simulation
     onClicked: { flightMenu.close(); disconnectDevice() }
     background: Rectangle { radius: 8; color: parent.hovered ? "#663c2d35" : "#382b1c25"; border.color: "#a56878" }
    }
    Item { Layout.preferredHeight: 8 }
   }
  }
 }
 Popup{
  id:streamsPopup;objectName:"streamsPopup";modal:true;anchors.centerIn:Overlay.overlay;width:Math.min(700,w.width-40);height:Math.min(520,w.height-48);background:Rectangle{color:"#0d1725";border.color:blue;radius:14}
  onAboutToShow:streamsContent.active=true
  contentItem:Loader{
   id:streamsContent;objectName:"streamsContent";anchors.fill:parent;active:false
   sourceComponent:Component{ColumnLayout{
    anchors.fill:parent;anchors.margins:16
    Text{text:"ВІДЕО";color:fg;font.pixelSize:20;font.bold:true}
    Text{text:"Основний: "+(streamWorkspace.state.primaryKind||"--")+" · Додатковий: "+(streamWorkspace.state.secondaryKind||"--");color:sub}
    Switch{text:"PiP";checked:pipEnabled;enabled:streamWorkspace.state.pipAvailable;onToggled:setPip(checked)}
    RowLayout{Layout.fillWidth:true
     Text{text:"Екран";color:sub}
     ComboBox{Layout.fillWidth:true;model:displayRuntime.displays;textRole:"label";currentIndex:w.selectedDisplayIndex;onActivated:function(index){w.selectedDisplayIndex=index}}
     Button{text:"Перемістити основний";enabled:primaryDetached;onClicked:w.displayMoveMessage=displayRuntime.moveWindow(primaryStreamWindow,w.selectedDisplayIndex)?"":"Не вдалося перемістити відеопотік."}
     Button{text:"Перемістити додатковий";enabled:secondaryDetached;onClicked:w.displayMoveMessage=displayRuntime.moveWindow(secondaryStreamWindow,w.selectedDisplayIndex)?"":"Не вдалося перемістити відеопотік."}
    }
    Text{visible:w.displayMoveMessage!=="";text:w.displayMoveMessage;color:red;Layout.fillWidth:true}
    Text{text:"При від’єднанні екрана потік повернеться на основний.";color:sub;font.pixelSize:10}
    ListView{Layout.fillWidth:true;Layout.fillHeight:true;model:devicesModel.activeStreams;delegate:RowLayout{required property var modelData;width:ListView.view.width;Text{text:modelData.name+" · "+modelData.kind;color:fg;Layout.fillWidth:true}Button{text:"Основний";onClicked:{streamWorkspace.selectPrimary(modelData.id);rebuildPlayback()}}Button{text:"Додатковий";enabled:modelData.id!==streamWorkspace.state.primaryId;onClicked:{streamWorkspace.selectSecondary(modelData.id);if(pipEnabled)startSecondary()}}}}
    RowLayout{Button{text:"Поміняти місцями";enabled:streamWorkspace.state.pipAvailable;onClicked:{streamWorkspace.swap();rebuildPlayback()}}Item{Layout.fillWidth:true}Button{text:"Закрити";onClicked:streamsPopup.close()}}
   }}
  }
 }
 function openHub(popup, loader, key){if(!loader.active){loader.active=true}if(loader.item&&key)loader.item.select(key);popup.open()}
 function openStationSettings(key){openHub(stationSettingsPopup,stationSettingsContent,key)}
 function openVehicleSettings(key){openHub(vehicleSettingsPopup,vehicleSettingsContent,key)}
 function openService(key){openHub(servicePopup,serviceContent,key)}
 Popup{
  id:stationSettingsPopup;objectName:"stationSettingsPopup";modal:true;anchors.centerIn:Overlay.overlay
  width:Math.min(1100,w.width-40);height:Math.min(760,w.height-48)
  background:Rectangle{color:"#0d1725";border.color:blue;radius:14}
  onClosed:stationSettingsContent.active=false
  contentItem:Loader{id:stationSettingsContent;objectName:"stationSettingsContent";anchors.fill:parent;active:false
   sourceComponent:Component{TabbedHub{
    anchors.fill:parent;anchors.margins:16
    title:"Налаштування станції"
    tabs:[
     {key:"controller",label:"Пульт",detail:controllerRuntime.summary},
     {key:"recording",label:"Запис відео",detail:dvrRuntime.folder},
     {key:"backup",label:"Резервна копія",detail:"Зберегти або відновити налаштування"}
    ]
    pages:({controller:controllerPage,recording:recordingPage,backup:backupPage})
    onCloseRequested:stationSettingsPopup.close()
    Component{id:controllerPage;ControllerPanel{}}
    Component{id:recordingPage;RecordingPanel{}}
    Component{id:backupPage;BackupPanel{}}
   }}
  }
 }
 Popup{
  id:vehicleSettingsPopup;objectName:"vehicleSettingsPopup";modal:true;anchors.centerIn:Overlay.overlay
  width:Math.min(1240,w.width-40);height:Math.min(900,w.height-48)
  background:Rectangle{color:"#0d1725";border.color:blue;radius:14}
  onClosed:vehicleSettingsContent.active=false
  contentItem:Loader{id:vehicleSettingsContent;objectName:"vehicleSettingsContent";anchors.fill:parent;active:false
   sourceComponent:Component{TabbedHub{
    anchors.fill:parent;anchors.margins:16
    title:"Дрони і пресети"
    tabs:[
     {key:"presets",label:"Пресети дронів",detail:presetsRuntime.activeName?"Активний: "+presetsRuntime.activeName:"Активного пресета немає"},
     {key:"osd",label:"OSD і попередження",detail:"Зберігаються в активному пресеті"}
    ]
    pages:({presets:presetsPage,osd:osdPage})
    onCloseRequested:vehicleSettingsPopup.close()
    onPageLoaded:function(key,item){if(key==="osd")item.editingAllowed=Qt.binding(function(){return w.simulation||t.armed!==true})}
    Component{id:presetsPage;PresetsPanel{}}
    Component{id:osdPage;OsdSettingsPanel{}}
   }}
  }
 }
 Popup{
  id:servicePopup;objectName:"servicePopup";modal:true;anchors.centerIn:Overlay.overlay
  width:Math.min(1180,w.width-40);height:Math.min(800,w.height-48)
  background:Rectangle{color:"#0d1725";border.color:green;radius:14}
  onClosed:serviceContent.active=false
  contentItem:Loader{id:serviceContent;objectName:"serviceContent";anchors.fill:parent;active:false
   sourceComponent:Component{TabbedHub{
    anchors.fill:parent;anchors.margins:16
    title:"Обслуговування"
    tabs:[
     {key:"diagnostics",label:"Діагностика",detail:"Перевірити підключення"},
     {key:"timeline",label:"Події",detail:"Історія важливих змін"},
     {key:"firmware",label:"Прошивка камери",detail:"Оновлення камери"}
    ]
    pages:({diagnostics:diagnosticsPage,timeline:timelinePage,firmware:firmwarePage})
    onCloseRequested:servicePopup.close()
    onPageLoaded:function(key,item){if(key==="firmware")item.activeDevice()}
    Component{id:diagnosticsPage;DiagnosticsPanel{}}
    Component{id:timelinePage;TimelinePanel{}}
    Component{id:firmwarePage;FirmwareCenter{}}
   }}
  }
 }
 Popup{id:recordingPopup;objectName:"recordingPopup";modal:true;anchors.centerIn:Overlay.overlay;width:Math.min(720,w.width-40);height:Math.min(420,w.height-48);background:Rectangle{color:"#0d1725";border.color:blue;radius:14}onAboutToShow:recordingContent.active=true;contentItem:Loader{id:recordingContent;objectName:"recordingContent";anchors.fill:parent;active:false;sourceComponent:Component{RecordingPanel{anchors.fill:parent;anchors.margins:16;onCloseRequested:recordingPopup.close()}}}}
 Popup{id:presetsPopup;objectName:"presetsPopup";modal:true;anchors.centerIn:Overlay.overlay;width:Math.min(820,w.width-40);height:Math.min(620,w.height-48);background:Rectangle{color:"#0d1725";border.color:blue;radius:14}onAboutToShow:presetsContent.active=true;contentItem:Loader{id:presetsContent;objectName:"presetsContent";anchors.fill:parent;active:false;sourceComponent:Component{PresetsPanel{anchors.fill:parent;anchors.margins:16;onCloseRequested:presetsPopup.close()}}}}
 Popup{id:controllerPopup;objectName:"controllerPopup";modal:true;anchors.centerIn:Overlay.overlay;width:Math.min(720,w.width-40);height:Math.min(560,w.height-48);background:Rectangle{color:"#0d1725";border.color:blue;radius:14}onAboutToShow:controllerContent.active=true;onClosed:controllerContent.active=false;contentItem:Loader{id:controllerContent;objectName:"controllerContent";anchors.fill:parent;active:false;sourceComponent:Component{ControllerPanel{anchors.fill:parent;anchors.margins:16;onCloseRequested:controllerPopup.close()}}}}
 Popup{id:timelinePopup;objectName:"timelinePopup";modal:true;anchors.centerIn:Overlay.overlay;width:Math.min(760,w.width-40);height:Math.min(560,w.height-48);background:Rectangle{color:"#0d1725";border.color:blue;radius:14}onAboutToShow:timelineContent.active=true;contentItem:Loader{id:timelineContent;objectName:"timelineContent";anchors.fill:parent;active:false;sourceComponent:Component{TimelinePanel{anchors.fill:parent;anchors.margins:16;onCloseRequested:timelinePopup.close()}}}}
 Popup{id:backupPopup;objectName:"backupPopup";modal:true;anchors.centerIn:Overlay.overlay;width:Math.min(700,w.width-40);height:Math.min(600,w.height-48);background:Rectangle{color:"#0d1725";border.color:blue;radius:14}onAboutToShow:backupContent.active=true;onClosed:if(backupContent.item)backupContent.item.clearSensitiveFields();contentItem:Loader{id:backupContent;objectName:"backupContent";anchors.fill:parent;active:false;sourceComponent:Component{BackupPanel{anchors.fill:parent;anchors.margins:16;onCloseRequested:backupPopup.close()}}}}
 Popup{id:osdSettingsPopup;objectName:"osdSettingsPopup";modal:true;anchors.centerIn:Overlay.overlay;width:Math.min(1180,w.width-40);height:Math.min(900,w.height-48);background:Rectangle{color:"#f00d1725";border.color:blue;radius:14}onAboutToShow:osdSettingsLoader.active=true;contentItem:Loader{id:osdSettingsLoader;objectName:"osdSettingsLoader";anchors.fill:parent;active:false;sourceComponent:Component{OsdSettingsPanel{anchors.fill:parent;anchors.margins:16;onCloseRequested:osdSettingsPopup.close()}}}}
 Popup{id:preflightPopup;objectName:"preflightPopup";modal:true;anchors.centerIn:Overlay.overlay;width:Math.min(860,w.width-40);height:Math.min(640,w.height-48);background:Rectangle{color:"#f00d1725";border.color:amber;radius:14}onAboutToShow:{preflightContent.active=true;controllerRuntime.observe()}contentItem:Loader{id:preflightContent;objectName:"preflightContent";anchors.fill:parent;active:false;sourceComponent:Component{PreflightPanel{anchors.fill:parent;anchors.margins:16;cameraName:devicesModel.activeName;video:vd;telemetry:t;network:net;navigation:ext;nextAction:homeDashboard.nextAction;osdEnabled:station.osdEnabled;controllerHealth:controllerRuntime.health;controllerDetail:controllerRuntime.summary;onCloseRequested:preflightPopup.close();onOpenOsdSettings:function(){preflightPopup.close();openOsdSettings()}onOpenSimulation:function(){preflightPopup.close();simulation=true}onOpenDiagnostics:function(){preflightPopup.close();diagnostics.open()}}}}}
 Popup{id:diagnostics;objectName:"diagnostics";modal:true;anchors.centerIn:Overlay.overlay;width:Math.min(860,w.width-40);height:Math.min(640,w.height-48);background:Rectangle{color:"#0d1725";border.color:green;radius:14}onAboutToShow:diagnosticsContent.active=true;contentItem:Loader{id:diagnosticsContent;objectName:"diagnosticsContent";anchors.fill:parent;active:false;sourceComponent:Component{DiagnosticsPanel{anchors.fill:parent;anchors.margins:16;onCloseRequested:diagnostics.close()}}}}
 Popup{id:firmwarePopup;objectName:"firmwarePopup";modal:true;anchors.centerIn:Overlay.overlay;width:Math.min(900,w.width-40);height:Math.min(700,w.height-48);onAboutToShow:firmwarePanelLoader.active=true;onOpened:if(firmwarePanelLoader.item)firmwarePanelLoader.item.activeDevice();background:Rectangle{color:"#0d1725";border.color:amber;radius:14}contentItem:Loader{id:firmwarePanelLoader;objectName:"firmwarePanelLoader";anchors.fill:parent;active:false;sourceComponent:Component{FirmwareCenter{anchors.fill:parent;anchors.margins:18;onCloseRequested:firmwarePopup.close()}}}}
 Popup{id:hardwareE2EPopup;objectName:"hardwareE2EPopup";modal:true;anchors.centerIn:Overlay.overlay;width:Math.min(760,w.width-40);height:Math.min(600,w.height-48);onOpened:hardwareE2ERuntime.reset();onAboutToShow:hardwareE2EContent.active=true;background:Rectangle{color:"#0d1725";border.color:amber;radius:14}contentItem:Loader{id:hardwareE2EContent;objectName:"hardwareE2EContent";anchors.fill:parent;active:false;sourceComponent:Component{HardwareE2EPanel{anchors.fill:parent;anchors.margins:18;onCloseRequested:hardwareE2EPopup.close()}}}}
 Popup{id:updatePopup;objectName:"updatePopup";modal:true;anchors.centerIn:Overlay.overlay;width:Math.min(740,w.width-40);height:Math.min(580,w.height-48);background:Rectangle{color:"#0d1725";border.color:green;radius:14}onAboutToShow:updateContent.active=true;contentItem:Loader{id:updateContent;objectName:"updateContent";anchors.fill:parent;active:false;sourceComponent:Component{UpdatePanel{anchors.fill:parent;anchors.margins:18;onCloseRequested:updatePopup.close()}}}}
 Popup{id:devices;objectName:"devices";modal:true;anchors.centerIn:Overlay.overlay;width:Math.min(960,w.width-40);height:Math.min(660,w.height-60);background:Rectangle{color:"#0d1725";border.color:blue;radius:14}onAboutToShow:devicesContent.active=true;contentItem:Loader{id:devicesContent;objectName:"devicesContent";anchors.fill:parent;active:false;sourceComponent:Component{DevicesPanel{anchors.fill:parent;anchors.margins:18;onCloseRequested:devices.close();onActivateDevice:function(deviceId){devices.close();connectDevice(deviceId)}}}}}
 Popup{id:backupFailurePopup;modal:true;anchors.centerIn:Overlay.overlay;width:Math.min(500,w.width-40);padding:18;background:Rectangle{color:"#0d1725";border.color:red;radius:12}contentItem:ColumnLayout{spacing:12;Text{id:backupFailureText;color:fg;wrapMode:Text.WordWrap;Layout.fillWidth:true}Button{text:"Зрозуміло";onClicked:backupFailurePopup.close()}}}
}
