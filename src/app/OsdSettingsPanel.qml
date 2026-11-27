import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
 id: root
 signal closeRequested()
 property var elementOptions: [
  {name:"link", label:"Стан зв’язку"},
  {name:"arm", label:"Стан ARM"},
  {name:"mode", label:"Режим польоту"},
  {name:"battery", label:"Акумулятор"},
  {name:"gps", label:"GPS і супутники"},
  {name:"altitude", label:"Висота"},
  {name:"speed", label:"Швидкість"},
  {name:"heading", label:"Напрямок"},
  {name:"video", label:"Стан відео"},
  {name:"homeDistance", label:"Відстань до точки повернення"},
  {name:"reticle", label:"Приціл"},
  {name:"horizon", label:"Штучний горизонт"}
 ]

 Rectangle {
  anchors.fill: parent
  color: "transparent"
 }

 ColumnLayout {
  anchors.fill: parent
  spacing: 14

  RowLayout {
   Layout.fillWidth: true
   Text {
    text: "Налаштування OSD станції"
    color: "#f4f7fb"
    font.pixelSize: 20
    font.bold: true
    Layout.fillWidth: true
   }
   Button { text: "Закрити"; onClicked: root.closeRequested() }
  }

  Text {
   text: "OSD станції — окремий шар поверх відео. Відео з польотника та його власне OSD не змінюються."
   color: "#aebdd0"
   wrapMode: Text.WordWrap
   Layout.fillWidth: true
  }

  RowLayout {
   Layout.fillWidth: true
   Layout.fillHeight: true
   spacing: 18

   ScrollView {
    Layout.preferredWidth: 300
    Layout.fillHeight: true
    contentWidth: availableWidth
    clip: true
    ColumnLayout {
     width: parent.width
     spacing: 10

     Switch { text: "Показувати OSD"; checked: station.osdEnabled; onToggled: station.setOSDEnabled(checked) }
     Text { text: "Оберіть потрібні елементи. Перетягування прилипає до сітки з кроком 5%."; color: "#dce6f2"; wrapMode: Text.WordWrap; Layout.fillWidth: true }

     Text { text: "Прозорість підкладки: " + Math.round((1 - station.osdOpacity) * 100) + "%"; color: "#dce6f2"; font.bold: true }
     Slider {
      id: opacitySlider
      objectName: "osdTransparencySlider"
      Layout.fillWidth: true
      from: 0
      to: 1
      stepSize: 0.05
      value: 1 - station.osdOpacity
      onMoved: station.setOSDStyle(1 - value, scaleSlider.value)
     }

     Text { text: "Розмір тексту: " + Math.round(station.osdScale * 100) + "%"; color: "#dce6f2"; font.bold: true }
     Slider {
      id: scaleSlider
      Layout.fillWidth: true
      from: 0.85
      to: 1.3
      stepSize: 0.05
      value: station.osdScale
      onMoved: station.setOSDStyle(1 - opacitySlider.value, value)
     }

     Text { text: "Елементи"; color: "#dce6f2"; font.bold: true; font.pixelSize: 15 }
     Repeater {
      model: root.elementOptions
      CheckBox {
       required property var modelData
       objectName: "osd-toggle-" + modelData.name
       Layout.fillWidth: true
       text: modelData.label
       checked: station.osdEnabledElements[modelData.name] === true
       onToggled: station.setOSDElementEnabled(modelData.name, checked)
      }
     }
     Button {
      text: "Стандартні налаштування"
      Layout.fillWidth: true
      onClicked: station.resetOSDStyle()
     }
    }
   }

   ColumnLayout {
    Layout.fillWidth: true
    Layout.fillHeight: true
    spacing: 6
    Text { text: "Попередній перегляд · екран польоту"; color: "#dce6f2"; font.bold: true }
    Rectangle {
     id: preview
     Layout.fillWidth: true
     Layout.fillHeight: true
     Layout.minimumHeight: 150
     gradient: Gradient {
      GradientStop { position: 0; color: "#355d78" }
      GradientStop { position: 0.55; color: "#9db4b1" }
      GradientStop { position: 0.56; color: "#465c45" }
      GradientStop { position: 1; color: "#182b23" }
     }
     border.color: "#273d55"
     clip: true
     Repeater {
      model: 19
      Rectangle { required property int index; x: preview.width * (index + 1) / 20; height: preview.height; width: 1; color: "#55ffffff" }
     }
     Repeater {
      model: 19
      Rectangle { required property int index; y: preview.height * (index + 1) / 20; width: preview.width; height: 1; color: "#55ffffff" }
     }
     OsdOverlay {
      anchors.fill: parent
      editing: true
      positions: station.osdElements
      enabledElements: station.osdEnabledElements
      corner: station.osdPosition
      telemetry: ({connected:true, provider:"MAVLink", armed:false, flightMode:"STABILIZE", batteryVoltage:15.8, batteryRemaining:82, gpsFix:3, satellites:12, altitude:124, groundSpeed:12.4, heading:348, roll:7, pitch:-3, yaw:348, homeDistance:86})
      video: ({streamId:"simulation", state:"playing"})
      opacityValue: station.osdOpacity
      scaleFactor: station.osdScale
      onPositionChanged: function(name, x, y) { station.setOSDElementPosition(name, x, y) }
     }
    }
   }
  }

  Text {
   visible: station.osdSettingsError !== ""
   text: station.osdSettingsError
   color: "#ff7080"
   wrapMode: Text.WordWrap
   Layout.fillWidth: true
  }

  Text {
   text: "Попередній перегляд використовує штучні дані. Зміни зберігаються автоматично й не впливають на реальний політ."
   color: "#b7c8da"
   font.pixelSize: 13
   Layout.fillWidth: true
  }
 }
}
