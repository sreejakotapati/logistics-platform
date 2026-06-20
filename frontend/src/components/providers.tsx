'use client';

import { useState, type ReactNode } from 'react';
import { QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from 'next-themes';
import { makeQueryClient } from '@/lib/api/query-client';
import { SessionProvider } from '@/features/auth/session-provider';
import { Toaster } from '@/components/ui/sonner';

export function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(makeQueryClient);
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
        <SessionProvider>{children}</SessionProvider>
        <Toaster position="top-right" />
      </ThemeProvider>
    </QueryClientProvider>
  );
}
