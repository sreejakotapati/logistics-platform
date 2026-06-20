'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Loader2 } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { orgApi } from '@/lib/api/organizations';
import { useSession } from '@/features/auth/use-session';
import { errorMessage } from '@/lib/errors';

export function AcceptInvite({ token }: { token: string }) {
  const router = useRouter();
  const { isAuthenticated } = useSession();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const preview = useQuery({
    queryKey: ['invitation', token],
    queryFn: () => orgApi.previewInvitation(token),
  });

  async function accept() {
    setError(null);
    setBusy(true);
    try {
      await orgApi.acceptInvitation(token);
      router.replace('/dashboard');
    } catch (err) {
      setError(errorMessage(err, 'This invitation could not be accepted'));
    } finally {
      setBusy(false);
    }
  }

  if (preview.isLoading) return <p className="text-sm text-muted-foreground">Loading invitation…</p>;
  if (preview.isError) return <Alert variant="destructive"><AlertDescription>This invitation link is invalid.</AlertDescription></Alert>;

  const inv = preview.data!;
  if (inv.expired || inv.status !== 'pending') {
    return <Alert variant="destructive"><AlertDescription>This invitation has expired or already been used.</AlertDescription></Alert>;
  }

  return (
    <div className="space-y-4">
      <p className="text-sm">
        You have been invited to join <span className="font-medium">{inv.organization_name}</span> as{' '}
        <span className="font-medium">{inv.email}</span>.
      </p>
      {error && <Alert variant="destructive"><AlertDescription>{error}</AlertDescription></Alert>}
      {isAuthenticated ? (
        <Button className="w-full" onClick={accept} disabled={busy}>
          {busy && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}Accept invitation
        </Button>
      ) : (
        <Alert><AlertDescription>Sign in as {inv.email} to accept this invitation.</AlertDescription></Alert>
      )}
    </div>
  );
}
