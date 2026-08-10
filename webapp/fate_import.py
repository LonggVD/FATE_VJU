# -*- coding: utf-8 -*-
"""Doc file ke hoach giang day (Excel) ra cac DONG CHUAN HOA de nap vao form
"Du lieu hoc phan".

Khac gi voi scheduler_core.load_real_fate_data()?
  - Ham do doc file cho THUAT TOAN: chi lay ~12 cot no can (mon/GV/gio/phong),
    va tra ve thang cau truc solver. Khong co thuc the "hoc phan" (courses),
    section chi giu 11 truong.
  - Module nay doc file cho FORM: lay DU 29 cot ma bang mirror dang hien (ma HP,
    so TC, khoa, so SV, email, SDT, dia diem, hinh thuc, ngon ngu, ghi chu...),
    de giao vu nap file cu vao roi sua tiep nhu tu go tay.

Module nay CHI doc va chuan hoa - khong dung toi Flask, khong dung toi STATE.
Viec dung du lieu nhap tay tu cac dong nay do app.py lam, bang chinh cac ham ma
endpoint nhap tay dung (_validate_section_body/_apply_section_time), de du lieu
import ra khong khac gi du lieu go tay.
"""
import re

import openpyxl

import scheduler_core as sc

# Ban do COT -> truong cua form, cho tung dang file da gap.
# Khoa dat trung ten field trong body JSON cua POST /api/manual/section, de app.py
# chi viec chuyen tiep.
#
# Them dang moi thi them mot muc o day; cac cot khong co trong file thi de None
# va se ra rong trong form (giao vu dien sau).
LAYOUTS = {
    # HK2 2025-2026 - cau truc CHUAN, dung tiep cho cac ky sau.
    # Khong co cot "Hoc ham/vi" rieng (hoc ham nam san trong ho ten), cung khong
    # co cot GV ky truoc de doi chieu.
    "FATE": {
        "header_row": 6,
        "courseCode": 0, "courseName": 1, "credits": 2, "classCode": 3,
        "ltCredits": 4, "thCredits": 5,
        "cohort": 7, "program": 8, "expectedStudents": 9,
        "timeText": None, "thu": 11, "tietDau": 12, "tietCuoi": 13,
        "teacherTitle": None, "teacherName": 14, "teacherOrg": 15,
        "teacherEmail": 16, "teacherPhone": 17,
        "teachingHoursLt": 18, "teachingHoursTh": 19,
        "location": 21, "teachingMode": 22, "language": 23,
        "otherRequirements": 24, "notes": 25, "coordinatorOverride": None,
        "prevTeacherName": None, "prevTeacherOrg": None,
    },
    # HK1 2026-2027 - cau truc CU. Day chinh la file ma bang 29 cot cua form
    # dang mo phong, nen anh xa gan nhu 1:1.
    "Giảng dạy cho FATE": {
        "header_row": 8,
        "courseCode": 1, "courseName": 2, "credits": 3, "classCode": 4,
        "ltCredits": 5, "thCredits": 6,
        "cohort": 7, "program": 8, "expectedStudents": 9,
        "timeText": 10, "thu": 11, "tietDau": 12, "tietCuoi": 13,
        "prevTeacherName": 14, "prevTeacherOrg": 15,
        "teacherTitle": 16, "teacherName": 17, "teacherOrg": 18,
        "teacherEmail": 19, "teacherPhone": 20,
        "teachingHoursLt": 21, "teachingHoursTh": 22,
        "location": 23, "teachingMode": 24, "language": 25,
        "otherRequirements": 26, "notes": 27, "coordinatorOverride": 28,
    },
}

# O ten GV co the ghi NHIEU nguoi dong giang, ngan boi dau phay HOAC xuong dong.
_NAME_SPLIT_RE = re.compile(r"[,\n]")

# Cac o "GV" thuc ra la ghi chu dieu phoi, khong phai mot con nguoi cu the:
# "Phong Dao tao dieu phoi", "JLE dieu phoi"...
#
# KHONG duoc chi quet chu "dieu phoi": trong file that co o ghi
# "TS. Ta Quang Ngoc (dieu phoi)" - la NGUOI THAT kem ghi chu, quet thô se bo oan
# ca mot lop. Phan biet bang hoc ham/hoc vi: co TS./ThS./PGS/GS thi la nguoi.
_COORD_RE = re.compile(r"điều phối|chưa có|chưa phân|tbd|n/a", re.IGNORECASE)
_PERSON_TITLE_RE = re.compile(r"\b(gs|pgs|ts|ths|cn|bs|kts)\b\.?", re.IGNORECASE)
# Ghi chu "(dieu phoi)" dinh sau ten nguoi - cat bo de ban ghi GV sach.
_TRAILING_NOTE_RE = re.compile(r"\s*\([^)]*điều phối[^)]*\)\s*$", re.IGNORECASE)


def _is_placeholder(cell):
    """True khi o ten GV thuc ra la don vi dieu phoi chu khong phai mot ca nhan."""
    if not _COORD_RE.search(cell):
        return False
    return not _PERSON_TITLE_RE.search(cell)


def _text(v):
    if v is None:
        return ""
    s = str(v).strip()
    return "" if s.lower() in ("none", "nan") else s


def _chuan(s):
    """Chuan hoa ten de so sanh: gop moi khoang trang/xuong dong lam mot, bo hoa
    thuong. Ten hoc phan trong file co ca xuong dong giua chung
    ("Tieng Nhat so cap 1\\n(Du kien chia lam 4 lop...")."""
    return " ".join(str(s or "").split()).lower()


def _num(v):
    """Excel tra ve float cho moi so (2.0, 20.0). Tra ve int khi tron, float khi
    le, None khi o rong hoac khong phai so."""
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return int(v) if float(v).is_integer() else float(v)
    s = str(v).strip().replace(",", ".")
    if not s:
        return None
    try:
        f = float(s)
    except ValueError:
        return None
    return int(f) if f.is_integer() else f


def _nums(v):
    """Doc mot o THOI GIAN co the chua NHIEU gia tri, moi gia tri mot dong.

    File that ghi kieu: Thu='2\\n2', Tiet dau='2\\n6', Tiet cuoi='5\\n9'
    -> hai buoi: Thu 2 tiet 2-5 VA Thu 2 tiet 6-9.

    Ham _num() cu tra None cho chuoi nhu vay (float('2\\n2') loi), lam 68 dong o
    HK1 va 61 dong o HK2 MAT SACH gio va bi danh nham la "de he thong tu xep".
    """
    if v is None:
        return []
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        n = _num(v)
        return [] if n is None else [n]
    out = []
    for phan in re.split(r"[\n,;/]", str(v)):
        n = _num(phan)
        if n is not None:
            out.append(n)
    return out


def detect_layout(workbook):
    """Nhan dien dang file theo ten sheet. Tra ve (ten_sheet, layout) hoac
    (None, None) neu khong khop dang nao da biet."""
    for name, layout in LAYOUTS.items():
        if name in workbook.sheetnames:
            return name, layout
    return None, None


def read_rows(source):
    """Doc file Excel -> (ket_qua, loi).

    `source` la duong dan hoac doi tuong file-like (vd stream cua file upload).

    ket_qua = {
      "sheet":     ten sheet da dung,
      "rows":      danh sach dong chuan hoa (moi dong = 1 LOP se tao trong form),
      "skipped":   danh sach {row, reason} - dong bi bo qua va vi sao,
      "warnings":  danh sach {row, message} - dong VAN nap nhung co diem can biet,
    }

    Mot dong Excel co the sinh ra NHIEU dong ket qua: khi o thoi gian ghi nhieu
    buoi trong tuan (vd "T2 tiet 1-3, T5 tiet 6-8"), moi buoi la mot lop rieng -
    dung khai niem "1 lop hoc N buoi/tuan = N dong cung Ma lop" ma form dang dung.
    """
    try:
        wb = openpyxl.load_workbook(source, data_only=True)
    except Exception as e:  # file hong / khong phai xlsx
        return None, f"Không đọc được file Excel: {e}"

    sheet_name, layout = detect_layout(wb)
    if layout is None:
        wb.close()
        return None, (
            "Không nhận diện được định dạng file. Cần có sheet tên "
            + " hoặc ".join(f"'{n}'" for n in LAYOUTS)
            + f". Sheet đang có trong file: {', '.join(wb.sheetnames)}."
        )

    sh = wb[sheet_name]
    raw_rows = list(sh.iter_rows(min_row=layout["header_row"], values_only=True))
    wb.close()

    def col(row, key):
        idx = layout.get(key)
        if idx is None or idx >= len(row):
            return None
        return row[idx]

    rows, skipped, warnings = [], [], []
    # Excel gop o theo chieu doc cho cac cot muc hoc phan -> dong sau de trong,
    # phai nho lai gia tri dong truoc (dung cach load_real_fate_data lam).
    carry = {"courseCode": None, "courseName": None, "credits": None,
             "classCode": None, "ltCredits": None, "thCredits": None}

    for i, row in enumerate(raw_rows):
        excel_row = i + layout["header_row"]

        # Doi TEN hoc phan -> CAT ke thua truoc khi doc dong nay.
        #
        # Excel gop o theo chieu doc cho cac cot muc hoc phan, nen dong sau de
        # trong va phai nho gia tri dong truoc. Nhung co hai tinh huong khac han
        # nhau ma khong duoc gop lam mot:
        #
        #   dong 14-15  "Giai tich 1" / "Giai tich 1"  -> CUNG hoc phan, chi rieng
        #               o "So tin chi" bi gop doc  => PHAI ke thua.
        #   dong  8-9   "Triet hoc Mac-Lenin" / "Tu tuong Ho Chi Minh..." -> HAI
        #               hoc phan KHAC nhau, dong sau bo trong Ma HP/Ma lop/LT/TH
        #               => KHONG duoc ke thua, neu khong se gan nham ma PHI1006 va
        #               so gio 42/6 cua "Triet hoc" sang "Tu tuong Ho Chi Minh".
        #
        # Phan biet bang chinh TEN hoc phan: co ten rieng va KHAC ten dang nho thi
        # la hoc phan moi -> xoa sach cac gia tri dang nho.
        ten_rieng = _text(col(row, "courseName"))
        if ten_rieng and _chuan(ten_rieng) != _chuan(carry["courseName"] or ""):
            for key in carry:
                carry[key] = None

        for key in carry:
            v = col(row, key)
            v = _text(v) if key in ("courseCode", "courseName", "classCode") else _num(v)
            if v not in (None, ""):
                carry[key] = v

        teacher_cell = _text(col(row, "teacherName"))
        # O CUA CHINH dong nay (chua carry) - dung de nhan dien dong co phai mot
        # LOP THAT khong, khi o giang vien bo trong.
        ma_lop_rieng = _text(col(row, "classCode"))
        ten_hp_rieng = _text(col(row, "courseName"))

        # Dong that = co giang vien HOAC co ma lop/ten hoc phan cua rieng no.
        # Hai file deu ~850 dong trong hoan toan o duoi vung du lieu, loc bang
        # dieu kien nay thay vi chi dua vao o giang vien: rat nhieu lop THAT chua
        # phan cong giang vien (o do bo trong hoac ghi ten don vi dieu phoi),
        # nhung van la lop can nap vao form.
        if not (teacher_cell or ma_lop_rieng or ten_hp_rieng):
            continue

        # "Chua phan cong" = chua biet ai day, KHONG phai la ly do bo dong.
        # Van tao lop, chi de trong o giang vien de giao vu gan sau.
        chua_phan_cong = False
        if not teacher_cell:
            chua_phan_cong = True
            warnings.append({"row": excel_row, "kind": "chua_phan_cong", "detail": "(ô giảng viên để trống)"})
        elif _is_placeholder(teacher_cell):
            chua_phan_cong = True
            warnings.append({"row": excel_row, "kind": "chua_phan_cong", "detail": teacher_cell[:60]})
        else:
            teacher_cell = _TRAILING_NOTE_RE.sub("", teacher_cell)

        if not carry["courseName"]:
            # Khong co ten hoc phan o bat ky dong nao phia tren -> lay ma lop lam
            # ten tam de van nap duoc, thay vi vut ca dong di.
            carry["courseName"] = carry["classCode"] or ma_lop_rieng or "(chưa đặt tên học phần)"
            warnings.append({
                "row": excel_row, "kind": "thieu_ten_hoc_phan",
                "detail": f"đặt tạm là “{carry['courseName']}”",
            })

        names = [] if chua_phan_cong else [n.strip() for n in _NAME_SPLIT_RE.split(teacher_cell) if n.strip()]
        if not names:
            # Giu nguyen chu trong file ("Phong Dao tao dieu phoi"...) neu co, con
            # o trong thi ghi ro la chua phan cong.
            names = [teacher_cell.strip() or "(Chưa phân công)"]
            chua_phan_cong = True
        elif len(names) > 1:
            warnings.append({
                "row": excel_row, "kind": "dong_giang",
                "detail": f"{len(names)} người: {', '.join(names)}"[:90],
            })

        # --- Thoi gian ---
        # Layout CU co cot text tu do va da duoc xac minh la DANG TIN HON cot
        # Thu/Tiet (hai nguon nay hay lech nhau trong file goc) -> uu tien text.
        # Ghep 3 cot Thu / Tiet dau / Tiet cuoi theo VI TRI: gia tri thu k cua moi
        # cot thuoc cung mot buoi. Rieng cot Thu hay chi ghi MOT lan roi dung cho
        # ca hai buoi (vd Thu='2', Tiet dau='2\n6') - luc do lay gia tri cuoi cung
        # da doc duoc.
        thus = _nums(col(row, "thu"))
        tds = _nums(col(row, "tietDau"))
        tcs = _nums(col(row, "tietCuoi"))
        structured = []
        for k in range(max(len(thus), len(tds), len(tcs))):
            t = thus[k] if k < len(thus) else (thus[-1] if thus else None)
            d = tds[k] if k < len(tds) else None
            e = tcs[k] if k < len(tcs) else None
            if None in (t, d, e):
                continue
            structured.append((int(t) - 2, int(d), int(e)))

        sessions = []
        if layout.get("timeText") is not None:
            try:
                sessions, _ = sc._parse_time_text(col(row, "timeText"))
            except Exception:
                sessions = []
            if not sessions:
                sessions = structured
        else:
            sessions = structured

        sessions = [s for s in sessions if 0 <= s[0] <= 6 and s[1] >= 1 and s[2] >= s[1]]
        if not sessions:
            sessions = [(None, None, None)]  # chua co gio -> de thuat toan tu xep
        elif len(sessions) > 1:
            warnings.append({
                "row": excel_row, "kind": "nhieu_buoi",
                "detail": f"{len(sessions)} buổi → {len(sessions)} lớp cùng mã “{carry['classCode'] or '?'}”",
            })

        base = {
            "excelRow": excel_row,
            "courseCode": carry["courseCode"] or "",
            "courseName": carry["courseName"],
            "credits": carry["credits"],
            "classCode": carry["classCode"] or "",
            "ltCredits": carry["ltCredits"],
            "thCredits": carry["thCredits"],
            "cohort": _text(col(row, "cohort")),
            "program": _text(col(row, "program")) or "Chung",
            "expectedStudents": _num(col(row, "expectedStudents")),
            "teacherTitle": _text(col(row, "teacherTitle")),
            "teacherName": names[0],
            # Lop chua biet ai day - van nap, giao vu gan giang vien sau trong form.
            "chuaPhanCong": chua_phan_cong,
            "coTeacherNames": names[1:],
            "teacherOrg": _text(col(row, "teacherOrg")),
            "teacherEmail": _text(col(row, "teacherEmail")),
            "teacherPhone": _text(col(row, "teacherPhone")),
            "teachingHoursLt": _num(col(row, "teachingHoursLt")),
            "teachingHoursTh": _num(col(row, "teachingHoursTh")),
            "location": _text(col(row, "location")),
            "teachingMode": _text(col(row, "teachingMode")),
            "language": _text(col(row, "language")),
            "otherRequirements": _text(col(row, "otherRequirements")),
            "notes": _text(col(row, "notes")),
            "coordinatorOverride": _text(col(row, "coordinatorOverride")),
            "prevTeacherName": _text(col(row, "prevTeacherName")),
            "prevTeacherOrg": _text(col(row, "prevTeacherOrg")),
        }

        for day, p_start, p_end in sessions:
            rows.append({
                **base,
                "day": day,
                "periodStart": p_start,
                "periodEnd": p_end,
                # Chua co gio -> bat "de he thong tu xep", dung nghia o cot
                # autoSchedule cua form.
                "autoSchedule": day is None,
                "duration": (p_end - p_start + 1) if (p_start is not None and p_end is not None) else None,
            })

    return {"sheet": sheet_name, "rows": rows, "skipped": skipped, "warnings": warnings}, None


def summarize(result):
    """Tom tat de hien o buoc xem truoc, truoc khi ghi de."""
    rows = result["rows"]
    courses, teachers, programs = set(), set(), set()
    co_gio = 0
    for r in rows:
        courses.add((r["courseCode"], r["courseName"]))
        teachers.add(r["teacherName"])
        programs.add(r["program"])
        if r["day"] is not None:
            co_gio += 1
    return {
        "sheet": result["sheet"],
        "soLop": len(rows),
        "soHocPhan": len(courses),
        "soGiangVien": len(teachers),
        "soChuongTrinh": len(programs),
        "soLopDaCoGio": co_gio,
        "soLopChuaCoGio": len(rows) - co_gio,
        "soLopChuaPhanCong": sum(1 for r in rows if r.get("chuaPhanCong")),
        "soDongBoQua": len(result["skipped"]),
        "soCanhBao": len(result["warnings"]),
    }
