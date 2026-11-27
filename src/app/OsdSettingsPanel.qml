import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
 id: root
 signal closeRequested()

 function positionIndex(position) {
  var positions = ["top-left", "top-right", "bottom-left", "bottom-right"]
  return Math.max(0, positions.indexOf(position))
 }

 Rectangle {
  anchors.fill: parent
  color: "#0d1725"
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

    Text { text: "Розташування"; color: "#dce6f2"; font.bold: true }
    ComboBox {
     id: positionSelector
     Layout.fillWidth: true
     model: ["Згори ліворуч", "Згори праворуч", "Знизу ліворуч", "Знизу праворуч"]
     currentIndex: root.positionIndex(station.osdPosition)
     onActivated: station.setOSDPosition(["top-left", "top-right", "bottom-left", "bottom-right"][currentIndex])
    }

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
    Text { text: "Приклад розміщення без телеметрії"; color: "#dce6f2"; font.bold: true }
    Rectangle {
     Layout.fillWidth: true
     Layout.fillHeight: true
     Layout.minimumHeight: 150
     color: "#050a12"
     border.color: "#273d55"
     clip: true
     OsdOverlay {
      width: Math.min(620, parent.width - 24)
      height: implicitHeight
      anchors.left: station.osdPosition.endsWith("left") ? parent.left : undefined
      anchors.right: station.osdPosition.endsWith("right") ? parent.right : undefined
      anchors.top: station.osdPosition.startsWith("top") ? parent.top : undefined
      anchors.bottom: station.osdPosition.startsWith("bottom") ? parent.bottom : undefined
      anchors.margins: 12
      opacityValue: station.osdOpacity
      scaleFactor: station.osdScale
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
   text: "Зміни зберігаються автоматично. Налаштовуйте OSD до початку роботи."
   color: "#8799ad"
   font.pixelSize: 11
   Layout.fillWidth: true
  }
 }
}
