import { DAY_LABELS, densityLevel, densityRanges } from "../../adapters/dayPeriod";
import { Panel } from "@/components/shared/panel";
import { Button } from "@/components/ui/button";

// Bang mat do = ban do thu nho cho luoi lon, va la BO DIEU HUONG:
// bam mot o thi cac buoi dien ra o thoi diem do noi len tren luoi, phan con lai
// chim xuong. Day la thu bu lai cho viec luoi phai cuon khi the mang du thong tin
// - canvas lon thi mat cai nhin toan cuc, bang nay tra lai cai nhin do.
//
// Nam NGOAI vung cuon cua luoi nen khong bao gio troi mat.
//
// KHUNG THE dung Panel (design system VJU), nhung BAN THAN BANG NHIET van giu
// cac class .wkgrid / d0..d5 trong styles.css: do la thang mau tuan tu duoc can
// rieng (5 bac, ΔL > 0.06 de mat con tach duoc), khong phai mau thuong hieu -
// va con duoc ReportedHoursPanel + TeacherAvailabilityPage dung chung.
export default function DensityNavigator({ view, activeCell, onPickCell }) {
  const { grid, numDays, slotsPerDay, maxDensity } = view;

  return (
    <Panel
      title="Số lớp học cùng lúc"
      description={`Bấm một ô để làm nổi các buổi ở thời điểm đó · cao điểm ${maxDensity} lớp`}
      action={
        activeCell && (
          <Button variant="outline" size="sm" onClick={() => onPickCell(null)}>
            Bỏ chọn
          </Button>
        )
      }
    >
      {/* Luoi + chu giai nam canh nhau: luoi chi rong ~280px, de chu giai xuong
          duoi thi vua ton them mot hang vua bo trong ben phai. */}
      <div className="nav-density-body">
        <div className="nav-density-wrap">
          <table className="wkgrid nav-density-grid">
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
                    {(DAY_LABELS[day] ?? `N${day + 1}`)
                      .replace("Thứ ", "T")
                      .replace("Chủ nhật", "CN")}
                  </th>
                  {Array.from({ length: slotsPerDay }, (_, p) => {
                    const v = grid[day]?.[p] ?? 0;
                    const on =
                      activeCell &&
                      activeCell.day === day &&
                      activeCell.period === p;
                    return (
                      <td
                        key={p}
                        className={`d${densityLevel(v, maxDensity)} ${on ? "picked" : ""}`}
                      >
                        <button
                          type="button"
                          className="nav-density-cell"
                          disabled={v === 0}
                          onClick={() => onPickCell(on ? null : { day, period: p })}
                          title={`${DAY_LABELS[day] ?? day} tiết ${p + 1}: ${v} lớp`}
                          aria-label={`${DAY_LABELS[day] ?? day} tiết ${p + 1}, ${v} lớp`}
                        >
                          {v > 0 ? v : ""}
                        </button>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Chu giai ghi KHOANG THAT cua tung bac, vi thang co gian theo bo loc -
            doi pham vi la khoang doi theo, khong the ghi cung "1 2 3 4+". */}
        <div className="wkgrid-legend">
          <span className="wkgrid-legend-label">Lớp / ô</span>
          <span className="wkgrid-legend-item">
            <span className="wkgrid-legend-swatch" aria-hidden="true" />
            trống
          </span>
          {densityRanges(maxDensity).map((r) => (
            <span key={r.level} className="wkgrid-legend-item">
              <span className={`wkgrid-legend-swatch d${r.level}`} aria-hidden="true" />
              {r.label}
            </span>
          ))}
        </div>
      </div>
    </Panel>
  );
}
