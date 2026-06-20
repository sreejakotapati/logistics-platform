'use client';

import { useState } from 'react';
import { Building2, Check, ChevronsUpDown, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel,
  DropdownMenuSeparator, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useSession, useSwitchOrg } from '@/features/auth/use-session';
import { cn } from '@/lib/utils';

// Switching mints a new active-org JWT server-side; on success every tenant-scoped query is invalidated.
export function OrgSwitcher() {
  const { organizations, activeOrgId } = useSession();
  const switchOrg = useSwitchOrg();
  const [pending, setPending] = useState<string | null>(null);

  const active = organizations.find((o) => o.id === activeOrgId);

  async function onSelect(id: string) {
    if (id === activeOrgId) return;
    setPending(id);
    try { await switchOrg(id); } finally { setPending(null); }
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="h-9 gap-2 px-2">
          <span className="flex h-6 w-6 items-center justify-center rounded bg-primary text-primary-foreground">
            <Building2 className="h-4 w-4" />
          </span>
          <span className="hidden max-w-40 truncate text-sm font-medium sm:inline">
            {active?.name ?? 'Select organization'}
          </span>
          <ChevronsUpDown className="h-4 w-4 text-muted-foreground" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-64">
        <DropdownMenuLabel>Organizations</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {organizations.map((o) => (
          <DropdownMenuItem key={o.id} onSelect={() => onSelect(o.id)} className="justify-between">
            <span className="truncate">{o.name}</span>
            {pending === o.id ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Check className={cn('h-4 w-4', o.id === activeOrgId ? 'opacity-100' : 'opacity-0')} />
            )}
          </DropdownMenuItem>
        ))}
        {organizations.length === 0 && (
          <DropdownMenuItem disabled className="text-xs text-muted-foreground">No organizations</DropdownMenuItem>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
