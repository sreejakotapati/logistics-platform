'use client';

import { useEffect, useRef, type ReactNode } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import {
  registerRefreshHandler, registerTokenGetter, registerUnauthorizedHandler,
} from '@/lib/api/client';
import { useAuthStore } from '@/stores/auth-store';

// Wires the in-memory token into the API client, attempts a silent refresh on first load, and
// redirects to /login when the session can no longer be refreshed.
export function SessionProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const booted = useRef(false);

  useEffect(() => {
    registerTokenGetter(() => useAuthStore.getState().accessToken);
    registerRefreshHandler(() => useAuthStore.getState().refresh());
    registerUnauthorizedHandler(() => {
      useAuthStore.getState().reset();
      if (!pathname.startsWith('/login') && !pathname.startsWith('/invite')) {
        router.replace('/login');
      }
    });
    if (!booted.current) {
      booted.current = true;
      void useAuthStore.getState().bootstrap();
    }
  }, [router, pathname]);

  return <>{children}</>;
}
