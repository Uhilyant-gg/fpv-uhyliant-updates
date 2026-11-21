import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    signal closeRequested()
    property color fg: "#f5f8fc"
    property color muted: "#91a3b8"
    property color surface: "#101925"
    property color surfaceHi: "#172536"
    property color accent: "#35e0a1"
    property color line: "#24384d"
    property var selectedFound: null
    property var selectedSaved: null
    function value(v) { return v === undefined || v === null || v === "" ? "Не визначено" : v }

    Rectangle { anchors.fill: parent; color: "#09111b" }
    ColumnLayout {
        anchors.fill: parent; anchors.margins: 18; spacing: 14
        RowLayout {
            Layout.fillWidth: true
            ColumnLayout {
                spacing: 2
                Text { text: "Підключити камеру"; color: fg; font.pixelSize: 28; font.bold: true }
                Text { text: "Автоматичний безпечний пошук у доступних мережах"; color: muted; font.pixelSize: 13 }
            }
            Item { Layout.fillWidth: true }
            Button { text: "Закрити"; flat: true; onClicked: root.closeRequested() }
        }
        Rectangle {
            Layout.fillWidth: true; Layout.preferredHeight: 88; radius: 16; color: surfaceHi
            RowLayout {
                anchors.fill: parent; anchors.margins: 14; spacing: 12
                Button {
                    text: devicesModel.scanning ? "Скасувати пошук" : "Знайти камери"
                    font.bold: true
                    onClicked: devicesModel.scanning ? devicesModel.cancelDiscovery() : devicesModel.discoverOpenIPC()
                }
                Button { text: "Вказати IP"; flat: true; onClicked: manualPopup.open() }
                Item { Layout.fillWidth: true }
                ColumnLayout {
                    visible: devicesModel.scanning || devicesModel.scanStatus !== "Готово"; spacing: 3
                    Text { text: devicesModel.scanStage; color: fg; horizontalAlignment: Text.AlignRight; Layout.fillWidth: true }
                    Text { text: devicesModel.foundCount + " знайдено · " + devicesModel.scanStatus; color: muted; font.pixelSize: 12 }
                    ProgressBar { from: 0; to: Math.max(1, devicesModel.scanTotal); value: devicesModel.scanDone; Layout.preferredWidth: 240 }
                }
            }
        }
        SplitView {
            Layout.fillWidth: true; Layout.fillHeight: true; orientation: Qt.Horizontal
            Rectangle {
                SplitView.preferredWidth: 340; SplitView.minimumWidth: 260; color: surface; radius: 14
                ColumnLayout {
                    anchors.fill: parent; anchors.margins: 12
                    Text { text: "МОЇ КАМЕРИ"; color: muted; font.bold: true; font.pixelSize: 12 }
                    ListView {
                        id: savedList; Layout.fillWidth: true; Layout.fillHeight: true; spacing: 8; clip: true; model: devicesModel.items
                        delegate: Rectangle {
                            required property var modelData; width: savedList.width; height: 76; radius: 12
                            color: selectedSaved && selectedSaved.id === modelData.id ? surfaceHi : "transparent"
                            border.color: modelData.active ? accent : "transparent"
                            MouseArea { anchors.fill: parent; onClicked: selectedSaved = modelData }
                            Column { anchors.fill: parent; anchors.margins: 11; spacing: 4
                                Text { text: modelData.name; color: fg; font.bold: true }
                                Text { text: modelData.host + (modelData.active ? " · активна" : ""); color: modelData.active ? accent : muted }
                                Text { text: modelData.openipcIdentity.verified ? "OpenIPC підтверджено" : "Ідентичність не підтверджена"; color: modelData.openipcIdentity.verified ? accent : muted; font.pixelSize: 11 }
                            }
                        }
                    }
                    Button { text: "Підключити"; Layout.fillWidth: true; enabled: selectedSaved !== null; onClicked: devicesModel.setActive(selectedSaved.id) }
                }
            }
            Rectangle {
                SplitView.fillWidth: true; color: surface; radius: 14
                ColumnLayout {
                    anchors.fill: parent; anchors.margins: 14; spacing: 10
                    RowLayout { Layout.fillWidth: true
                        Text { text: "ЗНАЙДЕНІ КАМЕРИ"; color: muted; font.bold: true; font.pixelSize: 12 }
                        Item { Layout.fillWidth: true }
                        Text { text: "Технічні деталі відкриваються після вибору"; color: muted; font.pixelSize: 11 }
                    }
                    ListView {
                        id: foundList; Layout.fillWidth: true; Layout.fillHeight: true; spacing: 8; clip: true; model: devicesModel.discovered
                        delegate: Rectangle {
                            required property var modelData; width: foundList.width; height: 88; radius: 12
                            color: selectedFound && selectedFound.host === modelData.host ? surfaceHi : "#0d1722"
                            MouseArea { anchors.fill: parent; onClicked: selectedFound = modelData }
                            RowLayout { anchors.fill: parent; anchors.margins: 12
                                ColumnLayout { Layout.fillWidth: true; spacing: 4
                                    Text { text: modelData.name; color: fg; font.bold: true; font.pixelSize: 16 }
                                    Text { text: modelData.host; color: muted }
                                }
                                Rectangle { width: 150; height: 30; radius: 15; color: modelData.openipc ? "#173e35" : "#2b3038"
                                    Text { anchors.centerIn: parent; text: modelData.openipc ? "OpenIPC підтверджено" : "Кандидат камери"; color: modelData.openipc ? accent : muted; font.pixelSize: 11 }
                                }
                            }
                        }
                    }
                    RowLayout { Layout.fillWidth: true
                        Button { text: "Додати камеру"; enabled: selectedFound && selectedFound.openipc; onClicked: devicesModel.addDiscovered(selectedFound.host, selectedFound.name, true) }
                        Button { text: "Деталі"; flat: true; enabled: selectedFound !== null; onClicked: detailsPopup.open() }
                        Item { Layout.fillWidth: true }
                    }
                }
            }
        }
    }
    Popup {
        id: manualPopup; anchors.centerIn: parent; width: 420; modal: true; padding: 18
        background: Rectangle { color: surfaceHi; radius: 16; border.color: line }
        ColumnLayout { width: parent.width; spacing: 12
            Text { text: "Вказати IP камери"; color: fg; font.pixelSize: 20; font.bold: true }
            TextField { id: manualIp; Layout.fillWidth: true; placeholderText: "192.168.1.50"; inputMethodHints: Qt.ImhFormattedNumbersOnly }
            Text { visible: devicesModel.manualError !== ""; text: devicesModel.manualError; color: "#ff8d8d"; wrapMode: Text.WordWrap; Layout.fillWidth: true }
            Text { visible: devicesModel.manualResult.openipc === true; text: "OpenIPC підтверджено · " + value(devicesModel.manualResult.identity.platform) + " · " + value(devicesModel.manualResult.identity.sensor); color: accent; wrapMode: Text.WordWrap; Layout.fillWidth: true }
            RowLayout { Layout.fillWidth: true
                Button { text: devicesModel.manualBusy ? "Перевірка…" : "Перевірити"; enabled: !devicesModel.manualBusy; onClicked: devicesModel.inspectManualIp(manualIp.text) }
                Button { text: "Додати"; enabled: devicesModel.manualResult.openipc === true; onClicked: { devicesModel.addDiscovered(devicesModel.manualResult.host, "OpenIPC " + devicesModel.manualResult.host, true); manualPopup.close() } }
                Item { Layout.fillWidth: true }
                Button { text: "Закрити"; flat: true; onClicked: manualPopup.close() }
            }
        }
    }
    Popup {
        id: detailsPopup; anchors.centerIn: parent; width: 520; modal: true; padding: 18
        background: Rectangle { color: surfaceHi; radius: 16; border.color: line }
        ColumnLayout { width: parent.width; spacing: 8
            Text { text: "Відомості про камеру"; color: fg; font.pixelSize: 20; font.bold: true }
            Text { text: "Адреса: " + (selectedFound ? selectedFound.host : ""); color: fg }
            Text { text: "OpenIPC: " + (selectedFound && selectedFound.openipc ? "підтверджено" : "не підтверджено"); color: selectedFound && selectedFound.openipc ? accent : muted }
            Text { text: "Платформа / SoC: " + value(selectedFound ? selectedFound.identity.platform : "") + " / " + value(selectedFound ? selectedFound.identity.soc : ""); color: fg }
            Text { text: "Сенсор: " + value(selectedFound ? selectedFound.identity.sensor : ""); color: fg }
            Text { text: "Прошивка: " + value(selectedFound ? selectedFound.identity.firmware : ""); color: fg }
            Text { text: "Majestic: " + value(selectedFound ? selectedFound.identity.majestic : ""); color: fg }
            Text { text: "Підтвердження: " + (selectedFound ? selectedFound.evidence.join("; ") : ""); color: muted; wrapMode: Text.WordWrap; Layout.fillWidth: true }
            Button { text: "Закрити"; Layout.alignment: Qt.AlignRight; onClicked: detailsPopup.close() }
        }
    }
}
