import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

ApplicationWindow {
 id: w
 visible: true
 visibility: Window.Maximized
 minimumWidth: 1024
 minimumHeight: 640
 color: "#050a12"
 title: appWindowTitle
 property color fg: "#f4f7fb"
 property color sub: "#8fa1b7"
 property color panel: "#e6101927"
 property color line: "#273d55"
 property color green: "#27d59a"
 property color blue: "#4aa3ff"
 property color amber: "#ffb84d"
 property bool updateOpen: false
 property bool deviceOpen: false
 property bool diagnosticsOpen: false
 property bool videoProfileOpen: false
 property string clockText: ""
 property string selectedVideoProfile: "Збалансований"
 property string selectedVideoTarget: "Основний потік"
 property var videoProfiles: ["Мінімальна затримка", "Збалансований", "Низький бітрейт", "Максимальна якість", "Користувацький"]
 component Glass: Rectangle { color: w.panel; border.color: w.line; border.width: 1; radius: 12 }
 component StatusCard: Glass { required property string titleText; required property string valueText; required property color accent; implicitWidth:190; implicitHeight:72; Column { anchors.fill:parent;anchors.margins:12;spacing:4;Text{text:titleText;color:w.sub;font.pixelSize:12;font.bold:true}Text{text:valueText;color:accent;font.pixelSize:17;font.bold:true;elide:Text.ElideRight;width:parent.width} } }
 Timer { interval:1000;running:true;repeat:true;triggeredOnStart:true;onTriggered:clockText=Qt.formatDateTime(new Date(),"dd.MM.yyyy  hh:mm:ss") }
 Shortcut { sequence:"F2";onActivated:station.toggleVideo() }
 Shortcut { sequence:"F11";onActivated:w.visibility=w.visibility===Window.FullScreen?Window.Maximized:Window.FullScreen }
 Shortcut { sequence:"Escape";onActivated:{station.setOSDEdit(false);if(station.menuOpen)station.toggleMenu();updateOpen=false;deviceOpen=false;diagnosticsOpen=false;videoProfileOpen=false} }
 Image { anchors.fill:parent;source:"preview.jpg";fillMode:Image.PreserveAspectCrop;opacity:station.videoRunning?.80:.16 }
 Rectangle { anchors.fill:parent;color:"#8a030812" }
 Rectangle { id:topBar;height:74;anchors.left:parent.left;anchors.right:parent.right;anchors.top:parent.top;color:"#f20a1220";border.color:line
  RowLayout { anchors.fill:parent;anchors.leftMargin:20;anchors.rightMargin:16;spacing:16
   Rectangle{width:10;height:34;radius:5;color:blue}
   ColumnLayout{spacing:1;Text{text:"ФПВ УХИЛЯНТ";color:fg;font.pixelSize:22;font.bold:true;font.letterSpacing:1.1}Text{text:"НАЗЕМНА СТАНЦІЯ  •  "+updater.currentVersion;color:sub;font.pixelSize:11}}
   Item{Layout.fillWidth:true} Rectangle{width:8;height:8;radius:4;color:green} Text{text:"СТАНЦІЯ ГОТОВА";color:green;font.bold:true;font.pixelSize:12} Text{text:clockText;color:fg;font.family:"Consolas";font.pixelSize:14} Button{text:station.menuOpen?"✕":"☰";onClicked:station.toggleMenu()}
  }
 }
 RowLayout { anchors.left:parent.left;anchors.right:parent.right;anchors.top:topBar.bottom;anchors.bottom:bottomBar.top;anchors.margins:16;spacing:14
  Glass { Layout.preferredWidth:86;Layout.fillHeight:true;ColumnLayout{anchors.fill:parent;anchors.margins:10;spacing:10
   Button{text:"⌂";font.pixelSize:20;Layout.fillWidth:true;onClicked:{deviceOpen=false;diagnosticsOpen=false;videoProfileOpen=false}}
   Button{text:"▣";font.pixelSize:20;Layout.fillWidth:true;onClicked:deviceOpen=true;ToolTip.visible:hovered;ToolTip.text:"Пристрої"}
   Button{text:"◉";font.pixelSize:20;Layout.fillWidth:true;onClicked:station.toggleVideo();ToolTip.visible:hovered;ToolTip.text:"Відео, F2"}
   Button{text:"▤";font.pixelSize:20;Layout.fillWidth:true;onClicked:videoProfileOpen=true;ToolTip.visible:hovered;ToolTip.text:"Відеопрофілі"}
   Button{text:"✚";font.pixelSize:20;Layout.fillWidth:true;onClicked:diagnosticsOpen=true;ToolTip.visible:hovered;ToolTip.text:"Діагностика"} Item{Layout.fillHeight:true} Button{text:"⚙";font.pixelSize:20;Layout.fillWidth:true;onClicked:station.toggleMenu()}
  }}
  Item { Layout.fillWidth:true;Layout.fillHeight:true;Glass{anchors.fill:parent;Rectangle{anchors.fill:parent;anchors.margins:8;radius:8;color:"#aa030812";border.color:"#20354a"}
   Column{visible:!station.videoRunning;anchors.centerIn:parent;spacing:10;Text{text:"ВІДЕОПОТІК НЕ ПІДКЛЮЧЕНО";color:fg;font.pixelSize:20;font.bold:true;anchors.horizontalCenter:parent.horizontalCenter}Button{text:"Відеопрофіль: "+selectedVideoProfile;anchors.horizontalCenter:parent.horizontalCenter;onClicked:videoProfileOpen=true}}
   Rectangle{visible:station.videoRunning;anchors.left:parent.left;anchors.top:parent.top;anchors.margins:20;width:132;height:34;radius:17;color:"#cc0d2b20";border.color:green;Text{anchors.centerIn:parent;text:"VIDEO ACTIVE";color:green;font.bold:true;font.pixelSize:11}}
  }}
  ColumnLayout { Layout.preferredWidth:Math.min(330,w.width*.24);Layout.fillHeight:true;spacing:12
   Glass{Layout.fillWidth:true;Layout.preferredHeight:150;ColumnLayout{anchors.fill:parent;anchors.margins:16;spacing:8;Text{text:"АКТИВНИЙ БОРТ";color:sub;font.pixelSize:12;font.bold:true}Text{text:devicesModel.activeName||"Не вибрано";color:fg;font.pixelSize:22;font.bold:true}Text{text:devicesModel.activeSummary||"Додайте пристрій у локальну базу";color:sub;wrapMode:Text.WordWrap;Layout.fillWidth:true}Button{text:"Відкрити пристрої";Layout.fillWidth:true;onClicked:deviceOpen=true}}}
   StatusCard{Layout.fillWidth:true;titleText:"ВІДЕО";valueText:station.videoRunning?"ТЕСТОВИЙ ПОТІК":"НЕ ПІДКЛЮЧЕНО";accent:station.videoRunning?green:amber}
   StatusCard{Layout.fillWidth:true;titleText:"ВІДЕОПРОФІЛЬ";valueText:selectedVideoProfile;accent:blue}
   StatusCard{Layout.fillWidth:true;titleText:"ТЕЛЕМЕТРІЯ";valueText:"НЕ НАЛАШТОВАНО";accent:sub}
   Glass{Layout.fillWidth:true;Layout.fillHeight:true;ColumnLayout{anchors.fill:parent;anchors.margins:16;spacing:8;Text{text:"ШВИДКІ ДІЇ";color:sub;font.pixelSize:12;font.bold:true}Button{text:"Вибрати відеопрофіль";Layout.fillWidth:true;onClicked:videoProfileOpen=true}Button{text:"Перевірити оновлення";Layout.fillWidth:true;onClicked:{updateOpen=true;updater.check()}}Button{text:"Діагностика станції";Layout.fillWidth:true;onClicked:diagnosticsOpen=true}Item{Layout.fillHeight:true}}}
  }
 }
 Rectangle { id:bottomBar;height:36;anchors.left:parent.left;anchors.right:parent.right;anchors.bottom:parent.bottom;color:"#f20a1220";border.color:line;RowLayout{anchors.fill:parent;anchors.leftMargin:18;anchors.rightMargin:18;Text{text:"●  CORE ONLINE";color:green;font.bold:true;font.pixelSize:11}Text{text:"DEVICE: "+(devicesModel.activeName||"--");color:sub;font.pixelSize:11}Text{text:"STREAM: "+selectedVideoTarget;color:sub;font.pixelSize:11}Text{text:"PROFILE: "+selectedVideoProfile;color:blue;font.pixelSize:11}Item{Layout.fillWidth:true}Text{text:appWindowTitle;color:sub;font.pixelSize:11}} }
 Glass { visible:station.menuOpen;z:20;width:360;anchors.right:parent.right;anchors.top:topBar.bottom;anchors.bottom:bottomBar.top;anchors.margins:12;ColumnLayout{anchors.fill:parent;anchors.margins:16;spacing:10;Text{text:"МЕНЮ СТАНЦІЇ";color:fg;font.pixelSize:18;font.bold:true}Button{text:"Пристрої";Layout.fillWidth:true;onClicked:{deviceOpen=true;station.toggleMenu()}}Button{text:"Відеопрофілі";Layout.fillWidth:true;onClicked:{videoProfileOpen=true;station.toggleMenu()}}Button{text:"Діагностика";Layout.fillWidth:true;onClicked:{diagnosticsOpen=true;station.toggleMenu()}}Button{text:"Оновлення станції";Layout.fillWidth:true;onClicked:{updateOpen=true;station.toggleMenu()}}Item{Layout.fillHeight:true}Button{text:"Вихід";Layout.fillWidth:true;onClicked:Qt.quit()}} }
 Popup { id:devices;visible:deviceOpen;modal:true;anchors.centerIn:Overlay.overlay;width:Math.min(900,w.width-48);height:Math.min(620,w.height-80);onClosed:deviceOpen=false;background:Rectangle{color:"#0d1725";border.color:blue;radius:14}contentItem:DevicesPanel{anchors.fill:parent;anchors.margins:22;onCloseRequested:devices.close()} }
 Popup { id:videoProfile;visible:videoProfileOpen;modal:true;anchors.centerIn:Overlay.overlay;width:Math.min(820,w.width-48);height:Math.min(620,w.height-80);onClosed:videoProfileOpen=false;background:Rectangle{color:"#0d1725";border.color:blue;radius:14}
  contentItem:ColumnLayout{anchors.fill:parent;anchors.margins:22;spacing:12;RowLayout{Layout.fillWidth:true;ColumnLayout{Text{text:"ВІДЕОПРОФІЛЬ";color:fg;font.pixelSize:22;font.bold:true}Text{text:"Профіль призначається потоку, а не прошивці камери";color:sub;font.pixelSize:12}}Item{Layout.fillWidth:true}Button{text:"Закрити";onClicked:videoProfile.close()}}ComboBox{id:streamBox;Layout.fillWidth:true;model:["Основний потік","Додатковий потік","Thermal / PiP"];onActivated:selectedVideoTarget=currentText}ListView{id:profileList;Layout.fillWidth:true;Layout.fillHeight:true;clip:true;spacing:8;model:videoProfiles;delegate:Rectangle{required property string modelData;width:profileList.width;height:72;radius:10;color:modelData===selectedVideoProfile?"#173650":"#111d2c";border.color:modelData===selectedVideoProfile?blue:line;RowLayout{anchors.fill:parent;anchors.margins:14;Text{text:modelData;color:fg;font.pixelSize:16;font.bold:true;Layout.fillWidth:true}Button{text:modelData===selectedVideoProfile?"Вибрано":"Вибрати";onClicked:selectedVideoProfile=modelData}}}}}
 }
 Popup { id:diagnostics;visible:diagnosticsOpen;modal:true;anchors.centerIn:Overlay.overlay;width:Math.min(760,w.width-48);height:Math.min(560,w.height-80);onClosed:diagnosticsOpen=false;background:Rectangle{color:"#0d1725";border.color:green;radius:14}contentItem:ColumnLayout{anchors.fill:parent;anchors.margins:22;spacing:12;Text{text:"ДІАГНОСТИКА СТАНЦІЇ";color:fg;font.pixelSize:22;font.bold:true}Text{text:"Пристроїв у базі: "+devicesModel.count;color:fg}Text{text:"Активний: "+(devicesModel.activeName||"НЕ ВИБРАНО");color:devicesModel.activeName?green:sub}Item{Layout.fillHeight:true}Button{text:"Закрити";Layout.alignment:Qt.AlignRight;onClicked:diagnostics.close()}} }
 Popup { id:up;visible:updateOpen;modal:true;anchors.centerIn:Overlay.overlay;width:Math.min(720,w.width-48);height:Math.min(580,w.height-80);onClosed:updateOpen=false;background:Rectangle{color:"#0d1725";border.color:blue;radius:14}contentItem:ColumnLayout{anchors.fill:parent;anchors.margins:22;spacing:12;Text{text:"ОНОВЛЕННЯ СТАНЦІЇ";color:fg;font.pixelSize:22;font.bold:true}Text{text:"Поточна: "+updater.currentVersion+"   Доступна: "+(updater.availableVersion||"--");color:fg;font.pixelSize:16}RowLayout{Button{text:"Перевірити";onClicked:updater.check()}Button{text:"Завантажити";enabled:updater.updateState==="available";onClicked:updater.download()}Item{Layout.fillWidth:true}Button{text:"Оновити";enabled:updater.installReady;onClicked:updater.install()}}ProgressBar{from:0;to:100;value:updater.progress;Layout.fillWidth:true}Text{text:updater.updateStatus;color:updater.updateState==="error"?"#ff6678":sub;wrapMode:Text.WordWrap;Layout.fillWidth:true}Item{Layout.fillHeight:true}Button{text:"Закрити";Layout.alignment:Qt.AlignRight;onClicked:up.close()}} }
}
