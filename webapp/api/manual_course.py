# -*- coding: utf-8 -*-
"""HOC PHAN nhap tay: them moi va sua. Mot hoc phan dung chung cho nhieu lop nen
sua o day anh huong TAT CA lop tham chieu toi no."""

from flask import Blueprint, request

from api.common import can_du_lieu, loi, tra_du_lieu
from domain.luoi import dong_bo_ket_qua
from domain.sections import id_moi
from snapshot import save_snapshot

bp = Blueprint("manual_course", __name__)


@bp.post("/api/manual/course")
@can_du_lieu
def api_manual_add_course(data):
    """Tao 1 hoc phan (dung chung cho nhieu lop - mirror cot B/C/D cua Excel,
    tuong tu 1 nhom dong merge-xuong). Body JSON: {code, name, credits}."""
    body = request.get_json(force=True)

    name = (body.get("name") or "").strip()
    if not name:
        return loi("Thiếu Tên học phần.")
    try:
        credits = int(body["credits"]) if body.get("credits") not in (None, "") else None
    except (TypeError, ValueError):
        return loi("Số tín chỉ phải là số nguyên.")

    courses = data.setdefault("courses", {})
    cid = id_moi(courses)
    courses[cid] = {"id": cid, "code": (body.get("code") or "").strip(),
                    "name": name, "credits": credits}

    save_snapshot()
    return tra_du_lieu(data)


@bp.patch("/api/manual/course/<int:course_id>")
@can_du_lieu
def api_manual_update_course(data, course_id):
    """Sua thong tin 1 hoc phan - anh huong tat ca lop tham chieu toi (course la
    entity rieng, khong can propagate tay xuong tung lop)."""
    course = data.setdefault("courses", {}).get(course_id)
    if course is None:
        return loi(f"Không tìm thấy học phần id={course_id}.")
    body = request.get_json(force=True)

    if "name" in body:
        name = (body.get("name") or "").strip()
        if not name:
            return loi("Tên học phần không được để trống.")
        course["name"] = name
    if "code" in body:
        course["code"] = (body.get("code") or "").strip()
    if "credits" in body:
        try:
            course["credits"] = int(body["credits"]) if body["credits"] not in (None, "") else None
        except (TypeError, ValueError):
            return loi("Số tín chỉ phải là số nguyên.")

    for s in data["sections"].values():
        if s.get("course_id") == course_id:
            s["course_name"] = f"{course['name']} ({s['class_code']})" if s.get("class_code") else course["name"]

    # Ten mon vua doi -> the buoi tren luoi Thoi khoa bieu phai ghi ten moi.
    dong_bo_ket_qua(data)
    save_snapshot()
    return tra_du_lieu(data)
