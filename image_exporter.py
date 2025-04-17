import os
import uuid
import imgkit
from config import WKHTMLTOIMAGE_PATH, table_type, month_filter, year_filter, month_names, title_mapping

def export_to_image(html_content):
    """ส่งออกตารางเป็นรูปภาพตามค่าในไฟล์ config"""
    return export_to_image_with_params(html_content, table_type, month_filter, year_filter)

def export_to_image_with_params(html_content, table_type_param, month_filter_param, year_filter_param):
    """ส่งออกตารางเป็นรูปภาพโดยรับพารามิเตอร์โดยตรง"""
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
        target_html_file = f"{table_type_param}_{month_filter_param}_{year_filter_param}.html"
        target_png_file = f"{table_type_param}_{month_filter_param}_{year_filter_param}.png"
        
        # เปลี่ยนชื่อไฟล์
        if os.path.exists(target_html_file):
            os.remove(target_html_file)
        if os.path.exists(target_png_file):
            os.remove(target_png_file)
            
        os.rename(temp_html_file, target_html_file)
        os.rename(temp_png_file, target_png_file)
        
        month_name = month_names.get(month_filter_param, f"เดือน {month_filter_param}")
        title = title_mapping.get(table_type_param, f"ตาราง {table_type_param}")
        print(f"สร้างตาราง {title} สำหรับเดือน {month_name} {year_filter_param} เรียบร้อยแล้ว")
        
        return True
        
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการแปลงไฟล์: {e}")
        # ลบไฟล์ชั่วคราวในกรณีที่เกิดข้อผิดพลาด
        if os.path.exists(temp_html_file):
            os.remove(temp_html_file)
        if os.path.exists(temp_png_file):
            os.remove(temp_png_file)
        return False