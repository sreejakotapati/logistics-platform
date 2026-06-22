'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { rbacApi } from '@/lib/api/rbac';
import { useSession } from '@/features/auth/use-session';

export function usePermissionCatalog() {
  return useQuery({ queryKey: ['rbac', 'permissions'], queryFn: rbacApi.permissions });
}

export function useRoles() {
  const { activeOrgId } = useSession();
  return useQuery({ queryKey: ['rbac', 'roles', activeOrgId], queryFn: rbacApi.roles, enabled: !!activeOrgId });
}

export function useMemberRoles(userId: string | null) {
  return useQuery({
    queryKey: ['rbac', 'member-roles', userId],
    queryFn: () => rbacApi.memberRoles(userId as string),
    enabled: !!userId,
  });
}

export function useCreateRole() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { name: string; description?: string; permission_ids: string[] }) =>
      rbacApi.createRole(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['rbac', 'roles'] }),
  });
}

export function useAssignRole() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ userId, roleId }: { userId: string; roleId: string }) =>
      rbacApi.assignRole(userId, roleId),
    onSuccess: (_d, v) => {
      qc.invalidateQueries({ queryKey: ['rbac', 'member-roles', v.userId] });
      qc.invalidateQueries({ queryKey: ['permissions'] });
    },
  });
}

export function useRemoveRole() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ userId, roleId }: { userId: string; roleId: string }) =>
      rbacApi.removeRole(userId, roleId),
    onSuccess: (_d, v) => {
      qc.invalidateQueries({ queryKey: ['rbac', 'member-roles', v.userId] });
      qc.invalidateQueries({ queryKey: ['permissions'] });
    },
  });
}
