# -*- coding: utf-8 -*-
"""Doc bo du lieu dang co trong STATE."""

from flask import Blueprint, jsonify

from api.common import can_du_lieu, tra_du_lieu
from state import STATE

bp = Blueprint("data", __name__)


@bp.get("/api/data")
@can_du_lieu
def api_data(data):
    """Tra lai dung khuon build_data_response() cho du lieu dang co trong STATE -
    dung khi SPA chuyen man/refresh ma khong muon nap lai tu dau (se lam mat
    guestResult/residentResult dang co)."""
    return tra_du_lieu(data)


@bp.get("/api/state")
def api_state():
    return jsonify({
        "hasData": STATE["data"] is not None,
        "hasGuestResult": STATE["guestResult"] is not None,
        "hasResidentResult": STATE["residentResult"] is not None,
        "overridesCount": len(STATE["overrides"]),
    })
