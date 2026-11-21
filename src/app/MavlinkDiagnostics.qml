import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
ScrollView {
 id:root
 property var t: mavlinkRuntime.telemetry
 property var l: t.link||({})
 clip:true
 ColumnLayout {
  width:root.availableWidth;spacing:8
  Label{text:"IDENTITY";font.bold:true;color:"#8fa1b7"}
  GridLayout{columns:4;Layout.fillWidth:true
   Label{text:"System / Component";color:"#8fa1b7"} Label{text:(t.systemId??"--")+" / "+(t.componentId??"--");color:"#f4f7fb"}
   Label{text:"Vehicle";color:"#8fa1b7"} Label{text:t.vehicleType||"--";color:"#f4f7fb"}
   Label{text:"Autopilot";color:"#8fa1b7"} Label{text:t.autopilotType||"--";color:"#f4f7fb"}
   Label{text:"System state";color:"#8fa1b7"} Label{text:t.systemStatus||"--";color:"#f4f7fb"}
   Label{text:"MAVLink";color:"#8fa1b7"} Label{text:t.mavlinkVersion===undefined?"--":String(t.mavlinkVersion);color:"#f4f7fb"}
   Label{text:"Flight software";color:"#8fa1b7"} Label{text:t.flightSoftwareVersion||"not broadcast";color:"#f4f7fb"}
   Label{text:"Vendor / Product";color:"#8fa1b7"} Label{text:(t.vendorId??"--")+" / "+(t.productId??"--");color:"#f4f7fb"}
   Label{text:"UID";color:"#8fa1b7"} Label{text:t.vehicleUid||"not broadcast";color:"#f4f7fb";elide:Text.ElideMiddle;Layout.fillWidth:true}
  }
  Rectangle{Layout.fillWidth:true;height:1;color:"#273d55"}
  Label{text:"LINK DIAGNOSTICS";font.bold:true;color:"#8fa1b7"}
  GridLayout{columns:4;Layout.fillWidth:true
   Label{text:"Message rate";color:"#8fa1b7"} Label{text:l.messageRate===undefined?"--":Number(l.messageRate).toFixed(1)+" msg/s";color:"#f4f7fb"}
   Label{text:"Last packet";color:"#8fa1b7"} Label{text:l.lastPacketAge===undefined||l.lastPacketAge===null?"--":Number(l.lastPacketAge).toFixed(2)+" s";color:"#f4f7fb"}
   Label{text:"Received";color:"#8fa1b7"} Label{text:l.messagesReceived??"--";color:"#f4f7fb"}
   Label{text:"Estimated lost";color:"#8fa1b7"} Label{text:(l.packetsLost??"--")+(l.packetLossPercent===undefined?"":" ("+Number(l.packetLossPercent).toFixed(2)+"%)");color:(l.packetLossPercent||0)>5?"#ff6678":"#f4f7fb"}
   Label{text:"Bad data";color:"#8fa1b7"} Label{text:l.badData??"--";color:(l.badData||0)>0?"#ffb84d":"#f4f7fb"}
   Label{text:"Comm errors";color:"#8fa1b7"} Label{text:t.communicationErrors??"--";color:"#f4f7fb"}
   Label{text:"RSSI source";color:"#8fa1b7"} Label{text:t.rssiSource||"--";color:"#f4f7fb"}
   Label{text:"Local / Remote RSSI";color:"#8fa1b7"} Label{text:(t.rssi??"--")+" / "+(l.remoteRssi??"--");color:"#f4f7fb"}
   Label{text:"Local / Remote noise";color:"#8fa1b7"} Label{text:(l.localNoise??"--")+" / "+(l.remoteNoise??"--");color:"#f4f7fb"}
   Label{text:"RX / fixed errors";color:"#8fa1b7"} Label{text:(l.rxErrors??"--")+" / "+(l.fixedErrors??"--");color:"#f4f7fb"}
   Label{text:"TX buffer";color:"#8fa1b7"} Label{text:l.txBuffer===undefined||l.txBuffer===null?"--":l.txBuffer+"%";color:"#f4f7fb"}
   Label{text:"Controller load";color:"#8fa1b7"} Label{text:t.controllerLoad===undefined||t.controllerLoad===null?"--":Number(t.controllerLoad).toFixed(1)+"%";color:"#f4f7fb"}
  }
  Label{text:"Packet loss is estimated from MAVLink sequence gaps per source component. RADIO_STATUS fields appear only when the link broadcasts them.";color:"#8fa1b7";wrapMode:Text.WordWrap;Layout.fillWidth:true}
 }
}
