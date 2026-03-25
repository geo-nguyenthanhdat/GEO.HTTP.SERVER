from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from iot_app.database import get_db
from iot_app import models, schemas, auth

router = APIRouter(tags=["Sensors"])

@router.get("/projects/{project_id}/sensors", response_model=List[schemas.SensorResponse])
def get_sensors(project_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role == "admin":
        project = db.query(models.Project).filter(models.Project.id == project_id).first()
    else:
        project = db.query(models.Project).filter(models.Project.id == project_id, models.Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return db.query(models.Sensor).filter(models.Sensor.project_id == project.id).all()

@router.get("/projects/{project_id}/data", response_model=List[schemas.SensorDataResponse])
def get_sensor_data(project_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role == "admin":
        project = db.query(models.Project).filter(models.Project.id == project_id).first()
    else:
        project = db.query(models.Project).filter(models.Project.id == project_id, models.Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    sensors = db.query(models.Sensor).filter(models.Sensor.project_id == project.id).all()
    sensor_names = [s.device_name for s in sensors]
    
    data = db.query(models.SensorData).filter(models.SensorData.device_name.in_(sensor_names)).order_by(models.SensorData.timestamp.desc()).all()
    return data

@router.post("/projects/{project_id}/sensors", response_model=schemas.SensorResponse)
def create_sensor(project_id: int, sensor_data: schemas.SensorCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    project = db.query(models.Project).filter(models.Project.id == project_id, models.Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    existing = db.query(models.Sensor).filter(models.Sensor.device_name == sensor_data.device_name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Device name already taken")
        
    new_sensor = models.Sensor(device_name=sensor_data.device_name, project_id=project.id)
    db.add(new_sensor)
    db.commit()
    db.refresh(new_sensor)
    return new_sensor

@router.post("/data/{device}", response_model=schemas.SensorDataResponse)
def receive_sensor_data(device: str, data: schemas.SensorDataCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    sensor = db.query(models.Sensor).filter(models.Sensor.device_name == device).first()
    
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not registered. Please add it to a project first.")
        
    project = db.query(models.Project).filter(models.Project.id == sensor.project_id).first()
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to write to this sensor")
            
    sensor_data = models.SensorData(device_name=device, value=data.value)
    db.add(sensor_data)
    db.commit()
    db.refresh(sensor_data)
    
    return sensor_data

@router.delete("/projects/{project_id}/sensors/{sensor_id}")
def delete_sensor(project_id: int, sensor_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role == "admin":
        project = db.query(models.Project).filter(models.Project.id == project_id).first()
    else:
        project = db.query(models.Project).filter(models.Project.id == project_id, models.Project.user_id == current_user.id).first()
        
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    sensor = db.query(models.Sensor).filter(models.Sensor.id == sensor_id, models.Sensor.project_id == project.id).first()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
        
    db.query(models.SensorData).filter(models.SensorData.device_name == sensor.device_name).delete()
    db.delete(sensor)
    db.commit()
    return {"status": "success", "message": "Sensor deleted"}
