// Cau truc dieu huong 2 CAP cho sidebar (dong bo voi app Nhap hoc VJU).
//
// Truoc refactor: 10 tab tran 2 hang, trong do Giai doan 1 / Giai doan 2 / Tra
// cuu theo giang vien / Check trung deu la CUNG MOT luoi tuan voi bo loc khac
// nhau. Giai doan 1 va 2 khong phai hai khung nhin ma la hai BUOC - buoc thuoc
// ve thanh tien trinh trong man Thoi khoa bieu, khong thuoc thanh dieu huong.
//
// Lan nay gom tiep: "Chuan bi du lieu" va "Nhat ky & ban luu" von da co tab con
// ben trong trang (DataPage/HistoryPage tu ve thanh tab rieng). Sidebar 2 cap
// nhan luon vai tro do - tab con trong trang bi go, khong con hai thanh dieu
// huong long nhau.
//
// "Du lieu hoc phan" la noi NHAP LIEU CHINH (thay Excel) - khong con la loi phu
// destructive nhu "Nhap lieu thu cong" cu, nen dung ngang hang cac muc con lai.
// Nut "Bat dau hoc ky moi" (xoa het, /api/manual/init) nam BEN TRONG trang do,
// co window.confirm rieng - tach khoi luong them/sua lop hang ngay.

import {
  BookOpen,
  CalendarClock,
  CalendarDays,
  ClipboardList,
  Clock,
  HelpCircle,
  ListChecks,
  Save,
  ScrollText,
} from 'lucide-react';

/** Muc don tren cung - man hinh chinh cua cong cu. */
export const NAV_HOME = {
  key: 'schedule',
  label: 'Thời khoá biểu',
  icon: CalendarDays,
};

/**
 * Muc don GHIM TREN CUNG thu hai, dong cap voi NAV_HOME - khong nam trong
 * NAV_GROUPS ("Nghiep vu") vi day khong phai mot buoc trong quy trinh, ma la
 * tai lieu tra cuu bat cu luc nao, danh cho ca hai vai tro.
 */
export const NAV_GUIDE = {
  key: 'guide',
  label: 'Hướng dẫn sử dụng',
  icon: HelpCircle,
};

/**
 * Cac muc con lai, xep theo DUNG THU TU LAM VIEC - khop voi 3 buoc tren thanh
 * tien trinh cua man Thoi khoa bieu (WorkflowStrip):
 *
 *   1. Du lieu hoc phan   - nhap lop/hoc phan/giang vien (nguon du lieu CHINH,
 *                           thay Excel). Khong co cai nay thi khong co gi de thu
 *                           gio, cung khong co gi de giai.
 *   2. Chuan bi du lieu   - thu khung gio GV thinh giang co the day (buoc "Thu
 *                           gio" tren thanh tien trinh).
 *   3. (Thoi khoa bieu)   - giai + xem ket qua. Nam RIENG o tren cung vi day la
 *                           man quay lai hang ngay, khong phai buoc lam mot lan.
 *   4. Nhat ky & ban luu  - tra cuu sau khi da lam xong.
 *
 * Ban dau xep "Chuan bi du lieu" TRUOC "Du lieu hoc phan" - tuc buoc 2 nam tren
 * buoc 1, nguoc voi thu tu that.
 *
 * `children` rong = muc don (khong xo ra), giong "Du lieu hoc phan".
 * `key` cua child chinh la `sub` cua trang - khop voi TABS trong DataPage/HistoryPage.
 *
 * "Giảng viên" TRUOC day la mot nhom rieng ngang hang (2 tab Co huu/Thinh
 * giang, xem git history) - da GOP vao "Chuẩn bị dữ liệu → Giờ rảnh GV": ca
 * hai deu la MAN QUAN LY GIANG VIEN, chi khac o loc theo loai truoc khi xem
 * ten, nen tach thanh hai nhom rieng tren sidebar chi lam nguoi dung phai doan
 * "sua thong tin GV" voi "khai gio ranh" nam o dau. Bo loc loai (Co huu/Thinh
 * giang) gio nam TRONG trang, khong con la muc dieu huong rieng.
 */
export const NAV_GROUPS = [
  {
    key: 'manual',
    label: 'Dữ liệu học phần',
    icon: BookOpen,
    children: [],
  },
  {
    key: 'data',
    label: 'Chuẩn bị dữ liệu',
    icon: ClipboardList,
    children: [
      // "Khung giờ đã báo" -> "Học phần": trang nay gio la BANG VIEC PHAI LAM
      // theo LOP hoc phan (chua co GV / co GV thinh giang nhung chua khai gio),
      // khong con chi noi ve "khung gio" don thuan (xem SubmissionsPage).
      { key: 'hours', label: 'Học phần', icon: Clock },
      // "Giờ rảnh GV" -> "Giảng viên": trang nay da GOP ca thong tin GV (truoc
      // o nhom "Giảng viên" rieng) VA gio ranh vao lam MOT, nen doi ten cho dung
      // pham vi that (xem TeacherAvailabilityPage).
      { key: 'availability', label: 'Giảng viên', icon: CalendarClock },
    ],
  },
  {
    key: 'history',
    label: 'Nhật ký & bản lưu',
    icon: ScrollText,
    children: [
      { key: 'log', label: 'Nhật ký thao tác', icon: ListChecks },
      { key: 'saved', label: 'Bản đã lưu', icon: Save },
    ],
  },
];

// Vai tro "Xem thoi" chi vao duoc man chi-doc + huong dan su dung.
export const VIEWER_ALLOWED_KEYS = ['schedule', 'history', 'guide'];

/** Nhan hien tren topbar / page header cho tung trang. */
export const PAGE_LABELS = {
  schedule: NAV_HOME.label,
  guide: NAV_GUIDE.label,
  ...Object.fromEntries(NAV_GROUPS.map((g) => [g.key, g.label])),
};

/** Nhan cua muc cap 2, tra ve null neu trang do khong co muc con. */
export function subLabel(pageKey, subKey) {
  const group = NAV_GROUPS.find((g) => g.key === pageKey);
  return group?.children.find((c) => c.key === subKey)?.label ?? null;
}

/** Muc con dau tien cua mot trang (dung lam `sub` mac dinh khi bam vao nhom). */
export function firstSubKey(pageKey) {
  const group = NAV_GROUPS.find((g) => g.key === pageKey);
  return group?.children[0]?.key ?? null;
}

/** Loc nhom theo vai tro; vai tro "Xem thoi" chi thay man chi-doc. */
export function getAllowedGroups(role) {
  if (role === 'viewer') {
    return NAV_GROUPS.filter((g) => VIEWER_ALLOWED_KEYS.includes(g.key));
  }
  return NAV_GROUPS;
}
