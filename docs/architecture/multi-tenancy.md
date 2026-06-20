# Multi-Tenant & Row-Level Security Strategy

## Strategy: shared schema + organization_id + RLS
A single schema holds all tenants' data; every business table carries `organization_id`. PostgreSQL
**Row-Level Security** makes the database itself refuse rows outside the active organization — so a
missing `WHERE organization_id = ...` in application code cannot leak data (defense in depth).

## The standard policy (applied by app.enable_org_rls)
For each org-scoped table:
```sql
ALTER TABLE <t> ENABLE ROW LEVEL SECURITY;
ALTER TABLE <t> FORCE ROW LEVEL SECURITY;
CREATE POLICY org_isolation ON <t>
  USING (organization_id = app.current_org_id())
  WITH CHECK (organization_id = app.current_org_id());
```
`USING` filters reads; `WITH CHECK` prevents writing rows into another org. `FORCE` subjects even the
table owner to the policy.

## JWT active-organization context
A user may belong to multiple organizations; they operate in **one active organization** at a time.
1. The access token (JWT) carries the active `organization_id` claim (locked decision #1).
2. On every request, inside the transaction, the backend runs:
   `SET LOCAL app.current_org_id = '<uuid-from-jwt>';`
3. `app.current_org_id()` reads that GUC; RLS policies use it to scope all queries.
4. Switching organizations issues a **new JWT** with a different claim — the context changes safely;
   org context is never taken from a client header.

`SET LOCAL` is transaction-scoped, so the context cannot leak across pooled connections.

## Identity vs membership
`users` is global (not RLS-scoped). Tenant scoping for people flows through `user_organizations`
(org-scoped, RLS-protected). These tables are created in Sprint 2; this document defines the rule the
foundation enforces.

## Super-admin / cross-tenant
Platform-level operations that legitimately span tenants use the `app_superadmin` role (BYPASSRLS) on
a dedicated connection, never the runtime role. Such access is audited.

## Why the runtime role matters
`app_user` is `NOSUPERUSER NOBYPASSRLS`. A superuser or BYPASSRLS role would ignore every policy —
this is the single most important configuration in the tenancy model.
