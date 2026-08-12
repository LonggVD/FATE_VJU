import { useRef, useState } from "react";
import { FileSpreadsheet, TriangleAlert, Upload } from "lucide-react";
import { useAppData } from "../../context/AppDataContext";
import { Notice } from "@/components/shared/notice";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

/**
 * Nap DANH SACH GIANG VIEN CO HUU cua truong (.xlsx).
 *
 * HAI BUOC nhu nhap file ke hoach: danh sach nay la NGUON CHINH THUC phan loai
 * co huu/thinh giang, nen nap no co the DOI LOAI nhieu giang viên - keo theo lop
 * cua ho chuyen giai doan xep lich. Phai cho xem truoc AI bi doi roi moi ghi.
 */
export default function ImportLecturersDialog({ open, onOpenChange }) {
  const { loading, doLecturersPreview, doLecturersCommit } = useAppData();
  const inputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [error, setError] = useState(null);

  const reset = () => {
    setFile(null);
    setPreview(null);
    setError(null);
    if (inputRef.current) inputRef.current.value = "";
  };

  const handlePick = async (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setFile(f);
    setPreview(null);
    setError(null);
    try {
      setPreview(await doLecturersPreview(f));
    } catch (err) {
      setError(err.message);
    }
  };

  const handleCommit = async () => {
    try {
      await doLecturersCommit();
      onOpenChange(false);
      reset();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <Dialog
      open={open}
      onOpenChange={(o) => {
        onOpenChange(o);
        if (!o) reset();
      }}
    >
      <DialogContent className="max-h-[85vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Nhập danh sách giảng viên cơ hữu</DialogTitle>
          <DialogDescription>
            File .xlsx có cột <strong>Full Name</strong> (hoặc “Họ và tên”). Sau khi nạp, danh sách
            này là <strong>nguồn chính thức</strong>: có tên trong đó là cơ hữu, không có là thỉnh
            giảng — hệ thống thôi đoán theo ô “Đơn vị công tác”.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3 text-sm">
          <label className="hover:bg-muted/50 flex cursor-pointer items-center gap-3 rounded-lg border border-dashed p-4">
            <FileSpreadsheet className="text-muted-foreground size-6 shrink-0" />
            <div className="min-w-0">
              <div className="font-medium">{file ? file.name : "Chọn file .xlsx"}</div>
              <div className="text-muted-foreground text-xs">
                Đọc xong chỉ hiện ra sẽ thay đổi những gì — chưa ghi gì cả.
              </div>
            </div>
            <input
              ref={inputRef}
              type="file"
              accept=".xlsx"
              className="hidden"
              onChange={handlePick}
            />
          </label>

          {error && (
            <Notice tone="red" icon={TriangleAlert}>
              {error}
            </Notice>
          )}

          {preview && (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                <Oto nhan="Người trong danh sách" so={preview.count} />
                <Oto nhan="Đang dạy kỳ này" so={preview.khop} />
                <Oto nhan="Không dạy kỳ này" so={preview.khongDay?.length ?? 0} />
              </div>
              <p className="text-muted-foreground text-xs">
                Đọc từ sheet “{preview.sheet}”. Ví dụ: {preview.sample?.slice(0, 4).join(", ")}…
              </p>

              {/* AI BI DOI LOAI - phan quan trong nhat cua ban xem truoc. Doi loai
                  lam lop chuyen giai doan xep lich, nen phai liet ke ten chu khong
                  chi dua ra con so. */}
              <DoiLoai
                tone="emerald"
                tieuDe="sẽ chuyển sang CƠ HỮU"
                moTa="Có tên trong danh sách nhưng hệ thống đang xếp thỉnh giảng:"
                ds={preview.doiSangCoHuu}
              />
              <DoiLoai
                tone="amber"
                tieuDe="sẽ chuyển sang THỈNH GIẢNG"
                moTa="Đang được xếp cơ hữu (theo ô Đơn vị công tác) nhưng KHÔNG có trong danh sách — nếu đây là người của trường thì nên bổ sung vào file trước khi nạp:"
                ds={preview.doiSangThinhGiang}
              />

              {preview.duplicates?.length > 0 && (
                <Notice tone="amber" icon={TriangleAlert}>
                  {preview.duplicates.length} người bị ghi nhiều lần trong file (đã gộp làm một):{" "}
                  {preview.duplicates.slice(0, 5).map((d) => d.name).join(", ")}
                </Notice>
              )}

              {preview.doiSangCoHuu?.length === 0 && preview.doiSangThinhGiang?.length === 0 && (
                <Notice tone="emerald">
                  Không giảng viên nào bị đổi loại — danh sách khớp với cách hệ thống đang xếp.
                </Notice>
              )}
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={loading}>
            Hủy
          </Button>
          <Button onClick={handleCommit} disabled={loading || !preview}>
            <Upload className="size-4" />
            {loading ? "Đang nạp…" : `Nạp danh sách${preview ? ` (${preview.count} người)` : ""}`}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function Oto({ nhan, so }) {
  return (
    <div className="bg-muted/40 rounded-lg border p-2.5">
      <div className="text-lg font-semibold tabular-nums">{so}</div>
      <div className="text-muted-foreground text-xs">{nhan}</div>
    </div>
  );
}

function DoiLoai({ tone, tieuDe, moTa, ds }) {
  if (!ds?.length) return null;
  return (
    <details className="rounded-lg border" open>
      <summary className="cursor-pointer px-3 py-2 text-sm font-medium">
        {ds.length} giảng viên {tieuDe}
      </summary>
      <div className="space-y-1.5 px-3 pb-3 text-xs">
        <p className="text-muted-foreground">{moTa}</p>
        {ds.map((t) => (
          <div key={t.id} className="bg-background/60 rounded border px-2 py-1.5">
            <span className="font-medium">{t.name}</span>
            <span className="text-muted-foreground"> — {t.org || "(không ghi đơn vị)"}</span>
          </div>
        ))}
      </div>
    </details>
  );
}
