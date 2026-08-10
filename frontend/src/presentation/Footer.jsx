// Ban cu la mot khoi 3 cot nen do dam, trong do 2/3 noi dung ("cong cu demo",
// "khong dung de van hanh chinh thuc") gio da nam o bang canh bao ho phach tren
// cung - lap lai o day vua thua vua chiem cho. Chi giu lai phan KHONG trung: he
// thuat toan va nguon du lieu.
export default function Footer() {
  return (
    <footer className="text-muted-foreground border-t px-4 py-3 text-xs md:px-6">
      <p>
        Thuật toán CP-SAT (Google OR-Tools) — 2 giai đoạn thỉnh giảng/cơ hữu · Dữ liệu
        nhập tay hoặc nạp từ file kế hoạch giảng dạy Excel
      </p>
    </footer>
  );
}
