import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Left strip of the flight screen: one square tile per source, no captions. Video streams at the
// top (only those the camera has now), sound, map and layouts at the bottom. A tile shows what the
// source is (an icon) and its number (1 is the main video; the same number is on its window).
// The name, what a click does and the settings appear under the mouse.
//   click — show in a window / close it (a closed stream is paused: no bitrate);
//   ⚙ in the tile's corner (under the mouse) or the right button — this source's settings.
// Dot in the corner: green — the picture plays, amber — waiting for it, none — paused.
// The camera's streams come and go here by themselves.
Rectangle {
 id: root
 signal openLayouts()
 signal openStreamSettings(var stream)
 signal openAudio()
 property color fg: "#f4f7fb"
 property color sub: "#b7c8da"
 property color green: "#27d59a"
 property color amber: "#ffb84d"
 implicitWidth: 64
 color: "#0b1420"
 border.color: "#1a2a3c"

 // Green dot: the picture plays; amber: waiting for it; none: the stream is paused (no bitrate).
 function dotFor(stream, slot) {
  if (stream.kind === "main") return linkMonitor.lost ? root.amber : root.green
  if (slot < 0) return "transparent"
  if (stream.kind === "map") return root.green
  var win = extraWindows.windows[slot] || {}
  return win.state === "playing" ? root.green : root.amber
 }
 function iconFor(kind) {
  return kind === "map" || kind === "thermal" || kind === "usb" || kind === "sound" ? kind : "main"
 }

 component Tile: Button {
  id: tile
  property string iconKind: "main"
  property int number: 0
  property bool on: false
  property bool muted: false
  property bool settings: true
  property color dot: "transparent"
  property string hint: ""
  signal settingsRequested()
  Layout.alignment: Qt.AlignHCenter
  implicitWidth: 50
  implicitHeight: 50
  padding: 0
  hoverEnabled: true
  opacity: enabled ? 1 : 0.4
  background: Rectangle {
   radius: 12
   color: tile.on ? "#123627" : (tile.hovered ? "#192a3d" : "#0f1a28")
   border.color: tile.on ? root.green : (tile.hovered ? "#3f5c79" : "#1e3045")
   border.width: tile.on ? 1.5 : 1
  }
  contentItem: Item {
   SidebarIcon {
    anchors.centerIn: parent
    width: 26; height: 26
    kind: tile.iconKind
    muted: tile.muted
    color: tile.on ? root.green : (tile.hovered ? root.fg : root.sub)
   }
   Rectangle { // the source's number, the same as on its window
    visible: tile.number > 0
    anchors.right: parent.right; anchors.bottom: parent.bottom; anchors.margins: 3
    width: 15; height: 15; radius: 5
    color: tile.on ? root.green : "#22364b"
    Text { anchors.centerIn: parent; text: tile.number; color: tile.on ? "#06130d" : root.fg; font.pixelSize: 10; font.bold: true }
   }
   Rectangle { // state dot
    visible: tile.dot.a > 0
    anchors.right: parent.right; anchors.top: parent.top; anchors.margins: 4
    width: 8; height: 8; radius: 4
    color: tile.dot
    border.color: "#0b1420"; border.width: 1
   }
   Button { // settings, only under the mouse
    objectName: "sideSettings"
    visible: tile.settings && (tile.hovered || hovered)
    anchors.left: parent.left; anchors.top: parent.top; anchors.margins: 2
    width: 18; height: 18; padding: 0
    hoverEnabled: true
    background: Rectangle { radius: 9; color: parent.hovered ? "#3f5c79" : "#e0192a3d"; border.color: "#3f5c79" }
    contentItem: Text { text: "⚙"; color: root.fg; font.pixelSize: 11; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
    onClicked: tile.settingsRequested()
   }
   TapHandler { acceptedButtons: Qt.RightButton; onTapped: if (tile.settings) tile.settingsRequested() }
  }
  HoverHint { text: tile.hint; delay: 500 }
 }

 readonly property var videoSources: extraWindows.sources.filter(function(x) { return x.kind !== "map" })
 readonly property var mapSource: extraWindows.sources.filter(function(x) { return x.kind === "map" })[0] || ({ id: "map", kind: "map", name: "Карта", slot: -1 })

 component SourceTile: Tile {
  property var source: ({})
  iconKind: root.iconFor(source.kind)
  number: source.number || 0
  on: source.slot >= 0
  enabled: on || extraWindows.openCount < 3
  dot: root.dotFor(source, source.slot)
  settings: source.kind !== "map"
  hint: (source.number ? source.number + " · " : "") + (source.name || "") + " — "
        + (source.slot >= 0 ? "клік закриває" + (source.kind !== "map" ? ", потік стане на паузу." : ".")
                            : (enabled ? "клік показує у вікні." : "вже відкрито три вікна."))
  onClicked: source.slot >= 0 ? extraWindows.close(source.slot) : extraWindows.open(source.id)
  onSettingsRequested: root.openStreamSettings(source)
 }

 // Top: the video streams — the main one, then the camera's others (only those it has now).
 Flickable {
  anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top
  anchors.bottom: bottomGroup.top
  anchors.topMargin: 7; anchors.bottomMargin: 7
  contentHeight: list.implicitHeight
  clip: true
  ColumnLayout {
   id: list
   width: parent.width
   spacing: 7
   Tile {
    objectName: "sideMain"
    on: true
    number: 1
    dot: root.dotFor({ kind: "main" }, 0)
    readonly property var stream: ({ id: streamWorkspace.state.primaryId || "", name: extraWindows.mainName || "Основне відео", kind: "main", channel: 0 })
    hint: "1 · " + stream.name + " — на великому екрані. ⚙ — пресети якості."
    onSettingsRequested: root.openStreamSettings(stream)
   }
   Repeater {
    model: root.videoSources
    delegate: SourceTile {
     required property var modelData
     objectName: "sideStream"
     source: modelData
    }
   }
  }
 }

 // Bottom: sound, map, layouts.
 ColumnLayout {
  id: bottomGroup
  anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom
  anchors.bottomMargin: 8
  spacing: 7
  Rectangle { Layout.alignment: Qt.AlignHCenter; Layout.preferredWidth: 34; Layout.preferredHeight: 1; color: "#22364b" }
  Tile {
   objectName: "sideSound"
   visible: cameraFeatures.audioSupported
   iconKind: "sound"
   on: cameraFeatures.micEnabled && !cameraAudio.muted
   muted: cameraAudio.muted || !cameraFeatures.micEnabled
   dot: cameraAudio.playing ? root.green : (on ? root.amber : "transparent")
   hint: "Звук з камери: " + cameraAudio.text + ". " + (cameraFeatures.micEnabled ? (cameraAudio.muted ? "Клік — увімкнути (M)." : "Клік — вимкнути (M).") : "⚙ — увімкнути мікрофон.")
   onClicked: cameraFeatures.micEnabled ? cameraAudio.toggleMute() : root.openAudio()
   onSettingsRequested: root.openAudio()
  }
  SourceTile { objectName: "sideMap"; source: root.mapSource }
  Tile {
   objectName: "sideLayouts"
   iconKind: "layouts"
   settings: false
   hint: "Розташування вікон: зберегти поточне, відкрити збережене, як минулого разу"
   onClicked: root.openLayouts()
  }
 }
}
