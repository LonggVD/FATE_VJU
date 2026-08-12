# -*- coding: utf-8 -*-
"""GOP hai bo du lieu va DOI so tiet/ngay.

Vi sao can gop: truoc day nhap file chi GHI DE - nap file cua khoa thu hai la mat
sach file thu nhat va mat cong giao vu da sua.

Cai bay lon nhat cua viec gop: `slot` la mot so nguyen chi co nghia KEM theo
slotsPerDay cua chinh bo du lieu do (slot = day * slotsPerDay + tiet-1). Tron hai
bo co so tiet/ngay khac nhau ma khong ma hoa lai thi gio bi doc sai hoan toan -
mot lop "Thu 4 tiet 3-4" (spd=13) sau khi gop vao bo spd=15 thanh "Thu 2 tiet 14".
"""

from collections import Counter

import fate_import
from domain.programs import program_ids_cua_lop
from domain.sections import khoa_lop
from domain.teachers import dem_lai_so_gv
from domain.time_rules import apply_section_time


def noi_slots_per_day(data, rows):
    """Noi so tiet/ngay cho vua tiet lon nhat co trong file (khong bao gio thu hep).

    Truoc day chot cung 12 nen file HK1 2026-2027-2 ghi tiet 13 (dong 280/281:
    CSE4001, CSE4002) bi coi la "khong hop le". Chot cung mot con so moi ky lai
    phai sua code, nen lay theo du lieu.

    Chan tren la fate_import.MAX_TIET - gia tri lon hon la go sai, noi theo no chi
    phong to mo hinh solver vo ich (moi tiet nhan 7 ngay). Nhung dong do da co
    canh bao "gio_ngoai_pham_vi_tiet" va se thanh "de he thong tu xep".
    """
    tiet = [r["periodEnd"] for r in rows
            if r["periodEnd"] and r["periodEnd"] <= fate_import.MAX_TIET]
    if tiet:
        data["params"]["slotsPerDay"] = max(data["params"]["slotsPerDay"], max(tiet))
    return data["params"]["slotsPerDay"]


def doi_slots_per_day(data, spd_moi):
    """Doi so tiet/ngay cua mot bo du lieu va MA HOA LAI moi slot theo so moi.

    Dung lai apply_section_time() cho tung lop thay vi tu tinh: no la CHO DUY NHAT
    biet luat sinh submissions/pending (gio da chot -> 1 slot; chua co gio -> khung
    ranh cua nhom hoac ca tuan).
    """
    spd_cu = data["params"]["slotsPerDay"]
    if spd_moi == spd_cu:
        return

    def ma_hoa_lai(slot):
        day, tiet0 = divmod(slot, spd_cu)
        return day * spd_moi + tiet0

    data["params"]["slotsPerDay"] = spd_moi
    for tid, slots in list((data.get("manual_teacher_windows") or {}).items()):
        data["manual_teacher_windows"][tid] = [ma_hoa_lai(s) for s in slots]

    for sid, s in data["sections"].items():
        teacher = data["teachers"].get(s["teacher_id"])
        if teacher is None:
            continue
        if s.get("time_assumed") or s.get("original_slot") is None:
            time_info = None
        elif s.get("day") is not None:
            time_info = {"day": s["day"], "period_start": s["period_start"],
                         "period_end": s["period_end"]}
        else:
            # Lop chi co original_slot, khong co day/period_start - suy lai tu slot
            # theo so tiet CU.
            day, tiet0 = divmod(s["original_slot"], spd_cu)
            time_info = {"day": day, "period_start": tiet0 + 1,
                         "period_end": tiet0 + s["duration"]}
        apply_section_time(data, sid, teacher, s["duration"], time_info)


def gop_manual_data(cu, moi):
    """GOP bo du lieu vua nap (moi) VAO bo dang co (cu). Doi `cu` tai cho.

    Gop theo dung cac khoa ma ban thanh cong dang dung: giang vien theo
    fate_import.khoa_gv (bo hoc ham/dau cau), hoc phan theo (ma, ten), chuong trinh
    theo ten qua programs.get_or_create_program. Lop TRUNG (xem sections.khoa_lop)
    thi BO QUA - nap lai cung mot file khong nhan doi so lop.

    Tra ve bao cao {soLopThem, soLopTrung, soGvThem, soHocPhanThem} de UI noi ro
    da gop duoc gi, thay vi bao "xong" mo ho.
    """
    bao_cao = {"soLopThem": 0, "soLopTrung": 0, "soGvThem": 0, "soHocPhanThem": 0}

    # Dua CA HAI bo ve cung so tiet/ngay TRUOC khi tron section: slot mang nghia
    # khac nhau o hai bo neu slotsPerDay khac nhau (xem doi_slots_per_day).
    spd = max(cu["params"]["slotsPerDay"], moi["params"]["slotsPerDay"])
    if spd != cu["params"]["slotsPerDay"]:
        bao_cao["soTietMoiNgay"] = spd
    doi_slots_per_day(cu, spd)
    doi_slots_per_day(moi, spd)

    # --- Giang vien: map id cu <- id moi ---
    gv_theo_khoa = {fate_import.khoa_gv(t["name"]): tid
                    for tid, t in cu["teachers"].items() if not t.get("placeholder")}
    map_gv = {}
    for tid, t in moi["teachers"].items():
        # Ban ghi "cho trong" (Phong Dao tao dieu phoi...) LUON tao moi: moi lop
        # chua phan cong phai co ban ghi rieng, khong duoc dung chung (neu khong
        # he thong coi ca chuc lop la cua mot nguoi -> bao trung gio gia).
        khoa = fate_import.khoa_gv(t["name"])
        if not t.get("placeholder") and khoa in gv_theo_khoa:
            map_gv[tid] = gv_theo_khoa[khoa]
            continue
        moi_id = max(cu["teachers"], default=-1) + 1
        cu["teachers"][moi_id] = {**t, "id": moi_id}
        cu.setdefault("manual_teacher_windows", {})[moi_id] = list(
            moi.get("manual_teacher_windows", {}).get(tid) or [])
        map_gv[tid] = moi_id
        if not t.get("placeholder"):
            gv_theo_khoa[khoa] = moi_id
            bao_cao["soGvThem"] += 1

    # --- Hoc phan ---
    hp_theo_khoa = {((c.get("code") or "").strip().lower(),
                     fate_import.khoa_gv(c.get("name") or "")): cid
                    for cid, c in cu.get("courses", {}).items()}
    map_hp = {}
    for cid, c in moi.get("courses", {}).items():
        khoa = ((c.get("code") or "").strip().lower(), fate_import.khoa_gv(c.get("name") or ""))
        if khoa in hp_theo_khoa:
            map_hp[cid] = hp_theo_khoa[khoa]
            continue
        moi_id = max(cu.setdefault("courses", {}), default=-1) + 1
        cu["courses"][moi_id] = {**c, "id": moi_id}
        map_hp[cid] = hp_theo_khoa[khoa] = moi_id
        bao_cao["soHocPhanThem"] += 1

    # --- Lop ---
    #
    # Dem theo SO LUONG, khong dung tap hop. Mot file that co nhieu lop DUNG CHUNG
    # khoa nay: 5 lop "THL1057 / Nha nuoc va phap luat / Phong Dao tao dieu phoi /
    # chua co gio" la 5 lop khac nhau nhung khong co gi de phan biet. Do tren HK2:
    # 23 khoa bi lap, phu 34 lop. Neu dung tap hop thi moi nhom thu ve 1 -> gop mot
    # file vao bo khac lam RUNG 34 lop that.
    #
    # Dem thi: nap lai dung file da co (5 gap 5) -> bo qua het, khong nhan doi; con
    # gop file khac (5 gap 0) -> them du 5.
    dem_da_co = Counter(khoa_lop(cu, s) for s in cu["sections"].values())
    for sid, s in sorted(moi["sections"].items()):
        moi_s = {
            **s,
            "teacher_id": map_gv[s["teacher_id"]],
            "teacher_ids": [map_gv[t] for t in (s.get("teacher_ids") or [s["teacher_id"]])],
            "course_id": map_hp.get(s.get("course_id")),
        }
        # CTDT: gop theo NGUYEN VAN o trong file ("BCSE+MJM") roi tach lai thanh
        # tung thanh phan trong bo `cu` - id o hai bo khong the dung chung.
        moi_s["program_ids"] = program_ids_cua_lop(cu, s.get("program_raw"))
        moi_s["program"] = moi_s["program_ids"][0]
        khoa = khoa_lop(cu, moi_s)
        if dem_da_co[khoa] > 0:
            dem_da_co[khoa] -= 1  # dung MOT ban da co cho lop nay
            bao_cao["soLopTrung"] += 1
            continue
        moi_sid = max(cu["sections"], default=-1) + 1
        moi_s["id"] = moi_sid
        cu["sections"][moi_sid] = moi_s
        cu["submissions"][moi_sid] = list(moi["submissions"].get(sid) or [])
        if sid in moi.get("pending_section_ids", []):
            cu["pending_section_ids"].append(moi_sid)
        bao_cao["soLopThem"] += 1

    dem_lai_so_gv(cu)
    cu["num_time_assumed"] = sum(1 for s in cu["sections"].values() if s.get("time_assumed"))
    cu["num_availability_assumed"] = sum(
        1 for s in cu["sections"].values() if s.get("availability_assumed"))
    return bao_cao
