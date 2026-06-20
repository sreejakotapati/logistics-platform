'use client';

import { useEffect, type ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { Loader2, Truck } from 'lucide-react';
import { useSession } from '@/features/auth/use-session';

export default function AuthLayout({ children }: { children: ReactNode }) {
  const { status } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (status === 'authenticated') router.replace('/dashboard');
  }, [status, router]);

  if (status === 'loading' || status === 'authenticated') {
    return (
      <div className="flex h-dvh items-center justify-center">
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="grid min-h-dvh lg:grid-cols-2">
      <div className="relative hidden flex-col justify-between bg-primary p-10 text-primary-foreground lg:flex">
        <div className="flex items-center gap-2 text-sm font-semibold">
          <Truck className="h-5 w-5" />Logistics Platform
        </div>
        <div className="space-y-3">
          <p className="text-2xl font-semibold leading-snug">One platform for every shipment, fleet, and invoice.</p>
          <p className="text-sm text-primary-foreground/80">Multi-tenant, India-first logistics operations — built for teams that move fast.</p>
        </div>
        <p className="text-xs text-primary-foreground/60">© {new Date().getFullYear()} Logistics Platform</p>
      </div>
      <div className="flex items-center justify-center p-6 sm:p-10">{children}</div>
    </div>
  );
}
