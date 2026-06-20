import {
  LayoutDashboard, Package, Truck, Warehouse, Wallet, BarChart3,
  Building2, Users, Mail, ShieldCheck, ScrollText, User,
} from 'lucide-react';
import type { NavGroup } from '@/types';

// Foundation navigation. Dashboard + Administration are live (Sprint 2). Operations/Business groups
// remain disabled placeholders until their modules ship in later sprints.
export const navigation: NavGroup[] = [
  {
    label: 'Overview',
    items: [{ label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard }],
  },
  {
    label: 'Operations',
    items: [
      { label: 'Orders', href: '#', icon: Package, disabled: true },
      { label: 'Shipments', href: '#', icon: Truck, disabled: true },
      { label: 'Warehouse', href: '#', icon: Warehouse, disabled: true },
    ],
  },
  {
    label: 'Business',
    items: [
      { label: 'Finance', href: '#', icon: Wallet, disabled: true },
      { label: 'Analytics', href: '#', icon: BarChart3, disabled: true },
    ],
  },
  {
    label: 'Administration',
    items: [
      { label: 'Profile', href: '/profile', icon: User },
      { label: 'Organization', href: '/settings/organization', icon: Building2 },
      { label: 'Members', href: '/settings/members', icon: Users },
      { label: 'Invitations', href: '/settings/invitations', icon: Mail },
      { label: 'Roles', href: '/settings/roles', icon: ShieldCheck },
      { label: 'Audit log', href: '/audit', icon: ScrollText },
    ],
  },
];
