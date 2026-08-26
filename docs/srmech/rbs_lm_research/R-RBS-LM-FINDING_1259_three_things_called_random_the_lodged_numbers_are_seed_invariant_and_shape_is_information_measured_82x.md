# F1259 — we call **three different things "random"** and only one of them is; the lodged conservation numbers are **seed-INVARIANT by construction** (8 seeds, byte-identical section-counts) so nothing shipped was a draw; and the user's "shape is also information" is **measurable at 82×** — a constructed lattice compresses 8192 B → **32 B** (it IS its rule) while the random coupling object sits at the entropy floor, 8192 B → 2612 B. A random-seeded shape **cannot be bit-serialized**: the seed is a reproducibility token, not a portable serialization, and it constitutes an **undeclared version pin** on srmech's internal RNG.

**User (2026-07-20):** *"what if what we call rng is part of our op(x)operand(x)responsion and should not be random? … run the seed-ensemble on a lodged result first and lodge the language fix. the exactly orthogonal idea rode that our early HDC object was a resonant lattice object whose shape was also information, unlike random seeded shape that cannot be bit serialized."*

Harness `R-RBS-LM-SEEDENSEMBLE_…py`, srmech **0.9.0rc288**.

## THE LANGUAGE FIX — three regimes, one word
Audited across `rbs_lm_research/` + `siona/`:

| call pattern | uses | what it actually is | proposed name |
|---|---|---|---|
| `klein4_random(D, seed=sha256(w))`, `seed=b`, `seed=digest(...)` | ~47 | a **deterministic Class-A content-address expanded to D** — a PRF keyed by content. Same word → same vector on every machine, forever. Verified: similarity exactly `1.0`. | **DERIVED** |
| `klein4_random(D, seed=1080 / 4242 / 0)` | ~54 | **one sample from an undeclared ensemble**; an unattested constant (Class-C in the F228 audit) | **DRAWN** |
| `klein4_random(D, rng)` | 52 | a live `Generator` — **not reproducible** unless the caller seeded it | **STOCHASTIC** |

**Only the third is random.** The first is not random *at all* and is load-bearing — it is what makes the vocabulary reproducible, and it is already exactly the user's "part of op(x)operand(x)responsion." Calling all three "random" hides the distinction at the call site, which is why the question could not be answered by reading the code.

**The discipline that follows:** DERIVED belongs in a cascade. DRAWN is a magic number and should be replaced by a construction. STOCHASTIC in a cascade is a defect — 52 sites are reproducible only by luck, and any that reach a lodged number make it unreproducible.

## A — the disclosure question: the lodged numbers were never a draw
8 widely-spread seeds (`1080 + k·7919`), 3,000 documents, the real `plasmid_extract → conserved_core` pipeline:

| quantity | across 8 seeds |
|---|---|
| vocab | **1714** — INVARIANT |
| derived `k` | **1127** — INVARIANT |
| `n_core` | **69** — INVARIANT |
| `n_sections` | **3000** — INVARIANT |
| full `section_count` digest | **identical** — INVARIANT |

**And the reason is structural, not lucky:** `section_count` is *document frequency* — an integer accumulator over tokens. The coupling object never enters it. So **F1254 / F1256 / F1257's headline results (k=10,714, core=170, 94/94) do not depend on the magic seed.** They were never samples. This is a clean negative on the disclosure worry, and it is worth stating in exactly those terms: the numbers are safe *because the pipeline's conserved-core read is couple-free*, not because 1080 was a good seed.

**Scope of that reassurance, stated honestly:** it covers the conservation/counting results. It does **not** cover anything reading the HDC turns themselves (similarity, recall, EPH harvest) — those *do* consume the coupling object and remain undisclosed ensembles. Any lodged recall/similarity number still needs its own seed-ensemble before it can be quoted as a constant.

## B — "shape is also information", measured at 82×
| object (D=8192, Klein-4) | raw | zlib | ratio |
|---|---|---|---|
| **random** `klein4_random(seed=1080)` | 8192 B | **2612 B** | 0.319 |
| **constructed lattice** (rule-generated from D alone) | 8192 B | **32 B** | **0.004** |

The Klein-4 alphabet is 2 bits in a byte, so the entropy floor is 0.25 — **the random object compresses to 0.319, essentially at that floor. It is incompressible.** The lattice compresses **82× further**, to 32 bytes, because *it is its rule*.

That is the user's claim made quantitative: **a shape that compresses HAS a rule, and the rule is the information; an incompressible shape carries nothing but itself.** The constructed object can be shipped as a few bytes of construction; the random one can only be shipped as all D values.

## C — the serialization dependency: the seed is not a serialization
`klein4_random(64, seed=1080)` → `[3,2,0,1,3,1,3,2,…]`. Reproducible **within this srmech build**. But the mapping `(D, seed) → vector` is defined by **srmech's internal RNG**, not by any attested rule. Consequences:

1. It is **not derivable by an outside party** from `(D, seed)` — a reader cannot reconstruct our vectors from the published parameters, only by running our exact srmech version.
2. It is **not pinned by `GENOME_FORMAT_VERSION`.** The container version tracks byte layout; the RNG is not part of it. **Any change to srmech's RNG silently re-points every content-seeded vector, and every stored genome decodes to different content with no version signal** — precisely the failure class rc287's ABI-bump reasoning identified ("a removal produces no symptom at all").
3. So the seed is a **reproducibility token, not a portable serialization.** This is the concrete form of "cannot be bit serialized."

A constructed basis has none of these: derivable from D alone, by anyone, forever, with no version pin.

## The consequence that matters most — melange (#263)
Two genomes built independently today each carry their own DRAWN basis, so the bridge `C` in `[[L_A,C],[C^T,L_B]]` couples across **unshared frames**. With a construction derived from D alone, separately-built genomes share the basis **by construction**, and cross-genome co-excitation becomes exact rather than best-effort. That moves melange from "hope the bases align" to "they are the same basis" — and it is the strongest practical argument for the change, stronger than the sidelobe argument.

## Honest bound on the orthogonality half
Exact orthogonality is only available while vocabulary ≤ D. At 1.1 M types against D=8192 quasi-orthogonality is **forced**. So the achievable claim is not "exactly orthogonal" but **"designed family vs drawn family"**: the Welch bound is the floor on worst-case cross-correlation for M vectors in D dimensions; random families approach it *in expectation with variance* (measured: mean pinned at 1/4 by Klein-4 algebra, per-pair sidelobe scattering ±0.04, seed-dependent), while designed families (Gold / Kasami / Zadoff-Chu / Legendre) **hit it exactly**. The mean is algebra and owes nothing to the RNG; **the sidelobe is the only thing randomness contributes, and it is error.**

## Verdict / next
The language fix is the deliverable: **DERIVED / DRAWN / STOCHASTIC are three different operations and only one is random.** The lodged conservation numbers are safe and now demonstrably so. "Shape is information" is real and 82× measurable, and the serialization dependency is a genuine undeclared version pin. **NEXT:** (1) the designed-family-vs-drawn sidelobe head-to-head at matched (M, D) against the Welch bound; (2) seed-ensemble any lodged *similarity/recall* number, which this run does **not** clear; (3) audit the 52 STOCHASTIC sites for reachability into lodged results.

Composes **F1254/F1256/F1257** (the lodged results, cleared for seed-dependence), **F1258**, **F1205/#263** (melange — the load-bearing consequence), `[[feedback_read_independent_structure_check_first]]` (the intrinsic Gram/sidelobe read came before any recall number), `[[feedback_persist_genome_native_not_loose_json]]` (serialization discipline), the **F228 no-magic-numbers audit** (DRAWN is Class-C; a construction is Class-A), `[[feedback_stay_rational_collapse_only_at_display]]`, #231/PKG-3.
