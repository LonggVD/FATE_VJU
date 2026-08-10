# -*- coding: utf-8 -*-
"""Xuat CAU TRUC DAU VAO THAT ma solve_guest_phase()/solve_resident_phase()/
check_cross_program_conflicts() nhan duoc - kem giai thich truong nao thuat
toan CO DOC, truong nao chi de hien thi (khong anh huong ket qua giai)."""
import json
import sys

sys.path.insert(0, r"D:\Cổng đào tạo\TKB\DEMO_CP_SAT\webapp")
import scheduler_core as sc

XLSX_PATH = r"D:\Cổng đào tạo\TKB\DEMO_CP_SAT\FATE.TKB.HK2_2025-2026.xlsx"  # file CHUAN
OUT_PATH = r"D:\Cổng đào tạo\TKB\DEMO_CP_SAT\algorithm_input_schema.json"

data = sc.load_real_fate_data(XLSX_PATH)


def sample(d, n=5):
    items = list(d.items())[:n]
    return {str(k): v for k, v in items}


output = {
    "_doc": (
        "Day la CHINH XAC cau truc du lieu (bien 'data') duoc truyen vao "
        "solve_guest_phase(data), solve_resident_phase(data, ...), "
        "check_cross_program_conflicts(data). Moi nhanh co '_fieldsUsedBySolver' "
        "liet ke dung nhung truong CP-SAT thuc su doc de dung rang buoc/muc tieu "
        "- cac truong con lai chi de hien thi/doi chieu, KHONG anh huong ket qua giai."
    ),

    "params": {
        "_fieldsUsedBySolver": ["numDays", "slotsPerDay", "ltPool", "labPool"],
        "_meaning": {
            "numDays": "So ngay/tuan (7 = tinh ca Chu nhat)",
            "slotsPerDay": "So tiet/ngay (12, suy tu tiet lon nhat gap trong file)",
            "duration": "KHONG con dung truc tiep - moi section co 'duration' RIENG (xem sections)",
            "ltPool": "So phong Ly thuyet dung DONG THOI toi da -> AddCumulative capacity. Hien dat TAM 60 (chua co so lieu thuc).",
            "labPool": "So phong Thuc hanh dung DONG THOI toi da -> AddCumulative capacity. Hien dat TAM 40 (chua co so lieu thuc).",
        },
        "actualValues": data["params"],
    },

    "teachers": {
        "_fieldsUsedBySolver": ["type (GUEST/RESIDENT quyet dinh vao Giai doan 1 hay 2)"],
        "_fieldsDisplayOnly": ["name", "org", "home_program"],
        "_meaning": {
            "id": "Khoa chinh, dung de gom nhom AddNoOverlap (GV nay khong duoc day 2 buoi cung luc)",
            "type": "GUEST -> vao solve_guest_phase (Giai doan 1) | RESIDENT -> vao solve_resident_phase (Giai doan 2)",
            "name": "Chi hien thi, khong anh huong giai",
            "org": "Chi hien thi (dung MOT LAN luc nap du lieu de QUYET DINH type, sau do khong dung nua)",
        },
        "totalCount": len(data["teachers"]),
        "sample (5/{})".format(len(data["teachers"])): sample(data["teachers"], 5),
    },

    "sections": {
        "_fieldsUsedBySolver": ["teacher_id / teacher_ids", "teacher_type", "room_type", "duration", "program (chi dung trong check_cross_program_conflicts)"],
        "_fieldsDisplayOnly": ["course_name", "source_row", "original_slot", "time_assumed"],
        "_meaning": {
            "id": "Khoa chinh cua 1 buoi hoc (= 1 bien quyet dinh 'start' trong CP-SAT)",
            "teacher_id": "GV chinh (dung de hien thi + fallback neu khong co teacher_ids)",
            "teacher_ids": "TOAN BO GV cung day buoi nay (dong giang day) - AddNoOverlap ap dung cho TAT CA nguoi trong list",
            "teacher_type": "GUEST/RESIDENT - quyet dinh section nay thuoc Giai doan 1 hay 2",
            "room_type": "'LT' hoac 'LAB' - quyet dinh section nay tinh vao AddCumulative pool nao",
            "duration": "So tiet lien tiep buoi nay chiem - dung truc tiep trong NewOptionalFixedSizeIntervalVar. Neu time_assumed=True thi day la GIA DINH mac dinh (2), khong phai so thuc.",
            "program": "Id chuong trinh - CHI dung trong check_cross_program_conflicts de nhom theo GV day lien chuong trinh",
            "original_slot": "Gio THAT trong file Excel (day*slotsPerDay + tiet-1) - null neu time_assumed=True (chua co gio thuc). CHUA dua vao rang buoc/muc tieu nao, chi de doi chieu.",
            "time_assumed": "True = dong nay trong file KHONG co Thu/Tiet -> duration dung mac dinh, GUEST duoc tu do chon ca tuan (xem submissions). False = co gio thuc trong file.",
        },
        "totalCount": len(data["sections"]),
        "sample (5/{}) - luu y section co 'teacher_ids' > 1 phan tu la truong hop dong giang day".format(len(data["sections"])):
            sample(data["sections"], 5),
    },

    "submissions": {
        "_fieldsUsedBySolver": ["TOAN BO - day la 'khung gio GV thinh giang bao minh co the day'"],
        "_meaning": (
            "Dict {section_id: [slot1, slot2, ...]}. CHI co y nghia voi section GUEST: "
            "Giai doan 1 BAT BUOC chon DUNG 1 slot trong list nay (hoac bo qua section = "
            "khong xep duoc). Section RESIDENT luon co list RONG [] - khong dung, vi "
            "Giai doan 2 duoc TU DO chon bat ky slot hop le nao (khong bi gioi han theo "
            "'da bao gio')."
        ),
        "sample (5)": sample(data["submissions"], 5),
    },

    "forced_conflict_teacher_ids / pending_section_ids": {
        "_meaning": "Chi dung cho du lieu GIA LAP (danh dau cac ca xung dot co y cay vao de demo) - LUON RONG voi du lieu THAT tu Excel.",
    },
}

with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2, default=str)

print("DONE")
