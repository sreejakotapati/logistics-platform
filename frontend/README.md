# Frontend (Next.js 15)

App Router · TypeScript · Tailwind · ShadCN · React Query · Zustand. Foundation + app shell
scaffolded in **S1-T6** (no business screens).

## Layout
```
src/
  app/
    layout.tsx              # root: fonts, Providers (Query + Theme)
    page.tsx                # foundation landing
    globals.css             # design tokens (CSS variables, light/dark, status spine)
    not-found.tsx · global-error.tsx
    (app)/                  # authenticated app group
      layout.tsx            # AppShell wrapper
      dashboard/page.tsx    # placeholder dashboard
      loading.tsx · error.tsx
  components/
    ui/                     # ShadCN primitives
    shared/                 # empty / error / loading states, page-header, status-badge
    shell/                  # app-shell, sidebar, top-nav, command-palette, org-switcher, theme/user menus
    providers.tsx           # QueryClient + Theme providers
  lib/
    utils.ts                # cn()
    api/{client,query-client}.ts
    config/{env,nav}.ts
  stores/ui-store.ts        # Zustand (sidebar, command palette)
  types/index.ts
```

## Run
```bash
cd frontend
npm install
cp .env.local.example .env.local   # or rely on the root .env via docker
npm run dev                          # http://localhost:3000
```

## Not implemented here (by design)
No Auth, login, users, organizations, RBAC, or business screens — only the shell and foundation.
The org switcher, user menu, and nav items beyond Dashboard are placeholders for Sprint 2.


---
**See also:** [Frontend architecture](../docs/architecture/frontend-architecture.md) · [Coding Standards](../CONVENTIONS.md) · [Local Development](../docs/guides/local-development.md) · [Docs index](../docs/README.md)
