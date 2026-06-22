'use client';

import { useEffect, useState } from 'react';
import { toast } from 'sonner';
import { Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { useUserProfile, useUpdateUserProfile } from '@/hooks/use-organizations';
import { errorMessage } from '@/lib/errors';

export function ProfileForm() {
  const { data, isLoading } = useUserProfile();
  const update = useUpdateUserProfile();
  const [fullName, setFullName] = useState('');

  useEffect(() => { if (data) setFullName(data.full_name ?? ''); }, [data]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    try { await update.mutateAsync(fullName); toast.success('Profile updated'); }
    catch (err) { toast.error(errorMessage(err)); }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Your profile</CardTitle>
        <CardDescription>Identity shared across every organization you belong to.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={onSubmit} className="max-w-md space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="email">Email</Label>
            <Input id="email" value={data?.email ?? ''} disabled />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="name">Full name</Label>
            <Input id="name" value={fullName} disabled={isLoading} onChange={(e) => setFullName(e.target.value)} />
          </div>
          <Button type="submit" disabled={update.isPending}>
            {update.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}Save changes
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
