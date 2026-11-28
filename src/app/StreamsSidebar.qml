import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Left strip of the flight screen. At the top the main stream, then the camera's other
// streams and the map: a click opens a window, another closes it (a closed stream is
// stopped, no bitrate). ⚙ under a stream opens its own settings. At the bottom: layouts.
Rectangle {
 id: root
 signal openLayouts()
 signal openStreamSettings(var stream)
 property color fg: "#f4f7fb"
 property color sub: "#b7c8da"
 property color green: "#27d59a"
 implicitWidth: 84
 color: "#0b1420"
 border.color: "#22364b"

 function glyph(kind) {
  return kind === "map" ? "⌖" : (kind === "thermal" ? "◐" : (kind === "main" ? "◉" : "▶"))
 }

 component StreamTile: ColumnLayout {
  id: tile
  property var stream: ({})
  property bool on: false
  property bool main: false
  property bool settings: true
  signal toggled()
  Layout.fillWidth: true
  spacing: 2
  Button {
   objectName: tile.main ? "sideMain" : "sideStream"
   Layout.fillWidth: true
   Layout.preferredHeight: 58
   padding: 3
   enabled: tile.main || tile.on || extraWindows.openCount < 3
   background: Rectangle {
    radius: 8
    color: tile.on ? "#1d3a2f" : (parent.hovered ? "#22364b" : "#132235")
    border.color: tile.on ? root.green : "#2f4860"
   }
   contentItem: ColumnLayout {
    spacing: 1
    Text { Layout.alignment: Qt.AlignHCenter; text: root.glyph(tile.stream.kind); color: tile.on ? root.green : root.sub; font.pixelSize: 18 }
    Text {
     Layout.fillWidth: true
     horizontalAlignment: Text.AlignHCenter
     text: tile.stream.name || ""
     color: root.fg; font.pixelSize: 10
     wrapMode: Text.Wrap; maximumLineCount: 2; elide: Text.ElideRight
    }
   }
   onClicked: tile.toggled()
   HoverHint { text: tile.main ? "Основне відео: завжди на екрані" : ((tile.on ? "Закрити: " : "Показати у вікні: ") + (tile.stream.name || "") + (tile.on && tile.stream.kind !== "map" ? ". Потік стане на паузу." : "")) }
  }
  Button {
   objectName: "sideSettings"
   visible: tile.settings
   Layout.fillWidth: true
   Layout.preferredHeight: 20
   padding: 0
   text: "⚙"
   font.pixelSize: 12
   background: Rectangle { radius: 5; color: parent.hovered ? "#22364b" : "transparent"; border.color: parent.hovered ? "#2f4860" : "transparent" }
   onClicked: root.openStreamSettings(tile.stream)
   HoverHint { text: "Налаштування цього потоку: якість (пресети) і показ у вікні" }
  }
 }

 Flickable {
  anchors.fill: parent
  anchors.margins: 6
  anchors.bottomMargin: 70
  contentHeight: list.implicitHeight
  clip: true
  ColumnLayout {
   id: list
   width: parent.width
   spacing: 8
   StreamTile {
    main: true
    on: true
    stream: ({ id: streamWorkspace.state.primaryId || "", name: extraWindows.mainName || "Основне", kind: "main", channel: 0 })
   }
   Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: "#22364b" }
   Repeater {
    model: extraWindows.sources
    delegate: StreamTile {
     required property var modelData
     stream: modelData
     on: modelData.slot >= 0
     settings: modelData.kind !== "map"
     onToggled: modelData.slot >= 0 ? extraWindows.close(modelData.slot) : extraWindows.open(modelData.id)
    }
   }
  }
 }

 Button {
  objectName: "sideLayouts"
  anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom
  anchors.margins: 6
  height: 52
  padding: 2
  background: Rectangle { radius: 8; color: parent.hovered ? "#22364b" : "#132235"; border.color: "#2f4860" }
  contentItem: Item {
   // A little screen with two windows: the layouts.
   Rectangle {
    anchors.centerIn: parent
    width: 34; height: 22; radius: 3
    color: "transparent"; border.color: root.fg; border.width: 1.5
    Rectangle { x: 19; y: 3; width: 12; height: 7; radius: 1; color: root.green }
    Rectangle { x: 19; y: 12; width: 12; height: 7; radius: 1; color: root.green; opacity: 0.6 }
   }
  }
  onClicked: root.openLayouts()
  HoverHint { text: "Розташування вікон: зберегти поточне, відкрити збережене, як минулого разу" }
 }
}
