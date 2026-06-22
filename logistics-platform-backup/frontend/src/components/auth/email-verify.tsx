'use client';

import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { CheckCircle2, Loader2, XCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { authApi } from '@/lib/api/auth';
import { errorMessage } from '@/lib/errors';

type State = 'verifying' | 'ok' | 'error';

export function EmailVerify() {
  const token = useSearchParams().get('token') ?? '';
  const [state, setState] = useState<State>('verifying');
  const [message, setMessage] = useState('');
  const ran = useRef(false);

  useEffect(() => {
    if (ran.current) return;
    ran.current = true;
    if (!token) { setState('error'); setMessage('This verification link is missing its token.'); return; }
    authApi.verifyEmail(token)
      .then(() => setState('ok'))
      .catch((e) => { setState('error'); setMessage(errorMessage(e, 'This link is invalid or has expired.')); });
  }, [token]);

  if (state === 'verifying') {
    return <p className="flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="h-4 w-4 animate-spin" />Verifying your email…</p>;
  }
  if (state === 'ok') {
    return (
      <div className="space-y-4">
        <p className="flex items-center gap-2 text-sm"><CheckCircle2 className="h-5 w-5 text-emerald-600" />Your email is verified.</p>
        <Button asChild className="w-full"><Link href="/dashboard">Continue</Link></Button>
      </div>
    );
  }
  return (
    <div className="space-y-4">
      <p className="flex items-center gap-2 text-sm"><XCircle className="h-5 w-5 text-destructive" />{message}</p>
      <Button asChild variant="outline" className="w-full"><Link href="/resend-verification">Request a new link</Link></Button>
    </div>
  );
}
