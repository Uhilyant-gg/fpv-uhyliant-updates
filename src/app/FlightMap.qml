import QtQuick
import QtCore
import QtLocation
import QtPositioning

// Satellite map (Esri World Imagery) for a flight window. Mouse wheel zooms, dragging pans.
// Tiles are kept on this PC, so places already seen open without the internet; downloading
// whole areas in advance comes with the map stage. The drone's own position will be drawn
// here once the flight controller's or Starlink's coordinates reach the station.
Item {
 id: root
 clip: true

 Settings {
  id: saved
  // Its own small file: the station's other settings are not touched.
  location: StandardPaths.writableLocation(StandardPaths.AppLocalDataLocation) + "/flight-map.ini"
  category: "flightMap"
  property real lat: 48.5
  property real lon: 31.2
  property real zoom: 6
 }

 Plugin {
  id: satellite
  name: "osm"
  PluginParameter { name: "osm.mapping.custom.host"; value: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/%z/%y/%x" }
  PluginParameter { name: "osm.mapping.providersrepository.disabled"; value: true }
  PluginParameter { name: "osm.mapping.cache.directory"; value: StandardPaths.writableLocation(StandardPaths.AppLocalDataLocation).toString().replace("file://", "") + "/map-tiles" }
  PluginParameter { name: "osm.useragent"; value: "FPV-Uhyliant-ground-station" }
 }

 MapView {
  id: view
  objectName: "flightMapView"
  anchors.fill: parent
  map.plugin: satellite
  map.activeMapType: map.supportedMapTypes.length > 0 ? map.supportedMapTypes[map.supportedMapTypes.length - 1] : null
  map.center: QtPositioning.coordinate(saved.lat, saved.lon)
  map.zoomLevel: saved.zoom
  map.copyrightsVisible: false
  Component.onDestruction: { saved.lat = map.center.latitude; saved.lon = map.center.longitude; saved.zoom = map.zoomLevel }
 }

 Rectangle {
  anchors.right: parent.right; anchors.bottom: parent.bottom
  width: credit.implicitWidth + 8; height: credit.implicitHeight + 2
  color: "#99000000"
  Text { id: credit; anchors.centerIn: parent; text: "© Esri, Maxar, Earthstar Geographics"; color: "#dddddd"; font.pixelSize: 9 }
 }
}
