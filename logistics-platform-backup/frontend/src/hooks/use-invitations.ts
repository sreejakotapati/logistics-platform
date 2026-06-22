'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { orgApi } from '@/lib/api/organizations';
import { useSession } from '@/features/auth/use-session';

export function useInvitations() {
  const { activeOrgId } = useSession();
  return useQuery({
    queryKey: ['invitations', activeOrgId],
    queryFn: orgApi.invitations,
    enabled: !!activeOrgId,
  });
}

export function useInvite() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { email: string; role_id?: string }) => orgApi.invite(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['invitations'] }),
  });
}

export function useRevokeInvitation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => orgApi.revokeInvitation(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['invitations'] }),
  });
}
