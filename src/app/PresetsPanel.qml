import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

Item {
 id: root
 signal closeRequested()
 property color fg: "#f4f7fb"
 property color sub: "#8fa1b7"
 property color line: "#273d55"
 property color blue: "#2387ff"
 property color green: "#3ddc97"
 property color amber: "#ffbf4a"
 property color red: "#ff6678"
 property string renamingId: ""
 property string exportId: ""
 property string deleteId: ""

 ColumnLayout {
  anchors.fill: parent
  spacing: 10

  RowLayout {
   Layout.fillWidth: true
   Text { text: "ПРЕСЕТИ"; color: root.fg; font.pixelSize: 20; font.bold: true; Layout.fillWidth: true }
   Button { text: "Закрити"; onClicked: root.closeRequested() }
  }
  Text {
   text: "Пресет — це налаштування OSD і попереджень під конкретний дрон. Налаштуйте один раз, збережіть і перемикайтеся між дронами одним натиском."
   color: root.sub; wrapMode: Text.WordWrap; Layout.fillWidth: true
  }

  Rectangle {
   Layout.fillWidth: true
   implicitHeight: activeRow.implicitHeight + 20
   radius: 10
   color: "#132235"
   border.color: presetsRuntime.dirty ? root.amber : root.line
   RowLayout {
    id: activeRow
    anchors.fill: parent
    anchors.margins: 10
    Text {
     objectName: "activePresetText"
     text: presetsRuntime.activeName
      ? "Активний: " + presetsRuntime.activeName + (presetsRuntime.dirty ? " · є незбережені зміни" : "")
      : "Активного пресета немає"
     color: presetsRuntime.dirty ? root.amber : root.fg
     wrapMode: Text.WordWrap; Layout.fillWidth: true
    }
    Button {
     objectName: "saveToActivePreset"
     visible: presetsRuntime.activeName !== ""
     enabled: presetsRuntime.dirty
     highlighted: presetsRuntime.dirty
     text: "Зберегти зміни"
     onClicked: presetsRuntime.saveToActive()
    }
   }
  }

  RowLayout {
   Layout.fillWidth: true
   TextField {
    id: newName
    objectName: "newPresetName"
    Layout.fillWidth: true
    placeholderText: "Назва нового пресета, напр. «Квадрик 5\"»"
    maximumLength: 60
    onAccepted: createButton.clicked()
   }
   Button {
    id: createButton
    objectName: "createPreset"
    text: "Створити з поточних"
    onClicked: if (presetsRuntime.createPreset(newName.text)) newName.text = ""
   }
   Button { text: "Імпорт…"; onClicked: importDialog.open() }
  }

  ListView {
   id: list
   objectName: "presetList"
   Layout.fillWidth: true
   Layout.fillHeight: true
   clip: true
   spacing: 6
   model: presetsRuntime.presets
   delegate: Rectangle {
    required property var modelData
    width: ListView.view.width
    height: 52
    radius: 8
    color: modelData.active ? "#16314a" : "#0f1b2a"
    border.color: modelData.active ? root.blue : root.line
    RowLayout {
     anchors.fill: parent
     anchors.margins: 8
     spacing: 6
     Text {
      visible: root.renamingId !== modelData.id
      text: (modelData.active ? "● " : "") + modelData.name
      color: root.fg; font.bold: modelData.active; elide: Text.ElideRight; Layout.fillWidth: true
     }
     TextField {
      id: renameField
      visible: root.renamingId === modelData.id
      text: modelData.name
      maximumLength: 60
      Layout.fillWidth: true
      onAccepted: if (presetsRuntime.renamePreset(modelData.id, text)) root.renamingId = ""
     }
     Button {
      visible: !modelData.active && root.renamingId !== modelData.id
      text: "Застосувати"
      highlighted: true
      onClicked: presetsRuntime.selectPreset(modelData.id)
     }
     Button {
      text: root.renamingId === modelData.id ? "OK" : "Назва"
      flat: true
      onClicked: {
       if (root.renamingId === modelData.id) {
        if (presetsRuntime.renamePreset(modelData.id, renameField.text)) root.renamingId = ""
       } else {
        root.renamingId = modelData.id
       }
      }
     }
     Button { text: "Копія"; flat: true; onClicked: presetsRuntime.duplicatePreset(modelData.id) }
     Button {
      text: "Експорт"
      flat: true
      onClicked: {
       root.exportId = modelData.id
       exportDialog.open()
      }
     }
     Button { text: "✕"; flat: true; onClicked: { root.deleteId = modelData.id; deleteConfirm.open() } }
    }
   }
   Text {
    anchors.centerIn: parent
    visible: list.count === 0
    text: "Пресетів ще немає. Налаштуйте OSD і попередження, введіть назву й натисніть «Створити з поточних»."
    color: root.sub; wrapMode: Text.WordWrap; width: parent.width * 0.8; horizontalAlignment: Text.AlignHCenter
   }
  }

  Text {
   objectName: "presetMessage"
   visible: presetsRuntime.message !== ""
   text: presetsRuntime.message
   color: presetsRuntime.messageOk ? root.green : root.red
   wrapMode: Text.WordWrap; Layout.fillWidth: true
  }
 }

 FileDialog {
  id: exportDialog
  title: "Експортувати пресет"
  fileMode: FileDialog.SaveFile
  nameFilters: ["Пресет FPV Uhyliant (*.fpvpreset)"]
  defaultSuffix: "fpvpreset"
  onAccepted: presetsRuntime.exportPreset(root.exportId, selectedFile.toString())
 }
 FileDialog {
  id: importDialog
  title: "Імпортувати пресет"
  fileMode: FileDialog.OpenFile
  nameFilters: ["Пресет FPV Uhyliant (*.fpvpreset)", "Усі файли (*)"]
  onAccepted: presetsRuntime.importPreset(selectedFile.toString())
 }
 Popup {
  id: deleteConfirm
  modal: true
  anchors.centerIn: parent
  padding: 16
  background: Rectangle { color: "#0d1725"; border.color: root.red; radius: 12 }
  contentItem: ColumnLayout {
   spacing: 12
   Text { text: "Видалити пресет? Цю дію не можна скасувати."; color: root.fg; wrapMode: Text.WordWrap; Layout.preferredWidth: 320 }
   RowLayout {
    Button { text: "Видалити"; onClicked: { presetsRuntime.deletePreset(root.deleteId); deleteConfirm.close() } }
    Button { text: "Скасувати"; flat: true; onClicked: deleteConfirm.close() }
   }
  }
 }
}
