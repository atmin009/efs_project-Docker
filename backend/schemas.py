from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from sqlalchemy import Column, Integer,String

from database import Base
class BuildingCreate(BaseModel):
    code: str
    name: str
    area: Optional[str] = None
    idGroup: Optional[int] = None

class BuildingResponse(BaseModel):
    id: int
    code: str
    name: str
    area: Optional[str] = None
    idGroup: Optional[int] = None

    class Config:
        orm_mode = True

class UnitCreate(BaseModel):
    years: int
    month: int
    amount: int
    idBuilding: int


class ExamStatusCreate(BaseModel):
    years: int
    month: int
    status: bool

class SemesterStatusCreate(BaseModel):
    years: int
    month: int
    status: bool

class MemberCreate(BaseModel):
    username: str
    fname: str
    lname: str
    email: str
    phone: str
    status: int
    password: Optional[str] = None  # Make password optional

class PredictionRequest(BaseModel):
    year: int
    month: int
    modelName: str

class PredictionResponse(BaseModel):
    building: Optional[str] = None
    area: Optional[float] = None
    prediction: float
    unit: Optional[float] = None
    modelName: Optional[str] = None
    month_current: Optional[int] = None
    year_current: Optional[int] = None
    month_predict: str
    year_predict: int

    class Config:
        from_attributes = True  # This replaces orm_mode=True

class LoginData(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    user_id: int
    username: str
    status: int
    name: str

class MemberResponse(BaseModel):
    id: int
    username: str
    fname: str
    lname: str
    email: str
    phone: str
    status: int

class PredictionSumResponse(BaseModel):
    year_predict: int
    month_predict: int
    prediction: float

    model_config = ConfigDict(from_attributes=True)

class PeriodSums(BaseModel):
    one_month: float
    three_months: float
    six_months: float
    twelve_months: float
    monthly_data: List[PredictionSumResponse]

    model_config = ConfigDict(from_attributes=True)
    
class Building(Base):
    __tablename__ = "building"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(255))
    name = Column(String(255))
    area = Column(String(255))
    idGroup = Column(Integer)  # เพิ่มคอลัมน์ idGroup

class GroupBuildingBase(BaseModel):
    name: str
    about: Optional[str] = None

class NumberOfUsersCreate(BaseModel):
    years: int
    amount: int

    class Config:
        orm_mode = True
class GroupBuildingCreate(BaseModel):
    name: str
    about: Optional[str] = None

class GroupBuildingResponse(GroupBuildingCreate):
    id: int

    class Config:
        orm_mode = True
class SemesterStatusCreate(BaseModel):
    years: int
    month: int
    status: int

class SemesterStatusResponse(SemesterStatusCreate):
    id: int

    class Config:
        orm_mode = True

class ExamStatusResponse(BaseModel):
    id: int
    years: int
    month: int
    status: bool

    class Config:
        orm_mode = True
class UnitResponse(BaseModel):
    id: int
    years: int
    month: int
    amount: int
    idBuilding: int
    building_name: str

    class Config:
        orm_mode = True

class AnnouncementCreate(BaseModel):
    title: str
    content: str
    attachment: str = None
    cover_image: str = None

class AnnouncementResponse(BaseModel):
    id: int
    title: str
    content: str
    attachment: str = None
    cover_image: str = None
    created_at: datetime

    class Config:
        orm_mode = True

