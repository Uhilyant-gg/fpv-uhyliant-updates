import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
Item {
 id:root
 signal openDevices();signal openFirmware();signal openUpdate();signal openDiagnostics();signal connectDevice(string deviceId)
 property color fg:"#f5f8fc";property color sub:"#8799ad";property color surface:"#0d1723";property color elevated:"#132235";property color line:"#203348";property color green:"#35e0a1"
 function canEnterFpv(deviceId){if(!deviceId)return false;for(var i=0;i<devicesModel.items.length;i++)if(devicesModel.items[i].id===deviceId){var streams=devicesModel.streams;for(var n=0;n<streams.length;n++)if(streams[n].device_id===deviceId&&streams[n].enabled===true)return true;return false}return false}
 Rectangle{anchors.fill:parent;color:"#08111b"}
 ColumnLayout{anchors.fill:parent;anchors.margins:20;spacing:12
  RowLayout{Layout.fillWidth:true;spacing:10
   Text{text:"ФПВ УХИЛЯНТ";color:fg;font.pixelSize:24;font.bold:true;font.letterSpacing:1}
   Text{text:"v"+updater.currentVersion;color:sub;font.pixelSize:11}
   Item{Layout.fillWidth:true}
   Button{text:"Прошивка";flat:true;onClicked:root.openFirmware();HoverHint{text:"Безпечне керування прошивкою камери."}}
   Button{text:"Оновлення";flat:true;onClicked:root.openUpdate();HoverHint{text:"Перевірити оновлення програми."}}
   Button{text:"Діагностика";flat:true;onClicked:root.openDiagnostics();HoverHint{text:"Переглянути фактично доступну діагностику."}}
  }
  RowLayout{Layout.fillWidth:true;spacing:8
   Text{text:"КАМЕРИ";color:sub;font.bold:true;font.pixelSize:11;font.letterSpacing:1}
   Text{text:devicesModel.count?devicesModel.count+" збережено":"немає збережених";color:sub;font.pixelSize:11}
   Item{Layout.fillWidth:true}
   Button{text:"Знайти / додати";Layout.preferredHeight:36;font.bold:true;onClicked:root.openDevices();HoverHint{text:"Знайти камери автоматично або вказати IP вручну."}}
  }
  Rectangle{Layout.fillWidth:true;Layout.fillHeight:true;radius:14;color:surface;border.color:line
   ListView{id:list;anchors.fill:parent;anchors.margins:8;clip:true;spacing:4;model:devicesModel.items
    delegate:Rectangle{required property var modelData;width:list.width;height:62;radius:10;color:mouse.hovered?elevated:"transparent";border.color:modelData.active?green:"transparent"
     HoverHandler{id:mouse}
     RowLayout{anchors.fill:parent;anchors.margins:10;spacing:10
      Rectangle{width:30;height:30;radius:8;color:modelData.openipcIdentity.verified?"#15392f":"#172334";Text{anchors.centerIn:parent;text:"●";color:modelData.openipcIdentity.verified?green:sub;font.pixelSize:12}}
      ColumnLayout{Layout.fillWidth:true;spacing:1;Text{text:modelData.name;color:fg;font.bold:true;font.pixelSize:14}Text{text:modelData.host+(modelData.openipcIdentity.verified?" · OpenIPC":"");color:sub;font.pixelSize:11}}
      Text{visible:modelData.active;text:"АКТИВНА";color:green;font.bold:true;font.pixelSize:10}
      Button{text:"FPV";enabled:root.canEnterFpv(modelData.id);onClicked:root.connectDevice(modelData.id);HoverHint{text:"Відкрити FPV для цієї камери."}}
     }
    }
    Column{anchors.centerIn:parent;visible:devicesModel.count===0;spacing:6
     Text{anchors.horizontalCenter:parent.horizontalCenter;text:"Камер ще немає";color:fg;font.pixelSize:18;font.bold:true}
     Text{anchors.horizontalCenter:parent.horizontalCenter;text:"Натисніть «Знайти / додати»";color:sub;font.pixelSize:12}
    }
   }
  }
 }
}
