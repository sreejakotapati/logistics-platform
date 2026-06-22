import { api } from '@/lib/api/client';
import type { MeUser, MessageResponse, TokenResponse } from '@/lib/api/types';

export const authApi = {
  register: (data: { email: string; password: string; full_name: string; organization_name: string }) =>
    api.post<TokenResponse>('/auth/register', data),
  login: (data: { email: string; password: string }) =>
    api.post<TokenResponse>('/auth/login', data),
  refresh: () => api.post<TokenResponse>('/auth/refresh'),
  logout: () => api.post<MessageResponse | void>('/auth/logout'),
  me: () => api.get<MeUser>('/auth/me'),
  activateOrg: (organizationId: string) =>
    api.post<TokenResponse>(`/auth/organizations/${organizationId}/activate`),
  requestPasswordReset: (email: string) =>
    api.post<MessageResponse>('/auth/password-reset/request', { email }),
  confirmPasswordReset: (token: string, password: string) =>
    api.post<MessageResponse>('/auth/password-reset/confirm', { token, password }),
  verifyEmail: (token: string) => api.post<MessageResponse>('/auth/email/verify', { token }),
  resendVerification: (email: string) =>
    api.post<MessageResponse>('/auth/email/verify/resend', { email }),
};
