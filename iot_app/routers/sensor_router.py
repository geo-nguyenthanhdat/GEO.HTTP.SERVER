from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
from iot_app.database import get_db
from iot_app import models, schemas, auth

router = APIRouter(tags=["Sensors"])


# ================== GET SENSORS ==================
@router.get("/projects/{project_id}/sensors", response_model=List[schemas.SensorResponse])
def get_sensors(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if current_user.role == "admin":
        project = db.query(models.Project).filter(models.Project.id == project_id).first()
    else:
        project = db.query(models.Project).filter(
            models.Project.id == project_id,
            models.Project.user_id == current_user.id
        ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return db.query(models.Sensor).filter(models.Sensor.project_id == project.id).all()


# ================== GET DATA ==================
@router.get("/projects/{project_id}/data", response_model=List[schemas.SensorDataResponse])
def get_sensor_data(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if current_user.role == "admin":
        project = db.query(models.Project).filter(models.Project.id == project_id).first()
    else:
        project = db.query(models.Project).filter(
            models.Project.id == project_id,
            models.Project.user_id == current_user.id
        ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    sensors = db.query(models.Sensor).filter(models.Sensor.project_id == project.id).all()
    sensor_names = [s.device_name for s in sensors]

    data = db.query(models.SensorData)\
        .filter(models.SensorData.device_name.in_(sensor_names))\
        .order_by(models.SensorData.timestamp.desc())\
        .all()

    return data


# ================== CREATE SENSOR ==================
@router.post("/projects/{project_id}/sensors", response_model=schemas.SensorResponse)
def create_sensor(
    project_id: int,
    sensor_data: schemas.SensorCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    project = db.query(models.Project).filter(
        models.Project.id == project_id,
        models.Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    existing = db.query(models.Sensor).filter(
        models.Sensor.device_name == sensor_data.device_name
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Device name already taken")

    new_sensor = models.Sensor(
        device_name=sensor_data.device_name,
        project_id=project.id
    )

    db.add(new_sensor)
    db.commit()
    db.refresh(new_sensor)

    return new_sensor


# ================== RECEIVE DATA (UPDATED) ==================
@router.post("/data/{device}", response_model=schemas.SensorDataResponse)
async def receive_sensor_data(
    device: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    from iot_app.utils import parse_sensor_value
    
    # Đọc raw body của HTTP request (chắc chắn luôn lấy được nguyên gốc)
    raw = await request.body()
    text = raw.decode(errors="ignore").strip()

    if not text:
        raise HTTPException(status_code=400, detail="No data received")

    # Mức độ an toàn: lưu toàn bộ chuỗi gốc, bóc tách `value_num` cho biểu đồ
    value_num = parse_sensor_value(text)

    print("📡 Device:", device)
    print("📦 Raw Value:", text)
    print("🔢 Parsed Number:", value_num)

    # ===== CHECK SENSOR =====
    sensor = db.query(models.Sensor).filter(
        models.Sensor.device_name == device
    ).first()

    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not registered")

    project = db.query(models.Project).filter(
        models.Project.id == sensor.project_id
    ).first()

    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # ===== SAVE =====
    sensor_data = models.SensorData(
        device_name=device,
        value=text,               # Lưu chuỗi gốc
        value_num=value_num       # Có thể int/float hoặc Null
    )

    db.add(sensor_data)
    db.commit()
    db.refresh(sensor_data)

    return sensor_data


# ================== DELETE SENSOR ==================
@router.delete("/projects/{project_id}/sensors/{sensor_id}")
def delete_sensor(
    project_id: int,
    sensor_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if current_user.role == "admin":
        project = db.query(models.Project).filter(models.Project.id == project_id).first()
    else:
        project = db.query(models.Project).filter(
            models.Project.id == project_id,
            models.Project.user_id == current_user.id
        ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    sensor = db.query(models.Sensor).filter(
        models.Sensor.id == sensor_id,
        models.Sensor.project_id == project.id
    ).first()

    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")

    db.query(models.SensorData).filter(
        models.SensorData.device_name == sensor.device_name
    ).delete()

    db.delete(sensor)
    db.commit()

    return {"status": "success", "message": "Sensor deleted"}