# -*- coding: utf-8 -*-
"""Ra soat CHAT LUONG DU LIEU cua file ke hoach giang day, hien ngay o buoc xem
truoc khi nhap.

Khac gi voi `warnings` cua fate_import?
  - `warnings` noi ve viec IMPORT da phai tu quyet dinh gi ("dong nay 2 buoi nen
    tach thanh 2 lop", "o giang vien de trong"). Doc xong la biet import lam gi.
  - Module nay noi ve LOI TRONG CHINH FILE: cung mot hoc phan ghi hai ma khac
    nhau, mot ma lop dung cho hai hoc phan, ten hoc phan khac dau tieng Viet
    thanh hai hoc phan, mot email gan cho hai nguoi, dong bi nhap trung... Import
    khong "sai" o cho nao, nhung du lieu ra khong dung y giao vu.

Vi sao can: ra soat tay ba file that tim ra ~12 loai loi nhu vay (mot ma lop
FLF1108 dung cho ca "Tieng Anh B1" va "Tieng Anh B2"; ma MNS2006 gan cho lop
VJU2012-3; VJU2031 ghi 3 va 5 tin chi...). Truoc do buoc xem truoc KHONG he
hien nhung thu nay - phai viet script rieng moi thay, tuc thuc te la khong ai
thay. Nay moi lan nhap file la thay.

Tra ve dung khuon nhom ma UI dang render (loai/nhan/so/dong/chiTiet), kem `muc`
de UI tach "sai chac chan" ra khoi "nen ra lai".
"""
import re
import unicodedata
from collections import defaultdict

# Ô email chuẩn: đúng một địa chỉ, không lẫn SĐT/địa chỉ thứ hai.
_EMAIL_RE = re.compile(r"^[^@\s,;]+@[^@\s,;]+\.[a-z]{2,}$", re.IGNORECASE)
# CTĐT phải là mã chương trình (BCSE, MJM, FTH + ESAS...) chứ không phải một câu.
_CTDT_LA_RE = re.compile(r"[()]|\bvới\b|\bhọc ghép\b|\bchưa\b|\bđã\b", re.IGNORECASE)
# Ma khoa: chu + NAM nhap hoc, vd "VJU2026". Ghep nhieu khoa thi ngan boi +/,/;
# tung phan phai khop mau nay.
#
# Bat buoc phan so la nam (19xx/20xx) chu khong phai 4 chu so bat ky: "VNU1001"
# la MA HOC PHAN lot vao cot Khoa (co that o HK2, 2 dong) - \\d{4} thi khong bat
# duoc. Con ma hoc phan dang "XXX20xx" (vd MNS2006) thi van lot, khong the phan
# biet bang hinh thuc - va KHONG the doi chieu voi danh sach ma hoc phan trong
# file: ma HP that co ca VJU2021/VJU2022, trung voi ma khoa.
_KHOA_RE = re.compile(r"^[A-Z]{2,4}(19|20)\d{2}$")
_SO_DONG_HIEN = 40  # so dong Excel gui kem moi nhom (UI con cat ngan nua)


def _bo_dau(s):
    """Bo dau tieng Viet + hoa/thuong + khoang trang du - de nhan ra "Hoá học 2"
    va "Hóa học 2" LA MOT hoc phan bi ghi hai kieu."""
    s = unicodedata.normalize("NFD", " ".join(str(s or "").split()).lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace("đ", "d")


def _nhom(loai, nhan, muc, chi_tiet, don_vi="trường hợp"):
    """`so` dem TRUONG HOP (vd 5 ma lop bi dung cho nhieu hoc phan), khong phai so
    dong - nen phai gui kem `donVi` de UI khong ghi "5 dong".

    chi_tiet: danh sach (text, so, cac_dong). Moi truong hop mang so dong RIENG -
    file xuat ra cho khoa sua can dung dong cua tung truong hop, chu khong phai
    dong cua ca nhom."""
    return {
        "loai": loai, "nhan": nhan, "muc": muc, "so": len(chi_tiet), "donVi": don_vi,
        "chiTiet": [{"text": t, "so": n, "dong": sorted(set(d))[:_SO_DONG_HIEN]}
                    for t, n, d in chi_tiet],
        "dong": sorted({x for _, _, d in chi_tiet for x in d})[:_SO_DONG_HIEN],
    }


def _gom(rows, khoa_fn, gia_tri_fn):
    """{khoa: (cac gia tri khac nhau, cac dong Excel)} - bo qua khoa/gia tri rong."""
    ra = defaultdict(lambda: (defaultdict(int), []))
    for r in rows:
        k = khoa_fn(r)
        v = gia_tri_fn(r)
        if not k or not v:
            continue
        dem, dong = ra[k]
        dem[v] += 1
        dong.append(r["excelRow"])
    return ra


def _ten(r):
    return " ".join((r["courseName"] or "").split())


def kiem_tra(rows, teachers=None):
    """rows: fate_import.read_rows()["rows"]; teachers: data["teachers"] (de doi
    chieu email sau khi da gop nguoi). Tra ve danh sach nhom, nang truoc nhe sau."""
    nhom = []

    # --- 1. Mot MA LOP dung cho nhieu hoc phan ---------------------------------
    g = _gom(rows, lambda r: (r["classCode"] or "").strip(), _ten)
    xau = [(k, v) for k, v in g.items() if len(v[0]) > 1]
    if xau:
        nhom.append(_nhom(
            "ma_lop_nhieu_hoc_phan",
            "Một mã lớp học phần dùng cho NHIỀU học phần khác nhau",
            "nghiem_trong",
            [(f"{k} → {' | '.join(sorted(v[0]))}"[:220], sum(v[0].values()), v[1])
             for k, v in xau],
        ))

    # --- 2. Mot MA HOC PHAN mang nhieu ten -------------------------------------
    g = _gom(rows, lambda r: (r["courseCode"] or "").strip(), _ten)
    xau = [(k, v) for k, v in g.items()
           if len({_bo_dau(x) for x in v[0]}) > 1]  # khac han, khong phai khac dau
    if xau:
        nhom.append(_nhom(
            "ma_hp_nhieu_ten",
            "Một mã học phần mang nhiều TÊN học phần khác nhau",
            "nghiem_trong",
            [(f"{k} → {' | '.join(sorted(v[0]))}"[:220], sum(v[0].values()), v[1])
             for k, v in xau],
        ))

    # --- 3. Cung TEN hoc phan nhung nhieu MA ----------------------------------
    # Gom theo ten DA BO DAU (de "Hoá"/"Hóa" ve cung nhom) nhung hien lai ten NHU
    # TRONG FILE - giao vu phai tim duoc dong do trong Excel.
    ten_that = {}
    for r in rows:
        ten_that.setdefault(_bo_dau(_ten(r)), _ten(r))
    g = _gom(rows, lambda r: _bo_dau(_ten(r)), lambda r: (r["courseCode"] or "").strip())
    xau = [(k, v) for k, v in g.items() if len(v[0]) > 1]
    if xau:
        nhom.append(_nhom(
            "ten_hp_nhieu_ma",
            "Cùng một tên học phần nhưng ghi nhiều MÃ khác nhau (nghi sai chính tả mã)",
            "nghiem_trong",
            [(f"{ten_that.get(k, k)[:60]} → {' | '.join(sorted(v[0]))}",
               sum(v[0].values()), v[1]) for k, v in xau],
        ))

    # --- 4. Ten hoc phan chi khac DAU / hoa thuong ----------------------------
    g = _gom(rows, lambda r: _bo_dau(_ten(r)), _ten)
    xau = [(k, v) for k, v in g.items() if len(v[0]) > 1]
    if xau:
        nhom.append(_nhom(
            "ten_hp_khac_dau",
            "Cùng một học phần nhưng tên ghi khác dấu/khác hoa-thường → bị tách thành 2 học phần",
            "nghiem_trong",
            [(" | ".join(sorted(v[0]))[:220], sum(v[0].values()), v[1]) for k, v in xau],
        ))

    # --- 5. So tin chi khac nhau giua cac dong cung hoc phan ------------------
    g = _gom(rows, lambda r: ((r["courseCode"] or "").strip(), _bo_dau(_ten(r))),
             lambda r: r["credits"] and str(r["credits"]))
    xau = [(k, v) for k, v in g.items() if len(v[0]) > 1]
    if xau:
        nhom.append(_nhom(
            "so_tc_khac_nhau",
            "Cùng một học phần nhưng Số tín chỉ ghi khác nhau giữa các dòng",
            "nghiem_trong",
            [(f"{k[0] or '(không mã)'} {ten_that.get(k[1], k[1])[:45]} → "
              f"{', '.join(sorted(v[0]))} tín chỉ", sum(v[0].values()), v[1])
             for k, v in xau],
        ))

    # --- 6. Dong nghi bi nhap TRUNG LAP --------------------------------------
    # Cung ma lop + cung GV + cung gio, o CAC DONG EXCEL KHAC NHAU. Moi ban trung
    # se an mot phong rieng va lam TKB doi hai lan tai nguyen cho cung mot lop.
    dup = defaultdict(list)
    for r in rows:
        if not (r["classCode"] or "").strip() or r["day"] is None:
            continue
        dup[(r["classCode"].strip(), r["teacherName"], r["day"],
             r["periodStart"], r["periodEnd"])].append(r["excelRow"])
    xau = [(k, v) for k, v in dup.items() if len(set(v)) > 1]
    if xau:
        nhom.append(_nhom(
            "dong_nghi_trung_lap",
            "Nghi NHẬP TRÙNG: cùng mã lớp, cùng giảng viên, cùng giờ ở nhiều dòng khác nhau",
            "nghiem_trong",
            [(f"{k[0]} · {k[1][:28]} · thứ {k[2] + 2}, tiết {k[3]}-{k[4]} → dòng "
              f"{', '.join(str(x) for x in sorted(set(v)))}", len(set(v)), v)
             for k, v in xau],
        ))

    # --- 7. Email --------------------------------------------------------------
    if teachers:
        that = [t for t in teachers.values() if not t.get("placeholder")]
        mail = defaultdict(set)
        loi_mail = []
        for t in that:
            e = (t.get("email") or "").strip()
            if not e:
                continue
            if _EMAIL_RE.match(e):
                mail[e.lower()].add(t["name"])
            else:
                loi_mail.append((f"{t['name']} → {e[:70]}", 1, []))
        chung = [(f"{k} → {' | '.join(sorted(v))}", len(v), []) for k, v in mail.items()
                 if len(v) > 1]
        if chung:
            nhom.append(_nhom(
                "email_nhieu_nguoi",
                "Một địa chỉ email được gán cho NHIỀU giảng viên khác nhau (nghi copy-paste sai)",
                "nghiem_trong", chung))
        if loi_mail:
            nhom.append(_nhom(
                "email_khong_hop_le",
                "Ô email không phải một địa chỉ (lẫn SĐT, hoặc ghi nhiều email trong một ô)",
                "luu_y", loi_mail))

    # --- 8. CTDT khong phai ma chuong trinh -----------------------------------
    ctdt = defaultdict(list)
    for r in rows:
        if _CTDT_LA_RE.search(r["program"] or ""):
            ctdt[r["program"]].append(r["excelRow"])
    if ctdt:
        nhom.append(_nhom(
            "ctdt_khong_phai_ma",
            "Cột CTĐT chứa cả câu giải thích → thành một “chương trình” riêng trong hệ thống",
            "luu_y",
            [(k[:120], len(v), v) for k, v in ctdt.items()],
        ))

    # --- 8b. Cot Khoa ---------------------------------------------------------
    # Cot nay gio la mot BO LOC tren ca hai man (bang du lieu hoc phan va thoi
    # khoa bieu), nen gia tri bay sai la hien thang vao danh sach chon.
    la_khoa, bien_the = defaultdict(list), defaultdict(dict)
    for r in rows:
        khoa = " ".join((r["cohort"] or "").split())
        if not khoa:
            continue  # da co phep kiem "thieu_khoa" rieng
        phan = [x.strip().upper() for x in re.split(r"[+,;/]", khoa) if x.strip()]
        if any(not _KHOA_RE.match(x) for x in phan):
            la_khoa[khoa].append(r["excelRow"])
        elif len(phan) > 1:
            # Ghep nhieu khoa: "VJU2023+VJU2024" va "VJU2024+VJU2023" cung nghia
            # nhung la HAI dong khac nhau trong bo loc.
            bien_the[tuple(sorted(set(phan)))].setdefault(khoa, []).extend([r["excelRow"]])
    if la_khoa:
        nhom.append(_nhom(
            "khoa_khong_hop_le",
            "Cột Khoá có giá trị không phải mã khoá (vd mã học phần lọt vào) → thành một mục "
            "lạ trong bộ lọc theo khoá",
            "nghiem_trong",
            [(k[:120], len(v), v) for k, v in la_khoa.items()],
        ))
    nhieu_kieu = {k: v for k, v in bien_the.items() if len(v) > 1}
    if nhieu_kieu:
        nhom.append(_nhom(
            "khoa_ghep_nhieu_kieu",
            "Cùng một nhóm khoá nhưng viết nhiều kiểu (khác thứ tự/dấu cách) — bộ lọc đã tách "
            "theo từng khoá nên không ảnh hưởng, nhưng nên viết thống nhất trong file",
            "luu_y",
            [(" | ".join(f"“{x}”" for x in sorted(v)), sum(len(d) for d in v.values()),
              [d for ds in v.values() for d in ds]) for v in nhieu_kieu.values()],
        ))

    # --- 9. Ten hoc phan chua ghi chu ----------------------------------------
    gc = defaultdict(list)
    for r in rows:
        t = _ten(r)
        if len(t) > 55 or re.search(r"\((?:dự kiến|khoa sẽ|hk|do số|chia làm)", t, re.IGNORECASE):
            gc[t].append(r["excelRow"])
    if gc:
        nhom.append(_nhom(
            "ten_hp_co_ghi_chu",
            "Ghi chú bị viết vào ô Tên học phần → thành một phần của tên học phần",
            "luu_y",
            [(k[:120], len(v), v) for k, v in gc.items()],
        ))

    # --- 10. Thieu du lieu ----------------------------------------------------
    thieu = [
        ("thieu_ma_lop", "Dòng không có Mã lớp học phần",
         lambda r: not (r["classCode"] or "").strip()),
        ("thieu_ma_hp", "Dòng không có Mã học phần",
         lambda r: not (r["courseCode"] or "").strip()),
        ("thieu_so_tc", "Dòng không có Số tín chỉ", lambda r: not r["credits"]),
        ("thieu_khoa", "Dòng không có Khoá", lambda r: not (r["cohort"] or "").strip()),
        ("thieu_so_sv", "Dòng không có Số SV dự kiến", lambda r: not r["expectedStudents"]),
    ]
    for loai, nhan, dk in thieu:
        dong = sorted({r["excelRow"] for r in rows if dk(r)})
        if dong:
            nhom.append({
                "loai": loai, "nhan": nhan, "muc": "luu_y", "so": len(dong),
                "donVi": "dòng", "chiTiet": [], "dong": dong[:_SO_DONG_HIEN],
            })

    return sorted(nhom, key=lambda g: (g["muc"] != "nghiem_trong", -g["so"]))


def tom_tat(nhom):
    """{soNghiemTrong, soLuuY} - de UI hien con so ngay o tieu de."""
    return {
        "soNghiemTrong": sum(g["so"] for g in nhom if g["muc"] == "nghiem_trong"),
        "soLuuY": sum(g["so"] for g in nhom if g["muc"] == "luu_y"),
    }
