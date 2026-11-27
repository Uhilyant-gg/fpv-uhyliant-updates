import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Static strip above the flight video: everything that is not flight-critical lives here,
// so nothing but the OSD and alerts is drawn over the picture.
Rectangle {
 id: root
 signal openVehicle()
 signal openStreams()
 signal openDiagnostics()
 signal openPreflight()
 signal openMenu()
 signal leaveFlight()
 signal hideRequested()
 property bool simulation: false
 property var telemetry: ({})
 property var video: ({})
 property string cameraName: ""
 property string presetName: ""
 property bool pipEnabled: false
 property bool pipAvailable: false
 property color fg: "#f4f7fb"
 property color sub: "#b7c8da"
 property color green: "#27d59a"
 property color amber: "#ffb84d"
 property color red: "#ff6678"
 implicitHeight: 52
 color: "#0b1420"
 border.color: "#22364b"

 function fresh(field) {
  return telemetry.connected === true && (telemetry.freshness || {})[field] !== false &&
    telemetry[field] !== undefined && telemetry[field] !== null && telemetry[field] !== ""
 }
 function linkText() {
  if (simulation) return "штучні дані"
  if (telemetry.connected !== true) return "немає телеметрії"
  var parts = []
  if (fresh("linkQuality")) parts.push("LQ " + Math.round(Number(telemetry.linkQuality)) + "%")
  if (fresh("rssiDbm")) parts.push(Math.round(Number(telemetry.rssiDbm)) + " dBm")
  return parts.length ? parts.join(" · ") : "телеметрія є"
 }
 function linkColor() {
  if (simulation) return amber
  if (telemetry.connected !== true) return red
  if (fresh("linkQuality") && Number(telemetry.linkQuality) < 50) return amber
  return green
 }
 function videoText() {
  if (simulation) return "симуляція"
  if (!video.streamId) return "немає потоку"
  if (video.state !== "playing") return "підключення…"
  var size = video.width && video.height ? video.width + "×" + video.height : ""
  var fps = video.fps ? Math.round(Number(video.fps)) + " к/с" : ""
  return [size, fps].filter(function(part) { return part !== "" }).join(" · ") || "активне"
 }

 component BarButton: Button {
  font.pixelSize: 13
  Layout.preferredHeight: 38
  background: Rectangle { radius: 7; color: parent.down ? "#2b4a6a" : (parent.hovered ? "#22364b" : "#132235"); border.color: parent.hovered ? "#5f7f9e" : "#2f4860" }
 }
 component Info: Button {
  id: info
  property string caption: ""
  property string value: ""
  property color dot: "transparent"
  Layout.preferredHeight: 42
  flat: true
  background: Rectangle { radius: 7; color: info.hovered ? "#1a2b3e" : "transparent"; border.color: info.hovered ? "#2f4860" : "transparent" }
  contentItem: RowLayout {
   spacing: 7
   Rectangle { visible: info.dot !== Qt.color("transparent"); width: 9; height: 9; radius: 5; color: info.dot }
   ColumnLayout {
    spacing: 0
    Text { text: info.caption; color: root.sub; font.pixelSize: 11 }
    Text { text: info.value; color: root.fg; font.pixelSize: 13; font.bold: true; elide: Text.ElideRight; Layout.maximumWidth: 230 }
   }
  }
 }

 RowLayout {
  anchors.fill: parent
  anchors.leftMargin: 8
  anchors.rightMargin: 8
  spacing: 6

  Info {
   objectName: "flightBarVehicle"
   caption: root.simulation ? "Симуляція" : (root.cameraName || "Камера")
   value: root.presetName ? "Пресет: " + root.presetName : "Пресет не вибрано"
   onClicked: root.openVehicle()
  }
  Rectangle { Layout.preferredWidth: 1; Layout.preferredHeight: 30; color: "#22364b" }
  Info {
   objectName: "flightBarVideo"
   caption: "Відео" + (root.pipEnabled ? " · 2 потоки" : "")
   value: root.videoText()
   dot: root.simulation ? root.amber : (root.video.state === "playing" ? root.green : root.amber)
   enabled: !root.simulation
   onClicked: root.openStreams()
  }
  Info {
   objectName: "flightBarLink"
   caption: "Зв’язок"
   value: root.linkText()
   dot: root.linkColor()
   enabled: !root.simulation
   onClicked: root.openDiagnostics()
  }

  Item { Layout.fillWidth: true }

  BarButton {
   objectName: "dvrToggle"
   visible: !root.simulation
   enabled: dvrRuntime.recording || dvrRuntime.canStart
   text: dvrRuntime.recording ? "■ " + dvrRuntime.elapsedText : "● REC"
   font.bold: true
   onClicked: dvrRuntime.toggle()
   contentItem: Text { text: parent.text; font: parent.font; color: dvrRuntime.recording ? "white" : (parent.enabled ? root.red : root.sub); horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
   background: Rectangle { radius: 7; color: dvrRuntime.recording ? "#b3263a" : (parent.hovered ? "#22364b" : "#132235"); border.color: dvrRuntime.recording ? root.red : "#2f4860" }
   HoverHint { text: "Почати або зупинити запис відео (F9)." }
  }
  Text {
   visible: !root.simulation && dvrRuntime.freeSpaceText !== ""
   text: dvrRuntime.freeSpaceText
   color: root.sub
   font.pixelSize: 11
  }
  BarButton {
   objectName: "flightBarOsd"
   text: station.osdEnabled ? "OSD ✓" : "OSD ✕"
   onClicked: station.setOSDEnabled(!station.osdEnabled)
   HoverHint { text: "Показати або сховати OSD станції поверх відео." }
  }
  BarButton { objectName: "flightBarPreflight"; text: "✓ Підготовка"; enabled: !root.simulation; onClicked: root.openPreflight() }
  BarButton { objectName: "flightMenuToggle"; text: "☰ Меню"; onClicked: root.openMenu() }
  BarButton {
   objectName: "flightBarHide"
   text: "▴"
   onClicked: root.hideRequested()
   HoverHint { text: "Сховати панель (F10). Відео займе весь екран." }
  }
  BarButton { objectName: root.simulation ? "exitSimulation" : "flightBarLeave"; text: root.simulation ? "Вийти з симуляції" : "⌂ Головна"; onClicked: root.leaveFlight() }
 }
}
