import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
Item {
 id:root
 signal openDevices();signal openFirmware();signal openUpdate();signal openDiagnostics();signal connectDevice(string deviceId)
 property color fg:"#f4f7fb";property color sub:"#8fa1b7";property color line:"#273d55";property color green:"#27d59a";property color blue:"#2387ff"
 function canEnterFpv(deviceId){if(!deviceId)return false;for(var i=0;i<devicesModel.items.length;i++)if(devicesModel.items[i].id===deviceId){var streams=devicesModel.streams;for(var n=0;n<streams.length;n++)if(streams[n].device_id===deviceId&&streams[n].enabled===true)return true;return false}return false}
 ColumnLayout{anchors.fill:parent;anchors.margins:32;spacing:22
  RowLayout{Layout.fillWidth:true;ColumnLayout{Text{text:"ФПВ УХИЛЯНТ";color:fg;font.pixelSize:30;font.bold:true}Text{text:"Наземна FPV-станція · відео передусім";color:sub}}Item{Layout.fillWidth:true}Text{text:"Версія "+updater.currentVersion;color:sub}}
  GridLayout{Layout.fillWidth:true;columns:5;columnSpacing:12;rowSpacing:12
   Button{id:devicesButton;text:"Пристрої";Layout.fillWidth:true;Layout.preferredHeight:64;onClicked:root.openDevices();HoverHint{text:"Пошук, додавання та налаштування збережених пристроїв."}}
   Button{id:quickButton;text:"Швидке підключення";Layout.fillWidth:true;Layout.preferredHeight:64;enabled:devicesModel.count>0;onClicked:quick.open();HoverHint{text:"Вибір уже збереженого пристрою з налаштованим активним відеопотоком."}}
   Button{id:firmwareButton;text:"Прошивка";Layout.fillWidth:true;Layout.preferredHeight:64;onClicked:root.openFirmware();HoverHint{text:"Центр безпечної підготовки та перевірки операцій із прошивкою."}}
   Button{id:updateButton;text:"Оновлення";Layout.fillWidth:true;Layout.preferredHeight:64;onClicked:root.openUpdate();HoverHint{text:"Перевірка, завантаження та встановлення оновлень програми."}}
   Button{id:diagnosticsButton;text:"Діагностика";Layout.fillWidth:true;Layout.preferredHeight:64;onClicked:root.openDiagnostics();HoverHint{text:"Перегляд фактично доступного стану телеметрії, мережі та відео."}}
  }
  Text{text:"ЗБЕРЕЖЕНІ ПРИСТРОЇ";color:sub;font.bold:true}
  Rectangle{Layout.fillWidth:true;Layout.fillHeight:true;radius:12;color:"#0b1420";border.color:line
   ListView{id:list;anchors.fill:parent;anchors.margins:12;clip:true;spacing:8;model:devicesModel.items
    delegate:Rectangle{required property var modelData;width:list.width;height:72;radius:9;color:"#111d2c";border.color:modelData.active?green:line
     RowLayout{anchors.fill:parent;anchors.margins:12;ColumnLayout{Layout.fillWidth:true;Text{text:modelData.name;color:fg;font.bold:true}Text{text:modelData.host;color:sub}}Text{text:modelData.active?"АКТИВНИЙ":"";color:green;font.bold:true}Button{text:"Відкрити FPV";enabled:root.canEnterFpv(modelData.id);onClicked:root.connectDevice(modelData.id);HoverHint{text:"Перейти до FPV-режиму цього пристрою. Доступність RTSP перевіряється під час запуску."}}}
    }
    Text{anchors.centerIn:parent;visible:devicesModel.count===0;text:"Немає збережених пристроїв";color:sub}
   }
  }
 }
 Popup{id:quick;modal:true;anchors.centerIn:Overlay.overlay;width:Math.min(560,root.width-48);height:Math.min(440,root.height-60);background:Rectangle{color:"#0d1725";border.color:blue;radius:14}
  contentItem:ColumnLayout{anchors.fill:parent;anchors.margins:18;Text{text:"ШВИДКЕ ПІДКЛЮЧЕННЯ";color:fg;font.pixelSize:20;font.bold:true}Text{text:"Використовуються лише збережені пристрої, для яких уже є фактичний увімкнений відеопотік. Наявність потоку не означає підтверджену мережеву доступність.";color:sub;wrapMode:Text.WordWrap;Layout.fillWidth:true}ListView{id:quickList;Layout.fillWidth:true;Layout.fillHeight:true;model:devicesModel.items;spacing:8;delegate:Button{required property var modelData;width:quickList.width;text:modelData.name+" · "+modelData.host;enabled:root.canEnterFpv(modelData.id);onClicked:{quick.close();root.connectDevice(modelData.id)}HoverHint{text:"Підключити цей збережений пристрій і перевірити доступність його RTSP-потоку."}}}Button{text:"Закрити";onClicked:quick.close()}}
 }
}
