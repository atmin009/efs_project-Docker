from datetime import datetime, timedelta
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import hashlib
import logging
import secrets
import shutil
import smtplib
from uuid import uuid4
from venv import logger
import aiosmtplib
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from marshmallow import ValidationError
from pydantic import BaseModel, EmailStr
import pymysql
from sqlalchemy import asc, create_engine, desc, distinct, func
from sqlalchemy.orm import sessionmaker, Session
from typing import Dict, List, Optional
from database import Base
from models import  Building, ForgotPasswordRequest, GroupBuilding, News, NewsUpdate, PredictionTable, ResetPasswordRequest, Unit, NumberOfUsers, ExamStatus, SemesterStatus, Member
from schemas import  BuildingCreate, BuildingResponse, ExamStatusResponse, GroupBuildingCreate, GroupBuildingResponse, LoginData, PeriodSums, PredictionSumResponse, SemesterStatusResponse, UnitCreate, NumberOfUsersCreate,NumberOfUsersCreate, ExamStatusCreate, SemesterStatusCreate, MemberResponse, MemberCreate, PredictionRequest, PredictionResponse, UnitResponse
from predict import predict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import os
import base64


# DATABASE_URL = "mysql+pymysql://root:@localhost/efsdata"

DATABASE_URL = "mysql+pymysql://EFSadm:EFSsys123@db:3306/mydatabase"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode('utf-8')))
    return f"{base64.urlsafe_b64encode(salt).decode('utf-8')}:{key.decode('utf-8')}"


def verify_password(stored_password, provided_password):
    salt, key = stored_password.split(":")
    salt = base64.urlsafe_b64decode(salt)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    return key == base64.urlsafe_b64encode(kdf.derive(provided_password.encode('utf-8'))).decode('utf-8')



Base.metadata.create_all(bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# CRUD for Building

@app.post("/buildings/", response_model=BuildingResponse)
def create_building(building: BuildingCreate, db: Session = Depends(get_db)):
    db_building = Building(code=building.code, name=building.name, area=building.area, idGroup=building.idGroup)
    db.add(db_building)
    db.commit()
    db.refresh(db_building)
    return db_building

@app.get("/buildings/", response_model=List[BuildingResponse])
def read_buildings(db: Session = Depends(get_db)):
    buildings = db.query(Building).all()
    return buildings


@app.put("/buildings/{building_id}", response_model=BuildingResponse)
def update_building(building_id: int, building: BuildingCreate, db: Session = Depends(get_db)):
    db_building = db.query(Building).filter(Building.id == building_id).first()
    if db_building is None:
        raise HTTPException(status_code=404, detail="Building not found")
    
    # ตรวจสอบว่ามีการอัปเดตค่า idGroup หรือไม่
    db_building.code = building.code
    db_building.name = building.name
    db_building.area = building.area
    db_building.idGroup = building.idGroup

    db.commit()
    db.refresh(db_building)
    return db_building


@app.delete("/buildings/{building_id}")
def delete_building(building_id: int, db: Session = Depends(get_db)):
    db_building = db.query(Building).filter(Building.id == building_id).first()
    if db_building is None:
        raise HTTPException(status_code=404, detail="Building not found")
    db.delete(db_building)
    db.commit()
    return {"detail": "Building deleted"}

# CRUD for Unit
@app.post("/units/", response_model=UnitCreate)
def create_unit(unit: UnitCreate, db: Session = Depends(get_db)):
    db_unit = Unit(years=unit.years, month=unit.month, amount=unit.amount, idBuilding=unit.idBuilding)
    db.add(db_unit)
    db.commit()
    db.refresh(db_unit)
    return db_unit

@app.get("/units/{unit_id}", response_model=UnitCreate)
def read_unit(unit_id: int, db: Session = Depends(get_db)):
    db_unit = db.query(Unit).filter(Unit.id == unit_id).first()
    if db_unit is None:
        raise HTTPException(status_code=404, detail="Unit not found")
    return db_unit


@app.get("/units/", response_model=List[UnitCreate])
def read_units(db: Session = Depends(get_db)):
    units = db.query(Unit).all()
    return units

@app.get("/unit/")
def get_units(db: Session = Depends(get_db)):
    units = db.query(Unit).all()
    return units



@app.put("/units/{unit_id}", response_model=UnitResponse)
def update_unit(unit_id: int, unit: UnitCreate, db: Session = Depends(get_db)):
    db_unit = db.query(Unit).filter(Unit.id == unit_id).first()
    if not db_unit:
        raise HTTPException(status_code=404, detail="Unit not found")

    db_unit.years = unit.years
    db_unit.month = unit.month
    db_unit.amount = unit.amount
    db_unit.idBuilding = unit.idBuilding

    db.commit()
    db.refresh(db_unit)  # รีเฟรช db_unit หลังจากการคอมมิต

    # เข้าถึงความสัมพันธ์หลังจากการรีเฟรช
    building_name = db.query(Building).filter(Building.id == db_unit.idBuilding).first().name

    return UnitResponse(
        id=db_unit.id,
        years=db_unit.years,
        month=db_unit.month,
        amount=db_unit.amount,
        idBuilding=db_unit.idBuilding,
        building_name=building_name
    )



logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.get("/units/check_duplicate")
def check_duplicate_unit(
    idBuilding: int = Query(...),
    years: int = Query(...),
    month: int = Query(...),
    db: Session = Depends(get_db)
):
    logger.debug(f"Received: idBuilding={idBuilding}, years={years}, month={month}")
    
    # ตรวจสอบว่าค่าที่รับมาเป็นตัวเลขจริงๆ
    try:
        idBuilding = int(idBuilding)
        years = int(years)
        month = int(month)
    except ValueError as e:
        logger.error(f"Error converting parameters to int: {e}")
        raise HTTPException(status_code=422, detail=f"Invalid input: {str(e)}")

    if not (1 <= month <= 12):
        logger.error(f"Invalid month: {month}")
        raise HTTPException(status_code=422, detail=f"Invalid month. Month must be between 1 and 12.")
    if years < 1900 or years > 2100:
        logger.error(f"Invalid year: {years}")
        raise HTTPException(status_code=422, detail=f"Invalid year. Year must be between 1900 and 2100.")
    
    duplicate = db.query(Unit).filter(
        Unit.idBuilding == idBuilding,
        Unit.years == years,
        Unit.month == month
    ).first()
    
    result = {"exists": duplicate is not None}
    logger.debug(f"Result: {result}")
    return result


@app.delete("/units/{unit_id}")
def delete_unit(unit_id: int, db: Session = Depends(get_db)):
    print(f"Received unit_id: {unit_id}")
    db_unit = db.query(Unit).filter(Unit.id == unit_id).first()
    if db_unit is None:
        raise HTTPException(status_code=404, detail="Unit not found")
    db.delete(db_unit)
    db.commit()
    return {"detail": "Unit deleted"}


# CRUD for NumberOfUsers
@app.post("/numberOfUsers/", response_model=NumberOfUsersCreate)
def create_number_of_users(number_of_users: NumberOfUsersCreate, db: Session = Depends(get_db)):
    db_number_of_users = NumberOfUsers(years=number_of_users.years, month=number_of_users.month, amount=number_of_users.amount)
    db.add(db_number_of_users)
    db.commit()
    db.refresh(db_number_of_users)
    return db_number_of_users

@app.get("/numberOfUsers/{number_of_users_id}", response_model=NumberOfUsersCreate)
def read_number_of_users(number_of_users_id: int, db: Session = Depends(get_db)):
    db_number_of_users = db.query(NumberOfUsers).filter(NumberOfUsers.id == number_of_users_id).first()
    if db_number_of_users is None:
        raise HTTPException(status_code=404, detail="Number of users not found")
    return db_number_of_users

@app.put("/numberOfUsers/{number_of_users_id}", response_model=NumberOfUsersCreate)
def update_number_of_users(number_of_users_id: int, number_of_users: NumberOfUsersCreate, db: Session = Depends(get_db)):
    db_number_of_users = db.query(NumberOfUsers).filter(NumberOfUsers.id == number_of_users_id).first()
    if db_number_of_users is None:
        raise HTTPException(status_code=404, detail="Number of users not found")
    db_number_of_users.years = number_of_users.years
    db_number_of_users.month = number_of_users.month
    db_number_of_users.amount = number_of_users.amount
    db.commit()
    db.refresh(db_number_of_users)
    return db_number_of_users

@app.delete("/numberOfUsers/{number_of_users_id}")
def delete_number_of_users(number_of_users_id: int, db: Session = Depends(get_db)):
    db_number_of_users = db.query(NumberOfUsers).filter(NumberOfUsers.id == number_of_users_id).first()
    if db_number_of_users is None:
        raise HTTPException(status_code=404, detail="Number of users not found")
    db.delete(db_number_of_users)
    db.commit()
    return {"detail": "Number of users deleted"}

# CRUD for ExamStatus
@app.get("/examStatus", response_model=List[ExamStatusResponse])
def get_exam_statuses(db: Session = Depends(get_db)):
    exam_statuses = db.query(ExamStatus).all()

    # แปลงปีจาก ค.ศ. เป็น พ.ศ.
    for status in exam_statuses:
        status.years = status.years + 543

    return exam_statuses

# Create a new exam status
@app.post("/examStatus", response_model=ExamStatusResponse)
def create_exam_status(exam_status: ExamStatusCreate, db: Session = Depends(get_db)):
    # ตรวจสอบว่ามีข้อมูลในปีและเดือนนี้อยู่แล้วหรือไม่
    existing_exam_status = db.query(ExamStatus).filter(
        ExamStatus.years == exam_status.years,
        ExamStatus.month == exam_status.month
    ).first()

    if existing_exam_status:
        raise HTTPException(status_code=400, detail="ข้อมูลซ้ำ: มีข้อมูลในเดือนและปีนี้อยู่แล้ว")

    db_exam_status = ExamStatus(**exam_status.dict())
    db.add(db_exam_status)
    db.commit()
    db.refresh(db_exam_status)
    return db_exam_status


# Update an exam status by ID
# Update an exam status by ID
@app.put("/examStatus/{id}", response_model=ExamStatusResponse)
def update_exam_status(id: int, updated_status: ExamStatusCreate, db: Session = Depends(get_db)):
    db_exam_status = db.query(ExamStatus).filter(ExamStatus.id == id).first()
    if not db_exam_status:
        raise HTTPException(status_code=404, detail="Exam status not found")

    # แปลงปีจาก พ.ศ. เป็น ค.ศ.
    updated_status.years = updated_status.years - 543

    # ตรวจสอบว่ามีข้อมูลในปีและเดือนนี้อยู่แล้วหรือไม่ แต่ไม่ใช่ของ ID เดียวกัน
    existing_exam_status = db.query(ExamStatus).filter(
        ExamStatus.years == updated_status.years,
        ExamStatus.month == updated_status.month,
        ExamStatus.id != id
    ).first()

    if existing_exam_status:
        raise HTTPException(status_code=400, detail="ข้อมูลซ้ำ: มีข้อมูลในเดือนและปีนี้อยู่แล้ว")

    for key, value in updated_status.dict().items():
        setattr(db_exam_status, key, value)
    db.commit()
    db.refresh(db_exam_status)
    return db_exam_status




# Delete an exam status by ID
@app.delete("/examStatus/{id}")
def delete_exam_status(id: int, db: Session = Depends(get_db)):
    db_exam_status = db.query(ExamStatus).filter(ExamStatus.id == id).first()
    if not db_exam_status:
        raise HTTPException(status_code=404, detail="Exam status not found")
    db.delete(db_exam_status)
    db.commit()
    return {"message": "Exam status deleted successfully"}
# CRUD for SemesterStatus
@app.get("/semesterstatus", response_model=List[SemesterStatusResponse])
def get_semester_statuses(db: Session = Depends(get_db)):
    return db.query(SemesterStatus).all()

# Create a new semester status
@app.post("/semesterstatus", response_model=SemesterStatusResponse)
def create_semester_status(semester_status: SemesterStatusCreate, db: Session = Depends(get_db)):
    db_semester_status = SemesterStatus(**semester_status.dict())
    db.add(db_semester_status)
    db.commit()
    db.refresh(db_semester_status)
    return db_semester_status

# Update a semester status by ID
@app.put("/semesterstatus/{id}", response_model=SemesterStatusResponse)
def update_semester_status(id: int, updated_status: SemesterStatusCreate, db: Session = Depends(get_db)):
    db_semester_status = db.query(SemesterStatus).filter(SemesterStatus.id == id).first()
    if not db_semester_status:
        raise HTTPException(status_code=404, detail="Semester status not found")
    for key, value in updated_status.dict().items():
        setattr(db_semester_status, key, value)
    db.commit()
    db.refresh(db_semester_status)
    return db_semester_status

# Delete a semester status by ID
@app.delete("/semesterstatus/{id}")
def delete_semester_status(id: int, db: Session = Depends(get_db)):
    db_semester_status = db.query(SemesterStatus).filter(SemesterStatus.id == id).first()
    if not db_semester_status:
        raise HTTPException(status_code=404, detail="Semester status not found")
    db.delete(db_semester_status)
    db.commit()
    return {"message": "Semester status deleted successfully"}

# CRUD for Member
@app.post("/members/", response_model=MemberCreate)
def create_member(member: MemberCreate, db: Session = Depends(get_db)):
    db_user = db.query(Member).filter(Member.username == member.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_password = hash_password(member.password)

    db_member = Member(
        username=member.username,
        password=hashed_password,
        fname=member.fname,
        lname=member.lname,
        email=member.email,
        phone=member.phone,
        status=member.status
    )
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member

@app.get("/members/{member_id}", response_model=MemberCreate)
def read_member(member_id: int, db: Session = Depends(get_db)):
    db_member = db.query(Member).filter(Member.id == member_id).first()
    if db_member is None:
        raise HTTPException(status_code=404, detail="Member not found")
    return db_member

@app.put("/members/{id}")
def update_member(id: int, member_data: MemberCreate, db: Session = Depends(get_db)):
    member = db.query(Member).filter(Member.id == id).first()
    if not member:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update other fields
    member.username = member_data.username
    member.fname = member_data.fname
    member.lname = member_data.lname
    member.email = member_data.email
    member.phone = member_data.phone
    member.status = member_data.status
    
    # If a new password is provided, hash it
    if member_data.password:
        member.password = hash_password(member_data.password)
    
    db.commit()
    db.refresh(member)
    
    return member

@app.get("/members/", response_model=List[MemberResponse])
def read_members(db: Session = Depends(get_db)):
    members = db.query(Member).all()
    return members


@app.get("/members/{id}")
def get_member(id: int, db: Session = Depends(get_db)):
    member = db.query(Member).filter(Member.id == id).first()
    if not member:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": member.id,
        "username": member.username,
        "fname": member.fname,
        "lname": member.lname,
        "email": member.email,
        "phone": member.phone,
        "status": member.status,
        "password": member.password,
    }


@app.delete("/members/{member_id}")
def delete_member(member_id: int, db: Session = Depends(get_db)):
    db_member = db.query(Member).filter(Member.id == member_id).first()
    if db_member is None:
        raise HTTPException(status_code=404, detail="Member not found")
    db.delete(db_member)
    db.commit()
    return {"detail": "Member deleted"}

@app.post("/login/")
def login(data: LoginData, db: Session = Depends(get_db)):
    db_user = db.query(Member).filter(Member.username == data.username).first()
    if not db_user or not verify_password(db_user.password, data.password):
        raise HTTPException(status_code=400, detail="ชื่อผู้ใช้งานหรือรหัสผ่านไม่ถูกต้อง")

    return {
        "user_id": db_user.id,
        "username": db_user.username,
        "status": db_user.status,
        "name": f"{db_user.fname} {db_user.lname}"
    }




def check_existing_prediction(db: Session, year: int, month: int):
    existing_predictions = db.query(PredictionTable).filter_by(year_current=year, month_current=month).all()
    return existing_predictions


def save_prediction_to_db(db: Session, predictions: List[dict]):
    for prediction in predictions:
        new_record = PredictionTable(
            building=prediction['building'],
            area=prediction['area'],
            prediction=prediction['prediction'],
            unit=prediction['unit'],
            modelName=prediction['modelName'],
            month_current=prediction['month_current'],
            year_current=prediction['year_current'],
            month_predict=prediction['month_predict'],
            year_predict=prediction['year_predict'],
        )
        db.add(new_record)
    db.commit()


@app.post("/predict-or-fetch", response_model=List[PredictionResponse])
def predict_or_fetch(request: PredictionRequest, db: Session = Depends(get_db)) -> List[PredictionResponse]:
    try:
        # ตรวจสอบว่ามีข้อมูลในฐานข้อมูลหรือไม่
        existing_predictions = check_existing_prediction(db, request.year, request.month)
        
        if existing_predictions:
            # ถ้ามีข้อมูลแล้วให้ดึงข้อมูลมาแสดง
            return existing_predictions
        else:
            # ถ้าไม่มีข้อมูล ให้ทำการพยากรณ์
            predictions = predict(request, db)
            # บันทึกผลลัพธ์ลงในฐานข้อมูล
            save_prediction_to_db(db, predictions)
            return predictions
    finally:
        # เมื่อประมวลผลเสร็จสั่งให้รีหน้าเว็บ
        refresh_page()

def refresh_page():
    # สั่งให้รีเฟรชหน้าเว็บโดยการส่งสัญญาณให้ frontend รีเฟรช
    # คุณสามารถใช้ WebSocket หรือ Event-based approach เพื่อแจ้งเตือน frontend
    pass


def get_latest_year_month(db: Session):
    latest_entry = db.query(PredictionTable).order_by(PredictionTable.year_current.desc(), PredictionTable.month_current.desc()).first()
    if latest_entry:
        return latest_entry.year_current, latest_entry.month_current
    else:
        return None, None  # หากไม่มีข้อมูลในฐานข้อมูล
    
@app.get("/current-month")
def get_current_month(db: Session = Depends(get_db)):
    latest_record = db.query(Unit).order_by(Unit.years.desc(), Unit.month.desc()).first()
    if not latest_record:
        raise HTTPException(status_code=404, detail="No data found")
    return {"year": latest_record.years, "month": latest_record.month}

@app.get("/check-predictions")
def check_predictions(year: int = Query(...), month: int = Query(...), db: Session = Depends(get_db)):
    predictions = db.query(PredictionTable).filter_by(year_current=year, month_current=month).all()
    
    if not predictions:
        return []
    
    return predictions


@app.get("/latest-usage")
def get_latest_usage(db: Session = Depends(get_db)):
    latest_record = db.query(Unit.years, Unit.month).order_by(Unit.years.desc(), Unit.month.desc()).first()

    if not latest_record:
        raise HTTPException(status_code=404, detail="No data found")

    latest_year, latest_month = latest_record

    total_usage = db.query(func.sum(Unit.usage)).filter(Unit.years == latest_year, Unit.month == latest_month).scalar()

    return {
        "year": latest_year,
        "month": latest_month,
        "total_usage": total_usage  # Return the sum of electricity usage
    }

@app.get("/forecast-data")
def get_forecast_data(db: Session = Depends(get_db)):
    # ค้นหาข้อมูลล่าสุด
    latest_prediction = db.query(
        PredictionTable.month_current, 
        PredictionTable.year_current
    ).order_by(PredictionTable.year_current.desc(), PredictionTable.month_current.desc()).first()

    if not latest_prediction:
        return {"error": "No forecast data available"}

    month_start = latest_prediction.month_current
    year_start = latest_prediction.year_current

    # คำนวณ 6 เดือนย้อนหลัง
    start_date = datetime(year_start, month_start, 1) - timedelta(days=180)
    start_year = start_date.year
    start_month = start_date.month

    # ดึงข้อมูลจริง 6 เดือนล่าสุด
    actual_data = db.query(
        Unit.month,
        Unit.years,
        func.sum(Unit.amount).label('actual_amount')
    ).filter(
        (Unit.years == start_year) & (Unit.month >= start_month)
        | (Unit.years == year_start) & (Unit.month <= month_start)
    ).group_by(Unit.month, Unit.years).order_by(Unit.years.asc(), Unit.month.asc()).all()

    print("Actual Data:", actual_data)  # Debugging print statement

    # ดึงข้อมูลการพยากรณ์
    forecast_data = db.query(
        PredictionTable.month_predict,
        PredictionTable.year_predict,
        func.sum(PredictionTable.prediction).label('forecast_sum')
    ).group_by(PredictionTable.month_predict, PredictionTable.year_predict).order_by(PredictionTable.year_predict.asc(), PredictionTable.month_predict.asc()).all()

    print("Forecast Data:", forecast_data)  # Debugging print statement

    # เตรียมข้อมูลผลลัพธ์
    result = []
    for item in actual_data:
        thai_month_name = get_thai_month_name(item.month)
        year = str(item.years + 543)[-2:]  # แสดงปีเป็น พ.ศ. และใช้สองหลักสุดท้าย
        result.append({
            "month": f"{thai_month_name} {year}",
            "actual": item.actual_amount,
            "forecast": None  # Placeholder for forecast data
        })

    for data in forecast_data:
        thai_month_name = get_thai_month_name(data.month_predict)
        year = str(data.year_predict + 543)[-2:]  # แสดงปีเป็น พ.ศ. และใช้สองหลักสุดท้าย
        result.append({
            "month": f"{thai_month_name} {year}",
            "actual": None,  # No actual data for forecasted months
            "forecast": data.forecast_sum
        })

    result.sort(key=lambda x: (int(x["month"].split()[1]), get_thai_month_index(x["month"].split()[0])))

    print("Result Data:", result)  # Debugging print statement

    return result

# ฟังก์ชันที่แปลงเดือนเป็นตัวย่อภาษาไทย
def get_thai_month_name(month_number):
    thai_months_abbr = [
        "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.",
        "พ.ค.", "มิ.ย.", "ก.ค.",
        "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."
    ]
    return thai_months_abbr[month_number - 1]

# ฟังก์ชันที่แปลงชื่อเดือนภาษาไทยกลับเป็นหมายเลขเดือน
def get_thai_month_index(thai_month_name):
    thai_months = [
        "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.",
        "พ.ค.", "มิ.ย.", "ก.ค.",
        "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."
    ]
    return thai_months.index(thai_month_name) + 1

thai_months = {
    1: "ม.ค.", 2: "ก.พ.", 3: "มี.ค.", 4: "เม.ย.", 5: "พ.ค.", 6: "มิ.ย.",
    7: "ก.ค.", 8: "ส.ค.", 9: "ก.ย.", 10: "ต.ค.", 11: "พ.ย.", 12: "ธ.ค."
}

@app.get("/prediction_sum_by_month", response_model=List[PredictionResponse])
def get_prediction_sum_by_month(db: Session = Depends(get_db)):
    results = db.query(
        PredictionTable.month_predict,
        PredictionTable.year_predict,
        func.sum(PredictionTable.prediction).label("prediction_sum")
    ).group_by(
        PredictionTable.month_predict,
        PredictionTable.year_predict
    ).order_by(
        PredictionTable.year_predict,
        PredictionTable.month_predict
    ).all()

    formatted_results = []
    for result in results:
        # Convert year to Buddhist calendar and get the last two digits
        year_buddhist = (result.year_predict + 543) % 100
        
        formatted_result = PredictionResponse(
            prediction=result.prediction_sum,
            month_predict=thai_months.get(result.month_predict, "Unknown"),
            year_predict=year_buddhist  # Send only the last two digits of the year
        )
        formatted_results.append(formatted_result)

    return formatted_results


@app.get("/building_predictions/{year}/{month}")
def get_building_predictions(year: int, month: int, db: Session = Depends(get_db)):
    # แปลงปีจาก 2 ตัวท้ายของ พ.ศ. ให้เป็นปีเต็ม (พ.ศ.)
    full_be_year = 2500 + year if year < 100 else year + 543

    results = db.query(
        Building.code.label("building_code"),
        func.sum(PredictionTable.prediction).label("total_prediction")
    ).join(Building, PredictionTable.building == Building.id)\
    .filter(
        PredictionTable.year_predict == full_be_year,
        PredictionTable.month_predict == month
    ).group_by(
        Building.code
    ).all()

    if not results:
        raise HTTPException(status_code=404, detail="No data found for the specified month and year")

    return [
        {
            "building": result.building_code,
            "prediction": float(result.total_prediction)
        }
        for result in results
    ]


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.get("/prediction_sum_by_month", response_model=PeriodSums)
def get_prediction_sum_by_month(db: Session = Depends(get_db)):
    try:
        # Fetch all predictions, ordered by year ascending and then by month ascending
        predictions = db.query(
            PredictionTable.year_predict,
            PredictionTable.month_predict,
            func.sum(PredictionTable.prediction).label("total_prediction")
        ).group_by(
            PredictionTable.year_predict,
            PredictionTable.month_predict
        ).order_by(
            asc(PredictionTable.year_predict),
            asc(PredictionTable.month_predict)
        ).all()

        if not predictions:
            raise HTTPException(status_code=404, detail="No prediction data found")

        # Log all fetched predictions
        logger.info("Fetched predictions:")
        for p in predictions:
            logger.info(f"Year: {p.year_predict}, Month: {p.month_predict}, Prediction: {p.total_prediction}")

        # Ensure we have the correct first month value (which is now the last in the list)
        one_month = predictions[-1].total_prediction if predictions else 0
        logger.info(f"Most recent month value: {one_month}")

        # Calculate sums for different periods
        three_months = sum(p.total_prediction for p in predictions[-3:])
        six_months = sum(p.total_prediction for p in predictions[-6:])
        twelve_months = sum(p.total_prediction for p in predictions[-12:])

        logger.info(f"1 month sum: {one_month}")
        logger.info(f"3 months sum: {three_months}")
        logger.info(f"6 months sum: {six_months}")
        logger.info(f"12 months sum: {twelve_months}")

        # Convert month numbers to Thai abbreviations
        thai_months = {
            1: "ม.ค.", 2: "ก.พ.", 3: "มี.ค.", 4: "เม.ย.", 5: "พ.ค.", 6: "มิ.ย.",
            7: "ก.ค.", 8: "ส.ค.", 9: "ก.ย.", 10: "ต.ค.", 11: "พ.ย.", 12: "ธ.ค."
        }

        monthly_data = [
            PredictionSumResponse(
                year_predict=p.year_predict,
                month_predict=thai_months[p.month_predict],
                prediction=p.total_prediction
            ) for p in predictions
        ]

        # Return the PeriodSums object
        return PeriodSums(
            one_month=one_month,
            three_months=three_months,
            six_months=six_months,
            twelve_months=twelve_months,
            monthly_data=monthly_data
        )

    except Exception as e:
        logger.error(f"Error in get_prediction_sum_by_month: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
def get_thai_month_name(month_number):
    thai_months = [
        "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.",
        "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.",
        "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."
    ]
    return thai_months[month_number - 1]

@app.get("/yearly-comparison")
def get_yearly_comparison(db: Session = Depends(get_db)) -> List[Dict]:
    # Step 1: Find the latest year and current month available in the predictiontable
    latest_prediction = db.query(
        PredictionTable.year_current,
        PredictionTable.month_current
    ).order_by(PredictionTable.year_current.desc(), PredictionTable.month_current.desc()).first()

    if not latest_prediction:
        raise HTTPException(status_code=404, detail="No forecast data available")

    latest_year = latest_prediction.year_current
    previous_year = latest_year - 1

    # Step 2: Fetch forecast data across the entire range of months and years
    forecast_data = db.query(
        PredictionTable.month_predict,
        PredictionTable.year_predict,
        func.sum(PredictionTable.prediction).label("forecast_sum")
    ).group_by(PredictionTable.year_predict, PredictionTable.month_predict)\
    .order_by(PredictionTable.year_predict.asc(), PredictionTable.month_predict.asc()).all()

    # Step 3: Fetch actual data across the entire range of months and years
    actual_data = db.query(
        Unit.month,
        Unit.years,
        func.sum(Unit.amount).label("actual_sum")
    ).group_by(Unit.years, Unit.month)\
    .order_by(Unit.years.asc(), Unit.month.asc()).all()

    # Create a dictionary for quick lookup of actual data by year and month
    actual_dict = {(a.years, a.month): a.actual_sum for a in actual_data}

    # Step 4: Organize data for comparison
    result = []
    for forecast in forecast_data:
        year = forecast.year_predict
        month = forecast.month_predict
        forecast_value = int(forecast.forecast_sum)  # Convert forecast to integer
        actual_value = actual_dict.get((year - 1, month), None)  # Get actual value for the same month but from the previous year

        # Prepare actual_year_month in the same pattern
        actual_year_month = f"{get_thai_month_name(month)} {year - 1 + 543}"

        thai_month_name = get_thai_month_name(month)
        result.append({
            "month": f"{thai_month_name} {year + 543}",  # Convert to BE
            "forecast": forecast_value,
            "actual": int(actual_value) if actual_value is not None else 0,  # Ensure we use 0 if no match, convert to integer
            "actual_year_month": actual_year_month  # Include actual year and month in the same pattern
        })

    return result

@app.get("/group-prediction-sum")
def get_group_prediction_sum(db: Session = Depends(get_db)) -> List[Dict]:
    # Step 1: Fetch sum of predictions grouped by idGroup with group name
    group_summary = db.query(
        GroupBuilding.id,  # Fetch the id of the group for filtering
        GroupBuilding.name,  # Fetch group name from groupbuilding table
        func.sum(PredictionTable.prediction).label("prediction_sum")
    ).join(Building, Building.idGroup == GroupBuilding.id)\
    .join(PredictionTable, PredictionTable.building == Building.id)\
    .group_by(GroupBuilding.id, GroupBuilding.name).all()

    if not group_summary:
        raise HTTPException(status_code=404, detail="No prediction data available")

    result = []

    # Step 2: For each group, fetch building details and their prediction
    for group_id, group_name, prediction_sum in group_summary:
        building_details = db.query(
            Building.name,
            func.sum(PredictionTable.prediction).label("building_prediction_sum")
        ).join(PredictionTable, PredictionTable.building == Building.id)\
        .filter(Building.idGroup == group_id)\
        .group_by(Building.name).all()

        buildings_data = [{"name": name, "prediction": pred} for name, pred in building_details]

        result.append({
            "group_name": group_name,  # Use the group name instead of idGroup
            "prediction_sum": prediction_sum,
            "buildings": buildings_data
        })

    return result


@app.get("/numberofusers")
def get_number_of_users(db: Session = Depends(get_db)):
    users = db.query(NumberOfUsers).all()
    return users

@app.post("/add-numberofusers/")
def add_number_of_users(user: NumberOfUsersCreate, db: Session = Depends(get_db)):
    print("Received data:", user)
    for month in range(1, 13):
        db_user = NumberOfUsers(
            years=user.years,
            month=month,
            amount=user.amount
        )
        db.add(db_user)
    db.commit()
    
    # ส่งข้อความตอบกลับว่าข้อมูลถูกเพิ่มเรียบร้อยแล้ว
    return {"message": "Data added successfully"}


@app.put("/update-numberofusers/{id}")
def update_number_of_users(id: int, user: NumberOfUsersCreate, db: Session = Depends(get_db)):
    db_user = db.query(NumberOfUsers).filter(NumberOfUsers.id == id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # อัปเดตข้อมูลใหม่
    db_user.years = user.years
    db_user.amount = user.amount
    db.commit()
    db.refresh(db_user)
    
    return {"message": "Data updated successfully"}


@app.delete("/delete-numberofusers/{id}")
def delete_number_of_users(id: int, db: Session = Depends(get_db)):
    db_user = db.query(NumberOfUsers).filter(NumberOfUsers.id == id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(db_user)
    db.commit()
    
    return {"message": "Data deleted successfully"}


# GET - ดึงข้อมูลทั้งหมดจากตาราง groupbuilding
@app.get("/groupbuildings/", response_model=List[GroupBuildingResponse])
def get_groupbuildings(db: Session = Depends(get_db)):
    return db.query(GroupBuilding).all()

# POST - เพิ่มข้อมูลใหม่ในตาราง groupbuilding
@app.post("/groupbuildings/", response_model=GroupBuildingResponse)
def create_groupbuilding(groupbuilding: GroupBuildingCreate, db: Session = Depends(get_db)):
    db_groupbuilding = GroupBuilding(name=groupbuilding.name, about=groupbuilding.about)
    db.add(db_groupbuilding)
    db.commit()
    db.refresh(db_groupbuilding)
    return db_groupbuilding

# PUT - แก้ไขข้อมูลในตาราง groupbuilding
@app.put("/groupbuildings/{groupbuilding_id}", response_model=GroupBuildingResponse)
def update_groupbuilding(groupbuilding_id: int, updated_groupbuilding: GroupBuildingCreate, db: Session = Depends(get_db)):
    db_groupbuilding = db.query(GroupBuilding).filter(GroupBuilding.id == groupbuilding_id).first()
    if db_groupbuilding is None:
        raise HTTPException(status_code=404, detail="GroupBuilding not found")
    
    db_groupbuilding.name = updated_groupbuilding.name
    db_groupbuilding.about = updated_groupbuilding.about
    db.commit()
    db.refresh(db_groupbuilding)
    return db_groupbuilding

# DELETE - ลบข้อมูลในตาราง groupbuilding
@app.delete("/groupbuildings/{groupbuilding_id}")
def delete_groupbuilding(groupbuilding_id: int, db: Session = Depends(get_db)):
    db_groupbuilding = db.query(GroupBuilding).filter(GroupBuilding.id == groupbuilding_id).first()
    if db_groupbuilding is None:
        raise HTTPException(status_code=404, detail="GroupBuilding not found")
    
    db.delete(db_groupbuilding)
    db.commit()
    return {"message": "GroupBuilding deleted successfully"}





def get_user_by_email(db: Session, email: str):
    return db.query(Member).filter(Member.email == email).first()

class ForgotPasswordRequest(BaseModel):
    email: EmailStr
def generate_reset_token():
    token = secrets.token_urlsafe(16)  # สร้าง token แบบสุ่ม
    return hashlib.sha256(token.encode()).hexdigest()  # แฮช token เพื่อความปลอดภัยเพิ่มเติม

@app.post("/forgot-password/")
async def forgot_password(request: ForgotPasswordRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    user = get_user_by_email(db, request.email)
    if not user:
        raise HTTPException(status_code=404, detail="Email not found")

    # สร้าง reset token และบันทึกลงในฐานข้อมูล
    user.reset_token = generate_reset_token()
    db.commit()

    # สร้างลิงก์รีเซ็ตรหัสผ่านที่รวมทั้ง ID และ token
    reset_link = f"http://localhost/reset-password/{user.id}/{user.reset_token}"
    background_tasks.add_task(send_reset_email, request.email, reset_link)

    return {"message": "Password reset email sent"}

@app.post("/reset-password/{member_id}/{token}")
async def reset_password(member_id: int, token: str, request: ResetPasswordRequest, db: Session = Depends(get_db)):
    member = db.query(Member).filter(Member.id == member_id, Member.reset_token == token).first()
    if not member:
        raise HTTPException(status_code=404, detail="Invalid token or user not found")
    
    # แฮชรหัสผ่านใหม่และบันทึกในฐานข้อมูล
    member.password = hash_password(request.password)
    member.reset_token = None  # ลบ token เพื่อป้องกันการใช้ซ้ำ
    db.commit()

    return {"message": "Password reset successfully"}


load_dotenv()  # โหลดตัวแปรจากไฟล์ .env

def send_reset_email(email_to: str, reset_link: str):
    email_sender = os.getenv("EMAIL_SENDER")
    email_password = os.getenv("EMAIL_PASSWORD")

    message = MIMEMultipart("alternative")
    message["Subject"] = "เปลี่ยนรหัสผ่านเข้าใช้งาน (Reset password)"
    message["From"] = email_sender
    message["To"] = email_to

    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; background-color: #ffffff; color: #333333;">
        <div style="text-align: center; padding: 20px; background-color: #4B0082; color: white;">
            <h2>เปลี่ยนรหัสผ่านเข้าใช้งาน (Reset password)</h2>
        </div>
        <div style="padding: 30px; text-align: center;">
            <p>คุณได้กดลืมรหัสผ่านในการลงชื่อเข้าใช้งานระบบการพยากรณ์การใช้ไฟฟ้า มหาวิทยาลัยลัยลักษณ์</p>
            <a href="{reset_link}" style="display: inline-block; padding: 10px 20px; margin: 20px 0; background-color: #FF7F50; color: white; text-decoration: none; border-radius: 10px;">
                กดที่นี่เพื่อเปลี่ยนรหัสผ่าน
            </a>
            <p>ลิงค์นี้สามารถใช้งานได้เพียงครั้งเดียวเท่านั้น</p>
            <p>หากคุณไม่ได้เป็นผู้ดำเนินการกด “ลืมรหัสผ่าน” ไม่ต้องสนใจ email ฉบับนี้</p>
        </div>
    </body>
    </html>
    """

    part = MIMEText(html, "html")
    message.attach(part)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(email_sender, email_password)
            server.sendmail(email_sender, email_to, message.as_string())
        print("Email sent successfully.")
    except smtplib.SMTPAuthenticationError as e:
        print(f"SMTPAuthenticationError: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

# ฟังก์ชันเก็บไฟล์อัพโหลด
def save_file(upload_file: UploadFile, directory: str) -> str:
    file_location = os.path.join(directory, f"{uuid4().hex}_{upload_file.filename}")
    try:
        with open(file_location, "wb") as f:
            f.write(upload_file.file.read())
        return file_location
    except Exception as e:
        logging.error(f"Error saving file: {e}")
        raise HTTPException(status_code=500, detail="Error saving file")


# API สำหรับสร้างข่าวใหม่
@app.post("/news/")
async def create_news(
    title: str = Form(...),
    content: str = Form(...),
    cover_image: UploadFile = File(...),
    attachment: UploadFile = File(...)
):
    # บันทึกภาพปก
    cover_image_path = f"src/img/news/{cover_image.filename}"
    with open(cover_image_path, "wb") as image_file:
        shutil.copyfileobj(cover_image.file, image_file)
    
    # บันทึกไฟล์แนบ
    attachment_path = f"src/img/news/{attachment.filename}"
    with open(attachment_path, "wb") as attachment_file:
        shutil.copyfileobj(attachment.file, attachment_file)

    # บันทึกข้อมูลข่าวในฐานข้อมูล
    db = SessionLocal()
    new_news = News(
        title=title,
        content=content,
        cover_image=cover_image.filename,
        attachment=attachment.filename
    )
    db.add(new_news)
    db.commit()
    db.refresh(new_news)
    db.close()

    return JSONResponse(content={"message": "News created successfully!", "news_id": new_news.id})

# Endpoints สำหรับดึงข้อมูลข่าวทั้งหมด
@app.get("/news/")
def get_news():
    db = SessionLocal()
    news_list = db.query(News).all()
    db.close()
    return news_list

# Endpoint สำหรับดึงรายละเอียดข่าวโดยใช้ ID
@app.get("/news/{news_id}")
def get_news_detail(news_id: int):
    db = SessionLocal()
    news_item = db.query(News).filter(News.id == news_id).first()
    db.close()
    if not news_item:
        raise HTTPException(status_code=404, detail="News not found")
    return news_item
# เสิร์ฟไฟล์ static (เช่น ภาพ) จาก backend/src/img/news
app.mount("/images", StaticFiles(directory="src/img/news"), name="images")

# อัปเดตข้อมูลข่าว
@app.put("/news/{news_id}")
def update_news(news_id: int, news: NewsUpdate, db: Session = Depends(get_db)):
    news_item = db.query(News).filter(News.id == news_id).first()
    
    if not news_item:
        raise HTTPException(status_code=404, detail="News not found")
    
    # อัปเดตข้อมูลในฐานข้อมูลตามที่ส่งมา
    if news.title:
        news_item.title = news.title
    if news.content:
        news_item.content = news.content
    if news.cover_image:
        news_item.cover_image = news.cover_image
    if news.attachment:
        news_item.attachment = news.attachment

    db.commit()  # บันทึกการเปลี่ยนแปลง
    db.refresh(news_item)  # รีเฟรชข้อมูลที่ถูกอัปเดต

    return {"message": "News updated successfully", "data": news_item}


@app.delete("/news/{news_id}")
def delete_news(news_id: int, db: Session = Depends(get_db)):
    news_item = db.query(News).filter(News.id == news_id).first()
    
    if not news_item:
        raise HTTPException(status_code=404, detail="News not found")

    db.delete(news_item)
    db.commit()  # บันทึกการเปลี่ยนแปลงในฐานข้อมูล

    return {"message": "News deleted successfully"}
