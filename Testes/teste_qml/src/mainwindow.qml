import QtQuick 2.0
import QtQuick.Controls 2.0

Rectangle {
    width: 200
    height: 100
    color: "red"

    Text {
        id: mytext
        objectName: "mytext"
        text: "Hello World"
        anchors.centerIn: parent
    }

    Button {
        id: mybutton
        objectName: "mybutton"
        text: "Hello"
    }
}
