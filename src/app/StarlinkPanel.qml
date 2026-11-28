import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// The Starlink link of the camera in flight: is it up, how fast, which address.
Item {
 id: root
 signal closeRequested()
 property color fg: "#f4f7fb"
 property color sub: "#b7c8da"
 property color green: "#27d59a"
 property color amber: "#ffb84d"
 property color red: "#ff6678"

 readonly property string deviceId: devicesModel.activeId
 readonly property var link: (connectionsRuntime.statuses[deviceId] || {}).starlink || ({})
 readonly property var facts: connectionsRuntime.cameraFacts[deviceId] || ({})
 readonly property string address: deviceId !== "" ? connectionsRuntime.addressFor(deviceId, "starlink") : ""

 ColumnLayout {
  anchors.fill: parent
  spacing: 14

  RowLayout {
   Layout.fillWidth: true
   Text { text: "STARLINK"; color: root.fg; font.pixelSize: 20; font.bold: true; Layout.fillWidth: true }
   Button { objectName: "closeStarlink"; text: "Закрити"; onClicked: root.closeRequested() }
  }
  Text {
   text: "Камера на дроні виходить в інтернет через Starlink, станція з’єднується з нею напряму за адресою IPv6. Станція перевіряє зв’язок кожні 5 секунд і відновлює відео сама."
   color: root.sub; wrapMode: Text.Wrap; Layout.fillWidth: true
  }

  RowLayout {
   spacing: 12
   Rectangle { width: 14; height: 14; radius: 7; color: root.link.state === "available" ? root.green : (root.link.state === "unavailable" ? root.red : root.amber) }
   Text {
    objectName: "starlinkState"
    text: root.link.state === "available" ? "Зв’язок є · затримка " + root.link.label
        : (root.link.state === "unconfigured" ? "Адресу камери в Starlink ще не отримано"
        : (root.link.state === "unavailable" ? "Зв’язку немає · відновлюю автоматично" : "Перевіряю…"))
    color: root.fg; font.pixelSize: 18; font.bold: true
   }
  }
  ColumnLayout {
   spacing: 4
   Layout.fillWidth: true
   Text { text: "Відео за останню хвилину (кадрів щосекунди)"; color: root.sub; font.pixelSize: 12 }
   LinkGraph { Layout.fillWidth: true; Layout.preferredHeight: 48; values: linkMonitor.history }
  }
  ColumnLayout {
   spacing: 2
   Text { text: "Адреса камери в мережі Starlink"; color: root.sub; font.pixelSize: 12 }
   Text {
    objectName: "starlinkAddress"
    text: (root.address || "не вказана") + (root.facts.starlinkFromCamera ? " — зчитано з камери" : "")
    color: root.fg; font.pixelSize: 15; font.family: "monospace"
   }
  }

  Rectangle {
   objectName: "starlinkDishSection"
   Layout.fillWidth: true
   implicitHeight: dishColumn.implicitHeight + 20
   radius: 8
   color: "#0f1c2b"
   border.color: "#2f4860"
   ColumnLayout {
    id: dishColumn
    anchors.fill: parent
    anchors.margins: 10
    spacing: 4
    Text { text: "Антена на дроні"; color: root.sub; font.pixelSize: 12 }
    Text {
     objectName: "starlinkDishState"
     text: starlinkDish.available ? starlinkDish.status.stateText + " · затримка до мережі Starlink " + starlinkDish.status.latencyMs + " мс · втрати " + String(starlinkDish.status.dropPct).replace(".", ",") + "%" : (starlinkDish.reason || "дані ще не отримано")
     color: root.fg; font.pixelSize: 15; font.bold: true; wrapMode: Text.Wrap; Layout.fillWidth: true
    }
    Text {
     visible: starlinkDish.available
     text: "небо закрите на " + String(starlinkDish.status.obstructedPct).replace(".", ",") + "%" + (starlinkDish.status.currentlyObstructed ? " · ЗАРАЗ перешкода" : "") + " · ↓ " + String(starlinkDish.status.downMbps).replace(".", ",") + " Мбіт/с · ↑ " + String(starlinkDish.status.upMbps).replace(".", ",") + " Мбіт/с"
     color: starlinkDish.status.currentlyObstructed ? root.amber : root.sub; wrapMode: Text.Wrap; Layout.fillWidth: true
    }
    Text {
     objectName: "starlinkDishAlerts"
     visible: starlinkDish.available && (starlinkDish.status.alerts || []).length > 0
     text: "Увага: " + (starlinkDish.status.alerts || []).join(", ")
     color: root.red; wrapMode: Text.Wrap; Layout.fillWidth: true
    }
    Text {
     objectName: "starlinkLastOutage"
     visible: starlinkDish.lastOutageCause !== ""
     text: "Останній обрив: " + starlinkDish.lastOutageCause
     color: root.sub; wrapMode: Text.Wrap; Layout.fillWidth: true
    }
   }
  }

  Item { Layout.fillHeight: true }
  Button { objectName: "starlinkCheckNow"; text: "Перевірити зараз"; onClicked: { connectionsRuntime.refresh(); starlinkDish.poll() } }
 }
}
