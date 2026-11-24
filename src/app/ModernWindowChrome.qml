import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

Rectangle {
    id: chrome
    required property Window window
    property color background: "#0A111B"
    property color foreground: "#F7F9FC"
    property color muted: "#8EA0B5"
    property color hover: "#172333"
    height: 44
    color: background
    z: 1000

    DragHandler {
        target: null
        onActiveChanged: if (active) window.startSystemMove()
    }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 16
        anchors.rightMargin: 8
        spacing: 10

        Rectangle {
            width: 26; height: 26; radius: 7
            color: "#14314A"
            Text { anchors.centerIn: parent; text: "FPV"; color: "#58A6FF"; font.pixelSize: 9; font.bold: true }
        }
        Text {
            text: "ФПВ УХИЛЯНТ"
            color: foreground
            font.family: "Segoe UI Variable"
            font.pixelSize: 14
            font.weight: Font.DemiBold
        }
        Text {
            text: "2.0.17"
            color: muted
            font.family: "Segoe UI Variable"
            font.pixelSize: 11
        }
        Item { Layout.fillWidth: true }

        ToolButton {
            text: "−"; flat: true; Layout.preferredWidth: 46; Layout.fillHeight: true
            font.pixelSize: 18
            onClicked: window.showMinimized()
            background: Rectangle { color: parent.hovered ? hover : "transparent"; radius: 7 }
        }
        ToolButton {
            text: window.visibility === Window.Maximized ? "❐" : "□"
            flat: true; Layout.preferredWidth: 46; Layout.fillHeight: true
            font.pixelSize: 15
            onClicked: window.visibility === Window.Maximized ? window.showNormal() : window.showMaximized()
            background: Rectangle { color: parent.hovered ? hover : "transparent"; radius: 7 }
        }
    }
}
