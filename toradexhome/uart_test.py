import serial

ser = serial.Serial("/dev/ttymxc1", 9600, timeout=1)

while True:
    data = ser.read(100)
    if data:
        print(data)

