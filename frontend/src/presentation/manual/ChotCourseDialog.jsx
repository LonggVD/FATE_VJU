import { useState } from "react";
import { Lock, TriangleAlert } from "lucide-react";
import { useAppData } from "../../context/AppDataContext";
import { Notice } from "@/components/shared/notice";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

const NGUOI_KEY = "tkb_nguoi_chot";

function dayNumber(day) {
  if (day == null) return "—";
  return day === 6 ? "CN" : `T${day + 2}`;
}

/**
 * CHOT LICH cho ca mot hoc phan.
 *
 * Vi sao la mot HOP THOAI chu khong phai bam mot cai la xong: chot = ghi gio dang
 * hien tren luoi thanh gio CHINH THUC va khoa lai (sua tay, keo-tha, xoa gio hang
 * loat deu bi chan). Phai cho nhin DU danh sach lop kem gio truoc khi quyet - va
 * ghi lai ai chot, luc nao, vi sao.
 */
export default function ChotCourseDialog({ open, onOpenChange, group }) {
  const { loading, doChotCourse } = useAppData();
  const [nguoi, setNguoi] = useState(() => {
    try {
      return localStorage.getItem(NGUOI_KEY) || "";
    } catch {
      return "";
    }
  });
  const [note, setNote] = useState("");
  const [error, setError] = useState(null);

  const rows = group?.rows ?? [];
  // Chot ma con lop chua co gio thi ban chinh thuc se thieu - backend cung tu
  // choi, nhung phai noi truoc chu khong de bam roi moi bao.
  const thieuGio = rows.filter((c) => c.day == null || c.periodStart == null);

  const handleChot = async () => {
    setError(null);
    try {
      if (nguoi.trim()) localStorage.setItem(NGUOI_KEY, nguoi.trim());
    } catch {
      /* ignore */
    }
    try {
      await doChotCourse(group.courseId, { by: nguoi, note });
      onOpenChange(false);
      setNote("");
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85vh] overflow-y-auto sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>Chốt lịch — {group?.courseName}</DialogTitle>
          <DialogDescription>
            Giờ đang hiển thị của <strong>{rows.length} lớp</strong> sẽ thành giờ chính thức và bị{" "}
            <strong>ghim cứng</strong>: giải lại không dịch được, sửa tay / kéo-thả / xoá giờ hàng
            loạt đều bị chặn cho đến khi bỏ chốt.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3 text-sm">
          {thieuGio.length > 0 && (
            <Notice tone="amber" icon={TriangleAlert}>
              {thieuGio.length}/{rows.length} lớp <strong>chưa có giờ</strong> — chốt được thì mọi
              lớp phải có giờ. Hãy chạy xếp lịch hoặc nhập giờ cho chúng trước:{" "}
              {thieuGio.slice(0, 4).map((c) => c.classCode || `#${c.sectionId}`).join(", ")}
              {thieuGio.length > 4 && `, +${thieuGio.length - 4}`}.
            </Notice>
          )}

          <div className="rounded-lg border">
            <div className="text-muted-foreground border-b px-3 py-1.5 text-xs">
              Các lớp sẽ được chốt
            </div>
            <div className="max-h-56 divide-y overflow-y-auto text-xs">
              {rows.map((c) => (
                <div key={c.sectionId} className="flex items-baseline justify-between gap-2 px-3 py-1.5">
                  <span className="min-w-0 truncate">
                    <span className="font-medium">{c.classCode || `#${c.sectionId}`}</span>
                    <span className="text-muted-foreground">
                      {" "}
                      · {(c.teachers ?? []).map((t) => t.name).join(", ") || "chưa phân công"}
                    </span>
                  </span>
                  <span
                    className={
                      "shrink-0 tabular-nums " +
                      (c.day == null ? "text-amber-700" : "text-muted-foreground")
                    }
                  >
                    {c.day == null
                      ? "chưa có giờ"
                      : `${dayNumber(c.day)} tiết ${c.periodStart}-${c.periodEnd}`}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <label className="block">
            <span className="text-muted-foreground text-xs">Người chốt</span>
            <Input
              value={nguoi}
              onChange={(e) => setNguoi(e.target.value)}
              placeholder="Tên người chốt (để trống = “Giáo vụ”)"
            />
          </label>

          <label className="block">
            <span className="text-muted-foreground text-xs">Ghi chú</span>
            <Input
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="Ví dụ: đã xác nhận qua email với cô A ngày 12/8"
            />
          </label>

          {error && (
            <Notice tone="red" icon={TriangleAlert}>
              {error}
            </Notice>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={loading}>
            Hủy
          </Button>
          <Button onClick={handleChot} disabled={loading || thieuGio.length > 0}>
            <Lock className="size-4" />
            {loading ? "Đang chốt…" : `Chốt ${rows.length} lớp`}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
