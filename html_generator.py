import pandas as pd
from config import month_names, month_filter, year_filter, department_filter, table_type, title_mapping

def highlight_weekend_rows(row):
    """ฟังก์ชั่นสำหรับไฮไลต์แถววันหยุดสุดสัปดาห์"""
    if row[("", "", "", "Day", "")] in ["Sat", "Sun"]:
        return ['background-color: #60B5FF'] * len(row)
    return ['background-color: #AFDDFF'] * len(row)

def generate_html(table_df):
    """สร้าง HTML จาก DataFrame"""
    # ดึงคอลัมน์จาก MultiIndex
    day_col = [col for col in table_df.columns if col[3] == "Day"]  # ปรับ index ตามโครงสร้างใหม่
    date_col = [col for col in table_df.columns if col[3] == "Date"]  # ปรับ index ตามโครงสร้างใหม่
    content_cols = [col for col in table_df.columns if col not in day_col and col not in date_col]
    
    # กำหนด title ตาม type
    title = title_mapping.get(table_type, f"{table_type}")
    
    # คำนวณจำนวนคอลัมน์ (ไม่นับคอลัมน์ Day และ Date)
    num_columns = len(content_cols)
    # กำหนดค่า zoom โดยขึ้นอยู่กับจำนวนคอลัมน์
    zoom_level = 0.33 if num_columns >= 6 else 1.0
    width_value = 3000 if num_columns >= 6 else 1200
    
    # สร้าง Styler
    styled = (
        table_df.style
        .hide(axis="index")
        .apply(highlight_weekend_rows, axis=1)
        .set_table_styles({
            **{
                col: [{'selector': 'th', 'props': [('background-color', '#1B56FD'), ('font-weight', 'bold'), ('color', 'white')]}]
                for col in day_col + date_col
            },
            **{
                col: [{'selector': 'th', 'props': [('background-color', '#1B56FD'), ('font-weight', 'bold'), ('color', 'white')]}]
                for col in content_cols
            },
        }, overwrite=False)
        .set_properties(**{
            'text-align': 'center',
            'font-family': 'Prompt',
            'padding': '10px'
        }).set_table_attributes('style="border-collapse:collapse; width:100%;"')
    )
    
    # ปรับแต่ง CSS เพิ่มเติมเพื่อรองรับส่วนหัวตารางหลายแถว
    css_styles = f"""
    @media print {{
        body {{
            zoom: {zoom_level}; /* สำหรับ Firefox */
            transform: scale({zoom_level}); /* สำหรับ browsers อื่นๆ */
            transform-origin: 0 0;
        }}
    }}
    
    body {{
        font-family: 'Prompt', sans-serif;
        background-color: #f7f9fc;
        padding: 20px;
        width: {width_value}px; /* ปรับตามจำนวนคอลัมน์ */
        max-width: {width_value}px;
    }}
    
    .table-container {{
        width: 100%;
        overflow-x: auto;
    }}
    
    h2, h3 {{
        margin: 0;
    }}
    
    table {{
        font-family: 'Prompt', sans-serif;
        border-collapse: separate;
        border-spacing: 0;
        width: 100%;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
        border-radius: 12px;
        overflow: hidden;
    }}
    
    th, td {{
        border: 1px solid white;
        padding: 8px; /* ลดขนาด padding */
        text-align: center;
        background-color: #AFDDFF;
        overflow: hidden;
    }}
    
    /* ถ้าคอลัมน์มีน้อย ให้ข้อความสามารถแสดงหลายบรรทัดได้ */
    td {{
        background-color: #fff;
        font-size: 14px; /* ปรับขนาดตัวอักษรให้พอดี */
        white-space: normal;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 150px; /* กำหนดความกว้างสูงสุดของเซลล์ */
        word-wrap: break-word;
        line-height: 1.5;
    }}
    
    th {{
        background-color: #1B56FD;
        color: white;
        font-weight: bold;
        border-right: 1px solid #ccc;
        border-bottom: 1px solid #ccc;
        font-size: 14px; /* ลดขนาดตัวอักษรสำหรับหัวตาราง */
        white-space: nowrap; /* headers ยังคงเป็นบรรทัดเดียวเสมอ */
    }}
    
    /* แสดงส่วนที่ว่างในหัวข้อเป็นโปร่งใส */
    th:empty {{
        background-color: transparent;
        border: none;
    }}
    
    /* ให้หัวข้อที่มีค่าว่างแสดงเป็นช่องว่าง */
    th:not(:empty) {{
        min-height: 36px;
    }}
    
    tr:nth-child(even) td {{
        background-color: #f1f6ff;
    }}
    """
    
    month_name = month_names.get(month_filter, f"เดือน {month_filter}")
    
    # สร้าง HTML content
    html_content = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
        {css_styles}
        </style>
        <link href="https://fonts.googleapis.com/css2?family=Prompt&display=swap" rel="stylesheet">
    </head>
    <body>
    <h2><center>ชื่อตาราง : {title}</center></h2>
    <h3><center>แผนก : {department_filter}</center></h3>
    <h3><center>ประจำเดือน : {month_name} {year_filter}</center></h3>
    <div class="table-container">
    {styled.to_html(escape=False)}
    </div>
    </body>
    </html>
    """
    
    return html_content