'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useTheme } from 'next-themes';
import { LayoutDashboard, Moon, Sun } from 'lucide-react';
import {
  CommandDialog, CommandInput, CommandList, CommandEmpty, CommandGroup, CommandItem,
} from '@/components/ui/command';
import { useUIStore } from '@/stores/ui-store';

export function CommandPalette() {
  // Select each field individually rather than `useUIStore()` (whole store), so this only re-renders
  // when `commandOpen` changes — not when the sidebar is toggled. The action ref is stable.
  const commandOpen = useUIStore((s) => s.commandOpen);
  const setCommandOpen = useUIStore((s) => s.setCommandOpen);
  const router = useRouter();
  const { setTheme } = useTheme();

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setCommandOpen(!commandOpen);
      }
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [commandOpen, setCommandOpen]);

  const run = (fn: () => void) => { fn(); setCommandOpen(false); };

  return (
    <CommandDialog open={commandOpen} onOpenChange={setCommandOpen}>
      <CommandInput placeholder="Search or jump to..." />
      <CommandList>
        <CommandEmpty>No results found.</CommandEmpty>
        <CommandGroup heading="Navigation">
          <CommandItem onSelect={() => run(() => router.push('/dashboard'))}>
            <LayoutDashboard /> Go to Dashboard
          </CommandItem>
        </CommandGroup>
        <CommandGroup heading="Theme">
          <CommandItem onSelect={() => run(() => setTheme('light'))}><Sun /> Light theme</CommandItem>
          <CommandItem onSelect={() => run(() => setTheme('dark'))}><Moon /> Dark theme</CommandItem>
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}
