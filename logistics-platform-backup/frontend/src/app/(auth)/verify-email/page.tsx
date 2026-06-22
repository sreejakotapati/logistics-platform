import { Suspense } from 'react';
import { AuthCard } from '@/components/auth/auth-card';
import { EmailVerify } from '@/components/auth/email-verify';

export const metadata = { title: 'Verify email · Logistics Platform' };

export default function VerifyEmailPage() {
  return (
    <AuthCard title="Email verification">
      <Suspense fallback={null}><EmailVerify /></Suspense>
    </AuthCard>
  );
}
