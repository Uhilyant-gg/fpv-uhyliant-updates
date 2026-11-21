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
  Rectangle{Layout.fillWidth:true;height:128;radius:10;color:"#0b1420";border.color:health.state==="problem"?"#ff6678":health.state==="attention"?"#ffb84d":"#273d55"
   ColumnLayout{anchors.fill:parent;anchors.margins:12
    Text{text:"Мережа · "+healthText(health.state);color:"#f4f7fb";font.bold:true}
    Text{text:show(health.problem);color:"#8fa1b7";wrapMode:Text.Wrap;Layout.fillWidth:true}
    RowLayout{visible:health.remediation!==null&&health.remediation!==undefined;Layout.fillWidth:true
     Text{text:health.remediation?"Рекомендована дія: "+health.remediation.title:"";color:"#27d59a";Layout.fillWidth:true}
     Button{text:"Виправити";enabled:health.remediation!==null&&health.remediation!==undefined;onClicked:diagnosticsRuntime.applyRemediation(health.remediation.action);HoverHint{text:"Виконати лише запропоновану безпечну дію та повторно оцінити стан."}}
    }
   }
  }
  Rectangle{Layout.fillWidth:true;Layout.fillHeight:true;radius:10;color:"#0b1420";border.color:"#273d55"
   ColumnLayout{anchors.fill:parent;anchors.margins:12;spacing:6
    Text{text:"Телеметрія: "+show(snap.protocols.active)+" · "+(snap.protocols.available?"готово":"невідомо / недоступно");color:"#f4f7fb"}
    Text{text:"Мережа: "+show(snap.network.network&&snap.network.network.state);color:"#8fa1b7"}
    Text{text:"Updater: "+show(snap.updater.state)+" · "+show(snap.updater.status);color:"#8fa1b7";wrapMode:Text.Wrap;Layout.fillWidth:true}
    Text{text:"Останнє виправлення: "+(snap.lastRemediation&&snap.lastRemediation.action?show(snap.lastRemediation.action)+" · "+(snap.lastRemediation.ok?"виконано":"не виконано"):"немає");color:"#8fa1b7"}
    Item{Layout.fillHeight:true}
   }
  }
  RowLayout{Layout.fillWidth:true
   Button{text:"Експортувати діагностику";onClicked:exportPath.text=diagnosticsRuntime.export();HoverHint{text:"Зберегти очищений від секретів діагностичний пакет."}}
   Text{id:exportPath;Layout.fillWidth:true;color:"#27d59a";elide:Text.ElideMiddle}
   Button{text:"Закрити";onClicked:closeRequested();HoverHint{text:"Закрити діагностику."}}
  }
 }
}
