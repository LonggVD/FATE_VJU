import { cn } from '@/lib/utils';

/** Viền + nền tint mềm cho hộp thông báo (light & dark). */
const NOTICE_CLASS = {
  blue: 'border-blue-500/20 bg-blue-500/10',
  violet: 'border-violet-500/20 bg-violet-500/10',
  amber: 'border-amber-500/20 bg-amber-500/10',
  emerald: 'border-emerald-500/20 bg-emerald-500/10',
  red: 'border-red-500/20 bg-red-500/10',
  slate: 'border-slate-400/20 bg-slate-400/10',
};

/** Màu icon dẫn đầu theo tone. */
const NOTICE_ICON = {
  blue: 'text-blue-600 dark:text-blue-400',
  violet: 'text-violet-600 dark:text-violet-400',
  amber: 'text-amber-600 dark:text-amber-400',
  emerald: 'text-emerald-600 dark:text-emerald-400',
  red: 'text-red-600 dark:text-red-400',
  slate: 'text-slate-500 dark:text-slate-400',
};

/**
 * Hộp thông báo/callout dùng chung (đầu trang, ghi chú nghiệp vụ).
 * Màu theo `tone` chuẩn; icon tuỳ chọn. Cho hành động thì truyền `action`.
 */
export function Notice({ tone = 'blue', icon: Icon, action, children, className }) {
  return (
    <div
      className={cn(
        'flex items-center gap-2 rounded-lg border px-4 py-3 text-sm',
        NOTICE_CLASS[tone],
        className,
      )}
    >
      {Icon && <Icon className={cn('size-4 shrink-0', NOTICE_ICON[tone])} />}
      <span className="min-w-0">{children}</span>
      {action && <span className="ml-auto shrink-0">{action}</span>}
    </div>
  );
}
