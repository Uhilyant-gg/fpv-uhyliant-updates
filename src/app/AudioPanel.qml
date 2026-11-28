import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Sound from the camera: what the station plays (on/off, loudness on this PC) and the camera's
// own microphone (on/off, its sensitivity, quality). Changes on the camera restart its video
// for about a second, so the station says so next to them.
Item {
 id: root
 signal closeRequested()
 property color fg: "#f4f7fb"
 property color sub: "#b7c8da"
 property color green: "#27d59a"
 implicitWidth: 360
 implicitHeight: column.implicitHeight + 24

 component Choice: Button {
  property bool on: false
  implicitHeight: 34
  background: Rectangle { radius: 7; color: parent.on ? "#1d3a2f" : (parent.hovered ? "#22364b" : "#132235"); border.color: parent.on ? root.green : "#2f4860" }
  contentItem: Text { text: parent.text; color: root.fg; font.pixelSize: 12; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter; wrapMode: Text.Wrap }
 }

 ColumnLayout {
  id: column
  anchors.fill: parent
  anchors.margins: 12
  spacing: 8
  RowLayout {
   spacing: 8
   SidebarIcon { width: 22; height: 22; kind: "sound"; muted: cameraAudio.muted || !cameraFeatures.micEnabled; color: root.fg }
   Text { text: "Звук з камери"; color: root.fg; font.pixelSize: 16; font.bold: true }
  }
  Text { objectName: "audioState"; text: cameraAudio.text; color: cameraAudio.playing ? root.green : root.sub; font.pixelSize: 12; wrapMode: Text.Wrap; Layout.fillWidth: true }

  // --- on this PC ---
  Text { visible: cameraFeatures.audioSupported; text: "На станції"; color: root.sub; font.pixelSize: 12; font.bold: true }
  Switch {
   objectName: "audioPlay"
   visible: cameraFeatures.audioSupported
   text: "Грати звук (M)"
   checked: !cameraAudio.muted
   onToggled: cameraAudio.setMuted(!checked)
   Layout.fillWidth: true
  }
  RowLayout {
   visible: cameraFeatures.audioSupported
   Layout.fillWidth: true
   Text { text: "Гучність"; color: root.fg; font.pixelSize: 13; Layout.preferredWidth: 96 }
   Slider { objectName: "audioVolume"; from: 0; to: 100; stepSize: 5; value: cameraAudio.volume; onMoved: cameraAudio.setVolume(value); Layout.fillWidth: true }
   Text { text: cameraAudio.volume + "%"; color: root.sub; font.pixelSize: 12; Layout.preferredWidth: 36 }
  }

  // --- on the camera ---
  Text { visible: cameraFeatures.audioSupported; text: "Мікрофон камери"; color: root.sub; font.pixelSize: 12; font.bold: true; Layout.topMargin: 4 }
  Switch {
   objectName: "audioMic"
   visible: cameraFeatures.audioSupported
   text: "Мікрофон увімкнено"
   checked: cameraFeatures.micEnabled
   onToggled: cameraFeatures.setMicEnabled(checked)
   Layout.fillWidth: true
  }
  RowLayout {
   visible: cameraFeatures.audioSupported && cameraFeatures.micEnabled && cameraFeatures.micVolume >= 0
   Layout.fillWidth: true
   Text { text: "Чутливість"; color: root.fg; font.pixelSize: 13; Layout.preferredWidth: 96 }
   Slider {
    id: micSlider
    objectName: "audioMicVolume"
    from: 1; to: 100; stepSize: 1
    value: cameraFeatures.micVolume
    // Sent once the pilot lets go: every change restarts the camera's video for a moment.
    onPressedChanged: if (!pressed) cameraFeatures.setMicVolume(Math.round(value))
    Layout.fillWidth: true
   }
   Text { text: Math.round(micSlider.value); color: root.sub; font.pixelSize: 12; Layout.preferredWidth: 36 }
  }
  Text { visible: cameraFeatures.audioSupported && cameraFeatures.micEnabled; text: "Якість (скільки бітрейту бере звук)"; color: root.fg; font.pixelSize: 13 }
  RowLayout {
   visible: cameraFeatures.audioSupported && cameraFeatures.micEnabled
   Layout.fillWidth: true
   spacing: 6
   component RateChoice: Choice {
    property int rate: 8000
    objectName: "audioRate" + rate
    Layout.fillWidth: true
    implicitHeight: 42
    on: cameraFeatures.micRate === rate
    onClicked: cameraFeatures.setMicRate(rate)
   }
   RateChoice { rate: 8000; text: "Мова\n64 кбіт/с" }
   RateChoice { rate: 16000; text: "Чіткіше\n128 кбіт/с" }
   RateChoice { rate: 48000; text: "Найкраще\n384 кбіт/с" }
  }
  Text {
   visible: cameraFeatures.audioSupported
   text: "Зміни мікрофона застосовуються на камері: її відео на мить перезапуститься. Через Starlink краще «Мова»."
   color: root.sub; font.pixelSize: 11; wrapMode: Text.Wrap; Layout.fillWidth: true
  }
  Text { objectName: "audioMessage"; visible: cameraFeatures.message !== ""; text: cameraFeatures.message; color: root.green; font.pixelSize: 12 }
  RowLayout { Item { Layout.fillWidth: true } Button { text: "Закрити"; flat: true; onClicked: root.closeRequested() } }
 }
}
