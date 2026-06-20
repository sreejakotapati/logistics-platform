import { LayoutDashboard } from 'lucide-react';
import { PageHeader } from '@/components/shared/page-header';
import { EmptyState } from '@/components/shared/empty-state';

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <PageHeader title="Dashboard" description="The foundation is live. Widgets arrive with the data modules." />
      <EmptyState
        icon={LayoutDashboard}
        title="No widgets yet"
        description="Role dashboards are wired up once orders, shipments, and analytics ship."
      />
    </div>
  );
}
