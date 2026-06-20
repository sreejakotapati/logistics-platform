# Definition of Done (reference)

## Per-change (PR) DoD
- CI green (lint, type-check, test, build); ≥1 review; conventional-commit title.
- Tests added/updated; coverage ≥80%.
- Org-scoped + RBAC-gated where applicable; audit events on mutations.
- No secrets committed; `.env.example` updated if new vars added.

## Sprint DoD
- All sprint modules delivered; end-to-end journey demoed on staging.
- Cross-tenant isolation suite green; no open critical/high defects.

## Release DoD
- SLAs met under load; pen-test passed (no open criticals).
- Observability + rollback rehearsed; UAT signed by pilot org.
