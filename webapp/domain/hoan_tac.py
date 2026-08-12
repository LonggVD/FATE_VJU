# -*- coding: utf-8 -*-
"""MOC HOAN TAC cho nut "Huy thay doi" o man Thoi khoa bieu.

"Huy thay doi" = tra TOAN BO ve dung trang thai cua LAN LUU gan nhat (hoac luc
vua nap file, neu chua luu lan nao). Day la undo MOT CAP, khong phai ngan xep
lich su - dung nhu da chot voi giao vu.

Khac snapshot.py: file do ben-vung-hoa du lieu dang lam viec sau MOI thao tac
sua; o day chi chup o HAI thoi diem (nap file / luu thoi khoa bieu). Vi vay moc
duoc ghi ra FILE RIENG - gop vao snapshot chinh la bat moi cu bam phai tra them
~500KB ghi dia vo ich.
"""

import copy
import datetime
import json
import os

from snapshot import KHOA_INT, save_snapshot
from state import STATE

MOC_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "moc_hoan_tac.json")


# "Huy thay doi" o man Thoi khoa bieu = tra ve dung trang thai cua LAN LUU gan
# nhat. Nen phai chup TOAN BO nhung gi mot thao tac tren man do co the doi:
#   data          gio cua tung lop (day/period/original_slot/time_assumed),
#                 submissions, pending_section_ids, trang thai chot cua hoc phan,
#                 cac nhom hoc chung
#   overrides     ghim tay
#   bo_ghim       cac lop da bam "cho he thong xep lai"
#   guest/residentResult  chinh cai luoi dang hien
# Chup thieu mot phan la "huy" tra ve mot trang thai nua voi nua kia - te hon
# khong huy.

def _chup():
    return {
        "data": copy.deepcopy(STATE["data"]),
        "extra": copy.deepcopy(STATE.get("extra")),
        "overrides": copy.deepcopy(STATE["overrides"]),
        "bo_ghim": set(STATE["bo_ghim"]),
        "guestResult": copy.deepcopy(STATE["guestResult"]),
        "residentResult": copy.deepcopy(STATE["residentResult"]),
    }


def dat_moc(nhan):
    """Ghi lai MOT MOC de "Huy thay doi" quay ve. Goi sau khi nap file va sau moi
    lan luu thoi khoa bieu - do la hai thoi diem giao vu coi la "ban da chot"."""
    if STATE["data"] is None:
        return
    STATE["moc_hoan_tac"] = {
        **_chup(),
        "nhan": nhan,
        "at": datetime.datetime.now().isoformat(timespec="seconds"),
    }
    _ghi_moc()


def thong_tin_moc():
    """Mo ta ngan cua moc de giao dien ghi len nut - None neu chua co moc nao."""
    m = STATE.get("moc_hoan_tac")
    if not m:
        return None
    return {"nhan": m["nhan"], "at": m["at"],
            "soLop": len((m.get("data") or {}).get("sections") or {})}


def hoan_tac():
    """Tra toan bo trang thai ve moc gan nhat. Tra ve (thong_tin, err).

    GIU LAI moc sau khi hoan tac: bam nhieu lan van ra cung mot ket qua, va giao
    vu lo bam thi khong mat diem quay ve."""
    m = STATE.get("moc_hoan_tac")
    if not m:
        return None, "Chưa có mốc nào để quay về. Mốc được ghi khi nạp file và mỗi lần lưu thời khoá biểu."
    # deepcopy TU moc chu khong gan thang: gan thang thi STATE va moc dung chung
    # mot doi tuong, thao tac sua tiep theo se an vao chinh ban chup -> bam "Huy"
    # lan hai ra trang thai da bi sua, tuc moc tu huy hoai.
    STATE["data"] = copy.deepcopy(m["data"])
    STATE["extra"] = copy.deepcopy(m["extra"])
    STATE["overrides"] = copy.deepcopy(m["overrides"])
    STATE["bo_ghim"] = set(m["bo_ghim"])
    STATE["guestResult"] = copy.deepcopy(m["guestResult"])
    STATE["residentResult"] = copy.deepcopy(m["residentResult"])
    save_snapshot()
    return thong_tin_moc(), None


def _ghi_moc():
    m = STATE.get("moc_hoan_tac")
    if not m:
        return
    try:
        with open(MOC_PATH, "w", encoding="utf-8") as f:
            json.dump({
                "data": {**m["data"],
                         "forced_conflict_teacher_ids":
                             sorted(m["data"].get("forced_conflict_teacher_ids") or [])},
                "extra": m["extra"],
                # Key cua overrides la INT -> JSON bien thanh chuoi, nap lai phai doi.
                "overrides": {str(k): v for k, v in m["overrides"].items()},
                "bo_ghim": sorted(m["bo_ghim"]),
                "guestResult": m["guestResult"], "residentResult": m["residentResult"],
                "nhan": m["nhan"], "at": m["at"],
            }, f, ensure_ascii=False)
    except OSError:
        pass


def nap_moc():
    """Doc lai moc khi khoi dong - de restart server khong mat diem quay ve."""
    if not os.path.exists(MOC_PATH):
        return
    try:
        with open(MOC_PATH, encoding="utf-8") as f:
            m = json.load(f)
    except (OSError, json.JSONDecodeError):
        return
    data = m.get("data")
    if not data:
        return
    for key in KHOA_INT:
        if isinstance(data.get(key), dict):
            data[key] = {int(k): v for k, v in data[key].items()}
    data["forced_conflict_teacher_ids"] = set(data.get("forced_conflict_teacher_ids") or [])
    STATE["moc_hoan_tac"] = {
        "data": data, "extra": m.get("extra"),
        "overrides": {int(k): v for k, v in (m.get("overrides") or {}).items()},
        "bo_ghim": set(m.get("bo_ghim") or []),
        "guestResult": m.get("guestResult"), "residentResult": m.get("residentResult"),
        "nhan": m.get("nhan") or "lần lưu trước", "at": m.get("at") or "",
    }
