import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// The flights journal: every flight of the black box, newest first, grouped by day.
// On the left the list, on the right what happened in the chosen flight.
Item {
 id: root
 signal closeRequested()
 property color fg: "#f4f7fb"
 property color sub: "#b7c8da"
 property color line: "#273d55"
 property color green: "#27d59a"
 property color red: "#ff6678"
 property color amber: "#ffb84d"
 property string selected: ""
 property var details: ({})
 property bool confirmDelete: false

 function choose(path) {
  selected = path
  confirmDelete = false
  details = path ? blackBox.flightDetails(path) : ({})
 }
 Component.onCompleted: {
  blackBox.refresh()
  if (blackBox.flights.length > 0) choose(blackBox.flights[0].path)
 }

 ColumnLayout {
  anchors.fill: parent
  spacing: 12

  RowLayout {
   Layout.fillWidth: true
   Text { text: "ЖУРНАЛ ПОЛЬОТІВ"; color: root.fg; font.pixelSize: 20; font.bold: true; Layout.fillWidth: true }
   Button { objectName: "flightLogFolder"; text: "Папка"; onClicked: blackBox.openFolder() }
   Button { objectName: "flightLogClose"; text: "Закрити"; onClicked: root.closeRequested() }
  }

  Text {
   visible: blackBox.flights.length === 0
   text: "Польотів ще немає. Кожен політ записується сам, коли відкривається екран польоту."
   color: root.sub; wrapMode: Text.WordWrap; Layout.fillWidth: true
  }

  RowLayout {
   visible: blackBox.flights.length > 0
   Layout.fillWidth: true
   Layout.fillHeight: true
   spacing: 12

   Rectangle {
    Layout.preferredWidth: 330
    Layout.fillHeight: true
    radius: 10
    color: "#0b1420"
    border.color: root.line
    ListView {
     id: list
     objectName: "flightLogList"
     anchors.fill: parent
     anchors.margins: 6
     clip: true
     spacing: 4
     model: blackBox.flights
     section.property: "day"
     section.delegate: Text {
      required property string section
      text: section
      color: root.sub; font.pixelSize: 12; font.bold: true
      topPadding: 8; bottomPadding: 4; leftPadding: 6
     }
     delegate: Button {
      id: row
      required property var modelData
      objectName: "flightLogItem"
      width: list.width
      height: 50
      padding: 8
      background: Rectangle {
       radius: 8
       color: root.selected === row.modelData.path ? "#1d3a2f" : (row.hovered ? "#1a2a3d" : "#0f1a28")
       border.color: root.selected === row.modelData.path ? root.green : "#1e3045"
      }
      contentItem: RowLayout {
       spacing: 10
       Text { text: row.modelData.time; color: root.fg; font.pixelSize: 16; font.bold: true }
       ColumnLayout {
        spacing: 0
        Layout.fillWidth: true
        Text { text: row.modelData.camera || "Камера"; color: root.fg; font.pixelSize: 13; elide: Text.ElideRight; Layout.fillWidth: true }
        Text { text: row.modelData.finished ? row.modelData.duration : "не завершено"; color: root.sub; font.pixelSize: 11 }
       }
       Rectangle { // dropouts at a glance
        radius: 6
        implicitWidth: badge.implicitWidth + 12
        implicitHeight: 20
        color: !row.modelData.finished ? "#3a3220" : (row.modelData.outages > 0 ? "#3d1d26" : "#173528")
        Text {
         id: badge
         anchors.centerIn: parent
         text: !row.modelData.finished ? "?" : (row.modelData.outages > 0 ? "обривів: " + row.modelData.outages : "без обривів")
         color: !row.modelData.finished ? root.amber : (row.modelData.outages > 0 ? root.red : root.green)
         font.pixelSize: 11
        }
       }
      }
      onClicked: root.choose(modelData.path)
     }
    }
   }

   Rectangle {
    Layout.fillWidth: true
    Layout.fillHeight: true
    radius: 10
    color: "#0b1420"
    border.color: root.line
    ColumnLayout {
     anchors.fill: parent
     anchors.margins: 14
     spacing: 6
     Text { objectName: "flightLogTitle"; text: (root.details.camera || "") + (root.details.started ? " · " + root.details.started : ""); color: root.fg; font.pixelSize: 17; font.bold: true; wrapMode: Text.Wrap; Layout.fillWidth: true }
     Text { visible: !!root.details.link; text: "Зв’язок: " + (root.details.link || ""); color: root.sub; font.pixelSize: 12 }
     Repeater {
      model: root.details.lines || []
      delegate: Text { required property string modelData; text: "• " + modelData; color: root.fg; font.pixelSize: 14; wrapMode: Text.Wrap; Layout.fillWidth: true }
     }
     Text { visible: (root.details.events || []).length > 0; text: "Події"; color: root.sub; font.pixelSize: 12; font.bold: true; Layout.topMargin: 6 }
     ListView {
      objectName: "flightLogEvents"
      Layout.fillWidth: true
      Layout.fillHeight: true
      clip: true
      model: root.details.events || []
      delegate: RowLayout {
       required property var modelData
       width: ListView.view.width
       spacing: 10
       Text { text: modelData.time; color: root.sub; font.pixelSize: 12; font.family: "monospace" }
       Text { text: modelData.text; color: root.fg; font.pixelSize: 12; wrapMode: Text.Wrap; Layout.fillWidth: true }
      }
     }
     Item { visible: (root.details.events || []).length === 0; Layout.fillHeight: true }
     RowLayout {
      Layout.fillWidth: true
      Button { objectName: "flightLogOpen"; text: "Відкрити папку польоту"; enabled: root.selected !== ""; onClicked: blackBox.openFlight(root.selected) }
      Item { Layout.fillWidth: true }
      Button {
       objectName: "flightLogDelete"
       text: root.confirmDelete ? "Точно видалити?" : "Видалити"
       enabled: root.selected !== ""
       onClicked: {
        if (!root.confirmDelete) { root.confirmDelete = true; return }
        blackBox.deleteFlight(root.selected)
        root.choose(blackBox.flights.length > 0 ? blackBox.flights[0].path : "")
       }
      }
     }
    }
   }
  }
 }
}
