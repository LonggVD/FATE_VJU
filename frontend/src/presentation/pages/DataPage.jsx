import SubmissionsPage from "./SubmissionsPage";
import TeacherAvailabilityPage from "./TeacherAvailabilityPage";

// "Chuan bi du lieu" - Khung gio da bao + Gio ranh GV: deu thuoc cung mot
// viec (thu du gio GV thinh giang truoc khi giai). Truoc day con co "Nguon
// du lieu" (sinh gia lap) va "Hoc ky" (tai Excel) - da bo vi luong that gio
// di qua "Du lieu hoc phan" (nhap tay) thay Excel/gia lap hoan toan.
//
// Thanh tab rieng cua trang nay da bi go: sidebar 2 cap giu vai tro do, hai
// thanh dieu huong long nhau chi lam nguoi dung phai doan cai nao dang dieu
// khien cai gi. `key` o day khop voi children cua nhom "data" trong nav.js.
const PANES = {
  hours: SubmissionsPage,
  availability: TeacherAvailabilityPage,
};

export default function DataPage({ role, sub }) {
  const Current = PANES[sub] ?? PANES.hours;
  return <Current role={role} />;
}
