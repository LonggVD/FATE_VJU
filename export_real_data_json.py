# -*- coding: utf-8 -*-
"""Xuat CHINH XAC du lieu ma load_real_fate_data() dua vao thuat toan CP-SAT
ra file JSON de nguoi dung doi chieu lai voi file Excel goc."""
import json
import sys

sys.path.insert(0, r"D:\Cổng đào tạo\TKB\DEMO_CP_SAT\webapp")
import scheduler_core as sc

XLSX_PATH = r"D:\Cổng đào tạo\TKB\DEMO_CP_SAT\FATE.TKB.HK1 2026-2027.xlsx"
OUT_PATH = r"D:\Cổng đào tạo\TKB\DEMO_CP_SAT\fate_data_for_review.json"

data = sc.load_real_fate_data(XLSX_PATH)
p = data["params"]
prog_names_rev = data["program_names_reverse"]

teachers_out = []
for tid, t in sorted(data["teachers"].items()):
    teachers_out.append({
        "id": tid,
        "name": t["name"],
        "type": t["type"],
        "org": t["org"],
        "homeProgram": prog_names_rev[t["home_program"]],
    })

sections_out = []
for sid, s in sorted(data["sections"].items()):
    # "original_slot" la gio THAT trong file Excel goc, luu cho CA GUEST va
    # RESIDENT (truoc day chi luu cho GUEST qua submissions, RESIDENT bi mat).
    slot = s.get("original_slot")
    if slot is not None:
        day_idx, period0 = divmod(slot, p["slotsPerDay"])
        day_label = sc.DAY_NAMES[day_idx]
        period_start = period0 + 1
        period_end = period_start + s["duration"] - 1
    else:
        day_label, period_start, period_end = None, None, None

    teacher_ids = s.get("teacher_ids") or [s["teacher_id"]]
    sections_out.append({
        "id": sid,
        "sourceExcelRow": s["source_row"],
        "courseName": s["course_name"],
        "program": prog_names_rev[s["program"]],
        "teacherId": s["teacher_id"],
        "teacherName": data["teachers"][s["teacher_id"]]["name"],
        "coTeachers": [data["teachers"][t]["name"] for t in teacher_ids[1:]] or None,
        "teacherType": s["teacher_type"],
        "roomType": s["room_type"],
        "day": day_label,
        "periodStart": period_start,
        "periodEnd": period_end,
        "durationPeriods": s["duration"],
    })

output = {
    "source": f"{XLSX_PATH} - sheet 'Giảng dạy cho FATE'",
    "note": "Day nay la DUNG du lieu da duoc trich xuat va dua vao thuat toan CP-SAT "
            "(qua ham load_real_fate_data trong scheduler_core.py). Cot 'sourceExcelRow' "
            "la so dong trong file Excel goc (1-indexed) de doi chieu lai.",
    "summary": {
        "totalTeachersExtracted": len(teachers_out),
        "residentTeachers": data["num_resident"],
        "guestTeachers": data["num_guest"],
        "totalSectionsExtracted": len(sections_out),
        "programsDetected": list(prog_names_rev.values()),
        "slotsPerDay": p["slotsPerDay"],
        "numDays": p["numDays"],
    },
    "teachers": teachers_out,
    "sections": sections_out,
}

with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print("DONE ->", OUT_PATH)
