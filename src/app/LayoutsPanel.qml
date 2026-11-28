import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// The pilot's layouts of the additional windows, as little pictures of the screen.
// Nothing opens unless the pilot presses it; what each tile does is said in its hint.
Item {
 id: root
 signal closeRequested()
 property color fg: "#f4f7fb"
 property color sub: "#b7c8da"
 property color accent: "#27d59a"
 implicitWidth: grid.implicitWidth + 24
 implicitHeight: grid.implicitHeight + 24

 // A tile: a tiny 16:9 screen with the windows of the arrangement drawn on it.
 component Tile: Button {
  id: tile
  property var shapes: []
  property string badge: ""
  property bool dashed: false
  property alias deletable: del.visible
  signal deleteRequested()
  implicitWidth: 104
  implicitHeight: 70
  padding: 0
  background: Rectangle {
   radius: 10
   color: tile.down ? "#2b4a6a" : (tile.hovered ? "#1f3550" : "#132235")
   border.color: tile.hovered ? "#7897b5" : "#2f4860"
   border.width: tile.dashed ? 0 : 1
  }
  contentItem: Item {
   Rectangle { // the screen
    id: screen
    anchors.centerIn: parent
    width: 76; height: 43; radius: 4
    color: tile.dashed ? "transparent" : "#24425f"
    border.color: tile.dashed ? root.sub : "#5f7f9e"
    border.width: tile.dashed ? 1.5 : 1
    Repeater {
     model: tile.shapes
     Rectangle {
      required property var modelData
      x: modelData.x * screen.width
      y: modelData.y * screen.height
      width: Math.max(8, modelData.w * screen.width)
      height: width * 9 / 16
      radius: 2
      color: root.accent
      opacity: 0.9
     }
    }
   }
   Text { // a symbol in the middle (plus, history)
    visible: tile.badge !== ""
    anchors.centerIn: screen
    text: tile.badge
    color: root.fg
    font.pixelSize: tile.dashed ? 24 : 16
    font.bold: true
    style: Text.Outline; styleColor: "#0b1420"
   }
   Rectangle { // delete, only on a saved layout under the mouse
    id: del
    visible: false
    opacity: tile.hovered ? 1 : 0
    anchors.right: parent.right; anchors.top: parent.top; anchors.margins: 3
    width: 20; height: 20; radius: 10
    color: delArea.containsMouse ? "#b3263a" : "#cc132235"
    border.color: "#a56878"
    Text { anchors.centerIn: parent; text: "✕"; color: root.fg; font.pixelSize: 10 }
    MouseArea { id: delArea; anchors.fill: parent; hoverEnabled: true; onClicked: tile.deleteRequested() }
    Behavior on opacity { NumberAnimation { duration: 120 } }
   }
  }
 }

 GridLayout {
  id: grid
  anchors.centerIn: parent
  columns: 3
  rowSpacing: 8
  columnSpacing: 8

  Tile {
   objectName: "layoutMainOnly"
   onClicked: { extraWindows.closeAll(); root.closeRequested() }
   HoverHint { text: "Тільки основне відео" }
  }
  Tile {
   objectName: "layoutLast"
   enabled: extraWindows.canRestore
   opacity: enabled ? 1 : 0.4
   shapes: extraWindows.lastWindows
   badge: "↺"
   onClicked: { extraWindows.restoreLast(); root.closeRequested() }
   HoverHint { text: "Як минулого разу" }
  }
  Repeater {
   model: extraWindows.layouts
   delegate: Tile {
    required property var modelData
    required property int index
    objectName: "layoutApply"
    shapes: modelData.windows
    deletable: true
    onClicked: { extraWindows.applyLayout(index); root.closeRequested() }
    onDeleteRequested: extraWindows.deleteLayout(index)
    HoverHint { text: modelData.name + " · вікон: " + modelData.count + ". Натисніть, щоб відкрити; ✕ — видалити." }
   }
  }
  Tile {
   objectName: "layoutSave"
   dashed: true
   badge: "＋"
   enabled: extraWindows.openCount > 0
   opacity: enabled ? 1 : 0.4
   onClicked: extraWindows.saveLayout()
   HoverHint { text: "Зберегти поточне розташування вікон" }
  }
 }
}
