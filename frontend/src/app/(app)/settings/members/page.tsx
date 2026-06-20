import { PageHeader } from '@/components/shared/page-header';
import { MembersTable } from '@/components/members/members-table';

export default function MembersPage() {
  return (
    <div className="space-y-6">
      <PageHeader title="Members" description="People with access to this organization." />
      <MembersTable />
    </div>
  );
}
