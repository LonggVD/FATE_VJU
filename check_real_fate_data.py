# -*- coding: utf-8 -*-
"""Kiem tra trung lich THAT tren file FATE.TKB.HK1 2026-2027.xlsx.

Cot da xac dinh dung (theo merged-cell ranges, khong doan mo):
  idx1  = Ma hoc phan
  idx2  = Ten hoc phan
  idx4  = Ma lop hoc phan
  idx8  = CTDT (chuong trinh: BCSE/FTH.ESAS/MJM/ECE/BJS...)
  idx10 = "Thoi gian (Thu, Tiet)" - TEXT TU DO, nguon dang tin cay nhat
  idx11-13 = Thu/Tiet dau/Tiet cuoi (cau truc, THUONG KHONG KHOP voi idx10 -
             chi dung de doi chieu, khong dung lam nguon chinh)
  idx16 = hoc ham/hoc vi GV hien tai
  idx17 = HO VA TEN GV hien tai (HK1 2026-2027) - da xac minh qua merge O6:P6/Q6:U6
  idx14 = ten GV HK cu (chi de doi chieu, KHONG dung)
"""
import io
import re
import openpyxl
from itertools import combinations

PLACEHOLDER_TEACHERS = {
    "phòng đào tạo điều phối", "jle điều phối", "phòng đào tạo",
}

DAY_RE = re.compile(r"th(?:ứ|u)\s*(\d)", re.IGNORECASE)
PERIOD_RE = re.compile(r"ti(?:ế|e)t\s*(\d+)\s*-\s*(\d+)", re.IGNORECASE)


def parse_time_text(text):
    """Tra ve list (day:int, p_start:int, p_end:int) tu 1 dong text tu do.
    Chua ro rang -> tra ve [] cho dong do (khong doan)."""
    if not text:
        return [], False
    sessions = []
    any_unparsed = False
    for line in str(text).split("\n"):
        line = line.strip()
        if not line:
            continue
        days = [int(d) for d in DAY_RE.findall(line)]
        periods = PERIOD_RE.findall(line)
        if not days or not periods:
            any_unparsed = True
            continue
        for d in days:
            for p_start, p_end in periods:
                sessions.append((d, int(p_start), int(p_end)))
    return sessions, any_unparsed


def overlaps(a_start, a_end, b_start, b_end):
    return not (a_end < b_start or b_end < a_start)


def main():
    wb = openpyxl.load_workbook(
        r"D:\Cổng đào tạo\TKB\DEMO_CP_SAT\FATE.TKB.HK1 2026-2027.xlsx", data_only=True
    )
    sh = wb["Giảng dạy cho FATE"]

    rows = list(sh.iter_rows(min_row=8, values_only=True))

    sessions = []  # {course, class_code, program, teacher, day, p_start, p_end, row}
    unparsed_time_rows = []
    no_teacher_rows = []
    placeholder_rows = []

    last_course, last_class_code = None, None

    for i, row in enumerate(rows):
        excel_row = i + 8
        course = row[2] if row[2] else last_course
        class_code = row[4] if row[4] else last_class_code
        if row[2]:
            last_course = row[2]
        if row[4]:
            last_class_code = row[4]

        program = row[8]
        time_text = row[10]
        teacher_title = row[16]
        teacher_name = row[17]

        if not course and not time_text and not teacher_name:
            continue  # dong trong hoan toan

        full_teacher = f"{teacher_title or ''} {teacher_name or ''}".strip()
        teacher_key = (teacher_name or "").strip().lower()

        if not teacher_name:
            no_teacher_rows.append((excel_row, course, class_code))
            continue
        if teacher_key in PLACEHOLDER_TEACHERS or "điều phối" in teacher_key:
            placeholder_rows.append((excel_row, course, class_code, full_teacher))
            continue

        parsed, had_unparsed = parse_time_text(time_text)
        if had_unparsed and not parsed:
            unparsed_time_rows.append((excel_row, course, class_code, time_text))
            continue
        if not parsed:
            continue  # khong co gio (chua xep) - khac voi "khong parse duoc"

        for day, p_start, p_end in parsed:
            sessions.append({
                "row": excel_row, "course": course, "class_code": class_code,
                "program": program, "teacher": full_teacher, "teacher_key": teacher_key,
                "day": day, "p_start": p_start, "p_end": p_end,
            })

    # ---- Check trung theo GV ----
    by_teacher = {}
    for s in sessions:
        by_teacher.setdefault(s["teacher_key"], []).append(s)

    conflicts = []
    for tkey, sess_list in by_teacher.items():
        for a, b in combinations(sess_list, 2):
            if a["day"] == b["day"] and overlaps(a["p_start"], a["p_end"], b["p_start"], b["p_end"]):
                if a["class_code"] == b["class_code"] and a["row"] != b["row"]:
                    continue  # cung 1 lop, nhieu GV cung day cung gio = co-teaching, khong phai xung dot
                conflicts.append((a, b))

    # ---- Bao cao ----
    out = io.open(r"D:\Cổng đào tạo\TKB\DEMO_CP_SAT\real_data_check_report.txt", "w", encoding="utf-8")
    out.write(f"Tong so dong du lieu quet: {len(rows)}\n")
    out.write(f"So buoi hoc trich xuat duoc (co GV thuc + gio parse duoc): {len(sessions)}\n")
    out.write(f"So dong KHONG co ten GV (dieu phoi chung/chua gan): {len(no_teacher_rows)}\n")
    out.write(f"So dong GV la placeholder (Phong DT dieu phoi / JLE dieu phoi): {len(placeholder_rows)}\n")
    out.write(f"So dong co GV thuc nhung KHONG parse duoc gio (text la, dac biet): {len(unparsed_time_rows)}\n\n")

    out.write("=== CAC DONG KHONG PARSE DUOC GIO (can xem tay) ===\n")
    for r, course, cc, txt in unparsed_time_rows:
        out.write(f"  Excel row {r}: {course} ({cc}) -> thoi gian ghi: {txt!r}\n")

    out.write(f"\n=== KET QUA CHECK TRUNG: {len(conflicts)} XUNG DOT ===\n")
    if not conflicts:
        out.write("  KHONG phat hien GV nao bi trung lich (trong pham vi parse duoc).\n")
    for a, b in conflicts:
        out.write(
            f"  GV '{a['teacher']}' TRUNG LICH:\n"
            f"    - row {a['row']}: {a['course']} ({a['class_code']}) Thu {a['day']} tiet {a['p_start']}-{a['p_end']}\n"
            f"    - row {b['row']}: {b['course']} ({b['class_code']}) Thu {b['day']} tiet {b['p_start']}-{b['p_end']}\n"
        )

    out.write(f"\n=== DANH SACH {len(sessions)} BUOI HOC DA TRICH XUAT (de doi chieu) ===\n")
    for s in sorted(sessions, key=lambda x: (x["teacher_key"], x["day"], x["p_start"])):
        out.write(
            f"  [{s['program']}] {s['course']} ({s['class_code']}) - {s['teacher']} "
            f"- Thu {s['day']} tiet {s['p_start']}-{s['p_end']} (row {s['row']})\n"
        )
    out.close()
    print("DONE")


if __name__ == "__main__":
    main()
