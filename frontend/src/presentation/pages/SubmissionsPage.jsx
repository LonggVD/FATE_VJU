import { useMemo, useState } from "react";
import { CircleCheck, X } from "lucide-react";
import { useAppData } from "../../context/AppDataContext";
import SubmissionWindowGrid from "../submissions/SubmissionWindowGrid";
import { analyzeSubmissions, filterRows, SUB_STATE, SUB_STATE_META } from "../../adapters/submissionQueue";
import { slotRangeLabel } from "../../adapters/crossConflictAnalysis";
import { FilterSelect } from "@/components/shared/filter-select";
import { ListSearch } from "@/components/shared/list-search";
import { Notice } from "@/components/shared/notice";
import { Pill } from "@/components/shared/pill";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";

const PAGE_STEP = 25;
const QUEUE_STEP = 15;
const MAX_WINDOW_CHIPS = 4;

const STATE_OPTIONS = [
  { value: SUB_STATE.SET, label: SUB_STATE_META.SET.label },
  { value: SUB_STATE.UNREPORTED, label: SUB_STATE_META.UNREPORTED.label },
];

// Man hinh cua DIEU PHOI VIEN. Ba viec khac nhau -> BA MAN CON, khong don tat ca
// vao mot trang dai: ban truoc do cao ~4300px va co hai vung cuon long nhau (hang
// doi tu cuon trong khung 520px, ben duoi lai do tiep 60 dong bang).
const VIEW = { QUEUE: "queue", TABLE: "table", COORDS: "coords" };

/** Khung the dung chung cho ba man con. */
function Card({ title, note, children, headExtra }) {
  return (
    <section className="bg-card rounded-xl border shadow-sm">
      <div className="flex flex-wrap items-center gap-2 border-b p-3">
        <h3 className="mr-1 text-sm font-semibold">{title}</h3>
        {note && <span className="text-muted-foreground text-xs">{note}</span>}
        {headExtra}
      </div>
      {children}
    </section>
  );
}

export default function SubmissionsPage({ role }) {
  const { data, loading, doSubmitAvailability } = useAppData();
  const [view, setView] = useState(null);
  const [openSectionId, setOpenSectionId] = useState(null);
  const [search, setSearch] = useState("");
  const [program, setProgram] = useState("");
  const [stateFilter, setStateFilter] = useState("");
  const [limit, setLimit] = useState(PAGE_STEP);
  const [queueLimit, setQueueLimit] = useState(QUEUE_STEP);
  const [coordFilter, setCoordFilter] = useState(null);
  const canEdit = role !== "viewer";

  const sq = useMemo(() => (data ? analyzeSubmissions(data) : null), [data]);

  if (!data || !sq) {
    return (
      <Notice tone="slate">
        Chưa có dữ liệu — sang "Dữ liệu học phần" để nhập hoặc nạp dữ liệu trước.
      </Notice>
    );
  }

  // Mo thang vao viec neu con gio phai thu.
  const activeView = view ?? (sq.queue.length > 0 ? VIEW.QUEUE : VIEW.TABLE);
  const pct = sq.guestCount ? Math.round((sq.doneCount / sq.guestCount) * 100) : 0;

  const handleSave = async (sectionId, slots) => {
    await doSubmitAvailability(Number(sectionId), slots);
    setOpenSectionId(null);
  };

  const tabs = [
    { key: VIEW.QUEUE, label: "Cần thu giờ", count: sq.queue.length, urgent: sq.queue.length > 0 },
    { key: VIEW.TABLE, label: "Bảng tra cứu", count: sq.guestCount },
    { key: VIEW.COORDS, label: "Theo điều phối viên", count: sq.coordinatorsBehind.length },
  ];

  return (
    <div className="space-y-3">
      {/* Tien do thu gio - so lieu quan trong nhat cua man nay, de len dau. */}
      <div className="bg-card flex flex-wrap items-center justify-between gap-4 rounded-xl border p-4 shadow-sm">
        <p className="text-muted-foreground max-w-prose text-xs">
          Điều phối viên nhập khung giờ GV thỉnh giảng có thể dạy. Buổi của GV cơ hữu không
          thuộc bước này.
        </p>
        <div className="min-w-56">
          <p className="text-2xl font-semibold tracking-tight tabular-nums">
            {sq.doneCount}
            <span className="text-muted-foreground text-base font-normal">
              /{sq.guestCount}
            </span>
            <span className="text-muted-foreground ml-2 text-xs font-normal">
              buổi đã có giờ
            </span>
          </p>
          <div className="bg-muted mt-1.5 h-1.5 overflow-hidden rounded-full">
            <div className="bg-primary h-full rounded-full" style={{ width: `${pct}%` }} />
          </div>
        </div>
      </div>

      <div className="bg-muted inline-flex h-9 items-center rounded-lg p-0.75" role="tablist">
        {tabs.map((t) => (
          <button
            type="button"
            key={t.key}
            role="tab"
            aria-selected={activeView === t.key}
            onClick={() => setView(t.key)}
            className={cn(
              "inline-flex h-full items-center gap-1.5 rounded-md px-2.5 text-sm font-medium transition-colors",
              activeView === t.key
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            {t.label}
            <span
              className={cn(
                "rounded px-1.5 text-xs tabular-nums",
                t.urgent ? "bg-red-500/15 text-red-700" : "bg-muted-foreground/15",
              )}
            >
              {t.count}
            </span>
          </button>
        ))}
      </div>

      {activeView === VIEW.QUEUE && (
        <QueueView
          sq={sq}
          canEdit={canEdit}
          loading={loading}
          openSectionId={openSectionId}
          setOpenSectionId={setOpenSectionId}
          onSave={handleSave}
          onGoTable={() => setView(VIEW.TABLE)}
          coordFilter={coordFilter}
          onClearCoord={() => { setCoordFilter(null); setQueueLimit(QUEUE_STEP); }}
          limit={queueLimit}
          onMore={() => setQueueLimit(queueLimit + QUEUE_STEP)}
        />
      )}

      {activeView === VIEW.TABLE && (
        <TableView
          sq={sq}
          search={search}
          program={program}
          stateFilter={stateFilter}
          limit={limit}
          onSearch={(v) => { setSearch(v); setLimit(PAGE_STEP); }}
          onProgram={(v) => { setProgram(v); setLimit(PAGE_STEP); }}
          onStateFilter={(v) => { setStateFilter(v); setLimit(PAGE_STEP); }}
          onMore={() => setLimit(limit + PAGE_STEP)}
        />
      )}

      {activeView === VIEW.COORDS && (
        <CoordsView
          sq={sq}
          onPickCoord={(name) => {
            setCoordFilter(name);
            setQueueLimit(QUEUE_STEP);
            setView(VIEW.QUEUE);
          }}
        />
      )}
    </div>
  );
}

function QueueView({
  sq, canEdit, loading, openSectionId, setOpenSectionId, onSave, onGoTable,
  coordFilter, onClearCoord, limit, onMore,
}) {
  if (sq.queue.length === 0) {
    return (
      <Notice
        tone="emerald"
        icon={CircleCheck}
        action={
          <Button variant="outline" size="sm" onClick={onGoTable}>
            Xem bảng tra cứu
          </Button>
        }
      >
        Cả {sq.guestCount} buổi thỉnh giảng đều đã có khung giờ cụ thể — không còn giờ nào
        phải thu.
      </Notice>
    );
  }

  const queue = coordFilter ? sq.queue.filter((r) => r.coordinator === coordFilter) : sq.queue;
  const shown = queue.slice(0, limit);

  return (
    <Card
      title={`Cần thu giờ (${queue.length}${coordFilter ? ` / ${sq.queue.length}` : ""})`}
      note={
        canEdit
          ? 'Bấm "Nhập giờ" để chọn khung giờ ngay tại dòng.'
          : 'Vai trò "Xem thôi" không nộp giờ được.'
      }
      headExtra={
        coordFilter && (
          <span className="text-muted-foreground ml-auto inline-flex items-center gap-1.5 text-xs">
            Đang lọc theo <strong className="text-foreground">{coordFilter}</strong>
            <Button variant="ghost" size="sm" onClick={onClearCoord}>
              <X className="size-3.5" />
              bỏ lọc
            </Button>
          </span>
        )
      }
    >
      <ul className="divide-y">
        {shown.map((r) => {
          const isOpen = openSectionId === r.sectionId;
          return (
            <li key={r.sectionId} className={cn(isOpen && "bg-muted/40")}>
              <div className="flex flex-wrap items-start justify-between gap-3 p-3">
                <div className="min-w-0 space-y-0.5">
                  <p className="flex flex-wrap items-baseline gap-x-2 text-sm">
                    <span className="text-muted-foreground tabular-nums">#{r.sectionId}</span>
                    <strong>{r.teacherName}</strong>
                    <span>{r.courseName}</span>
                  </p>
                  <p className="text-muted-foreground text-xs">
                    {r.programLabel} · {r.coordinator} · {r.roomType} · {r.duration} tiết
                    <span className="ml-2 text-amber-700">{r.reason}</span>
                  </p>
                </div>
                {canEdit && (
                  <Button
                    size="sm"
                    variant={isOpen ? "outline" : "default"}
                    onClick={() => setOpenSectionId(isOpen ? null : r.sectionId)}
                  >
                    {isOpen ? "Đóng" : "Nhập giờ"}
                  </Button>
                )}
              </div>

              {isOpen && canEdit && (
                <div className="border-t px-3 py-3">
                  <SubmissionWindowGrid
                    // Man nay chi lam viec voi lop THINH GIANG - gioi han toi Thu 7
                    // (index 5), dung quy tac sc.MAX_DAY_INDEX["GUEST"] o backend.
                    numDays={Math.min(sq.numDays, 6)}
                    slotsPerDay={sq.slotsPerDay}
                    initialSlots={r.isFreeChoice ? [] : r.windowSlots}
                    saving={loading}
                    onSave={(slots) => onSave(r.sectionId, slots)}
                    onCancel={() => setOpenSectionId(null)}
                  />
                </div>
              )}
            </li>
          );
        })}
      </ul>

      {queue.length > shown.length && (
        <div className="flex justify-center border-t p-3">
          <Button variant="outline" size="sm" onClick={onMore}>
            Hiện thêm {Math.min(QUEUE_STEP, queue.length - shown.length)} buổi (còn{" "}
            {queue.length - shown.length})
          </Button>
        </div>
      )}
    </Card>
  );
}

function TableView({ sq, search, program, stateFilter, limit, onSearch, onProgram, onStateFilter, onMore }) {
  const visible = filterRows(sq.rows, { search, program, state: stateFilter });
  const shown = visible.slice(0, limit);

  const renderWindowCell = (r) => {
    if (r.state === SUB_STATE.UNREPORTED) {
      return (
        <Pill tone="slate">
          {r.isEmpty ? "Chưa nộp" : `Tự do cả tuần · ${r.windowSlots.length}`}
        </Pill>
      );
    }
    const labels = r.windowSlots.map((w) => slotRangeLabel(w, r.duration, sq.slotsPerDay));
    return (
      <span className="flex flex-wrap items-center gap-1">
        {labels.slice(0, MAX_WINDOW_CHIPS).map((l, i) => (
          <Pill key={i} tone="emerald">{l}</Pill>
        ))}
        {labels.length > MAX_WINDOW_CHIPS && (
          <Pill tone="slate">+{labels.length - MAX_WINDOW_CHIPS}</Pill>
        )}
      </span>
    );
  };

  return (
    <Card
      title={`Buổi thỉnh giảng (${visible.length}${
        visible.length !== sq.guestCount ? `/${sq.guestCount}` : ""
      })`}
      headExtra={
        <div className="ml-auto flex flex-wrap items-center gap-2">
          <ListSearch
            value={search}
            onChange={onSearch}
            placeholder="Tìm tên GV, môn, điều phối viên, #id"
            className="w-full sm:w-72"
          />
          <FilterSelect
            label="Mọi chương trình"
            searchable
            value={program || null}
            options={sq.programs}
            onChange={(v) => onProgram(v ?? "")}
          />
          <FilterSelect
            label="Mọi trạng thái"
            value={stateFilter || null}
            options={STATE_OPTIONS}
            onChange={(v) => onStateFilter(v ?? "")}
          />
        </div>
      }
    >
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>#</TableHead>
            <TableHead>Trạng thái</TableHead>
            <TableHead>Giảng viên</TableHead>
            <TableHead>Môn học</TableHead>
            <TableHead>Chương trình</TableHead>
            <TableHead>Điều phối viên</TableHead>
            <TableHead>Khung giờ</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {shown.map((r) => {
            const meta = SUB_STATE_META[r.state];
            return (
              <TableRow key={r.sectionId}>
                <TableCell className="text-muted-foreground tabular-nums">
                  {r.sectionId}
                </TableCell>
                <TableCell>
                  <Pill tone={meta.tone}>{meta.label}</Pill>
                </TableCell>
                <TableCell>{r.teacherName}</TableCell>
                <TableCell className="whitespace-normal">{r.courseName}</TableCell>
                <TableCell>{r.programLabel}</TableCell>
                <TableCell className="text-muted-foreground">{r.coordinator}</TableCell>
                <TableCell className="whitespace-normal">{renderWindowCell(r)}</TableCell>
              </TableRow>
            );
          })}
          {shown.length === 0 && (
            <TableRow className="hover:bg-transparent">
              <TableCell colSpan={7} className="text-muted-foreground py-6 text-center">
                Không có buổi nào khớp bộ lọc.
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>

      {visible.length > shown.length && (
        <div className="flex justify-center border-t p-3">
          <Button variant="outline" size="sm" onClick={onMore}>
            Hiện thêm {Math.min(PAGE_STEP, visible.length - shown.length)} buổi (còn{" "}
            {visible.length - shown.length})
          </Button>
        </div>
      )}

      {sq.residentCount > 0 && (
        <p className="text-muted-foreground border-t p-3 text-xs">
          {sq.residentCount} buổi của GV cơ hữu không nằm trong bảng này: không điều phối
          viên nào nộp giờ cho họ, Giai đoạn 2 tự chọn giờ trong toàn tuần.
        </p>
      )}
    </Card>
  );
}

// Thanh bar do bang SO BUOI CON THIEU (khong phai % da xong) de do dai bar trung
// voi thu tu sap xep va voi viec can lam - bar dai nhat = nhieu viec nhat.
function CoordsView({ sq, onPickCoord }) {
  const maxMissing = Math.max(1, ...sq.coordinators.map((c) => c.missing));

  return (
    <Card
      title={`Theo điều phối viên (${sq.coordinators.length})`}
      note="Độ dài thanh = số buổi còn thiếu giờ · bấm một dòng để mở hàng đợi của riêng người đó"
    >
      <ul className="divide-y">
        {sq.coordinators.map((c) => {
          const isDone = c.missing === 0;
          const Row = isDone ? "div" : "button";
          return (
            <li key={c.coordinator}>
              <Row
                type={isDone ? undefined : "button"}
                onClick={isDone ? undefined : () => onPickCoord(c.coordinator)}
                title={isDone ? c.coordinator : `Mở ${c.missing} buổi cần thu giờ của ${c.coordinator}`}
                className={cn(
                  "flex w-full items-center gap-3 px-3 py-2 text-left text-sm",
                  !isDone && "hover:bg-muted transition-colors",
                  isDone && "text-muted-foreground",
                )}
              >
                <span className="w-40 shrink-0 truncate">{c.coordinator}</span>
                <span className="bg-muted h-2 min-w-0 flex-1 overflow-hidden rounded-full">
                  {c.missing > 0 && (
                    <span
                      className="block h-full rounded-full bg-amber-500"
                      style={{ width: `${Math.round((c.missing / maxMissing) * 100)}%` }}
                    />
                  )}
                </span>
                <span className="w-24 shrink-0 text-right text-xs">
                  {isDone ? (
                    <span className="text-emerald-700">đủ ✓</span>
                  ) : (
                    <span className="text-amber-700">thiếu {c.missing}</span>
                  )}
                </span>
                <span className="text-muted-foreground w-16 shrink-0 text-right text-xs tabular-nums">
                  {c.done}/{c.total}
                </span>
              </Row>
            </li>
          );
        })}
      </ul>
    </Card>
  );
}
