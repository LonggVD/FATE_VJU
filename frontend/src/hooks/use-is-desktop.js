import { useEffect, useState } from 'react';

const QUERY = '(min-width: 1024px)'; // Tailwind `lg`

/**
 * true khi màn hình ≥ lg (1024px). Dùng để tách hành vi thanh bên:
 * desktop = thu gọn rail (w-64 ↔ w-16); mobile = drawer trượt phủ nội dung.
 * Khởi tạo theo matchMedia ngay lần render đầu để tránh nháy layout.
 */
export function useIsDesktop() {
  const [isDesktop, setIsDesktop] = useState(() =>
    typeof window === 'undefined' ? true : window.matchMedia(QUERY).matches,
  );

  useEffect(() => {
    const mql = window.matchMedia(QUERY);
    const onChange = () => setIsDesktop(mql.matches);
    onChange();
    mql.addEventListener('change', onChange);
    return () => mql.removeEventListener('change', onChange);
  }, []);

  return isDesktop;
}
