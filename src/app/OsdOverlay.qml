import QtQuick
import QtQuick.Layouts

Item {
 id: root
 property var telemetry: ({})
 property var video: ({})
 property var enabledElements: ({})
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
 function elementEnabled(name) {
  if (enabledElements[name] !== undefined) return enabledElements[name] === true
  return name !== "homeDistance" && name !== "reticle" && name !== "horizon"
 }
 function attitudeAvailable() {
  var freshness = telemetry.freshness || {}
  return telemetry.connected === true && freshness.roll !== false && freshness.pitch !== false &&
    isFinite(Number(telemetry.roll)) && isFinite(Number(telemetry.pitch))
 }
 function gridPixel(value, extent, minimum, maximum) {
  if (extent <= 0) return 0
  var step = extent / 20
  var first = Math.ceil((minimum || 0) / step) * step
  var last = Math.floor((maximum === undefined ? extent : maximum) / step) * step
  return Math.max(first, Math.min(last, Math.round(value / step) * step))
 }
 function snapPercent(value, extent) {
  if (extent <= 0) return 0
  return Math.max(0, Math.min(100, Math.round(value * 20 / extent) * 5))
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
 function centerPercent(name, axis, defaultValue) {
  var saved = positions[name]
  return saved && saved.length === 2 ? saved[axis] : defaultValue
 }
 function centeredLeft(name, itemWidth, defaultValue) {
  return Math.max(0, Math.min(root.width - itemWidth, root.width * centerPercent(name, 0, defaultValue) / 100 - itemWidth / 2))
 }
 function centeredTop(name, itemHeight, defaultValue) {
  return Math.max(0, Math.min(root.height - itemHeight, root.height * centerPercent(name, 1, defaultValue) / 100 - itemHeight / 2))
 }

 property var tiles: [
  {name:"link", defaultX:0, defaultY:0, text:root.linkLabel()},
  {name:"arm", defaultX:0, defaultY:6, text:"ARM: " + (telemetry.connected !== true ? "—" : ((telemetry.freshness || {}).armed === false ? "застаріло" : (telemetry.armed === null || telemetry.armed === undefined ? "—" : (telemetry.armed ? "активний" : "вимкнений"))))},
  {name:"mode", defaultX:0, defaultY:12, text:"Режим: " + root.telemetryText("flightMode", telemetry.flightMode)},
  {name:"battery", defaultX:0, defaultY:18, text:"АКБ: " + root.telemetryText("batteryVoltage", telemetry.batteryVoltage, " В", 1) + root.optionalTelemetryText("batteryRemaining", telemetry.batteryRemaining, "%", 0)},
  {name:"gps", defaultX:0, defaultY:24, text:"GPS: " + root.gpsFixDisplay() + root.optionalTelemetryText("satellites", telemetry.satellites, " супутн.", 0)},
  {name:"altitude", defaultX:0, defaultY:30, text:"Висота: " + root.telemetryText("altitude", telemetry.altitude, " м", 0)},
  {name:"speed", defaultX:0, defaultY:36, text:"Швидкість: " + root.telemetryText("groundSpeed", telemetry.groundSpeed, root.speedSuffix(), 1)},
  {name:"heading", defaultX:0, defaultY:42, text:"Напрямок: " + root.telemetryText("heading", telemetry.heading, "°", 0)},
  {name:"video", defaultX:0, defaultY:48, text:"Відео: " + (video.streamId ? (video.state === "playing" ? "активне" : "перевіряється") : "немає")},
  {name:"homeDistance", defaultX:0, defaultY:54, text:"До точки повернення: " + root.telemetryText("homeDistance", telemetry.homeDistance, " м", 0)}
 ]
 property var visibleTiles: root.tiles.filter(function(tileData) { return root.elementEnabled(tileData.name) })
 function tilePosition(tile, axis, index) {
  var saved = positions[tile.name]
  if (saved && saved.length === 2) return saved[axis]
  var value = axis === 0 ? tile.defaultX : tile.defaultY
  if (axis === 0 && corner.endsWith("right")) return 100 - value
  if (axis === 1 && corner.startsWith("bottom")) return 100 - value
  return value
 }
 Repeater {
  model: root.visibleTiles
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
     tile.movingX = root.gridPixel(point.x - offsetX, root.width, 0, root.width - tile.width)
     tile.movingY = root.gridPixel(point.y - offsetY, root.height, 0, root.height - tile.height)
    }
    onReleased: {
     var x = root.width > tile.width ? root.snapPercent(tile.x, root.width) : 0
     var y = root.height > tile.height ? root.snapPercent(tile.y, root.height) : 0
     root.positionChanged(tile.modelData.name, x, y)
     tile.moving = false
    }
    onCanceled: tile.moving = false
   }
  }
 }
 Item {
  id: horizon
  objectName: "osd-horizon"
  visible: root.elementEnabled("horizon")
  z: 2
  width: 176 * root.scaleFactor
  height: 94 * root.scaleFactor
  x: moving ? movingX - width / 2 : root.centeredLeft("horizon", width, 50)
  y: moving ? movingY - height / 2 : root.centeredTop("horizon", height, 48)
  property bool moving: false
  property real movingX: 0
  property real movingY: 0
  Rectangle {
   anchors.fill: parent
   radius: height / 2
   color: "#cc0b1522"
   border.color: root.editing ? "#80c5ff" : "#8093a6"
   clip: true
   Item {
    visible: root.attitudeAvailable()
    width: parent.width * 1.7
    height: parent.height * 2
    x: (parent.width - width) / 2
    y: (parent.height - height) / 2 + Number(root.telemetry.pitch) * root.scaleFactor * 1.4
    rotation: -Number(root.telemetry.roll)
    Rectangle { anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top; height: parent.height / 2; color: "#4b8db8" }
    Rectangle { anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom; height: parent.height / 2; color: "#697d48" }
    Rectangle { anchors.left: parent.left; anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter; height: 2 * root.scaleFactor; color: "#f6f1d8" }
   }
   Text {
    objectName: "osd-horizon-unavailable"
    anchors.centerIn: parent
    visible: !root.attitudeAvailable()
    text: "Нахил: немає даних"
    color: root.foreground
    font.pixelSize: 11 * root.scaleFactor
   }
   Rectangle { anchors.left: parent.left; anchors.leftMargin: parent.width * 0.18; anchors.verticalCenter: parent.verticalCenter; width: parent.width * 0.16; height: 2; color: root.foreground }
   Rectangle { anchors.right: parent.right; anchors.rightMargin: parent.width * 0.18; anchors.verticalCenter: parent.verticalCenter; width: parent.width * 0.16; height: 2; color: root.foreground }
  }
  MouseArea {
   anchors.fill: parent
   enabled: root.editing
   property real offsetX: 0
   property real offsetY: 0
   onPressed: function(event) { offsetX = horizon.width / 2 - event.x; offsetY = horizon.height / 2 - event.y; horizon.movingX = horizon.x + horizon.width / 2; horizon.movingY = horizon.y + horizon.height / 2; horizon.moving = true }
   onPositionChanged: function(event) {
    if (!pressed) return
    var point = mapToItem(root, event.x, event.y)
    horizon.movingX = root.gridPixel(point.x + offsetX, root.width, horizon.width / 2, root.width - horizon.width / 2)
    horizon.movingY = root.gridPixel(point.y + offsetY, root.height, horizon.height / 2, root.height - horizon.height / 2)
   }
   onReleased: { root.positionChanged("horizon", root.snapPercent(horizon.x + horizon.width / 2, root.width), root.snapPercent(horizon.y + horizon.height / 2, root.height)); horizon.moving = false }
   onCanceled: horizon.moving = false
  }
 }
 Item {
  id: reticle
  objectName: "osd-reticle"
  visible: root.elementEnabled("reticle")
  z: 4
  width: 44 * root.scaleFactor
  height: 44 * root.scaleFactor
  x: moving ? movingX - width / 2 : root.centeredLeft("reticle", width, 50)
  y: moving ? movingY - height / 2 : root.centeredTop("reticle", height, 50)
  property bool moving: false
  property real movingX: 0
  property real movingY: 0
  Rectangle { anchors.horizontalCenter: parent.horizontalCenter; anchors.top: parent.top; width: 2; height: 13 * root.scaleFactor; color: "#cc08111b" }
  Rectangle { anchors.horizontalCenter: parent.horizontalCenter; anchors.bottom: parent.bottom; width: 2; height: 13 * root.scaleFactor; color: "#cc08111b" }
  Rectangle { anchors.verticalCenter: parent.verticalCenter; anchors.left: parent.left; width: 13 * root.scaleFactor; height: 2; color: "#cc08111b" }
  Rectangle { anchors.verticalCenter: parent.verticalCenter; anchors.right: parent.right; width: 13 * root.scaleFactor; height: 2; color: "#cc08111b" }
  Rectangle { anchors.horizontalCenter: parent.horizontalCenter; anchors.top: parent.top; width: 1; height: 12 * root.scaleFactor; color: "#72f4d5" }
  Rectangle { anchors.horizontalCenter: parent.horizontalCenter; anchors.bottom: parent.bottom; width: 1; height: 12 * root.scaleFactor; color: "#72f4d5" }
  Rectangle { anchors.verticalCenter: parent.verticalCenter; anchors.left: parent.left; width: 12 * root.scaleFactor; height: 1; color: "#72f4d5" }
  Rectangle { anchors.verticalCenter: parent.verticalCenter; anchors.right: parent.right; width: 12 * root.scaleFactor; height: 1; color: "#72f4d5" }
  Rectangle { anchors.centerIn: parent; width: 3 * root.scaleFactor; height: 3 * root.scaleFactor; radius: width / 2; color: "#72f4d5" }
  MouseArea {
   anchors.fill: parent
   enabled: root.editing
   property real offsetX: 0
   property real offsetY: 0
   onPressed: function(event) { offsetX = reticle.width / 2 - event.x; offsetY = reticle.height / 2 - event.y; reticle.movingX = reticle.x + reticle.width / 2; reticle.movingY = reticle.y + reticle.height / 2; reticle.moving = true }
   onPositionChanged: function(event) {
    if (!pressed) return
    var point = mapToItem(root, event.x, event.y)
    reticle.movingX = root.gridPixel(point.x + offsetX, root.width, reticle.width / 2, root.width - reticle.width / 2)
    reticle.movingY = root.gridPixel(point.y + offsetY, root.height, reticle.height / 2, root.height - reticle.height / 2)
   }
   onReleased: { root.positionChanged("reticle", root.snapPercent(reticle.x + reticle.width / 2, root.width), root.snapPercent(reticle.y + reticle.height / 2, root.height)); reticle.moving = false }
   onCanceled: reticle.moving = false
  }
 }
}
