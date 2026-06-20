import { AuthCard } from '@/components/auth/auth-card';
import { AcceptInvite } from '@/components/auth/accept-invite';

export const metadata = { title: 'Accept invitation · Logistics Platform' };

export default async function InvitePage({ params }: { params: Promise<{ token: string }> }) {
  const { token } = await params;
  return (
    <AuthCard title="You're invited">
      <AcceptInvite token={token} />
    </AuthCard>
  );
}
