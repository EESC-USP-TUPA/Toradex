import QtQuick 2.13
import QtQuick.Controls 2.13

Item {
    id: item1
    width: 1050
    height: 620

    Rectangle {
        anchors.fill: parent
        // anchors.top:
        color: "blue"
    }


    Image {
        id: image
        anchors.fill: parent
        anchors.margins: 20
        horizontalAlignment: Image.AlignHCenter
        verticalAlignment: Image.AlignVCenter
        source: "assets/torizon-logo.png"
        fillMode: Image.PreserveAspectFit
    }
}

/*##^##
Designer {
    D{i:0;formeditorZoom:0.66}
}
##^##*/
