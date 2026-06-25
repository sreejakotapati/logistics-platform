'use client';

import { ErrorState } from '@/components/shared/error-state';

// Local error boundary for the unauthenticated routes. Without it, any render error on /login,
// /register, etc. bubbles to the root global-error boundary (full-page replacement). This keeps a
// failure contained to the auth surface with a retry, so a transient hiccup never blanks the app.
export default function AuthError({ reset }: { error: Error; reset: () => void }) {
  return (
    <div className="flex min-h-dvh items-center justify-center p-6">
      <ErrorState
        title="Something went wrong"
        description="We couldn’t load this page. Please try again."
        onRetry={reset}
      />
    </div>
  );
}
