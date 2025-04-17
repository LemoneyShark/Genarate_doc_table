import re
import os
from flask import Flask, render_template, request, jsonify, send_file, make_response, abort
from data_loader import load_schedule_data
from table_processor import process_table_data
from html_generator import generate_html
from image_exporter import export_to_image
from config import month_filter as default_month_filter, year_filter as default_year_filter, department_filter as default_department_filter, table_type as default_table_type


app = Flask(__name__)   

@app.route("/")
def index():
    return jsonify("Yay")

@app.route("/gen_schedule", methods=["POST"])
def gen_schedule():
    try:
        # รับค่าจาก form data
        month = int(request.form.get("month_filter", default_month_filter))
        year = int(request.form.get("year_filter", default_year_filter))
        department = request.form.get("department_filter", default_department_filter)
        schedule_type = request.form.get("table_type", default_table_type)
        
        # ตรวจสอบข้อมูลที่รับมา
        if not (1 <= month <= 12):
            return jsonify({"error": "เดือนต้องอยู่ระหว่าง 1-12"}), 400
        
        # อัปเดตค่าใน config (อาจต้องสร้างฟังก์ชันเพิ่มเติมในโมดูลอื่น)
        from config import month_filter, year_filter, department_filter, table_type
        import config
        
        # กำหนดค่าชั่วคราวในรันไทม์
        config.month_filter = month
        config.year_filter = year
        config.department_filter = department
        config.table_type = schedule_type
        
        # 1.load Data
        df = load_schedule_data()
        if df is None:
            return jsonify({"error": "ไม่สามารถโหลดข้อมูลได้"}), 400
        
        # 2.Process
        table_df, column_keys = process_table_data(df)
        
        # 3.Create HTML
        html_content = generate_html(table_df)
        
        # 4.Export
        success = export_to_image(html_content)
        if not success:
            return jsonify({"error": "เกิดข้อผิดพลาดในการสร้างรูปภาพ"}), 500
        
        # 5.ส่งไฟล์กลับไปให้ผู้ใช้
        output_filename = f"{schedule_type}_{month}_{year}.png"
        
        # ตรวจสอบว่าไฟล์มีอยู่จริง
        if not os.path.exists(output_filename):
            return jsonify({"error": f"ไม่พบไฟล์ {output_filename}"}), 404
        
        # ส่งไฟล์กลับไปให้ผู้ใช้
        return send_file(
            output_filename,
            mimetype='image/png',
            as_attachment=True,
            download_name=output_filename
        )
        
    except Exception as e:
        return jsonify({"error": f"เกิดข้อผิดพลาด: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)