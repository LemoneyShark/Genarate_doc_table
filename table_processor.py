import pandas as pd
import re
from utils import natural_sort_key, custom_sort_key
from config import table_type

def format_ward_display(ward):
    """ฟังก์ชันสำหรับจัดรูปแบบการแสดงผลของ ward"""
    # กรณี ward มีรูปแบบเช่น "25 C-128 C" -> "25 C-1,28 C"
    if "-" in ward and not re.search(r'-\d+,', ward):
        parts = ward.split("-")
        if len(parts) == 2:
            left_part = parts[0].strip()
            right_part = parts[1].strip()
            
            # หาตำแหน่งที่จะแทรกเครื่องหมายจุลภาค
            # กรณี "128 C" -> "1,28 C"
            match = re.search(r'(\d+)(\s*[A-Za-z].*)', right_part)
            if match:
                numbers = match.group(1)
                suffix = match.group(2)
                if len(numbers) > 1:
                    formatted_right = f"{numbers[0]},{numbers[1:]}{suffix}"
                    return f"{left_part}-{formatted_right}"
    
    # กรณี ward มีรูปแบบเช่น "26 A27 C" -> "26 A,27 C"
    match = re.search(r'(\d+\s*[A-Za-z])(\d+\s*[A-Za-z])', ward)
    if match:
        first_part = match.group(1)
        second_part = match.group(2)
        return f"{first_part},{second_part}"
    
    # กรณีอื่นๆ ไม่ต้องเปลี่ยนแปลง
    return ward

def process_table_data(df):
    """ประมวลผลข้อมูลตารางและจัดรูปแบบ"""
    # 1. ดึง role จากข้อมูล
    roles = df["role"].dropna().unique().tolist() if "role" in df.columns else ["Staff"]
    roles.sort(key=lambda x: [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', str(x))])

    # 2. สร้างโครงสร้างข้อมูลแบบ hierarchy ใหม่ให้รองรับ period_w และ period_h
    role_data_mapping = {}
    
    for role in roles:
        # กรองข้อมูลตาม role
        role_data = df[df["role"] == role] if "role" in df.columns else df
        
        # ตรวจสอบว่ามี period_w หรือไม่
        if "period_w" in df.columns:
            period_ws = role_data["period_w"].dropna().unique().tolist()
        else:
            period_ws = [""]  # ถ้าไม่มี ใช้ค่าว่าง
        
        # เก็บข้อมูลลงใน mapping
        role_data_mapping[role] = {}
        
        for period_w in period_ws:
            # กรองข้อมูลตาม period_w
            period_w_data = role_data[role_data["period_w"] == period_w] if "period_w" in df.columns and period_w != "" else role_data
            
            # ตรวจสอบว่ามี period_h หรือไม่
            if "period_h" in df.columns:
                period_hs = period_w_data["period_h"].dropna().unique().tolist()
            else:
                period_hs = [""]  # ถ้าไม่มี ใช้ค่าว่าง
            
            role_data_mapping[role][period_w] = {}
            
            for period_h in period_hs:
                # กรองข้อมูลตาม period_h
                period_h_data = period_w_data[period_w_data["period_h"] == period_h] if "period_h" in df.columns and period_h != "" else period_w_data
                
                # ดึง ward ที่เกี่ยวข้อง
                wards = period_h_data["ward"].dropna().unique().tolist()
                wards.sort(key=natural_sort_key)
                
                role_data_mapping[role][period_w][period_h] = wards

    # สร้าง header_tuples และ column_keys
    header_tuples = [
        ("", "", "", "Day", ""),
        ("", "", "", "Date", "")
    ]
    
    column_keys = []
    
    # สร้าง header tuples ตามโครงสร้างใหม่
    for role in roles:
        for period_w, period_h_data in role_data_mapping[role].items():
            for period_h, wards in period_h_data.items():
                for ward in wards:
                    # จัดรูปแบบการแสดงผล ward ใหม่
                    display_ward = format_ward_display(ward)
                    
                    # ตรวจสอบว่ามี subward หรือไม่
                    if "subward" in df.columns:
                        subward_data = df[
                            (df["role"] == role) & 
                            ((df["period_w"] == period_w) if "period_w" in df.columns and period_w != "" else True) &
                            ((df["period_h"] == period_h) if "period_h" in df.columns and period_h != "" else True) &
                            (df["ward"] == ward)
                        ]
                        
                        subwards = subward_data["subward"].dropna().unique().tolist()
                        if subwards:
                            subward_order = {
                                "Chief": 1,
                                "SICU": 2, 
                                "CVT ICU": 3,
                                "Stroke" : 1,"Non Stroke" : 2,
                                
                            }
                            
                            # เรียงลำดับ subward
                            subwards = sorted(subwards, key=lambda x: subward_order.get(x, 999))

                            for subward in subwards:
                                # ใช้ display_ward แทน ward ตอนสร้าง header_tuples
                                header_tuples.append((role, period_w, period_h, display_ward, subward))
                                # แต่ยังคงใช้ ward เดิมใน column_keys เพื่อการ reference
                                column_keys.append(f"{role}|{period_w}|{period_h}|{ward}|{subward}")
                        else:
                            # ไม่มี subward
                            header_tuples.append((role, period_w, period_h, display_ward, ""))
                            column_keys.append(f"{role}|{period_w}|{period_h}|{ward}|")
                    else:
                        # ไม่มีฟิลด์ subward
                        header_tuples.append((role, period_w, period_h, display_ward, ""))
                        column_keys.append(f"{role}|{period_w}|{period_h}|{ward}|")

    # เรียงลำดับ header เพื่อให้แสดงเป็นระเบียบ (แยก Day, Date ออกก่อน)
    day_date_tuples = [header_tuples[0], header_tuples[1]]  # Day, Date
    content_tuples = header_tuples[2:]  # เนื้อหาอื่นๆ
    
    # เรียงลำดับตามเงื่อนไขให้
    def custom_sort_key_extended(item):
        role, period_w, period_h, ward, _ = item
        
        # ต้องใช้ ward ที่ยังไม่ได้จัดรูปแบบสำหรับการเรียงลำดับ
        # หา ward ดั้งเดิมจาก column_keys
        original_ward = ""
        for key in column_keys:
            parts = key.split("|")
            if parts[0] == role and parts[1] == period_w and parts[2] == period_h and format_ward_display(parts[3]) == ward:
                original_ward = parts[3]
                break
        
        if not original_ward:
            original_ward = ward
        
        # เรียงลำดับ role ตาม special_order
        special_order = {
            "R1": 1, "R2": 2, "R3": 3, "Fellow": 4, "Staff": 5,
            "Stroke" : 1,"Non Stroke" : 2,
        }
        role_priority = special_order.get(role, 999)
        
        # เรียงลำดับ period_w (เช่น เวลาช่วงเช้า กลางวัน เย็น)
        period_w_order = {
            "เช้า": 1, "กลางวัน": 2, "เย็น": 3, "ดึก": 4
        }
        period_w_priority = period_w_order.get(period_w, 999)
        
        # เรียงลำดับ period_h (เช่น เวลา 8-12, 12-16, ฯลฯ)
        # สมมติว่า period_h อาจมีรูปแบบเช่น "8-12", "12-16" เป็นต้น
        period_h_start = 0
        if period_h and "-" in period_h:
            try:
                period_h_start = int(period_h.split("-")[0])
            except:
                period_h_start = 0
        
        # เพิ่ม special_order สำหรับ ward
        ward_order = {
            "CVT": 1,"CRITICAL CARE": 2,"PAIN": 3,"PED": 4,
            "เวร Day" : 1,"เวรทั้งวัน" : 2,
            "19 B-2" : 1,"19 B-1" : 2,"25 C-128 C" : 3,"26 A27 C":4,"26 B27 C":5,
            "วังบน" : 1,"วังล่าง" : 2,"ICU 1" : 3,"ICU 2":4,"CCU":5,"ER":6,"COVID":7,"COVID 2 (จก4)":8,"OPD 9 บ่าย":9,"OPD 9 เช้าวันหยุด":10,
            #Cardiology
            "F1" : 1,"F2" : 2,"F3 MRI / ECHO" : 3,"F3 EP":4,"F3 HF":5,"F3 Cath":6,
            #Nephrology
            "1st call" : 1,"Standby" : 2,"F3":3,
            "Stroke" : 10,"Non Stroke" : 11,
            #กุมาร R1
            "ภส.20C, 19C1-C2 18C 21C, 28B":1,"สก.15G1 ,G2 สก. 6":2,"Nursery":7,"OPD No.9":8,
            #กุมาร R2
            "สก/ภส.":1,"OPD9":6,
            #กุมาร R3
            "สก/ภูมิสิริ":1,"PICU":3,"NICU":4,"CRC":5,
        }
        
        # ตรวจสอบถ้า ward ตรงกับ key ใน ward_order ให้ใช้ค่าลำดับจาก dictionary
        ward_priority = 999
        for key, value in ward_order.items():
            if key in original_ward:
                ward_priority = value
                break
        
        # แยกส่วนที่เป็นตัวอักษรและตัวเลขใน ward
        ward_text = ''.join(re.findall(r'[A-Za-z]+', original_ward))
        ward_numbers = re.findall(r'\d+', original_ward)
        ward_number = int(ward_numbers[0]) if ward_numbers else 0
        
        # ส่งคืนลำดับความสำคัญของแต่ละส่วน โดยเพิ่ม ward_priority เข้าไป
        return (role_priority, period_w_priority, period_h_start, ward_priority, ward_text, ward_number)
    
    # เรียงลำดับเนื้อหา
    sorted_content_tuples = sorted(content_tuples, key=custom_sort_key_extended)
    
    # รวม tuples กลับเข้าด้วยกัน
    header_tuples = day_date_tuples + sorted_content_tuples
    
    # สร้าง column_keys ใหม่และ header_mapping เพื่อเชื่อมโยงระหว่าง header ที่แสดงผลกับ key จริง
    column_keys = []
    header_mapping = {}  # เก็บการเชื่อมโยงระหว่าง header ที่แสดงผลกับ key จริง
    
    for i, (role, period_w, period_h, display_ward, subward) in enumerate(header_tuples[2:]):  # ข้าม Day และ Date
        # หา ward ดั้งเดิม (original ward) จาก display_ward
        original_ward = ""
        for key in role_data_mapping[role][period_w][period_h]:
            if format_ward_display(key) == display_ward:
                original_ward = key
                break
        
        if not original_ward:
            original_ward = display_ward  # ถ้าหาไม่เจอใช้ display_ward แทน
        
        column_key = f"{role}|{period_w}|{period_h}|{original_ward}|{subward}"
        column_keys.append(column_key)
        
        # เก็บการเชื่อมโยงระหว่าง header ที่แสดงผลกับ key จริง
        header_tuple = (role, period_w, period_h, display_ward, subward)
        header_mapping[header_tuple] = column_key
    
    # รวมข้อมูลเข้า days_data
    days_data = {}
    
    for _, row in df.iterrows():
        # ตรวจสอบกรณีพิเศษสำหรับแผนก Gastroenterology
        if table_type == "Gastoenterology":
            # ถ้าไม่มี ward ให้ใช้ remark แทน
            ward = row.get("remark", "")
        else:
            # กรณีปกติ
            ward = row.get("ward", "")

        date_key = row["date_key"]
        day = row["day"]
        date_num = row["date_num"]
        role = row.get("role", roles[0])
        subward = row.get("subward", "")
        name = row.get("name", "")
        period_w = row.get("period_w", "")
        period_h = row.get("period_h", "")
        remark = row.get("remark", "")  # ดึงค่า remark จาก row
        
        if date_key not in days_data:
            # สร้าง dictionary สำหรับวันนี้
            day_entry = {
                "Day": day,
                "Date": date_num
            }
            # เพิ่มคอลัมน์ทั้งหมดเป็นค่าว่าง
            for column_key in column_keys:
                day_entry[column_key] = ""
            
            days_data[date_key] = day_entry
        
        # สร้าง key สำหรับเข้าถึงข้อมูลใน days_data
        column_key = f"{role}|{period_w}|{period_h}|{ward}|{subward}"
        
        # ถ้าไม่มี subward ให้ใช้ key แบบไม่มี subward
        if not subward and f"{role}|{period_w}|{period_h}|{ward}|" in days_data[date_key]:
            column_key = f"{role}|{period_w}|{period_h}|{ward}|"
        
        # เพิ่มชื่อลงในตาราง (ถ้ามี column_key นี้)
        if column_key in days_data[date_key]:
            current_value = days_data[date_key][column_key]
            
            # เพิ่ม remark ถ้ามี
            name_with_remark = name
            if remark:
                name_with_remark = f"{name} ({remark})"
                
            if current_value:
                # เก็บชื่อเป็น list แทนการเชื่อมต่อเป็น string
                if isinstance(current_value, list):
                    days_data[date_key][column_key].append(name_with_remark)
                else:
                    days_data[date_key][column_key] = [current_value, name_with_remark]
            else:
                days_data[date_key][column_key] = name_with_remark
    
    # แปลงเป็น DataFrame
    table_data = []
    for date_key, day_entry in sorted(days_data.items()):
        row_data = {"Day": day_entry["Day"], "Date": day_entry["Date"]}
        
        # เพิ่มข้อมูลสำหรับแต่ละคอลัมน์
        for i, (role, period_w, period_h, display_ward, subward) in enumerate(header_tuples[2:]):  # ข้าม Day และ Date
            column_key = column_keys[i]
            cell_value = day_entry.get(column_key, "")
            
            # ถ้ามีชื่อหลายคน (เป็น list) ให้เตรียมข้อมูลสำหรับแสดงผลแบบขึ้นบรรทัดใหม่
            if isinstance(cell_value, list):
                # แปลง list เป็น HTML ที่มีการขึ้นบรรทัดใหม่
                cell_value = "<br>".join([f"{name}," if i < len(cell_value)-1 else name 
                              for i, name in enumerate(cell_value)])
            
            row_data[(role, period_w, period_h, display_ward, subward)] = cell_value
        
        table_data.append(row_data)
    
    # สร้าง DataFrame จากข้อมูล
    table_df = pd.DataFrame(table_data)
    table_df.columns = pd.MultiIndex.from_tuples(header_tuples)
    
    return table_df, column_keys