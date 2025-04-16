import re

def natural_sort_key(s):
    """ฟังก์ชันสำหรับเรียงลำดับตามธรรมชาติ (เช่น 1, 2, 10 แทนที่จะเป็น 1, 10, 2)"""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', str(s))]

def custom_sort_key(item):
    """ฟังก์ชันสำหรับเรียงลำดับหัวข้อตาราง"""
    role, ward, _ = item
    
    # เรียงลำดับพิเศษสำหรับ R1, R2, R3, Fellow
    special_order = {
        "R1": 1,
        "R2": 2, 
        "R3": 3,
        "Fellow": 4,
        "Staff": 5
    }
    
    # ถ้า role อยู่ใน special_order ให้เรียงตาม special_order
    if role in special_order:
        role_priority = special_order[role]
    else:
        # มิฉะนั้นให้เรียงตาม role ปกติ (ตัวอักษร)
        role_priority = 999  # ค่าสูงเพื่อให้มาทีหลัง special_order
    
    # แยกส่วนที่เป็นตัวอักษรและตัวเลขใน ward
    ward_text = ''.join(re.findall(r'[A-Za-z]+', ward))
    ward_numbers = re.findall(r'\d+', ward)
    ward_number = int(ward_numbers[0]) if ward_numbers else 0
    
    return (role_priority, ward_text, ward_number)