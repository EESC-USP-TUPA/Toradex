import struct
import time


class CANDecoderCore:

    def decode(self, msg):
        can_id = msg.arbitration_id
        signals = []

        if can_id == 0x03B:
            current = struct.unpack(">h", msg.data[0:2])[0] * 0.1
            voltage = struct.unpack(">h", msg.data[2:4])[0] * 0.1

            signals.append(("/BMS1/pack_current", current))
            signals.append(("/BMS1/pack_voltage", voltage))

        elif can_id == 0x587:
            rpm = struct.unpack(">H", msg.data[0:2])[0]
            signals.append(("/Wheel/RPM_L", rpm))

        elif can_id == 0x586:
            rpm = struct.unpack(">H", msg.data[0:2])[0]
            signals.append(("/Wheel/RPM_R", rpm))

        return signals
