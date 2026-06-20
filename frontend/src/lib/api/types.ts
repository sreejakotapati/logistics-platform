// API response/request types mirroring the backend Pydantic contracts (S2-T2 … S2-T6).

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in?: number;
}

export interface MeUser {
  id: string;
  email: string;
  full_name: string | null;
  status?: string;
  email_verified?: boolean;
}

export interface OrganizationSummary {
  id: string;
  name: string;
  slug: string;
  status: string;
  is_primary: boolean;
  membership_status: string;
}

export interface OrganizationProfile {
  id: string;
  name: string;
  slug: string;
  status: string;
  legal_name: string | null;
  gstin: string | null;
  country_code: string | null;
  currency: string | null;
  contact_email: string | null;
  contact_phone: string | null;
  website: string | null;
  address_line1: string | null;
  address_line2: string | null;
  city: string | null;
  state: string | null;
  postal_code: string | null;
}

export type OrganizationProfileUpdate = Partial<
  Pick<
    OrganizationProfile,
    | 'name' | 'legal_name' | 'gstin' | 'contact_email' | 'contact_phone' | 'website'
    | 'address_line1' | 'address_line2' | 'city' | 'state' | 'postal_code'
  >
>;

export interface MemberSummary {
  user_id: string;
  email: string;
  full_name: string | null;
  membership_status: string;
  is_primary: boolean;
}

export interface InvitationSummary {
  id: string;
  email: string;
  status: string;
  role_id: string | null;
  expires_at: string;
}

export interface InvitationPreview {
  organization_id: string;
  organization_name: string;
  email: string;
  status: string;
  expired: boolean;
}

export interface UserProfile {
  id: string;
  email: string;
  full_name: string | null;
  status: string;
  email_verified: boolean;
}

export interface Permission {
  id: string;
  key: string;
  description: string | null;
}

export interface Role {
  id: string;
  name: string;
  description: string | null;
  is_system: boolean;
  organization_id: string | null;
}

export interface AuditLog {
  id: string;
  organization_id: string | null;
  actor_user_id: string | null;
  action: string;
  entity_type: string | null;
  entity_id: string | null;
  metadata: Record<string, unknown>;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
}

export interface AuditPage {
  items: AuditLog[];
  next_cursor: string | null;
  total: number | null;
}

export interface TimelineBucket {
  date: string;
  count: number;
  items: AuditLog[];
}

export interface AuditTimeline {
  buckets: TimelineBucket[];
  next_cursor: string | null;
}

export interface RetentionPreview {
  retention_days: number;
  cutoff: string;
  total_records: number;
  archivable_records: number;
  oldest: string | null;
  newest: string | null;
  policy: string;
}

export interface MessageResponse {
  message: string;
}
