import Link from 'next/link';
import { AuthCard } from '@/components/auth/auth-card';
import { LoginForm } from '@/components/auth/login-form';

export const metadata = { title: 'Sign in · Logistics Platform' };

export default function LoginPage() {
  return (
    <AuthCard
      title="Sign in"
      description="Welcome back. Enter your details to continue."
      footer={<>New here? <Link href="/register" className="text-primary hover:underline">Create an account</Link></>}
    >
      <LoginForm />
    </AuthCard>
  );
}
