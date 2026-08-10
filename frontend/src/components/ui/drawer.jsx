import * as DialogPrimitive from '@radix-ui/react-dialog';
import { X } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * Ngăn kéo trượt từ mép phải, dựng trên Radix Dialog.
 *
 * Reference (BE_Enrollment) không có component này — bên đó form dài nằm trong
 * `Dialog` giữa màn hình. Ở đây vẫn cần drawer vì form sửa lớp có ~20 trường và
 * người dùng phải đối chiếu với bảng 29 cột phía sau trong lúc điền; hộp thoại
 * giữa màn che mất chính cái họ đang đối chiếu.
 *
 * Dựng trên Dialog nên vẫn được focus trap, khoá cuộn nền, Esc và nhãn a11y —
 * thứ mà bản `.sed-overlay` cũ (div + onClick) không có.
 *
 * z-250 chứ không phải z-50 mặc định: xem giải thích tầng xếp chồng ở đầu
 * `dialog.jsx` (chế độ toàn màn hình của SchedulePage chiếm dải z-200..z-220).
 */
export function Drawer({ open, onOpenChange, title, description, footer, children, className }) {
  return (
    <DialogPrimitive.Root open={open} onOpenChange={onOpenChange}>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className="fixed inset-0 z-250 bg-black/50" />
        <DialogPrimitive.Content
          className={cn(
            'bg-background fixed inset-y-0 right-0 z-250 flex w-full max-w-xl flex-col border-l shadow-2xl',
            className,
          )}
        >
          <div className="flex shrink-0 items-start justify-between gap-3 border-b px-5 py-4">
            <div className="min-w-0 space-y-1">
              <DialogPrimitive.Title className="text-base leading-none font-semibold">
                {title}
              </DialogPrimitive.Title>
              {description ? (
                <DialogPrimitive.Description className="text-muted-foreground text-xs">
                  {description}
                </DialogPrimitive.Description>
              ) : (
                // Radix canh bao neu Content khong co Description; an di van giu
                // duoc mo ta cho trinh doc man hinh.
                <DialogPrimitive.Description className="sr-only">
                  {title}
                </DialogPrimitive.Description>
              )}
            </div>
            <DialogPrimitive.Close className="text-muted-foreground hover:bg-muted hover:text-foreground focus-visible:ring-ring/50 inline-flex size-8 shrink-0 items-center justify-center rounded-md transition-colors focus-visible:ring-[3px] focus-visible:outline-none">
              <X className="size-4" />
              <span className="sr-only">Đóng</span>
            </DialogPrimitive.Close>
          </div>

          {children}

          {footer && (
            <div className="bg-muted/40 flex shrink-0 flex-wrap items-center justify-end gap-2 border-t px-5 py-3">
              {footer}
            </div>
          )}
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  );
}

/** Vùng nội dung cuộn được của ngăn kéo. */
export function DrawerBody({ className, ...props }) {
  return (
    <div
      className={cn('min-h-0 flex-1 space-y-5 overflow-y-auto px-5 py-4', className)}
      {...props}
    />
  );
}

/** Một nhóm trường trong ngăn kéo. */
export function DrawerSection({ title, hint, children }) {
  return (
    <section className="space-y-3">
      <div className="space-y-1">
        <h4 className="text-sm font-semibold">{title}</h4>
        {hint && <p className="text-muted-foreground text-xs">{hint}</p>}
      </div>
      {children}
    </section>
  );
}
