from pymongo import MongoClient
import pandas as pd
from config import MONGO_URI, month_filter, year_filter, department_filter, table_type, month_names

def connect_to_mongodb():
    """เชื่อมต่อกับ MongoDB"""
    client = MongoClient(MONGO_URI)
    db = client["company"]
    collection = db["doc"]
    return collection

def load_schedule_data():
    """โหลดข้อมูลตารางจาก MongoDB"""
    collection = connect_to_mongodb()
    
    # ดึงข้อมูลและแปลงเป็น DataFrame - เพิ่ม filter ตาม type
    data = list(collection.find({
        "datetime": {"$exists": True, "$ne": None},
        "department": department_filter,
        "type": table_type,
        "$expr": {
            "$and": [
                {"$eq": [{"$month": "$datetime"}, month_filter]},
                {"$eq": [{"$year": "$datetime"}, year_filter]}
            ]
        }
    }))
    
    df = pd.DataFrame(data)
    if df.empty:
        month_name = month_names.get(month_filter, f"เดือน {month_filter}")
        print(f"ไม่พบข้อมูลสำหรับประเภท {table_type} ในเดือน {month_name} {year_filter}")
        return None
    
    # แปลง datetime เป็นวันที่ + ชื่อวัน
    df["datetime"] = pd.to_datetime(df["datetime"])
    df["day"] = df["datetime"].dt.strftime('%a')
    df["date_num"] = df["datetime"].dt.day
    df["date_key"] = df["datetime"].dt.strftime('%Y-%m-%d')
    
    return df