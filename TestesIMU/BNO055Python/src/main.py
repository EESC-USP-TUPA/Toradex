import time
import board
import busio
from adafruit_bno055 import BNO055_I2C

# Inicializa I2C
i2c = busio.I2C(board.SCL, board.SDA)

# Endereço padrão do BNO055 é 0x28
sensor = BNO055_I2C(i2c, address=0x28)

print("BNO055 inicializado")

while True:
    # Aceleração (m/s²)
    accel_x, accel_y, accel_z = sensor.acceleration

    # Giroscópio (rad/s)
    gyro_x, gyro_y, gyro_z = sensor.gyro

    # Orientação absoluta (graus)
    heading, roll, pitch = sensor.euler

    print(
        f"Accel: X={accel_x:.2f} Y={accel_y:.2f} Z={accel_z:.2f} m/s² | "
        f"Gyro: X={gyro_x:.2f} Y={gyro_y:.2f} Z={gyro_z:.2f} rad/s | "
        f"Euler: Heading={heading:.2f} Roll={roll:.2f} Pitch={pitch:.2f}"
    )

    time.sleep(0.5)
