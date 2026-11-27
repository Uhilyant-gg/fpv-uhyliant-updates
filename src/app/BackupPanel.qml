import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

Item {
 id:root
 signal closeRequested()
 property string message:""
 property bool messageOk:false
 property var restorePlan:({})
 property color fg:"#f4f7fb"
 property color sub:"#8fa1b7"
 property color line:"#273d55"
 property color blue:"#2387ff"
 property color red:"#ff6678"

 function clearExportPassword(){exportPassword.text="";confirmPassword.text=""}
 function clearSensitiveFields(){clearExportPassword();restorePassword.text="";if(restorePlan.execution)cancelRestore()}
 function createBackup(){
  if(exportPassword.text.length<8){message="Введіть пароль щонайменше з 8 символів.";messageOk=false;return}
  if(exportPassword.text!==confirmPassword.text){message="Паролі не збігаються.";messageOk=false;return}
  message="";saveDialog.open()
 }
 function finishExport(){
  var path=saveDialog.selectedFile.toLocalFile()
  messageOk=path!==""&&stationBackup.exportEncrypted(path,exportPassword.text)
  message=messageOk?"Зашифровану резервну копію створено.":"Не вдалося створити копію. Перевірте доступ до вибраної папки."
  if(messageOk)timelineRuntime.recordEvent("backup-created")
  clearExportPassword()
 }
 function chooseRestore(){
  if(restorePassword.text===""){message="Введіть пароль цієї резервної копії.";messageOk=false;return}
  message="";openDialog.open()
 }
 function inspectRestore(){
  var path=openDialog.selectedFile.toLocalFile()
  restorePlan=path!==""?stationBackup.inspectEncryptedImport(path,restorePassword.text):({})
  restorePassword.text=""
  if(!restorePlan.execution){message="Не вдалося перевірити копію. Перевірте пароль, файл і його сумісність.";messageOk=false;return}
  message="";restoreConfirmation.open()
 }
 function confirmRestore(){
  restorePlan=({})
  restoreConfirmation.close()
  messageOk=stationBackup.restoreInspected(true)
  message=messageOk?"Список пристроїв і відеопотоків відновлено.":"Не вдалося відновити копію. Поточні дані не змінено."
 }
 function inspectAutomatic(){
  restorePlan=stationBackup.inspectAutomatic()
  if(!restorePlan.execution){message="Автоматичну копію не перевірено.";messageOk=false;return}
  message="";restoreConfirmation.open()
 }
 function cancelRestore(){
  var pending=restorePlan.execution
  restorePlan=({})
  restoreConfirmation.close()
  if(pending)stationBackup.cancelRestore()
 }

 ColumnLayout {
  anchors.fill:parent
  spacing:12
  Text{text:"РЕЗЕРВНА КОПІЯ";color:root.fg;font.pixelSize:21;font.bold:true}
  Text{text:"Збережіть пристрої та відеопотоки у зашифрованому файлі.";color:root.sub;wrapMode:Text.WordWrap;Layout.fillWidth:true}
  Text{text:"Пароль не зберігається. Збережіть його окремо — без нього відновити копію неможливо.";color:root.sub;wrapMode:Text.WordWrap;Layout.fillWidth:true}
  Rectangle {
   Layout.fillWidth:true
   Layout.fillHeight:true
   radius:10
   color:"#0b1420"
   border.color:root.line
   ColumnLayout {
    anchors.fill:parent
    anchors.margins:14
    spacing:10
    Text{text:"Створити копію";color:root.fg;font.bold:true}
    TextField{id:exportPassword;Layout.fillWidth:true;placeholderText:"Пароль (щонайменше 8 символів)";echoMode:TextInput.Password;inputMethodHints:Qt.ImhSensitiveData|Qt.ImhNoPredictiveText}
    TextField{id:confirmPassword;Layout.fillWidth:true;placeholderText:"Повторіть пароль";echoMode:TextInput.Password;inputMethodHints:Qt.ImhSensitiveData|Qt.ImhNoPredictiveText}
    Button{text:"Зберегти резервну копію";onClicked:root.createBackup()}
    Rectangle{Layout.fillWidth:true;height:1;color:root.line}
    Text{text:"Відновити з копії";color:root.fg;font.bold:true}
    TextField{id:restorePassword;Layout.fillWidth:true;placeholderText:"Пароль резервної копії";echoMode:TextInput.Password;inputMethodHints:Qt.ImhSensitiveData|Qt.ImhNoPredictiveText}
    Button{text:"Перевірити копію";onClicked:root.chooseRestore()}
    Button{text:"Перевірити останню автоматичну копію";onClicked:root.inspectAutomatic()}
    Text{text:"Автоматична копія зберігається лише на цій станції. Відновлення OSD з неї поки не підтримується.";color:root.sub;wrapMode:Text.WordWrap;Layout.fillWidth:true}
    Text{visible:root.message!=="";text:root.message;color:root.messageOk?"#27d59a":root.red;wrapMode:Text.WordWrap;Layout.fillWidth:true}
    Item{Layout.fillHeight:true}
   }
  }
  RowLayout {
   Layout.fillWidth:true
   Item{Layout.fillWidth:true}
   Button{text:"Закрити";flat:true;onClicked:{root.clearSensitiveFields();root.closeRequested()}}
  }
 }

 FileDialog {
  id:saveDialog
  title:"Зберегти резервну копію"
  fileMode:FileDialog.SaveFile
  nameFilters:["Резервна копія FPV Uhyliant (*.fub)"]
  defaultSuffix:"fub"
  onAccepted:root.finishExport()
  onRejected:root.clearExportPassword()
 }
 FileDialog {
  id:openDialog
  title:"Вибрати резервну копію"
  fileMode:FileDialog.OpenFile
  nameFilters:["Резервна копія FPV Uhyliant (*.fub)"]
  onAccepted:root.inspectRestore()
  onRejected:restorePassword.text=""
 }
 Popup {
  id:restoreConfirmation
  modal:true
  focus:true
  anchors.centerIn:Overlay.overlay
  width:Math.min(460,root.width-32)
  padding:18
  background:Rectangle{color:"#0d1725";border.color:root.blue;radius:12}
  contentItem:ColumnLayout {
   spacing:12
   Text{text:"Підтвердьте відновлення";color:root.fg;font.pixelSize:18;font.bold:true}
   Text{text:"У копії пристроїв: "+(root.restorePlan.deviceCount||0)+". Поточний список пристроїв і відеопотоків буде замінено.";color:root.sub;wrapMode:Text.WordWrap;Layout.fillWidth:true}
   RowLayout{Layout.fillWidth:true;Item{Layout.fillWidth:true}Button{text:"Скасувати";onClicked:root.cancelRestore()}Button{text:"Відновити";onClicked:root.confirmRestore()}}
  }
  onClosed:if(root.restorePlan.execution){stationBackup.cancelRestore();root.restorePlan=({})}
 }
}
