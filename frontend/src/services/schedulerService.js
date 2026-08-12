import { apiGet, apiPost, apiPatch, apiDelete, apiUpload } from "./api";

export const getData = () => apiGet("/api/data");
export const submitAvailability = (sectionId, windowSlots) =>
  apiPost("/api/submit-availability", { sectionId, windowSlots });
export const solveGuest = () => apiPost("/api/solve-guest");
export const solveResident = () => apiPost("/api/solve-resident");
// Keo-tha sua tay (thay cho "Tu choi - luan chuyen" cu). moveLesson khong ghi
// reason se bi 409 neu o do dang co van de - xem api.js (err.body.conflict).
export const moveLesson = (sectionId, slot, reason) =>
  apiPost("/api/move-lesson", { sectionId, slot, reason });
export const clearOverride = (sectionId) => apiPost("/api/clear-override", { sectionId });
// "Luu thoi khoa bieu": ghi ket qua dang xem tren luoi thanh du lieu chinh
// thuc cua lop hoc phan (Thu/Tiet BD/Tiet KT/Trang thai).
export const saveSchedule = () => apiPost("/api/manual/save-schedule");
export const getState = () => apiGet("/api/state");
// Ket qua giai dang cache ben Flask - de tai lai trang khong mat luoi da xep.
export const getResults = () => apiGet("/api/results");

export const initManual = () => apiPost("/api/manual/init");
// Nap file ke hoach giang day cu vao form. HAI BUOC: xem truoc (khong ghi gi,
// chi doc file va bao se ra cai gi) roi moi commit (ghi de toan bo du lieu).
export const importPreview = (file) => apiUpload("/api/manual/import/preview", file);
// mode: "replace" (xoa het roi nap) | "merge" (gop them vao du lieu dang co)
export const importCommit = (mode = "replace") =>
  apiPost("/api/manual/import/commit", { mode });
// DANH SACH GV CO HUU cua truong - nguon CHINH THUC de phan loai co huu/thinh
// giang. Cung 2 buoc nhu nhap file ke hoach: nap no co the doi loai nhieu GV,
// keo theo lop chuyen giai doan xep lich.
export const lecturersPreview = (file) => apiUpload("/api/manual/lecturers/preview", file);
export const lecturersCommit = () => apiPost("/api/manual/lecturers/commit");
export const lecturersClear = () => apiDelete("/api/manual/lecturers");
export const getLecturers = () => apiGet("/api/manual/lecturers");
export const addManualTeacher = (payload) => apiPost("/api/manual/teacher", payload);
export const updateManualTeacher = (teacherId, payload) => apiPatch(`/api/manual/teacher/${teacherId}`, payload);
// CHOT LICH cho ca mot hoc phan: ghi gio dang hien tren luoi thanh gio chinh
// thuc VA ghim lai - giai lai khong dich duoc nua, sua tay/keo-tha bi chan.
export const chotCourse = (courseId, payload) =>
  apiPost(`/api/manual/course/${courseId}/chot`, payload);
export const boChotCourse = (courseId) => apiDelete(`/api/manual/course/${courseId}/chot`);
export const addManualCourse = (payload) => apiPost("/api/manual/course", payload);
export const updateManualCourse = (courseId, payload) => apiPatch(`/api/manual/course/${courseId}`, payload);
export const addManualSection = (payload) => apiPost("/api/manual/section", payload);
export const updateManualSection = (sectionId, payload) => apiPatch(`/api/manual/section/${sectionId}`, payload);
export const deleteManualSection = (sectionId) => apiDelete(`/api/manual/section/${sectionId}`);
// "Xoa gio" hang loat - dat lai Thu/Tiet dau/Tiet cuoi cua nhieu lop thanh
// "de he thong tu xep" cung mot luc (xem app.py: api_manual_clear_times).
export const clearManualTimes = (sectionIds) => apiPost("/api/manual/clear-times", { sectionIds });
