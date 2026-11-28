import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
 id: root
 signal closeRequested()
 property color fg: "#f4f7fb"
 property color sub: "#8fa1b7"
 property color line: "#273d55"
 property color blue: "#2387ff"
 property color green: "#3ddc97"
 property color amber: "#ffbf4a"
 property color red: "#ff6678"

 function healthColor(health) {
  return health === "ready" ? green : (health === "problem" ? red : (health === "attention" ? amber : sub))
 }
 function axisLabel(axis) {
  return ({roll: "Крен", pitch: "Тангаж", yaw: "Рискання", throttle: "Газ"})[axis] || axis
 }

 Component.onCompleted: controllerRuntime.activate()
 Component.onDestruction: controllerRuntime.deactivate()

 ColumnLayout {
  anchors.fill: parent
  spacing: 12

  RowLayout {
   Layout.fillWidth: true
   Text { text: "ПУЛЬТ"; color: root.fg; font.pixelSize: 20; font.bold: true; Layout.fillWidth: true }
   Button { text: "Закрити"; onClicked: root.closeRequested() }
  }

  Rectangle {
   Layout.fillWidth: true
   implicitHeight: statusColumn.implicitHeight + 24
   radius: 12
   color: "#132235"
   border.color: root.healthColor(controllerRuntime.health)
   ColumnLayout {
    id: statusColumn
    anchors.fill: parent
    anchors.margins: 12
    spacing: 4
    Text {
     objectName: "controllerName"
     text: controllerRuntime.controllerName || "Пульт не підключено"
     color: root.fg; font.pixelSize: 17; font.bold: true
    }
    Text {
     objectName: "controllerSummary"
     text: controllerRuntime.summary
     color: root.sub; wrapMode: Text.WordWrap; Layout.fillWidth: true
    }
   }
  }

  // Live normalized sticks once a profile is restored.
  ColumnLayout {
   visible: controllerRuntime.restored && !controllerRuntime.wizardActive
   Layout.fillWidth: true
   spacing: 6
   Repeater {
    model: ["roll", "pitch", "yaw", "throttle"]
    RowLayout {
     required property string modelData
     Layout.fillWidth: true
     Text { text: root.axisLabel(modelData); color: root.sub; Layout.preferredWidth: 90 }
     ProgressBar {
      Layout.fillWidth: true
      from: modelData === "throttle" ? 0 : -1
      to: 1
      value: controllerRuntime.controls[modelData] === undefined ? 0 : controllerRuntime.controls[modelData]
     }
    }
   }
  }

  // Setup wizard.
  ColumnLayout {
   visible: controllerRuntime.wizardActive
   Layout.fillWidth: true
   spacing: 8
   Text {
    objectName: "wizardPrompt"
    text: controllerRuntime.wizardPrompt
    color: root.fg; font.pixelSize: 16; wrapMode: Text.WordWrap; Layout.fillWidth: true
   }
   Flow {
    Layout.fillWidth: true
    spacing: 6
    Repeater {
     model: controllerRuntime.channels
     Rectangle {
      required property var modelData
      required property int index
      width: 86; height: 34; radius: 8; color: "#0f1b2a"; border.color: root.line
      Text { anchors.centerIn: parent; text: "К" + (index + 1) + ": " + Math.round(modelData); color: root.sub; font.pixelSize: 12 }
     }
    }
   }
  }

  Text {
   objectName: "stepError"
   visible: controllerRuntime.stepError !== ""
   text: controllerRuntime.stepError
   color: root.amber; wrapMode: Text.WordWrap; Layout.fillWidth: true
  }

  Rectangle {
   objectName: "swapSwitchSection"
   Layout.fillWidth: true
   implicitHeight: swapColumn.implicitHeight + 20
   radius: 8
   color: "#0f1c2b"
   border.color: "#2f4860"
   ColumnLayout {
    id: swapColumn
    anchors.fill: parent
    anchors.margins: 10
    spacing: 6
    Text { text: "Тумблер «поміняти потоки місцями»"; color: root.fg; font.bold: true }
    Text {
     text: "У польоті кожне перемикання цього тумблера міняє основне і додаткове відео місцями."
     color: root.sub; wrapMode: Text.WordWrap; Layout.fillWidth: true; font.pixelSize: 12
    }
    RowLayout {
     spacing: 8
     Text { objectName: "swapChannel"; text: controllerActions.swapText; color: root.fg; font.pixelSize: 15; Layout.fillWidth: true }
     Button { objectName: "assignSwap"; text: "Призначити"; enabled: !controllerActions.learning; onClicked: controllerActions.learnSwap() }
     Button { objectName: "clearSwap"; text: "Прибрати"; flat: true; visible: controllerActions.assigned && !controllerActions.learning; onClicked: controllerActions.clearSwap() }
    }
    Text { objectName: "swapMessage"; visible: text !== ""; text: controllerActions.message; color: root.sub; wrapMode: Text.WordWrap; Layout.fillWidth: true; font.pixelSize: 12 }
   }
  }

  Item { Layout.fillHeight: true }

  RowLayout {
   Layout.fillWidth: true
   spacing: 8
   Button {
    objectName: "configureController"
    visible: controllerRuntime.canConfigure || controllerRuntime.canForget
    enabled: !controllerRuntime.wizardActive
    text: controllerRuntime.restored ? "Налаштувати заново" : "Налаштувати пульт"
    highlighted: !controllerRuntime.restored
    onClicked: controllerRuntime.startWizard()
   }
   Button {
    visible: controllerRuntime.wizardActive
    text: controllerRuntime.wizardStep === "sweep" ? "Готово" : "Далі"
    highlighted: true
    onClicked: controllerRuntime.nextStep()
   }
   Button {
    visible: controllerRuntime.wizardActive
    text: "Скасувати"
    flat: true
    onClicked: controllerRuntime.cancelWizard()
   }
   Item { Layout.fillWidth: true }
   Button {
    visible: controllerRuntime.canForget
    text: "Забути налаштування"
    flat: true
    onClicked: controllerRuntime.forgetProfile()
   }
  }
 }
}
