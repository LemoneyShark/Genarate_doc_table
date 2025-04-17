import os
from dotenv import load_dotenv

# โหลด .env
load_dotenv()

# ตั้งค่าข้อมูลเชื่อมต่อ MongoDB
MONGO_URI = os.getenv("MONGO_URI")

# ตั้งค่าเดือนและปี
month_filter = 12
year_filter = 2024
department_filter = "วิสัญญี"  # อายุรกรรม วิสัญญี กุมารเวช
table_type = "ตารางประจำเดือน"  # สามารถเปลี่ยนเป็น Transplant ตารางประจำเดือน คลินิคนอกเวลา / Gastoenterology ตารางเวร R1 Resident Neurology

# ตั้งค่า path สำหรับ wkhtmltoimage
WKHTMLTOIMAGE_PATH = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltoimage.exe"

# ชื่อเดือนภาษาไทย
month_names = {
    1: "มกราคม", 2: "กุมภาพันธ์", 3: "มีนาคม", 4: "เมษายน",
    5: "พฤษภาคม", 6: "มิถุนายน", 7: "กรกฎาคม", 8: "สิงหาคม",
    9: "กันยายน", 10: "ตุลาคม", 11: "พฤศจิกายน", 12: "ธันวาคม"
}

# ตั้งค่าหัวข้อตามประเภทตาราง
title_mapping = {
    "คลินิคนอกเวลา": "ผู้ป่วยนอก",
}