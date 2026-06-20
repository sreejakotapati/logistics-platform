'use client';

import type { ReactNode } from 'react';
import { usePermissions } from '@/hooks/use-permissions';

// Renders children only when the active session holds the permission. Pure UI affordance — the backend
// re-checks every request, so this only hides controls the user could not use anyway.
export function PermissionGate({ permission, children, fallback = null }: {
  permission: string; children: ReactNode; fallback?: ReactNode;
}) {
  const { can, isLoading } = usePermissions();
  if (isLoading) return null;
  return can(permission) ? <>{children}</> : <>{fallback}</>;
}
