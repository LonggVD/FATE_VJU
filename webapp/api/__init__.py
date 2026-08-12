# -*- coding: utf-8 -*-
"""TANG HTTP: moi file la mot Blueprint theo MAN HINH/NHOM VIEC cua giao vu.

Cac file o day chi lam ba viec: doc request, goi domain/, dong goi response. Moi
quyet dinh nghiep vu nam ben domain/ - de sua mot luat khong phai mo tang route,
va de biet loi nam o dau chi can nhin ten file.
"""

from api.chot import bp as bp_chot
from api.data import bp as bp_data
from api.export import bp as bp_export
from api.frontend import bp as bp_frontend
from api.import_excel import bp as bp_import
from api.lecturers import bp as bp_lecturers
from api.manual import bp as bp_manual
from api.schedule import bp as bp_schedule
from api.solve import bp as bp_solve

_TAT_CA = (
    bp_frontend,   # /, /assets, /favicon.svg, /icons.svg
    bp_data,       # /api/data, /api/state
    bp_lecturers,  # /api/manual/lecturers*
    bp_import,     # /api/manual/import/*
    bp_manual,     # /api/manual/{init,teacher,course,section,clear-times}
    bp_solve,      # /api/{submit-availability,solve-guest,solve-resident,results}
    bp_schedule,   # /api/{move-lesson,clear-override}, /api/manual/save-schedule
    bp_chot,       # /api/manual/course/<id>/chot
    bp_export,     # /api/manual/export
)


def register_blueprints(app):
    for bp in _TAT_CA:
        app.register_blueprint(bp)
