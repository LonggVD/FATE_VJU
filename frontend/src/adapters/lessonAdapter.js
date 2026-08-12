// Map 1 lesson tra ve tu solve_guest_phase()/solve_resident_phase() cua
// scheduler_core.py sang prop shape ma LessonCard.jsx / LessonGridBoard.jsx /
// PeriodTimetable.jsx dung: giu nguyen cac truong da co san (day/period/slot/
// duration/teacherType...), chi them "phase" (THONG TIN, KHONG rang buoc gi)
// de biet buoi nay do GD1 hay GD2 xep.
//
// "frozen" TUNG co nghia "khoa, khong sua duoc" tu thoi con 2 trang rieng
// (man Giai doan 2 cu hien lai ket qua GD1 nhu 1 lop nen co dinh, khong cho
// dong vao). Sau khi gop thanh 1 trang, backend (/api/move-lesson) da kiem
// tra xung dot tren CA guestResult+residentResult bat ke buoi thuoc phase
// nao (xem _detect_move_conflict trong app.py), nen khong con ly do ky thuat
// nao de chan keo-tha buoi GD1. Truoc day co gan frozen=true CUNG DINH cho
// MOI buoi thinh giang (khong phu thuoc GD2 da giai hay chua) khien toan bo
// buoi thinh giang khong keo duoc - day chinh la loi da phat hien.
export function lessonToTimetableItem(lesson, { phase = null } = {}) {
  return {
    id: lesson.id,
    day: lesson.day,
    period: lesson.period,
    slot: lesson.slot,
    duration: lesson.duration,
    courseName: lesson.courseName,
    teacherId: lesson.teacherId,
    // CA NHOM giang vien (dong giang day) - bo loc theo GV va cac phep quet trung
    // phai xet het, khong chi GV chinh. Ham nay liet ke TUONG MINH tung truong nen
    // thieu o day la mat luon o moi noi dung grid item.
    teacherIds: lesson.teacherIds ?? (lesson.teacherId != null ? [lesson.teacherId] : []),
    teacherName: lesson.teacherName,
    teacherType: lesson.teacherType,
    roomType: lesson.roomType,
    // HOC CHUNG: nhieu ma mon la MOT buoi day. scheduleView gop cac buoi cung
    // nhom thanh mot the theo hai truong nay (xem webapp/domain/hoc_chung.py).
    hocChungId: lesson.hocChungId ?? null,
    hocChungWith: lesson.hocChungWith ?? [],
    programLabel: lesson.programLabel,
    // CTDT thanh phan + Khoa: bo loc/gom mau doc cai nay, khong boc tu chuoi nhan.
    programIds: lesson.programIds ?? (lesson.program != null ? [lesson.program] : []),
    programParts: lesson.programParts ?? [],
    facultyName: lesson.facultyName ?? null,
    usedWindowLabel: lesson.usedWindowLabel,
    phase,
  };
}

export function mergeGuestAndResidentLessons(guestLessons = [], residentLessons = []) {
  return [
    ...guestLessons.map((l) => lessonToTimetableItem(l, { phase: "GD1" })),
    ...residentLessons.map((l) => lessonToTimetableItem(l, { phase: "GD2" })),
  ];
}

// Khong co endpoint /api/teacher/:id rieng - loc phia client tu 3 mang da
// fetch san (submissions cua data, lessons cua guestResult/residentResult)
// theo teacherId, gop lai thanh 1 danh sach cho PeriodTimetable.
export function teacherLookupBuild(teacherId, { data, guestResult, residentResult }) {
  const tid = Number(teacherId);
  // Buoi DONG GIANG phai hien trong lich cua CA NHOM, khong chi GV chinh: nguoi
  // thu 2 tro di van phai co mat that, va solver cung chan ho day cho khac gio
  // do (teacherIds). Fallback teacherId cho ket qua giai cu chua co field nay.
  const cuaGv = (l) => (l.teacherIds?.length ? l.teacherIds.includes(tid) : l.teacherId === tid);
  const guestLessons = (guestResult?.lessons || []).filter(cuaGv);
  const residentLessons = (residentResult?.lessons || []).filter(cuaGv);
  const submissions = (data?.submissions || []).filter((s) => s.teacherId === tid);
  const lessons = mergeGuestAndResidentLessons(guestLessons, residentLessons);
  return { lessons, submissions };
}
