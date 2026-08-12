# -*- coding: utf-8 -*-
"""HOC CHUNG: nhieu lop (nhieu MA MON khac nhau) thuc chat la MOT buoi day.

Vi du that trong file HK1 2026-2027-3:
    #235 ECE3083 "Vat lieu tien tien trong xay dung"  GV#102  LAB  3 tiet  T4 2-4
    #317 BCE3023 "Vat lieu tien tien trong ky thuat"  GV#102  LAB  3 tiet  T4 2-4
Mot thay, mot phong, mot khung gio, sinh vien hai chuong trinh ngoi chung. Khoa
ghi thanh hai dong vi hai chuong trinh dao tao co ma mon rieng.

VI SAO KHONG CHI LA "TAT CANH BAO": truoc khi co co che nay, bam Giai la MAT MOT
BUOI - `AddNoOverlap` cua GV#102 cam hai buoi chong gio, ma ca hai deu bi ghim
vao dung slot 27, nen CP-SAT buoc phai bo mot (#317 roi vao "khong xep duoc",
blocker chinh la #235). Nen mot nhom hoc chung keo theo BA rang buoc, khong phai
mot:
    1. Khong bao trung GV giua cac thanh vien
    2. Solver EP cung slot (khong thi lan Giai sau lai tach chung ra)
    3. Chi ton MOT phong (AddCumulative dem moi lop 1 phong)

Chinh sach (tao/xoa/validate/tai lap) nam o day; hai phep TRA CUU ma solver can
nam o scheduler_core.py (cac_nhom_hoc_chung / dai_dien_hoc_chung /
cung_nhom_hoc_chung) de module do khong phai import gi tu webapp.

MOI CHO KIEM TRUNG GIANG VIEN phai goi cung_nhom_hoc_chung() - sot mot cho la
hai man hinh noi hai chuyen khac nhau ve cung mot cap lop:
    backend   scheduler_core.solve_guest_phase / solve_resident_phase (rang buoc)
              scheduler_core.check_cross_program_conflicts
              domain/pinning.py: detect_move_conflict
              api/schedule.py: api_save_schedule -> schedule_status
    frontend  adapters/problemInbox.js: scanTeacherClashes + scanPlacedClashes
              adapters/unplacedAnalysis.js
"""

import datetime

import scheduler_core as sc
from domain.time_rules import apply_section_time


def cac_nhom(data):
    """Danh sach nhom THO nhu dang luu (ke ca nhom da hong sau khi xoa lop)."""
    return data.setdefault("hoc_chung", [])


def nhom_cua(data, sid):
    """Nhom (ban ghi day du) chua lop nay, hoac None."""
    for nhom in cac_nhom(data):
        if sid in (nhom.get("sectionIds") or []):
            return nhom
    return None


def thanh_vien(data, sid):
    """Cac lop CUNG BUOI voi lop nay (ke ca chinh no). [] neu khong hoc chung."""
    for ds in sc.cac_nhom_hoc_chung(data):
        if sid in ds:
            return ds
    return []


def _id_moi(data):
    return max((n.get("id", -1) for n in cac_nhom(data)), default=-1) + 1


def kiem_tra_nhom(data, section_ids):
    """Validate DANH SACH lop truoc khi tao nhom. Tra ve (ds_da_chuan_hoa, err).

    Khong sua gi ca - tach rieng khoi tao_nhom() de tang API kiem TRUOC roi moi
    quyet dinh, va de thu tu thong bao loi dung: "khac so tiet" phai duoc bao
    truoc "hoc phan da chot lich", vi mot phep gop vo nghia thi khong con y nghia
    ban ve cam ket gio nua.

    Validate that chat, vi sai o day la solver ra ket qua vo nghia:
      - >= 2 lop, deu ton tai, khong trung nhau
      - cung DO DAI buoi: mot buoi khong the vua 2 tiet vua 3 tiet
      - cung LOAI PHONG: khong the vua o giang duong vua o phong lab
      - cung GIAI DOAN (teacher_type): hai pha giai la HAI mo hinh CP-SAT rieng,
        khong the rang buoc `start` cheo giua chung
      - chua thuoc nhom khac (muon gop them thi bo nhom cu truoc, de giao vu thay
        ro minh dang lam gi)
    """
    ds = []
    for raw in section_ids or []:
        try:
            sid = int(raw)
        except (TypeError, ValueError):
            return None, f"sectionIds có giá trị sai: {raw!r}."
        if sid not in data["sections"]:
            return None, f"Không tìm thấy lớp id={sid}."
        if sid not in ds:
            ds.append(sid)
    if len(ds) < 2:
        return None, "Cần chọn ít nhất 2 lớp để đánh dấu học chung."

    for sid in ds:
        cu = nhom_cua(data, sid)
        if cu is not None:
            return None, (f"Lớp #{sid} đã thuộc một nhóm học chung khác "
                          f"(nhóm #{cu.get('id')}). Bỏ nhóm đó trước.")

    secs = [data["sections"][sid] for sid in ds]
    if len({s["duration"] for s in secs}) > 1:
        return None, ("Các lớp học chung phải có cùng SỐ TIẾT mỗi buổi — đang là "
                      + ", ".join(f"#{s['id']}: {s['duration']} tiết" for s in secs) + ".")
    if len({s["room_type"] for s in secs}) > 1:
        return None, ("Các lớp học chung phải cùng LOẠI PHÒNG — đang là "
                      + ", ".join(f"#{s['id']}: {s['room_type']}" for s in secs) + ".")
    if len({s["teacher_type"] for s in secs}) > 1:
        # Hai pha giai la hai mo hinh CP-SAT rieng biet; khong the ep cung gio
        # giua mot lop o Giai doan 1 va mot lop o Giai doan 2.
        nhan = {"GUEST": "Thỉnh giảng", "RESIDENT": "Cơ hữu"}
        return None, ("Các lớp học chung phải cùng giai đoạn xếp lịch — đang là "
                      + ", ".join(f"#{s['id']}: {nhan.get(s['teacher_type'], s['teacher_type'])}"
                                  for s in secs)
                      + ". Sửa loại giảng viên cho khớp trước.")
    return sorted(ds), None


def tao_nhom(data, section_ids, by=None, note=None):
    """Danh dau cac lop nay la HOC CHUNG. Tra ve (nhom, err).

    Gio: cac lop duoc dong bo ve gio cua DAI DIEN (xem gio_dai_dien). Neu ca nhom
    deu chua co gio thi de nguyen - solver se tu chon mot gio chung nho rang buoc
    same-slot."""
    ds, err = kiem_tra_nhom(data, section_ids)
    if err:
        return None, err

    nhom = {
        "id": _id_moi(data),
        "sectionIds": ds,
        # Ma lop cua tung thanh vien - de TAI LAP nhom sau khi nap lai file Excel
        # (section id sinh lai moi lan nap, ma lop thi den tu file nen ben).
        "classCodes": [(data["sections"][s].get("class_code") or "").strip() for s in ds],
        "by": (by or "").strip() or "Giáo vụ",
        "at": datetime.datetime.now().isoformat(timespec="seconds"),
        "note": (note or "").strip(),
    }
    cac_nhom(data).append(nhom)
    dong_bo_gio_nhom(data, nhom)
    return nhom, None


def gio_dai_dien(data, section_ids):
    """Gio ma CA NHOM se dung, dang time_info (hoac None neu ca nhom chua co gio).

    Dai dien = thanh vien dau tien (id nho nhat) CO gio co dinh. Ca nhom chua co
    gio thi tra None: khong ai ap gio cho ai, solver se tu chon mot gio chung nho
    rang buoc same-slot.

    Tach rieng khoi dong_bo_gio_nhom() de tang API BIET TRUOC gio se la gi, tu do
    chi chan mon "da chot lich" khi gio THUC SU doi - hai lop von da cung gio (dung
    truong hop pho bien nhat: giao vu danh dau chinh cap dang bi bao trung) thi
    khong dung gi den cam ket nao ca."""
    ds = sorted(sid for sid in section_ids if sid in data["sections"])
    goc = next((sid for sid in ds
                if not data["sections"][sid].get("time_assumed")
                and data["sections"][sid].get("original_slot") is not None), None)
    if goc is None:
        return None
    s_goc = data["sections"][goc]
    if s_goc.get("day") is not None:
        return {"day": s_goc["day"], "period_start": s_goc["period_start"],
                "period_end": s_goc["period_end"]}
    # Lop chi co original_slot (nap tu Excel) - suy lai Thu/tiet tu slot.
    day, tiet0 = divmod(s_goc["original_slot"], data["params"]["slotsPerDay"])
    return {"day": day, "period_start": tiet0 + 1, "period_end": tiet0 + s_goc["duration"]}


def dong_bo_gio_nhom(data, nhom):
    """Dua moi thanh vien ve DUNG gio cua dai dien - mot buoi thi mot gio.

    Dung apply_section_time() chu khong tu ghi day/period: no la CHO DUY NHAT biet
    luat sinh submissions/pending, ma solver doc chinh submissions do.
    """
    ds = [sid for sid in nhom["sectionIds"] if sid in data["sections"]]
    time_info = gio_dai_dien(data, ds)
    if time_info is None:
        return []
    doi = []
    for sid in ds:
        s = data["sections"][sid]
        if (s.get("day") == time_info["day"]
                and s.get("period_start") == time_info["period_start"]
                and not s.get("time_assumed")):
            continue
        teacher = data["teachers"][(s.get("teacher_ids") or [s["teacher_id"]])[0]]
        apply_section_time(data, sid, teacher, s["duration"], time_info)
        doi.append(sid)
    return doi


def _nhan_pha(loai):
    return {"GUEST": "Thỉnh giảng", "RESIDENT": "Cơ hữu"}.get(loai, loai)


def kiem_tra_sua_lop(data, sid, fields):
    """Loi (str) neu SUA lop nay lam nhom hoc chung khong con la mot buoi - hoac None.

    Ba dieu kien o kiem_tra_nhom() duoc kiem luc TAO nhom, nhung khong ai canh ve
    sau: do thuc te truoc khi co ham nay, sua so tiet cua mot thanh vien tu 2 len 3
    van duoc chap nhan va nhom van con - solver ep cung `start` nhung hai buoi ket
    thuc khac nhau, tuc khong con la mot buoi day.

    TU CHOI thay vi tu tach nhom: bat giao vu tach truoc roi sua, dung cach chot
    lich dang lam ("Bo chot hoc phan truoc khi sua gio") - co y thuc va co dau vet,
    thay vi sua xong moi biet nhom da tan.
    """
    ds = [x for x in thanh_vien(data, sid) if x != sid]
    if not ds:
        return None
    khac = [data["sections"][x] for x in ds]
    ten = ", ".join(f"#{x['id']}" + (f" ({x.get('class_code')})" if x.get("class_code") else "")
                    for x in khac)
    duoi = f" Lớp học chung với {ten} — tách nhóm học chung trước."

    if fields.get("duration") is not None and any(x["duration"] != fields["duration"] for x in khac):
        return (f"Không đổi được số tiết: các lớp học chung phải cùng số tiết mỗi buổi "
                f"(các lớp kia đang {', '.join(str(x['duration']) for x in khac)} tiết)." + duoi)
    if fields.get("room_type") and any(x["room_type"] != fields["room_type"] for x in khac):
        return (f"Không đổi được loại phòng: các lớp học chung phải cùng loại phòng "
                f"(các lớp kia đang {', '.join(x['room_type'] for x in khac)})." + duoi)
    if fields.get("teacher_type") and any(x["teacher_type"] != fields["teacher_type"] for x in khac):
        # Hai pha giai la HAI mo hinh CP-SAT rieng - khong the rang buoc `start`
        # cheo giua chung, nen nhom vat qua hai pha se mat rang buoc cung gio ma
        # KHONG bao gi ca (vo am tham).
        return (f"Không đổi được giảng viên: đổi thế này làm lớp chuyển sang "
                f"{_nhan_pha(fields['teacher_type'])} trong khi các lớp học chung với nó vẫn là "
                f"{', '.join(_nhan_pha(x['teacher_type']) for x in khac)}. Hai giai đoạn xếp lịch "
                f"là hai bài toán riêng, không thể buộc cùng giờ được." + duoi)
    return None


def tach_nhom_khong_hop_le(data):
    """Tach cac nhom da MAT dieu kien (khac so tiet/loai phong/giai doan). Tra ve
    danh sach {id, sectionIds, vi_sao} de bao len giao dien.

    Dung cho cac thao tac HANG LOAT khong the "tu choi mot phep sua" duoc: nap
    danh sach GV co huu hay doi loai mot GV se phan loai lai NHIEU lop cung luc,
    trong do co the co thanh vien nhom bi lech pha. O do khong con phep sua nao de
    chan, nen phai tach nhom va NOI RA - de yen thi nhom mat rang buoc cung gio ma
    khong ai biet."""
    da_tach = []
    for nhom in list(cac_nhom(data)):
        ds = [x for x in (nhom.get("sectionIds") or []) if x in data["sections"]]
        if len(ds) < 2:
            continue
        secs = [data["sections"][x] for x in ds]
        vi_sao = None
        if len({x["duration"] for x in secs}) > 1:
            vi_sao = "các lớp không còn cùng số tiết mỗi buổi"
        elif len({x["room_type"] for x in secs}) > 1:
            vi_sao = "các lớp không còn cùng loại phòng"
        elif len({x["teacher_type"] for x in secs}) > 1:
            vi_sao = ("các lớp không còn cùng giai đoạn xếp lịch ("
                      + ", ".join(f"#{x['id']}: {_nhan_pha(x['teacher_type'])}" for x in secs) + ")")
        if vi_sao:
            xoa_nhom(data, nhom.get("id"))
            da_tach.append({"id": nhom.get("id"), "sectionIds": ds, "vi_sao": vi_sao})
    return da_tach


def xoa_nhom(data, nhom_id):
    """Bo mot nhom hoc chung. Tra ve nhom vua bo, hoac None neu khong co."""
    ds = cac_nhom(data)
    for i, nhom in enumerate(ds):
        if nhom.get("id") == nhom_id:
            return ds.pop(i)
    return None


def don_nhom_hong(data):
    """Bo cac nhom khong con y nghia sau khi xoa lop (con < 2 thanh vien).

    Goi sau moi lan xoa lop: mot nhom con MOT lop khong con la "hoc chung", de lai
    thi giao dien hien badge "Học chung" tren mot buoi don doc."""
    ds = cac_nhom(data)
    giu = []
    for nhom in ds:
        con = [sid for sid in (nhom.get("sectionIds") or []) if sid in data["sections"]]
        if len(con) > 1:
            nhom["sectionIds"] = con
            giu.append(nhom)
    ds[:] = giu


# --- Ben qua cac lan NAP LAI FILE ------------------------------------------
# section id sinh lai tu 0 moi lan nap file, nen nhom khoa theo id se mat sach.
# Ma lop thi den tu chinh file Excel -> dung no lam neo. Giao vu doi file kha
# thuong xuyen (da toi ban -5 trong mot ky) nen khong the bat ho danh dau lai.

def luu_de_tai_lap(data):
    """Ban ghi gon cua cac nhom, chi gom ma lop - de tai lap sau khi nap file."""
    ra = []
    for ds in sc.cac_nhom_hoc_chung(data):
        nhom = nhom_cua(data, ds[0]) or {}
        ma = [(data["sections"][sid].get("class_code") or "").strip() for sid in ds]
        if all(ma) and len(set(ma)) == len(ma):
            ra.append({"classCodes": ma, "by": nhom.get("by"), "note": nhom.get("note")})
    return ra


def tai_lap_theo_ma_lop(data, ds_luu):
    """Ghep lai cac nhom tren bo du lieu MOI theo ma lop. Tra ve (so_nhom, bo_qua).

    Mot ma lop co the ung nhieu section (mot lop nhieu buoi/tuan - xem
    fate_import 'nhieu_buoi'). Ghep theo (ma lop, gio) de tung BUOI vao dung nhom
    cua no: hai mon hoc chung thi buoi Thu 4 cua mon nay di voi buoi Thu 4 cua mon
    kia, khong phai voi buoi Thu 6.
    """
    theo_ma = {}
    for sid, s in data["sections"].items():
        ma = (s.get("class_code") or "").strip()
        if ma:
            theo_ma.setdefault(ma, []).append(sid)

    so, bo_qua = 0, []
    for luu in ds_luu or []:
        ma_ds = luu.get("classCodes") or []
        if not all(m in theo_ma for m in ma_ds):
            bo_qua.append({"classCodes": ma_ds, "vi_sao": "không còn mã lớp này trong dữ liệu mới"})
            continue
        # Ghep theo GIO: gom cac buoi cung slot lai thanh mot nhom.
        theo_slot = {}
        for m in ma_ds:
            for sid in theo_ma[m]:
                theo_slot.setdefault(data["sections"][sid].get("original_slot"), {}) \
                    .setdefault(m, []).append(sid)
        da_ghep = False
        for slot, theo_m in sorted(theo_slot.items(), key=lambda kv: (kv[0] is None, kv[0])):
            if len(theo_m) < len(ma_ds):
                continue  # slot nay khong co du moi ma lop -> khong phai buoi hoc chung
            chon = [sorted(theo_m[m])[0] for m in ma_ds]
            _, err = tao_nhom(data, chon, luu.get("by"), luu.get("note"))
            if err is None:
                so += 1
                da_ghep = True
        if not da_ghep:
            bo_qua.append({"classCodes": ma_ds,
                           "vi_sao": "không tìm được buổi nào có đủ các mã lớp ở cùng giờ"})
    return so, bo_qua
