#!/usr/bin/env python3
import serial
import pynmea2
import time
import sys

SERIAL_PORT = "/dev/verdin-uart1"
BAUDRATE = 9600

def main():
    try:
        ser = serial.Serial(
            SERIAL_PORT,
            BAUDRATE,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1
        )
    except serial.SerialException as e:
        print(f"Erro abrindo UART: {e}", file=sys.stderr)
        sys.exit(1)

    print("GPS NEO-M8N iniciado")
    print(f"Porta: {SERIAL_PORT} @ {BAUDRATE} bps\n")

    while True:
        try:
            raw = ser.readline()

            if not raw:
                continue

            line = raw.decode("utf-8", "ignore").strip()

            # Aceita GPS + GN (multi-constelação)
            if not line.startswith(("$GNGGA", "$GPGGA")):
                continue

            try:
                msg = pynmea2.parse(line)
            except pynmea2.ParseError as e:
                print("Erro NMEA:", e)
                continue

            # Timestamp
            if msg.timestamp:
                time_str = msg.timestamp.strftime("%H:%M:%S")
            else:
                time_str = "--:--:--"

            print(f"Hora UTC: {time_str}")

            # Fix quality
            fix_quality = int(msg.gps_qual) if msg.gps_qual else 0
            sats = int(msg.num_sats) if msg.num_sats else 0

            print(f"Fix quality: {fix_quality}")
            print(f"Satélites: {sats}")

            if fix_quality > 0 and msg.lat and msg.lon:
                print(f"Latitude : {msg.lat} {msg.lat_dir}")
                print(f"Longitude: {msg.lon} {msg.lon_dir}")
                print("STATUS: FIX OK ✅")
            else:
                print("STATUS: sem fix de GPS ⏳")

            print("-" * 40)

        except KeyboardInterrupt:
            print("\nEncerrando aplicação.")
            break

        except Exception as e:
            # Nunca derruba o container
            print("Erro inesperado:", e, file=sys.stderr)
            time.sleep(1)

    ser.close()


if __name__ == "__main__":
    main()
