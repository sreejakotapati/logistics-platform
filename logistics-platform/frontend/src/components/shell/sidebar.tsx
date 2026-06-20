'use client';

import Link from 'next/link';
import { Truck } from 'lucide-react';
import { useUIStore } from '@/stores/ui-store';
import { cn } from '@/lib/utils';
import { SidebarNav } from '@/components/shell/sidebar-nav';

export function Sidebar() {
  const collapsed = useUIStore((s) => s.sidebarCollapsed);
  return (
    <aside className={cn('hidden border-r bg-card md:flex md:flex-col', collapsed ? 'md:w-16' : 'md:w-60')}>
      <Link href="/dashboard" className="flex h-14 items-center gap-2 border-b px-4">
        <span className="flex h-7 w-7 items-center justify-center rounded bg-primary text-primary-foreground">
          <Truck className="h-4 w-4" />
        </span>
        {!collapsed && <span className="text-sm font-semibold">Logistics</span>}
      </Link>
      <SidebarNav collapsed={collapsed} />
    </aside>
  );
}
