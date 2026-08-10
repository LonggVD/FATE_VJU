import { Search, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

/**
 * Ô tìm dùng chung cho các bảng danh sách.
 *
 * 2 chế độ, quyết định bởi việc có truyền `onSubmit` hay không:
 *  - KHÔNG có onSubmit  → lọc NGAY tại client (dùng cho bảng nạp hết, không phân trang):
 *                         gõ tới đâu lọc tới đó, không gọi server.
 *  - CÓ onSubmit        → lọc ở SERVER (bảng có phân trang): gõ rồi Enter / bấm "Tìm",
 *                         KHÔNG gọi theo từng ký tự để tránh dội request.
 */
export function ListSearch({
  value,
  onChange,
  onSubmit,
  placeholder = 'Tìm…',
  className,
}) {
  function clear() {
    onChange('');
    onSubmit?.('');
  }

  return (
    <div className={cn('flex min-w-0 items-center gap-2', className)}>
      <div className="focus-within:ring-ring/40 bg-background flex h-9 min-w-0 flex-1 items-center rounded-md border focus-within:ring-2">
        <Search className="text-muted-foreground mx-2.5 size-4 shrink-0" />
        <input
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') onSubmit?.(value);
            if (e.key === 'Escape') clear();
          }}
          placeholder={placeholder}
          aria-label={placeholder}
          className="h-9 min-w-0 flex-1 bg-transparent text-sm outline-none"
        />
        {value && (
          <button
            type="button"
            onClick={clear}
            aria-label="Xoá từ khoá"
            className="text-muted-foreground hover:text-foreground px-2"
          >
            <X className="size-4" />
          </button>
        )}
      </div>
      {onSubmit && (
        <Button size="sm" className="shrink-0" onClick={() => onSubmit(value)}>
          <Search className="size-4" />
          Tìm
        </Button>
      )}
    </div>
  );
}

/** Khớp từ khoá với nhiều trường (không phân biệt hoa/thường, bỏ khoảng trắng thừa). */
export function matchesTerm(term, ...fields) {
  const t = term.trim().toLowerCase();
  if (!t) return true;

  return fields.some((f) => (f ?? '').toLowerCase().includes(t));
}
