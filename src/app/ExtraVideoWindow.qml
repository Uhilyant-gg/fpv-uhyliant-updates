import QtQuick
import QtQuick.Controls
import QtQuick.Window
import QtMultimedia

// One additional video window over the flight video, placed by the pilot.
// A click on the picture swaps it with the main video; dragging moves it; the corner
// handle resizes it. Small buttons appear while the mouse is over it and hide again.
Item {
 id: root
 property int slot: 0
 property var win: ({})
 property Item area
 property bool shownAsMain: false   // the main video sits in this window's place
 property bool canDetach: false
 // Above the OSD; the window used last lies on top of the others. Full screen covers everything but the banners.
 property int baseZ: 30
 // The main video, swapped into this window, lies just under the window's frame and buttons.
 readonly property real contentZ: baseZ - 0.5
 property color fg: "#f4f7fb"
 property color green: "#27d59a"
 property color amber: "#ffb84d"
 signal swapRequested(int slot)
 anchors.fill: parent
 visible: win.open === true
 // The whole window lies above the OSD; full screen covers everything but the banners.
 z: fullscreen ? 65 : baseZ

 readonly property bool fullscreen: win.fullscreen === true
 readonly property bool detached: win.detached === true
 readonly property real boxX: (win.x || 0) * width
 readonly property real boxY: (win.y || 0) * height
 readonly property real boxW: (win.w || 0.3) * width
 readonly property real boxH: boxW * 9 / 16
 readonly property bool playing: player.playbackState === MediaPlayer.PlayingState
 // Where the main video goes when it changes places with this window.
 readonly property rect windowRect: Qt.rect(boxX, boxY, boxW, boxH)

 MediaPlayer {
  id: player
  source: root.win.url || ""
  videoOutput: out
  onSourceChanged: if (source.toString() !== "") play(); else stop()
  onPlayingChanged: if (playing) { retry.stop(); extraWindows.markPlaying(root.slot) }
  onErrorOccurred: function(error, errorString) { extraWindows.playbackError(root.slot, errorString); retry.restart() }
 }
 Timer {
  id: retry
  interval: 1500
  onTriggered: if (root.win.open && extraWindows.reconnect(root.slot)) { player.stop(); player.play() } else if (root.win.open) restart()
 }
 // Moving the picture to another display: the player is re-opened there once.
 onDetachedChanged: { player.stop(); player.videoOutput = detached ? detachedOut : out; if (root.win.url) player.play() }

 Rectangle { // backdrop behind the small picture
  visible: !root.detached && !root.fullscreen && !root.shownAsMain
  x: root.boxX; y: root.boxY; width: root.boxW; height: root.boxH
  radius: 8; color: "black"; z: root.baseZ
 }
 Rectangle { // full screen hides the main video completely, even before the first frame
  visible: root.fullscreen && !root.detached
  anchors.fill: parent
  color: "black"
  z: 59
 }
 VideoOutput {
  id: out
  // On the big screen the stream goes under the OSD, like the main video normally is.
  parent: root.shownAsMain && !root.fullscreen ? root.parent : root
  objectName: "extraVideoOutput" + root.slot
  readonly property bool big: root.fullscreen || root.shownAsMain
  visible: !root.detached
  x: big ? 0 : root.boxX
  y: big ? 0 : root.boxY
  width: big ? root.width : root.boxW
  height: big ? root.height : root.boxH
  z: root.fullscreen ? 60 : (root.shownAsMain ? -1 : root.baseZ + 1)
  fillMode: VideoOutput.PreserveAspectFit
 }
 Text {
  visible: !root.playing && !root.detached
  x: root.fullscreen || root.shownAsMain ? (root.width - width) / 2 : root.boxX + (root.boxW - width) / 2
  y: root.fullscreen || root.shownAsMain ? (root.height - height) / 2 : root.boxY + (root.boxH - height) / 2
  z: root.fullscreen ? 61 : root.baseZ + 2
  text: (root.win.name || "Відео") + ": немає сигналу · відновлюю"
  color: root.fg; font.bold: true
 }

 // The frame the pilot handles: always where the window is (or over everything in full screen).
 Rectangle {
  id: frame
  objectName: "extraWindowFrame" + root.slot
  visible: !root.detached
  x: root.fullscreen ? 0 : root.boxX
  y: root.fullscreen ? 0 : root.boxY
  width: root.fullscreen ? root.width : root.boxW
  height: root.fullscreen ? root.height : root.boxH
  z: root.fullscreen ? 62 : root.baseZ + 3
  color: "transparent"
  radius: root.fullscreen ? 0 : 8
  border.width: root.fullscreen ? 0 : 2
  border.color: root.playing || root.shownAsMain ? root.green : root.amber

  HoverHandler { id: hover; onPointChanged: tools.restart(); onHoveredChanged: if (hovered) tools.restart() }
  Timer { id: tools; interval: 2000 }

  MouseArea {
   id: drag
   objectName: "extraWindowMouse" + root.slot
   anchors.fill: parent
   enabled: !root.fullscreen
   property point grab
   property real startX
   property real startY
   property bool moved: false
   onPressed: function(mouse) { grab = mapToItem(root, mouse.x, mouse.y); startX = root.boxX; startY = root.boxY; moved = false }
   onPositionChanged: function(mouse) {
    var p = mapToItem(root, mouse.x, mouse.y)
    var dx = p.x - grab.x, dy = p.y - grab.y
    if (!moved && Math.abs(dx) + Math.abs(dy) < 10) return
    moved = true
    frame.x = Math.max(0, Math.min(root.width - root.boxW, startX + dx))
    frame.y = Math.max(0, Math.min(root.height - root.boxH, startY + dy))
   }
   onReleased: {
    if (!moved) { root.swapRequested(root.slot); return }
    var snap = 16
    var x = frame.x, y = frame.y
    if (x < snap) x = 0
    if (root.width - root.boxW - x < snap) x = root.width - root.boxW
    if (y < snap) y = 0
    if (root.height - root.boxH - y < snap) y = root.height - root.boxH
    extraWindows.place(root.slot, x / root.width, y / root.height, root.boxW / root.width)
    frame.x = Qt.binding(function() { return root.fullscreen ? 0 : root.boxX })
    frame.y = Qt.binding(function() { return root.fullscreen ? 0 : root.boxY })
   }
  }

  Rectangle { // resize handle in the corner
   objectName: "extraWindowResize" + root.slot
   visible: !root.fullscreen && (hover.hovered || tools.running)
   width: 18; height: 18; radius: 4
   anchors.left: parent.left; anchors.bottom: parent.bottom; anchors.margins: 2
   color: "#cc22364b"; border.color: "#7897b5"
   Text { anchors.centerIn: parent; text: "◣"; color: root.fg; font.pixelSize: 11 }
   MouseArea {
    // Bottom-left corner: the window grows to the left and down, its top-right corner stays.
    anchors.fill: parent
    cursorShape: Qt.SizeBDiagCursor
    property real startW
    property real startX
    property real rightEdge
    onPressed: function(mouse) { startW = root.boxW; startX = mapToItem(root, mouse.x, mouse.y).x; rightEdge = root.boxX + root.boxW }
    onPositionChanged: function(mouse) {
     var w = Math.max(root.width * 0.12, Math.min(root.width * 0.7, rightEdge, startW - (mapToItem(root, mouse.x, mouse.y).x - startX)))
     frame.width = w; frame.height = w * 9 / 16; frame.x = rightEdge - w
    }
    onReleased: {
     extraWindows.place(root.slot, frame.x / root.width, root.boxY / root.height, frame.width / root.width)
     frame.x = Qt.binding(function() { return root.fullscreen ? 0 : root.boxX })
     frame.width = Qt.binding(function() { return root.fullscreen ? root.width : root.boxW })
     frame.height = Qt.binding(function() { return root.fullscreen ? root.height : root.boxH })
    }
   }
  }

  Row { // small buttons, only while the mouse is over the window
   objectName: "extraWindowTools" + root.slot
   visible: hover.hovered || tools.running
   anchors.right: parent.right; anchors.top: parent.top; anchors.margins: 4
   spacing: 3
   component Tool: Button {
    width: 28; height: 24; padding: 0; font.pixelSize: 13
    background: Rectangle { radius: 5; color: parent.hovered ? "#e040566e" : "#cc132235"; border.color: "#5f7f9e" }
   }
   Tool { objectName: "extraSwap" + root.slot; visible: !root.fullscreen; text: "⇄"; onClicked: root.swapRequested(root.slot); HoverHint { text: "Поміняти з основним відео (Tab)." } }
   Tool { objectName: "extraFullscreen" + root.slot; text: "⤢"; onClicked: extraWindows.setFullscreen(root.slot, !root.fullscreen); HoverHint { text: root.fullscreen ? "Повернути у вікно (Esc)." : "На весь екран." } }
   Tool { objectName: "extraDetach" + root.slot; visible: root.canDetach && !root.fullscreen; text: "⧉"; onClicked: extraWindows.setDetached(root.slot, true); HoverHint { text: "На другий дисплей." } }
   Tool { objectName: "extraClose" + root.slot; text: "✕"; onClicked: extraWindows.close(root.slot); HoverHint { text: "Закрити. Потік стане на паузу і не витрачатиме бітрейт." } }
  }
 }

 Window {
  id: detachedWindow
  visible: root.detached && root.win.open === true
  width: 960; height: 540
  title: (root.win.name || "Відео") + " · FPV Uhyliant"
  color: "black"
  onClosing: extraWindows.setDetached(root.slot, false)
  VideoOutput { id: detachedOut; anchors.fill: parent; fillMode: VideoOutput.PreserveAspectFit }
  Button {
   anchors.right: parent.right; anchors.top: parent.top; anchors.margins: 8
   text: "Повернути"
   onClicked: extraWindows.setDetached(root.slot, false)
  }
 }
}
