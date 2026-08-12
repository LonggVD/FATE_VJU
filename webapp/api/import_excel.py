# -*- coding: utf-8 -*-
"""NAP FILE EXCEL ke hoach giang day: xem truoc -> (tai loi ra .xlsx) -> ghi vao.

Hai buoc xem-truoc/ghi-vao dung chung mot ban doc duoc cache o
STATE['import_pending'], nen buoc ghi chi viec gan vao: khong phai tai file len
lan hai va khong co nguy co lan 2 ra ket qua khac lan 1.
"""

from flask import Blueprint, jsonify, request, send_file

from api.common import loi
from domain.excel_rows import build_import_preview_response, build_manual_data_from_rows
from domain.hoc_chung import luu_de_tai_lap, tai_lap_theo_ma_lop
from domain.merge import gop_manual_data
from domain.pinning import dat_lich_ban_dau
from domain.response import build_data_response
from snapshot import save_snapshot
from state import STATE

import fate_audit
import fate_export
import fate_import

bp = Blueprint("import_excel", __name__)

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@bp.post("/api/manual/import/preview")
def api_manual_import_preview():
    """Doc file Excel duoc tai len va tra ve BAN XEM TRUOC - CHUA ghi gi vao STATE."""
    f = request.files.get("file")
    if f is None or not f.filename:
        return loi("Chưa chọn file.")

    result, err = fate_import.read_rows(f)
    if err:
        return loi(err)

    data, err_rows, canh_bao_gv = build_manual_data_from_rows(result["rows"])

    STATE["import_pending"] = {
        "data": data,
        "fileName": f.filename,
        "sheet": result["sheet"],
        # Giu nguyen ban doc goc (rows/warnings/skipped) de cac endpoint sau
        # (vd tai loi du lieu ra .xlsx) dung lai, khong phai doc lai file.
        "result": result,
    }

    return jsonify(build_import_preview_response(result, data, err_rows, canh_bao_gv, f.filename))


@bp.get("/api/manual/import/issues.xlsx")
def api_manual_import_issues_xlsx():
    """Tai danh sach loi du lieu cua ban xem truoc ra .xlsx - de gui khoa/CTDT sua
    o FILE GOC (chi ho sua duoc; xem fate_audit). Doc-only, khong doi STATE."""
    pending = STATE.get("import_pending")
    if not pending or not pending.get("result"):
        return loi("Chưa có bản xem trước. Hãy tải file lên trước.")
    nhom = fate_audit.kiem_tra(pending["result"]["rows"], pending["data"]["teachers"])
    buf = fate_export.build_issues_workbook(nhom, pending.get("fileName") or "")
    ten = (pending.get("fileName") or "file").rsplit(".", 1)[0]
    return send_file(buf, as_attachment=True, download_name=f"Loi-du-lieu.{ten}.xlsx",
                     mimetype=XLSX_MIME)


@bp.post("/api/manual/import/commit")
def api_manual_import_commit():
    """Ghi ban xem truoc vao STATE. Body JSON tuy chon: {"mode": "replace"|"merge"}.

    - "replace" (mac dinh): XOA HET du lieu dang co.
    - "merge": GOP THEM vao du lieu dang co - de nap file cua khoa nay roi nap tiep
      file cua khoa khac, hoac nap bo sung dot 2 ma khong mat cong da sua.

    Dat sourceLabel = "Nhap lieu thu cong" chu KHONG phai ten file: form
    "Du lieu hoc phan" chi mo khoa sua khi thay nhan do (xem isManualMode ben
    ManualEntryPage). Ten file di rieng qua 'importedFrom' de van truy nguyen duoc.
    """
    pending = STATE.get("import_pending")
    if not pending:
        return loi("Chưa có bản xem trước. Hãy tải file lên trước.")

    body = request.get_json(silent=True) or {}
    mode = body.get("mode", "replace")
    if mode not in ("replace", "merge"):
        return loi("mode phải là 'replace' hoặc 'merge'.")

    # HOC CHUNG duoc neo theo MA LOP truoc khi THAY du lieu: section id sinh lai tu
    # 0 moi lan nap nen nhom khoa theo id se mat sach. Giao vu doi file kha thuong
    # xuyen (mot ky da toi ban -5) nen khong the bat ho danh dau lai moi lan.
    #
    # Chi can neo o che do "replace". "merge" gop THEM vao bo dang co nen section
    # id cu giu nguyen, nhom con nguyen ven - neo lai o do se tao nhom trung va bao
    # cao ra nhung con so vo nghia.
    thay_du_lieu = not (mode == "merge" and STATE["data"] is not None)
    nhom_cu = luu_de_tai_lap(STATE["data"]) if (thay_du_lieu and STATE["data"]) else []

    nguon = f"{pending['fileName']} (sheet '{pending['sheet']}')"
    if not thay_du_lieu:
        gop = gop_manual_data(STATE["data"], pending["data"])
        cu = (STATE["extra"] or {}).get("importedFrom")
        STATE["extra"] = {
            "isRealData": False,
            "sourceLabel": "Nhập liệu thủ công",
            "numTimeAssumed": STATE["data"].get("num_time_assumed", 0),
            "importedFrom": f"{cu} + {nguon}" if cu else nguon,
        }
    else:
        gop = None
        STATE["data"] = pending["data"]
        STATE["extra"] = {
            "isRealData": False,
            "sourceLabel": "Nhập liệu thủ công",
            "numTimeAssumed": pending["data"].get("num_time_assumed", 0),
            "importedFrom": nguon,
        }

    # Ket qua giai cu khong con dung voi bo du lieu moi (ke ca khi gop them: co
    # lop moi chen vao, phong/gio phai tinh lai).
    STATE["guestResult"] = None
    STATE["residentResult"] = None
    STATE["import_pending"] = None
    # Ghep lai cac nhom HOC CHUNG theo ma lop. Phai lam TRUOC dat_lich_ban_dau:
    # tao nhom co the dong bo gio cac thanh vien ve gio dai dien, ma lich ban dau
    # doc chinh gio do.
    so_nhom, bo_qua_nhom = tai_lap_theo_ma_lop(STATE["data"], nhom_cu)

    # ...nhung LICH BAN DAU tu cac gio da chot trong file thi hien duoc ngay, va
    # ghim san de hai buoc giai khong lam xe dich (xem pinning.dat_lich_ban_dau).
    dat_lich_ban_dau(STATE["data"], nguon)

    save_snapshot()
    resp = build_data_response(STATE["data"], STATE["extra"])
    if nhom_cu:
        # Noi ro da ghep lai duoc bao nhieu nhom va mat nhung nhom nao - khong thi
        # giao vu tuong nhom cu con nguyen trong khi mot vai da roi.
        resp["hocChungReport"] = {"taiLap": so_nhom, "boQua": bo_qua_nhom,
                                  "truoc": len(nhom_cu)}
    # Tra kem LICH BAN DAU de man "Thoi khoa bieu" hien duoc ngay sau khi nap,
    # khong phai tai lai trang.
    resp["guestResult"] = STATE["guestResult"]
    resp["residentResult"] = STATE["residentResult"]
    if gop is not None:
        resp["mergeReport"] = gop
    return jsonify(resp)
