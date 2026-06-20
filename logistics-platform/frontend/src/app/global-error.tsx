'use client';

import { ErrorState } from '@/components/shared/error-state';

export default function GlobalError({ reset }: { error: Error; reset: () => void }) {
  return (
    <html lang="en">
      <body>
        <main className="flex min-h-dvh items-center justify-center p-6">
          <ErrorState onRetry={reset} />
        </main>
      </body>
    </html>
  );
}
