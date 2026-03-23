from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from datetime import datetime
import psycopg2
import paho.mqtt.client as mqtt
import json



print("🔥 SERVER V2 ĐANG CHẠY 🔥")



app = FastAPI()

# =========================
# DATABASE CONFIG
# =========================
def get_db():
    return psycopg2.connect(
        host="localhost",
        database="IOT",
        user="postgres",
        password="250702"
    )

# =========================
# API NHẬN DATA (FIX 422)
# =========================
from fastapi import Request

@app.post("/data/{device}")
async def receive_data(device: str, request: Request):
    print("🔥 API V2 HIT 🔥")

    raw = await request.body()
    data = raw.decode("utf-8", errors="ignore")

    print("DATA:", data)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO data (device, value) VALUES (%s, %s)",
        (device.lower(), data)
    )

    conn.commit()
    conn.close()

    return {"status": "ok"}

# =========================
# API LẤY ALL DATA
# =========================
@app.get("/api/data")
def get_data():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT device, time, value
        FROM data
        ORDER BY id DESC
        LIMIT 100
    """)

    rows = cursor.fetchall()

    result = []
    for r in rows:
        result.append({
            "device": r[0],
            "time": str(r[1]),
            "data": r[2]
        })

    conn.close()
    return result

# =========================
# API LẤY THEO DEVICE (FIX THIẾU)
# =========================
@app.get("/api/data/{device}")
def get_data_device(device: str):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT device, time, value
        FROM data
        WHERE device = %s
        ORDER BY id DESC
        LIMIT 100
    """, (device.lower(),))

    rows = cursor.fetchall()

    result = []
    for r in rows:
        result.append({
            "device": r[0],
            "time": str(r[1]),
            "data": r[2]
        })

    conn.close()
    return result

# =========================
# MQTT CONFIG
# =========================
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "iot/#"

def on_connect(client, userdata, flags, rc):
    print("MQTT Connected:", rc)
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    try:
        topic = msg.topic
        payload = msg.payload.decode()

        print("MQTT:", topic, payload)

        device = topic.split("/")[-1]

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO data (device, value) VALUES (%s, %s)",
            (device, payload)
        )

        conn.commit()
        conn.close()

    except Exception as e:
        print("MQTT Error:", e)

mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()

# =========================
# HOME
# =========================
@app.get("/")
def home():
    return {"message": "IoT Server Running"}

# =========================
# WEB VIEW ALL
# =========================
@app.get("/view", response_class=HTMLResponse)
def view_all():

    html = """
    <html>
    <body>
    <h2>ALL DATA</h2>
    <table border="1" id="table"></table>

    <script>
    async function loadData(){
        let res = await fetch("/api/data")
        let data = await res.json()

        let table = document.getElementById("table")
        table.innerHTML = "<tr><th>Device</th><th>Time</th><th>Data</th></tr>"

        data.forEach(row => {
            table.innerHTML += `<tr>
            <td>${row.device}</td>
            <td>${row.time}</td>
            <td>${row.data}</td>
            </tr>`
        })
    }

    setInterval(loadData,2000)
    </script>

    </body>
    </html>
    """
    return html

# =========================
# WEB VIEW DEVICE
# =========================
@app.get("/view/{device}", response_class=HTMLResponse)
def view_device(device: str):

    html = f"""
    <html>
    <body>
    <h2>Device: {device}</h2>
    <table border="1" id="table"></table>

    <script>
    async function loadData(){{
        let res = await fetch("/api/data/{device}")
        let data = await res.json()

        let table = document.getElementById("table")
        table.innerHTML = "<tr><th>Time</th><th>Data</th></tr>"

        data.forEach(row => {{
            table.innerHTML += `<tr>
            <td>${{row.time}}</td>
            <td>${{row.data}}</td>
            </tr>`
        }})
    }}

    setInterval(loadData,2000)
    </script>

    </body>
    </html>
    """
    return html
#uvicorn serverv2:app --host 0.0.0.0 --port 8000