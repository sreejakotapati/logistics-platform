'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { orgApi } from '@/lib/api/organizations';
import type { OrganizationProfileUpdate } from '@/lib/api/types';
import { useSession } from '@/features/auth/use-session';

export function useCurrentOrganization() {
  const { activeOrgId } = useSession();
  return useQuery({
    queryKey: ['organization', 'current', activeOrgId],
    queryFn: orgApi.current,
    enabled: !!activeOrgId,
  });
}

export function useUpdateOrganization() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: OrganizationProfileUpdate) => orgApi.updateProfile(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['organization', 'current'] }),
  });
}

export function useOrganizationSettings() {
  const { activeOrgId } = useSession();
  return useQuery({
    queryKey: ['organization', 'settings', activeOrgId],
    queryFn: orgApi.getSettings,
    enabled: !!activeOrgId,
  });
}

export function useUpdateSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (settings: Record<string, unknown>) => orgApi.updateSettings(settings),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['organization', 'settings'] }),
  });
}

export function useUserProfile() {
  return useQuery({ queryKey: ['user', 'profile'], queryFn: orgApi.profile });
}

export function useUpdateUserProfile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (full_name: string) => orgApi.updateUserProfile(full_name),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['user', 'profile'] }),
  });
}
