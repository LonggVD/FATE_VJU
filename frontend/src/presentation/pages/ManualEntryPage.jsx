import { useMemo, useState } from "react";
import { Download, Eraser, Eye, GraduationCap, Lock, Plus, RotateCcw, TriangleAlert, Upload } from "lucide-react";
import { useAppData } from "../../context/AppDataContext";
import SectionEditDrawer from "../manual/SectionEditDrawer";
import TeacherEditDrawer from "../manual/TeacherEditDrawer";
import CourseEditDrawer from "../manual/CourseEditDrawer";
import ImportExcelDialog from "../manual/ImportExcelDialog";
import ExportExcelDialog from "../manual/ExportExcelDialog";
import ChotCourseDialog from "../manual/ChotCourseDialog";
import { FilterSelect } from "@/components/shared/filter-select";
import { ListSearch } from "@/components/shared/list-search";
import { Notice } from "@/components/shared/notice";
import { Button } from "@/components/ui/button";
import SectionTable, { STATUS_META } from "../manual/SectionTable";

const PAGE_STEP = 25;

// STATUS_META dung chung voi bang - xem manual/SectionTable.jsx.
const STATUS_OPTIONS = Object.entries(STATUS_META).map(([value, m]) => ({
  value,
  label: m.label,
}));

// Loc theo TRANG THAI CHOT cua hoc phan - khac han "Trang thai" o tren (von noi
// ve gio cua tung lop). Giao vu chot dan tung mon nen phai tra loi duoc ngay
// "con nhung mon nao chua chot".
const CHOT_OPTIONS = [
  { value: "chua", label: "Chưa chốt lịch" },
  { value: "roi", label: "Đã chốt lịch" },
];

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
  const { data, loading, initManual, doClearManualTimes, doBoChotCourse,
          doBoHocChung } = useAppData();
  const canEdit = role !== "viewer";

  // Da BO lenh refreshData() luc mount o day: AppDataProvider nay nap du lieu
  // ngay khi mo app cho MOI trang, khong rieng trang nay. Giu lai chi lam goi
  // /api/data hai lan o lan tai dau tien.

  const [search, setSearch] = useState("");
  const [programFilter, setProgramFilter] = useState("");
  const [cohortFilter, setCohortFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [chotFilter, setChotFilter] = useState("");
  // Nhom hoc phan dang mo hop thoai chot (null = dong).
  const [chotGroup, setChotGroup] = useState(null);
  const [limit, setLimit] = useState(PAGE_STEP);
  // { type: "section"|"teacher"|"course", id: number|"new" } | null (dong) - moi
  // domain co 1 form rieng (SectionEditDrawer/TeacherEditDrawer/CourseEditDrawer),
  // mo dung form theo O nguoi dung click trong bang, khong dong tat ca vao 1 form.
  const [drawer, setDrawer] = useState(null);
  const [importOpen, setImportOpen] = useState(false);
  const [exportOpen, setExportOpen] = useState(false);

  const isManualMode = data?.sourceLabel === "Nhập liệu thủ công";
  const classes = data?.classes || [];

  // O GHEP ("BCSE+MJM", "VJU2023+VJU2024") = lop cua CA HAI -> danh sach chon la
  // cac ma DON (backend tach san o programParts/cohortParts). Nho vay chon "BCSE"
  // ra ca lop "BCSE+MJM", va het canh "VJU2023+VJU2024" voi "VJU2024+VJU2023"
  // nam thanh hai muc gan giong nhau trong danh sach.
  const programs = useMemo(
    () => [...new Set(classes.flatMap((c) => c.programParts ?? []))].sort(),
    [classes],
  );

  // Khoa (cot "Khóa", vd VJU2026) - lay tu chinh du lieu dang co, khong chot cung
  // danh sach: moi ky file lai co khoa moi. Sap giam dan de khoa moi nhat len dau.
  const cohorts = useMemo(
    () => [...new Set(classes.flatMap((c) => c.cohortParts ?? []))].sort().reverse(),
    [classes],
  );

  const visible = useMemo(() => {
    const q = search.trim().toLowerCase();
    return classes.filter((c) => {
      if (programFilter && !(c.programParts ?? []).includes(programFilter)) return false;
      if (cohortFilter && !(c.cohortParts ?? []).includes(cohortFilter)) return false;
      if (statusFilter && c.status !== statusFilter) return false;
      if (chotFilter === "roi" && !c.courseChot) return false;
      if (chotFilter === "chua" && c.courseChot) return false;
      if (!q) return true;
      return [c.courseName, c.classCode, c.teacherName, String(c.sectionId)]
        .some((v) => (v || "").toLowerCase().includes(q));
    });
  }, [classes, search, programFilter, cohortFilter, statusFilter, chotFilter]);
  const shown = visible.slice(0, limit);

  // Tooltip nhom hoc chung phai goi lop bang MA LOP, khong phai id noi bo (#317)
  // - dung quy uoc chung cua du an (xem adapters/problemInbox.js).
  const maLopTheoId = useMemo(
    () => new Map(classes.map((c) => [c.sectionId, c.classCode])),
    [classes],
  );
  const tenLop = (sid) => maLopTheoId.get(sid) || `#${sid}`;

  const tienDoChot = useMemo(() => {
    const m = new Map();
    for (const c of classes) {
      if (c.courseId == null) continue;
      if (!m.has(c.courseId)) m.set(c.courseId, Boolean(c.courseChot));
    }
    const tong = m.size;
    const roi = [...m.values()].filter(Boolean).length;
    return { tong, roi, con: tong - roi };
  }, [classes]);

  const handleBoChot = (g) => async (e) => {
    e.stopPropagation();
    const ok = window.confirm(
      `Bỏ chốt học phần "${g.courseName}"?

` +
      `Giờ của ${g.rows.length} lớp sẽ trả về đúng trạng thái TRƯỚC khi chốt ` +
      `(lớp vốn chưa có giờ quay lại "để hệ thống tự xếp"), và hệ thống được xếp lại môn này.`,
    );
    if (!ok) return;
    await doBoChotCourse(g.courseId);
  };

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
    //
    // CHIEM TRON chieu cao con lai (AppLayout duoc goi voi fullHeight=true cho
    // trang nay): canh bao va thanh cong cu la flex item co dinh, BANG lay het
    // phan con lai va tu cuon - co the bang moi "dong bang" duoc hang tieu de va
    // 5 cot dau (xem .xls-scroll trong styles.css).
    <div className="bg-background flex min-h-0 flex-1 flex-col">
      {(!canEdit || (canEdit && !isManualMode)) && (
        <div className="shrink-0 px-4 pt-3 md:px-6">
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

      <div className="flex min-h-0 flex-1 flex-col">
        {/* Thanh cong cu LUON hien: bang co toi vai tram lop, cuon xuong ma mat
            o tim/bo loc/nut thi phai cuon nguoc len moi lam tiep duoc.

            Truoc day dat `sticky top-(--page-header-h)` vi ca trang cuon chung.
            Nay trang la mot cot flex chiem tron chieu cao, cuon doc do CHINH
            bang lo (xem fullHeight trong AppLayout) - thanh nay chi can la flex
            item khong co lai (`shrink-0`) la da dung yen, khong can sticky nua. */}
        <div className="bg-background shrink-0 border-b">
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
            label="Mọi khoá"
            searchable
            value={cohortFilter || null}
            options={cohorts}
            onChange={(v) => setCohortFilter(v ?? "")}
          />
          <FilterSelect
            label="Mọi trạng thái"
            value={statusFilter || null}
            options={STATUS_OPTIONS}
            onChange={(v) => setStatusFilter(v ?? "")}
          />
          <FilterSelect
            label="Mọi tình trạng chốt lịch"
            value={chotFilter || null}
            options={CHOT_OPTIONS}
            onChange={(v) => setChotFilter(v ?? "")}
          />
          {/* Tien do tinh tren CA KY, khong theo bo loc dang hien: cau hoi that
              su la "con bao nhieu mon chua chot", khong phai "trong man nay". */}
          {tienDoChot.tong > 0 && (
            <button
              type="button"
              className="inline-flex items-center gap-1.5 rounded-md border px-2 py-1 text-xs"
              title={`${tienDoChot.roi} học phần đã chốt lịch, còn ${tienDoChot.con} chưa chốt. Bấm để lọc.`}
              onClick={() => setChotFilter(chotFilter === "chua" ? "" : "chua")}
            >
              <Lock className="size-3.5" />
              Chốt lịch{" "}
              <strong className="tabular-nums">
                {tienDoChot.roi}/{tienDoChot.tong}
              </strong>{" "}
              môn
              {tienDoChot.con > 0 && (
                <span className="text-amber-700">· còn {tienDoChot.con}</span>
              )}
            </button>
          )}

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

        <SectionTable
          rows={shown}
          canEdit={canEdit}
          loading={loading}
          tenLop={tenLop}
          onOpenSection={openSection}
          onOpenCourse={openCourse}
          onOpenTeacher={openTeacher}
          onChot={setChotGroup}
          onBoChot={handleBoChot}
          onBoHocChung={doBoHocChung}
        />

        {visible.length > shown.length && (
          <div className="flex shrink-0 justify-center border-t p-3">
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
      {chotGroup && (
        <ChotCourseDialog
          open
          group={chotGroup}
          onOpenChange={(o) => !o && setChotGroup(null)}
        />
      )}
    </div>
  );
}
