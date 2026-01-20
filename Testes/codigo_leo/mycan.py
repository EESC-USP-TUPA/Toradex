import can


class MyCAN:
    def __init__(self, channel='can0', bustype='socketcan'):
        self.bus = can.interface.Bus(channel=channel, bustype=bustype)

    def receive_can_messages(self):
        while True:
            message = self.bus.recv()
            if message is not None:
                self.process_can_message(message)
                print("Mensagem chegou")
                print(message)

    def process_can_message(self, message, data):
        if message.arbitration_id == 0x080:
            data['AccelPedal'] = message.data[0] | (message.data[1] << 8)
            data['BrakePedal'] = message.data[2] | (message.data[3] << 8)
            data['SteerAngle'] = message.data[4] | (message.data[5] << 8)
            data['Flags'] = message.data[6]
        elif message.arbitration_id == 0x081:
            data['InterruptBtn'] = message.data[0]
        elif message.arbitration_id == 0x180:
            data['APPS2_L'] = message.data[0] | (message.data[1] << 8)
            data['Susp_L'] = message.data[2] | (message.data[3] << 8)
            data['WheelRPM_L'] = message.data[4] | (message.data[5] << 8)
            data['BrakeTemp_L'] = message.data[6] | (message.data[7] << 8)
        elif message.arbitration_id == 0x181:
            data['Pitot_L'] = message.data[0] | (message.data[1] << 8)
        elif message.arbitration_id == 0x280:
            data['APPS2_R'] = message.data[0] | (message.data[1] << 8)
            data['Susp_R'] = message.data[2] | (message.data[3] << 8)
            data['WheelRPM_R'] = message.data[4] | (message.data[5] << 8)
            data['BrakeTemp_R'] = message.data[6] | (message.data[7] << 8)
        elif message.arbitration_id == 0x281:
            data['Pitot_R'] = message.data[0] | (message.data[1] << 8)
        elif message.arbitration_id == 0x050:
            data['Inv_SW_L'] = message.data[0]
            data['Inv_SW_R'] = message.data[1]
            data['Inv_AN_L'] = message.data[2]
            data['Inv_AN_R'] = message.data[3]
            data['BuzzerFlag'] = message.data[4]
            data['BreaklightFlag'] = message.data[5]
        elif message.arbitration_id == 0x380:
            data['MotorRPM1_BL'] = message.data[0] | (message.data[1] << 8)
            data['WheelRPM_BL'] = message.data[2] | (message.data[3] << 8)
            data['Susp_BL'] = message.data[4] | (message.data[5] << 8)
        elif message.arbitration_id == 0x381:
            data['MotorTemp2_BL'] = message.data[0]
            data['InvTemp2_BL'] = message.data[1]
            data['TransTemp2_BL'] = message.data[2]
            data['BrakeTemp4_BL'] = message.data[3] | (message.data[4] << 8)
        elif message.arbitration_id == 0x382:
            data['GPS_BL'] = message.data.hex()  # Assumindo que GPS é uma sequência de bytes
        elif message.arbitration_id == 0x480:
            data['MotorRPM2_BR'] = message.data[0] | (message.data[1] << 8)
            data['WheelRPM_BR'] = message.data[2] | (message.data[3] << 8)
            data['Susp_BR'] = message.data[4] | (message.data[5] << 8)
        elif message.arbitration_id == 0x481:
            data['MotorTemp2_BR'] = message.data[0]
            data['InvTemp2_BR'] = message.data[1]
            data['TransTemp2_BR'] = message.data[2]
            data['BrakeTemp4_BR'] = message.data[3] | (message.data[4] << 8)
        elif message.arbitration_id == 0x482:
            data['Accel1_BR'] = list(message.data[:6])
        elif message.arbitration_id == 0x484:
            data['Accel2_BR'] = list(message.data[:6])
        elif message.arbitration_id == 0x081:
            data['InvShutdown'] = message.data[0]
        



