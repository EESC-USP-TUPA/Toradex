import time
import smbus2

# -----------------------------------------------------------------------------
# Configuração I2C
# -----------------------------------------------------------------------------
I2C_BUS = "/dev/verdin-i2c1"
BNO055_ADDRESS = 0x28  # ou 0x29

bus = smbus2.SMBus(I2C_BUS)

# -----------------------------------------------------------------------------
# Registradores BNO055 (datasheet oficial)
# -----------------------------------------------------------------------------
PAGE_ID        = 0x07
OPR_MODE       = 0x3D
PWR_MODE       = 0x3E
SYS_TRIGGER    = 0x3F
UNIT_SEL       = 0x3B

# Dados
ACCEL_DATA_X_LSB = 0x08
GYRO_DATA_X_LSB  = 0x14
EULER_H_LSB      = 0x1A
CALIB_STAT       = 0x35

# Modos de operação
CONFIGMODE = 0x00
NDOF_MODE  = 0x0C

# -----------------------------------------------------------------------------
# Funções auxiliares
# -----------------------------------------------------------------------------
def write_reg(reg, value):
    bus.write_byte_data(BNO055_ADDRESS, reg, value)

def read_reg(reg):
    return bus.read_byte_data(BNO055_ADDRESS, reg)

def read_vector(lsb_reg, scale):
    data = bus.read_i2c_block_data(BNO055_ADDRESS, lsb_reg, 6)

    x = (data[1] << 8) | data[0]
    y = (data[3] << 8) | data[2]
    z = (data[5] << 8) | data[4]

    if x > 32767: x -= 65536
    if y > 32767: y -= 65536
    if z > 32767: z -= 65536

    return (x / scale, y / scale, z / scale)

# -----------------------------------------------------------------------------
# Inicialização do BNO055
# -----------------------------------------------------------------------------
print("Inicializando BNO055...")

# Modo CONFIG
write_reg(OPR_MODE, CONFIGMODE)
time.sleep(0.03)

# Página 0
write_reg(PAGE_ID, 0x00)

# Power mode normal
write_reg(PWR_MODE, 0x00)
time.sleep(0.01)

# Unidades:
# accel: m/s² | gyro: rad/s | euler: graus
write_reg(UNIT_SEL, 0x00)

# Modo NDOF (fusão completa)
write_reg(OPR_MODE, NDOF_MODE)
time.sleep(0.05)

print("BNO055 pronto")

# -----------------------------------------------------------------------------
# Loop principal
# -----------------------------------------------------------------------------
while True:
    try:
        accel = read_vector(ACCEL_DATA_X_LSB, 100.0)   # m/s²
        gyro  = read_vector(GYRO_DATA_X_LSB, 900.0)    # rad/s
        euler = read_vector(EULER_H_LSB, 16.0)         # graus

        calib = read_reg(CALIB_STAT)
        sys   = (calib >> 6) & 0x03
        gyro_c= (calib >> 4) & 0x03
        accel_c = (calib >> 2) & 0x03
        mag   = calib & 0x03

        print(
            f"Accel [m/s²] X={accel[0]:6.2f} Y={accel[1]:6.2f} Z={accel[2]:6.2f} | "
            f"Gyro [rad/s] X={gyro[0]:6.2f} Y={gyro[1]:6.2f} Z={gyro[2]:6.2f} | "
            f"Euler [°] H={euler[0]:6.2f} R={euler[1]:6.2f} P={euler[2]:6.2f} | "
            f"Calib SYS/G/A/M={sys}/{gyro_c}/{accel_c}/{mag}"
        )

    except Exception as e:
        print(f"Erro I2C: {e}")

    time.sleep(0.5)
