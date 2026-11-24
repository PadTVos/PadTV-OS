import QtQuick

Item {
    Image { anchors.fill: parent; source: "waterfall.png"; fillMode: Image.PreserveAspectCrop }
    Rectangle { anchors.fill: parent; color: "#66091619" }
    Image { anchors.centerIn: parent; width: parent.width * 0.6; height: parent.height * 0.3; source: "logo.png"; fillMode: Image.PreserveAspectFit }
    Text { anchors.horizontalCenter: parent.horizontalCenter; anchors.bottom: parent.bottom; anchors.bottomMargin: 36; text: "Připravujeme váš PadTV"; color: "white"; font.pixelSize: 24 }
}
