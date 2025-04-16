import pandas as pd
import re
from utils import natural_sort_key, custom_sort_key
from config import table_type

def format_ward_display(ward):
    """ฟังก์ชันสำหรับจัดรูปแบบการแสดงผลของ ward"""
    # กรณีไม่มี ward
    if not ward:
        return ""
        
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

    # ตรวจสอบว่ามีฟิลด์ ward หรือควรใช้ remark แทน
    use_remark_as_ward = False
    if "ward" not in df.columns and "remark" in df.columns:
        use_remark_as_ward = True
        print(f"ไม่พบฟิลด์ 'ward' ในข้อมูล กำลังใช้ฟิลด์ 'remark' แทน")
    elif "ward" not in df.columns and "remark" not in df.columns:
        # ถ้าไม่มีทั้ง ward และ remark ให้สร้างคอลัมน์ ward เปล่า
        df["ward"] = ""
        print(f"ไม่พบทั้งฟิลด์ 'ward' และ 'remark' ในข้อมูล กำลังสร้างคอลัมน์ 'ward' เปล่า")

    # เพิ่มคอลัมน์ subward หากยังไม่มี และเก็บ remark เป็น subward ในกรณี Neurology
    if "subward" not in df.columns:
        df["subward"] = ""
    
    # กรณี Neurology: ถ้ามี ward และ remark ให้ใช้ remark เป็น subward
    if "ward" in df.columns and "remark" in df.columns and not use_remark_as_ward:
        print("พบทั้งฟิลด์ 'ward' และ 'remark' กำลังใช้ 'remark' เป็น subward")
        # คัดลอก remark ไปใส่ subward
        for idx, row in df.iterrows():
            if row.get("remark", ""):
                df.at[idx, "subward"] = row["remark"]

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
                if use_remark_as_ward:
                    wards = period_h_data["remark"].dropna().unique().tolist()
                else:
                    wards = period_h_data["ward"].dropna().unique().tolist()
                
                wards.sort(key=natural_sort_key)
                
                # เก็บข้อมูล ward และ subward
                role_data_mapping[role][period_w][period_h] = {}
                
                for ward in wards:
                    # กรองข้อมูลตาม ward
                    if use_remark_as_ward:
                        ward_data = period_h_data[period_h_data["remark"] == ward]
                    else:
                        ward_data = period_h_data[period_h_data["ward"] == ward]
                    
                    # ดึง subward ที่เกี่ยวข้อง
                    subwards = ward_data["subward"].dropna().unique().tolist()
                    
                    # เก็บ subward
                    role_data_mapping[role][period_w][period_h][ward] = subwards
    
    # สร้าง header_tuples และ column_keys
    header_tuples = [
        ("", "", "", "Day", ""),
        ("", "", "", "Date", "")
    ]
    
    column_keys = []
    
    # สร้าง header tuples ตามโครงสร้างใหม่
    for role in roles:
        for period_w, period_h_data in role_data_mapping[role].items():
            for period_h, wards_data in period_h_data.items():
                for ward, subwards in wards_data.items():
                    # จัดรูปแบบการแสดงผล ward ใหม่
                    display_ward = format_ward_display(ward)
                    
                    if subwards:
                        # เรียงลำดับ subward
                        subward_order = {
                            "Chief": 1,
                            "SICU": 2, 
                            "CVT ICU": 3,
                            "Stroke": 1,
                            "Non Stroke": 2,
                        }
                        
                        subwards = sorted(subwards, key=lambda x: subward_order.get(x, 999))
                        
                        for subward in subwards:
                            header_tuples.append((role, period_w, period_h, display_ward, subward))
                            column_keys.append(f"{role}|{period_w}|{period_h}|{ward}|{subward}")
                    else:
                        # ไม่มี subward
                        header_tuples.append((role, period_w, period_h, display_ward, ""))
                        column_keys.append(f"{role}|{period_w}|{period_h}|{ward}|")

    # เรียงลำดับ header เพื่อให้แสดงเป็นระเบียบ (แยก Day, Date ออกก่อน)
    day_date_tuples = [header_tuples[0], header_tuples[1]]  # Day, Date
    content_tuples = header_tuples[2:]  # เนื้อหาอื่นๆ
    
    # เรียงลำดับตามเงื่อนไขให้
    def custom_sort_key_extended(item):
        role, period_w, period_h, ward, subward = item
        
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
            "Stroke": 1, "Non Stroke": 2,
        }
        role_priority = special_order.get(role, 999)
        
        # เรียงลำดับ period_w
        period_w_order = {
            "เช้า": 1, "กลางวัน": 2, "เย็น": 3, "ดึก": 4
        }
        period_w_priority = period_w_order.get(period_w, 999)
        
        # เรียงลำดับ period_h
        period_h_start = 0
        if period_h and "-" in period_h:
            try:
                period_h_start = int(period_h.split("-")[0])
            except:
                period_h_start = 0
        
        # เรียงลำดับ ward
        ward_order = {
            "CVT": 1,"CRITICAL CARE": 2,"PAIN": 3,"PED": 4,
            "เวร Day": 1,"เวรทั้งวัน": 2,
            "19 B-2": 1,"19 B-1": 2,"25 C-128 C": 3,"26 A27 C":4,"26 B27 C":5,
            "วังบน": 1,"วังล่าง": 2,"ICU 1": 3,"ICU 2":4,"CCU":5,"ER":6,"COVID":7,"COVID 2 (จก4)":8,"OPD 9 บ่าย":9,"OPD 9 เช้าวันหยุด":10,
            #Cardiology
            "F1": 1,"F2": 2,"F3 MRI / ECHO": 3,"F3 EP":4,"F3 HF":5,"F3 Cath":6,
            #Nephrology
            "1st call": 1,"Standby": 2,"F3":3,
            "Stroke": 10,"Non Stroke": 11,
            #กุมาร R1
            "ภส.20C, 19C1-C2 18C 21C, 28B":1,"สก.15G1 ,G2 สก. 6":2,"Nursery":7,"OPD No.9":8,
            #กุมาร R2
            "สก/ภส.":1,"OPD9":6,
            #กุมาร R3
            "สก/ภูมิสิริ":1,"PICU":3,"NICU":4,"CRC":5,
        }
        
        ward_priority = 999
        for key, value in ward_order.items():
            if key in original_ward:
                ward_priority = value
                break
        
        # แยกส่วนที่เป็นตัวอักษรและตัวเลขใน ward
        ward_text = ''.join(re.findall(r'[A-Za-z]+', original_ward))
        ward_numbers = re.findall(r'\d+', original_ward)
        ward_number = int(ward_numbers[0]) if ward_numbers else 0
        
        # ส่งคืนลำดับความสำคัญ
        return (role_priority, period_w_priority, period_h_start, ward_priority, ward_text, ward_number, subward)
    
    # เรียงลำดับเนื้อหา
    sorted_content_tuples = sorted(content_tuples, key=custom_sort_key_extended)
    
    # รวม tuples กลับเข้าด้วยกัน
    header_tuples = day_date_tuples + sorted_content_tuples
    
    # สร้าง column_keys ใหม่
    column_keys = ["Day", "Date"]
    
    for i, (role, period_w, period_h, display_ward, subward) in enumerate(header_tuples[2:]):
        # หา ward ดั้งเดิม
        original_ward = ""
        for role_key, period_w_data in role_data_mapping.items():
            if role_key != role:
                continue
            for period_w_key, period_h_data in period_w_data.items():
                if period_w_key != period_w:
                    continue
                for period_h_key, wards_data in period_h_data.items():
                    if period_h_key != period_h:
                        continue
                    for ward_key in wards_data.keys():
                        if format_ward_display(ward_key) == display_ward:
                            original_ward = ward_key
                            break
        
        if not original_ward:
            original_ward = display_ward
        
        column_key = f"{role}|{period_w}|{period_h}|{original_ward}|{subward}"
        column_keys.append(column_key)
    
    # รวมข้อมูลเข้า days_data
    days_data = {}
    
    for _, row in df.iterrows():
        date_key = row["date_key"]
        day = row["day"]
        date_num = row["date_num"]
        role = row.get("role", roles[0])
        name = row.get("name", "")
        period_w = row.get("period_w", "")
        period_h = row.get("period_h", "")
        
        # ดึงค่า ward ตามเงื่อนไข
        if use_remark_as_ward:
            ward = row.get("remark", "")
        else:
            # ตรวจสอบกรณีพิเศษสำหรับแผนก Gastroenterology
            if table_type == "Gastoenterology" and not row.get("ward", ""):
                ward = row.get("remark", "")
            else:
                ward = row.get("ward", "")
        
        # ดึงค่า subward (จากฟิลด์ subward ที่อาจได้ค่าจาก remark แล้ว)
        subward = row.get("subward", "")
        
        if date_key not in days_data:
            # สร้าง dictionary สำหรับวันนี้
            day_entry = {
                "Day": day,
                "Date": date_num
            }
            # เพิ่มคอลัมน์ทั้งหมดเป็นค่าว่าง
            for column_key in column_keys[2:]:  # ข้าม Day และ Date
                day_entry[column_key] = ""
            
            days_data[date_key] = day_entry
        
        # สร้าง key สำหรับเข้าถึงข้อมูลใน days_data
        column_key = f"{role}|{period_w}|{period_h}|{ward}|{subward}"
        
        # ถ้าไม่มี subward ให้ตรวจสอบว่ามี key แบบไม่มี subward หรือไม่
        if not subward:
            alt_key = f"{role}|{period_w}|{period_h}|{ward}|"
            if alt_key in days_data[date_key]:
                column_key = alt_key
        
        # ถ้าหา key ไม่เจอ ให้ลองค้นหาจาก column_keys
        if column_key not in days_data[date_key]:
            found = False
            for existing_key in column_keys[2:]:  # ข้าม Day และ Date
                parts = existing_key.split("|")
                if (parts[0] == role and parts[1] == period_w and parts[2] == period_h and
                    parts[3] == ward and (not subward or parts[4] == subward)):
                    column_key = existing_key
                    found = True
                    break
            
            # ถ้ายังหาไม่เจอ ให้ข้ามข้อมูลนี้
            if not found:
                print(f"Warning: ไม่พบ column key ที่เหมาะสมสำหรับ {name} ({role}, {period_w}, {period_h}, {ward}, {subward})")
                continue
        
        # เพิ่มชื่อลงในตาราง
        current_value = days_data[date_key].get(column_key, "")
        
        if current_value:
            # เก็บชื่อเป็น list
            if isinstance(current_value, list):
                days_data[date_key][column_key].append(name)
            else:
                days_data[date_key][column_key] = [current_value, name]
        else:
            days_data[date_key][column_key] = name
    
    # แปลงเป็น DataFrame
    table_data = []
    for date_key, day_entry in sorted(days_data.items()):
        row_data = {"Day": day_entry["Day"], "Date": day_entry["Date"]}
        
        # เพิ่มข้อมูลสำหรับแต่ละคอลัมน์
        for column_key in column_keys[2:]:  # ข้าม Day และ Date
            cell_value = day_entry.get(column_key, "")
            
            # แยกแต่ละส่วนของ column_key
            parts = column_key.split("|")
            if len(parts) >= 5:
                role, period_w, period_h, ward, subward = parts
                
                # จัดรูปแบบการแสดงผล ward
                display_ward = format_ward_display(ward)
                
                # สร้าง header tuple
                header_tuple = (role, period_w, period_h, display_ward, subward)
                
                # ถ้ามีชื่อหลายคน ให้เตรียมข้อมูลสำหรับแสดงผลแบบขึ้นบรรทัดใหม่
                if isinstance(cell_value, list):
                    cell_value = "<br>".join([f"{name}," if i < len(cell_value)-1 else name 
                                for i, name in enumerate(cell_value)])
                
                row_data[header_tuple] = cell_value
        
        table_data.append(row_data)
    
    # สร้าง DataFrame จากข้อมูล
    table_df = pd.DataFrame(table_data)
    
    # สร้าง MultiIndex columns
    multi_index_headers = [("", "", "", "Day", ""), ("", "", "", "Date", "")]
    for column_key in column_keys[2:]:  # ข้าม Day และ Date
        parts = column_key.split("|")
        if len(parts) >= 5:
            role, period_w, period_h, ward, subward = parts
            display_ward = format_ward_display(ward)
            multi_index_headers.append((role, period_w, period_h, display_ward, subward))
    
    table_df.columns = pd.MultiIndex.from_tuples(multi_index_headers)
    
    return table_df, column_keys