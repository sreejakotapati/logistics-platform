'use client';

import { useState } from 'react';
import { toast } from 'sonner';
import { MoreHorizontal, ShieldCheck } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { LoadingState } from '@/components/shared/loading-state';
import { EmptyState } from '@/components/shared/empty-state';
import { PermissionGate } from '@/components/auth/permission-gate';
import { MemberRolesDialog } from '@/components/members/member-roles-dialog';
import { useMembers, useUpdateMember, useRemoveMember } from '@/hooks/use-members';
import type { MemberSummary } from '@/lib/api/types';
import { errorMessage } from '@/lib/errors';

export function MembersTable() {
  const { data, isLoading } = useMembers();
  const updateMember = useUpdateMember();
  const removeMember = useRemoveMember();
  const [rolesFor, setRolesFor] = useState<MemberSummary | null>(null);

  if (isLoading) return <LoadingState label="Loading members…" />;
  if (!data || data.length === 0) return <EmptyState title="No members yet" description="Invite teammates to get started." />;

  async function setStatus(userId: string, status: string) {
    try { await updateMember.mutateAsync({ userId, status }); toast.success('Member updated'); }
    catch (err) { toast.error(errorMessage(err)); }
  }
  async function remove(userId: string) {
    try { await removeMember.mutateAsync(userId); toast.success('Member removed'); }
    catch (err) { toast.error(errorMessage(err)); }
  }

  return (
    <Card>
      <CardContent className="p-0">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Member</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="w-12"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((m) => (
              <TableRow key={m.user_id}>
                <TableCell>
                  <div className="font-medium">{m.full_name ?? '—'}</div>
                  <div className="text-xs text-muted-foreground">{m.email}</div>
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    <Badge variant={m.membership_status === 'active' ? 'success' : 'warning'}>{m.membership_status}</Badge>
                    {m.is_primary && <Badge variant="outline">primary</Badge>}
                  </div>
                </TableCell>
                <TableCell>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon" aria-label="Member actions"><MoreHorizontal className="h-4 w-4" /></Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <PermissionGate permission="roles:manage">
                        <DropdownMenuItem onSelect={() => setRolesFor(m)}>
                          <ShieldCheck className="mr-2 h-4 w-4" />Manage roles
                        </DropdownMenuItem>
                      </PermissionGate>
                      <PermissionGate permission="users:update">
                        {m.membership_status === 'active' ? (
                          <DropdownMenuItem onSelect={() => setStatus(m.user_id, 'suspended')}>Suspend</DropdownMenuItem>
                        ) : (
                          <DropdownMenuItem onSelect={() => setStatus(m.user_id, 'active')}>Reactivate</DropdownMenuItem>
                        )}
                      </PermissionGate>
                      <PermissionGate permission="users:remove">
                        <DropdownMenuItem className="text-destructive" onSelect={() => remove(m.user_id)}>Remove</DropdownMenuItem>
                      </PermissionGate>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
      <MemberRolesDialog member={rolesFor} open={!!rolesFor} onOpenChange={(v) => !v && setRolesFor(null)} />
    </Card>
  );
}
