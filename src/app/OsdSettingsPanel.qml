import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
 id: root
 signal closeRequested()

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

   ColumnLayout {
    Layout.preferredWidth: 250
    Layout.fillHeight: true
    spacing: 10

    Switch { text: "Показувати OSD"; checked: station.osdEnabled; onToggled: station.setOSDEnabled(checked) }
    Text { text: "Перетягніть показники на сітці праворуч."; color: "#dce6f2"; wrapMode: Text.WordWrap; Layout.fillWidth: true }

    Text { text: "Прозорість фону"; color: "#dce6f2"; font.bold: true }
    Slider {
     id: opacitySlider
     Layout.fillWidth: true
     from: 0.25
     to: 0.8
     stepSize: 0.05
     value: station.osdOpacity
     onMoved: station.setOSDStyle(value, scaleSlider.value)
    }

    Text { text: "Розмір тексту"; color: "#dce6f2"; font.bold: true }
    Slider {
     id: scaleSlider
     Layout.fillWidth: true
     from: 0.85
     to: 1.3
     stepSize: 0.05
     value: station.osdScale
     onMoved: station.setOSDStyle(opacitySlider.value, value)
    }
    Button {
     text: "Стандартні налаштування"
     Layout.fillWidth: true
     onClicked: station.resetOSDStyle()
    }
    Item { Layout.fillHeight: true }
   }

   ColumnLayout {
    Layout.fillWidth: true
    Layout.fillHeight: true
    spacing: 6
    Text { text: "Симуляція · приклад відео і даних"; color: "#dce6f2"; font.bold: true }
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
      corner: station.osdPosition
      telemetry: ({connected:true, provider:"MAVLink", armed:false, flightMode:"STABILIZE", batteryVoltage:15.8, batteryRemaining:82, gpsFix:3, satellites:12, altitude:124, groundSpeed:12.4, heading:348})
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
   text: "Це лише приклад, не реальна камера чи телеметрія. Зміни зберігаються автоматично."
   color: "#b7c8da"
   font.pixelSize: 13
   Layout.fillWidth: true
  }
 }
}
