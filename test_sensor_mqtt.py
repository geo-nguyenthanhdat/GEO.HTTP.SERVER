import paho.mqtt.client as mqtt
import json
import time
import random

BROKER = "127.0.0.1"
PORT = 1883
DEVICE = "demo_mqtt_sensor"
TOPIC = f"sensors/{DEVICE}"

try:
    print(f"Bắt đầu giả lập gửi dữ liệu lên MQTT tới {BROKER}:{PORT} trên topic {TOPIC}")
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
except AttributeError:
    client = mqtt.Client()

try:
    client.connect(BROKER, PORT, 60)
except Exception as e:
    print(f"LỖI: Không thể kết nối tới MQTT Broker. Bạn đã bật phần mềm Mosquitto chưa? (Lỗi: {e})")
    exit(1)

client.loop_start()

try:
    while True:
        value = round(random.uniform(20.0, 35.0), 2)
        payload = json.dumps({"value": value})
        client.publish(TOPIC, payload)
        print(f"Đã đẩy: {payload} lên topic {TOPIC}")
        time.sleep(3)
except KeyboardInterrupt:
    print("Dừng gửi MQTT.")
finally:
    client.loop_stop()
    client.disconnect()
