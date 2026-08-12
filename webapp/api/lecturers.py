# -*- coding: utf-8 -*-
"""DANH SACH GIANG VIEN CO HUU cua truong - nguon CHINH THUC de phan loai co huu/
thinh giang.

Hai buoc (xem truoc -> nap) giong luong nhap file ke hoach: nap danh sach co the
DOI LOAI nhieu giang vien, keo theo lop doi giai doan xep lich - phai cho xem
truoc ai bi doi roi moi quyet.
"""

from flask import Blueprint, jsonify, request

from api.common import loi
from domain.response import build_data_response
from domain.hoc_chung import tach_nhom_khong_hop_le
from domain.teachers import ap_lai_loai_gv, doi_chieu_danh_sach
from snapshot import save_snapshot
from state import STATE

import fate_lecturers

bp = Blueprint("lecturers", __name__)


@bp.get("/api/manual/lecturers")
def api_manual_lecturers():
    """Danh sach GV co huu dang luu (None = chua nap -> van dung luat o don vi)."""
    ds = STATE.get("co_huu")
    if not ds:
        return jsonify({"loaded": False, "rows": [], "count": 0, "fileName": None})
    return jsonify({
        "loaded": True, "count": ds["count"], "fileName": ds.get("fileName"),
        "rows": sorted(ds["byKey"].values(), key=lambda m: m["name"]),
    })


@bp.post("/api/manual/lecturers/preview")
def api_manual_lecturers_preview():
    """Doc file danh sach GV co huu -> BAN XEM TRUOC, CHUA ghi gi vao STATE."""
    f = request.files.get("file")
    if f is None or not f.filename:
        return loi("Chưa chọn file.")
    result, err = fate_lecturers.read_lecturers(f.stream)
    if err:
        return loi(err)
    by_key = {m["key"]: m for m in result["rows"]}
    STATE["co_huu_pending"] = {"byKey": by_key, "fileName": f.filename,
                               "count": len(by_key), "result": result}
    return jsonify({
        "fileName": f.filename, "sheet": result["sheet"], "count": len(by_key),
        "duplicates": result["duplicates"], "skipped": result["skipped"],
        "sample": [m["name"] for m in result["rows"][:8]],
        **doi_chieu_danh_sach(STATE.get("data"), by_key),
    })


@bp.post("/api/manual/lecturers/commit")
def api_manual_lecturers_commit():
    """Ghi danh sach vua xem truoc vao STATE va phan loai lai toan bo GV."""
    pending = STATE.get("co_huu_pending")
    if not pending:
        return loi("Chưa có bản xem trước. Hãy tải file lên trước.")
    STATE["co_huu"] = {"byKey": pending["byKey"], "fileName": pending["fileName"],
                       "count": pending["count"]}
    STATE["co_huu_pending"] = None
    doi = ap_lai_loai_gv(STATE["data"]) if STATE["data"] else []
    # Phan loai lai HANG LOAT co the lam mot nhom hoc chung lech pha (mot lop sang
    # thinh giang, lop kia con co huu) - hai pha giai la hai bai toan rieng nen
    # nhom do mat rang buoc cung gio. Khong con phep sua nao de tu choi, phai tach
    # va noi ra.
    tach = tach_nhom_khong_hop_le(STATE["data"]) if STATE["data"] else []
    save_snapshot()
    return jsonify({
        "count": STATE["co_huu"]["count"], "fileName": STATE["co_huu"]["fileName"],
        "changed": doi, "hocChungSplit": tach,
        **(build_data_response(STATE["data"], STATE.get("extra")) if STATE["data"] else {}),
    })


@bp.delete("/api/manual/lecturers")
def api_manual_lecturers_clear():
    """Bo danh sach co huu -> quay ve luat cu (doc o "Don vi cong tac")."""
    STATE["co_huu"] = None
    STATE["co_huu_pending"] = None
    doi = ap_lai_loai_gv(STATE["data"]) if STATE["data"] else []
    tach = tach_nhom_khong_hop_le(STATE["data"]) if STATE["data"] else []
    save_snapshot()
    return jsonify({
        "loaded": False, "changed": doi, "hocChungSplit": tach,
        **(build_data_response(STATE["data"], STATE.get("extra")) if STATE["data"] else {}),
    })
