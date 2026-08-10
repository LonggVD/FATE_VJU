import { useState } from "react";
import { Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

/**
 * Xuat bang "Du lieu hoc phan" hien co ra file .xlsx dung khuon FATE (sheet
 * "FATE", xem webapp/fate_export.py) - dat ten hoc ky de dat ten file va ghi
 * vao dong tieu de trong sheet, giong quy uoc file FATE.TKB.<hoc ky>.xlsx dang
 * dung. Tai file qua dieu huong <a>/window.location - KHONG qua apiGet
 * (helper do luon parse JSON, khong xu ly duoc file nhi phan).
 */
export default function ExportExcelDialog({ open, onOpenChange }) {
  const [label, setLabel] = useState("HK1 2026-2027");

  const handleExport = () => {
    const value = label.trim() || "TKB";
    window.location.href = `/api/manual/export?label=${encodeURIComponent(value)}`;
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Xuất file Excel</DialogTitle>
          <DialogDescription>
            Xuất toàn bộ "Dữ liệu học phần" hiện có ra file theo khuôn FATE (sheet "FATE"),
            dùng lại được cho kỳ sau qua "Nhập từ Excel".
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-2">
          <Label htmlFor="export-label">Tên học kỳ</Label>
          <Input
            id="export-label"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            placeholder="HK1 2026-2027"
            autoFocus
          />
          <p className="text-muted-foreground text-xs">
            Dùng để đặt tên file (FATE.TKB.{label.trim() || "…"}.xlsx) và ghi vào dòng tiêu đề
            trong sheet.
          </p>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Hủy
          </Button>
          <Button onClick={handleExport}>
            <Download className="size-4" />
            Xuất file
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
