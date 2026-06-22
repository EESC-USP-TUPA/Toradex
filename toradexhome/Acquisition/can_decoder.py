import struct


class CANDecoderCore:

    def __init__(self):
        self.handlers = {
            0x050: self._decode_0x050,
            0x100: self._decode_0x100,
            0x101: self._decode_0x101,
            0x150: self._decode_0x150,
            0x151: self._decode_0x151,
            0x200: self._decode_0x200,
            0x201: self._decode_0x201,
            0x202: self._decode_0x202,
            0x250: self._decode_0x250,
            0x251: self._decode_0x251,
            0x300: self._decode_0x300,
            0x301: self._decode_0x301,
            0x302: self._decode_0x302,
            0x303: self._decode_0x303,
            0x304: self._decode_0x304,
            0x305: self._decode_0x305,
            0x500: self._decode_0x500,
        }

    # ============================================
    # Main entry point
    # ============================================
    def decode(self, msg):
        handler = self.handlers.get(msg.arbitration_id)
        if handler:
            return handler(msg)
        return []

    # ============================================
    # Individual decoders
    # ============================================

    def _decode_0x050(self, msg):
        current = struct.unpack(">h", msg.data[0:2])[0] * 0.1
        voltage = struct.unpack(">h", msg.data[2:4])[0] * 0.1

        return [
            {"name": "/BMS1/pack_current", "value": current, "unit": "A"},
            {"name": "/BMS1/pack_voltage", "value": voltage, "unit": "V"}
        ]

    def _decode_0x100(self, msg):
        apps1 = struct.unpack(">H", msg.data[0:2])[0]
        apps2 = struct.unpack(">H", msg.data[2:4])[0]

        return [
            {"name": "/0x100/APPS1raw", "value": apps1, "unit": ""},
            {"name": "/0x100/APPS2raw", "value": apps2, "unit": ""}
        ]

    def _decode_0x101(self, msg):
        bse1 = struct.unpack(">H", msg.data[0:2])[0]
        bse2 = struct.unpack(">H", msg.data[2:4])[0]
        vol  = struct.unpack(">H", msg.data[4:6])[0]

        return [
            {"name": "/0x101/BSE1raw", "value": bse1, "unit": ""},
            {"name": "/0x101/BSE2raw", "value": bse2, "unit": ""},
            {"name": "/0x101/VOL", "value": vol, "unit": ""}
        ]

    def _decode_0x150(self, msg):
        return [
            {"name": "/BMS2/PackDCL", "value": msg.data[0] * 0.1, "unit": "A"},
            {"name": "/BMS2/PackCCL", "value": msg.data[1], "unit": "A"},
            {"name": "/BMS2/PackFlag", "value": msg.data[2], "unit": ""},
            {"name": "/BMS2/simulatedSOC", "value": msg.data[3], "unit": "%"},
            {"name": "/BMS2/PackHighTempCell", "value": msg.data[4], "unit": "°C"},
            {"name": "/BMS2/PackLowTempCell", "value": msg.data[5], "unit": "°C"},
        ]
    
    def _decode_0x151(self, msg):
        soc = msg.data[1]
        open_voltage = struct.unpack(">H", msg.data[4:6])[0]

        return [
            {"name": "/BMS3/PackSOC", "value": soc, "unit": "%"},
            {"name": "/BMS3/PackOpenVoltage", "value": open_voltage, "unit": "V"}
        ]
    
    def _decode_0x200(self, msg):
        accelx = struct.unpack(">H", msg.data[0:2])[0]
        accely = struct.unpack(">H", msg.data[2:4])[0]
        accelz = struct.unpack(">H", msg.data[4:6])[0]

        return [
            {"name": "/IMU1/AccelX", "value": accelx, "unit": "A"},
            {"name": "/IMU1/AccelY", "value": accely, "unit": "A"},
            {"name": "/IMU1/AccelZ", "value": accelz, "unit": "A"}
        ]

    def _decode_0x201(self, msg):
        gyrox = struct.unpack(">H", msg.data[0:2])[0]
        gyroy = struct.unpack(">H", msg.data[2:4])[0]
        gyroz = struct.unpack(">H", msg.data[4:6])[0]

        return [
            {"name": "/IMU2/GyroX", "value": gyrox, "unit": "rad/s"},
            {"name": "/IMU2/GyroY", "value": gyroy, "unit": "rad/s"},
            {"name": "/IMU2/GyroZ", "value": gyroz, "unit": "rad/s"}
        ]

    def _decode_0x202(self, msg):
        yaw = struct.unpack(">H", msg.data[0:2])[0]
        pitch = struct.unpack(">H", msg.data[2:4])[0]
        roll = struct.unpack(">H", msg.data[4:6])[0]

        return [
            {"name": "/IMU3/Yaw", "value": yaw, "unit": "°"},
            {"name": "/IMU3/Pitch", "value": pitch, "unit": "°"},
            {"name": "/IMU3/Roll", "value": roll, "unit": "°"}
        ]
    
    def _decode_0x250(self, msg):
        tempL_transmissao = struct.unpack(">H", msg.data[0:2])[0]
        tempL_inversor = struct.unpack(">H", msg.data[2:4])[0]
        tempL_motor = struct.unpack(">H", msg.data[4:6])[0]

        return [
            {"name": "/TEMP1/TempTransmissaoL", "value": tempL_transmissao, "unit": "°C"},
            {"name": "/TEMP1/TempInversorL", "value": tempL_inversor, "unit": "°C"},
            {"name": "/TEMP1/TempMotorL", "value": tempL_motor, "unit": "°C"}
        ]
    
    def _decode_0x251(self, msg):
        tempR_transmissao = struct.unpack(">H", msg.data[0:2])[0]
        tempR_inversor = struct.unpack(">H", msg.data[2:4])[0]
        tempR_motor = struct.unpack(">H", msg.data[4:6])[0]

        return [
            {"name": "/TEMP2/TempTransmissaoR", "value": tempR_transmissao, "unit": "°C"},
            {"name": "/TEMP2/TempInversorR", "value": tempR_inversor, "unit": "°C"},
            {"name": "/TEMP2/TempMotorR", "value": tempR_motor, "unit": "°C"}
        ]
    
    def _decode_0x300(self, msg):
        rpm = struct.unpack(">H", msg.data[0:2])[0]
        return [{"name": "/MOTOR/RPM_L", "value": rpm, "unit": "RPM"}]
    
    def _decode_0x301(self, msg):
        rpm = struct.unpack(">H", msg.data[0:2])[0]
        return [{"name": "/MOTOR/RPM_R", "value": rpm, "unit": "RPM"}]

    def _decode_0x302(self, msg):
        rpm = struct.unpack(">H", msg.data[0:2])[0]
        return [{"name": "/FRONTWHEEL/RPM_L", "value": rpm, "unit": "RPM"}]

    def _decode_0x303(self, msg):
        rpm = struct.unpack(">H", msg.data[0:2])[0]
        return [{"name": "/FRONTWHEEL/RPM_R", "value": rpm, "unit": "RPM"}]

    def _decode_0x304(self, msg):
        rpm = struct.unpack(">H", msg.data[0:2])[0]
        return [{"name": "/BACKWHEEL/RPM_L", "value": rpm, "unit": "RPM"}]

    def _decode_0x305(self, msg):
        rpm = struct.unpack(">H", msg.data[0:2])[0]
        return [{"name": "/BACKWHEEL/RPM_R", "value": rpm, "unit": "RPM"}]
    
    def _decode_0x500(self, msg):
        return [
            {"name": "/CHANNEL/Number", "value": msg.data[0], "unit": ""},
            {"name": "/CHANNEL/Current", "value": msg.data[1], "unit": "A"},
            {"name": "/CHANNEL/Voltage", "value": msg.data[2], "unit": "V"},
        ]

