import serial
import struct
import threading
import time
import logging

logger = logging.getLogger("NEO-M8N")

SERIAL_PORT = "/dev/ttymxc1"

# =========================================================
# UBX HELPERS
# =========================================================

def checksum(data):
    ck_a = 0
    ck_b = 0
    for b in data:
        ck_a = (ck_a + b) & 0xFF
        ck_b = (ck_b + ck_a) & 0xFF
    return bytes([ck_a, ck_b])


def send_ubx(ser, cls, id_, payload=b""):
    header = b"\xB5\x62"
    length = struct.pack("<H", len(payload))
    msg = bytes([cls, id_]) + length + payload
    ser.write(header + msg + checksum(msg))


# =========================================================
# CONFIGURATION SEQUENCE
# =========================================================

def configure_module():

    # Step 1 — connect at default 9600
    ser = serial.Serial(SERIAL_PORT, 9600, timeout=1)
    time.sleep(0.5)

    # Step 2 — set baudrate to 115200
    payload = struct.pack(
        "<BBHIIHHH",
        1,          # UART1
        0,
        0,
        0x000008D0, # 8N1
        115200,
        0x0001,     # UBX in
        0x0001,     # UBX out
        0
    )
    send_ubx(ser, 0x06, 0x00, payload)
    time.sleep(0.2)
    ser.close()

    # Step 3 — reopen at 115200
    ser = serial.Serial(SERIAL_PORT, 115200, timeout=1)
    time.sleep(0.5)

    # Step 4 — disable all NMEA
    for msg_id in range(0x00, 0x0F):
        send_ubx(ser, 0x06, 0x01, struct.pack("<BBH", 0xF0, msg_id, 0))

    # Step 5 — enable NAV-PVT only
    send_ubx(ser, 0x06, 0x01, struct.pack("<BBH", 0x01, 0x07, 1))

    # Step 6 — set update rate to 10Hz
    send_ubx(ser, 0x06, 0x08, struct.pack("<HHH", 100, 1, 1))

    # Optional — save to flash
    send_ubx(ser, 0x06, 0x09, b"\x00\x00\x00\x00\xFF\xFF\x00\x00\x00\x00\x00\x00")

    logger.info("GNSS configured: UBX NAV-PVT @ 10Hz 115200")

    return ser


# =========================================================
# NAV-PVT PARSER
# =========================================================

def parse_nav_pvt(data):

    lon = struct.unpack("<i", data[24:28])[0] * 1e-7
    lat = struct.unpack("<i", data[28:32])[0] * 1e-7
    height = struct.unpack("<i", data[32:36])[0] / 1000
    fix_type = data[20]
    num_sv = data[23]
    vel_n = struct.unpack("<i", data[48:52])[0] / 1000
    vel_e = struct.unpack("<i", data[52:56])[0] / 1000
    gspeed = struct.unpack("<i", data[60:64])[0] / 1000
    heading = struct.unpack("<i", data[64:68])[0] * 1e-5

    return lat, lon, height, fix_type, num_sv, vel_n, vel_e, gspeed, heading


# =========================================================
# START GNSS THREAD
# =========================================================

def start(callback):

    def loop():

        ser = configure_module()
        buffer = b""

        while True:

            buffer += ser.read(1024)

            while b"\xB5\x62" in buffer:

                start_idx = buffer.find(b"\xB5\x62")
                if len(buffer) < start_idx + 6:
                    break

                length = struct.unpack("<H", buffer[start_idx+4:start_idx+6])[0]
                end = start_idx + 6 + length + 2

                if len(buffer) < end:
                    break

                msg = buffer[start_idx:end]
                buffer = buffer[end:]

                if msg[2] == 0x01 and msg[3] == 0x07:

                    data = msg[6:-2]
                    lat, lon, alt, fix, sats, vn, ve, gs, hdg = parse_nav_pvt(data)

                    payload = {
                        "source": "gnss",
                        "timestamp_ns": time.time_ns(),
                        "signals": [
                            {"name": "/GNSS/latitude", "value": lat, "unit": "deg"},
                            {"name": "/GNSS/longitude", "value": lon, "unit": "deg"},
                            {"name": "/GNSS/altitude", "value": alt, "unit": "m"},
                            {"name": "/GNSS/fix_type", "value": fix, "unit": ""},
                            {"name": "/GNSS/satellites", "value": sats, "unit": ""},
                            {"name": "/GNSS/ground_speed", "value": gs, "unit": "m/s"},
                            {"name": "/GNSS/heading", "value": hdg, "unit": "deg"},
                            {"name": "/GNSS/vel_north", "value": vn, "unit": "m/s"},
                            {"name": "/GNSS/vel_east", "value": ve, "unit": "m/s"},
                        ]
                    }

                    callback(payload)

    threading.Thread(target=loop, daemon=True).start()
