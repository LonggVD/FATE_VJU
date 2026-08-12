# -*- coding: utf-8 -*-
"""GHIM / BO GHIM va LICH BAN DAU doc tu file.

"Ghim" la co che manh nhat trong ca hai pha giai: thay vi sua scheduler_core.py,
no thu hep MIEN cua buoi bi ghim ve dung mot slot truoc khi goi solver
(Giai doan 1 qua submissions, Giai doan 2 qua tham so ghim_tay). Nho vay giao vu
keo-tha xong thi giai lai bao nhieu lan buoi do cung dung yen.
"""

import contextlib
import datetime

import scheduler_core as sc
from domain.time_rules import apply_section_time, overlaps
from state import STATE


def detect_move_conflict(data, section_id, slot):
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

    # Trung GV xet theo CA NHOM dong giang (giao cua hai tap teacher_ids), khong
    # chi GV chinh: solver rang buoc ca nhom nen neu chi so GV chinh o day thi
    # keo-tha se bao "khong sao" cho dung cai cho ma thuat toan coi la trung.
    my_tids = set(s.get("teacher_ids") or [s["teacher_id"]])
    teacher_blockers = [
        l for l in placed
        if my_tids.intersection(l.get("teacherIds") or [l["teacherId"]])
        and overlaps(slot, duration, l["slot"], l["duration"])
    ]
    same_room = [
        l for l in placed
        if l["roomType"] == s["room_type"] and overlaps(slot, duration, l["slot"], l["duration"])
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
    p = data["params"]
    theo_pha = {"GUEST": [], "RESIDENT": []}
    for sid, s in data["sections"].items():
        if s.get("time_assumed") or s.get("original_slot") is None:
            continue
        day, period = divmod(s["original_slot"], p["slotsPerDay"])
        theo_pha.setdefault(s["teacher_type"], []).append({
            "id": sid, "teacherId": s["teacher_id"],
            "teacherName": sc.teacher_display(data, s["teacher_id"]),
            "teacherIds": list(s.get("teacher_ids") or [s["teacher_id"]]),
            "courseName": s.get("course_name"), "program": s["program"],
            "programLabel": sc.section_program_label(data, s),
            "coordinator": ", ".join(sc.section_coordinators(data, s)),
            "roomType": s["room_type"], "day": day, "period": period,
            "slot": s["original_slot"], "duration": s["duration"],
            "teacherType": s["teacher_type"], "status": "DRAFT",
        })

    def goi(loai):
        lessons = sorted(theo_pha[loai], key=lambda l: l["id"])
        return {
            "status": "TU_FILE", "elapsedSeconds": 0.0,
            "total": sum(1 for s in data["sections"].values() if s["teacher_type"] == loai),
            "placedCount": len(lessons), "lessons": lessons, "unplaced": [],
            "initial": True,
        }

    return goi("GUEST"), goi("RESIDENT")


def ghim_gio_da_chot(data):
    """GHIM moi lop da chot gio trong file vao STATE['overrides'].

    Ghim la co che manh nhat trong ca hai pha (xem solve_guest_with_overrides va
    ghim_tay_o_giai_doan_2) nen chay "Xep thinh giang"/"Ghep co huu" khong lam
    xe dich cac lop nay. Solver von cung da ghim theo `original_slot`, nhung ghi
    vao overrides de GIAO DIEN hien dung trang thai "da ghim" - giao vu nhin ra
    ngay lop nao la gio chot tu file, lop nao do he thong xep.
    """
    STATE["overrides"] = {
        sid: {"slot": s["original_slot"], "reason": "Giờ đã chốt trong file"}
        for sid, s in data["sections"].items()
        if not s.get("time_assumed") and s.get("original_slot") is not None
    }


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


def solve_guest_with_overrides(data):
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


def _mien_sau_khi_bo_ghim(data, sid):
    """Mien gio cua mot lop SAU KHI bo ghim: dung y het nhu lop chua bao gio co gio
    trong file - khung DA KHAI cua ca nhom day, chua ai khai thi tu do ca tuan.

    Tinh lai bang chinh apply_section_time(time_info=None) chu khong viet rieng:
    luat "khai roi thi gioi han cung / chua khai thi tu do" chi nen nam mot cho.
    Ham do sua thang tren `data` nen phai cat va tra lai nguyen ven ban goc - lop
    van la lop DA CHOT GIO trong file, bo ghim chi la mot y kien cua giao vu o lan
    giai nay, khong xoa du lieu file."""
    s = data["sections"][sid]
    giu = {k: s.get(k) for k in ("day", "period_start", "period_end", "original_slot",
                                 "time_assumed", "availability_assumed")}
    giu_sub = data["submissions"].get(sid)
    giu_pending = sid in data["pending_section_ids"]
    try:
        teacher = data["teachers"][(s.get("teacher_ids") or [s["teacher_id"]])[0]]
        apply_section_time(data, sid, teacher, s["duration"], None)
        return data["submissions"].get(sid) or []
    finally:
        s.update(giu)
        if giu_sub is None:
            data["submissions"].pop(sid, None)
        else:
            data["submissions"][sid] = giu_sub
        if giu_pending and sid not in data["pending_section_ids"]:
            data["pending_section_ids"].append(sid)
        elif not giu_pending and sid in data["pending_section_ids"]:
            data["pending_section_ids"].remove(sid)


@contextlib.contextmanager
def tam_bo_ghim(data):
    """Trong khoi `with`, cac lop da bam "Bo ghim" co submissions cua lop CHUA co
    gio (thay vi dung mot slot chot tu file) - de ca hai pha deu xep lai that.

    Dung `with` chu khong sua han: du lieu file van phai nguyen ven de con hien
    "gio da chot trong file" o UI va de bo ghim nham thi ghim lai duoc."""
    sids = [sid for sid in STATE["bo_ghim"] if sid in data["sections"]]
    goc = {sid: data["submissions"].get(sid) for sid in sids}
    goc_pending = list(data["pending_section_ids"])
    try:
        for sid in sids:
            data["submissions"][sid] = _mien_sau_khi_bo_ghim(data, sid)
        yield
    finally:
        for sid, v in goc.items():
            if v is None:
                data["submissions"].pop(sid, None)
            else:
                data["submissions"][sid] = v
        data["pending_section_ids"][:] = goc_pending


def ghim_tay_o_giai_doan_2(data):
    """Ghim (dong 1) o Giai doan 2: {section_id: slot} tu STATE['overrides'].

    Truoc day ghim bang cach CAM toan bo slot hop le TRU slot da ghim
    (`forbidden`). Cach do vo khi ghim sang Thu 7/Chu nhat: slot do khong nam
    trong valid_starts() cua RESIDENT nen "cam tat ca" -> domain rong ->
    solve_resident_phase quay ve toan bo valid_starts -> GHIM BI BO QUA am tham,
    lop nhay ve mot ngay khac trong tuan.

    Nay dua thang slot cho solver dat domain (xem tham so ghim_tay) - ghim duoc
    moi ngay, dung nhu Giai doan 1 von da lam qua submissions=[slot]."""
    return {
        sid: ov["slot"]
        for sid, ov in STATE["overrides"].items()
        if ov.get("slot") is not None
        and data["sections"].get(sid, {}).get("teacher_type") == "RESIDENT"
    }
