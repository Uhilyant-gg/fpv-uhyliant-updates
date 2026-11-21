import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    signal closeRequested()

    property color fg: "#f4f7fb"
    property color sub: "#8fa1b7"
    property color line: "#273d55"
    property color green: "#27d59a"
    property string selectedId: ""
    property var selectedFound: null
    property var selectedSaved: null

    function show(value) {
        return value === undefined || value === null || value === "" ? "--" : value
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 10

        RowLayout {
            Layout.fillWidth: true

            ColumnLayout {
                Text {
                    text: "ПРИСТРОЇ"
                    color: fg
                    font.pixelSize: 22
                    font.bold: true
                }
                Text {
                    text: "mDNS → ONVIF → відбиток → /24"
                    color: sub
                }
            }

            Item { Layout.fillWidth: true }

            Button {
                text: "Оновити інтерфейси"
                enabled: !devicesModel.scanning
                onClicked: {
                    devicesModel.refreshInterfaces()
                }
                HoverHint { text: "Оновити перелік доступних мережевих інтерфейсів." }
            }

            Button {
                text: "Знайти камери"
                visible: !devicesModel.scanning
                enabled: ifaceBox.count > 0
                onClicked: {
                    devicesModel.discoverOpenIPC()
                }
                HoverHint { text: "Запустити наявний пошук камер через вибраний мережевий інтерфейс." }
            }

            Button {
                text: "Скасувати"
                visible: devicesModel.scanning
                onClicked: {
                    devicesModel.cancelDiscovery()
                }
            }

            Button {
                text: "Закрити"
                onClicked: {
                    root.closeRequested()
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Text {
                text: "Мережевий інтерфейс:"
                color: sub
            }
            ComboBox {
                id: ifaceBox
                Layout.fillWidth: true
                enabled: !devicesModel.scanning
                model: devicesModel.networkInterfaces
                textRole: "label"
                valueRole: "id"
                onActivated: {
                    devicesModel.setSelectedInterface(currentValue)
                }
                Component.onCompleted: {
                    for (var i = 0; i < count; i++) {
                        if (valueAt(i) === devicesModel.selectedInterfaceId) {
                            currentIndex = i
                            break
                        }
                    }
                }
                HoverHint { text: "Інтерфейс, через який виконуватиметься пошук камер." }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            height: 72
            radius: 8
            color: "#111d2c"
            border.color: line

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 10
                RowLayout {
                    Layout.fillWidth: true
                    Text { text: "Етап: " + devicesModel.scanStage; color: fg; font.bold: true }
                    Item { Layout.fillWidth: true }
                    Text { text: "Знайдено: " + devicesModel.foundCount; color: green }
                    Text { text: devicesModel.scanStatus; color: sub }
                }
                ProgressBar {
                    Layout.fillWidth: true
                    from: 0
                    to: Math.max(1, devicesModel.scanTotal)
                    value: devicesModel.scanDone
                    indeterminate: devicesModel.scanning && devicesModel.scanTotal === 0
                }
                Text {
                    visible: devicesModel.scanStage === "/24"
                    text: devicesModel.scanDone + " / " + devicesModel.scanTotal
                    color: sub
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 10

            ColumnLayout {
                Layout.preferredWidth: 350
                Layout.fillHeight: true
                Text { text: "ЗБЕРЕЖЕНІ"; color: sub; font.bold: true }

                ListView {
                    id: saved
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    model: devicesModel.items
                    spacing: 6
                    clip: true
                    delegate: Rectangle {
                        required property var modelData
                        width: saved.width
                        height: 82
                        radius: 8
                        color: selectedId === modelData.id ? "#173650" : "#111d2c"
                        border.color: modelData.active ? green : line

                        MouseArea {
                            anchors.fill: parent
                            onClicked: {
                                selectedId = modelData.id
                                selectedSaved = modelData
                                editName.text = modelData.name
                                editHost.text = modelData.host
                                editPort.value = modelData.port
                                editNotes.text = modelData.notes
                            }
                        }

                        Column {
                            anchors.fill: parent
                            anchors.margins: 9
                            Text {
                                text: (modelData.active ? "● " : "") + modelData.name
                                color: modelData.active ? green : fg
                                font.bold: true
                            }
                            Text { text: modelData.host; color: sub }
                            Text {
                                text: modelData.openipcIdentity && modelData.openipcIdentity.verified
                                      ? "OpenIPC ✓ · " + show(modelData.openipcIdentity.platform) + " · " + show(modelData.openipcIdentity.sensor)
                                      : "OpenIPC: не підтверджено"
                                color: modelData.openipcIdentity && modelData.openipcIdentity.verified ? green : sub
                                font.pixelSize: 10
                            }
                        }
                    }
                }

                RowLayout {
                    Button {
                        text: "Зробити активним"
                        enabled: selectedId !== ""
                        onClicked: {
                            devicesModel.setActive(selectedId)
                        }
                        HoverHint { text: "Вибрати цей збережений пристрій як активний." }
                    }
                    Button {
                        text: "Видалити"
                        enabled: selectedId !== ""
                        onClicked: {
                            devicesModel.removeDevice(selectedId)
                            selectedId = ""
                            selectedSaved = null
                        }
                        HoverHint { text: "Видалити вибраний запис зі списку збережених пристроїв." }
                    }
                }

                Rectangle {
                    visible: selectedSaved && selectedSaved.openipcIdentity && selectedSaved.openipcIdentity.verified
                    Layout.fillWidth: true
                    Layout.preferredHeight: 240
                    radius: 8
                    color: "#111d2c"
                    border.color: green

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 9
                        Text { text: "ІДЕНТИЧНІСТЬ OPENIPC · ПІДТВЕРДЖЕНО"; color: green; font.bold: true }
                        Text { text: "Платформа / SoC: " + show(selectedSaved ? selectedSaved.openipcIdentity.platform : "") + " / " + show(selectedSaved ? selectedSaved.openipcIdentity.soc : ""); color: fg }
                        Text { text: "Сенсор: " + show(selectedSaved ? selectedSaved.openipcIdentity.sensor : ""); color: fg }
                        Text { text: "Прошивка: " + show(selectedSaved ? selectedSaved.openipcIdentity.firmware : ""); color: fg }
                        Text { text: "Majestic: " + show(selectedSaved ? selectedSaved.openipcIdentity.majestic : ""); color: fg }
                        Text {
                            text: "Підтвердження: " + (selectedSaved ? selectedSaved.openipcIdentity.evidence.join("; ") : "")
                            color: sub
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                        ComboBox {
                            id: presetBox
                            Layout.fillWidth: true
                            model: cameraPresets.items
                            textRole: "name"
                            HoverHint { text: "Пресет камери є окремою сутністю і не змінює відеопрофіль." }
                        }
                        RowLayout {
                            Button {
                                text: "Перевірити пресет"
                                enabled: presetBox.currentIndex >= 0
                                onClicked: {
                                    var preset = cameraPresets.items[presetBox.currentIndex]
                                    cameraPresets.selectForDevice(preset.key, selectedId)
                                }
                                HoverHint { text: "Перевірити сумісність пресета з підтвердженою ідентичністю камери." }
                            }
                            Button {
                                text: "План застосування"
                                enabled: cameraPresets.result.ready
                                onClicked: {
                                    cameraPresets.buildApplyPlan()
                                }
                                HoverHint { text: "Побудувати безпечний план застосування перевіреного пресета." }
                            }
                        }
                        Text {
                            text: cameraPresets.result.reason
                            color: cameraPresets.result.ready ? green : sub
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                    }
                }
            }

            Rectangle { width: 1; Layout.fillHeight: true; color: line }

            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Text { text: "ЗНАЙДЕНІ"; color: sub; font.bold: true }

                ListView {
                    id: found
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    model: devicesModel.discovered
                    spacing: 6
                    clip: true
                    delegate: Rectangle {
                        required property var modelData
                        width: found.width
                        height: 82
                        radius: 8
                        color: selectedFound && selectedFound.host === modelData.host ? "#173650" : "#111d2c"
                        border.color: modelData.openipc ? green : line

                        MouseArea {
                            anchors.fill: parent
                            onClicked: {
                                selectedFound = modelData
                            }
                        }
                        Column {
                            anchors.fill: parent
                            anchors.margins: 9
                            Text { text: modelData.name; color: fg; font.bold: true }
                            Text {
                                text: modelData.host + " · " + (modelData.openipc ? "OpenIPC підтверджено" : "не підтверджено")
                                color: modelData.openipc ? green : sub
                            }
                            Text { text: modelData.services.join(", "); color: sub; font.pixelSize: 10 }
                        }
                    }
                }

                Button {
                    text: "Додати підтверджену OpenIPC"
                    enabled: selectedFound && selectedFound.openipc
                    onClicked: {
                        var id = devicesModel.addDiscovered(selectedFound.host, selectedFound.name, selectedFound.openipc)
                        if (id) {
                            selectedId = id
                            for (var n = 0; n < devicesModel.items.length; n++) {
                                if (devicesModel.items[n].id === id) {
                                    selectedSaved = devicesModel.items[n]
                                    break
                                }
                            }
                        }
                    }
                    HoverHint { text: "Зберегти знайдену камеру лише коли OpenIPC-ідентичність підтверджена." }
                }

                Rectangle {
                    visible: selectedFound
                    Layout.fillWidth: true
                    Layout.preferredHeight: selectedFound && selectedFound.openipc ? 225 : 145
                    radius: 8
                    color: "#111d2c"
                    border.color: line
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        Text { text: "ДЕТАЛІ КАМЕРИ"; color: fg; font.bold: true }
                        Text { text: "IP: " + (selectedFound ? selectedFound.host : ""); color: sub }
                        Text { text: "Ім'я хоста: " + (selectedFound ? selectedFound.hostname : ""); color: sub }
                        Text {
                            text: "OpenIPC: " + (selectedFound ? (selectedFound.openipc ? "Підтверджено" : "Не підтверджено") : "")
                            color: selectedFound && selectedFound.openipc ? green : sub
                        }
                        Text { visible: selectedFound && selectedFound.openipc; text: "Платформа / SoC: " + show(selectedFound ? selectedFound.identity.platform : "") + " / " + show(selectedFound ? selectedFound.identity.soc : ""); color: fg }
                        Text { visible: selectedFound && selectedFound.openipc; text: "Сенсор: " + show(selectedFound ? selectedFound.identity.sensor : ""); color: fg }
                        Text { visible: selectedFound && selectedFound.openipc; text: "Прошивка / Majestic: " + show(selectedFound ? selectedFound.identity.firmware : "") + " / " + show(selectedFound ? selectedFound.identity.majestic : ""); color: fg }
                        Text { text: "Джерела: " + (selectedFound ? selectedFound.services.join(", ") : ""); color: sub; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                        Text { text: "Причина: " + (selectedFound ? selectedFound.evidence.join("; ") : ""); color: sub; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                    }
                }
            }

            Rectangle { width: 1; Layout.fillHeight: true; color: line }

            ColumnLayout {
                Layout.preferredWidth: 250
                Layout.fillHeight: true
                Text { text: "РЕДАГУВАННЯ"; color: sub; font.bold: true }
                TextField { id: editName; Layout.fillWidth: true; placeholderText: "Назва" }
                TextField { id: editHost; Layout.fillWidth: true; placeholderText: "IP / ім'я хоста" }
                SpinBox { id: editPort; Layout.fillWidth: true; from: 0; to: 65535; editable: true }
                TextArea { id: editNotes; Layout.fillWidth: true; Layout.preferredHeight: 90; placeholderText: "Примітка"; wrapMode: TextEdit.Wrap }
                Button {
                    text: "Зберегти зміни"
                    enabled: selectedId !== ""
                    Layout.fillWidth: true
                    onClicked: {
                        devicesModel.updateDevice(selectedId, editName.text, editHost.text, editPort.value, editNotes.text)
                    }
                    HoverHint { text: "Зберегти відредаговані локальні метадані пристрою." }
                }
                Item { Layout.fillHeight: true }
                Text {
                    text: "Пресет камери не є відеопрофілем. План пресета не змінює кодек, FPS або профіль потоку; застосування на обладнанні очікує фізичної перевірки."
                    color: sub
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
            }
        }
    }
}
