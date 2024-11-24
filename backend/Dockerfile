# ใช้ base image
FROM python:3.11-slim

# ตั้งค่า working directory
WORKDIR /app

# ติดตั้ง dependencies ที่จำเป็น
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    pkg-config \
    libmariadb-dev && \
    apt-get clean

# คัดลอกไฟล์ requirements.txt
COPY requirements.txt /app/

# ติดตั้ง Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# คัดลอกไฟล์ทั้งหมด
COPY . .

# เปิดพอร์ต 8000
EXPOSE 8000

# รัน FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
