# -*- coding: utf-8 -*-
"""MO HINH CP-SAT (hai giai doan) + cac ham doc thuoc tinh cua mot lop.

Tach rieng khoi Flask de de test/tai su dung: khong import gi tu webapp ca, chi
nhan vao/tra ve bo du lieu `data` (xem domain/sections.py: empty_manual_data).

Hai giai doan:
    solve_guest_phase()     xep lop THINH GIANG trong khung gio ho da bao
    solve_resident_phase()  ghep lop CO HUU vao cho con lai, giu nguyen GD1

check_cross_program_conflicts() la buoc "giao vu khoa check trung" chay TRUOC khi
giai: xet rieng tung giang vien xem cac khung gio hai dieu phoi vien bao cho ho
co the cung ton tai duoc khong.
"""

import itertools
import time
from ortools.sat.python import cp_model

DAY_NAMES = ["Thu 2", "Thu 3", "Thu 4", "Thu 5", "Thu 6", "Thu 7", "Chu nhat"]


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


# --- HOC CHUNG ------------------------------------------------------------
# Mot nhom hoc chung = MOT buoi day vat ly, ghi thanh NHIEU lop vi co nhieu ma
# mon (vd ECE3083 "Vat lieu tien tien trong xay dung" + BCE3023 "Vat lieu tien
# tien trong ky thuat": cung thay, cung phong LAB, cung Thu 4 tiet 2-4, sinh vien
# hai chuong trinh ngoi chung).
#
# Doc THANG tu data["hoc_chung"] chu khong nhan qua tham so: `data` la toan bo
# hop dong giua module nay va tang tren, va giu duoc nguyen tac "scheduler_core
# khong import gi tu webapp".
#
# Chinh sach (tao/xoa/validate nhom) nam o domain/hoc_chung.py - o day chi co
# hai phep TRA CUU ma solver va cac ham kiem trung can.

def cac_nhom_hoc_chung(data):
    """Danh sach nhom, moi nhom la list section_id (chi giu lop CON TON TAI)."""
    ra = []
    for nhom in data.get("hoc_chung") or []:
        ds = [sid for sid in nhom.get("sectionIds") or [] if sid in data["sections"]]
        if len(ds) > 1:
            ra.append(sorted(ds))
    return ra


def dai_dien_hoc_chung(data):
    """{section_id: section_id DAI DIEN cua nhom}. Lop khong thuoc nhom nao thi
    khong co trong dict.

    Dai dien = id nho nhat, on dinh giua cac lan giai. Solver rang buoc moi thanh
    vien BANG dai dien (cung start, cung placed) va chi dua interval cua DAI DIEN
    vao NoOverlap/Cumulative - nho vay ca nhom la mot buoi, mot phong, va khong
    tu bao trung gio voi chinh minh."""
    ra = {}
    for ds in cac_nhom_hoc_chung(data):
        for sid in ds:
            ra[sid] = ds[0]
    return ra


def cung_nhom_hoc_chung(data, sid_a, sid_b):
    """Hai lop nay la CUNG MOT buoi (hoc chung) chu khong phai trung gio?

    Moi cho kiem trung giang vien deu phai goi ham nay - xem danh sach o
    domain/hoc_chung.py."""
    if sid_a == sid_b:
        return False
    dd = dai_dien_hoc_chung(data)
    return sid_a in dd and dd[sid_a] == dd.get(sid_b)




def check_cross_program_conflicts(data):
    """'Check trung' truoc khi giai: voi moi GV thinh giang day >= 2 buoi (thuong la
    lien 2 chuong trinh, moi chuong trinh 1 dieu phoi vien bao gio rieng), thu TAT
    CA to hop lua chon window cua rieng GV do (khong xet den GV/phong khac) de xem
    co TON TAI it nhat 1 cach xep khong trung gio cho chinh GV nay hay khong.
    Day la buoc "giao vu khoa check trung" xay ra o cap 1 GV, TRUOC khi dua vao
    CP-SAT giai toan bo (CP-SAT giai ca xung dot voi GV/phong khac nua)."""
    p = data["params"]

    # HOC CHUNG: ca nhom la MOT buoi -> chi xet DAI DIEN. Giu ca nhom thi ham nay
    # bao "khong ton tai cach xep nao khong trung" cho dung cai cap ma giao vu da
    # noi ro la hoc chung.
    dai_dien = dai_dien_hoc_chung(data)

    guest_sections_by_teacher = {}
    for s in data["sections"].values():
        if s["teacher_type"] != "GUEST":
            continue
        dd = dai_dien.get(s["id"])
        if dd is not None and dd != s["id"]:
            continue
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


def guest_sections_can_thu_gio(data):
    """Cac lop THINH GIANG con can xu ly truoc khi giai Giai doan 1 (xem
    api/solve.py: api_solve_guest) - dung dung 3 dieu kien nay, KHONG tinh lai
    tu dau, de giong het cach frontend (adapters/submissionQueue.js:
    analyzeSubmissions) chia "Chưa phân công giảng viên" / "Chưa khai giờ",
    tranh hai noi bao lech nhau con bao nhieu lop con thieu.

    Mot lop con can xu ly khi:
      - GV la CHO TRONG (teacher placeholder, chua ai duoc phan cong that) - giai
        luc nay se gan lich cho mot "con nguoi" khong ton tai.
      - hoac availability_assumed=True: co GV that nhung chua ai bao gio THAT,
        he thong dang tam coi la "ranh ca tuan" (xem apply_section_time) - giai
        luc nay se ra lich khong dung rang buoc gio thuc cua GV.
      - hoac dang nam trong pending_section_ids: da khai nhung khong con khung
        nao hop le (xung dot gio giua cac GV dong giang), submissions rong."""
    pending = set(data["pending_section_ids"])
    return [
        s for s in data["sections"].values()
        if s.get("teacher_type") == "GUEST"
        and (
            data["teachers"].get(s["teacher_id"], {}).get("placeholder")
            or s.get("availability_assumed")
            or s["id"] in pending
        )
    ]


def solve_guest_phase(data, time_limit_s=30):
    p = data["params"]
    guest_sections = [s for s in data["sections"].values() if s["teacher_type"] == "GUEST"]

    model = cp_model.CpModel()
    starts, placed = {}, {}
    intervals_by_teacher = {}
    intervals_by_roomtype = {"LT": [], "LAB": []}
    day_load_terms = {d: [] for d in range(p["numDays"])}  # cho muc tieu dan ngay (phu)

    # HOC CHUNG: ca nhom la MOT buoi -> chi DAI DIEN gop mat trong NoOverlap
    # (khong tu bao trung voi chinh minh) va Cumulative (chi ton 1 phong), con
    # cac thanh vien bi rang buoc BANG dai dien o cuoi vong lap.
    dai_dien = dai_dien_hoc_chung(data)
    gv_cua_nhom = {}   # sid dai dien -> hop teacher_ids cua CA NHOM
    for s in guest_sections:
        dd = dai_dien.get(s["id"])
        if dd is not None:
            gv_cua_nhom.setdefault(dd, set()).update(s.get("teacher_ids") or [s["teacher_id"]])

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
        dd = dai_dien.get(sid)
        if dd is not None and dd != sid:
            continue  # thanh vien: rang buoc theo dai dien, khong chiem GV/phong rieng
        # Doi voi lesson co NHIEU GV dong giang day (teacher_ids), cung 1 interval
        # duoc dua vao NoOverlap cua TAT CA nguoi do - dam bao khong ai trong nhom
        # bi trung lich o cho khac, ma khong nhan doi nhu cau phong.
        # Lop la DAI DIEN mot nhom hoc chung thi lay hop GV cua ca nhom: buoi do
        # co mat CA HO, nen ho khong the day cho khac cung gio.
        for tid in (gv_cua_nhom.get(sid) or s.get("teacher_ids") or [s["teacher_id"]]):
            intervals_by_teacher.setdefault(tid, []).append(interval)
        intervals_by_roomtype[s["room_type"]].append(interval)

    # Thanh vien nhom hoc chung: CUNG gio va CUNG so phan voi dai dien.
    for ds in cac_nhom_hoc_chung(data):
        rep = ds[0]
        if rep not in starts:
            continue  # nhom nay khong thuoc pha nay
        for sid in ds[1:]:
            if sid in starts:
                model.Add(starts[sid] == starts[rep])
                model.Add(placed[sid] == placed[rep])

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
    # HOC CHUNG o Giai doan 1: chi dong bang DAI DIEN. Neu dong bang ca nhom thi
    # hai interval CO DINH trung khit nhau (cung slot, cung GV) cung vao
    # AddNoOverlap cua nguoi do -> mo hinh INFEASIBLE ngay, Giai doan 2 mat trang
    # ket qua. Phong cung vay: mot buoi chi ton mot phong.
    dai_dien = dai_dien_hoc_chung(data)
    for g in frozen_guest_lessons:
        dd = dai_dien.get(g["id"])
        if dd is not None and dd != g["id"]:
            continue
        iv = model.NewFixedSizeIntervalVar(
            g["slot"], g.get("duration", p["duration"]), f"frozen_{g['id']}")
        intervals_by_roomtype[g["roomType"]].append(iv)
        # Dai dien mang theo GV cua CA NHOM hoc chung (buoi do co mat ca ho).
        gv = set(g.get("teacherIds") or [g["teacherId"]])
        if dd is not None:
            for sid in next((x for x in cac_nhom_hoc_chung(data) if x[0] == dd), []):
                s2 = data["sections"].get(sid) or {}
                gv.update(s2.get("teacher_ids") or ([s2["teacher_id"]] if s2 else []))
        for tid in gv:
            intervals_by_teacher.setdefault(tid, []).append(iv)

    on_day_by_section = {}  # sid -> [bool theo ngay] - dung cho muc tieu dan ngay (phu)
    pending_ids = set(data.get("pending_section_ids") or [])

    # Hop GV cua tung nhom hoc chung o pha nay - dai dien mang theo ca nhom (xem
    # solve_guest_phase, cung mot ly le).
    gv_cua_nhom = {}
    for s in resident_sections:
        dd = dai_dien.get(s["id"])
        if dd is not None:
            gv_cua_nhom.setdefault(dd, set()).update(s.get("teacher_ids") or [s["teacher_id"]])

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

        # Khung gio GV DA KHAI cho lop nay (domain/time_rules.py:
        # apply_section_time da giao khung cua ca nhom va loc theo do dai buoi).
        # Rong = chua ai khai -> tu do.
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
        dd = dai_dien.get(sid)
        if dd is not None and dd != sid:
            continue  # thanh vien hoc chung: xem khoi rang buoc o cuoi
        for tid in (gv_cua_nhom.get(sid) or s.get("teacher_ids") or [s["teacher_id"]]):
            intervals_by_teacher.setdefault(tid, []).append(interval)
        intervals_by_roomtype[s["room_type"]].append(interval)

    # Thanh vien nhom hoc chung: CUNG gio va CUNG so phan voi dai dien.
    for ds in cac_nhom_hoc_chung(data):
        rep = ds[0]
        if rep not in starts:
            continue  # nhom nay khong thuoc pha nay
        for sid in ds[1:]:
            if sid in starts:
                model.Add(starts[sid] == starts[rep])
                model.Add(placed[sid] == placed[rep])

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
