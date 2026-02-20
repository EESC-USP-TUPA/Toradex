import json
import time
import asyncio
import threading
import logging
from foxglove_websocket.server import FoxgloveServer


class FoxgloveSender:
    def __init__(self, port=8765):
        self.port = port
        self.server = None
        self.loop = None
        self.channels = {}  # topic -> channel_id
        self.logger = logging.getLogger("FoxgloveSender")

    # ======================================================
    # START SERVER
    # ======================================================

    def start(self):
        self.loop = asyncio.new_event_loop()

        thread = threading.Thread(
            target=self._run_server,
            daemon=True
        )
        thread.start()

        self.logger.info(f"📡 Foxglove server iniciando na porta {self.port}")

    def _run_server(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._async_main())

    async def _async_main(self):
        async with FoxgloveServer(
            "0.0.0.0",
            self.port,
            "CAN Signals"
        ) as server:
            self.server = server
            self.logger.info("✅ Foxglove ONLINE")
            await asyncio.Future()  # mantém o servidor vivo

    # ======================================================
    # SEND SIGNAL (COMPATÍVEL COM SEU CANDecoder)
    # ======================================================

    def send_message(self, topic, payload):
        """
        topic: string  -> ex: "/0x90/APPS1raw"
        payload: dict -> {"value": ..., "unit": "", "timestamp_ns": ...}
        """
        if self.server is None or self.loop is None:
            return

        timestamp_ns = payload.get("timestamp_ns", time.time_ns())

        asyncio.run_coroutine_threadsafe(
            self._ensure_channel_and_send(topic, payload, timestamp_ns),
            self.loop
        )

    async def _ensure_channel_and_send(self, topic, payload, timestamp_ns):
        try:
            # Cria canal se ainda não existir
            if topic not in self.channels:
                channel_id = await self.server.add_channel(
                    {
                        "topic": topic,
                        "encoding": "json",
                        "schemaName": "Signal",
                        "schema": json.dumps({
                            "type": "object",
                            "properties": {
                                "value": {
                                    "type": "number"
                                },
                                "unit": {
                                    "type": "string"
                                }
                            },
                            "required": ["value"]
                        })
                    }
                )
                self.channels[topic] = channel_id

            # Envia mensagem
            await self.server.send_message(
                self.channels[topic],
                timestamp_ns,  # timestamp usado pelo Foxglove
                json.dumps(payload).encode("utf-8")
            )

        except Exception as e:
            self.logger.error(f"Erro Foxglove ({topic}): {e}")
