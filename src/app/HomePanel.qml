import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
Item {
 id:root
 signal openDevices();signal openFirmware();signal openUpdate();signal openDiagnostics();signal connectDevice(string deviceId)
 property color fg:"#f5f8fc";property color sub:"#8799ad";property color surface:"#0d1723";property color elevated:"#132235";property color line:"#203348";property color green:"#35e0a1";property color blue:"#4195ff"
 function canEnterFpv(deviceId){if(!deviceId)return false;for(var i=0;i<devicesModel.items.length;i++)if(devicesModel.items[i].id===deviceId){var streams=devicesModel.streams;for(var n=0;n<streams.length;n++)if(streams[n].device_id===deviceId&&streams[n].enabled===true)return true;return false}return false}
 Rectangle{anchors.fill:parent;color:"#08111b"}
 ColumnLayout{anchors.fill:parent;anchors.margins:28;spacing:22
  RowLayout{Layout.fillWidth:true
   ColumnLayout{spacing:3;Text{text:"ФПВ УХИЛЯНТ";color:fg;font.pixelSize:28;font.bold:true;font.letterSpacing:1}Text{text:"Відео передусім";color:sub;font.pixelSize:13}}
   Item{Layout.fillWidth:true}
   Rectangle{width:110;height:32;radius:16;color:surface;Text{anchors.centerIn:parent;text:"v"+updater.currentVersion;color:sub;font.pixelSize:12}}
  }
  RowLayout{Layout.fillWidth:true;spacing:12
   Button{id:devicesButton;text:"Пристрої · Додати камеру";Layout.preferredWidth:210;Layout.preferredHeight:48;font.bold:true;onClicked:root.openDevices();HoverHint{text:"Знайти, перевірити або додати камеру."}}
   Button{id:quickButton;text:"Швидке підключення";Layout.preferredHeight:48;enabled:devicesModel.count>0;onClicked:quick.open();HoverHint{text:"Вибрати збережену камеру з налаштованим відеопотоком."}}
   Item{Layout.fillWidth:true}
   Button{id:firmwareButton;text:"Прошивка";flat:true;onClicked:root.openFirmware();HoverHint{text:"Відкрити безпечне керування прошивкою."}}
   Button{id:updateButton;text:"Оновлення";flat:true;onClicked:root.openUpdate();HoverHint{text:"Перевірити оновлення програми."}}
   Button{id:diagnosticsButton;text:"Діагностика";flat:true;onClicked:root.openDiagnostics();HoverHint{text:"Переглянути фактично доступну діагностику."}}
  }
  RowLayout{Layout.fillWidth:true;Text{text:"МОЇ КАМЕРИ";color:sub;font.bold:true;font.pixelSize:12;font.letterSpacing:1}Item{Layout.fillWidth:true}Text{text:devicesModel.count===0?"":devicesModel.count+" збережено";color:sub;font.pixelSize:12}}
  Rectangle{Layout.fillWidth:true;Layout.fillHeight:true;radius:18;color:surface;border.color:line
   ListView{id:list;anchors.fill:parent;anchors.margins:12;clip:true;spacing:8;model:devicesModel.items
    delegate:Rectangle{required property var modelData;width:list.width;height:82;radius:13;color:mouse.hovered?elevated:"transparent";border.color:modelData.active?green:"transparent"
     HoverHandler{id:mouse}
     RowLayout{anchors.fill:parent;anchors.margins:13;spacing:12
      Rectangle{width:42;height:42;radius:12;color:modelData.openipcIdentity.verified?"#15392f":"#172334";Text{anchors.centerIn:parent;text:"●";color:modelData.openipcIdentity.verified?green:sub;font.pixelSize:16}}
      ColumnLayout{Layout.fillWidth:true;spacing:3;Text{text:modelData.name;color:fg;font.bold:true;font.pixelSize:15}Text{text:modelData.host+(modelData.openipcIdentity.verified?" · OpenIPC":"");color:sub;font.pixelSize:12}}
      Text{visible:modelData.active;text:"АКТИВНИЙ";color:green;font.bold:true;font.pixelSize:11}
      Button{text:"FPV";enabled:root.canEnterFpv(modelData.id);onClicked:root.connectDevice(modelData.id);HoverHint{text:"Відкрити FPV. Доступність потоку перевіряється перед запуском."}}
     }
    }
    Column{anchors.centerIn:parent;visible:devicesModel.count===0;spacing:10
     Text{anchors.horizontalCenter:parent.horizontalCenter;text:"Камер ще немає";color:fg;font.pixelSize:20;font.bold:true}
     Text{anchors.horizontalCenter:parent.horizontalCenter;text:"Знайдіть камеру автоматично або вкажіть її IP";color:sub}
     Button{anchors.horizontalCenter:parent.horizontalCenter;text:"Знайти камеру";onClicked:root.openDevices();HoverHint{text:"Відкрити простий пошук камер."}}
    }
   }
  }
 }
 Popup{id:quick;modal:true;anchors.centerIn:Overlay.overlay;width:Math.min(560,root.width-48);height:Math.min(460,root.height-60);padding:0;background:Rectangle{color:elevated;border.color:line;radius:18}
  contentItem:ColumnLayout{anchors.fill:parent;anchors.margins:20;spacing:12
   RowLayout{Layout.fillWidth:true;Text{text:"Швидке підключення";color:fg;font.pixelSize:22;font.bold:true}Item{Layout.fillWidth:true}Button{text:"Закрити";flat:true;onClicked:quick.close()}}
   Text{text:"Використовуються лише збережені камери з налаштованим увімкненим відеопотоком. Наявність потоку не означає підтверджену мережеву доступність. Перед входом у FPV програма перевірить його кінцеву точку.";color:sub;wrapMode:Text.WordWrap;Layout.fillWidth:true}
   ListView{id:quickList;Layout.fillWidth:true;Layout.fillHeight:true;model:devicesModel.items;spacing:8;delegate:Button{required property var modelData;width:quickList.width;height:54;text:modelData.name+"   ·   "+modelData.host;enabled:root.canEnterFpv(modelData.id);onClicked:{quick.close();root.connectDevice(modelData.id)}HoverHint{text:"Підключити камеру і перевірити її RTSP-потік."}}}
  }
 }
}
