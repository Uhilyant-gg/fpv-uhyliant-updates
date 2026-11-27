import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
 id: root
 signal openDevices()
 signal openFirmware()
 signal openUpdate()
 signal openDiagnostics()
 signal openPreflight()
 signal openTimeline()
 signal openOsdSettings()
 signal openBackup()
 signal openSimulation()
 signal openController()
 signal connectDevice(string deviceId)
 signal runNextAction(string action)

 property color fg: "#f5f8fc"
 property color sub: "#c2cfdd"
 property color surface: "#d90b1725"
 property color elevated: "#e6162638"
 property color line: "#64788d"
 property color green: "#35e0a1"
 property bool menuOpen: false
 readonly property var menuItems: [
  {label: "Камери", detail: "Знайти або вибрати пристрій", glyph: "◉", action: "devices"},
  {label: "Пульт", detail: "Підключити та налаштувати стіки", glyph: "✥", action: "controller"},
  {label: "Підготовка", detail: "Перевірити стан системи", glyph: "✓", action: "preflight"},
  {label: "Симуляція", detail: "Налаштувати екран без обладнання", glyph: "▣", action: "simulation"},
  {label: "Події", detail: "Історія важливих змін", glyph: "⌁", action: "timeline"},
  {label: "Прошивка", detail: "Оновлення камери", glyph: "↑", action: "firmware"},
  {label: "Діагностика", detail: "Перевірити підключення", glyph: "⌕", action: "diagnostics"},
  {label: "Резервна копія", detail: "Зберегти або відновити", glyph: "▤", action: "backup"}
 ]

 function canEnterFpv(deviceId) {
  if (!deviceId) return false
  for (var i = 0; i < devicesModel.items.length; i++) {
   if (devicesModel.items[i].id !== deviceId) continue
   for (var n = 0; n < devicesModel.streams.length; n++)
    if (devicesModel.streams[n].device_id === deviceId && devicesModel.streams[n].enabled === true) return true
   return false
  }
  return false
 }
 function activateMenuItem(action) {
  menuOpen = false
  if (action === "devices") openDevices()
  else if (action === "preflight") openPreflight()
  else if (action === "simulation") openSimulation()
  else if (action === "timeline") openTimeline()
  else if (action === "firmware") openFirmware()
  else if (action === "diagnostics") openDiagnostics()
  else if (action === "backup") openBackup()
  else if (action === "controller") openController()
 }

 Rectangle {
  anchors.fill: parent
  gradient: Gradient {
   GradientStop { position: 0; color: "#182b3c" }
   GradientStop { position: 0.58; color: "#101e2b" }
   GradientStop { position: 1; color: "#071019" }
  }
 }

 ColumnLayout {
  anchors.fill: parent
  anchors.margins: 20
  spacing: 16

  Rectangle {
   Layout.fillWidth: true
   Layout.preferredHeight: 76
   radius: 12
   color: root.surface
   border.color: root.line

   RowLayout {
    anchors.fill: parent
    anchors.leftMargin: 18
    anchors.rightMargin: 14
    spacing: 14

    Rectangle {
     Layout.preferredWidth: 42
     Layout.preferredHeight: 42
     radius: 9
     color: "#183758"
     border.color: "#557da4"
     Text { anchors.centerIn: parent; text: "FPV"; color: "#e8f4ff"; font.pixelSize: 13; font.bold: true }
    }

    ColumnLayout {
     spacing: 1
     Text { text: "ФПВ УХИЛЯНТ"; color: root.fg; font.pixelSize: 21; font.bold: true; font.letterSpacing: 1 }
     Text { text: "НАЗЕМНА СТАНЦІЯ  ·  v" + updater.currentVersion; color: root.sub; font.pixelSize: 12 }
    }

    Item { Layout.fillWidth: true }

    Rectangle {
     Layout.preferredWidth: statusLabel.implicitWidth + 26
     Layout.preferredHeight: 38
     radius: 8
     color: "#99101925"
     border.color: root.line
     RowLayout {
      anchors.centerIn: parent
      spacing: 8
      Rectangle {
       width: 9; height: 9; radius: 5
       color: homeDashboard.health === "ready" ? root.green :
              (homeDashboard.health === "problem" ? "#ff6678" : "#ffbd59")
      }
      Text {
       id: statusLabel
       text: homeDashboard.title
       color: root.fg
       font.pixelSize: 14
       font.bold: true
      }
     }
    }

    Button {
     objectName: "mainMenuToggle"
     Layout.preferredWidth: 48
     Layout.preferredHeight: 48
     Accessible.name: root.menuOpen ? "Закрити меню" : "Відкрити меню"
     onClicked: root.menuOpen = !root.menuOpen
     background: Rectangle {
      radius: 9
      color: parent.hovered ? "#334b64" : "#1d3145"
      border.color: root.menuOpen ? "#6eafe8" : "#506b84"
     }
     contentItem: Item {
      Rectangle { width: 22; height: 2; radius: 1; color: root.fg; anchors.horizontalCenter: parent.horizontalCenter; y: 15 }
      Rectangle { width: 22; height: 2; radius: 1; color: root.fg; anchors.horizontalCenter: parent.horizontalCenter; y: 23 }
      Rectangle { width: 22; height: 2; radius: 1; color: root.fg; anchors.horizontalCenter: parent.horizontalCenter; y: 31 }
     }
    }
   }
  }

  Rectangle {
   Layout.fillWidth: true
   Layout.preferredHeight: 118
   radius: 12
   color: root.surface
   border.color: homeDashboard.health === "problem" ? "#ff6678" :
                 (homeDashboard.health === "attention" ? "#ffbd59" :
                  (homeDashboard.health === "ready" ? root.green : root.line))

   RowLayout {
    anchors.fill: parent
    anchors.margins: 16
    spacing: 14

    Rectangle {
     Layout.preferredWidth: 56; Layout.preferredHeight: 56; radius: 28
     color: homeDashboard.health === "ready" ? "#15392f" :
            (homeDashboard.health === "problem" ? "#3a1d27" : "#3a301b")
     Text {
      anchors.centerIn: parent
      text: homeDashboard.health === "ready" ? "✓" : (homeDashboard.health === "problem" ? "!" : "?")
      color: homeDashboard.health === "ready" ? root.green :
             (homeDashboard.health === "problem" ? "#ff6678" : "#ffbd59")
      font.pixelSize: 25
      font.bold: true
     }
    }

    ColumnLayout {
     Layout.fillWidth: true
     spacing: 4
     Text { text: "Стан системи"; color: root.sub; font.pixelSize: 13 }
     Text { text: homeDashboard.summary; color: root.fg; font.pixelSize: 17; font.bold: true; wrapMode: Text.WordWrap; Layout.fillWidth: true }
     Text {
      text: "На головному екрані: " + homeDashboard.deviceCount +
            "   ·   Очікують перевірки: " + homeDashboard.pendingCount +
            "   ·   Потребують уваги: " + homeDashboard.warningCount
      color: root.sub
      font.pixelSize: 13
      elide: Text.ElideRight
      Layout.fillWidth: true
     }
    }

    Button {
     objectName: "homeNextAction"
     visible: homeDashboard.nextAction.available
     text: homeDashboard.nextAction.label
     font.pixelSize: 15
     font.bold: true
     Layout.minimumWidth: 154
     Layout.preferredHeight: 48
     onClicked: root.runNextAction(homeDashboard.nextAction.action)
     HoverHint { text: "Рекомендована дія для поточного стану." }
    }
   }
  }

  Rectangle {
   Layout.fillWidth: true
   Layout.fillHeight: true
   radius: 12
   color: root.surface
   border.color: root.line

   ColumnLayout {
    anchors.fill: parent
    anchors.margins: 14
    spacing: 10
    RowLayout {
     Layout.fillWidth: true
     Text { text: "МОЇ КАМЕРИ"; color: root.fg; font.bold: true; font.pixelSize: 15; font.letterSpacing: 1 }
     Text { text: homeDashboard.deviceCount ? homeDashboard.deviceCount + " готово" : (homeDashboard.pendingCount ? homeDashboard.pendingCount + " на перевірці" : "ще не додано"); color: root.sub; font.pixelSize: 13 }
     Item { Layout.fillWidth: true }
     Button {
      visible: updater.updateState === "available" || updater.updateState === "ready"
      text: updater.updateState === "ready" ? "Встановити " + updater.availableVersion : "Оновити до " + updater.availableVersion
      font.pixelSize: 14
      onClicked: root.openUpdate()
     }
    }

    ListView {
     id: list
     Layout.fillWidth: true
     Layout.fillHeight: true
     clip: true
     spacing: 6
     model: devicesModel.homeItems
     delegate: Rectangle {
      required property var modelData
      width: list.width
      height: 68
      radius: 9
      color: rowHover.hovered ? root.elevated : "#58132130"
      border.color: modelData.active ? root.green : "#454f6070"
      HoverHandler { id: rowHover }
      RowLayout {
       anchors.fill: parent
       anchors.leftMargin: 12
       anchors.rightMargin: 12
       spacing: 11
       Rectangle {
        Layout.preferredWidth: 38; Layout.preferredHeight: 38; radius: 8
        color: modelData.openipcIdentity.verified ? "#15392f" : "#253449"
        border.color: modelData.openipcIdentity.verified ? root.green : root.line
        Text { anchors.centerIn: parent; text: "◉"; color: modelData.openipcIdentity.verified ? root.green : root.sub; font.pixelSize: 18 }
       }
       ColumnLayout {
        Layout.fillWidth: true
        spacing: 2
        Text { text: modelData.name; color: root.fg; font.bold: true; font.pixelSize: 16 }
        Text { text: modelData.host + (modelData.openipcIdentity.verified ? "  ·  OpenIPC" : ""); color: root.sub; font.pixelSize: 13 }
       }
       Text { visible: modelData.active; text: "АКТИВНА"; color: root.green; font.bold: true; font.pixelSize: 12 }
       Button {
        text: "Відкрити FPV"
        enabled: root.canEnterFpv(modelData.id)
        font.pixelSize: 14
        onClicked: root.connectDevice(modelData.id)
       }
      }
     }

     Column {
      anchors.centerIn: parent
      visible: devicesModel.homeItems.length === 0
      spacing: 6
      Text { anchors.horizontalCenter: parent.horizontalCenter; text: devicesModel.pendingCount ? "Камера ще проходить перевірку" : "Камер ще не додано"; color: root.fg; font.pixelSize: 19; font.bold: true }
      Text { anchors.horizontalCenter: parent.horizontalCenter; text: devicesModel.pendingCount ? "На головний екран камера потрапить після підтвердження прошивки та відео." : "Відкрийте меню та виберіть «Камери»"; color: root.sub; font.pixelSize: 15; wrapMode: Text.WordWrap; width: list.width * 0.8; horizontalAlignment: Text.AlignHCenter }
     }
    }
   }
  }
 }

 Rectangle {
  anchors.fill: parent
  visible: root.menuOpen
  color: "transparent"
  z: 10
  MouseArea { anchors.fill: parent; onClicked: root.menuOpen = false }
 }

 Rectangle {
  id: drawer
  objectName: "mainMenuDrawer"
  z: 11
  visible: root.menuOpen
  anchors.top: parent.top
  anchors.right: parent.right
  anchors.topMargin: 96
  anchors.rightMargin: 20
  width: Math.min(350, root.width - 40)
  height: Math.min(drawerContent.implicitHeight + 30, root.height - 116)
  radius: 12
  color: "#f20a1420"
  border.color: "#71879c"
  clip: true

  ColumnLayout {
   id: drawerContent
   anchors.fill: parent
   anchors.margins: 14
   spacing: 5
   Text { text: "МЕНЮ СТАНЦІЇ"; color: root.sub; font.pixelSize: 12; font.bold: true; font.letterSpacing: 1; Layout.bottomMargin: 4 }
   Repeater {
    model: root.menuItems
    delegate: Button {
     required property var modelData
     objectName: "menu-" + modelData.action
     Layout.fillWidth: true
     Layout.preferredHeight: 58
     flat: true
     onClicked: root.activateMenuItem(modelData.action)
     background: Rectangle {
      radius: 8
      color: parent.hovered ? "#40566e" : "#181a2b3c"
      border.color: parent.hovered ? "#7897b5" : "#3b566d"
     }
     contentItem: RowLayout {
      spacing: 12
      Rectangle {
       Layout.preferredWidth: 36; Layout.preferredHeight: 36; radius: 8
       color: "#2b4259"
       Text { anchors.centerIn: parent; text: modelData.glyph; color: "#f2f7fc"; font.pixelSize: 19; font.bold: true }
      }
      ColumnLayout {
       Layout.fillWidth: true
       spacing: 1
       Text { text: modelData.label; color: root.fg; font.pixelSize: 16; font.bold: true }
       Text { text: modelData.detail; color: root.sub; font.pixelSize: 12; Layout.fillWidth: true; elide: Text.ElideRight }
      }
      Text { text: "›"; color: "#d8e5f1"; font.pixelSize: 22 }
     }
    }
   }
   Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: "#627489" }
   Text {
    text: "Налаштування OSD доступні в розділі «Підготовка»."
    color: root.sub
    wrapMode: Text.WordWrap
    font.pixelSize: 12
    Layout.fillWidth: true
    Layout.topMargin: 2
   }
  }
 }

 Component.onCompleted: updater.check()
}
