import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

Item {
 id: root
 signal closeRequested()
 property color fg: "#f4f7fb"
 property color sub: "#b7c8da"
 property color line: "#273d55"
 property color green: "#3ddc97"
 property color red: "#ff6678"

 ColumnLayout {
  anchors.fill: parent
  spacing: 12

  RowLayout {
   Layout.fillWidth: true
   Text { text: "ЗАПИС І ЧОРНА СКРИНЬКА"; color: root.fg; font.pixelSize: 20; font.bold: true; Layout.fillWidth: true }
   Button { objectName: "closeRecording"; text: "Закрити"; onClicked: root.closeRequested() }
  }

  Text {
   text: "Запис вмикається і зупиняється кнопкою «● REC» на екрані польоту або клавішею F9. Відео зберігається у форматі MP4 саме таким, яким його видно на екрані."
   color: root.sub
   wrapMode: Text.WordWrap
   Layout.fillWidth: true
  }

  Rectangle {
   Layout.fillWidth: true
   implicitHeight: folderColumn.implicitHeight + 24
   radius: 12
   color: "#132235"
   border.color: root.line
   ColumnLayout {
    id: folderColumn
    anchors.fill: parent
    anchors.margins: 12
    spacing: 8
    Text { text: "Папка для записів"; color: root.sub; font.pixelSize: 13 }
    Text {
     objectName: "recordingFolderText"
     text: dvrRuntime.folder + (dvrRuntime.folderIsDefault ? "  (типова)" : "")
     color: root.fg
     font.pixelSize: 15
     font.bold: true
     wrapMode: Text.WrapAnywhere
     Layout.fillWidth: true
    }
    RowLayout {
     Layout.fillWidth: true
     spacing: 8
     Button { objectName: "chooseRecordingFolder"; text: "Змінити папку…"; enabled: !dvrRuntime.recording; onClicked: folderDialog.open() }
     Button { objectName: "openRecordingFolder"; text: "Відкрити папку"; onClicked: dvrRuntime.openFolder() }
     Button { objectName: "resetRecordingFolder"; text: "Типова папка"; enabled: !dvrRuntime.folderIsDefault && !dvrRuntime.recording; onClicked: dvrRuntime.resetFolder() }
     Item { Layout.fillWidth: true }
    }
   }
  }

  Rectangle {
   Layout.fillWidth: true
   implicitHeight: boxColumn.implicitHeight + 24
   radius: 12
   color: "#132235"
   border.color: root.line
   ColumnLayout {
    id: boxColumn
    anchors.fill: parent
    anchors.margins: 12
    spacing: 8
    Text { text: "Чорна скринька"; color: root.sub; font.pixelSize: 13 }
    Text {
     text: "Кожен політ сам записується в окрему папку: що було з відео, зв’язком, Starlink і польотником щосекунди, усі події і короткий підсумок. Зберігаються останні 200 польотів."
     color: root.sub; font.pixelSize: 12; wrapMode: Text.WordWrap; Layout.fillWidth: true
    }
    Text {
     objectName: "blackBoxFolderText"
     text: blackBox.folder + (blackBox.folderIsDefault ? "  (типова)" : "")
     color: root.fg; font.pixelSize: 15; font.bold: true; wrapMode: Text.WrapAnywhere; Layout.fillWidth: true
    }
    RowLayout {
     Layout.fillWidth: true
     spacing: 8
     Button { objectName: "chooseBlackBoxFolder"; text: "Змінити папку…"; enabled: !blackBox.active; onClicked: boxDialog.open() }
     Button { objectName: "openBlackBoxFolder"; text: "Відкрити папку"; onClicked: blackBox.openFolder() }
     Button { objectName: "resetBlackBoxFolder"; text: "Типова папка"; enabled: !blackBox.folderIsDefault && !blackBox.active; onClicked: blackBox.resetFolder() }
     Item { Layout.fillWidth: true }
    }
    Text { visible: blackBox.error !== ""; text: blackBox.error; color: root.red; wrapMode: Text.WordWrap; Layout.fillWidth: true }
   }
  }

  Text {
   objectName: "recordingState"
   text: dvrRuntime.recording ? "● Іде запис: " + dvrRuntime.elapsedText : (dvrRuntime.lastFileName !== "" ? "Останній запис: " + dvrRuntime.lastFileName : "Записів у цьому сеансі ще немає.")
   color: dvrRuntime.recording ? root.red : root.sub
   font.bold: dvrRuntime.recording
   wrapMode: Text.WordWrap
   Layout.fillWidth: true
  }

  Text {
   objectName: "recordingMessage"
   visible: text !== ""
   text: dvrRuntime.status
   color: dvrRuntime.statusLevel === "error" ? root.red : root.green
   wrapMode: Text.WordWrap
   Layout.fillWidth: true
  }

  Item { Layout.fillHeight: true }
 }

 FolderDialog {
  id: boxDialog
  title: "Папка чорної скриньки"
  currentFolder: blackBox.folderUrl
  onAccepted: blackBox.setFolder(selectedFolder.toString())
 }
 FolderDialog {
  id: folderDialog
  title: "Папка для записів відео"
  currentFolder: dvrRuntime.folderUrl
  onAccepted: dvrRuntime.setFolder(selectedFolder.toString())
 }
}
