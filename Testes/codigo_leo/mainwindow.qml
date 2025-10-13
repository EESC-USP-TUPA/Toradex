import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15  // Para estilos adicionais, se necessário
// import QtQuick.Extras 1.4
import QtQuick 2.13
import QtQuick.Window 2.13
import QtQuick.Layouts 1.15

Window {

    id: mainWindow
    visible: true
    visibility: "FullScreen"
    width: 900
    height: 600
    color: "#000"
    title: qsTr("Title")

     property real gaugeValue: backend.gaugeValue
     property real gaugeValueRPM: backend.gaugeValueRPM
     property real gaugeValueVel: backend.gaugeValueVel
     property real gaugeValueAPPS: backend.gaugeValueAPPS
     property real gaugeValueBSE: backend.gaugeValueBSE
     property real gaugeValueVOL: backend.gaugeValueVol
     property real gaugeValueSOC: backend.gaugeValueSOC
     property real gaugeValueCurrent: backend.gaugeValueCurrent
     property real gaugeValueVoltage: backend.gaugeValueVoltage
     property real counterCAN: backend.counterCAN



    Rectangle {

        width: 1000
        height: 600
        // color: "#FF0000"
        color: "#00000000"


   Row
   {

    ColumnLayout
    {

        Row
        {

           Rectangle {
                width: 300
                height: 300
                color: "#00000000"// Background color

            Canvas {
                id: canvas
                anchors.fill: parent
                onPaint: {
                    var ctx = getContext("2d");
                    ctx.reset();
                    
                    // Draw the gauge background
                    ctx.beginPath();
                    ctx.arc(width / 2, height / 2, 140, 0, 2 * Math.PI);
                    var gradient = ctx.createRadialGradient(width / 2, height / 2, 70, width / 2, height / 2, 140);
                    gradient.addColorStop(0, "#00000000");
                    gradient.addColorStop(1, "#00000000");
                    ctx.fillStyle = gradient;
                    ctx.fill();
                    
                    // Draw the gauge scale
                    ctx.lineWidth = 4;
                    for (var i = 0; i <= 10; i++) {
                        if (i <= 2) {
                            ctx.strokeStyle = "#0000ff";
                        } else if (i > 8) {
                            ctx.strokeStyle = "#AA0000";
                        } else {
                            ctx.strokeStyle = "white";
                        }
                        var angle = i * Math.PI / 10;
                        var x1 = width / 2 + Math.cos(angle) * 120;
                        var y1 = height / 2 - Math.sin(angle) * 120;
                        var x2 = width / 2 + Math.cos(angle) * 140;
                        var y2 = height / 2 - Math.sin(angle) * 140;
                        ctx.beginPath();
                        ctx.moveTo(x1, y1);
                        ctx.lineTo(x2, y2);
                        ctx.stroke();
                    }

                    // Draw the gauge labels
                    var labels = ["200", "180", "160", "140", "120", "100", "80", "60", "40", "20", "0"];
                    ctx.font = "bold 18px Arial";
                    ctx.fillStyle = "#FFFFFF";
                    for (var i = 0; i <= 10; i++) {
                        var angle = i * Math.PI / 10;
                        var x = width / 2 + Math.cos(angle) * 105;
                        var y = height / 2 - Math.sin(angle) * 105;
                        ctx.fillText(labels[i], x - 10, y + 5);
                    }

                    // Draw the needle
                    var valueAngle = Math.PI - ((gaugeValue / 200) * Math.PI);
                    ctx.beginPath();
                    ctx.moveTo(width / 2, height / 2);
                    ctx.lineTo(width / 2 + Math.cos(valueAngle) * 120, height / 2 - Math.sin(valueAngle) * 120);
                    ctx.lineWidth = 4;
                    ctx.strokeStyle = "#FFFFFF";
                    ctx.stroke();

                    // Draw the center circle
                    ctx.beginPath();
                    ctx.arc(width / 2, height / 2, 10, 0, 2 * Math.PI);
                    ctx.fillStyle ="#white";
                    ctx.fill();
                }
            }

            Text {
                id: gaugeLabel
                text: "VEL\n" + Math.round(gaugeValue) + " km/h" 
                anchors.centerIn: parent
                wrapMode: Text.WordWrap
                anchors.verticalCenterOffset: 60
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                font.pixelSize: 30
                font.bold: true
                font.family: "Arial"
                color: "white"
                layer.enabled: true
                layer.smooth: true
                renderType: Text.NativeRendering
            }
}

        Rectangle {
            // anchors.centerIn: parent
            // anchors.fill: parent
            // anchors.top = parent.top
            // anchors.left = parent.left
            width: 300
            height: 300
            // color: "#00F000"
            color: "black"

            Canvas {
                id: canvasRPM
                anchors.fill: parent
                onPaint: {
                    var ctx = getContext("2d");
                    ctx.reset();
                    
                    // Draw the gauge background
                    ctx.beginPath();
                    ctx.arc(width / 2, height / 2, 140, 0, 2 * Math.PI);
                    var gradient = ctx.createRadialGradient(width / 2, height / 2, 70, width / 2, height / 2, 140);
                    gradient.addColorStop(0, "#00000000");
                    gradient.addColorStop(1, "#00000000");
                    ctx.fillStyle = gradient;
                    ctx.fill();
                    
                    // Draw the gauge scale
                    ctx.lineWidth = 4;
                    for (var i = 0; i <= 10; i++) {
                        if (i <= 2) {
                            ctx.strokeStyle = "#0000ff";
                        } else if (i > 8) {
                            ctx.strokeStyle = "#AA0000";
                        } else {
                            ctx.strokeStyle = "#FFFFFF";
                        }
                        var angle = i * Math.PI / 10;
                        var x1 = width / 2 + Math.cos(angle) * 120;
                        var y1 = height / 2 - Math.sin(angle) * 120;
                        var x2 = width / 2 + Math.cos(angle) * 140;
                        var y2 = height / 2 - Math.sin(angle) * 140;
                        ctx.beginPath();
                        ctx.moveTo(x1, y1);
                        ctx.lineTo(x2, y2);
                        ctx.stroke();
                    }

                    // Draw the gauge labels
                    var labels = ["5000", "4500", "4000", "3500", "3000", "2500", "2000", "1500", "1000", "500", "0"];
                    ctx.font = "bold 18px Arial";
                    ctx.fillStyle = "#FFFFFF";
                    for (var i = 0; i <= 10; i++) {
                        var angle = i * Math.PI / 10;
                        var x = width / 2 + Math.cos(angle) * 105;
                        var y = height / 2 - Math.sin(angle) * 105;
                        ctx.fillText(labels[i], x - 10, y + 5);
                    }

                    // Draw the needle
                    var valueAngle = Math.PI - (((gaugeValueRPM)  / 5000) * Math.PI);
                    ctx.beginPath();
                    ctx.moveTo(width / 2, height / 2);
                    ctx.lineTo(width / 2 + Math.cos(valueAngle) * 120, height / 2 - Math.sin(valueAngle) * 120);
                    ctx.lineWidth = 4;
                    ctx.strokeStyle = "#FFFFFF";
                    ctx.stroke();

                    // Draw the center circle
                    ctx.beginPath();
                    ctx.arc(width / 2, height / 2, 10, 0, 2 * Math.PI);
                    ctx.fillStyle ="#FFFFFF";
                    ctx.fill();
                }
    }

    Text {
        id: gaugeLabelRPM
        text: "RPM\n" + Math.round(gaugeValueRPM) 
        anchors.centerIn: parent
        wrapMode: Text.WordWrap
        anchors.verticalCenterOffset: 60
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        font.pixelSize: 30
        font.bold: true
        font.family: "Arial"
        color: "white"
        layer.enabled: true
        layer.smooth: true
        renderType: Text.NativeRendering
    }


        }

        }

         Rectangle {
            width: 600
            height: 300
            // color: "#00F000"
            color:  "#00000000"

            ColumnLayout
            {

                Row
                {
                    Rectangle {
                    
                    width: 310
                    height: 50
                    color: "#00000000" // Background color

               Canvas {
                    id: canvasAPPS
                    width: parent.width
                    height: 50
                    anchors.centerIn: parent
                    onPaint: {
                        var ctx = getContext("2d");
                        ctx.reset();

                        // Draw the gauge background
                        ctx.fillStyle = "#cccccc";
                        ctx.fillRect(0, 0, canvas.width, 30);

                        // Draw the gauge progress
                        var progressWidth = (gaugeValueAPPS / 100) * (canvas.width);
                        ctx.fillStyle = "#fd00d9";
                        ctx.fillRect(0, 0, progressWidth, 30);

                        // Draw the gauge border
                        ctx.strokeStyle = "#000000";
                        ctx.lineWidth = 2;
                        ctx.strokeRect(0, 0, canvas.width, 30);

                        // Draw the needle
                        var needleX = progressWidth;
                        ctx.strokeStyle = "#fdddd9";
                        ctx.lineWidth = 4;
                        ctx.beginPath();
                        ctx.moveTo(needleX, 0);
                        ctx.lineTo(needleX, 30);
                        ctx.stroke();
                    }
}

                }


                Rectangle{
                    width: 250
                    height: 50
                    color: "#00000000"

                     Text {
                        id: gaugeLabel453
                        text: "APPS: " + Math.round(gaugeValueAPPS) + "%" + " (-|-)%"
                        anchors.left: parent.left
                        anchors.top: parent.top
                        wrapMode: Text.WordWrap
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        font.pixelSize: 24
                        font.bold: true
                        font.family: "Arial"
                        color: "white"
                        layer.enabled: true
                        layer.smooth: true
                        renderType: Text.NativeRendering
                    }

                }

                }

                Row
                {
                    Rectangle {
                    
                    width: 310
                    height: 50
                    color: "#00000000" // Background color

               Canvas {
                    id: canvasBSE
                    width: parent.width
                    height: 50
                    anchors.centerIn: parent
                    onPaint: {
                        var ctx = getContext("2d");
                        ctx.reset();

                        // Draw the gauge background
                        ctx.fillStyle = "#cccccc";
                        ctx.fillRect(0, 0, canvas.width, 30);

                        // Draw the gauge progress
                        var progressWidth = (gaugeValueBSE / 100) * (canvas.width);
                        ctx.fillStyle = "#00ff00";
                        ctx.fillRect(0, 0, progressWidth, 30);

                        // Draw the gauge border
                        ctx.strokeStyle = "#000000";
                        ctx.lineWidth = 2;
                        ctx.strokeRect(0, 0, canvas.width, 30);

                        // Draw the needle
                        var needleX = progressWidth;
                        ctx.strokeStyle = "#00ff00";
                        ctx.lineWidth = 4;
                        ctx.beginPath();
                        ctx.moveTo(needleX, 0);
                        ctx.lineTo(needleX, 30);
                        ctx.stroke();
                    }
}

                }


                Rectangle{
                    width: 250
                    height: 50
                    color: "#00000000"

                     Text {
                        id: gaugeLabel4533
                        text: "BSE: " + Math.round(gaugeValueBSE) + "%" + " (-|-)%"
                        anchors.left: parent.left
                        anchors.top: parent.top
                        wrapMode: Text.WordWrap
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        font.pixelSize: 24
                        font.bold: true
                        font.family: "Arial"
                        color: "white"
                        layer.enabled: true
                        layer.smooth: true
                        renderType: Text.NativeRendering
                    }

                }

                }

                Row
                {
                    Rectangle {
                    
                    width: 310
                    height: 50
                    color: "#00000000" // Background color

               Canvas {
                    id: canvasVOL
                    width: parent.width
                    height: 50
                    anchors.centerIn: parent
                    onPaint: {
                        var ctx = getContext("2d");
                        ctx.reset();

                        // Draw the gauge background
                        ctx.fillStyle = "#cccccc";
                        ctx.fillRect(0, 0, canvas.width, 30);

                        // Draw the gauge progress
                        var progressWidth = (gaugeValueVOL / 100) * (canvas.width);
                        ctx.fillStyle = "#0000ff";
                        ctx.fillRect(0, 0, progressWidth, 30);

                        // Draw the gauge border
                        ctx.strokeStyle = "#000000";
                        ctx.lineWidth = 2;
                        ctx.strokeRect(0, 0, canvas.width, 30);

                        // Draw the needle
                        var needleX = progressWidth;
                        ctx.strokeStyle = "#0000ff";
                        ctx.lineWidth = 4;
                        ctx.beginPath();
                        ctx.moveTo(needleX, 0);
                        ctx.lineTo(needleX, 30);
                        ctx.stroke();
                    }
}

                }


                Rectangle{
                    width: 250
                    height: 50
                    color: "#00000000"

                     Text {
                        id: gaugeLabel45334
                        text: "VOL: " + Math.round(90 - gaugeValueVOL) + "°"
                        anchors.left: parent.left
                        anchors.top: parent.top
                        wrapMode: Text.WordWrap
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        font.pixelSize: 24
                        font.bold: true
                        font.family: "Arial"
                        color: "white"
                        layer.enabled: true
                        layer.smooth: true
                        renderType: Text.NativeRendering
                    }

                }

                }


            Row
            {

                
                Rectangle{
                        width: 300
                        height: 150
                        // color: "red"
                        color: "#00000000"
                

                    Image {
                            id: image333
                            anchors.fill: parent
                            horizontalAlignment: Image.AlignHCenter
                            verticalAlignment: Image.AlignVCenter
                            source: "assets/toradexmain.png"
                            fillMode: Image.PreserveAspectFit
                        }
                    }


                    Rectangle
                    {
                        width: 30
                        height: 50
                        color: "#00000000"
                    }

                    Rectangle
                    {
                        width: 300
                        height: 150
                        // color: "red"
                        color: "#00000000"

                         Text {
                            anchors.centerIn: parent
                            text: "EVERYTHING OK"
                            font.pixelSize: 30
                            font.bold : true
                            color: "#f00"
                            font.family: "Arial"
                            layer.enabled: true
                            layer.smooth: true
                            renderType: Text.NativeRendering
            }
                    }



                    

            //          Rectangle{
            //             width: 200
            //             height: 70
            //             color: "#00000000"
            //             Text {
            //                 anchors.centerIn: parent
            //                 text: "TEMPERATURE"
            //                 font.pixelSize: 30
            //                 font.bold : true
            //                 color: "#FFF"
            //                 font.family: "Arial"
            //                 layer.enabled: true
            //                 layer.smooth: true
            //                 renderType: Text.NativeRendering
            // }
            //          }
            }

            }

        }

        
      

    }


    Rectangle{
         width: 500
         height: 600
        //  color: "green"
        color: "#00000000"

         ColumnLayout
         {
            spacing: 10

            Rectangle{
                width: 430
                height: 10
                color: "#00000000"
            }

            Rectangle{
                width: 430
                height: 150
                // color: "red"
                color: "#00000000"
        

               Image {
                    id: image
                    anchors.fill: parent
                    anchors.margins: 20
                    horizontalAlignment: Image.AlignHCenter
                    verticalAlignment: Image.AlignVCenter
                    source: "assets/tupa-logo-main.png"
                    fillMode: Image.PreserveAspectFit
                }
            }
            

          Rectangle
          {
            width: 300
            height: 70
            color: "#00000000"

            
            Row
            {

                Rectangle
                {
                    width: 60
                    height: 50
                    color: "#00000000"
                }
                
                Rectangle{
                        width: 70
                        height: 70
                        // color: "red"
                        color: "#00000000"
                

                    Image {
                            id: image3
                            anchors.fill: parent
                            horizontalAlignment: Image.AlignHCenter
                            verticalAlignment: Image.AlignVCenter
                            source: "assets/bat.png"
                            fillMode: Image.PreserveAspectFit
                        }
                    }

                     Rectangle{
                        width: 290
                        height: 70
                        color: "#00000000"
                        Text {
                            anchors.centerIn: parent
                            text: "PACK STATUS"
                            font.pixelSize: 30
                            font.bold : true
                            color: "#FFF"
                            font.family: "Arial"
                            layer.enabled: true
                            layer.smooth: true
                            renderType: Text.NativeRendering
            }
                     }

            }
          }

            Rectangle
                {
                    width: 60
                    height: 3
                    color: "#00000000"
                }

            Rectangle
            {
                width:  430
                height: 30
                color: "#00000000"
                Text {
                anchors.left: parent.left
                anchors.leftMargin: 100
                // anchors.centerIn: parent
                text: "Current : " + Math.round(gaugeValueCurrent) + " [A]"
                font.pixelSize: 27
                font.bold : true
                color: "#0f0"
                font.family: "Arial"
                layer.enabled: true
                layer.smooth: true
                renderType: Text.NativeRendering
            }
            }

            Rectangle
            {
                width:  430
                height: 30
                color: "#00000000"
                Text {
                anchors.left: parent.left
                anchors.leftMargin: 100
                text: "Voltage : " + Math.round(gaugeValueVoltage) + " [V]"
                font.pixelSize: 27
                font.bold : true
                color: "#0f0"
                font.family: "Arial"
                layer.enabled: true
                layer.smooth: true
                renderType: Text.NativeRendering
            }
            }

            Rectangle
            {
                width:  430
                height: 27
                color: "#00000000"
                Text {
                anchors.left: parent.left
                anchors.leftMargin: 100
                text: "Pack SOC : " + Math.round(gaugeValueSOC) + "%" 
                font.pixelSize: 30
                font.bold : true
                // color: "#00F"
                color: "#0f0"
                font.family: "Arial"
                layer.enabled: true
                layer.smooth: true
                renderType: Text.NativeRendering
            }
            }

            Rectangle
                {
                    width: 60
                    height: 3
                    color: "#00000000"
                }


                      Rectangle
          {
            width: 300
            height: 70
            color: "#00000000"

            
            Row
            {

                Rectangle
                {
                    width: 60
                    height: 50
                    color: "#00000000"
                }
                
                Rectangle{
                        width: 70
                        height: 70
                        // color: "red"
                        color: "#00000000"
                

                    Image {
                            id: image33
                            anchors.fill: parent
                            horizontalAlignment: Image.AlignHCenter
                            verticalAlignment: Image.AlignVCenter
                            source: "assets/car.png"
                            fillMode: Image.PreserveAspectFit
                        }
                    }

                     Rectangle{
                        width: 290
                        height: 70
                        color: "#00000000"
                        Text {
                            anchors.centerIn: parent
                            text: "CONNECTIVITY"
                            font.pixelSize: 30
                            font.bold : true
                            color: "#FFF"
                            font.family: "Arial"
                            layer.enabled: true
                            layer.smooth: true
                            renderType: Text.NativeRendering
            }
                     }
            }
          }

            Rectangle
                {
                    width: 60
                    height: 3
                    color: "#00000000"
                }
    
        
            Rectangle
            {
                width:  430
                height: 30
                color: "#00000000"
                Text {
                anchors.centerIn: parent
                text: "Message CAN/s : " + Math.round(counterCAN)
                font.pixelSize: 27
                font.bold : true
                color: "#F00"
                font.family: "Arial"
                layer.enabled: true
                layer.smooth: true
                renderType: Text.NativeRendering
            }
            }

                        Rectangle
            {
                width:  430
                height: 30
                color: "#00000000"
                Text {
                anchors.centerIn: parent
                text: "Telemetry : OK"
                font.pixelSize: 27
                font.bold : true
                color: "#F00"
                font.family: "Arial"
                layer.enabled: true
                layer.smooth: true
                renderType: Text.NativeRendering
            }
            }



            // Rectangle
            // {
            //     width:  430
            //     height: 30
            //     color: "#00000000"
            //     Text {
            //     anchors.centerIn: parent
            //     text: "MESSAGE CAN/s : 12"
            //     font.pixelSize: 30
            //     font.bold : true
            //     color: "#F00"
            // }
            // }

            // Rectangle
            // {
            //     width:  430
            //     height: 30
            //     color: "#00000000"
            //     Text {
            //     anchors.centerIn: parent
            //     text: "MESSAGE CAN/s : 12"
            //     font.pixelSize: 30
            //     font.bold : true
            //     color: "#F00"
            // }
            // }

            
          



         }


    }
        //   Rectangle {
        //     width: 40
        //     height: 300
        //     color: "#d3d3d3"
        //     border.color: "#000"
        //     border.width: 2
        //     radius: 5

        //     Rectangle {
        //         width: parent.height * (gaugeValue / 100)
        //         height: parent.width
        //         color: Qt.rgba(0, 1, 0, 0.7)
        //         radius: 5
        //     }
        // }

   }

    }





    Connections {
        target: backend
        onGaugeValueChanged: {
            canvas.requestPaint()
        }

        onGaugeValueRPMChanged: {
        canvasRPM.requestPaint()
        }

        onGaugeValueAPPSChanged: {
        canvasAPPS.requestPaint()
        }

        onGaugeValueBSEChanged: {
        canvasBSE.requestPaint()
        }

        onGaugeValueVolChanged: {
        canvasVOL.requestPaint()
        }



        

        
    }


}
