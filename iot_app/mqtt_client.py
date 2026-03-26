import paho.mqtt.client as mqtt
import json
import logging
from iot_app.database import SessionLocal
from iot_app import models

logger = logging.getLogger(__name__)

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "sensors/#"


# ================== CONNECT ==================
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        logger.info(f"Connected to MQTT broker {MQTT_BROKER}")
        client.subscribe(MQTT_TOPIC)
    else:
        logger.error(f"Failed to connect to MQTT broker, return code {rc}")


def on_connect_v1(client, userdata, flags, rc):
    on_connect(client, userdata, flags, rc)


# ================== ON MESSAGE ==================
def on_message(client, userdata, msg):
    from iot_app.utils import parse_sensor_value
    
    topic_parts = msg.topic.split("/")
    if len(topic_parts) < 2:
        return

    device_name = topic_parts[1]

    raw = msg.payload
    text = raw.decode(errors="ignore").strip()

    logger.info(f"📡 RAW [{device_name}]: {text}")

    # Trích xuất số để vẽ đồ thị
    value_num = parse_sensor_value(text)

    logger.info(f"👉 PARSED NUM [{device_name}]: {value_num}")

    # ================== DB ==================
    db = SessionLocal()
    try:
        sensor = db.query(models.Sensor).filter(
            models.Sensor.device_name == device_name
        ).first()

        if not sensor:
            logger.warning(f"Sensor {device_name} not registered. Ignoring.")
            return

        sensor_data = models.SensorData(
            device_name=device_name,
            value=text,               # 🔥 LUÔN lưu chuỗi gốc nguyên bản
            value_num=value_num       # Có thể int/float hoặc Null
        )

        db.add(sensor_data)
        db.commit()

        logger.info(f"✅ Saved: {device_name} = {text}")

    except Exception as e:
        logger.error(f"Database error: {e}")
        db.rollback()

    finally:
        db.close()


# ================== MQTT CLIENT ==================
try:
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqtt_client.on_connect = on_connect
except AttributeError:
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect_v1

mqtt_client.on_message = on_message


# ================== START / STOP ==================
def start_mqtt_client():
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
        logger.info("🚀 MQTT Client Started")
    except Exception as e:
        logger.error(f"Could not connect to MQTT broker: {e}")


def stop_mqtt_client():
    mqtt_client.loop_stop()
    mqtt_client.disconnect()