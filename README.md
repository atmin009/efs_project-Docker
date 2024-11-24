
# 🚀 การพยากรณ์การใช้ไฟฟ้ารายเดือนของหน่วยการศึกษาโดยใช้เทคนิคการทำเหมืองข้อมูล กรณีศึกษา มหาวิทยาลัยวลัยลักษณ์

โปรเจกต์นี้ใช้ Docker เพื่อช่วยให้การรันบริการต่างๆ บน Localhost เป็นไปอย่างง่ายดาย คู่มือนี้จะช่วยแนะนำวิธีการ Clone โปรเจกต์จาก GitHub และการรัน Docker บนเครื่องของคุณ

---

## 📋 ความต้องการเบื้องต้น

ก่อนเริ่มต้น กรุณาติดตั้งโปรแกรมดังต่อไปนี้บนเครื่องของคุณ:

- [Git](https://git-scm.com/downloads)
- [Docker Desktop](https://www.docker.com/products/docker-desktop)
- [Docker Compose](https://docs.docker.com/compose/install/)

---

## 🛠️ ขั้นตอนการตั้งค่า

### 1. Clone โปรเจกต์จาก GitHub

1. เปิด Terminal หรือ Command Prompt บนเครื่องของคุณ
2. ไปยังไดเรกทอรีที่คุณต้องการเก็บโปรเจกต์
3. รันคำสั่งต่อไปนี้:
   ```bash
   git clone https://github.com/atmin009/efs_project-Docker.git
   ```
4. เข้าสู่โฟลเดอร์โปรเจกต์:
   ```bash
   cd efs_project-Docker
   ```

---

### 2. รัน Docker Containers

1. ตรวจสอบให้แน่ใจว่า Docker Desktop ทำงานอยู่
2. รันคำสั่งต่อไปนี้เพื่อ Build และเริ่มต้น Containers:
   ```bash
   docker-compose up --build
   ```
3. รอจน Docker ดึง Images ที่จำเป็นและเริ่ม Containers คุณจะเห็นข้อความแสดงสถานะใน Terminal

---

## 🌐 การเข้าถึงแอปพลิเคชัน

เมื่อ Containers เริ่มทำงานแล้ว คุณสามารถเข้าถึงแอปพลิเคชันได้ดังนี้:

- **แอปพลิเคชันหลัก**: [http://localhost:8080](http://localhost:8080)

---

## 🛑 การหยุด Containers

หากต้องการหยุด Containers ให้กด `Ctrl + C` ใน Terminal จากนั้นรันคำสั่ง:
```bash
docker-compose down
```

---


## 📂 โครงสร้างโปรเจกต์

```plaintext
efs_project-Docker/
│
├── docker-compose.yml   # ไฟล์สำหรับกำหนดค่าบริการของ Docker Compose
├── Dockerfile           # ไฟล์สำหรับสร้าง Docker Image
├── src/                 # โค้ดของแอปพลิเคชัน
├── init.sql             # สคริปต์ตั้งค่าฐานข้อมูลเบื้องต้น
├── README.md            # เอกสารประกอบโปรเจกต์ (ไฟล์นี้)
```

---

## 💡 เคล็ดลับ

- ใช้คำสั่ง `docker-compose logs` เพื่อดู Logs ของ Containers ในกรณีที่ต้องการแก้ไขปัญหา
- หากมีการเปลี่ยนแปลงโค้ด ให้รันคำสั่ง Build ใหม่:
  ```bash
  docker-compose up --build
  ```
- หากต้องการลบ Containers และเริ่มต้นใหม่ ให้ใช้:
  ```bash
  docker-compose down
  ```

---

🎉 **พบปัญหาการใช้งานกรุณาติดต่อ atmin009@gmail.com!**
