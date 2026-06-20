import Link from 'next/link';
import { Truck } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function Home() {
  return (
    <main className="flex min-h-dvh flex-col items-center justify-center gap-6 p-6 text-center">
      <span className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary text-primary-foreground">
        <Truck className="h-6 w-6" />
      </span>
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Logistics Management Platform</h1>
        <p className="mt-2 text-sm text-muted-foreground">Multi-tenant logistics operations, India-first.</p>
      </div>
      <div className="flex gap-3">
        <Button asChild><Link href="/dashboard">Open dashboard</Link></Button>
        <Button asChild variant="outline"><Link href="/login">Sign in</Link></Button>
      </div>
    </main>
  );
}
