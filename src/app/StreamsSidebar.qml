import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Left strip of the flight screen: one icon per additional stream of the camera.
// A click opens its window, another click closes it (the stream is stopped: no bitrate).
// At the bottom: the pilot's layouts of windows.
Rectangle {
 id: root
 signal openLayouts()
 property color fg: "#f4f7fb"
 property color sub: "#b7c8da"
 property color green: "#27d59a"
 implicitWidth: 64
 color: "#0b1420"
 border.color: "#22364b"

 function shortName(name) {
  var first = String(name || "").split(" ")[0]
  return first.length > 6 ? first.slice(0, 5) + "." : first
 }

 ColumnLayout {
  anchors.fill: parent
  anchors.margins: 6
  spacing: 6

  Repeater {
   model: extraWindows.sources
   delegate: Button {
    required property var modelData
    objectName: "sideStream"
    Layout.fillWidth: true
    Layout.preferredHeight: 52
    enabled: modelData.slot >= 0 || extraWindows.openCount < 3
    padding: 2
    background: Rectangle {
     radius: 8
     color: modelData.slot >= 0 ? "#1d3a2f" : (parent.hovered ? "#22364b" : "#132235")
     border.color: modelData.slot >= 0 ? root.green : "#2f4860"
    }
    contentItem: ColumnLayout {
     spacing: 1
     Text { Layout.alignment: Qt.AlignHCenter; text: modelData.slot >= 0 ? "▣" : "□"; color: modelData.slot >= 0 ? root.green : root.sub; font.pixelSize: 18 }
     Text { Layout.alignment: Qt.AlignHCenter; text: root.shortName(modelData.name); color: root.fg; font.pixelSize: 10 }
    }
    onClicked: modelData.slot >= 0 ? extraWindows.close(modelData.slot) : extraWindows.open(modelData.id)
    HoverHint { text: (modelData.slot >= 0 ? "Закрити: " : "Показати у вікні: ") + modelData.name + (modelData.slot >= 0 ? ". Потік стане на паузу." : "") }
   }
  }

  Item { Layout.fillHeight: true }

  Button {
   objectName: "sideLayouts"
   Layout.fillWidth: true
   Layout.preferredHeight: 52
   padding: 2
   background: Rectangle { radius: 8; color: parent.hovered ? "#22364b" : "#132235"; border.color: "#2f4860" }
   contentItem: ColumnLayout {
    spacing: 1
    Text { Layout.alignment: Qt.AlignHCenter; text: "▦"; color: root.fg; font.pixelSize: 18 }
    Text { Layout.alignment: Qt.AlignHCenter; text: "Розташ."; color: root.fg; font.pixelSize: 10 }
   }
   onClicked: root.openLayouts()
   HoverHint { text: "Пресети розташування вікон: зберегти поточне, відкрити збережене, як минулого разу." }
  }
 }
}
