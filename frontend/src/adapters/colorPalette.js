// Bang mau + ham hash dung chung cho PeriodTimetable.jsx (mau theo mon hoc,
// co dinh) va LessonCard.jsx (mau theo nhom do nguoi dung chon - xem
// colorGrouping.js) - cung 1 key luon ra cung 1 mau, khong can luu trang thai.
export const PALETTE = [
  { bg: "#EFF6FF", border: "#3B82F6", text: "#1E40AF" },
  { bg: "#FFF7ED", border: "#F97316", text: "#9A3412" },
  { bg: "#F0FDF4", border: "#22C55E", text: "#166534" },
  { bg: "#FDF2F8", border: "#EC4899", text: "#9D174D" },
  { bg: "#F5F3FF", border: "#8B5CF6", text: "#5B21B6" },
  { bg: "#FFFBEB", border: "#EAB308", text: "#854D0E" },
  { bg: "#ECFDF5", border: "#10B981", text: "#065F46" },
  { bg: "#FFF1F2", border: "#F43F5E", text: "#9F1239" },
  { bg: "#F0F9FF", border: "#0EA5E9", text: "#0C4A6E" },
  { bg: "#FAF5FF", border: "#A855F7", text: "#6B21A8" },
];

export function getColor(key) {
  let hash = 0;
  const s = key || "";
  for (let i = 0; i < s.length; i++) hash = s.charCodeAt(i) + ((hash << 5) - hash);
  return PALETTE[Math.abs(hash) % PALETTE.length];
}
