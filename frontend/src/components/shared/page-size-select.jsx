import { Check, ChevronDown } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

const SIZES = [10, 20, 50, 100];

/** Chọn số bản ghi hiển thị mỗi trang (dùng ở khu phân trang các bảng). */
export function PageSizeSelect({ value, onChange }) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger className="border-input bg-background hover:bg-accent focus-visible:ring-ring/50 inline-flex h-8 items-center gap-1.5 rounded-md border px-2.5 text-sm shadow-xs transition-colors focus-visible:ring-[3px] focus-visible:outline-none">
        {value} / trang
        <ChevronDown className="text-muted-foreground size-3.5" />
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="min-w-32">
        {SIZES.map((s) => (
          <DropdownMenuItem key={s} onSelect={() => onChange(s)}>
            <span className="flex-1">{s} / trang</span>
            {s === value && <Check className="size-4" />}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
