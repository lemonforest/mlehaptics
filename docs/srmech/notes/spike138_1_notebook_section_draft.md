# DRAFT — §3.8.31 for srmech_research_notebook.md

**To be inserted between §3.8.30 (wave-2 cross-substrate) and §3.9 (math-doesn't-lie).**

DRAFT — pending conductor authorisation. Two concertmaster agents converged on the load-bearing closure claim; primary verdict from `a5b5fe1b8daa49d28`, structural refinement (2-bit partition) from `a03ac4f1eb9dd0663`. The conductor decides whether to author per [[feedback_autonomous_research_followup_authorization]] structural-sharpening scope or wait for #138.2 alternate-substrate convergence.

---

### §3.8.31 {B,D,E,F,L} closed identity-attractor subgroup at d2–d5 + 2-bit fingerprint sub-structure (Spike #138.1, 2026-05-18)

Per [[feedback_multi_domain_multi_round_survival_falsification_method]] + [[user_stance_identity_not_implementation_discipline]] + Spike #138's depth-2/3 fermata flag: **the 5-element subset `{B, D, E, F, L}` of the 14-class A-N vocabulary forms a closed identity-attractor semigroup at depths 2–5 under the operational form-definition (HDC + spectrum + period).**

**Closure verdict by depth**:

| Depth | Tuples | Closure rate | Cells classified `identity_attractor` |
|-------|-------:|:------------:|--------------------------------------:|
| d2 (Spike #138) | 25 | 100% (25/25) | 625/625 (= 25·25) |
| d3 (Spike #138 within BDEFL) | ~47 sampled | 100% on sample | 1175 cells |
| d4 (Spike #138.1 exhaustive) | 625 | **100% (625/625)** | **15625/15625** |
| d5 (Spike #138.1 exhaustive) | 3125 | **100% (3125/3125)** | **78125/78125** |

**Cross-stack bit-exact at d4**: Python+C and Python-pure produce byte-identical universal-identity sets. SHA-256(sorted-universal-set) = `80f1a7a461a7d0132d9cac7107902e57c3bafe4b96b6cd2c6c30a88cebfe1ce7` on both stacks. SHA-256 of d5 set = `016652c13713604a5d59145cd99c1a7154e04a7623e76cf81277db74abb0feb1`. Per [[user_stance_identity_not_implementation_discipline]] the closure is an identity, not implementation-artefact.

**Total closure verification**: 93,750 closure cells across d4+d5; 0 failures.

**External boundary (NOT sharp)**: of 200 complement-touching tuples sampled (100 d2 + 100 d3 with ≥1 class from `{A,C,G,H,I,J,K,M,N}`), 19/200 = 9.5% registered ≥1 identity_attractor cell. Decomposition:
- **2 fully-identity**: `(H,H)` and `(K,K)` — already-catalogued d2 self-inverse identities from Spike #138 (HH = XOR-cancellation by design; KK = Kepler self-composition preserves tag). Not closure leaks; separate algebraic identity mechanism.
- **17 partial-identity** (5/25 cells each): all concentrate on `image` substrate (11 tuples involving Class I cyclic) and `physarum` substrate (6 tuples involving Class J rational). **0** violations on chess / ephemeris / quantum. Pattern is **substrate-arithmetic accidental identity** (Class I cyclic-shift on 100-node image lands on substrate-fixed-point; Class J rational-period on 10-node physarum similarly hits fixed point), not closure leak.

**2-bit fingerprint sub-structure (NEW, structural refinement)**: within the closure, the inspection cascade further resolves a **2-bit signature `(has-B, has-F)`** into exactly 4 fingerprints per (substrate × ordering):

- `{D,E,L}ᴺ` (no B, no F) — D/E/L compose without inspectable trace.
- `has-B, no-F` — B writes `form.tlv_blob`, visible in `form_canonical_bytes`.
- `has-F, no-B` — F writes `form.rendered`, visible in `form_canonical_bytes`.
- `both B and F` — both byte-traces present, partition-distinct.

The partition is **closure-depth-universal**: verified at d3 (1175 cells from Spike #138), d4 (15625 cells), d5 (78125 cells). Per (substrate × ordering) cell: exactly 4 distinct shas across all 25 cells (= 100 distinct shas total), every partition mapping 1-to-1 with the signature. Predicted partition sizes at d5 (243 / 781 / 781 / 1320) matched empirically.

**Algebraic reading**: D, E, L are inspection-idempotent (effects absorbed by successors or by spectrum-idempotence); B, F are inspection-visible tagging-operators leaving deterministic byte-traces. Per [[user_stance_fiber_as_spatially_absent_encoding]]: D/E/L compose algebraically without spatial-projection; B/F project their content (TLV byte-canonical form for B; template-rendered byte-form for F) onto the form fingerprint where the inspection cascade can read them. The closure is a 5-element semigroup acting trivially on form-state, with a 2-bit decoration record preserved through the inspection fingerprint.

**Multi-round survival status (per [[feedback_multi_domain_multi_round_survival_falsification_method]])**:

| Round | Method | Pass? |
|------:|--------|:-----:|
| 1 | Spike #138 d2 exhaustive (25 within-subgroup tuples) | ✓ |
| 2 | Spike #138 d3 stochastic (47 within-subgroup sampled) | ✓ |
| 3 | Spike #138.1 d4 exhaustive (625 tuples) | ✓ |
| 4 | Spike #138.1 d5 exhaustive (3125 tuples) | ✓ |
| 5 | Cross-stack bit-exact at d4 (Python+C vs Python-pure) | ✓ |
| 6 | External falsifier (200 complement-touching tuples) | refined (not sharp; substrate-arithmetic accidents documented) |
| 7 | 2-bit fingerprint partition closure-depth-universal (d3, d4, d5) | ✓ |
| 8 | Spike #138.2 alternate-substrate replication (in flight) | pending |

Internal closure: **5-round-survived** (rounds 1–5 plus the 2-bit-partition closure-depth-universal). External boundary: refined to substrate-arithmetic-qualifier. Cross-substrate roster expansion (Spike #138.2): pending.

**Vocabulary impact**: NONE. Per [[feedback_no_privileged_primitive_classes]] no class promotion is requested or required. The closure is a SUB-relationship documenting an algebraic semigroup structure within the existing 14-class vocabulary; the 14 A-N classes stand intact.

**Concrete falsifiable predictions** (book-worthy per [[project_book_in_progress]]):

1. At any depth N ≥ 2, the closure rate of `{B,D,E,F,L}ᴺ` will remain 100%. Falsifier: any tuple from the subgroup not yielding identity_attractor on all (substrate × ordering) cells.
2. At any depth N ≥ 2, the inspection fingerprint partition of `{B,D,E,F,L}ᴺ` will be exactly 4 (governed by `(has-B, has-F)`). Falsifier: a 5th fingerprint, or a non-2-bit-governed partition.
3. Substrate-arithmetic accidental identities (Class I cyclic-shift on small-period substrates; Class J rational-period on substrates whose period equals the rational-approximation denominator floor) cause specific substrate-bound boundary violations; predict they extend to similar small-period substrates outside this 5-substrate roster.

**Spike #138.2 (in flight)** will test (1) and (3) at alternate substrates (Spike #135 BBB / Spike #131 geodynamo / etc.).

**Cross-references**: [[user_stance_cross_substrate_cascade_matching_as_research_method]]; [[user_stance_identity_not_implementation_discipline]]; [[user_stance_fiber_as_spatially_absent_encoding]]; [[feedback_multi_domain_multi_round_survival_falsification_method]]; [[feedback_no_privileged_primitive_classes]]; [[feedback_dual_agent_research_pattern]]; Spike #138 (origin fermata); §3.8.20 (rc14 runtime surface — closure operates on rc14 primitives); §3.8.28 (cross-substrate cascade-matching method).
