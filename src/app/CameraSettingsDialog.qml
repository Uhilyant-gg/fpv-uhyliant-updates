import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Settings of one camera from the home screen: name, addresses for every
// connection type, firmware and moving to the archive.
Popup {
 id: root
 objectName: "cameraSettingsDialog"
 signal openFirmware(string deviceId)
 property string deviceId: ""
 property var camera: ({})
 property string error: ""
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
  ztNetworkField.text = connectionsRuntime.zerotierNetworkFor(device.id)
  ztNodeField.text = connectionsRuntime.zerotierNodeFor(device.id)
  error = ""
  open()
  if (focusKind === "cloud") ztNetworkField.forceActiveFocus()
  else if (focusKind === "starlink") starlinkField.forceActiveFocus()
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
  if ((ztNetworkField.text.trim() !== connectionsRuntime.zerotierNetworkFor(deviceId) || ztNodeField.text.trim() !== connectionsRuntime.zerotierNodeFor(deviceId))
    && !connectionsRuntime.setZeroTier(deviceId, ztNetworkField.text, ztNodeField.text)) {
   error = "ZeroTier: ID мережі — 16 символів (0–9, a–f), ID вузла камери — 10 символів."
   return
  }
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

  Text { text: "ZeroTier: ID мережі та ID вузла камери"; color: root.sub; font.pixelSize: 12; Layout.topMargin: 4 }
  RowLayout {
   Layout.fillWidth: true
   spacing: 8
   TextField { id: ztNetworkField; objectName: "cameraZtNetworkField"; Layout.fillWidth: true; Layout.preferredWidth: 3; placeholderText: "8056c2e21c000001" }
   TextField { id: ztNodeField; objectName: "cameraZtNodeField"; Layout.fillWidth: true; Layout.preferredWidth: 2; placeholderText: "89e92ceee5" }
  }

  Text { text: "Порожнє поле — цей тип підключення не використовується."; color: root.sub; font.pixelSize: 11; wrapMode: Text.WordWrap; Layout.fillWidth: true }
  Text { objectName: "cameraSettingsError"; visible: text !== ""; text: root.error; color: root.red; wrapMode: Text.WordWrap; Layout.fillWidth: true }

  Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; Layout.topMargin: 6; color: "#2f4860" }

  RowLayout {
   Layout.fillWidth: true
   spacing: 8
   Button { objectName: "cameraFirmware"; text: "Прошивка камери"; onClicked: { var id = root.deviceId; root.close(); root.openFirmware(id) } }
   Button {
    objectName: "cameraArchive"
    text: "В архів"
    onClicked: { if (devicesModel.archiveDevice(root.deviceId)) root.close() }
    HoverHint { text: "Камера зникне з головного екрана. Повернути або остаточно видалити її можна в архіві." }
   }
   Item { Layout.fillWidth: true }
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
