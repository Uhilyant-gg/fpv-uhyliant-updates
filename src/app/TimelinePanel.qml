import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
 id: root
 signal closeRequested()
 property var items: timelineRuntime.items
 property color foreground: "#f4f7fb"
 property color secondary: "#8fa1b7"
 property color line: "#273d55"
 property color green: "#27d59a"
 property color amber: "#ffb84d"

 ColumnLayout {
  anchors.fill: parent
  spacing: 12

  RowLayout {
   Layout.fillWidth: true
   Text { text: "Події сесії"; color: root.foreground; font.pixelSize: 22; font.bold: true }
   Item { Layout.fillWidth: true }
   Button { text: "Очистити"; enabled: root.items.length > 0; onClicked: clearHistoryDialog.open() }
   Button { text: "Закрити"; onClicked: root.closeRequested() }
  }
  Text {
   Layout.fillWidth: true
   text: "Важливі зміни стану — нові події з’являються автоматично."
   color: root.secondary
   font.pixelSize: 12
   wrapMode: Text.WordWrap
  }
  Rectangle {
   Layout.fillWidth: true
   Layout.fillHeight: true
   radius: 10
   color: "#0b1420"
   border.color: root.line
   ListView {
    id: eventList
    anchors.fill: parent
    anchors.margins: 8
    clip: true
    spacing: 4
    model: root.items
    delegate: Rectangle {
     required property var modelData
     width: eventList.width
     height: 48
     radius: 7
     color: "#0d1723"
     RowLayout {
      anchors.fill: parent
      anchors.margins: 10
      spacing: 10
      Text { text: modelData.time; color: root.secondary; font.pixelSize: 11; Layout.preferredWidth: 52 }
      Rectangle {
       width: 7
       height: 7
       radius: 4
       color: modelData.level === "warning" ? root.amber : root.green
      }
      Text { text: modelData.title; color: root.foreground; font.pixelSize: 12; Layout.fillWidth: true }
     }
    }
   }
   Column {
    anchors.centerIn: parent
    spacing: 6
    visible: root.items.length === 0
    Text { anchors.horizontalCenter: parent.horizontalCenter; text: "Подій поки немає"; color: root.foreground; font.pixelSize: 17; font.bold: true }
    Text { anchors.horizontalCenter: parent.horizontalCenter; text: "Важливі зміни з’являться тут."; color: root.secondary; font.pixelSize: 12 }
   }
  }
  Text {
   visible: timelineRuntime.persistenceError !== ""
   Layout.fillWidth: true
   text: timelineRuntime.persistenceError
   color: root.amber
   font.pixelSize: 11
   wrapMode: Text.WordWrap
  }
  Text {
   Layout.fillWidth: true
   text: "Історія зберігається локально: до 200 подій або 30 днів. Координати та секрети не записуються."
   color: root.secondary
   font.pixelSize: 10
   wrapMode: Text.WordWrap
  }
 }

 Dialog {
  id: clearHistoryDialog
  modal: true
  title: "Очистити історію?"
  standardButtons: Dialog.Yes | Dialog.No
  Label { text: "Збережені події буде видалено."; wrapMode: Text.WordWrap }
  onAccepted: timelineRuntime.clearHistory()
 }
}
