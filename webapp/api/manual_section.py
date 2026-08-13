# -*- coding: utf-8 -*-
"""LOP HOC PHAN nhap tay: them, sua, xoa."""

from flask import Blueprint, request

from api.common import can_du_lieu, loi, tra_du_lieu
from domain.chot import khoa_vi_da_chot
from domain.hoc_chung import don_nhom_hong, kiem_tra_sua_lop
from domain.luoi import dong_bo_ket_qua
from domain.pinning import ghim_theo_gio_form, lan_gio_sang_nhom
from domain.sections import don_ma_lop_sau_xoa, id_moi, validate_section_body
from domain.time_rules import apply_section_time
from snapshot import save_snapshot
from state import STATE

bp = Blueprint("manual_section", __name__)


@bp.post("/api/manual/section")
@can_du_lieu
def api_manual_add_section(data):
    """Them 1 lop (section) nhap tay, gan cho danh sach GV + 1 hoc phan da co san.
    Body JSON: xem sections.validate_section_body() - gom teacherIds, courseId,
    duration, cac field mirror 29 cot Excel.
    - room_type suy tu thCredits>0 -> LAB, nguoc lai LT.
    - Gio da CHOT (day+periodStart+periodEnd) -> submissions rut ve DUNG 1 slot
      (xem time_rules.apply_section_time). Tick autoSchedule/de trong ca 3 ->
      xep theo khung gio ranh da khai bao, chua ai khai thi tu do ca tuan."""
    body = request.get_json(force=True)

    fields, teacher, duration, time_info, err = validate_section_body(data, body)
    if err:
        return loi(err)

    sid = id_moi(data["sections"])
    data["sections"][sid] = {"id": sid, **fields}
    apply_section_time(data, sid, teacher, duration, time_info)
    ghim_theo_gio_form(data, sid, time_info)

    # Lop moi co gio co dinh phai hien tren luoi Thoi khoa bieu NGAY - khong thi
    # giao vu them lop xong sang man TKB khong thay gi va tuong minh chua luu.
    dong_bo_ket_qua(data, [sid])
    save_snapshot()
    return tra_du_lieu(data)


@bp.patch("/api/manual/section/<int:section_id>")
@can_du_lieu
def api_manual_update_section(data, section_id):
    """Sua 1 lop da nhap - body cung dinh dang day du nhu POST /api/manual/section
    (khong merge tung phan, xem ly do o sections.validate_section_body).

    Luu y: `teacherIds` phai gui DAY DU ca danh sach. Gui thieu = nhung nguoi con
    lai bi bo khoi lop - dung y nghia "gui du ca form", nhung de sot thi mat du
    lieu am tham."""
    if section_id not in data["sections"]:
        return loi(f"Không tìm thấy lớp id={section_id}.")
    body = request.get_json(force=True)

    fields, teacher, duration, time_info, err = validate_section_body(data, body)
    if err:
        return loi(err)

    # HOC CHUNG: sua so tiet/loai phong/giai doan cua MOT thanh vien lam nhom khong
    # con la mot buoi day - tu choi, bat tach nhom truoc (xem kiem_tra_sua_lop).
    pha_nhom = kiem_tra_sua_lop(data, section_id, fields)
    if pha_nhom:
        return loi(pha_nhom, 409, hocChungLocked=True)

    # Chan SAU khi validate: chi tu choi khi yeu cau nay lam DOI gio cua mot lop
    # thuoc hoc phan da chot (hoac hoc chung voi mot lop thuoc mon da chot - xem
    # domain/chot.py). Sua ten GV/email/dia diem... van cho qua.
    khoa = khoa_vi_da_chot(data, section_id, time_info)
    if khoa:
        return loi(khoa, 409, locked=True)

    data["sections"][section_id].update(fields)
    apply_section_time(data, section_id, teacher, duration, time_info)
    ghim_theo_gio_form(data, section_id, time_info)
    # HOC CHUNG la MOT buoi -> cac lop cung nhom phai sang dung gio moi.
    cung_nhom = lan_gio_sang_nhom(data, section_id, time_info)

    # Gio/GV/hoc phan cua lop vua doi -> luoi Thoi khoa bieu phai theo. Truyen
    # section_id vao bo_vi_tri_cu: gio vua go tay thang vi tri cu tren luoi.
    dong_bo_ket_qua(data, [section_id, *cung_nhom])
    save_snapshot()
    return tra_du_lieu(data)


@bp.delete("/api/manual/section/<int:section_id>")
@can_du_lieu
def api_manual_delete_section(data, section_id):
    """Xoa 1 lop nhap nham - don luon submissions/pending_section_ids/overrides
    lien quan de khong con tham chieu treo den sectionId da mat.

    dong_bo_ket_qua() don CA guestResult/residentResult dang cache (neu da giai
    truoc do) - khong lam vay thi lop da xoa van con hien "ma" tren luoi Thoi khoa
    bieu cho toi khi giai lai, vi 2 ket qua nay la snapshot rieng, khong tu dong
    doc lai data['sections'] moi lan render."""
    if section_id not in data["sections"]:
        return loi(f"Không tìm thấy lớp id={section_id}.")

    da_xoa = data["sections"][section_id]
    course_id, ma_lop = da_xoa.get("course_id"), da_xoa.get("class_code")

    data["sections"].pop(section_id)
    data["submissions"].pop(section_id, None)
    if section_id in data["pending_section_ids"]:
        data["pending_section_ids"].remove(section_id)
    STATE["overrides"].pop(section_id, None)
    STATE["bo_ghim"].discard(section_id)
    # Nhom hoc chung con MOT lop thi khong con la "hoc chung" - de lai thi giao
    # dien hien badge "Học chung" tren mot buoi don doc.
    don_nhom_hong(data)
    # Xoa "AET2014-2" thi cac lop con lai (AET2014-3, -4...) don xuong 1 don vi
    # (-2, -3...) - khong de trong so giua ma lop cua cung hoc phan.
    don_ma_lop_sau_xoa(data, course_id, ma_lop)

    dong_bo_ket_qua(data, [section_id])
    save_snapshot()
    return tra_du_lieu(data)
