# -*- coding: utf-8 -*-
"""HOC CHUNG: danh dau nhieu lop (nhieu ma mon) la MOT buoi day.

Xem domain/hoc_chung.py cho quy tac va ly do. Diem chinh: day KHONG phai "tat
canh bao" - nhom hoc chung bi solver ep cung gio va chi ton mot phong, nen sau
khi danh dau thi bam Giai bao nhieu lan ca nhom cung dung yen mot cho.
"""

from flask import Blueprint, jsonify, request

from api.common import can_du_lieu, loi, tra_du_lieu
from domain.chot import khoa_vi_da_chot
from domain.hoc_chung import cac_nhom, gio_dai_dien, kiem_tra_nhom, tao_nhom, xoa_nhom
from domain.pinning import dong_bo_ket_qua
from snapshot import save_snapshot

bp = Blueprint("hoc_chung", __name__)


@bp.get("/api/manual/hoc-chung")
@can_du_lieu
def api_hoc_chung_list(data):
    return jsonify({"groups": cac_nhom(data)})


@bp.post("/api/manual/hoc-chung")
@can_du_lieu
def api_hoc_chung_tao(data):
    """Danh dau cac lop la HOC CHUNG. Body: {sectionIds: [int,...], by, note}."""
    body = request.get_json(force=True)
    section_ids = body.get("sectionIds") or []

    # Mon da CHOT LICH = da cam ket voi giang vien ve GIO. Danh dau hoc chung co
    # the doi gio cua thanh vien (dong bo ve gio dai dien) nen phai chan y nhu
    # keo-tha - NHUNG chi khi gio THUC SU doi.
    #
    # Truyen `time_info` vao khoa_vi_da_chot de no tu so: truong hop pho bien nhat
    # la giao vu danh dau dung cap dang bi bao "trung giang vien", tuc hai lop VON
    # DA cung gio -> khong dung gi den cam ket nao, phai cho qua. Chan cung o day
    # lam co che nay vo dung ngay voi du lieu nap tu file (moi mon du gio deu duoc
    # chot san - xem pinning.chot_hoc_phan_du_gio_tu_file).
    # Validate HINH DANG nhom truoc (cung so tiet/loai phong/giai doan): mot phep
    # gop vo nghia thi bao thang ly do do, khong lai sang chuyen "da chot lich".
    ds_int, err = kiem_tra_nhom(data, section_ids)
    if err:
        return loi(err)

    time_info = gio_dai_dien(data, ds_int)
    for sid in ds_int:
        khoa = khoa_vi_da_chot(data, sid, time_info)
        if khoa:
            return loi(khoa, 409, locked=True)

    nhom, err = tao_nhom(data, ds_int, body.get("by"), body.get("note"))
    if err:
        return loi(err)

    # Gio cua thanh vien vua duoc dong bo ve dai dien -> luoi phai theo.
    dong_bo_ket_qua(data, nhom["sectionIds"])
    save_snapshot()
    return tra_du_lieu(data, hocChungGroup=nhom)


@bp.delete("/api/manual/hoc-chung/<int:nhom_id>")
@can_du_lieu
def api_hoc_chung_xoa(data, nhom_id):
    """Bo mot nhom hoc chung - cac lop tro lai doc lap, va tu lan Giai sau solver
    lai coi chung la trung gio (dung y: khong con ai noi day la mot buoi)."""
    nhom = xoa_nhom(data, nhom_id)
    if nhom is None:
        return loi(f"Không tìm thấy nhóm học chung id={nhom_id}.")
    dong_bo_ket_qua(data, nhom.get("sectionIds") or [])
    save_snapshot()
    return tra_du_lieu(data, hocChungRemoved=nhom_id)
