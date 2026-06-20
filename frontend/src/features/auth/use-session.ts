'use client';

import { useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/auth-store';

export function useSession() {
  return useAuthStore((s) => ({
    status: s.status,
    user: s.user,
    activeOrgId: s.activeOrgId,
    organizations: s.organizations,
    isAuthenticated: s.status === 'authenticated',
  }));
}

export function useSwitchOrg() {
  const queryClient = useQueryClient();
  const switchOrg = useAuthStore((s) => s.switchOrg);
  return async (organizationId: string) => {
    await switchOrg(organizationId);
    // The active org changed → every tenant-scoped query is now stale.
    await queryClient.invalidateQueries();
  };
}

export function useLogout() {
  const queryClient = useQueryClient();
  const router = useRouter();
  const logout = useAuthStore((s) => s.logout);
  return async () => {
    await logout();
    queryClient.clear();
    router.replace('/login');
  };
}
