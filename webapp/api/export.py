# -*- coding: utf-8 -*-
"""XUAT ra .xlsx dung khuon FATE chuan - de dung lam van ban chinh thuc va nap
lai duoc o ky sau."""

from flask import Blueprint, request, send_file

from api.common import can_du_lieu
from api.import_excel import XLSX_MIME
from domain.response import build_classes_list

import fate_export

bp = Blueprint("export", __name__)


@bp.get("/api/manual/export")
@can_du_lieu
def api_manual_export(data):
    """Xuat bang 'Du lieu hoc phan' hien co ra .xlsx (fate_export.py)."""
    label = (request.args.get("label") or "").strip() or "TKB"
    buf = fate_export.build_workbook(build_classes_list(data), label)
    return send_file(buf, as_attachment=True,
                     download_name=f"FATE.TKB.{label}.xlsx", mimetype=XLSX_MIME)
