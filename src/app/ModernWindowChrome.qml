import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

Rectangle {
    id: chrome
    required property Window window
    height: UiTokens.chromeHeight
    color: UiTokens.chrome
    z: 1000

    DragHandler {
        target: null
        onActiveChanged: if (active) window.startSystemMove()
    }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: UiTokens.space16
        anchors.rightMargin: UiTokens.space8
        spacing: UiTokens.space12

        Rectangle {
            width: 26; height: 26; radius: UiTokens.radiusSmall
            color: UiTokens.interactive
            Text { anchors.centerIn: parent; text: "FPV"; color: UiTokens.primary; font.family: UiTokens.fontFamily; font.pixelSize: 9; font.bold: true }
        }
        Text { text: "ФПВ УХИЛЯНТ"; color: UiTokens.foreground; font.family: UiTokens.fontFamily; font.pixelSize: UiTokens.fontControl; font.weight: Font.DemiBold }
        Text { text: "2.0.17"; color: UiTokens.secondary; font.family: UiTokens.fontFamily; font.pixelSize: UiTokens.fontCaption }
        Item { Layout.fillWidth: true }
        ToolButton { text: "−"; flat: true; Layout.preferredWidth: 46; Layout.fillHeight: true; font.pixelSize: 18; onClicked: window.showMinimized(); background: Rectangle { color: parent.hovered ? UiTokens.interactive : "transparent"; radius: UiTokens.radiusSmall } }
        ToolButton { text: window.visibility === Window.Maximized ? "❐" : "□"; flat: true; Layout.preferredWidth: 46; Layout.fillHeight: true; font.pixelSize: 15; onClicked: window.visibility === Window.Maximized ? window.showNormal() : window.showMaximized(); background: Rectangle { color: parent.hovered ? UiTokens.interactive : "transparent"; radius: UiTokens.radiusSmall } }
    }
}
