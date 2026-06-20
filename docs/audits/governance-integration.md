# Governance Repository Integration

**Owner:** Engineering Manager · **Action:** integrate the agent-team governance into the repository
and verify alignment with the approved architecture.

---

## 1. Governance Audit Report

### What was wrong
The governance artifacts (`CLAUDE.md` master charter + the ten `.claude/agents/` definitions) existed
but lived **outside the repository** (in the output workspace, not under version control). Audit
finding AR/§6.3 — "bring governance into the repo" — is the trigger for this task.

### What was verified
| Check | Result |
|---|---|
| `CLAUDE.md` exists and is coherent | ✅ Master charter: roadmap (11 sprints), 5 locked decisions, shared non-negotiables, pipeline |
| All 10 agent files exist | ✅ product-manager, business-analyst, solution-architect, ui-ux-designer, database-architect, backend-engineer, frontend-engineer, qa-engineer, devops-engineer, ai-engineer |
| Each agent has the standard structure | ✅ All 10 carry the same 8 sections (Role · Responsibilities · Inputs · Outputs · Rules · Quality Standards · Handoff Process · Communication Protocol) |
| `CLAUDE.md` is the single source of truth | ✅ Now at **repo root** (auto-loaded); agents reference it and must not contradict it |
| Agent responsibilities align with the approved architecture | ✅ See alignment matrix below |
| Review routing maps to agents | ✅ `CODEOWNERS` extended (QA, AI, governance) — see §2 |

### Architecture-alignment matrix
Each agent's mandate was checked against the locked decisions and the modular-monolith design:

| Agent | Carries the right guardrails? |
|---|---|
| solution-architect | ✅ Owns modular monolith, multi-tenancy via RLS, JWT org-context, ADRs |
| database-architect | ✅ RLS policy **in the same migration**, `organization_id` + UUIDv7 + audit/soft-delete/version, single-primary-team constraint (decision #3), India-first fields |
| backend-engineer | ✅ router→service→repository, RBAC permission checks (not role-name checks), notification adapters behind provider interfaces (decision #4) |
| frontend-engineer | ✅ Four surfaces, ShadCN/React Query/Zustand, design-system tokens incl. the 8-status spine |
| qa-engineer | ✅ Explicitly owns the **cross-tenant isolation suite** + coverage gate (ties to the RLS verification plan) |
| ui-ux-designer | ✅ Four surfaces, 8-status spine, accessibility |
| devops-engineer | ✅ Docker, CI/CD, environments, secrets, observability, release |
| ai-engineer | ✅ Sprint-10 services with feature-flag gating |
| product-manager / business-analyst | ✅ Scope/spec roles; inherit the shared non-negotiables from `CLAUDE.md` |

**Conclusion:** the agent definitions are consistent with the approved architecture and the locked
decisions. No contradictions found; the only change required was **placement** (into the repo) plus a
CODEOWNERS extension.

---

## 2. Missing Files Report

| File | Status | Action |
|---|---|---|
| `CLAUDE.md` (repo root) | **Added** | Copied in as the single source of truth (auto-loaded by Claude Code) |
| `.claude/agents/*.md` (×10) | **Added** | All ten placed under `.claude/agents/` |
| `.claude/README.md` | **Added** | New governance index pointing to `../CLAUDE.md` |
| `CODEOWNERS` QA/AI/governance routing | **Added** | Extended to map `tests/`, `ai-services/`, `CLAUDE.md`, `.claude/` |
| `SECURITY.md` | ❌ Missing | Recommend adding a disclosure policy (also in the Sprint-1 audit) |
| `.claude/settings.json` | ⚪ Optional | Claude Code project settings (tool permissions); add when wiring real agent execution — left out here to avoid fabricating config |
| `.claude/commands/` | ⚪ Optional | Custom slash-commands; not needed yet |
| `CHANGELOG.md` | ❌ Missing | Seed a keep-a-changelog file (audit item) |
| `CODE_OF_CONDUCT.md` | ⚪ Optional | Expected for a real team repo |
| RACI / ways-of-working in-repo | ⚪ Partial | RACI lives in the Execution Plan doc (out of repo); recommend linking or summarizing in-repo |
| Project tracker baselined to 11 sprints | ❌ Out-of-date | Tracker is on the old 24-sprint layout and lives outside the repo — re-baseline + bring in (separate task) |

---

## 3. Final Repository Structure (governance)

```
logistics-platform/
├── CLAUDE.md                      ← SINGLE SOURCE OF TRUTH (charter; auto-loaded)
├── .claude/
│   ├── README.md                  ← governance index → ../CLAUDE.md
│   └── agents/
│       ├── product-manager.md
│       ├── business-analyst.md
│       ├── solution-architect.md
│       ├── ui-ux-designer.md
│       ├── database-architect.md
│       ├── backend-engineer.md
│       ├── frontend-engineer.md
│       ├── qa-engineer.md
│       ├── devops-engineer.md
│       └── ai-engineer.md
├── .github/
│   └── CODEOWNERS                 ← code paths → owning agents (QA/AI/governance added)
├── CONTRIBUTING.md                ← contribution workflow
├── CONVENTIONS.md                 ← coding standards
├── REPOSITORY_STANDARDS.md        ← repo standards
└── docs/
    ├── adr/                       ← decision records (locked decisions)
    ├── guides/sprint-process.md   ← cadence, roles, DoD
    └── onboarding/definition-of-done.md
```

### Governance source-of-truth chain
```
CLAUDE.md  (charter: scope · locked decisions · roadmap · non-negotiables)
   │  referenced by ▼
.claude/agents/*.md   (per-role mandates — never contradict the charter)
   │  enforced via ▼
.github/CODEOWNERS    (review routing) + docs/adr (decision changes need an ADR + EM approval)
```

### Rules of engagement (recorded)
1. `CLAUDE.md` is authoritative. Agent files reference it and may not override it.
2. Changing a locked decision requires an **ADR + EM approval**, then the charter and affected agents
   are updated together.
3. Agent files stay declarative/reference-based — no duplication of charter content (prevents drift).
4. New code-owning areas get a `CODEOWNERS` entry pointing at the owning agent/role.

---

### Result
Governance is now **in the repository and version-controlled**, `CLAUDE.md` is the single source of
truth at the root, all ten agents are present and architecture-aligned, and review routing covers
every code-owning role. Remaining items (`SECURITY.md`, `CHANGELOG.md`, tracker re-baseline) are
listed above and tracked in the Sprint-1 audit.
