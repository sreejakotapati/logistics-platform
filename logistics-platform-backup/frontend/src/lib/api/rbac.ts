import { api } from '@/lib/api/client';
import type { MessageResponse, Permission, Role } from '@/lib/api/types';

export const rbacApi = {
  permissions: () => api.get<Permission[]>('/rbac/permissions'),
  myPermissions: () => api.get<string[]>('/rbac/me/permissions'),
  roles: () => api.get<Role[]>('/organizations/current/roles'),
  createRole: (data: { name: string; description?: string; permission_ids: string[] }) =>
    api.post<Role>('/organizations/current/roles', data),
  memberRoles: (userId: string) =>
    api.get<Role[]>(`/organizations/current/members/${userId}/roles`),
  assignRole: (userId: string, roleId: string) =>
    api.post<MessageResponse>(`/organizations/current/members/${userId}/roles`, { role_id: roleId }),
  removeRole: (userId: string, roleId: string) =>
    api.delete<MessageResponse>(`/organizations/current/members/${userId}/roles/${roleId}`),
};
