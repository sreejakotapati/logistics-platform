'use client';

import Link from 'next/link';
import { LogOut, User } from 'lucide-react';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel,
  DropdownMenuSeparator, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useSession, useLogout } from '@/features/auth/use-session';

function initials(name: string | null, email: string | undefined): string {
  if (name) return name.split(' ').map((p) => p[0]).slice(0, 2).join('').toUpperCase();
  return (email ?? '?').slice(0, 2).toUpperCase();
}

export function UserMenu() {
  const { user } = useSession();
  const logout = useLogout();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="rounded-full" aria-label="Account">
          <Avatar><AvatarFallback>{initials(user?.full_name ?? null, user?.email)}</AvatarFallback></Avatar>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel className="flex flex-col">
          <span className="truncate text-sm">{user?.full_name ?? 'Account'}</span>
          <span className="truncate text-xs font-normal text-muted-foreground">{user?.email}</span>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild>
          <Link href="/profile"><User className="mr-2 h-4 w-4" />Profile</Link>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={() => void logout()}>
          <LogOut className="mr-2 h-4 w-4" />Sign out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
