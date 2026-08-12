# -*- coding: utf-8 -*-
"""Quy tac NGHIEP VU xep thoi khoa bieu - khong biet gi ve Flask/HTTP.

Moi module o day chi doc/sua bo du lieu `data` (xem sections.empty_manual_data)
va STATE (state.py). Khong module nao import tu api/ - chieu phu thuoc luon la
api/ -> domain/, de doi mot quy tac nghiep vu khong phai mo tang route.

Thu tu phu thuoc trong noi bo domain/ (khong co vong tron):

    programs.py  availability.py     <- tang duoi, khong phu thuoc domain khac
         |            |
         |       time_rules.py       <- parse/ghi gio cho mot lop
         |         |    |    |
    sections.py  teachers.py  pinning.py  chot.py
         |            |
    merge.py     response.py
         |
    excel_rows.py                    <- tang tren, dung lai gan het cac module tren
"""
