import { useEffect, useState } from "react";
import { TriangleAlert } from "lucide-react";
import { useAppData } from "../../context/AppDataContext";
import { FormRow } from "@/components/shared/form-row";
import { Notice } from "@/components/shared/notice";
import { Button } from "@/components/ui/button";
import { Drawer, DrawerBody, DrawerSection } from "@/components/ui/drawer";
import { Input } from "@/components/ui/input";

function emptyForm() {
  return { code: "", name: "", credits: "" };
}
function formFromCourse(c) {
  return { code: c.code || "", name: c.name || "", credits: c.credits ?? "" };
}

// Form RIENG cho 1 hoc phan (Ma HP/Ten HP/So TC) - tach khoi SectionEditDrawer
// vi day la thong tin dung CHUNG cho nhieu lop, sua o day anh huong tat ca lop
// thuoc hoc phan nay (khong gan voi 1 lop cu the).
export default function CourseEditDrawer({ course, onClose }) {
  const { loading, addManualCourse, updateManualCourse } = useAppData();
  const [form, setForm] = useState(course ? formFromCourse(course) : emptyForm());
  const [error, setError] = useState(null);
  const courseKey = course?.id ?? "new";

  useEffect(() => {
    setForm(course ? formFromCourse(course) : emptyForm());
    setError(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [courseKey]);

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));

  const handleSave = async (e) => {
    e.preventDefault();
    setError(null);
    if (!form.name.trim()) return setError("Chưa nhập Tên học phần.");
    const payload = {
      code: form.code.trim(), name: form.name.trim(),
      credits: form.credits === "" ? null : Number(form.credits),
    };
    try {
      if (course) await updateManualCourse(course.id, payload);
      else await addManualCourse(payload);
      onClose();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <Drawer
      open
      onOpenChange={(o) => !o && onClose()}
      title={course ? `Sửa học phần #${course.id}` : "Thêm học phần mới"}
      description={
        course ? "Sửa ở đây áp dụng cho tất cả lớp thuộc học phần này." : undefined
      }
      className="max-w-md"
      footer={
        <>
          <Button type="button" variant="outline" disabled={loading} onClick={onClose}>
            Hủy
          </Button>
          <Button type="submit" form="course-form" disabled={loading}>
            {loading ? "Đang lưu…" : "Lưu"}
          </Button>
        </>
      }
    >
      <form id="course-form" onSubmit={handleSave} className="flex min-h-0 flex-1 flex-col">
        <DrawerBody>
          {error && (
            <Notice tone="red" icon={TriangleAlert}>
              {error}
            </Notice>
          )}

          <DrawerSection title="Học phần">
            <FormRow label="Mã học phần">
              {(id) => (
                <Input id={id} value={form.code} onChange={set("code")} placeholder="IT101" />
              )}
            </FormRow>
            <FormRow label="Tên học phần" required>
              {(id) => (
                <Input
                  id={id}
                  value={form.name}
                  onChange={set("name")}
                  placeholder="Nhập môn Công nghệ thông tin"
                  required
                />
              )}
            </FormRow>
            <FormRow label="Số tín chỉ">
              {(id) => (
                <Input
                  id={id}
                  type="number"
                  min={0}
                  value={form.credits}
                  onChange={set("credits")}
                />
              )}
            </FormRow>
          </DrawerSection>
        </DrawerBody>
      </form>
    </Drawer>
  );
}
