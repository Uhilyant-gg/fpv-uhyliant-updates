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
 function telemetryText(value, suffix, digits) {
  return telemetry.connected === true ? valueText(value, suffix, digits) : "—"
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
 function linkLabel() {
  if (telemetry.connected === true) return "Телеметрія: актуальна"
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
    text: "ARM: " + (telemetry.connected !== true || telemetry.armed === null || telemetry.armed === undefined ? "—" : (telemetry.armed ? "активний" : "вимкнений"))
    color: root.foreground
    font.pixelSize: 11 * root.scaleFactor
    font.bold: true
   }
   Text {
    text: "Режим: " + root.telemetryText(telemetry.flightMode)
    color: root.foreground
    font.pixelSize: 11 * root.scaleFactor
    font.bold: true
    elide: Text.ElideRight
    Layout.maximumWidth: 150
   }
   Text {
    text: "АКБ: " + root.telemetryText(telemetry.batteryVoltage, " В", 1) +
      (telemetry.connected === true && telemetry.batteryRemaining !== null && telemetry.batteryRemaining !== undefined
       ? " · " + root.valueText(telemetry.batteryRemaining, "%", 0) : "")
    color: root.foreground
    font.pixelSize: 11 * root.scaleFactor
    font.bold: true
   }
  }

  RowLayout {
   Layout.fillWidth: true
   spacing: 10
   Text {
    text: "GPS: " + (telemetry.connected === true ? root.gpsFixText(telemetry.gpsFix) : "—") +
      (telemetry.connected === true && telemetry.satellites !== null && telemetry.satellites !== undefined
       ? " · " + root.valueText(telemetry.satellites, " супутн.", 0) : "")
    color: root.muted
    font.pixelSize: 10 * root.scaleFactor
   }
   Text { text: "Висота: " + root.telemetryText(telemetry.altitude, " м", 0); color: root.foreground; font.pixelSize: 10 * root.scaleFactor; font.bold: true }
   Text { text: "Швидкість: " + root.telemetryText(telemetry.groundSpeed, root.speedSuffix(), 1); color: root.foreground; font.pixelSize: 10 * root.scaleFactor; font.bold: true }
   Text { text: "Напрямок: " + root.telemetryText(telemetry.heading, "°", 0); color: root.foreground; font.pixelSize: 10 * root.scaleFactor; font.bold: true }
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
