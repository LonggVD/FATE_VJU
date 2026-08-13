// Vi sao CP-SAT khong xep duoc 1 buoi thinh giang - tinh o frontend.
//
// Backend chi tra ve unplaced[] kem TOAN BO cac buoi khac cung giang vien
// (otherSectionsSameTeacher), khong noi buoi nao thuc su chiem cho. Vi du that:
// #91 co 2 buoi cung GV, nhung chi #139 dung gio - con #100 hoan toan vo can.
// Panel cu do het ra roi de nguoi doc tu so nhan gio.
//
// Du lieu can co san: guestResult.lessons (buoi DA xep, co slot/duration/roomType)
// va data.submissions (windowSlots tho + duration). unplaced[].windows chi la
// NHAN chu nen khong dung de tinh chong lan duoc.

import { slotToDayPeriod } from "./dayPeriod";
import { taoCungBuoi } from "./hocChung";
import { slotRangeLabel } from "./crossConflictAnalysis";

function overlaps(a, durA, b, durB) {
  return !(a + durA <= b || b + durB <= a);
}

export const UNPLACED_REASON = {
  TEACHER: "TEACHER",
  ROOM: "ROOM",
  MIXED: "MIXED",
  NOT_SUBMITTED: "NOT_SUBMITTED",
  OTHER: "OTHER",
};

export const REASON_META = {
  TEACHER: {
    label: "Trùng giảng viên",
    cls: "teacher",
    hint: "Buổi khác của chính GV này đã chiếm khung giờ đó",
    fix: "Đổi giờ một trong hai buổi",
  },
  ROOM: {
    label: "Hết phòng",
    cls: "room",
    hint: "Mọi khung giờ đã báo đều kín phòng cùng loại",
    fix: "Thêm phòng, hoặc báo thêm khung giờ khác",
  },
  MIXED: {
    label: "Trùng GV + hết phòng",
    cls: "mixed",
    hint: "Mỗi khung giờ bị chặn bởi một lý do khác nhau",
    fix: "Báo thêm khung giờ khác",
  },
  NOT_SUBMITTED: {
    label: "Chưa nộp giờ",
    cls: "pending",
    hint: "Không có khung giờ nào để xếp",
    fix: "Điều phối viên nộp giờ ở tab \"Học phần\"",
  },
  OTHER: {
    label: "Chưa xác định được",
    cls: "other",
    hint: "Còn khung giờ trống nhưng CP-SAT vẫn không dùng — do ràng buộc kết hợp",
    fix: "Xem lại toàn cục ở lưới bên dưới",
  },
};

export function analyzeUnplaced(guestResult, data) {
  const unplaced = guestResult?.unplaced ?? [];
  const placed = guestResult?.lessons ?? [];
  const slotsPerDay = data?.slotsPerDay ?? 12;
  const pools = { LT: data?.ltPool ?? 0, LAB: data?.labPool ?? 0 };

  // sectionId -> windowSlots tho + duration
  const subById = new Map((data?.submissions ?? []).map((s) => [s.sectionId, s]));
  // Ma lop hoc phan de hien THAY CHO "#<id noi bo>" (giong cach lam o
  // scheduleView.js) - unplaced[] tu backend khong tu co field nay.
  const classCodeById = new Map((data?.classes ?? []).map((c) => [c.sectionId, c.classCode]));
  // HOC CHUNG: buoi cung nhom KHONG phai thu pham chan cho - chung o cung o gio
  // theo dung y giao vu, va solver da coi ca nhom la mot buoi mot phong.
  const cungBuoi = taoCungBuoi(data);

  const items = unplaced.map((u) => {
    const sub = subById.get(u.id);
    const duration = sub?.duration ?? data?.duration ?? 2;
    const windowSlots = sub?.windowSlots ?? [];

    const windows = windowSlots.map((w) => {
      // classCode gan them vao TUNG buoi chan (khong chi buoi #u.id) - de UI
      // hien "trung voi CSE3056 (#263)" thay vi trung so #263 kho hieu.
      // Chan cho tinh theo CA NHOM dong giang day: lop 5 nguoi day thi ai trong
      // nhom dang day cho khac cung gio cung la thu pham. Chi soi GV chinh thi
      // giao vu doc "khong xep duoc" ma khong thay ai dang chan.
      const tidsCuaLop = u.teacherIds?.length ? u.teacherIds : [u.teacherId];
      const teacherBlockers = placed
        .filter((l) => {
          if (cungBuoi(u.id, l.id)) return false;
          const tidsCuaBuoi = l.teacherIds?.length ? l.teacherIds : [l.teacherId];
          return (
            tidsCuaBuoi.some((t) => tidsCuaLop.includes(t)) &&
            overlaps(w, duration, l.slot, l.duration)
          );
        })
        .map((l) => ({ ...l, classCode: classCodeById.get(l.id) || null }));
      const sameRoomCount = placed.filter(
        (l) => !cungBuoi(u.id, l.id) && l.roomType === u.roomType
          && overlaps(w, duration, l.slot, l.duration),
      ).length;
      const pool = pools[u.roomType] ?? 0;
      const roomFull = pool > 0 && sameRoomCount >= pool;
      return {
        slot: w,
        label: slotRangeLabel(w, duration, slotsPerDay),
        day: slotToDayPeriod(w, slotsPerDay).day,
        teacherBlockers,
        sameRoomCount,
        pool,
        roomFull,
        blocked: teacherBlockers.length > 0 || roomFull,
      };
    });

    const allBlocked = windows.length > 0 && windows.every((w) => w.blocked);
    const allTeacher = windows.length > 0 && windows.every((w) => w.teacherBlockers.length > 0);
    const allRoom = windows.length > 0 && windows.every((w) => w.roomFull);

    let reason;
    if (windowSlots.length === 0) reason = UNPLACED_REASON.NOT_SUBMITTED;
    else if (allTeacher) reason = UNPLACED_REASON.TEACHER;
    else if (allRoom) reason = UNPLACED_REASON.ROOM;
    else if (allBlocked) reason = UNPLACED_REASON.MIXED;
    else reason = UNPLACED_REASON.OTHER;

    // Thu pham: cac buoi DA xep dang chiem cho, KHONG phai moi buoi cung GV.
    const blockerMap = new Map();
    for (const w of windows) {
      for (const b of w.teacherBlockers) {
        if (!blockerMap.has(b.id)) blockerMap.set(b.id, { lesson: b, atLabels: [] });
        blockerMap.get(b.id).atLabels.push(w.label);
      }
    }
    const blockers = [...blockerMap.values()];

    return {
      ...u,
      classCode: classCodeById.get(u.id) || null,
      duration,
      windowSlots,
      windows,
      reason,
      blockers,
      // Buoi khac cung GV nhung KHONG lien quan - de noi ro da loc bao nhieu.
      irrelevantSiblings: (u.otherSectionsSameTeacher ?? []).filter(
        (o) => !blockerMap.has(o.sectionId),
      ).length,
      singleWindow: windowSlots.length === 1,
    };
  });

  const byReason = {};
  for (const it of items) byReason[it.reason] = (byReason[it.reason] ?? 0) + 1;

  const reasonList = Object.entries(byReason)
    .map(([reason, count]) => ({ reason, count }))
    .sort((a, b) => b.count - a.count);

  return {
    items,
    byReason,
    reasonList,
    total: items.length,
    // Neu tat ca cung 1 nguyen nhan thi noi thanh 1 cau, khoi phai doc 5 dong.
    singleReason: reasonList.length === 1 ? reasonList[0] : null,
  };
}
