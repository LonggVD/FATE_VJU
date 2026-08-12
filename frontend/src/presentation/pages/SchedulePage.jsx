import { useEffect, useMemo, useState } from "react";
import { LayoutGrid, Maximize2, Minimize2, Map as MapIcon, Rows3, Save, TriangleAlert, X } from "lucide-react";
import { useAppData } from "../../context/AppDataContext";
import { buildProblemInbox, filterProblemInbox } from "../../adapters/problemInbox";
import { buildScheduleView, scopeLabel, SCOPE, DEFAULT_FILTER } from "../../adapters/scheduleView";
import { analyzeSubmissions, teacherReportedHours } from "../../adapters/submissionQueue";
import ReportedHoursPanel from "../teacher/ReportedHoursPanel";
import { COLOR_BY_OPTIONS, STATUS_COLORS, buildLegend } from "../../adapters/colorGrouping";
import LessonGridBoard from "../timetable/LessonGridBoard";
import LessonTable from "../timetable/LessonTable";
import ProblemInbox from "../schedule/ProblemInbox";
import DensityNavigator from "../schedule/DensityNavigator";
import WorkflowStrip from "../schedule/WorkflowStrip";
import MoveReasonDialog from "../schedule/MoveReasonDialog";
import SaveMoveDialog from "../schedule/SaveMoveDialog";
import PendingMoveBanner from "../schedule/PendingMoveBanner";
import { slotRangeLabel } from "../../adapters/crossConflictAnalysis";
import SolverProgress from "../SolverProgress";
import { FilterSelect } from "@/components/shared/filter-select";
import { ListSearch } from "@/components/shared/list-search";
import { Notice } from "@/components/shared/notice";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { NativeSelect } from "@/components/ui/native-select";
import { cn } from "@/lib/utils";

// MAN TRUNG TAM sau refactor - gop Giai doan 1, Giai doan 2, Tra cuu theo giang
// vien va Check trung lien chuong trinh.
//
// Ca bon von la CUNG MOT luoi tuan voi bo loc khac nhau; cai khac nhau that su
// chi la pham vi du lieu va nut bam. Nay dung la nhu vay: mot luoi, mot thanh
// loc, mot hop thu van de, mot thanh tien trinh giu lai rang buoc GD2-sau-GD1.
export default function SchedulePage({ role, filter, onFilterChange }) {
  const {
    data, guestResult, residentResult, loading, error, solveGuest, solveResident,
    doMoveLesson, doClearOverride, doSaveSchedule, doHocChung,
  } = useAppData();
  const [activeProblem, setActiveProblem] = useState(null);
  // Buoi can cuon toi tren luoi - { id, seq }; xem pickProblem.
  const [scrollTarget, setScrollTarget] = useState(null);
  const [activeCell, setActiveCell] = useState(null);
  const [mode, setMode] = useState("grid");
  // Keo-tha xong CHUA goi API ngay - chi TAM GIU vao pendingMove (thi giac: the
  // hien o vi tri moi qua displayLessons ben duoi), cho toi khi bam "Luu" tren
  // banner roi xac nhan trong SaveMoveDialog thi moi thuc su goi doMoveLesson().
  // { sectionId, lesson, fromSlot, toSlot }
  const [pendingMove, setPendingMove] = useState(null);
  const [saveConfirmOpen, setSaveConfirmOpen] = useState(false);
  // Khi tha vao o dang trung GV/het phong, backend tra 409 kem chi tiet xung
  // dot - luu lai de mo hop thoai xin ly do (xem handleConfirmSave/handleConfirmReason).
  const [moveDialog, setMoveDialog] = useState(null);
  // Toan man hinh = che do "du chu": the co dinh 180px, luoi duoc phep rong hon
  // man hinh va cuon ca 2 chieu. Chi tiet ca hoc CHI hien o day - o che do thuong
  // the van la thanh mau, de cung mot man khong cho ra ngay nay co chu ngay kia
  // khong (be rong cot phu thuoc so lop chong gio cua tung ngay).
  const [fullscreen, setFullscreen] = useState(false);
  const [inboxOpen, setInboxOpen] = useState(false);
  const [navOpen, setNavOpen] = useState(false);
  const canEdit = role !== "viewer";

  useEffect(() => {
    if (!fullscreen) return;
    // Esc dong lop dang mo tren cung truoc, het lop moi thoat toan man hinh.
    const onKey = (e) => {
      if (e.key !== "Escape") return;
      // Dialog dang mo dong truoc (khong huy pendingMove - banner van con de
      // bam Luu lai), roi moi den cac lop ngan keo, cuoi cung la thoat toan man hinh.
      // Hai dialog gio la Radix Dialog nen chung TU xu ly Esc; nhanh o day chi
      // con de "nuot" phim, khong cho Esc rot xuong lam thoat toan man hinh oan.
      if (moveDialog) setMoveDialog(null);
      else if (saveConfirmOpen) setSaveConfirmOpen(false);
      else if (inboxOpen) setInboxOpen(false);
      else if (navOpen) setNavOpen(false);
      else setFullscreen(false);
    };
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [fullscreen, inboxOpen, navOpen, moveDialog, saveConfirmOpen]);

  const f = { ...DEFAULT_FILTER, ...(filter ?? {}) };
  const set = (patch) => onFilterChange({ ...f, ...patch });

  // pendingMove nam trong deps: vua tha xong la hop thu + mau tren luoi phai
  // tinh lai NGAY theo vi tri moi, khong doi bam Luu moi biet co dam vao ai khong.
  const inbox = useMemo(
    () => buildProblemInbox(data, guestResult, residentResult, pendingMove),
    [data, guestResult, residentResult, pendingMove],
  );
  const view = useMemo(
    () => buildScheduleView({ data, guestResult, residentResult, inbox, filter: f }),
    [data, guestResult, residentResult, inbox, filter],
  );
  // Hop thu hien tren man: DA LOC theo dung pham vi dang chon o luoi. `inbox`
  // day du van duoc buildScheduleView dung (to mau buoi co van de) - loc ban do
  // se lam buoi ngoai pham vi mat danh dau khi doi bo loc.
  const inboxHien = useMemo(
    () => filterProblemInbox(inbox, data, f),
    [inbox, data, f.scope, f.scopeValue],
  );

  const sq = useMemo(() => (data ? analyzeSubmissions(data) : null), [data]);
  const legend = useMemo(() => buildLegend(view.lessons, f.colorBy), [view.lessons, f.colorBy]);

  // Phu 1 lop hien thi len tren view.lessons: buoi dang pendingMove (chua luu)
  // hien o VI TRI MOI ngay lap tuc, du chua goi API - nguoi dung phai thay ro
  // "keo xong se ra sao" truoc khi bam Luu, khong the chi bam nut ma khong thay
  // gi doi tren luoi.
  const displayLessons = useMemo(() => {
    if (!pendingMove) return view.lessons;
    return view.lessons.map((l) =>
      l.id === pendingMove.sectionId
        ? { ...l, day: pendingMove.toDay, period: pendingMove.toPeriod, slot: pendingMove.toSlot, pendingSave: true }
        : l,
    );
  }, [view.lessons, pendingMove]);

  const fromLabel = pendingMove
    ? slotRangeLabel(pendingMove.fromSlot, pendingMove.lesson.duration || 1, view.slotsPerDay)
    : "";
  const toLabel = pendingMove
    ? slotRangeLabel(pendingMove.toSlot, pendingMove.lesson.duration || 1, view.slotsPerDay)
    : "";

  // Chi tinh khi dang loc ve dung 1 giang vien.
  const teacherId = f.scope === SCOPE.TEACHER && f.scopeValue ? f.scopeValue : null;
  const hours = useMemo(
    () => (data && teacherId ? teacherReportedHours(data, teacherId) : null),
    [data, teacherId],
  );
  const selectedTeacher = useMemo(
    () => (data && teacherId ? (data.teachers ?? []).find((t) => String(t.id) === String(teacherId)) : null),
    [data, teacherId],
  );

  if (!data) {
    return (
      <Notice tone="slate">
        Chưa có dữ liệu — sang "Chuẩn bị dữ liệu" để sinh hoặc nạp dữ liệu trước.
      </Notice>
    );
  }

  // Buoi duoc lam noi: uu tien vu dang chon trong hop thu, sau do la o gio dang
  // chon tren bang mat do.
  const highlighted = new Set(
    activeProblem
      ? activeProblem.sectionIds
      : activeCell
      ? view.idsAt[activeCell.day]?.[activeCell.period] ?? []
      : [],
  );

  const steps = [
    {
      key: "collect",
      label: "Thu giờ",
      value: sq ? `${sq.doneCount}/${sq.guestCount}` : "—",
      state: sq && sq.queue.length === 0 ? "done" : "todo",
    },
    // guestResult/residentResult co the la LICH BAN DAU doc tu file (initial),
    // chua phai ket qua giai - thanh tien trinh phai noi ro, khong thi nap file
    // xong buoc 2/3 hien "done" ma chua ai bam Giai.
    {
      key: "guest",
      label: "Xếp thỉnh giảng",
      value: !guestResult
        ? "chưa chạy"
        : guestResult.initial
          ? `${guestResult.placedCount} buổi chốt từ file`
          : `${guestResult.placedCount}/${guestResult.total}`,
      state: guestResult && !guestResult.initial ? "done" : "todo",
      action: solveGuest,
      actionLabel: guestResult && !guestResult.initial ? "Giải lại" : "Giải",
    },
    {
      key: "resident",
      label: "Ghép cơ hữu",
      value: !residentResult
        ? "chưa chạy"
        : residentResult.initial
          ? `${residentResult.placedCount} buổi chốt từ file`
          : `${residentResult.placedCount}/${residentResult.total}`,
      state: residentResult && !residentResult.initial ? "done" : "todo",
      action: solveResident,
      actionLabel: residentResult && !residentResult.initial ? "Giải lại" : "Giải",
      // Lich ban dau khong tinh la "da chay Giai doan 1" (backend cung chan).
      disabled: !guestResult || guestResult.initial,
    },
  ];

  const pickProblem = (item) => {
    setActiveProblem(item);
    setActiveCell(null);
    if (!item) return;
    // Vu dan duong cho khung nhin: mo rong pham vi de chac chan thay duoc buoi
    // lien quan, thay vi de nguoi dung tu doi bo loc. Phai go CA scope va hai o
    // tich loai GV - chi go onlyProblems/search nhu truoc thi buoi nam ngoai
    // chuong trinh dang loc van bi an, va cuon toi mot the khong ton tai.
    set({
      onlyProblems: false,
      search: "",
      scope: SCOPE.ALL,
      scopeValue: "",
      guest: true,
      resident: true,
    });

    // ...roi CUON THANG toi buoi do. To sang thoi la chua du: luoi rong hon man
    // hinh ca hai chieu (15 chuong trinh x 7 ngay x 12 tiet), the duoc to sang
    // hoan toan co the dang nam ngoai khung nhin va nguoi dung van phai tu tim.
    //
    // Chon buoi DAU TIEN cua vu ma thuc su co mat tren luoi: vu "trung giang
    // vien" co 2 buoi (mot bi bo lai, mot da xep) va buoi bi bo lai khong co o
    // nao de cuon toi.
    const tren = new Set(view.lessons.map((l) => l.id));
    const dich = (item.sectionIds || []).find((id) => tren.has(id));
    if (dich != null) setScrollTarget((truoc) => ({ id: dich, seq: (truoc?.seq ?? 0) + 1 }));
  };

  // ===== Luong keo-tha 3 buoc: tha (tam giu) -> bam Luu -> xac nhan -> goi API =====

  // 1. Tha 1 buoi vao 1 o - CHUA goi API, chi tam giu de banner + hien vi tri moi
  // ngay tren luoi (qua displayLessons). "Luu" o day CHi luu ban ghi TAM, khong
  // phai luu vao backend.
  const handleDropLesson = (sectionId, toSlot) => {
    const lesson = view.lessons.find((l) => l.id === sectionId);
    if (!lesson || lesson.slot === toSlot) return; // tha lai dung cho cu - bo qua
    setPendingMove({
      sectionId, lesson,
      fromSlot: lesson.slot,
      toSlot, toDay: Math.floor(toSlot / view.slotsPerDay), toPeriod: toSlot % view.slotsPerDay,
    });
  };

  // 2. Bam "Luu" tren banner -> mo hop thoai xac nhan (chua goi API).
  const openSaveConfirm = () => setSaveConfirmOpen(true);

  // 3. Xac nhan trong hop thoai -> THUC SU goi API lan dau, KHONG kem ly do.
  // Sach (khong xung dot) thi xong luon; 409 thi chuyen sang hop thoai xin ly do
  // (buoc 4), pendingMove van giu nguyen de con "Luu" lai duoc.
  const handleConfirmSave = async () => {
    setSaveConfirmOpen(false);
    try {
      await doMoveLesson(pendingMove.sectionId, pendingMove.toSlot);
      setPendingMove(null);
    } catch (err) {
      if (err.status === 409) {
        setMoveDialog({ sectionId: pendingMove.sectionId, slot: pendingMove.toSlot, conflict: err.body?.conflict });
      }
    }
  };

  // 4. Xac nhan trong hop thoai xin ly do (chi toi khi co xung dot) -> goi API
  // lan 2 kem ly do.
  const handleConfirmReason = async (reason) => {
    try {
      await doMoveLesson(moveDialog.sectionId, moveDialog.slot, reason);
      setMoveDialog(null);
      setPendingMove(null);
    } catch {
      // doMoveLesson da tu ghi Nhat ky + error state - dong hop thoai, banner
      // pendingMove giu nguyen de nguoi dung bam Luu thu lai.
      setMoveDialog(null);
    }
  };

  const cancelPendingMove = () => {
    setPendingMove(null);
    setSaveConfirmOpen(false);
    setMoveDialog(null);
  };

  const densityBlock = (
    <>
      <DensityNavigator
        view={view}
        activeCell={activeCell}
        onPickCell={(cell) => {
          setActiveCell(cell);
          setActiveProblem(null);
        }}
      />
      {hours && selectedTeacher && (
        <ReportedHoursPanel teacher={selectedTeacher} hours={hours} />
      )}
    </>
  );

  const inboxBlock = (
    <ProblemInbox
      inbox={inboxHien}
      activeId={activeProblem?.id ?? null}
      onPick={pickProblem}
      onClear={() => setActiveProblem(null)}
      // Tab "Chua xep duoc": bam 1 khung gio con trong la GHIM luon buoi vao do -
      // dung lai chinh doMoveLesson() ma keo-tha tren luoi dang dung, khong viet
      // duong rieng. Khong kem reason: cac khung goi y da duoc loc chi con o
      // KHONG bi trung GV/het phong (xem unplacedAnalysis.js), nen thuong di
      // thang, 409 (hiem, vd 2 giao vu bam gan nhau) se hien qua thong bao loi
      // ngay trong tab.
      onPlace={(sectionId, slot) => doMoveLesson(sectionId, slot)}
      // "Danh dau hoc chung": cach sua thu hai cho vu trung giang vien - xem
      // ProblemInbox va webapp/domain/hoc_chung.py.
      onHocChung={canEdit ? (sectionIds) => doHocChung(sectionIds) : undefined}
    />
  );

  return (
    <div
      className={cn(
        fullscreen
          // Nen phai DAC. Dung bg-muted/40 nhu nen canvas cua AppLayout thi lop
          // phu trong suot 40%, page header + bang canh bao ben duoi xuyen qua
          // va de chong len hang chu giai.
          ? "bg-background fixed inset-0 z-200 flex flex-col gap-2 overflow-hidden p-3"
          : "space-y-3",
      )}
    >
      {/* Toan man hinh la ban lam viec: bo thanh tien trinh de nhuong cho luoi. */}
      {!fullscreen && <WorkflowStrip steps={steps} canEdit={canEdit} loading={loading} />}

      {error && (
        <Notice tone="red" icon={TriangleAlert}>
          {error}
        </Notice>
      )}

      {/* ===== Thanh loc ===== */}
      <div className="bg-card flex flex-wrap items-center gap-2 rounded-xl border p-3 shadow-sm">
        <div className="flex items-center gap-2">
          <Label htmlFor="sv-scope" className="text-muted-foreground text-xs">
            Xem
          </Label>
          <NativeSelect
            id="sv-scope"
            value={f.scope}
            onChange={(e) => set({ scope: e.target.value, scopeValue: "" })}
          >
            <option value={SCOPE.ALL}>Toàn khoa</option>
            <option value={SCOPE.PROGRAM}>Theo chương trình</option>
            <option value={SCOPE.COHORT}>Theo khoá</option>
            <option value={SCOPE.TEACHER}>Theo giảng viên</option>
          </NativeSelect>
        </div>

        {/* Hai danh sach nay dai (19 chuong trinh, hang chuc GV) nen dung
            FilterSelect co o tim; scopeValue rong = khong loc, dung bang nghia
            "Tat ca" ma FilterSelect hien cho value===null. */}
        {f.scope === SCOPE.PROGRAM && (
          <FilterSelect
            label="Tất cả chương trình"
            searchable
            value={f.scopeValue || null}
            options={view.programs}
            onChange={(v) => set({ scopeValue: v ?? "" })}
          />
        )}

        {/* Khoa (cot "Khóa" cua bang du lieu hoc phan, vd VJU2026) - in TKB cho
            mot khoa la viec thuong lam, truoc day phai loc tay tung chuong trinh. */}
        {f.scope === SCOPE.COHORT && (
          <FilterSelect
            label="Tất cả khoá"
            searchable
            value={f.scopeValue || null}
            options={view.cohorts}
            onChange={(v) => set({ scopeValue: v ?? "" })}
          />
        )}

        {f.scope === SCOPE.TEACHER && (
          <FilterSelect
            label="Tất cả giảng viên"
            searchable
            value={f.scopeValue ? String(f.scopeValue) : null}
            options={view.teachers.map((t) => ({ value: String(t.id), label: t.name }))}
            onChange={(v) => set({ scopeValue: v ?? "" })}
          />
        )}

        <div className="flex items-center gap-3">
          <span className="text-muted-foreground text-xs">Lớp</span>
          <Label htmlFor="sv-guest" className="text-sm font-normal">
            <Checkbox
              id="sv-guest"
              checked={f.guest}
              onCheckedChange={(v) => set({ guest: v === true })}
            />
            Thỉnh giảng
          </Label>
          <Label htmlFor="sv-resident" className="text-sm font-normal">
            <Checkbox
              id="sv-resident"
              checked={f.resident}
              onCheckedChange={(v) => set({ resident: v === true })}
            />
            Cơ hữu
          </Label>
        </div>

        <ListSearch
          value={f.search}
          onChange={(v) => set({ search: v })}
          placeholder="Tìm môn, giảng viên, #id"
          className="w-full sm:w-64"
        />

        <Label htmlFor="sv-problems" className="text-sm font-normal">
          <Checkbox
            id="sv-problems"
            checked={f.onlyProblems}
            onCheckedChange={(v) => set({ onlyProblems: v === true })}
          />
          Chỉ buổi có vấn đề
        </Label>

        {mode === "grid" && (
          <NativeSelect
            value={f.colorBy}
            onChange={(e) => set({ colorBy: e.target.value })}
          >
            {COLOR_BY_OPTIONS.map((o) => (
              <option key={o.key} value={o.key}>Tô màu: {o.label}</option>
            ))}
          </NativeSelect>
        )}

        <div className="ml-auto flex items-center gap-2">
          {canEdit && (guestResult || residentResult) && (
            <Button
              size="sm"
              disabled={loading}
              onClick={() => {
                if (window.confirm(
                  "Ghi đè Thứ, Tiết bắt đầu/kết thúc và Trạng thái của TOÀN BỘ lớp đang xếp vào Dữ liệu học phần?",
                )) {
                  doSaveSchedule();
                }
              }}
              title="Cập nhật Thứ, Tiết bắt đầu/kết thúc và trạng thái vào Dữ liệu học phần"
            >
              <Save className="size-4" />
              Lưu thời khoá biểu
            </Button>
          )}
          {/* Bo chuyen che do dang segmented - cung ngon ngu voi TabsList. */}
          <div className="bg-muted inline-flex h-9 items-center rounded-lg p-0.75">
            {[
              { key: "grid", label: "Lưới", icon: LayoutGrid },
              { key: "table", label: "Bảng", icon: Rows3 },
            ].map((m) => (
              <button
                key={m.key}
                type="button"
                onClick={() => setMode(m.key)}
                aria-pressed={mode === m.key}
                className={cn(
                  "inline-flex h-full items-center gap-1.5 rounded-md px-2.5 text-sm font-medium transition-colors",
                  mode === m.key
                    ? "bg-background text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground",
                )}
              >
                <m.icon className="size-4" />
                {m.label}
              </button>
            ))}
          </div>

          {mode === "grid" && (
            <Button
              variant={fullscreen ? "default" : "outline"}
              size="sm"
              onClick={() => setFullscreen(!fullscreen)}
              title={
                canEdit
                  ? "Toàn màn hình — thẻ hiện đủ thông tin, kéo-thả được để sửa tay"
                  : "Toàn màn hình — thẻ hiện đủ mã lớp, môn, giảng viên, phòng"
              }
            >
              {fullscreen ? <Minimize2 className="size-4" /> : <Maximize2 className="size-4" />}
              {fullscreen ? "Thoát" : "Toàn màn hình"}
            </Button>
          )}
        </div>
      </div>

      <div className="text-muted-foreground flex flex-wrap items-baseline gap-x-3 gap-y-1 px-0.5 text-xs">
        <strong className="text-foreground text-[13px]">{scopeLabel(view, data)}</strong>
        <span>
          {view.lessons.length}/{view.totalLessons} buổi đang hiện
          {view.problemCount > 0 && ` · ${view.problemCount} buổi có vấn đề`}
        </span>
      </div>

      <PendingMoveBanner
        pending={pendingMove}
        fromLabel={fromLabel}
        toLabel={toLabel}
        onSave={openSaveConfirm}
        onCancel={cancelPendingMove}
      />

      {loading && <SolverProgress label="Đang giải" />}

      {view.totalLessons === 0 ? (
        <Notice tone="slate">
          Chưa có lịch nào — bấm "Giải" ở bước 2 trên thanh tiến trình.
        </Notice>
      ) : (
        <div
          className={cn(
            "grid items-start gap-3",
            fullscreen
              ? "min-h-0 flex-1 grid-cols-1"
              : "grid-cols-1 xl:grid-cols-[minmax(0,1fr)_330px]",
          )}
        >
          <div
            className={cn(
              "flex min-w-0 flex-col gap-2.5",
              fullscreen && "h-full min-h-0",
            )}
          >
            {mode === "grid" ? (
              <>
                {f.colorBy === "status" ? (
                  <div className="text-muted-foreground flex flex-wrap gap-x-3.5 gap-y-1 text-[11.5px]">
                    {Object.entries(STATUS_COLORS).map(([k, c]) => (
                      <span key={k} className="inline-flex items-center gap-1.5">
                        <span
                          className="size-2.5 rounded-sm"
                          style={{ background: c.border }}
                          aria-hidden="true"
                        />
                        {k}
                      </span>
                    ))}
                  </div>
                ) : (
                  // Ba lop mau con lai (Chuong trinh/Loai GV/Khoa) dung getColor()
                  // hash theo ten nhom - khong co chu giai thi mau vo nghia. Cap 8
                  // nhom, phan du gap vao "+n khac" (khong ve o).
                  legend?.length > 0 && (
                    <div className="text-muted-foreground flex flex-wrap gap-x-3.5 gap-y-1 text-[11.5px]">
                      {legend.map((it) => (
                        <span key={it.key} className="inline-flex items-center gap-1.5">
                          {it.color && (
                            <span
                              className="size-2.5 rounded-sm"
                              style={{ background: it.color.border }}
                              aria-hidden="true"
                            />
                          )}
                          {it.key}
                        </span>
                      ))}
                    </div>
                  )
                )}
                <LessonGridBoard
                  lessons={displayLessons}
                  numDays={view.numDays}
                  slotsPerDay={view.slotsPerDay}
                  highlightedIds={highlighted}
                  colorBy={f.colorBy}
                  onPickProblem={pickProblem}
                  scrollTarget={scrollTarget}
                  detailed={fullscreen}
                  // BUG DA SUA: truoc day gate them "&& !pendingMove" o day -
                  // nhung onMoveLesson=undefined lam dragEnabled (= detailed &&
                  // !!onMoveLesson, xem LessonGridBoard) sup xuong false, KEO
                  // THEO tat ca o body mat luon onDrop (ke ca o TRONG) va tat ca
                  // the mat luon draggable - khong chi chan "keo tiep" nhu du
                  // dinh, ma tat ca het toan bo he thong keo-tha ngay sau lan
                  // dau. Keo tiep gio se THAY THE pendingMove cu (chua luu gi nen
                  // khong mat du lieu) thay vi bi khoa.
                  onMoveLesson={canEdit ? handleDropLesson : undefined}
                  onClearOverride={canEdit ? doClearOverride : undefined}
                />
              </>
            ) : (
              <LessonTable lessons={displayLessons} />
            )}

            {/* Che do thuong: hai luoi 7x12 nam cung mot hang.
                Toan man hinh: KHONG hien o day - chung an mat mot dai ngang lon
                ma nua phai bo trong, trong khi cho do phai danh cho luoi. Chuyen
                thanh nut o goc duoi, can moi mo. */}
            {!fullscreen && (
              <div className="grid grid-cols-[repeat(auto-fit,minmax(430px,1fr))] items-start gap-2.5 *:min-w-0">
                {densityBlock}
              </div>
            )}
          </div>

          {/* Toan man hinh: hop thu thu ve mot nut co badge, bam moi bung ra dang
              ngan keo - luoi lay tron be ngang. */}
          {fullscreen ? (
            <>
              {/* Hai nut cung mot cum o goc phai duoi - luon hien, bam de bat/tat
                  lop tuong ung. */}
              <div className="fixed right-4 bottom-4 z-210 flex items-center gap-2">
                <Button
                  variant={navOpen ? "default" : "outline"}
                  className="rounded-full shadow-lg"
                  onClick={() => setNavOpen(!navOpen)}
                  aria-pressed={navOpen}
                >
                  <MapIcon className="size-4" />
                  Bản đồ tuần
                </Button>
                {inbox.total > 0 && (
                  <Button
                    variant="destructive"
                    className="rounded-full shadow-lg"
                    onClick={() => setInboxOpen(!inboxOpen)}
                    aria-pressed={inboxOpen}
                  >
                    <TriangleAlert className="size-4" />
                    Vấn đề
                    <span className="rounded-full bg-white/25 px-2 tabular-nums">
                      {inbox.total}
                    </span>
                  </Button>
                )}
              </div>

              {navOpen && (
                <div className="bg-background fixed right-4 bottom-17 z-215 flex max-h-[74vh] max-w-[min(760px,94vw)] flex-col gap-2 overflow-auto rounded-xl border p-2.5 shadow-2xl">
                  <DrawerClose onClick={() => setNavOpen(false)} />
                  {densityBlock}
                </div>
              )}
              {inboxOpen && (
                <div className="bg-background fixed inset-y-0 right-0 z-220 flex w-90 max-w-[92vw] flex-col gap-2 overflow-hidden border-l p-2.5 shadow-2xl">
                  <DrawerClose onClick={() => setInboxOpen(false)} />
                  <div className="min-h-0 flex-1 overflow-auto">{inboxBlock}</div>
                </div>
              )}
            </>
          ) : (
            inboxBlock
          )}
        </div>
      )}

      {/* pending chi truyen khi saveConfirmOpen=true - co pendingMove khong co
          nghia la hop thoai dang mo, chi la CO the doi da tam giu (banner). */}
      <SaveMoveDialog
        pending={saveConfirmOpen ? pendingMove : null}
        fromLabel={fromLabel}
        toLabel={toLabel}
        onCancel={() => setSaveConfirmOpen(false)}
        onConfirm={handleConfirmSave}
      />

      <MoveReasonDialog
        pending={moveDialog}
        onCancel={() => setMoveDialog(null)}
        onConfirm={handleConfirmReason}
      />
    </div>
  );
}

function DrawerClose({ onClick }) {
  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={onClick}
      className="text-muted-foreground self-end"
    >
      <X className="size-4" />
      Đóng
    </Button>
  );
}
