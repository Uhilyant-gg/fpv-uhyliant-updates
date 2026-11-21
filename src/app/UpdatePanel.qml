import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
Item{
 id:root;signal closeRequested();property color fg:"#f4f7fb";property color sub:"#8fa1b7";property color green:"#27d59a"
 ColumnLayout{anchors.fill:parent;spacing:12
  RowLayout{Layout.fillWidth:true;ColumnLayout{Text{text:"ОНОВЛЕННЯ";color:fg;font.pixelSize:22;font.bold:true}Text{text:"Поточна версія: "+updater.currentVersion;color:sub}}Item{Layout.fillWidth:true}Button{text:"Закрити";onClicked:root.closeRequested()}}
  Text{text:"Стан: "+updater.updateStatus;color:updater.updateState==="error"||updater.updateState==="blocked"?"#ff6678":sub;wrapMode:Text.WordWrap;Layout.fillWidth:true}
  Text{visible:updater.availableVersion!=="";text:"Доступна версія: "+updater.availableVersion;color:green;font.bold:true}
  ProgressBar{Layout.fillWidth:true;from:0;to:100;value:updater.progress;visible:updater.busy}
  RowLayout{Button{text:"Перевірити";enabled:!updater.busy;onClicked:updater.check();HoverHint{text:"Отримати та перевірити підписаний маніфест оновлення."}}Button{text:"Завантажити";enabled:!updater.busy&&updater.updateState==="available";onClicked:updater.download();HoverHint{text:"Завантажити пакет і перевірити його SHA-256 перед позначенням готовим."}}Button{text:"Встановити";enabled:!updater.busy&&updater.installReady;onClicked:updater.install();HoverHint{text:"Запустити наявний захищений механізм встановлення лише для перевіреного пакета."}}}
  Text{text:"Маніфест і пакет проходять наявну перевірку ланцюжка довіри та SHA-256 перед готовністю до встановлення.";color:sub;wrapMode:Text.WordWrap;Layout.fillWidth:true}
  ListView{Layout.fillWidth:true;Layout.fillHeight:true;model:updater.releaseNotes;clip:true;delegate:Text{required property string modelData;width:ListView.view.width;text:"• "+modelData;color:fg;wrapMode:Text.WordWrap}}
 }
}
