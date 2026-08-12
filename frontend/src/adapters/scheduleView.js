// Nguon du lieu cho man "Thoi khoa bieu" gop. Mot bo loc duy nhat quyet dinh
// nhin thay gi - thay cho viec truoc day moi pham vi la mot man rieng:
//   Giai doan 1  = layers{guest} + phase view
//   Giai doan 2  = layers{guest+resident}
//   Tra cuu GV   = scope{teacher}
//
// Bang mat do (navigator) cung tinh o day: no la thu bu lai cho viec luoi phai
// cuon khi the hien du thong tin ca hoc.

import { lessonToTimetableItem, mergeGuestAndResidentLessons } from "./lessonAdapter";

export const SCOPE = { ALL: "all", PROGRAM: "program", TEACHER: "teacher", COHORT: "cohort" };

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
  // Khoa (cot "Khóa", vd VJU2026) khong nam tren lesson - noi tu bang lop qua
  // sectionId, cung cach lam voi classCode. Khong bat solver phai mang thong tin
  // hanh chinh nay chi de loc o giao dien.
  // O GHEP ("BCSE+MJM", "VJU2023+VJU2024") = lop cua CA HAI - loc theo THANH
  // PHAN, xem app._tach_phan(). Noi tu bang lop qua sectionId nhu classCode.
  const cohortById = new Map((data?.classes ?? []).map((c) => [c.sectionId, c.cohortParts ?? []]));
  const programPartsById = new Map((data?.classes ?? []).map((c) => [c.sectionId, c.programParts ?? []]));
  // Si so - the HOC CHUNG cong don de biet phong phai chua bao nhieu nguoi.
  const sinhVienById = new Map((data?.classes ?? []).map((c) => [c.sectionId, c.expectedStudents]));

  const withFlags = all.map((l) => {
    const ovMap = l.teacherType === "RESIDENT" ? residentOverrides : guestOverrides;
    const override = ovMap[l.id] ?? ovMap[String(l.id)] ?? null;
    return {
      ...l,
      classCode: classCodeById.get(l.id) || null,
      cohortParts: cohortById.get(l.id) ?? [],
      programParts: programPartsById.get(l.id) ?? [],
      problems: problemMap.get(l.id) ?? [],
      hasProblem: problemMap.has(l.id),
      override,
      isPinned: !!override,
      hocChungId: l.hocChungId ?? null,
    };
  });

  // --- HOC CHUNG: gop cac buoi cung nhom thanh MOT THE ---------------------
  // Chung o CUNG mot o gio (solver ep vay - xem webapp/domain/hoc_chung.py) nen
  // neu de nguyen thi N the ve de len nhau trong mot o, khong doc duoc cai nao.
  // Mot buoi day vat ly thi mot the: giu buoi DAI DIEN, gan them danh sach cac
  // mon cung hoc de the/popup ke ra.
  //
  // Hop programParts/cohortParts/teacherIds cua ca nhom: bo loc theo CTDT/Khoa/GV
  // phai tim ra the nay qua BAT KY thanh vien nao - lop hoc chung thuoc ve moi
  // chuong trinh trong nhom.
  const gopHocChung = (ds) => {
    const theoNhom = new Map();
    for (const l of ds) {
      if (l.hocChungId == null) continue;
      if (!theoNhom.has(l.hocChungId)) theoNhom.set(l.hocChungId, []);
      theoNhom.get(l.hocChungId).push(l);
    }
    if (theoNhom.size === 0) return ds;
    const bo = new Set();
    const gop = new Map();
    for (const [nhomId, ds2] of theoNhom) {
      if (ds2.length < 2) continue;
      const sx = [...ds2].sort((a, b) => a.id - b.id);
      const rep = sx[0];
      sx.slice(1).forEach((l) => bo.add(l.id));
      gop.set(rep.id, {
        ...rep,
        programParts: [...new Set(sx.flatMap((l) => l.programParts ?? []))],
        cohortParts: [...new Set(sx.flatMap((l) => l.cohortParts ?? []))],
        teacherIds: [...new Set(sx.flatMap((l) => l.teacherIds ?? [l.teacherId]))],
        problems: sx.flatMap((l) => l.problems ?? []),
        hasProblem: sx.some((l) => l.hasProblem),
        hocChung: {
          id: nhomId,
          count: sx.length,
          members: sx.map((l) => ({
            id: l.id, classCode: l.classCode, courseName: l.courseName,
            programLabel: l.programLabel,
            expectedStudents: sinhVienById.get(l.id) ?? null,
          })),
          tongSV: sx.reduce((t, l) => t + (sinhVienById.get(l.id) ?? 0), 0) || null,
        },
      });
    }
    return ds.filter((l) => !bo.has(l.id)).map((l) => gop.get(l.id) ?? l);
  };
  const daGop = gopHocChung(withFlags);

  const q = f.search.trim().toLowerCase();
  const lessons = daGop.filter((l) => {
    if (l.teacherType === "GUEST" && !f.guest) return false;
    if (l.teacherType === "RESIDENT" && !f.resident) return false;
    if (f.scope === SCOPE.PROGRAM && f.scopeValue && !l.programParts.includes(f.scopeValue)) return false;
    // Loc theo GV xet CA NHOM (dong giang + hoc chung), khong chi GV chinh -
    // cung ly le voi lessonAdapter.teacherLookupBuild.
    if (f.scope === SCOPE.TEACHER && f.scopeValue) {
      const tids = l.teacherIds?.length ? l.teacherIds : [l.teacherId];
      if (!tids.some((t) => String(t) === String(f.scopeValue))) return false;
    }
    if (f.scope === SCOPE.COHORT && f.scopeValue && !l.cohortParts.includes(f.scopeValue)) return false;
    if (f.onlyProblems && !l.hasProblem) return false;
    if (!q) return true;
    return (
      String(l.id) === q ||
      (l.courseName ?? "").toLowerCase().includes(q) ||
      (l.teacherName ?? "").toLowerCase().includes(q) ||
      (l.programLabel ?? "").toLowerCase().includes(q) ||
      l.cohortParts.some((k) => k.toLowerCase().includes(q)) ||
      // The gop: tim duoc qua ten/ma lop cua BAT KY mon cung hoc chung
      (l.hocChung?.members ?? []).some(
        (m) => (m.courseName ?? "").toLowerCase().includes(q)
          || (m.classCode ?? "").toLowerCase().includes(q),
      )
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
  const programs = [...new Set(withFlags.flatMap((l) => l.programParts))].sort((a, b) =>
    a.localeCompare(b),
  );
  const teachers = [
    ...new Map(withFlags.map((l) => [l.teacherId, l.teacherName])).entries(),
  ]
    .map(([id, name]) => ({ id, name }))
    .sort((a, b) => (a.name ?? "").localeCompare(b.name ?? ""));
  // Khoa moi nhat len dau (VJU2026 truoc VJU2023) - giao vu hay xem khoa moi.
  const cohorts = [...new Set(withFlags.flatMap((l) => l.cohortParts))].sort().reverse();

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
    cohorts,
    numDays,
    slotsPerDay,
    filter: f,
  };
}

// Nhan gon cho biet dang xem pham vi nao - dung o thanh tieu de.
export function scopeLabel(view, data) {
  const f = view.filter;
  if (f.scope === SCOPE.PROGRAM && f.scopeValue) return f.scopeValue;
  if (f.scope === SCOPE.COHORT && f.scopeValue) return `Khoá ${f.scopeValue}`;
  if (f.scope === SCOPE.TEACHER && f.scopeValue) {
    const t = view.teachers.find((x) => String(x.id) === String(f.scopeValue));
    return t?.name ?? `GV #${f.scopeValue}`;
  }
  return `Toàn khoa · ${data?.numPrograms ?? "?"} chương trình`;
}
