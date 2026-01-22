from data_logger import DataLogger
from foxglove_sender import FoxgloveSender
from media_movel import MediaMovelProcessor
from tcp_can_receiver import TCPCANReceiver
from can_decoder import CANDecoder


def main():
    data_logger = DataLogger()

    fox_sender = FoxgloveSender(port=8765)
    fox_sender.start()

    media_movel = MediaMovelProcessor(fox_sender)

    decoder = CANDecoder(
        fox_sender,
        signal_callback=media_movel.process_signal
    )

    can_receiver = TCPCANReceiver(port=5000)

    def message_handler(message):
        processed = data_logger.process_message(message)
        data_logger.log_data(processed)

        decoder.handle_message(message)

    can_receiver.start_receiving(message_handler)


if __name__ == "__main__":
    main()
