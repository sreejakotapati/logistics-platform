'use client';

import { useEffect } from 'react';
import { env } from '@/lib/config/env';

// Logs the deployed build SHA once per page load (so the live build is identifiable in production),
// and renders a tiny build badge in development only. Does not touch auth or application state.
let logged = false;

export function BuildInfo() {
  useEffect(() => {
    if (logged) return;
    logged = true;
    console.info(`Frontend Build: ${env.commitSha}`);
  }, []);

  if (process.env.NODE_ENV !== 'development') return null;
  return (
    <div className="pointer-events-none fixed bottom-2 right-2 z-50 rounded bg-muted px-2 py-1 font-mono text-[10px] text-muted-foreground">
      build {env.commitSha}
    </div>
  );
}
