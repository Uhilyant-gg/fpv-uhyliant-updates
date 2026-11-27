import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// A section of the station menu: tabs on the left, the selected page on the right.
// Pages are loaded only while their tab is open, so closing the hub releases them.
Item {
 id: root
 objectName: "tabbedHub"
 signal closeRequested()
 signal pageLoaded(string key, var item)
 property string title: ""
 property var tabs: []          // [{key, label, detail}]
 property var pages: ({})       // key -> Component
 property string currentKey: tabs.length ? tabs[0].key : ""
 property color fg: "#f4f7fb"
 property color sub: "#b7c8da"

 function select(key) {
  for (var i = 0; i < tabs.length; i++) {
   if (tabs[i].key === key) { currentKey = key; return true }
  }
  return false
 }

 RowLayout {
  anchors.fill: parent
  spacing: 14

  ColumnLayout {
   Layout.preferredWidth: 230
   Layout.maximumWidth: 230
   Layout.fillHeight: true
   spacing: 6
   Text { text: root.title; color: root.fg; font.pixelSize: 18; font.bold: true; wrapMode: Text.WordWrap; Layout.fillWidth: true; Layout.bottomMargin: 6 }
   Repeater {
    model: root.tabs
    delegate: Button {
     required property var modelData
     objectName: "hubTab-" + modelData.key
     Layout.fillWidth: true
     Layout.preferredHeight: 54
     checkable: true
     checked: root.currentKey === modelData.key
     onClicked: root.currentKey = modelData.key
     background: Rectangle {
      radius: 8
      color: parent.checked ? "#2b4a6a" : (parent.hovered ? "#22364b" : "#132235")
      border.color: parent.checked ? "#5aa4ff" : "#2f4860"
     }
     contentItem: ColumnLayout {
      spacing: 1
      Text { text: modelData.label; color: root.fg; font.pixelSize: 15; font.bold: true; Layout.fillWidth: true; elide: Text.ElideRight }
      Text { visible: text !== ""; text: modelData.detail || ""; color: root.sub; font.pixelSize: 11; Layout.fillWidth: true; elide: Text.ElideMiddle }
     }
    }
   }
   Item { Layout.fillHeight: true }
   Text { text: "Esc — закрити"; color: root.sub; font.pixelSize: 11 }
  }

  Rectangle { Layout.preferredWidth: 1; Layout.fillHeight: true; color: "#2f4860" }

  Loader {
   id: page
   objectName: "hubPage"
   Layout.fillWidth: true
   Layout.fillHeight: true
   sourceComponent: root.pages[root.currentKey] || null
   onLoaded: root.pageLoaded(root.currentKey, item)
  }
  Connections {
   target: page.item
   ignoreUnknownSignals: true
   function onCloseRequested() { root.closeRequested() }
  }
 }
}
