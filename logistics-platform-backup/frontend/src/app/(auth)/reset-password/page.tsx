import { Suspense } from 'react';
import Link from 'next/link';
import { AuthCard } from '@/components/auth/auth-card';
import { PasswordResetConfirmForm } from '@/components/auth/password-reset-confirm-form';

export const metadata = { title: 'Set new password · Logistics Platform' };

export default function ResetPasswordPage() {
  return (
    <AuthCard
      title="Set a new password"
      footer={<Link href="/login" className="text-primary hover:underline">Back to sign in</Link>}
    >
      <Suspense fallback={null}><PasswordResetConfirmForm /></Suspense>
    </AuthCard>
  );
}
