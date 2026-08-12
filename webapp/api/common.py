# -*- coding: utf-8 -*-
"""Ba thu lap lai o gan nhu moi endpoint - go ve mot cho.

Truoc day 20 endpoint moi cai tu viet lai `if STATE["data"] is None: return
jsonify({"error": ...}), 400` voi 4 cach dien dat khac nhau, va tu goi
build_data_response + jsonify. Sua thong diep hay them mot truong chung phai di
sua 20 cho.
"""

import functools

from flask import jsonify

from domain.response import build_data_response
from state import STATE

CHUA_CO_DU_LIEU = ("Chưa có dữ liệu. Hãy nạp file Excel kế hoạch giảng dạy "
                   "hoặc bắt đầu nhập tay trước.")


def can_du_lieu(fn):
    """Chan endpoint khi chua co bo du lieu nao, va TRUYEN THANG `data` vao ham -
    de trong than ham khong con dong `data = STATE["data"]` nao nua.

    Tham so tu URL (vd <int:teacher_id>) van den binh thuong qua **kwargs.
    """
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if STATE["data"] is None:
            return jsonify({"error": CHUA_CO_DU_LIEU}), 400
        return fn(STATE["data"], *args, **kwargs)
    return wrapper


def tra_du_lieu(data, **extra):
    """Response chuan: toan bo bo du lieu (khuon build_data_response) + LUOI THOI
    KHOA BIEU dang co + cac truong rieng cua endpoint nay (savedCount,
    mergeReport, chotCount...).

    Vi sao luon gui kem guest/residentResult: moi form o "Du lieu hoc phan" deu co
    the doi cho cua buoi tren luoi (doi Thu/Tiet, xoa gio, doi loai GV lam buoi
    nhay giai doan, doi ten mon/GV lam the buoi ghi khac). Truoc day cac endpoint
    do chi tra `data`, nen frontend cap nhat bang ma man Thoi khoa bieu van hien
    ban cu cho toi khi bam Giai lai hoac F5 - hai man noi hai chuyen khac nhau ve
    cung mot lop. Gui kem thi frontend chi viec gan lai ca hai."""
    return jsonify({
        **build_data_response(data, STATE.get("extra")),
        "guestResult": STATE["guestResult"],
        "residentResult": STATE["residentResult"],
        **extra,
    })


def loi(thong_diep, ma=400, **extra):
    return jsonify({"error": thong_diep, **extra}), ma
