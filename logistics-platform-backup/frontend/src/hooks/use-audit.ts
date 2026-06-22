'use client';

import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { auditApi, type AuditQuery } from '@/lib/api/audit';
import { useSession } from '@/features/auth/use-session';

export function useAuditLogs(query: AuditQuery) {
  const { activeOrgId } = useSession();
  return useQuery({
    queryKey: ['audit', 'logs', activeOrgId, query],
    queryFn: () => auditApi.logs({ ...query, include_total: true }),
    enabled: !!activeOrgId,
    placeholderData: keepPreviousData,
  });
}

export function useAuditRetention() {
  const { activeOrgId } = useSession();
  return useQuery({
    queryKey: ['audit', 'retention', activeOrgId],
    queryFn: auditApi.retention,
    enabled: !!activeOrgId,
  });
}

import { useInfiniteQuery } from '@tanstack/react-query';

export function useInfiniteAuditLogs(query: AuditQuery) {
  const { activeOrgId } = useSession();
  return useInfiniteQuery({
    queryKey: ['audit', 'infinite', activeOrgId, query],
    enabled: !!activeOrgId,
    initialPageParam: undefined as string | undefined,
    queryFn: ({ pageParam }) => auditApi.logs({ ...query, cursor: pageParam, include_total: true }),
    getNextPageParam: (last) => last.next_cursor ?? undefined,
  });
}
