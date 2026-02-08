import asyncio
import logging
import os
from typing import Set

import paho.mqtt.client as mqtt
import serial_asyncio

# Configuration
SERIAL_PORT = os.getenv("SERIAL_PORT", "/dev/ttyUSB0")
SERIAL_BAUD = int(os.getenv("SERIAL_BAUD", "115200"))
MQTT_HOST = os.getenv("MQTT_HOST", "mqtt")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
TCP_PORT = int(os.getenv("TCP_PORT", "2560"))

TOP_CMD = "rails49/dcc-ex/cmd"
TOP_STATUS = "rails49/dcc-ex/status/"
TOP_TCP = "rails49/dcc-ex/tcp-2560"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger("dcc-ex-bridge")


def wrap_message(msg: str) -> str:
    """Ensures a message is strictly wrapped in < > with no internal partial brackets."""
    content = msg.strip().lstrip("<").rstrip(">").strip()
    if not content:
        return ""
    return f"<{content}>"


class Bridge:
    def __init__(self):
        self.serial_reader = None
        self.serial_writer = None
        self.mqtt_client = None
        self.tcp_clients: Set[asyncio.StreamWriter] = set()
        self.serial_lock = asyncio.Lock()
        self.loop = None
        self.last_mtime = os.path.getmtime(__file__)

    async def check_for_updates(self):
        while True:
            await asyncio.sleep(2)
            try:
                if os.path.getmtime(__file__) > self.last_mtime:
                    logger.info("Code change detected, restarting...")
                    os._exit(0)
            except Exception:
                pass

    async def connect_mqtt(self):
        try:
            self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        except Exception:
            self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = (
            lambda c, u, f, r, p=None: c.subscribe(TOP_CMD) if r == 0 else None
        )
        self.mqtt_client.on_message = self.on_mqtt_message
        self.mqtt_client.connect(MQTT_HOST, MQTT_PORT, 60)
        self.mqtt_client.loop_start()

    def on_mqtt_message(self, client, userdata, msg):
        try:
            raw = msg.payload.decode().strip()
            if not raw:
                return
            clean = wrap_message(raw)
            if not clean:
                return

            logger.info(f"MQTT -> Bridge: {clean}")
            # RELAY: Only to Serial (PLAN.md says status echo is Serial -> MQTT)
            if self.loop:
                self.loop.call_soon_threadsafe(
                    lambda: asyncio.create_task(self.relay_inbound(clean))
                )
        except Exception as e:
            logger.error(f"MQTT Error: {e}")

    async def relay_inbound(self, msg: str, mqtt_echo_topic: str = None):
        """Relay a validated <msg> to Serial and all TCP clients. Optionally echo to MQTT."""
        if mqtt_echo_topic:
            logger.info(f"Bridge -> MQTT [{mqtt_echo_topic}]: {msg}")
            self.mqtt_client.publish(mqtt_echo_topic, msg)
        await asyncio.gather(self.send_to_serial(msg), self.broadcast_to_tcp(msg))

    async def broadcast_to_tcp(self, msg: str):
        if not self.tcp_clients:
            return
        data = (msg + "\n").encode()
        for w in list(self.tcp_clients):
            try:
                w.write(data)
                # We don't necessarily need to drain strictly here if we want to avoid blocking others
                # but for simplicity we keep it.
                await w.drain()
            except Exception:
                self.tcp_clients.discard(w)

    async def send_to_serial(self, msg: str):
        if not self.serial_writer:
            return
        async with self.serial_lock:
            try:
                # Ensure we only send complete commands
                if msg.startswith("<") and msg.endswith(">"):
                    self.serial_writer.write((msg + "\n").encode())
                    await self.serial_writer.drain()
                    logger.info(f"Bridge -> Serial: {msg}")
                else:
                    logger.warning(f"Discarding incomplete command for serial: {msg}")
            except Exception as e:
                logger.error(f"Serial Write Error: {e}")

    async def handle_serial(self):
        while True:
            try:
                (
                    self.serial_reader,
                    self.serial_writer,
                ) = await serial_asyncio.open_serial_connection(
                    url=SERIAL_PORT, baudrate=SERIAL_BAUD
                )
                logger.info(f"Connected to Serial {SERIAL_PORT}")
                buffer = ""
                while True:
                    data = await self.serial_reader.read(1024)
                    if not data:
                        break
                    buffer += data.decode(errors="ignore")
                    while "<" in buffer and ">" in buffer:
                        start, end = buffer.find("<"), buffer.find(">")
                        if end > start:
                            msg = buffer[start : end + 1].strip()
                            if msg:
                                await self.process_outbound(msg)
                            buffer = buffer[end + 1 :]
                        else:
                            buffer = buffer[start:]
            except Exception as e:
                logger.error(f"Serial Error: {e}")
                await asyncio.sleep(5)

    async def process_outbound(self, msg: str):
        """Process a validated <msg> from Serial to MQTT and TCP."""
        logger.info(f"Serial -> Bridge: {msg}")
        # Parse OPCODE for status topic
        content = msg[1:-1].strip()
        if content:
            opcode = content[0]
            # Handle opcodes that are MQTT wildcards (#, +)
            topic_suffix = opcode
            if opcode == "#":
                topic_suffix = "hash"
            elif opcode == "+":
                topic_suffix = "plus"

            topic = f"{TOP_STATUS}{topic_suffix}"
            logger.info(f"Bridge -> MQTT [{topic}]: {msg}")
            self.mqtt_client.publish(topic, msg)
        await self.broadcast_to_tcp(msg)

    async def handle_tcp_client(self, r, w):
        addr = w.get_extra_info("peername")
        logger.info(f"TCP Client Connected: {addr}")
        self.tcp_clients.add(w)
        buffer = ""
        try:
            while True:
                data = await r.read(1024)
                if not data:
                    break
                buffer += data.decode(errors="ignore")

                while "<" in buffer and ">" in buffer:
                    start, end = buffer.find("<"), buffer.find(">")
                    if end > start:
                        raw = buffer[start : end + 1]
                        clean = wrap_message(raw)
                        if clean:
                            logger.info(f"TCP -> Bridge: {clean}")
                            # Relay to Serial and echo to MQTT tcp-2560 topic
                            await self.relay_inbound(clean, mqtt_echo_topic=TOP_TCP)
                        buffer = buffer[end + 1 :]
                    else:
                        buffer = buffer[start:]

                # Fallback for line-based clients (less likely but for robustness)
                if "\n" in buffer and "<" not in buffer:
                    line = buffer.split("\n")[0].strip()
                    if line:
                        clean = wrap_message(line)
                        if clean:
                            await self.relay_inbound(clean, mqtt_echo_topic=TOP_TCP)
                    buffer = buffer[len(line) + 1 :]
        except Exception as e:
            logger.debug(f"TCP Client Error {addr}: {e}")
        finally:
            self.tcp_clients.discard(w)
            w.close()
            logger.info(f"TCP Client Disconnected: {addr}")

    async def run(self):
        self.loop = asyncio.get_running_loop()
        import serial.tools.list_ports

        ports = serial.tools.list_ports.comports()
        logger.info(f"Available serial ports: {[p.device for p in ports]}")
        await self.connect_mqtt()
        server = await asyncio.start_server(self.handle_tcp_client, "0.0.0.0", TCP_PORT)
        logger.info(f"Bridge online. TCP:{TCP_PORT} MQTT:{MQTT_HOST}")
        await asyncio.gather(
            server.serve_forever(), self.handle_serial(), self.check_for_updates()
        )


if __name__ == "__main__":
    try:
        asyncio.run(Bridge().run())
    except KeyboardInterrupt:
        pass
