import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Static strip above the flight video. Only what matters in the air lives here:
// the vehicle, one link block, one flight-controller block, recording, menu, hide, exit.
// Everything set once (preflight, OSD, presets, streams) is in the menu.
Rectangle {
 id: root
 signal openVehicle()
 signal openHardware()
 signal openStarlink()
 signal openMenu()
 signal leaveFlight()
 signal hideRequested()
 property bool simulation: false
 property var telemetry: ({})
 property var video: ({})
 property string cameraName: ""
 property string presetName: ""
 // The selected connection of the camera in flight: "local", "static", "cloud" or "starlink".
 property string linkKind: ""
 property string linkKindLabel: ""
 property var linkStatus: ({})
 property var linkHistory: []
 property bool linkLost: false
 property int linkLostSeconds: 0
 property int linkFps: 0
 property bool linkWarning: false
 // Narrow screens keep the dots and values, without captions.
 readonly property bool compact: width < 1100
 property color fg: "#f4f7fb"
 property color sub: "#b7c8da"
 property color green: "#27d59a"
 property color amber: "#ffb84d"
 property color red: "#ff6678"
 implicitHeight: 44
 color: "#0b1420"
 border.color: "#22364b"

 function fresh(field) {
  return telemetry.connected === true && (telemetry.freshness || {})[field] !== false &&
    telemetry[field] !== undefined && telemetry[field] !== null && telemetry[field] !== ""
 }
 function linkColor() {
  if (simulation) return amber
  if (linkLost) return red
  if (linkWarning || video.state !== "playing") return amber
  return green
 }
 function linkValue() {
  if (simulation) return "симуляція"
  if (linkLost) return "немає відео " + linkLostSeconds + " с"
  if (video.state !== "playing") return "підключення…"
  var parts = []
  if (linkStatus.state === "available" && linkStatus.latencyMs !== null && linkStatus.latencyMs !== undefined)
   parts.push(linkStatus.latencyMs + " мс")
  parts.push(linkFps + " к/с")
  return parts.join(" · ")
 }
 function fcColor() {
  if (simulation) return amber
  return telemetry.connected === true ? green : red
 }
 function fcValue() {
  if (simulation) return "штучні дані"
  if (telemetry.connected !== true) return "немає даних"
  if (fresh("batteryVoltage")) return "АКБ " + Number(telemetry.batteryVoltage).toFixed(1).replace(".", ",") + " В"
  return "дані є"
 }

 component BarButton: Button {
  font.pixelSize: 13
  Layout.preferredHeight: 34
  background: Rectangle { radius: 7; color: parent.down ? "#2b4a6a" : (parent.hovered ? "#22364b" : "#132235"); border.color: parent.hovered ? "#5f7f9e" : "#2f4860" }
 }
 component Info: Button {
  id: info
  property string caption: ""
  property string value: ""
  property color dot: "transparent"
  default property alias extra: extraSlot.data
  Layout.preferredHeight: 38
  flat: true
  background: Rectangle { radius: 7; color: info.hovered ? "#1a2b3e" : "transparent"; border.color: info.hovered ? "#2f4860" : "transparent" }
  contentItem: RowLayout {
   spacing: 7
   Rectangle { visible: info.dot !== Qt.color("transparent"); width: 9; height: 9; radius: 5; color: info.dot }
   ColumnLayout {
    spacing: 0
    Text { visible: !root.compact; text: info.caption; color: root.sub; font.pixelSize: 11 }
    Text { text: info.value; color: root.fg; font.pixelSize: 13; font.bold: true; elide: Text.ElideRight; Layout.maximumWidth: 200 }
   }
   Item { id: extraSlot; implicitWidth: children.length > 0 ? children[0].width : 0; implicitHeight: children.length > 0 ? children[0].height : 0; visible: children.length > 0 }
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
   value: root.compact ? (root.cameraName || "Камера") : (root.presetName ? root.presetName : "Пресет не вибрано")
   onClicked: root.openVehicle()
   HoverHint { text: "Пресет відео камери. Клавіша 1 — «Авто», 2…0 — пресети, − і + змінюють бітрейт." }
  }
  BarButton {
   objectName: "flightBarBitrateDown"
   visible: !root.simulation
   enabled: !videoPresets.busy
   text: "−"
   Layout.preferredWidth: 30
   onClicked: videoPresets.stepBitrate(-1)
   HoverHint { text: "Зменшити бітрейт камери на крок." }
  }
  BarButton {
   objectName: "flightBarBitrateUp"
   visible: !root.simulation
   enabled: !videoPresets.busy
   text: "+"
   Layout.preferredWidth: 30
   onClicked: videoPresets.stepBitrate(1)
   HoverHint { text: "Збільшити бітрейт камери на крок." }
  }
  Rectangle { Layout.preferredWidth: 1; Layout.preferredHeight: 26; color: "#22364b" }
  Info {
   objectName: "flightBarLink"
   caption: "Зв’язок" + (root.linkKindLabel ? " · " + root.linkKindLabel : "")
   value: root.linkValue()
   dot: root.linkColor()
   onClicked: root.openHardware()
   LinkGraph { visible: !root.simulation; width: root.compact ? 64 : 110; height: 20; values: root.linkHistory }
   HoverHint { text: "Відео за останню хвилину: стовпчик — кадри за секунду, червоний — секунда без відео. Натисніть, щоб побачити все обладнання." }
  }
  Info {
   objectName: "flightBarFc"
   caption: "Польотник"
   value: (root.compact ? "Польотник: " : "") + root.fcValue()
   dot: root.fcColor()
   onClicked: root.openHardware()
  }

  Item { Layout.fillWidth: true }

  Text {
   objectName: "flightBarLowSpace"
   visible: !root.simulation && dvrRuntime.lowSpace
   text: dvrRuntime.freeSpaceText
   color: root.amber
   font.pixelSize: 12
   font.bold: true
  }
  BarButton {
   objectName: "dvrToggle"
   visible: !root.simulation
   enabled: dvrRuntime.recording || dvrRuntime.canStart
   text: dvrRuntime.recording ? "■ " + dvrRuntime.elapsedText : "● REC"
   font.bold: true
   onClicked: dvrRuntime.toggle()
   contentItem: Text { text: parent.text; font: parent.font; color: dvrRuntime.recording ? "white" : (parent.enabled ? root.red : root.sub); horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
   background: Rectangle { radius: 7; color: dvrRuntime.recording ? "#b3263a" : (parent.hovered ? "#22364b" : "#132235"); border.color: dvrRuntime.recording ? root.red : "#2f4860" }
   HoverHint { text: "Почати або зупинити запис відео (F9). " + dvrRuntime.freeSpaceText }
  }
  BarButton { objectName: "flightMenuToggle"; text: root.compact ? "☰" : "☰ Меню"; onClicked: root.openMenu() }
  BarButton {
   objectName: "flightBarHide"
   text: "▴"
   onClicked: root.hideRequested()
   HoverHint { text: "Сховати панель (F10). Відео займе весь екран." }
  }
  BarButton {
   objectName: root.simulation ? "exitSimulation" : "flightBarLeave"
   text: root.simulation ? "Вийти з симуляції" : (root.compact ? "⌂" : "⌂ Головна")
   onClicked: root.leaveFlight()
   HoverHint { text: "Вийти з екрана польоту. Якщо дрон озброєний, станція перепитає." }
  }
 }
}
