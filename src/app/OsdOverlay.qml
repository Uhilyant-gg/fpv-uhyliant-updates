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

 implicitWidth: Math.min(620, parent ? parent.width - 32 : 620)
 implicitHeight: osdColumn.implicitHeight + 16

 Rectangle {
  anchors.fill: parent
  radius: 6
  color: Qt.rgba(0, 0, 0, root.opacityValue)
  border.color: "#607f9ab5"
 }

 ColumnLayout {
  id: osdColumn
  anchors.fill: parent
  anchors.margins: 8
  spacing: 5

  RowLayout {
   Layout.fillWidth: true
   spacing: 10
   Text {
    text: root.linkLabel()
    color: telemetry.connected === true ? root.good : root.warning
    font.pixelSize: 11 * root.scaleFactor
    font.bold: true
   }
   Text {
    text: "ARM: " + (telemetry.connected !== true ? "—" : ((telemetry.freshness || {}).armed === false ? "застаріло" : (telemetry.armed === null || telemetry.armed === undefined ? "—" : (telemetry.armed ? "активний" : "вимкнений"))))
    color: root.foreground
    font.pixelSize: 11 * root.scaleFactor
    font.bold: true
   }
   Text {
    text: "Режим: " + root.telemetryText("flightMode", telemetry.flightMode)
    color: root.foreground
    font.pixelSize: 11 * root.scaleFactor
    font.bold: true
    elide: Text.ElideRight
    Layout.maximumWidth: 150
   }
   Text {
    text: "АКБ: " + root.telemetryText("batteryVoltage", telemetry.batteryVoltage, " В", 1) +
      root.optionalTelemetryText("batteryRemaining", telemetry.batteryRemaining, "%", 0)
    color: root.foreground
    font.pixelSize: 11 * root.scaleFactor
    font.bold: true
   }
  }

  RowLayout {
   Layout.fillWidth: true
   spacing: 10
   Text {
    text: "GPS: " + root.gpsFixDisplay() +
      root.optionalTelemetryText("satellites", telemetry.satellites, " супутн.", 0)
    color: root.muted
    font.pixelSize: 10 * root.scaleFactor
   }
   Text { text: "Висота: " + root.telemetryText("altitude", telemetry.altitude, " м", 0); color: root.foreground; font.pixelSize: 10 * root.scaleFactor; font.bold: true }
   Text { text: "Швидкість: " + root.telemetryText("groundSpeed", telemetry.groundSpeed, root.speedSuffix(), 1); color: root.foreground; font.pixelSize: 10 * root.scaleFactor; font.bold: true }
   Text { text: "Напрямок: " + root.telemetryText("heading", telemetry.heading, "°", 0); color: root.foreground; font.pixelSize: 10 * root.scaleFactor; font.bold: true }
   Item { Layout.fillWidth: true }
   Text {
    text: "Відео: " + (video.streamId ? (video.state === "playing" ? "активне" : "перевіряється") : "немає")
    color: video.state === "playing" ? root.good : root.muted
    font.pixelSize: 10 * root.scaleFactor
    font.bold: true
   }
  }
 }
}
