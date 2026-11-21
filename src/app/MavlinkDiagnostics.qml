import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ScrollView {
 id:root;property var t:mavlinkRuntime.telemetry;property var l:t.link||({});clip:true
 function healthUa(value){if(value===undefined||value===null||value==="")return "недоступно";var states={"ok":"справно","connected":"підключено","disconnected":"відключено","stale":"застаріло","unknown":"невідомо","unavailable":"недоступно","error":"помилка"};return states[value]||value}
 ColumnLayout {width:root.availableWidth;spacing:8
  Label{text:"ІДЕНТИФІКАЦІЯ";font.bold:true;color:"#8fa1b7"}
  GridLayout{columns:4;Layout.fillWidth:true
   Label{text:"Система / компонент";color:"#8fa1b7"} Label{text:(t.systemId??"--")+" / "+(t.componentId??"--");color:"#f4f7fb"}
   Label{text:"Літальний апарат";color:"#8fa1b7"} Label{text:t.vehicleType||"--";color:"#f4f7fb"}
   Label{text:"Автопілот";color:"#8fa1b7"} Label{text:t.autopilotType||"--";color:"#f4f7fb"}
   Label{text:"Стан системи";color:"#8fa1b7"} Label{text:t.systemStatus||"--";color:"#f4f7fb"}
   Label{text:"Поле MAVLink";color:"#8fa1b7"} Label{text:t.mavlinkVersion===undefined?"--":String(t.mavlinkVersion);color:"#f4f7fb"}
   Label{text:"Польотне ПЗ";color:"#8fa1b7"} Label{text:t.flightSoftwareVersion||"не передається";color:"#f4f7fb"}
   Label{text:"Виробник / продукт";color:"#8fa1b7"} Label{text:(t.vendorId??"--")+" / "+(t.productId??"--");color:"#f4f7fb"}
   Label{text:"UID";color:"#8fa1b7"} Label{text:t.vehicleUid||"не передається";color:"#f4f7fb";elide:Text.ElideMiddle;Layout.fillWidth:true}
  }
  Rectangle{Layout.fillWidth:true;height:1;color:"#273d55"}
  Label{text:"ДІАГНОСТИКА КАНАЛУ";font.bold:true;color:"#8fa1b7"}
  GridLayout{columns:4;Layout.fillWidth:true
   Label{text:"Стан";color:"#8fa1b7"} Label{text:healthUa(t.health);color:t.connected===true?"#27d59a":(t.connected===false?"#ff6678":"#8fa1b7")}
   Label{text:"Частота повідомлень";color:"#8fa1b7"} Label{text:l.messageRate===undefined?"--":Number(l.messageRate).toFixed(1)+" повід./с";color:"#f4f7fb"}
   Label{text:"Останній пакет";color:"#8fa1b7"} Label{text:l.lastPacketAge===undefined||l.lastPacketAge===null?"--":Number(l.lastPacketAge).toFixed(2)+" с";color:"#f4f7fb"}
   Label{text:"Отримано";color:"#8fa1b7"} Label{text:l.messagesReceived??"--";color:"#f4f7fb"}
   Label{text:"Оцінка втрат";color:"#8fa1b7"} Label{text:(l.packetsLost??"--")+(l.packetLossPercent===undefined?"":" ("+Number(l.packetLossPercent).toFixed(2)+"%)");color:(l.packetLossPercent||0)>5?"#ff6678":"#f4f7fb"}
   Label{text:"Некоректні дані";color:"#8fa1b7"} Label{text:l.badData??"--";color:(l.badData||0)>0?"#ffb84d":"#f4f7fb"}
   Label{text:"Помилки зв’язку";color:"#8fa1b7"} Label{text:t.communicationErrors??"--";color:"#f4f7fb"}
   Label{text:"Джерело RSSI";color:"#8fa1b7"} Label{text:t.rssiSource||"--";color:"#f4f7fb"}
   Label{text:"Локальний / віддалений RSSI";color:"#8fa1b7"} Label{text:(t.rssi??"--")+" / "+(l.remoteRssi??"--");color:"#f4f7fb"}
   Label{text:"Локальний / віддалений шум";color:"#8fa1b7"} Label{text:(l.localNoise??"--")+" / "+(l.remoteNoise??"--");color:"#f4f7fb"}
   Label{text:"Помилки RX / виправлені";color:"#8fa1b7"} Label{text:(l.rxErrors??"--")+" / "+(l.fixedErrors??"--");color:"#f4f7fb"}
   Label{text:"Буфер TX";color:"#8fa1b7"} Label{text:l.txBuffer===undefined||l.txBuffer===null?"--":l.txBuffer+"%";color:"#f4f7fb"}
   Label{text:"Завантаження контролера";color:"#8fa1b7"} Label{text:t.controllerLoad===undefined||t.controllerLoad===null?"--":Number(t.controllerLoad).toFixed(1)+"%";color:"#f4f7fb"}
  }
  Label{text:"Втрати оцінюються за розривами послідовності MAVLink. У маршрутизованих або резервованих мережах це лише діагностична оцінка.";color:"#8fa1b7";wrapMode:Text.WordWrap;Layout.fillWidth:true}
 }
}
