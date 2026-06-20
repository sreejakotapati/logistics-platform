import { PageHeader } from '@/components/shared/page-header';
import { OrgProfileForm } from '@/components/organizations/org-profile-form';
import { OrgSettingsForm } from '@/components/organizations/org-settings-form';

export default function OrganizationSettingsPage() {
  return (
    <div className="space-y-6">
      <PageHeader title="Organization" description="Profile and workspace settings for the active organization." />
      <OrgProfileForm />
      <OrgSettingsForm />
    </div>
  );
}
