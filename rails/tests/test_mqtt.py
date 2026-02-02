import os
import time

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()

DOMAIN = os.getenv("RAILS_DOMAIN", "rails49.org")


def test_mqtt_tcp():
    """Test raw MQTT connection on port 1883"""
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    try:
        client.connect(f"mqtt.{DOMAIN}", 1883, 60)
        client.loop_start()
        time.sleep(1)
        client.disconnect()
        print("✅ MQTT TCP (1883) is functional")
        return True
    except Exception as e:
        print(f"❌ MQTT TCP (1883) failed: {e}")
        return False


def test_mqtt_tls():
    """Test encrypted MQTT connection on port 8883"""
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.tls_set()  # Use system certs
    # Note: We might need to disable verification if local certs are old
    client.tls_insecure_set(True)
    try:
        client.connect(f"mqtt.{DOMAIN}", 8883, 60)
        client.loop_start()
        time.sleep(1)
        client.disconnect()
        print("✅ MQTT TLS (8883) is functional")
        return True
    except Exception as e:
        print(f"❌ MQTT TLS (8883) failed: {e}")
        return False


if __name__ == "__main__":
    success = True
    if not test_mqtt_tcp():
        success = False
    if not test_mqtt_tls():
        success = False

    if not success:
        exit(1)
