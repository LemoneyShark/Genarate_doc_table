import os
import uuid
import imgkit
from config import WKHTMLTOIMAGE_PATH, table_type, month_filter, year_filter, month_names, title_mapping

def export_to_image(html_content):
    """ส่งออกตารางเป็นรูปภาพ"""
    # ตั้งค่า path สำหรับ wkhtmltoimage
    config = imgkit.config(wkhtmltoimage=WKHTMLTOIMAGE_PATH)
    
    # สร้างชื่อไฟล์ชั่วคราว
    temp_html_file = f"temp_{uuid.uuid4().hex}.html"
    temp_png_file = f"temp_{uuid.uuid4().hex}.png"
    
    try:
        # บันทึกเป็น HTML ด้วยชื่อชั่วคราว
        with open(temp_html_file, "w", encoding='utf-8') as f:
            f.write(html_content)
        
        # แปลงเป็นรูปภาพ
        imgkit.from_file(temp_html_file, temp_png_file, config=config)
        
        # กำหนดชื่อไฟล์เป้าหมาย
        target_html_file = f"{table_type}_{month_filter}_{year_filter}.html"
        target_png_file = f"{table_type}_{month_filter}_{year_filter}.png"
        
        # เปลี่ยนชื่อไฟล์
        if os.path.exists(target_html_file):
            os.remove(target_html_file)
        if os.path.exists(target_png_file):
            os.remove(target_png_file)
            
        os.rename(temp_html_file, target_html_file)
        os.rename(temp_png_file, target_png_file)
        
        month_name = month_names.get(month_filter, f"เดือน {month_filter}")
        title = title_mapping.get(table_type, f"ตาราง {table_type} ")
        print(f"สร้างตาราง {title} สำหรับเดือน {month_name} {year_filter} เรียบร้อยแล้ว")
        
        return True
        
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการแปลงไฟล์: {e}")
        # ลบไฟล์ชั่วคราวในกรณีที่เกิดข้อผิดพลาด
        if os.path.exists(temp_html_file):
            os.remove(temp_html_file)
        if os.path.exists(temp_png_file):
            os.remove(temp_png_file)
        return False