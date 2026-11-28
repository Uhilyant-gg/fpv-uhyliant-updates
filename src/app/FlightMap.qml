import QtQuick
import QtQuick.Controls
import QtCore
import QtLocation
import QtPositioning

// Satellite map (Esri World Imagery) for a flight window. Mouse wheel zooms, dragging pans.
// Tiles are kept on this PC, so places already seen open without the internet.
// The drone is drawn from its flight controller's GPS: an arrow along its heading, the trail it
// flew, its home point and a line home. "Follow" keeps it in the middle (dragging the map turns
// following off); "Course up" turns the map so the drone flies up the screen.
Item {
 id: root
 clip: true
 property var telemetry: (typeof telemetryRuntime !== "undefined" && telemetryRuntime) ? telemetryRuntime.telemetry : ({})
 readonly property bool hasDrone: telemetry.connected === true && isFinite(Number(telemetry.latitude)) && isFinite(Number(telemetry.longitude))
                                  && telemetry.latitude !== null && telemetry.longitude !== null
 readonly property var drone: hasDrone ? QtPositioning.coordinate(Number(telemetry.latitude), Number(telemetry.longitude)) : QtPositioning.coordinate()
 readonly property bool hasHome: isFinite(Number(telemetry.homeLatitude)) && telemetry.homeLatitude !== null && telemetry.homeLatitude !== undefined
 readonly property var home: hasHome ? QtPositioning.coordinate(Number(telemetry.homeLatitude), Number(telemetry.homeLongitude)) : QtPositioning.coordinate()
 readonly property real heading: isFinite(Number(telemetry.heading)) && telemetry.heading !== null ? Number(telemetry.heading) : 0
 property var trail: []
 // Every time the map opens it follows the drone; panning by hand turns that off until pressed again.
 property bool follow: true
 readonly property bool marksAvailable: typeof mapMarks !== "undefined" && mapMarks !== null
 property bool marksOpen: false
 // For checks: where the map looks and how it is turned.
 readonly property real centerLatitude: view.map.center.latitude
 readonly property real centerLongitude: view.map.center.longitude
 readonly property real mapBearing: view.map.bearing
 readonly property int trailLength: trail.length
 readonly property real zoom: view.map.zoomLevel
 function panTo(lat, lon) { view.map.center = QtPositioning.coordinate(lat, lon) }
 readonly property int trailMax: 600  // ten minutes at one point a second

 Settings {
  id: saved
  // Its own small file: the station's other settings are not touched.
  location: StandardPaths.writableLocation(StandardPaths.AppLocalDataLocation) + "/flight-map.ini"
  category: "flightMap"
  property real lat: 48.5
  property real lon: 31.2
  property real zoom: 6
  property bool courseUp: false
 }

 Plugin {
  id: satellite
  name: "osm"
  // The station's own map server on this PC keeps every tile it once loaded and fills the area
  // around the drone ahead of time; without it the map asks Esri directly.
  PluginParameter { name: "osm.mapping.custom.host"; value: typeof mapTiles !== "undefined" && mapTiles ? mapTiles.url : "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/%z/%y/%x" }
  PluginParameter { name: "osm.mapping.providersrepository.disabled"; value: true }
  // A real folder path from the station (a file:// URL turned into a path breaks on Windows: "/C:/...").
  PluginParameter { name: "osm.mapping.cache.directory"; value: typeof mapTilesDir !== "undefined" ? mapTilesDir : StandardPaths.writableLocation(StandardPaths.AppLocalDataLocation).toString().replace("file://", "") + "/map-tiles" }
  PluginParameter { name: "osm.useragent"; value: "FPV-Uhyliant-ground-station" }
 }

 // Once a second: a point of the trail, and the map follows the drone.
 Timer {
  interval: 1000
  repeat: true
  running: root.hasDrone
  triggeredOnStart: true
  onTriggered: {
   var points = root.trail.slice(Math.max(0, root.trail.length - root.trailMax + 1))
   var last = points.length ? points[points.length - 1] : null
   if (!last || last.distanceTo(root.drone) > 2) points.push(root.drone)
   root.trail = points
   if (root.follow) root.centreOnDrone()
  }
 }

 MapView {
  id: view
  objectName: "flightMapView"
  anchors.fill: parent
  map.plugin: satellite
  map.activeMapType: map.supportedMapTypes.length > 0 ? map.supportedMapTypes[map.supportedMapTypes.length - 1] : null
  map.center: QtPositioning.coordinate(saved.lat, saved.lon)
  map.zoomLevel: saved.zoom
  map.bearing: saved.courseUp && root.hasDrone ? root.heading : 0
  map.copyrightsVisible: false
  Component.onDestruction: { saved.lat = map.center.latitude; saved.lon = map.center.longitude; saved.zoom = map.zoomLevel }

  MapPolyline {
   objectName: "flightMapTrail"
   parent: view.map
   line.width: 3
   line.color: "#ccffb84d"
   path: root.trail
  }
  MapPolyline {
   objectName: "flightMapHomeLine"
   parent: view.map
   visible: root.hasDrone && root.hasHome
   line.width: 2
   line.color: "#cc27d59a"
   path: root.hasDrone && root.hasHome ? [root.drone, root.home] : []
  }
  MapItemView {
   parent: view.map
   model: root.marksAvailable ? mapMarks.marks : []
   delegate: MapQuickItem {
    required property var modelData
    coordinate: QtPositioning.coordinate(modelData.lat, modelData.lon)
    anchorPoint.x: pin.width / 2
    anchorPoint.y: pin.height
    sourceItem: Item {
     id: pin
     width: Math.max(24, label.implicitWidth + 10); height: 34
     Rectangle {
      anchors.horizontalCenter: parent.horizontalCenter
      width: parent.width; height: 22; radius: 6
      color: "#e6ff6678"; border.color: "white"; border.width: 1.5
      Text { id: label; anchors.centerIn: parent; text: modelData.name; color: "white"; font.bold: true; font.pixelSize: 12 }
     }
     Rectangle { anchors.horizontalCenter: parent.horizontalCenter; y: 22; width: 2; height: 12; color: "white" }
    }
   }
  }
  MapQuickItem {
   objectName: "flightMapHome"
   parent: view.map
   visible: root.hasHome
   coordinate: root.home
   anchorPoint.x: homeMark.width / 2
   anchorPoint.y: homeMark.height / 2
   sourceItem: Rectangle {
    id: homeMark
    width: 22; height: 22; radius: 11
    color: "#e627d59a"; border.color: "white"; border.width: 2
    Text { anchors.centerIn: parent; text: "H"; color: "#06130d"; font.bold: true; font.pixelSize: 12 }
   }
  }
  MapQuickItem {
   objectName: "flightMapDrone"
   parent: view.map
   visible: root.hasDrone
   coordinate: root.drone
   anchorPoint.x: arrow.width / 2
   anchorPoint.y: arrow.height / 2
   sourceItem: Canvas {
    id: arrow
    width: 30; height: 30
    // Turned along the heading, against the map's own turn.
    rotation: root.heading - view.map.bearing
    onPaint: {
     var ctx = getContext("2d")
     ctx.reset()
     ctx.beginPath()
     ctx.moveTo(15, 2); ctx.lineTo(27, 27); ctx.lineTo(15, 21); ctx.lineTo(3, 27); ctx.closePath()
     ctx.fillStyle = "#ffb84d"; ctx.fill()
     ctx.lineWidth = 2; ctx.strokeStyle = "#0b1420"; ctx.stroke()
    }
   }
  }
 }

 // Zoom with the mouse wheel or the laptop touchpad while the pointer is over the map: the place
 // under the pointer stays where it is; while following, the map zooms around the drone.
 // (Qt's own map takes only a mouse wheel on Windows, not a touchpad.)
 Item {
  objectName: "flightMapWheel"
  anchors.fill: parent
  z: 1
  TapHandler {
   // A right click marks the place: the station names it and shows its MGRS.
   acceptedButtons: Qt.RightButton
   enabled: root.marksAvailable
   onTapped: function(eventPoint) {
    var c = view.map.toCoordinate(eventPoint.position, false)
    if (c.isValid) mapMarks.addAt(c.latitude, c.longitude)
   }
  }
  WheelHandler {
   acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
   target: null
   onWheel: function(event) {
    var steps = event.angleDelta.y !== 0 ? event.angleDelta.y / 120 : event.pixelDelta.y / 60
    if (steps === 0) return
    root.zoomAt(steps, point.position)
    event.accepted = true
   }
  }
 }
 function zoomAt(steps, position) {
  var map = view.map
  var level = Math.max(map.minimumZoomLevel, Math.min(map.maximumZoomLevel, map.zoomLevel + steps))
  if (root.follow && root.hasDrone) {
   map.zoomLevel = level
   centreOnDrone()
   return
  }
  var under = map.toCoordinate(position, false)
  map.zoomLevel = level
  if (under.isValid) { centring = true; map.alignCoordinateToPoint(under, position); centring = false }
 }

 // Panning by hand turns following off; the pilot turns it back on with the button.
 // A move of the centre that the station did not make and that is not a zoom is the pilot's pan.
 property bool centring: false
 property real zoomedAt: 0
 function centreOnDrone() {
  centring = true
  // From a country-wide view straight to where the drone is: streets and fields.
  if (view.map.zoomLevel < 13) view.map.zoomLevel = 16
  view.map.center = root.drone
  centring = false
 }
 Connections {
  target: view.map
  function onZoomLevelChanged() { root.zoomedAt = Date.now(); viewSettled.restart() }
  function onCenterChanged() { if (!root.centring && root.follow) Qt.callLater(root.checkPan); viewSettled.restart() }
  function onWidthChanged() { viewSettled.restart() }
  function onHeightChanged() { viewSettled.restart() }
 }
 // Once the view stops moving: the station fetches what the window shows, and one level closer.
 Timer {
  id: viewSettled
  interval: 600
  onTriggered: {
   if (typeof mapTiles === "undefined" || !mapTiles) return
   var box = view.map.visibleRegion.boundingGeoRectangle()
   if (!box.isValid) return
   mapTiles.prefetchView(box.topLeft.latitude, box.topLeft.longitude, box.bottomRight.latitude, box.bottomRight.longitude, view.map.zoomLevel)
  }
 }
 function checkPan() { if (Date.now() - zoomedAt > 300) root.follow = false }

 Column {
  z: 2
  anchors.left: parent.left; anchors.top: parent.top; anchors.margins: 6
  anchors.topMargin: 28  // below the window's own handle strip
  spacing: 4
  component MapButton: Button {
   property bool on: false
   width: 34; height: 30; padding: 0
   font.pixelSize: 14
   background: Rectangle { radius: 6; color: parent.on ? "#e01d3a2f" : (parent.hovered ? "#e040566e" : "#cc132235"); border.color: parent.on ? "#27d59a" : "#5f7f9e" }
   contentItem: Text { text: parent.text; font: parent.font; color: "#f4f7fb"; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
  }
  MapButton {
   objectName: "flightMapFollow"
   text: "⌖"
   on: root.follow
   enabled: root.hasDrone
   opacity: enabled ? 1 : 0.5
   onClicked: { root.follow = !root.follow; if (root.follow) root.centreOnDrone() }
   HoverHint { text: root.follow ? "Карта стежить за дроном. Перетягніть карту, щоб роздивитися інше місце." : "Стежити за дроном"; delay: 500 }
  }
  MapButton {
   objectName: "flightMapCourseUp"
   text: saved.courseUp ? "↑" : "N"
   on: saved.courseUp
   onClicked: saved.courseUp = !saved.courseUp
   HoverHint { text: saved.courseUp ? "Карта повертається за курсом дрона. Натисніть — північ угорі." : "Північ угорі. Натисніть — карта за курсом дрона."; delay: 500 }
  }
  MapButton {
   objectName: "flightMapZoomIn"
   text: "+"
   onClicked: root.zoomAt(1, Qt.point(view.width / 2, view.height / 2))
   HoverHint { text: "Ближче (або колесо миші над картою)"; delay: 500 }
  }
  MapButton {
   objectName: "flightMapZoomOut"
   text: "−"
   onClicked: root.zoomAt(-1, Qt.point(view.width / 2, view.height / 2))
   HoverHint { text: "Далі (або колесо миші над картою)"; delay: 500 }
  }
  MapButton {
   objectName: "flightMapMarks"
   visible: root.marksAvailable
   text: "⚑"
   on: root.marksOpen
   onClicked: root.marksOpen = !root.marksOpen
   HoverHint { text: "Точки на карті: додати за координатами MGRS. Правий клік по карті теж ставить точку."; delay: 500 }
  }
 }

 Rectangle {
  objectName: "flightMapAhead"
  visible: typeof mapTiles !== "undefined" && mapTiles && mapTiles.downloading && root.hasDrone
  anchors.horizontalCenter: parent.horizontalCenter
  anchors.bottom: parent.bottom; anchors.bottomMargin: 18
  width: aheadText.implicitWidth + 16; height: aheadText.implicitHeight + 8; radius: 6
  color: "#cc0b1420"
  Text { id: aheadText; anchors.centerIn: parent; text: parent.visible ? mapTiles.text : ""; color: "#dddddd"; font.pixelSize: 11 }
 }

 Rectangle {
  objectName: "flightMapNoDrone"
  visible: !root.hasDrone
  anchors.horizontalCenter: parent.horizontalCenter
  anchors.bottom: parent.bottom; anchors.bottomMargin: 18
  width: noDrone.implicitWidth + 16; height: noDrone.implicitHeight + 8; radius: 6
  color: "#cc0b1420"
  Text { id: noDrone; anchors.centerIn: parent; text: "Чекаю координати від польотника"; color: "#dddddd"; font.pixelSize: 11 }
 }

 Rectangle {
  objectName: "flightMapMarksPanel"
  visible: root.marksOpen && root.marksAvailable
  z: 3
  anchors.left: parent.left; anchors.leftMargin: 46
  anchors.top: parent.top; anchors.topMargin: 28
  width: Math.min(300, parent.width - 56)
  height: Math.min(parent.height - 40, marksColumn.implicitHeight + 16)
  radius: 8
  color: "#ee0b1420"; border.color: "#5f7f9e"
  Column {
   id: marksColumn
   anchors.fill: parent; anchors.margins: 8
   spacing: 6
   Row {
    spacing: 6
    TextField {
     id: mgrsField
     objectName: "flightMapMgrsField"
     width: marksColumn.width - addButton.width - 6
     placeholderText: "MGRS, напр. 36U UA 24182 91607"
     font.pixelSize: 12
     onAccepted: if (mapMarks.addMgrs(text, "")) text = ""
    }
    Button { id: addButton; objectName: "flightMapMgrsAdd"; text: "＋"; width: 34; onClicked: if (mapMarks.addMgrs(mgrsField.text, "")) mgrsField.text = "" }
   }
   Text { visible: root.marksAvailable && mapMarks.message !== ""; text: root.marksAvailable ? mapMarks.message : ""; color: "#b7c8da"; font.pixelSize: 11; wrapMode: Text.Wrap; width: marksColumn.width }
   Repeater {
    model: root.marksAvailable ? mapMarks.marks : []
    delegate: Row {
     required property var modelData
     spacing: 6
     Button {
      width: marksColumn.width - 34
      height: 26; padding: 2
      contentItem: Text { text: modelData.name + "   " + modelData.mgrs; color: "#f4f7fb"; font.pixelSize: 12; elide: Text.ElideRight; verticalAlignment: Text.AlignVCenter }
      background: Rectangle { radius: 4; color: parent.hovered ? "#22364b" : "transparent" }
      onClicked: { root.follow = false; view.map.center = QtPositioning.coordinate(modelData.lat, modelData.lon) }
     }
     Button { width: 28; height: 26; text: "✕"; onClicked: mapMarks.remove(modelData.index) }
    }
   }
  }
 }

 // The wind at the drone's height: an arrow to where it blows, speed and gusts (no warnings).
 Rectangle {
  objectName: "flightMapWind"
  readonly property bool windAvailable: typeof windRuntime !== "undefined" && windRuntime !== null && windRuntime.available
  visible: windAvailable
  z: 2
  anchors.right: parent.right; anchors.top: parent.top; anchors.margins: 6
  anchors.topMargin: 28
  width: windRow.implicitWidth + 12; height: 30; radius: 6
  color: "#cc0b1420"; border.color: "#5f7f9e"
  Row {
   id: windRow
   anchors.centerIn: parent
   spacing: 6
   Text {
    text: "➜"
    color: "#7fd3ff"; font.pixelSize: 16; font.bold: true
    // Where the wind blows to, turned with the map.
    rotation: parent.parent.windAvailable ? windRuntime.wind.fromDeg + 180 - 90 - view.map.bearing : 0
   }
   Text {
    anchors.verticalCenter: parent.verticalCenter
    text: parent.parent.windAvailable ? (String(windRuntime.wind.speedMs).replace(".", ",") + " м/с" + (windRuntime.wind.gustMs ? " · пориви " + String(windRuntime.wind.gustMs).replace(".", ",") : "") + " · " + windRuntime.wind.levelM + " м") : ""
    color: "#f4f7fb"; font.pixelSize: 12; font.bold: true
   }
  }
  HoverHint { text: parent.windAvailable ? windRuntime.text + ". Прогноз Open-Meteo для точки дрона." : ""; delay: 500 }
 }

 Rectangle {
  objectName: "flightMapDroneMgrs"
  visible: root.hasDrone && root.marksAvailable
  anchors.left: parent.left; anchors.bottom: parent.bottom
  width: droneMgrs.implicitWidth + 10; height: droneMgrs.implicitHeight + 4
  color: "#99000000"
  Text { id: droneMgrs; anchors.centerIn: parent; text: root.marksAvailable && root.hasDrone ? "Дрон: " + mapMarks.mgrsOf(Number(root.telemetry.latitude), Number(root.telemetry.longitude)) : ""; color: "#f4f7fb"; font.pixelSize: 11; font.bold: true }
 }

 Rectangle {
  anchors.right: parent.right; anchors.bottom: parent.bottom
  width: credit.implicitWidth + 8; height: credit.implicitHeight + 2
  color: "#99000000"
  Text { id: credit; anchors.centerIn: parent; text: "© Esri, Maxar, Earthstar Geographics"; color: "#dddddd"; font.pixelSize: 9 }
 }
}
