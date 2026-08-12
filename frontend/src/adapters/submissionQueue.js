// Phan loai lai du lieu cho man hinh "Khung gio da bao".
//
// Ban cu do TAT CA sections vao 1 bang mang tieu de "Da nop (N)" va tin vao
// data.pendingSections de biet con viec hay khong. Ca hai deu sai:
//
//  1. submissions[] chua CA lop co huu (RESIDENT). Lop co huu khong co dieu phoi
//     vien nop gio - Giai doan 2 tu chon gio - nen chung luon hien "—". Tren du
//     lieu that chung chiem 108/188 dong, keo con so "Da nop" lech han.
//  2. load_real_fate_data() dat cung pending_section_ids = [] (scheduler_core.py
//     :743), nen voi du lieu that danh sach cho LUON rong -> man hinh bao "khong
//     con buoi nao cho nop gio" va an luon form nop gio, du thuc te van con lop
//     chua bao gio (dang de "tu do ca tuan").
//
// Nen trang thai duoc tinh lai o day tu chinh windowSlots, khong phu thuoc vao
// pendingSections nua.

import { slotToDayPeriod } from "./dayPeriod";

const WEEK_COVER_RATIO = 0.9;

export const SUB_STATE = {
  SET: "SET", // da chot khung gio cu the
  UNREPORTED: "UNREPORTED", // chua co gio thuc su (rong, hoac dang de tu do ca tuan)
};

// `tone` khop bo 6 tone cua design system VJU (xem constants/tones.js) - thay
// cho `cls` cu von tro toi cac class .sq-state.set/.unreported trong styles.css.
export const SUB_STATE_META = {
  SET: { label: "Đã chốt giờ", icon: "✓", cls: "set", tone: "emerald" },
  UNREPORTED: { label: "Chưa báo giờ", icon: "…", cls: "unreported", tone: "slate" },
};

function weekStartCount(duration, numDays, slotsPerDay) {
  return numDays * Math.max(slotsPerDay - duration + 1, 0);
}

export function analyzeSubmissions(data) {
  const numDays = data.numDays ?? 7;
  const slotsPerDay = data.slotsPerDay ?? 12;
  const defaultDuration = data.duration ?? 2;
  const all = data.submissions ?? [];

  // Neu backend chua gui teacherType (ban cu), tra ve tu danh sach teachers.
  const typeById = new Map((data.teachers ?? []).map((t) => [t.id, t.type]));

  const rows = [];
  let residentCount = 0;

  for (const s of all) {
    const teacherType = s.teacherType ?? typeById.get(s.teacherId);
    if (teacherType !== "GUEST") {
      residentCount += 1;
      continue;
    }
    const duration = s.duration ?? defaultDuration;
    const windowSlots = s.windowSlots ?? [];
    const weekTotal = weekStartCount(duration, numDays, slotsPerDay);
    // "Tu do ca tuan" = chua ai bao gio, backend chi gan tam toan bo tuan.
    const isFreeChoice = weekTotal > 0 && windowSlots.length >= Math.floor(weekTotal * WEEK_COVER_RATIO);
    const isEmpty = windowSlots.length === 0;

    rows.push({
      ...s,
      duration,
      windowSlots,
      isFreeChoice,
      isEmpty,
      state: isEmpty || isFreeChoice ? SUB_STATE.UNREPORTED : SUB_STATE.SET,
      reason: isEmpty
        ? "Điều phối viên chưa nộp"
        : isFreeChoice
          ? "Chưa khai giờ rảnh — đang để tự do cả tuần"
          : null,
    });
  }

  const queue = rows.filter((r) => r.state === SUB_STATE.UNREPORTED);
  const done = rows.filter((r) => r.state === SUB_STATE.SET);

  // Tien do theo dieu phoi vien - vi day la man hinh cua ho, va viec con lai
  // luon thuoc ve mot nguoi cu the.
  const byCoord = new Map();
  for (const r of rows) {
    const key = r.coordinator || "(không rõ)";
    const acc = byCoord.get(key) ?? { coordinator: key, total: 0, done: 0 };
    acc.total += 1;
    if (r.state === SUB_STATE.SET) acc.done += 1;
    byCoord.set(key, acc);
  }
  const coordinators = [...byCoord.values()]
    .map((c) => ({ ...c, missing: c.total - c.done, pct: c.total ? Math.round((c.done / c.total) * 100) : 0 }))
    .sort((a, b) => b.missing - a.missing || a.coordinator.localeCompare(b.coordinator));

  const programs = [...new Set(rows.map((r) => r.programLabel).filter(Boolean))].sort((a, b) =>
    a.localeCompare(b),
  );

  return {
    rows,
    queue,
    residentCount,
    doneCount: done.length,
    guestCount: rows.length,
    coordinators,
    coordinatorsBehind: coordinators.filter((c) => c.missing > 0),
    programs,
    numDays,
    slotsPerDay,
  };
}

function overlaps(a, durA, b, durB) {
  return !(a + durA <= b || b + durB <= a);
}

// Cap buoi cua CUNG 1 GV ma MOI to hop khung gio deu trung -> khong co duong tranh.
//
// Vi sao phai kiem o day: man "Check trung lien chuong trinh" co y chi soi GV day
// >= 2 chuong trinh (scheduler_core.py:216), vi bai toan goc la "hai dieu phoi vien
// khong thay nhau". Nhung tren du lieu that, 4/5 vu trung that lai la GV day CUNG
// MOT chuong trinh - cung mot dieu phoi vien bao hai lop vao cung gio. Nhung ca do
// khong man nao bat truoc khi giai. Man tra cuu theo GV soi theo NGUOI, khong quan
// tam chuong trinh, nen la cho duy nhat bat duoc ca 5.
function findClashPairs(sections) {
  const pairs = [];
  for (let i = 0; i < sections.length; i++) {
    for (let j = i + 1; j < sections.length; j++) {
      const a = sections[i];
      const b = sections[j];
      if (!a.windowSlots.length || !b.windowSlots.length) continue;
      let always = true;
      for (const wa of a.windowSlots) {
        for (const wb of b.windowSlots) {
          if (!overlaps(wa, a.duration, wb, b.duration)) {
            always = false;
            break;
          }
        }
        if (!always) break;
      }
      if (always) pairs.push({ a, b });
    }
  }
  return pairs;
}

// Gio da bao CUA MOT GIANG VIEN. Du lieu goc chi to chuc theo BUOI, nen muon xem
// "GV nay bao la day duoc nhung gio nao" thi phai gop cac buoi cua ho lai roi ve
// lai len luoi tuan - viec khong man nao dang lam.
export function teacherReportedHours(data, teacherId) {
  const sq = analyzeSubmissions(data);
  const tid = Number(teacherId);
  const sections = sq.rows.filter((r) => r.teacherId === tid);
  const set = sections.filter((r) => r.state === SUB_STATE.SET);
  const unreported = sections.filter((r) => r.state === SUB_STATE.UNREPORTED);

  // Moi o = so buoi DA CHOT GIO co the roi vao o do. Buoi dang "tu do ca tuan"
  // khong ve: no se to kin ca tuan va xoa sach tin hieu.
  const grid = Array.from({ length: sq.numDays }, () => new Array(sq.slotsPerDay).fill(0));
  let reportedCells = 0;

  for (const r of set) {
    const touched = new Set();
    for (const w of r.windowSlots) {
      const { day, period } = slotToDayPeriod(w, sq.slotsPerDay);
      for (let k = 0; k < r.duration; k++) {
        const p = period + k;
        if (day < sq.numDays && p < sq.slotsPerDay) touched.add(`${day}:${p}`);
      }
    }
    for (const key of touched) {
      const [d, p] = key.split(":").map(Number);
      if (grid[d][p] === 0) reportedCells += 1;
      grid[d][p] += 1;
    }
  }

  // Cac o giờ nam trong mot vu trung -> to canh bao thay vi mau mat do binh thuong.
  const clashPairs = findClashPairs(set);
  const clashCells = new Set();
  const clashSectionIds = new Set();
  for (const p of clashPairs) {
    clashSectionIds.add(p.a.sectionId);
    clashSectionIds.add(p.b.sectionId);
    for (const sec of [p.a, p.b]) {
      for (const w of sec.windowSlots) {
        const { day, period } = slotToDayPeriod(w, sq.slotsPerDay);
        for (let k = 0; k < sec.duration; k++) {
          const pp = period + k;
          if (day < sq.numDays && pp < sq.slotsPerDay) clashCells.add(`${day}:${pp}`);
        }
      }
    }
  }

  return {
    sections,
    set,
    unreported,
    grid,
    reportedCells,
    clashPairs,
    clashCells,
    clashSectionIds,
    numDays: sq.numDays,
    slotsPerDay: sq.slotsPerDay,
  };
}

export function filterRows(rows, { search, program, state }) {
  const q = (search ?? "").trim().toLowerCase();
  return rows.filter((r) => {
    if (state && r.state !== state) return false;
    if (program && r.programLabel !== program) return false;
    if (!q) return true;
    return (
      String(r.sectionId) === q ||
      (r.teacherName ?? "").toLowerCase().includes(q) ||
      (r.courseName ?? "").toLowerCase().includes(q) ||
      (r.coordinator ?? "").toLowerCase().includes(q)
    );
  });
}
