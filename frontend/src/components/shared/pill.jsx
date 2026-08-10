import { cn } from '@/lib/utils';

/** Nền + chữ mềm cho chip trạng thái (light & dark). */
export const TONE_CLASS = {
  blue: 'bg-blue-500/15 text-blue-700 dark:text-blue-300',
  violet: 'bg-violet-500/15 text-violet-700 dark:text-violet-300',
  amber: 'bg-amber-500/20 text-amber-700 dark:text-amber-300',
  emerald: 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300',
  red: 'bg-red-500/15 text-red-700 dark:text-red-300',
  slate: 'bg-slate-500/15 text-slate-600 dark:text-slate-300',
};

/** Chấm tròn dẫn đầu chip / chú giải. */
export const TONE_DOT = {
  blue: 'bg-blue-500',
  violet: 'bg-violet-500',
  amber: 'bg-amber-500',
  emerald: 'bg-emerald-500',
  red: 'bg-red-500',
  slate: 'bg-slate-400',
};

/** Nền đặc (thanh biểu đồ dạng div). */
export const TONE_SOLID = TONE_DOT;

/** Fill đặc cho SVG. */
export const TONE_FILL = {
  blue: 'fill-blue-500',
  violet: 'fill-violet-500',
  amber: 'fill-amber-500',
  emerald: 'fill-emerald-500',
  red: 'fill-red-500',
  slate: 'fill-slate-400',
};

/** Stroke đặc cho SVG (donut). */
export const TONE_STROKE = {
  blue: 'stroke-blue-500',
  violet: 'stroke-violet-500',
  amber: 'stroke-amber-500',
  emerald: 'stroke-emerald-500',
  red: 'stroke-red-500',
  slate: 'stroke-slate-300 dark:stroke-slate-600',
};

/** Chữ nhấn (phụ đề KPI…). */
export const TONE_TEXT = {
  blue: 'text-blue-600 dark:text-blue-400',
  violet: 'text-violet-600 dark:text-violet-400',
  amber: 'text-amber-600 dark:text-amber-400',
  emerald: 'text-emerald-600 dark:text-emerald-400',
  red: 'text-red-600 dark:text-red-400',
  slate: 'text-muted-foreground',
};

/** Chip trạng thái nghiệp vụ dùng chung cho mọi bảng. */
export function Pill({ tone, dot = false, children, className }) {
  return (
    <span
      className={cn(
        'inline-flex w-fit items-center gap-1.5 rounded-md px-2 py-0.5 text-xs font-medium',
        TONE_CLASS[tone],
        className,
      )}
    >
      {dot && <span className={cn('size-1.5 rounded-full', TONE_DOT[tone])} />}
      {children}
    </span>
  );
}
