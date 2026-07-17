# srmech Architecture Decision Records

Each ADR captures one durable architecture decision — the *context* that forced it,
the *decision*, and its *consequences* — so the reasoning is versioned with the code
and discoverable by anyone, not held only in a maintainer's head. ADRs are additive:
a decision is *superseded*, never edited away.

## Conventions

- **Filename:** `NNNN-kebab-title.md`; the number is permanent (append-only).
- **Status:** `Draft` → `Accepted` → (`Superseded-by: NNNN`). "Accepted — standing
  policy" governs every rc, op, and review.
- **Sources footer:** the discipline ADRs (0005–0007) link the project-memory topic
  files they consolidate, preserving the trail.
- **Companion artifacts** share an ADR's number with a distinct extension — they are
  NOT separate ADRs. `0001-profile-pattern.schema.json` is the machine-readable
  `srmech_profile.toml` v1 schema that ADR-0001 defines (not a second ADR-0001).
- **Numbering note:** the only genuine *number collision* (two different ADRs both
  named `0002`) was resolved 2026-07-17 by renumbering the operator-chain schema to
  `0008`; older CHANGELOG / design-note references to
  `0002-phase-1-operator-chain-schema` resolve to `0008`.

## Index

### Extension & computation model

| ADR | Title | Status |
|----|-------|--------|
| [0001](0001-profile-pattern.md) | The srmech **profile pattern** — domain-specific extension as configuration (catalogs + bridge functions + an optional native lib via ctypes). | Draft |
| [0002](0002-catalog-as-computation.md) | **Catalog-as-computation** — the 14 A–N primitive classes are closed; plugins are optimization backends, not new primitives. | Draft |
| [0008](0008-phase-1-operator-chain-schema.md) | **Operator-chain DSL** — the Phase 1 descriptor-TOML chain schema (v1) + the 4-namespace reference grammar. | Phase 1 candidate |

### Architecture — standing policy

| ADR | Title | Status |
|----|-------|--------|
| [0003](0003-c-host-standalone-no-python-assumption.md) | **C-host-standalone & C↔Python parity** — srmech runs with no Python present; every composite mirrors in C, standalone-complete, same-rc, byte-parity, PAL-mirrored I/O. | Accepted |
| [0004](0004-config-driven-domain-agnostic-surface.md) | **Config-driven, domain-agnostic surface** — a user declares classes, chains, catalogs, and names in TOML; framework naming is a re-aliasable default; config gives names, not capabilities. | Accepted |
| [0005](0005-no-external-math-library.md) | **No external mathematics library** — srmech imports *no* math library (numpy / `math` / `fractions` / `decimal` / scipy / sympy / gmpy / any). A missing primitive is added natively; srmech owns `srmech_bigint` / `Q` / `Mat`, deliberately named so the external-lib reflex never fires. | Accepted |
| [0006](0006-carrier-discipline.md) | **Carrier discipline** — stay rational (collapse to a decimal only at display); ALU all the way, FPU last mile; sign is Class-K, never `abs()`; preserve carrier format; bounded arena (a RAM blow-up is a missed fiber). | Accepted |
| [0007](0007-release-engineering.md) | **Release engineering** — the 5-file version SSOT; rc-first to TestPyPI + autotag-clean-only; the new-public-callable registry ripple; platform-agnostic via the HAL (optimize) + PAL (I/O) + the pedantic 3-OS matrix; JPL Power-of-Ten. | Accepted |

## Related

- `docs/srmech/c/JPL_AUDIT.md` — the Power-of-Ten audit referenced by ADR-0007.
- `docs/srmech/notes/` — design notes + spikes behind several ADRs (e.g. the Phase 1
  operator-chain DSL design note behind ADR-0008).
