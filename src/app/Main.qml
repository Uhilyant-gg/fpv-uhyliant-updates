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
 property var simulatedTelemetry: ({connected:true, provider:"MAVLink", armed:false, flightMode:"STABILIZE", batteryVoltage:15.8, batteryRemaining:82, gpsFix:3, satellites:12, altitude:124 + Math.round(4 * Math.sin(simulationTick / 5)), groundSpeed:12.4 + Math.sin(simulationTick / 4), heading:(348 + simulationTick) % 360})
 Timer { interval: 1000; repeat: true; running: w.simulation; onTriggered: w.simulationTick++ }
 property bool connected:devicesModel.activeName!=="";property bool serviceMode:false;property bool primaryDetached:false;property bool secondaryDetached:false;property int selectedDisplayIndex:0;property string displayMoveMessage:"";property string displayFallbackNotice:"";property string selectedStreamId:streamWorkspace.state.primaryId||"";property string secondaryStreamId:streamWorkspace.state.secondaryId||"";readonly property bool pipEnabled:videoWorkspaceRuntime.pipEnabled;property var t:telemetryRuntime.telemetry;property var vd:videoRuntime.diagnostics;property var sd:secondaryVideoRuntime.diagnostics;property var ext:linkDiagnostics.externalNavigation;property var net:linkDiagnostics.network;property int videoRecoveryCount:0;property int secondaryRecoveryCount:0
 function val(v,suffix,digits){return v===undefined||v===null?"--":Number(v).toFixed(digits===undefined?0:digits)+(suffix||"")}
 function stateUa(value){if(value===undefined||value===null||value==="")return "недоступно";var states={"idle":"очікування","stopped":"зупинено","checking":"перевірка","ready":"готово","playing":"відтворення","reconnecting":"перепідключення","stalled":"зупинка потоку","error":"помилка","blocked":"заблоковано","executing":"виконання","installing":"встановлення","reboot-pending":"очікується перезапуск","verified":"перевірено","hardware-validation-pending":"очікується перевірка на обладнанні","applied-pending-verification":"застосовано, очікується перевірка","unavailable":"недоступно","unknown":"ще не визначено","connected":"підключено","disconnected":"відключено","stale":"дані давно не оновлювалися","degraded":"працює нестабільно","attention":"потребує уваги","traffic-no-heartbeat":"є передавання без підтвердження зв’язку","ok":"справно"};return states[value]||"потрібна перевірка"}
 function stopPrimary(){videoRecovery.stop();player.stop();player.source="";videoRuntime.stop();videoRecoveryCount=0}
 function stopSecondary(){secondaryRecovery.stop();secondaryPlayer.stop();secondaryPlayer.source="";secondaryVideoRuntime.stop();secondaryRecoveryCount=0}
 function setPip(enabled){var requested=enabled&&streamWorkspace.state.pipAvailable;videoWorkspaceRuntime.setPipEnabled(requested);if(!requested)stopSecondary();else startSecondary()}
 function connectDevice(id){serviceMode=false;stopPrimary();setPip(false);devicesModel.setActive(id);timelineRuntime.recordEvent("camera-selected");streamWorkspace.autoSelect();if(devicesModel.activeName!==""&&streamWorkspace.state.primaryId!=="")startSelected()}
 function disconnectDevice(){serviceMode=false;primaryDetached=false;secondaryDetached=false;stopPrimary();setPip(false);videoWorkspaceRuntime.stopAll();devicesModel.clearActive();streamWorkspace.autoSelect()}
 function enterServiceMode(){serviceMode=true;stopPrimary();setPip(false)}
 function startSelected(){stopPrimary();if(connected&&selectedStreamId!==""&&videoWorkspaceRuntime.preparePrimary(selectedStreamId)){player.source=videoRuntime.url;player.play()}if(pipEnabled)startSecondary()}
 function startSecondary(){stopSecondary();if(pipEnabled&&connected&&secondaryStreamId!==""&&videoWorkspaceRuntime.prepareSecondary(secondaryStreamId)){secondaryPlayer.source=secondaryVideoRuntime.url;secondaryPlayer.play()}}
 function rebuildPlayback(){var wasPlaying=player.playbackState===MediaPlayer.PlayingState||videoRuntime.streamId!=="";var keepPip=pipEnabled&&streamWorkspace.state.pipAvailable;stopPrimary();stopSecondary();if(wasPlaying)startSelected();if(keepPip&&streamWorkspace.state.pipAvailable){videoWorkspaceRuntime.setPipEnabled(true);startSecondary()}}
 function recoverPrimary(){if(!connected||videoRuntime.url==="")return;if(videoRecoveryCount>=5){videoRuntime.markStalled("Не вдалося автоматично відновити основний відеопотік.");return}videoRecoveryCount++;player.stop();if(videoRuntime.reconnect()){player.source="";player.source=videoRuntime.url;player.play()}else videoRecovery.start()}
 function recoverSecondary(){if(!pipEnabled||secondaryVideoRuntime.url==="")return;if(secondaryRecoveryCount>=5){secondaryVideoRuntime.markStalled("Не вдалося автоматично відновити додатковий відеопотік.");return}secondaryRecoveryCount++;secondaryPlayer.stop();if(secondaryVideoRuntime.reconnect()){secondaryPlayer.source="";secondaryPlayer.source=secondaryVideoRuntime.url;secondaryPlayer.play()}else secondaryRecovery.start()}
 onPipEnabledChanged:if(!pipEnabled){secondaryDetached=false;secondaryRecovery.stop();secondaryPlayer.stop();secondaryPlayer.source="";secondaryRecoveryCount=0}
 MediaPlayer{id:player;videoOutput:primaryDetached?detachedPrimaryVideoOut:videoOut;onPlayingChanged:{timelineRuntime.observe("primary-video",playing?"playing":"stopped");if(playing){videoRecovery.stop();videoRecoveryCount=0;videoRuntime.markPlaying()}else if(videoRuntime.state==="playing"){videoRuntime.markStalled("Основний відеопотік несподівано зупинився.");videoRecovery.restart()}}onErrorOccurred:function(error,errorString){videoRuntime.playbackError(errorString);if(videoRuntime.streamId!=="")videoRecovery.restart()}}
 MediaPlayer{id:secondaryPlayer;videoOutput:secondaryDetached?detachedSecondaryVideoOut:secondaryVideoOut;onPlayingChanged:{timelineRuntime.observe("secondary-video",playing?"playing":"stopped");if(playing){secondaryRecovery.stop();secondaryRecoveryCount=0;secondaryVideoRuntime.markPlaying()}else if(pipEnabled&&secondaryVideoRuntime.state==="playing"){secondaryVideoRuntime.markStalled("Додатковий відеопотік несподівано зупинився.");secondaryRecovery.restart()}}onErrorOccurred:function(error,errorString){secondaryVideoRuntime.playbackError(errorString);if(pipEnabled&&secondaryVideoRuntime.streamId!=="")secondaryRecovery.restart()}}
 Connections{target:telemetryRuntime;function onChanged(){timelineRuntime.observe("telemetry",t.connected===true?"connected":(t.connected===false?"lost":"unknown"))}}
 Connections{target:devicesModel;function onDiscoveryChanged(){timelineRuntime.observe("discovery",devicesModel.scanning?"scanning":(devicesModel.discoveryStage==="Готово"?"completed":(devicesModel.discoveryStage==="Скасовано"?"cancelled":(devicesModel.discoveryStage==="Помилка"?"failed":"unknown"))))}}
 Connections{target:devicesModel;function onDeviceAdded(){timelineRuntime.recordEvent("device-added")}function onDeviceUpdated(){timelineRuntime.recordEvent("device-updated")}function onDeviceRemoved(){timelineRuntime.recordEvent("device-removed")}function onDeviceListRestored(){timelineRuntime.recordEvent("device-list-restored")}}
 Connections{target:station;function onOsdSettingsSaved(){osdSettingsTimelineTimer.restart()}}
 Connections{target:updater;function onChanged(){timelineRuntime.observe("update",updater.updateState)}}
 Connections{target:firmwareUpdateSession;function onChanged(){timelineRuntime.observe("camera-firmware",firmwareUpdateSession.result.state)}}
 Connections{target:linkDiagnostics;function onChanged(){timelineRuntime.observe("network",net.state==="ready"?"ready":(net.state==="degraded"?"degraded":(net.state==="error"||net.state==="stale"?"lost":"unknown")));timelineRuntime.observe("navigation",ext.state==="ready"?"ready":(ext.state==="degraded"?"degraded":(ext.state==="error"||ext.state==="stale"?"lost":"unknown")))}}
 Connections{target:displayRuntime;function onChanged(){if(w.selectedDisplayIndex>=displayRuntime.displays.length)w.selectedDisplayIndex=0}function onWindowReturnedToWorkspace(window){if(window===primaryStreamWindow||window===secondaryStreamWindow){if(window===primaryStreamWindow)w.primaryDetached=false;else w.secondaryDetached=false;w.displayFallbackNotice="Екран від’єднано. Відеопотік повернуто до основного робочого простору.";displayFallbackTimer.restart()}}}
 Timer{id:displayFallbackTimer;interval:6000;repeat:false;onTriggered:w.displayFallbackNotice=""}
 Timer{id:osdSettingsTimelineTimer;interval:1200;repeat:false;onTriggered:timelineRuntime.recordEvent("station-osd-settings-saved")}
 Timer{id:videoRecovery;interval:2000;repeat:false;onTriggered:recoverPrimary()} Timer{id:secondaryRecovery;interval:2000;repeat:false;onTriggered:recoverSecondary()}
 Window{id:primaryStreamWindow;visible:connected&&!serviceMode&&primaryDetached;x:w.x+40;y:w.y+40;width:Math.min(960,w.width);height:Math.min(540,w.height);title:"Основний відеопотік · "+devicesModel.activeName;color:"black";onClosing:primaryDetached=false;onVisibleChanged:if(visible)displayRuntime.trackWindow(primaryStreamWindow)
  VideoOutput{id:detachedPrimaryVideoOut;anchors.fill:parent;fillMode:VideoOutput.PreserveAspectFit}
  OsdOverlay{anchors.fill:parent;anchors.margins:12;visible:station.osdEnabled;positions:station.osdElements;corner:station.osdPosition;opacityValue:station.osdOpacity;scaleFactor:station.osdScale;telemetry:t;video:vd}
 }
 Window{id:secondaryStreamWindow;visible:connected&&!serviceMode&&secondaryDetached;x:w.x+80;y:w.y+80;width:Math.min(960,w.width);height:Math.min(540,w.height);title:"Додатковий відеопотік · "+devicesModel.activeName;color:"black";onClosing:secondaryDetached=false;onVisibleChanged:if(visible)displayRuntime.trackWindow(secondaryStreamWindow)
  VideoOutput{id:detachedSecondaryVideoOut;anchors.fill:parent;fillMode:VideoOutput.PreserveAspectFit}
  OsdOverlay{anchors.fill:parent;anchors.margins:12;visible:station.osdEnabled;positions:station.osdElements;corner:station.osdPosition;opacityValue:station.osdOpacity;scaleFactor:station.osdScale;telemetry:t;video:sd}
 }
 Shortcut{sequence:"F2";enabled:connected&&!serviceMode&&!simulation;onActivated:startSelected()} Shortcut{sequence:"F11";onActivated:w.visibility=w.visibility===Window.FullScreen?Window.Maximized:Window.FullScreen}
 StackLayout{id:pages;objectName:"mainPages";currentIndex:simulation?3:(!connected?0:(serviceMode?2:1));anchors.fill:parent
  HomePanel{onOpenSimulation:simulation=true;onOpenDevices:devices.open();onOpenFirmware:firmwarePopup.open();onOpenUpdate:updatePopup.open();onOpenDiagnostics:diagnostics.open();onOpenPreflight:preflightPopup.open();onOpenTimeline:timelinePopup.open();onOpenOsdSettings:osdSettingsPopup.open();onOpenBackup:backupPopup.open();onConnectDevice:function(deviceId){connectDevice(deviceId)};onRunNextAction:function(action){if(action==="diagnose"){diagnostics.open()}else if(action==="show-video"||action==="connect-camera"){var activeId="";for(var i=0;i<devicesModel.items.length;i++){if(devicesModel.items[i].active){activeId=devicesModel.items[i].id;break}}if(activeId===""){activeId=devicesModel.count>0?devicesModel.items[0].id:""}if(activeId!=="")connectDevice(activeId);else devices.open()}else{devices.open()}}}
  Item{Rectangle{anchors.fill:parent;color:"black"}VideoOutput{id:videoOut;anchors.fill:parent;fillMode:VideoOutput.PreserveAspectFit}Rectangle{visible:w.displayFallbackNotice!=="";z:20;anchors.top:parent.top;anchors.horizontalCenter:parent.horizontalCenter;anchors.topMargin:16;width:Math.min(parent.width-32,620);height:48;radius:10;color:"#e60b1522";border.color:amber;Text{anchors.fill:parent;anchors.margins:10;text:w.displayFallbackNotice;color:fg;horizontalAlignment:Text.AlignHCenter;verticalAlignment:Text.AlignVCenter;wrapMode:Text.WordWrap}}Column{visible:player.playbackState!==MediaPlayer.PlayingState&&!primaryDetached;anchors.centerIn:parent;spacing:8;Text{text:stateUa(videoRuntime.state);color:fg;font.pixelSize:20;font.bold:true}Text{text:videoRuntime.error;color:red;visible:text!==""}Button{text:"Запустити відео";enabled:selectedStreamId!=="";onClicked:startSelected()}}Column{visible:primaryDetached;anchors.centerIn:parent;spacing:8;Text{text:"Основний потік відкрито в окремому вікні";color:fg;font.pixelSize:18}Button{text:"Повернути до основного екрана";onClicked:primaryDetached=false}}
   Rectangle{visible:pipEnabled&&streamWorkspace.state.pipAvailable&&!secondaryDetached;z:5;width:Math.min(parent.width*0.32,480);height:width*9/16;anchors.right:parent.right;anchors.top:parent.top;anchors.margins:12;color:"black";border.color:secondaryVideoRuntime.state==="playing"?green:amber;border.width:2;radius:8;clip:true;VideoOutput{id:secondaryVideoOut;anchors.fill:parent;fillMode:VideoOutput.PreserveAspectFit}Text{anchors.centerIn:parent;visible:secondaryPlayer.playbackState!==MediaPlayer.PlayingState;text:stateUa(secondaryVideoRuntime.state);color:fg;font.bold:true}}
   OsdOverlay{anchors.fill:parent;anchors.margins:12;visible:station.osdEnabled&&!primaryDetached;positions:station.osdElements;corner:station.osdPosition;opacityValue:station.osdOpacity;scaleFactor:station.osdScale;telemetry:t;video:vd}
   Button{anchors.right:parent.right;anchors.bottom:parent.bottom;anchors.margins:10;text:"☰";onClicked:flightMenu.open()}
  }
  Item{ColumnLayout{anchors.fill:parent;anchors.margins:20;spacing:10;RowLayout{Layout.fillWidth:true;ColumnLayout{Text{text:"СЕРВІСНИЙ РЕЖИМ";color:fg;font.pixelSize:24;font.bold:true}Text{text:devicesModel.activeName;color:sub}}Item{Layout.fillWidth:true}Button{text:"Налаштувати OSD";onClicked:osdSettingsPopup.open()}Button{text:"FPV";enabled:selectedStreamId!=="";onClicked:{serviceMode=false;startSelected()}}}Rectangle{Layout.fillWidth:true;Layout.fillHeight:true;radius:12;color:"#0b1420";border.color:line;ColumnLayout{anchors.fill:parent;anchors.margins:14;Text{text:"Поточний стан системи";color:fg;font.bold:true}Text{text:"Дані польоту: "+stateUa(t.health);color:sub}Text{text:"Зовнішня навігація: "+stateUa(ext.state);color:sub}Text{text:"Мережеве з’єднання: "+stateUa(net.state);color:sub}Item{Layout.fillHeight:true}}}Button{text:"Відключити пристрій";onClicked:disconnectDevice()}}}
  Item {
   Rectangle { id: simulatedScene; anchors.fill: parent; clip:true; gradient: Gradient { GradientStop { position:0; color:"#294e71" } GradientStop { position:0.54; color:"#c2c6af" } GradientStop { position:0.55; color:"#526a4a" } GradientStop { position:1; color:"#172b23" } }
    Repeater { model: 8
     Rectangle { required property int index; width: simulatedScene.width * 0.18; height: simulatedScene.height * 0.045; radius: height / 2; color: "#48613d"; x: ((index * simulatedScene.width * 0.23 + w.simulationTick * 9) % (simulatedScene.width * 1.8)) - width; y: simulatedScene.height * (0.62 + (index % 4) * 0.095) }
    }
   }
   OsdOverlay { anchors.fill:parent; anchors.margins:12; visible:station.osdEnabled; positions:station.osdElements; corner:station.osdPosition; opacityValue:station.osdOpacity; scaleFactor:station.osdScale; telemetry:w.simulatedTelemetry; video:({streamId:"simulation",state:"playing"}) }
   Rectangle { anchors.horizontalCenter:parent.horizontalCenter; anchors.bottom:parent.bottom; anchors.bottomMargin:18; width:simulationControls.implicitWidth+24; height:simulationControls.implicitHeight+20; radius:10; color:"#e60b1522"; border.color:amber
    RowLayout { id:simulationControls; anchors.centerIn:parent; spacing:12
     Text { text:"СИМУЛЯЦІЯ · відео та дані MAVLink не справжні"; color:fg; font.bold:true }
     Button { objectName:"openSimulationOsd"; text:"Налаштувати OSD"; onClicked:osdSettingsPopup.open() }
     Button { objectName:"exitSimulation"; text:"Вийти"; onClicked:simulation=false }
    }
   }
  }
 }
 Popup {
  id: flightMenu
  x: w.width - width - 12
  y: 12
  width: Math.min(360, w.width - 24)
  height: Math.min(640, w.height - 24)
  padding: 0
  background: Rectangle { color: "#f20a1420"; border.color: "#71879c"; radius: 12 }
  contentItem: ScrollView {
   clip: true
   ColumnLayout {
    width: parent.width
    spacing: 5
    Text {
     text: devicesModel.activeName || "МЕНЮ ПОЛЬОТНОГО ЕКРАНА"
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
    Button {
     text: "Перевірити підготовку"
     font.pixelSize: 15
     Layout.fillWidth: true
     Layout.preferredHeight: 48
     onClicked: { flightMenu.close(); preflightPopup.open() }
     background: Rectangle { radius: 8; color: parent.hovered ? "#40566e" : "#18233342"; border.color: parent.hovered ? "#7897b5" : "#435b72" }
    }
    Switch {
     text: "Показувати OSD станції"
     font.pixelSize: 15
     Layout.fillWidth: true
     Layout.leftMargin: 8
     checked: station.osdEnabled
     onToggled: station.setOSDEnabled(checked)
    }
    Text {
     text: "OSD камери не змінюється."
     color: sub
     wrapMode: Text.WordWrap
     Layout.fillWidth: true
     Layout.leftMargin: 14
     Layout.rightMargin: 14
     font.pixelSize: 12
    }
    Button {
     text: "Налаштувати розташування OSD"
     font.pixelSize: 14
     Layout.fillWidth: true
     Layout.preferredHeight: 44
     onClicked: { flightMenu.close(); osdSettingsPopup.open() }
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
     enabled: primaryDetached || player.playbackState === MediaPlayer.PlayingState
     onClicked: { primaryDetached = !primaryDetached; flightMenu.close() }
     background: Rectangle { radius: 8; color: parent.hovered ? "#40566e" : "#18233342"; border.color: parent.hovered ? "#7897b5" : "#435b72" }
    }
    Button {
     text: secondaryDetached ? "Повернути додаткове відео" : "Відкрити додаткове відео окремо"
     font.pixelSize: 14
     Layout.fillWidth: true
     Layout.preferredHeight: 46
     enabled: secondaryDetached || secondaryPlayer.playbackState === MediaPlayer.PlayingState
     onClicked: { secondaryDetached = !secondaryDetached; flightMenu.close() }
     background: Rectangle { radius: 8; color: parent.hovered ? "#40566e" : "#18233342"; border.color: parent.hovered ? "#7897b5" : "#435b72" }
    }
    Button {
     text: "Вибрати відеопотоки"
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
     text: "Події сесії"; font.pixelSize: 15; Layout.fillWidth: true; Layout.preferredHeight: 46
     onClicked: { flightMenu.close(); timelinePopup.open() }
     background: Rectangle { radius: 8; color: parent.hovered ? "#40566e" : "#18233342"; border.color: parent.hovered ? "#7897b5" : "#435b72" }
    }
    Button {
     text: "Пристрої"; font.pixelSize: 15; Layout.fillWidth: true; Layout.preferredHeight: 46
     onClicked: { flightMenu.close(); devices.open() }
     background: Rectangle { radius: 8; color: parent.hovered ? "#40566e" : "#18233342"; border.color: parent.hovered ? "#7897b5" : "#435b72" }
    }
    Button {
     text: "Діагностика"; font.pixelSize: 15; Layout.fillWidth: true; Layout.preferredHeight: 46
     onClicked: { flightMenu.close(); diagnostics.open() }
     background: Rectangle { radius: 8; color: parent.hovered ? "#40566e" : "#18233342"; border.color: parent.hovered ? "#7897b5" : "#435b72" }
    }
    Button {
     text: "Прошивка камери"; font.pixelSize: 15; Layout.fillWidth: true; Layout.preferredHeight: 46
     onClicked: { flightMenu.close(); firmwarePopup.open() }
     background: Rectangle { radius: 8; color: parent.hovered ? "#40566e" : "#18233342"; border.color: parent.hovered ? "#7897b5" : "#435b72" }
    }
    Button {
     text: "Оновлення програми"; font.pixelSize: 15; Layout.fillWidth: true; Layout.preferredHeight: 46
     onClicked: { flightMenu.close(); updatePopup.open() }
     background: Rectangle { radius: 8; color: parent.hovered ? "#40566e" : "#18233342"; border.color: parent.hovered ? "#7897b5" : "#435b72" }
    }
    Button {
     text: "Перейти до сервісного режиму"; font.pixelSize: 14; Layout.fillWidth: true; Layout.preferredHeight: 46
     onClicked: { flightMenu.close(); enterServiceMode() }
     background: Rectangle { radius: 8; color: parent.hovered ? "#40566e" : "#18233342"; border.color: parent.hovered ? "#7897b5" : "#435b72" }
    }
    Button {
     text: "Hardware E2E"; font.pixelSize: 14; Layout.fillWidth: true; Layout.preferredHeight: 46
     onClicked: { flightMenu.close(); hardwareE2EPopup.open() }
     background: Rectangle { radius: 8; color: parent.hovered ? "#40566e" : "#18233342"; border.color: parent.hovered ? "#7897b5" : "#435b72" }
    }
    Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: "#627489" }
    Button {
     text: "Відключити камеру"
     font.pixelSize: 15
     Layout.fillWidth: true
     Layout.preferredHeight: 48
     onClicked: { flightMenu.close(); disconnectDevice() }
     background: Rectangle { radius: 8; color: parent.hovered ? "#663c2d35" : "#382b1c25"; border.color: "#a56878" }
    }
    Item { Layout.preferredHeight: 8 }
   }
  }
 }
 Popup{id:streamsPopup;modal:true;anchors.centerIn:Overlay.overlay;width:Math.min(700,w.width-40);height:Math.min(520,w.height-48);background:Rectangle{color:"#0d1725";border.color:blue;radius:14}contentItem:ColumnLayout{anchors.fill:parent;anchors.margins:16;Text{text:"ВІДЕО";color:fg;font.pixelSize:20;font.bold:true}Text{text:"Основний: "+(streamWorkspace.state.primaryKind||"--")+" · Додатковий: "+(streamWorkspace.state.secondaryKind||"--");color:sub}Switch{text:"PiP";checked:pipEnabled;enabled:streamWorkspace.state.pipAvailable;onToggled:setPip(checked)}RowLayout{Layout.fillWidth:true;Text{text:"Екран";color:sub}ComboBox{Layout.fillWidth:true;model:displayRuntime.displays;textRole:"label";currentIndex:w.selectedDisplayIndex;onActivated:function(index){w.selectedDisplayIndex=index}}Button{text:"Перемістити основний";enabled:primaryDetached;onClicked:w.displayMoveMessage=displayRuntime.moveWindow(primaryStreamWindow,w.selectedDisplayIndex)?"":"Не вдалося перемістити відеопотік."}Button{text:"Перемістити додатковий";enabled:secondaryDetached;onClicked:w.displayMoveMessage=displayRuntime.moveWindow(secondaryStreamWindow,w.selectedDisplayIndex)?"":"Не вдалося перемістити відеопотік."}}Text{visible:w.displayMoveMessage!=="";text:w.displayMoveMessage;color:red;Layout.fillWidth:true}Text{text:"При від’єднанні екрана потік повернеться на основний.";color:sub;font.pixelSize:10}ListView{Layout.fillWidth:true;Layout.fillHeight:true;model:devicesModel.activeStreams;delegate:RowLayout{required property var modelData;width:ListView.view.width;Text{text:modelData.name+" · "+modelData.kind;color:fg;Layout.fillWidth:true}Button{text:"Основний";onClicked:{streamWorkspace.selectPrimary(modelData.id);rebuildPlayback()}}Button{text:"Додатковий";enabled:modelData.id!==streamWorkspace.state.primaryId;onClicked:{streamWorkspace.selectSecondary(modelData.id);if(pipEnabled)startSecondary()}}}}RowLayout{Button{text:"Поміняти місцями";enabled:streamWorkspace.state.pipAvailable;onClicked:{streamWorkspace.swap();rebuildPlayback()}}Item{Layout.fillWidth:true}Button{text:"Закрити";onClicked:streamsPopup.close()}}}}
 Popup{id:timelinePopup;modal:true;anchors.centerIn:Overlay.overlay;width:Math.min(760,w.width-40);height:Math.min(560,w.height-48);background:Rectangle{color:"#0d1725";border.color:blue;radius:14}contentItem:TimelinePanel{anchors.fill:parent;anchors.margins:16;onCloseRequested:timelinePopup.close()}}
 Popup{id:backupPopup;modal:true;anchors.centerIn:Overlay.overlay;width:Math.min(700,w.width-40);height:Math.min(600,w.height-48);background:Rectangle{color:"#0d1725";border.color:blue;radius:14}contentItem:BackupPanel{id:backupPanel;anchors.fill:parent;anchors.margins:16;onCloseRequested:backupPopup.close()}onClosed:backupPanel.clearSensitiveFields()}
 Popup{id:osdSettingsPopup;objectName:"osdSettingsPopup";modal:true;anchors.centerIn:Overlay.overlay;width:Math.min(1000,w.width-40);height:Math.min(680,w.height-48);background:Rectangle{color:"#f00d1725";border.color:blue;radius:14}contentItem:OsdSettingsPanel{anchors.fill:parent;anchors.margins:16;onCloseRequested:osdSettingsPopup.close()}}
 Popup{id:preflightPopup;modal:true;anchors.centerIn:Overlay.overlay;width:Math.min(860,w.width-40);height:Math.min(640,w.height-48);background:Rectangle{color:"#f00d1725";border.color:amber;radius:14}contentItem:PreflightPanel{anchors.fill:parent;anchors.margins:16;cameraName:devicesModel.activeName;video:vd;telemetry:t;network:net;navigation:ext;nextAction:homeDashboard.nextAction;osdEnabled:station.osdEnabled;onCloseRequested:preflightPopup.close();onOpenOsdSettings:function(){preflightPopup.close();osdSettingsPopup.open()}onOpenSimulation:function(){preflightPopup.close();simulation=true}onOpenDiagnostics:function(){preflightPopup.close();diagnostics.open()}}}
 Popup{id:diagnostics;modal:true;anchors.centerIn:Overlay.overlay;width:Math.min(860,w.width-40);height:Math.min(640,w.height-48);background:Rectangle{color:"#0d1725";border.color:green;radius:14}contentItem:DiagnosticsPanel{anchors.fill:parent;anchors.margins:16;onCloseRequested:diagnostics.close()}}
 Popup{id:firmwarePopup;modal:true;anchors.centerIn:Overlay.overlay;width:Math.min(900,w.width-40);height:Math.min(700,w.height-48);background:Rectangle{color:"#0d1725";border.color:amber;radius:14}contentItem:FirmwareCenter{anchors.fill:parent;anchors.margins:18;onCloseRequested:firmwarePopup.close()}}
 Popup{id:hardwareE2EPopup;modal:true;anchors.centerIn:Overlay.overlay;width:Math.min(760,w.width-40);height:Math.min(600,w.height-48);onOpened:hardwareE2ERuntime.reset();background:Rectangle{color:"#0d1725";border.color:amber;radius:14}contentItem:HardwareE2EPanel{anchors.fill:parent;anchors.margins:18;onCloseRequested:hardwareE2EPopup.close()}}
 Popup{id:updatePopup;modal:true;anchors.centerIn:Overlay.overlay;width:Math.min(740,w.width-40);height:Math.min(580,w.height-48);background:Rectangle{color:"#0d1725";border.color:green;radius:14}contentItem:UpdatePanel{anchors.fill:parent;anchors.margins:18;onCloseRequested:updatePopup.close()}}
 Popup{id:devices;modal:true;anchors.centerIn:Overlay.overlay;width:Math.min(960,w.width-40);height:Math.min(660,w.height-60);background:Rectangle{color:"#0d1725";border.color:blue;radius:14}contentItem:DevicesPanel{anchors.fill:parent;anchors.margins:18;onCloseRequested:devices.close();onActivateDevice:function(deviceId){devices.close();connectDevice(deviceId)}}}
}
