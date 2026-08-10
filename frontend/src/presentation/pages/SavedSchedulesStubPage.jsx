import { PagePlaceholder } from "@/components/shared/page-placeholder";

export default function SavedSchedulesStubPage() {
  return (
    <PagePlaceholder
      title="Lịch đã lưu"
      description="Hiện demo chỉ giữ 1 phương án đang làm việc trong bộ nhớ máy chủ (Giai đoạn 1 + Giai đoạn 2)."
      todo={[
        "Lưu nhiều phương án xếp lịch, đặt tên và ghi chú cho từng bản",
        "So sánh hai phương án cạnh nhau (số buổi xếp được, số vấn đề còn lại)",
        "Khôi phục một bản đã lưu về làm phương án đang làm việc",
      ]}
    />
  );
}
