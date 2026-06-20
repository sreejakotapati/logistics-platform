import { PageHeader } from '@/components/shared/page-header';
import { RolesPanel } from '@/components/rbac/roles-panel';

export default function RolesPage() {
  return (
    <div className="space-y-6">
      <PageHeader title="Roles & permissions" description="Define what members can do in this organization." />
      <RolesPanel />
    </div>
  );
}
