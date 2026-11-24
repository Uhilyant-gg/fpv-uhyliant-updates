import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
 id: root
 signal closeRequested()
 signal activateDevice(string deviceId)
 property color fg: "#f5f8fc"
 property color muted: "#8799ad"
 property color surface: "#0d1723"
 property color raised: "#132235"
 property color accent: "#35e0a1"
 property color blue: "#4195ff"
 property color line: "#203348"
 property color danger: "#ff7080"
 property var selectedFound: null
 property var selectedSaved: null
 property string authHost: ""
 property string authName: ""
 function value(v) { return v === undefined || v === null || v === "" ? "Не визначено" : v }
 function selectFound(item) { selectedFound = item }

 Rectangle { anchors.fill: parent; color: "#08111b" }
 ColumnLayout {
  anchors.fill: parent
  anchors.margins: 20
  spacing: 14
  RowLayout {
   Layout.fillWidth: true
   ColumnLayout { spacing: 3; Text { text: "Камери"; color: fg; font.pixelSize: 26; font.bold: true } Text { text: "Знайдіть і підключіть камеру без ручних мережевих налаштувань"; color: muted; font.pixelSize: 13 } }
   Item { Layout.fillWidth: true }
   Button { text: "Закрити"; flat: true; onClicked: root.closeRequested(); HoverHint { text: "Повернутися до попереднього екрана." } }
  }
  Rectangle {
   Layout.fillWidth: true; height: 74; radius: 16; color: raised
   RowLayout {
    anchors.fill: parent; anchors.margins: 12; spacing: 10
    Button { text: devicesModel.scanning ? "Скасувати" : "Знайти камери"; font.bold: true; Layout.preferredHeight: 44; onClicked: devicesModel.scanning ? devicesModel.cancelDiscovery() : devicesModel.discoverOpenIPC(); HoverHint { text: devicesModel.scanning ? "Зупинити поточний пошук." : "Автоматично перевірити доступні безпечні приватні мережі." } }
    Button { text: "Вказати IP"; flat: true; onClicked: manualPopup.open(); HoverHint { text: "Перевірити камеру безпосередньо за приватною IPv4-адресою." } }
    Item { Layout.fillWidth: true }
    ColumnLayout { visible: devicesModel.scanning || devicesModel.scanStatus !== "Готово"; spacing: 3; Text { text: devicesModel.scanStage; color: fg; horizontalAlignment: Text.AlignRight; Layout.fillWidth: true; font.pixelSize: 12 } ProgressBar { from: 0; to: Math.max(1, devicesModel.scanTotal); value: devicesModel.scanDone; Layout.preferredWidth: 230 } Text { text: devicesModel.foundCount + " знайдено"; color: muted; font.pixelSize: 11; horizontalAlignment: Text.AlignRight; Layout.fillWidth: true } }
   }
  }
  SplitView {
   Layout.fillWidth: true; Layout.fillHeight: true; orientation: Qt.Horizontal
   Rectangle {
    SplitView.preferredWidth: 310; SplitView.minimumWidth: 250; color: surface; radius: 16
    ColumnLayout {
     anchors.fill: parent; anchors.margins: 12; spacing: 10
     RowLayout { Layout.fillWidth: true; Text { text: "МОЇ КАМЕРИ"; color: muted; font.bold: true; font.pixelSize: 11 } Item { Layout.fillWidth: true } Text { text: devicesModel.count; color: muted } }
     ListView {
      id: savedList; Layout.fillWidth: true; Layout.fillHeight: true; spacing: 7; clip: true; model: devicesModel.items
      delegate: Rectangle {
       required property var modelData
       width: savedList.width; height: 72; radius: 12
       color: selectedSaved && selectedSaved.id === modelData.id ? raised : "transparent"
       border.color: modelData.active ? accent : "transparent"
       MouseArea { anchors.fill: parent; onClicked: selectedSaved = modelData }
       Column { anchors.fill: parent; anchors.margins: 10; spacing: 4; Text { text: modelData.name; color: fg; font.bold: true } Text { text: modelData.host; color: muted; font.pixelSize: 12 } Text { text: modelData.openipcIdentity.verified ? "● OpenIPC підтверджено" : "○ Ідентичність не підтверджена"; color: modelData.openipcIdentity.verified ? accent : muted; font.pixelSize: 11 } }
      }
     }
     RowLayout { Layout.fillWidth: true; Button { text: "Зробити активною"; Layout.fillWidth: true; enabled: selectedSaved !== null; onClicked: root.activateDevice(selectedSaved.id); HoverHint { text: "Вибрати цю камеру як активну для FPV та сервісних функцій." } } Button { text: "⋯"; enabled: selectedSaved !== null; onClicked: savedDetails.open(); HoverHint { text: "Показати збережені відомості про камеру." } } }
    }
   }
   Item { SplitView.preferredWidth: 12 }
   Rectangle {
    SplitView.fillWidth: true; color: surface; radius: 16
    ColumnLayout {
     anchors.fill: parent; anchors.margins: 14; spacing: 10
     RowLayout { Layout.fillWidth: true; Text { text: "ЗНАЙДЕНІ"; color: muted; font.bold: true; font.pixelSize: 11 } Item { Layout.fillWidth: true } Text { text: devicesModel.discovered.length === 0 ? "" : "Оберіть камеру для продовження"; color: muted; font.pixelSize: 11 } }
     ListView {
      id: foundList; Layout.fillWidth: true; Layout.fillHeight: true; spacing: 8; clip: true; model: devicesModel.discovered
      delegate: Rectangle {
       required property var modelData
       width: foundList.width; height: 78; radius: 13
       color: selectedFound && selectedFound.host === modelData.host ? raised : "#0a141f"
       MouseArea { anchors.fill: parent; onClicked: root.selectFound(modelData) }
       RowLayout { anchors.fill: parent; anchors.margins: 12; Text { text: modelData.name + "  ·  " + modelData.host; color: fg; Layout.fillWidth: true } Text { text: modelData.openipc ? "OpenIPC підтверджено" : (modelData.authRequired ? "Потрібен логін" : "Кандидат"); color: modelData.openipc ? accent : muted } }
      }
     }
     ColumnLayout { visible: devicesModel.discovered.length === 0 && !devicesModel.scanning; Layout.alignment: Qt.AlignHCenter | Qt.AlignVCenter; Text { text: "Нічого не знайдено"; color: fg; font.pixelSize: 18; font.bold: true } Text { text: "Запустіть пошук або вкажіть IP камери"; color: muted } }
     RowLayout {
      Layout.fillWidth: true
      Button {
       text: "Додати камеру"; font.bold: true; enabled: selectedFound !== null
       onClicked: { if (selectedFound.openipc && selectedFound.identityVerified) { var id = devicesModel.addDiscovered(selectedFound.host, selectedFound.name, true); if (id !== "") { selectedSaved = null; selectedFound = null } } else { root.authHost = selectedFound.host; root.authName = selectedFound.name; authPopup.open() } }
       HoverHint { text: "Додати підтверджену камеру або запросити доступ для перевірки." }
      }
      Button { text: "Відомості"; flat: true; enabled: selectedFound !== null; onClicked: detailsPopup.open(); HoverHint { text: "Показати спостережену ідентичність та технічні відомості." } }
      Item { Layout.fillWidth: true }
     }
    }
   }
  }
 }

 Popup {
  id: manualPopup
  anchors.centerIn: parent; width: Math.min(500, root.width - 40); modal: true; padding: 20
  property string verifiedHost: ""
  property string addedHost: ""
  function invalidateEvidence(hostText) { verifiedHost = ""; addedHost = ""; devicesModel.invalidateManualIp(hostText) }
  background: Rectangle { color: raised; radius: 18; border.color: line }
  ColumnLayout {
   width: parent.width; spacing: 13
   Text { text: "Вказати IP"; color: fg; font.pixelSize: 22; font.bold: true }
   Text { text: "Введіть адресу камери. Решту програма перевірить автоматично."; color: muted; wrapMode: Text.WordWrap; Layout.fillWidth: true }
   TextField { id: manualIp; Layout.fillWidth: true; placeholderText: "192.168.1.50"; inputMethodHints: Qt.ImhFormattedNumbersOnly; onTextEdited: manualPopup.invalidateEvidence(text); HoverHint { text: "Приватна IPv4-адреса камери для прямої перевірки." } }
   Connections { target: devicesModel; function onManualChanged() { if (devicesModel.manualStatus === "verified") manualPopup.verifiedHost = devicesModel.manualResult.host || ""; if (devicesModel.manualStatus === "added") manualPopup.addedHost = devicesModel.manualResult.host || "" } }
   Text { visible: devicesModel.manualBusy; text: "Перевіряємо камеру…"; color: blue }
   Text { visible: !devicesModel.manualBusy && devicesModel.manualMessage !== ""; text: devicesModel.manualMessage; color: devicesModel.manualStatus === "added" || devicesModel.manualStatus === "verified" ? accent : muted; wrapMode: Text.WordWrap; Layout.fillWidth: true; font.bold: true }
   Text { visible: devicesModel.manualError !== ""; text: devicesModel.manualError; color: danger; wrapMode: Text.WordWrap; Layout.fillWidth: true }
   Rectangle { visible: devicesModel.manualStatus === "verified" && manualPopup.verifiedHost !== "" && manualIp.text.trim() === manualPopup.verifiedHost && devicesModel.manualResult.openipc === true && devicesModel.manualResult.identityVerified === true; Layout.fillWidth: true; height: 104; radius: 12; color: "#15392f"; Column { anchors.fill: parent; anchors.margins: 10; spacing: 4; Text { text: "OpenIPC підтверджено"; color: accent; font.bold: true } Text { text: "Платформа / SoC: " + value(devicesModel.manualResult.identity.platform) + " / " + value(devicesModel.manualResult.identity.soc); color: fg } Text { text: "Сенсор: " + value(devicesModel.manualResult.identity.sensor); color: fg } Text { text: "Прошивка: " + value(devicesModel.manualResult.identity.firmware); color: fg } } }
   Rectangle { visible: devicesModel.manualStatus === "added" && manualPopup.addedHost !== ""; Layout.fillWidth: true; height: 48; radius: 12; color: "#15392f"; Text { anchors.centerIn: parent; text: "Камеру " + manualPopup.addedHost + " додано до Моїх камер"; color: accent; font.bold: true } }
   RowLayout {
    Layout.fillWidth: true
    Button { text: devicesModel.manualBusy ? "Перевірка…" : "Перевірити"; enabled: !devicesModel.manualBusy; onClicked: devicesModel.inspectManualIp(manualIp.text); HoverHint { text: "Перевірити доступність, OpenIPC та спостережену ідентичність камери." } }
    Button {
     text: devicesModel.manualStatus === "added" ? "Додано" : "Додати"
     enabled: !devicesModel.manualBusy && devicesModel.manualStatus === "verified" && manualPopup.verifiedHost !== "" && manualIp.text.trim() === manualPopup.verifiedHost && devicesModel.manualResult.camera === true && devicesModel.manualResult.openipc === true && devicesModel.manualResult.identityVerified === true
     onClicked: { var id = devicesModel.addDiscovered(manualPopup.verifiedHost, "OpenIPC " + manualPopup.verifiedHost, true); if (id !== "") { selectedSaved = null; manualPopup.addedHost = manualPopup.verifiedHost } }
     HoverHint { text: "Зберегти лише поточну підтверджену OpenIPC-камеру." }
    }
    Item { Layout.fillWidth: true }
    Button { text: "Закрити"; flat: true; onClicked: manualPopup.close() }
   }
  }
 }

 Popup {
  id: authPopup
  anchors.centerIn: parent; width: Math.min(440, root.width - 40); modal: true; padding: 20
  background: Rectangle { color: raised; radius: 18; border.color: line }
  ColumnLayout {
   width: parent.width; spacing: 12
   Text { text: "Доступ до камери"; color: fg; font.pixelSize: 22; font.bold: true }
   Text { text: root.authHost; color: muted }
   TextField { id: authUser; Layout.fillWidth: true; text: "root"; placeholderText: "Логін" }
   TextField { id: authPassword; Layout.fillWidth: true; placeholderText: "Пароль"; echoMode: TextInput.Password }
   Text { visible: devicesModel.manualError !== ""; text: devicesModel.manualError; color: danger; wrapMode: Text.WordWrap; Layout.fillWidth: true }
   RowLayout {
    Layout.fillWidth: true
    Button {
     text: "Перевірити й додати"; font.bold: true
     onClicked: { var added = devicesModel.authenticateAndAdd(root.authHost, root.authName, authUser.text, authPassword.text); authPassword.text = ""; if (added !== "") authPopup.close() }
     HoverHint { text: "Дані доступу використовуються лише для перевірки цієї сесії." }
    }
    Item { Layout.fillWidth: true }
    Button { text: "Скасувати"; flat: true; onClicked: { authPassword.text = ""; authPopup.close() } }
   }
  }
 }

 Popup {
  id: detailsPopup
  anchors.centerIn: parent; width: Math.min(540, root.width - 40); modal: true; padding: 20
  background: Rectangle { color: raised; radius: 18; border.color: line }
  ColumnLayout {
   width: parent.width; spacing: 9
   Text { text: "Відомості про камеру"; color: fg; font.pixelSize: 21; font.bold: true }
   Text { text: "Адреса  " + (selectedFound ? selectedFound.host : ""); color: fg }
   Text { text: "OpenIPC  " + (selectedFound && selectedFound.openipc ? "підтверджено" : "не підтверджено"); color: selectedFound && selectedFound.openipc ? accent : muted }
   Text { text: "Платформа / SoC  " + value(selectedFound ? selectedFound.identity.platform : "") + " / " + value(selectedFound ? selectedFound.identity.soc : ""); color: fg }
   Text { text: "Сенсор  " + value(selectedFound ? selectedFound.identity.sensor : ""); color: fg }
   Text { text: "Прошивка  " + value(selectedFound ? selectedFound.identity.firmware : ""); color: fg }
   Button { text: "Закрити"; Layout.alignment: Qt.AlignRight; onClicked: detailsPopup.close() }
  }
 }

 Popup {
  id: savedDetails
  anchors.centerIn: parent; width: Math.min(500, root.width - 40); modal: true; padding: 20
  background: Rectangle { color: raised; radius: 18; border.color: line }
  ColumnLayout {
   width: parent.width; spacing: 9
   Text { text: selectedSaved ? selectedSaved.name : "Камера"; color: fg; font.pixelSize: 21; font.bold: true }
   Text { text: selectedSaved ? selectedSaved.host : ""; color: muted }
   Text { text: selectedSaved && selectedSaved.openipcIdentity.verified ? "OpenIPC підтверджено" : "OpenIPC не підтверджено"; color: selectedSaved && selectedSaved.openipcIdentity.verified ? accent : muted }
   Text { visible: selectedSaved && selectedSaved.openipcIdentity.verified; text: "Платформа / SoC  " + value(selectedSaved ? selectedSaved.openipcIdentity.platform : "") + " / " + value(selectedSaved ? selectedSaved.openipcIdentity.soc : ""); color: fg }
   Text { visible: selectedSaved && selectedSaved.openipcIdentity.verified; text: "Сенсор  " + value(selectedSaved ? selectedSaved.openipcIdentity.sensor : ""); color: fg }
   Button { text: "Закрити"; Layout.alignment: Qt.AlignRight; onClicked: savedDetails.close() }
  }
 }
}
