import { ArrowRight, Save } from "lucide-react";
import { Button } from "@/components/ui/button";

// Banner "co 1 thay doi chua luu" - hien ngay sau khi keo-tha (chi thi giac,
// CHUA goi API). Nam giua dong pham vi va luoi nen thay duoc o ca che do thuong
// va toan man hinh, khong can plumbing rieng cho fullscreen.
//
// Dung tone ho phach (khong phai do): day la trang thai "dang cho", khong phai
// loi - do la mau thuong hieu va da danh cho canh bao that.
export default function PendingMoveBanner({ pending, fromLabel, toLabel, onSave, onCancel }) {
  if (!pending) return null;

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-amber-500/20 bg-amber-500/10 px-4 py-2.5 text-sm">
      <span className="flex min-w-0 flex-wrap items-center gap-x-2 gap-y-1">
        <strong className="truncate">
          {pending.lesson.classCode || `#${pending.sectionId}`} {pending.lesson.courseName}
        </strong>
        <span className="text-muted-foreground inline-flex items-center gap-1.5">
          {fromLabel}
          <ArrowRight className="size-3.5 shrink-0" />
          {toLabel}
        </span>
        <span className="rounded-md bg-amber-500/20 px-2 py-0.5 text-xs font-medium text-amber-700">
          chưa lưu
        </span>
      </span>

      <div className="flex shrink-0 items-center gap-2">
        <Button variant="outline" size="sm" onClick={onCancel}>
          Hủy
        </Button>
        <Button size="sm" onClick={onSave}>
          <Save className="size-4" />
          Lưu
        </Button>
      </div>
    </div>
  );
}
