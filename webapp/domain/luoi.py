# -*- coding: utf-8 -*-
"""DUNG va DONG BO LUOI THOI KHOA BIEU dang hien.

guest/residentResult la SNAPSHOT rieng, khong tu doc lai data['sections'] moi lan
render - nen sau moi thao tac sua du lieu phai dong bo lai, khong thi bang "Du
lieu hoc phan" va luoi noi hai chuyen khac nhau ve cung mot lop.

Tach khoi domain/pinning.py: ben do lo RANG BUOC dua vao solver (ghim/bo ghim),
o day lo cai NGUOI DUNG NHIN THAY. Hai viec khac nhau du deu doc STATE['overrides']
- truoc day o chung mot file 487 dong.
"""

import datetime

import scheduler_core as sc
from domain.hoc_chung import nhom_cua, thanh_vien
from domain.pinning import ghim_gio_da_chot
from state import STATE


def buoi_tren_luoi(data, s, slot):
    """Mot BUOI HOC de dat len luoi Thoi khoa bieu, dung khuon ma
    solve_guest_phase()/solve_resident_phase() tra ve - de frontend
    (adapters/lessonAdapter.js) doc duoc y nhu buoi do solver xep.

    Mot cho duy nhat dung khuon nay (lich ban dau tu file, va dong bo lai sau moi
    lan sua form) - truoc day lich ban dau tu ghep dict rieng nen thieu
    programIds/programParts/facultyName, khien bo loc theo CTDT/Khoa tren man
    Thoi khoa bieu khong loc duoc gi cho toi khi bam Giai.
    """
    slots_per_day = data["params"]["slotsPerDay"]
    day, period = divmod(slot, slots_per_day)
    return {
        "id": s["id"], "teacherId": s["teacher_id"],
        "teacherName": sc.teacher_display(data, s["teacher_id"]),
        "teacherIds": list(s.get("teacher_ids") or [s["teacher_id"]]),
        "courseName": s.get("course_name"), "program": s["program"],
        "programLabel": sc.section_program_label(data, s),
        "programIds": sc.section_program_ids(s),
        "programParts": sc.section_program_names(data, s),
        "facultyName": sc.section_faculty_name(data, s),
        "coordinator": ", ".join(sc.section_coordinators(data, s)),
        "classCode": s.get("class_code"),
        "roomType": s["room_type"], "day": day, "period": period,
        "slot": slot, "duration": s["duration"],
        "teacherType": s["teacher_type"], "status": "DRAFT",
        "usedWindowLabel": sc.slot_label(slot, slots_per_day),
        # HOC CHUNG: cac buoi cung nhom nam DE LEN NHAU tren luoi (dung y - mot
        # buoi that). Frontend gop chung thanh mot the theo hai truong nay.
        "hocChungId": (nhom_cua(data, s["id"]) or {}).get("id"),
        "hocChungWith": [x for x in thanh_vien(data, s["id"]) if x != s["id"]],
    }


def lich_ban_dau(data):
    """Dung LICH BAN DAU tu cac lop DA CHOT GIO trong file, khong chay solver.

    Vi sao can: nap file xong, man "Thoi khoa bieu" bao "Chua co lich nao - bam
    Giai o buoc 2" du file da chot gio cho phan lon cac lop (HK1-2: 246/343). Giao
    vu phai bam Giai moi thay duoc chinh cai minh vua nap - trong khi nhung gio do
    la DA CHOT, khong phai do thuat toan xep.

    Tra ve (ket_qua_GD1, ket_qua_GD2) dung khuon solver tra ve, kem co
    initial=True de UI biet day KHONG phai ket qua da giai (thanh tien trinh van
    hien "chua chay", nut buoc 3 van cho chay buoc 2 truoc).
    """
    theo_pha = {"GUEST": [], "RESIDENT": []}
    for sid, s in data["sections"].items():
        if s.get("time_assumed") or s.get("original_slot") is None:
            continue
        theo_pha.setdefault(s["teacher_type"], []).append(
            buoi_tren_luoi(data, s, s["original_slot"]))

    return (_goi_ket_qua(data, "GUEST", theo_pha["GUEST"]),
            _goi_ket_qua(data, "RESIDENT", theo_pha["RESIDENT"]))


def _goi_ket_qua(data, loai, lessons):
    """Khuon ket qua "chua giai" - chi la cac gio DA CO SAN dat len luoi."""
    return {
        "status": "TU_FILE", "elapsedSeconds": 0.0,
        "total": sum(1 for s in data["sections"].values() if s["teacher_type"] == loai),
        "placedCount": len(lessons), "lessons": sorted(lessons, key=lambda l: l["id"]),
        "unplaced": [], "initial": True,
    }


def dong_bo_ket_qua(data, bo_vi_tri_cu=(), chi_pha=None):
    """Dong bo LUOI THOI KHOA BIEU dang cache (STATE guest/residentResult) voi
    data['sections'] hien tai. Goi sau MOI thao tac sua du lieu hoc phan.

    Vi sao can: guest/residentResult la SNAPSHOT rieng, khong tu doc lai
    data['sections'] moi lan render. Sua lop/GV/hoc phan qua form ma khong dong bo
    thi man Thoi khoa bieu con hien ban cu: lop moi them khong xuat hien, lop doi
    gio van o o cu, doi ten mon/GV thi the buoi ghi ten cu, va doi loai GV thi
    buoi ket lai o giai doan cu.

    `chi_pha`: "GUEST"/"RESIDENT" - chi dung lai mot pha, de nguyen pha kia. Dung
    ngay sau khi giai xong mot giai doan: khong duoc cham vao ket qua solver vua
    tra ve (se lam mat cac truong rieng cua no).

    `bo_vi_tri_cu`: cac section_id vua bi form GHI LAI GIO - voi chung, KHONG
    duoc dung vi tri cu tren luoi lam can cu nua. Can co tham so nay vi mot lop
    "de he thong tu xep" khong co gio rieng, nghiem cua solver la thu duy nhat
    noi no dang o dau -> phai giu. Nhung mot lop VUA BI XOA GIO thi cung o dung
    trang thai do (time_assumed=True, khong co original_slot), khong the phan biet
    bang du lieu; nen cho ben goi noi ro no vua cham vao nhung lop nao.
    """
    bo_vi_tri_cu = set(bo_vi_tri_cu)

    # Vi tri solver da chon cho tung buoi (doc TRUOC khi dung lai luoi).
    slot_solver = {}
    for res in (STATE["guestResult"], STATE["residentResult"]):
        for l in (res or {}).get("lessons") or []:
            if l["id"] not in bo_vi_tri_cu:
                slot_solver[l["id"]] = l["slot"]

    theo_pha = {"GUEST": [], "RESIDENT": []}
    for sid, s in data["sections"].items():
        slot = _slot_len_luoi(data, sid, slot_solver)
        if slot is None:
            continue
        theo_pha.setdefault(s["teacher_type"], []).append(buoi_tren_luoi(data, s, slot))

    for loai, khoa in (("GUEST", "guestResult"), ("RESIDENT", "residentResult")):
        if chi_pha is not None and loai != chi_pha:
            continue
        lessons = sorted(theo_pha[loai], key=lambda l: l["id"])
        cu = STATE[khoa]
        if cu is None:
            # Chua giai lan nao va cung chua nap file: chi dung ket qua "chua
            # giai" khi that su co gio de hien, khong tao khung rong.
            if lessons:
                STATE[khoa] = _goi_ket_qua(data, loai, lessons)
                attach_override_metadata(data, STATE[khoa], loai)
            continue
        cu["lessons"] = lessons
        cu["placedCount"] = len(lessons)
        cu["total"] = sum(1 for s in data["sections"].values() if s["teacher_type"] == loai)
        # Buoi da co cho tren luoi thi khong con "khong xep duoc"; buoi da bi xoa
        # thi khong con gi de noi. Cac muc con lai giu NGUYEN VAN ban solver tra
        # ve (kem `blockers` giai thich vi sao) - khong tu dung muc unplaced moi:
        # lop giao vu vua chuyen sang "de he thong tu xep" chua duoc giai, no
        # KHONG phai "solver khong xep duoc".
        tren_luoi = {l["id"] for l in lessons}
        cu["unplaced"] = [u for u in (cu.get("unplaced") or [])
                          if u["id"] in data["sections"] and u["id"] not in tren_luoi]
        attach_override_metadata(data, cu, loai)


def _slot_len_luoi(data, sid, slot_solver):
    """Buoi nay phai hien o o gio nao tren luoi? None = chua o dau ca.

    Thu tu uu tien, tu manh den yeu:
      1. GHIM  - keo-tha sua tay, hoac gio vua go o form (ghim_theo_gio_form)
      2. GIO CO DINH cua lop - con nguoi da chot, solver buoc phai theo
      3. NGHIEM SOLVER - lop "de he thong tu xep", chi solver biet no o dau
    Dung thu tu ma _detect_move_conflict/chot.slot_dang_hien dang dung, chi khac
    o cho (2) len truoc (3): gio con nguoi vua go phai thang mot nghiem cu.
    """
    ov = STATE["overrides"].get(sid)
    if ov and ov.get("slot") is not None:
        return ov["slot"]
    s = data["sections"][sid]
    if not s.get("time_assumed") and s.get("original_slot") is not None:
        return s["original_slot"]
    return slot_solver.get(sid)


def chot_hoc_phan_du_gio_tu_file(data, nguon=None):
    """Danh dau DA CHOT LICH cho moi hoc phan ma MOI lop cua no deu co gio trong
    file. Tra ve so hoc phan vua chot.

    Theo dung quyet dinh A2: *"cac lop da duoc import tu file la cac lop da chot
    gio, tuc giao vien day da chot qua loi voi dieu phoi vien"*. Gio do von da
    duoc ghim (ghim_gio_da_chot) - viec con thieu chi la NOI RA tren giao dien,
    de o "Da chot n/153 mon" khong bao 0 trong khi 246/343 lop da co gio chot.

    Chi chot hoc phan DU gio: mot mon con lop chua co gio thi ban chinh thuc cua
    no chua hoan chinh, chot vao la sai nghia. `truoc` de rong tuong ung "moi lop
    von da co gio nay" - bo chot se tra dung ve gio trong file, khong ve "de he
    thong tu xep".
    """
    theo_hp = {}
    for sid, sec in data["sections"].items():
        theo_hp.setdefault(sec.get("course_id"), []).append(sec)
    now = datetime.datetime.now().isoformat(timespec="seconds")
    dem = 0
    for cid, ds in theo_hp.items():
        hp = data.get("courses", {}).get(cid)
        if hp is None or hp.get("chot"):
            continue
        if not ds or any(x.get("time_assumed") or x.get("original_slot") is None for x in ds):
            continue
        hp["chot"] = {
            "at": now, "by": "Nhập từ Excel",
            "note": f"Giờ đã chốt sẵn trong {nguon}" if nguon else "Giờ đã chốt sẵn trong file",
            "soLop": len(ds), "tuFile": True,
            "truoc": {str(x["id"]): {"day": x.get("day"), "periodStart": x.get("period_start"),
                                     "periodEnd": x.get("period_end"), "timeAssumed": False}
                      for x in ds},
        }
        dem += 1
    return dem


def dat_lich_ban_dau(data, nguon=None):
    """Ghim gio da chot + danh dau hoc phan du gio la DA CHOT + dat lich ban dau
    vao STATE (dung sau khi nap file)."""
    ghim_gio_da_chot(data)
    chot_hoc_phan_du_gio_tu_file(data, nguon)
    g, r = lich_ban_dau(data)
    attach_override_metadata(data, g, "GUEST")
    attach_override_metadata(data, r, "RESIDENT")
    STATE["guestResult"], STATE["residentResult"] = g, r


def attach_override_metadata(data, result, teacher_type):
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


def attach_ca_hai(data):
    """Gan metadata ghim cho CA HAI ket qua dang cache - go tat mot buoc lap lai
    o 5 endpoint (chot/bo chot/bo ghim/doc lai ket qua)."""
    attach_override_metadata(data, STATE["guestResult"], "GUEST")
    attach_override_metadata(data, STATE["residentResult"], "RESIDENT")
