import { ChevronRight } from 'lucide-react';
import { useEffect, useState } from 'react';
import { NAV_HOME, getAllowedGroups } from '@/constants/nav';
import { cn } from '@/lib/utils';

/**
 * Thanh bên 2 cấp. Khác reference ở đúng một chỗ: app này là SPA theo state,
 * không có Inertia — nên mọi mục là <button> gọi onNavigate(page, sub) thay vì
 * <Link href>. Phần còn lại (kích thước, màu, hành vi thu gọn/drawer) giữ 1:1.
 */
export function AppSidebar({
  page,
  sub,
  role,
  collapsed,
  mobileOpen,
  onSetCollapsed,
  onNavigate,
}) {
  const groups = getAllowedGroups(role);
  const isViewer = role === 'viewer';

  return (
    <aside
      className={cn(
        'bg-background flex shrink-0 flex-col overflow-y-auto border-r py-3 duration-200',
        // Mobile: drawer cố định dưới topbar, trượt vào/ra. Desktop: cột tĩnh trong luồng.
        'fixed inset-y-0 top-12 left-0 z-50 w-64 px-2.5 transition-transform',
        'lg:static lg:top-0 lg:z-auto lg:translate-x-0 lg:transition-[width]',
        mobileOpen
          ? 'translate-x-0 shadow-xl'
          : '-translate-x-full lg:translate-x-0',
        // Thu gọn rail chỉ áp dụng ở desktop (mobile luôn hiện đầy đủ trong drawer).
        collapsed ? 'lg:w-16 lg:items-center lg:px-2' : 'lg:w-64',
      )}
    >
      {/* Màn hình chính */}
      <button
        type="button"
        onClick={() => onNavigate(NAV_HOME.key, null)}
        title={collapsed ? NAV_HOME.label : undefined}
        className={cn(
          'flex items-center rounded-lg text-sm font-medium transition-colors',
          collapsed ? 'size-10 justify-center' : 'gap-2.5 px-3 py-2',
          page === NAV_HOME.key
            ? 'bg-muted text-foreground font-semibold'
            : 'text-foreground hover:bg-muted',
        )}
      >
        <NAV_HOME.icon className="size-4.5 shrink-0" />
        {!collapsed && NAV_HOME.label}
      </button>

      {!collapsed && (
        <p className="text-muted-foreground/70 px-3 pt-4 pb-1 text-[11px] font-semibold tracking-wide uppercase">
          {isViewer ? 'Tra cứu' : 'Nghiệp vụ'}
        </p>
      )}
      {collapsed && <div className="bg-border my-2 h-px w-6" />}

      {groups.map((group) => (
        <NavGroupItem
          key={group.key}
          group={group}
          page={page}
          sub={sub}
          collapsed={collapsed}
          onNavigate={onNavigate}
          onExpand={() => onSetCollapsed(false)}
        />
      ))}
    </aside>
  );
}

function NavGroupItem({ group, page, sub, collapsed, onNavigate, onExpand }) {
  const hasActive = page === group.key;
  const single = group.children.length === 0;
  const [open, setOpen] = useState(hasActive);
  const Icon = group.icon;

  // Xổ nhóm ra khi điều hướng tới nó từ nơi khác (vd bấm ở rail thu gọn, hoặc
  // mở bằng URL) - nếu không, mục con đang hoạt động lại bị giấu.
  useEffect(() => {
    if (hasActive) setOpen(true);
  }, [hasActive]);

  // Thu gọn: chỉ hiện icon nhóm; bấm để mở rộng + xổ nhóm đó.
  if (collapsed) {
    return (
      <button
        type="button"
        title={group.label}
        onClick={() => {
          onExpand();
          setOpen(true);
          onNavigate(group.key, null);
        }}
        className={cn(
          'flex size-10 items-center justify-center rounded-lg transition-colors',
          hasActive
            ? 'bg-muted text-foreground font-semibold'
            : 'text-foreground hover:bg-muted',
        )}
      >
        <Icon className="size-4.5" />
      </button>
    );
  }

  // Mục đơn (không có mục con) — bấm là đi thẳng, không có mũi tên xổ.
  if (single) {
    return (
      <button
        type="button"
        onClick={() => onNavigate(group.key, null)}
        className={cn(
          'flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
          hasActive
            ? 'bg-muted text-foreground font-semibold'
            : 'text-foreground hover:bg-muted',
        )}
      >
        <Icon className="size-4.5 shrink-0" />
        <span className="flex-1 text-left">{group.label}</span>
      </button>
    );
  }

  return (
    <div>
      {/* Nut nhom PHAI co trang thai active. Bam vao nhom dang mo se dong no lai
          va giau mat muc con dang xem - luc do neu nut nhom cung khong danh dau
          gi thi sidebar khong con cho nao bao nguoi dung dang o dau. Nhanh rail
          thu gon ben tren da danh dau, nhanh nay truoc do thi khong. */}
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className={cn(
          'text-foreground hover:bg-muted flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
          // Dang mo: muc con da to sang roi, nhom chi can dam chu.
          hasActive && open && 'font-semibold',
          // Da dong: muc con bi giau, nhom phai tu mang dau hieu - to nen giong
          // het cach rail thu gon danh dau.
          hasActive && !open && 'bg-muted font-semibold',
        )}
      >
        <Icon className="size-4.5 shrink-0" />
        <span className="flex-1 text-left">{group.label}</span>
        <ChevronRight
          className={cn(
            'text-muted-foreground size-3.5 transition-transform',
            open && 'rotate-90',
          )}
        />
      </button>

      {open && (
        <div className="border-border mt-0.5 mb-1 ml-5 space-y-0.5 border-l border-dashed pl-2">
          {group.children.map((child) => {
            const ChildIcon = child.icon;
            const active = hasActive && sub === child.key;
            return (
              <button
                key={child.key}
                type="button"
                onClick={() => onNavigate(group.key, child.key)}
                className={cn(
                  'flex w-full items-center gap-2 rounded-md px-3 py-1.5 text-[13px] transition-colors',
                  active
                    ? 'bg-muted text-foreground font-medium'
                    : 'text-muted-foreground hover:bg-muted hover:text-foreground',
                )}
              >
                {ChildIcon && <ChildIcon className="size-3.5 shrink-0" />}
                <span className="text-left">{child.label}</span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
