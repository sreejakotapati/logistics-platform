# Sprint 2 Execution Plan — Secure Core

**Owner:** Engineering Manager · Source backlog: [`sprint-2-backlog.md`](sprint-2-backlog.md) ·
Milestone: **M1**. Work proceeds **one task at a time**, each gated by approval. Agents map to
`.claude/agents/`.

## Order of execution

| # | Task | Primary agent(s) | Depends on | Deliverables | Expected outputs |
|---|---|---|---|---|---|
| 1 | **S2-T0 RLS Verification Harness** *(gate)* | qa-engineer + database-architect | S1 | `backend/tests/integration/` suite; CI required check | All isolation cases green; required status check; ephemeral probe (no business tables) |
| 2 | S2-T1 Secure-core schema & migrations | database-architect | S2-T0 | Alembic migration(s) for orgs/users/memberships/RBAC/audit; RLS in same migration; seed | New tenant tables RLS-enabled; `users` global; system roles/permissions seeded; T0 extended to these tables |
| 3 | S2-T2 Authentication service | backend-engineer | S2-T1 | register(A)/provision(B), login, refresh(rotating), logout, switch-org, `/me` | JWT (15m) + rotating refresh cookie; new-JWT-on-switch; reuse detection |
| 4 | S2-T3 Tenancy context wiring | backend-engineer | S2-T1, S2-T2 | request session sets `app.current_org_id` from JWT claim; tenant-route guard | Every tenant request RLS-scoped server-side; no header/body override |
| 5 | S2-T5 RBAC engine | backend-engineer | S2-T1, S2-T3 | permission catalog, roles, `require_permission` guard, role/permission admin APIs | Deny-by-default authorization; no role-name checks; allow/deny matrix |
| 6 | S2-T4 Users & Organizations APIs | backend-engineer | S2-T3, S2-T5 | org profile/provision/suspend; member invite/list/update/remove; multi-org | CRUD inside tenancy + RBAC, audit-emitting |
| 7 | S2-T6 Audit logging | backend-engineer | S2-T1, S2-T2 | append-only audit emitter + query API | Immutable audit on every security action; org + platform views |
| 8 | S2-T8 Security hardening & gate flips | devops-engineer + backend-engineer | S2-T2 | rate limiting, secret guard, secure cookies; CI gates blocking | Brute-force protection; boot refuses weak secret; coverage/security gates on |
| 9 | S2-T7 Frontend auth & admin surfaces | frontend-engineer + ui-ux-designer | S2-T2, S2-T4, S2-T5 | login/register, real org switcher, members & roles admin, audit viewer, org settings | Secure core usable on real APIs; placeholders replaced |
| 10 | S2-T9 QA & verification | qa-engineer | all | extended RLS suite, RBAC matrix, auth-flow, audit, e2e | Coverage ≥80; M1 exit criteria met |

**Critical path:** S2-T0 → S2-T1 → S2-T2 → S2-T3 → (S2-T5 ∥ S2-T4) → S2-T9.
**Parallelizable once their deps land (capacity permitting):** S2-T6 with T4/T5; S2-T8 after T2; S2-T7 after T2/T4/T5.

## Working rules (per the directive)
- One task at a time; **no future-task code** is written ahead of its turn.
- Each task: build only its scope → validate → show files + folder structure + explanation → **wait
  for approval** before the next task.
- No tenant (business) table merges until S2-T0 is green (audit gate AR-01).
- Every org-scoped table calls `app.enable_org_rls()` in the same migration and is added to the T0 run.
