import re
from data_loader import load_schedule_data
from table_processor import process_table_data
from html_generator import generate_html
from image_exporter import export_to_image

def main():
    """เป็นจุดเริ่มต้นของโปรแกรม"""
    # 1. โหลดข้อมูล
    df = load_schedule_data()
    if df is None:
        return
    
    # 2. ประมวลผลข้อมูลตาราง
    table_df, column_keys = process_table_data(df)
    
    # 3. สร้าง HTML
    html_content = generate_html(table_df)
    
    # 4. ส่งออกเป็นรูปภาพ
    export_to_image(html_content)

if __name__ == "__main__":
    main()