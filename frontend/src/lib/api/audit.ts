import { api } from '@/lib/api/client';
import type { AuditPage, AuditTimeline, RetentionPreview } from '@/lib/api/types';

export interface AuditQuery {
  action?: string;
  entity_type?: string;
  entity_id?: string;
  actor_user_id?: string;
  date_from?: string;
  date_to?: string;
  q?: string;
  limit?: number;
  cursor?: string;
  include_total?: boolean;
}

function qs(params: object): string {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== '') sp.set(k, String(v));
  }
  const s = sp.toString();
  return s ? `?${s}` : '';
}

export const auditApi = {
  logs: (query: AuditQuery = {}) => api.get<AuditPage>(`/audit/logs${qs(query)}`),
  search: (q: string, limit?: number, cursor?: string) =>
    api.get<AuditPage>(`/audit/search${qs({ q, limit, cursor })}`),
  timeline: (query: AuditQuery = {}) => api.get<AuditTimeline>(`/audit/timeline${qs(query)}`),
  actor: (actorUserId: string, cursor?: string) =>
    api.get<AuditPage>(`/audit/actors/${actorUserId}${qs({ cursor })}`),
  entity: (entityType: string, entityId: string, cursor?: string) =>
    api.get<AuditPage>(`/audit/entities/${entityType}/${entityId}${qs({ cursor })}`),
  retention: () => api.get<RetentionPreview>('/audit/retention'),
  exportPath: (format: 'csv' | 'json', query: AuditQuery = {}) =>
    `/audit/export${qs({ ...query, format })}`,
};
