import { DAY_LABELS, densityLevel } from "../../adapters/dayPeriod";
import { slotRangeLabel } from "../../adapters/crossConflictAnalysis";
import { SUB_STATE, SUB_STATE_META } from "../../adapters/submissionQueue";
import { Panel } from "@/components/shared/panel";
import { Pill } from "@/components/shared/pill";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";

// "Gio da bao" cua 1 giang vien - thu duy nhat cau hoi "GV nay bao la day duoc
// nhung gio nao?" can den, va truoc day khong man nao tra loi: du lieu chi to
// chuc theo BUOI, con man Tra cuu thi chi ve lich DA GIAI.
//
// Khung the dung Panel; rieng BANG NHIET giu class .wkgrid + thang d0..d5 trong
// styles.css - dung chung voi DensityNavigator va TeacherAvailabilityPage.
export default function ReportedHoursPanel({ teacher, hours }) {
  if (teacher.type !== "GUEST") {
    return (
      <Panel title="Giờ đã báo">
        <p className="text-muted-foreground text-xs">
          GV cơ hữu — không điều phối viên nào nộp giờ cho họ. Giai đoạn 2 tự chọn giờ
          trong toàn tuần, nên ở bước này không có "giờ đã báo" nào để xem.
        </p>
      </Panel>
    );
  }

  if (hours.sections.length === 0) {
    return (
      <Panel title="Giờ đã báo">
        <p className="text-muted-foreground text-xs">
          GV này không có buổi thỉnh giảng nào trong dữ liệu hiện tại.
        </p>
      </Panel>
    );
  }

  const { numDays, slotsPerDay } = hours;
  const maxLevel = Math.max(0, ...hours.grid.flat());
  // Hai bang canh bao (trung gio / khong co tren luoi) da chuyen sang TeacherAlerts,
  // dat o cot phai canh luoi "Lich da xep" - vi ca hai deu noi ve chinh luoi do.
  // Khoi nay chi con lo phan "gio da bao".

  return (
    <Panel
      title="Giờ đã báo"
      description={
        <>
          <strong className="text-foreground">
            {hours.set.length}/{hours.sections.length}
          </strong>{" "}
          buổi đã chốt giờ
          {hours.reportedCells > 0 && (
            <>
              {" · "}
              <strong className="text-foreground">{hours.reportedCells}</strong> ô giờ được
              báo là dạy được
            </>
          )}
          {hours.unreported.length > 0 && (
            <>
              {" · "}
              <strong className="text-foreground">{hours.unreported.length}</strong> buổi
              chưa báo giờ
            </>
          )}
        </>
      }
      bodyClassName="space-y-3"
    >
      {hours.reportedCells === 0 ? (
        <p className="text-muted-foreground text-xs">
          Chưa buổi nào của GV này được chốt giờ cụ thể — chưa có ô giờ nào để vẽ. Xem danh
          sách bên dưới.
        </p>
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="wkgrid">
              <thead>
                <tr>
                  <th />
                  {Array.from({ length: slotsPerDay }, (_, p) => (
                    <th key={p}>{p + 1}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {Array.from({ length: numDays }, (_, day) => (
                  <tr key={day}>
                    <th scope="row">
                      {(DAY_LABELS[day] ?? `N${day + 1}`).replace("Thứ ", "T").replace("Chủ nhật", "CN")}
                    </th>
                    {Array.from({ length: slotsPerDay }, (_, p) => {
                      const v = hours.grid[day]?.[p] ?? 0;
                      const isClash = hours.clashCells.has(`${day}:${p}`);
                      return (
                        <td
                          key={p}
                          className={isClash ? "clash" : `d${densityLevel(v)}`}
                          title={
                            `${DAY_LABELS[day] ?? day} tiết ${p + 1}: ${v} buổi` +
                            (isClash ? " — TRÙNG GIỜ" : "")
                          }
                        >
                          {v >= 2 ? v : ""}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="wkgrid-legend">
            <span className="wkgrid-legend-label">Số buổi / ô</span>
            <span className="wkgrid-legend-item">
              <span className="wkgrid-legend-swatch" aria-hidden="true" />
              không báo
            </span>
            {[1, 2, 3, 4].slice(0, Math.max(maxLevel, 1)).map((v) => (
              <span key={v} className="wkgrid-legend-item">
                <span className={`wkgrid-legend-swatch d${v}`} aria-hidden="true" />
                {v === 4 ? "4+" : v}
              </span>
            ))}
            {hours.clashPairs.length > 0 && (
              <span className="wkgrid-legend-item">
                <span className="wkgrid-legend-swatch clash" aria-hidden="true" />
                trùng giờ
              </span>
            )}
            {hours.unreported.length > 0 && (
              <span className="text-muted-foreground">
                {hours.unreported.length} buổi chưa báo giờ không vẽ trên lưới
              </span>
            )}
          </div>
        </>
      )}

      {/* Bang phai co vung cuon RIENG: khi the nay nam trong cot hep, bang rong
          hon cot se tran ra ngoai va chui xuong duoi cot hop thu. */}
      <div className="overflow-hidden rounded-lg border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>#</TableHead>
              <TableHead>Trạng thái</TableHead>
              <TableHead>Môn học</TableHead>
              <TableHead>Điều phối viên</TableHead>
              <TableHead>Khung giờ báo là dạy được</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {hours.sections.map((r) => {
              const meta = SUB_STATE_META[r.state];
              const isClash = hours.clashSectionIds.has(r.sectionId);
              return (
                <TableRow key={r.sectionId} className={cn(isClash && "bg-red-500/5")}>
                  <TableCell className="text-muted-foreground tabular-nums">
                    {r.sectionId}
                  </TableCell>
                  <TableCell>
                    <Pill tone={meta.tone}>{meta.label}</Pill>
                  </TableCell>
                  <TableCell className="whitespace-normal">{r.courseName}</TableCell>
                  <TableCell className="text-muted-foreground">{r.coordinator}</TableCell>
                  <TableCell className="whitespace-normal">
                    {r.state === SUB_STATE.UNREPORTED ? (
                      <Pill tone="slate">
                        {r.isEmpty ? "Chưa nộp" : `Tự do cả tuần · ${r.windowSlots.length}`}
                      </Pill>
                    ) : (
                      <span className="flex flex-wrap items-center gap-1">
                        {r.windowSlots.map((w, i) => (
                          <Pill key={i} tone={isClash ? "red" : "emerald"}>
                            {slotRangeLabel(w, r.duration, slotsPerDay)}
                          </Pill>
                        ))}
                        {isClash && (
                          <span className="text-xs font-medium text-red-700">trùng giờ</span>
                        )}
                      </span>
                    )}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
    </Panel>
  );
}
