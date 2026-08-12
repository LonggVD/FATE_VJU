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
_PERSON_TITLE_RE = re.compile(r"\b(gs|pgs|ts|ths|cn|bs|kts|ks|kỹ sư|dr|prof)\b\.?", re.IGNORECASE)
# Manh CHI co hoc ham/hoc vi, khong co ten nguoi.
_CHI_HOC_HAM_RE = re.compile(r"^(gs|pgs|ts|ths|cn|bs|kts|ks|dr|prof)(\.\s*(gs|pgs|ts|ths))*\.?$",
                             re.IGNORECASE)
# So thu tu nguoi viet vao dau o ten (HK2 dong 178-185: "1. TS. Pham Hoai Luan").
_SO_THU_TU_RE = re.compile(r"^\d+\s*[.)]\s*")

# O "GV" thuc ra ghi mot DON VI/vai tro chung, khong phai mot ca nhan: "Khoa FATE",
# "GV Thỉnh giảng", "Chuyên gia", "Viện Toán học". Cung ban chat voi "Phòng Đào tạo
# điều phối" (_COORD_RE) nen phai xu ly nhu nhau: coi la CHUA PHAN CONG.
#
# Chi khop khi tu don vi o DAU o, KHONG co hoc ham/hoc vi, va o ngan (<=4 tu) -
# de khong bat oan nguoi that: "TS. Nguyễn Đăng Khoa" co chu "khoa" nhung co hoc vi
# va chu do khong o dau; "Chuyên gia Nguyễn Văn A" thi dai hon 4 tu.
_DON_VI_RE = re.compile(
    r"^(khoa|phòng|viện|trung tâm|bộ môn|ban|gv|giảng viên|chuyên gia|nhóm|tổ)\b",
    re.IGNORECASE)


def khoa_gv(name):
    """KHOA de gop hai ban ghi giang vien lam MOT nguoi. Bo hoc ham/hoc vi, so
    thu tu, dau cau; gop khoang trang; bo hoa/thuong; dua ve NFC.

    Vi sao khong lay nguyen ten lam khoa: file that ghi cung mot nguoi nhieu kieu
    - "PGS.TS. Nguyễn Đình Thắng" / "PGS. TS. Nguyễn Đình Thắng" (khac dau cach),
    "Tạ Kim Nhung" / "TS. Tạ Kim Nhung" (co/khong hoc ham). Moi bien the thanh mot
    ban ghi rieng -> he thong khong con thay nguoi do TRUNG LICH VOI CHINH MINH,
    dung cong dung chinh cua cong cu. Do tren file that: HK2 3 cap, HK1 6 cap,
    HK1-2 2 cap.

    KHONG gop theo email: file that co 4 truong hop mot email dung cho HAI nguoi
    khac nhau (loi copy-paste khi nhap), gop theo email se nhap 2 nguoi thanh 1.
    """
    s = _SO_THU_TU_RE.sub("", _chuan(name))
    s = _PERSON_TITLE_RE.sub(" ", s)
    return " ".join(re.sub(r"[.,;:()\-–]", " ", s).split())


def _split_names(cell):
    """Tach o ten GV thanh danh sach NGUOI. Ngan boi dau phay/xuong dong, nhung
    KHONG tach ben trong ngoac va bo cac manh chi co ghi chu.

    File that (HK2 dong 188) ghi:
        "TS. Bui Huy Kien
         ThS. Nguyen Tien Dat
         (Nhung, IoT, Robotic)"
    Tach tho theo dau phay/xuong dong ra 5 manh, trong do ba manh "(Nhung",
    "IoT", "Robotic)" khong phai nguoi. Truoc day vo hai vi chi nguoi DAU duoc
    dung; nay ca nhom deu thanh GV that co rang buoc lich nen phai loc cho dung.
    """
    parts, buf, sau = [], [], 0
    for ch in cell or "":
        if ch == "(":
            sau += 1
        elif ch == ")":
            sau = max(0, sau - 1)
        if ch in ",\n" and sau == 0:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    parts.append("".join(buf))

    out, hoc_ham_le = [], ""
    for p in parts:
        p = " ".join(p.split())
        if not p or p.startswith("("):
            continue  # manh chi la ghi chu chuyen mon, khong phai mot con nguoi
        # So thu tu nguoi nhap them vao ("1. TS. Pham Hoai Luan") khong phai mot
        # phan cua ten - de lai thi ban ghi nay khong gop voi cac dong ghi ten
        # khong danh so.
        p = _SO_THU_TU_RE.sub("", p)
        p = _TEN_GHI_CHU_RE.sub("", p).strip()
        if not p:
            continue
        # O ghi "TS, Nomura" (dau phay thay cho dau cham sau hoc vi - HK2 dong
        # 215): tach ra thi "TS" thanh mot "nguoi" rieng con "Nomura" thanh nguoi
        # thu hai. Manh chi co hoc ham/hoc vi thi ghep vao ten NGAY SAU.
        if _CHI_HOC_HAM_RE.match(p):
            hoc_ham_le = p if p.endswith(".") else p + "."
            continue
        out.append(f"{hoc_ham_le} {p}".strip() if hoc_ham_le else p)
        hoc_ham_le = ""
    return out


def _is_placeholder(cell):
    """True khi o ten GV thuc ra la don vi/vai tro chung chu khong phai ca nhan."""
    if _PERSON_TITLE_RE.search(cell):
        return False  # co hoc ham/hoc vi -> la nguoi that (co the kem ghi chu)
    if _COORD_RE.search(cell):
        return True
    return bool(_DON_VI_RE.match(cell)) and len(cell.split()) <= 4


def _text(v):
    if v is None:
        return ""
    s = str(v).strip()
    return "" if s.lower() in ("none", "nan") else s


def _chuan(s):
    """Chuan hoa ten de so sanh: gop moi khoang trang/xuong dong lam mot, bo hoa
    thuong, dua dau tieng Viet ve dang NFC. Ten hoc phan trong file co ca xuong
    dong giua chung ("Tieng Nhat so cap 1\\n(Du kien chia lam 4 lop...").

    NFC vi cung mot chu ("Khóa") co the duoc luu o hai dang Unicode khac nhau
    tuy cong cu tao file - so sanh nhan cot ma khong chuan hoa thi hai dang do
    khong khop nhau."""
    return unicodedata.normalize("NFC", " ".join(str(s or "").split()).lower())


# --- Nhan dien COT theo NHAN o hang tieu de --------------------------------
#
# Ban dau module nay map cot theo VI TRI co dinh, chon bang TEN SHEET. Da vo:
# file "FATE.TKB.HK1 2026-2027-2.xlsx" giu cau truc HK1 (co cot "TT" o dau, co
# block "GV ky truoc de doi chieu") nhung sheet duoc doi ten thanh "FATE" ->
# khop vao layout HK2 -> LECH DUNG 1 COT tu dau den cuoi (ma hoc phan thanh ten
# hoc phan, GV ky truoc thanh GV ky nay, dia diem thanh ngon ngu...) va doc tu
# dong 6 nen 2 dong tieu de bi nap thanh lop.
#
# Ten sheet va vi tri cot deu do giao vu sua moi ky, khong on dinh. NHAN cot thi
# on dinh (van la "Mã lớp học phần", "Tiết đầu"...) -> doc theo nhan.
#
# Moi cot duoc xet bang mot DUONG DAN nhan (labels tu hang tieu de tren cung
# xuong hang duoi cung), vi rieng nhan la KHONG du de phan biet:
#   "Lý thuyết" duoi "Phân bổ TC"  -> so tin chi ly thuyet
#   "Lý thuyết" duoi "Số giờ dạy"  -> so gio day ly thuyet
#   "Họ và tên" duoi "HK1 năm 2025-2026 (để đối chiếu)" -> GV KY TRUOC
_PREV_MARK_RE = re.compile(r"đối chiếu|năm ngoái|năm trước|kỳ trước|hk trước")
_LB_NAME_RE = re.compile(r"^(họ và tên|họ tên|tên gv|tên giảng viên)")
_LB_ORG_RE = re.compile(r"^(đơn vị|cơ quan) công tác")


def _hien_tai(path):
    """True khi duong dan nhan KHONG mang dau hieu 'du lieu ky truoc, de doi
    chieu' - de khong lay GV/gio cua ky truoc lam cua ky nay."""
    return not _PREV_MARK_RE.search(path)


# (ten_truong, dieu_kien(nhan_la, duong_dan)) - xet theo thu tu, cot khop rule
# nao truoc thi thuoc truong do. Truong khong tim thay cot nao thi de None va se
# ra rong trong form (giao vu dien sau), dung nhu khi thieu cot truoc day.
_COLUMN_RULES = (
    ("courseCode", lambda leaf, path: leaf == "mã học phần"),
    ("courseName", lambda leaf, path: leaf == "tên học phần"),
    ("credits", lambda leaf, path: leaf == "số tín chỉ"),
    ("classCode", lambda leaf, path: leaf == "mã lớp học phần"),
    ("ltCredits", lambda leaf, path: leaf == "lý thuyết" and "phân bổ" in path),
    ("thCredits", lambda leaf, path: leaf == "thực hành" and "phân bổ" in path),
    ("cohort", lambda leaf, path: leaf == "khóa"),
    ("program", lambda leaf, path: leaf == "ctđt"),
    ("expectedStudents", lambda leaf, path: leaf.startswith("số sv")),
    # KHONG con quy tac cho cot text tu do "Thời gian (Thứ, Tiết)": khoa xac nhan
    # do la CHO GHI CU cua cac ky truoc, du lieu bo di. Khong doc, khong doi chieu,
    # khong canh bao - dong nao thieu 3 cot Thu/Tiet dau/Tiet cuoi thi coi nhu chua
    # co gio, de thuat toan tu xep.
    ("thu", lambda leaf, path: leaf == "thứ"),
    ("tietDau", lambda leaf, path: leaf == "tiết đầu"),
    ("tietCuoi", lambda leaf, path: leaf == "tiết cuối"),
    ("teachingHoursLt", lambda leaf, path: leaf == "lý thuyết" and "số giờ" in path),
    ("teachingHoursTh", lambda leaf, path: leaf == "thực hành" and "số giờ" in path),
    ("teacherTitle", lambda leaf, path: leaf.startswith("học hàm") and _hien_tai(path)),
    ("teacherName", lambda leaf, path: _LB_NAME_RE.match(leaf) and _hien_tai(path)),
    ("teacherOrg", lambda leaf, path: _LB_ORG_RE.match(leaf) and _hien_tai(path)),
    ("teacherEmail", lambda leaf, path: leaf.startswith("email") and _hien_tai(path)),
    ("teacherPhone", lambda leaf, path: leaf in ("số điện thoại", "sđt", "điện thoại") and _hien_tai(path)),
    ("prevTeacherName", lambda leaf, path: _LB_NAME_RE.match(leaf) and not _hien_tai(path)),
    ("prevTeacherOrg", lambda leaf, path: _LB_ORG_RE.match(leaf) and not _hien_tai(path)),
    ("location", lambda leaf, path: leaf.startswith("địa điểm")),
    ("teachingMode", lambda leaf, path: leaf.startswith("hình thức")),
    ("language", lambda leaf, path: leaf.startswith("ngôn ngữ")),
    ("otherRequirements", lambda leaf, path: leaf.startswith("yêu cầu khác") or leaf.startswith("đề xuất")),
    ("notes", lambda leaf, path: leaf.startswith("ghi chú") or leaf.startswith("phụ trách nhập điểm")),
    ("coordinatorOverride", lambda leaf, path: "điều phối" in leaf and ("giảng viên" in leaf or leaf.startswith("gv"))),
)

FIELDS = tuple(dict.fromkeys(f for f, _ in _COLUMN_RULES))

# Cot BAT BUOC phai tim thay, kem nhan de bao loi cho nguoi dung. Thieu mot
# trong so nay thi khong phai bang du lieu hoc phan (vd sheet "Thống kê số lớp
# HP" cung co cot "Mã học phần") -> bao loi thay vi nap ra du lieu rac.
_REQUIRED = (
    ("courseName", "Tên học phần"),
    ("classCode", "Mã lớp học phần"),
    ("teacherName", "Họ và tên giảng viên"),
)

# Trong block thong tin GV, khi CO NHIEU cot cung khop mot truong (file HK1 co
# hai cap "Họ và tên / Đơn vị công tác": ky truoc va ky nay) thi lay cot BEN
# PHAI. Dau hieu chinh de loai cot ky truoc van la _PREV_MARK_RE; day chi la
# luoi do thu hai cho truong hop file khong ghi "(để đối chiếu)" nua - theo
# khuon file that, du lieu de doi chieu nam BEN TRAI, du lieu ky nay ben phai.
_TEACHER_FIELDS = frozenset({
    "teacherTitle", "teacherName", "teacherOrg", "teacherEmail", "teacherPhone",
})

# Nhan hay gap o hang tieu de - dung de nhan ra "hang nay chi gom nhan, chua
# phai du lieu" (xem _header_bottom).
_HEADER_LABEL_RE = re.compile(
    r"^(tt|stt|mã |tên |số |phân bổ|lý thuyết|thực hành|tự học|khóa|ctđt|thời gian"
    r"|thứ|tiết |họ |đơn vị|cơ quan|học hàm|email|sđt|điện thoại|địa điểm|hình thức"
    r"|ngôn ngữ|yêu cầu|ghi chú|đề xuất|phụ trách|giảng viên|gv |trạng thái)"
)

_HEADER_SCAN_ROWS = 20  # so dong dau file de tim hang tieu de
_HEADER_MAX_DEPTH = 3   # tieu de sau nhat da gap: 3 hang (nhom / nhom con / la)


def _find_header_top(sh):
    """Hang tieu de TREN CUNG = hang co o ghi dung "Mã học phần" (cot dau tien
    cua bang o ca hai khuon file da gap). None neu khong thay."""
    for r in range(1, min(sh.max_row, _HEADER_SCAN_ROWS) + 1):
        for c in range(1, sh.max_column + 1):
            if _chuan(sh.cell(row=r, column=c).value) == "mã học phần":
                return r
    return None


def _is_label_row(sh, r):
    """True khi hang chi gom NHAN: khong o nao la so, va co it nhat 3 nhan quen
    biet. Dong du lieu luon co so (so tin chi, so SV, thu, tiet...) nen day la
    ranh gioi du chac giua vung tieu de va vung du lieu."""
    dem = 0
    for c in range(1, sh.max_column + 1):
        v = sh.cell(row=r, column=c).value
        if v is None:
            continue
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return False
        if _HEADER_LABEL_RE.match(_chuan(v)):
            dem += 1
    return dem >= 3


def _header_bottom(sh, top):
    """Hang tieu de DUOI CUNG (hang nhan la). Lay xa nhat trong hai dau hieu:

      - o gop DOC bat dau tu hang `top` (file that gop "Số tín chỉ" D5:D7...);
      - hang chi gom nhan nam ngay duoi (file do CHINH webapp xuat ra khong gop
        o nao ca - xem fate_export.py - nhung van co hang nhan la o duoi).

    Can ca hai vi moi dau hieu rieng le deu thieu voi mot trong hai loai file.
    """
    bottom = top
    for mr in sh.merged_cells.ranges:
        if mr.min_row == top:
            bottom = max(bottom, mr.max_row)
    for r in range(top + 1, min(top + _HEADER_MAX_DEPTH, sh.max_row) + 1):
        if _is_label_row(sh, r):
            bottom = max(bottom, r)
    return min(bottom, top + _HEADER_MAX_DEPTH)


def _label_grid(sh, top, bottom):
    """Luoi nhan da chuan hoa cua vung tieu de [top..bottom] x [moi cot]."""
    ncol = sh.max_column
    grid = [[_chuan(sh.cell(row=r, column=c).value) for c in range(1, ncol + 1)]
            for r in range(top, bottom + 1)]

    # Bung o gop: openpyxl chi tra gia tri o o goc tren-trai, phan con lai None.
    for mr in sh.merged_cells.ranges:
        if mr.max_row < top or mr.min_row > bottom:
            continue
        val = _chuan(sh.cell(row=mr.min_row, column=mr.min_col).value)
        if not val:
            continue
        for r in range(max(mr.min_row, top), min(mr.max_row, bottom) + 1):
            for c in range(mr.min_col, min(mr.max_col, ncol) + 1):
                grid[r - top][c - 1] = val

    # Nhan NHOM co the chi ghi o o dau nhom, cac o sau de trong ma KHONG gop o
    # (file webapp xuat ra la vay) -> keo nhan sang phai.
    # Chi lam voi cac hang NHOM, KHONG lam voi hang nhan la duoi cung: o trong o
    # hang do nghia la "cot nay khong co nhan rieng", keo sang se de nhan cua
    # cot khac len (nhan "Thực hành" tran sang cot "Khóa").
    for i in range(len(grid) - 1):
        for c in range(1, ncol):
            if grid[i][c] or not grid[i][c - 1]:
                continue
            # Chi keo trong pham vi mot nhom cha: hang tren cung khong co cha nen
            # keo tu do, hang duoi chi keo khi o ben trai CUNG cha voi o nay.
            if i == 0 or grid[i - 1][c] == grid[i - 1][c - 1]:
                grid[i][c] = grid[i][c - 1]
    return grid


def read_layout(sh):
    """Doc ban do COT -> truong cua form tu chinh hang tieu de cua sheet.

    Tra ve dict {ten_truong: chi_so_cot_0based | None} kem "firstDataRow" va
    "headerRows"; None neu sheet khong co hang tieu de nhan ra duoc.

    Khoa dat trung ten field trong body JSON cua POST /api/manual/section, de
    app.py chi viec chuyen tiep.
    """
    top = _find_header_top(sh)
    if top is None:
        return None
    bottom = _header_bottom(sh, top)
    grid = _label_grid(sh, top, bottom)

    layout = dict.fromkeys(FIELDS)
    layout["firstDataRow"] = bottom + 1
    layout["headerRows"] = (top, bottom)
    for c in range(len(grid[0])):
        labels = [grid[r][c] for r in range(len(grid))]
        leaf = next((l for l in reversed(labels) if l), "")
        if not leaf:
            continue
        # Duong dan nhan tu tren xuong, bo cac nhan lap lai lien tiep do bung o
        # gop doc ("Số tín chỉ | Số tín chỉ | Số tín chỉ").
        path_parts = []
        for l in labels:
            if l and (not path_parts or path_parts[-1] != l):
                path_parts.append(l)
        path = " | ".join(path_parts)
        for field, khop in _COLUMN_RULES:
            if not khop(leaf, path):
                continue
            if layout[field] is None or field in _TEACHER_FIELDS:
                layout[field] = c
            break
    return layout


def _missing_required(layout):
    """Nhan cua cac cot bat buoc ma khong tim thay trong hang tieu de."""
    thieu = [nhan for field, nhan in _REQUIRED if layout.get(field) is None]
    # Nguon gio DUY NHAT: 3 cot cau truc. Thieu chung thi ca file khong lop nao co
    # gio - bao loi ngay o buoc xem truoc con hon nap ra 300 lop deu "chua co gio".
    if any(layout.get(k) is None for k in ("thu", "tietDau", "tietCuoi")):
        thieu.append("Thời gian (Thứ / Tiết đầu / Tiết cuối)")
    return thieu


def detect_sheet(wb):
    """Chon sheet du lieu va doc ban do cot cua no -> (ten_sheet, layout, loi).

    Uu tien sheet co chu "FATE" trong ten: file that con co sheet cua khoa khac
    ("Giảng dạy cho BJS") va cac sheet phu ("Thống kê số lớp HP", "HP ở MĐ cần
    thực hành...") - nhung sheet do CUNG co cot "Mã học phần"/"Tên học phần" nen
    khong loc theo ten thi rat de doc dung sheet sai.
    """
    uu_tien = [n for n in wb.sheetnames if "fate" in _chuan(n)]
    da_thu = []
    for name in uu_tien or wb.sheetnames:
        layout = read_layout(wb[name])
        if layout is None:
            da_thu.append((name, "không thấy hàng tiêu đề nào có ô “Mã học phần”"))
            continue
        thieu = _missing_required(layout)
        if not thieu:
            return name, layout, None
        da_thu.append((name, "thiếu cột " + ", ".join(f"“{t}”" for t in thieu)))

    chi_tiet = "; ".join(f"sheet “{n}”: {ly_do}" for n, ly_do in da_thu)
    return None, None, (
        "Không tìm thấy bảng dữ liệu học phần trong file. "
        + (chi_tiet or "File không có sheet nào.")
        + ". Cần một sheet có hàng tiêu đề với các cột “Mã học phần”, "
        "“Tên học phần”, “Mã lớp học phần”, “Họ và tên giảng viên” và "
        "“Thứ / Tiết đầu / Tiết cuối”."
    )


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


def _text_sessions(row, layout, col):
    """Buoi doc duoc tu cot text tu do (rong neu layout khong co cot nay hoac
    khong parse duoc gi) - tach rieng khoi _structured_sessions() de so sanh
    hai nguon truoc khi quyet dinh dung nguon nao (xem _group_time_overrides)."""
    if layout.get("timeText") is None:
        return []
    try:
        sessions, _ = sc._parse_time_text(col(row, "timeText"))
    except Exception:
        sessions = []
    return sessions or []


def _structured_sessions(row, layout, col):
    """Buoi doc duoc tu 3 cot Thu/Tiet dau/Tiet cuoi, ghep theo VI TRI (xem chi
    thich chi tiet o _group_time_overrides/read_rows)."""
    thus = _nums(col(row, "thu"))
    tds = _nums(col(row, "tietDau"))
    tcs = _nums(col(row, "tietCuoi"))
    out = []
    for k in range(max(len(thus), len(tds), len(tcs))):
        t = thus[k] if k < len(thus) else (thus[-1] if thus else None)
        d = tds[k] if k < len(tds) else None
        e = tcs[k] if k < len(tcs) else None
        if None in (t, d, e):
            continue
        out.append((int(t) - 2, int(d), int(e)))
    return out


_DAY_LABELS_VN = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]

# Tiet lon nhat con TIN DUOC. He thong khong con chot cung 12 tiet/ngay: app.py noi
# slotsPerDay theo tiet lon nhat gap trong file (file HK1 2026-2027-2 dung tiet 13),
# nen "ngoai pham vi" chi con nghia la gia tri VO LY - gan nhu chac chan go sai.
#
# 16 vi mot ngay hoc toi da la sang (1-5) + chieu (6-10) + toi (11-15); ghi tiet 20
# hay 99 thi khong the la gio hoc that, ma noi slotsPerDay theo do se phong to mo
# hinh solver vo ich (moi tiet x 7 ngay).
MAX_TIET = 16


def _session_label(session):
    day, p_start, p_end = session
    if day is None:
        return "chưa có giờ"
    return f"{_DAY_LABELS_VN[day]}, tiết {p_start}-{p_end}"


def _sessions_label(sessions):
    """Nhan cho CA DANH SACH buoi - mot o gio co the ghi nhieu buoi/tuan, va man
    "Xac nhan gio hoc" phai noi ro moi ben ghi may buoi (truoc day chi hien duoc
    truong hop 1 buoi nen dong nhieu buoi khong bao gio hien ra).

    Buoi vuot pham vi tiet duoc ghi ro NGAY TREN NHAN: giao vu bam chon nguon o
    man do, phai thay truoc hau qua chu khong bam roi moi biet lop mat gio."""
    if not sessions:
        return "không có giờ"
    nhan = " + ".join(_session_label(s) for s in sessions)
    if any(s[2] > MAX_TIET for s in sessions):
        nhan += f" (tiết > {MAX_TIET}, nghi gõ sai — sẽ phải để hệ thống tự xếp)"
    return nhan


def _hop_le(sessions):
    """Bo cac buoi khong dung duoc (thu ngoai 0-6, tiet <1, tiet cuoi < tiet dau).

    Loc NGAY khi doc tung nguon, truoc khi so sanh/chon nguon: co dong ghi rac o
    mot nguon, neu chi loc SAU khi chon thi lop mat sach gio du nguon con lai co
    gio dung.

    CO Y khong loc buoi vuot MAX_TIET o day: gia tri do van phai hien o man "Xac
    nhan gio hoc" de giao vu doi chieu voi file (file HK1-2 dong 280/281 ghi tiet
    11-13). Cho nao chiu no la app._parse_class_time - coi nhu chua co gio."""
    return [s for s in sessions if 0 <= s[0] <= 6 and s[1] >= 1 and s[2] >= s[1]]


def read_rows(source):
    """Doc file Excel -> (ket_qua, loi).

    `source` la duong dan hoac doi tuong file-like (vd stream cua file upload).

    ket_qua = {
      "sheet":       ten sheet da dung,
      "rows":        danh sach dong chuan hoa (moi dong = 1 LOP se tao trong form),
      "skipped":     danh sach {row, reason} - dong bi bo qua va vi sao,
      "warnings":    danh sach {row, message} - dong VAN nap nhung co diem can biet,
      "timeReviews": danh sach lop co 2 nguon gio (text/cau truc) khac nhau -
                     "buoc 1: chuan hoa du lieu" o UI, giao vu xem/doi chieu
                     source dang dung TRUOC khi nap (buoc 2) - xem
                     app.py: api_manual_import_apply_time_fix.
    }

    Mot dong Excel co the sinh ra NHIEU dong ket qua: khi o thoi gian ghi nhieu
    buoi trong tuan (vd "T2 tiet 1-3, T5 tiet 6-8"), moi buoi la mot lop rieng -
    dung khai niem "1 lop hoc N buoi/tuan = N dong cung Ma lop" ma form dang dung.
    """
    try:
        wb = openpyxl.load_workbook(source, data_only=True)
    except Exception as e:  # file hong / khong phai xlsx
        return None, f"Không đọc được file Excel: {e}"

    sheet_name, layout, err = detect_sheet(wb)
    if err:
        wb.close()
        return None, err

    sh = wb[sheet_name]
    first_data_row = layout["firstDataRow"]
    raw_rows = list(sh.iter_rows(min_row=first_data_row, values_only=True))
    wb.close()

    def col(row, key):
        idx = layout.get(key)
        if idx is None or idx >= len(row):
            return None
        return row[idx]

    rows, skipped, warnings, time_reviews = [], [], [], []
    # Excel gop o theo chieu doc cho cac cot muc hoc phan -> dong sau de trong,
    # phai nho lai gia tri dong truoc (dung cach load_real_fate_data lam).
    carry = {"courseCode": None, "courseName": None, "credits": None,
             "classCode": None, "ltCredits": None, "thCredits": None}

    # Xem truoc ca file 1 luot (chi de nhom hoc phan + so sanh 2 nguon gio) -
    # PHAI lam TRUOC vong chinh vi can biet ca cac dong "anh em" phia sau moi
    # nhom moi ket luan duoc nguon nao dang tin (xem _group_time_overrides).
    group_ids = _course_group_ids(raw_rows, col)
    time_overrides = _group_time_overrides(raw_rows, layout, col, group_ids)

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

        if not carry["courseName"]:
            # Khong co ten hoc phan o bat ky dong nao phia tren -> lay ma lop lam
            # ten tam de van nap duoc, thay vi vut ca dong di.
            carry["courseName"] = carry["classCode"] or ma_lop_rieng or "(chưa đặt tên học phần)"
            warnings.append({
                "row": excel_row, "kind": "thieu_ten_hoc_phan",
                "detail": f"đặt tạm là “{carry['courseName']}”",
            })

        names = [] if chua_phan_cong else _split_names(teacher_cell)
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
        # Thu/Tiet (hai nguon nay hay lech nhau trong file goc) -> uu tien text
        # theo MAC DINH khi khong co dau hieu nao khac. Ghep 3 cot Thu / Tiet
        # dau / Tiet cuoi theo VI TRI: gia tri thu k cua moi cot thuoc cung mot
        # buoi. Rieng cot Thu hay chi ghi MOT lan roi dung cho ca hai buoi (vd
        # Thu='2', Tiet dau='2\n6') - luc do lay gia tri cuoi cung da doc duoc.
        text_sessions = _text_sessions(row, layout, col)
        structured = _structured_sessions(row, layout, col)

        # Nhom hoc phan nay co dau hieu 1 trong 2 cot bi "quen sua" khi copy
        # dong tao lop thu 2 (xem _group_time_overrides) -> DAO nguoc uu tien
        # cho DUNG cac dong lien quan, danh dau certain=True (he thong CHAC).
        # Cac dong lech khac (khong co dau hieu ro) van duoc dua vao
        # time_reviews (certain=False, van dung MAC DINH cu) - giao vu XEM va
        # SUA truoc khi nap, thay vi am tham tin 1 ben nhu ban dau.
        override = time_overrides.get(group_ids[i])
        chosen_source = override or ("text" if text_sessions else "structured")

        # CHI xet lech khi CA HAI nguon co DUNG 1 buoi (bo qua truong hop nhieu
        # buoi/o - hiem va phuc tap hoa man xem lai khong dang) VA hai gia tri
        # THUC SU khac nhau.
        if len(text_sessions) == 1 and len(structured) == 1 and text_sessions[0] != structured[0]:
            time_reviews.append({
                "excelRow": excel_row,
                "classCode": carry["classCode"] or "",
                "courseName": carry["courseName"],
                "teacherName": names[0],
                "chosen": chosen_source,
                "certain": override is not None,
                "text": {"day": text_sessions[0][0], "periodStart": text_sessions[0][1], "periodEnd": text_sessions[0][2]},
                "structured": {"day": structured[0][0], "periodStart": structured[0][1], "periodEnd": structured[0][2]},
                "textLabel": _session_label(text_sessions[0]),
                "structuredLabel": _session_label(structured[0]),
            })
            warnings.append({
                "row": excel_row, "kind": "lech_nguon_gio",
                "detail": (
                    f"2 nguồn giờ khác nhau — cột text: {_session_label(text_sessions[0])}; "
                    f"cột cấu trúc: {_session_label(structured[0])}. Đang dùng "
                    f"{'cột cấu trúc' if chosen_source == 'structured' else 'cột text'}"
                    + (" (đã tự phát hiện trùng lặp)" if override is not None else " (mặc định — cần xem lại ở bước xem trước)")
                ),
            })

        if chosen_source == "structured" and structured:
            sessions = structured
        elif text_sessions:
            sessions = text_sessions
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

        # Tiet VO LY (> MAX_TIET). Bao tu day (buoc xem truoc) chu khong de
        # app._parse_class_time bao "Thu/Tiet khong hop le" - o luong nap file, loi
        # do lam RUNG CA LOP (mat GV/SV/hoc phan), xem chu thich o _parse_class_time.
        ngoai = [s for s in sessions if s[2] is not None and s[2] > MAX_TIET]
        if ngoai:
            warnings.append({
                "row": excel_row, "kind": "gio_ngoai_pham_vi_tiet",
                "detail": (f"{_sessions_label(ngoai)} — tiết lớn hơn {MAX_TIET} thì "
                           f"không thể là giờ học thật, lớp này chuyển sang "
                           f"“để hệ thống tự xếp”"),
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
            # GV dong giang: TUNG NGUOI mot, kem email/SDT cua rieng ho khi tach
            # duoc. app.py tao ban ghi GV that cho ca nhom va dua het vao
            # section["teacher_ids"] - solver ap NoOverlap cho tat ca (xem
            # scheduler_core.solve_*: mot interval, nhieu nguoi).
            "coTeacherNames": names[1:],
            "coTeacherEmails": [_phan(emails, k) for k in range(1, len(names))],
            "coTeacherPhones": [_phan(phones, k) for k in range(1, len(names))],
            "coTeacherOrgs": [_phan(orgs, k) for k in range(1, len(names))],
            "teacherOrg": orgs[0] if orgs else org_cell,
            # Tach duoc thi GV chinh lay phan dau, khong tach duoc thi giu NGUYEN
            # ca o (khong doan bua) - dung nhu truoc day.
            "teacherEmail": emails[0] if emails else email_cell,
            "teacherPhone": phones[0] if phones else phone_cell,
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

    return {
        "sheet": sheet_name, "rows": rows, "skipped": skipped, "warnings": warnings,
        "timeReviews": time_reviews,
    }, None


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
