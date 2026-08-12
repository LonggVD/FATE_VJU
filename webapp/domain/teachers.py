# -*- coding: utf-8 -*-
"""GIANG VIEN: phan loai co huu/thinh giang va dong bo lop khi phan loai doi.

Phan loai la thu quyet dinh lop di GIAI DOAN NAO (thinh giang truoc, co huu sau)
va MIEN GIO nao lop duoc xep vao - nen doi mot chu o day keo theo phai tinh lai
lop, khong duoc chi ghi lai truong `type`.
"""

import fate_lecturers
from domain.time_rules import apply_section_time
from state import STATE


def loai_lop(data, teacher_ids):
    """Lop thuoc Giai doan 1 (GUEST) hay 2 (RESIDENT) khi co NHIEU GV dong giang.

    Quy tac: CO MOT NGUOI thinh giang la lop di Giai doan 1.

    Vi sao khong lay theo GV chinh: GD1 xep theo KHUNG GIO DA KHAI cua thinh giang,
    GD2 thi cho chon tu do ca tuan. Neu lop co mot khach moi ma lai di GD2 thi he
    thong co the dat lop vao gio ma nguoi do khong den duoc - va khong ai biet, vi
    khung gio ho khai khong duoc dung den. Huong sai con lai (di GD1 trong khi ca
    nhom deu co huu) chi lam lop bi bo hep hon can thiet, giao vu nhin ra ngay.
    """
    return ("GUEST" if any(data["teachers"][t]["type"] == "GUEST"
                           for t in teacher_ids if t in data["teachers"])
            else "RESIDENT")


def co_huu_theo_danh_sach(name):
    """True/False neu DA nap danh sach co huu, None neu chua nap."""
    ds = STATE.get("co_huu")
    if not ds or not ds.get("byKey"):
        return None
    return fate_lecturers.khoa_ten(name) in ds["byKey"]


def loai_gv(org, name=None):
    """Co huu (RESIDENT, Giai doan 2) hay thinh giang (GUEST, Giai doan 1)?

    1. DA nap danh sach GV co huu -> danh sach la NGUON CHINH THUC: co ten trong
       do la co huu, khong co la thinh giang. Khong doc o don vi nua.
    2. CHUA nap -> quay ve luat cu: o "Don vi cong tac" chua "Viet Nhat" thi co
       huu.

    Vi sao doi: luat cu doc chinh o don vi trong file ke hoach giang day, ma o do
    giao vu go tay moi ky nen sai du kieu - bo trong (HK2: 6 nguoi), ghi ten
    truong moi dong mot kieu, va nang nhat la MOT o don vi cho ca nhom dong giang
    (dong 243 HK1-2: hai khach moi DH Tokyo bi xep co huu vi o do co ca dong
    "Truong DH Viet Nhat" cua nguoi thu ba).
    """
    theo_ds = co_huu_theo_danh_sach(name) if name else None
    if theo_ds is not None:
        return "RESIDENT" if theo_ds else "GUEST"
    low = (org or "").lower()
    return "RESIDENT" if ("việt nhật" in low or "viet nhat" in low) else "GUEST"


def phan_tu(ds, k):
    """Phan tu thu k, "" neu khong co (o email/SDT cua dong dong giang khong luon
    du cho moi nguoi - xem fate_import._split_aligned)."""
    return ds[k] if ds and k < len(ds) else ""


def sync_teacher_sections(data, teacher_id):
    """Dong bo lai cac lop cua 1 GV sau khi PATCH doi loai GV hoac gio ranh.
    CHI cham vao lop nhap qua UI moi (co course_id - lop tu Excel khong co truong
    nay, dung co che 'tu do chon ca tuan' rieng qua valid_starts() toan tuan,
    KHONG lien quan manual_teacher_windows, khong duoc dong bo lai o day) VA dang
    time_assumed=True (chua duoc chot gio cu the boi giao vu - gio da chot thi
    khong phu thuoc GV ranh luc nao nua).
    Khop theo teacher_ids (ca dong giang day, giong check_cross_program_conflicts
    ben scheduler_core.py). teacher_type va gio ranh tinh lai theo CA NHOM
    (loai_lop/gio_ranh_chung) chu khong theo GV chinh: doi mot nguoi dong giang
    tu co huu sang thinh giang thi lop phai chuyen sang Giai doan 1, va khung gio
    cua lop phai hep lai theo nguoi vua khai."""
    for sid, s in data["sections"].items():
        if s.get("course_id") is None:
            continue
        tids = s.get("teacher_ids") or [s["teacher_id"]]
        if teacher_id not in tids:
            continue
        s["teacher_type"] = loai_lop(data, tids)
        if not s.get("time_assumed"):
            continue
        # Dung LAI apply_section_time thay vi tinh lai o day: no la CHO DUY NHAT
        # biet luat "da khai -> gioi han cung / chua khai -> tu do ca tuan", va
        # luat do vua doi (khai cho co huu gio cung co tac dung). Hai ban sao thi
        # se lech nhau ngay lan sua sau.
        chinh = data["teachers"].get(s["teacher_id"])
        if chinh is not None:
            apply_section_time(data, sid, chinh, s["duration"], None)


def ap_lai_loai_gv(data):
    """Phan loai lai TOAN BO giang vien dang co theo luat hien hanh (loai_gv) roi
    dong bo cac lop bi anh huong. Tra ve danh sach {id, name, tu, sang}.

    Dung khi vua nap/xoa danh sach co huu: du lieu da nap tu truoc phai theo luat
    MOI ngay, khong doi nap lai file ke hoach. Doi loai GV keo theo lop doi giai
    doan (loai_lop) va doi MIEN GIO (thinh giang xep theo khung da khai, co huu
    tu do) - nen phai di qua sync_teacher_sections chu khong chi ghi lai `type`.
    """
    doi = []
    for t in data["teachers"].values():
        # Ban ghi "cho trong" van theo luat o don vi - xem cho tao no
        # (domain/excel_rows.py).
        moi = loai_gv(t.get("org"), None if t.get("placeholder") else t.get("name"))
        if moi != t["type"]:
            doi.append({"id": t["id"], "name": t.get("name"), "tu": t["type"], "sang": moi})
            t["type"] = moi
    for m in doi:
        sync_teacher_sections(data, m["id"])
    # Lop KHONG nhap qua UI (nap tu Excel) khong duoc sync_teacher_sections cham
    # vao, nhung loai lop van phai theo nhom GV moi - neu khong, lop cua GV vua
    # doi loai se ket lai o giai doan cu.
    for s in data["sections"].values():
        s["teacher_type"] = loai_lop(data, s.get("teacher_ids") or [s["teacher_id"]])
    dem_lai_so_gv(data)
    return doi


def dem_lai_so_gv(data):
    """Cap nhat num_resident/num_guest theo `type` hien tai cua tung GV.

    Ba dong nay truoc day duoc go lai o 5 endpoint khac nhau; go sot mot cho la
    con so tren giao dien lech ma khong co gi bao."""
    data["num_resident"] = sum(1 for t in data["teachers"].values() if t["type"] == "RESIDENT")
    data["num_guest"] = len(data["teachers"]) - data["num_resident"]


def doi_chieu_danh_sach(data, by_key):
    """So danh sach co huu voi giang vien dang co -> bao cao cho buoc XEM TRUOC.

    Ba con so quan trong, moi con so mot y nghia khac han:
      - `khop`      : nguoi trong danh sach co day ky nay (se thanh co huu)
      - `doiSangCoHuu` / `doiSangThinhGiang`: ai bi DOI loai neu bam nap
      - `khongDay`  : nguoi trong danh sach nhung khong day lop nao ky nay -
                      binh thuong (nghi/khong phan cong), chi de biet.
    """
    that = [t for t in (data or {}).get("teachers", {}).values() if not t.get("placeholder")]
    co_trong_ds = {fate_lecturers.khoa_ten(t.get("name")) for t in that}
    khop = [t for t in that if fate_lecturers.khoa_ten(t.get("name")) in by_key]
    return {
        "soGvDangCo": len(that),
        "khop": len(khop),
        "doiSangCoHuu": [
            {"id": t["id"], "name": t.get("name"), "org": t.get("org")}
            for t in that
            if t["type"] != "RESIDENT" and fate_lecturers.khoa_ten(t.get("name")) in by_key
        ],
        "doiSangThinhGiang": [
            {"id": t["id"], "name": t.get("name"), "org": t.get("org")}
            for t in that
            if t["type"] == "RESIDENT" and fate_lecturers.khoa_ten(t.get("name")) not in by_key
        ],
        "khongDay": sorted(v["name"] for k, v in by_key.items() if k not in co_trong_ds),
    }
