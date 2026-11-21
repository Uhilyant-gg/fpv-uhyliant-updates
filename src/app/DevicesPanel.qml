import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
Item {
 id:root
 signal closeRequested()
 property color fg:"#f5f8fc";property color muted:"#8799ad";property color surface:"#0d1723";property color raised:"#132235";property color accent:"#35e0a1";property color blue:"#4195ff";property color line:"#203348";property color danger:"#ff7080"
 property var selectedFound:null;property var selectedSaved:null
 function value(v){return v===undefined||v===null||v===""?"Не визначено":v}
 function selectFound(item){selectedFound=item}
 Rectangle{anchors.fill:parent;color:"#08111b"}
 ColumnLayout{anchors.fill:parent;anchors.margins:20;spacing:14
  RowLayout{Layout.fillWidth:true
   ColumnLayout{spacing:3;Text{text:"Камери";color:fg;font.pixelSize:26;font.bold:true}Text{text:"Знайдіть і підключіть камеру без ручних мережевих налаштувань";color:muted;font.pixelSize:13}}
   Item{Layout.fillWidth:true}Button{text:"Закрити";flat:true;onClicked:root.closeRequested();HoverHint{text:"Повернутися до попереднього екрана."}}
  }
  Rectangle{Layout.fillWidth:true;height:74;radius:16;color:raised
   RowLayout{anchors.fill:parent;anchors.margins:12;spacing:10
    Button{text:devicesModel.scanning?"Скасувати":"Знайти камери";font.bold:true;Layout.preferredHeight:44;onClicked:devicesModel.scanning?devicesModel.cancelDiscovery():devicesModel.discoverOpenIPC();HoverHint{text:devicesModel.scanning?"Зупинити поточний пошук.":"Автоматично перевірити доступні безпечні приватні мережі."}}
    Button{text:"Вказати IP";flat:true;onClicked:manualPopup.open();HoverHint{text:"Перевірити камеру безпосередньо за IPv4-адресою."}}
    Item{Layout.fillWidth:true}
    ColumnLayout{visible:devicesModel.scanning||devicesModel.scanStatus!=="Готово";spacing:3;Text{text:devicesModel.scanStage;color:fg;horizontalAlignment:Text.AlignRight;Layout.fillWidth:true;font.pixelSize:12}ProgressBar{from:0;to:Math.max(1,devicesModel.scanTotal);value:devicesModel.scanDone;Layout.preferredWidth:230}Text{text:devicesModel.foundCount+" знайдено";color:muted;font.pixelSize:11;horizontalAlignment:Text.AlignRight;Layout.fillWidth:true}}
   }
  }
  SplitView{Layout.fillWidth:true;Layout.fillHeight:true;orientation:Qt.Horizontal
   Rectangle{SplitView.preferredWidth:310;SplitView.minimumWidth:250;color:surface;radius:16
    ColumnLayout{anchors.fill:parent;anchors.margins:12;spacing:10
     RowLayout{Layout.fillWidth:true;Text{text:"МОЇ КАМЕРИ";color:muted;font.bold:true;font.pixelSize:11;letterSpacing:1}Item{Layout.fillWidth:true}Text{text:devicesModel.count;color:muted}}
     ListView{id:savedList;Layout.fillWidth:true;Layout.fillHeight:true;spacing:7;clip:true;model:devicesModel.items
      delegate:Rectangle{required property var modelData;width:savedList.width;height:72;radius:12;color:selectedSaved&&selectedSaved.id===modelData.id?raised:"transparent";border.color:modelData.active?accent:"transparent"
       MouseArea{anchors.fill:parent;onClicked:selectedSaved=modelData}
       Column{anchors.fill:parent;anchors.margins:10;spacing:4;Text{text:modelData.name;color:fg;font.bold:true}Text{text:modelData.host;color:muted;font.pixelSize:12}Text{text:modelData.openipcIdentity.verified?"● OpenIPC підтверджено":"○ Ідентичність не підтверджена";color:modelData.openipcIdentity.verified?accent:muted;font.pixelSize:11}}
      }
     }
     RowLayout{Layout.fillWidth:true;Button{text:"Зробити активною";Layout.fillWidth:true;enabled:selectedSaved!==null;onClicked:devicesModel.setActive(selectedSaved.id);HoverHint{text:"Вибрати цю збережену камеру як активну."}}Button{text:"⋯";enabled:selectedSaved!==null;onClicked:savedDetails.open();HoverHint{text:"Показати відомості про збережену камеру."}}}
    }
   }
   Item{SplitView.preferredWidth:12}
   Rectangle{SplitView.fillWidth:true;color:surface;radius:16
    ColumnLayout{anchors.fill:parent;anchors.margins:14;spacing:10
     RowLayout{Layout.fillWidth:true;Text{text:"ЗНАЙДЕНІ";color:muted;font.bold:true;font.pixelSize:11;letterSpacing:1}Item{Layout.fillWidth:true}Text{text:devicesModel.discovered.length===0?"":"Оберіть камеру для продовження";color:muted;font.pixelSize:11}}
     ListView{id:foundList;Layout.fillWidth:true;Layout.fillHeight:true;spacing:8;clip:true;model:devicesModel.discovered
      delegate:Rectangle{required property var modelData;width:foundList.width;height:78;radius:13;color:selectedFound&&selectedFound.host===modelData.host?raised:"#0a141f";border.color:selectedFound&&selectedFound.host===modelData.host?blue:"transparent"
       MouseArea{anchors.fill:parent;onClicked:root.selectFound(modelData)}
       RowLayout{anchors.fill:parent;anchors.margins:12;spacing:12
        Rectangle{width:39;height:39;radius:12;color:modelData.openipc?"#15392f":"#172334";Text{anchors.centerIn:parent;text:"●";color:modelData.openipc?accent:muted}}
        ColumnLayout{Layout.fillWidth:true;spacing:3;Text{text:modelData.name;color:fg;font.bold:true;font.pixelSize:15}Text{text:modelData.host;color:muted;font.pixelSize:12}}
        Rectangle{width:150;height:28;radius:14;color:modelData.openipc?"#15392f":"#202b38";Text{anchors.centerIn:parent;text:modelData.openipc?"OpenIPC підтверджено":"Кандидат";color:modelData.openipc?accent:muted;font.pixelSize:11}}
       }
      }
     }
     ColumnLayout{visible:devicesModel.discovered.length===0&&!devicesModel.scanning;Layout.alignment:Qt.AlignHCenter|Qt.AlignVCenter;spacing:8;Text{text:"Нічого не знайдено";color:fg;font.pixelSize:18;font.bold:true;horizontalAlignment:Text.AlignHCenter;Layout.fillWidth:true}Text{text:"Запустіть пошук або вкажіть IP камери";color:muted;horizontalAlignment:Text.AlignHCenter;Layout.fillWidth:true}}
     RowLayout{Layout.fillWidth:true
      Button{text:"Додати камеру";font.bold:true;enabled:selectedFound&&selectedFound.openipc;onClicked:{devicesModel.addDiscovered(selectedFound.host,selectedFound.name,true);selectedSaved=null}HoverHint{text:"Зберегти камеру лише після підтвердження OpenIPC."}}
      Button{text:"Відомості";flat:true;enabled:selectedFound!==null;onClicked:detailsPopup.open();HoverHint{text:"Показати отримані технічні відомості та evidence."}}
      Item{Layout.fillWidth:true}
      Text{visible:selectedFound!==null;text:selectedFound&&selectedFound.r2d2?"R2D2 підтверджено":"";color:accent;font.bold:true;font.pixelSize:11}
     }
    }
   }
  }
 }
 Popup{id:manualPopup;anchors.centerIn:parent;width:Math.min(440,root.width-40);modal:true;padding:20;background:Rectangle{color:raised;radius:18;border.color:line}
  ColumnLayout{width:parent.width;spacing:13
   Text{text:"Вказати IP";color:fg;font.pixelSize:22;font.bold:true}Text{text:"Введіть адресу камери. Решту програма перевірить автоматично.";color:muted;wrapMode:Text.WordWrap;Layout.fillWidth:true}
   TextField{id:manualIp;Layout.fillWidth:true;placeholderText:"192.168.1.50";inputMethodHints:Qt.ImhFormattedNumbersOnly;HoverHint{text:"IPv4-адреса камери для прямої перевірки."}}
   Text{visible:devicesModel.manualBusy;text:"Перевіряємо камеру…";color:blue}
   Text{visible:devicesModel.manualError!=="";text:devicesModel.manualError;color:danger;wrapMode:Text.WordWrap;Layout.fillWidth:true}
   Rectangle{visible:devicesModel.manualResult.openipc===true;Layout.fillWidth:true;height:66;radius:12;color:"#15392f";Column{anchors.fill:parent;anchors.margins:10;spacing:4;Text{text:"OpenIPC підтверджено";color:accent;font.bold:true}Text{text:value(devicesModel.manualResult.identity.platform)+" · "+value(devicesModel.manualResult.identity.sensor);color:fg}}}
   RowLayout{Layout.fillWidth:true;Button{text:devicesModel.manualBusy?"Перевірка…":"Перевірити";enabled:!devicesModel.manualBusy;onClicked:devicesModel.inspectManualIp(manualIp.text);HoverHint{text:"Перевірити адресу через той самий fingerprint pipeline."}}Button{text:"Додати";enabled:devicesModel.manualResult.openipc===true;onClicked:{devicesModel.addDiscovered(devicesModel.manualResult.host,"OpenIPC "+devicesModel.manualResult.host,true);manualPopup.close()}HoverHint{text:"Зберегти підтверджену OpenIPC-камеру."}}Item{Layout.fillWidth:true}Button{text:"Закрити";flat:true;onClicked:manualPopup.close()}}
  }
 }
 Popup{id:detailsPopup;anchors.centerIn:parent;width:Math.min(540,root.width-40);modal:true;padding:20;background:Rectangle{color:raised;radius:18;border.color:line}
  ColumnLayout{width:parent.width;spacing:9;Text{text:"Відомості про камеру";color:fg;font.pixelSize:21;font.bold:true}Text{text:"Адреса  "+(selectedFound?selectedFound.host:"");color:fg}Text{text:"OpenIPC  "+(selectedFound&&selectedFound.openipc?"підтверджено":"не підтверджено");color:selectedFound&&selectedFound.openipc?accent:muted}Text{text:"Платформа / SoC  "+value(selectedFound?selectedFound.identity.platform:"")+" / "+value(selectedFound?selectedFound.identity.soc:"");color:fg}Text{text:"Сенсор  "+value(selectedFound?selectedFound.identity.sensor:"");color:fg}Text{text:"Прошивка  "+value(selectedFound?selectedFound.identity.firmware:"");color:fg}Text{text:"Majestic  "+value(selectedFound?selectedFound.identity.majestic:"");color:fg}Text{text:"Підтвердження  "+(selectedFound?selectedFound.evidence.join("; "):"");color:muted;wrapMode:Text.WordWrap;Layout.fillWidth:true}Button{text:"Закрити";Layout.alignment:Qt.AlignRight;onClicked:detailsPopup.close()}}
 }
 Popup{id:savedDetails;anchors.centerIn:parent;width:Math.min(500,root.width-40);modal:true;padding:20;background:Rectangle{color:raised;radius:18;border.color:line}
  ColumnLayout{width:parent.width;spacing:9;Text{text:selectedSaved?selectedSaved.name:"Камера";color:fg;font.pixelSize:21;font.bold:true}Text{text:selectedSaved?selectedSaved.host:"";color:muted}Text{text:selectedSaved&&selectedSaved.openipcIdentity.verified?"OpenIPC підтверджено":"OpenIPC не підтверджено";color:selectedSaved&&selectedSaved.openipcIdentity.verified?accent:muted}Text{visible:selectedSaved&&selectedSaved.openipcIdentity.verified;text:"Платформа / SoC  "+value(selectedSaved?selectedSaved.openipcIdentity.platform:"")+" / "+value(selectedSaved?selectedSaved.openipcIdentity.soc:"");color:fg}Text{visible:selectedSaved&&selectedSaved.openipcIdentity.verified;text:"Сенсор  "+value(selectedSaved?selectedSaved.openipcIdentity.sensor:"");color:fg}Button{text:"Закрити";Layout.alignment:Qt.AlignRight;onClicked:savedDetails.close()}}
 }
}
