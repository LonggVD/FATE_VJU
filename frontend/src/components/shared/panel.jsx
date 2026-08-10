import { cn } from '@/lib/utils';

/**
 * Khung thẻ nội dung có tiêu đề + vùng hành động (dùng chung mọi trang).
 * `description` — dòng giải thích ngắn dưới tiêu đề, nêu rõ phạm vi dữ liệu của thẻ.
 */
export function Panel({
  title,
  description,
  action,
  children,
  className,
  bodyClassName,
}) {
  return (
    <section
      className={cn('bg-card rounded-xl border p-4 shadow-sm sm:p-5', className)}
    >
      {(title || action) && (
        <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
          {title && (
            <div className="min-w-0 space-y-1">
              <h2 className="text-sm font-semibold">{title}</h2>
              {description && (
                <p className="text-muted-foreground text-xs">{description}</p>
              )}
            </div>
          )}
          {action}
        </div>
      )}
      <div className={bodyClassName}>{children}</div>
    </section>
  );
}
