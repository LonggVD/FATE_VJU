# -*- coding: utf-8 -*-
"""DUNG BO DU LIEU tu cac dong Excel da chuan hoa (fate_import).

Nguyen tac cua module nay: KHONG tu ghep dict bang tay. Chay lai dung nhung ham
ma duong nhap tay dung (sections.validate_section_body -> programs.
get_or_create_program, time_rules.apply_section_time), de du lieu nap tu file
KHONG khac gi du lieu giao vu go tay - program_id, submissions,
pending_section_ids, room_type... deu do cung mot doan code sinh ra. Neu sau nay
sua luat o do thi ca hai duong deu doi theo.
"""

import fate_import
import scheduler_core as sc
from domain.excel_trung import bo_dong_nhap_trung
from domain.merge import noi_slots_per_day
from domain.sections import empty_manual_data, id_moi, validate_section_body
from domain.teachers import dem_lai_so_gv, loai_gv, phan_tu
from domain.time_rules import apply_section_time
from state import DAY_LABELS_VN

# Bo dong nhap trung nam o domain/excel_trung.py; bao cao xem truoc o
# domain/excel_preview.py - xem docstring cua tung file.


def build_manual_data_from_rows(rows):
    """Dung bo du lieu NHAP TAY tu cac dong Excel da chuan hoa.

    Tra ve (data, loi, canh_bao) - loi la cac dong khong dung duoc section, kem ly do.
    """
    data = empty_manual_data()
    loi = []
    canh_bao = []

    # Bo dong nhap trung TRUOC MOI THU: dong trung se dang ky GV/hoc phan va tao
    # section y nhu dong that, tuc an mot phong rieng va lam solver doi hai lan
    # tai nguyen cho cung mot lop.
    rows, canh_bao_trung = bo_dong_nhap_trung(rows)
    canh_bao.extend(canh_bao_trung)

    # PHAI noi truoc khi dung section: parse_class_time kiem tra tiet <= slotsPerDay
    # va apply_section_time tinh slot = day * slotsPerDay + (tiet - 1).
    spd = noi_slots_per_day(data, rows)
    if spd > empty_manual_data()["params"]["slotsPerDay"]:
        canh_bao.append({
            "row": None, "kind": "noi_so_tiet",
            "detail": f"File có giờ tới tiết {spd} → đặt {spd} tiết/ngày cho cả thời khoá biểu",
        })

    # --- Giang vien: gop theo TEN (da chuan hoa), KHONG theo (ten, don vi) ---
    #
    # Trong file that, cung mot nguoi hay bi ghi don vi moi dong mot kieu:
    # "Truong DH Viet Nhat" / "Truong Dai hoc Viet Nhat", co dong con bo trong.
    # Neu gop theo (ten, don vi) thi mot nguoi tach thanh 2-3 ban ghi -> he thong
    # coi ho la nhung nguoi KHAC NHAU va khong con phat hien duoc ho bi trung
    # lich voi chinh minh, tuc mat dung cong dung chinh cua cong cu. Nang hon:
    # dong bo trong don vi se bi xep GUEST trong khi cac dong khac la RESIDENT,
    # mot nguoi bi chia sang ca hai giai doan.
    #
    # Doi lai, hai nguoi TRUNG HO TEN se bi gop lam mot. Trong pham vi mot file
    # cua mot khoa thi hiem, va huong sai nay AN TOAN hon: gop nham chi lam bao
    # thua xung dot (giao vu nhin ra ngay), con tach nham thi GIAU MAT xung dot.
    # Moi truong hop don vi ghi khac nhau deu duoc bao len o buoc xem truoc.
    teacher_ids = {}
    org_khac = {}
    bien_the = {}

    def _dang_ky_gv(name, org, title, email, phone):
        """Tao moi HOAC dung lai ban ghi GV theo TEN da chuan hoa. Tra ve id.

        Dung chung cho GV chinh va GV dong giang: nguoi dong giang o lop nay co
        the la GV chinh o lop khac, phai ra CUNG mot ban ghi - neu khong thi mot
        nguoi bi tach lam hai va het phat hien duoc trung lich cua chinh ho.

        Khoa gop BO hoc ham/so thu tu/dau cau (fate_import.khoa_gv) - xem chu
        thich o do; ten HIEN THI giu nguyen cach ghi trong file (uu tien ban day
        du hon, thuong la ban co hoc ham).
        """
        name = " ".join(str(name or "").split())
        key = fate_import.khoa_gv(name)
        if key in teacher_ids:
            t = data["teachers"][teacher_ids[key]]
            if name and name != t["name"]:
                bien_the.setdefault(t["id"], {t["name"]}).add(name)
                if len(name) > len(t["name"]):
                    t["name"] = name  # ban ghi day du hon (thuong la co hoc ham)
            if org and org != t["org"]:
                if t["org"]:
                    org_khac.setdefault(t["id"], {t["org"]}).add(org)
                else:
                    # Ban ghi dau bo trong don vi -> lay don vi dau tien tim duoc,
                    # va phan loai lai GUEST/RESIDENT theo no.
                    t["org"] = org
                    t["type"] = loai_gv(org, t["name"])
            # Cac truong con lai: lap day cho nao con trong.
            for field, val in (("title", title), ("email", email), ("phone", phone)):
                if not t[field] and val:
                    t[field] = val
            return teacher_ids[key]

        tid = len(data["teachers"])
        data["teachers"][tid] = {
            "id": tid, "name": name, "type": loai_gv(org, name), "org": org,
            "title": title, "email": email, "phone": phone,
        }
        # Chua khai gio ranh - giao vu se khai sau o "Chuan bi du lieu".
        data.setdefault("manual_teacher_windows", {})[tid] = []
        teacher_ids[key] = tid
        return tid

    for idx, r in enumerate(rows):
        org = r["teacherOrg"].strip()

        # Lop CHUA phan cong giang vien: moi lop mot ban ghi RIENG, khong dung
        # chung mot ban ghi "Phong Dao tao dieu phoi".
        #
        # Dung chung thi he thong coi 60 lop do la CUA MOT NGUOI - do thuc te tren
        # file HK1 cho 54 o gio chong nhau, tuc hop thu van de se ngap bao "trung
        # giang vien" GIA va nhan chim cac vu trung THAT. Ma chung von khong phai
        # mot nguoi, chi la cho trong cho den khi giao vu phan cong.
        #
        # Danh dau `placeholder` de cac man danh cho giang vien that (vd "Gio ranh
        # GV") loc chung ra, khong hien 114 dong "Phong Dao tao dieu phoi".
        if r.get("chuaPhanCong"):
            tid = len(data["teachers"])
            data["teachers"][tid] = {
                # CHO TRONG, khong phai mot con nguoi -> danh sach GV co huu
                # khong the noi gi ve no. Phan loai theo o "Don vi cong tac" nhu
                # cu; giao vu gan GV that thi lop tinh lai theo nguoi do.
                "id": tid, "name": r["teacherName"] or "(Chưa phân công)",
                "type": loai_gv(org),
                "org": org, "title": r["teacherTitle"],
                "email": r["teacherEmail"], "phone": r["teacherPhone"],
                "placeholder": True,
            }
            data.setdefault("manual_teacher_windows", {})[tid] = []
            teacher_ids[f"__chua_phan_cong_{idx}"] = tid
            continue

        _dang_ky_gv(r["teacherName"], org, r["teacherTitle"], r["teacherEmail"], r["teacherPhone"])

        # GV DONG GIANG (o ten ghi nhieu nguoi): moi nguoi mot ban ghi RIENG, de
        # ho cung bi rang buoc lich o lop nay - xem chu thich o
        # sections.validate_section_body. Truoc day chi lay nguoi dau, nen nguoi
        # thu 2+ bien mat khoi lop: ai cung day mot lop khac dung gio nay thi he
        # thong KHONG bao trung, va nguoi khong day lop nao khac thi khong ton tai.
        #
        # Hoc ham chi gan cho nguoi DAU: o "Học hàm, học vị" cua file ghi mot gia
        # tri cho ca o ten (vd "TS." cho 5 nguoi) nen khong the biet chac cua ai.
        for j, ten_dg in enumerate(r.get("coTeacherNames") or []):
            # Don vi RIENG cua tung nguoi khi o do tach duoc (fate_import tach
            # theo vi tri nhu email/SDT); khong tach duoc thi dung chung o.
            _dang_ky_gv(ten_dg, phan_tu(r.get("coTeacherOrgs"), j) or org, "",
                        phan_tu(r.get("coTeacherEmails"), j),
                        phan_tu(r.get("coTeacherPhones"), j))

    for tid, orgs in org_khac.items():
        canh_bao.append({
            "row": None, "kind": "gop_giang_vien",
            "detail": f"{data['teachers'][tid]['name']} — {' · '.join(sorted(orgs))}",
        })
    for tid, tens in bien_the.items():
        canh_bao.append({
            "row": None, "kind": "gop_bien_the_ten",
            "detail": " · ".join(sorted(tens)),
        })

    # --- Hoc phan: gop theo (ma, ten) ---
    course_ids = {}
    for r in rows:
        key = (r["courseCode"].strip().lower(), r["courseName"].strip().lower())
        if key in course_ids:
            continue
        cid = len(data["courses"])
        data["courses"][cid] = {
            "id": cid, "code": r["courseCode"], "name": r["courseName"],
            "credits": r["credits"],
        }
        course_ids[key] = cid

    # --- Lop ---
    for idx, r in enumerate(rows):
        tkey = (f"__chua_phan_cong_{idx}" if r.get("chuaPhanCong")
                else fate_import.khoa_gv(r["teacherName"]))
        body = {
            # Ca nhom trong MOT danh sach, vai tro ngang nhau (nguoi dau la nguoi
            # ghi dau tien trong o ten cua file).
            "teacherIds": [teacher_ids[tkey]] + [
                teacher_ids[fate_import.khoa_gv(n)]
                for n in (r.get("coTeacherNames") or [])
                if fate_import.khoa_gv(n) in teacher_ids
            ],
            "courseId": course_ids[(r["courseCode"].strip().lower(), r["courseName"].strip().lower())],
            "duration": r["duration"] or data["params"]["duration"],
            "classCode": r["classCode"], "program": r["program"],
            "ltCredits": r["ltCredits"], "thCredits": r["thCredits"],
            "cohort": r["cohort"], "expectedStudents": r["expectedStudents"],
            "location": r["location"], "teachingMode": r["teachingMode"],
            "language": r["language"], "otherRequirements": r["otherRequirements"],
            "notes": r["notes"], "coordinatorOverride": r["coordinatorOverride"],
            "prevTeacherName": r["prevTeacherName"], "prevTeacherOrg": r["prevTeacherOrg"],
            "teachingHoursLt": r["teachingHoursLt"], "teachingHoursTh": r["teachingHoursTh"],
        }
        if r["autoSchedule"]:
            body["autoSchedule"] = True
        else:
            body["day"], body["periodStart"], body["periodEnd"] = r["day"], r["periodStart"], r["periodEnd"]

        # enforce_day_cap=False: file that co the co dong vi pham quy tac ngay
        # (vd lop thuc tap co huu ghi Chu nhat) - KHONG duoc lam RUNG ca lop
        # (mat het GV/SV/hoc phan chi vi 1 o gio sai), xem time_rules.parse_class_time.
        fields, teacher, duration, time_info, err = validate_section_body(
            data, body, enforce_day_cap=False,
        )
        if err:
            loi.append({"row": r["excelRow"], "reason": err})
            continue
        if time_info is None and not r["autoSchedule"] and r["day"] is not None:
            # Chi con MOT ly do lam mat gio: tiet vo ly (> MAX_TIET). Ngay ngoai quy
            # dinh khong con bi bo gio nua - xem time_rules.parse_class_time.
            canh_bao.append({
                "row": r["excelRow"], "kind": "gio_ngoai_pham_vi_tiet",
                "detail": (
                    f"“{r['classCode'] or r['courseName'][:30]}” — tiết {r['periodStart']}-"
                    f"{r['periodEnd']} không thể là giờ học thật — đã bỏ giờ, chuyển sang "
                    f"“để hệ thống tự xếp”"
                ),
            })
        elif time_info is not None and time_info["day"] > sc.max_day_index(teacher["type"]):
            # Gio da chot -> GIU NGUYEN, nhung phai noi ra: day la ngoai le so voi
            # quy dinh (thinh giang toi Thu 7, co huu toi Thu 6).
            loai = "Thỉnh giảng" if teacher["type"] == "GUEST" else "Cơ hữu"
            canh_bao.append({
                "row": r["excelRow"], "kind": "ngay_ngoai_quy_dinh_giu_nguyen",
                "detail": (
                    f"{loai} “{r['teacherName']}” dạy {DAY_LABELS_VN[time_info['day']]} — "
                    f"ngoài quy định ({loai} chỉ tới "
                    f"{DAY_LABELS_VN[sc.max_day_index(teacher['type'])]}), "
                    f"nhưng GIỮ NGUYÊN vì là giờ đã chốt trong file"
                ),
            })
        sid = id_moi(data["sections"])
        data["sections"][sid] = {"id": sid, **fields}
        apply_section_time(data, sid, teacher, duration, time_info)

    dem_lai_so_gv(data)
    data["num_time_assumed"] = sum(1 for s in data["sections"].values() if s.get("time_assumed"))
    # Lop dang xep theo "GV chua khai gio ranh nen coi nhu ranh ca tuan" - dem rieng
    # de man hinh noi ro day la GIA DINH, khong phai gio GV da xac nhan.
    data["num_availability_assumed"] = sum(
        1 for s in data["sections"].values() if s.get("availability_assumed"))
    return data, loi, canh_bao
