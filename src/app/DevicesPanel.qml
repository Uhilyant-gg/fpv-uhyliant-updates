import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
 id: root
 signal closeRequested()
 property color fg: "#f4f7fb"
 property color sub: "#8fa1b7"
 property color line: "#273d55"
 property color blue: "#4aa3ff"
 property color green: "#27d59a"
 property string selectedId: ""

 ColumnLayout {
  anchors.fill: parent; spacing: 12
  RowLayout { Layout.fillWidth: true
   ColumnLayout { Text { text: "ПРИСТРОЇ"; color: root.fg; font.pixelSize: 22; font.bold: true } Text { text: "Локальна база бортів, камер і політних контролерів"; color: root.sub } }
   Item { Layout.fillWidth: true }
   Button { text: "Закрити"; onClicked: root.closeRequested() }
  }
  Rectangle { Layout.fillWidth: true; height: 1; color: root.line }
  RowLayout { Layout.fillWidth: true; Layout.fillHeight: true; spacing: 12
   ListView {
    id: list; Layout.preferredWidth: 360; Layout.fillHeight: true; clip: true; spacing: 8; model: devicesModel.items
    delegate: Rectangle {
     required property var modelData
     width: list.width; height: 86; radius: 10
     color: root.selectedId===modelData.id ? "#173650" : "#111d2c"
     border.color: modelData.active ? root.green : root.line
     MouseArea { anchors.fill: parent; onClicked: root.selectedId=modelData.id }
     Column { anchors.fill: parent; anchors.margins: 12; spacing: 4
      Text { text: (modelData.active ? "●  " : "") + modelData.name; color: modelData.active ? root.green : root.fg; font.bold: true; font.pixelSize: 15 }
      Text { text: modelData.type + " · " + modelData.connection; color: root.sub; font.pixelSize: 12 }
      Text { text: modelData.host ? (modelData.host + (modelData.port ? ":" + modelData.port : "")) : "Адресу не задано"; color: root.sub; font.pixelSize: 11 }
     }
    }
   }
   Rectangle { Layout.fillHeight: true; width: 1; color: root.line }
   ColumnLayout { Layout.fillWidth: true; Layout.fillHeight: true; spacing: 8
    TextField { id: nameField; Layout.fillWidth: true; placeholderText: "Назва, наприклад Camera 1" }
    ComboBox { id: typeBox; Layout.fillWidth: true; model: ["Камера OpenIPC", "Політний контролер", "Борт"] }
    ComboBox { id: connBox; Layout.fillWidth: true; model: ["Мережа", "Serial/COM", "Комбінований"] }
    TextField { id: hostField; Layout.fillWidth: true; placeholderText: "IP / hostname / COM-порт" }
    SpinBox { id: portBox; Layout.fillWidth: true; from: 0; to: 65535; value: 0; editable: true }
    TextArea { id: notesField; Layout.fillWidth: true; Layout.preferredHeight: 80; placeholderText: "Примітка"; wrapMode: TextEdit.Wrap }
    Button { text: "+ Додати пристрій"; Layout.fillWidth: true; onClicked: { var id=devicesModel.addDevice(nameField.text,typeBox.currentText,hostField.text,portBox.value,connBox.currentText,notesField.text); if(id){root.selectedId=id;nameField.clear();hostField.clear();portBox.value=0;notesField.clear()} } }
    Rectangle { Layout.fillWidth: true; height: 1; color: root.line }
    Text { text: devicesModel.activeName ? "Активний: " + devicesModel.activeName : "Активний пристрій не вибрано"; color: devicesModel.activeName ? root.green : root.sub; font.bold: true }
    RowLayout { Layout.fillWidth: true
     Button { text: "Зробити активним"; enabled: root.selectedId!==""; onClicked: devicesModel.setActive(root.selectedId) }
     Button { text: "Видалити"; enabled: root.selectedId!==""; onClicked: { devicesModel.removeDevice(root.selectedId); root.selectedId="" } }
    }
    Item { Layout.fillHeight: true }
    Text { text: "Відеопрофілі не зберігаються в записі пристрою."; color: root.sub; wrapMode: Text.WordWrap; Layout.fillWidth: true }
   }
  }
 }
}
