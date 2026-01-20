''' Docstring '''
# pylint: disable = unused-import
# pylint: disable = no-name-in-module

import sys
import time
import threading
from telemetry import MyTelemetry
from mycan import MyCAN
import can
import os
import subprocess
from PySide2.QtQml import QQmlApplicationEngine
from PySide2.QtGui import QGuiApplication
from PySide2.QtCore import QUrl
from PySide2.QtCore import QFile, QTimer, QUrl
from PySide2.QtGui import QGuiApplication
from PySide2.QtCore import QObject, Property, Signal

#DEFAULT
THINGSBOARD_HOST = 'demo.thingsboard.io'
#ALTERAR O TOKEN DE ACORDO COM O PROJETO
ACCESS_TOKEN = '5ajqn2DYKCUGMqZYTbKJ'

mainData = {
    'AccelPedal': 0,
    'BrakePedal': 0,
    'SteerAngle': 0,
    'PackCurrent': 0,
    'PackVoltage': 0,
}

packData = {
    'SOC' : 0,
    'HighTemp' : 0,
    'LowTemp' : 0,
    'PackAmphours' : 0,
}

flagsData = {
    'APPSFlag' : 0,
    'BPPCFlag' : 0,
    'BSEFlag' : 0,
}

tempData = {
    'MotorTemp_BL' : 0,
    'InvTemp_BL' : 0,
    'TransTemp_BL': 0,
    'MotorTemp_BR' : 0,
    'InvTemp_BR: 0' : 0,
    'TransTemp_BR': 0,
}

rpmData = {
    'MotorRPM_1' : 0,
    'MotorRPM_2' : 0,
}

canData = {
    'Counter' : 0
}


def publish_every_1_seconds():
    while True:
        time.sleep(1)
        thingsBoard.public_on_ThingsBoard(mainData)
        thingsBoard.public_on_ThingsBoard(flagsData)
        time.sleep(1)
        thingsBoard.public_on_ThingsBoard(tempData)
        thingsBoard.public_on_ThingsBoard(rpmData)

def update_gauge():
    backend.gaugeValueRPM = (rpmData['MotorRPM_1'] + rpmData['MotorRPM_2'])/2
    test_sanity = ((backend.gaugeValueRPM/60) / 4.5 ) * 2 * 3.1415 * 0.25
    if(test_sanity<200) :
        backend.gaugeValue = ((backend.gaugeValueRPM/60) / 4.5 ) * 2 * 3.1415 * 0.25
    else:
        backend.gaugeValue = 200
    backend.gaugeValueAPPS = mainData['AccelPedal'] / 10
    backend.gaugeValueBSE = mainData['BrakePedal'] / 10
    backend.gaugeValueVol = mainData['SteerAngle'] / 18
    backend.gaugeValueCurrent = mainData['PackCurrent'] 
    backend.gaugeValueVoltage = mainData['PackVoltage'] 
    backend.counterCAN = canData['Counter'] / (0.1)
    canData['Counter'] = 0
    backend.gaugeValueSOC = packData['SOC'] 


    
    

class GaugeBackend(QObject):
    def __init__(self):
        super().__init__()  
        self._gaugeValue = 0
        self._gaugeValueRPM = 0
        self._gaugeValueVel = 0
        self._gaugeValueAPPS = 0
        self._gaugeValueBSE = 0
        self._gaugeValueVol = 0
        self._gaugeValueSOC = 0
        self._gaugeValueCurrent = 0
        self._gaugeValueVoltage = 0
        self._counterCAN = 0

    gaugeValueChanged = Signal()
    gaugeValueRPMChanged = Signal()
    gaugeValueAPPSChanged = Signal()
    gaugeValueBSEChanged = Signal()
    gaugeValueVolChanged = Signal()
    gaugeValueSOCChanged = Signal()
    gaugeValueCurrentChanged = Signal()
    gaugeValueVoltageChanged = Signal()
    counterCANChanged = Signal()


    @Property(float, notify=gaugeValueChanged)
    def gaugeValue(self):
        return self._gaugeValue

    @gaugeValue.setter
    def gaugeValue(self, value):
        if self._gaugeValue != value:
            self._gaugeValue = value
            self.gaugeValueChanged.emit()

    @Property(float, notify=gaugeValueRPMChanged)
    def gaugeValueRPM(self):
        return self._gaugeValueRPM

    @gaugeValueRPM.setter
    def gaugeValueRPM(self, value):
        if self._gaugeValueRPM != value:
            self._gaugeValueRPM = value
            self.gaugeValueRPMChanged.emit()

    @Property(float, notify=gaugeValueAPPSChanged)
    def gaugeValueAPPS(self):
        return self._gaugeValueAPPS

    @gaugeValueAPPS.setter
    def gaugeValueAPPS(self, value):
        if self._gaugeValueAPPS != value:
            self._gaugeValueAPPS = value
            self.gaugeValueAPPSChanged.emit()

    @Property(float, notify=gaugeValueBSEChanged)
    def gaugeValueBSE(self):
        return self._gaugeValueBSE

    @gaugeValueBSE.setter
    def gaugeValueBSE(self, value):
        if self._gaugeValueBSE != value:
            self._gaugeValueBSE = value
            self.gaugeValueBSEChanged.emit()

    @Property(float, notify=gaugeValueVolChanged)
    def gaugeValueVol(self):
        return self._gaugeValueVol

    @gaugeValueVol.setter
    def gaugeValueVol(self, value):
        if self._gaugeValueVol != value:
            self._gaugeValueVol = value
            self.gaugeValueVolChanged.emit()

    @Property(float, notify=gaugeValueSOCChanged)
    def gaugeValueSOC(self):
        return self._gaugeValueSOC

    @gaugeValueSOC.setter
    def gaugeValueSOC(self, value):
        if self._gaugeValueSOC != value:
            self._gaugeValueSOC = value
            self.gaugeValueSOCChanged.emit()

    @Property(float, notify=gaugeValueCurrentChanged)
    def gaugeValueCurrent(self):
        return self._gaugeValueCurrent

    @gaugeValueCurrent.setter
    def gaugeValueCurrent(self, value):
        if self._gaugeValueCurrent != value:
            self._gaugeValueCurrent = value
            self.gaugeValueCurrentChanged.emit()

    @Property(float, notify=gaugeValueVoltageChanged)
    def gaugeValueVoltage(self):
        return self._gaugeValueVoltage

    @gaugeValueVoltage.setter
    def gaugeValueVoltage(self, value):
        if self._gaugeValueVoltage != value:
            self._gaugeValueVoltage = value
            self.gaugeValueVoltageChanged.emit()

    @Property(float, notify=counterCANChanged)
    def counterCAN(self):
        return self._counterCAN

    @counterCAN.setter
    def counterCAN(self, value):
        if self._counterCAN != value:
            self._counterCAN = value
            self.counterCANChanged.emit()



def run_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return e.stdout, e.stderr



def can_init():

    result, anotherResult = run_command("ip link show can0")
    time.sleep(1)
    print(result)
    print(anotherResult)

def receive_can_messages():
    while True:
            message = bus.recv()  # Lê a mensagem CAN
            if message:
                canData['Counter'] = canData['Counter'] + 1
                print(message)
                #BMS STATUS
                if message.arbitration_id == 0x03B:
                    mainData['PackCurrent'] =  (message.data[1] | (message.data[0] << 8)) / 10
                    mainData['PackVoltage'] =  (message.data[3] | (message.data[2] << 8)) / 10
                elif message.arbitration_id == 0x3CB:
                    packData["HighTemperature"] = message.data[4]
                    packData["LowTemperature"] = message.data[5]
                    packData["SOC"] = message.data[3]
                elif message.arbitration_id == 0x6B2:
                    packData['PackAmphours'] = message.data[6]
                #CONTROL STATUS
                elif message.arbitration_id == 0x080:
                    mainData['AccelPedal'] = (message.data[0] * 100) + message.data[1] 
                    mainData['BrakePedal'] = (message.data[2] * 100) + message.data[3] 
                    mainData['SteerAngle'] = (message.data[4] * 100) + message.data[5]
                    flagsData['APPSFlag'] = (message.data[6] & 0x01)
                    flagsData['BSEFlag'] = (message.data[6] & 0x02) >> 1
                    flagsData['APPSFlag'] = (message.data[6] & 0x04) >> 2
                #RPM AND TEMP STATUS
                elif message.arbitration_id == 0x380:
                    rpmData['MotorRPM_1'] = message.data[0] * 100 + message.data[1]
                    tempData["MotorTemp_BL"] = message.data[2]
                    tempData["InvTemp_BL"] = message.data[3]
                    tempData["TransTemp_BL"] = message.data[4]
                elif message.arbitration_id == 0x480:
                    rpmData['MotorRPM_2'] = message.data[0] * 100 + message.data[1]
                    tempData["MotorTemp_BR"] = message.data[2]
                    tempData["TransTemp_BR"] = message.data[4]


def start_can_receiver_thread():
    receiver_thread = threading.Thread(target=receive_can_messages)
    receiver_thread.daemon = True
    receiver_thread.start()


if __name__ == "__main__":
    print("Hello Torizon!")

    QURL_PATH = "src/mainwindow.qml"
    #QURL_PATH = "src/teste.qml"

    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()
    engine.load(QUrl(QURL_PATH))
    thingsBoard = MyTelemetry(THINGSBOARD_HOST, ACCESS_TOKEN)

    # Create an instance of GaugeBackend
    backend = GaugeBackend()
    engine.rootContext().setContextProperty("backend", backend)

    timer = QTimer()
    timer.timeout.connect(update_gauge)
    timer.start(100)  # Update every second
    can_init()
    
    bus = can.interface.Bus(channel='can0', bustype='socketcan')
    
    start_can_receiver_thread()
    thread_1_s = threading.Thread(target=publish_every_1_seconds, daemon=True)
    thread_1_s.start()

    sys.exit(app.exec_())
