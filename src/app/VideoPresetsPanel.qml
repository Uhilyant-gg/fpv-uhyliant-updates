import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Video presets of the camera in flight: key 1 is Auto, nine slots on the keys 2…0 from the weakest link (2) up.
// Applying one writes it into the camera; the station re-opens the video by itself.
Item {
 id: root
 signal closeRequested()
 property color fg: "#f4f7fb"
 property color sub: "#b7c8da"
 property color green: "#27d59a"
 property color red: "#ff6678"
 property color line: "#2f4860"
 property string editKey: ""

 function mbps(kbps) { return (Math.round(kbps / 102.4) / 10).toString().replace(".", ",") }
 function describe(slot) {
  return slot.empty ? "порожній" : slot.size.replace("x", "×") + " · " + slot.fps + " к/с · " + mbps(slot.bitrateKbps) + " Мбіт/с · повний кадр кожні " + String(slot.gopS).replace(".", ",") + " с"
 }
 function startEdit(slot) {
  editKey = slot.key
  nameField.text = slot.empty ? "" : slot.name
  sizeBox.currentIndex = Math.max(0, videoPresets.sizes.indexOf(slot.empty ? "1280x720" : slot.size))
  fpsBox.currentIndex = Math.max(0, videoPresets.fpsChoices.indexOf(slot.empty ? 30 : slot.fps))
  bitrateBox.value = slot.empty ? 2048 : slot.bitrateKbps
  gopBox.currentIndex = Math.max(0, videoPresets.gopChoices.indexOf(slot.empty ? 1 : slot.gopS))
 }

 ColumnLayout {
  anchors.fill: parent
  spacing: 10

  RowLayout {
   Layout.fillWidth: true
   Text { text: "ПРЕСЕТИ ВІДЕО · " + (devicesModel.activeName || "камера не вибрана"); color: root.fg; font.pixelSize: 20; font.bold: true; Layout.fillWidth: true; elide: Text.ElideRight }
   Button { objectName: "closeVideoPresets"; text: "Закрити"; onClicked: root.closeRequested() }
  }
  Text {
   text: "Клавіша 1 — «Авто», клавіші 2…0 — пресети від найслабшого каналу (2). Пресет записується в саму камеру, відео відновиться саме за секунду-дві. Вибір пресету пілотом вимикає «Авто»."
   color: root.sub; wrapMode: Text.Wrap; Layout.fillWidth: true
  }
  Switch {
   objectName: "videoPresetsAuto"
   text: "1 · Авто: станція сама перемикає ці пресети за станом каналу"
   checked: videoPresets.auto
   onToggled: checked ? videoPresets.choose("1") : videoPresets.setAuto(false)
  }
  Text {
   objectName: "videoPresetsMessage"
   visible: videoPresets.message !== ""
   text: videoPresets.message
   color: videoPresets.messageOk ? root.green : root.red
   wrapMode: Text.Wrap; Layout.fillWidth: true
  }

  ListView {
   id: list
   Layout.fillWidth: true
   Layout.fillHeight: true
   clip: true
   spacing: 4
   model: videoPresets.slots
   delegate: Rectangle {
    objectName: "videoPresetSlot"
    width: list.width
    height: 46
    radius: 7
    color: modelData.key === videoPresets.activeKey ? "#1d3a2f" : "#132235"
    border.color: modelData.key === root.editKey ? "#7897b5" : root.line
    RowLayout {
     anchors.fill: parent
     anchors.leftMargin: 10
     anchors.rightMargin: 6
     spacing: 10
     Text { text: modelData.key; color: root.fg; font.pixelSize: 18; font.bold: true; Layout.preferredWidth: 18 }
     ColumnLayout {
      spacing: 0
      Layout.fillWidth: true
      Text { text: modelData.empty ? "—" : modelData.name; color: root.fg; font.pixelSize: 14; font.bold: true }
      Text { text: root.describe(modelData); color: root.sub; font.pixelSize: 11; elide: Text.ElideRight; Layout.fillWidth: true }
     }
     Button { objectName: "videoPresetApply"; text: "Застосувати"; enabled: !modelData.empty && !videoPresets.busy; onClicked: videoPresets.choose(modelData.key) }
     Button { objectName: "videoPresetEdit"; text: "Змінити"; onClicked: root.startEdit(modelData) }
    }
   }
  }

  Rectangle {
   objectName: "videoPresetEditor"
   visible: root.editKey !== ""
   Layout.fillWidth: true
   implicitHeight: editor.implicitHeight + 20
   radius: 8
   color: "#0f1c2b"
   border.color: root.line
   ColumnLayout {
    id: editor
    anchors.fill: parent
    anchors.margins: 10
    spacing: 6
    Text { text: "Слот " + root.editKey; color: root.fg; font.bold: true }
    RowLayout {
     spacing: 8
     TextField { id: nameField; objectName: "videoPresetName"; placeholderText: "Назва"; Layout.preferredWidth: 160 }
     ComboBox { id: sizeBox; objectName: "videoPresetSize"; model: videoPresets.sizes; displayText: currentText.replace("x", "×") }
     ComboBox { id: fpsBox; objectName: "videoPresetFps"; model: videoPresets.fpsChoices; displayText: currentText + " к/с" }
     SpinBox { id: bitrateBox; objectName: "videoPresetBitrate"; from: 256; to: 20000; stepSize: 256; editable: true; textFromValue: function(v) { return v + " кбіт/с" }; valueFromText: function(t) { return parseInt(t) } }
     ComboBox { id: gopBox; objectName: "videoPresetGop"; model: videoPresets.gopChoices; displayText: "кадр кожні " + currentText.replace(".", ",") + " с" }
    }
    RowLayout {
     spacing: 8
     Button {
      objectName: "videoPresetSave"
      text: "Зберегти"
      onClicked: if (videoPresets.saveSlot(root.editKey, {name: nameField.text, size: sizeBox.currentText, fps: Number(fpsBox.currentText), bitrateKbps: bitrateBox.value, gopS: Number(gopBox.currentText)})) root.editKey = ""
     }
     Button { objectName: "videoPresetClear"; text: "Очистити слот"; onClicked: { videoPresets.clearSlot(root.editKey); root.editKey = "" } }
     Button { text: "Скасувати"; onClicked: root.editKey = "" }
    }
   }
  }
 }
}
