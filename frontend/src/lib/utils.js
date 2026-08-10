import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/** Gộp className có điều kiện + dedupe class Tailwind (dùng bởi shadcn/ui). */
export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

/** Viết tắt 2 chữ cái từ họ tên (dùng cho avatar). VD "Nguyễn Văn An" → "NA". */
export function initials(name) {
  const parts = String(name ?? '').trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return '?';
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}
