'use client';

import { useState } from 'react';
import { Download, Loader2, Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { LoadingState } from '@/components/shared/loading-state';
import { EmptyState } from '@/components/shared/empty-state';
import { useInfiniteAuditLogs, useAuditRetention } from '@/hooks/use-audit';
import { auditApi, type AuditQuery } from '@/lib/api/audit';
import { apiUrl } from '@/lib/api/client';
import { useAuthStore } from '@/stores/auth-store';

async function download(path: string, filename: string) {
  const token = useAuthStore.getState().accessToken;
  const res = await fetch(apiUrl(path), {
    credentials: 'include',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

export function AuditViewer() {
  const [draft, setDraft] = useState<AuditQuery>({});
  const [filters, setFilters] = useState<AuditQuery>({});
  const retention = useAuditRetention();
  const logs = useInfiniteAuditLogs(filters);

  const items = logs.data?.pages.flatMap((p) => p.items) ?? [];
  const total = logs.data?.pages[0]?.total ?? null;

  function apply(e: React.FormEvent) { e.preventDefault(); setFilters(draft); }

  return (
    <div className="space-y-6">
      {retention.data && (
        <Card>
          <CardHeader>
            <CardTitle>Retention</CardTitle>
            <CardDescription>{retention.data.policy}</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-6 text-sm">
            <div><div className="text-muted-foreground">Window</div><div className="font-medium">{retention.data.retention_days} days</div></div>
            <div><div className="text-muted-foreground">Total records</div><div className="font-medium">{retention.data.total_records}</div></div>
            <div><div className="text-muted-foreground">Past window</div><div className="font-medium">{retention.data.archivable_records}</div></div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader className="flex-row items-center justify-between space-y-0">
          <CardTitle>Activity</CardTitle>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => download(auditApi.exportPath('csv', filters), 'audit-export.csv')}>
              <Download className="mr-2 h-4 w-4" />CSV
            </Button>
            <Button variant="outline" size="sm" onClick={() => download(auditApi.exportPath('json', filters), 'audit-export.json')}>
              <Download className="mr-2 h-4 w-4" />JSON
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={apply} className="mb-4 flex flex-wrap items-end gap-2">
            <Input placeholder="Search action, entity, metadata" className="max-w-64"
              value={draft.q ?? ''} onChange={(e) => setDraft((d) => ({ ...d, q: e.target.value }))} />
            <Input placeholder="action (e.g. role.assigned)" className="max-w-56"
              value={draft.action ?? ''} onChange={(e) => setDraft((d) => ({ ...d, action: e.target.value }))} />
            <Input placeholder="entity type" className="max-w-44"
              value={draft.entity_type ?? ''} onChange={(e) => setDraft((d) => ({ ...d, entity_type: e.target.value }))} />
            <Button type="submit" size="sm"><Search className="mr-2 h-4 w-4" />Filter</Button>
            {total !== null && <span className="ml-auto text-sm text-muted-foreground">{total} events</span>}
          </form>

          {logs.isLoading ? (
            <LoadingState label="Loading activity…" />
          ) : items.length === 0 ? (
            <EmptyState icon={Search} title="No matching activity" description="Adjust the filters to widen your search." />
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow><TableHead>When</TableHead><TableHead>Action</TableHead><TableHead>Entity</TableHead><TableHead>Actor</TableHead></TableRow>
                </TableHeader>
                <TableBody>
                  {items.map((a) => (
                    <TableRow key={a.id}>
                      <TableCell className="whitespace-nowrap text-sm text-muted-foreground">{new Date(a.created_at).toLocaleString()}</TableCell>
                      <TableCell><Badge variant="secondary" className="font-mono text-xs">{a.action}</Badge></TableCell>
                      <TableCell className="text-sm">{a.entity_type ?? '—'}</TableCell>
                      <TableCell className="font-mono text-xs text-muted-foreground">{a.actor_user_id?.slice(0, 8) ?? 'system'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              {logs.hasNextPage && (
                <div className="mt-4 flex justify-center">
                  <Button variant="outline" size="sm" onClick={() => logs.fetchNextPage()} disabled={logs.isFetchingNextPage}>
                    {logs.isFetchingNextPage && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}Load more
                  </Button>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
