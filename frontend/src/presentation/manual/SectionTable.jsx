import { useLayoutEffect, useRef } from "react";
import { Lock, LockOpen } from "lucide-react";
import { Pill } from "@/components/shared/pill";

// BANG MIRROR 29 COT cua file Excel ke hoach giang day - trai tim cua man "Du
// lieu hoc phan". Tach khoi ManualEntryPage vi day la mot khoi tu chung: nhan
// danh sach lop da loc, ve ra bang, bao ra ngoai khi nguoi dung bam.
//
// Giu nguyen CSS cu (.xls-*): day la ban sao CO CHU Y cua file Excel goc, mat do
// rat day (29 cot, header 3 tang, rowSpan merge-xuong). Padding px-3 py-3 cua
// shadcn Table se lam no phinh gap may lan va mat cong dung.

// Tone thay cho cac class danger/warn/ok cu - dung chung bo 6 tone cua design
// system VJU. "Thieu gio" la thu chan xep lich -> do; "Tu dong xep" la chap nhan
// duoc nhung chua chot -> ho phach; "Da chot gio" -> xanh la.
// Xuat ra ngoai: thanh loc ben ManualEntryPage dung chinh bo nhan nay lam danh
// sach chon, khong duoc phep lech voi cai bang dang ve.
export const STATUS_META = {
  missing_time: { label: "Thiếu giờ", tone: "red" },
  ready_auto: { label: "Tự động xếp", tone: "amber" },
  ready_fixed: { label: "Có giờ cố định", tone: "emerald" },
};

// Trang thai SAU khi bam "Luu thoi khoa bieu" ben man Thoi khoa bieu (khac
// STATUS_META o tren - cai do noi ve gio gia dinh/co dinh, khong noi co trung
// gio hay khong). null = chua bam luu lan nao.
const SCHEDULE_STATUS_META = {
  scheduled: { label: "Đã xếp", tone: "emerald" },
  problem: { label: "Có vấn đề", tone: "red" },
  missing: { label: "Chưa có giờ", tone: "amber" },
};

// "Thu" hien so gon (2..7, CN) giong dung cot L cua Excel goc, KHONG dung
// DAY_LABELS ("Thứ 2") - cot nay trong file that chi ghi 1 so/chu.
function dayNumber(day) {
  if (day == null) return "";
  return day === 6 ? "CN" : day + 2;
}

// Toan bo chi tiet chot lich, gop thanh MOT chuoi cho tooltip: ai chot, luc nao,
// bao nhieu lop, ghi chu. Truoc day mo ra thanh 3 dong chu in san trong cot
// "Chot lich" - lap lai o moi hoc phan va keo cot rong ra, trong khi bang da co
// 29 cot. Nay trang thai chi con mot badge duoi ten mon, chi tiet nam o day.
function nhanChot(chot) {
  if (!chot) return "";
  const luc = (chot.at || "").slice(0, 16).replace("T", " ");
  return [
    `${chot.tuFile ? "Chốt theo file" : "Đã chốt lịch"} bởi ${chot.by}${luc ? ` lúc ${luc}` : ""}`,
    chot.soLop ? `${chot.soLop} lớp` : null,
    chot.note || null,
  ].filter(Boolean).join(" · ");
}

// Nhom cac lop (da loc/da cat trang) theo hoc phan, giu THU TU xuat hien -
// dung de ve rowSpan cho 4 cot muc hoc phan (TT/Ma HP/Ten HP/So TC), tai tao
// dung kieu "merge-xuong" cua file Excel goc (xem plan/backend _apply merge).
function groupByCourse(rows) {
  const groups = [];
  const byKey = new Map();
  rows.forEach((c) => {
    const key = c.courseId ?? `__none_${c.courseName || c.sectionId}`;
    let g = byKey.get(key);
    if (!g) {
      g = { courseId: c.courseId, courseCode: c.courseCode, courseName: c.courseName,
            credits: c.credits, chot: c.courseChot || null, rows: [] };
      byKey.set(key, g);
      groups.push(g);
    }
    g.rows.push(c);
  });
  return groups;
}


// So cot DONG BANG ben trai: TT · Ma hoc phan · Ten hoc phan · So tin chi ·
// Chot lich - dung 5 o dau cua dong tieu de thu nhat (chung deu rowSpan={3}).
const SO_COT_DONG_BANG = 5;


export default function SectionTable({
  rows, canEdit, loading, tenLop,
  onOpenSection, onOpenCourse, onOpenTeacher, onChot, onBoChot, onBoHocChung,
}) {
  const courseGroups = groupByCourse(rows);
  const tableRef = useRef(null);

  // DO be rong that cua 5 cot dong bang, ghi thanh --fz-1..--fz-4 cho CSS dat
  // `left` (xem khoi "DONG BANG" trong styles.css).
  //
  // Khong tinh san trong CSS duoc: cac cot do khai `width` chu khong phai be
  // rong CHOT - table-layout mac dinh van noi cot ra khi noi dung doi (ma lop
  // dai, tieu de xuong dong), va zoom le lam moi so le di vai phan muoi px. Chi
  // can lech mot chut la hai cot dinh chong len nhau hoac ho ra khe trang.
  //
  // Cong don tu getBoundingClientRect().width chu khong doc offsetLeft: o dang
  // dinh da bi day khoi vi tri that cua no, doc toa do se ra so cua trang thai
  // dang cuon roi tu khoa chinh no o do.
  useLayoutEffect(() => {
    const table = tableRef.current;
    if (!table) return;
    const ths = [...table.querySelectorAll(":scope > thead > tr:first-child > th")]
      .slice(0, SO_COT_DONG_BANG);
    if (ths.length === 0) return;

    const do_lai = () => {
      let x = 0;
      ths.forEach((th, i) => {
        x += th.getBoundingClientRect().width;
        // --fz-1 la moc trai cua cot THU HAI (= be rong cot dau), nen ghi sau
        // khi da cong. Cot dau luon left:0, khong can bien.
        table.style.setProperty(`--fz-${i + 1}`, `${x}px`);
      });
    };

    do_lai();
    const ro = new ResizeObserver(do_lai);
    ths.forEach((th) => ro.observe(th));
    return () => ro.disconnect();
  }, []);

  // Bong cua vung dong bang chi hien khi DA cuon qua no - bong hien san luc chua
  // cuon doc ra thanh mot vet toi vo co giua bang. Ghi thang vao DOM chu khong
  // qua useState: moi nac cuon ma ve lai ca bang vai tram dong thi giat.
  const onScroll = (e) => {
    const el = e.currentTarget;
    el.dataset.sx = el.scrollLeft > 0 ? "1" : "0";
    el.dataset.sy = el.scrollTop > 0 ? "1" : "0";
  };

  return (
  <div className="xls-scroll" onScroll={onScroll}>
    <table className="data-table xls-table" ref={tableRef}>
      {/* Ba vung form phan biet bang NEN (`xls-z-course` / `xls-z-teacher`),
          khong bang vach ke. Vung con lai (Lop hoc phan) de tran - no chiem
          da so cot, to nen ca thi bang thanh nang.

          Truoc do dung vach doc 2px, nhung vien bi rang cua khi nguoi dung
          zoom le (chieu cao o ra so thap phan, moi o lam tron mot kieu) -
          ma bang 29 cot thi zoom nho lai la phan xa tu nhien. Nen khong co
          vien de lam tron nen dung vung o moi muc zoom.

          Class dat TRUC TIEP len o, khong dung :nth-child: dong DAU moi nhom
          co them 4 o merge con dong sau khong, nen chi so cot lech nhau. */}
      <thead>
        <tr>
          <th rowSpan={3} className="xls-z-course xls-c-tt">TT</th>
          <th rowSpan={3} className="xls-z-course xls-c-ma">Mã học phần</th>
          <th rowSpan={3} className="xls-z-course xls-c-ten">Tên học phần</th>
          <th rowSpan={3} className="xls-z-course xls-c-tc">Số tín chỉ</th>
          <th rowSpan={3} className="xls-z-course xls-chot-head">Chốt lịch</th>
          <th rowSpan={3}>Mã lớp học phần</th>
          <th colSpan={2}>Phân bổ TC</th>
          <th rowSpan={3}>Khóa</th>
          <th rowSpan={3}>CTĐT</th>
          <th rowSpan={3}>Số SV dự kiến</th>
          <th colSpan={3}>Thời gian</th>
          <th colSpan={7}>Thông tin giảng viên</th>
          <th colSpan={2}>Số giờ dạy</th>
          <th rowSpan={3}>Địa điểm</th>
          <th rowSpan={3}>Hình thức</th>
          <th rowSpan={3}>Ngôn ngữ</th>
          <th rowSpan={3}>Yêu cầu khác</th>
          <th rowSpan={3}>Ghi chú</th>
          <th rowSpan={3}>Trạng thái</th>
          <th rowSpan={3}>Trạng thái lịch</th>
        </tr>
        <tr>
          <th rowSpan={2}>Lý thuyết</th>
          <th rowSpan={2}>Thực hành</th>
          <th rowSpan={2}>Thứ</th>
          <th rowSpan={2}>Tiết đầu</th>
          <th rowSpan={2}>Tiết cuối</th>
          <th colSpan={2} className="xls-ref-head">Kỳ trước (để đối chiếu)</th>
          <th colSpan={5} className="xls-z-teacher">Kỳ này</th>
          <th rowSpan={2}>Lý thuyết</th>
          <th rowSpan={2}>Thực hành</th>
        </tr>
        <tr>
          <th className="xls-ref-head">Họ tên GV</th>
          <th className="xls-ref-head">Đơn vị công tác</th>
          <th className="xls-z-teacher">Học hàm/vị</th>
          <th className="xls-z-teacher">Họ và tên GV</th>
          <th className="xls-z-teacher">Đơn vị công tác</th>
          <th className="xls-z-teacher">Email</th>
          <th className="xls-z-teacher">SĐT</th>
        </tr>
      </thead>
      {/* MOI HOC PHAN = MOT <tbody> rieng, khong don het vao 1 tbody.
          Day vua la HTML dung nghia (tbody = nhom dong), vua la thu duy
          nhat cho phep to sang CA VUNG khi hover: cac o merge-xuong
          (Ma/Ten hoc phan/So TC) thuoc ve dong DAU nhom, nen hover 1 dong
          bang CSS tren <tr> se keo theo o merge cao 7 dong -> vet mau hinh
          chu L, khong doc duoc dang tro vao dau. Voi tbody rieng thi:
            · hover bat ky dong nao -> ca vung hoc phan sang nhe (thay ranh gioi)
            · rieng dong dang tro -> dam hon (thay dang nham dong nao)
            · o merge CHI theo mau vung, khong theo mau dong. */}
      {courseGroups.map((g, gi) => (
        <tbody key={g.courseId ?? `none-${gi}`}>
          {g.rows.map((c, i) => {
          const meta = STATUS_META[c.status] || { label: c.status, tone: "slate" };
          return (
            <tr key={c.sectionId} className="sed-row xls-row" onClick={onOpenSection(c.sectionId)}>
              {i === 0 && <td className="xls-course xls-z-course xls-c-tt" rowSpan={g.rows.length} onClick={onOpenCourse(g.courseId)}>{c.sectionId}</td>}
              {i === 0 && <td className="xls-course xls-z-course xls-c-ma" rowSpan={g.rows.length} onClick={onOpenCourse(g.courseId)}>{g.courseCode || "—"}</td>}
              {/* TRANG THAI da chot nam ngay DUOI TEN hoc phan, khong o cot
                  rieng: chot ap cho ca hoc phan nen day moi la cho doc
                  no tu nhien. Cot "Chot lich" ben canh chi con NUT.
                  Chi tiet (nguoi chot, luc nao, ghi chu) vao tooltip -
                  truoc day in het ra o rieng, lap lai o moi hoc phan va
                  keo cot rong ra ~9rem trong khi bang da co 29 cot. */}
              {i === 0 && (
                <td className="xls-course xls-z-course xls-c-ten" rowSpan={g.rows.length} onClick={onOpenCourse(g.courseId)}>
                  {/* Bo trong DIV chu khong dat flex thang len <td>: mot o
                      co rowSpan ma doi display khoi table-cell thi trinh
                      duyet bo qua rowSpan -> vo toan bo layout merge. */}
                  <div className="xls-course-ten">
                    <span>{g.courseName || "—"}</span>
                    {g.chot && (
                      <span className="xls-chot-badge" title={nhanChot(g.chot)}>
                        <Lock className="size-3" />
                        {/* Chot TU FILE (moi lop deu co gio da thong nhat
                            san - quy tac A2) khac chot TAY: giao vu can
                            biet mon nao minh da thuc su ra soat. */}
                        {g.chot.tuFile ? "Chốt theo file" : "Đã chốt"}
                      </span>
                    )}
                  </div>
                </td>
              )}
              {i === 0 && <td className="xls-course xls-z-course xls-c-tc" rowSpan={g.rows.length} onClick={onOpenCourse(g.courseId)}>{g.credits ?? "—"}</td>}
              {/* CHOT LICH theo HOC PHAN: o merge xuong ca nhom, dung
                  nhu Ma/Ten hoc phan - vi chot ap cho MOI lop cua mon,
                  khong phai cho dong dang tro.

                  Cot nay chi con NUT (icon), trang thai da chuyen xuong
                  duoi ten hoc phan - xem o "Ten hoc phan" ben tren. */}
              {i === 0 && (
                <td
                  className="xls-course xls-z-course xls-chot"
                  rowSpan={g.rows.length}
                  onClick={(e) => e.stopPropagation()}
                >
                  {canEdit && g.courseId != null ? (
                    <button
                      type="button"
                      className={g.chot ? "xls-chot-btn xls-chot-btn-mo" : "xls-chot-btn"}
                      disabled={loading}
                      onClick={g.chot ? onBoChot(g) : () => onChot(g)}
                      aria-label={g.chot ? "Bỏ chốt học phần" : "Chốt lịch học phần"}
                      title={g.chot
                        ? `Bỏ chốt để sửa lại giờ.\n${nhanChot(g.chot)}`
                        : "Chốt lịch: ghi giờ đang hiển thị của mọi lớp trong học phần này thành giờ chính thức và ghim cứng"}
                    >
                      {g.chot ? <LockOpen className="size-3.5" /> : <Lock className="size-3.5" />}
                    </button>
                  ) : (
                    <span className="xls-chot-meta">{g.chot ? "đã chốt" : "—"}</span>
                  )}
                </td>
              )}
              <td>
                {c.classCode || "—"}
                {/* HOC CHUNG: lop nay la MOT buoi cung cac lop khac. Badge
                    bam duoc de TACH - can o day vi khi sua du lieu bi chan
                    ("tách nhóm học chung trước") thi giao vu dang o chinh
                    bang nay, khong phai o man Thoi khoa bieu. */}
                {c.hocChungId != null && (
                  <button
                    type="button"
                    className="xls-hc-badge"
                    disabled={loading || !canEdit}
                    onClick={(e) => {
                      e.stopPropagation();
                      if (!canEdit) return;
                      if (!window.confirm(
                        `Tách nhóm học chung của lớp "${c.classCode || `#${c.sectionId}`}"?

`
                        + `Các lớp sẽ trở lại độc lập. Từ lần Giải sau hệ thống xếp chúng riêng `
                        + `và báo trùng giảng viên nếu vẫn cùng giờ.`)) return;
                      onBoHocChung(c.hocChungId);
                    }}
                    title={
                      `Học chung một buổi với: ${c.hocChungWith.map(tenLop).join(", ")}`
                      + `. Bấm để tách nhóm.`
                      + (c.hocChungLockedBy ? `

Đang bị khoá giờ: ${c.hocChungLockedBy}` : "")
                    }
                  >
                    học chung ×{c.hocChungWith.length + 1}
                    {c.hocChungLockedBy && " 🔒"}
                  </button>
                )}
              </td>
              <td>{c.ltCredits ?? "—"}</td>
              <td>{c.thCredits ?? "—"}</td>
              <td>{c.cohort || "—"}</td>
              <td>{c.programLabel}</td>
              <td>{c.expectedStudents ?? "—"}</td>
              <td>{dayNumber(c.day)}</td>
              <td>{c.periodStart ?? "—"}</td>
              <td>{c.periodEnd ?? "—"}</td>
              <td className="xls-ref">{c.prevTeacherName || "—"}</td>
              <td className="xls-ref">{c.prevTeacherOrg || "—"}</td>
              {/* MOI GIANG VIEN MOT DONG trong o - dung nhu file Excel goc
                  ghi ca nhom trong mot o. Truoc day chi hien nguoi dau nen
                  email/SDT cua nhung nguoi con lai khong doc duoc o dau, va
                  khong bam vao ho de khai gio duoc. Bam vao TUNG dong -> mo
                  ngan sua CHINH nguoi do (co muc "Gio co the day"). */}
              {["title", "name", "org", "email", "phone"].map((truong) => (
                <td key={truong} className="xls-z-teacher xls-gv-cell">
                  {(c.teachers?.length ? c.teachers : [null]).map((t, k) => (
                    <button
                      type="button"
                      key={t ? t.id : k}
                      // Gio da chot cua lop nam NGOAI khung nguoi do da khai:
                      // he thong CO Y khong doi gio da chot, nhung phai thay
                      // duoc cho venh nay chu khong de giao vu tu doan.
                      className={
                        "xls-gv-line" + (t?.outsideDeclared ? " xls-gv-venh" : "")
                      }
                      title={
                        t
                          ? t.outsideDeclared
                            ? `${t.name} — giờ đã chốt của lớp này NGOÀI khung giờ ${t.name} đã khai. Hệ thống giữ nguyên giờ đã chốt; sửa giờ lớp hoặc khung giờ đã khai nếu cần.`
                            : `${t.name} — bấm để sửa / khai giờ có thể dạy`
                          : undefined
                      }
                      onClick={t ? onOpenTeacher(t.id) : undefined}
                    >
                      {(truong === "name" ? t?.name : t?.[truong]) || "—"}
                    </button>
                  ))}
                </td>
              ))}
              <td>{c.teachingHoursLt ?? "—"}</td>
              <td>{c.teachingHoursTh ?? "—"}</td>
              <td>{c.location || "—"}</td>
              <td>{c.teachingMode || "—"}</td>
              <td>{c.language || "—"}</td>
              <td>{c.otherRequirements || "—"}</td>
              <td>{c.notes || "—"}</td>
              <td><Pill tone={meta.tone}>{meta.label}</Pill></td>
              <td>
                {c.scheduleStatus
                  ? (() => {
                    const sm = SCHEDULE_STATUS_META[c.scheduleStatus] || { label: c.scheduleStatus, tone: "slate" };
                    return <Pill tone={sm.tone}>{sm.label}</Pill>;
                  })()
                  : "—"}
              </td>
            </tr>
          );
          })}
        </tbody>
      ))}
      {rows.length === 0 && (
        <tbody>
          <tr>
            <td colSpan={29} className="text-muted-foreground p-6 text-center">
              Chưa có lớp nào khớp bộ lọc.
            </td>
          </tr>
        </tbody>
      )}
    </table>
  </div>
  );
}
