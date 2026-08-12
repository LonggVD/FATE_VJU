import { useMemo, useState } from "react";
import { Download, Eraser, Eye, GraduationCap, Plus, RotateCcw, TriangleAlert, Upload } from "lucide-react";
import { useAppData } from "../../context/AppDataContext";
import SectionEditDrawer from "../manual/SectionEditDrawer";
import TeacherEditDrawer from "../manual/TeacherEditDrawer";
import CourseEditDrawer from "../manual/CourseEditDrawer";
import ImportExcelDialog from "../manual/ImportExcelDialog";
import ExportExcelDialog from "../manual/ExportExcelDialog";
import { FilterSelect } from "@/components/shared/filter-select";
import { ListSearch } from "@/components/shared/list-search";
import { Notice } from "@/components/shared/notice";
import { Pill } from "@/components/shared/pill";
import { Button } from "@/components/ui/button";

const PAGE_STEP = 25;

// Tone thay cho cac class danger/warn/ok cu - dung chung bo 6 tone cua design
// system VJU. "Thieu gio" la thu chan xep lich -> do; "Tu dong xep" la chap nhan
// duoc nhung chua chot -> ho phach; "Da chot gio" -> xanh la.
const STATUS_META = {
  missing_time: { label: "Thiếu giờ", tone: "red" },
  ready_auto: { label: "Tự động xếp", tone: "amber" },
  ready_fixed: { label: "Đã chốt giờ", tone: "emerald" },
};

const STATUS_OPTIONS = Object.entries(STATUS_META).map(([value, m]) => ({
  value,
  label: m.label,
}));

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
      g = { courseId: c.courseId, courseCode: c.courseCode, courseName: c.courseName, credits: c.credits, rows: [] };
      byKey.set(key, g);
      groups.push(g);
    }
    g.rows.push(c);
  });
  return groups;
}

// Thay the "Nhap lieu thu cong" don gian cu (2 form roi rac, khong co khai niem
// "hoc phan" tach rieng): bang tong quan mirror 29 cot Excel + click 1 dong mo
// side-panel (SectionEditDrawer) de hoan thien du lieu. Day la NGUON DUY NHAT
// dua ca day sang "Thoi khoa bieu" thay cho tai Excel.
//
// BANG mirror giu nguyen CSS cu (.xls-*): day la ban sao co chu y cua file Excel
// goc, mat do rat day (29 cot, header 3 tang, rowSpan merge-xuong). Padding
// px-3 py-3 cua shadcn Table se lam no phinh gap may lan va mat cong dung. Chi
// phan khung (thanh loc, trang thai, nut) chuyen sang design system.
export default function ManualEntryPage({ role }) {
  const { data, loading, initManual, doClearManualTimes } = useAppData();
  const canEdit = role !== "viewer";

  // Da BO lenh refreshData() luc mount o day: AppDataProvider nay nap du lieu
  // ngay khi mo app cho MOI trang, khong rieng trang nay. Giu lai chi lam goi
  // /api/data hai lan o lan tai dau tien.

  const [search, setSearch] = useState("");
  const [programFilter, setProgramFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [limit, setLimit] = useState(PAGE_STEP);
  // { type: "section"|"teacher"|"course", id: number|"new" } | null (dong) - moi
  // domain co 1 form rieng (SectionEditDrawer/TeacherEditDrawer/CourseEditDrawer),
  // mo dung form theo O nguoi dung click trong bang, khong dong tat ca vao 1 form.
  const [drawer, setDrawer] = useState(null);
  const [importOpen, setImportOpen] = useState(false);
  const [exportOpen, setExportOpen] = useState(false);

  const isManualMode = data?.sourceLabel === "Nhập liệu thủ công";
  const classes = data?.classes || [];

  const programs = useMemo(
    () => [...new Set(classes.map((c) => c.programLabel).filter(Boolean))].sort(),
    [classes],
  );

  const visible = useMemo(() => {
    const q = search.trim().toLowerCase();
    return classes.filter((c) => {
      if (programFilter && c.programLabel !== programFilter) return false;
      if (statusFilter && c.status !== statusFilter) return false;
      if (!q) return true;
      return [c.courseName, c.classCode, c.teacherName, String(c.sectionId)]
        .some((v) => (v || "").toLowerCase().includes(q));
    });
  }, [classes, search, programFilter, statusFilter]);
  const shown = visible.slice(0, limit);
  const courseGroups = useMemo(() => groupByCourse(shown), [shown]);

  const handleStart = async () => {
    if (data && (data.numSections > 0 || data.numTeachers > 0)) {
      const ok = window.confirm(
        "Bắt đầu học kỳ mới sẽ XÓA HẾT dữ liệu hiện tại (kể cả dữ liệu đã nạp từ Excel). Tiếp tục?",
      );
      if (!ok) return;
    }
    await initManual();
    setDrawer(null);
  };

  // Xoa gio hang loat: CHINH XAC cac lop dang hien theo bo loc/tim kiem hien
  // tai (visible, chua cat trang limit) - WYSIWYG, khong phai toan bo du lieu.
  const handleClearTimes = async () => {
    if (visible.length === 0) return;
    const ok = window.confirm(
      `Xoá giờ (Thứ/Tiết đầu/Tiết cuối) của ${visible.length} lớp đang hiển thị? ` +
      `Các lớp này sẽ chuyển về "để hệ thống tự xếp". Không hoàn tác được.`,
    );
    if (!ok) return;
    await doClearManualTimes(visible.map((c) => c.sectionId));
  };

  const openSection = (id) => (e) => { e?.stopPropagation(); setDrawer({ type: "section", id }); };
  const openTeacher = (id) => (e) => { e?.stopPropagation(); setDrawer({ type: "teacher", id }); };
  const openCourse = (id) => (e) => { e?.stopPropagation(); setDrawer({ type: "course", id }); };

  const selectedSection = drawer?.type === "section" && drawer.id !== "new"
    ? classes.find((c) => c.sectionId === drawer.id) || null
    : null;
  const selectedTeacher = drawer?.type === "teacher" && drawer.id !== "new"
    ? (data?.teachers || []).find((t) => t.id === drawer.id) || null
    : null;
  const selectedCourse = drawer?.type === "course" && drawer.id !== "new"
    ? (data?.courses || []).find((c) => c.id === drawer.id) || null
    : null;

  return (
    // KHONG boc trong the: bang mirror 29 cot da rong hon man hinh san, ngoi
    // trong the co padding + vien chi lam no cuon ngang som hon can thiet.
    // AppLayout duoc goi voi bleed=true cho trang nay (xem BLEED_PAGES trong
    // App.jsx) nen vung noi dung khong con padding - thanh cong cu va bang tu lo
    // le trai/phai cua rieng chung.
    <div className="bg-background">
      {(!canEdit || (canEdit && !isManualMode)) && (
        <div className="px-4 pt-3 md:px-6">
          {!canEdit && (
            <Notice tone="slate" icon={Eye}>
              Vai trò "Xem thôi" — không thể sửa.
            </Notice>
          )}
          {canEdit && !isManualMode && (
            <Notice tone="amber" icon={TriangleAlert}>
              Chưa ở chế độ nhập liệu — bấm "Bắt đầu học kỳ mới".
            </Notice>
          )}
        </div>
      )}

      <div>
        {/* Dinh lai ngay duoi page header khi cuon - bang co toi 62 lop, cuon
            xuong ma mat o tim/bo loc/nut thi phai cuon nguoc len moi lam tiep
            duoc. Offset lay tu bien --page-header-h do AppLayout DO duoc, khong
            hard-code (chieu cao header doi theo breakpoint va theo co crumbs
            hay khong). z-10 de nam DUOI page header (z-20), khong de len no. */}
        <div className="bg-background sticky top-(--page-header-h) z-10 border-b">
        <div className="flex flex-wrap items-center gap-2 px-4 py-3 md:px-6">
          <h2 className="mr-1 text-sm font-semibold">
            Lớp đã nhập ({visible.length}
            {visible.length !== classes.length && `/${classes.length}`})
          </h2>

          <ListSearch
            value={search}
            onChange={setSearch}
            placeholder="Tìm mã lớp, học phần, GV, #id"
            className="w-full sm:w-64"
          />
          <FilterSelect
            label="Mọi chương trình"
            searchable
            value={programFilter || null}
            options={programs}
            onChange={(v) => setProgramFilter(v ?? "")}
          />
          <FilterSelect
            label="Mọi trạng thái"
            value={statusFilter || null}
            options={STATUS_OPTIONS}
            onChange={(v) => setStatusFilter(v ?? "")}
          />

          <div className="ml-auto flex flex-wrap items-center gap-2">
            {canEdit && isManualMode && (
              <>
                <Button variant="outline" size="sm" onClick={() => setDrawer({ type: "teacher", id: "new" })}>
                  <GraduationCap className="size-4" />
                  Giảng viên
                </Button>
                <Button variant="outline" size="sm" onClick={() => setDrawer({ type: "course", id: "new" })}>
                  <Plus className="size-4" />
                  Học phần
                </Button>
                <Button size="sm" onClick={() => setDrawer({ type: "section", id: "new" })}>
                  <Plus className="size-4" />
                  Thêm lớp
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={loading || visible.length === 0}
                  onClick={handleClearTimes}
                  title={`Đặt lại Thứ/Tiết đầu/Tiết cuối của ${visible.length} lớp đang hiển thị thành "để hệ thống tự xếp"`}
                >
                  <Eraser className="size-4" />
                  Xoá giờ ({visible.length})
                </Button>
              </>
            )}
            {canEdit && (
              <Button
                variant="outline"
                size="sm"
                disabled={loading}
                onClick={() => setImportOpen(true)}
                title="Nạp file kế hoạch giảng dạy (.xlsx) của kỳ cũ vào form"
              >
                <Upload className="size-4" />
                Nhập từ Excel
              </Button>
            )}
            {classes.length > 0 && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setExportOpen(true)}
                title="Xuất Dữ liệu học phần ra file .xlsx theo khuôn FATE"
              >
                <Download className="size-4" />
                Xuất file
              </Button>
            )}
            {canEdit && (
              <Button
                variant="outline"
                size="sm"
                className="text-destructive"
                disabled={loading}
                onClick={handleStart}
                title="Xóa hết dữ liệu hiện tại và bắt đầu lại"
              >
                <RotateCcw className="size-4" />
                {loading ? "Đang xử lý…" : "Bắt đầu học kỳ mới"}
              </Button>
            )}
          </div>
        </div>

        {/* Chu giai cho ba vung nen trong bang: bam vao vung nao mo form nao.
            O mau lay DUNG mau nen cua vung (bien --xls-z-*), khong go tay lai -
            de doi mau vung thi chu giai tu theo. Nam TRONG khoi sticky de cuon
            sau van con doc duoc. */}
        <div className="text-muted-foreground flex flex-wrap items-center gap-x-4 gap-y-1 border-t px-4 py-1.5 text-[11px] md:px-6">
          <span className="font-medium">Bấm vào ô để mở form:</span>
          <span className="inline-flex items-center gap-1.5">
            <span className="xls-swatch xls-z-course" aria-hidden="true" />
            4 cột đầu → <strong className="text-foreground font-medium">Học phần</strong>
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span className="xls-swatch xls-z-teacher" aria-hidden="true" />
            nhóm “Kỳ này” → <strong className="text-foreground font-medium">Giảng viên</strong>
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span className="xls-swatch" aria-hidden="true" />
            các cột còn lại → <strong className="text-foreground font-medium">Lớp học phần</strong>
          </span>
        </div>
        </div>

        <div className="xls-scroll">
          <table className="data-table xls-table">
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
                <th rowSpan={3} className="xls-z-course">TT</th>
                <th rowSpan={3} className="xls-z-course">Mã học phần</th>
                <th rowSpan={3} className="xls-z-course">Tên học phần</th>
                <th rowSpan={3} className="xls-z-course">Số tín chỉ</th>
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
                  <tr key={c.sectionId} className="sed-row xls-row" onClick={openSection(c.sectionId)}>
                    {i === 0 && <td className="xls-course xls-z-course" rowSpan={g.rows.length} onClick={openCourse(g.courseId)}>{c.sectionId}</td>}
                    {i === 0 && <td className="xls-course xls-z-course" rowSpan={g.rows.length} onClick={openCourse(g.courseId)}>{g.courseCode || "—"}</td>}
                    {i === 0 && <td className="xls-course xls-z-course" rowSpan={g.rows.length} onClick={openCourse(g.courseId)}>{g.courseName || "—"}</td>}
                    {i === 0 && <td className="xls-course xls-z-course" rowSpan={g.rows.length} onClick={openCourse(g.courseId)}>{g.credits ?? "—"}</td>}
                    <td>{c.classCode || "—"}</td>
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
                            onClick={t ? openTeacher(t.id) : undefined}
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
            {shown.length === 0 && (
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

        {visible.length > shown.length && (
          <div className="flex justify-center border-t p-3">
            <Button variant="outline" size="sm" onClick={() => setLimit((l) => l + PAGE_STEP)}>
              Hiện thêm {Math.min(PAGE_STEP, visible.length - shown.length)} lớp (còn{" "}
              {visible.length - shown.length})
            </Button>
          </div>
        )}
      </div>

      {drawer?.type === "section" && (
        <SectionEditDrawer
          data={data}
          section={selectedSection}
          onClose={() => setDrawer(null)}
          onDuplicated={(newId) => setDrawer({ type: "section", id: newId })}
          // Bam "Giờ dạy" canh mot giang vien trong lop -> chuyen sang ngan cua
          // chinh nguoi do (co muc khai gio co the day).
          onOpenTeacher={(id) => setDrawer({ type: "teacher", id })}
        />
      )}
      {drawer?.type === "teacher" && (
        <TeacherEditDrawer
          data={data}
          teacher={selectedTeacher}
          onClose={() => setDrawer(null)}
        />
      )}
      {drawer?.type === "course" && (
        <CourseEditDrawer
          course={selectedCourse}
          onClose={() => setDrawer(null)}
        />
      )}

      <ImportExcelDialog open={importOpen} onOpenChange={setImportOpen} />
      <ExportExcelDialog open={exportOpen} onOpenChange={setExportOpen} />
    </div>
  );
}
