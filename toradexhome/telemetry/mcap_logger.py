from mcap.writer import Writer
import json, time, os
from datetime import datetime

class MCAPLogger:

    def __init__(self):
        base_dir="/datalogger"
        os.makedirs(base_dir, exist_ok=True)

        filename=f"{base_dir}/telemetry_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.mcap"

        self.file=open(filename,"wb")
        self.writer=Writer(self.file)
        self.writer.start()

        self.channels={}
        self.schema_id=self.writer.register_schema(
            name="json",
            encoding="jsonschema",
            data=json.dumps({"type":"object"}).encode()
        )

    def write(self,topic,payload):

        if topic not in self.channels:
            cid=self.writer.register_channel(
                topic=topic,
                message_encoding="json",
                schema_id=self.schema_id
            )
            self.channels[topic]=cid

        ts=payload.get("timestamp_ns",time.time_ns())

        self.writer.add_message(
            channel_id=self.channels[topic],
            log_time=ts,
            publish_time=ts,
            data=json.dumps(payload).encode()
        )

    def close(self):
        self.writer.finish()
        self.file.close()
