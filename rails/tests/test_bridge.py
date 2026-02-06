import os
import socket
import threading
import time

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()

DOMAIN = os.getenv("RAILS_DOMAIN", "rails49.org")
TCP_PORT = 2560
TOPIC_REQ = "rails49/dcc-ex/cmd"
TOPIC_STA = "rails49/dcc-ex/status/#"
TOPIC_CMD = "rails49/dcc-ex/status/cmd"


class BridgeTester:
    def __init__(self):
        self.received_mqtt = []
        self.received_tcp = []
        self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.mqtt_client.on_message = self.on_mqtt_message
        self.tcp_sock = None
        self.stop_tcp = False

    def on_mqtt_message(self, client, userdata, msg):
        payload = msg.payload.decode()
        # print(f"DEBUG: MQTT Recv {msg.topic}: {payload}")
        self.received_mqtt.append((msg.topic, payload))

    def tcp_listener(self):
        self.tcp_sock.settimeout(1.0)
        while not self.stop_tcp:
            try:
                data = self.tcp_sock.recv(1024)
                if data:
                    msg = data.decode()
                    # print(f"DEBUG: TCP Recv: {msg.strip()}")
                    self.received_tcp.append(msg)
            except socket.timeout:
                continue
            except Exception as e:
                print(f"TCP Listener Error: {e}")
                break

    def run_tests(self):
        print(f"--- Starting Bidirectional Bridge Tests on {DOMAIN} ---")

        # 1. Setup Connections
        try:
            self.mqtt_client.connect(f"mqtt.{DOMAIN}", 1883, 60)
            # Subscribe to status topics and tcp traffic topic
            self.mqtt_client.subscribe([(TOPIC_STA, 0), ("rails49/dcc-ex/tcp-2560", 0)])
            self.mqtt_client.loop_start()

            host = f"ui.{DOMAIN}"
            self.tcp_sock = socket.create_connection((host, TCP_PORT), timeout=5)
            self.tcp_thread = threading.Thread(target=self.tcp_listener)
            self.tcp_thread.start()
        except Exception as e:
            print(f"Connection Setup Failed: {e}")
            return False

        success = True

        # TEST 1: MQTT -> TCP (Simulating App sending command to Hardware)
        print("Test 1: MQTT -> TCP Relay...")
        self.received_tcp.clear()
        self.received_mqtt.clear()
        test_cmd = "<s>"
        self.mqtt_client.publish(TOPIC_REQ, test_cmd)

        # Wait for TCP to receive it
        timeout = 5
        start = time.time()
        found_tcp = False
        while time.time() - start < timeout:
            if any(test_cmd in msg for msg in self.received_tcp):
                found_tcp = True
                break
            time.sleep(0.2)

        # Check that we DON'T see an echo on status/cmd (it was removed in bridge.py)
        echo_found = any(
            test_cmd == p
            for t, p in self.received_mqtt
            if t == "rails49/dcc-ex/status/cmd"
        )

        if found_tcp:
            print("✅ OK: MQTT command reached TCP listener")
        else:
            print("❌ FAIL: MQTT command did NOT reach TCP listener")
            success = False

        if not echo_found:
            print("✅ OK: No redundant status/cmd echo for MQTT commands")
        else:
            print("❌ FAIL: Redundant status/cmd echo still present")
            success = False

        # TEST 2: TCP -> MQTT (Simulating Hardware sending status to App)
        print("Test 2: TCP -> MQTT Status Relay...")
        self.received_mqtt.clear()
        test_msg = "<p1 JOIN>"
        self.tcp_sock.sendall(test_msg.encode() + b"\n")

        # In bridge.py, TCP input is relayed to Serial AND published to rails49/dcc-ex/tcp-2560
        start = time.time()
        found_mqtt_tcp = False
        while time.time() - start < timeout:
            if any(
                test_msg == p
                for t, p in self.received_mqtt
                if t == "rails49/dcc-ex/tcp-2560"
            ):
                found_mqtt_tcp = True
                break
            time.sleep(0.2)

        if found_mqtt_tcp:
            print("✅ OK: TCP message reached rails49/dcc-ex/tcp-2560 topic")
        else:
            print("❌ FAIL: TCP message did NOT reach rails49/dcc-ex/tcp-2560 topic")
            success = False

        # TEST 3: Formatting (Auto-wrapping)
        print("Test 3: Formatting (Auto-wrapping check)...")
        self.received_tcp.clear()
        self.mqtt_client.publish(TOPIC_REQ, "J Q")  # No brackets

        start = time.time()
        found = False
        while time.time() - start < timeout:
            if any("<J Q>" in msg for msg in self.received_tcp):
                found = True
                break
            time.sleep(0.2)

        if found:
            print("✅ OK: Brackets automatically added to MQTT -> TCP command")
        else:
            print("❌ FAIL: Brackets NOT added for 'J Q'")
            success = False

        # Cleanup
        self.stop_tcp = True
        self.tcp_thread.join()
        self.tcp_sock.close()
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()

        return success


if __name__ == "__main__":
    tester = BridgeTester()
    if tester.run_tests():
        print("\n=== ALL INTEGRATION TESTS PASSED ===")
        exit(0)
    else:
        print("\n=== SOME INTEGRATION TESTS FAILED ===")
        exit(1)
