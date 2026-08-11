// Nguon du lieu cho man "Thoi khoa bieu" gop. Mot bo loc duy nhat quyet dinh
// nhin thay gi - thay cho viec truoc day moi pham vi la mot man rieng:
//   Giai doan 1  = layers{guest} + phase view
//   Giai doan 2  = layers{guest+resident}
//   Tra cuu GV   = scope{teacher}
//
// Bang mat do (navigator) cung tinh o day: no la thu bu lai cho viec luoi phai
// cuon khi the hien du thong tin ca hoc.

import { lessonToTimetableItem, mergeGuestAndResidentLessons } from "./lessonAdapter";

export const SCOPE = { ALL: "all", PROGRAM: "program", TEACHER: "teacher" };

export const DEFAULT_FILTER = {
  scope: SCOPE.ALL,
  scopeValue: "",
  guest: true,
  resident: true,
  search: "",
  colorBy: "status",
  onlyProblems: false,
};

// Buoi "co van de" = nam trong bat ky vu nao cua hop thu.
function buildProblemSectionMap(inbox) {
  const map = new Map();
  for (const it of inbox?.items ?? []) {
    for (const sid of it.sectionIds) {
      if (!map.has(sid)) map.set(sid, []);
      map.get(sid).push(it);
    }
  }
  return map;
}

export function buildScheduleView({ data, guestResult, residentResult, inbox, filter }) {
  const f = { ...DEFAULT_FILTER, ...(filter ?? {}) };
  const numDays = data?.numDays ?? 7;
  const slotsPerDay = data?.slotsPerDay ?? 12;

  const all = mergeGuestAndResidentLessons(
    guestResult?.lessons ?? [],
    residentResult?.lessons ?? [],
  ).map((l) => (l.id != null ? l : lessonToTimetableItem(l)));

  const problemMap = buildProblemSectionMap(inbox);
  // Metadata ghim (reason/problem/pinFailed) nam o result.overrides[sid], KHONG
  // nam tren tung lesson - backend gan rieng vi 1 buoi co the dang trong
  // 'unplaced' (chua co lesson) luc override duoc tao. Ghep lai o day theo dung
  // phase cua tung buoi (GUEST doc tu guestResult, RESIDENT tu residentResult).
  const guestOverrides = guestResult?.overrides ?? {};
  const residentOverrides = residentResult?.overrides ?? {};

  // Ma lop hoc phan (vd "CSE3003-1") de hien THAY CHO "#<id noi bo>" tren the/
  // popup/hop thoai - id chi co nghia voi backend, giao vu nhan dien lop qua ma
  // lop. lesson (tu guestResult/residentResult) khong tu co field nay, phai
  // noi voi data.classes (bang mirror) qua sectionId.
  const classCodeById = new Map((data?.classes ?? []).map((c) => [c.sectionId, c.classCode]));

  const withFlags = all.map((l) => {
    const ovMap = l.teacherType === "RESIDENT" ? residentOverrides : guestOverrides;
    const override = ovMap[l.id] ?? ovMap[String(l.id)] ?? null;
    return {
      ...l,
      classCode: classCodeById.get(l.id) || null,
      problems: problemMap.get(l.id) ?? [],
      hasProblem: problemMap.has(l.id),
      override,
      isPinned: !!override,
    };
  });

  const q = f.search.trim().toLowerCase();
  const lessons = withFlags.filter((l) => {
    if (l.teacherType === "GUEST" && !f.guest) return false;
    if (l.teacherType === "RESIDENT" && !f.resident) return false;
    if (f.scope === SCOPE.PROGRAM && f.scopeValue && l.programLabel !== f.scopeValue) return false;
    if (f.scope === SCOPE.TEACHER && f.scopeValue && String(l.teacherId) !== String(f.scopeValue)) return false;
    if (f.onlyProblems && !l.hasProblem) return false;
    if (!q) return true;
    return (
      String(l.id) === q ||
      (l.courseName ?? "").toLowerCase().includes(q) ||
      (l.teacherName ?? "").toLowerCase().includes(q) ||
      (l.programLabel ?? "").toLowerCase().includes(q)
    );
  });

  // --- Bang mat do: moi o = so buoi DANG HIEN dang dien ra o thoi diem do ---
  const grid = Array.from({ length: numDays }, () => new Array(slotsPerDay).fill(0));
  const idsAt = Array.from({ length: numDays }, () =>
    Array.from({ length: slotsPerDay }, () => []),
  );
  for (const l of lessons) {
    if (l.day == null || l.period == null) continue;
    for (let k = 0; k < (l.duration || 1); k++) {
      const p = l.period + k;
      if (l.day < numDays && p < slotsPerDay) {
        grid[l.day][p] += 1;
        idsAt[l.day][p].push(l.id);
      }
    }
  }
  let maxDensity = 0;
  for (const row of grid) for (const v of row) if (v > maxDensity) maxDensity = v;

  // Danh sach de do bo loc pham vi
  const programs = [...new Set(withFlags.map((l) => l.programLabel).filter(Boolean))].sort((a, b) =>
    a.localeCompare(b),
  );
  const teachers = [
    ...new Map(withFlags.map((l) => [l.teacherId, l.teacherName])).entries(),
  ]
    .map(([id, name]) => ({ id, name }))
    .sort((a, b) => (a.name ?? "").localeCompare(b.name ?? ""));

  return {
    lessons,
    totalLessons: withFlags.length,
    guestCount: lessons.filter((l) => l.teacherType === "GUEST").length,
    residentCount: lessons.filter((l) => l.teacherType === "RESIDENT").length,
    problemCount: lessons.filter((l) => l.hasProblem).length,
    grid,
    idsAt,
    maxDensity,
    programs,
    teachers,
    numDays,
    slotsPerDay,
    filter: f,
  };
}

// Nhan gon cho biet dang xem pham vi nao - dung o thanh tieu de.
export function scopeLabel(view, data) {
  const f = view.filter;
  if (f.scope === SCOPE.PROGRAM && f.scopeValue) return f.scopeValue;
  if (f.scope === SCOPE.TEACHER && f.scopeValue) {
    const t = view.teachers.find((x) => String(x.id) === String(f.scopeValue));
    return t?.name ?? `GV #${f.scopeValue}`;
  }
  return `Toàn khoa · ${data?.numPrograms ?? "?"} chương trình`;
}
