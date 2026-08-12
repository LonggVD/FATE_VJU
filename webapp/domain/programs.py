# -*- coding: utf-8 -*-
"""CHUONG TRINH DAO TAO (CTDT): tach o ghep, chuan hoa ten, cap program_id.

O CTDT trong file Excel vua la MA ghep ("BCSE+MJM" = lop cua ca hai chuong
trinh) vua co the chua GHI CHU cua giao vu ("BCSE (voi nhung SV chua hoc o ky
1)"). Toan bo viec go hai thu do ra nam trong module nay.
"""

import re

# Chuan hoa program_id: chi tach dau ghep that su. KHONG dung cho bo loc.
PROGRAM_SPLIT_RE = re.compile(r"[+.]")

# Rieng cho BO LOC: ngoac va " - " trong file that vua dung de ghep ma
# ('BICA (+ESCT)') vua de ghi chu ('BCSE (voi nhung SV...)', 'ESAS - Hoc ghep
# voi cac lop khac') nen phai cat ca hai roi loc bo ghi chu, xem tach_phan().
# Khong gop vao PROGRAM_SPLIT_RE: ham canonical_program_name dat TEN chuong
# trinh, cat ngoac o do se doi 'BCSE (voi nhung SV chua hoc o ky 1)' thanh mot
# ten khac han.
PROGRAM_PART_RE = re.compile(r"[+.()\[\]]|\s-\s")

KHOA_SPLIT_RE = re.compile(r"[+,;/]")


def _la_ghi_chu(phan):
    """Phan nay la GHI CHU cua giao vu chu khong phai mot ma?

    Ma chuong trinh/khoa la mot tu ('BCSE', 'Chung', 'VJU2024'). Ghi chu la mot
    cau: 'voi nhung SV da hoc Triet', 'Hoc ghep voi cac lop khac'. Moc phan biet:
    >= 2 tu VA co chu thuong - du de giu 'Chung' (1 tu) va loai het cac cau that
    gap trong 3 file.
    """
    return len(phan.split()) >= 2 and any(c.islower() for c in phan)


def tach_phan(raw, chia_re):
    """Tach mot o GHEP thanh cac thanh phan: 'BCSE+MJM' -> ['BCSE', 'MJM'],
    'VJU2023+VJU2024' -> ['VJU2023', 'VJU2024'].

    Dung cho BO LOC: mot lop ghi 'BCSE+MJM' la lop cua CA HAI chuong trinh, nen
    loc 'BCSE' phai ra ca no. Truoc day loc so khop nguyen chuoi -> 'BCSE+MJM'
    thanh mot muc RIENG trong danh sach chon, va chon 'BCSE' thi khong thay lop
    do dau. Cung the voi khoa, cong them chuyen 'VJU2023+VJU2024' va
    'VJU2024+VJU2023' hien thanh HAI muc gan giong nhau.

    NGOAC lam duoc CA HAI viec trong file that, nen phai cat theo ngoac roi moi
    xet tung phan:
        'BICA (+ESCT)'                        -> ngoac chua MA thu hai
        'BCSE (voi nhung SV chua hoc o ky 1)' -> ngoac chua GHI CHU
    Cat theo ngoac ma khong xet thi ra 'BICA (' va 'ESCT)'; con bo thang phan
    trong ngoac thi mat ESCT. Nen: cat, roi bo phan nao la ghi chu
    (_la_ghi_chu). Con lai rong (ca o chi la mot cau) thi tra ve nguyen o - tha
    de bo loc co mot muc xau con hon lam bien mat lop khoi moi bo loc.
    """
    tho = [p.strip(" \t.,;/+-()[]") for p in chia_re.split(raw or "")]
    phan = [p for p in tho if p and not _la_ghi_chu(p)]
    if phan:
        return phan
    goc = " ".join(str(raw or "").split())
    return [goc] if goc else []


def canonical_program_name(raw):
    """Chuan hoa ten chuong trinh GHEP ve 1 dang duy nhat: tach theo dau '+' hoac
    '.', sap xep cac phan theo alphabet, noi lai bang '+'. Vi du that trong file
    Excel: 'FTH+ESAS', 'ESAS+FTH', 'FTH.ESAS' deu la MOT chuong trinh nhung viet
    3 kieu khac nhau -> neu khong chuan hoa thi thanh 3 program_id rieng, khien
    19 'chuong trinh' thuc chat chi la 13, va DPV cua cung 1 pham vi bi tach doi
    (DPV-FTH+ESAS / DPV-ESAS+FTH).
    Chuong trinh 1-thanh-phan (vd 'BCSE') tra ve nguyen ven, khong dung den ham nay."""
    parts = [p.strip() for p in PROGRAM_SPLIT_RE.split(raw) if p.strip()]
    if len(parts) <= 1:
        return raw
    return "+".join(sorted(parts))


def get_or_create_program(data, program_name):
    """Tra ve program_id da co neu trung ten (khong phan biet hoa/thuong, VA
    khong phan biet thu tu ghep '+'/'.' - dung canonical_program_name de tranh
    tao 2 CTDT rieng cho 'FTH+ESAS' va 'ESAS+FTH'), tao moi neu chua co - dung
    khi giao vu nhap tay ten CTDT tu do, khong chon tu danh sach co san."""
    program_name = (program_name or "").strip() or "Chung"
    canon = canonical_program_name(program_name).lower()
    rev = data.setdefault("program_names_reverse", {})
    for pid, name in rev.items():
        if canonical_program_name(name).lower() == canon:
            return pid
    pid = len(data["program_faculty"])
    while pid in data["program_faculty"]:
        pid += 1
    rev[pid] = program_name
    data["programs"].append(pid)
    data["program_faculty"][pid] = 0  # nhap tay: dung chung 1 "khoa" mac dinh cho don gian
    data["coordinator_names"][pid] = f"DPV-{program_name}"
    data["num_programs"] = len(data["program_faculty"])
    return pid


def program_ids_cua_lop(data, program_name):
    """CTDT cua mot lop -> DANH SACH program_id, moi THANH PHAN mot id.

    Chot voi khoa: o ghi "BCSE+MJM" la lop cua CA HAI chuong trinh, khong phai mot
    chuong trinh thu ba ten "BCSE+MJM". Truoc day ca chuoi ghep thanh MOT
    program_id rieng, keo theo hai cho sai:
      - check_cross_program_conflicts coi "BCSE+MJM" khac "BCSE" nen GV day ca hai
        khong bi tinh la day lien chuong trinh (bo sot);
      - dieu phoi vien sinh ra ten "DPV-BCSE+MJM", trong khi thuc te la DPV cua
        BCSE va DPV cua MJM - hai nguoi.

    Ten hien thi VAN giu nguyen nhu file (section['program_raw']) - day chi la cach
    he thong HIEU o do, khong phai cach no VIET ra."""
    phan = tach_phan(program_name, PROGRAM_PART_RE) or ["Chung"]
    ids, da_co = [], set()
    for ten in phan:
        pid = get_or_create_program(data, ten)
        if pid not in da_co:
            da_co.add(pid)
            ids.append(pid)
    return ids
