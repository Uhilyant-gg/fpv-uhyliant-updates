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
    property color amber: "#ffb84d"
    property color red: "#ff6678"

    ColumnLayout {
        anchors.fill: parent
        spacing: 12

        RowLayout {
            Layout.fillWidth: true
            Text { text: "ДОВІРА ПАРУВАННЯ"; color: fg; font.pixelSize: 22; font.bold: true }
            Item { Layout.fillWidth: true }
            Button {
                text: "Закрити"
                onClicked: {
                    root.closeRequested()
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            implicitHeight: statusColumn.implicitHeight + 24
            radius: 8
            color: "#101d2d"
            border.color: line

            ColumnLayout {
                id: statusColumn
                anchors.fill: parent
                anchors.margins: 12
                Text {
                    text: "Захищене сховище секретів: " + (pairingRegistry.secretStoreAvailable ? "доступне" : "недоступне")
                    color: pairingRegistry.secretStoreAvailable ? green : red
                    font.bold: true
                }
                Text {
                    text: "Сховище метаданих довіри: " + (pairingRegistry.metadataStoreAvailable ? "доступне" : "недоступне")
                    color: pairingRegistry.metadataStoreAvailable ? green : red
                    font.bold: true
                }
                Text { visible: pairingRegistry.secretStoreError !== ""; text: pairingRegistry.secretStoreError; color: red; wrapMode: Text.Wrap; Layout.fillWidth: true }
                Text { visible: pairingRegistry.metadataError !== ""; text: pairingRegistry.metadataError; color: red; wrapMode: Text.Wrap; Layout.fillWidth: true }
                Text { visible: pairingRegistry.recoveryError !== ""; text: "Потрібне відновлення: " + pairingRegistry.recoveryError; color: red; wrapMode: Text.Wrap; Layout.fillWidth: true }
                Button {
                    visible: pairingRegistry.recoveryError !== ""
                    text: "Повторити узгодження"
                    onClicked: {
                        pairingRegistry.reconcile()
                    }
                    HoverHint { text: "Повторно звірити метадані довіри із захищеним сховищем секретів." }
                }
                Text {
                    text: "Протокол доказу та обміну з вузлом ще не реалізований. Цей екран не створює нових сеансів парування."
                    color: amber
                    wrapMode: Text.Wrap
                    Layout.fillWidth: true
                }
            }
        }

        Text { text: "Довірені записи"; color: fg; font.pixelSize: 18; font.bold: true }
        Label { visible: pairingRegistry.trusted.length === 0; text: "Немає збережених довірених записів."; color: sub }

        ListView {
            id: trustedList
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            spacing: 8
            model: pairingRegistry.trusted
            delegate: Rectangle {
                required property var modelData
                width: trustedList.width
                height: itemColumn.implicitHeight + 20
                radius: 8
                color: "#101d2d"
                border.color: line

                ColumnLayout {
                    id: itemColumn
                    anchors.fill: parent
                    anchors.margins: 10
                    RowLayout {
                        Layout.fillWidth: true
                        ColumnLayout {
                            Layout.fillWidth: true
                            Text { text: modelData.label; color: fg; font.bold: true }
                            Text { text: modelData.endpoint; color: sub }
                            Text { text: "Відбиток: " + modelData.fingerprint; color: sub; font.family: "Consolas"; elide: Text.ElideMiddle; Layout.fillWidth: true }
                        }
                        Button {
                            text: "Відкликати довіру"
                            enabled: pairingRegistry.recoveryError === ""
                            onClicked: {
                                revokeDialog.open()
                            }
                            HoverHint { text: "Видалити захищений секрет і відповідні метадані довіри для цього запису." }
                        }
                    }

                    Dialog {
                        id: revokeDialog
                        title: "Відкликати довіру?"
                        modal: true
                        standardButtons: Dialog.Yes | Dialog.No
                        onAccepted: {
                            pairingRegistry.revoke(modelData.id)
                        }
                        contentItem: Text {
                            text: "Захищений секрет і метадані довіри для «" + modelData.label + "» буде видалено."
                            color: fg
                            wrapMode: Text.Wrap
                            width: 360
                        }
                    }
                }
            }
        }
    }
}
