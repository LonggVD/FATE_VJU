# Nhập dữ liệu từ file Excel vào form "Dữ liệu học phần"

Nạp file kế hoạch giảng dạy của kỳ cũ vào form, để giáo vụ sửa tiếp thay vì gõ lại từ đầu.

## Dùng thế nào

"Dữ liệu học phần" → **Nhập từ Excel** → chọn file `.xlsx` → đọc bản xem trước →
**Xóa dữ liệu cũ và nạp N lớp**.

Hai bước có chủ ý: bước đọc file **không ghi gì cả**, chỉ hiện ra sẽ nạp được những gì.
Import là thao tác xóa hết dữ liệu đang có và **không hoàn tác được**, nên phải cho người
dùng đối chiếu con số trước khi quyết.

## Định dạng nhận được

Tự nhận diện theo tên sheet:

| Sheet | Ví dụ | Ghi chú |
|---|---|---|
| `FATE` | `FATE.TKB.HK2_2025-2026.xlsx` | cấu trúc CHUẨN, dùng cho các kỳ sau |
| `Giảng dạy cho FATE` | `FATE.TKB.HK1 2026-2027.xlsx` | cấu trúc cũ |

Thêm định dạng mới: thêm một mục vào `LAYOUTS` trong `webapp/fate_import.py`, không phải
sửa chỗ nào khác.

**Bảng 29 cột của form chính là bản sao của file HK1** nên ánh xạ gần như 1:1. File HK2
thiếu vài cột (không có "Học hàm/vị" riêng — học hàm nằm trong họ tên; không có cột GV kỳ
trước) → những ô đó để trống, giáo vụ điền sau.

## Cách dựng

`webapp/fate_import.py` — **chỉ đọc Excel** ra các dòng chuẩn hoá. Không dính Flask,
không dính STATE, chạy độc lập được nên test riêng dễ.

`_build_manual_data_from_rows()` trong `app.py` — dựng dữ liệu nhập tay từ các dòng đó,
bằng **chính** những hàm mà endpoint nhập tay dùng (`_validate_section_body` →
`_get_or_create_program`, `_apply_section_time`). Nhờ vậy dữ liệu nạp từ file không khác
gì dữ liệu gõ tay: program_id, submissions, pending_section_ids, room_type… đều do cùng
một đoạn code sinh ra. Sau này sửa luật ở đó thì cả hai đường đều đổi theo.

Vì sao **không dùng lại** `scheduler_core.load_real_fate_data()` có sẵn:
1. Nó chỉ đọc ~12 cột thuật toán cần; section sau khi parse chỉ có 11 trường, form cần ~28.
2. Nó không tạo thực thể `courses` — mà form gom 4 cột merge theo học phần và có form
   "Sửa học phần" riêng.
3. Dữ liệu nạp kiểu đó bị đánh dấu không phải "Nhập liệu thủ công" nên form **khoá hết
   nút sửa** — đúng thứ cần tránh.

`sourceLabel` sau khi import vẫn là `"Nhập liệu thủ công"` (điều kiện để form cho sửa);
tên file đi riêng qua `importedFrom` để còn truy nguyên được.

## Ô gộp dọc: đổi tên học phần thì CẮT kế thừa

Excel gộp ô theo chiều dọc cho các cột mức học phần, nên dòng sau để trống và phải nhớ
giá trị dòng trước. Nhưng có **hai tình huống khác hẳn nhau**, ban đầu bị gộp làm một và
gây sai dữ liệu:

| Dòng (HK1) | Tên học phần | Mã HP / Mã lớp / LT / TH | Phải làm gì |
|---|---|---|---|
| 14 → 15 | "Giải tích 1" → "Giải tích 1" | có đủ, chỉ "Số TC" trống | **kế thừa** — ô gộp dọc thật |
| 8 → 9 | "Triết học Mác-Lênin" → "Tư tưởng Hồ Chí Minh…" | trống hết | **không kế thừa** — học phần khác |

Bản đầu kế thừa vô điều kiện, nên "Tư tưởng Hồ Chí Minh", "Giáo dục thể chất" và
"Tiếng Anh B1" đều bị gán nhầm `PHI1006`, LT `42`, TH `6` của "Triết học Mác-Lênin".

Mốc phân biệt là chính **tên học phần**: dòng có tên riêng và **khác** tên đang nhớ thì
xoá sạch mọi giá trị đang nhớ trước khi đọc dòng đó. So sánh sau khi gộp khoảng trắng và
bỏ hoa/thường — tên trong file có cả xuống dòng giữa chừng.

Kiểm toán toàn bộ hai file: với **mọi** giá trị được kế thừa, truy ngược lên dòng nguồn và
đối chiếu tên học phần — **0 trường hợp** lấy từ học phần khác. Số học phần giảm 165 → 153
(HK1) vì hết các bản trùng giả.

## Ô thời gian chứa NHIỀU buổi

Cột Thứ / Tiết đầu / Tiết cuối có thể ghi nhiều giá trị, mỗi giá trị một dòng trong cùng
một ô:

```
Thứ        Tiết đầu   Tiết cuối
 2            2          5        → Thứ 2, tiết 2-5
 2            6          9        → Thứ 2, tiết 6-9
```

Bản đầu đọc bằng `float()` nên chuỗi `'2\n2'` trả `None` → **68 dòng ở HK1 và 61 dòng ở
HK2 mất sạch giờ** và bị đánh nhầm là "để hệ thống tự xếp". Nay ghép ba cột **theo vị
trí**: giá trị thứ k của mỗi cột thuộc cùng một buổi. Riêng cột Thứ hay chỉ ghi một lần
rồi dùng cho cả hai buổi (`Thứ='2'`, `Tiết đầu='2\n6'`) — lúc đó lấy giá trị cuối đã đọc.

Mỗi buổi thành một lớp riêng, đúng quy ước "1 lớp N buổi/tuần = N dòng cùng mã lớp".

**Hai nguồn giờ, giữ nguyên thứ tự ưu tiên.** File cũ có thêm cột text tự do
"Thời gian (Thứ, Tiết)". Đo trên HK1: 54 dòng có cả hai nguồn thì **52 dòng lệch nhau** —
ví dụ dòng 14 và 15 ("Giải tích 1" hai lớp) đều có cột cấu trúc ghi *cùng* một giá trị
`T5 tiết 3-5`, trong khi cột text ghi đúng `T3 tiết 2-3` và `T3 tiết 4-5`. Khớp với ghi
chú sẵn có trong `scheduler_core`: với layout cũ, cột text đáng tin hơn. Nên vẫn **ưu tiên
text, chỉ dùng cột cấu trúc khi không có text** — sửa lần này chỉ vá chỗ đọc cột cấu trúc,
không đảo thứ tự ưu tiên.

Kiểm toán cả hai file: **0 dòng** có giờ trong Excel mà ra lớp không giờ; **0 giờ** nằm
ngoài phạm vi hợp lệ. Số lớp đã có giờ ở HK1 tăng 138 → **238**.

## Hai quyết định về dữ liệu

**Gộp giảng viên theo TÊN, không theo (tên + đơn vị).** Trong file thật, cùng một người
hay bị ghi đơn vị mỗi dòng một kiểu — "Trường ĐH Việt Nhật" / "Trường Đại học Việt Nhật",
có dòng bỏ trống. File HK1 có **15 trường hợp** như vậy. Nếu gộp theo cặp thì một người
tách thành 2–3 bản ghi, hệ thống coi là những người khác nhau và **không còn phát hiện
được họ trùng lịch với chính mình** — mất đúng công dụng chính của công cụ. Nặng hơn:
dòng bỏ trống đơn vị bị xếp thỉnh giảng trong khi các dòng khác là cơ hữu, một người bị
chia sang cả hai giai đoạn.

Đổi lại, hai người **trùng họ tên** sẽ bị gộp làm một. Trong phạm vi một file của một
khoa thì hiếm, và hướng sai này an toàn hơn: gộp nhầm chỉ báo thừa xung đột (giáo vụ nhìn
ra ngay), còn tách nhầm thì **giấu mất** xung đột. Mọi trường hợp đơn vị ghi khác nhau
đều được liệt kê ở bước xem trước.

**Nạp MỌI dòng có dữ liệu, kể cả lớp chưa phân công giảng viên.** Bản đầu bỏ qua các dòng
ghi "Phòng Đào tạo điều phối"/"JLE điều phối" và các dòng để trống ô giảng viên — **sai**.
Đó là lớp thật, chỉ chưa biết ai dạy; không có lý do gì để chặn.

Mốc phân biệt dòng thật với dòng trống của bảng tính (hai file đều có ~850 dòng trống
phía dưới vùng dữ liệu): **dòng có giảng viên HOẶC có mã lớp/tên học phần của riêng nó**.
Dòng chỉ có mỗi CTĐT không tính — nạp vào chỉ thành rác.

Ô giảng viên giữ nguyên như trong file ("Phòng Đào tạo điều phối"…) hoặc ghi
"(Chưa phân công)" nếu trống. Số lớp chưa phân công hiện ngay ở bước xem trước.

Lưu ý: **không được chỉ quét chữ "điều phối"**. File thật có ô ghi
`TS. Tạ Quang Ngọc (điều phối)` — là người thật kèm ghi chú. Phân biệt bằng học hàm/học vị
(TS./ThS./PGS/GS): có thì là người, và ghi chú "(điều phối)" bị cắt khỏi tên.

**Mỗi lớp chưa phân công có MỘT bản ghi giảng viên riêng**, không dùng chung một bản ghi
"Phòng Đào tạo điều phối". Dùng chung thì hệ thống coi 60 lớp đó là **của một người** — đo
trên file HK1 cho **54 ô giờ chồng nhau**, tức hộp thư vấn đề sẽ ngập báo "trùng giảng
viên" giả và nhấn chìm các vụ trùng thật. Mà chúng vốn không phải một người, chỉ là chỗ
trống chờ phân công. Sau khi tách: **0 ô chồng nhau**.

Các bản ghi này mang cờ `isPlaceholder`, để màn dành cho giảng viên thật lọc ra — "Giờ
rảnh GV" chỉ hiện 48 GV thật thay vì thêm 114 dòng "Phòng Đào tạo điều phối".

## Kết quả trên hai file thật

| | HK1 2026-2027 | HK2 2025-2026 |
|---|---|---|
| Lớp dựng được | **313 / 313** | **238 / 238** |
| Trong đó đã có giờ cụ thể | 238 | 64 |
| Trong đó chưa phân công GV | 114 | 61 |
| Học phần | 153 | 121 |
| Giảng viên thật (sau gộp) | 80 | 67 |
| **Dòng bỏ qua** | **0** | **0** |

Không dòng nào bị bỏ, không dòng nào lỗi. Số ở bản xem trước **khớp chính xác** với số sau
khi ghi — đã đối chiếu tự động cho cả hai file.

## Bản xem trước liệt kê theo NHÓM LÝ DO

Bản đầu trả về danh sách dòng phẳng rồi cắt 20 dòng đầu. Ra màn hình thành 20 dòng lặp y
hệt nhau cộng một câu "…và 12 dòng nữa cùng loại" — không ai hiểu "loại" là loại gì, và
không trả lời được câu hỏi thật sự: **quy tắc nào làm dòng bị bỏ, tổng cộng bao nhiêu**.

Nay gom theo `kind`: mỗi nhóm là một quy tắc, kèm số lượng, các giá trị khác nhau đã gặp
(có đếm), và số dòng Excel để mở file ra đối chiếu. Số nhóm ít (2–3) nên gửi hết, không
cắt.

Ví dụ với HK2:

```
32 dòng KHÔNG được nạp
  32 dòng — Ô giảng viên ghi tên một ĐƠN VỊ điều phối, không phải một người cụ thể
      ・Phòng Đào tạo điều phối (27 dòng)
      ・JLE điều phối (3 dòng)
      ・Phòng ĐT điều phối (2 dòng)
      Dòng trong file: 6, 7, 8, 9, 10, 11, 12, 32, … (+2 dòng)

13 dòng có lưu ý (vẫn được nạp)
  10 dòng — Ô ghi nhiều giảng viên đồng giảng — chỉ lấy người đầu làm GV chính
   3 dòng — Cùng một họ tên nhưng ghi nhiều đơn vị công tác khác nhau — đã gộp làm một người
```

## Kiểm chứng

Chạy đầu-cuối qua giao diện bằng Chrome (không gọi API tay): mở hộp thoại → gán file thật
vào ô chọn file → đọc bản xem trước → xác nhận ghi → kiểm tra kết quả.

- Bảng phía sau **không đổi** trong lúc xem trước (174 → vẫn 174) — bước đọc file không
  có tác dụng phụ.
- Sau khi ghi: 188 lớp, hộp thoại đóng, nút "Thêm lớp" còn đó → form vẫn cho sửa.
- Mở được ngăn kéo "Sửa lớp #0" trên dữ liệu vừa nhập.
- Không lỗi console.

## Còn hạn chế

- **Đồng giảng**: ô ghi nhiều giảng viên thì chỉ lấy người đầu làm GV chính, những người
  còn lại phải thêm bằng tay. Có cảnh báo ở bước xem trước (HK1: 7 dòng, HK2: 10 dòng).
- **Một dòng nhiều buổi/tuần** được tách thành nhiều lớp cùng mã — đúng quy ước
  "1 lớp học N buổi/tuần = N dòng cùng Mã lớp" mà form đang dùng.
- Chỉ **ghi đè**, chưa có gộp thêm vào dữ liệu đang có.
