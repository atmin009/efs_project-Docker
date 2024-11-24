from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, ForeignKey, Integer, String, Float, Boolean, Text, DateTime, TIMESTAMP, func
from sqlalchemy.ext.declarative import declarative_base
import pymysql

# ใช้ pymysql แทน MySQLdb
pymysql.install_as_MySQLdb()
Base = declarative_base()

class Building(Base):
    __tablename__ = 'building'
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, index=True)
    name = Column(String, index=True)
    area = Column(String, index=True)
    idGroup = Column(Integer)

class Unit(Base):
    __tablename__ = "unit"

    id = Column(Integer, primary_key=True, index=True)
    years = Column(Integer)
    month = Column(Integer)
    amount = Column(Integer)
    idBuilding = Column(Integer, ForeignKey("building.id"))



class ExamStatus(Base):
    __tablename__ = 'examStatus'
    id = Column(Integer, primary_key=True, index=True)
    years = Column(Integer)
    month = Column(Integer)
    status = Column(Boolean)

class SemesterStatus(Base):
    __tablename__ = 'semesterStatus'
    id = Column(Integer, primary_key=True, index=True)
    years = Column(Integer)
    month = Column(Integer)
    status = Column(Boolean)

class Member(Base):
    __tablename__ = 'member'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    fname = Column(String)
    lname = Column(String)
    email = Column(String)
    phone = Column(String)
    status = Column(Integer)
    reset_token = Column(String)  # เพิ่มคอลัมน์ reset_token


class UserUpdate(BaseModel):
    username: str
    fname: str
    lname: str
    email: str
    phone: str
    status: int
    password: Optional[str] = None  # Optional password field

class PredictionTable(Base):
    __tablename__ = "predictiontable"

    id = Column(Integer, primary_key=True, index=True)
    building = Column(String(50), nullable=True)
    area = Column(Float, nullable=True)
    prediction = Column(Float, nullable=True)
    unit = Column(Float, nullable=True)
    modelName = Column(String(50), nullable=True)
    month_current = Column(Integer, nullable=True)
    year_current = Column(Integer, nullable=True)
    month_predict = Column(Integer, nullable=True)
    year_predict = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)



class GroupBuilding(Base):
    __tablename__ = "groupbuilding"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    about = Column(Text, nullable=True)  # คอลัมน์ about ที่อนุญาตให้เป็น NULL ได้

class NumberOfUsers(Base):
    __tablename__ = "numberofusers"

    id = Column(Integer, primary_key=True, index=True)
    years = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    amount = Column(Integer, nullable=False)

class ForgotPasswordRequest(BaseModel):
    email: EmailStr
class ResetPasswordRequest(BaseModel):
    password: str

# Models
class News(Base):
    __tablename__ = "news"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    content = Column(Text)
    cover_image = Column(String(255))  # ชื่อไฟล์ภาพปก
    attachment = Column(String(255))   # ชื่อไฟล์แนบ
    
class NewsUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    cover_image: Optional[str] = None
    attachment: Optional[str] = None
