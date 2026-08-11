import { useState } from "react";
import { Calendar, Check, CircleCheck, X } from "lucide-react";
import { PROBLEM_META, PROBLEM_TYPE } from "../../adapters/problemInbox";
import { REASON_META, UNPLACED_REASON } from "../../adapters/unplacedAnalysis";
import { TONE_CLASS, TONE_DOT } from "@/components/shared/pill";
import { cn } from "@/lib/utils";

// Mot hop thu duy nhat thay cho 4 khoi bao loi cu.
//
// Cot chi rong ~330px nen moi muc phai gon MOT DONG khi chua mo. Ban truoc moi
// muc chiem ~5 dong (tieu de + cau mo ta + dong hau qua + nhan loai + ten DPV)
// -> 13 muc thanh mot buc tuong chu, dung lai loi da mac o panel 280px truoc do.
//
// Cach rut: nhan loai noi MOT LAN o dau nhom thay vi lap lai tung dong; cau mo ta
// va ten dieu phoi vien day xuong phan mo ra; gio dung dang rut gon "T6·6-9".
//
// UNPLACED (buoi khong xep duoc) tach rieng sang tab "Chua xep duoc" - co goi y
// vung tiet trong khung gio GV da bao con TRONG, bam la xep (ghim) luon vao do
// (xem TAB_UNPLACED ben duoi), thay vi chi liet ke "khong xep duoc" suong nhu tab
// "Van de" von lam.
const ORDER = [
  PROBLEM_TYPE.CLASH,
  PROBLEM_TYPE.DUPLICATE,
  PROBLEM_TYPE.MISSING_HOURS,
];

// Anh xa 4 loai van de sang bo tone cua design system, thay cho cac class cu
// (.clash/.duplicate/.unplaced/.missing) trong styles.css. Do danh cho loai nang
// nhat (trung giang vien - lich sai that su); ba loai con lai giam dan.
const TONE_BY_TYPE = {
  [PROBLEM_TYPE.CLASH]: "red",
  [PROBLEM_TYPE.DUPLICATE]: "amber",
  [PROBLEM_TYPE.UNPLACED]: "violet",
  [PROBLEM_TYPE.MISSING_HOURS]: "slate",
};

const TAB = { VAN_DE: "van-de", UNPLACED: "unplaced" };

function Shell({ children }) {
  return (
    <aside className="bg-card sticky top-3 flex max-h-[calc(100vh-7rem)] flex-col gap-2.5 rounded-xl border p-3 shadow-sm">
      {children}
    </aside>
  );
}

function TabButton({ active, onClick, count, tone, children }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={cn(
        "flex-1 rounded-md px-2 py-1.5 text-xs font-medium transition-colors",
        active ? "bg-background shadow-sm" : "text-muted-foreground hover:text-foreground",
      )}
    >
      {children}
      <span
        className={cn(
          "ml-1.5 rounded-full px-1.5 py-0.5 text-[11px] tabular-nums",
          count > 0 ? TONE_CLASS[tone] : "bg-muted text-muted-foreground",
        )}
      >
        {count}
      </span>
    </button>
  );
}

/**
 * @param inbox ket qua buildProblemInbox() - gom {items, total, unplacedReport}.
 * @param onPlace(sectionId, slot) - xep (ghim) 1 buoi CHUA xep duoc vao 1 khung
 *   gio con trong (tab "Chua xep duoc"). Khong truyen thi tab do an nut xep.
 */
export default function ProblemInbox({ inbox, activeId, onPick, onClear, onPlace }) {
  const [tab, setTab] = useState(TAB.VAN_DE);
  const [openUnplacedId, setOpenUnplacedId] = useState(null);
  const [placing, setPlacing] = useState(null); // {sectionId, slot} dang xu ly
  const [placeError, setPlaceError] = useState(null);

  // CHI tinh lop THAT SU khong xep duoc (co bao gio nhung bi trung/het phong) -
  // loai NOT_SUBMITTED (chua nop gio, khong co gi de xet ca) ra khoi day, vi
  // do la van de "chua co du lieu", khac han "da co du lieu ma khong xep duoc" -
  // da co muc "Chua co gio" rieng ben tab "Van de" (gom theo DPV) lo dung viec
  // do, dua ca 2 loai vao chung 1 danh sach lam nguoi dung lam ro "chua xep
  // duoc" that su la bao nhieu.
  const unplacedItems = (inbox?.unplacedReport?.items ?? []).filter(
    (it) => it.reason !== UNPLACED_REASON.NOT_SUBMITTED,
  );

  if (!inbox || (inbox.total === 0 && unplacedItems.length === 0)) {
    return (
      <Shell>
        <div className="flex items-center justify-between">
          <span className="text-sm font-semibold">Hộp thư vấn đề</span>
        </div>
        <div className="flex items-center gap-2 rounded-lg border border-emerald-500/20 bg-emerald-500/10 px-3 py-2.5 text-sm text-emerald-700">
          <CircleCheck className="size-4 shrink-0" />
          Không có vấn đề nào
        </div>
      </Shell>
    );
  }

  const groups = ORDER.map((type) => ({
    type,
    meta: PROBLEM_META[type],
    tone: TONE_BY_TYPE[type],
    items: inbox.items.filter((i) => i.type === type),
  })).filter((g) => g.items.length > 0);
  const vanDeCount = groups.reduce((n, g) => n + g.items.length, 0);

  const handlePlace = async (sectionId, slot) => {
    if (!onPlace) return;
    setPlacing({ sectionId, slot });
    setPlaceError(null);
    try {
      await onPlace(sectionId, slot);
      setOpenUnplacedId(null);
    } catch (err) {
      setPlaceError(err.message || "Không xếp được vào ô này.");
    } finally {
      setPlacing(null);
    }
  };

  return (
    <Shell>
      <div className="flex items-center justify-between gap-2">
        <span className="text-sm font-semibold">Hộp thư vấn đề</span>
      </div>

      <div className="bg-muted flex items-center gap-1 rounded-lg p-1">
        <TabButton active={tab === TAB.VAN_DE} onClick={() => setTab(TAB.VAN_DE)} count={vanDeCount} tone="red">
          Vấn đề
        </TabButton>
        <TabButton
          active={tab === TAB.UNPLACED}
          onClick={() => setTab(TAB.UNPLACED)}
          count={unplacedItems.length}
          tone="violet"
        >
          Chưa xếp được
        </TabButton>
      </div>

      {tab === TAB.VAN_DE && activeId && (
        <button
          type="button"
          onClick={onClear}
          className="text-muted-foreground hover:bg-muted hover:text-foreground rounded-md border border-dashed px-2 py-1.5 text-xs transition-colors"
        >
          Bỏ chọn, xem lại toàn bộ
        </button>
      )}

      {tab === TAB.VAN_DE && (
        <div className="-mr-1 min-h-0 flex-1 space-y-3 overflow-y-auto pr-1">
          {groups.length === 0 && (
            <div className="flex items-center gap-2 rounded-lg border border-emerald-500/20 bg-emerald-500/10 px-3 py-2.5 text-sm text-emerald-700">
              <CircleCheck className="size-4 shrink-0" />
              Không có vấn đề nào
            </div>
          )}
          {groups.map((g) => (
            <section key={g.type}>
              <h4 className="mb-1 flex items-center justify-between gap-2">
                <span className="inline-flex items-center gap-1.5 text-xs font-semibold">
                  <span
                    className={cn("size-1.5 rounded-full", TONE_DOT[g.tone])}
                    aria-hidden="true"
                  />
                  {g.meta.label}
                </span>
                <span
                  className={cn(
                    "rounded-md px-1.5 py-0.5 text-[11px] font-medium tabular-nums",
                    TONE_CLASS[g.tone],
                  )}
                >
                  {g.items.length}
                </span>
              </h4>

              <div className="space-y-1">
                {g.items.map((it) => {
                  const on = activeId === it.id;
                  const isPair =
                    (it.type === PROBLEM_TYPE.CLASH ||
                      it.type === PROBLEM_TYPE.DUPLICATE) &&
                    it.sections?.length === 2;

                  return (
                    <div
                      key={it.id}
                      className={cn(
                        "overflow-hidden rounded-md border",
                        on ? "border-primary/40 bg-muted/50" : "border-transparent",
                      )}
                    >
                      <button
                        type="button"
                        onClick={() => onPick(on ? null : it)}
                        aria-pressed={on}
                        title={it.detail}
                        className={cn(
                          "hover:bg-muted flex w-full items-baseline justify-between gap-2 px-2 py-1.5 text-left text-[13px] transition-colors",
                          on && "font-medium",
                        )}
                      >
                        <span className="min-w-0 truncate">{it.title}</span>
                        <span className="text-muted-foreground shrink-0 text-[11px] tabular-nums">
                          {it.whenShort}
                        </span>
                      </button>

                      {on && (
                        <div className="space-y-2 px-2 pt-1 pb-2 text-xs">
                          {it.brief && (
                            <div className="text-muted-foreground">{it.brief}</div>
                          )}

                          {isPair && it.when && (
                            // So do "hai buoi tranh mot cho" - giu tu man Giai doan 1 cu.
                            <div className="bg-background space-y-1 rounded-md border p-2">
                              <div className="text-muted-foreground text-[11px]">
                                {it.when} — chỉ chứa được 1 buổi
                              </div>
                              {it.sections.map((s) => {
                                const dropped = it.unplacedIds?.includes(
                                  s.sectionId,
                                );
                                return (
                                  <div
                                    key={s.sectionId}
                                    className={cn(
                                      "flex items-center gap-1.5 rounded px-1.5 py-1",
                                      dropped
                                        ? "bg-red-500/10 text-red-700"
                                        : "bg-emerald-500/10 text-emerald-700",
                                    )}
                                  >
                                    {dropped ? (
                                      <X className="size-3 shrink-0" />
                                    ) : (
                                      <Check className="size-3 shrink-0" />
                                    )}
                                    <span className="font-medium">
                                      {s.classCode || `#${s.sectionId}`}
                                    </span>
                                    <span className="opacity-80">
                                      {dropped ? "bị bỏ lại" : "đã xếp"}
                                    </span>
                                  </div>
                                );
                              })}
                            </div>
                          )}

                          {it.coordinators?.length > 0 && (
                            <div className="text-muted-foreground">
                              {it.sameCoordinator
                                ? `Liên hệ ${it.coordinators[0]}`
                                : `Liên hệ ${it.coordinators.join(" và ")}`}
                            </div>
                          )}

                          <div className="bg-muted/60 text-muted-foreground rounded p-1.5">
                            {g.meta.fix}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </section>
          ))}
        </div>
      )}

      {tab === TAB.UNPLACED && (
        <div className="-mr-1 min-h-0 flex-1 space-y-2 overflow-y-auto pr-1">
          {unplacedItems.length === 0 && (
            <div className="flex items-center gap-2 rounded-lg border border-emerald-500/20 bg-emerald-500/10 px-3 py-2.5 text-sm text-emerald-700">
              <CircleCheck className="size-4 shrink-0" />
              Mọi buổi thỉnh giảng đều đã xếp được.
            </div>
          )}

          {placeError && (
            <div className="rounded-md border border-red-500/20 bg-red-500/10 px-2 py-1.5 text-xs text-red-700">
              {placeError}
            </div>
          )}

          {unplacedItems.map((it) => {
            const open = openUnplacedId === it.id;
            const reasonMeta = REASON_META[it.reason];
            return (
              <div
                key={it.id}
                className={cn(
                  "overflow-hidden rounded-md border",
                  open ? "border-primary/40 bg-muted/50" : "border-transparent",
                )}
              >
                <button
                  type="button"
                  onClick={() => setOpenUnplacedId(open ? null : it.id)}
                  aria-pressed={open}
                  className={cn(
                    "hover:bg-muted flex w-full flex-col gap-0.5 px-2 py-1.5 text-left text-[13px] transition-colors",
                    open && "font-medium",
                  )}
                >
                  <span className="flex items-center justify-between gap-2">
                    <span className="min-w-0 truncate">
                      {it.classCode || `#${it.id}`} · {it.courseName}
                    </span>
                    <span
                      className={cn(
                        "shrink-0 rounded-md px-1.5 py-0.5 text-[11px] font-medium",
                        TONE_CLASS.violet,
                      )}
                    >
                      {reasonMeta.label}
                    </span>
                  </span>
                  <span className="text-muted-foreground truncate text-[11px] font-normal">
                    {it.teacherName}
                  </span>
                </button>

                {open && (
                  <div className="space-y-2 px-2 pt-1 pb-2 text-xs">
                    <div className="text-muted-foreground">{reasonMeta.hint}</div>

                    {it.windowSlots.length === 0 ? (
                      <div className="bg-muted/60 text-muted-foreground rounded p-1.5">
                        {reasonMeta.fix}
                      </div>
                    ) : (
                      <div className="space-y-1">
                        <div className="text-muted-foreground flex items-center gap-1 text-[11px]">
                          <Calendar className="size-3" />
                          Khung giờ GV đã báo — bấm ô còn trống để xếp vào ngay:
                        </div>
                        <div className="space-y-1.5">
                          {it.windows.map((w) => {
                            const isPlacing =
                              placing?.sectionId === it.id && placing?.slot === w.slot;
                            if (!w.blocked) {
                              return (
                                <button
                                  key={w.slot}
                                  type="button"
                                  disabled={!onPlace || isPlacing}
                                  onClick={() => handlePlace(it.id, w.slot)}
                                  className="block w-full rounded-md border border-emerald-500/40 bg-emerald-500/10 px-2 py-1 text-left font-medium text-emerald-700 transition-colors hover:bg-emerald-500/20 disabled:opacity-60"
                                >
                                  {isPlacing ? "Đang xếp…" : `${w.label} — còn trống, bấm để xếp vào đây`}
                                </button>
                              );
                            }
                            // Hien DAY DU ten mon/ma lop dang chiem cho, khong
                            // chi so #id kho hieu - day chinh la thong tin giao
                            // vu can de biet "phai doi gio voi ai".
                            return (
                              <div
                                key={w.slot}
                                className="rounded-md border border-dashed px-2 py-1 text-muted-foreground"
                              >
                                <div className="flex items-center justify-between gap-2">
                                  <span className="font-medium">{w.label}</span>
                                  <span className="text-[11px]">đang bận</span>
                                </div>
                                {w.roomFull && (
                                  <div className="text-[11px]">
                                    Hết phòng {it.roomType} ({w.sameRoomCount}/{w.pool})
                                  </div>
                                )}
                                {w.teacherBlockers.length > 0 && (
                                  <ul className="mt-0.5 space-y-0.5 text-[11px]">
                                    {w.teacherBlockers.map((b) => (
                                      <li key={b.id}>
                                        Trùng với <strong>{b.classCode || `#${b.id}`}</strong> ·{" "}
                                        {b.courseName} ({b.teacherName})
                                      </li>
                                    ))}
                                  </ul>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {it.coordinator && (
                      <div className="text-muted-foreground">Liên hệ {it.coordinator}</div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </Shell>
  );
}
