# -*- coding: utf-8 -*-
"""NHAP LIEU THU CONG: giang vien, hoc phan, lop - va xoa gio hang loat.

Day la duong du lieu CHINH cua he thong (thay Excel). Luong nap file
(api/import_excel.py) chay lai dung nhung ham o day (domain/excel_rows.py) nen
du lieu hai duong khong khac nhau cho nao.
"""

from flask import Blueprint, request

from api.common import can_du_lieu, loi, tra_du_lieu
from domain.availability import parse_availability_slots
from domain.chot import khoa_vi_da_chot
from domain.pinning import dong_bo_ket_qua, ghim_theo_gio_form
from domain.sections import empty_manual_data, id_moi, validate_section_body
from domain.teachers import dem_lai_so_gv, sync_teacher_sections
from domain.time_rules import apply_section_time
from snapshot import save_snapshot
from state import STATE, reset_ket_qua

bp = Blueprint("manual", __name__)


@bp.post("/api/manual/init")
def api_manual_init():
    """Bat dau 'nhap lieu thu cong': XOA HET du lieu dang co, bat dau tu 1 bo du
    lieu rong roi giao vu tu them GV/lop bang tay qua /api/manual/teacher va
    /api/manual/section."""
    data = empty_manual_data()
    extra = {"isRealData": False, "sourceLabel": "Nhập liệu thủ công", "numTimeAssumed": 0}
    STATE["data"] = data
    STATE["extra"] = extra
    reset_ket_qua()
    save_snapshot()
    return tra_du_lieu(data)


@bp.post("/api/manual/clear-times")
@can_du_lieu
def api_manual_clear_times(data):
    """'Xoá giờ' hàng loạt tren man 'Du lieu hoc phan': dat lai Thu/Tiet dau/Tiet
    cuoi cua NHIEU lop cung luc thanh 'de he thong tu xep' (time_info=None),
    dung LAI apply_section_time() dung nhu sua tung lop mot. Body JSON:
    {sectionIds: [int, ...]} - danh sach lop dang hien theo bo loc HIEN TAI o
    frontend, de xoa dung nhung dong giao vu dang thay tren man (WYSIWYG), khong
    phai toan bo du lieu."""
    body = request.get_json(force=True)
    try:
        section_ids = [int(x) for x in (body.get("sectionIds") or [])]
    except (TypeError, ValueError):
        return loi("sectionIds phải là danh sách số nguyên.")

    cleared = 0
    bo_qua_da_chot = 0
    da_xoa = []
    for sid in section_ids:
        s = data["sections"].get(sid)
        teacher = data["teachers"].get(s["teacher_id"]) if s else None
        if s is None or teacher is None:
            continue
        # Xoa gio hang loat KHONG duoc pha mon da chot: nut nay xoa theo bo loc
        # dang hien nen rat de quet trung vao mon da cam ket voi giang vien.
        if khoa_vi_da_chot(data, sid):
            bo_qua_da_chot += 1
            continue
        apply_section_time(data, sid, teacher, s["duration"], None)
        # Go ghim: khong go thi lop van bi ep ve gio vua xoa o lan Giai ke tiep,
        # tuc nut "Xoa gio" khong lam gi ca (xem ghim_theo_gio_form).
        ghim_theo_gio_form(data, sid, None)
        # Gio cu khong con - "Trang thai lich" (tu Luu thoi khoa bieu) da het
        # nghia, khong the de nguyen kieu "Da xep" tren mot lop vua bi xoa gio.
        s["schedule_status"] = None
        da_xoa.append(sid)
        cleared += 1

    # Lop vua bi xoa gio phai RUNG KHOI luoi Thoi khoa bieu - xem bo_vi_tri_cu.
    dong_bo_ket_qua(data, da_xoa)
    save_snapshot()
    return tra_du_lieu(data, clearedCount=cleared, skippedChotCount=bo_qua_da_chot)


# --------------------------------------------------------------------------
# Giang vien
# --------------------------------------------------------------------------

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

    # Doi loai GV lam cac lop cua ho NHAY GIAI DOAN (thinh giang <-> co huu), va
    # doi ten thi the buoi tren luoi phai ghi ten moi. KHONG truyen bo_vi_tri_cu:
    # cac lop nay khong bi ghi lai gio, nghiem cua lan giai truoc van la thong tin
    # dung nhat ve cho cua chung.
    dong_bo_ket_qua(data)
    save_snapshot()
    return tra_du_lieu(data)


# --------------------------------------------------------------------------
# Hoc phan
# --------------------------------------------------------------------------

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


# --------------------------------------------------------------------------
# Lop
# --------------------------------------------------------------------------

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

    # Chan SAU khi validate: chi tu choi khi yeu cau nay lam DOI gio cua mot lop
    # thuoc hoc phan da chot. Sua ten GV/email/dia diem... van cho qua.
    khoa = khoa_vi_da_chot(data, section_id, time_info)
    if khoa:
        return loi(khoa, 409, locked=True)

    data["sections"][section_id].update(fields)
    apply_section_time(data, section_id, teacher, duration, time_info)
    ghim_theo_gio_form(data, section_id, time_info)

    # Gio/GV/hoc phan cua lop vua doi -> luoi Thoi khoa bieu phai theo. Truyen
    # section_id vao bo_vi_tri_cu: gio vua go tay thang vi tri cu tren luoi.
    dong_bo_ket_qua(data, [section_id])
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

    data["sections"].pop(section_id)
    data["submissions"].pop(section_id, None)
    if section_id in data["pending_section_ids"]:
        data["pending_section_ids"].remove(section_id)
    STATE["overrides"].pop(section_id, None)
    STATE["bo_ghim"].discard(section_id)

    dong_bo_ket_qua(data, [section_id])
    save_snapshot()
    return tra_du_lieu(data)
