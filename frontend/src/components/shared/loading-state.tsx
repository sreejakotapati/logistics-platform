import { Skeleton } from '@/components/ui/skeleton';

export function LoadingState({ label = 'Loading' }: { label?: string }) {
  return (
    <div className="space-y-4" aria-busy="true" aria-label={label}>
      <Skeleton className="h-8 w-1/3" />
      <div className="grid gap-4 sm:grid-cols-3">
        <Skeleton className="h-24" />
        <Skeleton className="h-24" />
        <Skeleton className="h-24" />
      </div>
      <Skeleton className="h-64 w-full" />
    </div>
  );
}
