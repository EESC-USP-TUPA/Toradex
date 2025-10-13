import QtQuick 2.15
import QtQuick.Controls 2.15

Window {
    visible: true
    width: 50
    height: 50
    x: 100
    y: 100

    flags: Qt.Window | Qt.CustomizeWindowHint | Qt.WindowSystemMenuHint
    title: qsTr("Title")

    Rectangle {
        width: parent.width
        height: parent.height
        color: "lightblue"
    }
}
