# Quy trình nghiệp vụ xếp TKB — 3 vai trò

> Phạm vi: quy trình nghiệp vụ xếp thời khóa biểu (vai trò nào làm gì, input/xử lý/
> output từng bước), áp dụng cho N khoa dùng chung phòng. Không bao gồm phân quyền/
> tài khoản đăng nhập và giao diện cụ thể — xem mục 8.

## 1. Vai trò & trách nhiệm

| Vai trò | Gắn với | Trách nhiệm chính |
|---|---|---|
| **GĐCT** (Giám đốc Chương trình) | 1 chương trình đào tạo (CTĐT), thuộc 1 khoa | Xác định nhu cầu lớp học phần của CTĐT mình; mời giảng viên thỉnh giảng |
| **Chuyên viên Giáo vụ Khoa** | 1 khoa (quản lý nhiều CTĐT/GĐCT) | Tổng hợp input từ các GĐCT trong khoa, xếp TKB **theo thời gian** cho toàn khoa (chưa gán phòng) |
| **Chuyên viên Phòng Đào Tạo** | Toàn trường, dùng chung cho N khoa | Quản lý danh sách phòng của trường; gán **phòng cụ thể** cho TKB (đã có giờ) từ tất cả các khoa |

1 khoa có nhiều CTĐT, mỗi CTĐT có 1 GĐCT phụ trách. Giáo vụ Khoa nhận input từ tất cả
GĐCT thuộc khoa mình rồi mới xếp TKB chung cho khoa.

## 2. Luồng tổng quát

```
[0a] Phòng Đào Tạo: quản lý danh sách phòng toàn trường (nền, ít thay đổi trong kỳ)
[0b] (tuỳ chọn, thủ công) Mô phỏng lại TKB kỳ cũ — dựa vào đó fill TKB kỳ mới,
     không tương đồng thì bỏ qua
        │
        ▼
[1] GĐCT + hệ thống: tính số lớp cần mở cho môn X
        │  output: "Môn X cần K lớp"
        ▼
[2] GĐCT: mời giảng viên thỉnh giảng, cố chốt giờ dạy được
        │  output: GV → môn → (có thể có) khung giờ
        ▼
[3] Giáo vụ Khoa: chỉ khi [2] chưa chốt giờ — liên hệ lại GV để xác nhận khung giờ
        │  output: GV + khung giờ đầy đủ
        ▼
[4] Giáo vụ Khoa: xếp TKB theo THỜI GIAN cho toàn khoa (chưa gán phòng)
        │  output: TKB theo giờ của khoa
        ▼
[5] Phòng Đào Tạo: gán phòng cụ thể, dựa trên TKB của tất cả N khoa cùng lúc
        │
        ▼
   Thời khóa biểu cuối cùng (có phòng) — bảng tổng hợp toàn trường
```

Danh sách phòng ([0a]) cần có sẵn từ sớm — không chỉ để gán phòng ở [5], mà bước [1]
(tính số lớp tối ưu sức chứa) cũng cần dùng dữ liệu sức chứa phòng.

## 3. Chi tiết từng bước

### [0a] Phòng Đào Tạo — quản lý danh sách phòng

Phòng Đào Tạo nắm và cập nhật danh sách phòng của trường, mỗi phòng gồm: tên/mã
phòng, sức chứa, khu vực (Hòa Lạc/Mỹ Đình/...), loại (Lý thuyết/Thực hành), và có thể
kèm khung giờ đã bận sẵn ngoài giảng dạy. Danh sách này dùng ở bước [1] (dạng tổng hợp
sức chứa theo loại) và bước [5] (dạng chi tiết từng phòng + khung giờ trống/bận).

### [0b] Mô phỏng lại TKB kỳ cũ (tuỳ chọn, thủ công)

Dựa vào TKB kỳ trước để fill nhanh TKB kỳ mới — so sánh môn/lớp/GV kỳ mới với kỳ cũ,
môn/lớp nào giống thì tái dùng luôn. Không có điểm tương đồng thì bỏ qua, làm mới hoàn
toàn từ [1]. Chỉ là gợi ý điền nhanh, không bắt buộc và không ảnh hưởng kết quả cuối.

### [1] Tính số lớp cần mở

GĐCT cung cấp số SV dự kiến học môn X trong kỳ (gộp cả SV học lại/trượt vào cùng một
tổng, không tách lớp riêng). Hệ thống dùng tổng SV này cùng sức chứa các phòng cùng
loại (không lọc theo khu vực ở bước này — xem mục 6) để tính số lớp K cần mở, theo
nguyên tắc ở mục 5. Kết quả "Môn X cần K lớp" được gửi cho Giáo vụ Khoa.

### [2] GĐCT mời giảng viên thỉnh giảng

GĐCT mời GV cho các môn cần thỉnh giảng, cố gắng chốt luôn khung giờ GV có thể dạy
ngay lúc mời — GV nào dạy môn nào, có thể dạy ngày nào, khung giờ nào. Kết quả (có thể
đầy đủ khung giờ hoặc còn thiếu nếu GV chưa xác nhận) được gửi cho Giáo vụ Khoa.

### [3] Giáo vụ Khoa bổ sung khung giờ còn thiếu

Với phần GV thỉnh giảng ở [2] chưa có khung giờ, Giáo vụ Khoa liên hệ lại GV để xác
nhận/thu thập khung giờ. Chỉ cần biết GV đã có giờ hay chưa — GV chưa có giờ thì buổi
dạy của GV đó ở trạng thái chờ, không được đưa vào xếp TKB ở [4] cho đến khi có giờ.

### [4] Giáo vụ Khoa xếp TKB theo thời gian

Input: số lớp cần mở theo môn (từ [1], tổng hợp từ mọi GĐCT trong khoa), GV + khung
giờ đầy đủ (từ [2]+[3]), gợi ý từ TKB kỳ cũ (từ [0b], nếu có).

Xếp TKB chỉ dựa vào giờ GV rảnh, không xét khu vực/2 cơ sở (xem mục 6); check trùng
theo giảng viên (đủ dữ liệu vì GV thuộc phạm vi khoa). **Không check trùng phòng ở
bước này** — khoa không thấy TKB của khoa khác, mà phòng là tài nguyên dùng chung
N khoa. Hoàn thiện xếp thời khóa biểu cho tới khi hết khả năng xếp thêm.

Nếu có buổi thỉnh giảng không xếp được, GĐCT/Giáo vụ Khoa mời GV khác hoặc đổi khung
giờ thủ công, rồi nhập lại thông tin mới.

Output: TKB hoàn chỉnh theo thời gian của khoa (giờ dạy theo lớp/môn/GV, chưa gán
phòng) → Phòng Đào Tạo.

### [5] Phòng Đào Tạo gán phòng cụ thể

Input: TKB theo giờ (chưa có phòng) từ tất cả N khoa; danh sách phòng chi tiết + tình
trạng trống/bận theo khung giờ.

Xếp phòng dựa trên TKB của các khoa: gán đúng 1 phòng cho mỗi buổi học, đảm bảo loại
phòng khớp (LT/TH), sức chứa ≥ số SV của lớp, không phòng nào bị 2 khoa dùng trùng
giờ, và xử lý ràng buộc khu vực theo giảng viên (mục 6). Đây là bước duy nhất đủ dữ
liệu để check trùng phòng và khu vực chính xác — lý do phòng phải xét theo TKB của
tất cả khoa cùng lúc.

Output cuối cùng: thời khóa biểu đầy đủ có phòng — bảng tổng hợp tất cả chương trình
của N khoa.

## 4. Thông tin về Phòng học cần quản lý

Mỗi phòng cần các thông tin: tên/mã phòng, sức chứa (số SV tối đa), khu vực (Hòa
Lạc/Mỹ Đình/...), loại (Lý thuyết/Thực hành), và có thể kèm khung giờ đã bận sẵn
ngoài giảng dạy. Sau khi gán phòng ở bước [5], mỗi buổi học cần ghi rõ đã dùng đúng
phòng nào.

Với trường hợp nhiều khoa, cách tổng hợp dữ liệu phòng/TKB từ các khoa khác nhau về
một nơi chung để Phòng Đào Tạo xử lý ở bước [5] — chưa chốt, để quyết định khi triển
khai.

## 5. Nguyên tắc tính số lớp cần mở (bước [1])

Mục tiêu: **tối thiểu hoá ghế trống** (không phải tối thiểu số lớp).

- Input: tổng số SV cần học môn X trong kỳ (đã gộp SV học lại/trượt), danh sách sức
  chứa các phòng cùng loại đang có — xét chung tất cả khu vực.
- Chọn số lớp và sức chứa mục tiêu mỗi lớp sao cho tổng sức chứa các lớp đã chọn sát
  nhất với tổng số SV cần học (không được ít hơn số SV, nhưng dư ra càng ít càng tốt).
- Không cần thêm ràng buộc "sức chứa tối thiểu để mở 1 lớp" riêng: thực tế không có
  phòng nào sức chứa dưới 40 SV và không có môn nào dưới 50 SV theo học, nên mức sàn
  tự nhiên này đã tự đảm bảo không phát sinh lớp quá nhỏ bất thường.

## 6. Ràng buộc khu vực (Hòa Lạc/Mỹ Đình)

2 khu vực cách rất xa nhau, không di chuyển kịp trong ngày — ràng buộc: **trong 1
ngày, 1 giảng viên không được dạy ở cả 2 khu vực**. Ràng buộc này chỉ áp dụng cho
giảng viên; sinh viên đăng ký ở đâu học ở đó, không cần theo dõi/kiểm tra khu vực
học của SV.

Cách xử lý trong luồng:

- **Bước [4]** (Giáo vụ Khoa xếp giờ) chỉ dựa vào giờ GV rảnh, không xét khu vực — vì
  phòng (và do đó khu vực) chưa được gán ở bước này.
- **Bước [5]** (Phòng Đào Tạo gán phòng) là bước duy nhất xét khu vực: vì mỗi phòng
  gắn liền đúng 1 khu vực, gán phòng tức là gán khu vực, nên ràng buộc "1 giảng viên
  không dạy 2 khu vực cùng ngày" được kiểm tra và xử lý ở đây.

Vì giờ đã chốt cứng từ [4] mà không xét khu vực, có thể (hiếm) gặp trường hợp 1 GV bị
đặt 2 buổi dạy cùng ngày mà lúc gán phòng ở [5] không tìm được cách giữ đúng 1 khu vực
cho cả ngày đó. Trường hợp này xử lý bằng cách sửa tay lại TKB giờ ở bước [4] (mục 7).

## 7. Yêu cầu cho phép sắp xếp thủ công

Ở cả 3 bước có tính toán tự động — [1] tính số lớp, [4] xếp giờ, [5] gán phòng —
người phù hợp phải luôn có thể tự tay sửa/ghi đè, không bị bắt buộc dùng đúng kết quả
hệ thống tự tính ra:

| Bước tự động | Cho phép sửa tay gì |
|---|---|
| [1] Tính số lớp | Sửa tay số lớp (và/hoặc sức chứa mục tiêu mỗi lớp) trước khi gửi cho Giáo vụ Khoa |
| [4] Xếp TKB theo giờ | Tự tay xếp/sửa giờ dạy cho 1 hoặc nhiều buổi học, không bắt buộc chạy tự động |
| [5] Gán phòng | Tự tay gán/đổi phòng cụ thể cho 1 buổi học, không bắt buộc theo gán tự động |

## 8. Ngoài phạm vi tài liệu này

- Phân quyền/tài khoản: 3 vai trò (+ quản trị, nếu có) có phải các login riêng, ai
  xem/sửa được gì trong hệ thống thật — để tài liệu riêng.
- Giao diện cụ thể cho từng vai trò.
- Cách tổng hợp dữ liệu phòng/TKB từ nhiều khoa về một nơi chung (mục 4) — chưa chốt.
