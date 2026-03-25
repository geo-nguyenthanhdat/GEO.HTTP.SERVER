import paho.mqtt.client as mqtt
import json
import logging
from iot_app.database import SessionLocal
from iot_app import models

logger = logging.getLogger(__name__)

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "sensors/#"

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        logger.info(f"Connected to MQTT broker {MQTT_BROKER}")
        client.subscribe(MQTT_TOPIC)
    else:
        logger.error(f"Failed to connect to MQTT broker, return code {rc}")

# Wrapper for older paho-mqtt versions
def on_connect_v1(client, userdata, flags, rc):
    on_connect(client, userdata, flags, rc)

def on_message(client, userdata, msg):
    topic_parts = msg.topic.split("/")
    if len(topic_parts) < 2:
        return
        
    device_name = topic_parts[1]

    # 🔥 parse payload
    try:
        raw = msg.payload.decode()
        payload = json.loads(raw)

        if isinstance(payload, dict):
            value = float(payload.get("value", 0.0))
        else:
            value = float(payload)

    except Exception as e:
        logger.error(f"Error parsing MQTT payload: {e} | RAW: {msg.payload}")
        return

    # 🔥 xử lý database
    db = SessionLocal()
    try:
        sensor = db.query(models.Sensor).filter(models.Sensor.device_name == device_name).first()

        if not sensor:
            logger.warning(f"Sensor {device_name} not registered. Ignoring MQTT data.")
            return

        sensor_data = models.SensorData(device_name=device_name, value=value)
        db.add(sensor_data)
        db.commit()

        logger.info(f"Saved data: {device_name} = {value}")

    except Exception as e:
        logger.error(f"Database error: {e}")
        db.rollback()
    finally:
        db.close()

try:
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqtt_client.on_connect = on_connect
except AttributeError:
    # Fallback to v1.x
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect_v1

mqtt_client.on_message = on_message

def start_mqtt_client():
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
        logger.info("MQTT Client Started")
    except Exception as e:
        logger.error(f"Could not connect to MQTT broker: {e}")

def stop_mqtt_client():
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
