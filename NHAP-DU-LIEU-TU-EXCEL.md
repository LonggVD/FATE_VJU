# Nhập dữ liệu từ file Excel vào form "Dữ liệu học phần"

Nạp file kế hoạch giảng dạy của kỳ cũ vào form, để giáo vụ sửa tiếp thay vì gõ lại từ đầu.

## Dùng thế nào

"Dữ liệu học phần" → **Nhập từ Excel** → chọn file `.xlsx` → đọc bản xem trước →
**Xóa dữ liệu cũ và nạp N lớp**.

Hai bước có chủ ý: bước đọc file **không ghi gì cả**, chỉ hiện ra sẽ nạp được những gì.
Import là thao tác xóa hết dữ liệu đang có và **không hoàn tác được**, nên phải cho người
dùng đối chiếu con số trước khi quyết.

## Định dạng nhận được: đọc theo NHÃN CỘT, không theo vị trí

Không có danh sách định dạng được hỗ trợ. Mỗi lần nhập, cột được tìm bằng **chính nhãn ở
hàng tiêu đề** của file: tìm hàng có ô `Mã học phần`, đọc luôn cả khối tiêu đề (1–3 hàng),
rồi map từng cột theo nhãn. Dòng dữ liệu bắt đầu ngay sau khối đó.

**Bảng 29 cột của form chính là bản sao của file HK1** nên ánh xạ gần như 1:1. File HK2
thiếu vài cột (không có "Học hàm/vị" riêng — học hàm nằm trong họ tên; không có cột GV kỳ
trước) → những ô đó để trống, giáo vụ điền sau.

**Vì sao không map theo vị trí cột + tên sheet như bản đầu.** Bản đầu có `LAYOUTS` gồm hai
mục, chọn theo tên sheet (`FATE` → cấu trúc HK2, `Giảng dạy cho FATE` → cấu trúc HK1). Vỡ
ngay khi gặp `FATE.TKB.HK1 2026-2027-2.xlsx`: file giữ nguyên cấu trúc HK1 (có cột `TT` ở
đầu, có block "GV kỳ trước để đối chiếu") nhưng sheet được **đổi tên** thành `FATE` → khớp
vào layout HK2 → **lệch đúng 1 cột** từ đầu đến cuối, mà không có một dòng lỗi nào:

| Trường | Đọc được | Đúng ra |
|---|---|---|
| courseName | `PHI1006` | `Triết học Mác-Lênin…` |
| classCode | `3` | `PHI1006` |
| teacherName | GV **kỳ trước** (cột O) | GV kỳ này (cột R) |
| language | `Hòa Lạc` | ngôn ngữ |

Cộng thêm dòng đầu dữ liệu lệch 2 (6 thay vì 8) nên hai **dòng tiêu đề** bị nạp thành lớp,
tạo ra "giảng viên" tên `Họ và tên giảng viên`. Tên sheet và vị trí cột đều do giáo vụ sửa
mỗi kỳ; **nhãn cột thì ổn định** — nên đọc nhãn.

### Một nhãn không đủ: phải xét ĐƯỜNG DẪN nhãn

Tiêu đề có 2–3 tầng (nhóm / nhóm con / lá) và nhãn lá **trùng nhau** giữa các nhóm:

| Đường dẫn | Trường |
|---|---|
| `Phân bổ TC` → `Lý thuyết` | số tín chỉ LT |
| `Số giờ dạy` → `Lý thuyết` | số giờ dạy LT |
| `HK1 năm 2025-2026 (để đối chiếu)` → `Họ và tên` | GV **kỳ trước** |
| `HK1 năm 2026-2027` → `Họ và tên` | GV kỳ này |

Nên mỗi cột được xét bằng cả đường dẫn nhãn từ trên xuống, sau khi **bung ô gộp**
(openpyxl chỉ trả giá trị ở ô góc trên-trái của vùng gộp).

Dấu hiệu loại cột "dữ liệu kỳ trước, để đối chiếu": `để đối chiếu`, `năm ngoái`,
`năm trước`, `kỳ trước`. Đây cũng là lý do file HK2 **không** dùng cột text
`Thời gian (Thứ, Tiết) - NĂM NGOÁI` — trước đây phải ghi tay `timeText: None` cho layout
đó, nay chính nhãn nói ra điều đó. Lưới đỡ thứ hai, cho trường hợp file bỏ hẳn chữ
"(để đối chiếu)": trong khối thông tin GV, nếu nhiều cột cùng khớp một trường thì **lấy cột
bên phải** — theo khuôn file thật, dữ liệu đối chiếu nằm bên trái, dữ liệu kỳ này bên phải.

### Ranh giới tiêu đề / dữ liệu

Hàng tiêu đề cuối cùng lấy theo **hai** dấu hiệu, xa nhất thắng:

- ô **gộp dọc** bắt đầu từ hàng đầu tiêu đề (file thật gộp `Số tín chỉ` D5:D7);
- **hàng chỉ gồm nhãn** ngay dưới (không ô nào là số, có ≥3 nhãn quen biết) — file do chính
  webapp xuất ra không gộp ô nào (xem `fate_export.py`) nên chỉ dấu hiệu gộp ô là không đủ.

Cùng lý do đó, nhãn nhóm chỉ ghi ở ô đầu nhóm và các ô sau để trống mà **không** gộp cũng
được kéo sang phải — nhưng chỉ với các hàng nhóm, không với hàng nhãn lá (kéo ở hàng lá thì
nhãn `Thực hành` tràn sang đè cột `Khóa`).

### Chọn sheet và bắt lỗi

Ưu tiên sheet có chữ `FATE` trong tên: file thật còn có sheet của khoa khác
(`Giảng dạy cho BJS`) và các sheet phụ (`Thống kê số lớp HP`, `HP ở MĐ cần thực hành…`) —
mà mấy sheet đó **cũng có** cột `Mã học phần`/`Tên học phần`. Không có sheet nào tên chứa
`FATE` thì quét mọi sheet.

Thiếu một trong các cột bắt buộc (`Tên học phần`, `Mã lớp học phần`,
`Họ và tên giảng viên`, và nguồn giờ) → **báo lỗi kèm tên sheet và cột còn thiếu**, chứ
không nạp. Đây là điểm khác quan trọng nhất so với bản đầu: hỏng kiểu này trước đây **im
lặng** ra 300 lớp sai, giờ nó phải nói ra.

Sửa nhãn/thêm cột: `_COLUMN_RULES` trong `webapp/fate_import.py`. `read_rows()` còn trả
`result["columns"]` — bản đồ trường → cột Excel đã nhận diện — để đối chiếu khi nghi đọc
lệch cột.

## Cách dựng

`webapp/fate_import.py` — **chỉ đọc Excel** ra các dòng chuẩn hoá. Không dính Flask,
không dính STATE, chạy độc lập được nên test riêng dễ.

`webapp/fate_audit.py` — **chỉ soi lỗi trong file**, không sửa gì (xem "Kiểm tra chất lượng
dữ liệu"). Cũng độc lập, chỉ nhận vào các dòng đã chuẩn hoá.

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

**NGUỒN GIỜ DUY NHẤT là cột cấu trúc (Thứ / Tiết đầu / Tiết cuối).** File còn một cột text tự
do "Thời gian (Thứ, Tiết)"; khoa xác nhận đó là **chỗ ghi cũ của các kỳ trước, dữ liệu bỏ đi,
hoàn toàn không liên quan đến hệ thống**. Nên cột đó bị bỏ **hẳn**: không đọc, không đối chiếu,
không cảnh báo. Dòng nào thiếu 3 cột cấu trúc thì lớp coi như **chưa có giờ**, để thuật toán tự
xếp — không quay về đọc text nữa.

Bỏ ở **cả ba** đường đọc: `fate_import.read_rows` (đường nhập file), `scheduler_core.
load_real_fate_data` (đường nạp dữ liệu thật) và màn "Đối chiếu giờ học" ở bước xem trước
(cùng endpoint `apply-time-fix` — đã xoá). Trước đó `load_real_fate_data` còn **ưu tiên** cột
text hơn cột cấu trúc.

Thiếu 3 cột cấu trúc trong hàng tiêu đề giờ là **lỗi chặn nhập** (`Thời gian (Thứ / Tiết đầu /
Tiết cuối)`), vì lúc đó cả file không lớp nào có giờ — báo ngay còn hơn nạp ra 300 lớp đều
"chưa có giờ".

Số đo sau khi bỏ hẳn (không lớp nào mất đi, chỉ chuyển sang "để hệ thống tự xếp"):

| | HK2 | HK1 | HK1-2 |
|---|---|---|---|
| Số lớp | 238 | 305 | 343 |
| Lớp chưa có giờ → hệ thống tự xếp | 174 | 166 | 97 |
| Cảnh báo về cột text (`bo_gio_cot_text`, `lech_nguon_gio`) | 0 | 0 → **0** *(trước: 91 + 52)* | 0 → **0** *(trước: 56 + 86)* |

Bản đầu ưu tiên ngược lại (text trước) kèm một cơ chế **tự đoán**: nếu trong cùng một học phần,
một nguồn giữ y nguyên giá trị cho mọi lớp trong khi nguồn kia phân biệt từng lớp, thì đảo ưu
tiên cho nhóm đó. Đã bỏ hết — khoa đã chốt cột nào đúng thì hệ thống không cần đoán nữa, và
đoán sai thì âm thầm.

Cuối cùng, buổi **không hợp lệ** (thứ ngoài 0-6, tiết cuối < tiết đầu) bị lọc ngay khi đọc
khi đọc — một dòng ghi rác thì bỏ đúng buổi rác đó, các buổi còn lại của dòng vẫn giữ.

## Giờ trong file là giờ ĐÃ CHỐT

Quy ước nghiệp vụ: một dòng trong file kế hoạch giảng dạy là một lớp mà **giảng viên và điều
phối viên đã thống nhất giờ với nhau**. Hệ thống không có quyền đổi. Ba hệ quả:

**1. Ghim cứng, không tự dời.** Giai đoạn 2 (cơ hữu) trước đây dựng miền giá trị bằng
`valid_starts(...)` = mọi ô Thứ 2–Thứ 6, **không đọc** `original_slot` — nên trên HK1-2 có
**139/140 lớp cơ hữu bị xếp sang giờ khác** (VJU2031 file ghi Thứ 2 tiết 6 → hệ thống xếp Thứ 3
tiết 1). Nay lớp nào có giờ trong file thì miền chỉ gồm đúng ô đó. Đo lại: **0 lớp bị dời** ở
cả ba file. Thứ tự ưu tiên: quyết định tay (kéo-thả/ghim ở màn TKB) > giờ chốt từ file > tự do.

**2. Quy định ngày không áp cho lớp đã chốt giờ.** Thỉnh giảng tới Thứ 7, cơ hữu tới Thứ 6
(`MAX_DAY_INDEX`) — quy định này để hệ thống **chọn hộ** cho lớp chưa có giờ. Lớp đã chốt thì
giữ nguyên, kể cả cơ hữu dạy Chủ nhật, và ghi cảnh báo `ngay_ngoai_quy_dinh_giu_nguyen` để
giáo vụ biết. Trước đây những dòng đó bị **bỏ giờ**: HK1-2 mất 15 lớp thực tập/thực hành/đồ án.
Gõ tay qua form thì **vẫn bị chặn** — lúc đó chưa có ai chốt gì.

**3. Trùng thì BÁO, không tự sắp lại.** Ghim bằng cách thu hẹp domain, interval vẫn là
`Optional` → hai lớp đòi cùng một ô của cùng một người thì một lớp rơi vào "không xếp được"
kèm tên lớp đang chiếm chỗ, thay vì bị lặng lẽ dời. Ví dụ thật: *Vật lý 1 (VJU2005-3), giờ đã
chốt Thứ 2 tiết 6 — đang bị Vật lý 1 (VJU2005-4) chiếm chỗ*.

Việc số 3 lộ ra một **lỗi có sẵn** trong mô hình Giai đoạn 2: nó không thể có lớp "không xếp
được". `on_day_bools` được reify hai chiều (`day_var != d` khi bool sai), mà `start` luôn có
giá trị cụ thể kể cả khi lớp không được xếp → luôn đúng một bool bật → `sum(b) == is_placed`
**ép `is_placed` = 1 cho mọi lớp**. Tức GD2 chỉ có "xếp hết" hoặc `INFEASIBLE` mất trắng — và
đúng thế: vừa ghim giờ là HK2 từ `OPTIMAL 119/119` thành `INFEASIBLE 0/119`. Sửa bằng cách bỏ
chiều ngược, thay bằng `AddImplication(b, is_placed)`. Trước đây không ai thấy vì solver có cả
Thứ 2–Thứ 6 × 13 tiết để lách nên luôn xếp hết.

## Khai giờ rảnh = GIỚI HẠN CỨNG, kể cả cơ hữu

Khung giờ giảng viên khai (`manual_teacher_windows`) trước đây **chỉ có tác dụng với thỉnh
giảng**: Giai đoạn 2 không đọc `submissions`, cơ hữu luôn tự do Thứ 2–Thứ 6, nên khai cho cơ hữu
là vô ích. Nay khai rồi thì **chỉ xếp trong khung đó**. Thứ tự ưu tiên khi dựng miền giá trị:

| Trạng thái | Miền của lớp |
|---|---|
| Ghim tay (kéo-thả ở màn TKB) | đúng ô đã ghim |
| Giờ đã chốt trong file | đúng ô đó |
| **Đã khai giờ rảnh** | **chỉ trong khung đã khai** — giao khung của cả nhóm giảng viên |
| Chưa ai khai | tự do (theo quy định ngày) |

Khung đã khai **không** bị cắt theo `MAX_DAY_INDEX`: quy định "cơ hữu tới Thứ 6" là để **hệ thống
chọn hộ**, còn giảng viên khai Thứ 7 là con người tự nói mình dạy được hôm đó — cùng lý lẽ với
"giờ trong file là giờ đã chốt".

**Khai rồi mà không còn chỗ thì BÁO, không tự nới.** `submissions` để rỗng + lớp vào
`pending_section_ids`; solver phân biệt trạng thái này với "chưa ai khai" (cũng rỗng nhưng không
trong pending) và ép lớp thành "không xếp được" kèm tên lớp đang chiếm chỗ. Không phân biệt thì
khai xong lại được tự do cả tuần — ngược hẳn ý.

`_sync_teacher_sections` gọi lại `_apply_section_time` thay vì tự tính, để luật chỉ nằm một chỗ.

**Kéo theo một lỗ hổng phải bịt.** Giai đoạn 2 vốn chỉ đưa các buổi đã xếp ở Giai đoạn 1 vào ràng
buộc *phòng*, không vào ràng buộc *không-trùng-giờ theo giảng viên*. Không ai thấy vì trước đây
GV cơ hữu không thể có lớp ở GĐ1 (loại lớp lấy theo "GV chính"). Từ khi loại lớp tính theo cả
nhóm, một GV cơ hữu có thể có lớp ở GĐ1 và lớp khác ở GĐ2 → GĐ2 không biết giờ của họ đã bị
chiếm. HK2 có 2 giảng viên như vậy, và có lần chạy ra đúng 1 ô chồng nhau. Nay buổi của GĐ1 vào
cả hai ràng buộc; chạy 5 lần/file đều **0 ô chồng nhau**.

Đo trên dữ liệu dựng riêng: chưa khai → tự do · khai Thứ 3 tiết 5-8 → cả 2 lớp nằm trong khung ·
khai 1 tiết cho lớp 2 tiết → **0/2 và báo `NO_SLOT`** · khai đủ cho 1 lớp mà có 2 lớp → 1 xếp,
1 báo kèm thủ phạm · xoá khung → về tự do. Trên ba file thật (không ai khai) kết quả **không đổi**.

## Nạp xong là thấy ngay thời khoá biểu, đã ghim sẵn

Trước đây nạp file xong mở màn "Thời khoá biểu" thì thấy *"Chưa có lịch nào — bấm Giải ở bước 2"*,
dù file đã chốt giờ cho phần lớn các lớp. Giáo vụ phải bấm Giải mới xem được chính cái mình vừa
nạp — trong khi những giờ đó là **đã chốt**, không phải do thuật toán xếp.

Nay ngay sau khi nạp (`_dat_lich_ban_dau`):

| | HK2 | HK1 | HK1-2 |
|---|---|---|---|
| Buổi hiện ngay trên TKB | 64 | 139 | **246** |
| Lớp được ghim sẵn | 64 | 139 | 246 |

**Mọi buổi đó được GHIM** (`STATE["overrides"]`) nên chạy "Xếp thỉnh giảng"/"Ghép cơ hữu" không
làm xê dịch — đo trên cả ba file: **0 buổi bị dời**. Solver vốn đã ghim theo `original_slot`, ghi
vào `overrides` để **giao diện** hiện đúng trạng thái "đã ghim": nhìn ra ngay lớp nào là giờ chốt
từ file, lớp nào do hệ thống xếp.

Lịch này mang cờ `initial: True` nên thanh tiến trình vẫn ghi *"N buổi chốt từ file"* thay vì báo
"đã chạy", và bước 3 vẫn đòi chạy bước 2 trước (backend cũng chặn). Snapshot chỉ lưu dữ liệu chứ
không lưu kết quả giải, nên lịch ban đầu được **dựng lại khi khởi động** — mở app là thấy, không
phải nạp lại file.

Có 8–18 lớp *"ghim thất bại"* sau khi giải: đó là các lớp đã chốt giờ nhưng **trùng nhau trong
file** (xem "17 bộ dòng nhập trùng"). Đúng nguyên tắc đã chốt — không tự dời giờ đã chốt, mà báo
ra để giáo vụ sắp lại.

## "Chưa khai giờ rảnh" = rảnh cả tuần

Lớp **chưa** có giờ trong file thì cần khung giờ rảnh của giảng viên để xếp. Nạp HK2 cho
**88/119 lớp thỉnh giảng** không có giờ và giảng viên chưa khai gì → giải ra chỉ xếp được
**24/119**, tức gần như vô dụng cho tới khi có người khai tay 88 lần.

Nay: giảng viên **chưa khai gì** thì coi như rảnh cả tuần → HK2 xếp được **112/119**. Giảng
viên **đã khai** mà không khung nào đủ dài cho lớp đó thì **vẫn báo** — đấy là xung đột thật,
không được tự nới ra cả tuần.

Số lớp đang chạy bằng giả định này được đếm riêng (`num_availability_assumed`: HK2 89, HK1 40,
HK1-2 21) để không ai hiểu nhầm đó là giờ giảng viên đã xác nhận. Mỗi dòng ở
`submissions` mang cờ `availabilityAssumed`, và màn "Khung giờ đã báo" đọc cờ đó.

Phải là **cờ từ backend**, không để frontend tự đoán: cách cũ đếm số khung rồi so với ngưỡng
90% số ô cả tuần, mà khung "cả tuần" của thỉnh giảng chỉ có 6 ngày (không ai dạy Chủ nhật) trong
khi ngưỡng tính theo 7 ngày → 72/84 = 86% < 90% → 89 lớp HK2 bị xếp thành **"Đã chốt giờ"**,
nói ngược hẳn sự thực. Cách đếm vẫn giữ làm dự phòng cho dữ liệu cũ chưa có cờ.

## Số tiết/ngày: mặc định 13, tự nới theo file

Trước đây chốt cứng 12 nên HK1-2 dòng 280 (CSE4001) và 281 (CSE4002) ghi **tiết 11-13** bị coi
là không hợp lệ — mà tiết 13 là giờ học thật ở VJU.

Chốt cứng một con số thì mỗi kỳ file đổi lại phải sửa code, nên làm như `load_real_fate_data`
vốn đã làm: **lấy theo dữ liệu**. Mặc định 13 (cho cả nhập tay), rồi `_noi_slots_per_day()`
nới lên bằng tiết cuối lớn nhất có trong file. Frontend không phải sửa gì — mọi lưới tiết đọc
`slotsPerDay` từ params.

Chặn trên là `fate_import.MAX_TIET` = **16**, nghĩa là "tiết lớn nhất còn tin được": một ngày
tối đa là sáng (1-5) + chiều (6-10) + tối (11-15), ghi tiết 20 hay 99 thì không thể là giờ học
thật — mà nới `slotsPerDay` theo đó chỉ phình mô hình solver vô ích (mỗi tiết nhân 7 ngày).

Giờ **vượt 16** thì bỏ giờ, **giữ lớp**, kèm cảnh báo `gio_ngoai_pham_vi_tiet`. Đây là nguyên
tắc chung: một ô giờ sai không được làm rụng cả lớp. Trước đây `_parse_class_time` trả lỗi
*"Thứ/Tiết không hợp lệ"*, mà ở luồng nạp file thì lỗi = **rụng cả lớp**: giáo vụ vào màn "Xác
nhận giờ học", chọn đúng cái nguồn khoa vừa sửa, và mất luôn lớp — mất cả giảng viên, sĩ số,
học phần. Đo được lúc đó: `347 lớp, errors=0` → chọn cột cấu trúc dòng 280 → `347 lớp,
errors=1`.

Buổi vượt tiết **không** bị lọc ở `_hop_le` (chỗ lọc buổi vô lý khi đọc) — nó phải đi tiếp để
còn hiện được ra cảnh báo kèm giá trị cụ thể; lọc sớm thì lớp im lặng mất giờ.

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

**Khoá gộp bỏ học hàm, số thứ tự, dấu câu** (`fate_import.khoa_gv`) — không lấy nguyên tên.
Vì file thật ghi cùng một người nhiều kiểu, và mỗi biến thể thành một bản ghi riêng thì mất
đúng khả năng phát hiện người đó trùng lịch với chính mình:

| Hai bản ghi trong file | Số lớp mỗi bên | File |
|---|---|---|
| `PGS.TS. Nguyễn Đình Thắng` / `PGS. TS. Nguyễn Đình Thắng` (khác dấu cách) | 2 và 5 | HK2 |
| `Tạ Kim Nhung` / `TS. Tạ Kim Nhung` | 7 và 1 | HK1 |
| `Đặng Minh Hiếu` / `TS. Đặng Minh Hiếu` | 6 và 2 | HK1 |
| `Phạm Thu Thúy` / `ThS. Phạm Thu Thúy` | 4 và 1 | HK1-2 |
| `1. TS. Phạm Hoài Luân` (số thứ tự người nhập thêm) | — | HK2 dòng 178-185 |

Gộp được: HK2 3 cặp, HK1 6 cặp, HK1-2 2 cặp — và sau khi sửa thì **không còn cặp nào sót**.
Tên hiển thị lấy bản đầy đủ hơn (thường là bản có học hàm); mọi lần gộp được liệt kê ở bước
xem trước (`gop_bien_the_ten`) để giáo vụ rà lại — vì hướng gộp này cũng có thể gộp nhầm hai
người trùng tên khác học hàm.

**Không gộp theo email**, dù email trùng là dấu hiệu mạnh: file thật có **4 trường hợp một
email dùng cho hai người khác nhau** (`nt.dung@vju.ac.vn` cho cả Nguyễn Tiến Dũng và Trần
Quang Đức…) — lỗi copy-paste khi nhập. Gộp theo email sẽ nhập hai người thành một.

**Ô giảng viên ghi một ĐƠN VỊ/vai trò chung** cũng là "chưa phân công", không chỉ
"…điều phối": file có `Khoa FATE`, `GV Thỉnh giảng` (HK2), `Chuyên gia` (HK1, HK1-2), mỗi
cái đang giữ 2 lớp. Coi chúng là một *người* thì hệ thống ràng buộc 2 lớp đó không được
trùng giờ — sai bản chất, vì đó là hai người khác nhau chưa biết tên. Nhận diện bằng: từ chỉ
đơn vị ở **đầu** ô (`khoa|phòng|viện|trung tâm|bộ môn|ban|gv|giảng viên|chuyên gia|nhóm|tổ`),
**không** có học hàm, và ô **ngắn ≤ 4 từ** — để không bắt oan `TS. Nguyễn Đăng Khoa` hay
`Chuyên gia Nguyễn Văn A`.

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

## Kiểm tra chất lượng dữ liệu (`fate_audit.py`)

Khác `warnings` ở chỗ nào: `warnings` nói về việc **import đã phải tự quyết định gì** ("dòng
này 2 buổi nên tách thành 2 lớp", "ô giảng viên để trống"). `fate_audit` nói về **lỗi trong
chính file** — import không sai ở đâu cả, nhưng dữ liệu ra không đúng ý giáo vụ.

Rà tay ba file thật tìm ra 12 loại lỗi như vậy, mà bước xem trước **không hề hiện** — phải
viết script riêng mới thấy, tức thực tế là không ai thấy. Nay mỗi lần nhập file là thấy.

Nhóm "nghi SAI" (nên sửa file gốc rồi nạp lại):

| Loại | Ví dụ thật |
|---|---|
| Một mã lớp cho nhiều học phần | HK2: `FLF1108` dùng cho **cả "Tiếng Anh B1" và "Tiếng Anh B2"** |
| Một mã học phần mang nhiều tên | `PHI1006` → "Triết học Mác - Lênin" / "Triết học Mác-Lênin" / "…(chia làm 2 lớp)" |
| Cùng tên học phần nhiều mã | "Nhập môn hệ thống máy tính" = AET2014 / AET2015 / **ATE2015**; "Nguyên lý kinh tế" = INE2004 / **NE2004**; "Khoa học toàn cầu và môi trường" = VJU2012 / **MNS2006** (HK1 dòng 78-80) |
| Tên chỉ khác dấu → tách thành 2 học phần | "Hoá học 2" / "Hóa học 2"; "Lịch sử Đảng Cộng sản" / "Lịch sử Đảng cộng sản" |
| Số tín chỉ khác nhau cùng học phần | `VJU2031` "Tiếng Nhật sơ cấp 1" ghi **3 và 5** |
| Nghi nhập trùng | `PHI1006` Thứ 2 tiết 2-5 ở **dòng 8 và 43**; `VJU2031` Thứ 2 tiết 8-9 ở **dòng 12, 33, 47** |
| Một email cho nhiều người | `nt.dung@vju.ac.vn` → Nguyễn Tiến Dũng \| Trần Quang Đức |

Nhóm "nên rà lại": ô email lẫn SĐT/nhiều email, CTĐT chứa cả câu (`BCSE (với những SV đã học
Triết)` → thành một "chương trình" riêng, HK1 có 21 giá trị CTĐT cho ~8 chương trình), ghi
chú viết vào ô Tên học phần, và các ô để trống (mã lớp, mã HP, số TC, khoá, số SV).

**Ô ghép bằng dấu `+` được tính cho TẤT CẢ thành phần.** `BCSE+MJM` là lớp của **cả** BCSE và
MJM; `VJU2023+VJU2024` là lớp của **cả hai khoá**. Backend tách sẵn ra `programParts` /
`cohortParts`), bộ lọc ở cả hai màn dùng danh sách **mã đơn** và so theo thành phần. Nhờ vậy chọn
"BCSE" ra cả lớp `BCSE+MJM`, và `VJU2023+VJU2024` với `VJU2024+VJU2023` không còn nằm thành hai
mục gần giống nhau.

Dấu ngăn: CTĐT tách theo `+ . ( ) [ ]` và ` - `; khoá theo `+ , ; /`.

**Ngoặc trong file thật làm CẢ HAI việc**, nên không thể chỉ cắt hoặc chỉ bỏ:

| Ô trong file | Ngoặc chứa gì | Ra |
|---|---|---|
| `BICA (+ESCT)` | mã thứ hai | `BICA`, `ESCT` |
| `BCSE (với những SV chưa học ở kỳ 1)` | ghi chú | `BCSE` |
| `FTH + ESAS (với những SV đã học Triết)` | cả hai | `FTH`, `ESAS` |
| `ESAS - Học ghép với các lớp khác` | ghi chú sau ` - ` | `ESAS` |

Nên: cắt theo ngoặc trước, rồi bỏ phần nào là **ghi chú** — mốc phân biệt là **≥2 từ và có chữ
thường** (`_la_ghi_chu`), đủ để giữ `Chung` (1 từ) và loại hết các câu có thật trong 3 file. Nếu
lọc xong không còn phần nào (cả ô chỉ là một câu) thì trả về nguyên ô — thà để bộ lọc có một mục
xấu còn hơn làm lớp biến mất khỏi mọi bộ lọc.

`_PROGRAM_SPLIT_RE` (đặt `program_id`) và `_PROGRAM_PART_RE` (bộ lọc) **là hai regex riêng**, có
chủ ý: cắt ngoặc ở chỗ đặt tên sẽ biến `BCSE (với những SV chưa học ở kỳ 1)` thành một chương
trình tên khác hẳn.

Đo được:

| | Ô CTĐT khác nhau trong file | → mã | Ô khoá | → khoá |
|---|---|---|---|---|
| HK1-2 | 16 | **9** | 7 | **5** |
| HK1 | 15 | **10** | 6 | **5** |
| HK2 | 15 | **9** | 8 | **6** |

Lọc `BCSE` (HK1-2) ra 80 lớp — 8 lớp đến từ ô ghép; `MJM` 45 (9 từ ô ghép); `VJU2023` 57 (9 từ
ô ghép).

Bộ lọc theo chương trình có ở **bốn** màn (Dữ liệu học phần · Thời khoá biểu · Khung giờ đã báo ·
Giờ rảnh GV) và cả bốn đều dựng danh sách từ `programParts`. Backend gửi kèm `programParts` /
`programIds` / `facultyName` trên **mọi** bản ghi lớp — buổi học, submission, lớp chưa nộp giờ —
để không màn nào phải bóc tách lại từ chuỗi nhãn (chỗ nào bóc từ chuỗi đều đã vỡ một lần).

Tên hiển thị trên bảng vẫn **giữ nguyên như file** (`BCSE+MJM`), chỉ bộ lọc mới hiểu theo thành
phần. Bên trong hệ thống, `BCSE+MJM` vẫn là **một** chương trình riêng (`program_id`) — xem "Còn
hạn chế".

**Cột Khoá** giờ là một bộ lọc trên cả hai màn nên giá trị bẩn hiện thẳng vào danh sách chọn —
có hai phép kiểm riêng:

| Lỗi | Thật trong file |
|---|---|
| Giá trị không phải mã khoá | HK2 dòng 7, 33: `VNU1001` — **mã học phần** lọt vào cột Khoá |
| Cùng nhóm khoá viết nhiều kiểu | HK1-2: `VJU2023+VJU2024` và `VJU2024+VJU2023` (9 dòng); HK2: `VJU2022,VJU2023,VJU2024` và `VJU2022, VJU2023,VJU2024` (khác một dấu cách) |

Mã khoá phải là chữ + **năm** (`VJU2026`); nếu chỉ đòi 4 chữ số thì `VNU1001` lọt. Mã học phần
dạng `XXX20xx` (vd `MNS2006`) thì vẫn không phân biệt được bằng hình thức — và **không** đối chiếu
được với danh sách mã học phần trong file, vì mã HP thật có cả `VJU2021`/`VJU2022`, trùng mã khoá.

Đếm được trên ba file: **25 / 49 / 50** chỗ nghi sai và **134 / 130 / 160** chỗ nên rà
(HK2 / HK1 / HK1-2).

Gom theo nhóm nguyên nhân, kèm số dòng Excel — cùng khuôn hiển thị với các mục cảnh báo có
sẵn nên UI dùng lại `ChiTiet`, chỉ thêm `donVi` vì có nhóm đếm **trường hợp** chứ không đếm
dòng ("5 mã lớp bị dùng cho nhiều học phần").

Cố ý **không tự sửa** những lỗi này: đoán hộ (tự chọn mã nào là đúng, tự gộp tên khác dấu)
thì sai một lần là sai âm thầm cả kỳ. Chỗ nào có thể chuẩn hoá an toàn thì đã làm ở tầng đọc
(gộp tên giảng viên, cắt ghi chú trong ô tên); còn lại phải sửa ở file gốc.

**Tải được ra .xlsx** (`GET /api/manual/import/issues.xlsx`, nút ngay trên màn xem trước):
mỗi trường hợp một dòng, kèm số dòng Excel để nhảy đến. Vì người sửa được những lỗi này là
**khoa/CTĐT**, không phải người đang bấm nhập — họ cần một file mở bằng Excel, không phải ảnh
chụp màn hình.

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

## Gộp thêm hay ghi đè

`POST /api/manual/import/commit` nhận `{"mode": "replace"|"merge"}` — dialog có hai nút. Gộp
thêm để nạp file khoa này rồi nạp tiếp file khoa khác, hoặc nạp lại file đã sửa mà không mất
công đã chỉnh.

Gộp theo đúng các khoá đã dùng ở tầng đọc: giảng viên theo `khoa_gv` (bỏ học hàm/dấu câu), học
phần theo (mã, tên), chương trình qua `_get_or_create_program`. Bản ghi "chỗ trống" (*Phòng Đào
tạo điều phối*…) **luôn tạo mới** — dùng chung thì cả chục lớp chưa phân công thành của một
người và sinh ra báo trùng giờ giả.

Lớp **trùng** — cùng mã lớp + học phần + GV chính + giờ — thì bỏ qua và **báo số lượng**, nên
nạp lại cùng một file không nhân đôi số lớp.

Đếm theo **số lượng**, không dùng tập hợp: một file thật có nhiều lớp dùng chung đúng bốn thứ
trên mà vẫn là các lớp khác nhau — 5 lớp `THL1057 / Nhà nước và pháp luật / Phòng Đào tạo điều
phối / chưa có giờ` không có gì để phân biệt. Riêng HK2 có **23 khoá bị lặp, phủ 34 lớp**; dùng
tập hợp thì mỗi nhóm thu về 1 và gộp file đó vào bộ khác làm **rụng 34 lớp thật**. Đếm thì nạp
lại đúng file đã có (5 gặp 5) vẫn bỏ qua hết, mà gộp file khác (5 gặp 0) thì thêm đủ 5.

Đo: HK2 (238) + HK1 (313) = **546 lớp** (5 trùng thật); gộp lại chính file đó lần nữa → 0 thêm,
313 trùng, tổng không đổi.

**Hai bộ khác số tiết/ngày phải mã hoá lại slot.** `slot = day * slotsPerDay + (tiết - 1)` nên
con số slot chỉ có nghĩa kèm `slotsPerDay` của chính bộ đó. Gộp mà không mã hoá lại thì một lớp
`Thứ 4 tiết 3-4` (spd 13) trộn vào bộ spd 15 thành **`Thứ 2 tiết 14`**. `_doi_slots_per_day()`
đưa cả hai bộ về `max(spd)` và dựng lại slot/khung giờ qua chính `_apply_section_time` — kể cả
`manual_teacher_windows`. Số tiết/ngày bị nới thì báo ra trong thông báo sau khi gộp.

Không gộp được vào bộ "Dữ liệu thật" (chặn ở endpoint) — bộ đó không phải dữ liệu nhập tay.

## Kiểm chứng

Chạy đầu-cuối qua giao diện bằng Chrome (không gọi API tay): mở hộp thoại → gán file thật
vào ô chọn file → đọc bản xem trước → xác nhận ghi → kiểm tra kết quả.

- Bảng phía sau **không đổi** trong lúc xem trước (174 → vẫn 174) — bước đọc file không
  có tác dụng phụ.
- Sau khi ghi: 188 lớp, hộp thoại đóng, nút "Thêm lớp" còn đó → form vẫn cho sửa.
- Mở được ngăn kéo "Sửa lớp #0" trên dữ liệu vừa nhập.
- Không lỗi console.

## Nhiều giảng viên một lớp: VAI TRÒ NGANG NHAU

Ô giảng viên có thể ghi nhiều người (`TS. A, TS. B, TS. C`). Mỗi người thành **một bản ghi
giảng viên riêng** (gộp theo tên như mọi trường hợp khác — một người dạy nhiều lớp phải ra cùng
một bản ghi), và **tất cả** vào `section["teacher_ids"]`.

**Không có "giảng viên chính".** `teacher_ids` là một danh sách, mọi người vai trò như nhau;
`teacher_id` chỉ là *người đầu danh sách*, giữ lại làm khoá hiển thị cho các màn vốn chỉ hiện
được một tên (lưới TKB, tra cứu theo giảng viên). Bản đầu chia "GV chính + đồng giảng" và cho
sửa bằng một hộp tick — không theo dõi được: người thứ 2 trở đi nằm trong một danh sách tick
dài, không thấy đơn vị/email/SĐT của họ, và nhìn không ra lớp đang có bao nhiêu người.

Thuật toán vốn đã hỗ trợ: cùng một interval được đưa vào `AddNoOverlap` của **từng** người
trong `teacher_ids`, nên không ai trong nhóm bị xếp dạy chỗ khác đúng giờ đó, mà nhu cầu
phòng không bị nhân lên. `check_cross_program_conflicts` cũng khớp theo danh sách này.

Bản đầu chỉ lấy người đầu, `coTeacherNames` sinh ra rồi **không ai đọc**. Hệ quả đo được
trên file HK1-2: giữ nguyên mọi thứ khác, chỉ ràng buộc GV chính thì lời giải cho **Bùi Huy
Kiên bị xếp hai lớp chồng giờ** (section 270 và 272) — ràng buộc cả nhóm thì **0 ô chồng
nhau**. Nặng hơn: người không dạy lớp nào khác (Lê Kim Quy) trước đây **không tồn tại**
trong hệ thống.

Mọi thứ tính theo cả nhóm:

| | Luật | Vì sao |
|---|---|---|
| Ràng buộc không trùng giờ | mọi người trong `teacher_ids` | solver: một interval, nhiều người |
| **Lớp đi Giai đoạn 1 hay 2** (`_loai_lop`) | **có một người thỉnh giảng → GĐ1** | GĐ1 xếp theo khung giờ khách mời đã khai; GĐ2 chọn tự do cả tuần, có thể đặt lớp vào giờ người đó không đến được mà không ai biết |
| **Giờ rảnh của lớp** (`_gio_ranh_chung`) | **GIAO** khung của những người đã khai | lớp 5 người dạy thì phải xếp vào giờ cả 5 người rảnh; người chưa khai gì không làm hẹp khung của người khác |
| Lịch của một GV, hộp thư vấn đề, kiểm trùng khi kéo-thả | đọc `teacherIds` | chỉ soi một người thì buổi đó **vô hình** với những người còn lại, dù solver đã ràng buộc họ |

Đổi loại một người (cơ hữu ↔ thỉnh giảng) hoặc người đó khai lại giờ rảnh thì
`_sync_teacher_sections` tính lại **cả hai** thứ trên cho mọi lớp có người đó — trước đây
`teacher_type` chỉ đổi khi người đó là người đầu danh sách.

Đo trên ba file: **1 lớp** đổi giai đoạn so với luật cũ (HK2 `CSE3049-3`, cơ hữu → thỉnh
giảng vì có một người trong nhóm là khách mời).

### Trên giao diện: mỗi giảng viên MỘT DÒNG

Bảng "Dữ liệu học phần" là bản sao file Excel, mà file gốc ghi cả nhóm trong **một ô**. Nay
năm ô của khối giảng viên (Học hàm/vị · Họ và tên · Đơn vị · Email · SĐT) đều sinh cùng số
dòng theo cùng thứ tự, nên **đọc ngang là ra đúng bộ thông tin của một người**. Trước đây bảng
chỉ hiện người đầu danh sách → email/SĐT của những người còn lại không đọc được ở đâu trên
giao diện.

Bấm vào **từng dòng** → mở ngăn của chính người đó, có mục "Giờ có thể dạy" — nay hiện với **mọi**
giảng viên (trước chỉ thỉnh giảng) và **có tác dụng thật** lên xếp lịch, xem mục dưới.

Dòng giảng viên bị **tô đỏ gạch chân chấm** khi giờ đã chốt của lớp nằm ngoài khung giờ người đó
đã khai — hệ thống giữ nguyên giờ đã chốt (đúng thứ tự ưu tiên), nhưng phải thấy được chỗ vênh
chứ không để giáo vụ tự đoán. Hover ra lý do.

Ngăn "Sửa lớp" cũng đổi theo: một **danh sách ngang hàng**, mỗi dòng một giảng viên (chọn/đổi/
bỏ tại chỗ), dưới mỗi người có dòng đơn vị · email · SĐT, cạnh mỗi người có nút mở ngăn khai
giờ. Lớp phải còn ít nhất một người (bỏ hết thì báo lỗi).

API: `_build_classes_list` trả `teachers: [{id, name, title, org, email, phone, type,
isPlaceholder, availabilitySlots}]` và `teacherIds`. `POST/PATCH /api/manual/section` nhận
`teacherIds` (danh sách); vẫn nhận `teacherId` + `coTeacherIds` kiểu cũ để bản gọi cũ không
vỡ. File xuất ra lấy tên/email từ chính danh sách đó.

**Email/SĐT chia theo vị trí**, chỉ khi số phần khớp số người (`a@x, b@x, c@x` cho 3 người);
lệch số thì để trống chứ không đoán, vì gán sai email cho người khác còn tệ hơn bỏ trống.
**Học hàm chỉ gán cho người đầu**: cột "Học hàm, học vị" ghi một giá trị cho cả ô tên
(`TS.` cho 5 người) nên không biết chắc của ai.

File xuất ra ghi lại **cả nhóm** trong một ô theo đúng khuôn file gốc (`A, B, C`) — nếu chỉ
ghi GV chính thì mỗi lần xuất/nạp lại sẽ rụng dần những người còn lại.

Số lớp đồng giảng: HK1 7, HK2 10, HK1-2 4 (2–5 người/lớp).

### Tách tên: ba cái bẫy trong ô giảng viên

Cắt thô theo dấu phẩy/xuống dòng là **không đủ**. Khi chỉ người đầu được dùng thì mấy chỗ
này vô hại; nay cả nhóm thành GV thật có ràng buộc lịch nên phải lọc cho đúng:

| Ô trong file thật | Cắt thô ra | Đúng ra |
|---|---|---|
| `TS. Bùi Huy Kiên` / `ThS. Nguyễn Tiến Đạt` / `(Nhúng, IoT, Robotic)` (HK2 d.188) | 5 người, trong đó `(Nhúng`, `IoT`, `Robotic)` | 2 người |
| `TS, Nomura` (HK2 d.215 — phẩy thay cho chấm) | `TS` và `Nomura` là 2 người | `TS. Nomura` |
| `TS. Tạ Quang Ngọc (trợ giảng)` cạnh `TS. Tạ Quang Ngọc` | 2 bản ghi cho cùng một người | 1 người |

Ba quy tắc tương ứng: **không cắt bên trong ngoặc**; mảnh **chỉ có học hàm** thì ghép vào
tên ngay sau; **ghi chú `(...)` ở cuối tên bị cắt** trước khi gộp. Cái thứ ba mở rộng từ luật
sẵn có (trước chỉ cắt `(điều phối)`) — cùng lý do đã nêu ở phần gộp theo tên: một người bị
tách làm hai thì **giấu mất** xung đột của chính họ.

Sau khi sửa: **0 tên đáng ngờ** trên cả ba file; HK2 từ 140 xuống 134 bản ghi giảng viên
(bỏ 3 mảnh rác và các bản trùng do ghi chú).

## Còn hạn chế

- **Một dòng nhiều buổi/tuần** được tách thành nhiều lớp cùng mã — đúng quy ước
  "1 lớp học N buổi/tuần = N dòng cùng Mã lớp" mà form đang dùng.
- **Ô CTĐT có ghi chú bị cắt khi lọc.** `BCSE (với những SV chưa học ở kỳ 1)` và
  `BCSE (với những SV đã học Triết)` đều gom về mã `BCSE`: lọc theo chương trình ra đúng, nhưng
  hệ thống **không phân biệt** hai nhóm sinh viên đó. Ghi chú vẫn còn nguyên ở tên hiển thị và ở
  mục Kiểm tra dữ liệu (`ctdt_khong_phai_ma`) để giáo vụ tự xử.
- **Cơ hữu chưa tự khai được "giờ có thể dạy"**: `manual_teacher_windows` và màn "Giờ rảnh GV"
  hiện chỉ có tác dụng với thỉnh giảng. Cần chốt trước: khung giờ cơ hữu khai là giới hạn cứng
  hay chỉ ưu tiên.
