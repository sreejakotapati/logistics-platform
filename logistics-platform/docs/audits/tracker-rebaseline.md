# Project Tracker Re-baseline — 24-sprint → 11-sprint

**Owners:** Product Manager + Engineering Manager · **Status:** Proposed (awaiting approval to rebuild the `.xlsx`)
**Trigger:** Sprint-1 audit **TD-08** — the tracker still follows the obsolete 24-sprint plan.

> The current `Logistics_Platform_Project_Tracker.xlsx` encodes **24 two-week sprints across 48 weeks**
> with a phase taxonomy **P0–P9** and milestones **M0–M9**. The approved charter (`CLAUDE.md`) defines
> **11 themed sprints**. This document re-baselines the tracker onto the 11-sprint roadmap and is the
> spec for regenerating the workbook on approval.

---

## 1. Sprint Mapping (Old → New)

The old plan splits each theme across 2–3 fine-grained sprints; the new plan groups them into 11
themed sprints. Nothing in scope is dropped — only regrouped.

| Old | Old focus | → New | New theme |
|---|---|---|---|
| S1 | Repos, Docker, CI, FastAPI core, Alembic | **S1** | Foundations |
| S2 | Design tokens, component lib, app shell, staging deploy | **S1** | Foundations |
| S3 | Migrations + RLS + multi-org auth + tenancy | **S2** | Secure core |
| S4 | RBAC + org structure + members | **S2** (RBAC) + **S3** (depts/teams) | Secure core / Platform services |
| S5 | Notifications + feature flags + audit + admin UI | **S2** (audit) + **S3** (notif/flags) | Secure core / Platform services |
| S6 | Customers + vendors | **S4** | Master data |
| S7 | Warehouses + addresses + CSV import | **S4** | Master data |
| S8 | Orders + order_items + lifecycle FSM | **S5** | Booking spine |
| S9 | Shipments + status model + split | **S5** | Booking spine |
| S10 | AWB number + label + status-timeline UI | **S5** | Booking spine |
| S11 | Vehicles + drivers + maintenance | **S6** | Fleet |
| S12 | Trips + assignment + dispatch UI | **S6** | Fleet |
| S13 | WebSocket infra + location ingestion + Pub/Sub | **S7** | Realtime tracking |
| S14 | Tracking UI (map) + customer track + notif triggers | **S7** | Realtime tracking |
| S15 | Rate cards + invoice model + generation | **S8** | Billing & compliance |
| S16 | GST computation + e-way bill integration | **S8** | Billing & compliance |
| S17 | Payments + reconciliation + finance UI + portal | **S8** | Billing & compliance |
| S18 | Aggregation layer + role dashboards | **S9** | Analytics |
| S19 | Report builder + exports + KPI polish | **S9** | Analytics |
| S20 | Data pipelines + ETA model | **S10** | AI services |
| S21 | Route optimization + dispatch integration | **S10** | AI services |
| S22 | Demand forecast + anomaly + monitoring | **S10** | AI services |
| S23 | Security + performance + regression + observability | **S11** | Hardening & release |
| S24 | UAT + fixes + production deploy + go-live + hypercare | **S11** | Hardening & release |

**Consolidation ratio:** 24 → 11. Three new sprints absorb 3 old sprints each (S5, S8, S10); the rest
absorb ~2. This is the root of the capacity question in §5.

---

## 2. Milestone Mapping

Milestones move from phase-anchored (P0–P9) to sprint-anchored (one exit state per sprint). The old
plan had no explicit "platform services" milestone (it lived inside P1); the new plan adds **M2**.

| Old M | Exit state | → New M | New sprint exit |
|---|---|---|---|
| M0 | Paved road: CI green, staging live, shell rendering | **M0** | S1 — Foundations ✅ *(complete)* |
| M1 | Secure foundation: auth + RLS proven + RBAC + audit | **M1** | S2 — Secure core |
| *(new)* | Platform services: depts/teams + notifications + flags | **M2** | S3 — Platform services |
| M2 | Master data live | **M3** | S4 — Master data |
| M3 | Booking spine: order → shipment → AWB | **M4** | S5 — Booking spine |
| M4 | Dispatchable fleet | **M5** | S6 — Fleet |
| M5 | Live tracking | **M6** | S7 — Realtime tracking |
| M6 | Billing & compliance: GST + e-way + payment | **M7** | S8 — Billing & compliance |
| M7 | Visibility: dashboards + reports on real data | **M8** | S9 — Analytics |
| M8 | Intelligence: ETA + routing behind flags | **M9** | S10 — AI services |
| M9 | Production release: hardened, UAT-signed, go-live | **M10** | S11 — Hardening & release |

Result: **11 milestones (M0–M10)**, one per sprint.

---

## 3. Dependency Mapping (sprint-level, 11-sprint roadmap)

| Sprint | Depends on | Why |
|---|---|---|
| S1 Foundations | — | Start |
| S2 Secure core | S1 | Needs DB/RLS foundation + backend scaffold |
| S3 Platform services | S2 | Depts/teams need orgs+RBAC; notifications/flags need org context |
| S4 Master data | S2 | Org-scoped entities need tenancy + RBAC (parallelizable with S3) |
| S5 Booking spine | S4 | Orders reference customers; shipments reference warehouses |
| S6 Fleet | S5 | Trips/assignment relate to shipments to dispatch |
| S7 Realtime tracking | S6 (+S5, Redis from S1, notif from S3) | Tracks drivers/vehicles/trips; needs Pub/Sub + triggers |
| S8 Billing & compliance | S5 (+S4) | Invoices/GST/e-way derive from shipments + customers |
| S9 Analytics | S5–S8 | Aggregates real operational + financial data |
| S10 AI services | S7 + S5–S8 | ETA needs GPS/tracking; models need historical data |
| S11 Hardening & release | S1–S10 | Hardens and ships the whole system |

**Parallelization slack:** S3 can overlap S4; S8/S9 can overlap S6/S7 **if capacity allows**. With a
single-threaded team, everything is serial and slack disappears (see §5).

---

## 4. Updated Timeline

S1 is **complete**, so the calendar runs from S2. Two-week themed cadence; three sprints carry a
**split risk** (they each absorbed 3 old sprints) and may need a second iteration under a small team.

| Sprint | Theme | Weeks (no-split baseline) | Split risk → buffered |
|---|---|---|---|
| S1 | Foundations | ✅ complete | — |
| S2 | Secure core | Wk 1–2 | **+2** (auth+RLS+RBAC+audit is dense) → Wk 1–4 |
| S3 | Platform services | Wk 3–4 | — |
| S4 | Master data | Wk 5–6 | — |
| S5 | Booking spine | Wk 7–8 | possible +2 (orders+shipments+AWB) |
| S6 | Fleet | Wk 9–10 | — |
| S7 | Realtime tracking | Wk 11–12 | — |
| S8 | Billing & compliance | Wk 13–14 | **+2** (rate cards+GST+e-way+payments) → Wk 13–16 |
| S9 | Analytics | Wk 15–16 | — |
| S10 | AI services | Wk 17–18 | **+2** (ETA+routing+forecast+anomaly) → Wk 17–20 |
| S11 | Hardening & release | Wk 19–20 | — |

- **No-split floor:** ~**22 weeks** from S2 (~5.5 months total) — matches the charter's "~11 two-week sprints."
- **With the three split sprints buffered:** ~**28 weeks** (~6.5 months). This is the realistic planning number under a full squad.
- **Absolute dates are intentionally omitted** — they require a confirmed start date **and** team size (§5).

---

## 5. Capacity Assumptions

**The re-baseline is not free calendar time.** Collapsing 24 two-week sprints (48 wk) into 11 themed
two-week sprints (22 wk) for the **same scope** roughly **doubles per-sprint throughput**. That is only
achievable with more parallel capacity than the old plan assumed.

| Assumption | Implication |
|---|---|
| The 22-week figure presumes a **full squad (~6–7 FTE)** working the themes in parallel | Matches the EM execution plan's staffing baseline |
| `CLAUDE.md` names a **single developer**; staffing is **unresolved** (Sprint-1 audit blocker #4) | The calendar cannot be committed until this is decided |
| Heaviest sprints **S2, S8, S10** "may split under a small team" (per charter) | Build the three split buffers into any committed plan |

**Two planning scenarios:**
- **Scenario B — full squad (~6–7 FTE):** 11 themed sprints, S2/S8/S10 split → ~13–14 calendar
  iterations → **~26–28 weeks (~6.5 months)**. *Recommended planning basis.*
- **Scenario A — small team (~1–3 FTE):** per-sprint scope can't double; each theme spans multiple
  calendar iterations; the calendar trends back toward the old **~40–48 weeks**. The 11-sprint
  **structure** still holds — only the calendar stretches.

**EM recommendation:** adopt the 11-sprint **structure** now (this re-baseline), but **do not publish
calendar dates** until team size is confirmed. Track the heavy sprints with explicit split buffers.

---

## 6. Critical Path

The binding (longest, non-parallelizable) dependency chain:

```
S1 ─▶ S2 ─▶ S4 ─▶ S5 ─▶ S6 ─▶ S7 ─▶ S10 ─▶ S11
Foundations  Secure  Master  Booking  Fleet  Realtime  AI   Hardening
             core    data    spine                    services & release
```
- **8 nodes**, anchored by the tracking/AI dependency (S10 needs GPS data from S7, which needs the
  fleet from S6, which needs the booking spine from S5).
- **Off the critical path (slack):** **S3** (overlaps S4) and **S8 + S9** (billing/analytics overlap
  S6/S7 once S5 lands) — *only if a multi-stream team exists*. Single-threaded, the path is the full
  S1→S11 sequence.
- **Critical-path risks:** RLS correctness at S2 (gates everything tenant-scoped) and the data
  dependency for S10 (no ETA model without S7 telemetry). Both are reflected in the risk register.

---

## 7. Updated Tracker Structure

The workbook keeps its five sheets; each is re-baselined to 11 sprints and de-phased.

**Overview** — title, status vocabulary, progress summary (auto-recalculated), legend, and a
"Re-baselined to 11-sprint roadmap on <date>" note. Remove all P0–P9 references.

**Milestones** — `# · Milestone (exit state) · Sprint · Target (Scenario B weeks) · Owner · Status`,
rows **M0–M10** (per §2).

**Sprints** — `Sprint · Theme · Modules · Depends on · Weeks (Scenario B) · Split risk · Status`,
rows **S1–S11** (per §1/§3/§4). S1 marked **Done**.

**Tasks** — reframed to **sprint-level epics** (`ID · Sprint · Epic · Owner (agent role) · Depends on
· Status`), e.g. `S2-E1 Multi-org auth`, `S2-E2 RLS + tenancy context`, `S2-E3 RBAC`, `S2-E4 Audit`.
Detailed per-sprint task breakdowns live in the sprint backlogs (e.g. `Sprint1_Backlog.xlsx`), not in
this roll-up. Old `T01–T??` week/phase tasks are replaced.

**Risks** — keep R1–R6 with phase references re-pointed to sprints, plus two new entries:

| # | Risk | L | I | Mitigation | Owner |
|---|---|---|---|---|---|
| R1 | RLS misconfiguration → tenant leakage | Med | Critical | Isolation suite each build; security gate before **S5** | TL |
| R2 | GST / e-way bill incorrectness | Med | High | Tax SME review; sandbox; golden-case tests (**S8**) | BE lead |
| R3 | WebSocket scaling under load | Med | High | Redis Pub/Sub fan-out; load tests in **S7/S11** | TL |
| R4 | AI training data insufficient | High | Med | Heuristics first; collect from **S7+**; flag-gated (**S10**) | ML |
| R5 | Gov/map third-party API reliability | Med | Med | Retry/queue; manual fallback; idempotency | BE lead |
| R6 | Scope creep across sprints | Med | High | Locked scope lists; change-control via EM | EM |
| **R7** | **Team size unresolved → calendar uncommittable** | **High** | **High** | Confirm staffing before publishing dates; plan on Scenario B | EM |
| **R8** | **Heavy sprints (S2/S8/S10) overrun** | **Med** | **High** | Pre-budgeted split buffers; descope to flags if needed | EM |

---

## Re-baseline Report (summary)
- Scope is **fully preserved**; 24 fine-grained sprints regrouped into **11 themed sprints** (§1).
- Milestones re-anchored to sprints; **+1 milestone** (M2 Platform services) → **M0–M10** (§2).
- Dependencies re-expressed at sprint level and validated against the roadmap (§3).
- Timeline floor **~22 wk**, realistic **~28 wk** with split buffers; **dates withheld** pending team
  size (§4, §5).
- Critical path identified: **S1→S2→S4→S5→S6→S7→S10→S11** (§6).

## Tracker Correction Report
**Removed / replaced:**
- Sprints **S12–S24** (regrouped into S6–S11).
- Phase taxonomy **P0–P9** (replaced by 11 themed sprints).
- 48-week / Wk 25–48 timeline anchors (replaced by Scenario-B week ranges).
- Old `T01–T??` phase/week tasks (replaced by sprint epics).

**Added / corrected:**
- Milestone **M2** (Platform services); milestone count 10 → **11**.
- Dependency references: phase-based → sprint-based.
- Risk register: phase refs → sprint refs; added **R7** (capacity) and **R8** (heavy-sprint overrun).

**Verification checklist (run against the regenerated workbook):**
- [ ] No cell contains `S12`…`S24`.
- [ ] No cell contains `P6`…`P9` (or any `P#` phase taxonomy).
- [ ] No stale `Wk 25`…`Wk 48` milestone targets.
- [ ] Sprints sheet lists exactly **S1–S11**.
- [ ] Milestones sheet lists exactly **M0–M10**.
- [ ] Every "Depends on" references a valid S1–S11 sprint.
- [ ] S1 status = **Done**.

## Updated Sprint Structure (canonical, 11 sprints)
| # | Theme | Modules | Depends on | Milestone |
|---|---|---|---|---|
| S1 | Foundations | Docker · Env · PostgreSQL · Redis · Backend scaffold · Frontend scaffold | — | M0 ✅ |
| S2 | Secure core | Authentication · Users · Organizations · RBAC · Audit | S1 | M1 |
| S3 | Platform services | Departments · Teams · Notifications · Feature flags | S2 | M2 |
| S4 | Master data | Customers · Vendors · Warehouses | S2 | M3 |
| S5 | Booking spine | Orders · Shipments · AWB | S4 | M4 |
| S6 | Fleet | Drivers · Vehicles · Trips · Assignment · Dispatch · Maintenance | S5 | M5 |
| S7 | Realtime tracking | WebSocket · GPS ingestion · Live map · Customer track · Triggers | S6 | M6 |
| S8 | Billing & compliance | Rate cards · Invoices · Payments · GST · E-Way Bill | S5 | M7 |
| S9 | Analytics | Aggregation · Role dashboards · Report builder · Exports | S5–S8 | M8 |
| S10 | AI services | ETA · Route optimization · Demand forecasting · Anomaly detection | S7 | M9 |
| S11 | Hardening & release | Security · Pen-test · Load/perf · Regression · UAT · Observability · DR · Go-live | S1–S10 | M10 |

---

**On approval**, I will regenerate `Logistics_Platform_Project_Tracker.xlsx` to this structure (five
sheets, S1–S11, M0–M10, sprint epics, updated risks, live progress summary), run the verification
checklist above, and place the workbook in the repo (governance-tracked) rather than loose in the
output folder.
