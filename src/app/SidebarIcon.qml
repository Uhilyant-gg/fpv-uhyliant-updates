import QtQuick

// Small line icons of the side panel, drawn so they stay sharp at any size and in any color:
// camera, USB camera, thermal camera, map, sound, layouts.
Canvas {
 id: icon
 property string kind: "main"
 property color color: "#f4f7fb"
 property bool muted: false
 implicitWidth: 26
 implicitHeight: 26
 onKindChanged: requestPaint()
 onColorChanged: requestPaint()
 onMutedChanged: requestPaint()
 onWidthChanged: requestPaint()
 onHeightChanged: requestPaint()

 function camera(ctx, s) {
  // A camera body with a lens.
  var w = 0.66, h = 0.5
  var x = 0.5 - w / 2 - 0.07, y = 0.5 - h / 2
  ctx.beginPath(); ctx.roundedRect(x * s, y * s, w * s, h * s, 0.08 * s, 0.08 * s); ctx.stroke()
  ctx.beginPath(); ctx.arc((x + w / 2) * s, (y + h / 2) * s, h * 0.3 * s, 0, Math.PI * 2); ctx.stroke()
  ctx.beginPath(); ctx.moveTo((x + w) * s, (y + h * 0.35) * s); ctx.lineTo((x + w + 0.14) * s, (y + h * 0.15) * s)
  ctx.lineTo((x + w + 0.14) * s, (y + h * 0.85) * s); ctx.lineTo((x + w) * s, (y + h * 0.65) * s); ctx.stroke()
 }

 onPaint: {
  var ctx = getContext("2d")
  var s = Math.min(width, height)
  ctx.reset()
  ctx.translate((width - s) / 2, (height - s) / 2)
  ctx.strokeStyle = icon.color
  ctx.fillStyle = icon.color
  ctx.lineWidth = Math.max(1.5, s * 0.075)
  ctx.lineCap = "round"; ctx.lineJoin = "round"
  if (kind === "main") {
   camera(ctx, s)
  } else if (kind === "usb") {
   // The USB trident.
   ctx.beginPath(); ctx.moveTo(0.5 * s, 0.1 * s); ctx.lineTo(0.5 * s, 0.84 * s); ctx.stroke()
   ctx.beginPath(); ctx.moveTo(0.42 * s, 0.2 * s); ctx.lineTo(0.5 * s, 0.08 * s); ctx.lineTo(0.58 * s, 0.2 * s); ctx.stroke()
   ctx.beginPath(); ctx.moveTo(0.5 * s, 0.62 * s); ctx.lineTo(0.26 * s, 0.46 * s); ctx.lineTo(0.26 * s, 0.34 * s); ctx.stroke()
   ctx.beginPath(); ctx.arc(0.26 * s, 0.3 * s, 0.06 * s, 0, Math.PI * 2); ctx.fill()
   ctx.beginPath(); ctx.moveTo(0.5 * s, 0.52 * s); ctx.lineTo(0.74 * s, 0.38 * s); ctx.lineTo(0.74 * s, 0.3 * s); ctx.stroke()
   ctx.fillRect(0.68 * s, 0.2 * s, 0.12 * s, 0.1 * s)
   ctx.beginPath(); ctx.arc(0.5 * s, 0.88 * s, 0.07 * s, 0, Math.PI * 2); ctx.fill()
  } else if (kind === "thermal") {
   // A thermometer.
   ctx.beginPath()
   ctx.arc(0.5 * s, 0.74 * s, 0.15 * s, -Math.PI * 0.32, Math.PI * 1.32)
   ctx.lineTo(0.42 * s, 0.18 * s); ctx.arc(0.5 * s, 0.18 * s, 0.08 * s, Math.PI, 0); ctx.closePath(); ctx.stroke()
   ctx.beginPath(); ctx.arc(0.5 * s, 0.74 * s, 0.08 * s, 0, Math.PI * 2); ctx.fill()
   ctx.fillRect(0.47 * s, 0.38 * s, 0.06 * s, 0.32 * s)
   for (var i = 0; i < 3; i++) { ctx.beginPath(); ctx.moveTo(0.66 * s, (0.24 + i * 0.12) * s); ctx.lineTo(0.76 * s, (0.24 + i * 0.12) * s); ctx.stroke() }
  } else if (kind === "map") {
   // A map pin.
   ctx.beginPath()
   ctx.arc(0.5 * s, 0.4 * s, 0.24 * s, Math.PI * 0.82, Math.PI * 2.18)
   ctx.lineTo(0.5 * s, 0.9 * s); ctx.closePath(); ctx.stroke()
   ctx.beginPath(); ctx.arc(0.5 * s, 0.4 * s, 0.08 * s, 0, Math.PI * 2); ctx.fill()
  } else if (kind === "sound") {
   // A speaker with waves, or crossed out when muted.
   ctx.beginPath(); ctx.moveTo(0.14 * s, 0.38 * s); ctx.lineTo(0.3 * s, 0.38 * s); ctx.lineTo(0.5 * s, 0.2 * s)
   ctx.lineTo(0.5 * s, 0.8 * s); ctx.lineTo(0.3 * s, 0.62 * s); ctx.lineTo(0.14 * s, 0.62 * s); ctx.closePath(); ctx.stroke()
   if (muted) {
    ctx.beginPath(); ctx.moveTo(0.64 * s, 0.38 * s); ctx.lineTo(0.86 * s, 0.62 * s); ctx.stroke()
    ctx.beginPath(); ctx.moveTo(0.86 * s, 0.38 * s); ctx.lineTo(0.64 * s, 0.62 * s); ctx.stroke()
   } else {
    ctx.beginPath(); ctx.arc(0.5 * s, 0.5 * s, 0.17 * s, -Math.PI / 4, Math.PI / 4); ctx.stroke()
    ctx.beginPath(); ctx.arc(0.5 * s, 0.5 * s, 0.32 * s, -Math.PI / 4, Math.PI / 4); ctx.stroke()
   }
  } else if (kind === "layouts") {
   // A screen with two windows.
   ctx.beginPath(); ctx.roundedRect(0.08 * s, 0.2 * s, 0.84 * s, 0.6 * s, 0.07 * s, 0.07 * s); ctx.stroke()
   ctx.fillRect(0.56 * s, 0.3 * s, 0.26 * s, 0.16 * s)
   ctx.globalAlpha = 0.6; ctx.fillRect(0.56 * s, 0.54 * s, 0.26 * s, 0.16 * s); ctx.globalAlpha = 1
  }
 }
}
