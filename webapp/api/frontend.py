# -*- coding: utf-8 -*-
"""Phuc vu giao dien React da build (../frontend/dist).

Giao dien nam o ../frontend (React + Vite), build ra ../frontend/dist. Ban giao
dien CU mot-file (webapp/templates/index.html) da bi XOA: no khong co cac man
"Nhap tu Excel"/"Kiem tra du lieu"/"Xac nhan gio hoc", va da hong san (con goi
/api/reject - endpoint khong con ton tai). Nen o day chi con MOT duong: dist.
"""

import pathlib

from flask import Blueprint, request, send_from_directory

bp = Blueprint("frontend", __name__)

DIST = pathlib.Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

_CHUA_BUILD = """<!doctype html><meta charset="utf-8">
<title>Chưa build giao diện</title>
<body style="font:16px/1.6 system-ui;max-width:44rem;margin:4rem auto;padding:0 1rem">
<h1>Chưa build giao diện</h1>
<p>Không tìm thấy <code>frontend/dist/index.html</code>. Chạy một trong hai cách:</p>
<pre style="background:#f4f4f5;padding:1rem;border-radius:.5rem">cd frontend
npm install
npm run build      # rồi tải lại trang này

npm run dev        # hoặc chạy Vite dev server và mở cổng nó in ra</pre>
</body>"""


def da_build():
    return (DIST / "index.html").is_file()


@bp.get("/")
def index():
    if da_build():
        return send_from_directory(DIST, "index.html")
    return _CHUA_BUILD, 503


@bp.get("/assets/<path:ten>")
def dist_assets(ten):
    """File js/css da build (ten co ma bam, doi moi lan build)."""
    return send_from_directory(DIST / "assets", ten)


@bp.get("/favicon.svg")
@bp.get("/icons.svg")
def dist_icons():
    return send_from_directory(DIST, request.path.lstrip("/"))
