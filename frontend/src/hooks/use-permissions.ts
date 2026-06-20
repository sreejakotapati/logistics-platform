'use client';

import { useQuery } from '@tanstack/react-query';
import { rbacApi } from '@/lib/api/rbac';
import { useSession } from '@/features/auth/use-session';

// Effective permissions for the active org, used to gate UI. Keyed by active org so a switch refetches.
export function usePermissions() {
  const { activeOrgId, isAuthenticated } = useSession();
  const query = useQuery({
    queryKey: ['permissions', activeOrgId],
    queryFn: rbacApi.myPermissions,
    enabled: isAuthenticated && !!activeOrgId,
    staleTime: 60_000,
  });
  const set = new Set(query.data ?? []);
  return {
    permissions: query.data ?? [],
    isLoading: query.isLoading,
    can: (key: string) => set.has(key),
  };
}
