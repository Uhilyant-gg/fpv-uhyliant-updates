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

 // The selected link of the camera, as the camera card shows it (given by the main window).
 property string linkKind: ""
 property string linkLabel: ""
 property var linkStatus: ({})

 // Only what is useful before take-off; a flight controller that is not connected is one calm line.
 property var checks: {
  var list = [
   {label: "Камера", state: cameraName ? "ready" : "unavailable", detail: cameraName || "Не вибрано"},
   {label: "Відео", state: video.state || "unavailable", detail: video.streamId ? stateLabel(video.state) : "Потік не запущено"},
   // A camera pushing to a static IP is not pinged: its video arriving is the answer.
   linkKind === "static" && video.state === "playing"
    ? {label: "Зв’язок", state: "ready", detail: linkLabel + " · камера надсилає відео"}
    : {label: "Зв’язок", state: linkStatus.state === "available" ? "ready" : (linkKind === "" ? "unavailable" : (linkStatus.state === "unavailable" ? "error" : "degraded")),
       detail: linkKind === "" ? "Тип з’єднання не вибрано" : linkLabel + (linkStatus.label ? " · " + linkStatus.label : "")}
  ]
  if (telemetry.connected === true) {
   list.push({label: "Польотник", state: "connected", detail: telemetry.provider || ""})
   list.push({label: "GPS", state: gpsState(), detail: gpsDetail()})
  } else {
   list.push({label: "Польотник", state: "unavailable", detail: "Дані польотника не надходять"})
  }
  list.push({label: "Пульт", state: controllerHealth === "ready" ? "ready" : (controllerHealth === "problem" ? "error" : (controllerHealth === "attention" ? "attention" : "unavailable")), detail: controllerDetail || "Не перевірено"})
  if (navigation.state === "ready" || navigation.state === "degraded")
   list.push({label: "Зовнішня навігація", state: navigation.state, detail: navigation.source || ""})
  return list
 }

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
   objectName: "linkTestBox"
   Layout.fillWidth: true
   implicitHeight: linkTestColumn.implicitHeight + 20
   radius: 10
   color: "#0b1420"
   border.color: linkTest.running ? root.line : (linkTest.result.level === "ok" ? root.green : (linkTest.result.level === "bad" ? root.red : (linkTest.result.level ? root.amber : root.line)))
   ColumnLayout {
    id: linkTestColumn
    anchors.fill: parent
    anchors.margins: 10
    spacing: 4
    RowLayout {
     Layout.fillWidth: true
     Text {
      objectName: "linkTestTitle"
      text: linkTest.running ? "Тест зв’язку: ще " + linkTest.secondsLeft + " с" : (linkTest.result.title || "Тест зв’язку (20 с)")
      color: linkTest.result.level === "ok" ? root.green : (linkTest.result.level === "bad" ? root.red : (linkTest.result.level ? root.amber : root.foreground))
      font.pixelSize: 14; font.bold: true; wrapMode: Text.Wrap; Layout.fillWidth: true
     }
     Button { objectName: "linkTestStart"; text: linkTest.running ? "Зупинити" : (linkTest.result.level ? "Повторити" : "Почати"); enabled: root.cameraName !== ""; onClicked: linkTest.running ? linkTest.stop() : linkTest.start() }
    }
    ProgressBar { visible: linkTest.running; value: linkTest.progress; Layout.fillWidth: true }
    Repeater {
     model: linkTest.running ? [] : (linkTest.result.lines || [])
     delegate: Text { required property string modelData; text: "• " + modelData; color: root.secondary; font.pixelSize: 12; wrapMode: Text.Wrap; Layout.fillWidth: true }
    }
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
  Text {
   text: "Тут лише те, що станція бачить сама; рішення про політ — за пілотом."
   color: root.secondary; font.pixelSize: 11; wrapMode: Text.WordWrap; Layout.fillWidth: true
  }
  RowLayout {
   Layout.fillWidth: true
   Item { Layout.fillWidth: true }
   Button { objectName: "preflightDiagnostics"; text: "Діагностика мережі"; onClicked: root.openDiagnostics() }
  }
 }
}
