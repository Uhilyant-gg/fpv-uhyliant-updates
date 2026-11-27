import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
Item {
 id:root;signal closeRequested();property color fg:"#f4f7fb";property color sub:"#8fa1b7";property color line:"#273d55";property color green:"#27d59a";property color red:"#ff6678";property color amber:"#ffb84d";property var hw:firmwareCenter.acquisitionIdentity(deviceBox.currentValue||"");property var selectedFirmware:firmwareAcquisition.status.selection||({});property var sessionResult:firmwareUpdateSession.result;property var hardwareReady:hardwareE2ERuntime.readiness;property bool advanced:false;property string automaticProfile:firmwareCenter.compatibleProfile(deviceBox.currentValue||"")
 function clearSensitive(){passwordField.text="";cameraCredentials.clear()} function closePanel(){clearSensitive();firmwareUpdateSession.disableTransport();hardwareE2ERuntime.selectDevice("");root.closeRequested()}
 function bindDevice(){hardwareE2ERuntime.selectDevice(deviceBox.currentValue||"")}
 function selectDevice(deviceId){var items=devicesModel.items||[];for(var i=0;i<items.length;i++){if(items[i].id===deviceId){deviceBox.currentIndex=i;bindDevice();return true}}return false}
 function activeDevice(){var items=devicesModel.items||[];for(var i=0;i<items.length;i++){if(items[i].onboardingState==="pending-firmware"){selectDevice(items[i].id);return}}for(var n=0;n<items.length;n++){if(items[n].active===true){selectDevice(items[n].id);return}}bindDevice()}
 function prepareAutomatic(){if(!deviceBox.currentValue||firmwareExecutor.busy)return;firmwareUpdateSession.disableTransport();firmwareCenter.reset();bindDevice();if(firmwareAcquisition.prepareRecommended(deviceBox.currentValue)){firmwareCenter.prepareAutomaticUpgrade(deviceBox.currentValue)}}
 function phase(){var s=firmwareExecutor.status.state;if(s==="executing")return "Оновлення";if(s==="reboot-pending")return "Перезапуск";if(s==="rediscovering")return "Перевірка";if(firmwareAcquisition.status.state==="loading")return "Підготовка";if(firmwareAcquisition.status.state==="downloading")return "Завантаження";return ""}
 function stateText(){if(sessionResult.state==="verified"){var streams=sessionResult.verification.streams||[];return streams.length?"Камеру оновлено до "+sessionResult.observedFirmware+". Відеопотік перевірено, камера додана на головний екран.":"Прошивку оновлено до "+sessionResult.observedFirmware+", але відеопотік не підтверджено. Камера залишиться поза головним екраном до повторної перевірки."}if(sessionResult.state==="error"||sessionResult.state==="blocked")return sessionResult.reason||"Оновлення не завершено";if(firmwareAcquisition.status.reason)return firmwareAcquisition.status.reason;if(selectedFirmware.reason)return selectedFirmware.reason;if(firmwareCenter.executionPlan.ready)return "Все готово. Оновлення запуститься лише після вашого підтвердження.";if(!hw.ready)return "Потрібна підтверджена OpenIPC-камера зі спостереженими platform і sensor.";if(automaticProfile==="")return "Для цієї спостереженої платформи та сенсора немає однозначного підтримуваного профілю.";return "Перевірте доступне оновлення."}
 Component.onCompleted:activeDevice()
 ScrollView{anchors.fill:parent;clip:true
  ColumnLayout{width:root.width;spacing:12
   RowLayout{Layout.fillWidth:true;Text{text:"ЦЕНТР ПРОШИВКИ";color:fg;font.pixelSize:22;font.bold:true}Item{Layout.fillWidth:true}Button{text:"Закрити";enabled:!firmwareExecutor.busy;onClicked:root.closePanel()}}
   Text{text:"Безпечне автоматичне оновлення OpenIPC-камери";color:sub;Layout.fillWidth:true;wrapMode:Text.WordWrap}
   Rectangle{Layout.fillWidth:true;implicitHeight:cameraCard.implicitHeight+24;radius:10;color:"#111d2c";border.color:hw.ready?green:line
    ColumnLayout{id:cameraCard;anchors.fill:parent;anchors.margins:12;spacing:7
     Text{text:"КАМЕРА";color:sub;font.bold:true}
     ComboBox{id:deviceBox;Layout.fillWidth:true;model:devicesModel.items;textRole:"name";valueRole:"id";enabled:!firmwareExecutor.busy;onCurrentValueChanged:root.bindDevice()}
     Text{text:deviceBox.currentText||"Активну камеру не вибрано";color:fg;font.pixelSize:18;font.bold:true}
     Text{text:"OpenIPC: "+(hw.verifiedOpenIPC?"підтверджено":"не підтверджено");color:hw.verifiedOpenIPC?green:amber}
     Text{text:"Платформа / сенсор: "+(hw.ready?(hw.platform+" / "+hw.sensor):"не спостережено");color:hw.ready?fg:sub}
     Text{text:"Встановлена firmware: "+(firmwareCenter.upgradeReadiness(deviceBox.currentValue).currentFirmware||"не спостережено");color:sub}
     Button{text:"Знайти або вибрати камеру";visible:!deviceBox.currentValue||!hw.ready;enabled:!firmwareExecutor.busy;onClicked:root.closeRequested()}
    }
   }
   Rectangle{Layout.fillWidth:true;implicitHeight:updateCard.implicitHeight+24;radius:10;color:"#111d2c";border.color:firmwareCenter.executionPlan.ready?green:line
    ColumnLayout{id:updateCard;anchors.fill:parent;anchors.margins:12;spacing:8
     Text{text:"ОНОВЛЕННЯ";color:sub;font.bold:true}
     Text{text:selectedFirmware.ready?("Доступна firmware: "+selectedFirmware.artifact.build):"Доступна firmware: ще не визначено";color:selectedFirmware.ready?fg:sub;font.pixelSize:17;font.bold:true}
     Text{text:stateText();color:sessionResult.state==="verified"?((sessionResult.verification.streams||[]).length?green:amber):(sessionResult.state==="error"||sessionResult.state==="blocked"?red:sub);Layout.fillWidth:true;wrapMode:Text.WordWrap}
     Button{text:"Перевірити оновлення";Layout.fillWidth:true;enabled:hw.ready&&automaticProfile!==""&&!firmwareExecutor.busy;onClicked:prepareAutomatic()}
     Text{text:phase();visible:phase()!=="";color:green;font.bold:true}
     RowLayout{Layout.fillWidth:true;visible:firmwareExecutor.busy||firmwareExecutor.status.state==="reboot-pending"||firmwareExecutor.status.state==="rediscovering";Repeater{model:["Підготовка","Завантаження","Оновлення","Перезапуск","Перевірка"];delegate:Text{required property var modelData;text:modelData;color:modelData===phase()?green:sub;font.bold:modelData===phase()}}}
    }
   }
   Rectangle{Layout.fillWidth:true;implicitHeight:authColumn.implicitHeight+24;radius:10;color:"#111d2c";border.color:hardwareReady.ready?green:line;visible:firmwareCenter.executionPlan.ready||hardwareReady.checks.credentialsPresent
    ColumnLayout{id:authColumn;anchors.fill:parent;anchors.margins:12;spacing:8
     Text{text:"ПІДТВЕРДЖЕННЯ ДОСТУПУ";color:sub;font.bold:true}
     Text{text:"Дані потрібні лише для цього сеансу й не зберігаються.";color:sub;Layout.fillWidth:true;wrapMode:Text.WordWrap}
     TextField{id:usernameField;Layout.fillWidth:true;placeholderText:"Логін (зазвичай root)";text:cameraCredentials.username;enabled:!firmwareExecutor.busy;onEditingFinished:cameraCredentials.username=text}
     TextField{id:passwordField;Layout.fillWidth:true;placeholderText:"Пароль";echoMode:TextInput.Password;inputMethodHints:Qt.ImhSensitiveData|Qt.ImhNoPredictiveText;enabled:!firmwareExecutor.busy;onTextChanged:cameraCredentials.password=text}
     CheckBox{text:"Підтверджую оновлення вибраної камери";checked:hardwareE2ERuntime.updateConfirmed;enabled:!firmwareExecutor.busy;onToggled:hardwareE2ERuntime.confirmDeviceUpdate(checked);HoverHint{text:"Ця позначка дозволяє оновити вибрану камеру. Вона не змушує програму довіряти невідомому пристрою: якщо з'єднання не перевірено, оновлення зупиниться."}}
     Button{text:sessionResult.enabled?"Доступ підтверджено":"Підтвердити доступ";Layout.fillWidth:true;enabled:hardwareReady.ready&&!sessionResult.enabled&&!firmwareExecutor.busy&&cameraCredentials.username!==""&&passwordField.text!=="";onClicked:firmwareUpdateSession.enableAuthenticatedTransport(cameraCredentials,hardwareE2ERuntime)}
    }
   }
   Button{text:"Оновити камеру";Layout.fillWidth:true;highlighted:true;enabled:sessionResult.enabled&&firmwareCenter.executionPlan.ready&&automaticProfile!==""&&!firmwareExecutor.busy;onClicked:firmwareUpdateSession.execute(deviceBox.currentValue,automaticProfile,"upgrade")}
   Button{text:"Перевірити зараз";Layout.fillWidth:true;visible:firmwareExecutor.status.state==="reboot-pending";enabled:visible;onClicked:firmwareUpdateSession.verifyAfterReboot()}
   Button{text:advanced?"Сховати додатково":"Додатково";flat:true;onClicked:advanced=!advanced}
   ColumnLayout{Layout.fillWidth:true;visible:advanced;spacing:8
    Text{text:"РУЧНИЙ ШЛЯХ ЛОКАЛЬНОГО ОБРАЗУ";color:amber;font.bold:true}
    Text{text:"Це окремий експертний сценарій, не рекомендоване автоматичне оновлення.";color:sub;Layout.fillWidth:true;wrapMode:Text.WordWrap}
    TextField{id:imagePath;Layout.fillWidth:true;placeholderText:"Повний шлях до локального образу";enabled:!firmwareExecutor.busy}
    TextField{id:imageSha;Layout.fillWidth:true;placeholderText:"Очікуваний SHA-256";enabled:!firmwareExecutor.busy}
    Button{text:"Перевірити локальний образ";enabled:imagePath.text!==""&&imageSha.text!==""&&!firmwareExecutor.busy;onClicked:firmwareCenter.verifyImage(imagePath.text,imageSha.text)}
    Text{text:firmwareCenter.artifact.verified?"Образ перевірено":firmwareCenter.artifact.error;color:firmwareCenter.artifact.verified?green:red;Layout.fillWidth:true;wrapMode:Text.WordWrap}
    Rectangle{Layout.fillWidth:true;height:1;color:line}
    Text{text:"Технічний вибір каталогу";color:fg;font.bold:true}
    RowLayout{Layout.fillWidth:true;ComboBox{id:channelBox;Layout.fillWidth:true;model:firmwareAcquisition.channels}ComboBox{id:variantBox;Layout.fillWidth:true;model:firmwareAcquisition.variants(hw.platform||"",hw.sensor||"",channelBox.currentText)}ComboBox{id:buildBox;Layout.fillWidth:true;model:firmwareAcquisition.builds(hw.platform||"",hw.sensor||"",channelBox.currentText,variantBox.currentText)}}
    Button{text:"Застосувати явний вибір";enabled:hw.ready&&!firmwareExecutor.busy;onClicked:{firmwareAcquisition.selectForDevice(deviceBox.currentValue,channelBox.currentText,buildBox.currentText,variantBox.currentText);firmwareAcquisition.downloadSelected(deviceBox.currentValue)}}
    Text{text:"Варіант вибирається явно, якщо офіційний каталог не дає однозначної рекомендації. Збірка вибирається явно лише в цьому ручному режимі.";color:sub;Layout.fillWidth:true;wrapMode:Text.WordWrap}
    Button{text:"Скинути сеанс";enabled:!firmwareExecutor.busy;onClicked:{clearSensitive();firmwareUpdateSession.disableTransport();hardwareE2ERuntime.reset();cameraCredentials.reset();firmwareAcquisition.reset();firmwareCenter.reset();firmwareUpdateSession.reset()}}
   }
  }
 }
}
