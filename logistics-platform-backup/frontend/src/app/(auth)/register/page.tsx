import Link from 'next/link';
import { AuthCard } from '@/components/auth/auth-card';
import { RegisterForm } from '@/components/auth/register-form';

export const metadata = { title: 'Create account · Logistics Platform' };

export default function RegisterPage() {
  return (
    <AuthCard
      title="Create your account"
      description="Set up your organization in a minute."
      footer={<>Already have an account? <Link href="/login" className="text-primary hover:underline">Sign in</Link></>}
    >
      <RegisterForm />
    </AuthCard>
  );
}
