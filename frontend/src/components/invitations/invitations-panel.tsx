'use client';

import { useState } from 'react';
import { toast } from 'sonner';
import { Loader2, Mail, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { LoadingState } from '@/components/shared/loading-state';
import { EmptyState } from '@/components/shared/empty-state';
import { PermissionGate } from '@/components/auth/permission-gate';
import { useInvitations, useInvite, useRevokeInvitation } from '@/hooks/use-invitations';
import { errorMessage } from '@/lib/errors';

export function InvitationsPanel() {
  const { data, isLoading } = useInvitations();
  const invite = useInvite();
  const revoke = useRevokeInvitation();
  const [email, setEmail] = useState('');

  async function onInvite(e: React.FormEvent) {
    e.preventDefault();
    try { await invite.mutateAsync({ email }); setEmail(''); toast.success('Invitation sent'); }
    catch (err) { toast.error(errorMessage(err)); }
  }
  async function onRevoke(id: string) {
    try { await revoke.mutateAsync(id); toast.success('Invitation revoked'); }
    catch (err) { toast.error(errorMessage(err)); }
  }

  return (
    <div className="space-y-6">
      <PermissionGate permission="users:invite">
        <Card>
          <CardHeader>
            <CardTitle>Invite a teammate</CardTitle>
            <CardDescription>They will receive a single-use link that expires in 7 days.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={onInvite} className="flex max-w-md items-end gap-2">
              <div className="flex-1 space-y-1.5">
                <Label htmlFor="invite-email">Email</Label>
                <Input id="invite-email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
              </div>
              <Button type="submit" disabled={invite.isPending}>
                {invite.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Mail className="mr-2 h-4 w-4" />}
                Send invite
              </Button>
            </form>
          </CardContent>
        </Card>
      </PermissionGate>

      <Card>
        <CardHeader><CardTitle>Pending invitations</CardTitle></CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6"><LoadingState label="Loading invitations…" /></div>
          ) : !data || data.length === 0 ? (
            <div className="p-6"><EmptyState title="No pending invitations" description="Invitations you send appear here until accepted." /></div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow><TableHead>Email</TableHead><TableHead>Status</TableHead><TableHead>Expires</TableHead><TableHead className="w-12" /></TableRow>
              </TableHeader>
              <TableBody>
                {data.map((inv) => (
                  <TableRow key={inv.id}>
                    <TableCell className="font-medium">{inv.email}</TableCell>
                    <TableCell><Badge variant="secondary">{inv.status}</Badge></TableCell>
                    <TableCell className="text-sm text-muted-foreground">{new Date(inv.expires_at).toLocaleDateString()}</TableCell>
                    <TableCell>
                      <PermissionGate permission="users:invite">
                        <Button variant="ghost" size="icon" aria-label="Revoke" onClick={() => onRevoke(inv.id)}>
                          <X className="h-4 w-4" />
                        </Button>
                      </PermissionGate>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
