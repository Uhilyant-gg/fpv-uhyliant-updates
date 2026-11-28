import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// The pilot's layouts of the additional windows. Nothing opens unless the pilot presses it.
Item {
 id: root
 signal closeRequested()
 property color fg: "#f4f7fb"
 property color sub: "#b7c8da"
 implicitWidth: 320
 implicitHeight: column.implicitHeight + 24

 ColumnLayout {
  id: column
  anchors.fill: parent
  anchors.margins: 12
  spacing: 6
  Text { text: "Розташування вікон"; color: root.fg; font.pixelSize: 16; font.bold: true }
  Button {
   objectName: "layoutMainOnly"
   Layout.fillWidth: true
   text: "Тільки основне відео"
   onClicked: { extraWindows.closeAll(); root.closeRequested() }
  }
  Button {
   objectName: "layoutLast"
   Layout.fillWidth: true
   text: "Як минулого разу"
   enabled: extraWindows.canRestore
   onClicked: { extraWindows.restoreLast(); root.closeRequested() }
  }
  Repeater {
   model: extraWindows.layouts
   delegate: RowLayout {
    required property var modelData
    required property int index
    Layout.fillWidth: true
    Button {
     objectName: "layoutApply"
     Layout.fillWidth: true
     text: modelData.name + " · вікон: " + modelData.count
     onClicked: { extraWindows.applyLayout(index); root.closeRequested() }
    }
    Button { objectName: "layoutDelete"; text: "✕"; implicitWidth: 36; onClicked: extraWindows.deleteLayout(index) }
   }
  }
  Button {
   objectName: "layoutSave"
   Layout.fillWidth: true
   text: "Зберегти поточне розташування"
   enabled: extraWindows.openCount > 0
   onClicked: extraWindows.saveLayout()
  }
  Text {
   text: "Пресет запам’ятовує, які потоки відкриті, де стоять вікна і якого вони розміру."
   color: root.sub; font.pixelSize: 11; wrapMode: Text.Wrap; Layout.fillWidth: true
  }
 }
}
