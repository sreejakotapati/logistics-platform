'use client';

import { useState } from 'react';
import { toast } from 'sonner';
import { Loader2, Plus } from 'lucide-react';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogTrigger, DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { usePermissionCatalog, useCreateRole } from '@/hooks/use-rbac';
import { errorMessage } from '@/lib/errors';

export function CreateRoleDialog() {
  const { data: permissions } = usePermissionCatalog();
  const create = useCreateRole();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [selected, setSelected] = useState<Set<string>>(new Set());

  function toggle(id: string) {
    setSelected((s) => { const n = new Set(s); n.has(id) ? n.delete(id) : n.add(id); return n; });
  }

  async function onCreate() {
    try {
      await create.mutateAsync({ name, description: description || undefined, permission_ids: [...selected] });
      toast.success('Role created');
      setOpen(false); setName(''); setDescription(''); setSelected(new Set());
    } catch (err) { toast.error(errorMessage(err)); }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm"><Plus className="mr-2 h-4 w-4" />New role</Button>
      </DialogTrigger>
      <DialogContent className="max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create custom role</DialogTitle>
          <DialogDescription>Bundle permissions into a role you can assign to members.</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="role-name">Name</Label>
            <Input id="role-name" value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="role-desc">Description</Label>
            <Textarea id="role-desc" value={description} onChange={(e) => setDescription(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label>Permissions</Label>
            <div className="grid grid-cols-1 gap-1.5 rounded-md border p-3 sm:grid-cols-2">
              {(permissions ?? []).map((p) => (
                <label key={p.id} className="flex items-start gap-2 text-sm">
                  <input type="checkbox" checked={selected.has(p.id)} onChange={() => toggle(p.id)} className="mt-0.5" />
                  <span><span className="font-mono text-xs">{p.key}</span>{p.description ? <span className="block text-xs text-muted-foreground">{p.description}</span> : null}</span>
                </label>
              ))}
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button onClick={onCreate} disabled={!name || create.isPending}>
            {create.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}Create role
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
