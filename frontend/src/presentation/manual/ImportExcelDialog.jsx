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
 * Nap file ke hoach giang day (Excel) cu vao form "Du lieu hoc phan".
 *
 * HAI BUOC co chu y, khong nhap thanh mot: doc file xong chi HIEN RA se nap
 * duoc nhung gi, phai bam xac nhan moi ghi. Ly do: import la thao tac XOA HET
 * du lieu dang co va khong hoan tac duoc - phai cho nguoi dung doi chieu con so
 * (bao nhieu lop/hoc phan/GV, bao nhieu dong bi bo va vi sao) truoc khi quyet.
 */
export default function ImportExcelDialog({ open, onOpenChange }) {
  const { loading, doImportPreview, doImportCommit } = useAppData();
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
      setPreview(await doImportPreview(f));
    } catch (err) {
      setError(err.message);
    }
  };

  const handleCommit = async (mode = "replace") => {
    try {
      await doImportCommit(mode);
      onOpenChange(false);
      reset();
    } catch (err) {
      setError(err.message);
    }
  };

  const s = preview?.summary;

  return (
    <Dialog
      open={open}
      onOpenChange={(o) => {
        onOpenChange(o);
        if (!o) reset();
      }}
    >
      <DialogContent className="max-h-[85vh] gap-0 overflow-hidden p-0 sm:max-w-2xl">
        <DialogHeader className="border-b px-6 py-4">
          <DialogTitle>Nhập dữ liệu từ file Excel</DialogTitle>
          <DialogDescription>
            Nhận file kế hoạch giảng dạy có sheet “FATE” hoặc “Giảng dạy cho FATE”.
          </DialogDescription>
        </DialogHeader>

        <div className="max-h-[60vh] space-y-4 overflow-y-auto px-6 py-4">
          <div>
            <input
              ref={inputRef}
              type="file"
              accept=".xlsx"
              onChange={handlePick}
              className="sr-only"
              id="import-file"
            />
            <Button
              variant="outline"
              disabled={loading}
              onClick={() => inputRef.current?.click()}
            >
              <Upload className="size-4" />
              {file ? "Chọn file khác" : "Chọn file .xlsx"}
            </Button>
            {file && (
              <p className="text-muted-foreground mt-2 flex items-center gap-1.5 text-xs">
                <FileSpreadsheet className="size-3.5 shrink-0" />
                {file.name}
              </p>
            )}
          </div>

          {error && (
            <Notice tone="red" icon={TriangleAlert}>
              {error}
            </Notice>
          )}

          {loading && !preview && file && (
            <p className="text-muted-foreground text-sm">Đang đọc file…</p>
          )}

          {s && (
            <>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                {[
                  { nhan: "Lớp", so: s.soLopDungDuoc },
                  { nhan: "Học phần", so: s.soHocPhan },
                  { nhan: "Giảng viên", so: s.soGiangVien },
                  { nhan: "Chương trình", so: s.soChuongTrinh },
                ].map((x) => (
                  <div key={x.nhan} className="bg-muted/40 rounded-lg border p-3">
                    <p className="text-muted-foreground text-xs">{x.nhan}</p>
                    <p className="text-xl font-semibold tabular-nums">{x.so}</p>
                  </div>
                ))}
              </div>

              <p className="text-muted-foreground text-xs">
                Đọc từ sheet “{s.sheet}” ·{" "}
                <strong className="text-foreground">{s.soLopDaCoGio}</strong> lớp đã có
                giờ cụ thể ·{" "}
                <strong className="text-foreground">{s.soLopChuaCoGio}</strong> lớp chưa
                có giờ (để thuật toán tự xếp)
                {s.soLopChuaPhanCong > 0 && (
                  <>
                    {" · "}
                    <strong className="text-amber-700">{s.soLopChuaPhanCong}</strong> lớp
                    chưa phân công giảng viên
                  </>
                )}
              </p>

              <p className="text-muted-foreground text-xs">
                Mọi dòng có dữ liệu trong file đều được nạp — kể cả lớp chưa có giảng viên.
              </p>

              {/* LOI TRONG CHINH FILE - khac han cac canh bao ben duoi (von noi
                  ve viec import da phai tu quyet dinh gi). Day la nhung cho FILE
                  ghi sai: mot ma lop dung cho 2 hoc phan, ten khac dau thanh 2
                  hoc phan, mot email 2 nguoi, dong nhap trung... Import khong
                  sua duoc va cung khong nen tu doan - phai sua o file goc. Truoc
                  day buoc xem truoc khong he hien, phai viet script rieng moi
                  thay, tuc thuc te la khong ai thay. */}
              {preview.dataIssuesSummary?.soNghiemTrong > 0 && (
                <ChiTiet
                  tone="orange"
                  tieuDe={`Kiểm tra dữ liệu — ${preview.dataIssuesSummary.soNghiemTrong} chỗ nghi SAI trong file`}
                  moTa="Dữ liệu vẫn nạp được, nhưng những chỗ này gần như chắc chắn là sai trong file gốc — nên sửa file rồi nạp lại:"
                  nhom={preview.dataIssues.filter((g) => g.muc === "nghiem_trong")}
                  // Nguoi sua duoc nhung loi nay la khoa/CTDT, khong phai nguoi
                  // dang bam nhap - ho can mot file mo bang Excel duoc, co so dong
                  // de nhay den, chu khong phai anh chup man hinh.
                  taiVe="/api/manual/import/issues.xlsx"
                />
              )}

              {preview.dataIssuesSummary?.soLuuY > 0 && (
                <ChiTiet
                  tone="blue"
                  tieuDe={`Kiểm tra dữ liệu — ${preview.dataIssuesSummary.soLuuY} chỗ nên rà lại`}
                  moTa="Không chắc là sai, nhưng nên biết: ô để trống, ghi chú viết lẫn vào ô dữ liệu…"
                  nhom={preview.dataIssues.filter((g) => g.muc === "luu_y")}
                />
              )}

              {s.soDongBoQua > 0 && (
                <ChiTiet
                  tone="amber"
                  tieuDe={`${s.soDongBoQua} dòng KHÔNG được nạp`}
                  moTa="Những dòng này không tạo được lớp. Dưới đây là đủ các lý do, kèm số dòng cụ thể:"
                  nhom={preview.skippedGroups}
                />
              )}

              {s.soCanhBao > 0 && (
                <ChiTiet
                  tone="blue"
                  tieuDe={`${s.soCanhBao} dòng có lưu ý (vẫn được nạp)`}
                  moTa="Những dòng này VẪN vào form, nhưng có chỗ hệ thống phải tự quyết — nên biết để rà lại:"
                  nhom={preview.warningGroups}
                />
              )}

              {preview.errors?.length > 0 && (
                <ChiTiet
                  tone="red"
                  tieuDe={`${preview.errors.length} dòng lỗi`}
                  moTa="Không tạo được lớp từ những dòng này:"
                  nhom={[{
                    loai: "loi",
                    nhan: "Lỗi khi dựng lớp",
                    so: preview.errors.length,
                    dong: preview.errors.map((x) => x.row),
                    chiTiet: preview.errors.map((x) => ({ text: x.reason, so: 1 })),
                  }]}
                />
              )}

              <Notice tone="red" icon={TriangleAlert}>
                Nạp file sẽ <strong>xóa toàn bộ dữ liệu hiện có</strong> (kể cả kết quả đã
                giải) và thay bằng nội dung file. Không hoàn tác được.
              </Notice>
            </>
          )}
        </div>

        <DialogFooter className="flex-wrap gap-2 border-t px-6 py-3">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Hủy
          </Button>
          {/* GOP THEM: de nap file khoa nay roi nap tiep file khoa khac, hoac nap
              lai file da sua ma khong mat cong da chinh. Lop trung (cung ma lop +
              hoc phan + GV + gio) bi bo qua, so luong bao lai sau khi nap. */}
          <Button variant="outline" disabled={!preview || loading} onClick={() => handleCommit("merge")}>
            {loading ? "Đang nạp…" : "Gộp thêm vào dữ liệu hiện có"}
          </Button>
          <Button variant="destructive" disabled={!preview || loading} onClick={() => handleCommit("replace")}>
            {loading ? "Đang nạp…" : `Xóa dữ liệu cũ và nạp ${s?.soLopDungDuoc ?? ""} lớp`}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function ChiTiet({ tone, tieuDe, moTa, nhom, taiVe }) {
  const mau = {
    amber: "border-amber-500/20 bg-amber-500/10",
    blue: "border-blue-500/20 bg-blue-500/10",
    red: "border-red-500/20 bg-red-500/10",
    orange: "border-orange-500/30 bg-orange-500/10",
  }[tone];

  return (
    <details className={`rounded-lg border ${mau}`} open>
      <summary className="cursor-pointer px-3 py-2 text-sm font-medium">{tieuDe}</summary>
      <div className="space-y-2.5 px-3 pb-3 text-xs">
        <p className="text-muted-foreground">{moTa}</p>
        {taiVe && (
          <a
            href={taiVe}
            className="inline-flex items-center gap-1 rounded-md border px-2 py-1 font-medium hover:bg-muted/60"
          >
            Tải danh sách này ra Excel để gửi khoa sửa
          </a>
        )}
        {(nhom || []).map((g) => (
          <div key={g.loai} className="bg-background/60 rounded-md border p-2.5">
            <p className="font-medium">
              {/* Co nhom dem TRUONG HOP chu khong dem dong (vd "5 ma lop bi dung
                  cho nhieu hoc phan") - xem fate_audit._nhom. */}
              <span className="tabular-nums">{g.so}</span> {g.donVi || "dòng"} — {g.nhan}
            </p>

            {g.chiTiet?.length > 0 && (
              <ul className="text-muted-foreground mt-1.5 max-h-28 space-y-0.5 overflow-y-auto">
                {g.chiTiet.map((c, i) => (
                  <li key={i}>
                    ・{c.text}
                    {c.so > 1 && <span className="tabular-nums"> ({c.so} dòng)</span>}
                  </li>
                ))}
              </ul>
            )}

            {g.dong?.length > 0 && (
              <p className="text-muted-foreground mt-1.5">
                <span className="font-medium">Dòng trong file:</span>{" "}
                <span className="tabular-nums">
                  {g.dong.slice(0, 30).join(", ")}
                  {g.dong.length > 30 && ` … (+${g.dong.length - 30} dòng)`}
                </span>
              </p>
            )}
          </div>
        ))}
      </div>
    </details>
  );
}
