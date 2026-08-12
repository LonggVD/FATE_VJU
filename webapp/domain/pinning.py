# -*- coding: utf-8 -*-
"""GHIM / BO GHIM - rang buoc dua vao solver.

"Ghim" la co che manh nhat trong ca hai pha giai: thay vi sua scheduler_core.py,
no thu hep MIEN cua buoi bi ghim ve dung mot slot truoc khi goi solver
(Giai doan 1 qua submissions, Giai doan 2 qua tham so ghim_tay). Nho vay giao vu
keo-tha xong thi giai lai bao nhieu lan buoi do cung dung yen.

Viec DUNG LUOI hien thi tu cac ghim nay nam o domain/luoi.py.
"""

import contextlib

import scheduler_core as sc
from domain.hoc_chung import thanh_vien
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
    #
    # HOC CHUNG duoc tru ra: cac lop cung nhom la MOT buoi, chung PHAI o cung o
    # gio - do la muc dich, khong phai xung dot. Ke ca o phong: mot buoi mot phong.
    my_tids = set(s.get("teacher_ids") or [s["teacher_id"]])
    cung_buoi = set(thanh_vien(data, section_id))
    placed = [l for l in placed if l["id"] not in cung_buoi]
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


def ghim_theo_gio_form(data, sid, time_info):
    """Cap nhat GHIM sau khi mot form o "Du lieu hoc phan" dat/xoa gio cua lop.

    PHAI goi o moi cho form ghi gio. Bo qua buoc nay la loi da tung xay ra: nap
    file xong, MOI lop co gio deu duoc ghim (ghim_gio_da_chot). Giao vu sua Thu/
    Tiet trong form -> section doi sang gio moi, nhung ghim VAN tro gio cu, va
    ghim thang o ca ba noi:
      - bang "Du lieu hoc phan" in lai gio CU (build_classes_list doc overrides),
        nen cong sua vua roi nhu bien mat;
      - luoi Thoi khoa bieu giu buoi o o cu;
      - lan Giai lai ke tiep bi ep `submissions=[slot cu]` nen lop nhay ve cho cu.

    Gio do co dinh la mot QUYET DINH cua con nguoi, y het keo-tha tren luoi - nen
    ghim theo dung gio moi. Xoa gio ("de he thong tu xep") thi go ghim de solver
    duoc tu do chon lai.
    """
    if time_info is None:
        STATE["overrides"].pop(sid, None)
        return
    slot = data["sections"][sid].get("original_slot")
    if slot is None:
        STATE["overrides"].pop(sid, None)
        return
    STATE["overrides"][sid] = {
        "slot": slot, "reason": "Giờ đã nhập ở Dữ liệu học phần", "problem": None,
    }
    # Gio vua go tay la y kien MOI NHAT -> khong con la lop "cho he thong xep lai".
    STATE["bo_ghim"].discard(sid)


def lan_gio_sang_nhom(data, sid, time_info):
    """Dat CUNG mot gio cho moi lop HOC CHUNG voi sid. Tra ve cac sid vua doi.

    PHAI goi o moi cho form ghi gio (sua lop, xoa gio, xoa gio hang loat). Bo qua
    la nhom vo ngay: do thuc te truoc khi co ham nay, doi Thu/Tiet cua lop A qua
    form thi A sang slot moi con B o lai slot cu - hai lop "cung mot buoi" nam hai
    o gio khac nhau, va lan Giai sau solver ep chung ve cung slot theo mot trong
    hai gio do (khong biet gio nao) roi bao trung voi lop khac.

    Dung apply_section_time + ghim_theo_gio_form y nhu duong sua tay: gio do cung
    la mot quyet dinh cua con nguoi, chi la ap cho ca nhom."""
    doi = []
    for sid_khac in thanh_vien(data, sid):
        if sid_khac == sid:
            continue
        s = data["sections"].get(sid_khac)
        if s is None:
            continue
        teacher = data["teachers"].get((s.get("teacher_ids") or [s["teacher_id"]])[0])
        if teacher is None:
            continue
        apply_section_time(data, sid_khac, teacher, s["duration"], time_info)
        ghim_theo_gio_form(data, sid_khac, time_info)
        # Gio cu khong con -> "Trang thai lich" het nghia (giong api_manual_clear_times).
        if time_info is None:
            s["schedule_status"] = None
        doi.append(sid_khac)
    return doi


def bo_ghim_ca_nhom(data, sid):
    """Bo ghim lan sang ca nhom hoc chung. Tra ve cac sid vua tha them.

    Tha mot nua thi lan Giai sau mot lop bi ghim cho cu, mot lop tu do chon - hai
    lop "cung mot buoi" khong con o cung o gio nua."""
    them = []
    for sid_khac in thanh_vien(data, sid):
        if sid_khac == sid or sid_khac not in data["sections"]:
            continue
        STATE["overrides"].pop(sid_khac, None)
        STATE["bo_ghim"].add(sid_khac)
        them.append(sid_khac)
    return them


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
