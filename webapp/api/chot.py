# -*- coding: utf-8 -*-
"""CHOT LICH GIANG DAY theo HOC PHAN (va bo chot).

Chot lich la CAM KET voi giang vien: mon nao thong nhat xong thi khoa lai, cac
mon con lai van de he thong xep tiep ma khong lam xe dich mon da chot. Xem
domain/chot.py cho quy tac.
"""

from flask import Blueprint, jsonify, request

from api.common import can_du_lieu, loi, tra_du_lieu
from domain.chot import bo_chot_hoc_phan, chot_hoc_phan
from domain.pinning import attach_ca_hai
from snapshot import save_snapshot

bp = Blueprint("chot", __name__)


@bp.post("/api/manual/course/<int:course_id>/chot")
@can_du_lieu
def api_manual_chot_course(data, course_id):
    """Chot lich giang day cho 1 hoc phan (moi lop cua no)."""
    if course_id not in data.get("courses", {}):
        return loi(f"Không tìm thấy học phần id={course_id}.")
    body = request.get_json(silent=True) or {}
    so, err = chot_hoc_phan(data, course_id, body.get("by"), body.get("note"))
    if err:
        return (jsonify(err), 400) if isinstance(err, dict) else loi(err)
    attach_ca_hai(data)
    save_snapshot()
    return tra_du_lieu(data, chotCount=so,
                       courseName=data["courses"][course_id].get("name"))


@bp.delete("/api/manual/course/<int:course_id>/chot")
@can_du_lieu
def api_manual_bo_chot_course(data, course_id):
    """Bo chot 1 hoc phan - tra gio ve trang thai truoc khi chot."""
    if course_id not in data.get("courses", {}):
        return loi(f"Không tìm thấy học phần id={course_id}.")
    if not data["courses"][course_id].get("chot"):
        return loi("Học phần này chưa được chốt.")
    bo_chot_hoc_phan(data, course_id)
    attach_ca_hai(data)
    save_snapshot()
    return tra_du_lieu(data, courseName=data["courses"][course_id].get("name"))
