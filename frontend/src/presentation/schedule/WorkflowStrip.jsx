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
