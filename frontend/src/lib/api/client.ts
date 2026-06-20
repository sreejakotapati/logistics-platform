import { env } from '@/lib/config/env';
import type { ApiError } from '@/types';

// API client. Typed fetch wrapper that injects the active-org access token, sends the refresh cookie,
// and transparently refreshes once on a 401 (single-flight) before retrying. Token lives in memory only
// (never localStorage); the refresh token is an httpOnly cookie owned by the backend.

function requestId(): string {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : Math.random().toString(36).slice(2);
}

let tokenGetter: () => string | null = () => null;
let refreshHandler: (() => Promise<boolean>) | null = null;
let onUnauthorized: (() => void) | null = null;

export function registerTokenGetter(fn: () => string | null) { tokenGetter = fn; }
export function registerRefreshHandler(fn: () => Promise<boolean>) { refreshHandler = fn; }
export function registerUnauthorizedHandler(fn: () => void) { onUnauthorized = fn; }

// Single-flight: concurrent 401s share one refresh round-trip.
let inflightRefresh: Promise<boolean> | null = null;
function refreshOnce(): Promise<boolean> {
  if (!refreshHandler) return Promise.resolve(false);
  if (!inflightRefresh) {
    inflightRefresh = refreshHandler().finally(() => { inflightRefresh = null; });
  }
  return inflightRefresh;
}

const NO_RETRY = ['/auth/login', '/auth/refresh', '/auth/register'];

export class ApiClient {
  constructor(private readonly baseUrl: string = env.apiUrl) {}

  async request<T>(path: string, init: RequestInit = {}, _retried = false): Promise<T> {
    const token = tokenGetter();
    const res = await fetch(`${this.baseUrl}${path}`, {
      ...init,
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'X-Request-ID': requestId(),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...init.headers,
      },
    });

    if (res.status === 401 && !_retried && !NO_RETRY.some((p) => path.startsWith(p))) {
      const ok = await refreshOnce();
      if (ok) return this.request<T>(path, init, true);
      onUnauthorized?.();
    }

    const isJson = res.headers.get('content-type')?.includes('application/json');
    const body = isJson ? await res.json().catch(() => undefined) : undefined;

    if (!res.ok) {
      const error: ApiError = body?.error ?? {
        status: res.status,
        code: 'http_error',
        message: res.statusText || 'Request failed',
      };
      throw { ...error, status: res.status };
    }
    return body as T;
  }

  get<T>(path: string) { return this.request<T>(path, { method: 'GET' }); }
  post<T>(path: string, data?: unknown) {
    return this.request<T>(path, { method: 'POST', body: data ? JSON.stringify(data) : undefined });
  }
  patch<T>(path: string, data?: unknown) {
    return this.request<T>(path, { method: 'PATCH', body: data ? JSON.stringify(data) : undefined });
  }
  delete<T>(path: string) { return this.request<T>(path, { method: 'DELETE' }); }
}

export const api = new ApiClient();

// Absolute URL helper for non-JSON responses handled outside the client (e.g. file downloads).
export function apiUrl(path: string): string {
  return `${env.apiUrl}${path}`;
}
