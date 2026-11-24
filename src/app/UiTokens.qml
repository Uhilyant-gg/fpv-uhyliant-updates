pragma Singleton
import QtQuick

QtObject {
    // Typography
    readonly property string fontFamily: "Segoe UI Variable"
    readonly property int fontCaption: 11
    readonly property int fontBody: 13
    readonly property int fontControl: 14
    readonly property int fontSection: 18
    readonly property int fontTitle: 28

    // Dark shell palette
    readonly property color canvas: "#07101A"
    readonly property color chrome: "#0A111B"
    readonly property color surface: "#0D1723"
    readonly property color elevated: "#122033"
    readonly property color interactive: "#172B42"
    readonly property color line: "#20364F"
    readonly property color foreground: "#F7F9FC"
    readonly property color secondary: "#91A4BC"
    readonly property color muted: "#6F849D"

    // Semantic colors
    readonly property color primary: "#168AFF"
    readonly property color primaryHover: "#329BFF"
    readonly property color ready: "#2BD89F"
    readonly property color attention: "#FFB84D"
    readonly property color problem: "#FF6678"
    readonly property color unknown: "#8192A7"

    // Geometry and rhythm
    readonly property int radiusSmall: 8
    readonly property int radiusControl: 10
    readonly property int radiusCard: 16
    readonly property int radiusDialog: 18
    readonly property int space4: 4
    readonly property int space8: 8
    readonly property int space12: 12
    readonly property int space16: 16
    readonly property int space20: 20
    readonly property int space24: 24
    readonly property int controlHeight: 40
    readonly property int chromeHeight: 44
}
