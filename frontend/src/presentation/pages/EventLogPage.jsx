import { Trash2 } from "lucide-react";
import { useEventLog } from "../../context/EventLogContext";
import { Panel } from "@/components/shared/panel";
import { TONE_DOT } from "@/components/shared/pill";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

// Nhat ky ghi 3 loai: error / success / info (xem EventLogContext).
const TYPE_TONE = {
  error: "red",
  success: "emerald",
  info: "slate",
};

export default function EventLogPage() {
  const { entries, clear } = useEventLog();

  return (
    <Panel
      title={`Nhật ký thao tác (${entries.length})`}
      action={
        <Button variant="outline" size="sm" onClick={clear} disabled={!entries.length}>
          <Trash2 className="size-4" />
          Xóa nhật ký
        </Button>
      }
    >
      {entries.length === 0 ? (
        <p className="text-muted-foreground py-6 text-center text-sm">
          Chưa có thao tác nào được ghi lại.
        </p>
      ) : (
        <ul className="divide-y">
          {entries.map((e) => (
            <li key={e.id} className="flex items-start gap-2.5 py-2 text-sm">
              <span
                className={cn(
                  "mt-1.5 size-1.5 shrink-0 rounded-full",
                  TONE_DOT[TYPE_TONE[e.type] ?? "slate"],
                )}
                aria-hidden="true"
              />
              <span className="min-w-0">{e.message}</span>
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}
