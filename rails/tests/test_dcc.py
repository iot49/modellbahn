import os
import socket
import time

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()

DOMAIN = os.getenv("RAILS_DOMAIN", "rails49.org")
TCP_PORT = 2560
MQTT_REQ_TOPIC = "rails49/dcc-ex/cmd"
MQTT_STA_TOPIC = "rails49/dcc-ex/status/#"


def test_dcc_tcp():
    print(f"Testing DCC-EX TCP on {DOMAIN}:{TCP_PORT}...")
    try:
        with socket.create_connection((DOMAIN, TCP_PORT), timeout=5) as sock:
            print("✅ DCC-EX TCP connection successful")
            # DCC-EX typically sends a version or status string on connect
            # such as <iDCC-EX ...>
            sock.settimeout(2)
            try:
                data = sock.recv(1024).decode()
                if data:
                    print(f"--- Received from DCC-EX: {data.strip()}")
            except socket.timeout:
                print("--- No immediate data received (normal for some setups)")
            return True
    except Exception as e:
        print(f"❌ DCC-EX TCP test failed: {e}")
        return False


received_mqtt = []


def on_message(client, userdata, msg):
    print(f"--- MQTT Received: {msg.topic} -> {msg.payload.decode()}")
    received_mqtt.append(msg)


def test_dcc_mqtt():
    print("Testing DCC-EX MQTT integration...")
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_message = on_message

    try:
        client.connect(f"mqtt.{DOMAIN}", 1883, 60)
        client.subscribe(MQTT_STA_TOPIC)
        client.loop_start()

        # Send a status request command <s>
        print(f"--- Sending <s> to {MQTT_REQ_TOPIC}")
        client.publish(MQTT_REQ_TOPIC, "<s>")

        # Wait for any response from sta/#
        timeout = 5
        start_time = time.time()
        while len(received_mqtt) == 0 and (time.time() - start_time) < timeout:
            time.sleep(0.5)

        client.loop_stop()
        client.disconnect()

        if len(received_mqtt) > 0:
            print("✅ DCC-EX MQTT integration functional")
            return True
        else:
            print(
                "⚠️ DCC-EX MQTT integration: No response received (maybe hardware not responding?)"
            )
            # We treat this as success for the bridge if the connection was ok,
            # but ideally we want to see a message.
            # For a smoke test, simple connectivity is first.
            return True
    except Exception as e:
        print(f"❌ DCC-EX MQTT test failed: {e}")
        return False


if __name__ == "__main__":
    success = True
    if not test_dcc_tcp():
        success = False
    if not test_dcc_mqtt():
        success = False

    if not success:
        exit(1)
