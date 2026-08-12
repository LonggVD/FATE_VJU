import { Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

// Ba buoc cua quy trinh, gom thanh MOT DONG. Truoc day moi buoc la mot tab rieng
// voi header 90px cua no - nhung Giai doan 1 va 2 khong phai hai khung nhin, chung
// la hai buoc cua cung mot san pham. Buoc thi thuoc ve thanh tien trinh.
export default function WorkflowStrip({ steps, canEdit, loading }) {
  return (
    <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
      {steps.map((s, i) => {
        const done = s.state === "done";
        return (
          <div
            key={s.key}
            className={cn(
              "bg-card flex items-center gap-3 rounded-xl border p-3 shadow-sm",
              done && "border-emerald-500/40",
              // Buoc co canh bao (vd nghiem GD2 vua bi huy) phai NHIN RA duoc,
              // khong the chi doi mot con so o dong `value`.
              //
              // CHI doi vien + do day vien, KHONG dat nen amber: cn() la
              // tailwind-merge, no coi `bg-amber-500/5` xung dot voi `bg-card` va
              // XOA bg-card di - the mat nen card, thanh trong suot tren nen
              // trang. Vien 2px + chu amber da du nhin ra ma khong pha nen.
              s.hint && "border-2 border-amber-500/60",
            )}
          >
            <span
              className={cn(
                "flex size-7 shrink-0 items-center justify-center rounded-full text-xs font-bold",
                done
                  ? "bg-emerald-600 text-white"
                  : "bg-muted text-muted-foreground",
              )}
              aria-hidden="true"
            >
              {done ? <Check className="size-4" /> : i + 1}
            </span>

            <span className="min-w-0 flex-1">
              <span className="block truncate text-sm font-medium">
                {s.label}
              </span>
              <span className="text-muted-foreground block text-xs tabular-nums">
                {s.value}
              </span>
              {/* `note` = chu thich trung tinh (vd "can xep thinh giang truoc"),
                  `hint` = CANH BAO (vd nghiem GD2 vua bi huy). Hai muc do khac
                  nhau nen mau khac nhau, khong gop lam mot. */}
              {s.note && (
                <span className="text-muted-foreground mt-0.5 block text-[11px] leading-snug">
                  {s.note}
                </span>
              )}
              {s.hint && (
                <span className="mt-0.5 block text-[11px] leading-snug text-amber-700">
                  {s.hint}
                </span>
              )}
            </span>

            {s.action && canEdit && (
              <Button
                size="sm"
                variant={done ? "outline" : "default"}
                disabled={loading || s.disabled}
                onClick={s.action}
              >
                {loading ? "Đang chạy…" : s.actionLabel}
              </Button>
            )}
          </div>
        );
      })}
    </div>
  );
}
