# Frontend Build Verification

Closes Sprint 1 audit item **TD-01** (frontend reproducibility + build verification). No business
features — scaffold validation only.

## 1. Configuration validation (reviewed)

| File | Verdict | Notes |
|---|---|---|
| `package.json` | ✅ Valid | Scripts (`dev/build/start/lint/type-check`) correct. Next 15.1.0 + React 19 + the ShadCN/Radix set are mutually compatible (see §2). |
| `next.config.mjs` | ✅ Valid | `output: 'standalone'` matches the production Docker stage; `reactStrictMode` on. |
| `tsconfig.json` | ✅ Valid | `strict`, `moduleResolution: bundler`, `jsx: preserve`, `@/*` path alias, Next plugin — standard Next 15 config. |
| `tailwind.config.ts` | ✅ Valid | `darkMode: class`, content glob `./src/**/*.{ts,tsx}`, CSS-variable tokens + the 8-status spine, `tailwindcss-animate` plugin. |
| `.eslintrc.json` | ✅ Valid | `next/core-web-vitals`. (Optional: migrate to ESLint flat config later; not required.) |

**Dependency resolution (verified):** a strict `npm install --package-lock-only` (no
`--legacy-peer-deps`) resolves cleanly, so **React 19 peer requirements are satisfied** by the pinned
set. Resolved key versions:

| Package | Resolves to |
|---|---|
| next | 15.1.0 |
| react / react-dom | 19.0.0 |
| @radix-ui/react-dialog | 1.1.17 |
| cmdk | 1.1.1 |
| tailwindcss | 3.4.19 |
| typescript | 5.9.3 |

> No peer-dependency conflicts — `--legacy-peer-deps` is **not** required.

## 2. package-lock.json strategy

**Decision:** commit a `package-lock.json` (npm, lockfileVersion 3) and make CI install with `npm ci`
for byte-for-byte reproducible builds. npm is already the package manager (the Dockerfile and CI use
it); we standardize on it rather than introducing pnpm/yarn.

**Generate it once (bootstrap):**
```bash
cd frontend
npm install            # full resolution: writes package-lock.json + node_modules
npm run type-check     # tsc --noEmit — must pass
npm run lint           # next lint — must pass
npm run build          # next build — must pass (needs network for next/font Google fonts)
git add package-lock.json
git commit -m "build(frontend): add package-lock.json for reproducible installs"
```
> Generate the lockfile in a normal dev/CI environment with unrestricted network. (It could not be
> produced in the build sandbox here: the restricted mirror only resolved part of the tree with
> integrity hashes, which would make `npm ci` fail. A partial lockfile is worse than none, so none was
> committed — this is the correct call.)

**Keep it in sync:**
- Any dependency change is made via `npm install <pkg>` (updates both `package.json` and the lock),
  then both files are committed together.
- **Dependabot** already opens npm PRs; each updates the lockfile. Review and merge.
- Never hand-edit `package-lock.json`.
- The lockfile is the cache key in CI (`cache-dependency-path: frontend/package-lock.json`).

## 3. CI change: `npm install` → `npm ci`

Applied to both workflows:
- **`.github/workflows/frontend-ci.yml`** — install step is now `npm ci` (after asserting the lockfile
  exists, with a clear error if it doesn't).
- **`.github/workflows/dependency-scan.yml`** — frontend audit now uses `npm ci`.

`npm ci` installs **exactly** the locked tree, fails if `package.json` and the lock are out of sync,
and is faster than `npm install`. **Precondition:** the lockfile must be committed first (step in §2);
until then these jobs fail fast with a helpful message rather than silently resolving a fresh tree.

The frontend **Dockerfile** already prefers `npm ci` when a lockfile is present, so it aligns
automatically once the lockfile lands.

## 4. Frontend build verification checklist

Run from `frontend/`. Use this on the bootstrap PR and as the per-PR definition of done for frontend.

- [ ] **Install (reproducible):** `npm ci` succeeds (after the lockfile is committed). Bootstrap only:
      `npm install` to create the lockfile, then commit it.
- [ ] **Type-check:** `npm run type-check` (`tsc --noEmit`) passes with **zero** errors.
- [ ] **Lint:** `npm run lint` (`next lint`) passes with no errors.
- [ ] **Build:** `npm run build` completes; `.next/standalone/server.js` is produced
      (required by the production Docker image). Needs outbound network for `next/font` Google fonts.
- [ ] **Env at build time:** `NEXT_PUBLIC_API_URL` / `NEXT_PUBLIC_WS_URL` / `NEXT_PUBLIC_APP_ENV` are
      set (CI sets them; staging passes them as Docker build args — they are inlined at build time).
- [ ] **Production image:** `docker build -f docker/frontend/Dockerfile --target production` succeeds
      and the container starts (`node server.js`).
- [ ] **`public/` is clone-safe:** `frontend/public/` contains at least a tracked file (add
      `public/.gitkeep`) so the prod image's `COPY /app/public` works after a fresh clone.
- [ ] **Container runs non-root:** prod image runs as a non-root user (audit SR-01 / TD-04 — pending).
- [ ] **Lockfile committed and in sync:** `package-lock.json` present; `npm ci` does not report drift.
- [ ] **(Optional) Smoke test:** add a minimal render/test runner (e.g. Vitest) so the frontend has a
      test gate like the backend — currently there are none.

## 5. Still open (tracked in the audit)
- Frontend has **no tests** — add a test runner + one smoke test (audit TD-01 tail).
- Prod image runs as **root** — add a non-root `USER` (audit SR-01/TD-04).
- `frontend/public/.gitkeep` — add so empty `public/` survives a clone (audit §2 / build checklist).
