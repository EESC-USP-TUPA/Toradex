import asyncio
import json
import time
import websockets

# Endpoint do SEU device no SEU projeto Foxglove
ENDPOINT = "wss://ingest.cloud.foxglove.dev/v1/projects/prj_0e1YUpZX7FWbSt21/devices/dev_0e3FcAO7Wv1dPxkh"

# Token do device (NÃO compartilhar publicamente)
TOKEN = "fox_dt_raf8eqRyGddTYtXBl950smcO4Wshxg7T"


async def main():
    while True:
        try:
            print("Connecting...")
            async with websockets.client.connect(
                ENDPOINT,
                extra_headers={"Authorization": f"Bearer {TOKEN}"},
            ) as ws:
                print("✅ Connected to Foxglove!")

                i = 0
                while True:
                    i += 1
                    msg = {
                        "op": "publish",
                        "topic": "test_voltage",
                        "encoding": "json",
                        "data": {
                            "value": 390.0 + (i % 10),  # só pra variar um pouco o valor
                            "timestamp": time.time(),
                        },
                    }
                    await ws.send(json.dumps(msg))
                    print("Sent:", msg["data"])
                    await asyncio.sleep(0.1)

        except Exception as e:
            print("Connection lost:", repr(e))
            print("Retrying in 2s...")
            await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(main())

