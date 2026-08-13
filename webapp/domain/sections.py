# -*- coding: utf-8 -*-
"""LOP HOC PHAN (section): bo du lieu rong, validate body, khoa nhan dien lop."""

import re

import fate_import
from domain.programs import program_ids_cua_lop
from domain.teachers import loai_lop
from domain.time_rules import parse_class_time

# Ma lop dang "<gi_do>-<so>" (vd "AET2014-3") - GIU CHU DAU, so O CUOI. Dung de
# don gian sau khi xoa mot lop trong hoc phan (xem don_ma_lop_sau_xoa).
_MA_LOP_SO_CUOI = re.compile(r"^(.*-)(\d+)$")


def empty_manual_data():
    """Bo du lieu rong de bat dau 'nhap lieu thu cong' - dung cau truc ma
    solve_guest_phase/solve_resident_phase/check_cross_program_conflicts/
    build_data_response dung duoc khong can sua gi.
    numDays=7 de phu ca Thu2..CN. slotsPerDay=13 la MAC DINH cho nhap tay; luong
    nap file con noi them theo tiet lon nhat co trong file - xem
    domain/merge.py: noi_slots_per_day()."""
    return {
        "params": {
            "numDays": 7, "slotsPerDay": 13, "duration": 2,
            "ltPool": 60, "labPool": 40, "seed": 0,
            "pctPreSubmitted": 100, "numForcedConflicts": 0,
        },
        "programs": [],
        "faculty_names": ["Chưa phân khoa"],
        "program_faculty": {},
        "coordinator_names": {},
        "teachers": {},
        "courses": {},  # course_id -> {id, code, name, credits} - 1 hoc phan dung chung cho nhieu lop
        "sections": {},
        "submissions": {},
        "forced_conflict_teacher_ids": set(),
        "pending_section_ids": [],
        "valid_starts": [],
        "num_resident": 0,
        "num_guest": 0,
        "num_programs": 0,
        "program_names_reverse": {},
        "manual_teacher_windows": {},  # teacher_id -> [slot, ...] (slot=day*slotsPerDay+period)
        # Nhieu lop (nhieu ma mon) la MOT buoi day - xem domain/hoc_chung.py
        "hoc_chung": [],
        "num_time_assumed": 0,
    }


def validate_section_body(data, body, enforce_day_cap=True):
    """Doc + validate toan bo body cho 1 lop - dung chung cho POST tao moi va
    PATCH sua (PATCH doi hoi gui DU ca form, khong merge tung phan field-mot, de
    tranh tinh sai submissions khi chi doi 1 vai field ma thieu ngu canh gio/GV
    hien tai). Tra ve (fields, teacher, duration, time_info, None) neu hop le,
    hoac (None, None, None, None, error_message) neu khong.
    enforce_day_cap=False: xem parse_class_time - danh cho luong nap file, KHONG
    danh cho nhap tay qua form (POST/PATCH /api/manual/section luon giu True)."""
    # GIANG VIEN CUA LOP: mot DANH SACH, moi nguoi vai tro NGANG NHAU.
    #
    # `teacherIds` la dang chinh. Van nhan `teacherId` (+ `coTeacherIds` cu) de
    # cac ban goi cu khong vo, nhung ben trong khong con khai niem "GV chinh":
    # teacher_ids[0] chi la nguoi dau danh sach, dung lam khoa hien thi o cac man
    # von chi cho 1 ten (luoi TKB, tra cuu theo GV).
    #
    # Solver dua CUNG MOT interval vao NoOverlap cua tung nguoi trong danh sach
    # (scheduler_core: mot lop, nhieu nguoi, khong nhan doi nhu cau phong);
    # check_cross_program_conflicts, loai lop (teachers.loai_lop) va gio ranh cua
    # lop (availability.gio_ranh_chung) cung tinh theo ca danh sach.
    tho = body.get("teacherIds")
    if tho is None:
        tho = ([body["teacherId"]] if "teacherId" in body else []) + list(body.get("coTeacherIds") or [])
    teacher_ids = []
    for raw in tho:
        try:
            tid = int(raw)
        except (TypeError, ValueError):
            return None, None, None, None, f"Danh sách giảng viên có giá trị sai: {raw!r}."
        if tid not in data["teachers"]:
            return None, None, None, None, f"Không tìm thấy giảng viên id={tid}."
        if tid not in teacher_ids:
            teacher_ids.append(tid)
    if not teacher_ids:
        return None, None, None, None, "Lớp phải có ít nhất một giảng viên."
    teacher_id = teacher_ids[0]
    teacher = data["teachers"][teacher_id]

    try:
        course_id = int(body["courseId"])
    except (KeyError, TypeError, ValueError):
        return None, None, None, None, "Thiếu hoặc sai courseId."
    course = data.get("courses", {}).get(course_id)
    if course is None:
        return None, None, None, None, f"Không tìm thấy học phần id={course_id}."

    try:
        duration = int(body.get("duration") or 0)
    except (TypeError, ValueError):
        duration = 0
    if duration <= 0:
        return None, None, None, None, "Số tiết mỗi buổi dạy phải là số nguyên > 0."

    time_info, time_err = parse_class_time(
        body, data["params"]["slotsPerDay"], teacher["type"], enforce_cap=enforce_day_cap,
    )
    if time_err:
        return None, None, None, None, time_err

    class_code = (body.get("classCode") or "").strip()
    lt_credits = body.get("ltCredits")
    th_credits = body.get("thCredits")
    # Mot lop co the thuoc NHIEU chuong trinh ("BCSE+MJM"). program_ids la danh
    # sach day du; "program" chi la nguoi dau danh sach, dung lam khoa hien thi/
    # sap xep o cac man von chi cho 1 gia tri (giong teacher_id vs teacher_ids).
    program_ids = program_ids_cua_lop(data, body.get("program"))
    room_type = "LAB" if (th_credits or 0) else "LT"

    fields = {
        "program": program_ids[0], "program_ids": program_ids,
        # Nguyen van o CTDT trong file - de hien thi (A3: giu nguyen nhu file).
        "program_raw": (body.get("program") or "").strip() or "Chung",
        "course_id": course_id,
        "course_name": f"{course['name']} ({class_code})" if class_code else course["name"],
        # teacher_id = nguoi dau danh sach (khoa hien thi), teacher_ids = CA NHOM.
        "teacher_id": teacher_id, "teacher_ids": teacher_ids,
        # Loai lop tinh theo CA NHOM - xem teachers.loai_lop().
        "teacher_type": loai_lop(data, teacher_ids),
        "room_type": room_type, "duration": duration,
        "class_code": class_code, "lt_credits": lt_credits, "th_credits": th_credits,
        "cohort": (body.get("cohort") or "").strip(),
        "expected_students": body.get("expectedStudents"),
        "location": (body.get("location") or "").strip(),
        "teaching_mode": (body.get("teachingMode") or "").strip(),
        "language": (body.get("language") or "").strip(),
        "other_requirements": (body.get("otherRequirements") or "").strip(),
        "notes": (body.get("notes") or "").strip(),
        "coordinator_override": (body.get("coordinatorOverride") or "").strip(),
        "prev_teacher_name": (body.get("prevTeacherName") or "").strip(),
        "prev_teacher_org": (body.get("prevTeacherOrg") or "").strip(),
        "teaching_hours_lt": body.get("teachingHoursLt"),
        "teaching_hours_th": body.get("teachingHoursTh"),
    }
    return fields, teacher, duration, time_info, None


def id_moi(d):
    """Id nguyen nho nhat chua bi dung trong dict `d` (sections/courses/teachers).

    Truoc day moi cho tao ban ghi tu go lai `i = len(d); while i in d: i += 1` -
    5 ban sao cua cung mot phep tinh."""
    i = len(d)
    while i in d:
        i += 1
    return i


def don_ma_lop_sau_xoa(data, course_id, ma_lop_da_xoa):
    """Sau khi xoa 1 lop dang "<prefix>-<so>" (vd hoc phan AET2014 co cac lop
    AET2014-1..AET2014-7, xoa AET2014-2), don lai SO cua cac lop CON LAI trong
    CUNG hoc phan de khong de trong: lop nao co so LON HON so vua xoa thi giam
    di 1 (AET2014-3 -> AET2014-2, AET2014-4 -> AET2014-3...), giu nguyen do dai
    so (dem 0 dau, neu co) cua tung lop.

    CHI dong vao lop co CUNG hoc phan VA cung tien to chu (phan truoc dau "-"
    cuoi) voi ma vua xoa - ma lop khac dang (khong khop mau "-<so>") thi bo qua,
    tranh doi nham nhung ma go tay khong theo qui uoc nay."""
    if course_id is None:
        return
    m = _MA_LOP_SO_CUOI.match((ma_lop_da_xoa or "").strip())
    if not m:
        return
    tien_to, so_da_xoa = m.group(1), int(m.group(2))
    for s in data["sections"].values():
        if s.get("course_id") != course_id:
            continue
        cm = _MA_LOP_SO_CUOI.match((s.get("class_code") or "").strip())
        if not cm or cm.group(1) != tien_to:
            continue
        so = int(cm.group(2))
        if so > so_da_xoa:
            do_dai = len(cm.group(2))
            s["class_code"] = f"{tien_to}{so - 1:0{do_dai}d}"


def khoa_lop(data, s):
    """Khoa nhan dien MOT LOP de biet gop them co bi trung: ma lop + hoc phan +
    GV chinh + gio. Trung ca 4 thu nay thi gan nhu chac chan la nap lai dung dong
    do (vd nap lai file da sua vai o), khong phai lop that thu hai."""
    hp = data.get("courses", {}).get(s.get("course_id")) or {}
    gv = data["teachers"].get(s["teacher_id"], {})
    return (
        (s.get("class_code") or "").strip().lower(),
        fate_import.khoa_gv(hp.get("name") or s.get("course_name") or ""),
        fate_import.khoa_gv(gv.get("name") or ""),
        s.get("original_slot"),
    )
