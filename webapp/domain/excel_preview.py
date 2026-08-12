# -*- coding: utf-8 -*-
"""BAN XEM TRUOC khi nap file Excel: gom cac dong bi bo / can luu y theo LOAI.

Gom theo loai roi moi hien - ban dau tra ve danh sach phang roi cat 20 dong dau,
ra man hinh thanh 20 dong lap y het nhau va mot dong "...va 12 dong nua cung loai"
khong ai hieu la loai gi. Nguoi dung can biet QUY TAC nao lam dong bi bo, kem so
luong - khong phai doc tung dong mot.

Tach khoi domain/excel_rows.py: day la tang BAO CAO cho giao dien, khong tham gia
vao viec dung du lieu.
"""

import fate_audit
import fate_import


# Nhan doc duoc cho tung LOAI dong bi bo / dong can luu y. Gom theo loai roi moi
# hien - ban dau tra ve danh sach phang rồi cat 20 dong dau, ra man hinh thanh 20
# dong lap y het nhau va mot dong "…va 12 dong nua cung loai" khong ai hieu la
# loai gi. Nguoi dung can biet QUY TAC nao lam dong bi bo, kem so luong - khong
# phai doc tung dong mot.
NHAN_BO_QUA = {
    "don_vi_dieu_phoi": "Ô giảng viên ghi tên một ĐƠN VỊ điều phối, không phải một người cụ thể",
    "thieu_ten_hoc_phan": "Không xác định được Tên học phần cho dòng đó",
    "o_gv_rong": "Ô giảng viên rỗng sau khi tách tên",
}
NHAN_LUU_Y = {
    "chua_phan_cong": "Lớp CHƯA phân công giảng viên — vẫn nạp đủ, ô giảng viên giữ nguyên "
                      "như trong file (hoặc để trống) để gán sau",
    "thieu_ten_hoc_phan": "Dòng không có Tên học phần ở bất kỳ dòng nào phía trên — "
                          "đặt tạm tên theo mã lớp, sửa lại trong form",
    "dong_giang": "Ô ghi nhiều giảng viên đồng giảng — TẤT CẢ đều được ràng buộc lịch cho "
                  "lớp này (người đầu là GV chính để hiển thị); email/SĐT chia theo vị trí "
                  "khi số lượng khớp số người, học hàm chỉ gán cho người đầu",
    "nhieu_buoi": "Dòng ghi nhiều buổi trong tuần — tách thành nhiều lớp cùng mã lớp",
    "gop_giang_vien": "Cùng một họ tên nhưng ghi nhiều đơn vị công tác khác nhau — "
                      "đã gộp làm một người và lấy đơn vị ghi đầu tiên",
    "gop_bien_the_ten": "Cùng một người nhưng file ghi tên nhiều kiểu (có/không học hàm, "
                        "khác dấu cách, có số thứ tự) — đã gộp làm một người; nên rà lại "
                        "để chắc không phải hai người khác nhau",
    "dong_nhap_trung": "NHẬP TRÙNG: nhiều dòng cùng mã lớp + cùng giảng viên + cùng giờ + "
                       "cùng CTĐT — đã giữ dòng có Số SV dự kiến LỚN NHẤT và bỏ các dòng "
                       "còn lại (hai dòng trùng là một lớp được nhập hai lần, cộng dồn sĩ "
                       "số sẽ đếm sinh viên hai lần). Các lớp HỌC GHÉP — nhiều CTĐT học "
                       "chung một buổi — KHÔNG bị gộp, vẫn giữ đủ từng dòng",
    "ngay_ngoai_quy_dinh_giu_nguyen": "Dạy Thứ 7/Chủ nhật, ngoài quy định (thỉnh giảng tới "
                                      "Thứ 7, cơ hữu tới Thứ 6) — GIỮ NGUYÊN vì là giờ đã "
                                      "chốt trong file, hệ thống không tự đổi",
    "gio_ngoai_pham_vi_tiet": "Tiết trong file quá lớn, không thể là giờ học thật — đã bỏ giờ, "
                              "chuyển \"để hệ thống tự xếp\" (lớp vẫn được nạp đủ)",
    "noi_so_tiet": "File có giờ vượt số tiết/ngày mặc định — đã nới số tiết/ngày cho cả thời "
                   "khoá biểu để giữ đúng giờ trong file",
}


def gom_theo_loai(items, nhan_map):
    """Gom danh sach {row, kind, detail} theo `kind`. Moi nhom kem so luong, danh
    sach so dong Excel, va cac gia tri `detail` khac nhau da gap (co dem)."""
    nhom = {}
    for x in items:
        kind = x.get("kind", "khac")
        g = nhom.setdefault(kind, {"loai": kind, "nhan": nhan_map.get(kind, kind),
                                   "so": 0, "dong": [], "_ct": {}})
        g["so"] += 1
        if x.get("row") is not None:
            g["dong"].append(x["row"])
        d = (x.get("detail") or "").strip()
        if d:
            g["_ct"][d] = g["_ct"].get(d, 0) + 1
    out = []
    for g in nhom.values():
        g["chiTiet"] = [{"text": t, "so": n}
                        for t, n in sorted(g.pop("_ct").items(), key=lambda kv: -kv[1])]
        out.append(g)
    return sorted(out, key=lambda g: -g["so"])


def build_import_preview_response(result, data, loi, canh_bao_gv, file_name):
    """Gop ket qua doc file thanh BAN XEM TRUOC cho UI."""
    summary = fate_import.summarize(result)
    summary["soLopDungDuoc"] = len(data["sections"])
    summary["soGiangVien"] = len(data["teachers"])
    summary["soHocPhan"] = len(data["courses"])

    all_warnings = result["warnings"]
    summary["soCanhBao"] = len(all_warnings) + len(canh_bao_gv)
    data_issues = fate_audit.kiem_tra(result["rows"], data["teachers"])

    return {
        "fileName": file_name,
        "summary": summary,
        # Gom theo LOAI, khong cat top-20: so nhom it (2-3) nen gui het duoc, ma
        # nguoi dung doc mot cai la biet ngay co bao nhieu kieu dong bi bo va moi
        # kieu bao nhieu dong.
        "skippedGroups": gom_theo_loai(result["skipped"], NHAN_BO_QUA),
        "warningGroups": gom_theo_loai(all_warnings + canh_bao_gv, NHAN_LUU_Y),
        # LOI TRONG CHINH FILE (khac warningGroups - xem fate_audit): ma lop dung
        # cho 2 hoc phan, ten khac dau thanh 2 hoc phan, mot email 2 nguoi, dong
        # nhap trung... Import khong sai o dau ca, nhung du lieu ra khong dung y.
        "dataIssues": data_issues,
        "dataIssuesSummary": fate_audit.tom_tat(data_issues),
        "errors": loi[:20],
        "sampleRows": [
            {
                "excelRow": r["excelRow"], "courseCode": r["courseCode"],
                "courseName": r["courseName"], "classCode": r["classCode"],
                "program": r["program"], "teacherName": r["teacherName"],
                "day": r["day"], "periodStart": r["periodStart"], "periodEnd": r["periodEnd"],
            }
            for r in result["rows"][:8]
        ],
    }
