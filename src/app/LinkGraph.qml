import QtQuick

// Frames received in each of the last seconds, newest on the right.
// A second without video is a full-height red bar, so an outage is seen at a glance.
Item {
 id: root
 property var values: []
 // As many seconds as fit with bars at least 2 px wide; the newest are kept.
 property int slots: Math.max(10, Math.min(60, Math.floor((width - 4) / 3)))
 readonly property var shown: values.length > slots ? values.slice(values.length - slots) : values
 property color green: "#27d59a"
 property color amber: "#ffb84d"
 property color red: "#ff6678"
 readonly property real peak: {
  var top = 1
  for (var i = 0; i < shown.length; i++) top = Math.max(top, Number(shown[i]))
  return top
 }
 implicitWidth: 120
 implicitHeight: 22

 Rectangle { anchors.fill: parent; color: "#0f1c2b"; radius: 3 }
 Row {
  anchors.fill: parent
  anchors.margins: 2
  spacing: 1
  Repeater {
   model: root.slots
   Item {
    readonly property int offset: index - (root.slots - root.shown.length)
    readonly property real value: offset >= 0 ? Number(root.shown[offset]) : -1
    width: Math.max(2, Math.floor((root.width - 4 - (root.slots - 1)) / root.slots))
    height: root.height - 4
    Rectangle {
     visible: value >= 0
     anchors.bottom: parent.bottom
     width: parent.width
     height: value === 0 ? parent.height : Math.max(2, parent.height * value / root.peak)
     color: value === 0 ? root.red : (value < root.peak * 0.5 ? root.amber : root.green)
     opacity: value === 0 ? 0.75 : 1
    }
   }
  }
 }
}
