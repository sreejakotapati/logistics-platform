# Architecture Decision Records (ADRs)

An ADR captures a significant decision, its context, and its consequences — so future contributors
know **why** the system is the way it is.

## When to write one
- Choosing or changing a technology, pattern, or boundary that's hard to reverse.
- Anything that touches a **locked decision**
  ([ADR-0001](0001-foundation-architecture-decisions.md)). Reopening one needs a new ADR that
  supersedes it.
- A "we considered X and chose Y" that reviewers keep asking about.

You do **not** need an ADR for routine implementation choices.

## How to write one
1. Copy [`0000-adr-template.md`](0000-adr-template.md) to `NNNN-short-title.md` (next number).
2. Fill in **Context → Decision → Consequences** (and alternatives considered).
3. Set status: `Proposed` → `Accepted` (or `Rejected`/`Superseded by NNNN`).
4. Open it in a PR like any change; reviewers per CODEOWNERS (`docs/adr/` → solution architect).
5. Link it from affected docs and from the [Architecture Navigation Guide](../architecture/README.md).

## Index
| ADR | Title | Status |
|---|---|---|
| [0001](0001-foundation-architecture-decisions.md) | Foundation architecture decisions (tenancy, RLS, active-org JWT, feature flags, notification abstraction, modular monolith, …) | Accepted |

> Keep ADRs immutable once Accepted. To change a decision, add a new ADR that supersedes the old one.
