import serial
import socket
import json
import time
import struct
import requests
import os
from datetime import datetime

SERIAL_PORT = "/dev/ttymxc1"
BAUDRATE = 115200

TELEMETRY_HOST = "telemetry"
TELEMETRY_PORT = 5000

# ==========================================================
# UBX HELPER
# ==========================================================
def ubx_checksum(data):
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
    checksum = ubx_checksum(msg)
    ser.write(header + msg + checksum)

# ==========================================================
# CONFIGURATION
# ==========================================================
def configure_gnss(ser):
    # Enable all constellations
    send_ubx(ser, 0x06, 0x3E)

    # 10Hz update rate
    payload = struct.pack("<HHH", 100, 1, 1)
    send_ubx(ser, 0x06, 0x08, payload)

    # Enable NAV-PVT output
    payload = struct.pack("<BBH", 0x01, 0x07, 1)
    send_ubx(ser, 0x06, 0x01, payload)

# ==========================================================
# ASSISTNOW (A-GNSS)
# ==========================================================
def download_assistnow(ser):
    token = os.getenv("UBLOX_TOKEN")
    if not token:
        return

    url = f"https://online-live1.services.u-blox.com/GetOnlineData.ashx?token={token};gnss=gps,gal,bds,glo"
    r = requests.get(url)
    if r.status_code == 200:
        ser.write(r.content)

# ==========================================================
# UBX NAV-PVT PARSER
# ==========================================================
def parse_nav_pvt(data):
    lon = struct.unpack("<i", data[24:28])[0] * 1e-7
    lat = struct.unpack("<i", data[28:32])[0] * 1e-7
    height = struct.unpack("<i", data[32:36])[0] / 1000
    fix_type = data[20]
    num_sv = data[23]
    velN = struct.unpack("<i", data[48:52])[0] / 1000
    velE = struct.unpack("<i", data[52:56])[0] / 1000
    gSpeed = struct.unpack("<i", data[60:64])[0] / 1000
    heading = struct.unpack("<i", data[64:68])[0] * 1e-5

    return {
        "latitude": lat,
        "longitude": lon,
        "altitude": height,
        "fix_type": fix_type,
        "satellites": num_sv,
        "vel_north": velN,
        "vel_east": velE,
        "ground_speed": gSpeed,
        "heading": heading
    }

# ==========================================================
# MAIN LOOP
# ==========================================================
def main():
    ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)
    configure_gnss(ser)
    download_assistnow(ser)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((TELEMETRY_HOST, TELEMETRY_PORT))

    buffer = b""

    while True:
        buffer += ser.read(1024)

        while b"\xB5\x62" in buffer:
            start = buffer.find(b"\xB5\x62")
            if len(buffer) < start + 6:
                break

            length = struct.unpack("<H", buffer[start+4:start+6])[0]
            end = start + 6 + length + 2
            if len(buffer) < end:
                break

            msg = buffer[start:end]
            buffer = buffer[end:]

            cls = msg[2]
            id_ = msg[3]

            if cls == 0x01 and id_ == 0x07:  # NAV-PVT
                payload = msg[6:-2]
                data = parse_nav_pvt(payload)

                output = {
                    "type": "GNSS",
                    "data": data,
                    "timestamp_ns": time.time_ns(),
                    "time_human": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                }

                sock.sendall((json.dumps(output) + "\n").encode())

if __name__ == "__main__":
    main()
