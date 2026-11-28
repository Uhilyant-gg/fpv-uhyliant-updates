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
 signal openPresets()
 signal openRecording()
 signal openStationSettings()
 signal openVehicleSettings()
 signal openService()
 signal connectDevice(string deviceId)
 signal openPreflightFor(string deviceId)
 signal openFirmwareFor(string deviceId)
 signal runNextAction(string action)

 property color fg: "#f5f8fc"
 property color sub: "#c2cfdd"
 property color surface: "#d90b1725"
 property color elevated: "#e6162638"
 property color line: "#64788d"
 property color green: "#35e0a1"
 property color amber: "#ffbd59"
 property color red: "#ff6678"
 property bool menuOpen: false
 readonly property var menuItems: [
  {label: "Камери", detail: "Знайти, вибрати або додати камеру", glyph: "◉", action: "devices", section: "main"},
  {label: "Дрони і пресети", detail: "Пресети, OSD і попередження для кожного дрона", glyph: "☰", action: "vehicles", section: "main"},
  {label: "Налаштування станції", detail: "Пульт, запис відео, ZeroTier, резервна копія", glyph: "⚙", action: "station", section: "main"},
  {label: "Обслуговування", detail: "Діагностика, події, прошивка камери", glyph: "⌕", action: "service", section: "main"}
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
 function connectionColor(state) {
  return state === "available" ? root.green : (state === "unavailable" ? root.red : (state === "checking" ? root.amber : "#5b6b7c"))
 }
 function connectionReady(deviceId) {
  var kind = connectionsRuntime.selected[deviceId] || ""
  var statuses = connectionsRuntime.statuses[deviceId] || {}
  return kind !== "" && statuses[kind] !== undefined && statuses[kind].state === "available"
 }
 function flyHint(deviceId) {
  if (!canEnterFpv(deviceId)) return "Для камери ще не налаштовано відеопотік."
  if (!(connectionsRuntime.selected[deviceId] || "")) return "Спершу виберіть тип підключення."
  if (!connectionReady(deviceId)) return "Вибране підключення зараз недоступне."
  return "Відкрити відео й перейти до польоту."
 }
 function countersText() {
  var parts = []
  if (homeDashboard.pendingCount > 0) parts.push("на перевірці: " + homeDashboard.pendingCount)
  if (homeDashboard.warningCount > 0) parts.push("потребують уваги: " + homeDashboard.warningCount)
  return parts.join("  ·  ")
 }
 function lastSeenText(seconds) {
  if (!seconds) return "ще не виходила на зв’язок"
  var age = Math.max(0, Date.now() / 1000 - seconds)
  if (age < 120) return "на зв’язку щойно"
  if (age < 3600) return Math.round(age / 60) + " хв тому"
  if (age < 86400) return Math.round(age / 3600) + " год тому"
  return Math.round(age / 86400) + " дн тому"
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
  else if (action === "presets") openPresets()
  else if (action === "recording") openRecording()
  else if (action === "station") openStationSettings()
  else if (action === "vehicles") openVehicleSettings()
  else if (action === "service") openService()
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

  // One header: station identity and version, system state with its next action, menu.
  Rectangle {
   objectName: "homeHeader"
   Layout.fillWidth: true
   Layout.preferredHeight: 84
   radius: 12
   color: root.surface
   border.color: homeDashboard.health === "problem" ? root.red :
                 (homeDashboard.health === "attention" ? root.amber : root.line)

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

    Button {
     objectName: "homeUpdate"
     visible: updater.updateState === "available" || updater.updateState === "ready"
     text: updater.updateState === "ready" ? "Встановити " + updater.availableVersion : "Оновити до " + updater.availableVersion
     font.pixelSize: 14
     font.bold: true
     Layout.preferredHeight: 40
     onClicked: root.openUpdate()
     contentItem: Text { text: parent.text; font: parent.font; color: "#06130d"; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
     background: Rectangle { radius: 8; color: parent.hovered ? "#5cf0bd" : root.green }
     HoverHint { text: "Вийшла нова версія програми." }
    }

    Rectangle { Layout.preferredWidth: 1; Layout.preferredHeight: 44; Layout.leftMargin: 6; color: "#33485e" }

    RowLayout {
     objectName: "homeStatus"
     Layout.fillWidth: true
     Layout.leftMargin: 6
     spacing: 10
     Rectangle {
      Layout.preferredWidth: 12; Layout.preferredHeight: 12; radius: 6
      color: homeDashboard.health === "ready" ? root.green : (homeDashboard.health === "problem" ? root.red : root.amber)
     }
     ColumnLayout {
      Layout.fillWidth: true
      spacing: 2
      Text { text: homeDashboard.summary; color: root.fg; font.pixelSize: 15; font.bold: true; elide: Text.ElideRight; Layout.fillWidth: true }
      Text {
       objectName: "homeCounters"
       visible: text !== ""
       text: root.countersText()
       color: root.sub
       font.pixelSize: 12
       elide: Text.ElideRight
       Layout.fillWidth: true
      }
     }
    }

    Button {
     objectName: "homeNextAction"
     visible: homeDashboard.nextAction.available && !(homeDashboard.nextAction.action === "find-camera" && devicesModel.homeItems.length === 0)
     text: homeDashboard.nextAction.label
     font.pixelSize: 15
     font.bold: true
     Layout.preferredHeight: 44
     onClicked: root.runNextAction(homeDashboard.nextAction.action)
     HoverHint { text: "Рекомендована дія для поточного стану." }
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

  RowLayout {
   Layout.fillWidth: true
   Text { text: "МОЇ КАМЕРИ"; color: root.fg; font.bold: true; font.pixelSize: 15; font.letterSpacing: 1 }
   Text { visible: devicesModel.homeItems.length > 0; text: devicesModel.homeItems.length; color: root.sub; font.pixelSize: 15; font.bold: true }
   Item { Layout.fillWidth: true }
   Button { objectName: "homeArchive"; visible: devicesModel.archivedItems.length > 0; text: "Архів (" + devicesModel.archivedItems.length + ")"; font.pixelSize: 14; onClicked: archiveDialog.open() }
   Button { objectName: "homeAddCamera"; visible: devicesModel.homeItems.length > 0; text: "+ Додати камеру"; font.pixelSize: 14; onClicked: root.openDevices() }
   Button { objectName: "homeSimulation"; visible: devicesModel.homeItems.length > 0; text: "▣ Симуляція"; font.pixelSize: 14; onClicked: root.openSimulation() }
  }

  Item {
   visible: devicesModel.homeItems.length > 0
   Layout.fillWidth: true
   Layout.fillHeight: true
  GridView {
   id: list
   objectName: "homeCameraGrid"
   anchors.fill: parent
   // Each cell carries a 14 px gap on its right; the view extends past the edge by that gap.
   anchors.rightMargin: -14
   clip: true
   model: devicesModel.homeItems
   readonly property int columns: Math.max(1, Math.floor(width / 316))
   cellWidth: Math.floor(width / columns)
   cellHeight: 236
   delegate: Item {
    id: cameraCell
    required property var modelData
    readonly property string cameraId: modelData.id
    readonly property string selectedKind: connectionsRuntime.selected[cameraId] || ""
    width: list.cellWidth
    height: list.cellHeight
    Rectangle {
     objectName: "cameraCard"
     anchors.fill: parent
     anchors.rightMargin: 14
     anchors.bottomMargin: 14
     radius: 11
     color: cardHover.hovered ? root.elevated : root.surface
     border.color: modelData.active ? root.green : root.line
     border.width: modelData.active ? 2 : 1
     HoverHandler { id: cardHover }
     ColumnLayout {
      anchors.fill: parent
      anchors.margins: 12
      spacing: 5
      RowLayout {
       Layout.fillWidth: true
       spacing: 8
       Rectangle {
        Layout.preferredWidth: 32; Layout.preferredHeight: 32; radius: 8
        color: modelData.openipcIdentity.verified ? "#15392f" : "#253449"
        border.color: modelData.openipcIdentity.verified ? root.green : root.line
        Text { anchors.centerIn: parent; text: "◉"; color: modelData.openipcIdentity.verified ? root.green : root.sub; font.pixelSize: 15 }
       }
       ColumnLayout {
        Layout.fillWidth: true
        spacing: 0
        Text { text: modelData.name; color: root.fg; font.bold: true; font.pixelSize: 15; elide: Text.ElideRight; Layout.fillWidth: true }
        Text { text: modelData.host + (modelData.openipcIdentity.verified ? " · OpenIPC " + modelData.versionLabel : ""); color: root.sub; font.pixelSize: 11; elide: Text.ElideRight; Layout.fillWidth: true }
       }
       Button {
        objectName: "cameraSettings"
        text: "⚙"
        font.pixelSize: 16
        Layout.preferredWidth: 32
        Layout.preferredHeight: 32
        onClicked: cameraSettings.show(cameraCell.modelData, "")
        HoverHint { text: "Налаштування камери." }
       }
      }
      RowLayout {
       spacing: 6
       Layout.fillWidth: true
       Rectangle {
        Layout.preferredWidth: 8; Layout.preferredHeight: 8; radius: 4
        color: modelData.health === "ready" ? root.green : (modelData.health === "problem" ? root.red : root.amber)
       }
       Text { text: modelData.healthLabel + " · " + root.lastSeenText(modelData.lastObservedAt); color: root.sub; font.pixelSize: 11; elide: Text.ElideRight; Layout.fillWidth: true }
       Text { visible: modelData.active; text: "АКТИВНА"; color: root.green; font.bold: true; font.pixelSize: 10 }
      }
      GridLayout {
       columns: 2
       columnSpacing: 5
       rowSpacing: 5
       Layout.fillWidth: true
       Layout.topMargin: 3
       Repeater {
        model: connectionsRuntime.types
        delegate: Button {
         id: chip
         required property var modelData
         readonly property var status: (connectionsRuntime.statuses[cameraCell.cameraId] || {})[modelData.key] || ({})
         readonly property bool chosen: cameraCell.selectedKind === modelData.key
         objectName: "connection-" + modelData.key
         Layout.fillWidth: true
         Layout.preferredWidth: 1
         Layout.preferredHeight: 34
         enabled: status.state !== "unsupported"
         onClicked: {
          if (modelData.key === "static" && status.state === "unconfigured") {
           // The station finds the pilot's white address and opens the port itself.
           connectionsRuntime.bindThisNetwork(cameraCell.cameraId)
           connectionsRuntime.select(cameraCell.cameraId, "static")
          } else if (modelData.needsAddress && status.state === "unconfigured") cameraSettings.show(cameraCell.modelData, modelData.key)
          else connectionsRuntime.select(cameraCell.cameraId, modelData.key)
         }
         background: Rectangle {
          radius: 6
          color: chip.chosen ? "#1f4d72" : (chip.hovered ? "#22364b" : "#132235")
          border.color: chip.chosen ? "#5aa4ff" : "#2f4860"
          border.width: chip.chosen ? 2 : 1
         }
         contentItem: RowLayout {
          spacing: 6
          Rectangle {
           Layout.preferredWidth: 8; Layout.preferredHeight: 8; radius: 4
           color: root.connectionColor(chip.status.state)
          }
          ColumnLayout {
           spacing: 0
           Layout.fillWidth: true
           Text { text: chip.modelData.label; color: chip.enabled ? root.fg : root.sub; font.pixelSize: 12; font.bold: chip.chosen; elide: Text.ElideRight; Layout.fillWidth: true }
           Text { text: chip.status.label || ""; color: root.sub; font.pixelSize: 10; elide: Text.ElideRight; Layout.fillWidth: true }
          }
         }
        }
       }
      }
      Item { Layout.fillHeight: true }
      RowLayout {
       Layout.fillWidth: true
       spacing: 6
       Button {
        objectName: "homePreflight"
        text: "✓ Підготовка"
        font.pixelSize: 12
        Layout.preferredHeight: 36
        onClicked: root.openPreflightFor(modelData.id)
       }
       Button {
        objectName: "cameraFly"
        text: "▶  Летіти"
        enabled: root.canEnterFpv(modelData.id) && root.connectionReady(cameraCell.cameraId)
        font.pixelSize: 14
        font.bold: true
        Layout.fillWidth: true
        Layout.preferredHeight: 36
        onClicked: root.connectDevice(modelData.id)
        contentItem: Text { text: parent.text; font: parent.font; color: parent.enabled ? "#06130d" : root.sub; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
        background: Rectangle { radius: 7; color: !parent.enabled ? "#1d2c3c" : (parent.hovered ? "#5cf0bd" : root.green) }
        HoverHint { text: root.flyHint(cameraCell.cameraId) }
       }
      }
     }
    }
   }
  }

  }

  // Empty state: what is needed, and two equal ways forward.
  Item {
   visible: devicesModel.homeItems.length === 0
   Layout.fillWidth: true
   Layout.fillHeight: true
   Rectangle {
    objectName: "homeEmptyCard"
    anchors.centerIn: parent
    width: Math.min(parent.width, 640)
    height: emptyColumn.implicitHeight + 56
    radius: 14
    color: root.surface
    border.color: root.line
    ColumnLayout {
     id: emptyColumn
     anchors.fill: parent
     anchors.margins: 28
     spacing: 10
     Text { Layout.alignment: Qt.AlignHCenter; text: "◉"; color: root.sub; font.pixelSize: 40 }
     Text {
      Layout.alignment: Qt.AlignHCenter
      text: devicesModel.pendingCount ? "Камера проходить перевірку" : (devicesModel.archivedItems.length ? "Усі камери в архіві" : "Камер ще не додано")
      color: root.fg; font.pixelSize: 21; font.bold: true
     }
     Text {
      Layout.fillWidth: true
      text: devicesModel.pendingCount
       ? "На головний екран камера потрапить після підтвердження прошивки та відео."
       : "Підключіть камеру OpenIPC до тієї ж мережі, що й цей комп’ютер, і запустіть пошук. Без обладнання можна спробувати симуляцію."
      color: root.sub; font.pixelSize: 15; wrapMode: Text.WordWrap; horizontalAlignment: Text.AlignHCenter
     }
     RowLayout {
      Layout.alignment: Qt.AlignHCenter
      Layout.topMargin: 10
      spacing: 12
      Button {
       objectName: "emptyFindCamera"
       text: devicesModel.pendingCount ? "Відкрити камери" : "Знайти камеру в мережі"
       font.pixelSize: 15; font.bold: true
       Layout.preferredWidth: 240; Layout.preferredHeight: 48
       onClicked: root.openDevices()
       contentItem: Text { text: parent.text; font: parent.font; color: "#06130d"; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
       background: Rectangle { radius: 8; color: parent.hovered ? "#5cf0bd" : root.green }
      }
      Button {
       objectName: "emptyOpenSimulation"
       text: "Спробувати симуляцію"
       font.pixelSize: 15
       Layout.preferredWidth: 240; Layout.preferredHeight: 48
       onClicked: root.openSimulation()
      }
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
  anchors.topMargin: 108
  anchors.rightMargin: 20
  width: Math.min(350, root.width - 40)
  height: Math.min(drawerContent.implicitHeight + 24, root.height - 128)
  radius: 12
  color: "#f20a1420"
  border.color: "#71879c"
  clip: true

  Flickable {
   id: drawerScroll
   anchors.fill: parent
   anchors.margins: 12
   contentHeight: drawerContent.implicitHeight
   clip: true
   boundsBehavior: Flickable.StopAtBounds
   ScrollBar.vertical: ScrollBar { policy: drawerScroll.contentHeight > drawerScroll.height ? ScrollBar.AlwaysOn : ScrollBar.AsNeeded }

   ColumnLayout {
    id: drawerContent
    width: drawerScroll.width
    spacing: 4
    Repeater {
     model: [{title: "МЕНЮ СТАНЦІЇ", section: "main"}]
     delegate: ColumnLayout {
      required property var modelData
      Layout.fillWidth: true
      spacing: 4
      Text { text: modelData.title; color: root.sub; font.pixelSize: 12; font.bold: true; font.letterSpacing: 1; Layout.bottomMargin: 2 }
      Repeater {
       model: root.menuItems.filter(function(item) { return item.section === modelData.section })
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
          Layout.preferredWidth: 32; Layout.preferredHeight: 32; radius: 8
          color: "#2b4259"
          Text { anchors.centerIn: parent; text: modelData.glyph; color: "#f2f7fc"; font.pixelSize: 17; font.bold: true }
         }
         ColumnLayout {
          Layout.fillWidth: true
          spacing: 0
          Text { text: modelData.label; color: root.fg; font.pixelSize: 15; font.bold: true }
          Text { text: modelData.detail; color: root.sub; font.pixelSize: 12; Layout.fillWidth: true; elide: Text.ElideRight }
         }
         Text { text: "›"; color: "#d8e5f1"; font.pixelSize: 22 }
        }
       }
      }
     }
    }
   }
  }
 }

 ArchiveDialog { id: archiveDialog }

 CameraSettingsDialog {
  id: cameraSettings
  onOpenFirmware: function(deviceId) { root.openFirmwareFor(deviceId) }
 }

 Component.onCompleted: updater.check()
}
