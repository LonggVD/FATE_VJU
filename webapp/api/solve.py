# -*- coding: utf-8 -*-
"""CHAY THUAT TOAN: khai gio, Giai doan 1 (thinh giang), Giai doan 2 (co huu).

Thu tu bat buoc: GD1 xep thinh giang theo khung gio ho da bao -> dong bang ket
qua do -> GD2 ghep co huu vao cho con lai. Ca hai pha deu chay trong `with
tam_bo_ghim(...)` de nhung lop giao vu vua bam "Bo ghim" that su duoc xep lai.
"""

from flask import Blueprint, jsonify

from api.common import can_du_lieu, loi
from domain.luoi import attach_ca_hai, attach_override_metadata, dong_bo_ket_qua
from domain.pinning import (ghim_tay_o_giai_doan_2, solve_guest_with_overrides,
                            tam_bo_ghim)
from state import STATE

import scheduler_core as sc

bp = Blueprint("solve", __name__)


@bp.post("/api/solve-guest")
@can_du_lieu
def api_solve_guest(data):
    """Giai doan 1: xep cac lop THINH GIANG theo khung gio da bao."""
    # CHAN giai khi con lop chua san sang: hoac chua co GV THAT (con la cho
    # trong), hoac co GV nhung chua bao gio THAT - ca hai deu khien solver phai
    # "danh tam" (gan cho trong, hoac coi la ranh ca tuan), ra mot lich khong
    # dung dieu kien thuc te. Dieu phoi vien/CTDT phai xu ly xong (man "Chuẩn bị
    # dữ liệu → Học phần") truoc khi xep, khong duoc bo qua buoc nay.
    con_thieu = sc.guest_sections_can_thu_gio(data)
    if con_thieu:
        return loi(
            f"Còn {len(con_thieu)} lớp thỉnh giảng chưa sẵn sàng (thiếu giảng viên hoặc thiếu "
            "giờ) — xử lý hết ở 'Chuẩn bị dữ liệu → Học phần' trước khi xếp.",
            missingCount=len(con_thieu),
        )
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
