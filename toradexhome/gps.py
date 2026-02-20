import serial
import pynmea2
import time

PORT = "/dev/ttymxc1"
BAUD = 9600

# -------------------------
# conectar GPS
# -------------------------
def connect_gps():
    while True:
        try:
            print("Conectando ao GPS (NEO-M8X)...")
            ser = serial.Serial(
                PORT,
                BAUD,
                timeout=1
            )
            print("GPS conectado!")
            return ser
        except Exception as e:
            print("Falha ao abrir UART:", e)
            time.sleep(2)

gps = connect_gps()

# -------------------------
# loop principal
# -------------------------
while True:
    try:
        line = gps.readline().decode('ascii', errors='replace').strip()

        # ignorar lixo
        if not line.startswith('$'):
            continue

        # -------- POSIÇÃO --------
        if line.startswith(('$GNRMC', '$GPRMC')):
            msg = pynmea2.parse(line)

            if msg.status == 'A':   # A = fix válido
                speed_kmh = float(msg.spd_over_grnd) * 1.852

                print("\nFIX GPS OK")
                print(f"Latitude : {msg.latitude:.6f}")
                print(f"Longitude: {msg.longitude:.6f}")
                print(f"Velocidade: {speed_kmh:.2f} km/h")
                print(f"Curso: {msg.true_course}°")
                print(f"Hora UTC: {msg.timestamp}")

        # -------- SATÉLITES --------
        elif line.startswith(('$GNGGA', '$GPGGA')):
            msg = pynmea2.parse(line)

            print(f"Satélites: {msg.num_sats} | Altitude: {msg.altitude} m")

    except serial.SerialException:
        print("\nGPS desconectou... reconectando\n")
        time.sleep(1)
        gps = connect_gps()

    except pynmea2.ParseError:
        pass

    except Exception as e:
        print("Erro:", e)
        time.sleep(1)
