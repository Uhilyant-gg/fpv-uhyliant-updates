import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// ZeroTier on this PC: is the service there, and the node ID the camera owner needs.
Item {
 id: root
 signal closeRequested()
 property color fg: "#f4f7fb"
 property color sub: "#b7c8da"
 property color green: "#3ddc97"
 property color amber: "#ffbf4a"
 property bool copied: false

 Component.onCompleted: connectionsRuntime.refresh()

 ColumnLayout {
  anchors.fill: parent
  spacing: 12

  RowLayout {
   Layout.fillWidth: true
   Text { text: "ZEROTIER"; color: root.fg; font.pixelSize: 20; font.bold: true; Layout.fillWidth: true }
   Button { text: "Закрити"; onClicked: root.closeRequested() }
  }

  Text {
   Layout.fillWidth: true
   wrapMode: Text.WordWrap
   color: root.sub
   text: "ZeroTier з’єднує цей комп’ютер із камерами через інтернет, зокрема через Starlink. Кожна камера має постійну адресу, тож нічого не треба налаштовувати вручну."
  }

  Rectangle {
   Layout.fillWidth: true
   implicitHeight: stateColumn.implicitHeight + 24
   radius: 12
   color: "#132235"
   border.color: "#2f4860"
   ColumnLayout {
    id: stateColumn
    anchors.fill: parent
    anchors.margins: 12
    spacing: 8
    RowLayout {
     spacing: 8
     Rectangle { width: 10; height: 10; radius: 5; color: connectionsRuntime.zerotierState === "ok" ? root.green : root.amber }
     Text { objectName: "zerotierStateText"; text: connectionsRuntime.zerotierText; color: root.fg; font.pixelSize: 15; font.bold: true; wrapMode: Text.WordWrap; Layout.fillWidth: true }
    }
    Button {
     objectName: "zerotierDownload"
     visible: connectionsRuntime.zerotierState === "missing"
     text: "Завантажити ZeroTier для Windows"
     onClicked: Qt.openUrlExternally("https://www.zerotier.com/download/")
    }
    ColumnLayout {
     visible: connectionsRuntime.zerotierNodeId !== ""
     spacing: 4
     Text { text: "Адреса цього комп’ютера в ZeroTier"; color: root.sub; font.pixelSize: 12 }
     RowLayout {
      spacing: 10
      Text { objectName: "zerotierNodeId"; text: connectionsRuntime.zerotierNodeId; color: root.fg; font.pixelSize: 22; font.bold: true; font.family: "Consolas" }
      Button {
       objectName: "zerotierCopy"
       text: root.copied ? "Скопійовано" : "Копіювати"
       onClicked: { copyHelper.text = connectionsRuntime.zerotierNodeId; copyHelper.selectAll(); copyHelper.copy(); root.copied = true }
      }
     }
     Text {
      Layout.fillWidth: true
      wrapMode: Text.WordWrap
      color: root.sub
      font.pixelSize: 12
      text: "Передайте цю адресу господарю камери: він дозволить цьому комп’ютеру підключатися до неї. Після дозволу камера стане доступною на картці."
     }
    }
   }
  }

  Text {
   Layout.fillWidth: true
   wrapMode: Text.WordWrap
   color: root.sub
   font.pixelSize: 12
   text: "Щоб підключити камеру, в її налаштуваннях (⚙ на картці) вкажіть ID мережі ZeroTier та ID вузла камери. Станція сама приєднається до мережі, коли ви виберете підключення «ZeroTier»."
  }

  Item { Layout.fillHeight: true }
  TextEdit { id: copyHelper; visible: false }
 }
}
