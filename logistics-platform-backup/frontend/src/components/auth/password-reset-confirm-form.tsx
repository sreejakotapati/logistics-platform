'use client';

import { useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { authApi } from '@/lib/api/auth';
import { errorMessage } from '@/lib/errors';

export function PasswordResetConfirmForm() {
  const router = useRouter();
  const token = useSearchParams().get('token') ?? '';
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await authApi.confirmPasswordReset(token, password);
      router.replace('/login?reset=1');
    } catch (err) {
      setError(errorMessage(err, 'This reset link is invalid or has expired'));
    } finally {
      setBusy(false);
    }
  }

  if (!token) {
    return <Alert variant="destructive"><AlertDescription>This reset link is missing its token.</AlertDescription></Alert>;
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      {error && <Alert variant="destructive"><AlertDescription>{error}</AlertDescription></Alert>}
      <div className="space-y-1.5">
        <Label htmlFor="password">New password</Label>
        <Input id="password" type="password" autoComplete="new-password" required minLength={10}
          value={password} onChange={(e) => setPassword(e.target.value)} />
      </div>
      <Button type="submit" className="w-full" disabled={busy}>
        {busy && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}Set new password
      </Button>
    </form>
  );
}
