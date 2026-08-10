import { Spinner } from '@/components/ui/spinner';
import { cn } from '@/lib/utils';

/**
 * Lớp phủ "đang tải" đặt trên một vùng nội dung (phần tử cha cần `relative`).
 * Dùng cho bảng khi lọc/tìm/phân trang, hoặc khi đang chạy solver.
 */
export function LoadingOverlay({ show, label = 'Đang tải…', className }) {
  if (!show) return null;

  return (
    <div
      className={cn(
        'bg-background/60 absolute inset-0 z-10 flex items-center justify-center gap-2 rounded-lg backdrop-blur-[1px]',
        className,
      )}
    >
      <Spinner className="text-primary size-5" />
      <span className="text-muted-foreground text-sm">{label}</span>
    </div>
  );
}
