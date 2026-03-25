from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from contextlib import asynccontextmanager
from iot_app.database import engine, Base
from iot_app.routers import auth_router, project_router, sensor_router, admin_router
from iot_app.mqtt_client import start_mqtt_client, stop_mqtt_client
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
