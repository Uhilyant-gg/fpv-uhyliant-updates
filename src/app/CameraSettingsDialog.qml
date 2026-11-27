import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Settings of one camera from the home screen: name, addresses for every
// connection type, firmware and removal.
Popup {
 id: root
 objectName: "cameraSettingsDialog"
 signal openFirmware(string deviceId)
 property string deviceId: ""
 property var camera: ({})
 property string error: ""
 property bool confirmRemove: false
 property color fg: "#f4f7fb"
 property color sub: "#b7c8da"
 property color red: "#ff6678"
 modal: true
 padding: 20
 width: Math.min(520, parent ? parent.width - 40 : 520)
 anchors.centerIn: parent
 background: Rectangle { color: "#0d1725"; border.color: "#2387ff"; radius: 12 }

 function show(device, focusKind) {
  deviceId = device.id
  camera = device
  nameField.text = device.name
  hostField.text = device.host
  staticField.text = connectionsRuntime.addressFor(device.id, "static")
  starlinkField.text = connectionsRuntime.addressFor(device.id, "starlink")
  error = ""
  confirmRemove = false
  open()
  if (focusKind === "starlink") starlinkField.forceActiveFocus()
  else if (focusKind === "static") staticField.forceActiveFocus()
  else nameField.forceActiveFocus()
 }

 function saveAddress(kind, text) {
  var value = text.trim()
  if (value === "") { connectionsRuntime.clearAddress(deviceId, kind); return true }
  if (value === connectionsRuntime.addressFor(deviceId, kind)) return true
  return connectionsRuntime.setAddress(deviceId, kind, value)
 }

 function save() {
  if (nameField.text.trim() === "") { error = "Вкажіть назву камери."; return }
  if (nameField.text.trim() !== camera.name || hostField.text.trim() !== camera.host) {
   if (!devicesModel.updateDevice(deviceId, nameField.text, hostField.text, camera.port || 80, camera.notes || "")) {
    error = "Не вдалося зберегти назву чи локальну адресу. Перевірте адресу камери."
    return
   }
  }
  if (!saveAddress("static", staticField.text)) { error = "Статична адреса має неправильний формат."; return }
  if (!saveAddress("starlink", starlinkField.text)) { error = "Адреса Starlink має бути IPv6-адресою, наприклад 2001:db8::10."; return }
  close()
 }

 contentItem: ColumnLayout {
  spacing: 8

  RowLayout {
   Layout.fillWidth: true
   Text { text: "Налаштування камери"; color: root.fg; font.pixelSize: 18; font.bold: true; Layout.fillWidth: true }
   Button { text: "✕"; flat: true; onClicked: root.close() }
  }

  Text { text: "Назва"; color: root.sub; font.pixelSize: 12 }
  TextField { id: nameField; objectName: "cameraNameField"; Layout.fillWidth: true }

  Text { text: "Локальна адреса (у мережі станції)"; color: root.sub; font.pixelSize: 12; Layout.topMargin: 4 }
  TextField { id: hostField; objectName: "cameraHostField"; Layout.fillWidth: true; placeholderText: "192.168.1.10" }

  Text { text: "Статичний IP або доменне ім’я (DDNS)"; color: root.sub; font.pixelSize: 12; Layout.topMargin: 4 }
  TextField { id: staticField; objectName: "cameraStaticField"; Layout.fillWidth: true; placeholderText: "93.170.12.5 або drone.example.net" }

  Text { text: "Адреса через Starlink (IPv6)"; color: root.sub; font.pixelSize: 12; Layout.topMargin: 4 }
  TextField { id: starlinkField; objectName: "cameraStarlinkField"; Layout.fillWidth: true; placeholderText: "2001:db8::10" }

  Text { text: "Порожнє поле — цей тип підключення не використовується."; color: root.sub; font.pixelSize: 11; wrapMode: Text.WordWrap; Layout.fillWidth: true }
  Text { objectName: "cameraSettingsError"; visible: text !== ""; text: root.error; color: root.red; wrapMode: Text.WordWrap; Layout.fillWidth: true }

  Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; Layout.topMargin: 6; color: "#2f4860" }

  RowLayout {
   Layout.fillWidth: true
   spacing: 8
   Button { objectName: "cameraFirmware"; text: "Прошивка камери"; onClicked: { var id = root.deviceId; root.close(); root.openFirmware(id) } }
   Button { objectName: "cameraRemove"; text: "Видалити камеру"; visible: !root.confirmRemove; onClicked: root.confirmRemove = true }
   Item { Layout.fillWidth: true }
  }

  RowLayout {
   visible: root.confirmRemove
   Layout.fillWidth: true
   Text { text: "Видалити «" + (root.camera.name || "") + "» зі станції?"; color: root.red; wrapMode: Text.WordWrap; Layout.fillWidth: true }
   Button { text: "Ні"; onClicked: root.confirmRemove = false }
   Button {
    objectName: "cameraRemoveConfirm"
    text: "Так, видалити"
    onClicked: { devicesModel.removeDevice(root.deviceId); root.close() }
    contentItem: Text { text: parent.text; font: parent.font; color: "white"; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
    background: Rectangle { radius: 7; color: "#b3263a" }
   }
  }

  RowLayout {
   Layout.fillWidth: true
   Layout.topMargin: 6
   Item { Layout.fillWidth: true }
   Button { text: "Скасувати"; onClicked: root.close() }
   Button { objectName: "cameraSettingsSave"; text: "Зберегти"; font.bold: true; onClicked: root.save() }
  }
 }
}
