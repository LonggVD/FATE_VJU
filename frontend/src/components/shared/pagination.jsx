import { PageSizeSelect } from '@/components/shared/page-size-select';
import { Button } from '@/components/ui/button';

/**
 * Thanh phân trang dùng chung: "x–y / tổng" + chọn số/trang + Trước/Sau.
 * `meta` = { page, perPage, total, lastPage }.
 */
export function Pagination({
  meta,
  unit = 'bản ghi',
  onPage,
  onPerPage,
  disabled = false,
}) {
  const from = meta.total === 0 ? 0 : (meta.page - 1) * meta.perPage + 1;
  const to = Math.min(meta.page * meta.perPage, meta.total);

  return (
    <div className="text-muted-foreground mt-3 flex flex-wrap items-center justify-between gap-2 text-sm">
      <div className="flex items-center gap-3">
        <span>
          {from}–{to} trên {meta.total.toLocaleString('vi-VN')} {unit}
        </span>
        <PageSizeSelect value={meta.perPage} onChange={onPerPage} />
      </div>
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          disabled={meta.page <= 1 || disabled}
          onClick={() => onPage(meta.page - 1)}
        >
          ‹ Trước
        </Button>
        <span className="tabular-nums">
          Trang {meta.page} / {meta.lastPage}
        </span>
        <Button
          variant="outline"
          size="sm"
          disabled={meta.page >= meta.lastPage || disabled}
          onClick={() => onPage(meta.page + 1)}
        >
          Sau ›
        </Button>
      </div>
    </div>
  );
}
