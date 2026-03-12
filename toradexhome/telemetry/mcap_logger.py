import json
import time
import os
from datetime import datetime
from mcap.writer import Writer


class MCAPLogger:

    def __init__(self):
        base_dir = "/datalogger"
        os.makedirs(base_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{base_dir}/telemetry_{timestamp}.mcap"

        self.file = open(filename, "wb")
        self.writer = Writer(self.file)
        self.writer.start()

        self.channels = {}

        self.schema_id = self.writer.register_schema(
            name="json",
            encoding="jsonschema",
            data=json.dumps({"type": "object"}).encode()
        )

        print(f"MCAP recording started → {filename}")

    def write(self, topic, payload):

        if topic not in self.channels:
            channel_id = self.writer.register_channel(
                topic=topic,
                message_encoding="json",
                schema_id=self.schema_id
            )
            self.channels[topic] = channel_id

        timestamp = payload.get("timestamp_ns", time.time_ns())

        self.writer.add_message(
            channel_id=self.channels[topic],
            log_time=timestamp,
            publish_time=timestamp,
            data=json.dumps(payload).encode()
        )

        # force disk write so file size updates
        self.file.flush()
        os.fsync(self.file.fileno())

    def close(self):
        self.writer.finish()
        self.file.close()
