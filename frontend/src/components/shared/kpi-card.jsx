import { TONE_TEXT } from '@/components/shared/pill';
import { cn } from '@/lib/utils';

/**
 * Thẻ KPI. `stat` = { label, value, sub?, highlight?, highlightTone?, valueTone?, subTone? }.
 * `highlight` → nền đậm (đỏ VJU mặc định, amber nếu highlightTone='amber').
 */
export function KpiCard({ stat }) {
  const highlight = stat.highlight;
  const highlightBg =
    stat.highlightTone === 'amber' ? 'bg-amber-500' : 'bg-primary';

  return (
    <div
      className={cn(
        'rounded-xl border p-4 shadow-sm',
        highlight ? cn('border-transparent text-white', highlightBg) : 'bg-card',
      )}
    >
      <p
        className={cn(
          'text-sm',
          highlight ? 'text-white/80' : 'text-muted-foreground',
        )}
      >
        {stat.label}
      </p>
      <p
        className={cn(
          'mt-1 text-2xl font-semibold tracking-tight tabular-nums',
          !highlight && stat.valueTone && TONE_TEXT[stat.valueTone],
        )}
      >
        {stat.value}
      </p>
      {stat.sub && (
        <p
          className={cn(
            'mt-1 text-xs',
            highlight
              ? 'text-white/70'
              : stat.subTone
                ? TONE_TEXT[stat.subTone]
                : 'text-muted-foreground',
          )}
        >
          {stat.sub}
        </p>
      )}
    </div>
  );
}
