import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
Item {
 signal closeRequested()
 property var snap: diagnosticsRuntime.snapshot
 property var health: snap.networkHealth || ({})
 function show(v){return v===undefined||v===null||v===""?"невідомо":v}
 function healthText(v){var m={"ready":"Готово","attention":"Потребує уваги","problem":"Проблема","unknown":"Невідомо"};return m[v]||"Невідомо"}
 ColumnLayout{anchors.fill:parent;spacing:8
  Text{text:"ДІАГНОСТИКА";color:"#f4f7fb";font.pixelSize:20;font.bold:true}
  Text{text:"Зведений фактичний стан для пошуку проблем. Невідомі значення не вгадуються.";color:"#8fa1b7";wrapMode:Text.Wrap;Layout.fillWidth:true}
  Rectangle{Layout.fillWidth:true;height:96;radius:10;color:"#0b1420";border.color:health.state==="problem"?"#ff6678":health.state==="attention"?"#ffb84d":"#273d55"
   ColumnLayout{anchors.fill:parent;anchors.margins:12;Text{text:"Мережа · "+healthText(health.state);color:"#f4f7fb";font.bold:true}Text{text:show(health.problem);color:"#8fa1b7";wrapMode:Text.Wrap;Layout.fillWidth:true}Text{visible:health.remediation!==null&&health.remediation!==undefined;text:health.remediation?"Рекомендована дія: "+health.remediation.title:"";color:"#27d59a"}}
  }
  Rectangle{Layout.fillWidth:true;Layout.fillHeight:true;radius:10;color:"#0b1420";border.color:"#273d55"
   ColumnLayout{anchors.fill:parent;anchors.margins:12;spacing:6
    Text{text:"Телеметрія: "+show(snap.protocols.active)+" · "+(snap.protocols.available?"готово":"невідомо / недоступно");color:"#f4f7fb"}
    Text{text:"Мережа: "+show(snap.network.network&&snap.network.network.state);color:"#8fa1b7"}
    Text{text:"Updater: "+show(snap.updater.state)+" · "+show(snap.updater.status);color:"#8fa1b7";wrapMode:Text.Wrap;Layout.fillWidth:true}
    Text{text:"Пристроїв у snapshot: "+(snap.devices?snap.devices.length:0);color:"#8fa1b7"}
    Text{text:"Correlation ID: "+show(snap.correlationId);color:"#8fa1b7";font.family:"Consolas";font.pixelSize:12;elide:Text.ElideRight;Layout.fillWidth:true}
    Item{Layout.fillHeight:true}
   }
  }
  RowLayout{Layout.fillWidth:true
   Button{
    text:"Експортувати діагностику"
    onClicked: exportPath.text=diagnosticsRuntime.export()
    HoverHint{text:"Зберегти очищений від секретів діагностичний пакет."}
   }
   Text{id:exportPath;Layout.fillWidth:true;color:"#27d59a";elide:Text.ElideMiddle}
   Button{
    text:"Закрити"
    onClicked: closeRequested()
    HoverHint{text:"Закрити діагностику."}
   }
  }
 }
}
