import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
Item {
 id:root;signal closeRequested();property color fg:"#f4f7fb";property color sub:"#8fa1b7";property color line:"#273d55";property color green:"#27d59a";property color red:"#ff6678";property color amber:"#ffb84d";property var policy:firmwareCenter.modePolicy(modeBox.currentText)
 ColumnLayout{anchors.fill:parent;spacing:10
  RowLayout{Layout.fillWidth:true;Text{text:"FIRMWARE CENTER";color:fg;font.pixelSize:22;font.bold:true}Item{Layout.fillWidth:true}Button{text:"Скинути";onClicked:{firmwareCenter.reset();firmwareExecutor.reset()}}Button{text:"Закрити";onClicked:root.closeRequested()}}
  Text{text:"Detect → Identify → Select firmware → Pre-check → Flash → Reboot → Rediscover → Verify";color:sub}
  ComboBox{id:deviceBox;Layout.fillWidth:true;model:devicesModel.items;textRole:"name";valueRole:"id"}
  RowLayout{Layout.fillWidth:true;ComboBox{id:profileBox;Layout.fillWidth:true;model:firmwareCenter.profiles}ComboBox{id:modeBox;Layout.fillWidth:true;model:firmwareCenter.modes}}
  Text{text:policy.title+" · "+policy.description;color:modeBox.currentText==="recovery-fullflash"?amber:sub;wrapMode:Text.WordWrap;Layout.fillWidth:true}
  TextField{id:imagePath;Layout.fillWidth:true;placeholderText:"Повний шлях до firmware image"}
  TextField{id:imageSha;Layout.fillWidth:true;placeholderText:"Expected SHA-256 (64 hex)"}
  RowLayout{Button{text:"Перевірити SHA-256";enabled:imagePath.text!==""&&imageSha.text!=="";onClicked:firmwareCenter.verifyImage(imagePath.text,imageSha.text)}Text{text:firmwareCenter.artifact.verified?"✓ IMAGE VERIFIED":firmwareCenter.artifact.error;color:firmwareCenter.artifact.verified?green:red}}
  RowLayout{CheckBox{id:layoutOk;text:"Flash layout verified"}CheckBox{id:recoveryOk;text:"Recovery path verified"}Button{text:"Pre-check";onClicked:firmwareCenter.precheck(deviceBox.currentValue,profileBox.currentText,modeBox.currentText,recoveryOk.checked,layoutOk.checked)}Button{text:"Підготувати execution plan";enabled:firmwareCenter.approvalMatches(deviceBox.currentValue,profileBox.currentText,modeBox.currentText);onClicked:firmwareCenter.prepareExecution(deviceBox.currentValue,profileBox.currentText,modeBox.currentText)}}
  Text{text:"Executor: "+firmwareExecutor.status.state+" · "+(firmwareExecutor.status.step||"--")+(firmwareExecutor.status.error?" · "+firmwareExecutor.status.error:"");color:firmwareExecutor.status.state==="verified"?green:(firmwareExecutor.status.state==="error"?red:sub);wrapMode:Text.WordWrap;Layout.fillWidth:true}
  Rectangle{Layout.fillWidth:true;Layout.fillHeight:true;radius:8;color:"#111d2c";border.color:firmwareCenter.executionPlan.ready?green:line;ColumnLayout{anchors.fill:parent;anchors.margins:10;Text{text:firmwareCenter.result.ready?"PRE-CHECK APPROVED":"PRE-CHECK NOT APPROVED";color:firmwareCenter.result.ready?green:red;font.bold:true}Text{text:firmwareCenter.result.reason;color:sub}Text{text:firmwareCenter.executionPlan.ready?"EXECUTION PLAN READY":"EXECUTION PLAN NOT READY";color:firmwareCenter.executionPlan.ready?green:sub;font.bold:true}Text{text:firmwareCenter.executionPlan.reason;color:sub}ListView{Layout.fillWidth:true;Layout.fillHeight:true;model:firmwareCenter.executionPlan.steps;delegate:Text{required property var modelData;width:ListView.view.width;text:(index+1)+". "+modelData;color:fg;wrapMode:Text.WordWrap}}}}
  Rectangle{Layout.fillWidth:true;height:1;color:line}
  RowLayout{Layout.fillWidth:true;Text{text:"CAMERA PRESET";color:fg;font.bold:true}ComboBox{id:presetBox;Layout.fillWidth:true;model:cameraPresets.items;textRole:"name"}Button{text:"Перевірити preset";enabled:presetBox.count>0&&deviceBox.count>0;onClicked:cameraPresets.selectForDevice("ssc30kq-imx335-fpv-v1",deviceBox.currentValue)}}
  Text{text:(cameraPresets.result.ready?"✓ ":"✕ ")+cameraPresets.result.reason+" · Video profile не застосовується firmware workflow";color:cameraPresets.result.ready?green:sub;wrapMode:Text.WordWrap;Layout.fillWidth:true}
 }
}
