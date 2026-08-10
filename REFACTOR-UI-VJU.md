# Refactor giao diện theo design system VJU

Đồng bộ giao diện `frontend/` (công cụ xếp TKB) với app Nhập học VJU.

- **Nguồn tham chiếu:** `D:\App Nhập Học\Project\BE_Enrollment\resources\js`
  (KHÔNG phải `BE_Nhap_Hoc` — project đó là Laravel backend thuần, `resources/views`
  chỉ có `welcome.blade.php` mặc định, `app.css` không chứa token thương hiệu nào).
- **Hướng tiếp cận:** cài Tailwind v4 + port shadcn/ui từ `.tsx` sang `.jsx`.
- **Điều hướng:** đổi từ top-nav ngang sang topbar + sidebar 2 cấp thu gọn được.

---

## 1. Design spec chốt từ reference

### 1.1 Token màu (`resources/css/app.css`)

| Token | Giá trị | Ghi chú |
|---|---|---|
| `--primary` | `oklch(0.55 0.21 27)` | Đỏ VJU `#D82827` |
| `--primary-foreground` | `#ffffff` | |
| `--foreground` | `#333333` | Màu chữ chuẩn hệ thống |
| `--muted-foreground` | `#666666` | Màu xám chuẩn hệ thống |
| `--background` / `--card` / `--popover` | `#ffffff` | |
| `--secondary` / `--muted` | `oklch(0.968 0.007 247.896)` | slate-100 |
| `--accent` | `oklch(0.968 0.01 27)` | ám đỏ nhạt |
| `--accent-foreground` / `--secondary-foreground` | `oklch(0.3 0.12 27)` | đỏ đậm |
| `--destructive` | `oklch(0.577 0.245 27.325)` | |
| `--border` / `--input` | `oklch(0.925 0.012 30)` | |
| `--ring` | `oklch(0.62 0.19 27)` | |
| `--radius` | `0.625rem` | sm/md/lg/xl = −4px/−2px/0/+4px |
| `--font-sans` | `Roboto`, system-ui, … | |

Trạng thái nghiệp vụ: `--status-pending` `oklch(0.795 0.15 86)`,
`--status-approved` `oklch(0.52 0.14 148)` (xanh lá VJU `#1f701f` từ logo),
`--status-rejected` = `--destructive`, `--status-neutral` `#666666`.

Sidebar maroon (`--sidebar` `oklch(0.34 0.12 25)` …): **chỉ dùng cho màn đăng nhập /
chọn vai trò**, không dùng cho sidebar cán bộ.

Base layer: `* { border-color: var(--color-border) }`, outline = ring 50%,
`body` antialiased.

### 1.2 App shell (`layouts/admin-layout.tsx`)

```
bg-muted/40 h-dvh flex-col
├─ Topbar   h-12, bg-background, border-b, px-3
│           trái: nút toggle (Menu ở mobile / PanelLeftClose|Open ở desktop)
│           phải: chuông thông báo + dropdown tài khoản (Avatar + tên + ChevronDown)
└─ flex-1
   ├─ Sidebar  w-64 (thu gọn lg:w-16), bg-background, border-r, py-3 px-2.5
   │           mobile = drawer fixed top-14, trượt -translate-x-full, có overlay bg-black/40
   │           mục đơn "Dashboard" → nhóm 2 cấp (ChevronRight xoay 90° khi mở)
   │           mục con: ml-5 + border-l border-dashed pl-2, text-[13px]
   │           active: bg-muted text-foreground font-semibold
   │           thu gọn: chỉ icon size-10, bấm → mở rộng + xổ nhóm đó
   └─ main overflow-y-auto
      ├─ page header sticky top-0 z-20, border-b, bg-card/95 backdrop-blur,
      │  px-4 pt-4 pb-3 (md:px-6 md:pt-5)
      │  crumbs text-xs text-muted-foreground → h1 text-xl font-bold md:text-2xl
      │  actions bên phải
      └─ nội dung p-4 pt-3 md:p-6 md:pt-4
```

Trạng thái thu gọn lưu ở `localStorage`; drawer tự đóng khi điều hướng hoặc lên desktop.

### 1.3 Component primitive (`components/ui/`, shadcn new-york)

`avatar` `badge` `button` `card` `checkbox` `dialog` `dropdown-menu` `input`
`label` `separator` `spinner` `table` `tabs` — 13 file.

- `Button`: cva, variant `default|destructive|success|warning|outline|secondary|ghost|link`,
  size `default(h-9) |sm(h-8)|lg(h-10)|icon(size-9)`, `rounded-md`, focus ring `[3px] ring-ring/50`.
- `Card`: `bg-card rounded-xl border py-6 shadow-sm`, header/content/footer `px-6`.
- `Badge`: `rounded-md border px-2 py-0.5 text-xs font-medium`.

### 1.4 Component dùng chung (`components/shared/`)

`panel` `pill` `kpi-card` `notice` `list-filter-bar` `list-search` `filter-select`
`multi-select` `pagination` `page-size-select` `loading-overlay` `page-placeholder`
`detail-fields` `image-viewer` `lazy-mount` `charts/`.

- `Panel`: `bg-card rounded-xl border p-4 shadow-sm sm:p-5`, tiêu đề `text-sm font-semibold`
  + mô tả `text-xs text-muted-foreground`, vùng action bên phải.
- `Pill`: 6 tone `blue|violet|amber|emerald|red|slate`, nền `/15`–`/20`, chữ `-700`,
  có biến thể dot / solid / fill / stroke / text để dùng cho chart.
- `KpiCard`: `rounded-xl border p-4 shadow-sm`, biến thể `highlight` nền `bg-primary` chữ trắng.

### 1.5 Icon

`lucide-react`, cỡ chuẩn: `size-4` (nút), `size-4.5` (sidebar cấp 1), `size-3.5` (cấp 2),
`size-5` (topbar), `size-3` (trong badge).

---

## 2. Hiện trạng cần thay

| | Hiện tại | Sau refactor |
|---|---|---|
| CSS | `src/styles.css` 8.669 dòng, 642 class thủ công | Tailwind v4 + token VJU |
| Màu chủ đạo | `--brand-red: #4f46e5` (indigo — **sai brand**) | đỏ VJU `#D82827` |
| Font | Be Vietnam Pro | Roboto |
| Radius | `6px` | `0.625rem` |
| Shell | `Header` + `.top-nav` ngang + `Footer` | Topbar + sidebar 2 cấp + page header |
| Icon | không có | lucide-react |
| Số file JSX | 30 (~4.164 LOC) | giữ nguyên, viết lại className |

Hai trang cần toàn bộ bề ngang (`WIDE_PAGES` trong `App.jsx`): `schedule` (lưới tuần +
hộp thư vấn đề) và `manual` (bảng mirror 29 cột Excel) → sidebar phải **tự thu về rail
icon** khi vào 2 trang này.

---

## 3. Chia phase

Mỗi phase tự chạy được (`npm run build` xanh, app mở được), CSS cũ sống song song cho
tới Phase 10.

| Phase | Nội dung | File chạm |
|---|---|---|
| **1** | Nền tảng: cài `tailwindcss@4` `@tailwindcss/vite` `clsx` `tailwind-merge` `class-variance-authority` `lucide-react` + radix; tạo `src/app.css` với token VJU; alias `@` trong vite; `src/lib/utils.js` | `package.json`, `vite.config.js`, `src/app.css`, `src/main.jsx`, `src/lib/utils.js`, `index.html` |
| **2** | Port 13 primitive `.tsx` → `.jsx` (bỏ type, giữ nguyên class) | `src/components/ui/*` |
| **3** | Port shared: `panel` `pill` `kpi-card` `notice` `list-search` `filter-select` `pagination` `loading-overlay` `page-placeholder` | `src/components/shared/*` |
| **4** | Shell: `AppTopbar`, `AppSidebar` (2 cấp, auto-collapse ở trang rộng), `AppLayout`; đổi `App.jsx`; `nav.js` thành nhóm 2 cấp + icon; `RolePickerScreen` theo style login | `App.jsx`, `constants/nav.js`, `presentation/Header.jsx`, `RolePickerScreen.jsx`, `components/layout/*` |
| **5** | `DataPage` (39 LOC) — trang nhỏ, làm mẫu kiểm chứng token | `pages/DataPage.jsx` |
| **6** | `SchedulePage` (531) + `schedule/*` (5 file) + `timetable/*` (3 file) — nặng nhất, lưới TKB | 9 file |
| **7** | `ManualEntryPage` (284) + `manual/*` (4 drawer, 730 LOC) | 5 file |
| **8** | `SubmissionsPage` (385) + `TeacherAvailabilityPage` (247) + `teacher/ReportedHoursPanel` + `submissions/SubmissionWindowGrid` | 4 file |
| **9** | `HistoryPage` + `EventLogPage` + `SavedSchedulesStubPage` + `Footer` + `SolverProgress` | 5 file |
| **10** | Xoá class chết trong `styles.css`, gỡ import, kiểm build + responsive 3 breakpoint | `src/styles.css` |

### Nhật ký tiến độ

**Phase 1 — xong.**
- Cài `tailwindcss@4` + `@tailwindcss/vite` + `clsx` `tailwind-merge` `class-variance-authority`
  `lucide-react` + 8 gói Radix (66 package, 0 lỗ hổng).
- `src/app.css` — bản sao token VJU từ reference. `src/lib/utils.js` — `cn()` + `initials()`.
- `vite.config.js` — thêm plugin Tailwind + alias `@` → `src/`.
- `index.html` — `lang="vi"`, nạp font Roboto (subset tiếng Việt) như app Nhập học.
- **Va chạm tên biến:** `--muted` / `--accent` / `--radius` trùng giữa CSS cũ và token
  shadcn; nếu để nguyên, định nghĩa cũ đè lên token thật (vd `bg-muted` hoá xám đậm).
  Đã đổi thành `--tkb-muted` / `--tkb-accent` / `--tkb-radius` ở cả định nghĩa lẫn
  120 chỗ dùng trong `styles.css`.
- Token cũ còn lại trỏ thẳng về token VJU (`--brand-red: var(--primary)`…) nên trang
  chưa migrate cũng đúng brand ngay.
- Thay 77 mã màu indigo hard-code sang thang đỏ VJU
  (`#4f46e5→#d82827`, `#4338ca→#a81f1e`, `#6366f1→#e14544`, `#818cf8→#ea6f6e`,
  `#7c3aed→#a81f1e`, `#eef2ff→#fdf2f2`, `#c7d2fe→#f8c9c8`, `#3730a3→#7a1615`,
  `rgba(79|80,70,229,·)→rgba(216,40,39,·)`).
  **Giữ nguyên** `#1d4ed8` (xanh) và `#6d28d9` (tím) — đó là màu phân loại năm học /
  vai trò, ứng với tone `blue` / `violet` của reference, không phải màu thương hiệu.
- `STATUS_COLORS["Thỉnh giảng"]` chuyển từ indigo sang xanh dương — để đỏ dành riêng
  cho "Có vấn đề" và cho thương hiệu.
- `npm run build` xanh; build không còn mã indigo nào.

**Phase 2 — xong.** 13 primitive port sang `src/components/ui/*.jsx`, giữ nguyên
từng class. Bỏ type, `cva`/`Slot`/Radix giữ y nguyên. Tailwind sinh utility đúng
(CSS 119 → 136 kB). Lưu ý: các class `animate-in` / `fade-in-0` / `zoom-in-95` trong
`dialog` + `dropdown-menu` là **no-op** — reference cũng không nạp `tw-animate-css`,
giữ nguyên để không trôi khỏi reference.

**Phase 3 — xong.** 10 component `src/components/shared/*.jsx`: `panel` `pill`
`kpi-card` `notice` `loading-overlay` `page-placeholder` `page-size-select`
`pagination` `list-search` `filter-select`. Kiểu `Tone` (TS) thay bằng
`src/constants/tones.js` để 6 tone `blue|violet|amber|emerald|red|slate` có một chỗ tra cứu.

**Phase 4 — xong.**
- `hooks/use-is-desktop.js`, `components/layout/{app-topbar,app-sidebar,app-layout}.jsx`.
- **Sidebar 2 cấp ăn khớp sẵn có:** `DataPage` và `HistoryPage` vốn tự vẽ thanh tab
  con (`hours`/`availability`, `log`/`saved`). Các tab đó thành mục cấp 2 của sidebar;
  thanh tab trong trang bị gỡ để không có hai thanh điều hướng lồng nhau.
  `manual` không có tab con → mục đơn, không xổ.
- **Auto-collapse ở trang rộng:** `schedule` + `manual` vào là sidebar thu về rail 64px.
  Thu gọn tự động **không** ghi `localStorage` — nếu ghi, rời trang rộng người dùng sẽ
  thấy sidebar thu gọn ở mọi trang khác mà không hiểu tại sao. Lựa chọn thủ công trên
  trang rộng chỉ sống trong phiên xem trang đó.
- **Cảnh báo demo:** nội dung "không dùng vận hành chính thức" từ `Header`/`Footer` cũ
  chuyển thành băng hổ phách trên cùng, đúng chỗ `ImpersonationBar` của reference.
- `Header.jsx` **đã xoá** — topbar + băng cảnh báo thay thế hoàn toàn.
- `RolePickerScreen` dựng lại theo style màn đăng nhập reference (nền `bg-sidebar`
  đỏ đậm, khối thương hiệu VJU, thẻ trắng đổ bóng). Phát hiện vai trò giáo vụ có giá
  trị `"staff"` (không phải `"coordinator"`) → khớp lại `ROLE_LABELS`.
- `nav.js` viết lại thành `NAV_HOME` + `NAV_GROUPS` + `PAGE_LABELS`/`subLabel`/
  `firstSubKey`/`getAllowedGroups`. `App.jsx` bỏ `.page`/`.top-nav`/`.content`, dùng `AppLayout`.
- Kiểm chứng: `npm run build` xanh (1913 module — alias `@` chạy), dev server HTTP 200,
  22 icon lucide dùng đều tồn tại trong bản 1.30.0 đã cài.

**Sửa sau Phase 4 — cascade layer.** Màn chọn vai trò hiện ra mất sạch padding/margin
(chữ dính mép thẻ, nút tràn viền) trong khi màu và `gap` vẫn đúng.

Nguyên nhân: **CSS không nằm trong layer luôn thắng CSS nằm trong layer**, bất kể độ
đặc hiệu hay thứ tự khai báo. `styles.css` được import thẳng từ `main.jsx` nên nằm
ngoài layer, và riêng cái reset `* { margin:0; padding:0 }` của nó đã đủ vô hiệu hoá
**toàn bộ** utility `p-*` / `m-*` của Tailwind (vốn ở `@layer utilities`). `gap` sống
sót vì reset không đụng tới nó — đó là dấu hiệu nhận ra.

Sửa: khai báo `@layer theme, base, legacy, components, utilities;` ở đầu `app.css`
(trước mọi `@import` — hợp lệ theo spec), rồi nạp CSS cũ bằng
`@import './styles.css' layer(legacy);`. `main.jsx` chỉ còn import `app.css`.
Kết quả: legacy vẫn đè preflight (trang chưa migrate giữ diện mạo cũ) nhưng utility
Tailwind luôn thắng legacy. Đã kiểm tra thứ tự trong file build:
`properties → theme → base → legacy → components → utilities`.

**Phase 6 — xong.** Chia làm ba đợt.

- **6a** — `WorkflowStrip` (3 thẻ có số bước / dấu tích khi xong), `PendingMoveBanner`
  (tone hổ phách: "đang chờ" chứ không phải lỗi — đỏ đã là màu thương hiệu và dành cho
  cảnh báo thật), `SaveMoveDialog` + `MoveReasonDialog` chuyển sang shadcn `Dialog`
  (được thêm focus trap + Esc chuẩn), `SolverProgress` dựng lại bằng Tailwind.
  Sửa luôn một lỗi có sẵn: `MoveReasonDialog` không xoá ô lý do giữa các lần mở, lần
  xung đột sau sẽ điền sẵn lý do của lần trước và rất dễ bị gửi nhầm.
- **6b** — `ProblemInbox` ánh xạ 4 loại vấn đề sang tone
  (`clash→red`, `duplicate→amber`, `unplaced→violet`, `missing→slate`) thay cho các
  class `.pi-*`; `DensityNavigator` khoác `Panel` nhưng **giữ nguyên** `.wkgrid` + thang
  `d0..d5`; `LessonTable` chuyển sang shadcn `Table` + `Pill`.
- **6c** — `SchedulePage` viết lại toàn bộ markup: thanh lọc dùng `NativeSelect` /
  `FilterSelect` (có ô tìm, cho danh sách chương trình & giảng viên) / `ListSearch` /
  `Checkbox`, bộ chuyển Lưới–Bảng dạng segmented, ngăn kéo + FAB ở chế độ toàn màn hình.

**Không đụng vào `LessonGridBoard` và `LessonCard`** — toàn bộ thuật toán chia cột
(greedy interval-scheduling), định vị tuyệt đối theo px, tự cuộn khi kéo, và các ghi chú
sửa lỗi trong đó đều giữ nguyên. Chỉ chỉnh token cho các class `.schedv2-*` của chúng.

Thêm `ui/native-select.jsx` — reference không có (bên đó chỉ dùng `FilterSelect`), nhưng
trang này cần select gốc cho các bộ chọn 2–4 lựa chọn bắt buộc, nơi ngữ nghĩa
"`value === null` → Tất cả" của `FilterSelect` là sai.

### Kiểm chứng Phase 6 (chạy thật, không chỉ build)

Dựng kịch bản CDP (`scratchpad/shot.mjs`) chạy Chrome headless, chỉ dùng `fetch` +
`WebSocket` có sẵn của Node 22 — không cài thêm gói. Kịch bản tự chọn vai trò, điều
hướng, bấm "Giải", bắt `Runtime.exceptionThrown` + `console.error/warning`, rồi chụp màn hình.

Kết quả: 90 thẻ buổi học + 104 ô lưới render, **không có lỗi console hay exception** ở
cả ba bố cục (lưới, bảng, toàn màn hình).

**Lỗi phát hiện và đã sửa nhờ bước này:** nền chế độ toàn màn hình đặt `bg-muted/40`
cho giống nền canvas của `AppLayout` — nhưng đó là màu **trong suốt 40%**, nên page
header và băng cảnh báo bên dưới xuyên qua, chữ "Thời khoá biểu" đè lên hàng chú giải.
CSS cũ (`.sv-fullscreen`) dùng nền đặc. Đổi sang `bg-background`.

**Ghi nhận (không sửa — hành vi có sẵn):** dữ liệu chỉ được nạp khi ghé qua "Dữ liệu học
phần" — `ManualEntryPage` là trang duy nhất gọi `refreshData()` khi mount. Vào thẳng
"Thời khoá biểu" sẽ thấy "Chưa có dữ liệu" dù backend đã có. Ngoài ra `guestResult` chỉ
sống trong state React, tải lại trang là mất, phải bấm "Giải" lại.

**Phase 7 — xong.** `ManualEntryPage` + 4 file trong `manual/`.
- Thêm `ui/drawer.jsx` (ngăn kéo phải, dựng trên Radix Dialog) và
  `shared/form-row.jsx` (dòng nhãn–ô nhập 2 cột). Reference không có cả hai:
  form bên đó ngắn nên dùng `Dialog` giữa màn + nhãn xếp chồng, còn form "Sửa lớp"
  ở đây có ~20 trường và người dùng phải đối chiếu với bảng 29 cột phía sau
  trong lúc điền — hộp thoại giữa màn che mất chính cái họ đang đối chiếu.
  Dựng trên Dialog nên vẫn có focus trap, khoá cuộn nền, Esc, nhãn a11y —
  thứ mà `.sed-overlay` cũ (div + onClick) không có.
- **Giữ nguyên CSS bảng mirror 29 cột** (`.xls-*`, `.data-table`): đó là bản sao
  có chủ ý của file Excel gốc, mật độ rất dày (header 3 tầng, `rowSpan` merge-xuống).
  Padding `px-3 py-3` của shadcn `Table` sẽ làm nó phình gấp mấy lần và mất công dụng.
- Bỏ `<h2>Dữ liệu học phần</h2>` trong trang — trùng với tiêu đề mà `AppLayout` đã render.

**Phase 8 — xong.** `SubmissionWindowGrid` (lưới tick giờ rảnh), `ReportedHoursPanel`,
`SubmissionsPage` (3 màn con), `TeacherAvailabilityPage`. Thêm `tone` vào
`SUB_STATE_META` để thay `cls`. Bảng nhiệt `.wkgrid` giữ nguyên ở cả 3 nơi dùng nó.

**Phase 9 — xong.** `EventLogPage` → `Panel` + chấm tone theo loại log;
`SavedSchedulesStubPage` → `PagePlaceholder`; `Footer` rút từ khối 3 cột nền đỏ
xuống một dòng chữ nhạt — 2/3 nội dung cũ ("công cụ demo", "không dùng vận hành
chính thức") đã nằm ở băng cảnh báo trên cùng, lặp lại vừa thừa vừa chiếm chỗ.

**Phase 10 — xong.** Dọn `styles.css`: **8.681 → 1.627 dòng**, xoá 1.027 rule.
Bundle CSS **162 → 72 kB** (gzip 29,5 → 14,1 kB).

Danh sách class giữ lại được **liệt kê tay** từ 6 file còn dùng CSS cũ, KHÔNG suy
từ regex quét `className`: `LessonCard`/`LessonGridBoard` dựng class động (nối mảng
rồi `join`, template literal lồng nhau) nên mọi regex đều bỏ sót — mà đó lại đúng là
hai file không được phép hỏng. Regex thử nghiệm bỏ sót `has-highlight`, `lesson-bar`,
`highlighted`, `pending-save`.

Hai lỗi gặp khi dọn, đều đã sửa:
1. Parser đầu tiên gộp comment vào selector rồi `split(',')` → làm vỡ mọi comment
   có dấu phẩy. Viết lại tokenizer quét từng ký tự, tách comment khỏi selector.
2. Chính dòng comment header tôi viết chứa chuỗi `p-*` + `/m-*` — ký tự đóng comment
   nằm giữa câu nên đóng comment sớm và làm hỏng file.

Kiểm chứng sau khi dọn: chụp lại lưới TKB (toàn màn hình), bảng mirror Excel và bảng
nhiệt giờ rảnh — **giống hệt ảnh trước khi dọn**, không lỗi console. Thêm một lượt
quét tìm class cũ còn dùng trong JSX nhưng đã bị xoá khỏi CSS: không có.

### Sửa sau Phase 10 — nạp dữ liệu khi mở app

**Triệu chứng:** backend đang giữ đủ dữ liệu (`GET /api/data` → HTTP 200, 112 KB) nhưng
mở app lên màn đầu tiên vẫn báo "Chưa có dữ liệu". Phải vòng qua "Dữ liệu học phần" rồi
quay lại mới thấy — không ai đoán được điều đó.

**Nguyên nhân:** `refreshData()` chỉ được gọi ở đúng một chỗ — `ManualEntryPage` lúc
mount. Không trang nào khác gọi. Chính docstring của `GET /api/data` lại nói endpoint
đó sinh ra cho "SPA chuyển màn/refresh".

**Sửa:** chuyển việc nạp lên `AppDataProvider`, chạy một lần khi mount, và gỡ lệnh gọi
trong `ManualEntryPage` (giữ lại chỉ làm gọi `/api/data` hai lần ở lần tải đầu).

Không đi qua `refreshData`/`runAction`: `/api/data` trả **400** khi thật sự chưa có dữ
liệu, mà đó là trạng thái **hợp lệ** lúc đầu học kỳ — qua `runAction` sẽ ghi một dòng đỏ
vào Nhật ký và set `error` ngay màn đầu tiên, báo lỗi cho thứ không phải lỗi. Nên bắt
riêng `err.status === 400` và nuốt; lỗi khác (mất mạng, 500) vẫn báo bình thường.

**Kiểm chứng cả hai nhánh** (không chỉ nhánh thuận):
- Backend có dữ liệu → màn đầu tiên hiện 24 dòng ngay, không còn "Chưa có dữ liệu".
- Backend trống (tạm cất `manual_state_snapshot.json`, khởi động lại Flask để
  `/api/data` thật sự trả 400) → hiện thông báo "Chưa có dữ liệu" nhẹ nhàng, và
  **Nhật ký thao tác (0)** — không có dòng đỏ oan. Sau đó khôi phục snapshot + nạp lại
  dữ liệu thật.

### Sửa tiếp — F5 không còn mất kết quả giải

**Triệu chứng:** đang xem lưới đã xếp → F5 → lưới trống, phải bấm "Giải" lại (2–30 giây)
dù backend còn nguyên kết quả (`/api/state` báo `hasGuestResult: true`).

**Nguyên nhân:** `guestResult`/`residentResult` chỉ sống trong state React. Backend giữ
chúng trong `STATE` nhưng **không endpoint GET nào trả về chính kết quả** — `/api/state`
chỉ báo có/không.

**Sửa:** thêm `GET /api/results` trong `webapp/app.py` (đặt ngay trước `/api/state`), trả
`{guestResult, residentResult}` và **gắn metadata ghim trước khi trả** — giống
`/api/clear-override` đã làm — để thẻ buổi học hiện đúng "nhãn ghim" ngay sau khi tải
lại, không phải đợi tới lượt sửa tay kế tiếp. Frontend gọi nó trong cùng effect với
`/api/data`, và chỉ gọi khi đã có dữ liệu (không có dữ liệu thì chắc chắn không có kết
quả, hỏi thêm chỉ tốn một vòng gọi).

**Kiểm chứng:** tải trang, chọn vai trò, vào "Thời khoá biểu" — **90 thẻ buổi học hiện
ra mà không bấm "Giải" lần nào**; thanh tiến trình hiện đúng "Xếp thỉnh giảng 90/98" kèm
dấu tích và nút "Giải lại"; hộp thư vấn đề đầy đủ 17 mục.

### Dark mode — cố ý KHÔNG bật

Bảng token `.dark` và ~8 biến thể `dark:` trong `components/shared` được giữ theo
reference, nhưng không có gì gán class `.dark`: không nút bật, không đọc
`prefers-color-scheme`.

Lý do (đã đo): `styles.css` còn lại có **0 rule cho `.dark`** nhưng **37 màu nền
hard-code** — ô lưới trắng, popover thẻ buổi học nền `#1e293b`, bảng nhiệt, bảng mirror
Excel. Bật `.dark` bây giờ sẽ cho vỏ ngoài tối nhưng toàn bộ vùng dữ liệu vẫn trắng:
hỏng nửa vời, tệ hơn là không có. Đã ghi rõ ở đầu `src/app.css` để không ai bật nhầm.

### Bỏ vùng cuộn dọc lồng trong bảng mirror Excel

**Triệu chứng:** trang "Dữ liệu học phần" có hai thanh cuộn dọc chồng nhau — một của
trang, một của riêng bảng.

**Nguyên nhân:** `.xls-scroll` đặt `max-height: 72vh` + `overflow-y: auto`. Comment ngay
trong rule đó giải thích lý do: shell **cũ** (`.page{min-height:100vh}`) không ép được
chiều cao thật cho chuỗi flex bên trên, nên nhiều lớp sẽ đẩy cả trang cao ra thay vì cuộn
trong bảng. Lý do đó **hết hiệu lực** từ khi có `AppLayout` — `<main>` đã có
`overflow-y-auto` lo việc cuộn dọc cho toàn bộ nội dung.

**Sửa:** bỏ `max-height` / `overflow-y` / `flex` / `min-height`, **giữ `overflow-x: auto`**
— bảng 29 cột chắc chắn rộng hơn màn hình nên vẫn cần cuộn ngang.

**Kiểm chứng:** quét mọi element có `scrollHeight > clientHeight` kèm `overflow-y`
cuộn được → chỉ còn **đúng một** vùng cuộn dọc là `<main>`. `.xls-scroll` báo
`cuonDocDuoc: false`, `cuonNgangDuoc: true`.

### Bảng mirror Excel chuyển sang tràn viền

Gỡ dần theo phản hồi, kết thúc ở chỗ đúng nhất: **bỏ hẳn thẻ bọc**. Bảng 29 cột đã rộng
hơn màn hình sẵn, ngồi trong thẻ có padding + viền chỉ làm nó phải cuộn ngang sớm hơn
cần thiết — mỗi px bề ngang đều đáng giá.

Padding là do `AppLayout` áp cho **mọi** trang, nên sửa đúng chỗ là cho shell thêm khả
năng tràn viền thay vì lấy margin âm chống lại chính nó:
- `AppLayout` nhận prop `bleed` — bật thì vùng nội dung không còn `p-4 md:p-6`.
- `App.jsx` khai `BLEED_PAGES = new Set(["manual"])` và truyền `bleed` theo trang.
- `ManualEntryPage` bỏ thẻ bọc; thanh công cụ tự lo lề `px-4 md:px-6` của riêng nó, bảng
  chạy sát mép. Hai `Notice` đầu trang cũng tự lo lề.

**Kiểm chứng** — đo `paddingLeft/Right` của vùng nội dung trên từng trang:

| Trang | Desktop 1600px | Mobile 390px |
|---|---|---|
| Khung giờ đã báo | 24px | 16px |
| **Dữ liệu học phần** | **0px** | **0px** |
| Thời khoá biểu | 24px | 16px |

Không trang nào tràn ngang ở cả hai kích thước. Bảng hiện thêm được ~2 cột so với trước.

### Thanh công cụ dính khi cuộn — và biến `--page-header-h`

Bảng có tới 62 lớp; cuộn xuống mà mất ô tìm / bộ lọc / nút thì phải cuộn ngược lên mới
làm tiếp được. Thanh công cụ phải dính lại **ngay dưới** page header vốn đã
`sticky top-0`.

Chiều cao page header **không hard-code được**: nó đổi theo breakpoint
(`pt-4` → `md:pt-5`, `text-xl` → `md:text-2xl`) và theo việc trang đó có crumbs hay
không — một con số cứng sẽ lệch ở đúng một trong bốn tổ hợp. Nên `AppLayout` **đo thật**
bằng `ResizeObserver` rồi phơi ra biến CSS `--page-header-h` trên `<main>`; trang con chỉ
cần `sticky top-(--page-header-h)`.

**Kiểm chứng:** `--page-header-h` = `65px` (đo được). Đáy page header ở 144px, đỉnh thanh
công cụ cũng 144px — khít nhau. Cuộn `<main>` xuống 206px, thanh công cụ vẫn đứng ở 144px.

**Chưa làm:** hàng tiêu đề cột của bảng (`thead`) vẫn cuộn đi mất, nên cuộn sâu sẽ thấy 29
cột dữ liệu mà không còn tên cột. Làm sticky cho nó phức tạp hơn vì header 3 tầng có
`rowSpan`, và cần thêm một offset đo được nữa (chiều cao thanh công cụ).

### Phân vùng khi hover trên bảng mirror

**Triệu chứng:** hover một dòng thì các ô merge-xuống (Mã/Tên học phần, Số TC — cao tới
7 dòng) cũng đổi màu theo, tạo vệt màu **hình chữ L** — không đọc được đang trỏ vào đâu.

**Nguyên nhân:** các ô merge thuộc về dòng **đầu** nhóm. Mọi rule `tr:hover td` vì thế
đều kéo theo cả khối merge cao 7 dòng. Không sửa được bằng CSS chừng nào toàn bộ dòng
còn nằm chung một `<tbody>`.

**Sửa:** tách **mỗi học phần thành một `<tbody>` riêng** — vốn cũng là HTML đúng nghĩa
(`tbody` = nhóm dòng). Có nhóm rồi thì tô được ba mức:

| Vùng | Màu nền | Ý nghĩa |
|---|---|---|
| Ô merge trong vùng đang hover | `#fbeaea` | theo **vùng**, không theo dòng |
| Dòng đang trỏ | `#f9e3e3` | đậm nhất — biết đang nhắm dòng nào |
| Dòng khác cùng vùng | `#fdf5f5` | nhạt — thấy khối merge gồm những lớp nào |
| Vùng khác | trong suốt | không đụng |

Mấu chốt là `td:not(.xls-course)` ở rule hover dòng: ô merge **chỉ** ăn theo màu vùng.
Thêm `tbody + tbody td { border-top: 2px }` để ranh giới vùng đọc được cả khi không hover.

**Kiểm chứng:** dùng `Input.dispatchMouseEvent` qua CDP (di chuột thật — `:hover` không
kích hoạt được bằng `dispatchEvent` từ JS), rồi đọc `getComputedStyle` của từng loại ô.
Kết quả đúng cả bốn mức trong bảng trên; bảng tạo ra 8 `<tbody>` cho 8 học phần đang hiện.

### Chia bảng theo form — bằng NỀN, không bằng vạch kẻ

**Bản cuối.** Ba vùng form phân biệt bằng nền nhạt:

| Vùng | Nền thân bảng | Nền header |
|---|---|---|
| Học phần (4 cột merge) | `#eef3f8` lam slate | `#dde8f2` |
| Giảng viên (nhóm "Kỳ này") | `#f5f1fa` lam tím | `#e9e1f6` |
| Lớp học phần (còn lại) | *để trần* | mặc định |

Vùng "Lớp học phần" **cố ý để trần**: nó chiếm đa số cột, tô nền cả thì bảng thành nặng
và mất tác dụng phân biệt.

Header đậm hơn thân một bậc — nhìn hàng tiêu đề là đọc được ngay bảng chia mấy vùng,
không phải lướt mắt xuống dữ liệu.

Ô màu trong chú giải dùng **chung biến CSS** (`--xls-z-course` / `--xls-z-teacher`) với
bảng, nên đổi màu vùng là chú giải tự theo, không lệch nhau.

**Vì sao bỏ vạch kẻ:** bản trước dùng vạch dọc `2px`, nhưng viền bị răng cưa khi người
dùng zoom lẻ — mà bảng 29 cột thì zoom nhỏ lại chính là phản xạ tự nhiên. Nền không có
viền để làm tròn nên đứng vững ở mọi mức zoom. Đã đo màu nền thật tại
100 / 110 / 125 / 150 / 175 / 200%: **giống hệt nhau ở cả sáu mức**, và cả 25 dòng đều đủ
5 ô vùng Giảng viên.

**Không đụng nhau với hover:** lúc nghỉ hiện nền vùng, khi hover thì đỏ đè lên (đo được
`#f9e3e3` dòng đang trỏ / `#fdf5f5` nhóm / `#fbeaea` ô merge), còn vùng ở nhóm khác giữ
nguyên nền của nó. Hover có độ đặc hiệu cao hơn nên luôn thắng.

### Vạch đậm chia bảng theo form (bản trước — đã thay bằng nền)

Bảng mở **ba** form khác nhau tuỳ ô được bấm, nhưng trước đó không có dấu hiệu nào báo
ranh giới — bấm vào rồi mới biết mở nhầm form.

| Cột | Bấm vào mở | Handler |
|---|---|---|
| 1–4 (4 ô merge) | **Học phần** | `openCourse` |
| 5–15 | **Lớp học phần** | `openSection` (bubble từ `<tr>`) |
| 16–20 (nhóm "Kỳ này") | **Giảng viên** | `openTeacher` |
| 21–28 | **Lớp học phần** | `openSection` |

Vạch `2px #64748b` đặt ở ô **cuối** mỗi vùng (class `xls-formsep`), đậm và tối hơn viền
lưới thường (`1px #d5dbe3`) để không lẫn. Kèm chú giải một dòng dưới thanh công cụ, nằm
**trong** khối sticky nên cuộn sâu vẫn đọc được.

Class đặt **trực tiếp lên ô**, không dùng `:nth-child`: dòng đầu mỗi nhóm có thêm 4 ô
merge còn dòng sau thì không, nên chỉ số cột lệch nhau giữa các dòng — `nth-child` sẽ vẽ
vạch sai chỗ. Riêng ô cột 4 là ô merge (`rowSpan` = số lớp) nên vạch của nó tự kéo dài hết
chiều cao vùng.

**Kiểm chứng:** bấm thật (CDP) vào 4 ô đại diện và đọc tiêu đề ngăn kéo hiện ra —
cột 2 → "Sửa học phần", cột 5 → "Sửa lớp", cột 17 → "Sửa giảng viên", cột 23 → "Sửa lớp".
Đúng cả bốn. Đo `border-right`: cột 4/15/20 = `2px`, cột kề bên (5, 16) = `1px`.

**Sửa kèm:** ô "không có lớp nào khớp bộ lọc" khai `colSpan={27}` trong khi bảng có **28**
cột — dòng trống bị hụt một cột. Lỗi có sẵn, sửa luôn.

#### Vạch dọc trông bị đứt khúc — do ZOOM trình duyệt, không phải CSS

Vạch chia form nhìn như đứt quãng trên máy người dùng. Kết luận cuối: **mức phóng của
trình duyệt khác 100%**. Zoom lẻ làm chiều cao mỗi ô ra số thập phân, từng ô làm tròn
viền một kiểu, nên vạch dọc bị răng cưa/đứt khúc. `Ctrl+0` về 100% là hết.

Đây là lỗi kinh điển của viền bảng ở zoom lẻ, không sửa được bằng CSS.

Các phép đo đã chạy, **đều cho thấy vạch liền** (nên đừng mất công đo lại theo hướng này):

| Phép đo | Kết quả |
|---|---|
| 25/25 dòng có viền `2px` tại đúng `x` | đủ |
| Quét từng hàng pixel dọc vạch (giải mã PNG bằng `zlib` của Node) | 0/3366 hàng thiếu |
| deviceScaleFactor 100 / 125 / 150 / 200% | đều `2px`, không hàng nào thiếu |
| Lúc đang hover | vẫn liền |

**Ghi lại một kết luận sai của chính tài liệu này:** trước đó đoạn này viết rằng nguyên
nhân là vạch ngang chia nhóm (`tbody + tbody`) cũng đặt `2px` nên "cơ" với vạch dọc, và
đã sửa bằng cách hạ xuống `1px`. Sai. Đối chứng bằng cách tiêm ngược rule `2px` cũ vào
trang cho kết quả **giống hệt** bản `1px` — đều tăm tắp. Thay đổi `2px → 1px` vẫn giữ
(vạch dọc nên trội hơn vạch ngang) nhưng nó **không** phải thứ sửa được triệu chứng.

**Lưu ý cho sau này:** bảng này 29 cột nên người dùng có xu hướng zoom nhỏ để thấy nhiều
cột hơn — tức sẽ gặp lại hiện tượng này. Muốn miễn nhiễm hoàn toàn thì thay vạch kẻ bằng
tô nền nhạt khác nhau cho ba vùng: nền không có viền để làm tròn.

### Responsive — đã kiểm

390px / 768px / 1280px: không tràn ngang ở kích thước nào
(`scrollWidth === clientWidth`), sidebar thành drawer ẩn dưới 1024px đúng như reference,
mobile vẫn đọc và thao tác được.

Còn một điểm thẩm mỹ chưa xử lý (đã thống nhất bỏ qua): ở 390px, cụm tab
"Cần thu giờ / Bảng tra cứu / Theo điều phối viên" xuống dòng bên trong control cao
`h-9` nên tràn khỏi chiều cao viên thuốc — vẫn đọc và bấm được.

### Lượt kiểm tra tổng thể (cuối)

Kịch bản CDP chạy một lượt: cả 6 màn (2 cấp sidebar), 3 tab của "Khung giờ đã báo",
mở/đóng cả 3 ngăn kéo bằng Esc, gõ ô tìm, đổi vai trò, và 3 breakpoint. Bắt **mọi**
thông báo console kể cả cảnh báo React, gắn nhãn theo bước để biết lỗi phát sinh ở đâu.

**Một lỗi thật, đã sửa:** bấm vào nhóm sidebar đang mở sẽ đóng nó lại (đúng kiểu
accordion) và giấu mất mục con đang xem — nhưng nút nhóm **không có trạng thái active**,
nên sau khi đóng thì sidebar không còn chỗ nào cho biết người dùng đang ở đâu. Nhánh rail
thu gọn đã đánh dấu, nhánh mở rộng thì không. Sửa: nhóm đang chứa trang hiện tại thì đậm
chữ; nếu đã đóng thì tô thêm nền, giống hệt cách rail đánh dấu.

Chạy lại sau khi sửa: **không phát hiện sự cố nào** — không lỗi, không cảnh báo React,
không trang nào tràn ngang ở 390/768/1280px, vai trò "Xem thôi" chỉ thấy đúng 2 mục
được phép.

**Hai điều nhìn giống lỗi nhưng không phải:**
- Màn "Thời khoá biểu" rỗng trong lượt chạy: do Flask khởi động lại nên `guestResult`
  trong RAM mất (snapshot chỉ phục hồi dữ liệu học phần, không phục hồi kết quả giải).
  Giải lại rồi tải trang là lưới hiện ngay 24 thẻ mà không phải bấm "Giải" — tính năng
  khôi phục vẫn chạy.
- `/api/data` bị gọi **2 lần** mỗi lần tải trang, `/api/results` 1 lần. Đó là `StrictMode`
  của React cố tình chạy effect hai lượt ở chế độ dev. Cờ `cancelled` trong effect chặn
  đúng lượt đầu nên `/api/results` chỉ chạy một lần — tức effect xử lý đúng. Bản build
  production chỉ gọi một lần.

### Sắp lại thứ tự màn theo quy trình làm việc

Thứ tự cũ đi **ngược** quy trình: "Chuẩn bị dữ liệu" (thu giờ giảng viên — bước 2) nằm
**trên** "Dữ liệu học phần" (nhập lớp/học phần — bước 1). Không có bước 1 thì không có gì
để thu giờ, cũng không có gì để giải.

Thứ tự mới khớp đúng 3 bước trên thanh tiến trình của màn Thời khoá biểu:

| | Mục | Vai trò trong quy trình |
|---|---|---|
| — | **Thời khoá biểu** | màn quay lại hằng ngày, để riêng trên cùng |
| 1 | **Dữ liệu học phần** | nhập lớp/học phần/giảng viên (nguồn dữ liệu chính, thay Excel) |
| 2 | **Chuẩn bị dữ liệu** | thu khung giờ GV thỉnh giảng |
| 3 | **Nhật ký & bản lưu** | tra cứu sau khi làm xong |

**Đổi luôn màn vào đầu tiên:** cả hai vai trò giờ vào thẳng "Thời khoá biểu". Trước đây
Giáo vụ rơi vào "Khung giờ đã báo" — một màn *giữa* quy trình, và sau khi xếp lại thì nó
còn nằm ở nhóm thứ hai. Màn Thời khoá biểu mới là chỗ đúng: thanh tiến trình trên đó nói
rõ đang thiếu bước nào (thu giờ bao nhiêu, đã giải chưa), tự nó dẫn người dùng đi tiếp.

Kiểm chứng: chạy lại toàn bộ lượt test — **không phát hiện sự cố nào**.

### Sửa: hộp thoại bị tấm phủ toàn màn hình che (nút "Lưu" như chết)

Kéo-thả một buổi ở màn Thời khoá biểu chỉ bật trong chế độ **toàn màn hình**
(`dragEnabled = detailed && !!onMoveLesson`, `detailed = fullscreen`). Bấm "Lưu" trên
banner mở `SaveMoveDialog` để xác nhận — nhưng Dialog portal ra `document.body` ở `z-50`,
trong khi tấm phủ toàn màn hình là `fixed inset-0 z-200` nền **đục**. Hộp thoại mở thật
nhưng bị che kín, mà Radix đã đặt `pointer-events: none` lên `<body>` nên cả trang cũng
hết bấm được. Log Flask xác nhận: không có lấy một request `/api/move-lesson` nào.

Toàn màn hình dùng một dải z-index riêng (200 tấm phủ / 210 nút nổi / 215 popover /
220 ngăn kéo lỗi / 300 `SolverProgress`), còn primitive dùng chung vẫn ở `z-50` mặc định
của shadcn. Nâng lên trên dải đó, vẫn dưới `SolverProgress`:

| Component | Trước | Sau |
|---|---|---|
| `dialog.jsx` (overlay + content) | `z-50` | `z-250` |
| `drawer.jsx` (overlay + content) | `z-50` | `z-250` |
| `dropdown-menu.jsx` (content) | `z-50` | `z-260` (trên cả hộp thoại — menu có thể bung ra từ trong hộp thoại) |

Chú thích tầng xếp chồng đặt ở đầu `dialog.jsx`, hai file kia trỏ về đó.

### Trang "Giờ rảnh GV" cho khai báo được

Trang này trước chỉ **để xem**: hiện lưới tuần read-only và câu "Giảng viên này chưa khai
giờ rảnh nào" mà không có đường nào để khai — trong khi tên mục ("Chuẩn bị dữ liệu → Giờ
rảnh GV") thì hứa hẹn ngược lại. Chỗ khai giờ thật nằm khuất trong `TeacherEditDrawer` bên
"Dữ liệu học phần".

Nay dùng thẳng `SubmissionWindowGrid` — cùng một cách tương tác với drawer và màn "Khung
giờ đã báo", không chế thêm kiểu click riêng. Lưu qua `PATCH /api/manual/teacher/<id>`
với `{availability: [...]}`, backend tự `_sync_teacher_sections()` lại các lớp của GV đó.

Hai prop cộng thêm cho `SubmissionWindowGrid` (call site cũ không đổi hành vi):

- `allowEmpty` — cho lưu danh sách rỗng. Không có nó thì bấm "Xóa tất cả" xong nút lưu bị
  khoá, giáo vụ không xoá được giờ đã khai nhầm.
- `saveLabel(count)` — đổi nhãn "Nộp N khung giờ" thành "Lưu N khung giờ" / "Xóa hết giờ rảnh".

Lưới cũ `.tav-wkgrid`/`.tav-free` đã xoá khỏi `styles.css`. Trang chỉ liệt kê GV **thỉnh
giảng** (GV cơ hữu được xếp tự do ở Giai đoạn 2, không có khái niệm khung giờ rảnh) — nhãn
bộ lọc nói rõ điều đó để không ai đi tìm một người cơ hữu ở đây rồi tưởng thiếu dữ liệu.

### Chuẩn hoá: xem là mặc định, sửa phải bấm, xong thì Lưu hoặc Hủy

Rà soát toàn bộ chỗ ghi dữ liệu. Kết quả:

| Màn | Trước | Sau |
|---|---|---|
| Thời khoá biểu | kéo-thả → banner "chưa lưu" → Lưu/Hủy → hộp thoại xác nhận | giữ nguyên (đúng mẫu sẵn) |
| Dữ liệu học phần | bảng chỉ xem, bấm dòng mở ngăn kéo sửa — nhưng ngăn kéo **không có nút Hủy** | thêm "Hủy" cạnh "Lưu" ở cả 3 ngăn kéo (lớp / học phần / giảng viên) |
| Khung giờ đã báo | "Nhập giờ" mở lưới sửa, chỉ có nút nộp | thêm "Hủy" (đóng lưới, bỏ nháp) |
| Giờ rảnh GV | **luôn ở chế độ sửa** | mặc định xem → "Chỉnh sửa" → "Lưu"/"Hủy" |
| Nhật ký & bản lưu | chỉ xem | giữ nguyên |
| Nhập từ Excel | 2 bước: xem trước rồi mới ghi | giữ nguyên |

Dựa vào dấu **X** góc trên hoặc Esc để thoát ngăn kéo là bắt người dùng *đoán* rằng bỏ đi
thì không ghi gì — nút "Hủy" nói thẳng điều đó.

**Lưới `SubmissionWindowGrid` viết lại.** Bản cũ là 84 ô vuông viền rời rạc, luôn bấm
được, và không phân biệt nổi dữ liệu đã lưu với thao tác đang dở — ô chọn giảng viên ghi
"8 ô rảnh" trong khi lưới ghi "Đã chọn 0" thì nhìn vào không biết tin cái nào. Bản mới:

- **Hai chế độ tách bạch** — `readOnly` hiện đúng dữ liệu server, không bấm được, không có
  nút; chế độ sửa làm trên một bản nháp riêng, có nhãn "chưa lưu" khi nháp khác bản đã lưu
  (so sánh **tập hợp** chứ không so số lượng).
- **Kéo để quét cả vùng chữ nhật** — giáo vụ thường rảnh nguyên buổi ("T2–T6 tiết 1–4");
  bật từng ô là 20 cú click. Nhả chuột ngoài lưới vẫn chốt đúng (nghe `pointerup` trên
  `window`).
- **Bấm nhãn hàng/cột để bật-tắt cả ngày / cả tiết.**
- **Nhìn ra dáng bảng** — một khung bo góc, kẻ hairline, đầu bảng nền `muted`, ô chọn nền
  emerald đặc; thay vì 84 hộp trắng viền rời.
- Bàn phím: Space/Enter bật-tắt đúng ô đang focus (không tái dùng cơ chế kéo — nó mở một
  vùng quét mà không bao giờ có `pointerup` để chốt).

Ở chế độ xem còn thêm câu tóm tắt nén dải liên tiếp: `[12…19]` → **"T2 tiết 1-8"**, để
khỏi bắt người đọc tự dò 84 ô.

Kiểm chứng bằng CDP trên dữ liệu thật: kéo T4–T6 × tiết 10–12 → 8 ô thành 17 ô (+9, đúng
hình chữ nhật), hiện nhãn "chưa lưu"; bấm "Hủy" → về đúng 8 ô đã lưu; ngăn kéo sửa lớp có
đủ "Hủy"/"Lưu" và Hủy đóng được. Không có lỗi/cảnh báo console nào.

**Còn lệch, đã biết:** ngăn kéo sửa giảng viên có **hai** hành động lưu độc lập (thông tin
GV và giờ có thể dạy). Nút "Hủy" ở đó chỉ bỏ phần thông tin đang sửa — giờ rảnh nếu đã bấm
lưu riêng thì đã ghi rồi. Gộp làm một nút "Lưu" chung sẽ không biết đang lưu cái nào.

### Sửa: chọn vụ trong Hộp thư vấn đề thì phải nhảy tới đúng buổi

Bấm một vụ trong hộp thư chỉ **tô sáng** thẻ và làm mờ phần còn lại — không cuộn. Ở chế
độ toàn màn hình lưới rộng hơn màn hình **10 174px** (đo thật, 15 chương trình × 7 ngày),
nên thẻ được tô sáng hoàn toàn có thể đang nằm ngoài khung nhìn: người dùng vẫn phải tự đi
tìm cái mà hệ thống đã biết chính xác nó ở đâu.

Ba phần:

1. **Mốc trên thẻ** — `data-lesson-id` đặt trên wrapper (chính nó mang toạ độ tuyệt đối),
   không phải trên `LessonCard`.
2. **Cuộn tới, canh giữa** — tự tính `scrollLeft`/`scrollTop` của riêng `.schedv2-grid-wrap`
   thay vì `scrollIntoView()`: `scrollIntoView` cuộn **mọi** tổ tiên cuộn được, kể cả
   `<main>` của app shell, làm giật cả trang. Truyền `{id, seq}` chứ không phải id trần —
   bấm lại đúng vụ đó vẫn phải cuộn về được. Thử lại 5 khung hình vì gỡ bộ lọc làm lưới
   vẽ lại, thẻ có thể chưa tồn tại ngay khung hình đó.
3. **Chọn buổi nào** — buổi **đầu tiên của vụ mà thực sự có mặt trên lưới**. Vụ "trùng
   giảng viên" gồm 2 buổi, một *bị bỏ lại* (không có ô nào để cuộn tới) và một *đã xếp*.

`pickProblem` giờ gỡ **cả** `scope`/`scopeValue` và hai ô tích loại GV, không chỉ
`onlyProblems`/`search` như trước — buổi nằm ngoài chương trình đang lọc vẫn bị ẩn thì
cuộn tới một cái thẻ không tồn tại.

**Nhãn ngày dính theo bề ngang.** Phát hiện khi xem ảnh kiểm chứng: nhảy tới nơi rồi mà
không biết đang xem thứ mấy. Một ngày ở chế độ chi tiết rộng vài nghìn px (mỗi buổi chồng
giờ là một cột con 180px), nhãn canh giữa cột thì trôi hẳn ngoài khung nhìn. Đổi sang
`justify-content: flex-start` + `<span position: sticky; left: 70px>` (70px = bề rộng cột
"Tiết" đang dính trái).

Kiểm chứng CDP trên dữ liệu thật, chế độ toàn màn hình: bấm vụ `#149 ⟷ #201` từ vị trí
cuộn 0 → lưới cuộn tới **4671px**, thẻ `#201` nằm trọn trong khung nhìn, nhãn "Thứ 5" hiện
rõ. Không lỗi console.

### Sửa: kéo-thả xong phải kiểm lại vấn đề và đổi màu ngay

Hộp thư vấn đề đọc `data.submissions` — tức **khung giờ điều phối viên đã báo**, không
phải vị trí thật trên lưới. Hai hệ quả, cả hai đều làm màu đứng yên sau khi sửa tay:

1. `POST /api/move-lesson` chỉ ghi `STATE["overrides"]` và vá vị trí trong kết quả đang
   cache — nó **không** đụng vào `data["submissions"]`. Kéo một buổi đè lên buổi khác của
   cùng giảng viên thì khung giờ đã báo vẫn y nguyên, hộp thư không hề biết.
2. `analyzeSubmissions()` loại giảng viên **cơ hữu** ngay từ đầu (đúng cho màn "Khung giờ
   đã báo", vì cơ hữu không ai nộp giờ hộ). Nên kéo-thả buổi cơ hữu trước giờ **không bao
   giờ** được kiểm.

Thêm nguồn **1b** vào `buildProblemInbox`: quét trùng giờ trên **vị trí thật** của mọi buổi
đang nằm trên lưới — cả hai giai đoạn, cộng buổi vừa thả mà *chưa lưu*. Dùng đúng công thức
`overlaps()` mà `_detect_move_conflict` bên backend dùng, để hai nơi không báo lệch nhau.

Nguồn 1 (khung giờ đã báo) nay **bỏ qua cặp mà cả hai buổi đều đã nằm trên lưới**, nhường
quyền phán xử cho 1b. Thiếu bước này thì chỉ sửa được một nửa: vụ mới hiện ra, còn vụ cũ
kéo đi chỗ khác rồi vẫn nằm lì trong hộp thư.

Giữ nguyên phân loại **"Nghi trùng lặp dữ liệu"** ở 1b (cùng tên môn + cùng thời lượng +
cùng ô) — nếu chỉ báo "trùng giảng viên" thì mất hẳn gợi ý *đối chiếu file nguồn*, vốn mới
là cách xử lý đúng cho loại này. Khử trùng lặp theo cả hai họ id nên một cặp không thể hiện
hai lần dưới hai nhãn.

Kiểm chứng CDP trên dữ liệu thật, không gửi một request ghi nào:

| Thao tác | `buổi có vấn đề` | Vụ trong hộp thư |
|---|---|---|
| gốc | 6 | 8 |
| thả #72 đè lên #73 (cùng GV#61) | **8** | **9** — thêm `#72 ⟷ #73 T2·6-8` |
| kéo tiếp #72 ra ô trống | **6** | **8** — vụ vừa rồi biến mất |
| bấm Hủy | 6 | 8 |

Tất cả xảy ra **trước** khi bấm Lưu. Thứ tự và phân loại 8 vụ gốc không đổi.

#### Vá tiếp: cặp "một buổi đã xếp + một buổi bị bỏ lại"

Bản vá đầu chỉ bỏ qua cặp mà **cả hai** buổi đều đã nằm trên lưới, nên sót đúng trường hợp
phổ biến nhất: `#113 bị bỏ lại ⟷ #114 đã xếp`. Kéo #114 đi chỗ khác thì #113 vẫn đang ở
giờ cũ (nó có nằm trên lưới đâu mà đổi), nên cặp vẫn bị kết luận là trùng.

Sửa tận gốc bằng khái niệm **khung giờ hiệu lực** cho từng buổi:

- đang nằm trên lưới → đúng 1 ô: **vị trí thật**, kể cả bản kéo chưa lưu
- chưa/không xếp được → các khung giờ đã báo, vì đó là tất cả thông tin có

Quét trùng chạy trên khung giờ hiệu lực, bỏ hẳn luật "cả hai phải đã xếp".

Còn một tầng nữa: `analyzeUnplaced()` đọc `guestResult.lessons` để tìm buổi **đang chiếm
chỗ** của buổi bị bỏ lại. Bản kéo chưa lưu không nằm trong đó, nên #114 vẫn bị liệt vào
`blockers` → vẫn nằm trong `sectionIds` của mục "không xếp được" → **vẫn đỏ** dù vụ trùng
đã biến mất. Vá bằng cách truyền vào bản `guestResult` đã áp vị trí đang chờ lưu.

Đo trên dữ liệu thật, kéo #114 sang ô trống (chưa lưu, không một request ghi nào):

| | trước | sau |
|---|---|---|
| `buổi có vấn đề` | 3 | **2** |
| màu thẻ #114 | `rgb(254,226,226)` đỏ | `rgb(219,234,254)` xanh Thỉnh giảng |
| vụ `#113 ⟷ #114` | có | **hết** |
| #113 | nằm trong vụ trùng | chuyển sang **"Không xếp được"** — vẫn được báo, không bị giấu |

**Lưu ý về #113:** sau khi ô đã trống, lý do chi tiết của nó rơi vào nhánh "chưa xác định
được" (vì `analyzeUnplaced` thấy còn khung giờ trống mà CP-SAT không dùng — nó không biết ô
vừa được giải phóng bằng tay). Phân nhóm "Không xếp được" thì đúng; muốn câu chữ nói thẳng
"ô đã trống, bấm Giải lại" thì phải so vị trí trước/sau khi sửa tay, chưa làm.

**Còn thiếu, đã biết:** backend chặn cả **hết phòng** (`roomFull`, so số lớp cùng loại
phòng với `ltPool`/`labPool`) và vẫn trả 409 bắt ghi lý do khi lưu. Nhưng hộp thư chưa có
loại vấn đề "hết phòng" nên tình huống đó **không** đổi màu lúc thả. Thêm loại mới sẽ làm
lộ ra toàn bộ các ô hết phòng sẵn có trong dữ liệu — đó là quyết định về nghiệp vụ, không
phải sửa lỗi, nên để người dùng chốt.

### Rủi ro đã biết

- **Lưới TKB (Phase 6)** dùng nhiều CSS grid/position thủ công — không port máy móc sang
  Tailwind; giữ CSS riêng cho phần lưới nếu cần, chỉ đổi token màu/spacing.
- **Bảng 29 cột (Phase 7)** cần `overflow-x-auto` + `sticky` cột đầu; kiểm tra kỹ sau khi đổi.
- Reference dùng **Inertia** (`<Link>`, `usePage`, `router`) — project này là SPA state-based,
  phải thay bằng `onClick` + state, không copy nguyên.
