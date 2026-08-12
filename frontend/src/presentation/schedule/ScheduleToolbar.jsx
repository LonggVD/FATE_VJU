import { LayoutGrid, Maximize2, Minimize2, RotateCcw, Rows3, Save } from "lucide-react";
import { SCOPE } from "../../adapters/scheduleView";
import { COLOR_BY_OPTIONS } from "../../adapters/colorGrouping";
import { FilterSelect } from "@/components/shared/filter-select";
import { ListSearch } from "@/components/shared/list-search";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { NativeSelect } from "@/components/ui/native-select";
import { cn } from "@/lib/utils";

// THANH LOC + HANH DONG cua man thoi khoa bieu. Mot khoi thuan giao dien: nhan
// bo loc hien tai, tra ve bo loc moi qua set(); khong tu doc AppDataContext,
// khong biet gi ve luoi hay hop thu.

// mm:dd/mm cua moc hoan tac - " lúc 14:32 ngày 05/08".
function nhanGio(at) {
  return at ? ` lúc ${at.slice(11, 16)} ngày ${at.slice(8, 10)}/${at.slice(5, 7)}` : "";
}

export default function ScheduleToolbar({
  f, set, view, data, canEdit, loading, guestResult, residentResult,
  mode, onModeChange, fullscreen, onFullscreenChange, onSaveSchedule, onHoanTac,
}) {
  const moc = data.hoanTac;

  return (
    <div className="bg-card flex flex-wrap items-center gap-2 rounded-xl border p-3 shadow-sm">
      <div className="flex items-center gap-2">
        <Label htmlFor="sv-scope" className="text-muted-foreground text-xs">
          Xem
        </Label>
        <NativeSelect
          id="sv-scope"
          value={f.scope}
          onChange={(e) => set({ scope: e.target.value, scopeValue: "" })}
        >
          <option value={SCOPE.ALL}>Toàn khoa</option>
          <option value={SCOPE.PROGRAM}>Theo chương trình</option>
          <option value={SCOPE.COHORT}>Theo khoá</option>
          <option value={SCOPE.TEACHER}>Theo giảng viên</option>
        </NativeSelect>
      </div>

      {/* Hai danh sach nay dai (19 chuong trinh, hang chuc GV) nen dung
          FilterSelect co o tim; scopeValue rong = khong loc, dung bang nghia
          "Tat ca" ma FilterSelect hien cho value===null. */}
      {f.scope === SCOPE.PROGRAM && (
        <FilterSelect
          label="Tất cả chương trình"
          searchable
          value={f.scopeValue || null}
          options={view.programs}
          onChange={(v) => set({ scopeValue: v ?? "" })}
        />
      )}

      {/* Khoa (cot "Khóa" cua bang du lieu hoc phan, vd VJU2026) - in TKB cho
          mot khoa la viec thuong lam, truoc day phai loc tay tung chuong trinh. */}
      {f.scope === SCOPE.COHORT && (
        <FilterSelect
          label="Tất cả khoá"
          searchable
          value={f.scopeValue || null}
          options={view.cohorts}
          onChange={(v) => set({ scopeValue: v ?? "" })}
        />
      )}

      {f.scope === SCOPE.TEACHER && (
        <FilterSelect
          label="Tất cả giảng viên"
          searchable
          value={f.scopeValue ? String(f.scopeValue) : null}
          options={view.teachers.map((t) => ({ value: String(t.id), label: t.name }))}
          onChange={(v) => set({ scopeValue: v ?? "" })}
        />
      )}

      <div className="flex items-center gap-3">
        <span className="text-muted-foreground text-xs">Lớp</span>
        <Label htmlFor="sv-guest" className="text-sm font-normal">
          <Checkbox
            id="sv-guest"
            checked={f.guest}
            onCheckedChange={(v) => set({ guest: v === true })}
          />
          Thỉnh giảng
        </Label>
        <Label htmlFor="sv-resident" className="text-sm font-normal">
          <Checkbox
            id="sv-resident"
            checked={f.resident}
            onCheckedChange={(v) => set({ resident: v === true })}
          />
          Cơ hữu
        </Label>
      </div>

      <ListSearch
        value={f.search}
        onChange={(v) => set({ search: v })}
        placeholder="Tìm môn, giảng viên, #id"
        className="w-full sm:w-64"
      />

      <Label htmlFor="sv-problems" className="text-sm font-normal">
        <Checkbox
          id="sv-problems"
          checked={f.onlyProblems}
          onCheckedChange={(v) => set({ onlyProblems: v === true })}
        />
        Chỉ buổi có vấn đề
      </Label>

      {mode === "grid" && (
        <NativeSelect
          value={f.colorBy}
          onChange={(e) => set({ colorBy: e.target.value })}
        >
          {COLOR_BY_OPTIONS.map((o) => (
            <option key={o.key} value={o.key}>Tô màu: {o.label}</option>
          ))}
        </NativeSelect>
      )}

      <div className="ml-auto flex items-center gap-2">
        {canEdit && (guestResult || residentResult) && (
          <Button
            size="sm"
            disabled={loading}
            onClick={() => {
              if (window.confirm(
                "Ghi đè Thứ, Tiết bắt đầu/kết thúc và Trạng thái của TOÀN BỘ lớp đang xếp vào Dữ liệu học phần?",
              )) {
                onSaveSchedule();
              }
            }}
            title="Cập nhật Thứ, Tiết bắt đầu/kết thúc và trạng thái vào Dữ liệu học phần"
          >
            <Save className="size-4" />
            Lưu thời khoá biểu
          </Button>
        )}
        {/* HUY THAY DOI - cap doi cua "Luu": tra CA MAN ve dung lan luu gan
            nhat. Khac "Bo ghim" (mot buoi) va nut "Huy" o banner keo-tha (mot
            buoi CHUA luu). Mo khi chua co moc nao. */}
        {canEdit && (
          <Button
            variant="outline"
            size="sm"
            disabled={loading || !moc}
            onClick={() => {
              if (!moc) return;
              if (window.confirm(
                `Huỷ mọi thay đổi và quay về ${moc.nhan}${nhanGio(moc.at)}?`
                + "\n\nGiờ của mọi lớp, các ghim tay, trạng thái chốt lịch, nhóm học chung "
                + "và lưới đang hiện đều trở về đúng lúc đó. Không hoàn tác lại được.",
              )) {
                onHoanTac();
              }
            }}
            title={moc
              ? `Quay về ${moc.nhan}${moc.at ? ` lúc ${moc.at.slice(11, 16)}` : ""}`
                + " — giờ, ghim, chốt lịch, nhóm học chung và lưới đều trở về đúng lúc đó."
              : "Chưa có mốc nào để quay về. Mốc được ghi khi nạp file và mỗi lần lưu thời khoá biểu."}
          >
            <RotateCcw className="size-4" />
            Huỷ thay đổi
          </Button>
        )}
        {/* Bo chuyen che do dang segmented - cung ngon ngu voi TabsList. */}
        <div className="bg-muted inline-flex h-9 items-center rounded-lg p-0.75">
          {[
            { key: "grid", label: "Lưới", icon: LayoutGrid },
            { key: "table", label: "Bảng", icon: Rows3 },
          ].map((m) => (
            <button
              key={m.key}
              type="button"
              onClick={() => onModeChange(m.key)}
              aria-pressed={mode === m.key}
              className={cn(
                "inline-flex h-full items-center gap-1.5 rounded-md px-2.5 text-sm font-medium transition-colors",
                mode === m.key
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              <m.icon className="size-4" />
              {m.label}
            </button>
          ))}
        </div>

        {mode === "grid" && (
          <Button
            variant={fullscreen ? "default" : "outline"}
            size="sm"
            onClick={() => onFullscreenChange(!fullscreen)}
            title={
              canEdit
                ? "Toàn màn hình — thẻ hiện đủ thông tin, kéo-thả được để sửa tay"
                : "Toàn màn hình — thẻ hiện đủ mã lớp, môn, giảng viên, phòng"
            }
          >
            {fullscreen ? <Minimize2 className="size-4" /> : <Maximize2 className="size-4" />}
            {fullscreen ? "Thoát" : "Toàn màn hình"}
          </Button>
        )}
      </div>
    </div>
  );
}
