import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
Item {
 signal closeRequested();property var ready:hardwareE2ERuntime.readiness;property var captures:hardwareE2ERuntime.captures
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
  Text{text:"E2E evidence";color:"#f4f7fb";font.bold:true}
  RowLayout{Layout.fillWidth:true;Button{text:"Зберегти preflight";onClicked:hardwareE2ERuntime.capture("preflight")}Text{Layout.fillWidth:true;text:captures.preflight||"ще не збережено";color:captures.preflight?"#27d59a":"#8fa1b7";elide:Text.ElideMiddle}}
  RowLayout{Layout.fillWidth:true;Button{text:"Зберегти post-update";onClicked:hardwareE2ERuntime.capture("post-update")}Text{Layout.fillWidth:true;text:captures["post-update"]||"ще не збережено";color:captures["post-update"]?"#27d59a":"#8fa1b7";elide:Text.ElideMiddle}}
  RowLayout{Layout.fillWidth:true;Button{text:"Зберегти failure";onClicked:hardwareE2ERuntime.capture("failure")}Text{Layout.fillWidth:true;text:captures.failure||"ще не збережено";color:captures.failure?"#ffb84d":"#8fa1b7";elide:Text.ElideMiddle}}
  Item{Layout.fillHeight:true}
  Text{text:"Цей екран лише фіксує evidence. Destructive update залишається в окремому контрольованому workflow.";color:"#ffb84d";wrapMode:Text.Wrap;Layout.fillWidth:true}
 }
}
