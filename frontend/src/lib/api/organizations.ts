import { api } from '@/lib/api/client';
import type {
  InvitationPreview, InvitationSummary, MemberSummary, MessageResponse,
  OrganizationProfile, OrganizationProfileUpdate, OrganizationSummary, UserProfile,
} from '@/lib/api/types';

export const orgApi = {
  list: () => api.get<OrganizationSummary[]>('/organizations'),
  create: (data: { name: string; slug?: string }) =>
    api.post<OrganizationProfile>('/organizations', data),
  current: () => api.get<OrganizationProfile>('/organizations/current'),
  updateProfile: (data: OrganizationProfileUpdate) =>
    api.patch<OrganizationProfile>('/organizations/current', data),
  getSettings: () => api.get<{ settings: Record<string, unknown> }>('/organizations/current/settings'),
  updateSettings: (settings: Record<string, unknown>) =>
    api.patch<{ settings: Record<string, unknown> }>('/organizations/current/settings', { settings }),
  close: () => api.post<MessageResponse>('/organizations/current/close'),

  members: () => api.get<MemberSummary[]>('/organizations/current/members'),
  updateMember: (userId: string, status: string) =>
    api.patch<MessageResponse>(`/organizations/current/members/${userId}`, { status }),
  removeMember: (userId: string) =>
    api.delete<MessageResponse>(`/organizations/current/members/${userId}`),
  leave: () => api.post<MessageResponse>('/organizations/current/leave'),

  invitations: () => api.get<InvitationSummary[]>('/organizations/current/invitations'),
  invite: (data: { email: string; role_id?: string }) =>
    api.post<InvitationSummary>('/organizations/current/invitations', data),
  revokeInvitation: (id: string) =>
    api.delete<MessageResponse>(`/organizations/current/invitations/${id}`),

  previewInvitation: (token: string) => api.get<InvitationPreview>(`/invitations/${token}`),
  acceptInvitation: (token: string) => api.post<MessageResponse>(`/invitations/${token}/accept`),

  profile: () => api.get<UserProfile>('/users/me'),
  updateUserProfile: (full_name: string) => api.patch<UserProfile>('/users/me', { full_name }),
};
