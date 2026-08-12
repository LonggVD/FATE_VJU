import { createContext, useCallback, useContext, useEffect, useState } from "react";
import * as scheduler from "../services/schedulerService";
import { useEventLog } from "./EventLogContext";

const AppDataContext = createContext(null);

// Noi giu du lieu dang lam viec cua toan SPA - guong lai STATE ben Flask (1
// "data" dang active + ket qua Giai doan 1/2) de moi trang doc chung ma
// khong phai fetch lai/prop-drilling qua nhieu tang component.
export function AppDataProvider({ children }) {
  const { log } = useEventLog();
  const [data, setData] = useState(null); // shape cua _build_data_response()
  const [guestResult, setGuestResult] = useState(null);
  const [residentResult, setResidentResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Bao 1 action bang loading/error + ghi log; messageFn(result) tra ve dong
  // log khi thanh cong (khong bat buoc), errorPrefix ghep vao khi loi.
  const runAction = useCallback(async (fn, { onSuccess, messageFn, errorPrefix } = {}) => {
    setLoading(true);
    setError(null);
    try {
      const result = await fn();
      onSuccess?.(result);
      if (messageFn) log(messageFn(result), "success");
      return result;
    } catch (err) {
      setError(err.message);
      log(`${errorPrefix || "Lỗi"}: ${err.message}`, "error");
      throw err;
    } finally {
      setLoading(false);
    }
  }, [log]);

  const refreshData = useCallback(() => runAction(
    () => scheduler.getData(),
    { onSuccess: setData, errorPrefix: "Không lấy được dữ liệu" },
  ), [runAction]);

  // Nap lai TOAN BO trang thai dang co ben Flask NGAY khi mo app: du lieu hoc
  // phan + ket qua giai.
  //
  // Truoc day chi ManualEntryPage goi refreshData() luc mount, nen vao thang bat
  // ky trang nao khac deu bao "Chua co du lieu" du backend van dang giu nguyen
  // (STATE["data"] con duoc persist xuong manual_state_snapshot.json, song qua ca
  // restart server). Nguoi dung phai vong qua "Du lieu hoc phan" roi quay lai moi
  // thay - khong ai doan duoc dieu do. Chinh docstring cua GET /api/data cung noi
  // endpoint do sinh ra cho "SPA chuyen man/refresh".
  //
  // Tuong tu, guestResult/residentResult truoc chi song trong state React: bam F5
  // la luoi trong va phai bam "Giai" lai (2-30 giay) du backend con nguyen ket
  // qua. GET /api/results (them moi) tra lai chung.
  //
  // KHONG di qua refreshData/runAction o day: /api/data tra 400 khi that su chua
  // co du lieu, ma do la trang thai HOP LE luc dau hoc ky - qua runAction se ghi
  // mot dong do vao Nhat ky va set error ngay man dau tien, bao loi cho thu khong
  // phai loi. Cac loi khac (mat mang, 500) van phai bao binh thuong.
  useEffect(() => {
    let cancelled = false;

    scheduler.getData()
      .then((res) => {
        if (cancelled) return;
        setData(res);
        // Chi hoi ket qua giai KHI da co du lieu - khong co du lieu thi chac chan
        // khong co ket qua, hoi them chi ton mot vong goi.
        return scheduler.getResults().then((r) => {
          if (cancelled) return;
          if (r.guestResult) setGuestResult(r.guestResult);
          if (r.residentResult) setResidentResult(r.residentResult);
        });
      })
      .catch((err) => {
        if (cancelled || err.status === 400) return; // chua co du lieu - binh thuong
        setError(err.message);
        log(`Không lấy được dữ liệu: ${err.message}`, "error");
      });

    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const doSubmitAvailability = useCallback((sectionId, windowSlots) => runAction(
    () => scheduler.submitAvailability(sectionId, windowSlots),
    {
      onSuccess: () => { refreshData(); },
      messageFn: () => `Đã nộp giờ cho buổi #${sectionId} (${windowSlots.length} khung giờ).`,
      errorPrefix: "Nộp giờ thất bại",
    },
  ), [runAction, refreshData]);

  const solveGuest = useCallback(() => runAction(
    () => scheduler.solveGuest(),
    {
      onSuccess: (res) => { setGuestResult(res); setResidentResult(null); },
      messageFn: (res) => `Giai đoạn 1: ${res.status} — ${res.placedCount}/${res.total} xếp được (${res.elapsedSeconds}s).`,
      errorPrefix: "Giải Giai đoạn 1 thất bại",
    },
  ), [runAction]);

  const solveResident = useCallback(() => runAction(
    () => scheduler.solveResident(),
    {
      onSuccess: setResidentResult,
      messageFn: (res) => `Giai đoạn 2: ${res.status} — ${res.placedCount}/${res.total} xếp được (${res.elapsedSeconds}s).`,
      errorPrefix: "Giải Giai đoạn 2 thất bại",
    },
  ), [runAction]);

  // Keo-tha sua tay (thay "Tu choi - luan chuyen" cu). KHONG di qua runAction:
  // ham do tu dong log MOI loi thanh dong do trong Nhat ky, nhung 409 "can ghi
  // ly do" la MOT BUOC BINH THUONG cua luong keo-tha (component se tu mo hop
  // thoai xin ly do), khong phai that bai - log no vao Nhat ky la nhieu.
  const doMoveLesson = useCallback(async (sectionId, slot, reason) => {
    setLoading(true);
    setError(null);
    try {
      const res = await scheduler.moveLesson(sectionId, slot, reason);
      setGuestResult(res.guestResult);
      setResidentResult(res.residentResult);
      log(
        `Đã sửa tay buổi #${sectionId} sang ${res.day != null ? `Ngày ${res.day + 1} tiết ${res.period + 1}` : "giờ khác"}` +
          (reason ? ` — lý do: ${reason}` : ""),
        "success",
      );
      return res;
    } catch (err) {
      if (err.status !== 409) {
        setError(err.message);
        log(`Sửa tay thất bại: ${err.message}`, "error");
      }
      throw err; // component tu quyet dinh: 409 -> mo hop thoai xin ly do, con lai -> bao loi
    } finally {
      setLoading(false);
    }
  }, [log]);

  const doClearOverride = useCallback((sectionId) => runAction(
    () => scheduler.clearOverride(sectionId),
    {
      onSuccess: (res) => { setGuestResult(res.guestResult); setResidentResult(res.residentResult); },
      messageFn: () => `Đã bỏ ghim buổi #${sectionId} — có hiệu lực từ lần "Giải lại" tiếp theo.`,
      errorPrefix: "Bỏ ghim thất bại",
    },
  ), [runAction]);

  const doSaveSchedule = useCallback(() => runAction(
    () => scheduler.saveSchedule(),
    {
      onSuccess: setData,
      messageFn: (res) => `Đã lưu ${res.savedCount} buổi vào Dữ liệu học phần` +
        (res.problemCount ? ` — ${res.problemCount} buổi có vấn đề` : "") +
        (res.missingCount ? `, ${res.missingCount} buổi vẫn chưa có giờ` : "") + ".",
      errorPrefix: "Lưu thời khoá biểu thất bại",
    },
  ), [runAction]);

  const initManual = useCallback(() => runAction(
    () => scheduler.initManual(),
    {
      onSuccess: (res) => { setData(res); setGuestResult(null); setResidentResult(null); },
      messageFn: () => "Đã xóa dữ liệu cũ, bắt đầu nhập liệu thủ công từ đầu.",
      errorPrefix: "Khởi tạo nhập liệu thủ công thất bại",
    },
  ), [runAction]);

  // Doc file va tra ve ban xem truoc. KHONG setData - buoc nay chua ghi gi ca,
  // nen cung khong duoc dong vao du lieu dang hien tren man.
  const doImportPreview = useCallback((file) => runAction(
    () => scheduler.importPreview(file),
    {
      messageFn: (res) =>
        `Đã đọc "${res.fileName}": ${res.summary.soLopDungDuoc} lớp, ` +
        `${res.summary.soHocPhan} học phần, ${res.summary.soGiangVien} giảng viên — chưa ghi gì.`,
      errorPrefix: "Không đọc được file",
    },
  ), [runAction]);

  // "Buoc 1: chuan hoa du lieu" - doi nguon gio 1 dong dang xem truoc. KHONG
  // setData: pending['data'] moi doi, chua ghi gi vao STATE['data'] thuc (chi
  // doImportCommit moi lam vay) - dialog tu giu ban preview moi tra ve.
  const doImportFixTimeRow = useCallback((excelRow, source) => runAction(
    () => scheduler.importFixTimeRow(excelRow, source),
    { errorPrefix: "Không đổi được nguồn giờ" },
  ), [runAction]);

  const doImportCommit = useCallback(() => runAction(
    () => scheduler.importCommit(),
    {
      onSuccess: (res) => { setData(res); setGuestResult(null); setResidentResult(null); },
      messageFn: (res) =>
        `Đã nạp ${(res.classes || []).length} lớp từ ${res.importedFrom || "file Excel"} — ` +
        `dữ liệu cũ đã bị thay thế.`,
      errorPrefix: "Nạp dữ liệu thất bại",
    },
  ), [runAction]);

  const addManualTeacher = useCallback((payload) => runAction(
    () => scheduler.addManualTeacher(payload),
    {
      onSuccess: setData,
      messageFn: () => `Đã thêm giảng viên "${payload.name}" (${payload.teacherType === "GUEST" ? "thỉnh giảng" : "cơ hữu"}).`,
      errorPrefix: "Thêm giảng viên thất bại",
    },
  ), [runAction]);

  const updateManualTeacher = useCallback((teacherId, payload) => runAction(
    () => scheduler.updateManualTeacher(teacherId, payload),
    {
      onSuccess: setData,
      messageFn: () => (payload.availability
        ? `Đã lưu giờ có thể dạy cho giảng viên #${teacherId}.`
        : `Đã lưu thông tin giảng viên #${teacherId}.`),
      errorPrefix: "Sửa giảng viên thất bại",
    },
  ), [runAction]);

  const addManualCourse = useCallback((payload) => runAction(
    () => scheduler.addManualCourse(payload),
    {
      onSuccess: setData,
      messageFn: () => `Đã thêm học phần "${payload.name}".`,
      errorPrefix: "Thêm học phần thất bại",
    },
  ), [runAction]);

  const updateManualCourse = useCallback((courseId, payload) => runAction(
    () => scheduler.updateManualCourse(courseId, payload),
    {
      onSuccess: setData,
      messageFn: () => `Đã sửa học phần #${courseId}.`,
      errorPrefix: "Sửa học phần thất bại",
    },
  ), [runAction]);

  const addManualSection = useCallback((payload) => runAction(
    () => scheduler.addManualSection(payload),
    {
      onSuccess: setData,
      messageFn: () => `Đã thêm lớp "${payload.classCode || payload.courseId}".`,
      errorPrefix: "Thêm lớp thất bại",
    },
  ), [runAction]);

  const updateManualSection = useCallback((sectionId, payload) => runAction(
    () => scheduler.updateManualSection(sectionId, payload),
    {
      onSuccess: setData,
      messageFn: () => `Đã lưu lớp #${sectionId}.`,
      errorPrefix: "Sửa lớp thất bại",
    },
  ), [runAction]);

  const doClearManualTimes = useCallback((sectionIds) => runAction(
    () => scheduler.clearManualTimes(sectionIds),
    {
      onSuccess: setData,
      messageFn: (res) => `Đã xoá giờ của ${res.clearedCount} lớp — chuyển về "để hệ thống tự xếp".`,
      errorPrefix: "Xoá giờ thất bại",
    },
  ), [runAction]);

  const deleteManualSection = useCallback((sectionId) => runAction(
    () => scheduler.deleteManualSection(sectionId),
    {
      onSuccess: setData,
      messageFn: () => `Đã xóa lớp #${sectionId}.`,
      errorPrefix: "Xóa lớp thất bại",
    },
  ), [runAction]);

  const value = {
    data, guestResult, residentResult, loading, error,
    refreshData, doSubmitAvailability,
    solveGuest, solveResident, doMoveLesson, doClearOverride, doSaveSchedule,
    initManual, doImportPreview, doImportCommit,
    doLecturersPreview, doLecturersCommit, doChotCourse, doBoChotCourse,
    addManualTeacher, updateManualTeacher,
    addManualCourse, updateManualCourse,
    addManualSection, updateManualSection, deleteManualSection, doClearManualTimes,
  };

  return <AppDataContext.Provider value={value}>{children}</AppDataContext.Provider>;
}

export function useAppData() {
  const ctx = useContext(AppDataContext);
  if (!ctx) throw new Error("useAppData phai dung trong AppDataProvider");
  return ctx;
}
