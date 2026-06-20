'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useAuthStore } from '@/stores/auth-store';
import { errorMessage } from '@/lib/errors';

export function RegisterForm() {
  const router = useRouter();
  const register = useAuthStore((s) => s.register);
  const [form, setForm] = useState({ full_name: '', email: '', organization_name: '', password: '' });
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function set<K extends keyof typeof form>(k: K, v: string) { setForm((f) => ({ ...f, [k]: v })); }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await register(form);
      router.replace('/dashboard');
    } catch (err) {
      setError(errorMessage(err, 'Could not create your account'));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      {error && <Alert variant="destructive"><AlertDescription>{error}</AlertDescription></Alert>}
      <div className="space-y-1.5">
        <Label htmlFor="full_name">Your name</Label>
        <Input id="full_name" required value={form.full_name} onChange={(e) => set('full_name', e.target.value)} />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="org">Organization name</Label>
        <Input id="org" required value={form.organization_name} onChange={(e) => set('organization_name', e.target.value)} />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="email">Work email</Label>
        <Input id="email" type="email" autoComplete="email" required value={form.email} onChange={(e) => set('email', e.target.value)} />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="password">Password</Label>
        <Input id="password" type="password" autoComplete="new-password" required minLength={10}
          value={form.password} onChange={(e) => set('password', e.target.value)} />
        <p className="text-xs text-muted-foreground">At least 10 characters.</p>
      </div>
      <Button type="submit" className="w-full" disabled={busy}>
        {busy && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}Create account
      </Button>
    </form>
  );
}
