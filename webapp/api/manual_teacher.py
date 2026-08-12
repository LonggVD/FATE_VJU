# -*- coding: utf-8 -*-
"""GIANG VIEN nhap tay: them moi va sua (ke ca khung gio ranh)."""

from flask import Blueprint, request

from api.common import can_du_lieu, loi, tra_du_lieu
from domain.availability import parse_availability_slots
from domain.hoc_chung import tach_nhom_khong_hop_le
from domain.luoi import dong_bo_ket_qua
from domain.sections import id_moi
from domain.teachers import dem_lai_so_gv, sync_teacher_sections
from snapshot import save_snapshot

bp = Blueprint("manual_teacher", __name__)


@bp.post("/api/manual/teacher")
@can_du_lieu
def api_manual_add_teacher(data):
    """Them 1 giang vien nhap tay. Body JSON:
    {name, org, title, email, phone, teacherType: 'GUEST'|'RESIDENT', availability: [slot, ...]}
    'availability' CHI co tac dung voi GUEST (co huu Giai doan 2 luon tu do chon
    gio, khong can khai bao - theo quyet dinh cua giao vu), la danh sach slot
    PHANG GV ranh (xem availability.parse_availability_slots) - tick MOI tiet
    ranh, khong chi tiet bat dau, he thong tu tim gio bat dau hop le qua
    valid_starts_from_slots(). title/email/phone la tuy chon (fill-rate thuc
    te trong Excel rat thap)."""
    body = request.get_json(force=True)

    name = (body.get("name") or "").strip()
    if not name:
        return loi("Thiếu Họ tên giảng viên.")
    teacher_type = body.get("teacherType")
    if teacher_type not in ("GUEST", "RESIDENT"):
        return loi("teacherType phải là 'GUEST' hoặc 'RESIDENT'.")

    slots = []
    if teacher_type == "GUEST":
        slots, err = parse_availability_slots(data, body)
        if err:
            return loi(err)

    tid = id_moi(data["teachers"])
    data["teachers"][tid] = {
        "id": tid, "name": name, "type": teacher_type,
        "org": (body.get("org") or "").strip(),
        "title": (body.get("title") or "").strip(),
        "email": (body.get("email") or "").strip(),
        "phone": (body.get("phone") or "").strip(),
    }
    data.setdefault("manual_teacher_windows", {})[tid] = slots
    dem_lai_so_gv(data)

    save_snapshot()
    return tra_du_lieu(data)


@bp.patch("/api/manual/teacher/<int:teacher_id>")
@can_du_lieu
def api_manual_update_teacher(data, teacher_id):
    """Sua thong tin 1 GV va/hoac gio ranh - PARTIAL update (chi field co mat
    trong body moi bi ghi de), khac PATCH section (can gui du ca form): cac
    field GV doc lap voi nhau, khong can ngu canh cheo nhu section (thoi
    gian/GV/duration lien quan nhau). Sau khi doi teacherType/availability,
    dong bo lai cac lop dang cho GV nay qua sync_teacher_sections()."""
    teacher = data["teachers"].get(teacher_id)
    if teacher is None:
        return loi(f"Không tìm thấy giảng viên id={teacher_id}.")
    body = request.get_json(force=True)

    if "name" in body:
        name = (body.get("name") or "").strip()
        if not name:
            return loi("Họ tên không được để trống.")
        teacher["name"] = name
    for field in ("org", "title", "email", "phone"):
        if field in body:
            teacher[field] = (body.get(field) or "").strip()
    if "teacherType" in body:
        if body["teacherType"] not in ("GUEST", "RESIDENT"):
            return loi("teacherType phải là 'GUEST' hoặc 'RESIDENT'.")
        teacher["type"] = body["teacherType"]
    if "availability" in body:
        slots, err = parse_availability_slots(data, body)
        if err:
            return loi(err)
        data.setdefault("manual_teacher_windows", {})[teacher_id] = slots

    dem_lai_so_gv(data)
    sync_teacher_sections(data, teacher_id)
    # Doi loai GV co the lam mot nhom hoc chung LECH PHA (mot lop sang thinh giang,
    # lop kia con co huu) - o thao tac nay khong con "phep sua" nao de tu choi, nen
    # phai tach nhom va noi ra (xem tach_nhom_khong_hop_le).
    tach = tach_nhom_khong_hop_le(data)

    # Doi loai GV lam cac lop cua ho NHAY GIAI DOAN (thinh giang <-> co huu), va
    # doi ten thi the buoi tren luoi phai ghi ten moi. KHONG truyen bo_vi_tri_cu:
    # cac lop nay khong bi ghi lai gio, nghiem cua lan giai truoc van la thong tin
    # dung nhat ve cho cua chung.
    dong_bo_ket_qua(data)
    save_snapshot()
    return tra_du_lieu(data, hocChungSplit=tach)
