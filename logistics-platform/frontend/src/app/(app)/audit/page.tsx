import { PageHeader } from '@/components/shared/page-header';
import { AuditViewer } from '@/components/audit/audit-viewer';

export default function AuditPage() {
  return (
    <div className="space-y-6">
      <PageHeader title="Audit log" description="Every action taken in this organization, immutable and exportable." />
      <AuditViewer />
    </div>
  );
}
