from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str = "user"

class TokenData(BaseModel):
    username: Optional[str] = None

class ProjectBase(BaseModel):
    name: str

class ProjectCreate(ProjectBase):
    pass

class ProjectResponse(ProjectBase):
    id: int
    user_id: int
    class Config:
        from_attributes = True

class SensorBase(BaseModel):
    device_name: str

class SensorCreate(SensorBase):
    pass

class SensorResponse(SensorBase):
    id: int
    project_id: int
    class Config:
        from_attributes = True

class SensorDataCreate(BaseModel):
    value: float

class SensorDataResponse(BaseModel):
    id: int
    device_name: str
    value: float
    timestamp: datetime
    class Config:
        from_attributes = True
