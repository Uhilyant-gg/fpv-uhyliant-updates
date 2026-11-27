import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
 id: root
 signal closeRequested()
 signal openDiagnostics()
 signal openOsdSettings()
 signal openSimulation()
 property string cameraName: ""
 property var video: ({})
 property var telemetry: ({})
 property var network: ({})
 property var navigation: ({})
 property var nextAction: ({})
 property bool osdEnabled: true
 property string controllerHealth: "unknown"
 property string controllerDetail: ""
 property color foreground: "#f4f7fb"
 property color secondary: "#b7c8da"
 property color line: "#273d55"
 property color green: "#27d59a"
 property color amber: "#ffb84d"
 property color red: "#ff6678"

 function stateLabel(state) {
  var labels = {
   "ready": "Працює",
   "playing": "Працює",
   "connected": "Підключено",
   "degraded": "Погіршено",
   "stale": "Дані застаріли",
   "error": "Є проблема",
   "unavailable": "Немає даних",
   "not-integrated": "Не інтегровано",
   "attention": "Потрібна дія",
   "disconnected": "Немає зв’язку"
  }
  return labels[state] || "Не перевірено"
 }
 function stateColor(state) {
  if (state === "ready" || state === "playing" || state === "connected") return green
  if (state === "error" || state === "disconnected") return red
  return amber
 }
 function gpsAge() {
  if (telemetry.ages && telemetry.ages.gps !== undefined) return Number(telemetry.ages.gps)
  if (telemetry.ages && telemetry.ages.gpsFix !== undefined) return Number(telemetry.ages.gpsFix)
  return null
 }
 function gpsState() {
  if (telemetry.connected !== true) return "unavailable"
  if (telemetry.provider === "CRSF") return "degraded"
  if (telemetry.gpsFix === null || telemetry.gpsFix === undefined) return "unavailable"
  if (Number(telemetry.gpsFix) <= 1) return "degraded"
  var age = gpsAge()
  if (age === null || !isFinite(age)) return "degraded"
  return age <= 3 ? "ready" : "stale"
 }
 function gpsDetail() {
  if (telemetry.connected !== true) return "Телеметрія не підтверджена"
  if (telemetry.provider === "CRSF") return "Координати не надходять у цьому потоці"
  if (telemetry.gpsFix === null || telemetry.gpsFix === undefined) return "GPS-фікс відсутній"
  var fix = Number(telemetry.gpsFix)
  if (!isFinite(fix) || fix <= 1) return "GPS-фікс відсутній"
  var age = gpsAge()
  var fixLabel = fix === 2 ? "2D" : "3D"
  var satellites = telemetry.satellites === null || telemetry.satellites === undefined ? "" : " · супутників: " + telemetry.satellites
  return age === null || !isFinite(age)
   ? fixLabel + satellites + " · свіжість не підтверджена"
   : fixLabel + satellites + " · оновлено " + age.toFixed(1) + " с тому"
 }

 property var checks: [
  {label: "Камера", state: cameraName ? "ready" : "unavailable", detail: cameraName || "Не вибрано"},
  {label: "Відео", state: video.state || "unavailable", detail: video.streamId ? stateLabel(video.state) : "Потік не запущено"},
  {label: "Телеметрія", state: telemetry.connected === true ? "connected" : (telemetry.connected === false ? "disconnected" : "unavailable"), detail: (telemetry.provider || "Джерело не вибране") + " · " + (telemetry.health || "стан невідомий")},
  {label: "GPS-дані польотника", state: gpsState(), detail: gpsDetail()},
  {label: "Мережа", state: network.state || "unavailable", detail: network.transport || "З’єднання не підтверджене"},
  {label: "Зовнішня навігація", state: navigation.state || "unavailable", detail: navigation.source || "Джерело не підтверджене"},
  {label: "OSD станції", state: osdEnabled ? "ready" : "unavailable", detail: osdEnabled ? "Додається поверх відео; зображення камери не змінюється" : "Не додається; OSD камери залишається частиною відео"},
  {label: "Пульт", state: controllerHealth === "ready" ? "ready" : (controllerHealth === "problem" ? "error" : (controllerHealth === "attention" ? "attention" : "unavailable")), detail: controllerDetail || "Не перевірено"},
  {label: "Керування польотом", state: "not-integrated", detail: "Канал керування не інтегрований"}
 ]

 ColumnLayout {
  anchors.fill: parent
  spacing: 12

  RowLayout {
   Layout.fillWidth: true
   Text { text: "Стан підготовки"; color: root.foreground; font.pixelSize: 22; font.bold: true }
   Item { Layout.fillWidth: true }
   Button { text: "Закрити"; onClicked: root.closeRequested() }
  }
  Rectangle {
   Layout.fillWidth: true
   radius: 8
   color: "#332d1b"
   border.color: root.amber
   implicitHeight: notice.implicitHeight + 20
   Text {
    id: notice
    anchors.fill: parent
    anchors.margins: 10
    text: "Це зведення показує лише отримані дані й не підтверджує готовність до польоту. Застосунок наразі не керує польотом."
    color: root.foreground
    wrapMode: Text.WordWrap
    font.pixelSize: 12
   }
  }
  Rectangle {
   Layout.fillWidth: true
   Layout.fillHeight: true
   radius: 10
   color: "#0b1420"
   border.color: root.line
   ListView {
    id: checkList
    anchors.fill: parent
    anchors.margins: 8
    clip: true
    spacing: 4
    model: root.checks
    delegate: Rectangle {
     required property var modelData
     width: checkList.width
     height: 58
     radius: 7
     color: "#0d1723"
     RowLayout {
      anchors.fill: parent
      anchors.margins: 10
      spacing: 10
      Rectangle {
       width: 8
       height: 8
       radius: 4
       color: root.stateColor(modelData.state)
      }
      ColumnLayout {
       Layout.fillWidth: true
       spacing: 2
       Text { text: modelData.label; color: root.foreground; font.pixelSize: 12; font.bold: true }
       Text { text: modelData.detail; color: root.secondary; font.pixelSize: 11; elide: Text.ElideRight; Layout.fillWidth: true }
      }
      Text {
       text: root.stateLabel(modelData.state)
       color: root.stateColor(modelData.state)
       font.pixelSize: 11
       font.bold: true
      }
     }
    }
   }
  }
  RowLayout {
   Layout.fillWidth: true
   Text {
    visible: nextAction.available === true
    text: visible ? "Наступна дія: " + (nextAction.label || "") : "Потрібні додаткові спостереження"
    color: root.secondary
    font.pixelSize: 12
    wrapMode: Text.WordWrap
    Layout.fillWidth: true
   }
   Button { text: "Діагностика"; onClicked: root.openDiagnostics() }
   Button { text: "Налаштувати OSD"; onClicked: root.openOsdSettings() }
   Button { text: "Симуляція"; onClicked: root.openSimulation() }
  }
 }
}
