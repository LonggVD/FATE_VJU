// Khop dung DAY_NAMES/slot_label() cua scheduler_core.py: slot = day*slotsPerDay
// + period (0-based), day 0=Thu2..6=Chu nhat. KHONG can dich chi so nhu ban
// FE_SCHEDULE goc (backend do dung C# DayOfWeek Mon=1..Sat=6, con o day
// scheduler_core.py da tu quy uoc Mon=0 giong FE luon).
export const DAY_LABELS = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"];

export function slotToDayPeriod(slot, slotsPerDay) {
  return { day: Math.floor(slot / slotsPerDay), period: slot % slotsPerDay };
}

export function dayPeriodToSlot(day, period, slotsPerDay) {
  return day * slotsPerDay + period;
}

// Bac mat do cho luoi tuan dung chung (.wkgrid trong styles.css).
//
// Thang CO GIAN theo gia tri lon nhat cua khung nhin hien tai. Ly do: ban cu cat
// cung o 4 bac, trong khi du lieu that co o toi 14 lop -> 71% so o co lop bi don
// vao cung mot bac, bang mat do gan nhu vo dung o pham vi toan khoa. Va pham vi
// khac nhau co bien do khac han (toan khoa cao diem 14, mot chuong trinh chi 6)
// nen mot thang co dinh khong the phuc vu ca hai.
//
// 5 bac la toi da ma thang blue mot mau chiu duoc tren nen trang: 6 bac thi hai
// buoc cuoi cach nhau ΔL 0.047, duoi nguong 0.06 nen mat khong tach duoc.
export const DENSITY_LEVELS = 5;

export function densityLevel(value, max = DENSITY_LEVELS) {
  if (value <= 0) return 0;
  if (max <= DENSITY_LEVELS) return Math.min(value, DENSITY_LEVELS);
  return Math.ceil((value * DENSITY_LEVELS) / max);
}

// Khoang gia tri that cua tung bac - de chu giai luon noi ro dang doc thang nao,
// thay vi chi "1 2 3 4+" mo ho.
export function densityRanges(max) {
  if (!max || max <= 0) return [];
  const n = Math.min(DENSITY_LEVELS, max);
  const out = [];
  for (let lv = 1; lv <= n; lv++) {
    let from = null;
    let to = null;
    for (let v = 1; v <= max; v++) {
      if (densityLevel(v, max) !== lv) continue;
      if (from === null) from = v;
      to = v;
    }
    if (from !== null) out.push({ level: lv, from, to, label: from === to ? `${from}` : `${from}–${to}` });
  }
  return out;
}
