import struct
import time
import logging

class CANDecoder:
    def __init__(self, foxglove_sender):
        self.foxglove = foxglove_sender
        self.logger = logging.getLogger("CANDecoder")

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

    def _decode_0x90(self, msg):
        data = msg.data
        timestamp = time.time_ns()

        # Bytes 0–1: apps1raw (int16 unsigned)
        apps1raw = struct.unpack(">H", data[0:2])[0]

        # Bytes 2–3: apps2raw (int16 unsigned)
        apps2raw = struct.unpack(">H", data[2:4])[0]

        # Byte 4: erros (uint8)
        erros0x90 = data[4]

        # Byte 4: contador (uint8)
        contador0x90 = data[5]

        self.foxglove.send_message(
            "/0x90/APPS1raw",
            {
                "value": apps1raw,
                "unit": "",
                "timestamp_ns": timestamp
            }
        )

        self.foxglove.send_message(
            "/0x90/APPS2raw",
            {
                "value": apps2raw,
                "unit": "",
                "timestamp_ns": timestamp
            }
        )

        self.foxglove.send_message(
            "/0x90/erros",
            {
                "value": erros0x90,
                "unit": "",
                "timestamp_ns": timestamp
            }
        )

        self.foxglove.send_message(
            "/0x90/contador",
            {
                "value": contador0x90,
                "unit": "",
                "timestamp_ns": timestamp
            }
        )

    def _decode_0x91(self, msg):
        data = msg.data
        timestamp = time.time_ns()

        # Bytes 0–1: bse1raw (int16 unsigned)
        bse1raw = struct.unpack(">H", data[0:2])[0]

        # Bytes 2–3: bse2raw (int16 unsigned)
        bse2raw = struct.unpack(">H", data[2:4])[0]

        # Bytes 4–5: VolRaw (int16 unsigned)
        VolRaw = struct.unpack(">H", data[4:6])[0]

        # Byte 6: contador (uint8)
        contador0x91 = data[6]

        self.foxglove.send_message(
            "/0x91/BSE1raw",
            {
                "value": bse1raw,
                "unit": "",
                "timestamp_ns": timestamp
            }
        )

        self.foxglove.send_message(
            "/0x91/BSE2raw",
            {
                "value": bse2raw,
                "unit": "",
                "timestamp_ns": timestamp
            }
        )

        self.foxglove.send_message(
            "/0x91/VOL",
            {
                "value": VolRaw,
                "unit": "",
                "timestamp_ns": timestamp
            }
        )

        self.foxglove.send_message(
            "/0x91/contador",
            {
                "value": contador0x91,
                "unit": "",
                "timestamp_ns": timestamp
            }
        )


    def _decode_0x03b(self, msg):
        data = msg.data
        timestamp = time.time_ns()

        # Bytes 0–1: PackCurrent (int16 signed)
        PackCurrent = struct.unpack(">h", data[0:2])[0]

        # Bytes 2–3: PackVoltage (int16 signed)
        PackVoltage = struct.unpack(">h", data[2:4])[0]

        # Byte 4: checksum (uint8)
        checksum1 = data[4]

        self.foxglove.send_message(
            "/BMS1/pack_current",
            {
                "value": PackCurrent * 0.1,   # escala real aqui
                "unit": "A",
                "timestamp_ns": timestamp
            }
        )

        self.foxglove.send_message(
            "/BMS1/pack_voltage",
            {
                "value": PackVoltage * 0.1,
                "unit": "V",
                "timestamp_ns": timestamp
            }
        )

        self.foxglove.send_message(
            "/BMS1/checksum",
            {
                "value": checksum1,
                "unit": "",
                "timestamp_ns": timestamp
            }
        )

    def _decode_0x3cb(self, msg):
        data = msg.data
        timestamp = time.time_ns()

        # Byte 0: Pack DCL (uint8)
        PackDCL = data[0]

        # Byte 1: Pack CCL (uint8)
        PackCCL = data[1]

        # Byte 3: Simulated SOC (uint8)
        simulatedSOC = data[3]

        # Byte 4: High Temperature Cell (uint8)
        HTC = data[4]

        # Byte 7: Low Temperature Cell (uint8)
        LTC = data[5]

        # Byte 6: CheckSum (uint8)
        checksum2 = data[6]

        self.foxglove.send_message(
            "/BMS2/PackDCL",
            {
                "value": PackDCL * 0.1,
                "unit": "kW",
                "timestamp_ns": timestamp
            }
        )

        self.foxglove.send_message(
            "/BMS2/PackCCL",
            {
                "value": PackCCL,
                "unit": "A",
                "timestamp_ns": timestamp
            }
        )

        self.foxglove.send_message(
            "/BMS2/simulatedSOC",
            {
                "value": simulatedSOC,
                "unit": "",
                "timestamp_ns": timestamp
            }
        )

        self.foxglove.send_message(
            "/BMS2/HighTempCell",
            {
                "value": HTC,
                "unit": "C",
                "timestamp_ns": timestamp
            }
        )

        self.foxglove.send_message(
            "/BMS2/LowTempCell",
            {
                "value": LTC,
                "unit": "C",
                "timestamp_ns": timestamp
            }
        )

        self.foxglove.send_message(
            "/BMS2/Checksum2",
            {
                "value": checksum2,
                "unit": "",
                "timestamp_ns": timestamp
            }
        )

    def _decode_0x6b2(self, msg):
        data = msg.data
        timestamp = time.time_ns()

        # Byte 0: relaysatate (uint8)
        RelayState = data[0]

        # Byte 1: PackSOC (uint8)
        PackSOC = data[1]

        # Bytes 2–3: Resistence (int16 unsigned)
        Resistence = struct.unpack(">H", data[2:4])[0]

        # Bytes 4–5: PackOpenVoltage (int16 unsigned)
        PackOpenVoltage = struct.unpack(">H", data[4:6])[0]

        # Byte 6: Simulated SOC (uint8)
        PackAmphours = data[6]

        # Byte 7: High Temperature Cell (uint8)
        Checksum3 = data[7]

        self.foxglove.send_message(
            "/BMS3/RelayState",
            {
                "value": RelayState,
                "unit": "",
                "timestamp_ns": timestamp
            }
        )

        self.foxglove.send_message(
            "/BMS3/PackSOC",
            {
                "value": PackSOC,
                "unit": "",
                "timestamp_ns": timestamp
            }
        )

        self.foxglove.send_message(
            "/BMS3/Resistence",
            {
                "value": Resistence,
                "unit": "ohms?",
                "timestamp_ns": timestamp
            }
        )

        self.foxglove.send_message(
            "/BMS3/PackOpenVoltage",
            {
                "value": PackOpenVoltage,
                "unit": "V",
                "timestamp_ns": timestamp
            }
        )

        self.foxglove.send_message(
            "/BMS3/PackAmphours",
            {
                "value": PackAmphours,
                "unit": "A*h",
                "timestamp_ns": timestamp
            }
        )

        self.foxglove.send_message(
            "/BMS3/Checksum3",
            {
                "value": Checksum3,
                "unit": "",
                "timestamp_ns": timestamp
            }
        )

    def _decode_0x587(self, msg):
        data = msg.data
        timestamp = time.time_ns()

        # Bytes 0–1: RPMRodaL (int16 unsigned)
        RMPRodaL = struct.unpack(">H", data[0:2])[0]

        # Byte 3: contador (uint8)
        contador0x587 = data[3]

        self.foxglove.send_message(
            "/0x587/RMP Roda L",
            {
                "value": RMPRodaL,
                "unit": "RPM",
                "timestamp_ns": timestamp
            }
        )

        self.foxglove.send_message(
            "/0x587/contador",
            {
                "value": contador0x587,
                "unit": "",
                "timestamp_ns": timestamp
            }
        )

    def _decode_0x586(self, msg):
        data = msg.data
        timestamp = time.time_ns()

        # Bytes 0–1: RPMRodaR (int16 unsigned)
        RMPRodaR = struct.unpack(">H", data[0:2])[0]

        # Byte 3: contador (uint8)
        contador0x586 = data[3]

        self.foxglove.send_message(
            "/0x586/RMP Roda R",
            {
                "value": RMPRodaR,
                "unit": "RPM",
                "timestamp_ns": timestamp
            }
        )

        self.foxglove.send_message(
            "/0x586/contador",
            {
                "value": contador0x586,
                "unit": "",
                "timestamp_ns": timestamp
            }
        )

    def _decode_0x585(self, msg):
        data = msg.data
        timestamp = time.time_ns()

        # Bytes 0–1: RPMMotorR (int16 unsigned)
        RMPMotorR = struct.unpack(">H", data[0:2])[0]

        # Byte 3: contador (uint8)
        contador0x585 = data[3]

        self.foxglove.send_message(
            "/0x585/RMP Motor R",
            {
                "value": RMPMotorR,
                "unit": "RPM",
                "timestamp_ns": timestamp
            }
        )

        self.foxglove.send_message(
            "/0x585/contador",
            {
                "value": contador0x585,
                "unit": "",
                "timestamp_ns": timestamp
            }
        )

    def _decode_0x584(self, msg):
        data = msg.data
        timestamp = time.time_ns()

        # Bytes 0–1: RPMMotorL (int16 unsigned)
        RMPMotorL = struct.unpack(">H", data[0:2])[0]

        # Byte 3: contador (uint8)
        contador0x584 = data[3]

        self.foxglove.send_message(
            "/0x584/RMP Motor L",
            {
                "value": RMPMotorL,
                "unit": "RPM",
                "timestamp_ns": timestamp
            }
        )

        self.foxglove.send_message(
            "/0x587/contador",
            {
                "value": contador0x584,
                "unit": "",
                "timestamp_ns": timestamp
            }
        )

