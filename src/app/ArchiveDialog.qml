import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Archived cameras: restore one to the home screen, or delete it for good.
Popup {
 id: root
 objectName: "archiveDialog"
 property string confirmId: ""
 property color fg: "#f4f7fb"
 property color sub: "#b7c8da"
 property color red: "#ff6678"
 modal: true
 padding: 20
 width: Math.min(620, parent ? parent.width - 40 : 620)
 height: Math.min(520, parent ? parent.height - 48 : 520)
 anchors.centerIn: parent
 background: Rectangle { color: "#0d1725"; border.color: "#2387ff"; radius: 12 }
 onClosed: confirmId = ""

 function archivedText(seconds) {
  if (!seconds) return ""
  var date = new Date(seconds * 1000)
  return "В архіві з " + date.toLocaleDateString(Qt.locale("uk_UA"), "d MMMM yyyy")
 }

 contentItem: ColumnLayout {
  spacing: 10
  RowLayout {
   Layout.fillWidth: true
   Text { text: "Архів камер"; color: root.fg; font.pixelSize: 18; font.bold: true; Layout.fillWidth: true }
   Button { objectName: "archiveClose"; text: "✕"; flat: true; onClicked: root.close() }
  }
  Text {
   Layout.fillWidth: true
   wrapMode: Text.WordWrap
   color: root.sub
   text: "Камери в архіві не показуються на головному екрані й не використовуються. Їх можна повернути або видалити зі станції назавжди."
  }
  Text {
   visible: devicesModel.archivedItems.length === 0
   text: "Архів порожній."
   color: root.sub
   Layout.topMargin: 12
  }
  ListView {
   id: archiveList
   objectName: "archiveList"
   Layout.fillWidth: true
   Layout.fillHeight: true
   clip: true
   spacing: 8
   model: devicesModel.archivedItems
   delegate: Rectangle {
    required property var modelData
    width: archiveList.width
    height: archiveColumn.implicitHeight + 20
    radius: 9
    color: "#132235"
    border.color: root.confirmId === modelData.id ? root.red : "#2f4860"
    ColumnLayout {
     id: archiveColumn
     anchors.fill: parent
     anchors.margins: 10
     spacing: 6
     RowLayout {
      Layout.fillWidth: true
      ColumnLayout {
       Layout.fillWidth: true
       spacing: 1
       Text { text: modelData.name; color: root.fg; font.bold: true; font.pixelSize: 15; elide: Text.ElideRight; Layout.fillWidth: true }
       Text { text: modelData.host + "  ·  " + root.archivedText(modelData.archivedAt); color: root.sub; font.pixelSize: 12; elide: Text.ElideRight; Layout.fillWidth: true }
      }
      Button { objectName: "archiveRestore"; text: "Відновити"; visible: root.confirmId !== modelData.id; onClicked: devicesModel.restoreDevice(modelData.id) }
      Button { objectName: "archiveDelete"; text: "Видалити"; visible: root.confirmId !== modelData.id; onClicked: root.confirmId = modelData.id }
     }
     RowLayout {
      visible: root.confirmId === modelData.id
      Layout.fillWidth: true
      Text { text: "Видалити «" + modelData.name + "» назавжди? Повернути її не вийде."; color: root.red; wrapMode: Text.WordWrap; Layout.fillWidth: true }
      Button { text: "Ні"; onClicked: root.confirmId = "" }
      Button {
       objectName: "archiveDeleteConfirm"
       text: "Так, видалити"
       onClicked: { devicesModel.removeDevice(modelData.id); root.confirmId = "" }
       contentItem: Text { text: parent.text; font: parent.font; color: "white"; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
       background: Rectangle { radius: 7; color: "#b3263a" }
      }
     }
    }
   }
  }
 }
}
