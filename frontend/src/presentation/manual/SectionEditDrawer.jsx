import { useEffect, useState } from "react";
import { CopyPlus, Plus, TriangleAlert, Trash2 } from "lucide-react";
import { useAppData } from "../../context/AppDataContext";
import ClassTimeSlotPicker from "./ClassTimeSlotPicker";
import { FormRow } from "@/components/shared/form-row";
import { Notice } from "@/components/shared/notice";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Drawer, DrawerBody, DrawerSection } from "@/components/ui/drawer";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { NativeSelect } from "@/components/ui/native-select";

const LOCATION_OPTIONS = ["Hòa Lạc", "Mỹ Đình", "Khác"];
const TEACHING_MODE_OPTIONS = ["Trực tiếp", "Trực tuyến", "LMS"];

function suggestTeacherType(org) {
  const t = (org || "").toLowerCase();
  return t.includes("việt nhật") || t.includes("viet nhat") ? "RESIDENT" : "GUEST";
}

function emptyForm() {
  return {
    teacherId: "", courseId: "", classCode: "", program: "",
    ltCredits: "", thCredits: "", cohort: "", expectedStudents: "",
    duration: "2", autoSchedule: true, day: null, periodStart: null, periodEnd: null,
    location: "", teachingMode: "", language: "", otherRequirements: "", notes: "",
    coordinatorOverride: "", prevTeacherName: "", prevTeacherOrg: "",
    teachingHoursLt: "", teachingHoursTh: "",
  };
}

function formFromClass(c) {
  return {
    teacherId: String(c.teacherId), courseId: c.courseId != null ? String(c.courseId) : "",
    classCode: c.classCode || "", program: c.programName || "",
    ltCredits: c.ltCredits ?? "", thCredits: c.thCredits ?? "",
    cohort: c.cohort || "", expectedStudents: c.expectedStudents ?? "",
    duration: String(c.duration ?? "2"), autoSchedule: c.timeAssumed,
    day: c.day, periodStart: c.periodStart, periodEnd: c.periodEnd,
    location: c.location || "", teachingMode: c.teachingMode || "",
    language: c.language || "", otherRequirements: c.otherRequirements || "", notes: c.notes || "",
    coordinatorOverride: c.coordinatorOverride || "",
    prevTeacherName: c.prevTeacherName || "", prevTeacherOrg: c.prevTeacherOrg || "",
    teachingHoursLt: c.teachingHoursLt ?? "", teachingHoursTh: c.teachingHoursTh ?? "",
  };
}

// Side-panel: tao lop moi (section=null) hoac sua lop da co (section=1 dong tu
// data.classes). Tu goi useAppData() truc tiep (khong qua props tu trang cha) vi
// day la 1 "man con" kha doc lap voi nhieu hanh dong rieng (them GV/hoc phan
// nhanh, luu, xoa) - giam prop-drilling qua ManualEntryPage.
export default function SectionEditDrawer({ data, section, onClose, onDuplicated }) {
  const { loading, addManualTeacher, addManualCourse, addManualSection, updateManualSection, deleteManualSection } = useAppData();
  const [form, setForm] = useState(section ? formFromClass(section) : emptyForm());
  const [error, setError] = useState(null);
  const [showAddTeacher, setShowAddTeacher] = useState(false);
  const [showAddCourse, setShowAddCourse] = useState(false);
  const [newTeacher, setNewTeacher] = useState({ name: "", org: "", teacherType: "GUEST" });
  const [newCourse, setNewCourse] = useState({ code: "", name: "", credits: "" });

  // Khoa theo sectionId (so nguyen on dinh), KHONG khoa theo object 'section':
  // moi lan them nhanh GV/hoc phan (+ Giang vien moi/+ Hoc phan moi) lam setData()
  // thay THE CA data -> selectedSection ben ManualEntryPage la object MOI du cung
  // sectionId, neu dependency la object se reset mat sach cac o khac dang go nua
  // chung. Chi reset khi THUC SU chuyen sang sua 1 lop khac (hoac dong/mo lai).
  const sectionKey = section?.sectionId ?? "new";
  useEffect(() => {
    setForm(section ? formFromClass(section) : emptyForm());
    setError(null);
    setShowAddTeacher(false);
    setShowAddCourse(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sectionKey]);

  const teachers = data?.teachers || [];
  const courses = data?.courses || [];
  const numDays = data?.numDays ?? 7;
  const slotsPerDay = data?.slotsPerDay ?? 12;
  const selectedTeacher = teachers.find((t) => String(t.id) === String(form.teacherId));

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));

  const submitNewTeacher = async (e) => {
    e.preventDefault();
    if (!newTeacher.name.trim()) return;
    const res = await addManualTeacher({
      name: newTeacher.name.trim(), org: newTeacher.org.trim(), teacherType: newTeacher.teacherType,
    });
    const created = res.teachers[res.teachers.length - 1];
    setForm((f) => ({ ...f, teacherId: String(created.id) }));
    setNewTeacher({ name: "", org: "", teacherType: "GUEST" });
    setShowAddTeacher(false);
  };

  const submitNewCourse = async (e) => {
    e.preventDefault();
    if (!newCourse.name.trim()) return;
    const res = await addManualCourse({
      code: newCourse.code.trim(), name: newCourse.name.trim(),
      credits: newCourse.credits === "" ? null : Number(newCourse.credits),
    });
    const created = res.courses[res.courses.length - 1];
    setForm((f) => ({ ...f, courseId: String(created.id) }));
    setNewCourse({ code: "", name: "", credits: "" });
    setShowAddCourse(false);
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setError(null);
    if (!form.teacherId) return setError("Chưa chọn giảng viên.");
    if (!form.courseId) return setError("Chưa chọn học phần.");
    if (!form.duration || Number(form.duration) <= 0) return setError("Số tiết mỗi buổi dạy phải > 0.");
    if (!form.autoSchedule && (form.day == null || form.periodStart == null)) {
      return setError("Chưa chọn giờ — bấm chọn Thứ/Tiết, hoặc tick \"Để hệ thống tự xếp\".");
    }

    const payload = {
      teacherId: Number(form.teacherId), courseId: Number(form.courseId),
      classCode: form.classCode.trim(), program: form.program.trim(),
      ltCredits: form.ltCredits === "" ? 0 : Number(form.ltCredits),
      thCredits: form.thCredits === "" ? 0 : Number(form.thCredits),
      cohort: form.cohort.trim(),
      expectedStudents: form.expectedStudents === "" ? null : Number(form.expectedStudents),
      duration: Number(form.duration),
      location: form.location, teachingMode: form.teachingMode,
      language: form.language.trim(), otherRequirements: form.otherRequirements.trim(),
      notes: form.notes.trim(), coordinatorOverride: form.coordinatorOverride.trim(),
      prevTeacherName: form.prevTeacherName.trim(), prevTeacherOrg: form.prevTeacherOrg.trim(),
      teachingHoursLt: form.teachingHoursLt === "" ? null : Number(form.teachingHoursLt),
      teachingHoursTh: form.teachingHoursTh === "" ? null : Number(form.teachingHoursTh),
    };
    if (form.autoSchedule) {
      payload.autoSchedule = true;
    } else {
      payload.day = form.day;
      payload.periodStart = form.periodStart;
      payload.periodEnd = form.periodEnd;
    }

    try {
      if (section) await updateManualSection(section.sectionId, payload);
      else await addManualSection(payload);
      onClose();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDelete = async () => {
    if (!section) return;
    if (!window.confirm(`Xóa lớp "${section.classCode || section.courseName}" (#${section.sectionId})? Không thể hoàn tác.`)) return;
    await deleteManualSection(section.sectionId);
    onClose();
  };

  // "1 lop hoc N buoi/tuan khac ngay" = N dong cung Ma lop, khac Thoi gian (xem
  // giai thich voi giao vu) - nut nay sao chep MOI THONG TIN DANG CO trong form
  // (hoc phan/GV/TC/dia diem...) sang 1 dong MOI, CHI xoa rieng gio (bat auto)
  // de khoi phai go lai tu dau, rieng gio thi bat buoc chon lai cho buoi khac.
  const handleDuplicate = async () => {
    setError(null);
    if (!form.teacherId || !form.courseId) {
      return setError("Cần chọn học phần và giảng viên trước khi nhân bản.");
    }
    const payload = {
      teacherId: Number(form.teacherId), courseId: Number(form.courseId),
      classCode: form.classCode.trim(), program: form.program.trim(),
      ltCredits: form.ltCredits === "" ? 0 : Number(form.ltCredits),
      thCredits: form.thCredits === "" ? 0 : Number(form.thCredits),
      cohort: form.cohort.trim(),
      expectedStudents: form.expectedStudents === "" ? null : Number(form.expectedStudents),
      duration: Number(form.duration) || 2,
      location: form.location, teachingMode: form.teachingMode,
      language: form.language.trim(), otherRequirements: form.otherRequirements.trim(),
      notes: form.notes.trim(), coordinatorOverride: form.coordinatorOverride.trim(),
      prevTeacherName: form.prevTeacherName.trim(), prevTeacherOrg: form.prevTeacherOrg.trim(),
      teachingHoursLt: form.teachingHoursLt === "" ? null : Number(form.teachingHoursLt),
      teachingHoursTh: form.teachingHoursTh === "" ? null : Number(form.teachingHoursTh),
      autoSchedule: true, // buoi moi CHUA co gio - bat GV chon rieng cho buoi nay
    };
    try {
      const res = await addManualSection(payload);
      const created = res.classes[res.classes.length - 1];
      onDuplicated?.(created.sectionId);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <Drawer
      open
      onOpenChange={(o) => !o && onClose()}
      title={section ? `Sửa lớp #${section.sectionId}` : "Thêm lớp mới"}
      description={section?.courseName || undefined}
      footer={
        <>
          {section && (
            <Button
              type="button"
              variant="outline"
              className="text-destructive mr-auto"
              disabled={loading}
              onClick={handleDelete}
            >
              <Trash2 className="size-4" />
              Xóa lớp
            </Button>
          )}
          {section && (
            <Button type="button" variant="outline" disabled={loading} onClick={handleDuplicate}>
              <CopyPlus className="size-4" />
              Thêm buổi khác
            </Button>
          )}
          {/* "Hủy" ro rang canh "Lưu" - dua vao dau X goc tren hoac Esc de
              thoat la bat nguoi dung phai DOAN rang bo di thi khong ghi gi. */}
          <Button type="button" variant="outline" disabled={loading} onClick={onClose}>
            Hủy
          </Button>
          <Button type="submit" form="section-form" disabled={loading}>
            {loading ? "Đang lưu…" : "Lưu"}
          </Button>
        </>
      }
    >
      <form id="section-form" onSubmit={handleSave} className="flex min-h-0 flex-1 flex-col">
        <DrawerBody>
          {error && (
            <Notice tone="red" icon={TriangleAlert}>
              {error}
            </Notice>
          )}

          <DrawerSection title="Học phần">
            <FormRow label="Học phần" required>
              {(id) => (
                <NativeSelect id={id} className="w-full" value={form.courseId} onChange={set("courseId")}>
                  <option value="">— Chọn học phần —</option>
                  {courses.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.code ? `${c.code} — ${c.name}` : c.name}
                    </option>
                  ))}
                </NativeSelect>
              )}
            </FormRow>
            {!showAddCourse ? (
              <Button type="button" variant="ghost" size="sm" onClick={() => setShowAddCourse(true)}>
                <Plus className="size-4" />
                Học phần mới
              </Button>
            ) : (
              <div className="bg-muted/40 flex flex-wrap items-center gap-2 rounded-lg border p-2.5">
                <Input
                  className="w-32"
                  placeholder="Mã HP"
                  value={newCourse.code}
                  onChange={(e) => setNewCourse((f) => ({ ...f, code: e.target.value }))}
                />
                <Input
                  className="min-w-40 flex-1"
                  placeholder="Tên học phần"
                  value={newCourse.name}
                  onChange={(e) => setNewCourse((f) => ({ ...f, name: e.target.value }))}
                />
                <Input
                  className="w-20"
                  placeholder="Số TC"
                  type="number"
                  min={0}
                  value={newCourse.credits}
                  onChange={(e) => setNewCourse((f) => ({ ...f, credits: e.target.value }))}
                />
                <Button type="button" size="sm" onClick={submitNewCourse}>Thêm</Button>
                <Button type="button" variant="outline" size="sm" onClick={() => setShowAddCourse(false)}>
                  Hủy
                </Button>
              </div>
            )}
          </DrawerSection>

          <DrawerSection title="Lớp học phần">
            <FormRow label="Mã lớp">
              {(id) => <Input id={id} value={form.classCode} onChange={set("classCode")} placeholder="IT101.1" />}
            </FormRow>
            <FormRow label="Chương trình (CTĐT)">
              {(id) => <Input id={id} value={form.program} onChange={set("program")} placeholder="BCSE" />}
            </FormRow>
            <FormRow label="Phân bổ TC (LT / TH)">
              <div className="flex gap-2">
                <Input type="number" min={0} step="0.5" value={form.ltCredits} onChange={set("ltCredits")} placeholder="Lý thuyết" />
                <Input type="number" min={0} step="0.5" value={form.thCredits} onChange={set("thCredits")} placeholder="Thực hành" />
              </div>
            </FormRow>
            <FormRow label="Khóa">
              {(id) => <Input id={id} value={form.cohort} onChange={set("cohort")} placeholder="K68" />}
            </FormRow>
            <FormRow label="Số SV dự kiến">
              {(id) => <Input id={id} type="number" min={0} value={form.expectedStudents} onChange={set("expectedStudents")} />}
            </FormRow>
            <FormRow label="Số tiết / buổi" required>
              {(id) => <Input id={id} type="number" min={1} max={12} required value={form.duration} onChange={set("duration")} />}
            </FormRow>
          </DrawerSection>

          <DrawerSection title="Thời gian">
            <Label htmlFor="sed-auto" className="text-sm font-normal">
              <Checkbox
                id="sed-auto"
                checked={form.autoSchedule}
                onCheckedChange={(v) =>
                  setForm((f) => ({
                    ...f,
                    autoSchedule: v === true,
                    day: null, periodStart: null, periodEnd: null,
                  }))
                }
              />
              Để hệ thống tự xếp giờ
            </Label>
            {!form.autoSchedule && (
              <ClassTimeSlotPicker
                numDays={numDays} slotsPerDay={slotsPerDay}
                value={form.day != null ? { day: form.day, periodStart: form.periodStart, periodEnd: form.periodEnd } : null}
                onChange={(v) => setForm((f) => ({ ...f, day: v?.day ?? null, periodStart: v?.periodStart ?? null, periodEnd: v?.periodEnd ?? null }))}
              />
            )}
          </DrawerSection>

          <DrawerSection title="Giảng viên kỳ này">
            <FormRow label="Giảng viên" required hint={selectedTeacher?.org || undefined}>
              {(id) => (
                <NativeSelect id={id} className="w-full" value={form.teacherId} onChange={set("teacherId")}>
                  <option value="">— Chọn giảng viên —</option>
                  {teachers.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.name} · {t.type === "GUEST" ? "Thỉnh giảng" : "Cơ hữu"}
                    </option>
                  ))}
                </NativeSelect>
              )}
            </FormRow>
            {!showAddTeacher ? (
              <Button type="button" variant="ghost" size="sm" onClick={() => setShowAddTeacher(true)}>
                <Plus className="size-4" />
                Giảng viên mới
              </Button>
            ) : (
              <div className="bg-muted/40 flex flex-wrap items-center gap-2 rounded-lg border p-2.5">
                <Input
                  className="min-w-36 flex-1"
                  placeholder="Họ tên"
                  value={newTeacher.name}
                  onChange={(e) => setNewTeacher((f) => ({ ...f, name: e.target.value }))}
                />
                <Input
                  className="min-w-36 flex-1"
                  placeholder="Đơn vị công tác"
                  value={newTeacher.org}
                  onChange={(e) =>
                    setNewTeacher((f) => ({ ...f, org: e.target.value, teacherType: suggestTeacherType(e.target.value) }))
                  }
                />
                <NativeSelect
                  value={newTeacher.teacherType}
                  onChange={(e) => setNewTeacher((f) => ({ ...f, teacherType: e.target.value }))}
                >
                  <option value="GUEST">Thỉnh giảng</option>
                  <option value="RESIDENT">Cơ hữu</option>
                </NativeSelect>
                <Button type="button" size="sm" onClick={submitNewTeacher}>Thêm</Button>
                <Button type="button" variant="outline" size="sm" onClick={() => setShowAddTeacher(false)}>
                  Hủy
                </Button>
              </div>
            )}
          </DrawerSection>

          <DrawerSection
            title="Giảng viên kỳ trước"
            hint="Chỉ để đối chiếu, không dùng để xếp lịch."
          >
            <FormRow label="Họ tên">
              {(id) => <Input id={id} value={form.prevTeacherName} onChange={set("prevTeacherName")} placeholder="Không bắt buộc" />}
            </FormRow>
            <FormRow label="Đơn vị công tác">
              {(id) => <Input id={id} value={form.prevTeacherOrg} onChange={set("prevTeacherOrg")} placeholder="Không bắt buộc" />}
            </FormRow>
          </DrawerSection>

          <DrawerSection title="Giờ dạy & hình thức">
            <FormRow label="Số giờ dạy (LT / TH)">
              <div className="flex gap-2">
                <Input type="number" min={0} value={form.teachingHoursLt} onChange={set("teachingHoursLt")} placeholder="Lý thuyết" />
                <Input type="number" min={0} value={form.teachingHoursTh} onChange={set("teachingHoursTh")} placeholder="Thực hành" />
              </div>
            </FormRow>
            <FormRow label="Địa điểm giảng dạy">
              {(id) => (
                <NativeSelect id={id} className="w-full" value={form.location} onChange={set("location")}>
                  <option value="">— Không rõ —</option>
                  {LOCATION_OPTIONS.map((l) => <option key={l} value={l}>{l}</option>)}
                </NativeSelect>
              )}
            </FormRow>
            <FormRow label="Hình thức giảng dạy">
              {(id) => (
                <NativeSelect id={id} className="w-full" value={form.teachingMode} onChange={set("teachingMode")}>
                  <option value="">— Không rõ —</option>
                  {TEACHING_MODE_OPTIONS.map((m) => <option key={m} value={m}>{m}</option>)}
                </NativeSelect>
              )}
            </FormRow>
          </DrawerSection>

          <details className="rounded-lg border">
            <summary className="hover:bg-muted/60 cursor-pointer rounded-lg px-3 py-2 text-sm font-medium">
              Khác (ngôn ngữ, yêu cầu khác, ghi chú, điều phối viên)
            </summary>
            <div className="space-y-3 border-t px-3 py-3">
              <FormRow label="Ngôn ngữ giảng dạy">
                {(id) => <Input id={id} value={form.language} onChange={set("language")} placeholder="Không bắt buộc" />}
              </FormRow>
              <FormRow label="Yêu cầu khác">
                {(id) => <Input id={id} value={form.otherRequirements} onChange={set("otherRequirements")} placeholder="Không bắt buộc" />}
              </FormRow>
              <FormRow label="Ghi chú">
                {(id) => <Input id={id} value={form.notes} onChange={set("notes")} placeholder="Không bắt buộc" />}
              </FormRow>
              <FormRow label="Điều phối viên">
                {(id) => <Input id={id} value={form.coordinatorOverride} onChange={set("coordinatorOverride")} placeholder="Nếu khác mặc định" />}
              </FormRow>
            </div>
          </details>
        </DrawerBody>
      </form>
    </Drawer>
  );
}
