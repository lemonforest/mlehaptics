# srmech — Architecture Decision Records (ADR)

This directory holds the Architecture Decision Records for **srmech** (Stored-
Relationship Mechanism). Format follows the srmech-family `ADR-NNNN` convention:
**one file per decision, small and scoped, never monolithic**. Each ADR captures
**one** decision as **Status / Context / Decision / Consequences**; the discipline
ADRs forward-link the project-memory topic files they consolidate — the
*breadcrumb-web* discipline, so a decision survives even when the notes are not in
context.

---

## Index

| ID | Title | Status | Date |
|----|-------|--------|------|
| [ADR-0001](0001-profile-pattern.md) | The srmech profile pattern — domain-specific extension as configuration | 🟢 Implementing | 2026-05-14 |
| [ADR-0002](0002-catalog-as-computation.md) | Catalog-as-computation — primitive-class closure, plugins as optimization backends | ⏳ Draft | 2026-05-16 |
| [ADR-0003](0003-c-host-standalone-no-python-assumption.md) | C-host-standalone — never assume a Python environment (C↔Python parity) | ✅ Accepted | 2026-07-16 |
| [ADR-0004](0004-config-driven-domain-agnostic-surface.md) | Config-driven, domain-agnostic surface — classes, chains, catalogs, and names in TOML | ✅ Accepted | 2026-07-16 |
| [ADR-0005](0005-no-external-math-library.md) | No external mathematics library — srmech is its own math library | ✅ Accepted | 2026-07-17 |
| [ADR-0006](0006-carrier-discipline.md) | Carrier discipline — exactness, sign, format, and bounded memory | ✅ Accepted | 2026-07-17 |
| [ADR-0007](0007-release-engineering.md) | Release engineering — version SSOT, rc-first, the registry ripple, HAL/PAL, JPL | ✅ Accepted | 2026-07-17 |
| [ADR-0008](0008-phase-1-operator-chain-schema.md) | Operator-chain DSL — Phase 1 schema specification | 🔄 Proposed | 2026-05-16 |
| [ADR-0009](0009-multi-implementation-parity-capability-is-the-invariant.md) | Multi-implementation parity — the capability is the invariant, each implementation is a coherency projection (amends 0003) | ✅ Accepted | 2026-07-19 |
| [ADR-0010](0010-namespace-declustering.md) | srmech namespace declustering — `amsc` is the attestation framework, not the dumping ground | 🟢 Implementing | 2026-07-23 |
| [ADR-0011](0011-single-encoding-no-cache.md) | One encoding per datum — the genome has no cache (biology re-derives; a cache lives outside the genome or not at all) | ✅ Accepted | 2026-07-26 |
| [ADR-0012](0012-introspect-as-the-api-contract.md) | The introspect surface IS the API contract — autonomous composition, not documentation | 🟢 Accepted | 2026-07-30 |

**Status legend:** ✅ Accepted · 🟢 Implementing · 🔄 Proposed · ⏳ Draft · 🗑 Superseded.

## Conventions

- **Filename:** `NNNN-kebab-title.md`; the number is permanent (append-only).
- **Status lifecycle:** ⏳ Draft / 🔄 Proposed → 🟢 Implementing → ✅ Accepted → 🗑 Superseded
  (`Superseded-by: NNNN`). An "Accepted — standing policy" ADR governs every rc, op,
  and review.
- **🟢 Implementing — the fifth state, and why it exists.** Direction accepted,
  execution arc **OPEN**, shape still being learned. An ADR here is *deliberately
  revisable*: it may be amended in place as the build teaches it what it actually
  is, **without needing to be SUPERSEDED merely to change**. That is the whole
  point — user direction, 2026-08: *"we wanted to keep it plyable until we knew
  the shape to fully define it. to prevent many superseeded ADRs."* An ADR is
  promoted to ✅ **Accepted** once its shape has settled into standing policy.
  Before rc409 this state had no glyph, so an ADR in it had to either overclaim
  ✅ or underclaim 🔄; two ADRs improvised 🟢 and used it to mean two different
  things. `tests/test_adr_status_coherence_rc409.py` now holds file header ↔
  index row ↔ legend to strict equality.
- **Amendment:** an ADR may **amend** another without superseding it (`Amends: NNNN` in
  the header; the amended ADR carries an `Amended-by` note). Both stay Accepted and in
  force; the amending ADR states in its body exactly which clause it revises and why.
  ADR-0009 amends ADR-0003 §2.6 — the first use of this relation.
- **Sources footer:** the discipline ADRs (0005–0007) link the project-memory topic
  files they consolidate, preserving the trail.
- **Companion artifacts** share an ADR's number with a distinct extension — they are
  NOT separate ADRs. `0001-profile-pattern.schema.json` is the machine-readable
  `srmech_profile.toml` v1 schema that ADR-0001 defines (not a second ADR-0001).
- **Numbering note:** the only genuine *number collision* (two different ADRs both
  named `0002`) was resolved 2026-07-17 by renumbering the operator-chain schema to
  `0008`; older CHANGELOG / design-note references to
  `0002-phase-1-operator-chain-schema` resolve to `0008`.

## Scope note

These are **algebra / eigenbasis / cyclic-group / spectral side** decisions (the
framework-research + library-engineering discipline). They do **not** cover CAD /
fabrication / mechanical geometry — out of scope per the CAD-grade ban carried from
the parent monorepo.

## Related

- `docs/srmech/c/JPL_AUDIT.md` — the Power-of-Ten audit referenced by ADR-0007.
- `docs/srmech/notes/` — design notes + spikes behind several ADRs (e.g. the Phase 1
  operator-chain DSL design note behind ADR-0008).
