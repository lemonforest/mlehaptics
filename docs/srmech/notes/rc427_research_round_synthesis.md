# rc427 research-round synthesis — what to build, what to reject, what was wrong

**Task `#T1130`. READ-ONLY round.** No version bump, no rc, no PR, nothing under
`docs/srmech/python/srmech/` touched.

Four generative streams (G1/OPGAPS, G2/REVERSAL, G3/NOTATION, G4/ARROW) and four adversarial
verifiers (V1+V1b, V2, V3, V-G4) reported. This document adjudicates them and is the single
decision surface for the rc427 build.

---

## 0. Environment — verified, not assumed

| Item | Expected | Measured | Source |
|---|---|---|---|
| `origin/main` version | v0.9.0rc425 | `0.9.0rc425` | `docs/srmech/python/srmech/version.py:7` |
| registry | 649 | 649 live / 649 lines | `len(get_tool_schema().tools)` after `warmup_all()`; `tests/registered_op_names.txt` |
| ABI | 14 | 14 | `c/include/srmech.h:280` |
| numpy | ABSENT | `find_spec('numpy') is None` | WSL2 Ubuntu, python 3.10.12 |
| `srmech.__file__` | source tree | `/mnt/d/GitHub/mlehaptics/docs/srmech/python/srmech/__init__.py` | printed at the head of every run |

No STOP condition. `warmup_all()` is load-bearing — without it the count is short.

### My own artifacts (this synthesis pass)

| Path | Records |
|---|---|
| `D:\GitHub\mlehaptics\docs\srmech\notes\_s1_synthesis_adjudication_rc427.py` | 10 pre-registered falsifiers S1–S9 |
| `D:\GitHub\mlehaptics\docs\srmech\notes\_s1_synthesis_adjudication_rc427.ndjson` | 10 records, one per line |

Branch `srmech-rc427-research`. **Not pushed.**

### Branch topology — the streams are on THREE branches, and this matters

| Branch | Holds |
|---|---|
| `srmech-rc427-research` | G4, G2, G3, G1 (all four generative streams) — **the base** |
| `srmech-rc427-v1-opgaps-verify` | the above + V1, V1b |
| `srmech-rc427-g4-arrow-verify` | G4/G2/G3 + V-G4, V2, V3 — **does NOT contain G1 or V1** |

⚠️ **No single branch holds all eight streams.** Anyone opening `srmech-rc427-research` sees the
four proposals and none of the four refutations. The build rc must collect all three.

---

## 1. The costed op list — BUILD

Seven new registry rows, plus two parameter extensions that add no row. Every name below was
grep-verified ABSENT at rc425 (S1: 13/13 candidates absent across registry names, ToolEntry prose,
`__all__`s, package `def`s, the 24 DSL TOMLs, and `docs/srmech/notes/`).

| # | Op | Target module | A-N class | Exact? | Cost | Composes from | The concrete caller that needed it |
|---|---|---|---|---|---|---|---|
| 1 | `mod_mul_arrow(c, n)` | `srmech/math/cyclic.py` | **I** (cyclic) then **L** (kernel/rank read) — *not* G4's K; see §7 | ✅ exact ℤ | small | `srmech.math.primes.factor`, `srmech.math.cyclic.gcd`, `mod_mul` | `cyclic_period(6, 12)` **raises** `gcd != 1`; the eventual period of a non-unit multiplier is unreachable through shipped surface. G4 had to hand-roll `closed_form_arrow()`. |
| 2 | `finite_semiflow(table)` | `srmech/cascade/semiflow.py` (new) | **E** (orbit/index catalog) then **D** (permutation pattern) | ✅ exact ℤ | small | op 1's index/period logic | The tabulated peer of op 1. Real feeders: `q8_project_v4` (shipped, non-injective, C-peered) and `mod_pow`. **NOT `unit_loop`** — see §7. |
| 3 | `conjugacy_census(cayley_table)` **(merged — see §1.1)** | `srmech/cascade/finite_group.py` (new) | **E** (orbit catalog) then **D** (pattern) then **N** (exact-ℚ rate) | ✅ exact ℚ | medium | `unit_loop`, `cyclic_mod_add`, `srmech.math.cyclic.gcd`, `srmech.math.q.Q` | **The strongest single argument in the round.** An unguarded class-equation op reports **144 where the truth is 88** (M16) and **544 where the truth is 184** (M32) — silently wrong by 56 and by 360. The guard *is* the op. |
| 4 | `law_census(domain, dim=8, table=None)` **(narrowed — see §1.2)** | `srmech/cascade/cayley_dickson.py` | **D** (pattern-match) then **E** (catalog) | ✅ exact ℚ | large | `unit_loop`, `associator`, `cd_basis`, `algebra_table`, `table_product` | Alternativity / flexibility / LIP / RIP / division / power-associativity / diassociativity have no named op and were hand-rolled in ≥4 separate notes. `domain` has **no default**, by measurement. |
| 5 | `reversal_law_census(cayley_table, ...)` **(table-based — see §1.3)** | `srmech/cascade/reversal.py` (new) | **C** (which-way) then **D** (census) then **A** (SHA-256 of each hit SET) | ✅ exact | medium | `chiral_flip`, `srmech.amsc.format.sha256_bytes` | At O16 bare and chiral reversal **both score 2752/4096 and succeed on different triples** — 1344 each way. A count-only test declared them equivalent and was wrong. |
| 6 | `anti_automorphism_witnesses(cayley_table)` **(table-based)** | `srmech/cascade/reversal.py` | **C** then **D** then **A** | ✅ exact | small | `chiral_flip`, `sha256_bytes` | rc426 asserted "(ab)⁻¹ = a⁻¹b⁻¹ holds exactly on the commuting pairs" **from a count equality**. This measures the SET. |
| 7 | `dihedral_group(n, convention)` **(CONDITIONAL on #3 — see §1.4)** | `srmech/cascade/finite_group.py` | **I** (cyclic) then **C** (orientation) with **K** pin-slot | ✅ exact ℤ | medium | `cyclic_mod_add` | FA1: every shipped group constructor refuses non-power-of-two order, so **no group of order 12 or 24 is reachable at all**. It is the non-power-of-two carrier that makes #3 and #5 non-vacuous outside loops. |
| 8 | `unit_loop(dim=8, **table=None**)` | `srmech/cascade/cayley_dickson.py` | *no new class* — carrier plumbing | ✅ | small | — | **+0 registry rows** (parameter extension) |
| 9 | `loop_invariants(dim=8, **table=None**)` | `srmech/cascade/cayley_dickson.py` | *no new class* | ✅ | small | — | **+0 registry rows.** Measured S3: `unit_loop` and `loop_invariants` are the **only two** members of the 12-op cascade loop family without `table=`. Extending one leaves the wall one call later. |

### 1.1 — Ops 3 and 4 of G2 were the SAME op as G1's #3. Merged.

Neither verifier caught this, because **each verified only its own stream**.

| Stream | Proposal | Returns |
|---|---|---|
| G1 | `conjugacy_census(cayley_table)` | commuting pairs, k(G), commuting probability, class-equation guard |
| G2 | `commuting_probability(elems, mul, inv)` | commuting pairs, k(G), commuting probability, non-group detector |

These are one op with two calling conventions. Building both ships duplicate registry surface —
exactly the defect this round exists to prevent. **RULING: one op, `conjugacy_census`,** taking a
Cayley table, returning commuting pairs · k(G) · commuting probability as exact ℚ · the
class-equation agreement flag (which *is* G2's non-group detector) · the associativity guard.
G2's Gustafson verdict rides as fields.

Evidence the merged detector works: `Pr(G) ≠ k(G)/|G|` fires on **exactly `['O16']`** — 43/64 vs
9/16 — with zero false positives on ℤ/7, ℤ/12, Q8, TI24.

### 1.2 — `law_census` is NARROWED to the eight non-Moufang laws

I measured this directly (S2): `moufang_residue(x, y, z, table=algebra_table(16))` returns a
**per-ordered-triple exact-ℚ defect**, and **1176 of 4096** ordered basis triples carry a nonzero
residue while `is_moufang` returns the single bit `False`.

So FC3's justification — *"a count-only or boolean read erases that completely"* — is **already
answered for the Moufang third**. `law_census` survives on the eight laws that genuinely have no
op: left-alternative, right-alternative, flexible, LIP, RIP, division, power-associative,
diassociative.

Two contract requirements, both forced by measurement:

| Requirement | Why |
|---|---|
| `domain` is **REQUIRED, no default** | The same law NAME gives OPPOSITE verdicts on the SAME shipped table: flexibility is **256/256 (holds)** on the signed unit loop and **508/512 (4 violations)** on the algebra basis. |
| The three Moufang spellings must be **PINNED in the contract** | V1b: an independently chosen triple of textbook-equivalent spellings makes two of the three fail on the *identical* 5376-element set (symmetric difference 0), where G1's spellings give three pairwise-disjoint halves. The disjointness is a property of the spelling, not of the loop. |

### 1.3 — G2's census ops CANNOT take callables. Table-based, forced.

**A cross-stream finding neither verifier could reach.** G2 proposed
`reversal_law_census(elems, mul, inv, interval)` and `anti_automorphism_witnesses(elems, mul, inv)`
with `mul`/`inv` as **required** operands.

Measured (S9) over all 649 ToolEntries:

| Metric | Value |
|---|---|
| ops with a callable parameter | 12 |
| callable parameters total | 12 |
| distinct types | `host_callable` |
| **REQUIRED callable parameters** | **0** |

The shipped contract, verbatim at `srmech/introspect/tool_schema.py:3770`:

> *"a callable cannot cross JSON-RPC … typed `host_callable`, which publishes JSON-schema null —
> over the wire the only legal value is absence"*

All 12 shipped callable params are **optional** `progress` / `compatible` side-channels. G2's
`mul`/`inv` are the semantics and cannot be omitted. **RULING: both take a Cayley table
(`Sequence[Sequence[int]]`)** — which is also G1's `conjugacy_census` representation, so all three
censuses then eat the same carrier object, including `dihedral_group`'s output.

### 1.4 — `dihedral_group` is CONDITIONAL, and its justification is rewritten

V1 refuted two of its three supports; I re-measured and confirm both (S5):

| G1's support | Measured | Verdict |
|---|---|---|
| "360 of 576 Cayley cells differ between the two readings" | 360 — and `cells_differing == order² − commuting_pairs == 576 − 216`. R is exactly the transpose of L. | **Not independent evidence.** It restates "D12 is non-abelian", already reported one field away. |
| "downstream axiom A splits 13824 forward vs 5184 reversed" | Identical on BOTH tables. `5184 == commuting_pairs × order == 216 × 24`. | **Convention-INDEPENDENT.** It measures forward-vs-reversed composition *inside* one table. |
| "the decision belongs to the GROUP OBJECT" | `x → x⁻¹` is an isomorphism L → R on **576/576** products; class sizes identical `[1,2,2,2,2,2,1,6,6]`. Negative control (identity map) is **not** an isomorphism. | **The two conventions are ISOMORPHIC.** The decision is about ELEMENT LABELS. |

What survives, and is enough:

- **FA1** — no group of order 12 or 24 is reachable at all. `unit_loop` gives orders {4, 8, 16, 32};
  `group_algebra_table` raises `dim must be a power of two <= 64` on 3, 5, 12, 24 and is abelian by
  its own docstring.
- **FA4** — the 24-image T/I orbit partition **equals** the shipped `prime_form` partition:
  **79 blocks** on both `forte` and `rahn` over all 1507 subsets of cardinality 3–5. Negative
  control (rotations only) gives **128 blocks ≠ 79**, so the instrument can return otherwise.

⚠️ **But FA4 argues the OBJECT is real, not that the OP is needed** — `prime_form` already uses the
orbit privately, and rc426 already built TI24 from `cyclic_mod_add` in a note. So:

- `convention` stays **REQUIRED**, documented honestly as a **labelling** decision — the same shape
  as `prime_form`'s own required `convention`, which is legitimate precedent.
- **Build it only if op 3 is built.** Without `conjugacy_census` it has no caller.

---

## 1.5 Already shipped — DO NOT BUILD, with path

| Claimed / proposed capability | Ships as | Path |
|---|---|---|
| Per-triple Moufang failing SET | `srmech.cascade.moufang_residue` — measured **1176/4096** nonzero at dim 16 | `srmech/cascade/cayley_dickson.py:2227` |
| Whole-loop Moufang bit | `srmech.cascade.is_moufang` | `cayley_dickson.py:2277` |
| Associator / Mal'cev + Jacobi defect | `srmech.cascade.associator`, `.malcev_defect` | `cayley_dickson.py:2313` |
| Unit loop + Cayley table (Latin square) | `srmech.cascade.unit_loop` | `cayley_dickson.py:2377` |
| Nucleus · commutant · centre · Mlt(L) translations | `srmech.cascade.loop_invariants` | `cayley_dickson.py:2418` |
| "multiply-by-a-fixed-element is non-injective" + what it destroys | `srmech.cascade.left_mult_is_invertible`, `.left_mult_kernel` — shipped prose already says *"no backward direction to point"* | `cayley_dickson.py:2801`; registry lines 201–202 |
| A shipped non-injective idempotent self-map (with C peer) | `srmech.biology.q8.q8_project_v4` | `srmech/biology/q8.py:240`; `c/src/srmech_q8.c:108` |
| Sequence/catalog order reversal; chiral dual | `srmech.cascade.chiral_flip`, `.chiral_dual`, `srmech.introspect.naming.reverse_order` | `srmech/cascade/atoms.py:435`, `:469` |
| Flexibility negative control | `flip_pair` (one-named-bit control) | `cayley_dickson.py:808` |
| Enharmonic / spelling fibre | `srmech.math.covering.lift_fibre` ∘ `mod_inv` ∘ `mod_mul` — **6462/6462** agreement | `srmech/math/covering.py`, `srmech/math/cyclic.py` |
| Octave / register fibre | `srmech.math.covering.center_lift`, `.lift_fibre` — 10/10 moduli | `srmech/math/covering.py` |
| Pitch-class set theory (interval vector, normal order, prime form) | `srmech.music.relations` | `srmech/music/relations.py` |
| Cyclic period of a UNIT | `srmech.math.primes.cyclic_period` | `srmech/math/primes.py:180` |
| Z(Spin(8)) anchor | `srmech.physics.qm.triality.spin8_center` — **shipped at rc422** | `srmech/physics/qm/triality.py` |
| Carry-the-complement lossy record | `lossy_projection_record`, `fold_encode` | — |
| Frame-carrying + parallel transport before compare | `srmech.cascade.frame_carrier`, `.frame_carrier_compare` | `srmech/cascade/frame_carrier.py` |

⚠️ **Stale-absence trap:** `spin8_center` shipped *in rc422 itself*, so
`v4_so8_bridge_canonicity_rc422.ndjson`'s `anchor_present: false` is **true at rc421 and stale at
rc425**. Do not re-report the Z(Spin(8)) anchor as missing.

---

## 2. The reject list

A documented reject stops the question being re-asked in three rcs. Nineteen entries.

| # | Rejected | Proposed by | Reason | Evidence |
|---|---|---|---|---|
| R1 | `chiral_reversal` | G2 op 1 | **One shipped call, zero decision branches.** `chiral_reversal(word, inv) == chiral_flip(tuple(inv(x) for x in word))` — verified equal on 64/64 Q8 words. `music/relations.py:57-60` rejected three ops for exactly this shape. Ships as a **worked example** on `chiral_flip`, which is what that same file did for the ℤ/7 walk. | V2 |
| R2 | `gustafson_bound()` | G2 (self-rejected) | A **constant** carrying no decision. Ships as verdict fields on the merged census. | G2 |
| R3 | `bare_reversal` | G2 (self-rejected) | Already ships as `chiral_flip` — and it is the Class-C op the whole thesis warns against calling "reversal". | prior art |
| R4 | `opposite_table` / `opposite_group` | G2 (self-rejected) | A Cayley-table transpose carrying no decision. **Strengthened:** S5 shows the transpose is isomorphic to the original via `x → x⁻¹`, so it carries no isomorphism-invariant information either. | S5 |
| R5 | `half_inversion` | G2 (self-rejected) | A **negative control**, not a capability. Ships as cells R1–R4 of op 5, where it is exercised on every call. | G2 |
| R6 | `conjugacy_classes` standalone | G2 (self-rejected) | On a non-associative loop it is ill-defined without declaring a bracketing. Subsumed into op 3, which reports the bracketing agreement count so the ambiguity is visible. | G2 |
| R7 | `chart_declare` | G3 | **Its headline forcing law is VACUOUS.** "alphabet size is a theorem of the generator, 0 failures / 188 cells" — the failure branch is unreachable. Swept every alphabet size: **6274/6274 cells pass both predicates, 6086 of them with `a ≠ g⁻¹`.** At (n=12, g=7) the alphabet 5 also passes — that is the pentatonic scale. The refusal capability it is justified by **has nothing to refuse**. Separately: its entire return value reproduces bit-identically from shipped ops with one Class-K comparison. | V3 |
| R8 | `chart_transition` | G3 | **Its derivation IS the arithmetic the same spec rejects as `key_signature`**: `magnitude(least_magnitude_rep(mod_mul(mod_inv(g,n), t, n)))` — three shipped calls, zero search. Reproduced independently: `[0,5,2,3,4,1,6,1,4,3,2,5]`. The "49 evaluations" offered as its decision content is a **cross-check of** the closed form, not the derivation. | V3 |
| R9 | `action_lattice_read` | G3 | **Silent wrong answer outside the worked domain.** Translate the certified tuning `(0,5,10,15,20,25)` by any constant and the same rank-2 lattice, same kernel `(1,−5)`, same fibre structure flips the verdict to `is_group_homomorphism False, kernel None`. Affine maps have exactly the coset structure the op exists to report. Also: declared class "I then E" is unsupported — **0 modular calls** in the derivation. | V3 |
| R10 | `key_signature` | G3 (self-rejected) | Derived from two Class-I calls + a Class-K read; an op would store a table the arithmetic already derives. | G3, V3 |
| R11 | `spelling_fibre` / `enharmonic_fibre` / `chart_fibre` | G3 (self-rejected) | Composes from `lift_fibre(mod_mul(mod_inv(g,n), p, n), n, W)`. Verified at **SET** level: 6462/6462 set-agreement, **zero cells** in the dangerous counts-agree-memberships-differ class. | G3, V3 |
| R12 | octave / register fibre op | G3 (self-rejected) | rc426 P5 already ruled no new op warranted; `center_lift` + `lift_fibre` suffice on 10/10 moduli. | rc426 |
| R13 | `interval_invert` / `pitch_class_transpose` / `pitch_class_invert` | — (re-examined) | The **rc424 rejection STANDS**, re-examined as instructed and not overturned. Each is a single `cyclic_mod_add` carrying no decision. | `music/relations.py:54-63` |
| R14 | order-24 group via `group_algebra_table` | G1 (self-rejected) | Not reachable — refuses any non-power-of-two dim (`ValueError: dim must be a power of two <= 64`) and is abelian by construction. | FA1 |
| R15 | a flexibility negative control | G1 (self-rejected) | Already ships as `flip_pair`. What was missing is the **instrument** it is a control for — hence op 4. | prior art |
| R16 | a **torsor predicate** for the arrow | G4 (self-rejected) | Torsor is a **group** notion. Exhaustive over all 45 monoids of order ≤ 4 (1/2/7/35 — matching OEIS A058129): a simply transitive action exists **iff** the monoid is a group (5/5 groups yes, 0/40 non-groups yes), under all three torsor definitions, 0 disagreements. | G4 |
| R17 | a bare **projection** op | G4 (self-rejected) | An idempotent has index 1 and period 1: an arrow with one tick and no time. And it **already ships** as `q8_project_v4`. | G4 |
| R18 | a **trace/fold** that discards a coordinate | G4 (self-rejected) | Extant and already provenance-wrapped (`fold_encode` + `lossy_projection_record`). | G4 |
| R19 | `frame_scope` (ToolEntry field + swept ratchet) | G3 | **DEFERRED, not refuted.** V3 confirmed the `reads_lane` precedent is real (`tool_schema.py:342`, validated `:359-371`, C mirror `srmech.h:5531-5549`) and the ABI-additive argument survives at ABI 14. But it adds a field across 649 entries + a ratchet — a large ripple (4 generated files + the search corpus + the C struct) for a classification currently re-derived by hand once per round. **It belongs to an introspect rc, not a math-op rc.** | V3 |

---

## 3. Carrier vs chart — the split, the leak test, and the sourcing tiers

### 3.1 The split

| Lane | Meaning | Shipped ops in it |
|---|---|---|
| **CARRIER** | The interval object itself. No modulus baked in, or the modulus is a parameter. | `just_limit` (ℚ⁺, no modulus); `comma_of_chain`, `tempers_out` (carrier-parametric) |
| **CHART** | A presentation of the carrier. ℤ/12 hard-wired. | `interval_vector`, `normal_order`, `prime_form` |

Four private helpers hard-wire EDO12: `_as_pcs`, `_interval_class`, `_invert`, `_spans`.
The `12` is a **DECLARED** lane, not a silent assumption — 4/4 declarations true (rc426 C4).

### 3.2 The leak test, and its two known blind spots

| Version | Rule | Result |
|---|---|---|
| rc426 **F12** | one-clause leak predicate over 9 ops | 5 CARRIER / 4 CHART. Catches the 3 real leaks — **but misclassifies `just_limit` as CHART**. Recorded as a **KNOWN BOUND**, not hidden. |
| rc426 **F12b** | three-bucket correction | FRAME-FIXED (leak): `interval_vector`, `normal_order`, `prime_form`. FRAME-FREE: `just_limit`. FRAME-PARAMETRIC: `cyclic_mod_add`, `center_lift`, `lift_fibre`, `tempers_out`, `comma_of_chain`. |
| rc427 **G3b** | generator clause | **A second blind spot: an op that leaks its GENERATOR passes F12b.** The generator clause catches it. This finding SURVIVES V3 — it is independent of the forcing law V3 refuted. |

⚠️ The generator blind spot is real; the *op* proposed to fix it (`frame_scope`) is deferred (R19).
The classification stays hand-derived for now, and that is a known cost.

### 3.3 Sourcing tiers per tradition — **UNSOURCED stays UNSOURCED**

Tier ladder as defined verbatim in `_p7_chart_families_sourced_rc426.py`. All ten rows carry a tier;
`SECONDARY-OA` is defined with **0 instances**.

| # | Tradition | Family | Tier | Note |
|---|---|---|---|---|
| 1 | Byzantine neumes (psaltic) | DIFFERENTIAL | `VERIFIED-OA` | 72 dodekatemoria are **NOMINAL**; "Byzantine = 72-EDO" is an idealisation. System is **CONTEXTUALIZED**, pre-1814 layers **STENOGRAPHIC**. |
| 2 | Jianpu 简谱 | SCALE-DEGREE | `VERIFIED-OA` | ⚠️ **NOT a good example of "non-Western"** — Rousseau 1742 → Galin-Paris-Chevé → Mason (Meiji Japan) → China c.1905-12. Zhang Na PhD: metadata verified, **body NOT read**. |
| 3 | **Gongche 工尺譜** | SCALE-DEGREE | **`UNSOURCED`** | **NOTHING IS CLAIMED.** The previously cited source was checked directly and does not support the claim. Kept as an **EXPLICIT GAP** so the table cannot look complete. |
| 4 | Sargam (Hindustani + Carnatic) | SCALE-DEGREE | `VERIFIED-OA` | The 22-shruti question is a **LIVE scholarly DISAGREEMENT**, reported not resolved. "Movable" needs both halves. |
| 5 | **Arabic maqam / ajnas** | SCALE-DEGREE | **`EXPERT-WEB`** | 24-tone equal division is a **NOMENCLATURE**, not a realised tuning. The **"1932 Cairo Congress" date is WRONG/refuted**; the replacement is **PROVISIONAL**. al-Fārābī specifically IS sourced; the wider chain is SECONDARY at best. |
| 6 | Western staff notation | ABSOLUTE-POSITION | `VERIFIED-OA` | "Absolute" = absolute relative to a **DECLARED STANDARD** (Handel A=423, Mozart A=422). |
| 7 | **Jianzipu 減字譜 (guqin)** | INSTRUMENT-ACTION | **`VERIFIED-SELF`** | Strongest tier — PDF fetched + extracted in session. But pitch-as-output IS attested while the **STATEFULNESS rule is NOT** (0 hits across 417 KB). |
| 8 | Lute tablature | INSTRUMENT-ACTION | `VERIFIED-OA` | Dalitz & Crawford, Phoibos 2/2013: 167-185 |
| 9 | Guitar tablature | INSTRUMENT-ACTION | `VERIFIED-OA` | Wiggins & Kim, ISMIR 2019 (CC BY) |
| 10 | **Kepatihan (Javanese gamelan)** | DEGREE-FIXED / PITCH-FLOATING | **`CONTESTED`** | Two sourcing passes disagreed (VERIFIED-OA vs entirely UNSOURCED). Not independently re-checked. Marked CONTESTED rather than promoted or discarded. Only the **STRUCTURAL** claim is load-bearing. |

**Which family notates ACTION rather than pitch: `INSTRUMENT-ACTION`** (jianzipu, lute tab, guitar
tab). Verbatim: *"atoms_denote: an ACTION on an instrument; pitch is an OUTPUT"*,
`is_chart_of_interval_carrier: **false**`.

**TWO of five families are not charts of the pitch carrier**, not one — the second is
DEGREE-FIXED/PITCH-FLOATING (kepatihan). `n_charting_interval_carrier` = **3 of 5**. And the trap
is named outright: *"the two that resist are NOT the exotic ones — Western lute and guitar
tablature sit in the same bucket as jianzipu."*

Measured: action→pitch is **78 actions → 37 pitches**, total forward, **not injective backward**
(preimage histogram {1:10, 2:13, 3:14}).

⛔ **Vocabulary ban carried forward:** do **not** use "prescriptive/descriptive" as the axis. Seeger
1958 is verified but **PAYWALLED** (read via the 1977 reprint) and the Carnatic literature
**INVERTS** the term. Use **COMPLETE vs SKELETAL, applied PER DIMENSION**.

---

## 4. The directional-generator verdict

**BUILDABLE — accepted, exactly and closed-form, on the cyclic carrier.**

| Field | Value |
|---|---|
| Shape | `T_c(x) = mod_mul(x, c, n)` with `gcd(c, n) > 1` |
| Exact? | ✅ integers only — no limit, no norm, no resolvent, no operator semigroup on a Banach space |
| Carrier-native? | ✅ **YES** — it is ℤ/n's own multiplication, bottom-up from the carrier, not a cascade reverse-engineered toward a continuous target |
| Index (transient) | `index = max over shared primes p of ceil(v_p(n) / v_p(c))` |
| Eventual modulus | `n / g*` where `g* = gcd(c^index, n)` |
| Period | `cyclic_period(c mod (n/g*), n/g*)`, **with the `n/g* == 1` guard** |
| **What it destroys** | Per step: a **coset of `ker(T) = {x : c·x ≡ 0 mod n}`**, a subgroup of order `g = gcd(c, n)`. After `index` steps the total consumed order is `g*`, and the map is thereafter a **permutation of stride `g*`**. |

**Validation strength.** V-G4 wrote an independent enumeration oracle and ran the closed form over
every `(n, c)` with `2 ≤ n ≤ 60`, `0 ≤ c < n` — **1,829 cells vs the reported 37**. Disagreements:
index 0, period 0, eventual size 0. Index histogram `{0:1101, 1:509, 2:141, 3:54, 4:16, 5:8}`.
**Sets, not counts:** the eventual image was compared as a SET against predicted `g*·ℤ/n` on all
1,829 cells — **0 membership mismatches**. Negative controls are non-vacuous at scale (ceiling-free
control fails 141 cells; floor-variant fails 198).

**The gap is real** (S4, re-measured): `cyclic_period(6, 12)` raises
`gcd != 1; a not in (Z/nZ)*`, and `cyclic_period(c, 1)` raises `requires n >= 2`. Both guards fire.

### The tension G4 named honestly — and it is the interesting part

srmech's shipped doctrine for lossy ops is **CARRY THE COMPLEMENT** (`lossy_projection_record`:
*"recovery is EXACT because the complement is carried"*; `lift_fibre` enumerates what a shadow does
not determine). Applied to an arrow, that doctrine **ANNIHILATES it**: the moment the op returns
the coset index, the map is invertible and there is no arrow left.

Measured: on all 37 cells the fibres are uniform of size `g`, `ker T` is a subgroup, and
`(image, coset index)` reconstructs the input on **37/37** — the paired map is a **bijection**.

> **LEGIBILITY AND IRREVERSIBILITY ARE IN TENSION and cannot both be maximised.**

**Resolution, and it is a contract requirement:** report the **SHAPE and ORDER** of what was
consumed, never the element. *"This step consumed a coset of an order-g subgroup"* is legible and
still irreversible. *"This step consumed coset #3"* is legible and reversible.

### Not decorative

`T_c` is genuinely non-injective (image 12 → 2 → 1 on ℤ/12 with c=6). The contrast cases are
shipped: `cd_project` **RAISES** rather than truncating (a partial bijection — measured, it
succeeds on exactly 3 of 9 and raises on 6), and `propagate` accepts `z = −1` and round-trips at
**1.5e-15**, i.e. srmech's own EPH surface is a **GROUP, not a semigroup**.

---

## 5. Registry delta and ripple surfaces

### 5.1 Projected count

| | Ops | Registry |
|---|---|---|
| rc425 (`origin/main`) | — | **649** |
| + ops 1–6 | +6 | 655 |
| + op 7 `dihedral_group` (conditional) | +1 | **656** |
| ops 8–9 (parameter extensions) | +0 | 656 |

**Projected after rc427: 656** (or **655** if `dihedral_group` slips with op 3).

ABI stays **14** — adding symbols does not bump ABI; only a wire-format change to an exported
function does.

### 5.2 Ripple surfaces that WILL move, and why

All named observers verified present on the fast manifest (S8: 41 targets in
`docs/srmech/python/tools/ripple_gates.txt`).

| # | Surface / gate | Why it moves |
|---|---|---|
| 1 | **`tests/test_search_glyph_tokenizer_rc416.py`** — the introspect **search-corpus content-address** | The corpus is BUILT FROM ToolEntry prose. 7 new entries + 2 edited parameter blurbs (`unit_loop`, `loop_invariants`) move it. **It has moved four rcs running (rc416/419/420/421)**; on rc421 `ripple_check` went green while four native cells + pure shard 6 went red, purely because it was unlisted. It is listed now — run it. |
| 2 | `tests/test_registry_smoke_rc127.py`, `test_rc15_describe_resolve.py`, `test_carrier_contract_rc120.py` | Count pins on `describe()["tools"]["total"]`: 649 → 656. |
| 3 | `srmech/introspect/_tool_docs.py`, `_tool_docs_curated.py`, `_c_claims.py` (**generated**) | Regenerated from the registry; new entries + edited prose. |
| 4 | **`c/src/srmech_tool_registry.c`** — the compiled-in C registry | New entries. ⚠️ The compiled registry is the **LIVE path on a native host** — a Python-only change is a silent no-op on the actually-advertised catalog until this is regenerated **and libsrmech rebuilt**. |
| 5 | `tests/test_rosetta_transitive_standalone.py`, `test_rosetta_completeness.py` | The **Rosetta table**: standalone-C reachability + classification completeness for every new op. |
| 6 | `tests/test_mcp.py::test_all_param_types_json_coercible` and `::test_schema_signature_alignment_no_drift` | **New param TYPES**: `Sequence[Sequence[int]]` Cayley tables, and a required `domain: str`. This is the rc273/rc328 class — a novel param type with no `_PARAM_COERCERS` handler. **§1.3 exists because of this axis.** |
| 7 | `tests/test_namespace_prefix_decode_aware_rc361.py` | Adding cascade ops bumps the `srmech.cascade` DECODED-channel population — invisible to a text grep. rc387 had to run this manually. |
| 8 | `tests/test_composes_grain_rc412.py`, `test_composes_population_rc423.py` | Every new op declares `composes`; the population ratchet carries `CEIL_UNADJUDICATED`, which a new op with ≥2 call edges and no traced order trips immediately. All seven qualify. |
| 9 | `tests/test_preserves_taxonomy_rc423.py` | Strict-zero: every new `preserves` string must classify into a declared kind, keyed by the FULL sentence. |
| 10 | `tests/test_worked_examples_strict_zero_rc353.py`, `_execute_rc354.py`, `test_tool_example_input_schema_rc355.py` | Every new ToolEntry needs an **executable** worked example whose `example["input"]` validates as kwargs against its own rendered inputSchema. |
| 11 | `tests/test_readme_currency_rc419.py` | The README (= the PyPI long-description) names the **registry cardinal** and `native_version`. Both move. rc422 went green on the full manifest while the README still said 598 (live 605). |
| 12 | `tests/test_registry_completeness_rc416.py` | Registering ops is precisely what invalidates its allowlist rows — 40 rows stopped being gaps at rc425 for exactly this reason. |
| 13 | `tests/test_adr_citation_integrity_rc415.py` | New ToolEntries insert lines into `c/include/srmech.h` and `test_composes_grain_rc412.py`, moving `path:line` ADR citations. rc425 moved 12 and took 5 over `CEIL_TOKEN_EVIDENCE` — **two full green ripple runs still shipped a CI red.** |
| 14 | `tests/test_ref_notation_emitted_rc348.py` | New docstrings/ToolEntry prose ship inside the wheel. Task IDs must be `` `#T1130` ``, never bare. |
| 15 | `tests/test_selfhosting_import_ban.py` | New test files must not reach for stdlib `fractions`/`math`/`decimal`/numpy. This cost rc386 a full CI-red round. |
| 16 | `tests/test_jpl_audit.py` | Only if C peers ship. Violations go **DOWN, never up**. |
| 17 | `tools/ripple_gates.txt` itself | Only if a new gate **family** is added (e.g. a `finite_group` module gate). |

### 5.3 The gate that will NOT be on the fast sweep — and it is the dangerous one

`tests/test_immolation.py::test_advertised_return_type_is_honest` is **deliberately excluded**
(measured >10 min even as a single node; documented in `ripple_gates.txt`). It is the gate that
catches a `returns=` that lies — and **seven new ops all returning `Dict[str, Any]` is exactly its
target**. rc425 shipped six ops advertising `list` and returning `tuple`.

**Mitigation the manifest itself prescribes:** execute the contract when authoring each `returns=`.
rc425 measured all 47 signal_processing entries through the gate's own helpers in ~10 s once the
population was imported. Do that, per op, at authoring time.

---

## 6. All NULLs, classified

**REFUTED** = the hypothesis was tested and failed. **BOUNDED** = a real limit was found, not a
refutation. **EMPTY** = measured absence. **UNSUPPORTED** = not testable at the tier attempted.

| ID | Null | Class | Detail |
|---|---|---|---|
| S1 | 13/13 build candidates absent from registry, prose, `__all__`s, TOMLs, notes | **EMPTY** | Measured absence — the intended result. |
| FA1 | No order-12 or order-24 group ships | **EMPTY** | `unit_loop` gives {4,8,16,32}; `group_algebra_table` raises on 3/5/12/24. |
| FA2 | No public transposition/inversion op | **EMPTY** | `srmech.music.__all__` = 15, `relations.__all__` = 9; 0 word-part hits. |
| P1 | No carrier or op names a NOTATION object | **EMPTY** | 0/29 carriers, 0/649 ops (0/612 at rc424 — the load-bearing result is unchanged). |
| G4-P | No semigroup/monoid/index op ships | **EMPTY** | 1 homograph (`signal_processing.farrow`); 0 `def` hits. |
| FA3 | "The composition-order convention is a structural decision" | **REFUTED** | S5: the two conventions are **ISOMORPHIC** (576/576 via `x → x⁻¹`); the 360-cell diff is `order² − commuting`; the downstream split is convention-INDEPENDENT. |
| G1a | "Alphabet size is a theorem of the declared generator, 0 failures / 188" | **REFUTED** | 6274/6274 alphabet sizes pass both predicates; 6086 with `a ≠ g⁻¹`. Instrument cannot return otherwise. |
| G2-lead | "Chiral reversal succeeds on EXACTLY the forward-success set, 10/10 rows" | **REFUTED as a measurement** | Entailed by the anti-automorphism law, which is TOTAL on all five carriers chosen. S7: on an order-5 loop where the law fails 13/25, the sets split by **12 each way**. The claim is a **SCOPE statement**, not a finding. |
| G4-M6 | "Dedekind dichotomy holds on finite carriers, 39/39" | **REFUTED as a control** | A literal tautology — the script binds `injective` and `surjective` to the *same expression*. Even written correctly it cannot fail (finite-set theorem). The mathematical inference it supports is TRUE; the 39/39 is not evidence for it. |
| F6 | "Can `oct_torsor_*` host a pitch-interval object?" | **REFUTED** | 0 of 7 candidates hostable. |
| F14 | "Charts agree on intervals, 6/6" | **REFUTED as an instrument** | A *corrupted* chart also scores 1225/1225. `instrument_valid: false`. Corrected as F16b (30/35, rejects). |
| S6-mine | My first FA4 instrument (prime_form constant on the orbit) | **REFUTED as an instrument** | Returned 1507/1507 on **both** arms — constancy on a set implies constancy on its subsets. Replaced with a **partition** comparison: 79 blocks vs 79 (equal), control 128 ≠ 79 (separates). *My defect, recorded not hidden.* |
| FC3 | "The three Moufang identities fail on pairwise-disjoint halves" | **BOUNDED** | Reproduces exactly for G1's spellings — but an independent textbook-equivalent triple makes two coincide (symmetric difference 0). **Spelling-dependent.** The weaker headline "counts are not sets" SURVIVES. |
| NC3 | "Feeding a wrong inverse degrades the census, 10/10" | **BOUNDED** | **Vacuous on 4 of 8 rows** (ℤ/7, ℤ/12 are already total, so nothing could degrade). Informative only on the non-abelian rows, where it is genuinely decisive. |
| G4-cl(d) | "The clef atlas is a principal ℤ-bundle, 25/25 origins" | **BOUNDED** | Tautological **by search window**: translations sweep ±2W while origins sweep ±W. Narrow to ±6 and it gives 283/625, `False`. The conclusion is correct and the octonion side IS measured; only the clef side was assumed. |
| F5b | Across-line frame action | **BOUNDED** | 0/7 per unit with a 7/7 identity control — a real null with a working positive control. |
| F3.2 | ℤ³ 5-limit window is NOT-A-TORSOR | **BOUNDED** | A **windowing artifact**: every miss is a 0-preimage, no multiplicity > 1; the closed (ℤ/5)³ stand-in IS a torsor. |
| FKC1 | "Invert-then-flip == flip-then-invert, 100%" | **EMPTY** | A theorem (a pointwise map commutes with a position permutation). **G2 classified this correctly itself** — the one place the stream applied the standard unprompted. |
| FG1 | Gustafson 5/8 bound | **UNSUPPORTED as a citation** | arXiv:1001.4856 (Hofmann & Russo — title/authors/affiliations verified) contains **no 5/8 bound and no mention of Gustafson**. Classified DERIVED-AND-MEASURED instead. Honest. |
| Baez | "Baez arXiv:math/0105155 §2 covers Moufang" | **UNSUPPORTED — and this is a LIVE shipped defect** | Verified: the paper IS *The Octonions*, Baez, Bull. AMS 39:145-205 (2002). The **abstract contains no "Moufang"**; rc426 recorded that the paper does not contain the string at all and re-sourced to Wikipedia + Schafer 1966. **The citation is asserted on five shipped ops** at `cayley_dickson.py:2178`. See §7 A5. |
| 𝕆 anti-aut | "(ab)⁻¹ = b⁻¹a⁻¹ on 𝕆" | **UNSUPPORTED as a citation / MEASURED as fact** | 256/256, but NOT independently verified from an accessible source. |
| Brief-1 | "0 of 649 ops are semigroup-not-group" | **UNSUPPORTED** | **No registry-wide census exists.** `649` appears once in `reversal_is_not_rewind_rc426.ndjson`, as an environment stamp. The census covered **11 hand-picked surfaces**, 1 of which is semigroup-not-group. And it is **refuted by a shipped op** — `q8_project_v4` is a non-injective idempotent self-map with a C peer. |
| Burnside | Class-equation attribution | **UNSUPPORTED at theorem-number granularity** | Verified as an identity; Rotman was not opened. |
| F24b | Relation to the active-carrier thread | **UNSUPPORTED** | `claim_status: "OPEN QUESTION, deliberately not resolved"`. |
| F15 | Registry-order blindness, 120/120 | **BOUNDED (WEAK)** | Recorded as a weak check by construction, not counted as strong evidence. |
| F12 | Leak predicate | **BOUNDED** | Catches the 3 real leaks but misfires on `just_limit`; a **KNOWN BOUND** of the L1 clause. Corrected as F12b. |

---

## 7. Everything that turned out wrong

Merged from the streams' `wrong_in_brief` and the verifiers' `refuted`, plus my own.

### A. Wrong in the BRIEF / ground truth

| # | Claim | Truth |
|---|---|---|
| A1 | "0 of 649 ops are semigroup-not-group" | No registry-wide census was ever run. 11 hand-picked surfaces, 1 positive. Refuted outright by `q8_project_v4` (shipped, C-peered). |
| A2 | "the only proper monoid found in the whole tree" | Same 11-surface scope. Overstated. |
| A3 | "0 of 612 ops named a notation object" | Correct **at rc424**; live count is **0 of 649**. Load-bearing result unchanged. |
| A4 | "Bare-reversal rate = the commuting probability k(G)/\|G\|" | True on the four **GROUPS**; **FALSE at the O16 loop** (43/64 vs 9/16). It is a group theorem. |
| A5 | "Baez arXiv:math/0105155 §2" cited for **Moufang** on five shipped ops | The abstract contains no "Moufang"; rc426 recorded the string is absent from the paper. **A live unverified attestation inside the shipped wheel.** |
| A6 | "Lewin's GIS IS a torsor" | The artifact measures only *a stated axiom pair* and flags the Lewin attribution as a **separate citation question**. Do not read it as sourced. |
| A7 | `docs/srmech/notes/` holds ~1,370 files | 1,391 at the baseline read, **1,405+** now. It moves every session — measure it. |
| A8 | `spin8_center` absent (`v4_so8_bridge_canonicity_rc422`) | **Shipped in rc422 itself.** True at rc421, **stale at rc425**. |
| A9 | The O16 `abelian_bare_equals_chiral` verdict string | The prose says bare and chiral "SEPARATE" while the **same row** records `bare_equals_chiral: true` (2752 = 2752). The verdict string is templated off the `abelian` flag, not the measured equality. The correct reading is in `cell_set_overlap`: SET false, intersection 1408. **The counts-are-not-sets trap, inside the control meant to guard against it.** |

### B. Wrong in a STREAM's claims

| # | Stream | Claim | Truth |
|---|---|---|---|
| B1 | G1 | FA3 (i): "360 of 576 cells differ" is evidence the convention is a real decision | `360 == 576 − 216 == order² − commuting pairs`. R is the transpose of L. Restates "non-abelian". A nonzero census is GAUGE. |
| B2 | G1 | FA3 (ii): the 13824/5184 downstream split distinguishes the conventions | **Convention-INDEPENDENT** — identical on both tables. G1's own code passes only `L` to `axiom_a_counts`. The reversal read "could not fire" and a different quantity was substituted under the original falsifier's name. |
| B3 | G1 | The convention makes it "a different GROUP OBJECT" | **ISOMORPHIC** via `x → x⁻¹` (S5: 576/576, identical class sizes). It is a **labelling** decision — still legitimate grounds for a required parameter, but the spec must say so. |
| B4 | G1 | FC3: "a count-only or boolean read erases the failing set completely" | True of `is_moufang`, **false of the shipped surface** — `moufang_residue` already gives per-triple resolution (S2: 1176/4096 at dim 16). |
| B5 | G1 | FC3: the three Moufang identities fail on pairwise-disjoint halves | **Spelling-dependent.** An equivalent triple makes two coincide exactly. |
| B6 | G1 | `unit_loop` `table=` extension is "Class A — content-addressed by its table" | **Forced to fit.** Class A is content-addressing (SHA-256); no hash is computed anywhere. A `table=` parameter carries **no new class** — it is carrier plumbing. |
| B7 | G1 | `dihedral_group` prose: "C (orientation reversal), with the reflection as a K pin-slot" | **Inverted vs its own code.** CLAUDE.md fixes sign-FLIP as **K** and sign RE-application as **C** — which is exactly what its `_class_k_negate` does. Only the label is swapped. |
| B8 | G1 | `conjugacy_census` prior-art record | Never names `loop_invariants` — its **nearest shipped neighbour** is missing from its own prior-art field. |
| B9 | G2 | LEAD: "chiral reversal succeeds on exactly the forward set, 10/10 rows" — elevated as correcting the brief *upward* | **A corollary, not a measurement.** Entailed by the anti-automorphism law, total on all five carriers chosen. Confirmed by counterexample (S7). Must ship as a **scope** statement. |
| B10 | G2 | Op 1 `chiral_reversal` clears the registration bar | It does not, and the spec **quotes that very bar against a different op in the same document**. One shipped call, zero decisions. |
| B11 | G2 | NC3 passes 10/10 | **Vacuous on 4 of 8 rows.** G2 applied exactly this scoping honestly to NC5 and should have here. |
| B12 | G2 | "No package source touched: git status is clean" | git reports **315 modified files**. Substance is right — pure CRLF churn, 186,655 insertions vs 186,655 deletions, `--ignore-all-space` empty — but a builder opens a tree with 315 spurious modifications. **A live hazard** (standing memory: the Edit tool rewrites whole files to CRLF and this breaks `.sh` under WSL). |
| B13 | G2 | `CELL_DOC` labels P2 as `[BARE]` and Q2 as `[CHIRAL]` | Correct for only **one of the two readings**. On the left reading the cell labelled `[BARE]` IS the forward law. If the eight-cell shape ships, these become **docstring prose inside the wheel**. |
| B14 | G3 | G1a: "alphabet size is a theorem of the generator, 0 failures / 188" | **Vacuous** — the failure branch is unreachable. 6274/6274 pass; 6086 with `a ≠ g⁻¹`. And the conclusion is **false**: at (12, 7) the alphabet 5 also passes — the pentatonic scale. Choosing 7 over 5 is a Class-C orientation decision. |
| B15 | G3 | `action_lattice_read` returns a lattice verdict | **Silent wrong answer** off-anchor: translate the tuning and it flips to `False`/`None` on the same lattice. Class "I then E" unsupported — **0 modular calls**. |
| B16 | G3 | `chart_transition` is "the load-bearing op of the whole translator" | Its derivation **IS** the arithmetic the same spec rejects as `key_signature`. Only the per-symbol certification is genuinely new — a much narrower scope. |
| B17 | G3 | G4(d): "the clef atlas is a principal ℤ-bundle, 25/25, stabiliser trivial" | **Tautological by search window.** Narrow the window and it returns 283/625. Only one of the two sides was measured. |
| B18 | G3 | Its own prior-art grep pattern | **Omitted `fibre` and `lattice`** — narrower than the pattern its own rejected-op argument relies on. V3 ran the wider one; the absence claims still hold. |
| B19 | G4 | M6: "Dedekind dichotomy, 39/39" as a negative control | A **literal tautology** — both predicates bound to the same expression. A false-green seam. |
| B20 | G4 | Op 2 "earns its place by consuming a table `unit_loop` already produces" | **Measurably vacuous.** A loop's Cayley table is a **Latin square by axiom** (`unit_loop`'s own docstring says so; measured 4/4, 8/8, 16/16, 32/32). `finite_semiflow` on any `unit_loop` table can only ever return index 0. The one table it names is the one class where it is guaranteed to find no arrow. |
| B21 | G4 | Op 1 prior-art: "0 op names (substring noise only)" | **Misclassified.** `left_mult_is_invertible` / `left_mult_kernel` are not accidents — they are srmech's shipped surface for this exact question, with the irreversibility prose already in the ToolEntry. The op is still genuinely absent (neither iterates); the **summary named the wrong neighbours**, and its own NDJSON handled it correctly. |
| B22 | G4 | "19 of 37 cells with gcd > 1 have index ≥ 2" | **Denominator misstatement** — there are **24** non-unit cells, not 37. 19 of 24 non-units (= 19 of 37 total). The NDJSON is correct; the prose is not. |
| B23 | G4 | `period = cyclic_period(c mod (n/g*), n/g*)` as the stated method | **Raises on its own headline example.** Every nilpotent multiplier has `n/g* == 1`, including `mod_mul_arrow(2, 64)`. The script has the guard; **the spec handed to a builder omits it** (S4 confirms both refusals fire). |
| B24 | G4 | Op 1 class assignment **K** | The shipped precedent for the same object (`left_mult_kernel`) is **Class L**. Recommend **I then L** and reconcile explicitly. |

### C. Wrong in a VERIFIER's claims

| # | Claim | Truth |
|---|---|---|
| C1 | V2 predicted NC3's O16 rows would be count-only-decided | **Not confirmed.** The SET agrees with the count on every row (8/8), so NC3's O16 conclusion is set-confirmable after all. **V2 recorded its own miss** — correct behaviour. Only the vacuity finding stands. |
| C2 | V-G4's first `cd_project` probe used the wrong arity | **Its own harness defect**, recorded and corrected: 3 succeed / 6 raise of 9. |
| C3 | V-G4 cited `music/relations.py:54-63` | Actual span ~57-59. Immaterial, but the quote is verbatim-correct. |

### D. Wrong in MY OWN synthesis pass — recorded, not hidden

| # | Defect | Correction |
|---|---|---|
| D1 | First S2 probe passed **basis indices** to `moufang_residue`, which takes **elements**. Raised `TypeError`. | My harness defect, not the op's — the signature is element-wise by design. Rebuilt with one-hot exact-ℚ basis vectors. |
| D2 | First S5/S6 sign handling computed `0 - x` and fed it to `cyclic_mod_add`, which **correctly refused** (`a must be non-negative; got -1`). | A guard doing its job, not an obstacle. Replaced with `_cyclic_negate`: Class-K pin-slot for the magnitude, then Class-C re-application **inside** the cyclic lane. Never `abs()`. |
| D3 | First S6 instrument tested whether `prime_form` is **constant on the orbit**, with rotations-only as the control. Returned **1507/1507 on both arms**. | **Vacuous by construction** — constancy on a set implies constancy on its subsets. An instrument that cannot return otherwise is not a measurement. Replaced with a **partition** comparison: 79 = 79 (equal), control 128 ≠ 79 (separates). |

---

## 8. Build order, and what rc427 should NOT attempt

### 8.1 Recommended order

| Order | Op | One-line reason |
|---|---|---|
| **1** | `mod_mul_arrow` | Highest confidence in the round — a closed form that survived a **49× wider grid** (1,829 cells, 0 disagreements) with set-level image checks and non-vacuous controls; fills a gap the shipped `cyclic_period` provably refuses. |
| **2** | `finite_semiflow` | The tabulated peer of op 1, sharing its index/period core — build together or the core gets written twice. **Rewrite the rationale first** (B20). |
| **3** | `conjugacy_census` (merged) | The strongest *why*: an unguarded op emits **144 vs 88** and **544 vs 184**, silently. Ship the guard before anything consumes the class equation. |
| **4** | `unit_loop` + `loop_invariants` `table=` | +0 registry rows, small, and it unblocks op 5 and op 6 from having to hand-roll the signed loop through `table_product` — as G1's own note had to. |
| **5** | `reversal_law_census` | The mandatory counts-are-not-sets instrument. Needs op 4's `table=` and the §1.3 table-based signature. |
| **6** | `anti_automorphism_witnesses` | Small, and it is the n² mechanism that makes op 5's n³ result interpretable. Re-base onto `chiral_flip` (op R1 is rejected). |
| **7** | `law_census` | Largest cost, narrowest surviving justification (8 laws, not 11). Needs its spellings pinned and `domain` required. Safe to slip to rc428. |
| **8** | `dihedral_group` | **CONDITIONAL on #3.** Without `conjugacy_census` it has no caller. Justification rewritten to FA1 + "the carrier the censuses need". |

### 8.2 What rc427 should NOT attempt

| Do not | Reason |
|---|---|
| **Any of the four G3 notation ops** | Verifier verdict **UNSOUND**, `instrument_can_return_otherwise: false`. The forcing law forced nothing; one op returns a **silent wrong answer** off-anchor; one op's derivation is arithmetic the same spec rejects. |
| **`frame_scope`** | Not refuted — but a ToolEntry field across 649 entries + a swept ratchet is an **introspect** rc, not a math-op rc. Defer with the reasoning intact (R19). |
| **`chiral_reversal`** | One shipped call, zero decisions. Ship a **worked example** on `chiral_flip` instead — the remedy `music/relations.py` itself chose. |
| **Build G1's and G2's censuses separately** | They are the same op (§1.1). Building both ships duplicate registry surface. |
| **Any signature with a REQUIRED callable** | 0 of 12 shipped callable params are required; the contract publishes JSON-schema null (§1.3). |
| **A registry-wide semigroup census presented as pre-existing** | It has never been run (§6, Brief-1). If rc427 wants the claim, it must **run** it. |
| **Re-cite Baez arXiv:math/0105155 for Moufang** | The string is absent from the paper. Five shipped ops carry this. **Fixing it is a separate, higher-priority prose task** — it is a false attestation already inside the wheel. |
| **Assume a green `ripple_check` means a green CI** | rc421, rc422 and rc425 each shipped a CI red *after* a green sweep. Ops here move ≥17 surfaces (§5.2), and the `returns=`-honesty gate is **CI-only** (§5.3). |
| **Ship on one branch** | No branch holds all eight streams (§0). |
| **Anything CAD / GPU / continuum** | Standing ban. Everything above is exact integers and exact ℚ on cyclic and Cayley–Dickson carriers. |

---

## 9. One-paragraph verdict

**rc427 is a six-to-eight op arithmetic rc, not a notation rc.** The ARROW stream produced the
round's best result — a closed-form directional generator on ℤ/n that survived a 49× wider grid at
set level with working negative controls. The OPGAPS and REVERSAL streams each produced a real
instrument (the class-equation guard, the counts-are-not-sets census) whose *justifications* needed
correcting more than their *specifications* did — and they independently proposed **the same op**,
which only a synthesis pass could see. The NOTATION stream did not survive verification: its
headline law was vacuous and one of its ops returns a silent wrong answer outside its worked
example. Three findings had no owning stream and are recorded here for the first time: the
**op collision** between G1 and G2 (§1.1), the **required-callable contract violation** in both G2
census signatures (§1.3), and the fact that **no single branch holds all eight streams** (§0).
