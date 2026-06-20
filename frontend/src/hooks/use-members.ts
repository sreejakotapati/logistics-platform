'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { orgApi } from '@/lib/api/organizations';
import { useSession } from '@/features/auth/use-session';

export function useMembers() {
  const { activeOrgId } = useSession();
  return useQuery({
    queryKey: ['members', activeOrgId],
    queryFn: orgApi.members,
    enabled: !!activeOrgId,
  });
}

export function useUpdateMember() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ userId, status }: { userId: string; status: string }) =>
      orgApi.updateMember(userId, status),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['members'] }),
  });
}

export function useRemoveMember() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (userId: string) => orgApi.removeMember(userId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['members'] }),
  });
}
