# Sprint 2 Backlog — Secure Core

**Owners:** Product Manager + Engineering Manager · **Theme:** Authentication · Users · Organizations ·
RBAC · Audit Logs · **Milestone:** M1 (Secure foundation) · **Depends on:** Sprint 1 (Foundations) ✅

> Architecture is locked (`CLAUDE.md`, ADR-0001). Every item below respects: **multi-tenant isolation**
> (shared schema + `organization_id` + RLS), **JWT active-organization context** (active org is a signed
> token claim that sets `app.current_org_id` per request — never a client header), **database-driven
> RBAC** (permission checks, not role-name checks), and **append-only audit logging**.
> **Out of scope (Sprint 3):** Departments, Teams, Notifications, Feature Flags.

---

## 1. Sprint Goal

> Stand up the secure core: a person can register or be provisioned into an organization, sign in, and
> switch organizations, with **every tenant read/write enforced by PostgreSQL RLS**, **every protected
> action gated by database-driven permissions**, and **every security-relevant event captured in an
> append-only audit log** — proven by an automated cross-tenant isolation suite running green in CI.

A single sentence of done: *multi-org auth + RLS isolation proven + RBAC + audit.*

---

## 2 & 3. Tasks and Subtasks

### S2-T0 — RLS Verification Harness **(gate — do first)**
Implements the approved [RLS Verification Plan](../testing/rls-verification-plan.md) as an automated
suite and **required CI check**. No tenant table may merge until this is green.
- S2-T0.1 Integration harness (`backend/tests/integration/test_rls.py`): three role-scoped connections (`app_user`, owner/migrator, `app_superadmin`); ephemeral `rls_verify` probe; transaction-isolated cases.
- S2-T0.2 Implement all cases (A–J): positive isolation, cross-tenant insert/update/delete rejection, missing/empty/invalid context fail-closed, bypass resistance, approved-bypass control, owner-under-FORCE.
- S2-T0.3 Wire as a **required** status check in `backend-ci.yml`; provision test roles idempotently.
- S2-T0.4 Parametrize the suite so each real Sprint-2 tenant table is added to the run.

### S2-T1 — Secure-core schema & migrations *(Database Architect)*
- S2-T1.1 `organizations` (org-scoped root): name, slug, GSTIN, country=IN, currency=INR, status; UUIDv7 + audit/soft-delete/version.
- S2-T1.2 `users` (**global identity, no `organization_id`**): email (unique), password_hash (Argon2), name, status, email_verified_at.
- S2-T1.3 `user_organizations` (membership = the tenant boundary): user_id, organization_id, status, is_primary (one primary per user per org via partial unique index), invited_by.
- S2-T1.4 RBAC tables: `permissions` (catalog), `roles` (system + org-custom), `role_permissions`, `user_organization_roles` (roles assigned within a membership).
- S2-T1.5 `audit_logs` (append-only): organization_id (nullable for platform events), actor_user_id, action, entity_type, entity_id, metadata jsonb, ip, user_agent, created_at.
- S2-T1.6 Apply `app.enable_org_rls()` to **every** org-scoped table in the **same migration**; `users` stays global. Add the standard `updated_at` trigger.
- S2-T1.7 Seed system roles (Super Admin, Org Admin, Manager, Member) + permission catalog (idempotent seed migration).

### S2-T2 — Authentication service *(Backend)*
- S2-T2.1 Self-service **organization registration** (onboarding path A): creates org + user + Org Admin membership atomically.
- S2-T2.2 **Super Admin provisioning** (onboarding path B): create org + initial Org Admin membership.
- S2-T2.3 Login (email/password, Argon2 verify) → issue **access JWT (15 min)** with claims `sub`, active `org`, `jti`, `exp`; set **rotating refresh token** in an httpOnly/Secure/SameSite cookie.
- S2-T2.4 Refresh rotation with **reuse detection** (revoke family on reuse); refresh store in Redis/DB.
- S2-T2.5 Logout / revoke; `GET /me` session endpoint (user + active org + effective permissions).
- S2-T2.6 **Switch-organization** endpoint → mints a **new JWT** scoped to the chosen org (decision #1); rejects orgs the user isn't a member of.
- S2-T2.7 Auth dependency: validate token → resolve user + active org → hand to the tenancy dependency (T3).

### S2-T3 — Tenancy context wiring *(Backend — load-bearing)*
- S2-T3.1 Request-scoped session that executes `SET LOCAL app.current_org_id = <claim>` inside the transaction from the **validated JWT org claim only**.
- S2-T3.2 Tenant-route guard: a request without a valid authenticated org context cannot reach tenant data (fails closed).
- S2-T3.3 Negative tests: forged/absent/mismatched org claim → zero tenant rows (ties to T0).

### S2-T4 — Users & Organizations management APIs *(Backend)*
- S2-T4.1 Organization: read/update current org profile (GSTIN/status); Super Admin list/suspend orgs.
- S2-T4.2 Membership: invite user (create global user if absent + membership), list members (org-scoped), update membership status, remove membership, set primary.
- S2-T4.3 Multi-org: list my organizations; current active org; (switch lives in T2.6).
- S2-T4.4 Each endpoint: schema → repository → service → router, RBAC-gated (T5), audit-emitting (T6).

### S2-T5 — RBAC engine (database-driven) *(Backend)*
- S2-T5.1 Permission catalog (e.g. `org:read`, `org:update`, `users:invite`, `users:remove`, `roles:manage`, `audit:read`, `org:provision`) + seed.
- S2-T5.2 Roles: global **system** roles + org-scoped **custom** roles; `role_permissions` mapping; assign/revoke roles within a membership.
- S2-T5.3 Effective-permission resolution for a user in the active org.
- S2-T5.4 `require_permission("…")` dependency — **deny-by-default**, permission-based (never role-name checks); applied to every protected endpoint.
- S2-T5.5 Admin APIs to manage roles/permissions (Org Admin within org; Super Admin platform-wide).

### S2-T6 — Audit logging *(Backend)*
- S2-T6.1 Audit emitter/service writing append-only `audit_logs`.
- S2-T6.2 Emit on: register, login, failed login, logout, org-switch, org create/update/suspend, member invite/update/remove, role/permission changes.
- S2-T6.3 Immutability: no update/delete path; org-scoped RLS for org-visible logs + Super Admin platform view.
- S2-T6.4 Audit query API (Org Admin → own org; Super Admin → platform-wide), filter by actor/action/entity/date.

### S2-T7 — Frontend: auth & admin surfaces *(Frontend / UI-UX)*
- S2-T7.1 Login + self-service registration pages; session handling (refresh via cookie; protected routing).
- S2-T7.2 **Real org switcher** (replaces the placeholder) → calls switch-org, re-scopes the session.
- S2-T7.3 Real user menu + sign-out; `/me`-driven nav/permission gating.
- S2-T7.4 Members admin (list/invite/update/remove) + Roles & Permissions admin.
- S2-T7.5 Organization settings (profile/GSTIN/status).
- S2-T7.6 Audit log viewer.

### S2-T8 — Security hardening & gate flips *(DevOps / Backend)*
- S2-T8.1 Rate limiting (Redis) on auth endpoints; brute-force lockout.
- S2-T8.2 **JWT secret-strength guard**: refuse to boot in staging/production with a default/weak secret (audit SR-02).
- S2-T8.3 Cookie security (httpOnly/Secure/SameSite); refresh reuse detection verified.
- S2-T8.4 Flip CI gates to **blocking** for the auth surface: coverage `--cov-fail-under=80`, dependency/vuln gating.

### S2-T9 — QA & verification *(QA)*
- S2-T9.1 Extend the RLS suite (T0) over the real tables (organizations, user_organizations, roles, audit_logs).
- S2-T9.2 RBAC allow/deny matrix tests (per role × permission × endpoint).
- S2-T9.3 Auth-flow tests: login/refresh-rotation/reuse-detection/switch-org/logout.
- S2-T9.4 Audit-emission tests (every security action logs exactly once, immutable).
- S2-T9.5 E2E happy path: register org → invite member → assign role → act → see audit entry.

---

## 4. Dependencies

| Task | Depends on |
|---|---|
| S2-T0 RLS harness | S1 (app.* functions) — **gate for all tenant work** |
| S2-T1 schema | S2-T0 (gate), S1 |
| S2-T2 auth | S2-T1 |
| S2-T3 tenancy context | S2-T1, S2-T2 |
| S2-T4 users/orgs APIs | S2-T3, S2-T5 |
| S2-T5 RBAC | S2-T1, S2-T3 |
| S2-T6 audit | S2-T1, S2-T2 |
| S2-T7 frontend | S2-T2, S2-T4, S2-T5 |
| S2-T8 security | S2-T2 |
| S2-T9 QA | all of the above |

Critical path: **S2-T0 → S2-T1 → S2-T2 → S2-T3 → (S2-T5 ∥ S2-T4) → S2-T9**.

---

## 5. Deliverables
- RLS verification suite + required CI check (parametrized over Sprint-2 tables).
- Migrations: organizations, users, user_organizations, permissions, roles, role_permissions, user_organization_roles, audit_logs — all org-scoped tables RLS-enabled in the same migration; seed roles/permissions.
- Auth service: register (A) + provision (B), login, refresh (rotating, reuse-detecting), logout, switch-org, `/me`.
- Tenancy context dependency setting `app.current_org_id` from the JWT claim.
- RBAC engine + `require_permission` guard + role/permission admin APIs.
- Audit emitter + audit query API.
- Frontend: login/register, real org switcher + user menu, members & roles admin, org settings, audit viewer.
- Security: rate limiting, secret guard, secure cookies; CI gates flipped to blocking for the surface.
- Updated docs/ADRs (any new decision recorded); updated OpenAPI.

---

## 6. Acceptance Criteria (per requirement)

**RLS / Multi-tenant isolation**
- Every org-scoped table has RLS enabled+forced **in its creating migration**; `users` is global.
- As `app_user` in org A, no query returns or affects org B rows; cross-tenant insert/update/delete rejected; missing/invalid org context returns zero tenant rows. The RLS suite covers all real tables and is green.

**JWT active-organization context**
- Active org is read **only** from the validated JWT claim and applied via `SET LOCAL app.current_org_id` inside the request transaction. Switching orgs mints a **new** JWT; no endpoint accepts an org from a client header/body.

**Authentication**
- Register (path A) creates org + user + Org Admin membership atomically; Super Admin provisioning (path B) works. Login issues a 15-min access JWT + rotating httpOnly/Secure refresh cookie; refresh rotates and **detects reuse** (revokes the family). Logout revokes.

**Database-driven RBAC**
- Authorization is permission-based and **deny-by-default**; there are **no role-name checks** in business logic. The allow/deny matrix passes for every role × permission × endpoint. Org Admins manage roles within their org; Super Admin platform-wide.

**Audit logging**
- Every security-relevant action writes exactly one append-only `audit_logs` row (actor, org, action, entity, metadata, ip/ua, timestamp). Logs are immutable (no update/delete); Org Admins see their org, Super Admin sees platform-wide.

---

## 7. Definition of Done (sprint-level)
- [ ] Code merged via PR with CODEOWNERS review; Conventional Commits; branch deleted.
- [ ] Lint + type-check + tests green; **coverage ≥ 80%** for new backend modules (gate flipped on).
- [ ] **RLS suite green** as a required check; every new tenant table added to it.
- [ ] Every org-scoped table: `organization_id` + RLS-enabled in the same migration; migration has a reviewed rollback path.
- [ ] Every protected endpoint behind `require_permission` (deny-by-default); no role-name checks.
- [ ] Every security action emits an immutable audit row (verified by tests).
- [ ] Secrets: no defaults in staging/prod (boot guard); cookies Secure/httpOnly/SameSite.
- [ ] Docs/ADRs/OpenAPI updated; frontend surfaces wired to real APIs (no placeholders for shipped features).

---

## 8. Risk Register (Sprint 2)

| # | Risk | L | I | Mitigation |
|---|---|---|---|---|
| RS2-1 | A new tenant table ships without RLS → leakage | Med | **Critical** | RLS suite is a required gate; db-architect CODEOWNER; "RLS in same migration" DoD |
| RS2-2 | Org context leaks via header/body instead of JWT | Med | Critical | Active org read only from validated claim; negative tests; code review rule |
| RS2-3 | Refresh-token theft / replay | Med | High | Rotation + reuse detection (revoke family); httpOnly/Secure/SameSite; short access TTL |
| RS2-4 | RBAC bypass / privilege escalation | Med | High | Deny-by-default permission checks everywhere; allow/deny matrix tests; no role-name checks |
| RS2-5 | Audit gaps or mutability | Med | High | Append-only table; emit-on-every-action tests; immutability (no update/delete path) |
| RS2-6 | Weak/default JWT secret in non-dev | Low | Critical | Startup secret-strength guard (SR-02) |
| RS2-7 | Self-service registration abuse | Med | Med | Rate limiting + lockout; email verification flag; Super-Admin review of suspicious orgs |
| RS2-8 | `app_superadmin` bypass misused at runtime | Low | High | Runtime always connects as `app_user`; superadmin only platform-admin; every use audited |
| RS2-9 | Scope creep (teams/notifications pulled in) | Med | Med | Hard scope line — those are Sprint 3; change-control via EM |
| RS2-10 | Capacity (heavy sprint) overrun | Med | High | S2 is a flagged split-candidate; pre-budget a second iteration; descope custom roles if needed |

---

## 9. Exit Criteria (gate to Milestone M1)

Sprint 2 is **done** only when **all** hold:
1. **RLS proven:** the cross-tenant isolation suite (over the real Sprint-2 tables) runs **green as a required CI check**; no cross-org access is possible as `app_user`; missing/invalid context returns no tenant data.
2. **Multi-org auth works end to end:** register (A) + Super-Admin provision (B); login issues a scoped JWT; **switch-org mints a new JWT**; refresh rotates with reuse detection; logout revokes.
3. **Tenancy context is enforced server-side** from the JWT claim on every tenant request (no header/body override).
4. **RBAC is database-driven and deny-by-default;** the allow/deny matrix passes; role/permission admin works for Org Admin (own org) and Super Admin (platform).
5. **Audit logging is complete and immutable;** every security action is captured; org-scoped + Super-Admin views function.
6. **Quality gates green:** coverage ≥ 80% (new modules), security/dependency gates blocking for the surface, secret guard active.
7. **Frontend secure core usable:** login/register, real org switcher, members & roles admin, audit viewer — all on real APIs.
8. **Docs/ADRs updated;** any new decision recorded; OpenAPI published.

---

**On approval**, I will render this as `Sprint2_Backlog.xlsx` (tasks/subtasks, dependencies, DoD,
acceptance, risks — matching the Sprint 1 backlog format) and place it in the repo, and S2-T0 (the RLS
harness) becomes the first ticket worked, closing audit risk AR-01.
