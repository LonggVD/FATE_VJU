import { useEffect, useState } from "react";
import { Spinner } from "@/components/ui/spinner";
import { cn } from "@/lib/utils";

// Adapt tu FE_SCHEDULE/SolverProgress.jsx: bo toan bo co che poll jobId (giai
// cua scheduler_core.py la dong bo, chan toi da 30s, khong co job-queue) -
// chi giu lai phan hoat hinh cosmetic, dieu khien boi 1 boolean "active".
// Component chi duoc render khi active=true (component parent tu go bo khi
// giai xong), nen khong can logic "snap to 100% on unmount".
const STEPS = ["Khởi tạo", "Phân tích", "Xếp lịch", "Tối ưu", "Hoàn tất"];

export default function SolverProgress({ label = "Đang giải bằng CP-SAT" }) {
  const [pct, setPct] = useState(0);
  const [dots, setDots] = useState(0);

  useEffect(() => {
    const dotTimer = setInterval(() => setDots((d) => (d + 1) % 4), 500);
    const pctTimer = setInterval(() => setPct((p) => (p < 90 ? p + 1 : p)), 250);
    return () => { clearInterval(dotTimer); clearInterval(pctTimer); };
  }, []);

  return (
    <div
      className="fixed inset-0 z-300 flex items-center justify-center bg-black/40 p-4 backdrop-blur-[1px]"
      role="status"
      aria-live="polite"
    >
      <div className="bg-card w-full max-w-md rounded-xl border p-6 shadow-lg">
        <div className="flex items-center gap-3">
          <Spinner className="text-primary size-6" />
          <div className="min-w-0 flex-1">
            <p className="text-sm font-semibold">
              {label}
              {"...".slice(0, dots + 1)}
            </p>
          </div>
          <span className="text-primary text-2xl font-bold tabular-nums">
            {pct}%
          </span>
        </div>

        <div className="bg-muted mt-4 h-2 overflow-hidden rounded-full">
          <div
            className="bg-primary h-full rounded-full transition-[width] duration-200"
            style={{ width: `${pct}%` }}
          />
        </div>

        <div className="mt-4 flex flex-wrap gap-x-4 gap-y-2">
          {STEPS.map((step, i) => {
            const threshold = i * 20;
            const done = pct >= threshold + 18;
            const active = pct >= threshold && !done;
            return (
              <div
                key={step}
                className={cn(
                  "flex items-center gap-1.5 text-xs",
                  done
                    ? "text-emerald-600"
                    : active
                      ? "text-primary font-medium"
                      : "text-muted-foreground",
                )}
              >
                <span
                  className={cn(
                    "size-2.5 rounded-full border-2",
                    done
                      ? "border-emerald-600 bg-emerald-600"
                      : active
                        ? "border-primary bg-primary animate-pulse"
                        : "border-border",
                  )}
                  aria-hidden="true"
                />
                {step}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
