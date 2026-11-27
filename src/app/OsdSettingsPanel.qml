import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
 id: root
 signal closeRequested()
 property bool editingAllowed: true
 property var elementOptions: [
  {name:"link", label:"Стан зв’язку", shortLabel:"Зв’язок"},
  {name:"arm", label:"Стан ARM", shortLabel:"ARM"},
  {name:"mode", label:"Режим польоту", shortLabel:"Режим"},
  {name:"battery", label:"Акумулятор"},
  {name:"gps", label:"GPS і супутники", shortLabel:"GPS"},
  {name:"altitude", label:"Висота"},
  {name:"speed", label:"Швидкість"},
  {name:"heading", label:"Напрямок"},
  {name:"video", label:"Стан відео", shortLabel:"Відео"},
  {name:"homeDistance", label:"Відстань до точки повернення", shortLabel:"Відстань додому"},
  {name:"reticle", label:"Приціл"},
  {name:"horizon", label:"Штучний горизонт", shortLabel:"Горизонт"}
 ]
 property var aspectRatios: [16 / 9, 4 / 3, 1, 9 / 16]
 property var layoutOptions: [
  {value:"corners", label:"По кутах (рекомендовано)"},
  {value:"top-left", label:"Стовпчиком зліва вгорі"},
  {value:"top-right", label:"Стовпчиком справа вгорі"},
  {value:"bottom-left", label:"Стовпчиком зліва внизу"},
  {value:"bottom-right", label:"Стовпчиком справа внизу"}
 ]
 function layoutIndex(value) {
  for (var i = 0; i < layoutOptions.length; i++) if (layoutOptions[i].value === value) return i
  return 0
 }

 function elementLabel(name) {
  for (var i = 0; i < elementOptions.length; i++) {
   if (elementOptions[i].name === name) return elementOptions[i].label
  }
  return name
 }

 function layoutIssueText(issue) {
  if (issue.kind === "safe-area") return elementLabel(issue.name) + " виходить за безпечну область"
  return elementLabel(issue.first) + " перекриває " + elementLabel(issue.second)
 }

 Rectangle {
  anchors.fill: parent
  color: "transparent"
 }

 ColumnLayout {
  anchors.fill: parent
  spacing: 14

  RowLayout {
   Layout.fillWidth: true
   Text {
    text: "Налаштування OSD станції"
    color: "#f4f7fb"
    font.pixelSize: 20
    font.bold: true
    Layout.fillWidth: true
   }
   Button { text: "Закрити"; onClicked: root.closeRequested() }
  }

  Text {
   text: "OSD станції — окремий шар поверх відео. Відео з польотника та його власне OSD не змінюються."
   color: "#aebdd0"
   wrapMode: Text.WordWrap
   Layout.fillWidth: true
  }

  RowLayout {
   Layout.fillWidth: true
   Layout.fillHeight: true
   spacing: 18

   ScrollView {
    enabled: root.editingAllowed
    id: settingsScroll
    Layout.preferredWidth: 360
    Layout.fillHeight: true
    contentWidth: availableWidth
    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
    clip: true
    ColumnLayout {
     width: settingsScroll.availableWidth - 12
     spacing: 10

     Switch { text: "Показувати OSD станції"; Layout.fillWidth: true; checked: station.osdEnabled; onToggled: station.setOSDEnabled(checked) }
     Text {
      text: "Відео з камери не змінюється. Якщо її OSD вбудоване в зображення, приховати його тут неможливо."
      color: "#b7c8da"
      wrapMode: Text.WordWrap
      Layout.fillWidth: true
     }
     Text { text: "Розміщення елементів"; color: "#dce6f2"; font.bold: true }
     ComboBox {
      objectName: "osdLayoutSelector"
      Layout.fillWidth: true
      model: root.layoutOptions.map(function(option) { return option.label })
      currentIndex: root.layoutIndex(station.osdPosition)
      onActivated: function(index) { station.setOSDPosition(root.layoutOptions[index].value) }
     }
     Text { text: "Елемент можна перетягнути на попередньому перегляді — він прилипає до сітки з кроком 5% і залишається на своєму місці."; color: "#9fb2c6"; wrapMode: Text.WordWrap; Layout.fillWidth: true; font.pixelSize: 12 }

     Text { text: "Прозорість підкладки: " + Math.round((1 - station.osdOpacity) * 100) + "%"; color: "#dce6f2"; font.bold: true }
     Slider {
      id: opacitySlider
      objectName: "osdTransparencySlider"
      Layout.fillWidth: true
      from: 0
      to: 1
      stepSize: 0.05
      value: 1 - station.osdOpacity
      onMoved: station.setOSDStyle(1 - value, scaleSlider.value)
     }

     Text { text: "Розмір тексту: " + Math.round(station.osdScale * 100) + "%"; color: "#dce6f2"; font.bold: true }
     Slider {
      id: scaleSlider
      Layout.fillWidth: true
      from: 0.85
      to: 1.3
      stepSize: 0.05
      value: station.osdScale
      onMoved: station.setOSDStyle(1 - opacitySlider.value, value)
     }

     Text { text: "Елементи"; color: "#dce6f2"; font.bold: true; font.pixelSize: 15 }
     GridLayout {
      columns: 2
      columnSpacing: 4
      rowSpacing: 0
      Layout.fillWidth: true
      Repeater {
       model: root.elementOptions
       CheckBox {
        required property var modelData
        objectName: "osd-toggle-" + modelData.name
        Layout.fillWidth: true
        Layout.preferredWidth: 1
        text: modelData.shortLabel || modelData.label
        checked: station.osdEnabledElements[modelData.name] === true
        onToggled: station.setOSDElementEnabled(modelData.name, checked)
       }
      }
     }
     Button {
      text: "Стандартні налаштування"
      Layout.fillWidth: true
      onClicked: station.resetOSDStyle()
     }

     Text { text: "Попередження в польоті"; color: "#dce6f2"; font.bold: true; font.pixelSize: 15; Layout.topMargin: 8 }
     Text {
      text: "Значення 0 вимикає попередження. Спрацьовують лише свіжі дані телеметрії."
      color: "#9fb2c6"; wrapMode: Text.WordWrap; Layout.fillWidth: true; font.pixelSize: 11
     }
     GridLayout {
      columns: 2
      Layout.fillWidth: true
      columnSpacing: 10
      Text { text: "Якість лінку (LQ) нижче, %"; color: "#dce6f2"; Layout.fillWidth: true; wrapMode: Text.WordWrap }
      SpinBox {
       objectName: "alertLinkQualityMin"
       from: 0; to: 100; stepSize: 5; editable: true
       value: station.alertThresholds.linkQualityMin
       onValueModified: station.setAlertThreshold("linkQualityMin", value)
      }
      Text { text: "Заряд батареї нижче, %"; color: "#dce6f2"; Layout.fillWidth: true; wrapMode: Text.WordWrap }
      SpinBox {
       objectName: "alertBatteryRemainingMin"
       from: 0; to: 100; stepSize: 5; editable: true
       value: station.alertThresholds.batteryRemainingMin
       onValueModified: station.setAlertThreshold("batteryRemainingMin", value)
      }
      Text { text: "Кількість банок акумулятора (0 — не задано)"; color: "#dce6f2"; Layout.fillWidth: true; wrapMode: Text.WordWrap }
      SpinBox {
       objectName: "alertCellCount"
       from: 0; to: 12; editable: true
       value: station.alertThresholds.cellCount
       onValueModified: station.setAlertThreshold("cellCount", value)
      }
      Text { text: "Напруга на банку нижче, В"; color: "#dce6f2"; Layout.fillWidth: true; wrapMode: Text.WordWrap }
      SpinBox {
       objectName: "alertCellVoltageMin"
       from: 0; to: 420; stepSize: 5; editable: true
       value: Math.round(station.alertThresholds.cellVoltageMin * 100)
       textFromValue: function(v) { return (v / 100).toFixed(2) }
       valueFromText: function(text) { return Math.round(Number(String(text).replace(",", ".")) * 100) }
       onValueModified: station.setAlertThreshold("cellVoltageMin", value / 100)
      }
     }
     Button {
      text: "Стандартні пороги попереджень"
      Layout.fillWidth: true
      onClicked: station.resetAlertThresholds()
     }
    }
   }

   ColumnLayout {
    Layout.fillWidth: true
    Layout.fillHeight: true
    spacing: 6
    Text {
     objectName: "osd-editing-locked"
     visible: !root.editingAllowed
     text: "Телеметрія показує ARM. Редагування OSD заблоковане до завершення польоту."
     color: "#ffcf70"
     wrapMode: Text.WordWrap
     Layout.fillWidth: true
    }
    Text { text: "Попередній перегляд · екран польоту"; color: "#dce6f2"; font.bold: true }
     RowLayout {
     Layout.fillWidth: true
      Text { text: "Формат перевірки"; color: "#dce6f2" }
      ComboBox {
       id: aspectSelector
       objectName: "osdPreviewAspectSelector"
       Layout.preferredWidth: 220
       model: ["Широкий 16:9", "Класичний 4:3", "Квадрат 1:1", "Вертикальний 9:16"]
     }
      Item { Layout.fillWidth: true }
     }
     Item {
      id: previewHost
      objectName: "osdPreviewHost"
      Layout.fillWidth: true
      Layout.fillHeight: true
      Layout.minimumHeight: 150

      Rectangle {
       id: preview
       objectName: "osdPreviewViewport"
       property real aspectRatio: root.aspectRatios[aspectSelector.currentIndex]
       width: Math.min(previewHost.width, previewHost.height * aspectRatio)
       height: Math.min(previewHost.height, previewHost.width / aspectRatio)
       anchors.centerIn: parent
       gradient: Gradient {
        GradientStop { position: 0; color: "#355d78" }
        GradientStop { position: 0.55; color: "#9db4b1" }
        GradientStop { position: 0.56; color: "#465c45" }
        GradientStop { position: 1; color: "#182b23" }
       }
       border.color: "#273d55"
       clip: true
       Repeater {
        model: 19
        Rectangle { required property int index; x: preview.width * (index + 1) / 20; height: preview.height; width: 1; color: "#55ffffff" }
       }
       Repeater {
        model: 19
        Rectangle { required property int index; y: preview.height * (index + 1) / 20; width: preview.width; height: 1; color: "#55ffffff" }
       }
       Rectangle {
        anchors.fill: parent
        anchors.leftMargin: previewOsd.safeMarginX
        anchors.rightMargin: previewOsd.safeMarginX
        anchors.topMargin: previewOsd.safeMarginY
        anchors.bottomMargin: previewOsd.safeMarginY
        color: "transparent"
        border.color: "#a9e3f2"
        border.width: 1
        z: 1
       }
       OsdOverlay {
        id: previewOsd
        objectName: "osdPreviewOverlay"
        anchors.fill: parent
        editing: root.editingAllowed
        positions: station.osdElements
        enabledElements: station.osdEnabledElements
        corner: station.osdPosition
        telemetry: ({connected:true, provider:"MAVLink", armed:false, flightMode:"STABILIZE", batteryVoltage:15.8, batteryRemaining:82, gpsFix:3, satellites:12, altitude:124, groundSpeed:12.4, heading:348, roll:7, pitch:-3, yaw:348, homeDistance:86})
        video: ({streamId:"simulation", state:"playing"})
        opacityValue: station.osdOpacity
        scaleFactor: station.osdScale
        onPositionChanged: function(name, x, y) { station.setOSDElementPosition(name, x, y) }
       }
     }
     }
     Text {
      objectName: "osd-layout-warning"
      visible: previewOsd.layoutIssues.length > 0
      text: {
       var messages = []
       for (var i = 0; i < previewOsd.layoutIssues.length; i++) messages.push(root.layoutIssueText(previewOsd.layoutIssues[i]))
       return messages.join(" · ") + ". Перетягніть позначені елементи по сітці. Розташування не змінюється автоматично."
      }
      color: "#ffcf70"
      wrapMode: Text.WordWrap
      Layout.fillWidth: true
    }
   }
  }

  Text {
   visible: station.osdSettingsError !== ""
   text: station.osdSettingsError
   color: "#ff7080"
   wrapMode: Text.WordWrap
   Layout.fillWidth: true
  }

  Text {
   text: "Попередній перегляд використовує штучні дані. Зміни зберігаються автоматично й не впливають на реальний політ."
   color: "#b7c8da"
   font.pixelSize: 13
   Layout.fillWidth: true
  }
 }
}
