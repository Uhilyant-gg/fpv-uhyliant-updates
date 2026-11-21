import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
Item {
 id:root;signal closeRequested();property color fg:"#f4f7fb";property color sub:"#8fa1b7";property color line:"#273d55";property color green:"#27d59a";property color red:"#ff6678"
 ColumnLayout{anchors.fill:parent;spacing:10
  RowLayout{Layout.fillWidth:true;Text{text:"FIRMWARE CENTER";color:fg;font.pixelSize:22;font.bold:true}Item{Layout.fillWidth:true}Button{text:"Скинути";onClicked:firmwareCenter.reset()}Button{text:"Закрити";onClicked:root.closeRequested()}}
  Text{text:"Detect → Identify → Select firmware → Pre-check → Flash → Reboot → Rediscover → Verify";color:sub}
  ComboBox{id:deviceBox;Layout.fillWidth:true;model:devicesModel.items;textRole:"name";valueRole:"id"}
  RowLayout{Layout.fillWidth:true;ComboBox{id:profileBox;Layout.fillWidth:true;model:firmwareCenter.profiles}ComboBox{id:modeBox;Layout.fillWidth:true;model:firmwareCenter.modes}}
  Text{text:"SSC30KQ / IMX335 is the first explicit compatibility profile. Unknown hardware remains blocked.";color:sub;wrapMode:Text.WordWrap;Layout.fillWidth:true}
  Text{text:"Firmware image";color:fg;font.bold:true}
  TextField{id:imagePath;Layout.fillWidth:true;placeholderText:"Повний шлях до firmware image"}
  TextField{id:imageSha;Layout.fillWidth:true;placeholderText:"Expected SHA-256 (64 hex)"}
  RowLayout{Layout.fillWidth:true;Button{text:"Перевірити SHA-256";enabled:imagePath.text!==""&&imageSha.text!=="";onClicked:firmwareCenter.verifyImage(imagePath.text,imageSha.text)}Text{text:firmwareCenter.artifact.verified?"✓ IMAGE VERIFIED":(firmwareCenter.artifact.error||"IMAGE NOT VERIFIED");color:firmwareCenter.artifact.verified?green:red;Layout.fillWidth:true}}
  Text{text:firmwareCenter.artifact.sha256?"SHA-256: "+firmwareCenter.artifact.sha256:"SHA-256: --";color:sub;elide:Text.ElideMiddle;Layout.fillWidth:true}
  Text{text:firmwareCenter.artifact.size>0?"Size: "+firmwareCenter.artifact.size+" bytes":"Size: --";color:sub}
  CheckBox{id:layoutOk;text:"Flash layout verified"}
  CheckBox{id:recoveryOk;text:"Recovery path verified"}
  Button{text:"Виконати Pre-check";enabled:deviceBox.count>0&&profileBox.count>0&&modeBox.count>0;onClicked:firmwareCenter.precheck(deviceBox.currentValue,profileBox.currentText,modeBox.currentText,recoveryOk.checked,layoutOk.checked)}
  Rectangle{Layout.fillWidth:true;Layout.fillHeight:true;radius:8;color:"#111d2c";border.color:firmwareCenter.result.ready?green:line;ColumnLayout{anchors.fill:parent;anchors.margins:10;Text{text:firmwareCenter.result.ready?"PRE-CHECK PASSED":"PRE-CHECK NOT READY";color:firmwareCenter.result.ready?green:red;font.bold:true}Text{text:firmwareCenter.result.reason;color:sub}ListView{Layout.fillWidth:true;Layout.fillHeight:true;clip:true;model:firmwareCenter.result.checks;delegate:Text{required property var modelData;width:ListView.view.width;text:(modelData.ok?"✓ ":"✕ ")+modelData.name+" · "+modelData.detail;color:modelData.ok?green:red;wrapMode:Text.WordWrap}}}}
  Text{text:"Destructive flashing не виконується. Пройти pre-check можна лише з фактично перевіреним firmware image, hardware identity, flash layout та recovery path.";color:sub;wrapMode:Text.WordWrap;Layout.fillWidth:true}
 }
}
