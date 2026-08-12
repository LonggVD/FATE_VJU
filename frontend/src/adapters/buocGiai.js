import { analyzeSubmissions } from "./submissionQueue";

// BA BUOC cua thanh tien trinh (WorkflowStrip) - tach khoi SchedulePage vi day
// la LUAT chu khong phai giao dien: buoc nao xong, nut ghi chu gi, khi nao bi
// khoa. Sua cach dem hay cach dat ten nut thi sua o day, khong phai loi trong
// 700 dong JSX.

// Dem theo GIAI DOAN: bao nhieu lop DA co gio chot san (tu file/go tay) va bao
// nhieu lop CHUA co gio. Con so thu hai moi la VIEC ma nut "Giai" phai lam -
// truoc day nut chi ghi "Giai" nen khong ai doan duoc no se dong vao cai gi.
export function demTheoPha(data) {
  const m = { GUEST: { daChot: 0, chua: 0 }, RESIDENT: { daChot: 0, chua: 0 } };
  for (const c of data?.classes ?? []) {
    const o = m[c.teacherType];
    if (!o) continue;
    if (c.timeAssumed) o.chua += 1;
    else o.daChot += 1;
  }
  return m;
}

// "153/165 đã xếp · 2 không xếp được" - doc mot cai la biet ket qua ra sao.
const ketQua = (res) =>
  `${res.placedCount}/${res.total} đã xếp`
  + (res.unplaced?.length ? ` · ${res.unplaced.length} không xếp được` : "");

// guestResult/residentResult co the la LICH BAN DAU doc tu file (initial), chua
// phai ket qua giai - moi cho hien trang thai deu phai phan biet, khong thi nap
// file xong buoc 2/3 hien "done" ma chua ai bam Giai.
const daGiai = (res) => Boolean(res && !res.initial);

export function buildSteps({
  data, guestResult, residentResult, gd2HetHieuLuc, solveGuest, solveResident,
}) {
  const sq = data ? analyzeSubmissions(data) : null;
  const dem = demTheoPha(data);
  const chuaGiai = (pha) =>
    `${dem[pha].daChot} lớp đã chốt giờ · ${dem[pha].chua} chưa có giờ`;

  return [
    {
      key: "collect",
      label: "Thu giờ",
      value: sq ? `${sq.doneCount}/${sq.guestCount} lớp thỉnh giảng đã báo giờ` : "—",
      state: sq && sq.queue.length === 0 ? "done" : "todo",
    },
    {
      key: "guest",
      label: "Xếp thỉnh giảng",
      value: daGiai(guestResult) ? ketQua(guestResult) : chuaGiai("GUEST"),
      note: daGiai(guestResult)
        ? undefined
        : "Xếp giờ cho các lớp chưa có giờ; lớp đã chốt giữ nguyên chỗ.",
      state: daGiai(guestResult) ? "done" : "todo",
      action: solveGuest,
      // Nut ghi thang VIEC no lam, khong phai chu "Giai" chung chung.
      actionLabel: daGiai(guestResult)
        ? "Xếp lại"
        : dem.GUEST.chua > 0
          ? `Xếp ${dem.GUEST.chua} lớp chưa có giờ`
          : "Xếp lại",
    },
    {
      key: "resident",
      label: "Ghép cơ hữu",
      value: daGiai(residentResult) ? ketQua(residentResult) : chuaGiai("RESIDENT"),
      // Nut buoc 3 bi mo khi chua chay buoc 2 - phai noi VI SAO, khong de nguoi
      // dung bam mai khong duoc ma khong hieu.
      note: !daGiai(guestResult)
        ? "Cần xếp thỉnh giảng (bước 2) trước — cơ hữu ghép vào chỗ còn lại."
        : daGiai(residentResult)
          ? undefined
          : "Ghép các lớp chưa có giờ vào chỗ thỉnh giảng chưa chiếm.",
      state: daGiai(residentResult) ? "done" : "todo",
      // Nghiem GD2 vua bi huy vi buoc 2 chay lai - noi ro, khong de con so lang
      // le tu "158/163" ve "108 buoi chot tu file" (xem gd2HetHieuLuc).
      hint: gd2HetHieuLuc
        ? "Kết quả ghép cơ hữu trước đó đã hết hiệu lực vì vừa xếp lại thỉnh giảng — "
          + "các buổi đang hiện là giờ đã chốt sẵn. Chạy lại bước này."
        : undefined,
      action: solveResident,
      actionLabel: daGiai(residentResult)
        ? "Ghép lại"
        : dem.RESIDENT.chua > 0
          ? `Ghép ${dem.RESIDENT.chua} lớp chưa có giờ`
          : "Ghép lại",
      // Lich ban dau khong tinh la "da chay Giai doan 1" (backend cung chan).
      disabled: !daGiai(guestResult),
    },
  ];
}
