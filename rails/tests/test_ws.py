import asyncio
import os

import websockets
from dotenv import load_dotenv

load_dotenv()

DOMAIN = os.getenv("RAILS_DOMAIN", "rails49.org")
WS_URL = f"wss://mqtt.{DOMAIN}/mqtt"


async def test_ws_connection():
    try:
        # Use a subprotocol 'mqtt' which NanoMQ expects
        async with websockets.connect(WS_URL, subprotocols=["mqtt"]) as _:
            print(f"✅ WebSocket connection to {WS_URL} established!")
            return True
    except Exception as e:
        print(f"❌ WebSocket connection to {WS_URL} failed: {e}")
        return False


if __name__ == "__main__":
    result = asyncio.run(test_ws_connection())
    if not result:
        exit(1)
