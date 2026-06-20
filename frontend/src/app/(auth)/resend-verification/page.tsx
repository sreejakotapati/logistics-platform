import Link from 'next/link';
import { AuthCard } from '@/components/auth/auth-card';
import { ResendVerificationForm } from '@/components/auth/resend-verification-form';

export const metadata = { title: 'Resend verification · Logistics Platform' };

export default function ResendVerificationPage() {
  return (
    <AuthCard
      title="Resend verification"
      description="Enter your email to receive a new verification link."
      footer={<Link href="/login" className="text-primary hover:underline">Back to sign in</Link>}
    >
      <ResendVerificationForm />
    </AuthCard>
  );
}
