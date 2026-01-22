import subprocess
from can_receiver import CANReceiver
from data_logger import DataLogger
from foxglove_sender import FoxgloveSender
from media_movel import MediaMovelProcessor

def start_candump(interface='can0'):
    try:
        subprocess.Popen(["candump", interface, "-t", "d", "-d"])
    except FileNotFoundError:
        print("Aviso: candump não encontrado")

def main():
    # Inicializa componentes
    data_logger = DataLogger()
    media_movel = MediaMovelProcessor()
    can_receiver = CANReceiver()

    fox_sender = FoxgloveSender(port=8765)
    fox_sender.start()

    start_candump()

    # Callback CAN
    def message_handler(message):
        # Logger RAW (TXT)
        processed = data_logger.process_message(message)
        data_logger.log_data(processed)

        # Média móvel + CSV
        media_movel.process_message(message)

        # Foxglove
        fox_sender.send_message(message)

    try:
        can_receiver.start_receiving(message_handler)
    except KeyboardInterrupt:
        print("Encerrando aplicação...")

if __name__ == "__main__":
    main()
