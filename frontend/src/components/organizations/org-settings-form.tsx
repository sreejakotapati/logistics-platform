'use client';

import { useEffect, useState } from 'react';
import { toast } from 'sonner';
import { Loader2, Plus, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { useOrganizationSettings, useUpdateSettings } from '@/hooks/use-organizations';
import { PermissionGate } from '@/components/auth/permission-gate';
import { errorMessage } from '@/lib/errors';

type Entry = { key: string; value: string };

export function OrgSettingsForm() {
  const { data } = useOrganizationSettings();
  const update = useUpdateSettings();
  const [entries, setEntries] = useState<Entry[]>([]);

  useEffect(() => {
    if (data?.settings) {
      setEntries(Object.entries(data.settings).map(([key, value]) => ({ key, value: String(value) })));
    }
  }, [data]);

  async function onSave() {
    const settings = Object.fromEntries(entries.filter((e) => e.key).map((e) => [e.key, e.value]));
    try { await update.mutateAsync(settings); toast.success('Settings saved'); }
    catch (err) { toast.error(errorMessage(err)); }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Organization settings</CardTitle>
        <CardDescription>Preferences applied across the workspace (e.g. timezone, locale).</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {entries.map((e, i) => (
          <div key={i} className="flex items-center gap-2">
            <Input placeholder="key" value={e.key} className="max-w-48"
              onChange={(ev) => setEntries((s) => s.map((x, j) => (j === i ? { ...x, key: ev.target.value } : x)))} />
            <Input placeholder="value" value={e.value}
              onChange={(ev) => setEntries((s) => s.map((x, j) => (j === i ? { ...x, value: ev.target.value } : x)))} />
            <Button variant="ghost" size="icon" aria-label="Remove"
              onClick={() => setEntries((s) => s.filter((_, j) => j !== i))}>
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        ))}
        <Button variant="outline" size="sm" onClick={() => setEntries((s) => [...s, { key: '', value: '' }])}>
          <Plus className="mr-2 h-4 w-4" />Add setting
        </Button>
        <div className="pt-2">
          <PermissionGate permission="org:update"
            fallback={<p className="text-xs text-muted-foreground">You need the “org:update” permission to change settings.</p>}>
            <Button onClick={onSave} disabled={update.isPending}>
              {update.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}Save settings
            </Button>
          </PermissionGate>
        </div>
      </CardContent>
    </Card>
  );
}
