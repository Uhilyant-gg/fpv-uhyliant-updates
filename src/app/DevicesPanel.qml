import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
Item {
 id:root;signal closeRequested();property color fg:"#f4f7fb";property color sub:"#8fa1b7";property color line:"#273d55";property color blue:"#4aa3ff";property color green:"#27d59a";property string selectedId:""
 ColumnLayout { anchors.fill:parent;spacing:12
  RowLayout { Layout.fillWidth:true
   ColumnLayout{Text{text:"ПРИСТРОЇ";color:root.fg;font.pixelSize:22;font.bold:true}Text{text:"Локальна база та автовиявлення OpenIPC";color:root.sub}}
   Item{Layout.fillWidth:true}
   Button{text:devicesModel.scanning?"Пошук...":"Знайти OpenIPC";enabled:!devicesModel.scanning;onClicked:devicesModel.discoverOpenIPC()}
   Button{text:"Закрити";onClicked:root.closeRequested()}
  }
  Rectangle{Layout.fillWidth:true;height:1;color:root.line}
  RowLayout { Layout.fillWidth:true;Layout.fillHeight:true;spacing:12
   ColumnLayout { Layout.preferredWidth:390;Layout.fillHeight:true
    Text{text:"ЗБЕРЕЖЕНІ";color:root.sub;font.bold:true}
    ListView{id:list;Layout.fillWidth:true;Layout.fillHeight:true;clip:true;spacing:8;model:devicesModel.items;delegate:Rectangle{required property var modelData;width:list.width;height:76;radius:10;color:root.selectedId===modelData.id?"#173650":"#111d2c";border.color:modelData.active?root.green:root.line;MouseArea{anchors.fill:parent;onClicked:root.selectedId=modelData.id}Column{anchors.fill:parent;anchors.margins:10;spacing:3;Text{text:(modelData.active?"●  ":"")+modelData.name;color:modelData.active?root.green:root.fg;font.bold:true}Text{text:modelData.type+" · "+modelData.connection;color:root.sub}Text{text:modelData.host||"Адресу не задано";color:root.sub}}}}
    RowLayout{Button{text:"Зробити активним";enabled:root.selectedId!=="";onClicked:devicesModel.setActive(root.selectedId)}Button{text:"Видалити";enabled:root.selectedId!=="";onClicked:{devicesModel.removeDevice(root.selectedId);root.selectedId=""}}}
   }
   Rectangle{Layout.fillHeight:true;width:1;color:root.line}
   ColumnLayout { Layout.fillWidth:true;Layout.fillHeight:true;spacing:8
    Text{text:"ЗНАЙДЕНО В МЕРЕЖІ";color:root.sub;font.bold:true}
    BusyIndicator{visible:devicesModel.scanning;running:devicesModel.scanning;Layout.alignment:Qt.AlignHCenter}
    Text{visible:!devicesModel.scanning&&devicesModel.discovered.length===0;text:"Натисніть «Знайти OpenIPC». Пошук використовує mDNS у локальній мережі.";color:root.sub;wrapMode:Text.WordWrap;Layout.fillWidth:true}
    ListView{id:found;Layout.fillWidth:true;Layout.fillHeight:true;clip:true;spacing:8;model:devicesModel.discovered;delegate:Rectangle{required property var modelData;width:found.width;height:94;radius:10;color:"#111d2c";border.color:modelData.openipc?root.green:root.line;RowLayout{anchors.fill:parent;anchors.margins:10;ColumnLayout{Layout.fillWidth:true;Text{text:modelData.name;color:root.fg;font.bold:true}Text{text:modelData.host+" · "+modelData.confidence;color:modelData.openipc?root.green:root.sub}Text{text:modelData.services.join(", ");color:root.sub;font.pixelSize:10;elide:Text.ElideRight;Layout.fillWidth:true}}Button{text:"Додати";onClicked:{var id=devicesModel.addDiscovered(modelData.host,modelData.name);if(id)root.selectedId=id}}}}
    Rectangle{Layout.fillWidth:true;height:1;color:root.line}
    Text{text:"Відеопрофілі не записуються в пристрій і не входять до прошивки камери.";color:root.sub;wrapMode:Text.WordWrap;Layout.fillWidth:true}
   }
  }
 }
}
