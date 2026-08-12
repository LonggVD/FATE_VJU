# -*- coding: utf-8 -*-
"""Xuat du lieu hoc phan (STATE["data"]) ra file Excel theo dung khuon file mau
thuc FATE.TKB.HK2_2025-2026.xlsx, de file xuat ra dung lai duoc lam van ban
chinh thuc VA nap lai duoc qua "Nhap tu Excel" o ky sau (round-trip).

Rang buoc voi fate_import.py chi con la NHAN cot, khong phai vi tri: import doc
ban do cot tu chinh hang tieu de (xem fate_import.read_layout), nen doi thu tu
cot o day khong lam import doc lech nua - mien la cac nhan o _set_header() giu
nguyen cach viet. Doi NHAN thi phai doi _COLUMN_RULES ben fate_import.py.
"""
import io

import openpyxl

# Vi tri cot cua khuon FATE chuan (0based), dung cho ca _set_header va _class_row.
_COL = {
    "courseCode": 0, "courseName": 1, "credits": 2, "classCode": 3,
    "ltCredits": 4, "thCredits": 5,
    "cohort": 7, "program": 8, "expectedStudents": 9,
    "thu": 11, "tietDau": 12, "tietCuoi": 13,
    "teacherName": 14, "teacherOrg": 15, "teacherEmail": 16, "teacherPhone": 17,
    "teachingHoursLt": 18, "teachingHoursTh": 19,
    "location": 21, "teachingMode": 22, "language": 23,
    "otherRequirements": 24, "notes": 25,
}
_HEADER_ROW = 6  # dong du lieu dau tien (2 dong tieu de: 4 va 5)

_STATUS_LABELS = {
    "scheduled": "Đã xếp",
    "problem": "Có vấn đề",
    "missing": "Chưa có giờ",
}


def _set_header(ws, semester_label):
    """Dung lai dung 5 dong tieu de doc duoc tu file mau thuc
    FATE.TKB.HK2_2025-2026.xlsx (sheet 'FATE'), chi thay chuoi hoc ky/nam hoc."""
    ws["A1"] = "TRƯỜNG ĐẠI HỌC VIỆT NHẬT\n KHOA CÔNG NGHỆ VÀ KỸ THUẬT TIÊN TIẾN"
    ws["E2"] = f"THỜI KHÓA BIỂU {semester_label}".strip()
    ws["A3"] = "I. Giảng dạy cho Khoa FATE"

    row4 = [
        "Mã học phần", "Tên học phần", "Số tín chỉ", "Mã lớp học phần", "Phân bổ TC",
        None, None, "Khóa", "CTĐT", "Số SV tối đa\n theo lớp HP",
        "Thời gian (Thứ, Tiết) - NĂM NGOÁI", "Thời gian", None, None,
        "GV phụ trách  (Yêu cầu các CTĐT điền đầy đủ thông tin cho HK này)",
        None, None, None,
        "Số giờ thực dạy (Đối với HP có từ 2GV trở lên, yêu cầu điền đầy đủ số giờ mỗi người)",
        None, None,
        "Địa điểm giảng dạy\n(Nếu lớp có fieldtrip đề nghị ghi rõ)",
        "Hình thức giảng dạy", "Ngôn ngữ giảng dạy", "Đề xuất hỗ trợ", "Phụ trách nhập điểm",
    ]
    for col0, val in enumerate(row4):
        if val is not None:
            ws.cell(row=4, column=col0 + 1, value=val)

    row5 = [
        None, None, None, None, "Lý thuyết", "Thực hành", "Tự học", None, None, None, None,
        "Thứ", "Tiết đầu", "Tiết cuối", "Họ tên GV", "Đơn vị công tác", "Email", "Số điện thoại",
        "Lý thuyết", "Thực hành", "Tự học", None, None, None, None, None,
    ]
    for col0, val in enumerate(row5):
        if val is not None:
            ws.cell(row=5, column=col0 + 1, value=val)

    # Cot phu ngoai khuon FATE chuan - dat NGAY SAU cot cuoi (25 = "Phụ trách
    # nhập điểm", index0) de khong chen giua cac cot cua khuon.
    ws.cell(row=4, column=27, value="Trạng thái lịch (hệ thống)")


def _class_row(cls):
    """1 dong du lieu, dat dung vi tri cot cua khuon FATE (_COL)."""
    day = cls.get("day")
    row = [None] * 27
    row[_COL["courseCode"]] = cls.get("courseCode")
    row[_COL["courseName"]] = cls.get("courseName")
    row[_COL["credits"]] = cls.get("credits")
    row[_COL["classCode"]] = cls.get("classCode")
    row[_COL["ltCredits"]] = cls.get("ltCredits")
    row[_COL["thCredits"]] = cls.get("thCredits")
    row[_COL["cohort"]] = cls.get("cohort")
    # CTDT: ghi TEN nhu trong file goc ("BCSE+MJM"), khong phai cls["program"] -
    # truong do la program_id (mot SO), truoc day bi ghi thang ra file nen ca cot
    # CTDT trong ban xuat chi toan 0/1/2... va nap lai thi ra cac "chuong trinh"
    # ten "0", "1". programName giu nguyen van o trong file (xem app.py:
    # _build_classes_list / section['program_raw']).
    row[_COL["program"]] = cls.get("programName") or cls.get("program")
    row[_COL["expectedStudents"]] = cls.get("expectedStudents")
    row[_COL["thu"]] = (day + 2) if day is not None else None
    row[_COL["tietDau"]] = cls.get("periodStart")
    row[_COL["tietCuoi"]] = cls.get("periodEnd")
    # NHIEU GIANG VIEN: ghi lai CA NHOM vao mot o, dung khuon file goc
    # ("A, B, C") - de nap lai file thi fate_import tach ra dung tung nguoi. Chi
    # ghi nguoi dau thi moi lan xuat/nap lai se rung dan nhung nguoi con lai.
    nhom = cls.get("teachers") or []
    ten = [t.get("name") for t in nhom] or [cls.get("teacherNameRaw") or cls.get("teacherName")]
    email = [t.get("email") for t in nhom] or [cls.get("teacherEmail")]
    # SDT ghep GIONG email: fate_import tach hai o nay theo VI TRI so voi danh
    # sach ten (_split_aligned), nen ghi mot so cho ca nhom la nhap lai mat het
    # so cua nhung nguoi con lai.
    phone = [t.get("phone") for t in nhom] or [cls.get("teacherPhone")]
    row[_COL["teacherName"]] = ", ".join(t for t in ten if t)
    # Don vi cong tac thi KHONG ghep: khuon file chi co MOT o cho ca nhom, ghep
    # bang dau phay thi nap lai se thanh mot chuoi dai lam don vi cua moi nguoi.
    row[_COL["teacherOrg"]] = cls.get("teacherOrg")
    row[_COL["teacherEmail"]] = ", ".join(e for e in email if e)
    row[_COL["teacherPhone"]] = ", ".join(p for p in phone if p)
    row[_COL["teachingHoursLt"]] = cls.get("teachingHoursLt")
    row[_COL["teachingHoursTh"]] = cls.get("teachingHoursTh")
    row[_COL["location"]] = cls.get("location")
    row[_COL["teachingMode"]] = cls.get("teachingMode")
    row[_COL["language"]] = cls.get("language")
    row[_COL["otherRequirements"]] = cls.get("otherRequirements")
    row[_COL["notes"]] = cls.get("notes")
    row[26] = _STATUS_LABELS.get(cls.get("scheduleStatus"), "")
    return row


_ISSUE_HEADER = ["Mức", "Loại vấn đề", "Chi tiết", "Số dòng liên quan", "Dòng trong file Excel"]
_ISSUE_MUC = {"nghiem_trong": "Nghi SAI", "luu_y": "Nên rà lại"}


def build_issues_workbook(data_issues, file_name=""):
    """Xuat danh sach loi du lieu (fate_audit.kiem_tra) ra .xlsx de gui khoa sua
    tai NGUON.

    Vi sao can file rieng thay vi doc tren man hinh: nhung loi nay (ma hoc phan
    sai, ten khac dau, mot email 2 nguoi...) chi sua duoc o FILE GOC, ma nguoi sua
    la khoa/CTDT chu khong phai nguoi dang bam nhap. Ho can mot danh sach mo bang
    Excel duoc, co so dong de nhay den, khong phai anh chup man hinh.

    Moi TRUONG HOP mot dong (khong phai moi nhom mot dong) - nguoi sua di theo
    tung truong hop cu the.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Loi du lieu"
    ws.append(_ISSUE_HEADER)
    for g in data_issues or []:
        muc = _ISSUE_MUC.get(g.get("muc"), g.get("muc") or "")
        ct = g.get("chiTiet") or [{"text": "", "so": g.get("so"), "dong": g.get("dong")}]
        for c in ct:
            dong = c.get("dong") or g.get("dong") or []
            ws.append([muc, g.get("nhan"), c.get("text"), c.get("so"),
                       ", ".join(str(x) for x in dong)])
    for cot, rong in zip("ABCDE", (12, 62, 80, 16, 40)):
        ws.column_dimensions[cot].width = rong
    ws.freeze_panes = "A2"
    if file_name:
        ws.append([])
        ws.append(["", f"Nguồn: {file_name}"])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


def build_workbook(classes, semester_label):
    """classes: danh sach dict tu _build_classes_list(data) (app.py). Tra ve
    io.BytesIO da ghi xong workbook, con tro ve dau, san sang cho send_file()."""
    wb = openpyxl.Workbook()
    ws = wb.active
    # fate_import.detect_sheet() uu tien sheet co chu "FATE" trong ten - dat ten
    # nay de nap lai file thi chon dung sheet du lieu.
    ws.title = "FATE"

    _set_header(ws, semester_label)

    for i, cls in enumerate(classes):
        excel_row = _HEADER_ROW + i
        for col0, val in enumerate(_class_row(cls)):
            if val is not None:
                ws.cell(row=excel_row, column=col0 + 1, value=val)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf
