# -*- coding: utf-8 -*-
"""Flask demo UI cho phuong an xep TKB thinh giang truoc / co huu sau (CP-SAT).
Chay: py app.py   -> mo http://127.0.0.1:5055
"""

import json
import os
import re

from flask import Flask, request, jsonify, render_template, send_file

import fate_export
import fate_import
import scheduler_core as sc

app = Flask(__name__)

DEFAULT_PARAMS = {
    "numFaculties": 5,
    "programsPerFaculty": 3,
    "numTeachers": 230,
    "pctResident": 45,
    "numSections": 500,
    "pctSectionsGuest": 55,
    "ltPool": 35,
    "labPool": 15,
    "numDays": 6,
    "slotsPerDay": 6,
    "duration": 2,
    "numForcedConflicts": 12,
    "pctPreSubmitted": 70,
    "seed": 42,
}

# State toan cuc don gian (demo local, 1 nguoi dung tai 1 thoi diem)
STATE = {
    "data": None,
    "extra": None,  # {isRealData, sourceLabel, numTimeAssumed} - luu lai de /api/data doc lai duoc
    "guestResult": None,
    "residentResult": None,
    # section_id(int) -> {"slot": int, "reason": str|None, "problem": dict|None}
    # "Ghim" tu keo-tha sua tay (thay cho tinh nang "Tu choi - luan chuyen" cu).
    # KHAC voi ket qua giai (guestResult/residentResult): overrides KHONG bi xoa
    # khi giai lai - no la RANG BUOC duoc doc lai o moi lan giai (xem
    # _solve_guest_with_overrides/_forbidden_from_resident_overrides), chi mat
    # khi sinh/nap du lieu moi (section id khong con nghia) hoac giao vu tu bo ghim.
    "overrides": {},
}


@app.get("/")
def index():
    return render_template("index.html", default_params=DEFAULT_PARAMS)


_DAY_LABELS_VN = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]


def _section_status(data, s):
    """Trang thai 1 lop cho man hinh 'Du lieu hoc phan' - CHI ap dung y nghia cho
    lop nhap qua UI moi (co course_id); lop tu Excel/gia lap khong co field nay se
    ra 'ready_fixed'/'ready_auto' tuy time_assumed, khong anh huong gi khac."""
    if s.get("time_assumed"):
        if s["teacher_type"] == "GUEST" and s["id"] in data["pending_section_ids"]:
            return "missing_time"
        return "ready_auto"
    return "ready_fixed"


def _build_classes_list(data):
    """Bang phang 'moi lop 1 dong' mirror 29 cot Excel, dung cho man hinh nhap
    lieu thay Excel - CHI cong THEM vao response, khong doi gi cau truc
    submissions/pendingSections hien co (2 man hinh 'Khung gio da bao'/check-trung
    khong bi anh huong)."""
    out = []
    for sid, s in data["sections"].items():
        course = data.get("courses", {}).get(s.get("course_id")) or {}
        teacher = data["teachers"].get(s["teacher_id"], {})

        # Lop tu Excel/gia lap khong co day/period_start/period_end (chi co
        # original_slot) - suy ra tu original_slot de bang van hien duoc gio
        # thay vi de trong, KHONG ghi lai vao s (chi hien thi).
        day, p_start = s.get("day"), s.get("period_start")
        p_end = s.get("period_end")
        if day is None and not s.get("time_assumed") and s.get("original_slot") is not None:
            slots_per_day = data["params"]["slotsPerDay"]
            day, period0 = divmod(s["original_slot"], slots_per_day)
            p_start = period0 + 1
            p_end = p_start + s["duration"] - 1

        # Giao vu keo-tha sua tay tren man TKB -> STATE['overrides'] giu gio moi,
        # nhung s['day']/['period_start'] KHONG doi (dung y do: override la mot
        # lop phu, "Bỏ ghim" phai tra ve duoc gio cu). Neu khong doc lop phu do o
        # day thi cac man khac (bang 29 cot, cot "Thời gian" o Giờ rảnh GV) van
        # in gio CU, trong khi luoi TKB in gio MOI - cung mot lop, hai man noi hai
        # gio khac nhau. Chi hien thi, khong ghi lai vao s.
        ov = STATE["overrides"].get(sid)
        if ov and ov.get("slot") is not None:
            slots_per_day = data["params"]["slotsPerDay"]
            day, period0 = divmod(ov["slot"], slots_per_day)
            p_start = period0 + 1
            p_end = p_start + s["duration"] - 1

        time_assumed = bool(s.get("time_assumed")) and not ov
        time_label = f"{_DAY_LABELS_VN[day]}, tiết {p_start}-{p_end}" if not time_assumed and day is not None else None

        out.append({
            "sectionId": sid,
            "courseId": s.get("course_id"), "courseCode": course.get("code"),
            "courseName": course.get("name") or s.get("course_name"), "credits": course.get("credits"),
            "classCode": s.get("class_code"), "ltCredits": s.get("lt_credits"), "thCredits": s.get("th_credits"),
            "cohort": s.get("cohort"), "program": s["program"],
            "programName": data.get("program_names_reverse", {}).get(s["program"]),
            "programLabel": sc.program_label(s["program"], data["program_faculty"], data["faculty_names"], data.get("program_names_reverse")),
            "expectedStudents": s.get("expected_students"),
            "day": day, "periodStart": p_start, "periodEnd": p_end,
            "timeAssumed": time_assumed, "timeLabel": time_label,
            # Gio dang hien la do giao vu keo-tha dat, khong phai gio goc trong
            # du lieu - de man hinh noi ro thay vi im lang doi mot con so.
            "timeFromOverride": bool(ov and ov.get("slot") is not None),
            "teacherId": s["teacher_id"], "teacherName": sc.teacher_display(data, s["teacher_id"]),
            "teacherNameRaw": teacher.get("name"),  # khong co hau to "(GV#n)" - dung cho bang mirror Excel
            "teacherType": s["teacher_type"], "teacherOrg": teacher.get("org"), "teacherTitle": teacher.get("title"),
            "teacherEmail": teacher.get("email"), "teacherPhone": teacher.get("phone"),
            "prevTeacherName": s.get("prev_teacher_name"), "prevTeacherOrg": s.get("prev_teacher_org"),
            "teachingHoursLt": s.get("teaching_hours_lt"), "teachingHoursTh": s.get("teaching_hours_th"),
            "location": s.get("location"), "teachingMode": s.get("teaching_mode"),
            "language": s.get("language"), "otherRequirements": s.get("other_requirements"),
            "notes": s.get("notes"), "coordinatorOverride": s.get("coordinator_override"),
            "roomType": s["room_type"], "duration": s["duration"],
            "status": _section_status(data, s),
            # Trang thai lich sau khi "Luu thoi khoa bieu" - None khi chua bam
            # luu lan nao (khac "status" o tren, von chi noi ve gio gia dinh/co
            # dinh, khong noi ve co trung gio hay khong).
            "scheduleStatus": s.get("schedule_status"),
        })
    out.sort(key=lambda x: x["sectionId"])
    return out


def _build_data_response(data, extra=None):
    """Dung chung cho ca sinh du lieu gia lap va nap du lieu that - cung cau truc
    'data' (xem generate_data/load_real_fate_data) nen tai dung duoc toan bo."""
    params = data["params"]
    prog_names_rev = data.get("program_names_reverse")

    multi_program_count = sum(1 for t in data["teachers"].values() if "second_program" in t)

    manual_windows = data.get("manual_teacher_windows", {})
    teachers = [
        {
            "id": t["id"], "name": sc.teacher_display(data, t["id"]), "type": t["type"],
            "org": t.get("org"),
            # nameRaw/title/email/phone: dung de PREFILL form sua GV (TeacherEditDrawer) -
            # khac "name" o tren (da gan them hau to "(GV#n)" de phan biet tren cac man khac).
            "nameRaw": t.get("name"), "title": t.get("title"), "email": t.get("email"), "phone": t.get("phone"),
            "availabilitySlots": sorted(manual_windows.get(t["id"], [])),
            "availabilityWindows": [sc.slot_label(s, params["slotsPerDay"]) for s in sorted(manual_windows.get(t["id"], []))],
            # True = cho trong cho lop CHUA phan cong giang vien (nap tu Excel),
            # khong phai mot con nguoi. Cac man danh cho GV that loc bang co nay.
            "isPlaceholder": bool(t.get("placeholder")),
        }
        for t in sorted(data["teachers"].values(), key=lambda t: t["id"])
    ]

    submissions = []
    for sid, windows in data["submissions"].items():
        s = data["sections"][sid]
        submissions.append({
            "sectionId": sid,
            "teacherId": s["teacher_id"],
            "teacherName": sc.teacher_display(data, s["teacher_id"]),
            # teacherType + duration: man hinh "Khung gio da bao" phai phan biet
            # lop THINH GIANG (dieu phoi vien nop gio) voi lop CO HUU (Giai doan 2
            # tu chon gio, khong ai nop gio ho) - truoc day tron ca 2 vao 1 bang
            # nen dem "da nop" bi sai. duration de biet 1 window keo dai may tiet.
            "teacherType": s["teacher_type"],
            "duration": s["duration"],
            "courseName": s.get("course_name"),
            "program": s["program"],
            "programLabel": sc.program_label(s["program"], data["program_faculty"], data["faculty_names"], prog_names_rev),
            "coordinator": data["coordinator_names"][s["program"]],
            "facultyId": data["program_faculty"][s["program"]],
            "facultyName": data["faculty_names"][data["program_faculty"][s["program"]]],
            "roomType": s["room_type"],
            "windowSlots": windows,
            "windowLabels": [sc.slot_label(w, params["slotsPerDay"]) for w in windows],
            "isSingleFixedWindow": len(windows) == 1,
        })
    submissions.sort(key=lambda x: (x["teacherId"], x["sectionId"]))

    cross_conflicts = sc.check_cross_program_conflicts(data)

    # Bo sung duration RIENG cua tung lop vao ket qua check-trung. Man hinh
    # Check-trung moi ve dai khung gio tren luoi tuan nen phai biet 1 window keo
    # dai bao nhieu tiet - du lieu that co duration khac nhau tung lop
    # (p_end - p_start + 1), khong dung chung params["duration"] duoc.
    for c in cross_conflicts:
        for s in c["sections"]:
            s["duration"] = data["sections"][s["sectionId"]]["duration"]

    pending_sections = []
    for sid in data["pending_section_ids"]:
        s = data["sections"][sid]
        pending_sections.append({
            "sectionId": sid,
            "teacherId": s["teacher_id"],
            "teacherName": sc.teacher_display(data, s["teacher_id"]),
            "courseName": s.get("course_name"),
            "program": s["program"],
            "programLabel": sc.program_label(s["program"], data["program_faculty"], data["faculty_names"], prog_names_rev),
            "coordinator": data["coordinator_names"][s["program"]],
            "roomType": s["room_type"],
        })
    pending_sections.sort(key=lambda x: (x["program"], x["teacherId"]))

    faculty_stats = []
    for f_id, f_name in enumerate(data["faculty_names"]):
        progs = [p for p, fid in data["program_faculty"].items() if fid == f_id]
        secs = [s for s in data["sections"].values() if s["program"] in progs]
        faculty_stats.append({
            "facultyId": f_id, "facultyName": f_name,
            "numPrograms": len(progs),
            "numSections": len(secs),
            "numGuestSections": sum(1 for s in secs if s["teacher_type"] == "GUEST"),
            "numResidentSections": sum(1 for s in secs if s["teacher_type"] == "RESIDENT"),
        })

    resp = {
        "numPrograms": data["num_programs"],
        "numTeachers": len(data["teachers"]),
        "teachers": teachers,
        "submissions": submissions,
        "pendingSections": pending_sections,
        "crossProgramConflicts": cross_conflicts,
        "facultyStats": faculty_stats,
        "facultyNames": data["faculty_names"],
        "numResident": data["num_resident"],
        "numGuest": data["num_guest"],
        "numSections": len(data["sections"]),
        "numGuestSections": sum(1 for s in data["sections"].values() if s["teacher_type"] == "GUEST"),
        "numResidentSections": sum(1 for s in data["sections"].values() if s["teacher_type"] == "RESIDENT"),
        "multiProgramGuestTeachers": multi_program_count,
        "ltPool": params["ltPool"],
        "labPool": params["labPool"],
        "numDays": params["numDays"],
        "slotsPerDay": params["slotsPerDay"],
        "duration": params["duration"],
        "isRealData": bool(extra and extra.get("isRealData")),
        "sourceLabel": (extra or {}).get("sourceLabel"),
        "numTimeAssumed": (extra or {}).get("numTimeAssumed", 0),
        # Ten file Excel da nap (neu du lieu den tu /api/manual/import/commit).
        # sourceLabel van phai la "Nhap lieu thu cong" de form cho sua, nen nguon
        # goc phai di rieng o day - khong thi giao vu khong con biet dang lam
        # tren file nao.
        "importedFrom": (extra or {}).get("importedFrom"),
        "courses": sorted(data.get("courses", {}).values(), key=lambda c: c["id"]),
        "classes": _build_classes_list(data),
    }
    return resp


def _overlaps(a, dur_a, b, dur_b):
    return not (a + dur_a <= b or b + dur_b <= a)


def _own_valid_starts(data, section_id):
    s = data["sections"][section_id]
    p = data["params"]
    return sc.valid_starts(p["numDays"], p["slotsPerDay"], s["duration"], s["teacher_type"])


def _detect_move_conflict(data, section_id, slot):
    """Kiem tra NHANH dat buoi section_id vao slot co dung GV/het phong voi cac
    buoi DANG XEP (ket qua GD1/GD2 hien co, tru chinh buoi nay) hay khong. Dung de
    (a) quyet dinh co BAT ghi ly do khong (dong 2: cho phep vi pham nhung phai ghi
    ly do), va (b) tra ve canh bao hien thi. Doc-only, khong doi gi ca - tuong tu
    logic o unplacedAnalysis.js ben frontend, dung lai chinh xac 1 cong thuc chong
    lan de khong lech ket qua giua 2 noi."""
    s = data["sections"].get(section_id)
    if not s:
        return None
    duration = s["duration"]

    placed = []
    for res in (STATE["guestResult"], STATE["residentResult"]):
        if res:
            placed.extend(l for l in res["lessons"] if l["id"] != section_id)

    teacher_blockers = [
        l for l in placed
        if l["teacherId"] == s["teacher_id"] and _overlaps(slot, duration, l["slot"], l["duration"])
    ]
    same_room = [
        l for l in placed
        if l["roomType"] == s["room_type"] and _overlaps(slot, duration, l["slot"], l["duration"])
    ]
    pool = data["params"]["ltPool"] if s["room_type"] == "LT" else data["params"]["labPool"]
    room_full = pool > 0 and len(same_room) >= pool

    if not teacher_blockers and not room_full:
        return None
    return {
        "teacherClashIds": [l["id"] for l in teacher_blockers],
        "roomFull": room_full,
        "sameRoomCount": len(same_room),
        "pool": pool,
    }


def _attach_override_metadata(data, result, teacher_type):
    """Gan {reason, problem, pinFailed} tu STATE['overrides'] len tren ket qua
    giai - CHI la metadata hien thi, khong doi vi tri bat ky buoi nao. pinFailed=
    True khi mot buoi da GHIM van roi vao unplaced (rang buoc cung nhu NoOverlap/
    Cumulative buoc CP-SAT phai bo no du domain chi con 1 lua chon) - ghim la uu
    tien rat manh nhung khong tuyet doi truoc rang buoc cung, dung nhu da chon o
    dong 1."""
    if not result:
        return result
    overrides = {
        sid: ov for sid, ov in STATE["overrides"].items()
        if data["sections"].get(sid, {}).get("teacher_type") == teacher_type
    }
    # LUON gan lai (ke ca rong {}) - neu overrides rong ma return som o day, key
    # result["overrides"] cu se con SOT LAI gia tri cua lan goi truoc (vi du sau
    # khi bo ghim buoi DUY NHAT dang co, ban { } moi khong duoc ghi de len ban cu).
    if not overrides:
        result["overrides"] = {}
        return result

    placed_ids = {l["id"] for l in result["lessons"]}
    out = {}
    for sid, ov in overrides.items():
        out[sid] = {
            "reason": ov.get("reason"),
            "problem": ov.get("problem"),
            "pinFailed": sid not in placed_ids,
        }
    result["overrides"] = out
    return result


def _solve_guest_with_overrides(data):
    """Ghim (dong 1) o Giai doan 1: thu hep TAM THOI danh sach khung gio da bao
    cua buoi bi ghim ve DUY NHAT 1 slot truoc khi goi solve_guest_phase(), roi
    tra lai nguyen ven sau do. Day la cach ghim KHONG can sua scheduler_core.py -
    ham do von da chon 1 slot tu dung window_bools cua data['submissions'][sid];
    thu hep domain ve 1 gia tri la ep no chi con 1 lua chon (dat o do, hoac khong
    xep duoc neu xung dot rang buoc cung nhu NoOverlap/Cumulative voi buoi khac)."""
    guest_overrides = {
        sid: ov for sid, ov in STATE["overrides"].items()
        if data["sections"].get(sid, {}).get("teacher_type") == "GUEST"
    }
    if not guest_overrides:
        return sc.solve_guest_phase(data)

    original = {sid: data["submissions"][sid] for sid in guest_overrides}
    try:
        for sid, ov in guest_overrides.items():
            data["submissions"][sid] = [ov["slot"]]
        return sc.solve_guest_phase(data)
    finally:
        for sid, windows in original.items():
            data["submissions"][sid] = windows


def _forbidden_from_resident_overrides(data):
    """Ghim (dong 1) o Giai doan 2: solve_resident_phase() da co san tham so
    'forbidden' (danh sach slot BI CAM cho 1 section) - tai dung CHINH co che do,
    chi doi nguon: truoc day forbidden den tu nut 'Tu choi' cu (STATE['forbidden']),
    gio tinh THANG tu STATE['overrides'] bang cach cam TOAN BO slot hop le TRU
    slot da ghim, ep domain con lai dung 1 lua chon."""
    forbidden = {}
    for sid, ov in STATE["overrides"].items():
        s = data["sections"].get(sid)
        if not s or s["teacher_type"] != "RESIDENT":
            continue
        forbidden[sid] = [v for v in _own_valid_starts(data, sid) if v != ov["slot"]]
    return forbidden


@app.post("/api/generate")
def api_generate():
    params = {**DEFAULT_PARAMS, **(request.get_json(silent=True) or {})}
    data = sc.generate_data(params)
    STATE["data"] = data
    STATE["extra"] = None
    STATE["guestResult"] = None
    STATE["residentResult"] = None
    STATE["overrides"] = {}
    return jsonify(_build_data_response(data))


REAL_DATA_FILES = {
    "standard": {
        "path": r"D:\Cổng đào tạo\TKB\DEMO_CP_SAT\FATE.TKB.HK2_2025-2026.xlsx",
        "label": "FATE.TKB.HK2_2025-2026.xlsx (sheet 'FATE') — cấu trúc CHUẨN, dùng cho các kỳ sau",
    },
    "legacy": {
        "path": r"D:\Cổng đào tạo\TKB\DEMO_CP_SAT\FATE.TKB.HK1 2026-2027.xlsx",
        "label": "FATE.TKB.HK1 2026-2027.xlsx (sheet 'Giảng dạy cho FATE') — cấu trúc cũ",
    },
}


_PROGRAM_SPLIT_RE = re.compile(r"[+.]")


def _canonical_program_name(raw):
    """Chuan hoa ten chuong trinh GHEP ve 1 dang duy nhat: tach theo dau '+' hoac
    '.', sap xep cac phan theo alphabet, noi lai bang '+'. Vi du that trong file
    Excel: 'FTH+ESAS', 'ESAS+FTH', 'FTH.ESAS' deu la MOT chuong trinh nhung viet
    3 kieu khac nhau -> load_real_fate_data() (khong sua file do) dang tao ra 3
    program_id rieng cho chung, khien 19 'chuong trinh' thuc chat chi la 13, va
    DPV cua cung 1 pham vi bi tach doi (DPV-FTH+ESAS / DPV-ESAS+FTH).
    Chuong trinh 1-thanh-phan (vd 'BCSE') tra ve nguyen ven, khong dung den ham nay."""
    parts = [p.strip() for p in _PROGRAM_SPLIT_RE.split(raw) if p.strip()]
    if len(parts) <= 1:
        return raw
    return "+".join(sorted(parts))


def _merge_duplicate_programs(data):
    """Ghep cac program_id ma ten chi khac thu tu/dau phan cach thanh 1 id duy
    nhat, NGAY SAU KHI load_real_fate_data() tra ve - truoc khi dua vao
    check_cross_program_conflicts/solve_*. Chi doi du lieu o tang app.py, khong
    sua scheduler_core.py: cac ham do van doc dung "program" nhu mot int id binh
    thuong, chi la nay id da duoc gop dung truoc khi chung nhin thay."""
    raw_by_pid = data.get("program_names_reverse") or {}
    if not raw_by_pid:
        return data

    groups = {}  # canonical_name -> list[pid], theo dung thu tu pid tang dan
    for pid in sorted(raw_by_pid):
        canon = _canonical_program_name(raw_by_pid[pid])
        groups.setdefault(canon, []).append(pid)

    if not any(len(pids) > 1 for pids in groups.values()):
        return data  # khong co ten trung lap - khong can dong gi them

    pid_remap = {}
    for canon, pids in groups.items():
        target = pids[0]  # pid nho nhat trong nhom lam id dai dien, on dinh
        for pid in pids:
            pid_remap[pid] = target

    for s in data["sections"].values():
        s["program"] = pid_remap[s["program"]]
    for t in data["teachers"].values():
        if "home_program" in t:
            t["home_program"] = pid_remap[t["home_program"]]

    kept_pids = sorted(set(pid_remap.values()))
    data["program_faculty"] = {pid: data["program_faculty"][pid] for pid in kept_pids}
    data["program_names_reverse"] = {pid: _canonical_program_name(raw_by_pid[pid]) for pid in kept_pids}
    data["coordinator_names"] = {pid: f"DPV-{data['program_names_reverse'][pid]}" for pid in kept_pids}
    data["programs"] = kept_pids
    data["num_programs"] = len(kept_pids)
    return data


@app.post("/api/load-real-data")
def api_load_real_data():
    """Nap du lieu THAT tu file Excel ke hoach giang day, thay cho sinh gia lap.
    Body JSON tuy chon: {"file": "standard" | "legacy"} - mac dinh "standard"."""
    body = request.get_json(silent=True) or {}
    file_key = body.get("file", "standard")
    if file_key not in REAL_DATA_FILES:
        return jsonify({"error": f"file phai la 'standard' hoac 'legacy', nhan duoc: {file_key}"}), 400
    xlsx_path = REAL_DATA_FILES[file_key]["path"]
    try:
        data = sc.load_real_fate_data(xlsx_path)
    except FileNotFoundError:
        return jsonify({"error": f"Khong tim thay file: {xlsx_path}"}), 400
    data = _merge_duplicate_programs(data)
    extra = {
        "isRealData": True,
        "sourceLabel": REAL_DATA_FILES[file_key]["label"],
        "numTimeAssumed": data.get("num_time_assumed", 0),
    }
    STATE["data"] = data
    STATE["extra"] = extra
    STATE["guestResult"] = None
    STATE["residentResult"] = None
    STATE["overrides"] = {}
    return jsonify(_build_data_response(data, extra))


@app.get("/api/data")
def api_data():
    """Tra lai dung cau truc _build_data_response() cho du lieu dang co trong
    STATE - dung khi SPA chuyen man/refresh ma khong muon goi lai generate/
    load-real-data (se lam mat guestResult/residentResult/forbidden dang co)."""
    if STATE["data"] is None:
        return jsonify({"error": "Chua co du lieu. Goi /api/generate hoac /api/load-real-data truoc."}), 400
    return jsonify(_build_data_response(STATE["data"], STATE.get("extra")))


_SNAPSHOT_PATH = os.path.join(os.path.dirname(__file__), "manual_state_snapshot.json")


def _save_snapshot():
    """Ghi STATE['data']/STATE['extra'] xuong file JSON sau moi thay doi qua cac
    endpoint /api/manual/* - de KHONG mat du lieu nhap tay khi restart server (nay
    la nguon du lieu CHINH thay Excel, khac voi generate/load-real-data von co the
    nap lai tu file goc bat cu luc nao). Loi ghi file (vd het dung luong) khong
    duoc chan luong nhap lieu cua nguoi dung - chi bo qua, demo local 1 nguoi dung."""
    if STATE["data"] is None:
        return
    snapshot = {**STATE["data"], "forced_conflict_teacher_ids": sorted(STATE["data"].get("forced_conflict_teacher_ids") or [])}
    try:
        with open(_SNAPSHOT_PATH, "w", encoding="utf-8") as f:
            json.dump({"data": snapshot, "extra": STATE.get("extra")}, f, ensure_ascii=False)
    except OSError:
        pass


def _load_snapshot():
    """Nap lai snapshot nhap tay khi Flask khoi dong (neu co) - dao nguoc dung
    _save_snapshot(). Cac dict dung int lam key (teachers/sections/submissions/...)
    bi JSON bien key thanh string, phai chuyen lai int o day."""
    if not os.path.exists(_SNAPSHOT_PATH):
        return
    try:
        with open(_SNAPSHOT_PATH, encoding="utf-8") as f:
            snap = json.load(f)
    except (OSError, json.JSONDecodeError):
        return
    data = snap.get("data")
    if not data:
        return
    for key in ("teachers", "sections", "submissions", "courses", "program_faculty",
                "coordinator_names", "program_names_reverse", "manual_teacher_windows"):
        if isinstance(data.get(key), dict):
            data[key] = {int(k): v for k, v in data[key].items()}
    data["forced_conflict_teacher_ids"] = set(data.get("forced_conflict_teacher_ids") or [])
    STATE["data"] = data
    STATE["extra"] = snap.get("extra")


def _parse_class_time(body, slots_per_day, teacher_type=None):
    """Doc {day, periodStart, periodEnd, autoSchedule} tu body 1 lop nhap tay -
    day gio da CHOT boi con nguoi cho dung lop nay (khac voi 'khung gio ranh cua
    GV' o /api/manual/teacher, von la nhieu lua chon de GV/dieu phoi vien khai
    bao roi solver moi chon 1). Tra ve (time_dict, error) - time_dict la
    {'day','period_start','period_end'} hoac None neu tick 'de he thong tu xep'
    hoac de trong ca 3 truong; error la str neu du lieu nhap sai dinh dang/khoang.
    teacher_type (neu co): chan luon Thu vuot qua quy dinh (thinh giang toi
    Thu 7, co huu toi Thu 6) - giao vu go tay cung khong lach duoc rang buoc
    ma solver dang tuan theo (xem sc.MAX_DAY_INDEX)."""
    if body.get("autoSchedule"):
        return None, None
    day, p_start, p_end = body.get("day"), body.get("periodStart"), body.get("periodEnd")
    if day in (None, "") and p_start in (None, "") and p_end in (None, ""):
        return None, None
    try:
        day, p_start, p_end = int(day), int(p_start), int(p_end)
    except (TypeError, ValueError):
        return None, "Thứ/Tiết đầu/Tiết cuối phải là số nguyên."
    if not (0 <= day <= 6) or p_start < 1 or p_end < p_start or p_end > slots_per_day:
        return None, "Thứ/Tiết không hợp lệ."
    if teacher_type is not None and day > sc.max_day_index(teacher_type):
        max_label = _DAY_LABELS_VN[sc.max_day_index(teacher_type)]
        loai = "Thỉnh giảng" if teacher_type == "GUEST" else "Cơ hữu"
        return None, f"{loai} chỉ được dạy tới {max_label}."
    return {"day": day, "period_start": p_start, "period_end": p_end}, None


def _apply_section_time(data, sid, teacher, duration, time_info):
    """Cap nhat submissions[sid]/pending_section_ids/original_slot cua 1 lop dua
    theo time_info (None = de he thong tu xep) - dung chung cho tao moi va sua.
    time_info khac None: gio da CHOT, submissions rut ve DUNG 1 slot do (giong 1
    dong Excel co gio parse duoc), bo qua het co che 'khung gio ranh cua GV'.
    time_info None: giu nguyen hanh vi /api/manual/section cu - RESIDENT tu do
    hoan toan (Giai doan 2), GUEST tra theo khung gio ranh da khai (/api/manual/
    teacher), neu chua khai gi thi vao pending_section_ids nhu truoc."""
    s = data["sections"][sid]
    if sid in data["pending_section_ids"]:
        data["pending_section_ids"].remove(sid)

    if time_info is not None:
        slot = time_info["day"] * data["params"]["slotsPerDay"] + (time_info["period_start"] - 1)
        s["day"], s["period_start"], s["period_end"] = time_info["day"], time_info["period_start"], time_info["period_end"]
        s["original_slot"] = slot
        s["time_assumed"] = False
        data["submissions"][sid] = [slot]
        return

    s["day"] = s["period_start"] = s["period_end"] = s["original_slot"] = None
    s["time_assumed"] = True
    if teacher["type"] == "RESIDENT":
        data["submissions"][sid] = []
        return
    slots_per_day = data["params"]["slotsPerDay"]
    available = data.get("manual_teacher_windows", {}).get(teacher["id"], [])
    starts = _valid_starts_from_slots(available, duration, slots_per_day)
    if starts:
        data["submissions"][sid] = starts
    else:
        data["submissions"][sid] = []
        data["pending_section_ids"].append(sid)


def _validate_section_body(data, body):
    """Doc + validate toan bo body cho 1 lop - dung chung cho POST tao moi va
    PATCH sua (PATCH doi hoi gui DU ca form, khong merge tung phan field-mot, de
    tranh tinh sai submissions khi chi doi 1 vai field ma thieu ngu canh gio/GV
    hien tai). Tra ve (fields, teacher, duration, time_info, None) neu hop le,
    hoac (None, None, None, None, error_message) neu khong."""
    try:
        teacher_id = int(body["teacherId"])
    except (KeyError, TypeError, ValueError):
        return None, None, None, None, "Thiếu hoặc sai teacherId."
    teacher = data["teachers"].get(teacher_id)
    if teacher is None:
        return None, None, None, None, f"Không tìm thấy giảng viên id={teacher_id}."

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

    time_info, time_err = _parse_class_time(body, data["params"]["slotsPerDay"], teacher["type"])
    if time_err:
        return None, None, None, None, time_err

    class_code = (body.get("classCode") or "").strip()
    lt_credits = body.get("ltCredits")
    th_credits = body.get("thCredits")
    program_id = _get_or_create_program(data, body.get("program"))
    room_type = "LAB" if (th_credits or 0) else "LT"

    fields = {
        "program": program_id, "course_id": course_id,
        "course_name": f"{course['name']} ({class_code})" if class_code else course["name"],
        "teacher_id": teacher_id, "teacher_ids": [teacher_id],
        "teacher_type": teacher["type"], "room_type": room_type, "duration": duration,
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


def _empty_manual_data():
    """Bo du lieu rong de bat dau 'nhap lieu thu cong' - dung cau truc voi
    generate_data()/load_real_fate_data() de solve_guest_phase/solve_resident_phase/
    check_cross_program_conflicts/_build_data_response dung duoc khong can sua gi.
    numDays=7/slotsPerDay=12 khop quy uoc cua load_real_fate_data (Thu2..CN, toi da
    12 tiet/ngay)."""
    return {
        "params": {
            "numDays": 7, "slotsPerDay": 12, "duration": 2,
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
        "manual_teacher_windows": {},  # teacher_id -> [slot, ...] (slot=day*slotsPerDay+period) - CHI GUEST moi dung
        "num_time_assumed": 0,
    }


def _get_or_create_program(data, program_name):
    """Tra ve program_id da co neu trung ten (khong phan biet hoa/thuong, VA
    khong phan biet thu tu ghep '+'/'.' - dung _canonical_program_name nhu duong
    Excel de tranh tao 2 CTDT rieng cho 'FTH+ESAS' va 'ESAS+FTH'), tao moi neu
    chua co - dung khi giao vu nhap tay ten CTDT tu do, khong chon tu danh sach
    co san."""
    program_name = (program_name or "").strip() or "Chung"
    canon = _canonical_program_name(program_name).lower()
    rev = data.setdefault("program_names_reverse", {})
    for pid, name in rev.items():
        if _canonical_program_name(name).lower() == canon:
            return pid
    pid = len(data["program_faculty"])
    while pid in data["program_faculty"]:
        pid += 1
    rev[pid] = program_name
    data["programs"].append(pid)
    data["program_faculty"][pid] = 0  # nhap tay: dung chung 1 "khoa" mac dinh cho don gian
    data["coordinator_names"][pid] = f"DPV-{program_name}"
    data["num_programs"] = len(data["program_faculty"])
    return pid


def _valid_starts_from_slots(available_slots, duration, slots_per_day):
    """Slot bat dau hop le = TOAN BO 'duration' slot lien tiep TU day (cung 1
    ngay, KHONG duoc vat sang ngay hom sau) deu nam trong tap slot GV ranh.
    available_slots la tap PHANG cac slot ranh (slot = day*slotsPerDay+period,
    0-indexed) - cung dinh dang voi data['submissions'], khong phai 1 khoang
    lien tuc duy nhat nhu ham cu (_expand_window_to_starts, da bo) - ho tro GV
    ranh nhieu doan rieng le trong cung 1 ngay (vd ranh tiet 1-3 VA rieng tiet
    7-9), dong thoi tai dung dung dinh dang SubmissionWindowGrid da phat sinh
    san (frontend/src/adapters/submissionAdapter.js) - khong can widget rieng."""
    avail = set(available_slots)
    starts = []
    for slot in avail:
        _, period = divmod(slot, slots_per_day)
        if period + duration > slots_per_day:
            continue  # buoi hoc se vat sang ngay hom sau - khong hop le
        if all((slot + k) in avail for k in range(duration)):
            starts.append(slot)
    return sorted(starts)


def _sync_teacher_sections(data, teacher_id):
    """Dong bo lai cac lop cua 1 GV sau khi PATCH doi loai GV hoac gio ranh.
    CHI cham vao lop nhap qua UI moi (co course_id - lop tu Excel/gia lap
    khong co truong nay, dung co che 'tu do chon ca tuan' rieng qua
    valid_starts() toan tuan, KHONG lien quan manual_teacher_windows, khong
    duoc dong bo lai o day) VA dang time_assumed=True (chua duoc chot gio cu
    the boi giao vu - gio da chot thi khong phu thuoc GV ranh luc nao nua).
    Khop theo teacher_ids (ca dong giang day, giong check_cross_program_conflicts
    ben scheduler_core.py), nhung teacher_type tren section CHI cap nhat khi
    tid la GV CHINH (s['teacher_id']) - GV chinh moi quyet dinh section thuoc
    Giai doan 1/2, dung nhu luc tao (xem _validate_section_body)."""
    teacher = data["teachers"][teacher_id]
    slots_per_day = data["params"]["slotsPerDay"]
    availability = data.get("manual_teacher_windows", {}).get(teacher_id, [])
    for sid, s in data["sections"].items():
        if s.get("course_id") is None:
            continue
        tids = s.get("teacher_ids") or [s["teacher_id"]]
        if teacher_id not in tids:
            continue
        if teacher_id == s["teacher_id"]:
            s["teacher_type"] = teacher["type"]
        if not s.get("time_assumed"):
            continue
        if s["teacher_type"] == "RESIDENT":
            data["submissions"][sid] = []
            if sid in data["pending_section_ids"]:
                data["pending_section_ids"].remove(sid)
            continue
        starts = _valid_starts_from_slots(availability, s["duration"], slots_per_day)
        data["submissions"][sid] = starts
        if starts and sid in data["pending_section_ids"]:
            data["pending_section_ids"].remove(sid)
        elif not starts and sid not in data["pending_section_ids"]:
            data["pending_section_ids"].append(sid)


@app.post("/api/manual/init")
def api_manual_init():
    """Bat dau 'nhap lieu thu cong': XOA HET du lieu dang co (gia lap/Excel truoc
    do), bat dau tu 1 bo du lieu rong roi giao vu tu them GV/ca day bang tay qua
    /api/manual/teacher va /api/manual/section."""
    data = _empty_manual_data()
    extra = {"isRealData": False, "sourceLabel": "Nhập liệu thủ công", "numTimeAssumed": 0}
    STATE["data"] = data
    STATE["extra"] = extra
    STATE["guestResult"] = None
    STATE["residentResult"] = None
    STATE["overrides"] = {}
    _save_snapshot()
    return jsonify(_build_data_response(data, extra))


def _build_manual_data_from_rows(rows):
    """Dung bo du lieu NHAP TAY tu cac dong Excel da chuan hoa (fate_import).

    KHONG tu ghep dict bang tay: chay lai dung nhung ham ma endpoint nhap tay
    dung (_validate_section_body -> _get_or_create_program, _apply_section_time),
    de du lieu nap tu file KHONG khac gi du lieu giao vu go tay - program_id,
    submissions, pending_section_ids, room_type... deu do cung mot doan code sinh
    ra. Neu sau nay sua luat o day thi ca hai duong deu doi theo.

    Tra ve (data, loi) - loi la cac dong khong dung duoc section, kem ly do.
    """
    data = _empty_manual_data()
    loi = []
    canh_bao = []

    # --- Giang vien: gop theo TEN (da chuan hoa), KHONG theo (ten, don vi) ---
    #
    # Trong file that, cung mot nguoi hay bi ghi don vi moi dong mot kieu:
    # "Truong DH Viet Nhat" / "Truong Dai hoc Viet Nhat", co dong con bo trong.
    # Neu gop theo (ten, don vi) thi mot nguoi tach thanh 2-3 ban ghi -> he thong
    # coi ho la nhung nguoi KHAC NHAU va khong con phat hien duoc ho bi trung
    # lich voi chinh minh, tuc mat dung cong dung chinh cua cong cu. Nang hon:
    # dong bo trong don vi se bi xep GUEST trong khi cac dong khac la RESIDENT,
    # mot nguoi bi chia sang ca hai giai doan.
    #
    # Doi lai, hai nguoi TRUNG HO TEN se bi gop lam mot. Trong pham vi mot file
    # cua mot khoa thi hiem, va huong sai nay AN TOAN hon: gop nham chi lam bao
    # thua xung dot (giao vu nhin ra ngay), con tach nham thi GIAU MAT xung dot.
    # Moi truong hop don vi ghi khac nhau deu duoc bao len o buoc xem truoc.
    teacher_ids = {}
    org_khac = {}
    for idx, r in enumerate(rows):
        org = r["teacherOrg"].strip()

        # Lop CHUA phan cong giang vien: moi lop mot ban ghi RIENG, khong dung
        # chung mot ban ghi "Phong Dao tao dieu phoi".
        #
        # Dung chung thi he thong coi 60 lop do la CUA MOT NGUOI - do thuc te tren
        # file HK1 cho 54 o gio chong nhau, tuc hop thu van de se ngap bao "trung
        # giang vien" GIA va nhan chim cac vu trung THAT. Ma chung von khong phai
        # mot nguoi, chi la cho trong cho den khi giao vu phan cong.
        #
        # Danh dau `placeholder` de cac man danh cho giang vien that (vd "Gio ranh
        # GV") loc chung ra, khong hien 114 dong "Phong Dao tao dieu phoi".
        if r.get("chuaPhanCong"):
            tid = len(data["teachers"])
            data["teachers"][tid] = {
                "id": tid, "name": r["teacherName"] or "(Chưa phân công)",
                "type": "RESIDENT" if ("việt nhật" in org.lower() or "viet nhat" in org.lower()) else "GUEST",
                "org": org, "title": r["teacherTitle"],
                "email": r["teacherEmail"], "phone": r["teacherPhone"],
                "placeholder": True,
            }
            data.setdefault("manual_teacher_windows", {})[tid] = []
            teacher_ids[f"__chua_phan_cong_{idx}"] = tid
            continue

        key = " ".join(r["teacherName"].split()).lower()
        if key in teacher_ids:
            t = data["teachers"][teacher_ids[key]]
            if org and org != t["org"]:
                if t["org"]:
                    org_khac.setdefault(t["name"], {t["org"]}).add(org)
                else:
                    # Ban ghi dau bo trong don vi -> lay don vi dau tien tim duoc,
                    # va phan loai lai GUEST/RESIDENT theo no.
                    t["org"] = org
                    low = org.lower()
                    t["type"] = "RESIDENT" if ("việt nhật" in low or "viet nhat" in low) else "GUEST"
            # Cac truong con lai: lap day cho nao con trong.
            for field, val in (("title", r["teacherTitle"]), ("email", r["teacherEmail"]),
                               ("phone", r["teacherPhone"])):
                if not t[field] and val:
                    t[field] = val
            continue

        low = org.lower()
        tid = len(data["teachers"])
        data["teachers"][tid] = {
            "id": tid,
            "name": r["teacherName"],
            # Cung luat phan loai voi load_real_fate_data: don vi cong tac co
            # "Viet Nhat" -> co huu (Giai doan 2), con lai -> thinh giang (GD1).
            "type": "RESIDENT" if ("việt nhật" in low or "viet nhat" in low) else "GUEST",
            "org": org,
            "title": r["teacherTitle"],
            "email": r["teacherEmail"],
            "phone": r["teacherPhone"],
        }
        # Chua khai gio ranh - giao vu se khai sau o "Chuan bi du lieu".
        data.setdefault("manual_teacher_windows", {})[tid] = []
        teacher_ids[key] = tid

    for ten, orgs in org_khac.items():
        canh_bao.append({
            "row": None, "kind": "gop_giang_vien",
            "detail": f"{ten} — {' · '.join(sorted(orgs))}",
        })

    # --- Hoc phan: gop theo (ma, ten) ---
    course_ids = {}
    for r in rows:
        key = (r["courseCode"].strip().lower(), r["courseName"].strip().lower())
        if key in course_ids:
            continue
        cid = len(data["courses"])
        data["courses"][cid] = {
            "id": cid, "code": r["courseCode"], "name": r["courseName"],
            "credits": r["credits"],
        }
        course_ids[key] = cid

    # --- Lop ---
    for idx, r in enumerate(rows):
        tkey = (f"__chua_phan_cong_{idx}" if r.get("chuaPhanCong")
                else " ".join(r["teacherName"].split()).lower())
        body = {
            "teacherId": teacher_ids[tkey],
            "courseId": course_ids[(r["courseCode"].strip().lower(), r["courseName"].strip().lower())],
            "duration": r["duration"] or data["params"]["duration"],
            "classCode": r["classCode"], "program": r["program"],
            "ltCredits": r["ltCredits"], "thCredits": r["thCredits"],
            "cohort": r["cohort"], "expectedStudents": r["expectedStudents"],
            "location": r["location"], "teachingMode": r["teachingMode"],
            "language": r["language"], "otherRequirements": r["otherRequirements"],
            "notes": r["notes"], "coordinatorOverride": r["coordinatorOverride"],
            "prevTeacherName": r["prevTeacherName"], "prevTeacherOrg": r["prevTeacherOrg"],
            "teachingHoursLt": r["teachingHoursLt"], "teachingHoursTh": r["teachingHoursTh"],
        }
        if r["autoSchedule"]:
            body["autoSchedule"] = True
        else:
            body["day"], body["periodStart"], body["periodEnd"] = r["day"], r["periodStart"], r["periodEnd"]

        fields, teacher, duration, time_info, err = _validate_section_body(data, body)
        if err:
            loi.append({"row": r["excelRow"], "reason": err})
            continue
        sid = len(data["sections"])
        while sid in data["sections"]:
            sid += 1
        data["sections"][sid] = {"id": sid, **fields}
        _apply_section_time(data, sid, teacher, duration, time_info)

    data["num_resident"] = sum(1 for t in data["teachers"].values() if t["type"] == "RESIDENT")
    data["num_guest"] = len(data["teachers"]) - data["num_resident"]
    data["num_time_assumed"] = sum(1 for s in data["sections"].values() if s.get("time_assumed"))
    return data, loi, canh_bao


# Nhan doc duoc cho tung LOAI dong bi bo / dong can luu y. Gom theo loai roi moi
# hien - ban dau tra ve danh sach phang rồi cat 20 dong dau, ra man hinh thanh 20
# dong lap y het nhau va mot dong "…va 12 dong nua cung loai" khong ai hieu la
# loai gi. Nguoi dung can biet QUY TAC nao lam dong bi bo, kem so luong - khong
# phai doc tung dong mot.
_NHAN_BO_QUA = {
    "don_vi_dieu_phoi": "Ô giảng viên ghi tên một ĐƠN VỊ điều phối, không phải một người cụ thể",
    "thieu_ten_hoc_phan": "Không xác định được Tên học phần cho dòng đó",
    "o_gv_rong": "Ô giảng viên rỗng sau khi tách tên",
}
_NHAN_LUU_Y = {
    "chua_phan_cong": "Lớp CHƯA phân công giảng viên — vẫn nạp đủ, ô giảng viên giữ nguyên "
                      "như trong file (hoặc để trống) để gán sau",
    "thieu_ten_hoc_phan": "Dòng không có Tên học phần ở bất kỳ dòng nào phía trên — "
                          "đặt tạm tên theo mã lớp, sửa lại trong form",
    "dong_giang": "Ô ghi nhiều giảng viên đồng giảng — chỉ lấy người đầu làm GV chính, "
                  "những người còn lại cần thêm bằng tay",
    "nhieu_buoi": "Dòng ghi nhiều buổi trong tuần — tách thành nhiều lớp cùng mã lớp",
    "gop_giang_vien": "Cùng một họ tên nhưng ghi nhiều đơn vị công tác khác nhau — "
                      "đã gộp làm một người và lấy đơn vị ghi đầu tiên",
}


def _gom_theo_loai(items, nhan_map):
    """Gom danh sach {row, kind, detail} theo `kind`. Moi nhom kem so luong, danh
    sach so dong Excel, va cac gia tri `detail` khac nhau da gap (co dem)."""
    nhom = {}
    for x in items:
        kind = x.get("kind", "khac")
        g = nhom.setdefault(kind, {"loai": kind, "nhan": nhan_map.get(kind, kind),
                                   "so": 0, "dong": [], "_ct": {}})
        g["so"] += 1
        if x.get("row") is not None:
            g["dong"].append(x["row"])
        d = (x.get("detail") or "").strip()
        if d:
            g["_ct"][d] = g["_ct"].get(d, 0) + 1
    out = []
    for g in nhom.values():
        g["chiTiet"] = [{"text": t, "so": n}
                        for t, n in sorted(g.pop("_ct").items(), key=lambda kv: -kv[1])]
        out.append(g)
    return sorted(out, key=lambda g: -g["so"])


@app.post("/api/manual/import/preview")
def api_manual_import_preview():
    """Doc file Excel duoc tai len va tra ve BAN XEM TRUOC - CHUA ghi gi vao STATE.

    Dung lai luon ket qua da dung duoc (cache o STATE['import_pending']) de buoc
    'commit' chi viec gan vao, khong phai tai file len lan hai va khong co nguy co
    lan 2 ra ket qua khac lan 1.
    """
    f = request.files.get("file")
    if f is None or not f.filename:
        return jsonify({"error": "Chưa chọn file."}), 400

    result, err = fate_import.read_rows(f)
    if err:
        return jsonify({"error": err}), 400

    data, loi, canh_bao_gv = _build_manual_data_from_rows(result["rows"])
    summary = fate_import.summarize(result)
    summary["soLopDungDuoc"] = len(data["sections"])
    # Lay so GV/hoc phan THAT sau khi gop, khong dung con dem tho cua summarize()
    # - neu khong, so o ban xem truoc se lech voi so thuc te sau khi ghi.
    summary["soGiangVien"] = len(data["teachers"])
    summary["soHocPhan"] = len(data["courses"])
    summary["soCanhBao"] = len(result["warnings"]) + len(canh_bao_gv)

    STATE["import_pending"] = {
        "data": data,
        "fileName": f.filename,
        "sheet": result["sheet"],
    }

    return jsonify({
        "fileName": f.filename,
        "summary": summary,
        # Gom theo LOAI, khong cat top-20: so nhom it (2-3) nen gui het duoc, ma
        # nguoi dung doc mot cai la biet ngay co bao nhieu kieu dong bi bo va moi
        # kieu bao nhieu dong.
        "skippedGroups": _gom_theo_loai(result["skipped"], _NHAN_BO_QUA),
        "warningGroups": _gom_theo_loai(result["warnings"] + canh_bao_gv, _NHAN_LUU_Y),
        "errors": loi[:20],
        "sampleRows": [
            {
                "excelRow": r["excelRow"], "courseCode": r["courseCode"],
                "courseName": r["courseName"], "classCode": r["classCode"],
                "program": r["program"], "teacherName": r["teacherName"],
                "day": r["day"], "periodStart": r["periodStart"], "periodEnd": r["periodEnd"],
            }
            for r in result["rows"][:8]
        ],
    })


@app.post("/api/manual/import/commit")
def api_manual_import_commit():
    """Ghi ban xem truoc vao STATE - XOA HET du lieu dang co (da xac nhan o UI).

    Dat sourceLabel = "Nhap lieu thu cong" chu KHONG phai ten file: form
    "Du lieu hoc phan" chi mo khoa sua khi thay nhan do (xem isManualMode ben
    ManualEntryPage). Ten file di rieng qua 'importedFrom' de van truy nguyen duoc.
    """
    pending = STATE.get("import_pending")
    if not pending:
        return jsonify({"error": "Chưa có bản xem trước. Hãy tải file lên trước."}), 400

    STATE["data"] = pending["data"]
    STATE["extra"] = {
        "isRealData": False,
        "sourceLabel": "Nhập liệu thủ công",
        "numTimeAssumed": pending["data"].get("num_time_assumed", 0),
        "importedFrom": f"{pending['fileName']} (sheet '{pending['sheet']}')",
    }
    STATE["guestResult"] = None
    STATE["residentResult"] = None
    STATE["overrides"] = {}
    STATE["import_pending"] = None

    _save_snapshot()
    return jsonify(_build_data_response(STATE["data"], STATE["extra"]))


def _parse_availability_slots(data, body):
    """Doc 'availability' tu body: danh sach SO NGUYEN slot (slot=day*slotsPerDay+
    period, 0-indexed) - cung dinh dang data['submissions'] va cung dinh dang
    SubmissionWindowGrid/submissionAdapter.js da phat sinh san o frontend. Tra
    ve (slots, error) - slots la list da sap xep, error la str neu co gia tri
    ngoai pham vi tuan."""
    num_days, slots_per_day = data["params"]["numDays"], data["params"]["slotsPerDay"]
    # "availability" chi co tac dung voi GUEST (xem docstring api_manual_add_teacher)
    # - gioi han toi Thu 7 theo dung quy tac sc.MAX_DAY_INDEX.
    num_days = min(num_days, sc.max_day_index("GUEST") + 1)
    max_slot = num_days * slots_per_day
    try:
        slots = sorted({int(s) for s in (body.get("availability") or [])})
    except (TypeError, ValueError):
        return None, "availability phải là danh sách số nguyên (slot)."
    if any(s < 0 or s >= max_slot for s in slots):
        return None, "Có slot ngoài phạm vi tuần (thỉnh giảng chỉ dạy tới Thứ 7)."
    return slots, None


@app.post("/api/manual/clear-times")
def api_manual_clear_times():
    """'Xoá giờ' hàng loạt tren man 'Du lieu hoc phan': dat lai Thu/Tiet dau/Tiet
    cuoi cua NHIEU lop cung luc thanh 'de he thong tu xep' (time_info=None),
    dung LAI _apply_section_time() dung nhu sua tung lop mot (khong tu viet lai
    logic GUEST/RESIDENT). Body JSON: {sectionIds: [int, ...]} - danh sach lop
    dang hien theo bo loc HIEN TAI o frontend, de xoa dung nhung dong giao vu
    dang thay tren man (WYSIWYG), khong phai toan bo du lieu."""
    if STATE["data"] is None:
        return jsonify({"error": "Chưa có dữ liệu."}), 400
    data = STATE["data"]
    body = request.get_json(force=True)
    try:
        section_ids = [int(x) for x in (body.get("sectionIds") or [])]
    except (TypeError, ValueError):
        return jsonify({"error": "sectionIds phải là danh sách số nguyên."}), 400

    cleared = 0
    for sid in section_ids:
        s = data["sections"].get(sid)
        teacher = data["teachers"].get(s["teacher_id"]) if s else None
        if s is None or teacher is None:
            continue
        _apply_section_time(data, sid, teacher, s["duration"], None)
        # Gio cu khong con - "Trang thai lich" (tu Luu thoi khoa bieu) da het
        # nghia, khong the de nguyen kieu "Da xep" tren mot lop vua bi xoa gio.
        s["schedule_status"] = None
        cleared += 1

    _save_snapshot()
    resp = _build_data_response(data, STATE.get("extra"))
    resp["clearedCount"] = cleared
    return jsonify(resp)


@app.post("/api/manual/teacher")
def api_manual_add_teacher():
    """Them 1 giang vien nhap tay. Body JSON:
    {name, org, title, email, phone, teacherType: 'GUEST'|'RESIDENT', availability: [slot, ...]}
    'availability' CHI co tac dung voi GUEST (co huu Giai doan 2 luon tu do chon
    gio, khong can khai bao - theo quyet dinh cua giao vu), la danh sach slot
    PHANG GV ranh (xem _parse_availability_slots) - tick MOI tiet ranh, khong
    chi tiet bat dau, he thong tu tim gio bat dau hop le qua
    _valid_starts_from_slots(). title/email/phone la tuy chon (fill-rate thuc
    te trong Excel rat thap)."""
    if STATE["data"] is None:
        return jsonify({"error": "Chua khoi tao du lieu nhap tay. Goi /api/manual/init truoc."}), 400
    data = STATE["data"]
    body = request.get_json(force=True)

    name = (body.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Thieu Ho ten giang vien."}), 400
    teacher_type = body.get("teacherType")
    if teacher_type not in ("GUEST", "RESIDENT"):
        return jsonify({"error": "teacherType phai la 'GUEST' hoac 'RESIDENT'."}), 400
    org = (body.get("org") or "").strip()
    title = (body.get("title") or "").strip()
    email = (body.get("email") or "").strip()
    phone = (body.get("phone") or "").strip()

    tid = len(data["teachers"])
    while tid in data["teachers"]:
        tid += 1
    data["teachers"][tid] = {
        "id": tid, "name": name, "type": teacher_type, "org": org,
        "title": title, "email": email, "phone": phone,
    }

    slots = []
    if teacher_type == "GUEST":
        slots, err = _parse_availability_slots(data, body)
        if err:
            return jsonify({"error": err}), 400
    data.setdefault("manual_teacher_windows", {})[tid] = slots

    data["num_resident"] = sum(1 for t in data["teachers"].values() if t["type"] == "RESIDENT")
    data["num_guest"] = len(data["teachers"]) - data["num_resident"]

    _save_snapshot()
    return jsonify(_build_data_response(data, STATE.get("extra")))


@app.patch("/api/manual/teacher/<int:teacher_id>")
def api_manual_update_teacher(teacher_id):
    """Sua thong tin 1 GV va/hoac gio ranh - PARTIAL update (chi field co mat
    trong body moi bi ghi de), khac PATCH section (can gui du ca form): cac
    field GV doc lap voi nhau, khong can ngu canh cheo nhu section (thoi
    gian/GV/duration lien quan nhau). Sau khi doi teacherType/availability,
    dong bo lai cac lop dang cho GV nay qua _sync_teacher_sections()."""
    if STATE["data"] is None:
        return jsonify({"error": "Chưa có dữ liệu."}), 400
    data = STATE["data"]
    teacher = data["teachers"].get(teacher_id)
    if teacher is None:
        return jsonify({"error": f"Không tìm thấy giảng viên id={teacher_id}."}), 400
    body = request.get_json(force=True)

    if "name" in body:
        name = (body.get("name") or "").strip()
        if not name:
            return jsonify({"error": "Họ tên không được để trống."}), 400
        teacher["name"] = name
    if "org" in body:
        teacher["org"] = (body.get("org") or "").strip()
    if "title" in body:
        teacher["title"] = (body.get("title") or "").strip()
    if "email" in body:
        teacher["email"] = (body.get("email") or "").strip()
    if "phone" in body:
        teacher["phone"] = (body.get("phone") or "").strip()
    if "teacherType" in body:
        if body["teacherType"] not in ("GUEST", "RESIDENT"):
            return jsonify({"error": "teacherType phải là 'GUEST' hoặc 'RESIDENT'."}), 400
        teacher["type"] = body["teacherType"]
    if "availability" in body:
        slots, err = _parse_availability_slots(data, body)
        if err:
            return jsonify({"error": err}), 400
        data.setdefault("manual_teacher_windows", {})[teacher_id] = slots

    data["num_resident"] = sum(1 for t in data["teachers"].values() if t["type"] == "RESIDENT")
    data["num_guest"] = len(data["teachers"]) - data["num_resident"]
    _sync_teacher_sections(data, teacher_id)

    _save_snapshot()
    return jsonify(_build_data_response(data, STATE.get("extra")))


@app.post("/api/manual/course")
def api_manual_add_course():
    """Tao 1 hoc phan (dung chung cho nhieu lop - mirror cot B/C/D cua Excel,
    tuong tu 1 nhom dong merge-xuong). Body JSON: {code, name, credits}."""
    if STATE["data"] is None:
        return jsonify({"error": "Chua khoi tao du lieu nhap tay. Goi /api/manual/init truoc."}), 400
    data = STATE["data"]
    body = request.get_json(force=True)

    name = (body.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Thiếu Tên học phần."}), 400
    code = (body.get("code") or "").strip()
    try:
        credits = int(body["credits"]) if body.get("credits") not in (None, "") else None
    except (TypeError, ValueError):
        return jsonify({"error": "Số tín chỉ phải là số nguyên."}), 400

    courses = data.setdefault("courses", {})
    cid = len(courses)
    while cid in courses:
        cid += 1
    courses[cid] = {"id": cid, "code": code, "name": name, "credits": credits}

    _save_snapshot()
    return jsonify(_build_data_response(data, STATE.get("extra")))


@app.patch("/api/manual/course/<int:course_id>")
def api_manual_update_course(course_id):
    """Sua thong tin 1 hoc phan - anh huong tat ca lop tham chieu toi (course la
    entity rieng, khong can propagate tay xuong tung lop)."""
    if STATE["data"] is None:
        return jsonify({"error": "Chưa có dữ liệu."}), 400
    data = STATE["data"]
    courses = data.setdefault("courses", {})
    course = courses.get(course_id)
    if course is None:
        return jsonify({"error": f"Không tìm thấy học phần id={course_id}."}), 400
    body = request.get_json(force=True)

    if "name" in body:
        name = (body.get("name") or "").strip()
        if not name:
            return jsonify({"error": "Tên học phần không được để trống."}), 400
        course["name"] = name
    if "code" in body:
        course["code"] = (body.get("code") or "").strip()
    if "credits" in body:
        try:
            course["credits"] = int(body["credits"]) if body["credits"] not in (None, "") else None
        except (TypeError, ValueError):
            return jsonify({"error": "Số tín chỉ phải là số nguyên."}), 400

    for s in data["sections"].values():
        if s.get("course_id") == course_id:
            s["course_name"] = f"{course['name']} ({s['class_code']})" if s.get("class_code") else course["name"]

    _save_snapshot()
    return jsonify(_build_data_response(data, STATE.get("extra")))


@app.post("/api/manual/section")
def api_manual_add_section():
    """Them 1 lop (section) nhap tay, gan cho 1 GV + 1 hoc phan da co san. Body
    JSON: xem _validate_section_body() - gom teacherId, courseId, duration, cac
    field mirror 29 cot Excel (classCode/ltCredits/thCredits/cohort/program/
    expectedStudents/day+periodStart+periodEnd hoac autoSchedule/location/
    teachingMode/language/otherRequirements/notes/coordinatorOverride/
    prevTeacherName/prevTeacherOrg/teachingHoursLt/teachingHoursTh).
    - room_type suy tu thCredits>0 -> LAB, nguoc lai LT (giong load_real_fate_data).
    - Gio da CHOT (day+periodStart+periodEnd) -> submissions rut ve DUNG 1 slot
      (xem _apply_section_time). Tick autoSchedule/de trong ca 3 -> giu hanh vi cu:
      RESIDENT tu do hoan toan, GUEST theo khung gio ranh da khai bao qua
      /api/manual/teacher, neu chua co thi vao pending_section_ids nhu truoc."""
    if STATE["data"] is None:
        return jsonify({"error": "Chua khoi tao du lieu nhap tay. Goi /api/manual/init truoc."}), 400
    data = STATE["data"]
    body = request.get_json(force=True)

    fields, teacher, duration, time_info, err = _validate_section_body(data, body)
    if err:
        return jsonify({"error": err}), 400

    sid = len(data["sections"])
    while sid in data["sections"]:
        sid += 1
    data["sections"][sid] = {"id": sid, **fields}
    _apply_section_time(data, sid, teacher, duration, time_info)

    _save_snapshot()
    return jsonify(_build_data_response(data, STATE.get("extra")))


@app.patch("/api/manual/section/<int:section_id>")
def api_manual_update_section(section_id):
    """Sua 1 lop da nhap - body cung dinh dang day du nhu POST /api/manual/section
    (khong merge tung phan, xem ly do o _validate_section_body)."""
    if STATE["data"] is None:
        return jsonify({"error": "Chưa có dữ liệu."}), 400
    data = STATE["data"]
    if section_id not in data["sections"]:
        return jsonify({"error": f"Không tìm thấy lớp id={section_id}."}), 400
    body = request.get_json(force=True)

    fields, teacher, duration, time_info, err = _validate_section_body(data, body)
    if err:
        return jsonify({"error": err}), 400

    data["sections"][section_id].update(fields)
    _apply_section_time(data, section_id, teacher, duration, time_info)

    _save_snapshot()
    return jsonify(_build_data_response(data, STATE.get("extra")))


@app.delete("/api/manual/section/<int:section_id>")
def api_manual_delete_section(section_id):
    """Xoa 1 lop nhap nham - don luon submissions/pending_section_ids/overrides
    lien quan de khong con tham chieu treo den sectionId da mat. Don CA
    guestResult/residentResult dang cache (neu da giai truoc do) - khong lam
    vay thi lop da xoa van con hien "ma" tren luoi Thoi khoa bieu cho toi khi
    giai lai, vi 2 ket qua nay la snapshot rieng, khong tu dong doc lai
    data['sections'] moi lan render."""
    if STATE["data"] is None:
        return jsonify({"error": "Chưa có dữ liệu."}), 400
    data = STATE["data"]
    if section_id not in data["sections"]:
        return jsonify({"error": f"Không tìm thấy lớp id={section_id}."}), 400

    data["sections"].pop(section_id)
    data["submissions"].pop(section_id, None)
    if section_id in data["pending_section_ids"]:
        data["pending_section_ids"].remove(section_id)
    STATE["overrides"].pop(section_id, None)

    for result in (STATE["guestResult"], STATE["residentResult"]):
        if not result:
            continue
        result["lessons"] = [l for l in result["lessons"] if l["id"] != section_id]
        if "unplaced" in result:
            result["unplaced"] = [u for u in result["unplaced"] if u["id"] != section_id]

    _save_snapshot()
    return jsonify(_build_data_response(data, STATE.get("extra")))


@app.post("/api/submit-availability")
def api_submit_availability():
    """Mo phong dung 'Dieu phoi vien nhap Giao vien + Gio co the day'."""
    if STATE["data"] is None:
        return jsonify({"error": "Chua sinh du lieu. Goi /api/generate truoc."}), 400
    data = STATE["data"]
    body = request.get_json(force=True)
    section_id = int(body["sectionId"])
    window_slots = [int(w) for w in body["windowSlots"]]
    if not window_slots:
        return jsonify({"error": "Phai nhap it nhat 1 khung gio."}), 400

    # Cac lop trong pending_section_ids luon la THINH GIANG (xem generate_data) -
    # ap dung dung gioi han "thinh giang toi Thu 7" (sc.MAX_DAY_INDEX).
    slots_per_day = data["params"]["slotsPerDay"]
    max_day = sc.max_day_index("GUEST")
    if any((w // slots_per_day) > max_day for w in window_slots):
        return jsonify({"error": "Có khung giờ ngoài phạm vi (thỉnh giảng chỉ dạy tới Thứ 7)."}), 400

    result = sc.submit_availability(data, section_id, window_slots)

    remaining_pending = len(STATE["data"]["pending_section_ids"])
    return jsonify({**result, "remainingPending": remaining_pending})


@app.post("/api/solve-guest")
def api_solve_guest():
    if STATE["data"] is None:
        return jsonify({"error": "Chua sinh du lieu. Goi /api/generate truoc."}), 400
    data = STATE["data"]
    result = _solve_guest_with_overrides(data)
    _attach_override_metadata(data, result, "GUEST")
    STATE["guestResult"] = result
    STATE["residentResult"] = None
    return jsonify(result)


@app.post("/api/solve-resident")
def api_solve_resident():
    if STATE["guestResult"] is None:
        return jsonify({"error": "Can chay Giai doan 1 (thinh giang) truoc."}), 400
    data = STATE["data"]
    forbidden = _forbidden_from_resident_overrides(data)
    result = sc.solve_resident_phase(data, STATE["guestResult"]["lessons"], forbidden)
    _attach_override_metadata(data, result, "RESIDENT")
    STATE["residentResult"] = result
    return jsonify(result)


@app.post("/api/move-lesson")
def api_move_lesson():
    """Giao vu keo 1 buoi hoc sang o gio khac ('sua tay'). KHONG bi chan boi
    trung GV/het phong (dong 2 - cho phep vi pham rang buoc), nhung PHAI ghi ly
    do neu o do dang co van de. Buoi duoc GHIM (dong 1): luu vao STATE['overrides']
    de lan 'Giai lai' ke tiep CP-SAT chi con dung 1 lua chon la giu buoi nay o
    day (xem _solve_guest_with_overrides/_forbidden_from_resident_overrides).
    Ngay sau khi luu, PATCH ngay ket qua dang cache (STATE['guestResult'] hoac
    ['residentResult']) de luoi hien vi tri moi TUC THI, khong phai cho giai lai
    moi thay doi tren man hinh.
    Chi Giao vu/DPV duoc goi (dong 3) - canEdit da chan o frontend; backend demo
    dung 1 STATE chung cho ca phien, khong co dang nhap nen khong check lai role."""
    if STATE["data"] is None:
        return jsonify({"error": "Chua co du lieu."}), 400
    data = STATE["data"]
    body = request.get_json(force=True)
    try:
        section_id = int(body["sectionId"])
        slot = int(body["slot"])
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "Thieu hoac sai sectionId/slot."}), 400
    reason = (body.get("reason") or "").strip() or None

    s = data["sections"].get(section_id)
    if not s:
        return jsonify({"error": f"Khong tim thay buoi #{section_id}."}), 400

    p = data["params"]
    day, period = divmod(slot, p["slotsPerDay"])
    if not (0 <= day < p["numDays"]) or period + s["duration"] > p["slotsPerDay"]:
        return jsonify({"error": "Khung gio khong hop le (vuot ngay hoac vuot tiet)."}), 400
    if day > sc.max_day_index(s["teacher_type"]):
        max_label = _DAY_LABELS_VN[sc.max_day_index(s["teacher_type"])]
        loai = "Thỉnh giảng" if s["teacher_type"] == "GUEST" else "Cơ hữu"
        return jsonify({"error": f"{loai} chỉ được dạy tới {max_label}."}), 400

    conflict = _detect_move_conflict(data, section_id, slot)
    if conflict and not reason:
        return jsonify({
            "error": "Ô này đang trùng giờ giảng viên hoặc hết phòng — cần ghi lý do để xác nhận.",
            "conflict": conflict,
        }), 409

    STATE["overrides"][section_id] = {"slot": slot, "reason": reason, "problem": conflict}

    kind = s["teacher_type"]
    result = STATE["guestResult"] if kind == "GUEST" else STATE["residentResult"]
    if result is not None:
        by_id = {l["id"]: l for l in result["lessons"]}
        if section_id in by_id:
            l = by_id[section_id]
            l["day"], l["period"], l["slot"] = day, period, slot
        else:
            # Truoc do khong xep duoc (nam trong 'unplaced') - giao vu tu tay dat
            # vao 1 cho, chuyen sang lessons de hien tren luoi ngay.
            unplaced = result.get("unplaced") or []
            u = next((x for x in unplaced if x["id"] == section_id), None)
            if u is not None:
                result["unplaced"] = [x for x in unplaced if x["id"] != section_id]
                result["lessons"].append({
                    "id": section_id, "teacherId": s["teacher_id"], "teacherName": u["teacherName"],
                    "courseName": u.get("courseName"), "program": s["program"],
                    "programLabel": u.get("programLabel"), "coordinator": u.get("coordinator"),
                    "roomType": s["room_type"], "day": day, "period": period, "slot": slot,
                    "duration": s["duration"], "teacherType": kind,
                })
                result["placedCount"] = result.get("placedCount", 0) + 1
        _attach_override_metadata(data, result, kind)

    return jsonify({
        "sectionId": section_id, "slot": slot, "day": day, "period": period,
        "reason": reason, "problem": conflict,
        "guestResult": STATE["guestResult"], "residentResult": STATE["residentResult"],
    })


@app.post("/api/clear-override")
def api_clear_override():
    """Bo ghim 1 buoi. Chi anh huong lan 'Giai lai' KE TIEP (CP-SAT duoc tu do
    chon lai cho buoi do) - khong tu lui vi tri dang hien tren luoi, giong cach
    ban ghim cung chi thuc su co hieu luc tu lan giai ke tiep. Van tra ve
    guestResult/residentResult da cap nhat (giong /api/move-lesson) de frontend
    go ngay 'nhan ghim' tren the, du vi tri chua doi."""
    if STATE["data"] is None:
        return jsonify({"error": "Chua co du lieu."}), 400
    data = STATE["data"]
    body = request.get_json(force=True)
    section_id = int(body["sectionId"])
    STATE["overrides"].pop(section_id, None)

    _attach_override_metadata(data, STATE["guestResult"], "GUEST")
    _attach_override_metadata(data, STATE["residentResult"], "RESIDENT")

    return jsonify({
        "sectionId": section_id, "cleared": True,
        "guestResult": STATE["guestResult"], "residentResult": STATE["residentResult"],
    })


@app.get("/api/manual/export")
def api_manual_export():
    """Xuat bang 'Du lieu hoc phan' hien co ra .xlsx dung khuon LAYOUTS['FATE']
    (fate_export.py) - de dung lam van ban chinh thuc va nap lai duoc o ky sau."""
    if STATE["data"] is None:
        return jsonify({"error": "Chưa có dữ liệu."}), 400
    label = (request.args.get("label") or "").strip() or "TKB"
    classes = _build_classes_list(STATE["data"])
    buf = fate_export.build_workbook(classes, label)
    filename = f"FATE.TKB.{label}.xlsx"
    return send_file(
        buf, as_attachment=True, download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.post("/api/manual/save-schedule")
def api_save_schedule():
    """'Lưu thời khoá biểu': đóng băng kết quả đang xem trên lưới (ghim tay >
    Giai đoạn 2 > Giai đoạn 1, đúng thứ tự ưu tiên _detect_move_conflict/
    _attach_override_metadata dùng) THÀNH dữ liệu chính thức của lớp học phần -
    ghi lại qua _apply_section_time() (hàm nhập tay/import đang dùng, không tự
    viết lại), để cột Thứ/Tiết BĐ/Tiết KT ở màn 'Dữ liệu học phần' khớp với
    lưới. Không xoá guestResult/residentResult/overrides - chỉ sao chép giá trị
    sang sections, màn Thời khoá biểu hiển thị như cũ sau khi lưu."""
    if STATE["data"] is None:
        return jsonify({"error": "Chưa có dữ liệu."}), 400
    if STATE["guestResult"] is None and STATE["residentResult"] is None:
        return jsonify({"error": "Chưa có kết quả xếp để lưu."}), 400

    data = STATE["data"]
    slots_per_day = data["params"]["slotsPerDay"]

    lessons_by_id = {}
    for res in (STATE["guestResult"], STATE["residentResult"]):
        if res:
            for l in res["lessons"]:
                lessons_by_id[l["id"]] = l

    saved_count = 0
    for sid, s in data["sections"].items():
        ov = STATE["overrides"].get(sid)
        slot = ov["slot"] if ov else None
        if slot is None:
            lesson = lessons_by_id.get(sid)
            if lesson is not None:
                slot = lesson["slot"]
        if slot is None:
            continue  # buoi chua tung duoc xep/ghim - giu nguyen, khong dung vao

        day, period0 = divmod(slot, slots_per_day)
        period_start = period0 + 1
        period_end = period_start + s["duration"] - 1
        teacher = data["teachers"][s["teacher_id"]]
        _apply_section_time(data, sid, teacher, s["duration"], {
            "day": day, "period_start": period_start, "period_end": period_end,
        })
        saved_count += 1

    # Trang thai lich cho TOAN BO lop (khong chi cac lop vua luu) - quet trung
    # gio GV tren vi tri THUC vua ghi, dung lai cong thuc _overlaps() o tren.
    by_teacher = {}
    for s in data["sections"].values():
        if s.get("day") is not None:
            by_teacher.setdefault(s["teacher_id"], []).append(s)

    problem_ids = set()
    for group in by_teacher.values():
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                a, b = group[i], group[j]
                slot_a = a["day"] * slots_per_day + (a["period_start"] - 1)
                slot_b = b["day"] * slots_per_day + (b["period_start"] - 1)
                if _overlaps(slot_a, a["duration"], slot_b, b["duration"]):
                    problem_ids.add(a["id"])
                    problem_ids.add(b["id"])

    problem_count = missing_count = 0
    for s in data["sections"].values():
        if s["id"] in problem_ids:
            s["schedule_status"] = "problem"
            problem_count += 1
        elif s.get("day") is None:
            s["schedule_status"] = "missing"
            missing_count += 1
        else:
            s["schedule_status"] = "scheduled"

    _save_snapshot()

    resp = _build_data_response(data, STATE["extra"])
    resp["savedCount"] = saved_count
    resp["problemCount"] = problem_count
    resp["missingCount"] = missing_count
    return jsonify(resp)


@app.get("/api/results")
def api_results():
    """Tra lai ket qua giai dang cache trong STATE - dung khi SPA tai lai trang.

    Truoc khi co endpoint nay, guestResult/residentResult chi song trong state
    React: bam F5 la luoi trong va giao vu phai bam 'Giai' lai (2-30 giay) DU
    backend van con nguyen ket qua. /api/state co bao hasGuestResult nhung khong
    tra ve chinh ket qua, nen frontend biet 'co' ma khong lay duoc.

    Gan metadata ghim truoc khi tra (giong /api/clear-override) de the buoi hien
    dung 'nhan ghim' ngay sau khi tai lai, khong doi den luot sua tay ke tiep."""
    if STATE["data"] is None:
        return jsonify({"guestResult": None, "residentResult": None})

    _attach_override_metadata(STATE["data"], STATE["guestResult"], "GUEST")
    _attach_override_metadata(STATE["data"], STATE["residentResult"], "RESIDENT")

    return jsonify({
        "guestResult": STATE["guestResult"],
        "residentResult": STATE["residentResult"],
    })


@app.get("/api/state")
def api_state():
    return jsonify({
        "hasData": STATE["data"] is not None,
        "hasGuestResult": STATE["guestResult"] is not None,
        "hasResidentResult": STATE["residentResult"] is not None,
        "overridesCount": len(STATE["overrides"]),
    })


_load_snapshot()  # phuc hoi du lieu nhap tay lan chay truoc (neu co) ngay khi module nap


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5055, debug=False)
