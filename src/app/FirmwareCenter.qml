import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
Item {
 id:root;signal closeRequested();property color fg:"#f4f7fb";property color sub:"#8fa1b7";property color line:"#273d55";property color green:"#27d59a";property color red:"#ff6678";property color amber:"#ffb84d";property var policy:firmwareCenter.modePolicy(modeBox.currentText)
 function clearSensitive(){passwordField.text="";cameraCredentials.clear()}
 function closePanel(){clearSensitive();root.closeRequested()}
 function stateUa(value){var states={"idle":"очікування","blocked":"заблоковано","executing":"виконання","reboot-pending":"очікується перезапуск","verified":"перевірено","error":"помилка","hardware-validation-pending":"очікується перевірка на обладнанні"};return states[value]||value||"--"}
 function stepUa(value){var steps={"executor":"виконавець","flash":"прошивання","rediscover":"повторне виявлення","verify":"перевірка"};return steps[value]||value||"--"}
 ColumnLayout{anchors.fill:parent;spacing:10
  RowLayout{Layout.fillWidth:true;Text{text:"ЦЕНТР ПРОШИВКИ";color:fg;font.pixelSize:22;font.bold:true}Item{Layout.fillWidth:true}Button{text:"Скинути";onClicked:{clearSensitive();cameraCredentials.reset();firmwareCenter.reset();firmwareExecutor.reset()}}Button{text:"Закрити";onClicked:root.closePanel()}}
  Text{text:"Виявлення → Ідентифікація → Автентифікація → Схвалення → Оновлення → Перезапуск → Повторне виявлення → Перевірка";color:sub;wrapMode:Text.WordWrap;Layout.fillWidth:true}
  ComboBox{id:deviceBox;Layout.fillWidth:true;model:devicesModel.items;textRole:"name";valueRole:"id"}
  RowLayout{Layout.fillWidth:true;TextField{id:usernameField;Layout.fillWidth:true;placeholderText:"Логін камери";text:cameraCredentials.username;onEditingFinished:cameraCredentials.username=text}TextField{id:passwordField;Layout.fillWidth:true;placeholderText:"Пароль камери";echoMode:TextInput.Password;inputMethodHints:Qt.ImhSensitiveData|Qt.ImhNoPredictiveText;onTextChanged:cameraCredentials.password=text}}
  RowLayout{Layout.fillWidth:true;ComboBox{id:profileBox;Layout.fillWidth:true;model:firmwareCenter.profiles}ComboBox{id:modeBox;Layout.fillWidth:true;model:firmwareCenter.modes}}
  Text{text:policy.title+" · "+policy.description;color:modeBox.currentText==="recovery-fullflash"?amber:sub;wrapMode:Text.WordWrap;Layout.fillWidth:true}
  TextField{id:imagePath;Layout.fillWidth:true;placeholderText:"Повний шлях до образу прошивки"}
  TextField{id:imageSha;Layout.fillWidth:true;placeholderText:"Очікуваний SHA-256 (64 шістнадцяткові символи)"}
  RowLayout{Button{text:"Перевірити SHA-256";enabled:imagePath.text!==""&&imageSha.text!=="";onClicked:firmwareCenter.verifyImage(imagePath.text,imageSha.text)}Text{text:firmwareCenter.artifact.verified?"✓ ОБРАЗ ПЕРЕВІРЕНО":firmwareCenter.artifact.error;color:firmwareCenter.artifact.verified?green:red}}
  RowLayout{CheckBox{id:layoutOk;text:"Розмітку флеш-пам'яті перевірено"}CheckBox{id:recoveryOk;text:"Шлях відновлення перевірено"}Button{text:"Попередня перевірка";onClicked:firmwareCenter.precheck(deviceBox.currentValue,profileBox.currentText,modeBox.currentText,recoveryOk.checked,layoutOk.checked)}Button{text:"Підготувати план виконання";enabled:firmwareCenter.approvalMatches(deviceBox.currentValue,profileBox.currentText,modeBox.currentText);onClicked:firmwareCenter.prepareExecution(deviceBox.currentValue,profileBox.currentText,modeBox.currentText)}}
  Text{text:"Виконавець: "+stateUa(firmwareExecutor.status.state)+" · "+stepUa(firmwareExecutor.status.step)+(firmwareExecutor.status.error?" · "+firmwareExecutor.status.error:"");color:firmwareExecutor.status.state==="verified"?green:(firmwareExecutor.status.state==="error"?red:sub);wrapMode:Text.WordWrap;Layout.fillWidth:true}
  Rectangle{Layout.fillWidth:true;Layout.fillHeight:true;radius:8;color:"#111d2c";border.color:firmwareCenter.executionPlan.ready?green:line;ColumnLayout{anchors.fill:parent;anchors.margins:10;Text{text:firmwareCenter.result.ready?"ПОПЕРЕДНЮ ПЕРЕВІРКУ СХВАЛЕНО":"ПОПЕРЕДНЮ ПЕРЕВІРКУ НЕ СХВАЛЕНО";color:firmwareCenter.result.ready?green:red;font.bold:true}Text{text:firmwareCenter.result.reason;color:sub}Text{text:firmwareCenter.executionPlan.ready?"ПЛАН ВИКОНАННЯ ГОТОВИЙ":"ПЛАН ВИКОНАННЯ НЕ ГОТОВИЙ";color:firmwareCenter.executionPlan.ready?green:sub;font.bold:true}Text{text:firmwareCenter.executionPlan.reason;color:sub}ListView{Layout.fillWidth:true;Layout.fillHeight:true;model:firmwareCenter.executionPlan.steps;delegate:Text{required property var modelData;width:ListView.view.width;text:(index+1)+". "+modelData;color:fg;wrapMode:Text.WordWrap}}}}
 }
}
