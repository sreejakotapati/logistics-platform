'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { navigation } from '@/lib/config/nav';
import { cn } from '@/lib/utils';

export function SidebarNav({ collapsed = false }: { collapsed?: boolean }) {
  const pathname = usePathname();
  return (
    <nav className="flex-1 space-y-4 overflow-y-auto px-2 py-3">
      {navigation.map((group) => (
        <div key={group.label}>
          {!collapsed && (
            <p className="px-2 pb-1 text-xs font-medium uppercase tracking-wide text-muted-foreground">
              {group.label}
            </p>
          )}
          <div className="space-y-1">
            {group.items.map((item) => {
              const active = pathname === item.href;
              const Icon = item.icon;
              const content = (
                <>
                  <Icon className="h-4 w-4 shrink-0" />
                  {!collapsed && <span>{item.label}</span>}
                </>
              );
              const base = cn(
                'flex items-center gap-3 rounded-md px-2 py-2 text-sm font-medium transition-colors',
                active ? 'bg-accent text-accent-foreground' : 'text-foreground/70 hover:bg-accent hover:text-accent-foreground',
                item.disabled && 'pointer-events-none opacity-40'
              );
              return item.disabled ? (
                <span key={item.label} className={base} aria-disabled title="Coming soon">{content}</span>
              ) : (
                <Link key={item.label} href={item.href} className={base}>{content}</Link>
              );
            })}
          </div>
        </div>
      ))}
    </nav>
  );
}
