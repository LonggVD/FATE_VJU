import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Check, Pencil, X } from "lucide-react";
import { DAY_LABELS } from "../../adapters/dayPeriod";
import { submissionToWindowSlots, windowSlotsToSelectedCellsMap } from "../../adapters/submissionAdapter";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

// Luoi khai "gio co the day" trong tuan. Hai che do RO RANG, khong nhap lam mot:
//
//   readOnly  - chi hien gio DA LUU tren server. Khong bam duoc, khong co nut.
//   sua       - lam viec tren mot ban NHAP rieng; chi khi bam "Lưu" moi goi API,
//               "Hủy" tra ve dung trang thai da luu.
//
// Ban truoc luon o che do sua nen khong phan biet duoc dau la du lieu that, dau
// la thao tac dang do: o chon GV ghi "8 ô rảnh" trong khi luoi ghi "Đã chọn 0"
// (vi vua bam "Xóa tất cả" ma chua luu) - nhin vao khong biet tin cai nao.
//
// Mau o da chon giu xanh la (emerald) - day la "co the day", khong phai mau
// thuong hieu; do da danh cho canh bao/trung gio o cac luoi khac.
//
// allowEmpty: cho phep LUU danh sach rong. Mac dinh tat vi o man "Khung giờ đã
// báo" nop rong la vo nghia (khong con lua chon nao de solver xep). Rieng trang
// "Giờ rảnh GV" thi can bat: giao vu phai xoa duoc gio da khai nham cua 1 GV.
export default function SubmissionWindowGrid({
  numDays,
  slotsPerDay,
  initialSlots = [],
  onSave,
  onCancel,
  saving,
  disabled,
  readOnly = false,
  allowEmpty = false,
  saveLabel,
}) {
  const [grid, setGrid] = useState({});
  // Keo chuot quet mot VUNG CHU NHAT: giao vu thuong ranh nguyen buoi ("T2-T6
  // tiet 1-4"), bat tung o mot la 20 cu click. Giu trong ref vi doi lien tuc
  // theo con tro, khong can re-render moi lan.
  const dragRef = useRef(null);
  const [dragBox, setDragBox] = useState(null);

  const locked = readOnly || disabled || saving;

  useEffect(() => {
    setGrid(windowSlotsToSelectedCellsMap(initialSlots, slotsPerDay));
  }, [initialSlots, slotsPerDay]);

  const days = DAY_LABELS.slice(0, numDays).map((label, idx) => ({
    idx,
    label,
    short: label.replace("Thứ ", "T").replace("Chủ nhật", "CN"),
  }));
  const periods = Array.from({ length: slotsPerDay }, (_, i) => i);

  const commitDrag = useCallback(() => {
    const drag = dragRef.current;
    dragRef.current = null;
    setDragBox(null);
    if (!drag) return;
    const { anchor, head, value } = drag;
    setGrid((prev) => {
      const next = { ...prev };
      for (let d = Math.min(anchor.d, head.d); d <= Math.max(anchor.d, head.d); d++) {
        for (let p = Math.min(anchor.p, head.p); p <= Math.max(anchor.p, head.p); p++) {
          next[`${d}-${p}`] = value;
        }
      }
      return next;
    });
  }, []);

  // Nha chuot NGOAI luoi van phai chot vung dang quet - neu chi nghe pointerup
  // tren o thi keo ra ngoai roi tha se ket dinh o trang thai dang keo.
  useEffect(() => {
    if (!dragBox) return;
    window.addEventListener("pointerup", commitDrag);
    window.addEventListener("pointercancel", commitDrag);
    return () => {
      window.removeEventListener("pointerup", commitDrag);
      window.removeEventListener("pointercancel", commitDrag);
    };
  }, [dragBox, commitDrag]);

  const startDrag = (d, p) => {
    if (locked) return;
    const value = !grid[`${d}-${p}`];
    dragRef.current = { anchor: { d, p }, head: { d, p }, value };
    setDragBox({ d0: d, p0: p, d1: d, p1: p, value });
  };

  const extendDrag = (d, p) => {
    const drag = dragRef.current;
    if (!drag) return;
    drag.head = { d, p };
    setDragBox({
      d0: Math.min(drag.anchor.d, d), p0: Math.min(drag.anchor.p, p),
      d1: Math.max(drag.anchor.d, d), p1: Math.max(drag.anchor.p, p),
      value: drag.value,
    });
  };

  // Ban phim khong co "keo" - Space/Enter bat-tat DUNG o dang focus. Khong tai
  // dung startDrag o day vi no mo mot vung dang quet ma khong bao gio co
  // pointerup de chot lai.
  const toggleCell = (d, p) => {
    if (locked) return;
    setGrid((prev) => ({ ...prev, [`${d}-${p}`]: !prev[`${d}-${p}`] }));
  };

  // Bam nhan hang/cot = bat-tat ca hang/cot do. "Rảnh cả ngày thứ 4" hoac "kín
  // tiết 1 mọi ngày" la hai kieu khai pho bien nhat, khong nen bat nguoi dung
  // keo tay tung lan.
  const toggleDay = (d) => {
    if (locked) return;
    const allOn = periods.every((p) => grid[`${d}-${p}`]);
    setGrid((prev) => {
      const next = { ...prev };
      periods.forEach((p) => { next[`${d}-${p}`] = !allOn; });
      return next;
    });
  };

  const togglePeriod = (p) => {
    if (locked) return;
    const allOn = days.every((d) => grid[`${d.idx}-${p}`]);
    setGrid((prev) => {
      const next = { ...prev };
      days.forEach((d) => { next[`${d.idx}-${p}`] = !allOn; });
      return next;
    });
  };

  const cellOn = (d, p) => {
    if (dragBox && d >= dragBox.d0 && d <= dragBox.d1 && p >= dragBox.p0 && p <= dragBox.p1) {
      return dragBox.value;
    }
    return !!grid[`${d}-${p}`];
  };

  const selectedCount = useMemo(() => {
    let n = 0;
    for (const d of days) for (const p of periods) if (cellOn(d.idx, p)) n++;
    return n;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [grid, dragBox, numDays, slotsPerDay]);

  // So SANH TAP HOP chu khong so dem: bo 1 o roi tick 1 o khac van la co thay
  // doi chua luu, du tong van bang nhau.
  const dirty = useMemo(() => {
    if (readOnly) return false;
    const saved = new Set(initialSlots);
    if (saved.size !== selectedCount) return true;
    for (const d of days) {
      for (const p of periods) {
        if (cellOn(d.idx, p) && !saved.has(d.idx * slotsPerDay + p)) return true;
      }
    }
    return false;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [readOnly, initialSlots, grid, dragBox, selectedCount, numDays, slotsPerDay]);

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs">
        <span className="text-muted-foreground inline-flex items-center gap-1.5">
          <span className="border-input bg-background size-3 rounded-[3px] border" aria-hidden="true" />
          {readOnly ? "Không rảnh" : "Chưa chọn"}
        </span>
        <span className="text-muted-foreground inline-flex items-center gap-1.5">
          <span className="size-3 rounded-[3px] bg-emerald-500" aria-hidden="true" />
          Có thể dạy
        </span>
        <span className="ml-auto inline-flex items-center gap-2">
          {dirty && (
            <span className="rounded-md bg-amber-500/15 px-2 py-0.5 font-medium text-amber-700">
              chưa lưu
            </span>
          )}
          <span className="font-medium text-emerald-700 tabular-nums">
            {selectedCount} ô
          </span>
        </span>
      </div>

      <div className="overflow-x-auto">
        <div
          className={cn(
            "grid min-w-max overflow-hidden rounded-lg border select-none",
            !locked && "cursor-pointer",
          )}
          style={{ gridTemplateColumns: `3.5rem repeat(${numDays}, minmax(2.75rem, 1fr))` }}
        >
          <div className="bg-muted/60 text-muted-foreground border-b px-2 py-1.5 text-[11px] font-semibold">
            Tiết
          </div>
          {days.map((d) => (
            <button
              key={d.idx}
              type="button"
              disabled={locked}
              title={locked ? undefined : `Bật/tắt cả ${d.label}`}
              onClick={() => toggleDay(d.idx)}
              className={cn(
                "bg-muted/60 text-muted-foreground border-b border-l px-1 py-1.5 text-center text-[11px] font-semibold",
                !locked && "hover:bg-muted hover:text-foreground",
              )}
            >
              {d.short}
            </button>
          ))}

          {periods.map((p) => (
            <RowCells
              key={p}
              period={p}
              days={days}
              cellOn={cellOn}
              locked={locked}
              onTogglePeriod={togglePeriod}
              onToggleCell={toggleCell}
              onStartDrag={startDrag}
              onExtendDrag={extendDrag}
              lastRow={p === slotsPerDay - 1}
            />
          ))}
        </div>
      </div>

      {!readOnly && (
        <div className="flex flex-wrap items-center gap-2">
          <p className="text-muted-foreground text-xs">
            Kéo để quét cả vùng · bấm nhãn <strong className="text-foreground">T2…CN</strong> hoặc{" "}
            <strong className="text-foreground">số tiết</strong> để bật/tắt cả hàng
          </p>
          <div className="ml-auto flex flex-wrap items-center gap-2">
            <Button type="button" variant="ghost" size="sm" disabled={locked} onClick={() => setGrid({})}>
              <X className="size-4" />
              Bỏ chọn hết
            </Button>
            {onCancel && (
              <Button type="button" variant="outline" size="sm" disabled={saving} onClick={onCancel}>
                Hủy
              </Button>
            )}
            {!disabled && (
              <Button
                type="button"
                size="sm"
                disabled={saving || (!allowEmpty && selectedCount === 0)}
                onClick={() => onSave(submissionToWindowSlots(grid, slotsPerDay))}
              >
                {saving
                  ? "Đang lưu…"
                  : saveLabel
                    ? saveLabel(selectedCount)
                    : `Nộp ${selectedCount} khung giờ`}
              </Button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function RowCells({ period, days, cellOn, locked, onTogglePeriod, onToggleCell, onStartDrag, onExtendDrag, lastRow }) {
  return (
    <>
      <button
        type="button"
        disabled={locked}
        title={locked ? undefined : `Bật/tắt tiết ${period + 1} cả tuần`}
        onClick={() => onTogglePeriod(period)}
        className={cn(
          "bg-muted/60 text-muted-foreground px-2 py-1 text-left text-[11px] tabular-nums",
          !lastRow && "border-b",
          !locked && "hover:bg-muted hover:text-foreground",
        )}
      >
        Tiết {period + 1}
      </button>
      {days.map((d) => {
        const on = cellOn(d.idx, period);
        return (
          <div
            key={d.idx}
            role="checkbox"
            tabIndex={locked ? -1 : 0}
            aria-checked={on}
            aria-label={`${d.label} tiết ${period + 1}`}
            onPointerDown={(e) => {
              if (locked) return;
              e.preventDefault();
              onStartDrag(d.idx, period);
            }}
            onPointerEnter={() => onExtendDrag(d.idx, period)}
            onKeyDown={(e) => {
              if (locked || (e.key !== " " && e.key !== "Enter")) return;
              e.preventDefault();
              onToggleCell(d.idx, period);
            }}
            className={cn(
              "flex h-7 touch-none items-center justify-center border-l transition-colors",
              !lastRow && "border-b",
              on ? "bg-emerald-500 text-white" : "bg-background",
              !locked && !on && "hover:bg-emerald-500/20",
              !locked && on && "hover:bg-emerald-600",
              locked && "cursor-default",
            )}
          >
            {on && <Check className="size-3.5" aria-hidden="true" />}
          </div>
        );
      })}
    </>
  );
}

/** Nut "Chỉnh sửa" dung chung cho cac man dat luoi nay o che do readOnly. */
export function EditAvailabilityButton({ onClick, disabled, children = "Chỉnh sửa" }) {
  return (
    <Button type="button" variant="outline" size="sm" disabled={disabled} onClick={onClick}>
      <Pencil className="size-4" />
      {children}
    </Button>
  );
}
