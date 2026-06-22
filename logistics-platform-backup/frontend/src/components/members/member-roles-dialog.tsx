'use client';

import { useState } from 'react';
import { toast } from 'sonner';
import { Loader2, X } from 'lucide-react';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useMemberRoles, useRoles, useAssignRole, useRemoveRole } from '@/hooks/use-rbac';
import type { MemberSummary } from '@/lib/api/types';
import { errorMessage } from '@/lib/errors';

export function MemberRolesDialog({ member, open, onOpenChange }: {
  member: MemberSummary | null; open: boolean; onOpenChange: (v: boolean) => void;
}) {
  const userId = member?.user_id ?? null;
  const memberRoles = useMemberRoles(open ? userId : null);
  const roles = useRoles();
  const assign = useAssignRole();
  const remove = useRemoveRole();
  const [selected, setSelected] = useState<string>('');

  const assignedIds = new Set((memberRoles.data ?? []).map((r) => r.id));
  const assignable = (roles.data ?? []).filter((r) => !assignedIds.has(r.id));

  async function onAssign() {
    if (!userId || !selected) return;
    try { await assign.mutateAsync({ userId, roleId: selected }); setSelected(''); toast.success('Role assigned'); }
    catch (err) { toast.error(errorMessage(err)); }
  }

  async function onRemove(roleId: string) {
    if (!userId) return;
    try { await remove.mutateAsync({ userId, roleId }); toast.success('Role removed'); }
    catch (err) { toast.error(errorMessage(err)); }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Roles for {member?.full_name ?? member?.email}</DialogTitle>
          <DialogDescription>Permissions are the union of every assigned role.</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {(memberRoles.data ?? []).map((r) => (
              <Badge key={r.id} variant="secondary" className="gap-1">
                {r.name}
                <button onClick={() => onRemove(r.id)} aria-label={`Remove ${r.name}`} className="ml-1 hover:text-destructive">
                  <X className="h-3 w-3" />
                </button>
              </Badge>
            ))}
            {memberRoles.data?.length === 0 && <p className="text-sm text-muted-foreground">No roles assigned.</p>}
          </div>
          <div className="flex items-center gap-2">
            <Select value={selected} onValueChange={setSelected}>
              <SelectTrigger className="flex-1"><SelectValue placeholder="Add a role" /></SelectTrigger>
              <SelectContent>
                {assignable.map((r) => (
                  <SelectItem key={r.id} value={r.id}>
                    {r.name}{r.is_system ? ' · system' : ''}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button onClick={onAssign} disabled={!selected || assign.isPending}>
              {assign.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}Assign
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
