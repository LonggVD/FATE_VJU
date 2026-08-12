# Kế hoạch sửa — nhập dữ liệu & xếp lịch

Lập sau khi rà soát nhập cả 3 file thật (`FATE.TKB.HK2_2025-2026`, `HK1 2026-2027`,
`HK1 2026-2027-2`). Mọi con số trong tài liệu này là **đo được**, không phải ước lượng —
dùng làm mốc để đối chiếu sau khi sửa (xem [Phụ lục](#phụ-lục-số-đo-hiện-tại)).

---

## 0. Đã xong (không cần làm lại)

| Việc | Kết quả đo được |
|---|---|
| Đọc cột theo **nhãn hàng tiêu đề**, không theo tên sheet/vị trí | 3 file map đúng 100%; file HK1-2 hết lệch 1 cột |
| Thiếu cột bắt buộc → **báo lỗi** kèm tên sheet và cột thiếu | trước đây im lặng ra 300 lớp sai |
| **Đồng giảng**: cả nhóm vào `teacher_ids`, solver ràng buộc từng người | HK1-2: 4 lớp, +11 cặp (lớp, GV); 0 ô giờ chồng nhau |
| Tách tên GV: không cắt trong ngoặc, ghép học hàm lẻ, cắt ghi chú | hết tên rác (`(Nhúng`, `IoT`, `TS`) |
| **Khoá gộp GV** bỏ học hàm/số thứ tự/dấu câu | gộp 3 / 6 / 2 cặp, **0 cặp còn sót** |
| "GV" là **đơn vị** (`Khoa FATE`, `Chuyên gia`) → chưa phân công | 5 bản ghi giả bị loại |
| Tiết ngoài phạm vi **không làm mất lớp** nữa | trước: chọn nguồn đúng → mất lớp CSE4001 |
| Lệch nguồn giờ **khác số buổi** cũng phải xác nhận | HK1-2 hiện 86 lớp cần xác nhận (trước: 0) |
| Màn **Kiểm tra chất lượng dữ liệu** + tải ra Excel | 25 / 49 / 50 chỗ nghi sai mỗi file |
| **Bỏ hẳn cột text** khỏi cả 3 đường đọc | 0 cảnh báo về cột text (trước 143 / 142) |
| **Ô CTĐT ghép = nhiều chương trình thật** | 21 → 9 chương trình; DPV tách đúng người |
| "Bỏ ghim" thả lớp ra cho hệ thống xếp lại | bỏ ghim 2 lớp → cả 2 đổi chỗ, 0 lớp khác xê dịch |
| `fate_export` ghi **số** `program_id` vào cột CTĐT | đã sửa; round-trip khớp 1:1 |
| Phân loại cơ hữu theo **danh sách chính thức** của trường | 49 người; đổi loại 3/3/1 người mỗi file |
| Màn **Giảng viên** hai tab cơ hữu / thỉnh giảng | sửa thông tin · khai giờ · chuyển loại · xem lớp |
| **Chốt lịch theo học phần** (ghim cứng + khoá sửa + bỏ chốt) | 0 lớp đã chốt bị dịch sau 2 lần giải lại |
| Hộp thư vấn đề **theo bộ lọc** của lưới | lọc BCSE: 26 → 6 vấn đề, khớp 77/325 buổi |
| Ô đơn vị của dòng đồng giảng **không tách theo người** | 2 khách mời ĐH Tokyo bị xếp cơ hữu — đã sửa |

---

## 1. Đã chốt

### A1. Có tiết 13
Số tiết/ngày hiện cố định 12 ([app.py:718](webapp/app.py#L718)) nên tiết 13 bị coi là không
hợp lệ. Chốt: **có tiết 13**.

### A2. Giờ trong file là giờ ĐÃ CHỐT
Nguyên văn: *"các lớp đã được import từ file là các lớp đã chốt giờ, tức là giáo viên dạy đã
chốt qua lời với điều phối viên"*. Kéo theo hai điều: giờ đó **không được tự dời**, và quy
định Thứ 7/Chủ nhật **không áp** cho những lớp này.

### A3. Dữ liệu nhập vào giữ nguyên như file
Không tự sửa mã lớp, mã học phần, tên học phần. `VJU2012-3/-4` phải ra **2 mã lớp riêng**.
`VJU2031` trùng mã và `FLF1108` dùng cho cả B1/B2 — để nguyên, sửa file sau.

---

## 2. Đã chốt tiếp (Câu 1 & 2)

### ✅ Câu 1 → **C2**
Lớp đã chốt giờ: **ghim cứng**. GV chưa khai gì: coi như **rảnh cả tuần** để hệ thống xếp các
lớp chưa có giờ. Màn "Giờ rảnh GV" phải ghi rõ "chưa khai = rảnh cả tuần"; hệ thống đếm riêng
số lớp đang ở trạng thái giả định này (`num_availability_assumed`).

### ✅ Câu 2 → **báo lỗi ra để sắp**
Giờ đã chốt bị trùng thì **không tự dời**: lớp đó vào danh sách "không xếp được" kèm tên lớp
đang chiếm chỗ, để giáo vụ sắp lại.

---

## 3. Đợt 1 — ✅ ĐÃ LÀM XONG

Kết quả đo sau khi sửa (so với mốc ở [Phụ lục](#phụ-lục-số-đo-hiện-tại)):

| | HK2 | HK1 | HK1-2 |
|---|---|---|---|
| Lớp có giờ chốt **bị dời giờ** | 0 | 0 | **0** *(trước: 139/140)* |
| Lớp giữ được giờ Thứ 7/CN | 2 | 10 | **22** |
| GD1 thỉnh giảng xếp được | **112**/119 *(trước 24)* | **180**/183 *(trước 140)* | **165**/172 *(trước 144)* |
| GD2 cơ hữu xếp được | 112/119 | 122/130 | 161/175 |
| Lớp "không xếp được" **được liệt kê kèm thủ phạm** | 7 + 7 | 3 + 8 | 7 + 14 |
| Số tiết/ngày | 13 | 13 | **13** |
| Ô giờ chồng nhau (cả nhóm đồng giảng) | 0 | 0 | 0 |

Ngoài dự kiến: phải sửa thêm **một lỗi có sẵn trong mô hình Giai đoạn 2** (xem 1.2b) —
nó làm cả pha vô nghiệm ngay khi bắt đầu ghim giờ.



### 1.1 · Số tiết/ngày: 12 → 13, và tự nới theo file
**Vì sao không đặt cứng 13:** `load_real_fate_data` đã có cách tốt hơn —
`slots_per_day = max_period` ([scheduler_core.py:607, 676, 684](webapp/scheduler_core.py#L607)),
mặc định 12 rồi **nới theo tiết lớn nhất gặp trong file**. Dùng lại cách đó thì kỳ sau file
ghi tiết 14 cũng không phải sửa code.

| Sửa gì | Ở đâu |
|---|---|
| `slotsPerDay` mặc định 12 → **13** (cho cả nhập tay) | [app.py:718](webapp/app.py#L718) |
| Sau khi đọc file: nới `slotsPerDay` lên `max(13, tiết cuối lớn nhất)` | `_build_manual_data_from_rows` |
| `MAX_TIET` chuyển nghĩa: từ "số tiết hệ thống xếp được" thành **tiết lớn nhất còn tin được** (16) | [fate_import.py](webapp/fate_import.py) |

Frontend **không phải sửa**: `ClassTimeSlotPicker`, `SubmissionWindowGrid` và các adapter đều
đọc `slotsPerDay` từ params (đã kiểm).

**Kiểm chứng:** dòng 280/281 HK1-2 (`CSE4001`, `CSE4002` tiết 11-13) chọn cột cấu trúc →
giữ đúng giờ, không còn cảnh báo "vượt tiết", không mất lớp.

**✅ Đã làm.** `slotsPerDay` mặc định 13, `_noi_slots_per_day()` nới thêm theo file (cả 3 file
ra 13). `fate_import.MAX_TIET` giờ mang nghĩa **tiết lớn nhất còn tin được** = 16: quá số đó
thì coi là gõ sai, bỏ giờ (giữ lớp) chứ không nới mô hình solver vô ích.

### 1.2 · Ghim giờ đã chốt (việc quan trọng nhất)
**Phát hiện:** Giai đoạn 2 (cơ hữu) đang **bỏ qua hoàn toàn** giờ trong file.
[scheduler_core.py:448](webapp/scheduler_core.py#L448) dựng miền giá trị bằng
`valid_starts(...)` = mọi ô Thứ 2–Thứ 6, không đọc `original_slot` cũng không đọc
`submissions`.

| Đo trên HK1-2 | Lớp có giờ chốt | Xếp đúng giờ đó | Bị xếp sang giờ khác |
|---|---|---|---|
| GD1 — thỉnh giảng | 151 | 144 | **0** |
| GD2 — **cơ hữu** | 140 | **1** | **139** |

Ví dụ: `VJU2031` file ghi Thứ 2 tiết 6 → hệ thống xếp Thứ 3 tiết 1.

Đây là thiết kế cũ có chủ ý ("cơ hữu tự do hoàn toàn ở GD2") nhưng **trái** nguyên tắc A2.
Không phải 15 dòng như báo cáo trước, mà **~140 lớp mỗi lần nhập**.

**Cách sửa:** trong `solve_resident_phase`, lớp nào có `original_slot` và không phải
`time_assumed` thì miền giá trị chỉ gồm **đúng ô đó** (thay vì `own_valid_starts`). GD1 đã
đúng — miền là `submissions=[slot]` — không sửa.

Giữ nguyên cơ chế `NewOptionalFixedSizeIntervalVar`: trùng thì `is_placed=false`, lớp vào
danh sách "không xếp được" kèm lý do, **không** làm bài toán vô nghiệm (liên quan Câu 2).

**Kiểm chứng:** sau khi giải, **mọi** lớp có giờ trong file nằm đúng giờ đó (mốc hiện tại:
GD2 1/140). Lớp không xếp được phải có tên + lý do.

**✅ Đã làm** — `solve_resident_phase` ghim bằng cách thu hẹp **domain** (không dùng `AddHint`)
nên interval vẫn là Optional: trùng thì lớp rơi vào "không xếp được", không làm vô nghiệm.
Thứ tự ưu tiên: quyết định tay (kéo-thả/ghim ở màn TKB) > giờ chốt từ file > tự do.

### 1.2b · Lỗi có sẵn: Giai đoạn 2 không thể có lớp "không xếp được"
Phát hiện khi ghim: HK2 từ `OPTIMAL 119/119` thành **`INFEASIBLE 0/119`** — mất trắng kết quả.

Nguyên nhân trong mô hình cũ:
```python
model.Add(day_var == d).OnlyEnforceIf(b)
model.Add(day_var != d).OnlyEnforceIf(b.Not())   # <- chiều ngược
model.Add(sum(on_day_bools) == is_placed)
```
`start` luôn có một giá trị cụ thể trong domain **kể cả khi lớp không được xếp**, nên `day_var`
luôn bằng đúng một ngày → `sum(b) == 1` → **`is_placed` bị ép = 1 cho mọi lớp**. Tức GD2 chỉ có
hai kết cục: xếp hết (OPTIMAL) hoặc vô nghiệm. Trước đây không ai thấy vì solver có toàn bộ
Thứ 2–Thứ 6 × 13 tiết để lách nên luôn xếp hết.

**Đã sửa:** bỏ chiều ngược, thay bằng `AddImplication(b, is_placed)`. `b` giờ mang đúng nghĩa
"đã xếp VÀ rơi vào ngày d". Nhờ vậy GD2 mới báo được lớp nào không xếp được — điều kiện để
thực hiện Câu 2.

### 1.2c · Danh sách "không xếp được" của Giai đoạn 2
GD2 trước đây không trả về `unplaced` (chỉ `lessons`/`total`/`placedCount`), nên lớp thiếu chỉ
hiện ra qua con số `161/175` mà không biết là lớp nào.

**Đã thêm** `unplaced[]` cho GD2, mỗi mục kèm: `pinnedLabel` (giờ đã chốt), `reason`
(`PINNED_CONFLICT` / `NO_SLOT`) và **`blockers`** — lớp nào đang chiếm ô đó, ở giai đoạn nào.
Hộp thư vấn đề hiện chúng dưới mục "Không xếp được".

Ví dụ thật từ HK1-2: *Vật lý 1 (VJU2005-3), giờ đã chốt Thứ 2 tiết 6 — đang bị Vật lý 1
(VJU2005-4) chiếm chỗ*. Hai lớp khác nhau, cùng một giảng viên, cùng một ô giờ — file khai
vậy, hệ thống không tự chọn hộ.

### 1.3 · Bỏ chặn Thứ 7 / Chủ nhật cho lớp đã chốt giờ
`MAX_DAY_INDEX = {"GUEST": 5, "RESIDENT": 4}`
([scheduler_core.py:61](webapp/scheduler_core.py#L61)) làm 15 lớp HK1-2 (11 dòng Excel: 280,
281, 293-296, 310-312, 329, 331 — hầu hết Thực tập/Thực hành/Đồ án) bị **bỏ giờ** và chuyển
"để hệ thống tự xếp".

**Cách sửa:** `_parse_class_time` với `enforce_cap=False` **giữ** giờ thay vì trả `(None,
None)`; bỏ cảnh báo `vuot_quy_dinh_ngay` ở luồng nhập file. Quy định ngày **vẫn giữ** cho lớp
*chưa* có giờ — lúc đó là hệ thống chọn hộ, phải theo quy định. Sau 1.2 thì lớp đã ghim không
đi qua `valid_starts` nữa nên Thứ 7/CN tự nhiên hợp lệ.

**Kiểm chứng:** 15 lớp đó giữ đúng giờ Thứ 7/Chủ nhật trong file.

**✅ Đã làm.** Đo được: HK1-2 giữ **22 lớp** ở Thứ 7/CN (gồm cả thỉnh giảng vốn đã được phép),
HK1 10, HK2 2. Cảnh báo `vuot_quy_dinh_ngay` ("đã bỏ giờ") được thay bằng
`ngay_ngoai_quy_dinh_giu_nguyen` ("GIỮ NGUYÊN vì là giờ đã chốt"). Gõ tay qua form thì **vẫn
bị chặn** — đã test: `Cơ hữu chỉ được dạy tới Thứ 6.`

### 1.4 · Giờ rảnh mặc định (chờ Câu 1)
- **Nếu C2:** GV chưa khai gì → `_apply_section_time` cho lớp GUEST chưa có giờ dùng toàn bộ
  khung hợp lệ thay vì `pending_section_ids`. Màn "Giờ rảnh GV" hiện rõ trạng thái
  "chưa khai = rảnh cả tuần".
- **Nếu C1:** điền `manual_teacher_windows[tid]` bằng các slot đã chốt của chính GV đó; lớp
  chưa có giờ vẫn vào `pending_section_ids` như hiện nay.

**Kiểm chứng:** HK2 — số lớp thỉnh giảng không xếp được (mốc: 95, gồm 88 vì chưa khai giờ
rảnh) giảm đúng theo phương án đã chọn.

**✅ Đã làm theo C2.** HK2: thỉnh giảng xếp được từ **24/119 lên 112/119**; `pending_section_ids`
về 0. GV **đã khai** giờ rảnh mà không khung nào đủ dài thì **vẫn báo** (xung đột thật, không
tự nới ra cả tuần). Số lớp đang chạy bằng giả định: HK2 88, HK1 40, HK1-2 21 — đếm riêng ở
`num_availability_assumed`.

### 1.5 · Đồng giảng: hai màn phân tích còn soi GV chính (≈30 phút)
| Chỗ | Vấn đề |
|---|---|
| [app.py:178](webapp/app.py#L178), [app.py:214](webapp/app.py#L214) | payload `submissions`/`pendingSections` chỉ gửi `teacherId` |
| [problemInbox.js:72](frontend/src/adapters/problemInbox.js#L72) | `scanTeacherClashes` gom theo `r.teacherId` đơn lẻ |
| [unplacedAnalysis.js:81](frontend/src/adapters/unplacedAnalysis.js#L81) | "vì sao không xếp được" chỉ tính người chặn theo GV chính |

Thêm `teacherIds` vào 2 payload, sửa 2 chỗ JS, build lại frontend. (`scanPlacedClashes`,
`lessonAdapter`, `_detect_move_conflict` đã sửa hôm nay.)

**✅ Đã làm.** `submissions`, `pendingSections` và `unplaced` (cả hai giai đoạn) đều mang
`teacherIds`; `scanTeacherClashes` và `unplacedAnalysis` gom/soi theo cả nhóm đồng giảng.

### Kiểm chứng chung Đợt 1
- [ ] 3 file: vẫn 0 dòng lỗi, 0 dòng bỏ qua, số lớp không đổi (238 / 313 / 347).
- [ ] Mọi lớp có giờ trong file nằm **đúng** giờ đó sau khi giải, cả GD1 và GD2.
- [ ] Tiết 13 nạp được, xếp được, hiện đúng trên lưới.
- [ ] Danh sách "không xếp được" chỉ còn dòng trùng / xung đột thật, mỗi lớp có lý do.
- [ ] Đồng giảng: 0 ô giờ chồng nhau tính theo cả nhóm; hộp thư vấn đề thấy được người thứ 2.
- [ ] Round-trip xuất → nhập giữ đủ nhóm đồng giảng.

---

## 4. Đợt 2 — ✅ ĐÃ LÀM XONG

### 2.1 · Flask không phục vụ UI mới (≈15 phút)
`app.py` render [templates/index.html](webapp/templates/index.html) — bản UI **cũ**, **0 tham
chiếu** tới màn nhập Excel. Toàn bộ màn Nhập từ Excel / Kiểm tra dữ liệu / Xác nhận giờ nằm ở
`frontend/` (Vite), phải chạy 2 tiến trình. Chạy `py app.py` rồi mở `:5055` là **không thấy**
những màn này.

**✅ Đã làm.** `GET /` trả bản đã build ở `frontend/dist` nếu có, không thì về bản cũ; thêm
`/assets/<file>`, `/favicon.svg`, `/icons.svg`. Bản cũ vẫn mở được ở **`/legacy`** để đối chiếu.
Chạy `py app.py` là ra UI mới — không phải chạy Vite nữa (dev thì vẫn chạy Vite như cũ, có
hot-reload). Đã test: `/` nạp đúng bundle mới, `/legacy` HTTP 200, API không ảnh hưởng.

### 2.2 · Giờ rảnh và phân loại cơ hữu/thỉnh giảng của lớp đồng giảng
`_apply_section_time` lấy `teacher` = **GV chính**: nếu GV chính là cơ hữu mà người thứ 2 là
thỉnh giảng thì giờ rảnh đã khai của người thứ 2 **không được xét**, và lớp đi Giai đoạn 2
theo GV chính. Ràng buộc không-trùng-giờ thì đã áp đủ cả nhóm.

**✅ Đã làm.** Hai luật mới:
- `_loai_lop()` — **có một người thỉnh giảng thì cả lớp đi Giai đoạn 1**. Hướng sai còn lại
  (đi GĐ1 khi cả nhóm đều cơ hữu) chỉ làm lớp bị bó hẹp hơn cần thiết, giáo vụ nhìn ra ngay;
  hướng sai ngược lại thì hệ thống đặt lớp vào giờ khách mời không đến được mà **không ai biết**.
- `_gio_ranh_chung()` — khung giờ của lớp = **GIAO** khung của những người đã khai; ai chưa khai
  gì thì không làm hẹp khung của người khác (nhất quán với C2).

`_sync_teacher_sections` tính lại cả hai thứ đó cho mọi lớp có người vừa đổi — trước đây
`teacher_type` chỉ đổi khi người đó là GV chính.

Đã test 6 ca: chưa ai khai → 72 khung; A khai T2 tiết 1-4 → 3 khung; B khai T2 tiết 3-6 → giao
còn 1 khung; B đổi sang T3 → giao rỗng, vào "chưa xếp được"; A thành cơ hữu mà B vẫn thỉnh
giảng → lớp vẫn GĐ1; cả hai cơ hữu → lớp về GĐ2. Trên file thật: **1 lớp** đổi giai đoạn
(HK2 `CSE3049-3`).

---

## 5. Đợt 3 — ✅ ĐÃ LÀM XONG (trừ 3.4)

### 3.0 · Kéo-thả lớp cơ hữu sang Thứ 7/CN không dính — ✅
Ghim tay ở Giai đoạn 2 trước đây làm bằng cách **cấm mọi slot hợp lệ TRỪ slot đã ghim**
(`forbidden`). Cách đó vỡ khi ghim sang Thứ 7/Chủ nhật: slot đó **không nằm trong**
`valid_starts()` của RESIDENT → "cấm tất cả" → domain rỗng → solver quay về toàn bộ
`valid_starts` → **ghim bị bỏ qua âm thầm**, lớp nhảy về một ngày khác trong tuần.

Nay đưa thẳng slot cho solver qua tham số `ghim_tay={sid: slot}` (`_ghim_tay_o_giai_doan_2`),
đặt domain trực tiếp — không đi qua `valid_starts` nên ghim được mọi ngày, đúng như Giai đoạn 1
vốn đã làm qua `submissions=[slot]`. Thứ tự ưu tiên trong solver: **ghim tay > giờ chốt từ
file > tự do**.

Đã test: ghim một lớp cơ hữu vào Chủ nhật tiết 2 → solver đặt đúng ô đó.

### 3.1 · UI thêm/bớt GV đồng giảng — ✅
Ngăn "Sửa lớp" có thêm ô **Đồng giảng** (danh sách chọn nhiều, lọc bỏ các bản ghi "chỗ trống"
kiểu *Phòng Đào tạo điều phối* vì đó không phải người thật). Hint nói rõ hệ quả: *"N người cùng
dạy — lớp chỉ xếp được vào giờ tất cả đều rảnh"*.

Đã test qua API: POST kèm `coTeacherIds` → lớp thành GĐ1 (vì có 1 thỉnh giảng); PATCH bỏ đồng
giảng → về GĐ2; PATCH thêm lại → GĐ1; `coTeacherIds` sai → HTTP 400 kèm lý do.

### 3.2 · `load_real_fate_data` dùng chung bộ đọc theo nhãn — ✅
Bỏ `_LAYOUT_OLD`/`_LAYOUT_NEW` (hai bộ chỉ số cột cố định, chọn theo tên sheet), thay bằng
`fate_import.detect_sheet()` + `read_layout()`; tên cột cũ map qua `_COT_TU_FATE_IMPORT`.
Import `fate_import` **trong hàm** vì `fate_import` đã `import scheduler_core` — để ở đầu file
là vòng tròn.

| | Bản cũ | Bản mới |
|---|---|---|
| HK2 2025-26 | 173 section | 173 — **giống hệt** |
| HK1 2026-27 | 188 section | 188 — **giống hệt** |
| HK1 2026-27-2 | **crash** (`'>' not supported between str and int`) | 222 section |

Lúc chuyển có một lỗi phải bắt: còn một chỗ `layout.get("time_text")` dùng tên khoá **cũ** trên
layout **mới** → luôn `None` → mọi dòng bỏ cột text, chỉ đọc cột cấu trúc. Phát hiện vì HK1 ra
187 section thay vì 188: dòng 236 ghi `"Thứ 3 và thứ 5, tiết 6-9"` (2 buổi) bị đọc thành 1.

### 3.3 · Nhập gộp thêm — ✅
`POST /api/manual/import/commit` nhận `{"mode": "replace"|"merge"}`; dialog có thêm nút
**"Gộp thêm vào dữ liệu hiện có"** cạnh nút xoá-và-nạp.

Gộp theo đúng các khoá đã dùng trong bản thành công: giảng viên theo `fate_import.khoa_gv`
(bỏ học hàm/dấu câu), học phần theo (mã, tên), chương trình qua `_get_or_create_program`. Bản
ghi "chỗ trống" **luôn tạo mới** (mỗi lớp chưa phân công phải có bản ghi riêng, dùng chung thì
hệ thống coi cả chục lớp là của một người → báo trùng giờ giả).

Lớp **trùng** (cùng mã lớp + học phần + GV chính + giờ) thì bỏ qua, và báo lại số lượng — nạp
lại cùng một file **không** nhân đôi số lớp. Đã test: HK2 (238) + HK1 (313) → **511 lớp**
(40 trùng); gộp lại chính file đó lần nữa → 0 thêm, 313 trùng, tổng không đổi; bộ đã gộp vẫn
giải được (GĐ1 261/270, GĐ2 227/241, 0 lớp bị dời giờ). Gộp vào bộ "Dữ liệu thật" bị chặn
(HTTP 400).

### Lỗ hổng 2 pha: Giai đoạn 2 không thấy giờ Giai đoạn 1 đã chiếm của giảng viên — ✅ đã sửa
Phát hiện khi kiểm chứng 3.4: HK2 ra **1 ô giờ chồng nhau** (chạy lại thì hết — solver có nhiều
lời giải tối ưu nên không phải lần nào cũng trổ).

`solve_resident_phase` đưa các buổi đã xếp ở GĐ1 (`frozen_guest_lessons`) vào ràng buộc **phòng**
(`AddCumulative`) nhưng **không** vào ràng buộc **không-trùng-giờ theo giảng viên**. Trước đây
không ai thấy vì một GV cơ hữu không thể có lớp ở GĐ1 — loại lớp lấy theo loại của "GV chính".
Từ khi loại lớp tính theo **cả nhóm** (nhóm có một khách mời → cả lớp đi GĐ1), một **GV cơ hữu**
có thể có lớp ở GĐ1 và lớp khác ở GĐ2 → GĐ2 không biết giờ của họ đã bị chiếm. HK2 có **2 GV**
nằm ở cả hai giai đoạn.

Đã sửa: mỗi buổi đông băng của GĐ1 vào **cả hai** ràng buộc, theo đúng `teacherIds` của nó.
Chạy 5 lần/file sau khi sửa: **0 ô chồng nhau** ở cả ba file.

### Rà soát sau khi làm — 3 lỗi tìm thêm, đã sửa

| Lỗi | Hậu quả | Sửa |
|---|---|---|
| Gộp hai bộ **khác số tiết/ngày** không mã hoá lại slot | lớp `Thứ 4 tiết 3-4` (spd 13) vào bộ spd 15 thành **`Thứ 2 tiết 14`** — sai cả ngày lẫn tiết | `_doi_slots_per_day()` đưa cả hai về `max(spd)`, dựng lại slot + khung giờ + `manual_teacher_windows` qua chính `_apply_section_time` |
| Dedup khi gộp dùng **tập hợp** | HK2 có 23 khoá lặp phủ 34 lớp (5 lớp `THL1057` chung mã/GV/chưa giờ) → mỗi nhóm thu về 1 → **rụng 34 lớp thật**. HK2+HK1 ra 511 thay vì 546 | đếm theo **số lượng**: nạp lại file đã có vẫn bỏ qua hết, gộp file khác thì thêm đủ |
| Khung "cả tuần" của C2 bị màn *Khung giờ đã báo* xếp thành **"Đã chốt giờ"** | 89 lớp HK2 hiện ngược hẳn sự thực (chưa ai khai giờ) — ngưỡng 90% tính theo 7 ngày, mà khung cả tuần của thỉnh giảng chỉ 6 ngày → 72/84 = 86% | backend gửi cờ `availabilityAssumed` cho từng dòng + `numAvailabilityAssumed`; frontend đọc cờ, giữ cách đếm làm dự phòng |

Đã rà và **không** có vấn đề: khoá snapshot về int nên `max()` khi gộp an toàn (đã test nạp lại
snapshot rồi gộp tiếp); `rowById` có trong tầm vực chỗ liệt kê lớp GĐ2 chưa xếp; chỉ
`SectionEditDrawer` gọi PATCH lớp và nó luôn gửi `coTeacherIds` (đã ghi rõ trong docstring rằng
thiếu field này là xoá nhóm); `/assets` không đụng route static của Flask.

### 3.5 · Nhiều giảng viên: vai trò NGANG NHAU, hiện từng người ra bảng — ✅
Yêu cầu: *"hiển thị tất cả giảng viên đồng giảng ra ngoài giao diện, tách ra theo dòng… không
phân biệt giảng viên chính hay đồng giảng, mọi người vai trò như nhau"*, và *"xử lí ở màn form
kia hoàn toàn không hợp lí, quá khó để theo dõi"*.

**Bỏ khái niệm "GV chính".** `teacher_ids` là danh sách ngang hàng; `teacher_id` chỉ còn là
*người đầu danh sách*, giữ làm khoá hiển thị cho các màn vốn chỉ hiện được một tên (lưới TKB,
tra cứu theo giảng viên). `POST/PATCH /api/manual/section` nhận **`teacherIds`** (vẫn nhận
`teacherId` + `coTeacherIds` kiểu cũ để bản gọi cũ không vỡ); danh sách rỗng → HTTP 400
*"Lớp phải có ít nhất một giảng viên"*.

**Bảng 29 cột: mỗi giảng viên MỘT DÒNG trong ô.** Năm ô của khối giảng viên (Học hàm/vị · Họ và
tên · Đơn vị · Email · SĐT) sinh cùng số dòng theo cùng thứ tự → đọc ngang là ra đúng bộ thông
tin của một người, đúng như file Excel gốc ghi cả nhóm trong một ô. Trước đây bảng chỉ hiện
người đầu nên **email/SĐT của những người còn lại không đọc được ở đâu**. Bấm từng dòng → mở
ngăn của chính người đó.

**Khai giờ có thể dạy cho mọi giảng viên.** Mục "Giờ có thể dạy" trước đây chỉ hiện với thỉnh
giảng, nay hiện với tất cả — kèm ghi chú rằng với cơ hữu thì khung giờ mới chỉ để ghi nhận,
thuật toán chưa dùng để giới hạn Giai đoạn 2 (đó là 3.4 dưới đây).

**Ngăn "Sửa lớp" làm lại**: danh sách ngang hàng, mỗi dòng một giảng viên (chọn/đổi/bỏ tại chỗ),
dưới mỗi người là dòng *đơn vị · email · SĐT*, cạnh mỗi người có nút mở ngăn khai giờ, cuối
danh sách là "Thêm giảng viên cùng dạy". Thay cho hộp tick cũ — nơi người thứ 2 trở đi nằm
trong một danh sách dài, không thấy thông tin của họ và không biết lớp đang có bao nhiêu người.

File xuất ra lấy tên/email từ chính danh sách đó (không còn ghép "người chính + đồng giảng").

Đã test: bớt còn 3 người / đổi thứ tự / còn 2 người / gửi rỗng (400); khai giờ cho một GV **cơ
hữu** → bảng hiện đúng số khung đã khai của từng người; xuất → nhập lại giữ đủ nhóm 5 người.

### 3.6 · Nguồn giờ: cột CẤU TRÚC thắng cột text — ✅
Chốt: *"mặc định chọn tất cả cột cấu trúc, bỏ qua cột text (đấy là cột dữ liệu lỗi cũ)"*.

Bỏ luôn cơ chế tự đoán cũ (`_group_time_overrides` + `_course_group_ids`): nó dò xem nguồn nào
bị "copy chưa sửa" trong cùng học phần rồi đảo ưu tiên cho nhóm đó. Khoa đã chốt cột nào đúng
thì không cần đoán, và `certain`/"cần xem lại" trên UI cũng hết nghĩa — thay bằng nhãn
"đang dùng cột Thứ/Tiết", còn lớp nào phải dùng cột text thì đánh dấu vàng.

| | HK2 | HK1 | HK1-2 |
|---|---|---|---|
| Lớp 2 nguồn lệch nhau → nay đều dùng cột cấu trúc | 0 | 52 | 86 |
| Số lớp sau khi đổi | 238 | 313 → **308** | 347 → **345** |
| Dòng **chỉ có** cột text (phải dùng dự phòng) | 0 | **91** | **56** |
| Lớp bị dời giờ khi giải | 0 | 0 | 0 |

Ví dụ kiểm chứng: `Lê Hải Yến` từ *Thứ 3 tiết 2-3 · Thứ 4 tiết 3-5* → *Thứ 5 tiết 3-5 ·
Thứ 5 tiết 6-9*, khớp cột Thứ/Tiết trong file.

**Chốt cuối: bỏ HẲN cột text, không đọc nữa.** Nguyên văn: *"cột text trong file của tôi được
xác nhận là một cột bỏ đi, hoàn toàn không liên quan đến các dữ liệu của hệ thống"*.

Bỏ ở **cả ba** đường: `fate_import.read_rows`, `scheduler_core.load_real_fate_data` (đường này
trước đó còn **ưu tiên** cột text hơn cột cấu trúc), và màn "Đối chiếu giờ học" + endpoint
`apply-time-fix` (đã xoá cả hai). Quy tắc nhận cột `timeText`, hàm `_text_sessions`, mảng
`timeReviews`, hai loại cảnh báo `bo_gio_cot_text` / `lech_nguon_gio` — xoá hết.

Thiếu 3 cột cấu trúc trong hàng tiêu đề nay là **lỗi chặn nhập**: lúc đó cả file không lớp nào
có giờ, báo ngay còn hơn nạp ra 300 lớp đều "chưa có giờ".

| | HK2 | HK1 | HK1-2 |
|---|---|---|---|
| Số lớp | 238 | **305** | **343** |
| Lớp chưa có giờ → hệ thống tự xếp | 174 | 166 | 97 |
| Cảnh báo về cột text | 0 | **0** *(trước 91 + 52)* | **0** *(trước 56 + 86)* |
| Lỗi đọc file | 0 | 0 | 0 |

### 3.16 · Chốt lịch giảng dạy theo HỌC PHẦN — ✅
Chốt: ghim cứng + ghi chính thức · cả học phần (mọi lớp) · mở lại được · ghi nhật ký ai chốt ·
khoá sửa giờ · kèm ghi chú · nút ở màn Dữ liệu học phần, **nhìn ra ngay môn nào đã/chưa chốt**.

Trước đó chỉ có hai mức: ghim **từng buổi**, và "Lưu thời khoá biểu" chốt **một lần cho cả 343
lớp**. Thực tế giáo vụ chốt dần từng môn — môn nào thống nhất xong với giảng viên thì khoá lại,
các môn còn lại vẫn để hệ thống xếp tiếp mà không làm xê dịch môn đã chốt.

**Chốt** lấy giờ đang hiện trên lưới (ghim tay > GĐ2 > GĐ1 > giờ đã ghi ở lớp), ghi thành giờ
chính thức qua `_apply_section_time` **và** ghim qua `STATE["overrides"]` — cơ chế mạnh nhất ở cả
hai pha, nên giải lại bao nhiêu lần môn đó cũng đứng yên. Còn lớp nào chưa có giờ thì **từ chối
chốt** kèm danh sách lớp thiếu, chứ không chốt một nửa.

**Bỏ chốt** trả giờ về đúng trạng thái *trước khi chốt* — lưu sẵn ở `chot.truoc` cho từng lớp.
Không lưu thì không đoán lại được: sau khi chốt, mọi lớp đều có `original_slot` nên lớp vốn chưa
có giờ sẽ bị kẹt ở vị trí vừa chốt vĩnh viễn.

**Khoá** ở bốn đường, chặn tại backend chứ không chỉ ẩn nút (giáo vụ có thể đang mở hai tab):
`PATCH /section` → 409, `POST /move-lesson` → 409, `POST /clear-override` → 409, và "Xoá giờ hàng
loạt" bỏ qua các lớp đã chốt rồi báo số lượng.

**Nhìn ra tình trạng**: cột "Chốt lịch" gộp theo học phần (nhãn *Đã chốt* + người + ngày + ghi
chú + nút Bỏ chốt), cả vùng học phần đã chốt tô nền xanh nhạt, bộ lọc **Mọi tình trạng chốt**, và
chỉ báo `Đã chốt 5/153 môn · còn 148` bấm được để lọc thẳng ra các môn chưa chốt. Tiến độ tính
trên **cả kỳ**, không theo bộ lọc đang xem.

**Nhập file xong là đã chốt sẵn các môn đủ giờ.** Theo đúng A2 (*"các lớp import từ file là các
lớp đã chốt giờ"*), `_chot_hoc_phan_du_gio_tu_file` đánh dấu ngay khi nhập mọi học phần mà **mọi**
lớp của nó có giờ trong file — nhãn `Chốt theo file`, người chốt `Nhập từ Excel`. Trước đó chỉ báo
đọc "Đã chốt 0/153 môn" trong khi 246/343 lớp đã có giờ chốt, tức nói ngược sự thật.

Học phần còn lớp chưa có giờ thì **không** chốt: bản chính thức của nó chưa hoàn chỉnh.

| Ngay sau khi nhập | HK1-2 | HK1 | HK2 |
|---|---|---|---|
| Học phần chốt theo file | **104**/153 | **60**/153 | **19**/119 |
| Học phần còn lớp thiếu giờ (chưa chốt) | 11 | 6 | 14 |
| Học phần không lớp nào có giờ | 38 | 87 | 86 |

**Khoá đúng phần GIỜ, không khoá cả bản ghi.** Bản đầu chặn nguyên `PATCH /section`, nên môn đã
chốt thành bất khả xâm phạm — không sửa nổi mã lớp sai, email thiếu, địa điểm. Mà công việc ngay
sau khi nhập file chính là dọn những thứ đó. Nay so `time_info` với giờ hiện có (`_gio_doi`): giờ
không đổi thì cho qua. Đo: sửa địa điểm + ghi chú của lớp thuộc môn đã chốt → 200; đổi Thứ → 409;
chuyển "để hệ thống tự xếp" → 409; kéo-thả → 409; bỏ chốt rồi đổi Thứ → 200.

**Hai chữ "chốt" trên cùng màn hình** cũng đã tách: cột *Trạng thái* của từng lớp đổi
`Đã chốt giờ` → **`Có giờ cố định`** (nó chỉ nói lớp có giờ cụ thể hay để hệ thống xếp), còn
*chốt lịch* dành riêng cho học phần.

Đo trên HK1-2 (343 lớp / 153 học phần):

| | Kết quả |
|---|---|
| Chốt 5 môn (48 lớp) | ghim đủ 48/48 |
| Giải lại 2 lần | **0** lớp đã chốt bị dịch giờ |
| Sửa giờ / kéo-thả / bỏ ghim lớp đã chốt | 409, kèm tên người chốt và thời điểm |
| Xoá giờ hàng loạt trùng vào môn đã chốt | bỏ qua đúng 12 lớp, có báo |
| Chốt môn còn lớp chưa có giờ | 400 + liệt kê đích danh lớp thiếu |
| Bỏ chốt | giờ trả về **khớp 100%** trạng thái trước khi chốt |
| Khởi động lại server | trạng thái chốt còn nguyên (lưu cùng snapshot) |

### 3.14 · Phân loại cơ hữu / thỉnh giảng theo DANH SÁCH chính thức — ✅
Chốt: *"Nguồn chính thức — ngoài danh sách là thỉnh giảng"*, nạp qua nút trên giao diện.

Luật cũ đọc chữ "Việt Nhật" trong ô **Đơn vị công tác** của chính file kế hoạch giảng dạy — ô đó
giáo vụ gõ tay mỗi kỳ nên sai đủ kiểu. Nay `List of lecturers.xlsx` (49 người) là nguồn chính
thức: có tên → cơ hữu, không có → thỉnh giảng. Chưa nạp danh sách thì vẫn dùng luật cũ.

Khớp tên **bỏ dấu tiếng Việt** sau khi đã bỏ học hàm/số thứ tự (`fate_lecturers.khoa_ten`): hai
file do hai người gõ nên đặt dấu khác cách — danh sách ghi `PHAN THỊ THANH THỦY`, file kế hoạch
ghi `Phan Thị Thanh Thuỷ`. Giữ dấu thì cùng một người không khớp và bị xếp nhầm thỉnh giảng.

Bản ghi **"chưa phân công"** vẫn theo luật ô đơn vị — nó là chỗ trống, không phải con người, danh
sách không nói gì được về nó. Bỏ sót chỗ này thì 14 chỗ trống của HK1-2 nhảy sang Giai đoạn 1,
đẩy số lớp GĐ1 từ 176 lên 197 mà không ai chủ ý.

| Sau khi nạp danh sách | HK1-2 | HK1 | HK2 |
|---|---|---|---|
| GV cơ hữu | 30 → **27** | 28 → **25** | 25 → **24** |
| GV thỉnh giảng | 49 → **52** | 46 → **49** | 39 → **40** |
| Lớp GĐ1 / GĐ2 | 176/167 → **183/160** | 185/120 → **192/113** | 120/118 → **121/117** |
| Người bị đổi loại | 3 | 3 | 1 |

Cùng ba người ở cả ba file: `Hoàng Thị Thanh Tâm`, `Satoshi Honda`, `Nguyễn Thị Thúy Hằng` — ghi
đơn vị "Trường ĐH Việt Nhật" nhưng không có trong danh sách. Bước xem trước liệt kê đích danh
trước khi nạp, và tab Cơ hữu cảnh báo tiếp nếu còn ai "ngoài danh sách".

**Lỗi có sẵn phát hiện khi làm việc này:** ô Đơn vị công tác của dòng đồng giảng **không được
tách theo từng người** (ô tên, email, SĐT thì có). Dòng 243 HK1-2 *Sinh trắc học*:

```
Họ tên : Gota Morota, Hiroyoshi Iwata, Tạ Kim Nhung
Đơn vị : Trường ĐH Tokyo / Trường ĐH Tokyo / Trường ĐH Việt Nhật
```

Cả ba nhận nguyên chuỗi, mà chuỗi đó có chữ "Việt Nhật" → **hai khách mời ĐH Tokyo bị xếp cơ
hữu**, rơi xuống GĐ2 nơi hệ thống tự do chọn giờ cho họ. Đã tách theo vị trí như email/SĐT.

### 3.15 · Màn Giảng viên: hai tab cơ hữu / thỉnh giảng — ✅
Trước đó **không có chỗ nào nhìn thấy toàn bộ giảng viên**: sửa được qua ngăn kéo mở từ bảng lớp,
còn màn "Giờ rảnh GV" chỉ hiện thỉnh giảng. Nay có mục **Giảng viên** trên sidebar với hai mục
con — hai *loại*, không phải hai khung nhìn: hai loại được xếp ở hai giai đoạn khác nhau và thông
tin cần nhìn cũng khác.

Mỗi tab là một bảng: họ tên · đơn vị · email · SĐT · số lớp kỳ này · tiết/tuần · giờ đã khai ·
nguồn phân loại (`danh sách cơ hữu` / `ngoài danh sách` / `đoán từ ô đơn vị`). Bấm một dòng mở
ngăn kéo làm được cả bốn việc: sửa thông tin, khai giờ có thể dạy, chuyển loại, xem lớp kỳ này.

Ngăn kéo dùng lại `TeacherEditDrawer` sẵn có thay vì viết mới — nó đã có form thông tin + lưới
khai giờ; chỉ thêm mục "Lớp kỳ này" và dòng nhắc khi lựa chọn tay mâu thuẫn với danh sách (nạp
lại danh sách sẽ ghi đè).

Danh sách cơ hữu lưu cùng snapshot nên **sống qua restart** — đã kiểm: 49 người, 27 cơ hữu trước
và sau khi nạp lại.

### 3.17 · Hộp thư vấn đề phải theo BỘ LỌC của lưới — ✅
Hộp thư dựng từ dữ liệu **gốc** nên bộ lọc phạm vi ở màn Thời khoá biểu không chạm tới nó: chọn
"chương trình BCSE" thì lưới thu từ 325 xuống 77 buổi mà hộp thư vẫn báo y nguyên 26 vấn đề — đọc
thành "lọc xong vẫn còn từng đó vấn đề trong phạm vi này", tức nói sai.

`filterProblemInbox(inbox, data, filter)` lọc theo đúng `scope`/`scopeValue` mà lưới dùng
(chương trình · khoá · giảng viên), tính lại `total` / `byType` / `affectedSections` /
`missingHoursCount` và cả tab "Chưa xếp được".

Lọc ở **tầng hiển thị**, không lọc trong `buildProblemInbox`: bản đầy đủ còn được
`buildScheduleView` dùng để tô màu và đánh dấu buổi có vấn đề trên lưới — lọc bản đó thì buổi
ngoài phạm vi mất dấu ngay khi đổi bộ lọc.

Một **vụ** liên quan nhiều lớp (hai lớp trùng giờ): giữ nếu **ít nhất một** lớp thuộc phạm vi —
bỏ đi thì lớp trong phạm vi mất luôn lời giải thích vì sao nó có vấn đề.

| Bộ lọc (HK1-2) | Buổi trên lưới | Vấn đề | Chưa xếp được |
|---|---|---|---|
| Tất cả | 325 | 26 | 9 |
| Chương trình BCSE | 77 | **6** | 0 |
| Chương trình MJM | 41 | **7** | 1 |
| Khoá VJU2025 | 90 | **13** | 2 |
| Khoá VJU2022 | 1 | **1** | 0 |
| Một giảng viên | 2 | **0** | 0 |

Đầu hộp thư ghi thêm *"trong phạm vi đang lọc"*, và khi sạch thì báo "Phạm vi đang lọc không có
vấn đề nào" — chứ không phải "Không có vấn đề nào", câu này ở phạm vi hẹp sẽ đọc thành cả kỳ đã
xong.

### 3.13 · Hộp thư vấn đề: gộp nhóm trùng lặp thành MỘT dòng — ✅
Quét trùng lặp làm theo **từng cặp**, nên 3 lớp giống hệt nhau sinh ra 3 dòng y hệt nhau
(`SAS3021 ⟷ SAS3021` ba lần); 4 lớp thì 6 dòng. Đọc không ra là có **mấy** lớp trùng, mà số
đếm vấn đề cũng phồng lên.

Gộp bằng **hợp-nhóm (union-find)** trên `sectionId` chứ không gom theo khoá (GV + giờ + môn):
hai cặp chung một buổi thì chắc chắn cùng một nhóm, không phải đoán bằng cách dựng khoá nào.
Mục gộp ghi `SAS3021 ×3`, phần chi tiết liệt kê đủ các mã lớp, và `explainedBy` trỏ về mục gộp
để lớp không bị đếm hai lần ở các phân loại sau.

| | Số dòng "nghi trùng lặp" | |
|---|---|---|
| | Trước | Sau |
| HK2 (4 nhóm đôi + 1 nhóm ba) | 7 | **5** (`VJU2018 ×3`) |
| HK1-2 (7 nhóm đôi) | 7 | 7 *(không nhóm nào ≥3)* |
| Thử 4 lớp giống hệt nhau | 6 | **1** (`MA01 ×4`) |

Kiểm: **0** lớp bị kể ở nhiều nhóm; các cặp trùng giờ khác môn (`CLASH`) không đụng tới.

### 3.11 · "Bỏ ghim" = THẢ LỚP RA cho hệ thống xếp lại — ✅
Chốt: *"Cho hệ thống xếp lại"*.

Trước: xoá khỏi `STATE['overrides']` là **chưa đủ**. Giờ chốt từ file được ghim ở **hai chỗ độc
lập** — `overrides` (để UI hiện "đã ghim") **và** chính solver (`original_slot` ở GĐ2,
`submissions=[slot]` ở GĐ1). Bỏ ghim chỉ gỡ chỗ thứ nhất, nên lần giải sau lớp vẫn nằm nguyên
ô cũ: nút không làm gì cả.

Nay có `STATE['bo_ghim']` — tập lớp giáo vụ đã nói rõ "cho xếp lại":
- GĐ2: `solve_resident_phase(..., bo_ghim=...)` bỏ qua ghim theo `original_slot`;
- cả hai pha: `_tam_bo_ghim(data)` tạm đổi `submissions` của lớp đó về **miền của lớp chưa có
  giờ** — khung đã khai của cả nhóm dạy, chưa ai khai thì tự do cả tuần. Tính lại bằng chính
  `_apply_section_time(time_info=None)` để luật "khai rồi thì giới hạn cứng" chỉ nằm một chỗ.

Dùng `with` chứ không sửa hẳn: dữ liệu file vẫn nguyên vẹn để còn hiện "giờ đã chốt trong file"
và để bỏ ghim nhầm thì ghim lại được. Kéo-thả ghim tay lại → tự xoá khỏi `bo_ghim`.

Đo trên HK2 (64 lớp có giờ chốt): bỏ ghim 1 lớp thỉnh giảng (slot 1) và 1 lớp cơ hữu (slot 28)
→ cả hai **đổi chỗ** (slot 8 và 26), **0** lớp khác bị xê dịch.

Nhãn nút đổi thành *"Bỏ ghim — để hệ thống xếp lại"* kèm tooltip nói rõ vị trí chưa đổi ngay mà
đổi từ lần giải kế tiếp.

### 3.12 · Ô CTĐT ghép = NHIỀU chương trình thật — ✅
Chốt: *"Sửa — tính là 2 chương trình thật"*.

`BCSE+MJM` từng là **một** `program_id` riêng. Nay mỗi thành phần một `program_id`, lớp giữ
`program_ids` (danh sách) còn `program` chỉ là người đầu danh sách để làm khoá hiển thị/sắp xếp
— y hệt cặp `teacher_id` / `teacher_ids`.

| | Trước | Sau |
|---|---|---|
| Số chương trình (HK1-2) | 21 | **9** |
| Điều phối viên | `DPV-BCSE+MJM`, `DPV-FTH.ESAS`… | **`DPV-BCSE` + `DPV-MJM`** (mỗi lớp nhiều DPV) |
| Lớp thuộc nhiều CTĐT | — | 33 (HK1-2) · 34 (HK1) · 19 (HK2) |

Kéo theo:
- `check_cross_program_conflicts` lấy **hợp** các chương trình thành phần → GV dạy hai lớp cùng
  ghi `BCSE+MJM` nay tính là dạy liên chương trình (trước bị bỏ sót). Trên 3 file thật con số
  không đổi (9 / 6 / 6) — trường hợp này chưa xuất hiện, sửa là để nó không lọt về sau;
- việc "chưa nộp giờ" hiện trong danh sách của **từng** điều phối viên, không gom thành một mục
  mang tên cả hai (lúc đó cả hai đều tưởng người kia lo);
- thống kê theo khoa đếm lớp cho **mọi** chương trình nó thuộc.

Tên hiển thị vẫn **nguyên văn như file** (`BCSE+MJM`) qua `section_program_label` — hệ thống
*hiểu* là hai, nhưng *viết* đúng như file (A3).

**Bộ lọc: rà hết BỐN màn, không chỉ màn Dữ liệu học phần.** Đợt trước mới sửa 2 màn; hai màn còn
lại vẫn dựng danh sách chọn từ **nhãn nguyên văn** nên `BCSE+MJM` vẫn là một mục riêng:

| Màn | Trước | Sau |
|---|---|---|
| Dữ liệu học phần | `classes.programParts` ✅ | — |
| Thời khoá biểu | `lessons.programParts` ✅ | — |
| Khung giờ đã báo | `rows.programLabel` ❌ | `rows.programParts`, khớp bằng `includes` |
| Giờ rảnh GV | `classes.programName` ❌ | `classes.programParts` |

Backend gửi kèm `programParts` / `programIds` / `facultyName` trên **mọi** bản ghi lớp — buổi học,
submission, lớp chưa nộp giờ — để không màn nào phải bóc tách lại từ chuỗi nhãn.

Kéo theo hai chỗ trước đây bóc từ chuỗi và **vỡ** khi nhãn chuyển sang nguyên văn như file:
- **Tô màu theo Khoa** lấy phần trong ngoặc cuối nhãn (`BCSE (Chưa phân khoa)`); nhãn mới không
  còn ngoặc → mỗi lớp thành một nhóm màu riêng. Nay đọc thẳng `lesson.facultyName`.
- **Bộ lọc Khoa** ở màn Giờ rảnh GV bóc y hệt → danh sách rỗng trơn. Cùng cách sửa.

Và `crossProgram` (nhãn "liên chương trình" ở hộp thư vấn đề) so **tập** chương trình thay vì so
chuỗi: lớp `BCSE+MJM` đứng cạnh lớp `BCSE` thì *không* phải liên chương trình, nhưng so chuỗi
(`"BCSE+MJM" !== "BCSE"`) lại ra ngược.

Kiểm chứng: cả bốn danh sách chọn trên HK1-2 đều ra đúng 9 mã đơn, **0** mục còn dấu ghép.

**Lỗi có sẵn phát hiện khi làm việc này:** `fate_export` ghi `cls["program"]` — tức **số**
`program_id` — vào cột CTĐT, nên mọi file xuất ra có cột CTĐT toàn `0/1/2…` và nạp lại thì sinh
ra các "chương trình" tên `"0"`, `"1"`. Đã đổi sang `programName`. Round-trip HK1-2: 343 lớp /
9 CTĐT / 33 lớp đa-CTĐT — khớp 1:1 với bản gốc.

### 3.7 · Hiện giờ ĐANG DẠY trên lưới "Giờ có thể dạy" — ✅
Nạp file xong, lưới của mọi giảng viên đều trống trơn dù file đã ghi rõ họ dạy giờ nào. Nay lưới
hiện **hai loại ô**:

| Ô | Nghĩa | Tác dụng lên xếp lịch |
|---|---|---|
| Xanh đậm ✓ | Giờ đã khai | **Giới hạn cứng** cho các lớp chưa có giờ |
| Xanh nhạt · | Đang dạy (suy từ lớp đã chốt giờ) | Không giới hạn — chỉ là bằng chứng "dạy được lúc này" |

Không trộn hai loại: nếu nhập giờ đang dạy vào ô "đã khai" thì các lớp chưa có giờ của người đó
chỉ được xếp vào đúng những ô **đã bị chiếm** → không xếp được. Có nút *"Lấy các giờ đang dạy làm
khung đã khai"* cho ai muốn khoá đúng theo lịch hiện có. Đo trên HK1-2: **160 giảng viên** có giờ
đang dạy hiện ra lưới.

Dòng giảng viên trong bảng bị **tô đỏ gạch chân chấm** khi giờ đã chốt của lớp nằm ngoài khung
người đó đã khai — hệ thống giữ nguyên giờ đã chốt (đúng thứ tự ưu tiên) nhưng phải thấy được
chỗ vênh.

### 3.8 · Nạp xong hiện ngay TKB ban đầu, ghim sẵn mọi tiết — ✅
Yêu cầu: *"giờ ở file khi import lên là đã chốt rồi nên khi import xong phải hiện thời khoá biểu
ban đầu từ những khung giờ đã chốt, và mọi tiết phải đã ghim để không bị ảnh hưởng khi thực hiện 2
bước xếp thỉnh giảng và cơ hữu"*.

`_dat_lich_ban_dau()` = `_lich_ban_dau()` (dựng lessons từ `original_slot`, **không** chạy solver)
+ `_ghim_gio_da_chot()` (ghi `STATE["overrides"]`).

| | HK2 | HK1 | HK1-2 |
|---|---|---|---|
| Buổi hiện ngay sau khi nạp | 64 | 139 | **246** |
| Lớp ghim sẵn | 64 | 139 | 246 |
| Buổi bị dời sau khi chạy cả 2 bước | **0** | **0** | **0** |
| "Ghim thất bại" (lớp đã chốt giờ nhưng trùng nhau trong file) | 14 | 8 | 18 |

Chi tiết đáng lưu:
- Cờ `initial: True` để thanh tiến trình ghi *"N buổi chốt từ file"* chứ không báo "đã chạy"; bước
  3 vẫn đòi chạy bước 2 trước (chặn ở **cả** backend và UI).
- Response của `commit` trả kèm `guestResult`/`residentResult` — không thì frontend `setGuestResult(null)`
  và màn TKB vẫn trống cho tới khi tải lại trang.
- Snapshot không lưu kết quả giải, nên `_load_snapshot` dựng lại lịch ban đầu — mở app là thấy.
- Ghim ghi vào `overrides` để **giao diện** hiện trạng thái đã ghim (`isPinned` lấy từ đó); solver
  vốn đã ghim theo `original_slot` rồi.

### 3.9 · Bộ lọc theo KHOÁ — ✅
Thêm ở **cả hai** màn, lấy danh sách khoá từ chính dữ liệu đang có (mỗi kỳ file lại có khoá mới),
sắp giảm dần để khoá mới nhất lên đầu:

- **Dữ liệu học phần**: ô lọc "Mọi khoá" cạnh "Mọi chương trình"/"Mọi trạng thái". Lọc này cũng
  chi phối "Xoá giờ (N)" vì nút đó vốn WYSIWYG theo bộ lọc hiện tại.
- **Thời khoá biểu**: `Xem → Theo khoá` (cạnh Theo chương trình / Theo giảng viên) — in TKB cho
  một khoá là việc thường làm, trước phải lọc tay từng chương trình. Khoá được **nối từ bảng lớp
  qua `sectionId`** như `classCode`, không bắt solver mang thêm thông tin hành chính. Ô tìm kiếm
  cũng khớp cả khoá.

Đo trên file thật: HK1-2 có `VJU2026` 90 lớp · `VJU2025` 96 · `VJU2024` 53 · `VJU2023` 48 ·
`VJU2022` 2 · ghép 2 khoá 9 · trống 45.

**Hai phép kiểm mới trong "Kiểm tra dữ liệu"** — vì giá trị bẩn ở cột này giờ hiện thẳng vào danh
sách chọn: *giá trị không phải mã khoá* (HK2 dòng 7/33 ghi `VNU1001` — mã học phần lọt vào) và
*cùng nhóm khoá viết nhiều kiểu* (`VJU2023+VJU2024` vs `VJU2024+VJU2023`; `VJU2022,VJU2023,VJU2024`
vs cùng chuỗi thêm một dấu cách).

### 3.10 · Ô ghép bằng dấu `+` tính cho TẤT CẢ thành phần — ✅
Chốt: *"BCSE+MJM được tính là cả 2 chương trình BCSE và MJM; tương tự với khoá"*.

Backend tách sẵn `programParts` / `cohortParts`; bộ lọc ở **cả hai màn** dùng danh sách mã ĐƠN và
so theo thành phần. CTĐT tách theo `+ . ( ) [ ]` và ` - `, khoá theo `+ , ; /`.

Ngoặc trong file vừa dùng để **ghép mã** (`BICA (+ESCT)`) vừa để **ghi chú**
(`BCSE (với những SV chưa học ở kỳ 1)`) — cắt mà không xét thì ra `'BICA ('`/`'ESCT)'`, bỏ hẳn
phần trong ngoặc thì mất `ESCT`. Nên cắt trước rồi loại phần nào là ghi chú (**≥2 từ + có chữ
thường**); loại hết thì trả về nguyên ô.

`_PROGRAM_SPLIT_RE` (đặt `program_id`) tách riêng khỏi `_PROGRAM_PART_RE` (bộ lọc) — dùng chung
một regex làm đổi luôn tên chương trình, đo được: HK2 tụt từ 15 xuống 14 chương trình.

| | Trước | Sau |
|---|---|---|
| Mục trong bộ lọc CTĐT (HK1-2) | 16 chuỗi | **9 mã** |
| Mục trong bộ lọc Khoá | 7 | **5** |
| Lọc `BCSE` | 72 lớp | **80** (thêm 8 lớp từ `BCSE+ESCT`, `BCSE+MJM`, `BCSE+MJM+ECE`) |
| Lọc `MJM` | 36 | **45** (9 từ ô ghép) |
| Lọc `VJU2023` | 48 | **57** (9 từ `VJU2023+VJU2024` và `VJU2024+VJU2023`) |

Tên hiển thị trên bảng vẫn giữ nguyên như file (`BCSE+MJM`) — chỉ bộ lọc hiểu theo thành phần.

**Chưa làm**: bên trong hệ thống `BCSE+MJM` vẫn là MỘT `program_id` riêng, nên
`check_cross_program_conflicts` coi nó khác `BCSE` và điều phối viên sinh ra là `DPV-BCSE+MJM`.
Sửa phải đụng mô hình dữ liệu + solver.

### 3.4 · Cơ hữu khai giờ có thể dạy → GIỚI HẠN CỨNG — ✅
Chốt: *"Giới hạn cứng — chỉ xếp trong khung đã khai (giống thỉnh giảng); ai chưa khai thì vẫn tự
do cả tuần"*.

Trước đây Giai đoạn 2 **không đọc `submissions`**: cơ hữu luôn tự do Thứ 2–Thứ 6, nên khai giờ
rảnh cho cơ hữu là vô tác dụng. Nay:

| Trạng thái | Miền giá trị của lớp |
|---|---|
| Ghim tay (kéo-thả ở màn TKB) | đúng ô đã ghim |
| Giờ đã chốt trong file | đúng ô đó |
| **Đã khai giờ rảnh** | **chỉ trong khung đã khai** (giao khung của cả nhóm) |
| Chưa ai khai | tự do (Thứ 2–Thứ 6 theo quy định) |

Khung đã khai **không** bị cắt theo quy định ngày (`MAX_DAY_INDEX`): quy định là để **hệ thống
chọn hộ**, còn giảng viên khai Thứ 7 là con người tự nói mình dạy được hôm đó — cùng lý lẽ với
"giờ trong file là giờ đã chốt".

**Khai rồi mà không còn chỗ thì BÁO, không tự nới.** `_apply_section_time` để `submissions` rỗng
+ đưa lớp vào `pending_section_ids`; solver phân biệt trạng thái này với "chưa ai khai" (cũng
rỗng nhưng không trong pending) và ép `is_placed = 0` → lớp vào danh sách "không xếp được" kèm
**tên lớp đang chiếm chỗ**. Không phân biệt hai trạng thái đó thì khai xong lại được tự do cả
tuần — ngược hẳn ý.

`_sync_teacher_sections` giờ **gọi lại `_apply_section_time`** thay vì tự tính, để luật chỉ nằm
một chỗ.

Đã test 5 ca trên dữ liệu dựng riêng: chưa khai → tự do; khai Thứ 3 tiết 5-8 → cả 2 lớp nằm
trong khung; khai 1 tiết cho lớp 2 tiết → **0/2, báo `NO_SLOT`**; khai đủ cho 1 lớp mà có 2 lớp
→ 1 xếp / 1 báo kèm thủ phạm; xoá khung → về tự do. Trên file thật (không ai khai) kết quả
**không đổi**.

**Chỗ vênh phải nhìn ra được.** Giảng viên khai giờ rảnh mà lớp **đã chốt giờ** lại nằm ngoài
khung đó thì hệ thống **giữ nguyên giờ đã chốt** (đúng thứ tự ưu tiên) — nhưng dòng giảng viên
đó trong bảng được tô đỏ gạch chân chấm, hover ra lý do. Đo trên HK1-2: một GV cơ hữu khai Thứ 3
tiết 1-4 → **4 lớp** đã chốt giờ bị đánh dấu vênh, **1 lớp** chưa có giờ được xếp đúng vào
khung. Không có dấu này thì giáo vụ khai giờ xong thấy lớp vẫn nằm chỗ khác và không hiểu vì
sao.

---

## 6. Việc của khoa / giáo vụ — code không sửa được

Đã chốt A3 là giữ nguyên như file, nên những lỗi dưới đây **vẫn còn** trong dữ liệu. Hệ thống
chỉ liệt kê và **tải ra Excel** (`GET /api/manual/import/issues.xlsx`, nút ở màn xem trước).

| Lỗi | Vị trí | Hệ quả nếu để nguyên |
|---|---|---|
| `MNS2006` gán cho lớp `VJU2012-3/-4` | HK1 d.78-80, HK1-2 d.77,79 | có thêm học phần ảo "MNS2006 – Khoa học toàn cầu và môi trường" |
| `FLF1108` = cả "Tiếng Anh B1" và "Tiếng Anh B2" | HK2 | 2 học phần dùng chung mã lớp |
| `VJU2031` ghi **3 và 5** tín chỉ | HK1, HK1-2 d.33,47 | số tín chỉ không nhất quán |
| `ATE2015`/`AET2015`, `NE2004`/`INE2004`, `VJU20216`/`VJU2016` | HK2 | mỗi typo = một học phần riêng |
| Tên khác dấu: "Hoá/Hóa học 2", "Lịch sử Đảng Cộng sản/cộng sản" | cả 3 file | tách thành 2 học phần |
| **17 bộ dòng nhập trùng** | HK2 9, HK1 17, HK1-2 17 | sau khi ghim giờ (1.2) → **HK2 6 lớp, HK1-2 4 lớp không xếp được** |
| 1 email cho 2 người khác nhau | HK1 3, HK1-2 4 | nhầm người khi liên hệ |
| Ô email lẫn SĐT / 2 email | 4 trường hợp | — |
| CTĐT chứa cả câu (`BCSE (với những SV đã học Triết)`) | HK2 5, HK1 1 | HK1 có 21 "chương trình" cho ~8 chương trình thật |

**Việc còn lại sau khi nhập** (quy trình, không phải lỗi):

| | HK2 | HK1 | HK1-2 |
|---|---|---|---|
| Lớp thỉnh giảng chưa khai giờ rảnh | **88**/119 | 40/183 | 21/172 |
| Lớp cần xác nhận nguồn giờ | 0 | 52 | **86** (74 chưa chắc) |

---

## 7. Điểm nhỏ — cần bạn xác nhận quy ước

- **Buổi vắt qua tiết 6-7** — HK1-2 có 107 dòng (ví dụ tiết 6-9). Nếu tiết 6 là giờ nghỉ trưa
  thì đây là vấn đề lớn; tôi không biết quy ước tiết ↔ giờ của VJU nên chưa dám gọi là lỗi.
- **Số SV dự kiến = 3** ở 10 dòng HK1 (đồ án?).
- **Mã lớp lẫn định dạng**: `VJU2012.8` vs `VJU2012-5`.
- **`TS. Hải`** (HK2) — không đủ định danh để gộp với ai.

---

## Phụ lục: số đo hiện tại

Đây là số đo **TRƯỚC Đợt 1** — giữ nguyên làm mốc đối chiếu; kết quả sau Đợt 1 xem bảng ở
[§3](#3-đợt-1--đã-làm-xong). Đo bằng chính `fate_import.read_rows` →
`app._build_manual_data_from_rows` → `sc.solve_guest_phase` / `solve_resident_phase`.

| | HK2 2025-26 | HK1 2026-27 | HK1 2026-27-2 |
|---|---|---|---|
| Dòng Excel có dữ liệu → lớp | 235 → 238 | 288 → 313 | 303 → 347 |
| Dòng lỗi / bỏ qua | 0 / 0 | 0 / 0 | 0 / 0 |
| Học phần / GV thật / chỗ trống GV | 119 / 64 / 68 | 153 / 74 / 125 | 153 / 79 / 102 |
| Lớp đồng giảng | 10 | 7 | 4 |
| Lớp chưa có giờ | 174 | 75 | 41 |
| **Lớp có giờ chốt bị xếp sang giờ khác (GD2)** | — | — | **139/140** |
| Thỉnh giảng: xếp được / tổng | 24/119 | 140/183 | 144/172 |
| Có giờ mà không xếp được (do dòng trùng) | 7 (6) | 3 (1) | 7 (4) |
| Cơ hữu: xếp được / tổng | 119/119 | 130/130 | 175/175 |
| Kiểm tra dữ liệu: nghi sai / nên rà | 25 / 134 | 49 / 130 | 50 / 160 |
| Tiết cuối lớn nhất trong file | 10 | 12 | **13** |
