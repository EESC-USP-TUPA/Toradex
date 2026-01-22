import struct
import time
import logging
from datetime import datetime


class CANDecoder:
    def __init__(self, foxglove_sender, signal_callback=None):
        self.foxglove = foxglove_sender
        self.signal_callback = signal_callback
        self.logger = logging.getLogger("CANDecoder")

    # =====================================================
    # DISPATCH
    # =====================================================

    def handle_message(self, msg):
        can_id = msg.arbitration_id

        if can_id == 0x03B:
            self._decode_0x03b(msg)
        elif can_id == 0x3CB:
            self._decode_0x3cb(msg)
        elif can_id == 0x90:
            self._decode_0x90(msg)
        elif can_id == 0x91:
            self._decode_0x91(msg)
        elif can_id == 0x6B2:
            self._decode_0x6b2(msg)
        elif can_id == 0x587:
            self._decode_0x587(msg)
        elif can_id == 0x586:
            self._decode_0x586(msg)
        elif can_id == 0x585:
            self._decode_0x585(msg)
        elif can_id == 0x584:
            self._decode_0x584(msg)

    # =====================================================
    # HELPER
    # =====================================================

    def _publish(self, topic, value, unit):
        timestamp_ns = time.time_ns()
        time_human = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        payload = {
            "value": value,
            "unit": unit,
            "timestamp_ns": timestamp_ns,
            "time_human": time_human
        }

        # Envio RAW para Foxglove
        self.foxglove.send_message(topic, payload)

        # Callback para média móvel
        if self.signal_callback:
            self.signal_callback({
                "name": topic,
                "value": value,
                "unit": unit,
                "timestamp_ns": timestamp_ns,
                "time_human": time_human
            })

    # =====================================================
    # DECODERS
    # =====================================================

    def _decode_0x90(self, msg):
        data = msg.data
        apps1 = struct.unpack(">H", data[0:2])[0]
        apps2 = struct.unpack(">H", data[2:4])[0]

        self._publish("/0x90/APPS1raw", apps1, "")
        self._publish("/0x90/APPS2raw", apps2, "")

    def _decode_0x91(self, msg):
        data = msg.data
        bse1 = struct.unpack(">H", data[0:2])[0]
        bse2 = struct.unpack(">H", data[2:4])[0]
        vol = struct.unpack(">H", data[4:6])[0]

        self._publish("/0x91/BSE1raw", bse1, "")
        self._publish("/0x91/BSE2raw", bse2, "")
        self._publish("/0x91/VOL", vol, "")

    def _decode_0x03b(self, msg):
        data = msg.data
        current = struct.unpack(">h", data[0:2])[0] * 0.1
        voltage = struct.unpack(">h", data[2:4])[0] * 0.1

        self._publish("/BMS1/pack_current", current, "A")
        self._publish("/BMS1/pack_voltage", voltage, "V")

    def _decode_0x3cb(self, msg):
        data = msg.data
        self._publish("/BMS2/PackDCL", data[0] * 0.1, "kW")
        self._publish("/BMS2/PackCCL", data[1], "A")
        self._publish("/BMS2/simulatedSOC", data[3], "")

    def _decode_0x6b2(self, msg):
        data = msg.data
        self._publish("/BMS3/PackSOC", data[1], "%")
        self._publish("/BMS3/PackOpenVoltage", struct.unpack(">H", data[4:6])[0], "V")

    def _decode_0x587(self, msg):
        rpm = struct.unpack(">H", msg.data[0:2])[0]
        self._publish("/Wheel/RPM_L", rpm, "RPM")

    def _decode_0x586(self, msg):
        rpm = struct.unpack(">H", msg.data[0:2])[0]
        self._publish("/Wheel/RPM_R", rpm, "RPM")

    def _decode_0x585(self, msg):
        rpm = struct.unpack(">H", msg.data[0:2])[0]
        self._publish("/Motor/RPM_R", rpm, "RPM")

    def _decode_0x584(self, msg):
        rpm = struct.unpack(">H", msg.data[0:2])[0]
        self._publish("/Motor/RPM_L", rpm, "RPM")
