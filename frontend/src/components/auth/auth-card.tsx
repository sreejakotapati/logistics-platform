import type { ReactNode } from 'react';
import { Package } from 'lucide-react';

// Shared chrome for the unauthenticated flows. The brand mark anchors the column; the card holds the form.
export function AuthCard({ title, description, children, footer }: {
  title: string; description?: string; children: ReactNode; footer?: ReactNode;
}) {
  return (
    <div className="w-full max-w-sm">
      <div className="mb-6 flex items-center gap-2">
        <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <Package className="h-5 w-5" />
        </span>
        <span className="text-sm font-semibold tracking-tight">Logistics Platform</span>
      </div>
      <h1 className="text-xl font-semibold tracking-tight">{title}</h1>
      {description && <p className="mt-1 text-sm text-muted-foreground">{description}</p>}
      <div className="mt-6">{children}</div>
      {footer && <div className="mt-6 text-sm text-muted-foreground">{footer}</div>}
    </div>
  );
}
