'use client';

import { useEffect, useState } from 'react';
import { toast } from 'sonner';
import { Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { useCurrentOrganization, useUpdateOrganization } from '@/hooks/use-organizations';
import { PermissionGate } from '@/components/auth/permission-gate';
import type { OrganizationProfileUpdate } from '@/lib/api/types';
import { errorMessage } from '@/lib/errors';

const FIELDS: { key: keyof OrganizationProfileUpdate; label: string; placeholder?: string }[] = [
  { key: 'name', label: 'Organization name' },
  { key: 'legal_name', label: 'Legal name' },
  { key: 'gstin', label: 'GSTIN', placeholder: '29ABCDE1234F1Z5' },
  { key: 'contact_email', label: 'Contact email' },
  { key: 'contact_phone', label: 'Contact phone' },
  { key: 'website', label: 'Website' },
  { key: 'address_line1', label: 'Address line 1' },
  { key: 'address_line2', label: 'Address line 2' },
  { key: 'city', label: 'City' },
  { key: 'state', label: 'State' },
  { key: 'postal_code', label: 'Postal code' },
];

export function OrgProfileForm() {
  const { data } = useCurrentOrganization();
  const update = useUpdateOrganization();
  const [form, setForm] = useState<OrganizationProfileUpdate>({});

  useEffect(() => {
    if (data) {
      setForm(Object.fromEntries(FIELDS.map((f) => [f.key, (data[f.key] as string) ?? ''])));
    }
  }, [data]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const payload = Object.fromEntries(
      Object.entries(form).filter(([, v]) => v !== '' && v !== null),
    );
    try { await update.mutateAsync(payload); toast.success('Organization updated'); }
    catch (err) { toast.error(errorMessage(err)); }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Organization profile</CardTitle>
        <CardDescription>Details used across invoices, e-way bills, and compliance documents.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={onSubmit} className="grid max-w-2xl grid-cols-1 gap-4 sm:grid-cols-2">
          {FIELDS.map((f) => (
            <div key={f.key} className="space-y-1.5">
              <Label htmlFor={f.key}>{f.label}</Label>
              <Input id={f.key} placeholder={f.placeholder}
                value={(form[f.key] as string) ?? ''}
                onChange={(e) => setForm((s) => ({ ...s, [f.key]: e.target.value }))} />
            </div>
          ))}
          <div className="sm:col-span-2">
            <PermissionGate permission="org:update"
              fallback={<p className="text-xs text-muted-foreground">You need the “org:update” permission to edit these details.</p>}>
              <Button type="submit" disabled={update.isPending}>
                {update.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}Save changes
              </Button>
            </PermissionGate>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
