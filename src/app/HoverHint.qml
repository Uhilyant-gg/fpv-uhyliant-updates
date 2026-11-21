import QtQuick
import QtQuick.Controls

Item {
 id:root
 property string text:""
 property Item target:parent
 property int delay:5000
 anchors.fill:target
 z:1000
 HoverHandler{id:hover;acceptedDevices:PointerDevice.Mouse|PointerDevice.TouchPad}
 Timer{id:showTimer;interval:root.delay;repeat:false;onTriggered:tip.open()}
 onVisibleChanged:if(!visible){showTimer.stop();tip.close()}
 Connections{target:hover;function onHoveredChanged(){if(hover.hovered&&root.visible&&root.text!==""){showTimer.restart()}else{showTimer.stop();tip.close()}}}
 ToolTip{id:tip;text:root.text;delay:0;timeout:0;visible:false}
}
