# `.claude/` — Team Governance

This folder holds the multi-agent engineering team's operating definitions for the Logistics
Management Platform.

## Single source of truth
[`../CLAUDE.md`](../CLAUDE.md) is the **master charter** — product scope, the locked architecture
decisions, the 11-sprint roadmap, the shared non-negotiables, and the delivery pipeline. Agent files
**reference** it; they never restate or override it. If an agent file and `CLAUDE.md` ever disagree,
`CLAUDE.md` wins and the discrepancy is a bug to fix.

## Agents (`agents/`)
Ten specialist agents, each defined with the same eight sections (Role · Responsibilities · Inputs ·
Outputs · Rules · Quality Standards · Handoff Process · Communication Protocol):

| Agent | Owns |
|---|---|
| `product-manager` | Scope, prioritization, user stories, acceptance criteria |
| `business-analyst` | Specifications, process flows, data requirements, edge cases |
| `solution-architect` | System architecture, module boundaries, NFRs, ADRs |
| `ui-ux-designer` | Four surfaces, design system, the 8-status spine, accessibility |
| `database-architect` | Schema, RLS policies, migrations, indexing, integrity |
| `backend-engineer` | FastAPI modules (router→service→repository), APIs, RBAC, adapters |
| `frontend-engineer` | Next.js surfaces against the approved design system |
| `qa-engineer` | Test strategy, the cross-tenant isolation suite, coverage gate, UAT |
| `devops-engineer` | Docker, CI/CD, environments, secrets, observability, release |
| `ai-engineer` | Sprint-10 intelligence (ETA, routing, forecasting, anomaly) |

## How this maps to the repo
- **Review routing:** [`../.github/CODEOWNERS`](../.github/CODEOWNERS) maps code paths to the owning
  agent/role (replace `@placeholders` with real GitHub teams when the org is set up).
- **Process:** [`../docs/guides/sprint-process.md`](../docs/guides/sprint-process.md) and the
  [Definition of Done](../docs/onboarding/definition-of-done.md).
- **Decisions:** [`../docs/adr/`](../docs/adr/) — changing a locked decision needs an ADR + EM approval.

## Rules for changing governance
1. Update `CLAUDE.md` first for any scope/decision/roadmap change (with an ADR if it touches a locked
   decision).
2. Update the affected agent file(s) to match — never let them drift from the charter.
3. Keep agent files declarative and reference-based; do not duplicate charter content.
