# -*- coding: utf-8 -*-
"""CHAY THUAT TOAN: khai gio, Giai doan 1 (thinh giang), Giai doan 2 (co huu).

Thu tu bat buoc: GD1 xep thinh giang theo khung gio ho da bao -> dong bang ket
qua do -> GD2 ghep co huu vao cho con lai. Ca hai pha deu chay trong `with
tam_bo_ghim(...)` de nhung lop giao vu vua bam "Bo ghim" that su duoc xep lai.
"""

from flask import Blueprint, jsonify, request

from api.common import can_du_lieu, loi
from domain.luoi import attach_ca_hai, attach_override_metadata, dong_bo_ket_qua
from domain.pinning import (ghim_tay_o_giai_doan_2, solve_guest_with_overrides,
                            tam_bo_ghim)
from state import STATE

import scheduler_core as sc

bp = Blueprint("solve", __name__)


@bp.post("/api/submit-availability")
@can_du_lieu
def api_submit_availability(data):
    """Dieu phoi vien nhap 'Gio co the day' cho mot lop thinh giang."""
    body = request.get_json(force=True)
    section_id = int(body["sectionId"])
    window_slots = [int(w) for w in body["windowSlots"]]
    if not window_slots:
        return loi("Phải nhập ít nhất 1 khung giờ.")

    # Cac lop trong pending_section_ids luon la THINH GIANG - ap dung dung gioi
    # han "thinh giang toi Thu 7" (sc.MAX_DAY_INDEX).
    slots_per_day = data["params"]["slotsPerDay"]
    max_day = sc.max_day_index("GUEST")
    if any((w // slots_per_day) > max_day for w in window_slots):
        return loi("Có khung giờ ngoài phạm vi (thỉnh giảng chỉ dạy tới Thứ 7).")

    result = sc.submit_availability(data, section_id, window_slots)
    return jsonify({**result, "remainingPending": len(data["pending_section_ids"])})


@bp.post("/api/solve-guest")
@can_du_lieu
def api_solve_guest(data):
    """Giai doan 1: xep cac lop THINH GIANG theo khung gio da bao."""
    with tam_bo_ghim(data):
        result = solve_guest_with_overrides(data)
    attach_override_metadata(data, result, "GUEST")
    STATE["guestResult"] = result

    # NGHIEM cua Giai doan 2 khong con hieu luc: no duoc tinh tu vi tri cac buoi
    # thinh giang vua doi (xem solve_resident_phase, tham so frozen_guest_lessons).
    # Giu lai la hien mot lich khong con ton trong GD1 nua.
    #
    # NHUNG khong duoc xoa trang: phan lon lop co huu da co GIO CHOT trong file va
    # da duoc ghim (nap HK1 2026-2027-3: 108/163 lop). Do la du kien, khong phai
    # san pham cua solver. Truoc day cho nay dat thang None nen bam "Giai" o buoc 2
    # la 80 buoi co huu BIEN MAT khoi luoi, phai bam tiep buoc 3 moi thay lai -
    # giao vu tuong he thong lam mat lich cua minh.
    #
    # Dung lai bang dong_bo_ket_qua(chi_pha="RESIDENT"): no dat lai cac buoi co gio
    # co dinh/ghim, gan initial=True nen thanh tien trinh van bao buoc 3 "chua chay"
    # va nut buoc 3 van la "Giai" (xem WorkflowStrip), khong ai hieu nham day la
    # ket qua da ghep.
    STATE["residentResult"] = None
    dong_bo_ket_qua(data, chi_pha="RESIDENT")
    return jsonify({**result, "residentResult": STATE["residentResult"]})


@bp.post("/api/solve-resident")
@can_du_lieu
def api_solve_resident(data):
    """Giai doan 2: ghep cac lop CO HUU vao cho con lai sau Giai doan 1."""
    # "initial" = lich ban dau doc tu file, CHUA phai ket qua giai Giai doan 1
    # (xem pinning.lich_ban_dau) - van phai chay buoc 2 truoc.
    if STATE["guestResult"] is None or STATE["guestResult"].get("initial"):
        return loi("Cần chạy Giai đoạn 1 (thỉnh giảng) trước.")
    with tam_bo_ghim(data):
        result = sc.solve_resident_phase(data, STATE["guestResult"]["lessons"],
                                         ghim_tay=ghim_tay_o_giai_doan_2(data),
                                         bo_ghim=STATE["bo_ghim"])
    attach_override_metadata(data, result, "RESIDENT")
    STATE["residentResult"] = result
    return jsonify(result)


@bp.get("/api/results")
def api_results():
    """Tra lai ket qua giai dang cache trong STATE - dung khi SPA tai lai trang.

    Truoc khi co endpoint nay, guestResult/residentResult chi song trong state
    React: bam F5 la luoi trong va giao vu phai bam 'Giai' lai (2-30 giay) DU
    backend van con nguyen ket qua. /api/state co bao hasGuestResult nhung khong
    tra ve chinh ket qua, nen frontend biet 'co' ma khong lay duoc.

    Gan metadata ghim truoc khi tra de the buoi hien dung 'nhan ghim' ngay sau khi
    tai lai, khong doi den luot sua tay ke tiep."""
    if STATE["data"] is None:
        return jsonify({"guestResult": None, "residentResult": None})

    attach_ca_hai(STATE["data"])
    return jsonify({
        "guestResult": STATE["guestResult"],
        "residentResult": STATE["residentResult"],
    })
