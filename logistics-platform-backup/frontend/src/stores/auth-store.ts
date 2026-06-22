import { create } from 'zustand';
import { authApi } from '@/lib/api/auth';
import { orgApi } from '@/lib/api/organizations';
import type { MeUser, OrganizationSummary } from '@/lib/api/types';
import { decodeJwt } from '@/lib/utils';

export type SessionStatus = 'loading' | 'authenticated' | 'anonymous';

interface AuthState {
  status: SessionStatus;
  accessToken: string | null;
  user: MeUser | null;
  activeOrgId: string | null;
  organizations: OrganizationSummary[];

  setToken: (token: string | null) => void;
  hydrate: (token: string) => Promise<void>;
  bootstrap: () => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  register: (data: { email: string; password: string; full_name: string; organization_name: string }) => Promise<void>;
  refresh: () => Promise<boolean>;
  switchOrg: (organizationId: string) => Promise<void>;
  logout: () => Promise<void>;
  reset: () => void;
}

function orgFromToken(token: string): string | null {
  return decodeJwt<{ org?: string }>(token)?.org ?? null;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  status: 'loading',
  accessToken: null,
  user: null,
  activeOrgId: null,
  organizations: [],

  setToken: (token) => set({ accessToken: token, activeOrgId: token ? orgFromToken(token) : null }),

  hydrate: async (token) => {
    set({ accessToken: token, activeOrgId: orgFromToken(token) });
    const [user, organizations] = await Promise.all([authApi.me(), orgApi.list()]);
    set({ user, organizations, status: 'authenticated' });
  },

  bootstrap: async () => {
    try {
      const { access_token } = await authApi.refresh();
      await get().hydrate(access_token);
    } catch {
      get().reset();
    }
  },

  login: async (email, password) => {
    const { access_token } = await authApi.login({ email, password });
    await get().hydrate(access_token);
  },

  register: async (data) => {
    const { access_token } = await authApi.register(data);
    await get().hydrate(access_token);
  },

  refresh: async () => {
    try {
      const { access_token } = await authApi.refresh();
      set({ accessToken: access_token, activeOrgId: orgFromToken(access_token) });
      return true;
    } catch {
      get().reset();
      return false;
    }
  },

  switchOrg: async (organizationId) => {
    const { access_token } = await authApi.activateOrg(organizationId);
    set({ accessToken: access_token, activeOrgId: orgFromToken(access_token) });
  },

  logout: async () => {
    try { await authApi.logout(); } catch { /* best-effort */ }
    get().reset();
  },

  reset: () =>
    set({ status: 'anonymous', accessToken: null, user: null, activeOrgId: null, organizations: [] }),
}));
