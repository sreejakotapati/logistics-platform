# Frontend Architecture (Foundation)

## Stack
Next.js 15 (App Router, React 19) · TypeScript (strict) · Tailwind + ShadCN (new-york) ·
React Query (server state) · Zustand (client/UI state) · next-themes (dark mode).

## Folder structure
See `frontend/README.md`. Routes use the App Router; the authenticated surface lives under the
`(app)` route group wrapped by the `AppShell`.

## Providers & startup flow
```mermaid
flowchart TD
  root[app/layout.tsx] --> fonts[next/font: Inter + JetBrains Mono -> CSS vars]
  root --> prov[Providers (client)]
  prov --> q[QueryClientProvider]
  prov --> t[ThemeProvider (class strategy)]
  prov --> group[(app)/layout.tsx -> AppShell]
  group --> shell[Sidebar + TopNav + main + CommandPalette]
  shell --> page[route page]
```
1. Root layout loads fonts (as CSS variables), applies global tokens, and mounts `Providers`.
2. `Providers` sets up the React Query client (one per app instance) and the theme provider.
3. The `(app)` group renders the `AppShell` (sidebar, top nav, command palette) around each page.
4. `⌘K` toggles the command palette via the Zustand UI store.

## Design token system
- CSS variables in `globals.css` define ShadCN tokens (background/foreground/primary/...) for light
  and `.dark`, with **Indigo** as primary, plus the **8-status logistics spine** as `--status-*`.
- `tailwind.config.ts` maps those variables to utilities (`bg-primary`, `text-status-in-transit`, ...).
- Fonts: Inter (UI) + JetBrains Mono (data/IDs) via `--font-sans` / `--font-mono`.

## State management
- **React Query** owns server state (data fetching/caching) — used once modules ship.
- **Zustand** (`stores/ui-store.ts`) owns ephemeral UI state (sidebar collapsed, command palette).
- No business/server state is fetched in S1-T6.

## API client foundation
`lib/api/client.ts` is a typed `fetch` wrapper: base URL from `NEXT_PUBLIC_API_URL`, JSON handling, a
normalized `ApiError`, and an `X-Request-ID`. Auth (Bearer token) and active-org context are added in
Sprint 2.

## Universal states
`components/shared/` provides `LoadingState`, `EmptyState`, and `ErrorState`, wired into the App
Router's `loading.tsx` / `error.tsx` / `not-found.tsx` / `global-error.tsx`.

## What is NOT here (by design)
No Auth, login, users, organizations, RBAC, or any business screens (orders, shipments, tracking,
fleet, warehouses). The org switcher, user menu, notifications, and disabled nav items are placeholders
that light up from Sprint 2.
