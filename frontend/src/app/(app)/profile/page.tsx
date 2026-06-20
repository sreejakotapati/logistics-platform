import { PageHeader } from '@/components/shared/page-header';
import { ProfileForm } from '@/components/organizations/profile-form';

export default function ProfilePage() {
  return (
    <div className="space-y-6">
      <PageHeader title="Profile" description="Your personal account details." />
      <ProfileForm />
    </div>
  );
}
