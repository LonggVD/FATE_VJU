# -*- coding: utf-8 -*-
"""Xuat du lieu hoc phan (STATE["data"]) ra file Excel theo dung khuon
LAYOUTS["FATE"] cua fate_import.py, de file xuat ra dung lai duoc lam van ban
chinh thuc VA nap lai duoc qua "Nhap tu Excel" o ky sau (round-trip).

Doc gan voi fate_import.py: layout cot lay tu do CHINH LAYOUTS["FATE"], khong
tu dinh nghia lai o day - them cot o fate_import.py thi export cung phai doi
theo, nhung it nhat khong lech nhau ve VI TRI cot.
"""
import io

import openpyxl

from fate_import import LAYOUTS

_LAYOUT = LAYOUTS["FATE"]
_HEADER_ROW = _LAYOUT["header_row"]  # 6: dong du lieu dau tien

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

    # Cot phu ngoai khuon FATE chuan - dat NGAY SAU cot cuoi (26 = "Phụ trách
    # nhập điểm", index0) de khong lam lech vi tri cac cot LAYOUTS dang doc.
    ws.cell(row=4, column=27, value="Trạng thái lịch (hệ thống)")


def _class_row(cls):
    """1 dong du lieu, dung DUNG vi tri cot cua LAYOUTS['FATE'] (fate_import.py)."""
    day = cls.get("day")
    row = [None] * 27
    row[_LAYOUT["courseCode"]] = cls.get("courseCode")
    row[_LAYOUT["courseName"]] = cls.get("courseName")
    row[_LAYOUT["credits"]] = cls.get("credits")
    row[_LAYOUT["classCode"]] = cls.get("classCode")
    row[_LAYOUT["ltCredits"]] = cls.get("ltCredits")
    row[_LAYOUT["thCredits"]] = cls.get("thCredits")
    row[_LAYOUT["cohort"]] = cls.get("cohort")
    row[_LAYOUT["program"]] = cls.get("program")
    row[_LAYOUT["expectedStudents"]] = cls.get("expectedStudents")
    row[_LAYOUT["thu"]] = (day + 2) if day is not None else None
    row[_LAYOUT["tietDau"]] = cls.get("periodStart")
    row[_LAYOUT["tietCuoi"]] = cls.get("periodEnd")
    row[_LAYOUT["teacherName"]] = cls.get("teacherNameRaw") or cls.get("teacherName")
    row[_LAYOUT["teacherOrg"]] = cls.get("teacherOrg")
    row[_LAYOUT["teacherEmail"]] = cls.get("teacherEmail")
    row[_LAYOUT["teacherPhone"]] = cls.get("teacherPhone")
    row[_LAYOUT["teachingHoursLt"]] = cls.get("teachingHoursLt")
    row[_LAYOUT["teachingHoursTh"]] = cls.get("teachingHoursTh")
    row[_LAYOUT["location"]] = cls.get("location")
    row[_LAYOUT["teachingMode"]] = cls.get("teachingMode")
    row[_LAYOUT["language"]] = cls.get("language")
    row[_LAYOUT["otherRequirements"]] = cls.get("otherRequirements")
    row[_LAYOUT["notes"]] = cls.get("notes")
    row[26] = _STATUS_LABELS.get(cls.get("scheduleStatus"), "")
    return row


def build_workbook(classes, semester_label):
    """classes: danh sach dict tu _build_classes_list(data) (app.py). Tra ve
    io.BytesIO da ghi xong workbook, con tro ve dau, san sang cho send_file()."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "FATE"  # de fate_import.detect_layout() nhan lai duoc file nay

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
