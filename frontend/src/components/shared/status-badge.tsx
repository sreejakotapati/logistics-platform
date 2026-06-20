import { cn } from '@/lib/utils';

// Maps a logistics status to its spine color (see UI/UX spec). Status conveyed by label + dot.
const STATUS = {
  created: 'bg-status-created',
  picked: 'bg-status-picked',
  'in-transit': 'bg-status-in-transit',
  'out-for-delivery': 'bg-status-out-for-delivery',
  delivered: 'bg-status-delivered',
  exception: 'bg-status-exception',
  rto: 'bg-status-rto',
  cancelled: 'bg-status-cancelled',
} as const;

export type StatusKey = keyof typeof STATUS;

export function StatusBadge({ status, label }: { status: StatusKey; label?: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-xs font-medium">
      <span className={cn('h-2 w-2 rounded-full', STATUS[status])} aria-hidden />
      {label ?? status}
    </span>
  );
}
