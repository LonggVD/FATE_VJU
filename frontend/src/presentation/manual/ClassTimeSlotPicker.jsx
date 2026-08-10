import { useState } from "react";
import { DAY_LABELS } from "../../adapters/dayPeriod";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

// Picker gio CHOT cho 1 LOP - khac SubmissionWindowGrid (chon nhieu ngay/nhieu o
// roi rac cho "khung gio ranh cua GV"): o day 1 lop = DUNG 1 Thu + 1 khoang Tiet
// LIEN TUC, nen dung tab-chon-ngay + click-click cap (o dau/o cuoi) thay vi luoi
// nhieu ngay. value: {day, periodStart, periodEnd} | null (null = chua chon).
//
// selectedDay TACH RIENG khoi 'value' va CHI khoi tao 1 LAN tu prop luc mount
// (khong dung useEffect dong bo lai theo value): bam 1 Thu la xong ngay do
// ngay, nhung 'value' (day+periodStart+periodEnd) chi duoc CHOT sau khi bam ca
// tiet dau VA tiet cuoi - neu dong bo selectedDay theo value.day moi lan value
// doi, luc doi Thu SAU KHI da chot 1 khoang tiet cho Thu cu se bi hieu ung phu
// day selectedDay ve lai null ngay khi onChange(null) chay (xem lich su sua
// loi o day). Component nay CHAC CHAN duoc remount moi khi doi sang sua lop
// khac hoac khi bat/tat "Tu xep gio" (component cha chi render co dieu kien),
// nen useState 1 lan la du, khong can dong bo them.
export default function ClassTimeSlotPicker({ numDays, slotsPerDay, value, onChange, disabled }) {
  const [anchor, setAnchor] = useState(null);
  const [selectedDay, setSelectedDay] = useState(value?.day ?? null);
  const days = DAY_LABELS.slice(0, numDays);

  const pickDay = (day) => {
    if (disabled) return;
    setAnchor(null);
    setSelectedDay(day);
    if (value && value.day !== day) onChange(null); // doi sang ngay khac -> huy khoang tiet cua ngay cu
  };

  const clickPeriod = (period) => {
    if (disabled || selectedDay === null) return;
    if (anchor === null) {
      setAnchor(period);
      onChange({ day: selectedDay, periodStart: period, periodEnd: period });
      return;
    }
    const periodStart = Math.min(anchor, period);
    const periodEnd = Math.max(anchor, period);
    onChange({ day: selectedDay, periodStart, periodEnd });
    setAnchor(null);
  };

  const clear = () => {
    setAnchor(null);
    setSelectedDay(null);
    onChange(null);
  };

  const committedForSelectedDay = value && value.day === selectedDay ? value : null;

  return (
    <div className="bg-muted/40 space-y-2.5 rounded-lg border p-3">
      <div className="flex flex-wrap gap-1">
        {days.map((label, day) => (
          <button
            key={day}
            type="button"
            disabled={disabled}
            onClick={() => pickDay(day)}
            className={cn(
              "rounded-md border px-2.5 py-1 text-xs font-medium transition-colors disabled:opacity-50",
              selectedDay === day
                ? "border-primary bg-primary text-primary-foreground"
                : "bg-background hover:bg-accent hover:text-accent-foreground",
            )}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="flex flex-wrap gap-1">
        {Array.from({ length: slotsPerDay }, (_, i) => i + 1).map((period) => {
          const inRange = committedForSelectedDay
            && period >= committedForSelectedDay.periodStart && period <= committedForSelectedDay.periodEnd;
          const isAnchor = anchor === period;
          return (
            <button
              key={period}
              type="button"
              disabled={disabled || selectedDay === null}
              onClick={() => clickPeriod(period)}
              title={`Tiết ${period}`}
              className={cn(
                "size-8 rounded-md border text-xs font-medium tabular-nums transition-colors disabled:opacity-40",
                inRange
                  ? "border-primary bg-primary text-primary-foreground"
                  : isAnchor
                    ? "border-primary text-primary bg-primary/10"
                    : "bg-background hover:bg-accent hover:text-accent-foreground",
              )}
            >
              {period}
            </button>
          );
        })}
      </div>

      <div className="flex flex-wrap items-center justify-between gap-2">
        {selectedDay === null ? (
          <span className="text-muted-foreground text-xs">
            Chọn Thứ trước, rồi bấm tiết đầu → tiết cuối.
          </span>
        ) : committedForSelectedDay ? (
          <span className="text-xs">
            Đã chọn: <strong>{days[selectedDay]}</strong>, tiết{" "}
            <strong>
              {committedForSelectedDay.periodStart}–{committedForSelectedDay.periodEnd}
            </strong>
            {anchor !== null && (
              <span className="text-muted-foreground"> (bấm tiết cuối để chốt)</span>
            )}
          </span>
        ) : (
          <span className="text-muted-foreground text-xs">Bấm tiết đầu.</span>
        )}
        {committedForSelectedDay && !disabled && (
          <Button type="button" variant="ghost" size="sm" onClick={clear}>
            Xóa giờ
          </Button>
        )}
      </div>
    </div>
  );
}
