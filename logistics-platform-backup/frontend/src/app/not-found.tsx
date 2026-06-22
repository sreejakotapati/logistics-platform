import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { EmptyState } from '@/components/shared/empty-state';
import { Compass } from 'lucide-react';

export default function NotFound() {
  return (
    <main className="flex min-h-dvh items-center justify-center p-6">
      <EmptyState
        icon={Compass}
        title="Page not found"
        description="The page you are looking for does not exist or has moved."
        action={<Button asChild><Link href="/dashboard">Back to dashboard</Link></Button>}
      />
    </main>
  );
}
