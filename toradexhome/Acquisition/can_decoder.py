import struct


class CANDecoderCore:

    def __init__(self):
        self.handlers = {
            0x90: self._decode_0x90,
            0x91: self._decode_0x91,
            0x03B: self._decode_0x03B,
            0x3CB: self._decode_0x3CB,
            0x6B2: self._decode_0x6B2,
            0x587: self._decode_0x587,
            0x586: self._decode_0x586,
            0x585: self._decode_0x585,
            0x584: self._decode_0x584,
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

    def _decode_0x90(self, msg):
        apps1 = struct.unpack(">H", msg.data[0:2])[0]
        apps2 = struct.unpack(">H", msg.data[2:4])[0]

        return [
            {"name": "/0x90/APPS1raw", "value": apps1, "unit": ""},
            {"name": "/0x90/APPS2raw", "value": apps2, "unit": ""}
        ]

    def _decode_0x91(self, msg):
        bse1 = struct.unpack(">H", msg.data[0:2])[0]
        bse2 = struct.unpack(">H", msg.data[2:4])[0]
        vol  = struct.unpack(">H", msg.data[4:6])[0]

        return [
            {"name": "/0x91/BSE1raw", "value": bse1, "unit": ""},
            {"name": "/0x91/BSE2raw", "value": bse2, "unit": ""},
            {"name": "/0x91/VOL", "value": vol, "unit": ""}
        ]

    def _decode_0x03B(self, msg):
        current = struct.unpack(">h", msg.data[0:2])[0] * 0.1
        voltage = struct.unpack(">h", msg.data[2:4])[0] * 0.1

        return [
            {"name": "/BMS1/pack_current", "value": current, "unit": "A"},
            {"name": "/BMS1/pack_voltage", "value": voltage, "unit": "V"}
        ]

    def _decode_0x3CB(self, msg):
        return [
            {"name": "/BMS2/PackDCL", "value": msg.data[0] * 0.1, "unit": "A"},
            {"name": "/BMS2/PackCCL", "value": msg.data[1], "unit": "A"},
            {"name": "/BMS2/simulatedSOC", "value": msg.data[3], "unit": "%"}
        ]

    def _decode_0x6B2(self, msg):
        soc = msg.data[1]
        open_voltage = struct.unpack(">H", msg.data[4:6])[0]

        return [
            {"name": "/BMS3/PackSOC", "value": soc, "unit": "%"},
            {"name": "/BMS3/PackOpenVoltage", "value": open_voltage, "unit": "V"}
        ]

    def _decode_0x587(self, msg):
        rpm = struct.unpack(">H", msg.data[0:2])[0]
        return [{"name": "/Wheel/RPM_L", "value": rpm, "unit": "RPM"}]

    def _decode_0x586(self, msg):
        rpm = struct.unpack(">H", msg.data[0:2])[0]
        return [{"name": "/Wheel/RPM_R", "value": rpm, "unit": "RPM"}]

    def _decode_0x585(self, msg):
        rpm = struct.unpack(">H", msg.data[0:2])[0]
        return [{"name": "/Motor/RPM_R", "value": rpm, "unit": "RPM"}]

    def _decode_0x584(self, msg):
        rpm = struct.unpack(">H", msg.data[0:2])[0]
        return [{"name": "/Motor/RPM_L", "value": rpm, "unit": "RPM"}]
