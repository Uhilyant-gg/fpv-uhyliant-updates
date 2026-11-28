import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Left strip of the flight screen. At the top the main stream and the camera's sound, then the
// camera's other streams (they appear here by themselves when the camera has them) and the map:
// a click opens a window, another closes it (a closed stream is stopped, no bitrate). A dot in the
// corner: green — the picture plays, amber — waiting for it. ⚙ under a tile opens its settings.
Rectangle {
 id: root
 signal openLayouts()
 signal openStreamSettings(var stream)
 signal openAudio()
 property color fg: "#f4f7fb"
 property color sub: "#b7c8da"
 property color green: "#27d59a"
 color: "#0b1420"
 border.color: "#22364b"

 property color amber: "#ffb84d"
 implicitWidth: 76

 // Green dot: the picture plays; amber: waiting for it; none: the stream is paused (no bitrate).
 function dotFor(stream, slot) {
  if (stream.kind === "main") return linkMonitor.lost ? root.amber : root.green
  if (slot < 0) return "transparent"
  if (stream.kind === "map") return root.green
  var win = extraWindows.windows[slot] || {}
  return win.state === "playing" ? root.green : root.amber
 }

 component StreamTile: ColumnLayout {
  id: tile
  property var stream: ({})
  property bool on: false
  property bool main: false
  property bool settings: true
  property string iconKind: stream.kind === "secondary" ? "sub" : (stream.kind || "sub")
  property color dot: "transparent"
  property string hint: ""
  property bool muted: false
  signal toggled()
  signal settingsRequested()
  Layout.fillWidth: true
  spacing: 1
  Button {
   objectName: tile.main ? "sideMain" : (tile.iconKind === "sound" ? "sideSound" : "sideStream")
   Layout.fillWidth: true
   Layout.preferredHeight: 54
   padding: 2
   enabled: tile.main || tile.on || tile.iconKind === "sound" || extraWindows.openCount < 3
   opacity: enabled ? 1 : 0.45
   background: Rectangle {
    radius: 9
    color: tile.on ? "#173528" : (parent.hovered ? "#1d3047" : "#111e2e")
    border.color: tile.on ? root.green : (parent.hovered ? "#4f6c88" : "#22364b")
    border.width: tile.on ? 1.5 : 1
    Rectangle { // state dot
     visible: tile.dot.a > 0
     anchors.right: parent.right; anchors.top: parent.top; anchors.margins: 5
     width: 7; height: 7; radius: 4
     color: tile.dot
    }
   }
   contentItem: Column {
    spacing: 2
    topPadding: 4
    SidebarIcon {
     anchors.horizontalCenter: parent.horizontalCenter
     width: 24; height: 24
     kind: tile.iconKind
     muted: tile.muted
     color: tile.on ? root.green : root.fg
    }
    Text {
     width: parent.width
     horizontalAlignment: Text.AlignHCenter
     text: tile.stream.name || ""
     color: tile.on ? root.fg : root.sub
     font.pixelSize: 10
     wrapMode: Text.Wrap; maximumLineCount: 2; elide: Text.ElideRight
     lineHeight: 0.9
    }
   }
   onClicked: tile.toggled()
   HoverHint { text: tile.hint }
  }
  Button {
   objectName: "sideSettings"
   visible: tile.settings
   Layout.alignment: Qt.AlignHCenter
   Layout.preferredWidth: 40
   Layout.preferredHeight: 16
   padding: 0
   text: "⚙"
   font.pixelSize: 11
   contentItem: Text { text: parent.text; font: parent.font; color: parent.hovered ? root.fg : "#7f96ad"; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
   background: Rectangle { radius: 5; color: parent.hovered ? "#22364b" : "transparent" }
   onClicked: tile.settingsRequested()
   HoverHint { text: "Налаштування: " + (tile.stream.name || "потік") }
  }
 }

 Flickable {
  anchors.fill: parent
  anchors.margins: 6
  anchors.bottomMargin: 58
  contentHeight: list.implicitHeight
  clip: true
  ColumnLayout {
   id: list
   width: parent.width
   spacing: 6
   StreamTile {
    main: true
    on: true
    dot: root.dotFor(stream, 0)
    stream: ({ id: streamWorkspace.state.primaryId || "", name: extraWindows.mainName || "Основне", kind: "main", channel: 0 })
    hint: "Основне відео: завжди на екрані. ⚙ — пресети якості."
    onSettingsRequested: root.openStreamSettings(stream)
   }
   StreamTile {
    objectName: "sideSoundTile"
    visible: cameraFeatures.audioSupported
    iconKind: "sound"
    on: cameraFeatures.micEnabled && !cameraAudio.muted
    muted: cameraAudio.muted || !cameraFeatures.micEnabled
    dot: cameraAudio.playing ? root.green : (on ? root.amber : "transparent")
    stream: ({ name: "Звук" })
    hint: (cameraFeatures.micEnabled ? (cameraAudio.muted ? "Увімкнути звук (M)" : "Вимкнути звук (M)") : "Мікрофон камери вимкнено: ⚙, щоб увімкнути") + " · " + cameraAudio.text
    onToggled: cameraFeatures.micEnabled ? cameraAudio.toggleMute() : root.openAudio()
    onSettingsRequested: root.openAudio()
   }
   Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: "#22364b" }
   Repeater {
    model: extraWindows.sources
    delegate: StreamTile {
     required property var modelData
     stream: modelData
     on: modelData.slot >= 0
     dot: root.dotFor(modelData, modelData.slot)
     settings: modelData.kind !== "map"
     hint: (modelData.slot >= 0 ? "Закрити: " : "Показати у вікні: ") + (modelData.name || "") + (modelData.slot >= 0 && modelData.kind !== "map" ? ". Потік стане на паузу і не витрачатиме бітрейт." : "")
     onToggled: modelData.slot >= 0 ? extraWindows.close(modelData.slot) : extraWindows.open(modelData.id)
     onSettingsRequested: root.openStreamSettings(modelData)
    }
   }
  }
 }

 Button {
  objectName: "sideLayouts"
  anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom
  anchors.margins: 6
  height: 44
  padding: 8
  background: Rectangle { radius: 8; color: parent.hovered ? "#22364b" : "#132235"; border.color: "#2f4860" }
  contentItem: SidebarIcon { kind: "layouts"; color: root.fg }
  onClicked: root.openLayouts()
  HoverHint { text: "Розташування вікон: зберегти поточне, відкрити збережене, як минулого разу" }
 }
}
