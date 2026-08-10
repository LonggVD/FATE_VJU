// Phan tich ket qua check_cross_program_conflicts() thanh thong tin man hinh
// Check-trung THAT SU can de hien thi: cap lop DUNG NHAU cu the, o gio bi tranh,
// va goi y go. Backend chi tra ve feasible true/false/null cho ca 1 GV - khong
// noi ro LOP NAO dung LOP NAO, nen nguoi dung phai tu doc va so tung nhan gio.
//
// Tat ca tinh o frontend tren DUNG mo hinh cua scheduler_core.py (cung cong thuc
// overlap, cung duration tung lop) nen ket qua khong the lech voi thuat toan.
// Khong sua scheduler_core.py.

import { DAY_LABELS, slotToDayPeriod } from "./dayPeriod";

// Tran so nut cho backtracking tim "nhan chung". Du lieu that: 1 GV nhieu nhat
// vai lop, moi lop toi da 77 window -> tim thay/vet can trong vai chuc nut.
const WITNESS_NODE_BUDGET = 40000;

// Qua nhieu window thi khong the liet ke thanh cot trong ma tran Lop x Khung gio.
const WIDE_WINDOW_THRESHOLD = 6;

export function slotRangeLabel(slot, duration, slotsPerDay) {
  const { day, period } = slotToDayPeriod(slot, slotsPerDay);
  const dayLabel = DAY_LABELS[day] ?? `Ngày ${day + 1}`;
  const from = period + 1;
  const to = period + Math.max(duration, 1);
  return duration > 1 ? `${dayLabel} tiết ${from}-${to}` : `${dayLabel} tiết ${from}`;
}

// Giong het overlaps() trong check_cross_program_conflicts(): slot la chi so
// tuyet doi trong tuan, va valid_starts bao dam 1 buoi khong vat qua sang ngay
// hom sau nen so sanh tuyet doi la du.
function overlaps(a, durA, b, durB) {
  return !(a + durA <= b || b + durB <= a);
}

function allWeekStarts(duration, numDays, slotsPerDay) {
  const out = [];
  for (let d = 0; d < numDays; d++) {
    for (let p = 0; p + duration <= slotsPerDay; p++) out.push(d * slotsPerDay + p);
  }
  return out;
}

// Backtracking: chon 1 window cho moi lop sao cho khong lop nao dung nhau.
// - found=true            -> co NHAN CHUNG (1 cach xep cu the) => chac chan xep duoc
// - found=false, het nut  -> khong ket luan duoc
// - found=false, con nut  -> da vet can toan bo => chac chan BE TAC
// Manh hon vong itertools.product cua backend (bi cat o 5000 to hop) vi co tia nhanh.
function findWitness(sections) {
  const order = sections
    .map((_, i) => i)
    .sort((a, b) => sections[a].windowSlots.length - sections[b].windowSlots.length);
  const chosen = new Array(sections.length).fill(null);
  let nodes = 0;
  let budgetHit = false;

  function place(k) {
    if (k === order.length) return true;
    const idx = order[k];
    const sec = sections[idx];
    for (const w of sec.windowSlots) {
      if (nodes++ > WITNESS_NODE_BUDGET) {
        budgetHit = true;
        return false;
      }
      let ok = true;
      for (let j = 0; j < k; j++) {
        const other = order[j];
        if (overlaps(w, sec.duration, chosen[other], sections[other].duration)) {
          ok = false;
          break;
        }
      }
      if (ok) {
        chosen[idx] = w;
        if (place(k + 1)) return true;
        chosen[idx] = null;
      }
    }
    return false;
  }

  const found = place(0);
  return { found, exhausted: budgetHit, assignment: found ? chosen.slice() : null };
}

// Cap lop mà MOI to hop window deu dung nhau -> chinh la thu pham, khong the go
// bang cach doi lua chon trong so gio da bao.
function findCollidingPairs(sections, slotsPerDay) {
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
      if (!always) continue;

      // Ngay xay ra dung do - de dem "so VU dung" theo ngay, khong lan voi "so O
      // gio bi tranh" (1 vu dung cua lop 4 tiet chiem 4 o, de bi doc thanh 4 vu).
      const days = new Set();
      for (const wa of a.windowSlots) {
        for (const wb of b.windowSlots) {
          if (overlaps(wa, a.duration, wb, b.duration)) {
            days.add(slotToDayPeriod(wa, slotsPerDay).day);
            days.add(slotToDayPeriod(wb, slotsPerDay).day);
          }
        }
      }

      // Nhan gio de doc: neu ca 2 deu chot cung 1 window thi chi ghi 1 lan.
      const sameSingleWindow =
        a.windowSlots.length === 1 && b.windowSlots.length === 1 && a.windowSlots[0] === b.windowSlots[0];
      pairs.push({
        a,
        b,
        days: [...days].sort((x, y) => x - y),
        sameSingleWindow,
        whereLabel: sameSingleWindow
          ? slotRangeLabel(a.windowSlots[0], a.duration, slotsPerDay)
          : `${slotRangeLabel(a.windowSlots[0], a.duration, slotsPerDay)} ⟷ ${slotRangeLabel(
              b.windowSlots[0],
              b.duration,
              slotsPerDay,
            )}`,
      });
    }
  }
  return pairs;
}

// Voi ca be tac: lop nao neu duoc bao thay khung gio khac (tu do ca tuan) thi go
// duoc the be tac? Do chinh la viec giao vu can di lam - thay cho cau "chac chan trung".
function findRepairCandidates(sections, numDays, slotsPerDay) {
  const out = [];
  for (let i = 0; i < sections.length; i++) {
    const relaxed = sections.map((s, k) =>
      k === i ? { ...s, windowSlots: allWeekStarts(s.duration, numDays, slotsPerDay) } : s,
    );
    if (findWitness(relaxed).found) out.push(sections[i]);
  }
  return out;
}

// Luoi ngay x tiet: moi o = so lop CO THE roi vao o do. Lop "tu do ca tuan" bi
// loai khoi luoi (neu ve thi 77 window se to kin tuan va xoa sach tin hieu) -
// legend duoi luoi phai noi ro dieu nay.
function buildDensityGrid(sections, numDays, slotsPerDay) {
  const grid = Array.from({ length: numDays }, () => new Array(slotsPerDay).fill(0));
  let maxValue = 0;
  for (const s of sections) {
    if (s.isWide) continue;
    const touched = new Set();
    for (const w of s.windowSlots) {
      const { day, period } = slotToDayPeriod(w, slotsPerDay);
      for (let k = 0; k < s.duration; k++) {
        const p = period + k;
        if (day < numDays && p < slotsPerDay) touched.add(`${day}:${p}`);
      }
    }
    for (const key of touched) {
      const [day, p] = key.split(":").map(Number);
      grid[day][p] += 1;
      if (grid[day][p] > maxValue) maxValue = grid[day][p];
    }
  }
  return { grid, maxValue };
}

function analyzeOne(conflict, ctx) {
  const { numDays, slotsPerDay, defaultDuration } = ctx;

  const sections = conflict.sections.map((s) => {
    const duration = s.duration ?? defaultDuration ?? 2;
    const windowSlots = s.windowSlots ?? [];
    const weekTotal = allWeekStarts(duration, numDays, slotsPerDay).length;
    return {
      ...s,
      duration,
      windowSlots,
      isFreeChoice: weekTotal > 0 && windowSlots.length >= weekTotal,
      isWide: windowSlots.length > WIDE_WINDOW_THRESHOLD,
      isPinned: windowSlots.length === 1,
      isPending: windowSlots.length === 0,
      rangeLabels: windowSlots.map((w) => slotRangeLabel(w, duration, slotsPerDay)),
    };
  });

  const pendingSections = sections.filter((s) => s.isPending);
  const submitted = sections.filter((s) => !s.isPending);

  let status;
  let witness = null;
  let reclassifiedFromPending = false;
  let resolvedFromUndetermined = false;

  if (pendingSections.length > 0) {
    // BAY QUAN TRONG: backend tra ve feasible=False cho MOI GV co lop chua duoc
    // nop gio, vi itertools.product voi 1 danh sach rong cho ra 0 to hop nen vong
    // lap khong bao gio dat feasible=True. Do KHONG phai trung gio - do la CHUA CO
    // GIO NAO de ma trung. Phai tu danh gia rieng tren cac lop DA co gio bao.
    witness = findWitness(submitted);
    if (submitted.length === 0 || witness.found) {
      status = "PENDING";
    } else if (!witness.exhausted) {
      status = "BLOCKED"; // cac lop da bao gio tu dung nhau that
    } else {
      status = "UNDETERMINED";
    }
    reclassifiedFromPending = status !== "BLOCKED" && conflict.feasible === false;
  } else if (conflict.feasible === false) {
    // Backend da vet can toan bo to hop -> khong tu suy dien lai.
    status = "BLOCKED";
  } else if (conflict.feasible === true) {
    status = "OK";
    witness = findWitness(sections);
  } else {
    // feasible === null: backend bo qua vi qua nhieu to hop. Tia nhanh thi giai duoc.
    witness = findWitness(sections);
    if (witness.found) {
      status = "OK";
      resolvedFromUndetermined = true;
    } else if (!witness.exhausted) {
      status = "BLOCKED";
      resolvedFromUndetermined = true;
    } else {
      status = "UNDETERMINED";
    }
  }

  // Chi soi tren cac lop DA co gio bao - lop chua nop gio khong the "dung" ai.
  const collidingPairs = status === "BLOCKED" ? findCollidingPairs(submitted, slotsPerDay) : [];
  const repairCandidates = status === "BLOCKED" ? findRepairCandidates(submitted, numDays, slotsPerDay) : [];

  const culpritIds = new Set();
  collidingPairs.forEach((p) => {
    culpritIds.add(p.a.sectionId);
    culpritIds.add(p.b.sectionId);
  });
  repairCandidates.forEach((s) => culpritIds.add(s.sectionId));

  const { grid, maxValue } = buildDensityGrid(sections, numDays, slotsPerDay);

  // Cot cua ma tran Lop x Khung gio: hop cac window co the liet ke duoc.
  const columnSlots = [
    ...new Set(sections.filter((s) => !s.isWide).flatMap((s) => s.windowSlots)),
  ].sort((a, b) => a - b);

  const columns = columnSlots.map((slot) => {
    const takers = sections.filter((s) => !s.isWide && s.windowSlots.includes(slot));
    const pinnedTakers = takers.filter((s) => s.isPinned);
    return {
      slot,
      label: slotRangeLabel(slot, Math.min(...takers.map((s) => s.duration)), slotsPerDay),
      shortLabel: (() => {
        const { day, period } = slotToDayPeriod(slot, slotsPerDay);
        return `${(DAY_LABELS[day] ?? `N${day + 1}`).replace("Thứ ", "T").replace("Chủ nhật", "CN")}·${period + 1}`;
      })(),
      takerIds: takers.map((s) => s.sectionId),
      // "Tranh nhau" = >= 2 lop DA CHOT cung o nay, khong con lua chon nao khac.
      contested: pinnedTakers.length >= 2,
      pinnedCount: pinnedTakers.length,
    };
  });

  const programCount = new Set(sections.map((s) => s.program)).size;
  const coordinators = [...new Set(sections.map((s) => s.coordinator).filter(Boolean))];
  const culpritCoordinators = [
    ...new Set(sections.filter((s) => culpritIds.has(s.sectionId)).map((s) => s.coordinator).filter(Boolean)),
  ];

  return {
    key: `xc-${conflict.teacherId}`,
    teacherId: conflict.teacherId,
    teacherName: conflict.teacherName,
    isForcedConflict: conflict.isForcedConflict,
    backendFeasible: conflict.feasible,
    status,
    reclassifiedFromPending,
    resolvedFromUndetermined,
    sections,
    pendingSections,
    submittedSections: submitted,
    programCount,
    coordinators,
    culpritCoordinators,
    culpritIds,
    collidingPairs,
    repairCandidates,
    columns,
    grid,
    maxDensity: maxValue,
    freeChoiceCount: sections.filter((s) => s.isFreeChoice).length,
    witnessAssignment: witness?.assignment ?? null,
  };
}

// Xep theo do gap cua viec phai lam: dam phan lai gio > di nop gio > cho giai > khong phai lam gi.
const STATUS_ORDER = { BLOCKED: 0, PENDING: 1, UNDETERMINED: 2, OK: 3 };

export function analyzeCrossConflicts(crossConflicts = [], meta = {}) {
  const ctx = {
    numDays: meta.numDays ?? 7,
    slotsPerDay: meta.slotsPerDay ?? 12,
    defaultDuration: meta.duration ?? 2,
  };

  const items = crossConflicts
    .map((c) => analyzeOne(c, ctx))
    .sort((a, b) => STATUS_ORDER[a.status] - STATUS_ORDER[b.status] || a.teacherId - b.teacherId);

  // Danh sach VU dung chac chan (cap lop moi to hop deu trung) - de noi thanh cau
  // cu the thay vi de nguoi doc tu suy tu con so o giay.
  const collisions = items.flatMap((it) =>
    it.collidingPairs.map((p) => ({
      teacherId: it.teacherId,
      teacherName: it.teacherName,
      aId: p.a.sectionId,
      bId: p.b.sectionId,
      whereLabel: p.whereLabel,
      days: p.days ?? [],
    })),
  );

  // "Ngay nong": dem 2 thu KHAC NHAU cho moi ngay -
  //  - contendedCells: so O gio bi >= 2 lop cung nham (tin hieu chen chuc, co ca o
  //    truong hop van xep duoc)
  //  - collisionCount: so VU dung chac chan roi vao ngay do
  // 1 vu dung cua lop 4 tiet chiem 4 o -> hai con so nay khac nhau, phai tach.
  const hotDays = Array.from({ length: ctx.numDays }, (_, day) => {
    let contendedCells = 0;
    for (const it of items) {
      for (let p = 0; p < ctx.slotsPerDay; p++) {
        if ((it.grid[day]?.[p] ?? 0) >= 2) contendedCells += 1;
      }
    }
    return {
      day,
      label: (DAY_LABELS[day] ?? `Ngày ${day + 1}`).replace("Thứ ", "T").replace("Chủ nhật", "CN"),
      contendedCells,
      collisionCount: collisions.filter((c) => c.days.includes(day)).length,
    };
  });

  return {
    items,
    ctx,
    counts: {
      blocked: items.filter((i) => i.status === "BLOCKED").length,
      pending: items.filter((i) => i.status === "PENDING").length,
      undetermined: items.filter((i) => i.status === "UNDETERMINED").length,
      ok: items.filter((i) => i.status === "OK").length,
      total: items.length,
      reclassifiedFromPending: items.filter((i) => i.reclassifiedFromPending).length,
      resolvedFromUndetermined: items.filter((i) => i.resolvedFromUndetermined).length,
      pendingSectionCount: items.reduce((n, i) => n + i.pendingSections.length, 0),
    },
    hotDays,
    collisions,
    maxHot: Math.max(1, ...hotDays.map((d) => d.contendedCells)),
  };
}

export const STATUS_META = {
  BLOCKED: { label: "Bế tắc", icon: "✕", cls: "blocked", hint: "Phải đàm phán lại giờ — CP-SAT không gỡ được" },
  PENDING: { label: "Chờ nộp giờ", icon: "…", cls: "pending", hint: "Có lớp chưa được điều phối viên báo giờ — chưa đủ dữ liệu để kết luận" },
  UNDETERMINED: { label: "Chưa xác định", icon: "?", cls: "undetermined", hint: "Quá nhiều tổ hợp — để CP-SAT quyết" },
  OK: { label: "Xếp được", icon: "✓", cls: "ok", hint: "Có cách xếp không trùng giờ" },
};
