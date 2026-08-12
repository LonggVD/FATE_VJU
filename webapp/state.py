# -*- coding: utf-8 -*-
"""STATE toan cuc + cac hang so dung chung khap backend.

Module NEN cua ca goi: khong import gi tu webapp ca, nen moi module khac deu
import duoc tu day ma khong sinh vong tron.
"""

# State toan cuc don gian (demo local, 1 nguoi dung tai 1 thoi diem)
STATE = {
    "data": None,
    "extra": None,  # {isRealData, sourceLabel, numTimeAssumed} - luu lai de /api/data doc lai duoc
    "guestResult": None,
    "residentResult": None,
    # section_id(int) -> {"slot": int, "reason": str|None, "problem": dict|None}
    # "Ghim" tu keo-tha sua tay (thay cho tinh nang "Tu choi - luan chuyen" cu).
    # KHAC voi ket qua giai (guestResult/residentResult): overrides KHONG bi xoa
    # khi giai lai - no la RANG BUOC duoc doc lai o moi lan giai (xem
    # domain/pinning.py: solve_guest_with_overrides/ghim_tay_o_giai_doan_2), chi mat
    # khi nap du lieu moi (section id khong con nghia) hoac giao vu tu bo ghim.
    "overrides": {},
    # section_id(int) da bam "Bo ghim" o man TKB = "CHO HE THONG XEP LAI lop nay".
    #
    # Vi sao khong chi xoa khoi overrides: gio doc tu file duoc ghim o HAI cho doc
    # lap - overrides (de UI hien "da ghim") VA chinh solver (`original_slot` /
    # `submissions=[slot]`). Xoa moi overrides thi lan giai sau van ra dung o cu,
    # tuc nut "Bo ghim" khong lam gi ca. Tap nay la cho ghi "giao vu da noi ro y
    # minh", de ca hai duong ghim cung nhin vao.
    "bo_ghim": set(),
    # DANH SACH GIANG VIEN CO HUU cua truong (nap qua /api/manual/lecturers) -
    # NGUON CHINH THUC de phan loai co huu/thinh giang, thay cho viec do chu
    # "Viet Nhat" trong o "Don vi cong tac" cua file ke hoach giang day (o do
    # giao vu go tay moi ky nen bo trong / ghi moi kieu / mot o cho ca nhom).
    # {"byKey": {khoa_ten: {name, gender, faculty, note}}, "fileName", "count"}
    # None = chua nap -> quay ve luat cu theo o don vi.
    "co_huu": None,
    # Ban vua doc tu file, CHUA ap dung (buoc xem truoc) - xem
    # api/lecturers.py: api_manual_lecturers_preview.
    "co_huu_pending": None,
    # MOC HOAN TAC cho nut "Huy thay doi" o man Thoi khoa bieu: ban chup toan bo
    # trang thai tai lan LUU gan nhat (va lan nap file dau tien). Xem domain/hoan_tac.py.
    "moc_hoan_tac": None,
}


DAY_LABELS_VN = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]


# Sentinel: phan biet "khong truyen time_info" voi "truyen None" (= de he thong
# tu xep) - hai truong hop khac han nhau o domain/chot.py: khoa_vi_da_chot.
KHONG_TRUYEN = object()


def reset_ket_qua():
    """Xoa ket qua giai + ghim dang co - dung khi bo du lieu doi han (nap file
    moi/khoi tao lai). section id cua bo cu khong con nghia gi voi bo moi nen
    giu overrides lai la ghim bua vao cac lop khong lien quan."""
    STATE["guestResult"] = None
    STATE["residentResult"] = None
    STATE["overrides"] = {}
    STATE["bo_ghim"] = set()
