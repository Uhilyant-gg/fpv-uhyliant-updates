import QtQuick
import QtQuick.Layouts

Item {
 id: root
 property var telemetry: ({})
 property var video: ({})
 property color foreground: "white"
 property color muted: "#d5e0eb"
 property color good: "#35e0a1"
 property color warning: "#ffcf70"
 property real opacityValue: 0.58
 property real scaleFactor: 1.0
 property bool editing: false
 property var positions: ({})
 property string corner: "top-left"
 signal positionChanged(string name, int x, int y)

 function valueText(value, suffix, digits) {
  if (value === undefined || value === null || value === "") return "—"
  var number = Number(value)
  return (isFinite(number) ? number.toFixed(digits || 0) : String(value)) + (suffix || "")
 }
 function telemetryUnavailable(field) {
  var freshness = telemetry.freshness || {}
  return freshness[field] === false ? "застаріло" : "—"
 }
 function telemetryText(field, value, suffix, digits) {
  if (telemetry.connected !== true) return "—"
  if ((telemetry.freshness || {})[field] === false) return "застаріло"
  if (value === undefined || value === null || value === "") return telemetryUnavailable(field)
  return valueText(value, suffix, digits)
 }
 function optionalTelemetryText(field, value, suffix, digits) {
  if (telemetry.connected !== true) return ""
  if (value === undefined || value === null || value === "") {
   return telemetryUnavailable(field) === "застаріло" ? " · застаріло" : ""
  }
  return " · " + telemetryText(field, value, suffix, digits)
 }
 function speedSuffix() {
  return telemetry.provider === "CRSF" ? " км/год" : " м/с"
 }
 function gpsFixText(value) {
  if (value === undefined || value === null || value === "") return "—"
  var fix = Number(value)
  if (!isFinite(fix)) return "—"
  if (fix <= 1) return "немає"
  if (fix === 2) return "2D"
  return "3D"
 }
 function gpsFixDisplay() {
  if (telemetry.connected !== true) return "—"
  if ((telemetry.freshness || {}).gpsFix === false) return "застаріло"
  if (telemetry.gpsFix === undefined || telemetry.gpsFix === null || telemetry.gpsFix === "") return telemetryUnavailable("gpsFix")
  return gpsFixText(telemetry.gpsFix)
 }
 function linkLabel() {
  if (telemetry.connected === true) return "Телеметрія: зв’язок є"
  if (telemetry.connected === false) return "Телеметрія: немає зв’язку"
  return "Телеметрія: не підтверджена"
 }

 property var tiles: [
  {name:"link", text:root.linkLabel()},
  {name:"arm", text:"ARM: " + (telemetry.connected !== true ? "—" : ((telemetry.freshness || {}).armed === false ? "застаріло" : (telemetry.armed === null || telemetry.armed === undefined ? "—" : (telemetry.armed ? "активний" : "вимкнений"))))},
  {name:"mode", text:"Режим: " + root.telemetryText("flightMode", telemetry.flightMode)},
  {name:"battery", text:"АКБ: " + root.telemetryText("batteryVoltage", telemetry.batteryVoltage, " В", 1) + root.optionalTelemetryText("batteryRemaining", telemetry.batteryRemaining, "%", 0)},
  {name:"gps", text:"GPS: " + root.gpsFixDisplay() + root.optionalTelemetryText("satellites", telemetry.satellites, " супутн.", 0)},
  {name:"altitude", text:"Висота: " + root.telemetryText("altitude", telemetry.altitude, " м", 0)},
  {name:"speed", text:"Швидкість: " + root.telemetryText("groundSpeed", telemetry.groundSpeed, root.speedSuffix(), 1)},
  {name:"heading", text:"Напрямок: " + root.telemetryText("heading", telemetry.heading, "°", 0)},
  {name:"video", text:"Відео: " + (video.streamId ? (video.state === "playing" ? "активне" : "перевіряється") : "немає")}
 ]
 function tilePosition(tile, axis, index) {
  var saved = positions[tile.name]
  if (saved && saved.length === 2) return saved[axis]
  var value = axis === 0 ? 0 : index * 6
  if (axis === 0 && corner.endsWith("right")) return 100 - value
  if (axis === 1 && corner.startsWith("bottom")) return Math.min(100, value + 52)
  return value
 }
 Repeater {
  model: root.tiles
  delegate: Rectangle {
   id: tile
   required property var modelData
   required property int index
   objectName: "osd-" + modelData.name
   property bool moving: false
   property real movingX: 0
   property real movingY: 0
   width: Math.min(root.width, label.implicitWidth + 18)
   height: label.implicitHeight + 14
   x: moving ? movingX : Math.min(Math.max(0, root.width - width), root.width * root.tilePosition(modelData, 0, index) / 100)
   y: moving ? movingY : Math.min(Math.max(0, root.height - height), root.height * root.tilePosition(modelData, 1, index) / 100)
   radius: 6
   color: Qt.rgba(0, 0, 0, root.opacityValue)
   border.color: root.editing ? "#80c5ff" : "#8093a6"
   Text {
    id: label
    anchors.centerIn: parent
    text: tile.modelData.text
    color: root.foreground
    font.pixelSize: 13 * root.scaleFactor
    font.bold: true
    elide: Text.ElideRight
    width: Math.min(implicitWidth, Math.max(0, tile.width - 18))
   }
   MouseArea {
    id: mouse
    anchors.fill: parent
    enabled: root.editing
    property real offsetX: 0
    property real offsetY: 0
    onPressed: function(event) { offsetX = event.x; offsetY = event.y; tile.movingX = tile.x; tile.movingY = tile.y; tile.moving = true }
    onPositionChanged: function(event) {
     if (!pressed) return
     var point = mapToItem(root, event.x, event.y)
     tile.movingX = Math.max(0, Math.min(root.width - tile.width, point.x - offsetX))
     tile.movingY = Math.max(0, Math.min(root.height - tile.height, point.y - offsetY))
    }
    onReleased: {
     var x = root.width > tile.width ? Math.round(tile.x * 20 / root.width) * 5 : 0
     var y = root.height > tile.height ? Math.round(tile.y * 20 / root.height) * 5 : 0
     root.positionChanged(tile.modelData.name, Math.max(0, Math.min(100, x)), Math.max(0, Math.min(100, y)))
     tile.moving = false
    }
    onCanceled: tile.moving = false
   }
  }
 }
}
