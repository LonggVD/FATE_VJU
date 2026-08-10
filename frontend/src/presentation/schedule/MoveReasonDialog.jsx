import { useEffect, useState } from "react";
import { TriangleAlert } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";

// Bung ra khi keo 1 buoi tha vao o dang trung GV/het phong (backend tra 409).
// Dong 2 da chot: CHO PHEP dat vao do, nhung PHAI ghi ly do de xac nhan - hop
// thoai nay la buoc bat buoc ghi ly do do, khong phai canh bao suong.
export default function MoveReasonDialog({ pending, onConfirm, onCancel }) {
  const [reason, setReason] = useState("");

  // Component nay khong bi thao ra giua cac lan mo (parent luon render no, chi
  // doi prop `pending`), nen phai tu xoa o ly do moi lan mo lai - neu khong,
  // lan xung dot sau se dien san ly do cua lan truoc va rat de bi gui nham.
  useEffect(() => {
    if (pending) setReason("");
  }, [pending]);

  const conflict = pending?.conflict;

  return (
    <Dialog
      open={!!pending}
      onOpenChange={(open) => {
        if (!open) onCancel();
      }}
    >
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <TriangleAlert className="size-4 shrink-0 text-amber-600" />
            Ô này đang có vấn đề
          </DialogTitle>
          <DialogDescription>
            Vẫn có thể đặt vào đây, nhưng cần ghi lý do để giáo vụ khác biết đây
            là quyết định có chủ ý — không phải lỗi hệ thống.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-1 rounded-lg border border-amber-500/20 bg-amber-500/10 px-4 py-3 text-sm">
          {conflict?.teacherClashIds?.length > 0 && (
            <p>
              Trùng giờ với buổi{" "}
              <strong>#{conflict.teacherClashIds.join(", #")}</strong> (cùng
              giảng viên).
            </p>
          )}
          {conflict?.roomFull && (
            <p>
              Hết phòng cùng loại tại giờ này ({conflict.sameRoomCount}/
              {conflict.pool} phòng đang dùng).
            </p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="move-reason">Lý do (bắt buộc)</Label>
          <textarea
            id="move-reason"
            className="border-input focus-visible:border-ring focus-visible:ring-ring/50 min-h-24 w-full rounded-md border bg-transparent px-3 py-2 text-sm shadow-xs transition-[color,box-shadow] outline-none focus-visible:ring-[3px]"
            placeholder="Vì sao vẫn đặt vào đây?"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            autoFocus
          />
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onCancel}>
            Hủy
          </Button>
          <Button
            variant="warning"
            disabled={!reason.trim()}
            onClick={() => onConfirm(reason.trim())}
          >
            Xác nhận đặt vào đây
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
