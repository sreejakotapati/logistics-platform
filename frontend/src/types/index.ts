import type { LucideIcon } from 'lucide-react';

export interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
  /** Placeholder items render disabled until their module ships (Sprint 2+). */
  disabled?: boolean;
}

export interface NavGroup {
  label: string;
  items: NavItem[];
}

/** Standard API error shape thrown by the API client. */
export interface ApiError {
  status: number;
  code: string;
  message: string;
  details?: Record<string, unknown>;
}
