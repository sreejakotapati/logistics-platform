# RLS Verification Plan

**Owner:** Database Architect · **Status:** Proposed (gate for Sprint 2)
**Objective:** Prove PostgreSQL Row-Level Security tenant isolation works correctly **before** any
tenant (business) table is built in Sprint 2.

> **Scope guard.** This plan creates **no business tables and no business modules** — no Orders,
> Shipments, Customers, Warehouses, Drivers, or Vehicles. It exercises RLS against a single
> **ephemeral probe table** in a throwaway `rls_verify` schema that is created in test setup and
> dropped in teardown. Nothing is added to Alembic migrations.

## What this proves
| | Requirement |
|---|---|
| A | Organization A cannot access Organization B records |
| B | Organization B cannot access Organization A records |
| C | `app_user` cannot bypass RLS |
| D | Missing `app.current_org_id` returns no tenant data |
| E | Invalid `organization_id` returns no tenant data |
| F | Cross-tenant **inserts** are rejected |
| G | Cross-tenant **updates** are rejected |
| H | Cross-tenant **deletes** are rejected |
| I | Super Admin access works **only** through the approved bypass role |
| J | The runtime application role remains constrained by RLS |

## Primitives under test (from migration `0001_foundation`)
- `app.current_org_id()` → `SELECT NULLIF(current_setting('app.current_org_id', true), '')::uuid;`
  (STABLE; returns **NULL** when the GUC is unset or empty).
- `app.enable_org_rls(target regclass)` → `ENABLE` **and** `FORCE ROW LEVEL SECURITY`, then
  `CREATE POLICY org_isolation ... USING (organization_id = app.current_org_id())
  WITH CHECK (organization_id = app.current_org_id())`.
- `app.uuid_generate_v7()` → UUIDv7 default for primary keys.

---

## 1. RLS Test Architecture

Six layers, executed in order; each layer gates the next.

| Layer | Goal | Maps to |
|---|---|---|
| L0 Structural | Functions/policy/flags exist and are correct | prerequisite |
| L1 Positive isolation | Each org sees **only** its own rows | A, B, J |
| L2 Cross-tenant DML | Cross-tenant insert/update/delete rejected or no-op | F, G, H |
| L3 Context safety | Missing / empty / invalid context fails **closed** | D, E |
| L4 Bypass resistance | `app_user` cannot disable, escape, or escalate around RLS | C, J |
| L5 Approved bypass | `app_superadmin` bypasses; owner stays constrained by FORCE | I, J |

**Role-as-subject matrix** (the variable that decides RLS behavior):

| Role | superuser | BYPASSRLS | Owner of probe | Subject to RLS? | Used at runtime? |
|---|---|---|---|---|---|
| `logistics_owner` (POSTGRES_USER) | yes | (n/a) | no | no (bootstrap only) | no |
| `logistics_migrator` | no | no | **yes** (creates probe) | **yes** (FORCE) | no (migrations) |
| `app_user` | no | no | no | **yes** | **yes** ← the one that matters |
| `app_superadmin` | no | **yes** | no | no (approved bypass) | only for platform admin |

**Principles.** Every assertion runs in an explicit transaction with `SET LOCAL app.current_org_id`
(mirrors how the request layer sets it per request from the JWT claim — decision #3). Cases roll back
between runs for isolation. Leakage is made detectable by **asymmetric seed counts** (A≠B).

---

## 2. Test Database Design

- **Instance:** the same PostgreSQL 16 used by CI (the `logistics_test` database on the Postgres
  service container). The `pgcrypto` extension and the `app` schema/functions come from the existing
  CI step + migration `0001_foundation` (already applied in `backend-ci.yml`).
- **Ephemeral schema:** `rls_verify` — holds only the probe table; created in setup, `DROP SCHEMA
  rls_verify CASCADE` in teardown. The `public`/business schema is never touched.
- **Roles:** `app_user`, `logistics_migrator`, `app_superadmin` must exist with the correct
  attributes. In CI the role bootstrap scripts aren't mounted, so the harness provisions them
  idempotently (see §6). No role gets new privileges on `public`.

```sql
-- Role provisioning (idempotent; run as the superuser/owner connection). Test-env only.
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='app_user') THEN
    CREATE ROLE app_user LOGIN PASSWORD 'test_app' NOSUPERUSER NOBYPASSRLS NOCREATEROLE NOCREATEDB;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='logistics_migrator') THEN
    CREATE ROLE logistics_migrator LOGIN PASSWORD 'test_mig' NOSUPERUSER NOBYPASSRLS;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='app_superadmin') THEN
    CREATE ROLE app_superadmin LOGIN PASSWORD 'test_sa' NOSUPERUSER BYPASSRLS;
  END IF;
END $$;
```

---

## 3. Test Tables Required

Exactly **one** ephemeral probe table. It is **not** a business entity and is **not** migrated.

```sql
-- as logistics_migrator (owner of the probe)
CREATE SCHEMA IF NOT EXISTS rls_verify;

CREATE TABLE rls_verify.tenant_probe (
    id              uuid PRIMARY KEY DEFAULT app.uuid_generate_v7(),
    organization_id uuid NOT NULL,
    payload         text NOT NULL,
    created_at      timestamptz NOT NULL DEFAULT now()
);

GRANT USAGE ON SCHEMA rls_verify TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON rls_verify.tenant_probe TO app_user;
-- NOTE: app_user gets DML only — no ownership, no policy/DDL rights.
```

> Optional extension (not required for sign-off): a second probe `tenant_probe_child` with an FK to
> validate isolation across a parent/child relationship. Out of scope for the initial gate.

---

## 4. Test Data Strategy

Deterministic, asymmetric, PII-free. Seed **before** enabling RLS so seeding isn't itself blocked by
the policy (the alternative is to seed as `app_superadmin`).

```sql
-- Fixed org identifiers
--   ORG_A = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
--   ORG_B = 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb'
--   ORG_C = 'cccccccc-cccc-4ccc-8ccc-cccccccccccc'  (valid UUID, no rows — "nonexistent org")

-- Seed BEFORE app.enable_org_rls(): A×3, B×2 (asymmetric -> any leak changes a count)
INSERT INTO rls_verify.tenant_probe (organization_id, payload) VALUES
  ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa','A-1'),
  ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa','A-2'),
  ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa','A-3'),
  ('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb','B-1'),
  ('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb','B-2');

-- Capture known ids for targeted cross-tenant tests
--   A_ROW_ID = (any A row), B_ROW_ID = (any B row)

-- Now lock it down
SELECT app.enable_org_rls('rls_verify.tenant_probe');
```

Baseline truth: total rows = 5 (A=3, B=2). The harness records `A_ROW_ID` and `B_ROW_ID`.

---

## 5. Test Cases

Conventions: **subject role** is noted per case; `SET LOCAL` requires an open transaction; "rows" =
rows returned/affected. All SQL is illustrative of what the harness executes.

### L0 — Structural (prerequisite)
| ID | As | SQL (abbrev.) | Expected | Pass/Fail |
|---|---|---|---|---|
| S-1 | admin | `SELECT relrowsecurity, relforcerowsecurity FROM pg_class WHERE oid='rls_verify.tenant_probe'::regclass;` | `t, t` | Pass iff both true |
| S-2 | admin | `SELECT polname, polcmd, pg_get_expr(polqual,polrelid), pg_get_expr(polwithcheck,polrelid) FROM pg_policy WHERE polrelid='rls_verify.tenant_probe'::regclass;` | `org_isolation`, cmd `*` (ALL), both expressions reference `app.current_org_id()` | Pass iff policy present with USING **and** WITH CHECK |

### L1 — Positive isolation (A, B, J)
```sql
-- TC-01  as app_user
BEGIN; SET LOCAL app.current_org_id = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa';
SELECT count(*) FROM rls_verify.tenant_probe;            -- expect 3
SELECT count(*) FROM rls_verify.tenant_probe
  WHERE id = :B_ROW_ID;                                  -- TC-02 expect 0
COMMIT;
```
| ID | As | Action | Expected | Pass/Fail | Req |
|---|---|---|---|---|---|
| TC-01 | app_user | context=A, `count(*)` | **3** | exactly 3 (not 5) | A |
| TC-02 | app_user | context=A, select B_ROW_ID | **0** | 0 rows | A |
| TC-03 | app_user | context=B, `count(*)` | **2** | exactly 2 | B |
| TC-04 | app_user | context=B, select A_ROW_ID | **0** | 0 rows | B |

### L2 — Cross-tenant DML (F, G, H)
```sql
-- TC-05 cross-insert  as app_user, context=A
BEGIN; SET LOCAL app.current_org_id = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa';
INSERT INTO rls_verify.tenant_probe (organization_id, payload)
VALUES ('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb','A-injects-B');  -- expect ERROR
ROLLBACK;
```
| ID | As | Action | Expected | Pass/Fail | Req |
|---|---|---|---|---|---|
| TC-05 | app_user | ctx=A, INSERT org_id=B | `ERROR: new row violates row-level security policy` | rejected; B count stays 2 | F |
| TC-06 | app_user | ctx=A, INSERT org_id=A (control) | 1 row inserted | succeeds; A=4 | F |
| TC-07 | app_user | ctx=A, `UPDATE … WHERE id=B_ROW_ID SET payload='x'` | **0 rows** | 0 affected; B row unchanged | G |
| TC-08 | app_user | ctx=A, `UPDATE tenant_probe SET payload='x'` (no WHERE) | affects only visible A rows | A rows only; B untouched | G |
| TC-09 | app_user | ctx=A, `UPDATE own row SET organization_id=B` (re-tenant) | `ERROR: … row-level security policy` | rejected (WITH CHECK) | G |
| TC-10 | app_user | ctx=A, `DELETE … WHERE id=B_ROW_ID` | **0 rows** | 0 affected; B intact | H |
| TC-11 | app_user | ctx=A, `DELETE FROM tenant_probe` (no WHERE) | deletes only A's visible rows | B rows remain (verify via app_superadmin) | H |

> TC-08/TC-11 are the strongest leakage probes: a blind `UPDATE`/`DELETE` must **never** touch the
> other tenant's rows. Cross-check the survivor counts with the bypass role (§L5).

### L3 — Context safety (D, E)
```sql
-- TC-12 missing context  as app_user (no SET LOCAL)
BEGIN;
SELECT app.current_org_id();                 -- expect NULL
SELECT count(*) FROM rls_verify.tenant_probe; -- expect 0
COMMIT;
```
| ID | As | Action | Expected | Pass/Fail | Req |
|---|---|---|---|---|---|
| TC-12 | app_user | no context, `count(*)` | **0** (and `current_org_id()` IS NULL) | 0 rows (fail-closed) | D |
| TC-13 | app_user | no context, INSERT any org | `ERROR: … row-level security policy` | rejected | D, F |
| TC-14 | app_user | `SET LOCAL app.current_org_id=''`, `count(*)` | **0** | 0 rows | D, E |
| TC-15 | app_user | `SET LOCAL app.current_org_id='not-a-uuid'`, SELECT | `ERROR: invalid input syntax for type uuid` | query errors; **no rows** returned | E |
| TC-16 | app_user | context = ORG_C (valid uuid, no data), `count(*)` | **0** | 0 rows | E |

### L4 — Bypass resistance (C, J)
| ID | As | Action | Expected | Pass/Fail | Req |
|---|---|---|---|---|---|
| TC-17 | app_user | `SET LOCAL row_security = off; SELECT …` | `ERROR: query would be affected by row-level security policy` | no bypass; no cross-tenant rows | C |
| TC-18 | app_user | `ALTER TABLE rls_verify.tenant_probe DISABLE ROW LEVEL SECURITY` | `ERROR: must be owner of table tenant_probe` | denied | C |
| TC-19 | app_user | `ALTER TABLE … NO FORCE ROW LEVEL SECURITY` | permission denied | denied | C |
| TC-20 | app_user | `DROP POLICY org_isolation ON …` | permission denied | denied | C |
| TC-21 | app_user | `SET ROLE app_superadmin` (and `SET ROLE logistics_migrator`) | `ERROR: permission denied to set role` | denied | C, I |
| TC-22 | app_user | `ALTER ROLE app_user BYPASSRLS` | permission denied (needs superuser) | denied | C, J |
| TC-23 | admin | `SELECT rolsuper, rolbypassrls, rolcanlogin FROM pg_roles WHERE rolname='app_user';` | `f, f, t` | exact booleans | J |

### L5 — Approved bypass & FORCE (I, J)
| ID | As | Action | Expected | Pass/Fail | Req |
|---|---|---|---|---|---|
| TC-24 | app_superadmin | `count(*)` with **no** context | **5** (all orgs) | sees all rows (approved bypass works) | I |
| TC-25 | logistics_migrator (owner) | `count(*)` with no context | **0**; with ctx=A → **3** | owner is constrained by FORCE (not an implicit bypass) | I, J |

> TC-24 is a **positive control**: it proves the mechanism distinguishes roles and the approved
> platform-admin path functions. The plan also asserts (operationally) that `app_superadmin` is
> **never** the request-time connection — the application always connects as `app_user`.

---

## 6. Integration Test Strategy

- **Location:** `backend/tests/integration/test_rls.py`, marked `@pytest.mark.integration`. Pure-DB
  behavior, exercised through three connections (psycopg) with distinct roles:
  `conn_admin` (superuser, provisioning/teardown), `conn_app` (`app_user`, assertions),
  `conn_super` (`app_superadmin`, cross-checks + TC-24).
- **Fixtures (pytest):**
  1. `rls_roles` (session) — runs the idempotent role provisioning SQL (§2) via `conn_admin`.
  2. `rls_schema` (function or module) — creates `rls_verify` + probe, grants `app_user`, seeds A/B
     **before** `enable_org_rls`, yields ids; teardown `DROP SCHEMA rls_verify CASCADE`.
  3. Each test opens its own transaction, sets `SET LOCAL app.current_org_id`, asserts, rolls back.
- **CI wiring:** runs in the existing Postgres+Redis job in `backend-ci.yml` after `alembic upgrade
  head` (which provides `app.*`). Command: `pytest -m integration backend/tests/integration/test_rls.py`.
  The probe schema and test roles are created at runtime, so the foundation migration is unchanged and
  no business table is introduced.
- **Connection strings:** derived from env (`RLS_APP_DSN`, `RLS_SUPER_DSN`, `RLS_ADMIN_DSN`); CI sets
  the test passwords used in §2.
- **Determinism:** asymmetric seed (A=3, B=2) and captured ids make every leak observable as a count
  or a specific-row hit. Each case is transaction-isolated.
- **Alternative (optional):** a pgTAP `.sql` suite expressing the same cases for DB-native CI. Either
  satisfies the gate; the pytest harness is preferred to fit the existing toolchain.

---

## 7. Security Validation Strategy

The negative space is the point — we prove what **cannot** happen.

1. **Role attributes are the first line.** TC-23 asserts `app_user` is `NOSUPERUSER` +
   `NOBYPASSRLS`; without this, RLS is silently moot. This is checked on every run, not assumed.
2. **No escape hatches for `app_user`:** cannot turn off `row_security` to bypass (TC-17), cannot
   `DISABLE`/`NO FORCE`/`DROP POLICY` (not owner — TC-18/19/20), cannot `SET ROLE` to a privileged
   role (TC-21), cannot self-grant `BYPASSRLS` (TC-22).
3. **FORCE ROW LEVEL SECURITY** is verified (S-1) so even the table **owner** is bound (TC-25) —
   ownership is not an implicit bypass.
4. **Fail-closed semantics:** missing, empty, and malformed context all yield zero rows or a hard
   error (TC-12/14/15) — never a "see everything" fallback. Cross-tenant writes are rejected by
   `WITH CHECK`, including attempts to re-tenant a row (TC-09).
5. **Context provenance:** RLS depends on `app.current_org_id` being set from a **server-side signed
   JWT claim**, never a client-supplied header (decision #3). The harness sets it via `SET LOCAL`
   only; the application layer must do the same inside the request transaction (verified separately
   when the auth middleware lands in Sprint 2).
6. **Approved bypass is explicit and isolated:** only `app_superadmin` (BYPASSRLS) sees across orgs
   (TC-24), and the runtime app never connects as it.

---

## 8. Acceptance Criteria

The RLS gate is **passed** for Sprint 2 only when **all** of the following hold:

- [ ] **L0** structural checks pass: probe has `relrowsecurity` **and** `relforcerowsecurity` true; the
      `org_isolation` policy exists with both `USING` and `WITH CHECK` referencing `app.current_org_id()`.
- [ ] **A & B:** `app_user` in org-A context returns exactly A's rows and zero B rows, and symmetrically
      for B (TC-01..04). No count ever reveals the other tenant.
- [ ] **F:** every cross-tenant INSERT (including re-tenant via UPDATE) is rejected; same-org INSERT
      succeeds (TC-05/06/09).
- [ ] **G:** targeted and blind cross-tenant UPDATEs affect **zero** other-tenant rows (TC-07/08).
- [ ] **H:** targeted and blind cross-tenant DELETEs remove **zero** other-tenant rows; a blind
      `DELETE FROM` in org-A context leaves all B rows intact (TC-10/11).
- [ ] **D:** missing context → `current_org_id()` is NULL and SELECT returns 0 rows; INSERT rejected
      (TC-12/13).
- [ ] **E:** empty, malformed, and valid-but-unknown context all return no tenant data (errors are
      acceptable for malformed; rows must be 0) (TC-14/15/16).
- [ ] **C:** all `app_user` bypass attempts are denied (TC-17..22).
- [ ] **J:** `app_user` is `NOSUPERUSER`/`NOBYPASSRLS` (TC-23) and the owner is constrained by FORCE
      (TC-25).
- [ ] **I:** `app_superadmin` (and only it, among non-superusers) bypasses and returns all rows
      (TC-24); the runtime app connects exclusively as `app_user`.
- [ ] The suite runs **green in CI** as a **required check**, and `rls_verify` is fully dropped after
      the run (no residue, no business table created).

**Gate rule:** no Sprint-2 migration that adds an `organization_id` table may merge until this suite
is green and wired as a required status check. Every new tenant table must call
`app.enable_org_rls('<table>')` in its migration and be added to a parametrized run of these cases.

**Definition of failure:** any cross-tenant row returned or affected, any successful bypass by
`app_user`, any "missing/invalid context returns rows" result, or any structural check failing →
**hard fail**, Sprint 2 tenant work is blocked until remediated.

---

### Appendix — Test Execution Sequence
1. Provision test roles (idempotent) — `conn_admin`.
2. `CREATE SCHEMA rls_verify` + probe table — `conn_migrator`.
3. Grant `app_user` USAGE + DML — `conn_migrator`.
4. Seed A×3, B×2 (RLS not yet enabled); capture `A_ROW_ID`, `B_ROW_ID`.
5. `SELECT app.enable_org_rls('rls_verify.tenant_probe')`.
6. L0 structural assertions (S-1, S-2).
7. L1 positive isolation (TC-01..04).
8. L2 cross-tenant DML (TC-05..11) with survivor cross-checks via `conn_super`.
9. L3 context safety (TC-12..16).
10. L4 bypass resistance + role attributes (TC-17..23).
11. L5 approved bypass + owner-under-FORCE (TC-24..25).
12. Teardown: `DROP SCHEMA rls_verify CASCADE` (and optionally drop test roles).
