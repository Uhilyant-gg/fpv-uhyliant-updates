import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

ApplicationWindow {
 id: w
 visible: true
 visibility: Window.Maximized
 minimumWidth: 1024
 minimumHeight: 640
 color: "#050a12"
 title: appWindowTitle
 property color fg: "#f4f7fb"
 property color sub: "#8fa1b7"
 property color panel: "#e6101927"
 property color line: "#273d55"
 property color green: "#27d59a"
 property color blue: "#4aa3ff"
 property color amber: "#ffb84d"
 property bool updateOpen: false
 property bool deviceOpen: false
 property bool diagnosticsOpen: false
 property string clockText: ""

 component Glass: Rectangle { color: w.panel; border.color: w.line; border.width: 1; radius: 12 }
 component StatusCard: Glass {
  required property string titleText
  required property string valueText
  required property color accent
  implicitWidth: 190; implicitHeight: 72
  Column { anchors.fill: parent; anchors.margins: 12; spacing: 4
   Text { text: titleText; color: w.sub; font.pixelSize: 12; font.bold: true }
   Text { text: valueText; color: accent; font.pixelSize: 17; font.bold: true }
  }
 }

 Timer { interval: 1000; running: true; repeat: true; triggeredOnStart: true; onTriggered: clockText = Qt.formatDateTime(new Date(), "dd.MM.yyyy  hh:mm:ss") }
 Shortcut { sequence: "F2"; onActivated: station.toggleVideo() }
 Shortcut { sequence: "F11"; onActivated: w.visibility = w.visibility === Window.FullScreen ? Window.Maximized : Window.FullScreen }
 Shortcut { sequence: "Escape"; onActivated: { station.setOSDEdit(false); station.menuOpen ? station.toggleMenu() : null; updateOpen=false; deviceOpen=false; diagnosticsOpen=false } }

 Image { anchors.fill: parent; source: "preview.jpg"; fillMode: Image.PreserveAspectCrop; opacity: station.videoRunning ? 0.80 : 0.16 }
 Rectangle { anchors.fill: parent; color: "#8a030812" }

 Rectangle {
  id: topBar; height: 74; anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top; color: "#f20a1220"; border.color: line
  RowLayout { anchors.fill: parent; anchors.leftMargin: 20; anchors.rightMargin: 16; spacing: 16
   Rectangle { width: 10; height: 34; radius: 5; color: blue }
   ColumnLayout { spacing: 1
    Text { text: "ФПВ УХИЛЯНТ"; color: fg; font.pixelSize: 22; font.bold: true; font.letterSpacing: 1.1 }
    Text { text: "НАЗЕМНА СТАНЦІЯ  •  " + updater.currentVersion; color: sub; font.pixelSize: 11 }
   }
   Item { Layout.fillWidth: true }
   Rectangle { width: 8; height: 8; radius: 4; color: green
    SequentialAnimation on opacity { loops: Animation.Infinite; NumberAnimation { to: .35; duration: 900 } NumberAnimation { to: 1; duration: 900 } }
   }
   Text { text: "СТАНЦІЯ ГОТОВА"; color: green; font.bold: true; font.pixelSize: 12 }
   Text { text: clockText; color: fg; font.family: "Consolas"; font.pixelSize: 14 }
   Button { text: station.menuOpen ? "✕" : "☰"; onClicked: station.toggleMenu() }
  }
 }

 RowLayout {
  anchors.left: parent.left; anchors.right: parent.right; anchors.top: topBar.bottom; anchors.bottom: bottomBar.top
  anchors.margins: 16; spacing: 14

  Glass {
   Layout.preferredWidth: 86; Layout.fillHeight: true
   ColumnLayout { anchors.fill: parent; anchors.margins: 10; spacing: 10
    Button { text: "⌂"; font.pixelSize: 20; Layout.fillWidth: true; onClicked: { deviceOpen=false; diagnosticsOpen=false } }
    Button { text: "▣"; font.pixelSize: 20; Layout.fillWidth: true; onClicked: deviceOpen=true; ToolTip.visible: hovered; ToolTip.text: "Пристрої" }
    Button { text: "◉"; font.pixelSize: 20; Layout.fillWidth: true; onClicked: station.toggleVideo(); ToolTip.visible: hovered; ToolTip.text: "Відео, F2" }
    Button { text: "✚"; font.pixelSize: 20; Layout.fillWidth: true; onClicked: diagnosticsOpen=true; ToolTip.visible: hovered; ToolTip.text: "Діагностика" }
    Item { Layout.fillHeight: true }
    Button { text: "⚙"; font.pixelSize: 20; Layout.fillWidth: true; onClicked: station.toggleMenu() }
   }
  }

  Item {
   Layout.fillWidth: true; Layout.fillHeight: true
   Glass { anchors.fill: parent
    Rectangle { anchors.fill: parent; anchors.margins: 8; radius: 8; color: "#aa030812"; border.color: "#20354a" }
    Column { visible: !station.videoRunning; anchors.centerIn: parent; spacing: 10
     Rectangle { width: 92; height: 92; radius: 46; color: "#15283b"; border.color: blue; anchors.horizontalCenter: parent.horizontalCenter
      Text { anchors.centerIn: parent; text: "▶"; color: blue; font.pixelSize: 36 }
     }
     Text { text: "ВІДЕОПОТІК НЕ ПІДКЛЮЧЕНО"; color: fg; font.pixelSize: 20; font.bold: true; anchors.horizontalCenter: parent.horizontalCenter }
     Text { text: "Натисніть F2 або кнопку відео для тестового запуску"; color: sub; font.pixelSize: 14; anchors.horizontalCenter: parent.horizontalCenter }
    }
    Rectangle { visible: station.videoRunning; anchors.left: parent.left; anchors.top: parent.top; anchors.margins: 20; width: 132; height: 34; radius: 17; color: "#cc0d2b20"; border.color: green
     Row { anchors.centerIn: parent; spacing: 8; Rectangle { width: 8; height: 8; radius: 4; color: green } Text { text: "VIDEO ACTIVE"; color: green; font.bold: true; font.pixelSize: 11 } }
    }
   }
  }

  ColumnLayout {
   Layout.preferredWidth: Math.min(330, w.width * .24); Layout.fillHeight: true; spacing: 12
   Glass { Layout.fillWidth: true; Layout.preferredHeight: 150
    ColumnLayout { anchors.fill: parent; anchors.margins: 16; spacing: 8
     Text { text: "АКТИВНИЙ БОРТ"; color: sub; font.pixelSize: 12; font.bold: true }
     Text { text: "Не вибрано"; color: fg; font.pixelSize: 22; font.bold: true }
     Text { text: "База пристроїв буде наступним модулем"; color: sub; wrapMode: Text.WordWrap; Layout.fillWidth: true }
     Button { text: "Відкрити пристрої"; Layout.fillWidth: true; onClicked: deviceOpen=true }
    }
   }
   StatusCard { Layout.fillWidth: true; titleText: "ВІДЕО"; valueText: station.videoRunning ? "ТЕСТОВИЙ ПОТІК" : "НЕ ПІДКЛЮЧЕНО"; accent: station.videoRunning ? green : amber }
   StatusCard { Layout.fillWidth: true; titleText: "ТЕЛЕМЕТРІЯ"; valueText: "НЕ НАЛАШТОВАНО"; accent: sub }
   StatusCard { Layout.fillWidth: true; titleText: "МЕРЕЖА БОРТА"; valueText: "НЕ ПЕРЕВІРЕНО"; accent: sub }
   Glass { Layout.fillWidth: true; Layout.fillHeight: true
    ColumnLayout { anchors.fill: parent; anchors.margins: 16; spacing: 8
     Text { text: "ШВИДКІ ДІЇ"; color: sub; font.pixelSize: 12; font.bold: true }
     Button { text: "Перевірити оновлення"; Layout.fillWidth: true; onClicked: { updateOpen=true; updater.check() } }
     Button { text: "Діагностика станції"; Layout.fillWidth: true; onClicked: diagnosticsOpen=true }
     Item { Layout.fillHeight: true }
     Text { text: "F11 — повний екран\nF2 — відео\nEsc — закрити панелі"; color: sub; lineHeight: 1.35 }
    }
   }
  }
 }

 Rectangle {
  id: bottomBar; height: 36; anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom; color: "#f20a1220"; border.color: line
  RowLayout { anchors.fill: parent; anchors.leftMargin: 18; anchors.rightMargin: 18
   Text { text: "●  CORE ONLINE"; color: green; font.bold: true; font.pixelSize: 11 }
   Text { text: "DEVICE: --"; color: sub; font.pixelSize: 11 }
   Text { text: "FC: --"; color: sub; font.pixelSize: 11 }
   Text { text: "CAMERA: --"; color: sub; font.pixelSize: 11 }
   Item { Layout.fillWidth: true }
   Text { text: appWindowTitle; color: sub; font.pixelSize: 11 }
  }
 }

 Glass {
  visible: station.menuOpen; z: 20; width: 360; anchors.right: parent.right; anchors.top: topBar.bottom; anchors.bottom: bottomBar.top; anchors.margins: 12
  ColumnLayout { anchors.fill: parent; anchors.margins: 16; spacing: 10
   Text { text: "МЕНЮ СТАНЦІЇ"; color: fg; font.pixelSize: 18; font.bold: true }
   Rectangle { Layout.fillWidth: true; height: 1; color: line }
   Button { text: "Пристрої"; Layout.fillWidth: true; onClicked: { deviceOpen=true; station.toggleMenu() } }
   Button { text: "Діагностика"; Layout.fillWidth: true; onClicked: { diagnosticsOpen=true; station.toggleMenu() } }
   Button { text: "Оновлення станції"; Layout.fillWidth: true; onClicked: { updateOpen=true; station.toggleMenu() } }
   Text { text: "OSD"; color: sub; font.bold: true }
   ComboBox { Layout.fillWidth: true; model: ["OSD станції","OSD автопілота","OSD вимкнено"]; onActivated: station.setOSDSource(["station","fc","off"][currentIndex]) }
   CheckBox { text: "Редагувати OSD"; checked: station.osdEdit; onToggled: station.setOSDEdit(checked) }
   Text { text: "Прозорість"; color: sub }
   Slider { id: op; from: .2; to: 1; value: station.osdOpacity; Layout.fillWidth: true; onMoved: station.setOSDStyle(value, sz.value) }
   Text { text: "Масштаб"; color: sub }
   Slider { id: sz; from: .65; to: 1.25; value: station.osdScale; Layout.fillWidth: true; onMoved: station.setOSDStyle(op.value, value) }
   Item { Layout.fillHeight: true }
   Button { text: "Вихід"; Layout.fillWidth: true; onClicked: Qt.quit() }
  }
 }

 Popup {
  id: devices; visible: deviceOpen; modal: true; anchors.centerIn: Overlay.overlay; width: Math.min(760, w.width-48); height: Math.min(540, w.height-80); onClosed: deviceOpen=false
  background: Rectangle { color: "#0d1725"; border.color: blue; radius: 14 }
  contentItem: ColumnLayout { anchors.fill: parent; anchors.margins: 22; spacing: 12
   Text { text: "ПРИСТРОЇ"; color: fg; font.pixelSize: 22; font.bold: true }
   Text { text: "Локальна база бортів, камер і політних контролерів"; color: sub }
   Glass { Layout.fillWidth: true; Layout.fillHeight: true
    Column { anchors.centerIn: parent; spacing: 10
     Text { text: "База пристроїв порожня"; color: fg; font.pixelSize: 20; font.bold: true; anchors.horizontalCenter: parent.horizontalCenter }
     Text { text: "Після стабілізації OTA тут з'являться Device ID, камера, FC, CRSF/MSP/MAVLink і пресети."; color: sub; width: 560; wrapMode: Text.WordWrap; horizontalAlignment: Text.AlignHCenter }
    }
   }
   RowLayout { Layout.fillWidth: true; Button { text: "+ Додати пристрій"; enabled: false } Item { Layout.fillWidth: true } Button { text: "Закрити"; onClicked: devices.close() } }
  }
 }

 Popup {
  id: diagnostics; visible: diagnosticsOpen; modal: true; anchors.centerIn: Overlay.overlay; width: Math.min(760, w.width-48); height: Math.min(560, w.height-80); onClosed: diagnosticsOpen=false
  background: Rectangle { color: "#0d1725"; border.color: green; radius: 14 }
  contentItem: ColumnLayout { anchors.fill: parent; anchors.margins: 22; spacing: 12
   Text { text: "ДІАГНОСТИКА СТАНЦІЇ"; color: fg; font.pixelSize: 22; font.bold: true }
   Text { text: "Фундаментальний екран. Автоматичні checks і support bundle будуть додані разом із базою пристроїв."; color: sub; wrapMode: Text.WordWrap; Layout.fillWidth: true }
   Repeater { model: [["Застосунок", "OK", green], ["Updater", updater.installReady ? "ГОТОВИЙ" : "ОЧІКУЄ ПАКЕТ", updater.installReady ? green : sub], ["Активний борт", "НЕ ВИБРАНО", sub], ["Камера", "НЕ НАЛАШТОВАНО", sub]]
    delegate: Glass { required property var modelData; Layout.fillWidth: true; height: 60
     RowLayout { anchors.fill: parent; anchors.margins: 14; Text { text: modelData[0]; color: fg; font.bold: true } Item { Layout.fillWidth: true } Text { text: modelData[1]; color: modelData[2]; font.bold: true } }
    }
   }
   Item { Layout.fillHeight: true }
   RowLayout { Layout.fillWidth: true; Button { text: "Швидка перевірка"; enabled: false } Button { text: "Створити звіт"; enabled: false } Item { Layout.fillWidth: true } Button { text: "Закрити"; onClicked: diagnostics.close() } }
  }
 }

 Popup {
  id: up; visible: updateOpen; modal: true; anchors.centerIn: Overlay.overlay; width: Math.min(720, w.width-48); height: Math.min(580, w.height-80); onClosed: updateOpen=false
  background: Rectangle { color: "#0d1725"; border.color: blue; radius: 14 }
  contentItem: ColumnLayout { anchors.fill: parent; anchors.margins: 22; spacing: 12
   Text { text: "ОНОВЛЕННЯ СТАНЦІЇ"; color: fg; font.pixelSize: 22; font.bold: true }
   Text { text: "Поточна: " + updater.currentVersion + "   Доступна: " + (updater.availableVersion || "--"); color: fg; font.pixelSize: 16 }
   Text { text: updater.manifestUrl; color: sub; wrapMode: Text.WrapAnywhere; Layout.fillWidth: true }
   RowLayout { Button { text: "Перевірити"; onClicked: updater.check() } Button { text: "Завантажити"; enabled: updater.updateState === "available"; onClicked: updater.download() } Item { Layout.fillWidth: true } Button { text: "Оновити"; enabled: updater.installReady; onClicked: updater.install() } }
   ProgressBar { from: 0; to: 100; value: updater.progress; Layout.fillWidth: true }
   Text { text: updater.updateStatus; color: updater.updateState === "error" ? "#ff6678" : (updater.installReady ? green : sub); wrapMode: Text.WordWrap; Layout.fillWidth: true }
   ListView { Layout.fillWidth: true; Layout.fillHeight: true; clip: true; model: updater.releaseNotes; delegate: Text { required property string modelData; text: "• " + modelData; color: fg; padding: 6; width: ListView.view.width; wrapMode: Text.WordWrap } }
   Button { text: "Закрити"; Layout.alignment: Qt.AlignRight; onClicked: up.close() }
  }
 }
}
