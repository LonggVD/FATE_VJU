import { useEffect, useState } from "react";
import { TriangleAlert } from "lucide-react";
import { useAppData } from "../../context/AppDataContext";
import SubmissionWindowGrid from "../submissions/SubmissionWindowGrid";
import { FormRow } from "@/components/shared/form-row";
import { Notice } from "@/components/shared/notice";
import { Button } from "@/components/ui/button";
import { Drawer, DrawerBody, DrawerSection } from "@/components/ui/drawer";
import { Input } from "@/components/ui/input";
import { NativeSelect } from "@/components/ui/native-select";

function suggestTeacherType(org) {
  const t = (org || "").toLowerCase();
  return t.includes("việt nhật") || t.includes("viet nhat") ? "RESIDENT" : "GUEST";
}

function emptyForm() {
  return { name: "", org: "", title: "", email: "", phone: "", teacherType: "GUEST" };
}
function formFromTeacher(t) {
  return {
    name: t.nameRaw || "", org: t.org || "", title: t.title || "",
    email: t.email || "", phone: t.phone || "", teacherType: t.type,
  };
}

// Form RIENG cho 1 giang vien: thong tin ca nhan + (chi GUEST) gio co the day -
// tach khoi SectionEditDrawer vi day la du lieu cua RIENG GV, dung chung cho
// nhieu lop (sua o day anh huong tat ca lop cua GV nay). 2 khoi luu DOC LAP
// (thong tin va gio ranh) - KHONG gop thanh 1 nut chung, vi luc TAO MOI chua
// co id de gan gio ranh (phai tao xong GV truoc), va SubmissionWindowGrid von
// da co san nut luu rieng, tai dung nguyen khong sua de khong dong den 1
// component dang dung o man "Khung gio da bao".
export default function TeacherEditDrawer({ data, teacher, classes = [], onClose }) {
  const { loading, addManualTeacher, updateManualTeacher } = useAppData();
  const [teacherId, setTeacherId] = useState(teacher?.id ?? null);
  const [form, setForm] = useState(teacher ? formFromTeacher(teacher) : emptyForm());
  const [typeTouched, setTypeTouched] = useState(Boolean(teacher));
  const [error, setError] = useState(null);
  const teacherKey = teacher?.id ?? "new";

  useEffect(() => {
    setTeacherId(teacher?.id ?? null);
    setForm(teacher ? formFromTeacher(teacher) : emptyForm());
    setTypeTouched(Boolean(teacher));
    setError(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [teacherKey]);

  // "Gio co the day" chi ap dung cho GUEST, gioi han toi Thu 7 (index 5) -
  // dung quy tac sc.MAX_DAY_INDEX["GUEST"] o backend, tranh tick o Chu nhat
  // roi bi tu choi khi luu.
  const numDays = Math.min(data?.numDays ?? 7, 6);
  const slotsPerDay = data?.slotsPerDay ?? 12;
  // Sau khi vua tao xong trong phien nay, doc lai ban ghi moi nhat tu
  // data.teachers de co availabilitySlots hien tai (form nay khong tu giu).
  const liveTeacher = teacherId != null ? (data?.teachers || []).find((t) => t.id === teacherId) : null;

  const setField = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));

  const handleSaveInfo = async (e) => {
    e.preventDefault();
    setError(null);
    if (!form.name.trim()) return setError("Chưa nhập Họ tên.");
    const payload = {
      name: form.name.trim(), org: form.org.trim(), title: form.title.trim(),
      email: form.email.trim(), phone: form.phone.trim(), teacherType: form.teacherType,
    };
    try {
      if (teacherId != null) {
        await updateManualTeacher(teacherId, payload);
      } else {
        const res = await addManualTeacher(payload);
        const created = res.teachers[res.teachers.length - 1];
        setTeacherId(created.id); // khong dong drawer - de khai tiep gio ranh ngay neu la GUEST
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const handleSaveAvailability = async (slots) => {
    if (teacherId == null) return;
    await updateManualTeacher(teacherId, { availability: slots });
  };

  return (
    <Drawer
      open
      onOpenChange={(o) => !o && onClose()}
      title={teacherId != null ? `Sửa giảng viên #${teacherId}` : "Thêm giảng viên mới"}
      description="Sửa ở đây áp dụng cho mọi lớp của giảng viên này."
    >
      <DrawerBody>
        {error && (
          <Notice tone="red" icon={TriangleAlert}>
            {error}
          </Notice>
        )}

        <form onSubmit={handleSaveInfo}>
          <DrawerSection title="Thông tin giảng viên">
            <FormRow label="Học hàm/học vị">
              {(id) => (
                <Input
                  id={id}
                  value={form.title}
                  onChange={setField("title")}
                  placeholder="TS., PGS.TS… (không bắt buộc)"
                />
              )}
            </FormRow>
            <FormRow label="Họ tên" required>
              {(id) => (
                <Input
                  id={id}
                  value={form.name}
                  onChange={setField("name")}
                  placeholder="Nguyễn Văn A"
                  required
                />
              )}
            </FormRow>
            <FormRow label="Đơn vị công tác">
              {(id) => (
                <Input
                  id={id}
                  value={form.org}
                  onChange={(e) => {
                    const org = e.target.value;
                    setForm((f) => ({
                      ...f,
                      org,
                      teacherType: typeTouched ? f.teacherType : suggestTeacherType(org),
                    }));
                  }}
                  placeholder="Trường Đại học Việt Nhật / Trường ABC…"
                />
              )}
            </FormRow>
            <FormRow label="Loại giảng viên">
              {(id) => (
                <>
                  <NativeSelect
                    id={id}
                    className="w-full"
                    value={form.teacherType}
                    onChange={(e) => {
                      setTypeTouched(true);
                      setForm((f) => ({ ...f, teacherType: e.target.value }));
                    }}
                  >
                    <option value="GUEST">Thỉnh giảng</option>
                    <option value="RESIDENT">Cơ hữu</option>
                  </NativeSelect>
                  {/* Danh sach co huu la NGUON CHINH THUC: nap lai file danh sach
                      se ghi de lua chon tay o day. Noi truoc, khong de nguoi dung
                      sua roi thay no tu quay lai. */}
                  {teacher?.inLecturerList === false && form.teacherType === "RESIDENT" && (
                    <p className="text-muted-foreground mt-1 text-xs">
                      Người này <strong>không có trong danh sách cơ hữu</strong> — nạp lại danh sách
                      sẽ chuyển họ về thỉnh giảng. Nên bổ sung vào file danh sách.
                    </p>
                  )}
                  {teacher?.inLecturerList === true && form.teacherType === "GUEST" && (
                    <p className="text-muted-foreground mt-1 text-xs">
                      Người này <strong>có trong danh sách cơ hữu</strong> — nạp lại danh sách sẽ
                      chuyển họ về cơ hữu.
                    </p>
                  )}
                </>
              )}
            </FormRow>
            <FormRow label="Email">
              {(id) => (
                <Input
                  id={id}
                  type="email"
                  value={form.email}
                  onChange={setField("email")}
                  placeholder="Không bắt buộc"
                />
              )}
            </FormRow>
            <FormRow label="Số điện thoại">
              {(id) => (
                <Input
                  id={id}
                  value={form.phone}
                  onChange={setField("phone")}
                  placeholder="Không bắt buộc"
                />
              )}
            </FormRow>

            {/* Nut nam TRONG muc thong tin chu khong o chan ngan keo: ngan keo
                nay co HAI viec luu doc lap (thong tin GV va gio co the day),
                mot nut "Lưu" chung o chan se khong biet dang luu cai nao. */}
            <div className="flex justify-end gap-2">
              <Button type="button" variant="outline" disabled={loading} onClick={onClose}>
                Hủy
              </Button>
              <Button type="submit" disabled={loading}>
                {loading ? "Đang lưu…" : teacherId != null ? "Lưu thông tin" : "Tạo giảng viên"}
              </Button>
            </div>
          </DrawerSection>
        </form>

        {/* Khai gio cho MOI giang vien (ca co huu) va co TAC DUNG THAT: da khai
            thi chi xep trong khung do. Luoi con hien them cac o nguoi nay DANG
            DAY (suy tu lop da chot gio) bang mau nhat - de nap file xong nhin ra
            ngay "nguoi nay dang day T5 tiet 3-5", chu khong phai luoi trong tron.
            Hai loai o KHONG tron lam mot: xem chu thich o SubmissionWindowGrid. */}
        {teacherId != null && (
          <DrawerSection
            title="Giờ có thể dạy"
            hint="Tick MỌI tiết giảng viên rảnh trong tuần (không chỉ tiết bắt đầu). ĐÃ KHAI = giới hạn cứng: các lớp chưa có giờ của giảng viên này chỉ được xếp trong khung đã tick. Chưa khai gì thì hệ thống tự do xếp cả tuần. Ô xanh nhạt là giờ đang dạy theo lớp đã chốt — chỉ để tham khảo, không phải khung đã khai."
          >
            {(liveTeacher?.teachingSlots || []).length > 0 && (
              <p className="text-muted-foreground text-xs">
                Đang dạy {liveTeacher.teachingSlots.length} tiết theo các lớp đã chốt giờ.{" "}
                <button
                  type="button"
                  className="font-medium underline"
                  disabled={loading}
                  onClick={() => handleSaveAvailability(
                    [...new Set([...(liveTeacher.availabilitySlots || []), ...liveTeacher.teachingSlots])],
                  )}
                >
                  Lấy các giờ đang dạy làm khung đã khai
                </button>{" "}
                — chỉ bấm nếu giảng viên CHỈ dạy được đúng những giờ đó.
              </p>
            )}
            <SubmissionWindowGrid
              numDays={numDays} slotsPerDay={slotsPerDay}
              initialSlots={liveTeacher?.availabilitySlots || []}
              teachingSlots={liveTeacher?.teachingSlots || []}
              saving={loading}
              allowEmpty
              saveLabel={(n) => (n === 0 ? "Xóa hết giờ rảnh" : `Lưu ${n} khung giờ`)}
              onSave={handleSaveAvailability}
            />
          </DrawerSection>
        )}

        {/* CAC LOP KY NAY - de sua thong tin GV ma van thay ngay ho dang day gi,
            khong phai mo bang lop o man khac roi loc tay. */}
        {teacherId != null && classes.length > 0 && (
          <DrawerSection
            title={`Lớp kỳ này (${classes.length})`}
            hint="Các lớp giảng viên này đang dạy, kể cả lớp đồng giảng với người khác."
          >
            <div className="max-h-64 space-y-1 overflow-y-auto text-xs">
              {classes.map((c) => (
                <div key={c.sectionId} className="bg-muted/40 rounded-md border px-2 py-1.5">
                  <div className="flex items-baseline justify-between gap-2">
                    <span className="min-w-0 truncate font-medium">
                      {c.classCode || `#${c.sectionId}`} · {c.courseName}
                    </span>
                    <span className="text-muted-foreground shrink-0">
                      {c.day == null || c.periodStart == null
                        ? "chưa có giờ"
                        : `${c.day === 6 ? "CN" : `T${c.day + 2}`} tiết ${c.periodStart}-${c.periodEnd}`}
                    </span>
                  </div>
                  {(c.teacherIds ?? []).length > 1 && (
                    <div className="text-muted-foreground">
                      Đồng giảng: {(c.teachers ?? []).map((t) => t.name).join(", ")}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </DrawerSection>
        )}

        {teacherId == null && (
          <p className="text-muted-foreground text-xs">
            Tạo giảng viên xong sẽ hiện thêm mục khai giờ có thể dạy.
          </p>
        )}
      </DrawerBody>
    </Drawer>
  );
}
