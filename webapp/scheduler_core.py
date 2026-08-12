# -*- coding: utf-8 -*-
"""Loi logic sinh du lieu + giai CP-SAT, tach rieng khoi Flask de de test/tai su dung."""

import itertools
import json
import os
import random
import re
import time
from ortools.sat.python import cp_model

DAY_NAMES = ["Thu 2", "Thu 3", "Thu 4", "Thu 5", "Thu 6", "Thu 7", "Chu nhat"]

_DAY_RE = re.compile(r"th(?:ứ|u)\s*(\d)", re.IGNORECASE)
_SUNDAY_RE = re.compile(r"ch(?:ủ|u)\s*nh(?:ậ|a)t", re.IGNORECASE)
_PERIOD_RE = re.compile(r"ti(?:ế|e)t\s*(\d+)\s*-\s*(\d+)", re.IGNORECASE)
_PLACEHOLDER_TEACHERS = {"phòng đào tạo điều phối", "jle điều phối", "phòng đào tạo"}

_REAL_DATA_PATH = os.path.join(os.path.dirname(__file__), "real_data.json")
try:
    with open(_REAL_DATA_PATH, encoding="utf-8") as _f:
        REAL_DATA = json.load(_f)
except FileNotFoundError:
    REAL_DATA = {"faculties": [], "teacherNames": [], "courseNames": [], "roomNames": []}


def _cycled_names(pool, n, fallback_prefix):
    """Lay n ten tu pool (khong shuffle, giu thu tu on dinh) - lap lai + danh so
    neu n > len(pool). Neu pool rong, dung fallback 'Prefix A/B/C...'."""
    if not pool:
        return [f"{fallback_prefix} {chr(65 + i)}" for i in range(n)]
    names = []
    i = 0
    while len(names) < n:
        base = pool[i % len(pool)]
        cycle = i // len(pool)
        names.append(base if cycle == 0 else f"{base} ({cycle + 1})")
        i += 1
    return names


def _sampled_names(pool, n):
    """Lay n ten NGAU NHIEN (khong trung neu du pool, cho phep trung o phan du)."""
    if not pool:
        return [None] * n
    names = random.sample(pool, k=min(n, len(pool)))
    if n > len(names):
        names += random.choices(pool, k=n - len(names))
    return names


def slot_label(s, slots_per_day):
    day, period = divmod(s, slots_per_day)
    return f"{DAY_NAMES[day]} tiet {period + 1}"


def _giao_nhau(a, dur_a, b, dur_b):
    """Hai buoi co chong gio nhau khong (cung mot cong thuc voi app._overlaps va
    overlaps() ben frontend - ba noi phai giong nhau de khong bao lech)."""
    return not (a + dur_a <= b or b + dur_b <= a)


# Quy tac gio day: THINH GIANG duoc day toi Thu 7 (ngay index 5), CO HUU chi
# duoc day toi Thu 6 (ngay index 4) - gio hanh chinh Thu 7 danh rieng cho
# thinh giang, khong ai duoc day Chu nhat (index 6). Index tinh theo DAY_NAMES
# o tren (0 = Thu 2).
MAX_DAY_INDEX = {"GUEST": 5, "RESIDENT": 4}


def max_day_index(teacher_type):
    return MAX_DAY_INDEX.get(teacher_type, 6)


def valid_starts(num_days, slots_per_day, duration, teacher_type=None):
    """teacher_type: neu co, gioi han so ngay theo MAX_DAY_INDEX (GUEST toi Thu 7,
    RESIDENT toi Thu 6) - bo qua (giu hanh vi cu, toan bo num_days) neu None."""
    if teacher_type is not None:
        num_days = min(num_days, max_day_index(teacher_type) + 1)
    return [
        d * slots_per_day + p
        for d in range(num_days)
        for p in range(slots_per_day - duration + 1)
    ]


def program_label(program_id, program_faculty, faculty_names, program_names_reverse=None):
    name = program_names_reverse.get(program_id) if program_names_reverse else None
    name = name or f"CT{program_id}"
    return f"{name} ({faculty_names[program_faculty[program_id]]})"


def section_program_ids(s):
    """CTDT cua mot lop, LUON la danh sach. Lop cu (sinh gia lap, hoac ban ghi truoc
    khi co program_ids) chi co "program" -> boc thanh danh sach 1 phan tu."""
    return list(s.get("program_ids") or [s["program"]])


def section_program_label(data, s):
    """Nhan CTDT de HIEN THI cho mot lop.

    Uu tien nguyen van trong file ("BCSE+MJM"): he thong HIEU do la hai chuong
    trinh (section_program_ids), nhung VIET ra thi phai dung nhu file - neu khong,
    lop BCSE+MJM se hien thanh "BCSE" va giao vu tuong minh doc nham dong."""
    raw = s.get("program_raw")
    if raw:
        return raw
    return program_label(s["program"], data["program_faculty"], data["faculty_names"],
                         data.get("program_names_reverse"))


def section_program_names(data, s):
    """Ten TUNG chuong trinh thanh phan (["BCSE", "MJM"]) - danh sach de UI dung
    lam muc chon trong bo loc va so khop bang `includes`, thay vi so nguyen chuoi
    "BCSE+MJM" (chon "BCSE" khong ra lop do)."""
    rev = data.get("program_names_reverse") or {}
    ten = [rev.get(pid) for pid in section_program_ids(s)]
    return [t for t in ten if t]


def section_faculty_name(data, s):
    """Ten Khoa cua lop. Truoc day UI boc tu phan trong ngoac cuoi programLabel
    ("BCSE (Chua phan khoa)") - cach do vo ngay khi nhan chuyen sang nguyen van
    nhu file ("BCSE+MJM", khong con ngoac). Gui thang truong nay thi khong ai
    phai doan tu chuoi nua."""
    fid = (data.get("program_faculty") or {}).get(s["program"])
    ten = data.get("faculty_names") or []
    return ten[fid] if fid is not None and fid < len(ten) else None


def section_coordinators(data, s):
    """Ten dieu phoi vien cua lop - MOT NGUOI CHO MOI chuong trinh thanh phan.
    Lop "BCSE+MJM" co hai DPV (DPV-BCSE, DPV-MJM), khong phai mot "DPV-BCSE+MJM"."""
    ten = [data["coordinator_names"].get(pid) for pid in section_program_ids(s)]
    return [t for t in ten if t]


def teacher_display(data, teacher_id):
    """'Ten That (GV#12)' neu co ten that, hoac 'GV 12' neu khong."""
    name = data["teachers"][teacher_id].get("name")
    return f"{name} (GV#{teacher_id})" if name else f"GV {teacher_id}"


def generate_data(params):
    """params: dict voi cac khoa - xem DEFAULT_PARAMS trong app.py"""
    random.seed(params["seed"])

    num_programs = params["numFaculties"] * params["programsPerFaculty"]
    num_resident = int(params["numTeachers"] * params["pctResident"] / 100)
    num_guest = params["numTeachers"] - num_resident

    programs = list(range(num_programs))

    # --- Khoa & Chuong trinh & Dieu phoi vien (ten Khoa lay tu du lieu that neu co) ---
    faculty_names = _cycled_names(REAL_DATA["faculties"], params["numFaculties"], "Khoa")
    program_faculty = {p: p // params["programsPerFaculty"] for p in programs}
    coordinator_names = {p: f"DPV-CT{p} ({faculty_names[program_faculty[p]]})" for p in programs}

    # --- Ten GV that (neu co du lieu that) ---
    teacher_real_names = _sampled_names(REAL_DATA["teacherNames"], params["numTeachers"])

    teachers = []
    for i in range(params["numTeachers"]):
        is_guest = i >= num_resident
        teachers.append({
            "id": i,
            "name": teacher_real_names[i],
            "type": "GUEST" if is_guest else "RESIDENT",
            "home_program": random.choice(programs),
        })

    multi_program_guests = []
    for t in teachers:
        if t["type"] == "GUEST" and random.random() < 0.15:
            other = random.choice([p for p in programs if p != t["home_program"]])
            t["second_program"] = other
            multi_program_guests.append(t["id"])

    section_course_names = (
        random.choices(REAL_DATA["courseNames"], k=params["numSections"])
        if REAL_DATA["courseNames"] else [None] * params["numSections"]
    )

    sections = []
    for i in range(params["numSections"]):
        program = random.choice(programs)
        use_guest = random.random() < params["pctSectionsGuest"] / 100
        if use_guest:
            candidates = [t for t in teachers if t["type"] == "GUEST" and
                          (t["home_program"] == program or t.get("second_program") == program)]
            if not candidates:
                candidates = [t for t in teachers if t["type"] == "GUEST"]
            teacher = random.choice(candidates)
        else:
            candidates = [t for t in teachers if t["type"] == "RESIDENT" and
                          t["home_program"] == program]
            if not candidates:
                candidates = [t for t in teachers if t["type"] == "RESIDENT"]
            teacher = random.choice(candidates)

        room_type = "LAB" if random.random() < 0.25 else "LT"
        sections.append({
            "id": i,
            "program": program,
            "course_name": section_course_names[i],
            "teacher_id": teacher["id"],
            "teacher_type": teacher["type"],
            "room_type": room_type,
            "duration": params["duration"],
        })

    # Chi dung cho submissions cua GUEST (RESIDENT khong qua submissions - xem
    # ben duoi) - gioi han toi Thu 7 theo dung quy tac o valid_starts().
    v_starts = valid_starts(params["numDays"], params["slotsPerDay"], params["duration"], "GUEST")

    submissions = {}
    num_conflicts = min(params["numForcedConflicts"], len(multi_program_guests))
    forced_conflict_teacher_ids = set(random.sample(multi_program_guests, num_conflicts)) if num_conflicts else set()

    guest_sections_by_teacher = {}
    for s in sections:
        if s["teacher_type"] == "GUEST":
            guest_sections_by_teacher.setdefault(s["teacher_id"], []).append(s)

    pct_pre_submitted = params.get("pctPreSubmitted", 70) / 100
    pending_section_ids = []  # lop thinh giang CHUA duoc dieu phoi vien nop gio (submissions[sid] == [])

    for tid, secs in guest_sections_by_teacher.items():
        if tid in forced_conflict_teacher_ids and len(secs) >= 2:
            # Cac ca cay xung dot luon duoc "nop san" de demo check-trung hoat dong ngay
            fixed_slot = random.choice(v_starts)
            for s in secs[:2]:
                submissions[s["id"]] = [fixed_slot]
            for s in secs[2:]:
                submissions[s["id"]] = random.sample(v_starts, k=min(2, len(v_starts)))
        else:
            for s in secs:
                if random.random() < pct_pre_submitted:
                    k = 1 if random.random() < 0.2 else 2
                    submissions[s["id"]] = random.sample(v_starts, k=min(k, len(v_starts)))
                else:
                    submissions[s["id"]] = []  # dieu phoi vien CHUA nop - cho nhap tay qua UI
                    pending_section_ids.append(s["id"])

    return {
        "params": params,
        "programs": programs,
        "faculty_names": faculty_names,
        "program_faculty": program_faculty,
        "coordinator_names": coordinator_names,
        "teachers": {t["id"]: t for t in teachers},
        "sections": {s["id"]: s for s in sections},
        "submissions": submissions,
        "forced_conflict_teacher_ids": forced_conflict_teacher_ids,
        "pending_section_ids": pending_section_ids,
        "valid_starts": v_starts,
        "num_resident": num_resident,
        "num_guest": num_guest,
        "num_programs": num_programs,
    }


def check_cross_program_conflicts(data):
    """'Check trung' truoc khi giai: voi moi GV thinh giang day >= 2 buoi (thuong la
    lien 2 chuong trinh, moi chuong trinh 1 dieu phoi vien bao gio rieng), thu TAT
    CA to hop lua chon window cua rieng GV do (khong xet den GV/phong khac) de xem
    co TON TAI it nhat 1 cach xep khong trung gio cho chinh GV nay hay khong.
    Day la buoc "giao vu khoa check trung" xay ra o cap 1 GV, TRUOC khi dua vao
    CP-SAT giai toan bo (CP-SAT giai ca xung dot voi GV/phong khac nua)."""
    p = data["params"]

    guest_sections_by_teacher = {}
    for s in data["sections"].values():
        if s["teacher_type"] == "GUEST":
            for tid in (s.get("teacher_ids") or [s["teacher_id"]]):
                guest_sections_by_teacher.setdefault(tid, []).append(s)

    results = []
    for tid, secs in guest_sections_by_teacher.items():
        if len(secs) < 2:
            continue
        # HOP cac chuong trinh thanh phan cua moi lop, khong phai moi "program"
        # dai dien: lop ghi "BCSE+MJM" keo theo CA HAI dieu phoi vien, nen GV day
        # lop do cong mot lop BCSE khac VAN la day lien chuong trinh (truoc day
        # "BCSE+MJM" bi coi la mot chuong trinh thu ba nen truong hop nay bi bo sot).
        programs_involved = sorted({pid for s in secs for pid in section_program_ids(s)})
        is_multi_program = len(programs_involved) > 1
        if not is_multi_program:
            continue  # chi quan tam truong hop lien chuong trinh - dung 1 CT thi khong the co "2 dieu phoi vien"

        sec_windows = [data["submissions"][s["id"]] for s in secs]
        sec_durations = [s["duration"] for s in secs]  # duration RIENG cho tung lop

        # Brute-force: thu moi to hop (1 window/section), kiem tra khong trung
        # (chi giao nhau ve thoi gian, chua xet GV/phong khac)
        def overlaps(i, a, j, b):
            return not (a + sec_durations[i] <= b or b + sec_durations[j] <= a)

        feasible = False
        combo_count = 1
        for w in sec_windows:
            combo_count *= max(len(w), 1)
        if combo_count <= 5000:  # an toan, tranh no to hop voi GV qua nhieu buoi
            for combo in itertools.product(*sec_windows):
                ok = True
                for i in range(len(combo)):
                    for j in range(i + 1, len(combo)):
                        if overlaps(i, combo[i], j, combo[j]):
                            ok = False
                            break
                    if not ok:
                        break
                if ok:
                    feasible = True
                    break
        else:
            feasible = None  # khong the kiem tra het, de CP-SAT tu quyet dinh

        results.append({
            "teacherId": tid,
            "teacherName": teacher_display(data, tid),
            "sections": [
                {
                    "sectionId": s["id"],
                    "courseName": s.get("course_name"),
                    "program": s["program"],
                    "programLabel": section_program_label(data, s),
                    "programIds": section_program_ids(s),
                    "programParts": section_program_names(data, s),
                    "facultyName": section_faculty_name(data, s),
                                "coordinator": ", ".join(section_coordinators(data, s)),
                    "coordinators": section_coordinators(data, s),
                    "windowSlots": data["submissions"][s["id"]],
                    "windowLabels": [slot_label(w, p["slotsPerDay"]) for w in data["submissions"][s["id"]]],
                }
                for s in secs
            ],
            "feasible": feasible,
            "isForcedConflict": tid in data["forced_conflict_teacher_ids"],
        })

    return results


def submit_availability(data, section_id, window_slots):
    """Dieu phoi vien nhap gio day cho 1 section thinh giang (mo phong 'Dieu phoi
    vien nhap Giao vien + Gio co the day'). Cap nhat submissions + tra ve ket qua
    check-trung NGAY cho dung GV do (khong can cho chay ca Giai doan 1)."""
    p = data["params"]
    section = data["sections"][section_id]
    tid = section["teacher_id"]

    data["submissions"][section_id] = window_slots
    if section_id in data["pending_section_ids"]:
        data["pending_section_ids"].remove(section_id)

    all_conflicts = check_cross_program_conflicts(data)
    my_conflict = next((c for c in all_conflicts if c["teacherId"] == tid), None)

    return {
        "sectionId": section_id,
        "teacherId": tid,
        "teacherName": teacher_display(data, tid),
        "windowLabels": [slot_label(w, p["slotsPerDay"]) for w in window_slots],
        "crossProgramConflict": my_conflict,  # None neu GV nay chi day 1 chuong trinh (khong can check)
    }


def solve_guest_phase(data, time_limit_s=30):
    p = data["params"]
    guest_sections = [s for s in data["sections"].values() if s["teacher_type"] == "GUEST"]

    model = cp_model.CpModel()
    starts, placed = {}, {}
    intervals_by_teacher = {}
    intervals_by_roomtype = {"LT": [], "LAB": []}
    day_load_terms = {d: [] for d in range(p["numDays"])}  # cho muc tieu dan ngay (phu)

    for s in guest_sections:
        sid = s["id"]
        windows = data["submissions"][sid]
        start = model.NewIntVar(0, p["numDays"] * p["slotsPerDay"] - 1, f"start_{sid}")
        is_placed = model.NewBoolVar(f"placed_{sid}")
        window_bools = []
        for wi, slot in enumerate(windows):
            b = model.NewBoolVar(f"win_{sid}_{wi}")
            model.Add(start == slot).OnlyEnforceIf(b)
            window_bools.append(b)
            day_load_terms[slot // p["slotsPerDay"]].append(b)
        model.Add(sum(window_bools) == 1).OnlyEnforceIf(is_placed)
        model.Add(sum(window_bools) == 0).OnlyEnforceIf(is_placed.Not())
        interval = model.NewOptionalFixedSizeIntervalVar(start, s["duration"], is_placed, f"iv_{sid}")

        starts[sid] = start
        placed[sid] = is_placed
        # Doi voi lesson co NHIEU GV dong giang day (teacher_ids), cung 1 interval
        # duoc dua vao NoOverlap cua TAT CA nguoi do - dam bao khong ai trong nhom
        # bi trung lich o cho khac, ma khong nhan doi nhu cau phong.
        for tid in (s.get("teacher_ids") or [s["teacher_id"]]):
            intervals_by_teacher.setdefault(tid, []).append(interval)
        intervals_by_roomtype[s["room_type"]].append(interval)

    for ivs in intervals_by_teacher.values():
        if len(ivs) > 1:
            model.AddNoOverlap(ivs)

    for room_type, ivs in intervals_by_roomtype.items():
        pool = p["ltPool"] if room_type == "LT" else p["labPool"]
        if ivs:
            model.AddCumulative(ivs, [1] * len(ivs), pool)

    # Muc tieu chinh: toi da hoa so buoi xep duoc (trong so lon, luon uu tien
    # tuyet doi truoc). Muc tieu phu: giam tai cao nhat cua 1 ngay bat ky (dan
    # deu ra ca tuan, tranh don het vao 1 ngay khi khong bat buoc).
    max_day_load = model.NewIntVar(0, len(guest_sections) + 1, "max_day_load_guest")
    for d in range(p["numDays"]):
        if day_load_terms[d]:
            model.Add(sum(day_load_terms[d]) <= max_day_load)
    big_weight = 10 * (len(guest_sections) + 1)
    model.Maximize(big_weight * sum(placed.values()) - max_day_load)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_s
    solver.parameters.num_search_workers = 8

    t0 = time.time()
    status = solver.Solve(model)
    elapsed = time.time() - t0

    lessons = []
    unplaced = []
    for s in guest_sections:
        sid = s["id"]
        prog_label = section_program_label(data, s)
        # Danh sach chuong trinh thanh phan + ten Khoa: UI loc/gom theo cai nay,
        # khong boc tach lai tu chuoi nhan (xem section_program_names).
        prog_meta = {"programIds": section_program_ids(s),
                     "programParts": section_program_names(data, s),
                     "facultyName": section_faculty_name(data, s)}
        coordinator = ", ".join(section_coordinators(data, s))
        submitted_windows = data["submissions"][sid]
        if solver.Value(placed[sid]) == 1:
            slot = solver.Value(starts[sid])
            day, period = divmod(slot, p["slotsPerDay"])
            unused_windows = [w for w in submitted_windows if w != slot]
            lessons.append({
                "id": sid, "teacherId": s["teacher_id"], "teacherName": teacher_display(data, s["teacher_id"]),
                # TAT CA GV cua buoi nay (dong giang day). teacherId van la GV
                # chinh de hien thi; cac man kiem trung/lich cua 1 GV phai doc
                # teacherIds, khong thi buoi nay vo hinh voi nguoi thu 2 tro di
                # du solver DA rang buoc ho (xem AddNoOverlap o tren).
                "teacherIds": list(s.get("teacher_ids") or [s["teacher_id"]]),
                "courseName": s.get("course_name"), "program": s["program"],
                "programLabel": prog_label, **prog_meta, "coordinator": coordinator,
                "roomType": s["room_type"], "day": day, "period": period,
                "slot": slot, "duration": s["duration"], "teacherType": "GUEST",
                "usedWindowLabel": slot_label(slot, p["slotsPerDay"]),
                "unusedFlexibleWindows": [slot_label(w, p["slotsPerDay"]) for w in unused_windows],
            })
        else:
            other_sections = [
                {
                    "sectionId": s2["id"],
                    "courseName": s2.get("course_name"),
                    "program": s2["program"],
                    "programLabel": section_program_label(data, s2),
                    "programIds": section_program_ids(s2),
                    "programParts": section_program_names(data, s2),
                    "facultyName": section_faculty_name(data, s2),
                    "coordinator": ", ".join(section_coordinators(data, s2)),
                    "windows": [slot_label(w, p["slotsPerDay"]) for w in data["submissions"][s2["id"]]],
                }
                for s2 in guest_sections
                if s2["teacher_id"] == s["teacher_id"] and s2["id"] != sid
            ]
            unplaced.append({
                "id": sid, "teacherId": s["teacher_id"], "teacherName": teacher_display(data, s["teacher_id"]),
                "teacherIds": list(s.get("teacher_ids") or [s["teacher_id"]]),  # dong giang day
                "courseName": s.get("course_name"), "program": s["program"],
                "programLabel": prog_label, **prog_meta, "coordinator": coordinator,
                "roomType": s["room_type"],
                "windows": [slot_label(w, p["slotsPerDay"]) for w in submitted_windows],
                "isForcedConflict": s["teacher_id"] in data["forced_conflict_teacher_ids"],
                "notSubmittedYet": len(submitted_windows) == 0,
                "otherSectionsSameTeacher": other_sections,
            })

    return {
        "status": solver.StatusName(status),
        "elapsedSeconds": round(elapsed, 3),
        "total": len(guest_sections),
        "placedCount": len(lessons),
        "lessons": lessons,
        "unplaced": unplaced,
    }


def solve_resident_phase(data, frozen_guest_lessons, forbidden=None, time_limit_s=30,
                         ghim_tay=None, bo_ghim=None):
    """forbidden: dict {section_id: [danh sach slot bi tu choi]}
    ghim_tay: dict {section_id: slot} - giao vu keo-tha/ghim tay o man TKB.
    bo_ghim: set section_id - giao vu BAM "Bo ghim" o man TKB, tuc noi ro "cho he
    thong xep lai lop nay". Bo qua ghim theo `original_slot` cho cac lop do; app.py
    lo phan submissions (xem _mien_sau_khi_bo_ghim).

    ghim_tay dat domain THANG bang slot do, khong di qua valid_starts(): nho vay
    ghim duoc sang Thu 7/Chu nhat. Truoc day app.py ghim bang cach cam moi slot
    hop le TRU slot da ghim, ma slot Chu nhat KHONG nam trong valid_starts cua
    RESIDENT -> "cam tat ca" -> domain rong -> ghim bi bo qua am tham."""
    p = data["params"]
    forbidden = forbidden or {}
    bo_ghim = bo_ghim or set()
    resident_sections = [s for s in data["sections"].values() if s["teacher_type"] == "RESIDENT"]

    model = cp_model.CpModel()
    starts, placed = {}, {}
    intervals_by_teacher = {}
    intervals_by_roomtype = {"LT": [], "LAB": []}

    # Buoi da xep o Giai doan 1: dong bang (interval co dinh), dua vao CA HAI rang
    # buoc - phong (Cumulative) VA khong-trung-gio theo tung GIANG VIEN.
    #
    # Truoc day chi dua vao rang buoc phong. Khong ai thay lo do vi mot GV co huu
    # khong the co lop o GD1: loai lop = loai cua GV chinh. Nhung tu khi loai lop
    # tinh theo CA NHOM (app._loai_lop: nhom co mot khach moi -> ca lop di GD1),
    # mot GV CO HUU co the co lop o GD1 va lop khac o GD2 -> GD2 khong biet gio cua
    # ho da bi chiem -> xep chong nhau. Do tren HK2: 2 GV nam o ca hai giai doan,
    # va co lan chay ra dung 1 o chong nhau (solver co nhieu loi giai toi uu nen
    # khong phai lan nao cung tro).
    for g in frozen_guest_lessons:
        iv = model.NewFixedSizeIntervalVar(
            g["slot"], g.get("duration", p["duration"]), f"frozen_{g['id']}")
        intervals_by_roomtype[g["roomType"]].append(iv)
        for tid in (g.get("teacherIds") or [g["teacherId"]]):
            intervals_by_teacher.setdefault(tid, []).append(iv)

    on_day_by_section = {}  # sid -> [bool theo ngay] - dung cho muc tieu dan ngay (phu)
    pending_ids = set(data.get("pending_section_ids") or [])

    for s in resident_sections:
        sid = s["id"]
        own_valid_starts = valid_starts(p["numDays"], p["slotsPerDay"], s["duration"], "RESIDENT")
        cam = forbidden.get(sid, [])

        # Gio DA CHOT (doc tu file ke hoach giang day, hoac giao vu go tay vao form)
        # -> GHIM dung o do, khong phai chon lai.
        #
        # Truoc day cho nay luon dung own_valid_starts, tuc GD2 xep lai tu dau moi
        # lop co huu: do tren file HK1 2026-2027-2, 139/140 lop co gio chot bi xep
        # sang gio khac (VJU2031 file ghi Thu 2 tiet 6 -> he thong xep Thu 3 tiet 1).
        # Mot dong trong file la mot lop GV va dieu phoi vien da thong nhat gio voi
        # nhau, he thong khong co quyen doi.
        #
        # Ghim bang cach thu hep DOMAIN chu khong AddHint: interval van la Optional
        # nen neu o do bi trung (file co dong nhap trung) thi lop roi vao "khong xep
        # duoc" kem ly do - thay vi lam ca bai toan vo nghiem, cung khong am tham
        # doi gio da chot.
        # `bo_ghim` la CHO DUY NHAT go duoc ghim nay: giao vu phai noi ro y minh
        # bang mot cu bam, khong co duong nao khac lam gio trong file tu troi di.
        ghim_theo_file = (s.get("original_slot")
                          if not s.get("time_assumed") and sid not in bo_ghim else None)

        # Khung gio GV DA KHAI cho lop nay (app._apply_section_time da giao khung
        # cua ca nhom va loc theo do dai buoi). Rong = chua ai khai -> tu do.
        #
        # Truoc day Giai doan 2 KHONG doc submissions: co huu luon tu do ca tuan
        # (Thu 2-Thu 6), nen khai gio ranh cho co huu la vo tac dung. Nay khai roi
        # thi GIOI HAN CUNG, dung nhu Giai doan 1 lam voi thinh giang.
        da_khai = data["submissions"].get(sid) or []
        # DA KHAI gio nhung khong con khung nao du dai cho lop nay: app.py de
        # submissions rong VA dua lop vao pending_section_ids. Phai phan biet voi
        # "chua ai khai" (cung submissions rong nhung KHONG trong pending) - neu
        # khong thi khai xong lai duoc tu do ca tuan, nguoc han y nghia.
        khai_nhung_het_cho = (not da_khai) and sid in pending_ids

        if sid in (ghim_tay or {}):
            # Quyet dinh TAY o man TKB - moi nhat nen thang moi thu khac.
            domain_starts = [ghim_tay[sid]]
        elif cam:
            domain_starts = [v for v in own_valid_starts if v not in cam]
        elif ghim_theo_file is not None:
            domain_starts = [ghim_theo_file]
        elif da_khai:
            domain_starts = list(da_khai)
        else:
            domain_starts = own_valid_starts
        if not domain_starts:
            domain_starts = own_valid_starts  # an toan: neu cam het thi bo qua cam
        start = model.NewIntVarFromDomain(cp_model.Domain.FromValues(domain_starts), f"start_{sid}")
        is_placed = model.NewBoolVar(f"placed_{sid}")
        interval = model.NewOptionalFixedSizeIntervalVar(start, s["duration"], is_placed, f"iv_{sid}")

        # Ngay cua lesson nay = start // slotsPerDay - can 1 IntVar rieng (khong
        # phai bieu thuc) de dung lam dieu kien reify ben duoi.
        day_var = model.NewIntVar(0, p["numDays"] - 1, f"day_{sid}")
        model.AddDivisionEquality(day_var, start, p["slotsPerDay"])
        # b = "lop nay DA XEP va roi vao ngay d". Chi can implication mot chieu:
        #   b => (day_var == d) va b => is_placed
        # cong voi sum(b) == is_placed.
        #
        # KHONG duoc them chieu nguoc (day_var != d khi b sai): `start` luon co mot
        # gia tri cu the trong domain ke ca khi lop KHONG duoc xep, nen day_var luon
        # bang dung mot ngay -> ep sum(b) == 1 -> is_placed bi ep = 1 cho MOI lop.
        # Tuc Giai doan 2 khong he co khai niem "lop khong xep duoc": xep het thi
        # OPTIMAL, khong thi INFEASIBLE va MAT TRANG ket qua. Lo ra ngay khi bat dau
        # ghim gio da chot: HK2 tu 119/119 thanh INFEASIBLE 0/119 chi vi file co vai
        # dong nhap trung doi cung mot o cua cung mot nguoi.
        on_day_bools = []
        for d in range(p["numDays"]):
            b = model.NewBoolVar(f"onday_{sid}_{d}")
            model.Add(day_var == d).OnlyEnforceIf(b)
            model.AddImplication(b, is_placed)
            on_day_bools.append(b)
        model.Add(sum(on_day_bools) == is_placed)
        on_day_by_section[sid] = on_day_bools

        starts[sid] = start
        placed[sid] = is_placed
        if khai_nhung_het_cho:
            # Khong xep duoc THAT (khung da khai khong con cho) - de solver bao ra
            # thay vi am tham xep ra ngoai khung GV da khai.
            model.Add(is_placed == 0)
        for tid in (s.get("teacher_ids") or [s["teacher_id"]]):
            intervals_by_teacher.setdefault(tid, []).append(interval)
        intervals_by_roomtype[s["room_type"]].append(interval)

    for ivs in intervals_by_teacher.values():
        if len(ivs) > 1:
            model.AddNoOverlap(ivs)

    for room_type in ("LT", "LAB"):
        pool = p["ltPool"] if room_type == "LT" else p["labPool"]
        ivs = intervals_by_roomtype[room_type]
        if ivs:
            model.AddCumulative(ivs, [1] * len(ivs), pool)

    # Muc tieu chinh: toi da hoa so buoi xep duoc (trong so lon, uu tien tuyet
    # doi). Muc tieu phu: giam tai cao nhat cua 1 ngay bat ky trong tuan - day
    # chinh la phan xu ly hien tuong "don het vao Thu 2" da phat hien truoc do.
    max_day_load = model.NewIntVar(0, len(resident_sections) + 1, "max_day_load_resident")
    for d in range(p["numDays"]):
        terms = [on_day_by_section[s["id"]][d] for s in resident_sections]
        if terms:
            model.Add(sum(terms) <= max_day_load)
    big_weight = 10 * (len(resident_sections) + 1)
    model.Maximize(big_weight * sum(placed.values()) - max_day_load)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_s
    solver.parameters.num_search_workers = 8

    t0 = time.time()
    status = solver.Solve(model)
    elapsed = time.time() - t0

    lessons = []
    chua_xep = []
    for s in resident_sections:
        sid = s["id"]
        if solver.Value(placed[sid]) == 1:
            slot = solver.Value(starts[sid])
            day, period = divmod(slot, p["slotsPerDay"])
            lessons.append({
                "id": sid, "teacherId": s["teacher_id"], "teacherName": teacher_display(data, s["teacher_id"]),
                "teacherIds": list(s.get("teacher_ids") or [s["teacher_id"]]),  # dong giang day - xem GD1
                "courseName": s.get("course_name"), "program": s["program"],
                "programLabel": section_program_label(data, s),
                "programIds": section_program_ids(s),
                "programParts": section_program_names(data, s),
                "facultyName": section_faculty_name(data, s),
                            "roomType": s["room_type"], "day": day, "period": period,
                "slot": slot, "duration": s["duration"], "teacherType": "RESIDENT", "status": "DRAFT",
            })
        else:
            chua_xep.append(s)

    # Cac lop GD2 khong xep duoc - TRUOC DAY KHONG CO danh sach nay (xem chu thich
    # o cho tao on_day_bools: is_placed bi ep = 1 nen GD2 chi co "xep het" hoac
    # INFEASIBLE mat trang). Gio da xep duoc bao nhieu thi xep, phan con lai phai
    # noi ro LOP NAO va AI/CAI GI dang chiem cho - de giao vu sap lai.
    slot_da_xep = {l["id"]: l for l in lessons}
    frozen_by_id = {g["id"]: g for g in frozen_guest_lessons}
    unplaced = []
    for s in chua_xep:
        sid = s["id"]
        ghim = s.get("original_slot") if not s.get("time_assumed") else None
        tids = set(s.get("teacher_ids") or [s["teacher_id"]])
        # Cac o MA LOP NAY DUOC PHEP nam: gio da chot (1 o), hoac khung GV da khai.
        # Khong co gi ca (chua khai, khong chot) thi khong the chi ra "ai chiem cho"
        # - lop khong xep duoc vi het phong/qua tai, khong vi mot buoi cu the.
        o_cho_phep = [ghim] if ghim is not None else list(data["submissions"].get(sid) or [])
        blockers = []
        for l in list(slot_da_xep.values()) + list(frozen_by_id.values()):
            l_tids = set(l.get("teacherIds") or [l["teacherId"]])
            if not (tids & l_tids):
                continue
            if any(_giao_nhau(o, s["duration"], l["slot"], l["duration"]) for o in o_cho_phep):
                blockers.append({
                    "sectionId": l["id"], "courseName": l.get("courseName"),
                    "teacherName": l.get("teacherName"),
                    "slotLabel": slot_label(l["slot"], p["slotsPerDay"]),
                    "phase": "GD1" if l["id"] in frozen_by_id else "GD2",
                })
        unplaced.append({
            "id": sid, "teacherId": s["teacher_id"],
            "teacherName": teacher_display(data, s["teacher_id"]),
            "teacherIds": list(s.get("teacher_ids") or [s["teacher_id"]]),
            "courseName": s.get("course_name"), "program": s["program"],
            "programLabel": section_program_label(data, s),
            "programIds": section_program_ids(s),
            "programParts": section_program_names(data, s),
            "facultyName": section_faculty_name(data, s),
            "coordinator": ", ".join(section_coordinators(data, s)),
            "roomType": s["room_type"], "duration": s["duration"],
            "pinnedSlot": ghim,
            "pinnedLabel": slot_label(ghim, p["slotsPerDay"]) if ghim is not None else None,
            # PINNED_CONFLICT: co gio da chot nhung o do bi chiem (hay gap nhat la
            # file co hai dong nhap trung doi cung mot o cua cung mot nguoi).
            # NO_SLOT: khong co gio chot, khong con cho nao vua.
            "reason": "PINNED_CONFLICT" if ghim is not None else "NO_SLOT",
            "blockers": blockers,
        })

    return {
        "status": solver.StatusName(status),
        "elapsedSeconds": round(elapsed, 3),
        "total": len(resident_sections),
        "placedCount": len(lessons),
        "lessons": lessons,
        "unplaced": unplaced,
    }


def _parse_time_text(text):
    """'Thu 3, tiet 2-3' -> [(day0idx, p_start, p_end)]. day0idx: Thu2=0..Thu7=5, CN=6.
    Tra ve ([], True) neu co nhac den ngay nhung khong tim duoc tiet (khong doan)."""
    if not text:
        return [], False
    sessions = []
    any_unparsed = False
    for line in str(text).split("\n"):
        line = line.strip()
        if not line:
            continue
        days = [int(d) - 2 for d in _DAY_RE.findall(line)]
        if _SUNDAY_RE.search(line):
            days.append(6)
        periods = _PERIOD_RE.findall(line)
        if not days or not periods:
            any_unparsed = True
            continue
        for d in days:
            for p_start, p_end in periods:
                sessions.append((d, int(p_start), int(p_end)))
    return sessions, any_unparsed


_NAME_SPLIT_RE = re.compile(r"[,\n]")  # GV dong giang day ngan boi dau phay HOAC xuong dong (ca 2 kieu deu gap)

# Ten cot ma ham nay dung -> ten truong trong ban do cot cua fate_import.
# Truoc day o day co _LAYOUT_OLD/_LAYOUT_NEW: hai bo chi so cot CO DINH, chon theo
# TEN SHEET. Da vo voi file "FATE.TKB.HK1 2026-2027-2.xlsx" (cau truc HK1 nhung
# sheet doi ten thanh "FATE" -> lech dung 1 cot tu dau den cuoi ma khong bao loi);
# duong nhap file da chuyen sang doc theo NHAN o hang tieu de, cho nay dung lai
# chinh bo doc do de khong con hai cach nhan dien layout trong cung mot repo.
_COT_TU_FATE_IMPORT = {
    "course": "courseName", "class_code": "classCode",
    "lt_hours": "ltCredits", "th_hours": "thCredits",
    "program": "program",
    "thu": "thu", "tiet_dau": "tietDau", "tiet_cuoi": "tietCuoi",
    "title": "teacherTitle", "name": "teacherName", "org": "teacherOrg",
}


def load_real_fate_data(xlsx_path, sheet_name=None, default_duration=2):
    """Nap du lieu THAT tu file ke hoach giang day (Excel) thay cho generate_data()
    gia lap. Tra ve dung cau truc 'data' de solve_guest_phase/solve_resident_phase/
    check_cross_program_conflicts dung duoc khong can sua gi them.

    Ban do cot doc tu chinh HANG TIEU DE cua file (fate_import.read_layout) - xem
    _COT_TU_FATE_IMPORT. sheet_name (neu truyen) chi de chi dinh sheet, khong con
    quyet dinh layout.

    Phan loai GV co huu/thinh giang theo "Don vi cong tac": co chua "Viet Nhat"
    -> RESIDENT, nguoc lai -> GUEST. Cac dong do "Phong Dao tao dieu phoi"/"JLE
    dieu phoi" (khong phai 1 GV cu the) bi LOAI khoi bo du lieu nay.

    Dong co GV nhung CHUA co Thu/Tiet (rat pho bien o layout moi - Khoa moi xep
    xong "ai day", chua xep "luc nao") duoc coi la CAN THUAT TOAN TU XEP: GUEST
    duoc cho tu do chon bat ky slot hop le trong tuan (thay vi bi buoc theo 1
    window duy nhat), RESIDENT thi von da tu do o Giai doan 2 nen khong doi gi.
    Duration cho cac dong nay dung mac dinh 'default_duration' (KHONG suy tu du
    lieu thuc vi khong co gio de tinh) - danh dau ro qua co 'time_assumed'.
    """
    import openpyxl

    # Import trong ham (khong o dau file): fate_import da `import scheduler_core`
    # nen import nguoc o cap module se thanh vong tron.
    import fate_import

    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    if sheet_name is None:
        sheet_name, layout, err = fate_import.detect_sheet(wb)
        if err:
            raise ValueError(err)
    else:
        layout = fate_import.read_layout(wb[sheet_name])
        if layout is None:
            raise ValueError(f"Khong doc duoc hang tieu de trong sheet '{sheet_name}'.")
    first_data_row = layout["firstDataRow"]
    sh = wb[sheet_name]
    rows = list(sh.iter_rows(min_row=first_data_row, values_only=True))

    max_period = 12
    parsed_rows = []
    last_course, last_class_code, last_lt, last_th = None, None, None, None

    def col(row, key):
        idx = layout.get(_COT_TU_FATE_IMPORT[key])
        return row[idx] if idx is not None and idx < len(row) else None

    for i, row in enumerate(rows):
        excel_row = i + first_data_row
        course = col(row, "course") or last_course
        class_code = col(row, "class_code") or last_class_code
        lt_hours = col(row, "lt_hours") if col(row, "lt_hours") is not None else last_lt
        th_hours = col(row, "th_hours") if col(row, "th_hours") is not None else last_th
        if col(row, "course"): last_course = col(row, "course")
        if col(row, "class_code"): last_class_code = col(row, "class_code")
        if col(row, "lt_hours") is not None: last_lt = col(row, "lt_hours")
        if col(row, "th_hours") is not None: last_th = col(row, "th_hours")

        program_raw = col(row, "program")
        teacher_name = col(row, "name")

        if not teacher_name:
            continue
        tkey = str(teacher_name).strip().lower()
        if tkey in _PLACEHOLDER_TEACHERS or "điều phối" in tkey:
            continue

        org = col(row, "org") or ""
        is_resident = "việt nhật" in str(org).lower() or "viet nhat" in str(org).lower()

        # Mot o co the ghi NHIEU GV dong giang day, ngan boi dau phay HOAC xuong
        # dong (ca 2 kieu deu gap tuy file). Tach rieng tung nguoi de kiem tra
        # trung lich CHINH XAC cho tung ca nhan, khong coi ca cum la "1 GV ao".
        teacher_names = [n.strip() for n in _NAME_SPLIT_RE.split(str(teacher_name)) if n.strip()]
        if not teacher_names:
            continue
        title_raw = col(row, "title")

        room_type = "LAB" if (th_hours or 0) > 0 else "LT"
        common = {
            "row": excel_row, "course": course, "class_code": class_code,
            "program_raw": str(program_raw).strip() if program_raw else "Khac",
            "teacher_names": teacher_names,
            "teacher_title": (title_raw or "").strip(),
            "org": org, "is_resident": is_resident, "room_type": room_type,
        }

        # --- Truong hop A: co gio ro rang ---
        # NGUON GIO DUY NHAT la 3 cot Thu / Tiet dau / Tiet cuoi.
        #
        # Truoc day cot text tu do "Thoi gian (Thu, Tiet)" duoc uu tien HON (2 nguon
        # hay lech nhau, do do tin text hon). Khoa da xac nhan cot text la CHO GHI CU
        # cua cac ky truoc, du lieu bo di - nen bo han khoi moi duong doc. Dong nao
        # khong co 3 cot nay thi coi nhu CHUA co gio, de thuat toan tu xep, chu khong
        # quay ve doc text nua.
        thu, tiet_dau, tiet_cuoi = col(row, "thu"), col(row, "tiet_dau"), col(row, "tiet_cuoi")
        has_structured_time = all(isinstance(v, (int, float)) for v in (thu, tiet_dau, tiet_cuoi))
        sessions = [(int(thu) - 2, int(tiet_dau), int(tiet_cuoi))] if has_structured_time else []

        if sessions:
            for day, p_start, p_end in sessions:
                max_period = max(max_period, p_end + 1)
                parsed_rows.append({**common, "day": day, "p_start": p_start,
                                     "p_end": p_end, "time_assumed": False})
        else:
            # --- Truong hop B: CHUA co gio - can thuat toan tu xep ---
            parsed_rows.append({**common, "day": None, "p_start": None,
                                 "p_end": None, "time_assumed": True})

    slots_per_day = max_period
    params = {
        "numDays": 7, "slotsPerDay": slots_per_day, "duration": default_duration,
        "ltPool": 60, "labPool": 40,  # CHUA CO so lieu phong thuc te trong file -> dat rong de tap trung test GV
        "seed": 0, "pctPreSubmitted": 100, "numForcedConflicts": 0,
    }
    # Chi feed vao free_choice_starts cua GUEST "chua bao gio" ben duoi.
    v_starts_default = valid_starts(params["numDays"], slots_per_day, default_duration, "GUEST")

    program_ids = {}
    for r in parsed_rows:
        program_ids.setdefault(r["program_raw"], len(program_ids))
    faculty_names = ["FATE"]
    program_faculty = {pid: 0 for pid in program_ids.values()}
    coordinator_names = {pid: f"DPV-{name}" for name, pid in program_ids.items()}

    # Moi ten GV rieng le -> 1 teacher_id rieng (dung chung 1 nguoi neu ten trung
    # giua nhieu dong - vd 1 GV day nhieu lop). Voi dong "dong giang day" (nhieu
    # ten trong 1 o), TAO/DUNG LAI id cho DUNG tung nguoi, khong gop thanh 1 "GV ao".
    teacher_ids = {}
    teachers = {}
    for r in parsed_rows:
        for i, name in enumerate(r["teacher_names"]):
            if name not in teacher_ids:
                tid = len(teacher_ids)
                teacher_ids[name] = tid
                # title chi chac chan dung cho nguoi DAU trong danh sach dong giang day
                # (layout moi: title da nam san trong ten, khong can nhap them)
                title = r["teacher_title"] if i == 0 else ""
                teachers[tid] = {
                    "id": tid, "name": f"{title} {name}".strip(),
                    "type": "RESIDENT" if r["is_resident"] else "GUEST",
                    "home_program": program_ids[r["program_raw"]],
                    "org": r["org"],
                }

    sections = {}
    submissions = {}
    num_time_assumed = 0
    for idx, r in enumerate(parsed_rows):
        sid = idx
        tids = [teacher_ids[name] for name in r["teacher_names"]]
        primary_tid = tids[0]

        if r["time_assumed"]:
            num_time_assumed += 1
            duration = default_duration
            original_slot = None
            free_choice_starts = v_starts_default
        else:
            duration = r["p_end"] - r["p_start"] + 1
            original_slot = r["day"] * slots_per_day + (r["p_start"] - 1)
            free_choice_starts = None

        sections[sid] = {
            "id": sid, "program": program_ids[r["program_raw"]],
            "course_name": f"{r['course']} ({r['class_code']})" if r["class_code"] else r["course"],
            "teacher_id": primary_tid, "teacher_ids": tids,
            "teacher_type": teachers[primary_tid]["type"],
            "room_type": r["room_type"], "duration": duration,
            "source_row": r["row"], "original_slot": original_slot,
            "time_assumed": r["time_assumed"],
        }
        if teachers[primary_tid]["type"] != "GUEST":
            submissions[sid] = []  # RESIDENT: Giai doan 2 luon tu do chon, khong dung submissions
        elif r["time_assumed"]:
            submissions[sid] = free_choice_starts  # GUEST nhung CHUA bao gio -> tu do chon ca tuan
        else:
            submissions[sid] = [original_slot]  # GUEST da co gio -> dung DUNG gio do (nhu truoc)

    num_resident = sum(1 for t in teachers.values() if t["type"] == "RESIDENT")
    num_guest = len(teachers) - num_resident

    return {
        "params": params,
        "programs": list(program_ids.values()),
        "faculty_names": faculty_names,
        "program_faculty": program_faculty,
        "coordinator_names": coordinator_names,
        "teachers": teachers,
        "sections": sections,
        "submissions": submissions,
        "forced_conflict_teacher_ids": set(),
        "pending_section_ids": [],
        "valid_starts": v_starts_default,
        "num_resident": num_resident,
        "num_guest": num_guest,
        "num_programs": len(program_ids),
        "program_names_reverse": {v: k for k, v in program_ids.items()},
        "num_time_assumed": num_time_assumed,  # so buoi KHONG co gio thuc, phai gia dinh duration+tu do chon
    }