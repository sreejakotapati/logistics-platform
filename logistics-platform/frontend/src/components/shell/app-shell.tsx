'use client';

import type { ReactNode } from 'react';
import { Sidebar } from '@/components/shell/sidebar';
import { TopNav } from '@/components/shell/top-nav';
import { CommandPalette } from '@/components/shell/command-palette';

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex h-dvh overflow-hidden">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <TopNav />
        <main className="flex-1 overflow-y-auto p-6">{children}</main>
      </div>
      <CommandPalette />
    </div>
  );
}
