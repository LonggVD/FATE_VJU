# -*- coding: utf-8 -*-
"""BO DONG NHAP TRUNG khi nap file Excel - giu dong co nhieu SV nhat.

Cung mot lop bi hai nguoi nhap hai lan voi hai con so si so khac nhau (khoa nhap
roi CTDT nhap lai). Dong trung de lai se tao section rieng, an mot phong rieng va
lam solver doi hai lan tai nguyen cho cung mot buoi.

Tach khoi domain/excel_rows.py: ben do DUNG bo du lieu tu cac dong; o day quyet
dinh dong nao duoc vao. Hai viec doc lap - luat nhan dien trung co the doi ma
khong dung gi den cach dung du lieu.
"""

import fate_import
from domain.programs import canonical_program_name


def _so_sv(r):
    """So SV du kien de so sanh; -1 khi o do bo trong (de trong LUON thua mot con
    so that, du con so do la 0)."""
    v = r.get("expectedStudents")
    return v if isinstance(v, (int, float)) else -1


def _khoa_trung(r):
    """Khoa nhan dien MOT LOP-MOT BUOI de biet hai dong co phai nhap trung.

    Gom du BON thanh phan, thieu mot cai la gop nham du lieu that:
      - MA LOP      : ten dinh danh lop. Khong co thi khong the noi gi (xem duoi).
      - GIANG VIEN  : chuan hoa qua fate_import.khoa_gv (bo hoc ham/dau cau) - cung
                      mot nguoi hay duoc ghi 'PGS.TS. Bui Nguyen Quoc Trinh' o dong
                      nay va 'Bui Nguyen Quoc Trinh' o dong kia. Thieu GV thi cac
                      dong DONG GIANG (mot lop nhieu GV, moi nguoi mot dong) bi gop
                      lam mot -> mat GV thu 2 tro di.
      - GIO         : Thu + tiet dau + tiet cuoi. Thieu gio thi cac buoi KHAC NHAU
                      trong tuan cua cung mot lop bi gop lam mot -> mat buoi day.
      - CTDT        : chuan hoa thu tu ghep (canonical_program_name) de
                      'ESCT+BICA' va 'BICA+ESCT' ra cung mot khoa. Thieu CTDT thi
                      cac dong HOC GHEP (nhieu CTDT hoc chung mot buoi, moi CTDT
                      mot dong voi si so rieng) bi gop lam mot -> mat si so: dong
                      HIS1001 co 5 CTDT tong 244 SV se chi con 91.
    """
    return (
        (r["classCode"] or "").strip().lower(),
        fate_import.khoa_gv(r["teacherName"] or ""),
        r["day"], r["periodStart"], r["periodEnd"],
        canonical_program_name((r["program"] or "").strip()).lower(),
    )


def bo_dong_nhap_trung(rows):
    """Bo cac DONG NHAP TRUNG, moi nhom chi giu dong co SO SV DU KIEN lon nhat.

    Vi sao lay dong SV lon nhat chu khong cong don: hai dong trung nhau la CUNG
    MOT lop duoc hai nguoi nhap hai lan (vd khoa nhap va CTDT nhap lai), moi nguoi
    ghi mot con so uoc luong - vd SAS3039 co dong ghi 17 SV, dong ghi 20 SV cho
    dung mot lop ESAS. Cong don thanh 37 la dem sinh vien hai lan. Con cac dong
    HOC GHEP (nhieu CTDT that su hoc chung) KHONG bi coi la trung ca - CTDT nam
    trong khoa gom, xem _khoa_trung().

    Dong KHONG CO MA LOP duoc giu nguyen het: khong co gi dinh danh lop thi khong
    the ket luan hai dong la mot. Trong file that co 10 dong bo trong ma lop, bo
    trong ca gio, thuoc 10 CTDT khac nhau - gop theo cac truong con lai se lam
    rung 9 lop that.

    Tra ve (rows_giu, canh_bao) - canh_bao dung khuon {row, kind, detail} de vao
    thang bang "Nen ra lai" o buoc xem truoc.
    """
    nhom = {}
    thu_tu = []
    giu_nguyen = []
    for r in rows:
        if not (r["classCode"] or "").strip():
            giu_nguyen.append(r)
            continue
        k = _khoa_trung(r)
        if k not in nhom:
            nhom[k] = []
            thu_tu.append(k)
        nhom[k].append(r)

    ra, canh_bao = [], []
    for k in thu_tu:
        ds = nhom[k]
        if len(ds) == 1:
            ra.append(ds[0])
            continue
        # max() tra ve phan tu DAU trong cac phan tu bang nhau -> trung si so thi
        # giu dong xuat hien truoc trong file, on dinh giua cac lan nap.
        giu = max(ds, key=_so_sv)
        ra.append(giu)
        bo = [x for x in ds if x is not giu]
        canh_bao.append({
            "row": giu["excelRow"], "kind": "dong_nhap_trung",
            "detail": (
                f"“{k[0]}” · {k[5] or 'không CTĐT'} · "
                + (f"thứ {k[2] + 2}, tiết {k[3]}-{k[4]}" if k[2] is not None else "chưa có giờ")
                + f" — {len(ds)} dòng "
                + " · ".join(
                    f"dòng {x['excelRow']}: {'—' if _so_sv(x) < 0 else int(_so_sv(x))} SV"
                    + (" (GIỮ)" if x is giu else "")
                    for x in ds
                )
            ),
        })

    # Tra lai dung THU TU trong file (theo dong Excel) - buoc xem truoc va cac bang
    # ben duoi doc theo thu tu nay.
    ra.extend(giu_nguyen)
    ra.sort(key=lambda r: (r["excelRow"], r["day"] if r["day"] is not None else -1,
                           r["periodStart"] or 0))
    return ra, canh_bao
