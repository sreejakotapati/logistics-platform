'use client';

import { Bell, Menu, PanelLeft, Search, Truck } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { useUIStore } from '@/stores/ui-store';
import { OrgSwitcher } from '@/components/shell/org-switcher';
import { ThemeToggle } from '@/components/shell/theme-toggle';
import { UserMenu } from '@/components/shell/user-menu';
import { SidebarNav } from '@/components/shell/sidebar-nav';

export function TopNav() {
  // Select each action individually rather than `useUIStore()` (whole store), so this header does not
  // re-render when unrelated UI state (e.g. commandOpen) changes. Action refs are stable.
  const toggleSidebar = useUIStore((s) => s.toggleSidebar);
  const setCommandOpen = useUIStore((s) => s.setCommandOpen);
  return (
    <header className="flex h-14 items-center gap-2 border-b bg-background px-3">
      {/* Mobile nav */}
      <Sheet>
        <SheetTrigger asChild>
          <Button variant="ghost" size="icon" className="md:hidden" aria-label="Open menu">
            <Menu className="h-5 w-5" />
          </Button>
        </SheetTrigger>
        <SheetContent side="left">
          <div className="flex h-14 items-center gap-2 border-b px-4">
            <span className="flex h-7 w-7 items-center justify-center rounded bg-primary text-primary-foreground">
              <Truck className="h-4 w-4" />
            </span>
            <span className="text-sm font-semibold">Logistics</span>
          </div>
          <SidebarNav />
        </SheetContent>
      </Sheet>

      {/* Desktop collapse */}
      <Button variant="ghost" size="icon" className="hidden md:inline-flex" onClick={toggleSidebar} aria-label="Toggle sidebar">
        <PanelLeft className="h-5 w-5" />
      </Button>

      <OrgSwitcher />

      <button
        onClick={() => setCommandOpen(true)}
        className="ml-auto flex h-9 w-full max-w-xs items-center gap-2 rounded-md border bg-muted/40 px-3 text-sm text-muted-foreground transition-colors hover:bg-muted"
      >
        <Search className="h-4 w-4" />
        <span className="flex-1 text-left">Search...</span>
        <kbd className="hidden rounded border bg-background px-1.5 text-xs sm:inline">⌘K</kbd>
      </button>

      <div className="ml-auto flex items-center gap-1">
        <Button variant="ghost" size="icon" aria-label="Notifications"><Bell className="h-4 w-4" /></Button>
        <ThemeToggle />
        <UserMenu />
      </div>
    </header>
  );
}
