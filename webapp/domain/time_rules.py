# -*- coding: utf-8 -*-
"""GIO CUA MOT LOP: doc Thu/Tiet tu request, ghi vao bo du lieu, luat chong lan.

apply_section_time() la CHO DUY NHAT biet luat "gio da chot -> mot slot / chua co
gio -> khung ranh cua nhom hoac tu do ca tuan". Moi duong ghi gio (nhap tay, nap
file, chot hoc phan, luu TKB, doi so tiet/ngay) deu phai di qua no - hai ban sao
cua luat nay se lech nhau ngay lan sua sau.
"""

import scheduler_core as sc
from domain.availability import gio_ranh_chung, valid_starts_from_slots
from state import DAY_LABELS_VN


def overlaps(a, dur_a, b, dur_b):
    """Hai buoi co chong gio nhau khong. CUNG MOT cong thuc voi
    scheduler_core._giao_nhau va overlaps() ben frontend - ba noi phai giong nhau
    de khong bao lech."""
    return not (a + dur_a <= b or b + dur_b <= a)


def parse_class_time(body, slots_per_day, teacher_type=None, enforce_cap=True):
    """Doc {day, periodStart, periodEnd, autoSchedule} tu body 1 lop nhap tay -
    day gio da CHOT boi con nguoi cho dung lop nay (khac voi 'khung gio ranh cua
    GV' o /api/manual/teacher, von la nhieu lua chon de GV/dieu phoi vien khai
    bao roi solver moi chon 1). Tra ve (time_dict, error) - time_dict la
    {'day','period_start','period_end'} hoac None neu tick 'de he thong tu xep'
    hoac de trong ca 3 truong; error la str neu du lieu nhap sai dinh dang/khoang.
    teacher_type (neu co): chan Thu vuot qua quy dinh (thinh giang toi Thu 7,
    co huu toi Thu 6) - giao vu go tay khong lach duoc rang buoc ma solver dang
    tuan theo (xem sc.MAX_DAY_INDEX).

    enforce_cap=False (danh cho luong NAP FILE hang loat - xem
    domain/excel_rows.py): GIU NGUYEN gio trong file, ke ca Thu 7/Chu nhat
    voi GV co huu. Vi mot dong trong file la mot lop DA CHOT GIO - GV va dieu phoi
    vien da thong nhat voi nhau roi, he thong khong co quyen doi. Quy dinh ngay chi
    ap cho lop CHUA co gio, luc do he thong moi la nguoi chon.

    Truoc day cho nay tra (None, None) = bo gio, chuyen "de he thong tu xep": lam
    15 lop cua HK1 2026-2027-2 (thuc tap/thuc hanh/do an xep Thu 7-Chu nhat) mat
    gio thuc.

    Tiet ngoai pham vi thi van bo gio (khong bo lop) - xem trong than ham."""
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
        # O luong NAP FILE, mot o gio ngoai pham vi KHONG duoc lam rung ca lop:
        # truoc day chon nguon gio ghi tiet 13 o buoc "Xac nhan gio hoc" lam lop
        # bien mat khoi bo du lieu, mat luon GV/SV/hoc phan, chi de lai mot dong
        # loi "Thu/Tiet khong hop le". Bo gio, giu lop.
        if not enforce_cap:
            return None, None
        return None, "Thứ/Tiết không hợp lệ."
    # Quy dinh ngay: CHI ap khi go tay (enforce_cap=True). Gio tu file la gio da
    # chot - giu nguyen, chi ghi nhan de bao o buoc xem truoc.
    if enforce_cap and teacher_type is not None and day > sc.max_day_index(teacher_type):
        max_label = DAY_LABELS_VN[sc.max_day_index(teacher_type)]
        loai = "Thỉnh giảng" if teacher_type == "GUEST" else "Cơ hữu"
        return None, f"{loai} chỉ được dạy tới {max_label}."
    return {"day": day, "period_start": p_start, "period_end": p_end}, None


def apply_section_time(data, sid, teacher, duration, time_info):
    """Cap nhat submissions[sid]/pending_section_ids/original_slot cua 1 lop dua
    theo time_info (None = de he thong tu xep) - dung chung cho tao moi va sua.
    time_info khac None: gio da CHOT, submissions rut ve DUNG 1 slot do (giong 1
    dong Excel co gio parse duoc), bo qua het co che 'khung gio ranh cua GV'.
    time_info None: xep theo khung gio ranh DA KHAI (/api/manual/teacher) - CA
    thinh giang VA co huu, giao cac khung cua ca nhom (gio_ranh_chung). Chua ai
    khai gi thi tu do ca tuan (danh dau availability_assumed):
      - GUEST: submissions = toan bo khung hop le (mien cua Giai doan 1 CHINH LA
        submissions nen phai dien du).
      - RESIDENT: submissions = [] (Giai doan 2 tu dung mien tu do) - hai cach ghi
        khac nhau cho cung mot y, vi hai pha lay mien theo hai duong khac nhau.

    Vi sao "chua khai = ranh ca tuan" chu khong phai "khong xep duoc": nap file HK2
    cho 88/119 lop thinh giang khong co gio va GV chua khai gio ranh -> giai ra chi
    xep duoc 24/119, tuc gan nhu vo dung cho den khi co nguoi khai tay 88 lan. Coi
    nhu ranh ca tuan thi thuat toan xep duoc ngay, giao vu thu hep lai sau neu can
    - va van dem duoc bao nhieu lop dang o trang thai "doan" (num_availability_
    assumed) de khong ai hieu nham day la gio GV da xac nhan."""
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
    s["availability_assumed"] = False
    # Loai lop va gio ranh deu tinh theo CA NHOM dong giang (teachers.loai_lop/
    # availability.gio_ranh_chung), khong chi GV chinh: lop 5 nguoi day thi phai
    # xep vao gio CA 5 nguoi ranh.
    tids = s.get("teacher_ids") or [s["teacher_id"]]
    loai = s.get("teacher_type", teacher["type"])
    slots_per_day = data["params"]["slotsPerDay"]
    available, so_nguoi_khai = gio_ranh_chung(data, tids)
    starts = valid_starts_from_slots(available, duration, slots_per_day)
    if starts:
        # DA KHAI gio -> GIOI HAN CUNG, ke ca voi co huu: chi xep trong khung do.
        # Khung do khong bi cat theo quy dinh ngay (sc.MAX_DAY_INDEX): quy dinh la
        # de HE THONG chon ho, con GV khai Thu 7 la con nguoi tu noi minh day duoc
        # hom do - cung ly le voi "gio trong file la gio da chot".
        data["submissions"][sid] = starts
        return
    if so_nguoi_khai:
        # DA khai nhung khong con khung nao du dai cho lop nay (voi lop nhieu GV:
        # giao cac khung khong con cho) -> xung dot THAT, phai bao chu khong duoc
        # tu noi ra ca tuan.
        data["submissions"][sid] = []
        data["pending_section_ids"].append(sid)
        return
    # CHUA ai khai gi -> tu do ca tuan (xem docstring).
    s["availability_assumed"] = True
    if loai == "RESIDENT":
        data["submissions"][sid] = []
        return
    data["submissions"][sid] = sc.valid_starts(
        data["params"]["numDays"], slots_per_day, duration, loai)
