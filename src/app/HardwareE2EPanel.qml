import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
Item {
 signal closeRequested();property var ready:hardwareE2ERuntime.readiness
 function mark(v){return v?"✓":"○"}
 ColumnLayout{anchors.fill:parent;spacing:8
  RowLayout{Layout.fillWidth:true;Text{text:"ПЕРЕВІРКА OPENIPC НА ОБЛАДНАННІ";color:"#f4f7fb";font.pixelSize:18;font.bold:true;Layout.fillWidth:true}Button{text:"Закрити";onClicked:closeRequested()}}
  Text{text:ready.ready?"Передумови підтверджені":"Потрібно підтвердити всі передумови";color:ready.ready?"#27d59a":"#ffb84d";font.bold:true}
  Text{text:mark(ready.checks.deviceSelected)+" Вибрано пристрій";color:"#8fa1b7"}
  Text{text:mark(ready.checks.openipcVerified)+" OpenIPC підтверджено";color:"#8fa1b7"}
  Text{text:mark(ready.checks.hardwareIdentityObserved)+" Platform і sensor спостережені";color:"#8fa1b7"}
  Text{text:mark(ready.checks.networkRouteObserved)+" Безпечний локальний маршрут спостережено";color:"#8fa1b7"}
  Text{text:mark(ready.checks.deviceReachableObserved)+" Доступність пристрою спостережена";color:"#8fa1b7"}
  Text{text:mark(ready.checks.firmwareArtifactVerified)+" Firmware artifact перевірений SHA-256";color:"#8fa1b7"}
  Text{text:mark(ready.checks.executionPlanReady)+" План оновлення прив'язаний до цієї камери";color:"#8fa1b7"}
  Text{text:mark(ready.checks.credentialsPresent)+" Дані доступу введені для цієї сесії";color:"#8fa1b7"}
  Text{text:(ready.artifact&&ready.artifact.sha256)?("Artifact: "+ready.artifact.sha256.substring(0,12)+"… / "+(ready.artifact.build||"build невідомий")):"Artifact: не готовий";color:"#8fa1b7"}
  CheckBox{text:"SSH host key перевірено та прийнято";checked:hardwareE2ERuntime.hostKeyAccepted;onToggled:hardwareE2ERuntime.setHostKeyAccepted(checked);HoverHint{text:"Підтвердження прив'язане до камери, hardware identity, artifact і execution plan. Будь-яка зміна скидає його."}}
  RowLayout{Layout.fillWidth:true;Button{text:"Зберегти preflight";onClicked:preflightPath.text=hardwareE2ERuntime.exportPreflight();HoverHint{text:"Експортувати очищений diagnostic bundle перед фізичною перевіркою."}}Text{id:preflightPath;Layout.fillWidth:true;color:"#27d59a";elide:Text.ElideMiddle}}
  Item{Layout.fillHeight:true}
  Text{text:"Цей екран не запускає destructive update. Прошивка залишається в окремому контрольованому workflow.";color:"#ffb84d";wrapMode:Text.Wrap;Layout.fillWidth:true}
 }
}
