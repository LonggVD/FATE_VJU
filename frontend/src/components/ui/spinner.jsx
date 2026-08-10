import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

/** Vòng xoay loading dùng chung. */
export function Spinner({ className }) {
  return (
    <Loader2
      className={cn('size-4 animate-spin', className)}
      aria-label="Đang tải"
    />
  );
}
