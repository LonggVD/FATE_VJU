import { useMemo, useState } from "react";
import { useAppData } from "../../context/AppDataContext";
import SubmissionWindowGrid, { EditAvailabilityButton } from "../submissions/SubmissionWindowGrid";
import { DAY_LABELS } from "../../adapters/dayPeriod";
import { FilterSelect } from "@/components/shared/filter-select";
import { ListSearch } from "@/components/shared/list-search";
import { Notice } from "@/components/shared/notice";
import { Pill } from "@/components/shared/pill";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { NativeSelect } from "@/components/ui/native-select";

// Tone thay cho class danger/warn/ok cu - dong bo voi ManualEntryPage.
const STATUS_META = {
  missing_time: { label: "Thiếu giờ", tone: "red" },
  ready_auto: { label: "Tự động xếp", tone: "amber" },
  ready_fixed: { label: "Có giờ cố định", tone: "emerald" },
};

function dayNumber(day) {
  if (day == null) return "";
  return day === 6 ? "CN" : day + 2;
}

// Nen 1 list slot roi rac thanh cau doc duoc: [12,13,14,25] -> "T3 tiết 1-3 · T4
// tiết 2". O che do XEM nguoi dung can doc duoc ngay GV ranh khi nao, khong nen
// bat ho tu do lai 84 o trong luoi.
function moTaGioRanh(slots = [], slotsPerDay) {
  const theoNgay = new Map();
  for (const s of [...slots].sort((a, b) => a - b)) {
    const day = Math.floor(s / slotsPerDay);
    const period = (s % slotsPerDay) + 1;
    if (!theoNgay.has(day)) theoNgay.set(day, []);
    theoNgay.get(day).push(period);
  }
  const phan = [];
  for (const [day, tiets] of [...theoNgay.entries()].sort((a, b) => a[0] - b[0])) {
    const nhan = (DAY_LABELS[day] ?? `N${day + 1}`)
      .replace("Thứ ", "T")
      .replace("Chủ nhật", "CN");
    const doan = [];
    let dau = tiets[0];
    let truoc = tiets[0];
    for (const t of tiets.slice(1)) {
      if (t === truoc + 1) { truoc = t; continue; }
      doan.push(dau === truoc ? `${dau}` : `${dau}-${truoc}`);
      dau = truoc = t;
    }
    doan.push(dau === truoc ? `${dau}` : `${dau}-${truoc}`);
    phan.push(`${nhan} tiết ${doan.join(", ")}`);
  }
  return phan;
}

// Trang KHAI + SUA gio co the day cua giang vien thinh giang, tra cuu theo
// Khoa/Nganh/Hoc phan/Ten GV. Chi hien luoi cho DUNG 1 GV dang chon - khong ve
// chong nhieu luoi cung luc.
//
// Truoc day trang nay CHI DE XEM, cho khai gio nam trong TeacherEditDrawer ben
// "Dữ liệu học phần" - nhung ten muc ("Chuẩn bị dữ liệu → Giờ rảnh GV") va cau
// "Giảng viên này chưa khai giờ rảnh nào" thi hua hen khai duoc, ma bam vao
// khong co gi xay ra. Nay dung thang SubmissionWindowGrid nhu drawer va man
// "Khung giờ đã báo" - mot cach tuong tac duy nhat cho ca ba cho, khong che
// them kieu click rieng.
//
// MAC DINH LA XEM: vao trang thay gio da luu (luoi readOnly + cau tom tat), bam
// "Chỉnh sửa" moi vao che do sua, xong bam "Lưu" hoac "Hủy". Ban truoc luon o
// che do sua nen khong phan biet duoc du lieu that voi thao tac dang do.
export default function TeacherAvailabilityPage({ role }) {
  const { data, loading, updateManualTeacher } = useAppData();
  const canEdit = role !== "viewer";
  const [editing, setEditing] = useState(false);
  const [facultyFilter, setFacultyFilter] = useState("");
  const [programFilter, setProgramFilter] = useState("");
  const [courseFilter, setCourseFilter] = useState("");
  const [search, setSearch] = useState("");
  const [selectedId, setSelectedId] = useState(null);

  // Trang nay chi danh cho GV THINH GIANG khai gio ranh - gioi han toi Thu 7
  // (index 5), dung quy tac sc.MAX_DAY_INDEX["GUEST"] o backend.
  const numDays = Math.min(data?.numDays ?? 7, 6);
  const slotsPerDay = data?.slotsPerDay ?? 12;

  // Voi moi GV thinh giang, gop lai cac Khoa/Nganh(CTDT)/Hoc phan ho dang day
  // (suy tu data.classes - moi lop 1 dong, da co san courseName/programName/
  // programLabel). programName la ma nganh THAT (BCSE, ESAS...) - loc theo
  // truong nay huu ich hon Khoa, vi du lieu nhap tay hien gio toan bo CTDT
  // deu roi vao chung 1 Khoa mac dinh "Chua phan khoa".
  const teacherMeta = useMemo(() => {
    const map = new Map();
    for (const c of data?.classes || []) {
      if (c.teacherType !== "GUEST") continue;
      if (!map.has(c.teacherId)) map.set(c.teacherId, { courses: new Set(), faculties: new Set(), programs: new Set(), classes: [] });
      const m = map.get(c.teacherId);
      if (c.courseName) m.courses.add(c.courseName);
      // MA DON, khong phai nguyen van o: lop "BCSE+MJM" phai ra ca khi loc BCSE
      // lan khi loc MJM.
      for (const ma of c.programParts ?? []) m.programs.add(ma);
      // Ten Khoa lay thang tu backend. Truoc day boc tu phan trong ngoac cuoi
      // programLabel ("BCSE (Chưa phân khoa)") - vo ngay khi nhan chuyen sang
      // nguyen van nhu file ("BCSE+MJM", khong con ngoac) va bo loc Khoa rong tron.
      if (c.facultyName) m.faculties.add(c.facultyName);
      m.classes.push(c);
    }
    return map;
  }, [data]);

  const faculties = useMemo(
    () => [...new Set([...teacherMeta.values()].flatMap((m) => [...m.faculties]))].sort(),
    [teacherMeta],
  );
  const programsList = useMemo(
    () => [...new Set([...teacherMeta.values()].flatMap((m) => [...m.programs]))].sort(),
    [teacherMeta],
  );
  const courses = useMemo(
    () => [...new Set([...teacherMeta.values()].flatMap((m) => [...m.courses]))].sort(),
    [teacherMeta],
  );

  // Loai cac ban ghi CHO TRONG (lop nhap tu Excel chua phan cong giang vien):
  // chung khong phai nguoi that nen khong co "gio ranh" de khai, va so luong
  // rat lon (file HK1 co toi 114) - de vao se lam ngop danh sach GV that.
  const guestTeachers = useMemo(
    () => (data?.teachers || []).filter((t) => t.type === "GUEST" && !t.isPlaceholder),
    [data],
  );

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return guestTeachers.filter((t) => {
      const meta = teacherMeta.get(t.id);
      if (facultyFilter && !meta?.faculties.has(facultyFilter)) return false;
      if (programFilter && !meta?.programs.has(programFilter)) return false;
      if (courseFilter && !meta?.courses.has(courseFilter)) return false;
      if (q && !(t.nameRaw || t.name || "").toLowerCase().includes(q)) return false;
      return true;
    });
  }, [guestTeachers, teacherMeta, facultyFilter, programFilter, courseFilter, search]);

  const selected = filtered.find((t) => t.id === selectedId) || filtered[0] || null;
  const selectedMeta = selected ? teacherMeta.get(selected.id) : null;
  const daSoGio = selected?.availabilitySlots?.length ?? 0;

  // Luu xong, /api/data tra ve bo teachers moi -> initialSlots doi -> luoi tu
  // dong bo lai theo server. Ghim selectedId de lan re-render sau khong roi ve
  // filtered[0] neu thu tu danh sach doi.
  const handleSaveAvailability = async (slots) => {
    if (!selected) return;
    setSelectedId(selected.id);
    await updateManualTeacher(selected.id, { availability: slots });
    setEditing(false);
  };

  // Doi GV giua chung thi bo luon ban nhap dang sua - giu che do sua khi da
  // sang nguoi khac se de nham tuong sua tiep cua nguoi cu.
  const chonGiangVien = (id) => {
    setSelectedId(id);
    setEditing(false);
  };

  if (!data) {
    return (
      <Notice tone="slate">
        Chưa có dữ liệu — sang "Dữ liệu học phần" để nhập hoặc nạp dữ liệu trước.
      </Notice>
    );
  }

  return (
    <div className="space-y-3">
      <div className="bg-card rounded-xl border shadow-sm">
        <div className="flex flex-wrap items-center gap-2 border-b p-3">
          <h3 className="mr-1 text-sm font-semibold">Bộ lọc</h3>
          {/* Chi GV thinh giang moi can khai gio: GV co hue duoc xep tu do o
              Giai doan 2 nen khong co khai niem "khung gio ranh". Noi ro ra de
              giao vu khong di tim mot nguoi co huu o day roi tuong thieu. */}
          <span className="text-muted-foreground text-xs">
            {filtered.length}/{guestTeachers.length} giảng viên thỉnh giảng khớp
          </span>

          <div className="ml-auto flex flex-wrap items-center gap-2">
            <ListSearch
              value={search}
              onChange={setSearch}
              placeholder="Tìm tên giảng viên"
              className="w-full sm:w-56"
            />
            <FilterSelect
              label="Mọi khoa"
              value={facultyFilter || null}
              options={faculties}
              onChange={(v) => setFacultyFilter(v ?? "")}
            />
            <FilterSelect
              label="Mọi ngành (CTĐT)"
              value={programFilter || null}
              options={programsList}
              onChange={(v) => setProgramFilter(v ?? "")}
            />
            <FilterSelect
              label="Mọi học phần"
              searchable
              value={courseFilter || null}
              options={courses}
              onChange={(v) => setCourseFilter(v ?? "")}
            />
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2 border-b p-3">
          <span className="text-muted-foreground text-xs">Giảng viên</span>
          <NativeSelect
            className="w-full sm:w-96"
            value={selected?.id ?? ""}
            onChange={(e) => chonGiangVien(Number(e.target.value))}
          >
            {filtered.length === 0 && <option value="">— Không có giảng viên khớp —</option>}
            {filtered.map((t) => (
              <option key={t.id} value={t.id}>
                {t.nameRaw || t.name} ·{" "}
                {(t.availabilitySlots || []).length > 0
                  ? `${t.availabilitySlots.length} ô rảnh`
                  : "chưa khai giờ"}
              </option>
            ))}
          </NativeSelect>
        </div>

        <div className="p-3">
          {!selected ? (
            <p className="text-muted-foreground text-xs">
              Chọn 1 giảng viên ở ô phía trên để khai giờ rảnh.
            </p>
          ) : (
            <div className="space-y-3">
              <div>
                <h3 className="text-sm font-semibold">
                  {selected.title ? `${selected.title} ` : ""}
                  {selected.nameRaw || selected.name}
                </h3>
                <p className="text-muted-foreground text-xs">
                  {selected.org || "—"}
                  {selectedMeta?.courses.size > 0 && (
                    <> · Dạy: {[...selectedMeta.courses].join(", ")}</>
                  )}
                </p>
              </div>

              {/* Luoi khai gio + bang lop nam CANH NHAU: dang tick gio thi van
                  phai nhin duoc GV nay co nhung lop nao va lop nao da chot gio
                  - do chinh la can cu de biet nen tick khung nao. Man hep thi
                  flex-wrap cho bang tut xuong duoi. */}
              <div className="flex flex-wrap items-start gap-4">
                <div className="min-w-100 flex-1 space-y-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <h4 className="text-sm font-semibold">Giờ có thể dạy</h4>
                    {editing ? (
                      <span className="text-muted-foreground text-xs">
                        Tick <strong className="text-foreground">MỌI tiết</strong> rảnh trong
                        tuần (không chỉ tiết bắt đầu) — hệ thống tự tìm giờ bắt đầu hợp lệ cho
                        từng lớp.
                      </span>
                    ) : (
                      <span className="text-muted-foreground text-xs">
                        {daSoGio > 0 ? `${daSoGio} ô đã khai` : "Chưa khai giờ nào"}
                      </span>
                    )}
                    {!editing && canEdit && (
                      <div className="ml-auto">
                        <EditAvailabilityButton
                          disabled={loading}
                          onClick={() => setEditing(true)}
                        >
                          {daSoGio > 0 ? "Chỉnh sửa" : "Khai giờ rảnh"}
                        </EditAvailabilityButton>
                      </div>
                    )}
                  </div>

                  {!editing && daSoGio > 0 && (
                    <p className="text-muted-foreground text-xs">
                      {moTaGioRanh(selected.availabilitySlots, slotsPerDay).join(" · ")}
                    </p>
                  )}

                  <SubmissionWindowGrid
                    key={`${selected.id}-${editing ? "edit" : "view"}`}
                    numDays={numDays}
                    slotsPerDay={slotsPerDay}
                    initialSlots={selected.availabilitySlots || []}
                    saving={loading}
                    readOnly={!editing}
                    allowEmpty
                    saveLabel={(n) => (n === 0 ? "Xóa hết giờ rảnh" : `Lưu ${n} khung giờ`)}
                    onSave={handleSaveAvailability}
                    onCancel={() => setEditing(false)}
                  />
                </div>

                <div className="min-w-80 flex-1">
                  <h4 className="mb-2 text-sm font-semibold">
                    Các lớp đang dạy ({selectedMeta?.classes.length ?? 0})
                  </h4>
                  <div className="overflow-hidden rounded-lg border">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>#</TableHead>
                          <TableHead>Học phần</TableHead>
                          <TableHead>Mã lớp</TableHead>
                          <TableHead>Ngành</TableHead>
                          <TableHead>Thời gian</TableHead>
                          <TableHead>Trạng thái</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {(selectedMeta?.classes || []).map((c) => {
                          const meta = STATUS_META[c.status] || { label: c.status, tone: "slate" };
                          return (
                            <TableRow key={c.sectionId}>
                              <TableCell className="text-muted-foreground tabular-nums">
                                {c.sectionId}
                              </TableCell>
                              <TableCell className="whitespace-normal">{c.courseName}</TableCell>
                              <TableCell>{c.classCode || "—"}</TableCell>
                              <TableCell>{c.programName || "—"}</TableCell>
                              <TableCell>
                                {c.timeLabel || (c.timeAssumed
                                  ? `Tự xếp${c.day != null ? ` (đang: T${dayNumber(c.day)} tiết ${c.periodStart}-${c.periodEnd})` : ""}`
                                  : "—")}
                              </TableCell>
                              <TableCell>
                                <Pill tone={meta.tone}>{meta.label}</Pill>
                              </TableCell>
                            </TableRow>
                          );
                        })}
                        {(!selectedMeta || selectedMeta.classes.length === 0) && (
                          <TableRow className="hover:bg-transparent">
                            <TableCell colSpan={6} className="text-muted-foreground py-6 text-center">
                              Chưa có lớp nào.
                            </TableCell>
                          </TableRow>
                        )}
                      </TableBody>
                    </Table>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
