import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Everything the station is connected to, one line each, in plain words.
// Values come from live data only; what is not known is said so, never guessed.
Item {
 id: root
 signal closeRequested()
 signal openNetworkDetails()
 signal openStarlink()
 property var video: ({})
 property var telemetry: ({})
 property color fg: "#f4f7fb"
 property color sub: "#b7c8da"
 property color green: "#27d59a"
 property color amber: "#ffb84d"
 property color red: "#ff6678"
 property color grey: "#6f8299"

 readonly property string deviceId: devicesModel.activeId
 readonly property string kind: connectionsRuntime.selected[deviceId] || ""
 readonly property var link: (connectionsRuntime.statuses[deviceId] || {})[kind] || ({})
 readonly property var facts: connectionsRuntime.cameraFacts[deviceId] || ({})

 function kindLabel(key) {
  var types = connectionsRuntime.types
  for (var i = 0; i < types.length; i++) if (types[i].key === key) return types[i].label
  return "не вибрано"
 }
 function stateColor(state) { return state === "available" ? green : (state === "unavailable" ? red : amber) }
 function videoValue() {
  if (!video.streamId) return "немає потоку"
  if (linkMonitor.lost) return "немає кадрів " + linkMonitor.lostSeconds + " с · відновлюю"
  if (video.state !== "playing") return "підключення…"
  var size = video.width && video.height ? video.width + "×" + video.height : ""
  return [size, linkMonitor.fps + " к/с"].filter(function(p) { return p !== "" }).join(" · ")
 }
 function fcValue() {
  if (telemetry.connected !== true) return "немає даних від польотника"
  var parts = ["дані надходять"]
  if (telemetry.batteryVoltage) parts.push("АКБ " + Number(telemetry.batteryVoltage).toFixed(1) + " В")
  if (telemetry.satellites !== undefined && telemetry.satellites !== null) parts.push("супутників " + telemetry.satellites)
  return parts.join(" · ")
 }
 function streamText() {
  var d = linkDoctor.details
  if (!d.hasStream) return ""
  return "втрачено " + String(d.lossPct).replace(".", ",") + "% пакетів · нерівність " + Math.round(d.jitterMs) + " мс · " + (d.kbps / 1000).toFixed(1).replace(".", ",") + " Мбіт/с"
 }
 function controllerColor(health) { return health === "ready" ? green : (health === "problem" ? red : (health === "attention" ? amber : grey)) }

 component Row_: RowLayout {
  id: row
  property string title: ""
  property string value: ""
  property string detail: ""
  property color dot: root.grey
  default property alias extra: slot.data
  Layout.fillWidth: true
  spacing: 12
  Rectangle { width: 12; height: 12; radius: 6; color: row.dot; Layout.alignment: Qt.AlignTop; Layout.topMargin: 5 }
  ColumnLayout {
   Layout.fillWidth: true
   spacing: 2
   Text { text: row.title; color: root.sub; font.pixelSize: 12 }
   Text { text: row.value; color: root.fg; font.pixelSize: 16; font.bold: true; wrapMode: Text.Wrap; Layout.fillWidth: true }
   Text { visible: row.detail !== ""; text: row.detail; color: root.sub; font.pixelSize: 12; wrapMode: Text.Wrap; Layout.fillWidth: true }
   Item { id: slot; Layout.fillWidth: true; implicitHeight: childrenRect.height; visible: children.length > 0 }
  }
 }

 ColumnLayout {
  anchors.fill: parent
  spacing: 14

  RowLayout {
   Layout.fillWidth: true
   Text { text: "ОБЛАДНАННЯ"; color: root.fg; font.pixelSize: 20; font.bold: true; Layout.fillWidth: true }
   Button { objectName: "closeHardware"; text: "Закрити"; onClicked: root.closeRequested() }
  }
  Text {
   text: "Стан усього, що підключено до станції, оновлюється сам. Якщо щось червоне, станція вже пробує відновити зв’язок."
   color: root.sub; wrapMode: Text.Wrap; Layout.fillWidth: true
  }

  Row_ {
   objectName: "hardwareCamera"
   title: "Камера · " + (devicesModel.activeName || "не вибрана")
   value: root.videoValue()
   detail: root.facts.summary || ""
   dot: root.video.streamId && !linkMonitor.lost && root.video.state === "playing" ? root.green : root.red
  }
  Row_ {
   objectName: "hardwareLink"
   title: "Канал зв’язку · " + root.kindLabel(root.kind)
   value: root.link.state === "available" && root.link.latencyMs !== null && root.link.latencyMs !== undefined ? "затримка " + root.link.label : (root.link.label || "немає даних")
   dot: root.stateColor(root.link.state)
   detail: root.streamText()
   LinkGraph { width: Math.min(parent.width, 480); height: 36; values: linkMonitor.history }
  }
  Row_ {
   objectName: "hardwareInternet"
   visible: root.kind !== "" && root.kind !== "local"
   title: "Інтернет на цьому ПК"
   value: linkDoctor.details.internet === true ? "є" : (linkDoctor.details.internet === false ? "немає · перевірте роутер або провайдера" : "перевіряю…")
   dot: linkDoctor.details.internet === true ? root.green : (linkDoctor.details.internet === false ? root.red : root.amber)
  }
  Row_ {
   objectName: "hardwareFlightController"
   title: "Польотний контролер"
   value: root.fcValue()
   dot: root.telemetry.connected === true ? root.green : root.red
  }
  Row_ {
   objectName: "hardwareController"
   title: "Пульт"
   value: controllerRuntime.summary || "немає даних"
   dot: root.controllerColor(controllerRuntime.health)
  }
  Row_ {
   objectName: "hardwareZeroTier"
   visible: root.kind === "cloud"
   title: "ZeroTier на цьому ПК"
   value: connectionsRuntime.zerotierText || "немає даних"
   dot: connectionsRuntime.zerotierState === "ok" ? root.green : root.red
  }
  Row_ {
   objectName: "hardwareRecording"
   title: "Запис відео на цьому ПК"
   value: (dvrRuntime.recording ? "йде запис " + dvrRuntime.elapsedText : "запис вимкнено") + (dvrRuntime.freeSpaceText ? " · " + dvrRuntime.freeSpaceText : "")
   dot: dvrRuntime.recording ? root.red : root.grey
  }

  Item { Layout.fillHeight: true }
  RowLayout {
   spacing: 8
   Button { objectName: "hardwareStarlink"; visible: root.kind === "starlink"; text: "Starlink"; onClicked: root.openStarlink() }
   Button { objectName: "hardwareNetworkDetails"; text: "Мережа ПК детально"; onClicked: root.openNetworkDetails() }
  }
 }
}
