# -*- coding: utf-8 -*-
"""CHOT LICH THEO HOC PHAN: khoa gio cua mot mon lai va mo ra khi can.

Chot lich la mot CAM KET voi giang vien. Khac "Luu thoi khoa bieu" (chot MOT LAN
cho toan bo 343 lop): thuc te giao vu chot dan tung mon - mon nao thong nhat xong
voi giang vien thi khoa lai, cac mon con lai van de he thong xep tiep ma khong
lam xe dich mon da chot.
"""

import datetime

from domain.time_rules import apply_section_time
from state import KHONG_TRUYEN, STATE


def slot_dang_hien(data, sid):
    """Slot cua mot lop DANG HIEN tren luoi Thoi khoa bieu, theo dung thu tu uu
    tien ma man do dung: ghim tay > ket qua GD2 > ket qua GD1 > gio da ghi san o
    lop. None = lop nay chua o dau ca."""
    ov = STATE["overrides"].get(sid)
    if ov and ov.get("slot") is not None:
        return ov["slot"]
    for res in (STATE.get("residentResult"), STATE.get("guestResult")):
        for l in (res or {}).get("lessons") or []:
            if l["id"] == sid:
                return l["slot"]
    if not (data["sections"][sid].get("time_assumed")):
        return data["sections"][sid].get("original_slot")
    return None


def lop_cua_hoc_phan(data, course_id):
    return [s for s in data["sections"].values() if s.get("course_id") == course_id]


def gio_doi(s, time_info):
    """Yeu cau nay co lam DOI gio cua lop khong? time_info=None nghia la "de he
    thong tu xep" - voi lop dang co gio chot thi do CUNG la mot thay doi."""
    if time_info is None:
        return not s.get("time_assumed")
    return (bool(s.get("time_assumed"))
            or s.get("day") != time_info["day"]
            or s.get("period_start") != time_info["period_start"]
            or s.get("period_end") != time_info["period_end"])


def khoa_vi_da_chot(data, section_id, time_info=KHONG_TRUYEN):
    """Loi (str) neu thao tac nay dung vao GIO cua mot lop thuoc hoc phan DA CHOT -
    hoac None.

    Chot lich la mot cam ket voi giang vien; sua gio le tren bang sau do lam ban
    chinh thuc va ban da bao cho GV lech nhau ma khong ai thay. Muon doi gio thi
    phai BO CHOT truoc - mot thao tac co y thuc, co ghi lai.

    KHOA DUNG PHAN GIO, khong khoa ca ban ghi: sau khi nhap file van con phai sua
    ma lop sai, ten GV thieu, email, dia diem... Chan tat ca thi mon da chot thanh
    bat kha xam pham va giao vu het duong don du lieu. Truyen `time_info` (dang ma
    sections.validate_section_body tra ve) de so: gio KHONG doi thi cho qua.
    """
    s = data["sections"].get(section_id)
    if s is None:
        return None
    hp = data.get("courses", {}).get(s.get("course_id")) or {}
    chot = hp.get("chot")
    if not chot:
        return None
    if time_info is not KHONG_TRUYEN and not gio_doi(s, time_info):
        return None
    return (f"Học phần “{hp.get('name') or ''}” đã chốt lịch "
            f"({chot.get('by')}, {(chot.get('at') or '')[:16].replace('T', ' ')}). "
            f"Bỏ chốt học phần trước khi sửa giờ.")


def chot_hoc_phan(data, course_id, nguoi, ghi_chu):
    """CHOT LICH cho ca mot hoc phan: moi lop cua no lay gio dang hien tren luoi,
    ghi thanh gio chinh thuc VA ghim lai.

    Ghim qua STATE['overrides'] chu khong chi ghi gio vao lop: overrides la co che
    manh nhat o CA HAI pha (xem domain/pinning.py) nen giai lai bao nhieu lan mon
    nay cung dung yen.

    Luu `truoc` = trang thai gio TRUOC khi chot cua tung lop, de "bo chot" tra
    lai dung nhu cu: lop von co gio chot trong file thi giu gio do, lop von chua
    co gio thi ve lai "de he thong tu xep" - khong the doan lai duoc neu khong ghi.
    """
    lop = lop_cua_hoc_phan(data, course_id)
    if not lop:
        return None, "Học phần này chưa có lớp nào."

    slots_per_day = data["params"]["slotsPerDay"]
    thieu, gan = [], []
    for s in lop:
        slot = slot_dang_hien(data, s["id"])
        if slot is None:
            thieu.append(s)
            continue
        gan.append((s, slot))
    if thieu:
        return None, {
            "error": ("Chưa chốt được: %d lớp của học phần này chưa có giờ. "
                      "Hãy xếp hoặc nhập giờ cho chúng trước." % len(thieu)),
            "missing": [{"sectionId": s["id"], "classCode": s.get("class_code"),
                         "courseName": s.get("course_name")} for s in thieu],
        }

    truoc = {}
    for s, slot in gan:
        truoc[str(s["id"])] = {
            "day": s.get("day"), "periodStart": s.get("period_start"),
            "periodEnd": s.get("period_end"), "timeAssumed": bool(s.get("time_assumed")),
        }
        day, period0 = divmod(slot, slots_per_day)
        teacher = data["teachers"][s["teacher_id"]]
        apply_section_time(data, s["id"], teacher, s["duration"], {
            "day": day, "period_start": period0 + 1,
            "period_end": period0 + s["duration"],
        })
        STATE["overrides"][s["id"]] = {
            "slot": slot, "reason": "Đã chốt lịch học phần", "problem": None,
        }
        STATE["bo_ghim"].discard(s["id"])

    data["courses"][course_id]["chot"] = {
        "at": datetime.datetime.now().isoformat(timespec="seconds"),
        "by": (nguoi or "").strip() or "Giáo vụ",
        "note": (ghi_chu or "").strip(),
        "soLop": len(gan),
        "truoc": truoc,
    }
    return len(gan), None


def bo_chot_hoc_phan(data, course_id):
    """Mo lai mot hoc phan da chot: go ghim va TRA GIO VE dung trang thai truoc
    khi chot (xem `truoc` trong chot_hoc_phan). Lop von chua co gio quay lai
    "de he thong tu xep"; lop von co gio chot tu file giu nguyen gio do."""
    course = data["courses"][course_id]
    chot = course.get("chot") or {}
    truoc = chot.get("truoc") or {}
    for s in lop_cua_hoc_phan(data, course_id):
        STATE["overrides"].pop(s["id"], None)
        cu = truoc.get(str(s["id"]))
        teacher = data["teachers"][s["teacher_id"]]
        if cu is None or cu.get("timeAssumed") or cu.get("day") is None:
            apply_section_time(data, s["id"], teacher, s["duration"], None)
            # Lop von chua co gio: phai noi ro "cho he thong xep lai", neu khong
            # gio vua chot van con o original_slot va solver ghim theo no.
            STATE["bo_ghim"].add(s["id"])
        else:
            apply_section_time(data, s["id"], teacher, s["duration"], {
                "day": cu["day"], "period_start": cu["periodStart"],
                "period_end": cu["periodEnd"],
            })
            STATE["bo_ghim"].discard(s["id"])
    course.pop("chot", None)
