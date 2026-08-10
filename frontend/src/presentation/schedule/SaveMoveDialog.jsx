import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

// Xac nhan TRUOC KHI goi API - keo-tha xong chi TAM GIU (pendingMove trong
// SchedulePage), chua luu gi ca. Bam "Luu" tren banner mo hop thoai nay; chi khi
// bam "Xac nhan cap nhat" o day thi moi thuc su goi doMoveLesson().
export default function SaveMoveDialog({ pending, fromLabel, toLabel, onConfirm, onCancel }) {
  return (
    <Dialog
      open={!!pending}
      onOpenChange={(open) => {
        if (!open) onCancel();
      }}
    >
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Xác nhận cập nhật thời khoá biểu</DialogTitle>
          <DialogDescription>
            Thay đổi sẽ được ghi vào lịch và hiện với mọi người đang xem.
          </DialogDescription>
        </DialogHeader>

        {pending && (
          <div className="bg-muted/40 space-y-2 rounded-lg border p-3 text-sm">
            <p className="font-medium">
              #{pending.sectionId} {pending.lesson.courseName}
            </p>
            <p className="text-muted-foreground flex flex-wrap items-center gap-2">
              <span className="text-foreground rounded-md border bg-background px-2 py-0.5">
                {fromLabel}
              </span>
              <ArrowRight className="size-4 shrink-0" />
              <span className="text-foreground rounded-md border bg-background px-2 py-0.5">
                {toLabel}
              </span>
            </p>
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={onCancel}>
            Hủy
          </Button>
          <Button onClick={onConfirm}>Xác nhận cập nhật</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
