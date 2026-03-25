from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from iot_app.database import get_db
from iot_app import models, schemas, auth

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.get("/", response_model=List[schemas.ProjectResponse])
def get_projects(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    return db.query(models.Project).filter(models.Project.user_id == current_user.id).all()

@router.post("/", response_model=schemas.ProjectResponse)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    new_project = models.Project(name=project.name, user_id=current_user.id)
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return new_project

@router.get("/{project_id}", response_model=schemas.ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role == "admin":
        project = db.query(models.Project).filter(models.Project.id == project_id).first()
    else:
        project = db.query(models.Project).filter(models.Project.id == project_id, models.Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.delete("/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role == "admin":
        project = db.query(models.Project).filter(models.Project.id == project_id).first()
    else:
        project = db.query(models.Project).filter(models.Project.id == project_id, models.Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    sensors = db.query(models.Sensor).filter(models.Sensor.project_id == project.id).all()
    for s in sensors:
        db.query(models.SensorData).filter(models.SensorData.device_name == s.device_name).delete()
        db.delete(s)
    db.delete(project)
    db.commit()
    return {"status": "success", "message": "Project deleted successfully"}
