import { PageHeader } from '@/components/shared/page-header';
import { InvitationsPanel } from '@/components/invitations/invitations-panel';

export default function InvitationsPage() {
  return (
    <div className="space-y-6">
      <PageHeader title="Invitations" description="Invite teammates and manage pending invites." />
      <InvitationsPanel />
    </div>
  );
}
