from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from contextlib import asynccontextmanager
from iot_app.database import engine, Base
from iot_app.routers import auth_router, project_router, sensor_router, admin_router
from iot_app.mqtt_client import start_mqtt_client, stop_mqtt_client
from iot_app.database import SessionLocal
from iot_app import models
from iot_app.utils import parse_sensor_value
import os

# Create DB Tables
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_mqtt_client()
    yield
    stop_mqtt_client()

app = FastAPI(title="IoT API System", lifespan=lifespan)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Setup directories if missing
os.makedirs(os.path.join(BASE_DIR, "static"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "templates"), exist_ok=True)

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Include Routers
app.include_router(auth_router.router, prefix="/api")
app.include_router(project_router.router, prefix="/api")
app.include_router(sensor_router.router, prefix="/api")
app.include_router(admin_router.router, prefix="/api")

# =========================
# UNIVERSAL OPEN ENDPOINT 
# (For dump devices sending to root /data without auth)
# =========================
@app.post("/data/{device}")
@app.get("/data/{device}")
async def receive_data_open(device: str, request: Request):
    print(f"\n📡 [UNIVERSAL HTTP] Nhận request từ thiết bị: {device}")
    print(f"URL: {request.url}")
    
    # Đọc body gốc của POST request
    raw = await request.body()
    text = raw.decode("utf-8", errors="ignore").strip()
    
    # Nếu gửi qua GET hoặc URL Params, lấy query_params
    if not text and request.query_params:
        import json
        text = json.dumps(dict(request.query_params))
        
    print(f"📦 Dữ liệu: {text}")

    if not text or text == "{}":
        return {"status": "error", "message": "No data in body or query"}

    value_num = parse_sensor_value(text)
    print(f"🔢 Số trích xuất được: {value_num}")

    db = SessionLocal()
    try:
        # Kiểm tra xem thiết bị đã được đăng ký trong dự án nào chưa
        sensor = db.query(models.Sensor).filter(models.Sensor.device_name == device).first()
        if not sensor:
            print("❌ Thiết bị chưa đăng ký trên web, từ chối lưu.")
            return {"status": "error", "message": "Device not registered in any project"}

        sensor_data = models.SensorData(
            device_name=device,
            value=text,
            value_num=value_num
        )
        db.add(sensor_data)
        db.commit()
        print("✅ Đã lưu vào DB thành công!")
    except Exception as e:
        print("❌ Lỗi Database:", e)
        db.rollback()
    finally:
        db.close()

    return {"status": "ok", "message": "Data received"}

@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    return RedirectResponse(url="/login")

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/project/{id}", response_class=HTMLResponse)
def project_page(request: Request, id: int):
    return templates.TemplateResponse("project.html", {"request": request, "project_id": id})

@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})
