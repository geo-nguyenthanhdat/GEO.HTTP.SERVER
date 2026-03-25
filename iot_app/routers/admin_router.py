from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from iot_app.database import get_db
from iot_app import models, schemas, auth

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/users", response_model=List[schemas.UserResponse])
def get_all_users(db: Session = Depends(get_db), current_user: models.User = Depends(auth.require_admin)):
    return db.query(models.User).all()

@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.require_admin)):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    projects = db.query(models.Project).filter(models.Project.user_id == user.id).all()
    for p in projects:
        sensors = db.query(models.Sensor).filter(models.Sensor.project_id == p.id).all()
        for s in sensors:
            db.query(models.SensorData).filter(models.SensorData.device_name == s.device_name).delete()
            db.delete(s)
        db.delete(p)
    db.delete(user)
    db.commit()
    return {"status": "success"}

@router.get("/projects", response_model=List[schemas.ProjectResponse])
def get_all_projects(db: Session = Depends(get_db), current_user: models.User = Depends(auth.require_admin)):
    return db.query(models.Project).all()

from pydantic import BaseModel
class RoleUpdate(BaseModel):
    role: str

class ApproveUpdate(BaseModel):
    is_active: bool

@router.put("/users/{user_id}/approve")
def approve_user(user_id: int, approve_data: ApproveUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.require_admin)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id and approve_data.is_active is False:
        raise HTTPException(status_code=400, detail="Cannot disable yourself")
    
    user.is_active = approve_data.is_active
    db.commit()
    return {"status": "success", "is_active": user.is_active}

@router.put("/users/{user_id}/role")
def update_user_role(user_id: int, role_data: RoleUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.require_admin)):
    if role_data.role not in ["admin", "user"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot downgrade yourself")
    
    user.role = role_data.role
    db.commit()
    return {"status": "success", "new_role": user.role}
