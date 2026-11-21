import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
Item {
 id:root
 signal openDevices();signal openFirmware();signal openUpdate();signal openDiagnostics();signal connectDevice(string deviceId)
 property color fg:"#f4f7fb";property color sub:"#8fa1b7";property color line:"#273d55";property color green:"#27d59a";property color blue:"#2387ff"
 ColumnLayout{anchors.fill:parent;anchors.margins:32;spacing:22
  RowLayout{Layout.fillWidth:true;ColumnLayout{Text{text:"ФПВ УХИЛЯНТ";color:fg;font.pixelSize:30;font.bold:true}Text{text:"Ground station · video-first";color:sub}}Item{Layout.fillWidth:true}Text{text:"v"+updater.currentVersion;color:sub}}
  GridLayout{Layout.fillWidth:true;columns:5;columnSpacing:12;rowSpacing:12
   Button{text:"Пристрої";Layout.fillWidth:true;Layout.preferredHeight:64;onClicked:root.openDevices()}
   Button{text:"Швидке підключення";Layout.fillWidth:true;Layout.preferredHeight:64;enabled:devicesModel.count>0;onClicked:quick.open()}
   Button{text:"Firmware";Layout.fillWidth:true;Layout.preferredHeight:64;onClicked:root.openFirmware()}
   Button{text:"Оновлення";Layout.fillWidth:true;Layout.preferredHeight:64;onClicked:root.openUpdate()}
   Button{text:"Діагностика";Layout.fillWidth:true;Layout.preferredHeight:64;onClicked:root.openDiagnostics()}
  }
  Text{text:"ЗБЕРЕЖЕНІ ПРИСТРОЇ";color:sub;font.bold:true}
  Rectangle{Layout.fillWidth:true;Layout.fillHeight:true;radius:12;color:"#0b1420";border.color:line
   ListView{id:list;anchors.fill:parent;anchors.margins:12;clip:true;spacing:8;model:devicesModel.items
    delegate:Rectangle{required property var modelData;width:list.width;height:72;radius:9;color:"#111d2c";border.color:modelData.active?green:line
     RowLayout{anchors.fill:parent;anchors.margins:12;ColumnLayout{Layout.fillWidth:true;Text{text:modelData.name;color:fg;font.bold:true}Text{text:modelData.host;color:sub}}Text{text:modelData.active?"ACTIVE":"";color:green;font.bold:true}Button{text:"FPV";onClicked:root.connectDevice(modelData.id)}}
    }
    Text{anchors.centerIn:parent;visible:devicesModel.count===0;text:"Немає збережених пристроїв";color:sub}
   }
  }
 }
 Popup{id:quick;modal:true;anchors.centerIn:Overlay.overlay;width:Math.min(560,root.width-48);height:Math.min(440,root.height-60);background:Rectangle{color:"#0d1725";border.color:blue;radius:14}
  contentItem:ColumnLayout{anchors.fill:parent;anchors.margins:18;Text{text:"ШВИДКЕ ПІДКЛЮЧЕННЯ";color:fg;font.pixelSize:20;font.bold:true}Text{text:"Використовуються лише вже збережені пристрої та їхні фактичні потоки.";color:sub;wrapMode:Text.WordWrap;Layout.fillWidth:true}ListView{id:quickList;Layout.fillWidth:true;Layout.fillHeight:true;model:devicesModel.items;spacing:8;delegate:Button{required property var modelData;width:quickList.width;text:modelData.name+" · "+modelData.host;onClicked:{quick.close();root.connectDevice(modelData.id)}}}Button{text:"Закрити";onClicked:quick.close()}}
 }
}
