import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Settings of one stream: its quality (the camera's presets for that stream) and how it is
// shown in its window. Showing settings change only this PC's picture, never the camera.
Item {
 id: root
 signal closeRequested()
 signal openPresets(int channel, string name)
 property var stream: ({})
 readonly property var shown: stream.id ? extraWindows.display(stream.id) : ({})
 property int revision: 0  // re-read after a change
 property color fg: "#f4f7fb"
 property color sub: "#b7c8da"
 property color green: "#27d59a"
 implicitWidth: 340
 implicitHeight: column.implicitHeight + 24

 function value(key) { root.revision; return (extraWindows.display(stream.id || "") || {})[key] }
 function set(key, v) { extraWindows.setDisplay(stream.id, key, v); root.revision++ }

 component Choice: Button {
  property bool on: false
  checkable: false
  implicitHeight: 34
  background: Rectangle { radius: 7; color: parent.on ? "#1d3a2f" : (parent.hovered ? "#22364b" : "#132235"); border.color: parent.on ? root.green : "#2f4860" }
  contentItem: Text { text: parent.text; color: root.fg; font.pixelSize: 13; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
 }

 ColumnLayout {
  id: column
  anchors.fill: parent
  anchors.margins: 12
  spacing: 8
  Text { text: stream.name || "Потік"; color: root.fg; font.pixelSize: 16; font.bold: true; elide: Text.ElideRight; Layout.fillWidth: true }

  Text { text: "Якість"; color: root.sub; font.pixelSize: 12 }
  Choice {
   objectName: "streamPresets"
   visible: stream.channel === 0 || stream.channel === 1
   Layout.fillWidth: true
   text: "▤  Пресети відео цього потоку"
   onClicked: root.openPresets(stream.channel, stream.name || "")
  }
  Text {
   visible: stream.channel !== 0 && stream.channel !== 1
   text: "Цей потік камера не кодує сама (наприклад, тепловізор через USB): його якість задається на самому пристрої."
   color: root.sub; font.pixelSize: 12; wrapMode: Text.Wrap; Layout.fillWidth: true
  }

  Text { visible: stream.kind !== "main"; text: "Показ у вікні"; color: root.sub; font.pixelSize: 12 }
  RowLayout {
   visible: stream.kind !== "main"
   Layout.fillWidth: true
   spacing: 6
   Choice { objectName: "streamFit"; Layout.fillWidth: true; text: "▭ Вписати"; on: !root.value("fill"); onClicked: root.set("fill", false) }
   Choice { objectName: "streamFill"; Layout.fillWidth: true; text: "▣ Заповнити"; on: root.value("fill") === true; onClicked: root.set("fill", true) }
  }
  RowLayout {
   visible: stream.kind !== "main"
   Layout.fillWidth: true
   spacing: 6
   Choice { objectName: "streamRotate"; Layout.fillWidth: true; text: "↻ 180°"; on: root.value("rotate") === 180; onClicked: root.set("rotate", root.value("rotate") === 180 ? 0 : 180) }
   Choice { objectName: "streamMirror"; Layout.fillWidth: true; text: "⇋ Дзеркально"; on: root.value("mirror") === true; onClicked: root.set("mirror", !root.value("mirror")) }
  }
  Text {
   visible: stream.kind !== "main"
   text: "«Вписати» показує весь кадр, «Заповнити» — без чорних смуг. Поворот і дзеркало — для камери, встановленої догори дриґом або через дзеркало."
   color: root.sub; font.pixelSize: 11; wrapMode: Text.Wrap; Layout.fillWidth: true
  }
  RowLayout { Item { Layout.fillWidth: true } Button { text: "Закрити"; flat: true; onClicked: root.closeRequested() } }
 }
}
