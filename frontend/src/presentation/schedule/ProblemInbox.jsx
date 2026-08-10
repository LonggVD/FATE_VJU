import { Check, CircleCheck, X } from "lucide-react";
import { PROBLEM_META, PROBLEM_TYPE } from "../../adapters/problemInbox";
import { Pill, TONE_CLASS, TONE_DOT } from "@/components/shared/pill";
import { cn } from "@/lib/utils";

// Mot hop thu duy nhat thay cho 4 khoi bao loi cu.
//
// Cot chi rong ~330px nen moi muc phai gon MOT DONG khi chua mo. Ban truoc moi
// muc chiem ~5 dong (tieu de + cau mo ta + dong hau qua + nhan loai + ten DPV)
// -> 13 muc thanh mot buc tuong chu, dung lai loi da mac o panel 280px truoc do.
//
// Cach rut: nhan loai noi MOT LAN o dau nhom thay vi lap lai tung dong; cau mo ta
// va ten dieu phoi vien day xuong phan mo ra; gio dung dang rut gon "T6·6-9".
const ORDER = [
  PROBLEM_TYPE.CLASH,
  PROBLEM_TYPE.DUPLICATE,
  PROBLEM_TYPE.UNPLACED,
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

function Shell({ children }) {
  return (
    <aside className="bg-card sticky top-3 flex max-h-[calc(100vh-7rem)] flex-col gap-2.5 rounded-xl border p-3 shadow-sm">
      {children}
    </aside>
  );
}

export default function ProblemInbox({ inbox, activeId, onPick, onClear }) {
  if (!inbox || inbox.total === 0) {
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

  return (
    <Shell>
      <div className="flex items-center justify-between gap-2">
        <span className="text-sm font-semibold">Hộp thư vấn đề</span>
        <Pill tone="red">{inbox.total}</Pill>
      </div>

      {activeId && (
        <button
          type="button"
          onClick={onClear}
          className="text-muted-foreground hover:bg-muted hover:text-foreground rounded-md border border-dashed px-2 py-1.5 text-xs transition-colors"
        >
          Bỏ chọn, xem lại toàn bộ
        </button>
      )}

      <div className="-mr-1 min-h-0 flex-1 space-y-3 overflow-y-auto pr-1">
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
                                    #{s.sectionId}
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
    </Shell>
  );
}
