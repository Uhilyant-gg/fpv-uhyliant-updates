import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
Item {
 id:root
 signal openDevices();signal openFirmware();signal openUpdate();signal openDiagnostics();signal connectDevice(string deviceId)
 function canEnterFpv(deviceId){if(!deviceId)return false;for(var i=0;i<devicesModel.items.length;i++)if(devicesModel.items[i].id===deviceId){var streams=devicesModel.streams;for(var n=0;n<streams.length;n++)if(streams[n].device_id===deviceId&&streams[n].enabled===true)return true;return false}return false}
 Rectangle{anchors.fill:parent;color:UiTokens.canvas}
 ColumnLayout{anchors.fill:parent;anchors.margins:UiTokens.space24;spacing:UiTokens.space16
  RowLayout{Layout.fillWidth:true;spacing:UiTokens.space12
   Text{text:"ФПВ УХИЛЯНТ";color:UiTokens.foreground;font.family:UiTokens.fontFamily;font.pixelSize:UiTokens.fontTitle;font.weight:Font.DemiBold}
   Text{text:"Версія "+updater.currentVersion;color:UiTokens.secondary;font.family:UiTokens.fontFamily;font.pixelSize:UiTokens.fontCaption}
   Button{visible:updater.updateState==="available"||updater.updateState==="ready";text:updater.updateState==="ready"?"Встановити "+updater.availableVersion:"Оновити до "+updater.availableVersion;font.bold:true;onClicked:root.openUpdate();HoverHint{text:"Доступна нова версія програми."}}
   Text{visible:updater.busy;text:updater.updateStatus;color:UiTokens.secondary;font.family:UiTokens.fontFamily;font.pixelSize:UiTokens.fontCaption}
   Item{Layout.fillWidth:true}
   Button{text:"Прошивка";flat:true;onClicked:root.openFirmware();HoverHint{text:"Безпечне керування прошивкою камери."}}
   Button{text:"Діагностика";flat:true;onClicked:root.openDiagnostics();HoverHint{text:"Переглянути фактично доступну діагностику."}}
  }
  RowLayout{Layout.fillWidth:true;spacing:UiTokens.space8
   Text{text:"Камери";color:UiTokens.foreground;font.family:UiTokens.fontFamily;font.pixelSize:UiTokens.fontSection;font.weight:Font.DemiBold}
   Text{text:devicesModel.count?devicesModel.count+" збережено":"немає збережених";color:UiTokens.secondary;font.family:UiTokens.fontFamily;font.pixelSize:UiTokens.fontCaption}
   Item{Layout.fillWidth:true}
   Button{text:"Знайти / додати";Layout.preferredHeight:UiTokens.controlHeight;font.bold:true;onClicked:root.openDevices();HoverHint{text:"Знайти камери автоматично або вказати IP вручну."}}
  }
  Rectangle{Layout.fillWidth:true;Layout.fillHeight:true;radius:UiTokens.radiusCard;color:UiTokens.surface;border.color:UiTokens.line
   ListView{id:list;anchors.fill:parent;anchors.margins:UiTokens.space8;clip:true;spacing:UiTokens.space4;model:devicesModel.items
    delegate:Rectangle{required property var modelData;width:list.width;height:64;radius:UiTokens.radiusControl;color:mouse.hovered?UiTokens.elevated:"transparent";border.color:modelData.active?UiTokens.ready:"transparent"
     HoverHandler{id:mouse}
     RowLayout{anchors.fill:parent;anchors.margins:UiTokens.space12;spacing:UiTokens.space12
      Rectangle{width:32;height:32;radius:UiTokens.radiusSmall;color:modelData.openipcIdentity.verified?UiTokens.interactive:UiTokens.elevated;Text{anchors.centerIn:parent;text:"●";color:modelData.openipcIdentity.verified?UiTokens.ready:UiTokens.unknown;font.pixelSize:12}}
      ColumnLayout{Layout.fillWidth:true;spacing:UiTokens.space4;Text{text:modelData.name;color:UiTokens.foreground;font.family:UiTokens.fontFamily;font.bold:true;font.pixelSize:UiTokens.fontControl}Text{text:modelData.host+(modelData.openipcIdentity.verified?" · OpenIPC":"");color:UiTokens.secondary;font.family:UiTokens.fontFamily;font.pixelSize:UiTokens.fontCaption}}
      Text{visible:modelData.active;text:"АКТИВНА";color:UiTokens.ready;font.family:UiTokens.fontFamily;font.bold:true;font.pixelSize:UiTokens.fontCaption}
      Button{text:"FPV";enabled:root.canEnterFpv(modelData.id);onClicked:root.connectDevice(modelData.id);HoverHint{text:"Відкрити FPV для цієї камери."}}
     }
    }
    Column{anchors.centerIn:parent;visible:devicesModel.count===0;spacing:UiTokens.space8
     Text{anchors.horizontalCenter:parent.horizontalCenter;text:"Камер ще немає";color:UiTokens.foreground;font.family:UiTokens.fontFamily;font.pixelSize:UiTokens.fontSection;font.weight:Font.DemiBold}
     Text{anchors.horizontalCenter:parent.horizontalCenter;text:"Натисніть «Знайти / додати»";color:UiTokens.secondary;font.family:UiTokens.fontFamily;font.pixelSize:UiTokens.fontBody}
    }
   }
  }
  Component.onCompleted:updater.check()
 }
}
