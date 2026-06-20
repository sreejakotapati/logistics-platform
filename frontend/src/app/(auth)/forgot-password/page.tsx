import Link from 'next/link';
import { AuthCard } from '@/components/auth/auth-card';
import { PasswordResetRequestForm } from '@/components/auth/password-reset-request-form';

export const metadata = { title: 'Reset password · Logistics Platform' };

export default function ForgotPasswordPage() {
  return (
    <AuthCard
      title="Reset your password"
      description="We'll email you a link to set a new password."
      footer={<Link href="/login" className="text-primary hover:underline">Back to sign in</Link>}
    >
      <PasswordResetRequestForm />
    </AuthCard>
  );
}
