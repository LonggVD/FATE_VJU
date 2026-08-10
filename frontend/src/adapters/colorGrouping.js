// "To mau theo" gi trong Luoi (LessonGridBoard) - tach rieng khoi tin hieu
// canh bao (vien do khi highlight/trung) de 2 kenh khong de len nhau. Khong
// cho "theo Mon hoc" vi so ma mon co the len toi 100+ trong khi bang mau chi
// co 10 mau co dinh - se trung mau qua nhieu, nhin loan ma khong giup gi.

import { getColor } from "./colorPalette";
export const COLOR_BY_OPTIONS = [
  { key: "status", label: "Trạng thái" },
  { key: "program", label: "Chương trình" },
  { key: "teacherType", label: "Loại giảng viên" },
  { key: "faculty", label: "Khoa" },
];

// "Theo trang thai" la mac dinh moi, thay cho "theo chuong trinh". Ly do: du lieu
// that co 19 chuong trinh -> 19 muc chu giai, trong do co 3 mau xanh la va 4 mau
// do khong phan biet noi. Qua ~7 lop mau la mat khong doc duoc nua.
// Ba lop nay tra loi dung hai cau nguoi dung can: "co on khong" va "thuoc giai
// doan nao". Mau co dinh, khong lay tu bang mau bam (getColor).
export const STATUS_COLORS = {
  "Có vấn đề":   { bg: "#fee2e2", border: "#dc2626", text: "#991b1b" },
  // Xanh duong (tone "blue" cua design system VJU), KHONG dung do - do gio la
  // mau thuong hieu va da bi "Co van de" chiem trong chinh bang chu giai nay.
  "Thỉnh giảng": { bg: "#dbeafe", border: "#2563eb", text: "#1d4ed8" },
  "Cơ hữu":      { bg: "#ccfbf1", border: "#0d9488", text: "#115e59" },
};

export function statusKeyOf(lesson) {
  if (lesson.hasProblem) return "Có vấn đề";
  return lesson.teacherType === "GUEST" ? "Thỉnh giảng" : "Cơ hữu";
}

const FACULTY_RE = /\(([^)]+)\)\s*$/;

export function groupKeyOf(lesson, colorBy) {
  if (colorBy === "status") {
    return statusKeyOf(lesson);
  }
  if (colorBy === "teacherType") {
    return lesson.teacherType === "GUEST" ? "Thỉnh giảng" : "Cơ hữu";
  }
  if (colorBy === "faculty") {
    const m = FACULTY_RE.exec(lesson.programLabel || "");
    return m ? m[1] : (lesson.programLabel || "Khác");
  }
  return lesson.programLabel || "Khác";
}

const MAX_LEGEND_GROUPS = 8;

// Chu giai cho "Chuong trinh" / "Loai giang vien" / "Khoa" - truoc day CHI
// "Trang thai" co chu giai (mau co dinh 3 gia tri). Ba lop mau con lai dung
// getColor() hash theo ten nhom nen KHONG doan truoc duoc mau nao ung voi cai
// gi - khong co chu giai thi mau vo nghia, chi con la trang tri.
//
// Cap MAX_LEGEND_GROUPS: qua ~8 nhom mau la mat khong phan biet noi (dung
// nguyen tac da ap dung khi bo "theo Chuong trinh" lam mac dinh o buoc truoc -
// du lieu that co toi 19 chuong trinh). Nhom it buoi nhat gap chung vao "Khac",
// KHONG cat theo alphabet - giu lai cac nhom dang chiem nhieu cho, cai it thi
// nguoi dung it can phan biet.
export function buildLegend(lessons, colorBy) {
  if (colorBy === "status") return null; // da co STATUS_COLORS co dinh, khong can tinh

  const counts = new Map();
  for (const l of lessons) {
    const key = groupKeyOf(l, colorBy);
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }

  const sorted = [...counts.entries()].sort((a, b) => b[1] - a[1]);
  const kept = sorted.slice(0, MAX_LEGEND_GROUPS);
  const restCount = sorted.slice(MAX_LEGEND_GROUPS).reduce((n, [, c]) => n + c, 0);

  const items = kept.map(([key, count]) => ({ key, count, color: getColor(key) }));
  if (restCount > 0) {
    items.push({ key: `+${sorted.length - MAX_LEGEND_GROUPS} khác`, count: restCount, color: null });
  }
  return items;
}
