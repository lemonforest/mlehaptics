# ADR-0009: srmech is a multi-implementation codebase — the capability is the invariant, each implementation is a coherency projection

**Status:** ✅ Accepted — **standing policy** (governs every rc, every op, every review).
**Clauses:** unaudited.
**Date:** 2026-07-19.
**Authors:** Steven Kirkland + Claude Opus 4.8.
**Supersedes:** none.
**Superseded-by:** none.
**Amends:** **ADR-0003** (C-host-standalone — never assume a Python environment). ADR-0003 stays
in force in full; this ADR reframes the relationship its clause §2.6 describes and adds the
governance that made ADR-0003 unenforceable in practice. See §7 for the amend-not-supersede
rationale.
**Motivated by:** `docs/srmech/notes/c_host_parity_audit_rc273.md`.

---

## 1. Context — a correct principle that kept failing

ADR-0003 (2026-07-16) already says everything a reader would need: the C library is
first-class, every composite mirrors, orchestrators get their own entry point, delivery is
same-rc. It is right, it is Accepted, it is standing policy — and in the three days after it
was accepted, four capabilities shipped through review without a C implementation while
carrying language asserting they had one.

A principle that correct, failing that reliably, is not failing because people forgot it. It is
failing because the surrounding structure — vocabulary, taxonomy, tests — encodes the opposite
of what it says, and the structure wins. This ADR records the diagnosis, because an ADR that
only re-asserts ADR-0003 louder will produce the same result.

### 1.1 The default that generates the drift

The unstated default is: **Python is the implementation; C accelerates the hot parts.**

Under that default a missing C entry point is an **optimization gap, not a correctness gap** —
and an optimization gap is a legitimate thing to defer. That is why every individual deferral
below passed review while reading as reasonable. Each one is locally plausible; the sum is a
systemic hole in a shipped deliverable.

### 1.2 Observed instances (verified against the tree)

| rc | Capability | The claim made | What was actually true |
|----|-----------|----------------|------------------------|
| rc262 | `integrate` | docstring asserted "a C-only host integrates identically … region byte-offsets in the manifest" | the op ran on an in-memory strand with **no manifest at integrate-time**; the boundary-scan → locus → splice orchestration was Python-only. Refuted by the rc273 audit §G4; closed by rc276. |
| rc270 | `mint_strand` | "byte-identical whether the cap came from C or pure Python" | true of the **cap**, not of the **op** — the glue (data-turn scan → metacentric midpoint → single-block insert) was Python-only. Closed by rc277. |
| rc273 | `amplify` / `copy_number_of` | the C test proved reader-transparency and its comment concluded the additive field "needs no format bump … and no C change" | reader-transparency ≠ implementation parity. There is still **no C path to write or read the copy-number**. `grep srmech_genome_amplify c/include/srmech.h` → 0 hits, at rc280. **Still open.** |
| rc280 | `section_counts` | **claimed nothing false** — the CHANGELOG and header state the ceiling, the corpus figure, and the non-reentrancy plainly | the compiled implementation declines above ~11k sections against a 240,881-section corpus and the Python one runs. A *disclosed* missing capability is still a missing capability. Tracked as #899. **Still open.** Detailed below — this is mechanism 4, not mechanism 1. |
| rc466 | the five `exact=` Laplacian builders | rc466 shipped an exact-ℚ route on `normalized_laplacian`, `mass_normalized_laplacian`, `magnetic_laplacian`, `quaternion_laplacian` and `klein4_gain_laplacian`, and the drain gate measured every one of them exact | **a bare-C host runs 0 of the 5.** Every C symbol in the family is double-only in both directions: `const double *weights` in, `double *out_matrix` out, with no exact arm and no limb form. The four declarations are the `srmech_graph_*_laplacian` block of the public header, which spans c/include/srmech.h:2050-2156 — normalized, mass-normalized, magnetic and klein4-gain, in that order. There is no exact arm and no `Q` / `Qi` limb form, so the capability exists only in the scripting implementation. Recorded rather than closed at rc467 (`#T1188`): an exact arm needs exact-ℚ bigint matrix output plus the perfect-rational-square root path — a slice on the scale of the `srmech_qmat_*` family, not a rider. Tracked as task `#T1188`, this ADR row being the landing surface — §6a's capability-rooted ledger is authorized follow-on and is not yet implemented, so a row here is what §5 means by "files a tracked gap". Closing it later is ABI-ADDITIVE (new symbols; srmech.h:2160 states the convention), so `SRMECH_ABI_VERSION` is unmoved by it either way — 25 when this row was written, 26 since rc473 moved it for an unrelated reason (the row two below). **Still open.** |
| rc467 | `resonant_spectrum(exact=True)` | rc467 drained the last undeclared silent demoter by composing four shipped exact ops, and the route is exact end to end in Python | **a bare-C host runs 0 of the exact route.** `srmech_resonant_spectrum` (srmech.h:2987) takes `const double *L_rowmajor`, so the exact route must SKIP the native call entirely rather than dispatch to it; the Python marshalling that would feed it is a `float()` per entry (coupling.py, `_resonant_spectrum_native`). Note the shape: this is an ORCHESTRATOR-level gap, not a kernel one — every kernel the exact cascade needs already ships in C — Sturm isolation (`srmech_sturm_isolate`), exact eigenvectors (`srmech_eigvec_exact`), integer polynomial factorisation (`srmech_factor_integer_poly`), Faddeev–LeVerrier (`srmech_faddeev_leverrier`) and the whole exact-ℚ matrix family (the `srmech_qmat_*` block: `rref` / `rank` / `det` / `inverse` / `solve` / `nullspace` / `rref_crt`), all declared in `c/include/srmech.h` — so what is missing is the exact-route composition and its exact-ℚ return shape, not the arithmetic. *(rc473 repair pass, `#T1188`: this sentence cited `srmech.h` lines 13190 / 13271 / 10524 / 13160 "respectively", and every one of the four was wrong. Two ways at once — the header grew +170 lines in this rc so all four shifted, AND the mapping was already scrambled at `b398b8c46`, where `:13190` carried the Faddeev–LeVerrier text while the prose assigned that slot to Sturm. Re-pointed by SYMBOL and by symbol only: a line number into a header that every rc edits cannot be kept true, `test_adr_citation_integrity_rc415` can check a backticked identifier where it cannot check a bare number, and quoting the live addresses even as a snapshot would put five symbol names into that gate's adjacency window and re-create the defect in the act of correcting it — measured, a snapshot took the gate's token-evidence count from 7 to 13 against a CEIL of 7.)* Tracked as task `#T1188`, same landing surface; same close path and same ABI consequence as the row above. **Still open.** |
| rc473 | `exp` / `log` / `rational_sqrt` outside `rational`'s Q61 domain — ±Inf INCLUDED, but NOT exhausting it | rc473 repaired the Class-N refusal contract so the two projections agree on what they refuse — 24 discarded statuses propagated and NaN refused by every scalar callee | **agreement is restored for NaN and NOT for ±Inf**, and this row is the residue. Measured at the C symbols on this cell: `srmech_exp(+Inf) -> (SRMECH_OK, inf)`, `srmech_exp(-Inf) -> (SRMECH_OK, 0.0)`, `srmech_log(+Inf) -> (SRMECH_OK, inf)`, `srmech_rational_sqrt(+Inf) -> (SRMECH_OK, inf)`, while `rational.exp(±inf)` / `rational.log(inf)` / `rational.sqrt(inf)` all raise `ValueError("… x must be finite (Q is the finite-rational carrier)")`. §2.4 — implementations "may not differ in which inputs they serve" — so C serving three inputs the scripting implementation refuses is the same defect class this rc exists to remove, in the other direction. **Not repaired, and the reason is a measured hazard rather than a preference:** `lap_sqrt(1.0 + tau*tau)` in `c/src/srmech_laplacian.c` and `sq_sqrt` in `c/src/srmech_svd_qr.c` both reach `+Inf` on the tau-overflow path and rely on `sqrt(+Inf) = +Inf` to get `t = 1/(tau + Inf) = 0`, inside `static void` / `static double` rotates that have no status channel — so widening the refusal turns a working numerics path into a refusal in six enclosing functions that cannot report one. The executable half is shipped: four pinned DECLINE rows in `c/test/test_srmech_value_status_rc473.c` and four `xfail(strict=True)` rows under `_DECLINED_T1188` in `python/tests/test_value_status_c_boundary_rc473.py`, which turn RED when the decline is repaired instead of passing forever. §5 is explicit that those are necessary and not sufficient — "an exemption asserted in a docstring, a changelog entry, a test comment … is **not** an exemption" — so this row is the filing. Tracked as task `#T1188`, this ADR row being the landing surface, in the rc466/rc467 shape. Closing it is a STATUS reinterpretation and therefore a further ABI bump, not an additive change. **Still open.** ⚠️ **rc473 repair pass, `#T1188` — this row's TITLE was narrower than its own population, and the title is what a reader acts on.** It read *"at ±Inf"*, and all four instances above are non-finite, so the row asserts by omission that the residual divergence is confined to non-finite inputs. It is not. Measured on this cell (native, ABI 26 == 26, CPython 3.12.3 under `uv run --python 3.12 --no-project --offline`, numpy absent, gcc 13.3.0 Release/`SRMECH_PEDANTIC=ON`): `srmech_exp(-1e300) -> (SRMECH_OK, 0.0)` and `srmech_exp(1e300) -> (SRMECH_OK, inf)` — two FINITE arguments served by C — against `rational.exp(±1e300)` raising `ValueError("srmech_exp_q61: argument has no Q61 rational (status 2)")` in the native cell and `OverflowError("too many digits in integer")` in the pure one. A finite witness is now carried in the executable half (`_DECLINED_ROWS` gains `("exp", -1e300)`, which is safe to execute because `exp(-1e300)` UNDERFLOWS rather than allocating — unlike the `+2**55` direction, which is the `_NOT_EXERCISED_PURE` hazard in the row below). Filed as a correction rather than a new row because it is the same capability and the same close path; what changed is the stated boundary. |
| rc473 | `rational.exp` above the Q61 practical bound | the same rc473 statement of agreement | **the scripting implementation is the one that fails here, and it does not decline — it CRASHES.** `rational.exp(2.0**55)` builds `2**n * exp(r)` with `n ≈ 5.2e16`, so the exact integer carries ~5e16 bits: measured under `ulimit -v 4000000` it raises `MemoryError`, and unbounded it is a machine-filling allocation. The C peer answers `(SRMECH_OK, +Inf)` — `srmech_exp_q61` refuses at its own `1e18` line (`c/src/srmech_explog.c`) but the double `srmech_exp` overflows to `+Inf` by design. A crash is not a clean decline, so this is not even the §5 "correct failure mode" case; it is a missing precondition. **Not repaired in rc473, and deliberately NOT EXERCISED by any gate** — `_NOT_EXERCISED_PURE` in `python/tests/test_value_status_c_boundary_rc473.py` names the two arguments and the row table is asserted not to contain them, because a gate must not execute an unbounded allocation. Disclosed by name rather than dropped. The close path is an `EXP_MAX_ARG` precondition in `rational.exp` mirroring `srmech_exp_q61`'s existing bound, which is a pure-side change and bumps no ABI. Tracked as task `#T1188`, same landing surface. **Still open.** |
| rc473 (repair pass) | `elementwise_transcendental(…, "exp")` above the double-overflow bound | the same rc473 statement of agreement, and — sharper — the sibling row above locates the pure side's failure at `2**55`, an argument nobody passes by accident | **the two cells disagree at a FINITE, ordinary argument, and the crossover is exactly where a double overflows.** Measured by walking it, same conditions as the row above, the SAME public op in both cells: `x = 709.78` → both cells return `Vec(1, real)`; `x = 709.79` → native returns `Vec(1, real)`, pure raises `OverflowError("integer division result too large for a float")`, and so do 710.0 / 720.0 / 1000.0 / 1e300. `rational.exp` itself SUCCEEDS in both cells at every one of those — it returns an exact `Q` — so the divergence is not in the transcendental, it is in the array kernel's conversion of that exact `Q` back to a `double`, which the native kernel never performs because it computed in `double` all along and got `+Inf`. The negative direction agrees down to −800 and −1e6. This is the same §2.4 class as the two rows above (they differ in which inputs they serve) and it is the most REACHABLE instance of it in the tree: 709.79 is not a boundary-probe value, it is `log(DBL_MAX)` rounded up. **Pre-existing, and not introduced by rc473** — `git diff b398b8c46..HEAD -- python/srmech/math/laplacian.py` touches only the removal of `_q61_trig_range_refuse`, a cos/sin/`exp_i` guard, and nothing on the `exp` float-conversion path. Not repaired here: the close is a decision about which behaviour is RIGHT (native `+Inf`, or the pure refusal), and ADR-0006 §2.5's "do not add a fast path that declines at its ceiling" points at the refusal while the C projection has no channel to report one from inside `srmech_elementwise_transcendental`'s per-element loop — the same shape as the `lap_sqrt` hazard above. Filing it rather than repairing it is the §5 obligation, not a preference. Tracked as task `#T1188`, same landing surface. **Still open.** |
| rc473 (repair pass) | `kepler_solve` at an `M` of order 2^53 or above with large `e` | the same statement of agreement | **the same wheel answers or refuses depending only on whether a library is present.** Measured, same conditions, `kepler.kepler_solve(2.0**53, 0.999)` with the Python defaults (`tolerance=1e-12`, `max_iter=30`): native cell returns `9007199254740992.0` (that is `E == M`); pure cell raises `RuntimeError("kepler_solve: did not converge in 30 iterations")`. The cause is measured rather than assumed: at `M = 2^53` the float ULP is 2, so `f = E - e*sin_e - M` cancels to exactly `0.0` in `double` and the C loop "converges" in two iterations, while the pure loop uses `rational.sin` → exact `Q`, never cancels, and never converges. Neither projection is returning a wrong number for its own carrier — this is the float-vs-exact seam, which is ALU-arc territory and explicitly out of rc473's scope (the brief: *"This is not ALU-arc work"*) — but it IS a §2.4 "differ in which inputs they serve" instance and §5 requires it to be filed rather than left in prose. Note it is NOT the `2^55` row the C-host gate already pins: that one is `srmech_sin` refusing outright, and it is repaired. The close path is a convergence criterion that means the same thing on both carriers, or an explicit shared domain bound on the magnitude of `M`; either is a behaviour change and therefore a further ABI bump. Tracked as task `#T1188`, same landing surface. **Still open.** |
| rc473 (repair pass) | `winding_fold` / `scale_round_half_even` / `best_rational_signed` — the divergence in the OTHER direction | rc473's own framing throughout is "C serves what the scripting implementation refuses", which names only one of the two directions the invariant covers | **C is NARROWER than the scripting implementation at three exported symbols, and §2.4 is symmetric.** Measured at the ctypes symbols against their pure peers with MATCHED parameters (the first attempt passed four arguments to the five-parameter `srmech_cascade_best_rational_signed_f64` and compared against a different `max_denominator`; those figures were discarded rather than quoted). Conditions as above. `srmech_winding_fold(2^55)` → status 2, `theta=nan`, against `one.winding_fold(2^55)` → `(5734161139222659, -2.2273861987513897)`; `srmech_cascade_scale_round_half_even_i64(2^70, 1)` → status 2, against `rational.scale_round_half_even(2**70, 1)` → `1180591620717411303424`; `srmech_cascade_best_rational_signed_f64(2^53, max_denominator=100, fine_scale=1000000)` → status 2, against `composites.best_rational_signed(2.0**53)` → `(9007199254740992, 1)`. Controls in the same run agree exactly — `winding_fold(1.0)` → `(0, 1.0)` both, `scale_round_half_even(2.5, 1)` → `2` both, `best_rational_signed(±0.75)` → `(±3, 4)` both — so this is a bound, not a break. These are CLEAN DECLINES and not wrong answers, which is precisely why they need a row: §5's fourth pattern says *"it declines cleanly, the pure path works"* is a SAFETY argument offered where a CAPABILITY argument is required, and ADR-0006 §2.5 names it an anti-pattern. Two of the three are structural — `int64_t` out-parameters cannot carry a bignum, so closing those means a limb form, which is a slice and not a rider — while `srmech_winding_fold`'s `2^55` bound is the Q61 octant reduction's own and is the one the pure peer works around in Python. Not repaired in rc473; disclosed by name rather than dropped. Tracked as task `#T1188`, same landing surface. **Still open.** |
| rc473 (pre-publish pass) | `normalized_laplacian(n, edges, weights=[+inf])` — the first MATRIX-kernel instance | rc473's closing question — *"is any divergence left UNFILED?"* — was answered **0** over 90 rows, and that answer stands for the population it asked about | **the population was SCALAR, and the first probe at a matrix kernel found a divergence it could not have seen.** Measured in-process on both cells, same wall clock, same interpreter (CPython 3.12.3, WSL2 `6.18.33.2-microsoft-standard-WSL2`, numpy absent, `SRMECH_ALLOW_STALE_NATIVE` unset; the native cell authenticated by `srmech_rational_sqrt(NaN)` → status **2** at the ctypes symbol on a library reporting `0.9.0rc473` / ABI **26** / `nm -D \| grep -c __assert_fail` → 0, which is what separates an rc473 `.so` from an rc472 one — version and ABI alone do not): `srmech.math.laplacian.normalized_laplacian(2, [(0,1)], weights=[+inf])` answers `[[0.0, nan], [nan, 0.0]]` through the dispatched wrapper on the native cell and `[[1.0, nan], [nan, 1.0]]` through `_normalized_laplacian_py` **in the same process**, and `[[1.0, nan], [nan, 1.0]]` on a pure cell (`HAS_NATIVE False`, 0 `.so`/`.dll`/`.pyd` in the tree by construction). **The normalised diagonal is 1.0 or 0.0 depending only on whether a library is loaded** — §2.4, "may not differ in which inputs they serve", read at the VALUE rather than at the refusal. ⚠️ **It is `+inf`-SPECIFIC, which is narrower than "non-finite" and was measured rather than assumed:** `weights=[-inf]` and `weights=[nan]` give `[[0, nan], [nan, 0]]` on BOTH cells and through BOTH routes, and the finite controls `weights=[-1.0]` → all-zeros and `weights=[1.0]` → `[[1, -1], [-1, 1]]` agree everywhere, so the comparator can plainly return "agree". Cause, measured at the symbol rather than inferred: `srmech_rational_sqrt(+Inf)` → `(SRMECH_OK, +Inf)` — `+Inf` is not a refusal class — so the two routes differ only in the ORDER they take `1/sqrt(inf)` in, one reaching `1/inf → 0` where the other reaches a normalised `1.0`. **Not repaired in rc473, and the reason is that neither answer is yet wrong:** which projection is right is the float carrier's NON-FINITE CONTRACT, which is unwritten. Writing it is rc-J's subject and it must separate `+Inf` from `−Inf`, because at the one divergence found they behave differently. The executable half ships with this row: `test_normalized_laplacian_plus_inf_diverges_between_projections` in `python/tests/test_value_status_c_boundary_rc473.py`, `_needs_native`-gated and `xfail(strict=True)`, comparing the dispatched wrapper against `_normalized_laplacian_py` **in the same process** — gated because on a pure cell the wrapper IS `_normalized_laplacian_py` (measured above), so an ungated comparison would agree with itself and a strict xfail would then XPASS and redden the pure cell for the wrong reason. Its four agreeing siblings ship beside it as plain passing rows, so the instrument is not one that can only return "differ". Tracked as task `#T1188`, this ADR row being the landing surface. **Still open.** |

A fourth pattern — *"it declines cleanly, the pure path works"* — is a **safety** argument
offered where a **capability** argument is required. A clean decline means the compiled
implementation cannot serve an input the scripting implementation can; that the decline is
well-behaved is a separate (and good) property. This pattern is already named as an
anti-pattern for carriers in **ADR-0006 §2.5** ("do not add a fast path that declines at its
ceiling"); this ADR generalizes it from carriers to implementations.

**rc280 `section_counts` is the instance — and it is a different, sharper case than the three
above.** JPL Rule 3 bans malloc and the exported signature carries no `ws` arena, so
`srmech_genome_section_counts` works out of three file-scope statics (`g_sc_arena`,
`g_sc_slots`, `g_sc_win` — `c/src/srmech_genome.c`). The bounds, verified in the header block
at `c/include/srmech.h`:

- the 32 MiB catalog arena's ~2.7 KiB/chromosome term gives a **~11,000-section ceiling**,
  against the F1253 store's **240,881 sections**;
- the 2^18-slot count table gives a **196,608 distinct-id ceiling**, against the store's
  **1,100,189 ids** — a second bound, exceeded by more than 5×.

Over any bound the peer returns `SRMECH_ERR_OVERFLOW`, the binding reads that as a decline, and
the Python implementation runs. The same statics make the call **not reentrant**. Tracked as
task **#899** (per the conductor; the id does not appear in the tree, so it is recorded here on
that authority, not tree-verified).

**Why it is the sharper case:** rc262/rc270/rc273 each *asserted* a parity that did not exist.
rc280 does the opposite — the CHANGELOG entry and the header block state the ceiling, the
corpus figure, the non-reentrancy, and the fact that removing the ceiling would require a `ws`
parameter (a wire-signature change) *deliberately not taken in that rc*. That disclosure is
exemplary and this ADR does not fault it. **The mechanism survives full disclosure anyway** —
because the honest decline is offered as the resolution rather than as a filed gap, and a
capability the compiled implementation cannot serve at the only scale that matters remains a
missing capability no matter how well it is documented. This is precisely why §5 requires a
decline to file a tracked gap: candour about a hole is not the same as tracking it, and
mechanism 4 is the one mechanism that a well-written changelog does not defeat.

### 1.3 The four reinforcing mechanisms

Each verified against the tree at v0.9.0rc280:

1. **The vocabulary encodes hierarchy.** "C **peer**" (1668 occurrences), "**pure fallback**"
   (175), "**native dispatch**" (276), "accelerat\*" (499), `HAS_NATIVE` (1451). *Peer* is
   relative to something; *fallback* presupposes a primary; *accelerate* presupposes a
   reference implementation being sped up. The words do the thinking.

2. **The taxonomy is Python-rooted, so it cannot express the goal.** All **680** rows of
   `python/tests/rosetta_classification.ndjson` are keyed by a Python dotted path
   (`exposed_as` / `defined_at`); **zero** rows are keyed by a C symbol. The enumeration step
   in `test_rosetta_completeness.py` is explicitly "enumerate the live public-op surface
   (every public callable defined in `srmech.amsc` / `srmech.qm` /
   `srmech.signal_processing`)." Every bucket therefore describes *a Python op's relationship
   to C*: `c_dispatched` = "routes to a `srmech_*` C symbol", `composition_of_c` = "pure
   composition of `c_dispatched` ops". **There is no bucket meaning "this capability exists
   independently in both trees."** The classification literally cannot say the thing this
   project wants said.

   The live exhibit: `srmech.biology.genome.amplify` is classified `composition_of_c`, a bucket
   whose own docstring annotates it *"(standalone-ready)"*, while no `srmech_genome_amplify`
   symbol exists. The label is not a lie about the row's own definition — it is a true
   statement in a vocabulary that cannot distinguish "composes C parts" from "a C host can
   run this."

   **The defect is not confined to `composition_of_c`.** `srmech.biology.plasmid.section_counts`
   is classified **`c_dispatched`** — the *strongest* label the taxonomy has, "routes to a
   `srmech_*` C symbol (standalone-ready)" — and it does route to one. That C implementation
   also declines above ~11,000 sections against a 240,881-section corpus (§1.2). Both facts are
   true simultaneously, because `c_dispatched` records that a C symbol is **reached**, never
   that it **suffices**. No bucket in the taxonomy has a place to put "has a compiled
   implementation that cannot serve the real input domain."

3. **The tests run in one direction only.** `test_rosetta_transitive_standalone.py` walks the
   callee graph of every `composition_of_c` op, but `_reached_ledger_ops` treats a
   `c_dispatched` / `composition_of_c` / `non_compute` row as a **leaf and stops** (`continue
   # C-backed / validated-elsewhere leaf: stop`). So it proves a composite *reaches* C-backed
   leaves; it never proves a bare-C host can run the composite's own glue. Nothing anywhere
   enumerates the C header and asks "is the C host complete?" — the only test that reads
   `c/include/srmech.h` at all (`test_native_sha256.py`) reads it for the version string.

4. **"It declines cleanly" defers indefinitely.** A safety property is accepted in place of a
   capability property, and because the decline is genuinely well-behaved there is never a
   forcing moment. The rc280 `section_counts` instance (§1.2) shows this is the one mechanism
   that **full disclosure does not defeat**: everything about that ceiling is documented
   accurately and the gap is still open, because being candid about a hole and tracking it are
   different acts.

**Why the mechanisms are load-bearing together:** (1) makes the gap unspeakable, (2) makes it
unclassifiable, (3) makes it undetectable, (4) makes it indefinitely deferrable. Fixing any one
alone leaves the other three generating the same outcome.

## 2. Decision — the framing

**srmech is a multi-implementation codebase. The CAPABILITY is the invariant. Each
implementation is a COHERENCY PROJECTION of that capability into one execution regime. No
implementation is primary.**

```
                      CAPABILITY  (the invariant)
                   e.g. "amplify a gene's copy number"
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
   scripting-            compiled-            (future: a third
   coherency             coherency             implementation —
   implementation        implementation        Go / Rust / …)
   (python/srmech)       (c/src, c/include)
        │                     │                     │
        └─────────────────────┴─────────────────────┘
              same capability · byte-identical results
              differing only in execution regime
```

This is the project's own frame-relativity discipline applied to its own architecture.
Privileging the Python frame and calling C "the accelerator" is the same error as privileging
one quantity and calling its twin "only mathematically real." The implementations are related
by projection, not by rank.

Concretely:

1. **Capability-first.** A capability is defined once, independent of language. An
   implementation either realizes it over the full input domain or does not have it. "Realizes
   it by calling the other implementation" is not realizing it.

2. **No implementation is the reference.** The **differential-oracle role is a test-time role
   that rotates**, not a rank. When checking a new C implementation, the Python one is the
   oracle; when checking a Python refactor, the C one is. This is the clause of ADR-0003 §2.6
   ("Python is the oracle, not the fallback") that this ADR amends: the sentence is correct
   about what Python is *not* (a fallback) and, read as a standing description rather than a
   test-time role, incorrectly fixes Python as the thing the other implementation is measured
   *against*. The oracle relation is symmetric; the parity claim is what matters.

3. **Parity is byte-identical results, not similar behavior.** Unchanged from ADR-0003 §2.2.

4. **Implementations may differ in execution regime only** — scheduling, memory strategy,
   routing, packaging. They may not differ in which inputs they serve or what results they
   produce.

## 3. Decision — vocabulary

The hierarchy words are retired from **capability description**. Some remain valid as
**routing** or **packaging** description; those distinctions are stated, not glossed.

| Retired / restricted | Why | Use instead |
|---|---|---|
| "C **peer**" | a peer is defined relative to a primary | "the C implementation" / "the compiled-coherency implementation" |
| "**pure fallback**", "pure-Python fallback" | a fallback is what you get when the real thing is absent | "the Python implementation" / "the scripting-coherency implementation" |
| "C **accelerates** …", "the accelerator", "native **acceleration**" | frames C as a speed treatment applied to a Python original | "the compiled-coherency implementation" (capability); "faster on this path" (a measured performance claim, stated as such) |
| "**native dispatch**" — *restricted, not retired* | valid for **routing**: which implementation services a call inside a co-installed process. Invalid as a description of whether a capability **exists**. | keep for routing; never as evidence of parity |
| "Python is the **oracle**" | correct as a test-time role, wrong as a standing rank | "the differential oracle for this check" (naming which direction, this time) |
| "just glue", "only orchestration" | orchestration is a capability; ADR-0003 §2.2 already says so | name the capability |

**Kept deliberately:** "**C twin**" (already in use in the Rosetta ratchet) — *twin* is
symmetric and already carries the intended framing. Renaming symmetric vocabulary would be
churn.

**Not retired here:** the `HAS_NATIVE` **code symbol**. It names a real runtime fact (is the
shared library loaded in this process) and renaming it is code work, out of scope for a
documentation ADR. It is flagged for the follow-on work in §5 to consider; this ADR does not
authorize the rename.

## 4. Decision — the exemption rule

**Exempt from multi-implementation parity: host-integration and protocol-adapter layers.**
Specifically the MCP server adapter and the Anthropic-SDK / `claude_sdk` adapter (in the tree:
the `srmech.mcp` / `srmech.llm` surfaces, and the `host_glue` rows — 21 of them — under the
`non_compute` bucket). These bind srmech to a specific host runtime; there is no
language-independent capability underneath them to project.

**Nothing else is exempt.**

Any new exemption **requires an amendment to this ADR** — a PR that argues the case against
this rule, reviewed as an architecture decision. An exemption asserted in a docstring, a
changelog entry, a test comment, or a code review reply is **not an exemption**. This is the
specific procedural gap the rc262 / rc270 / rc273 instances went through: each recorded its
carve-out in prose attached to the code, where nothing was positioned to challenge it.

## 5. Decision — a clean decline is a correct FAILURE MODE, not parity

An implementation that declines an input the other implementation serves **does not have the
capability for that domain**. The decline being clean, typed, non-crashing, and well-tested is
required (ADR-0003 §2.1, ADR-0006 §2.6) and is **never sufficient**.

**Every such decline files a tracked gap** — a ledger row (§6a) recording the capability, the
declining implementation, and the boundary. "It declines cleanly, the other path works" is a
statement about the quality of the decline, and is not a parity argument.

This applies **even when the decline is fully and accurately documented**. rc280's
`section_counts` (§1.2) documents its ceiling, its corpus shortfall, its non-reentrancy, and the
signature change that would remove it — and the gap is still open, because a changelog entry is
not a tracked gap. **Disclosure is necessary and is not sufficient.** A build-time lever
(`SRMECH_GENOME_SC_ARENA_BYTES`) that a caller *could* raise is likewise not parity: parity is a
property of what the implementation serves as shipped, not of what a recompile could reach.

## 6. Consequences — follow-on work this ADR authorizes but does NOT implement

This ADR is the framing that the following derive from. Each is named here so the downstream
change is derivable rather than a third ad-hoc scheme. **None of it is implemented by this
ADR**, and each maps to a mechanism in §1.3:

| Mechanism (§1.3) | Follow-on this ADR authorizes |
|---|---|
| 1 — vocabulary encodes hierarchy | A vocabulary sweep of docstrings / `ToolEntry` summaries / ADR + CLAUDE.md prose per the §3 table; a decision on the `HAS_NATIVE` symbol |
| 2 — taxonomy is Python-rooted | **(a) A capability-rooted ledger** |
| 3 — tests run one direction | **(b) A C-host capability manifest** |
| 4 — clean decline defers indefinitely | The §5 rule made mechanical: a decline boundary is a ledger row, not a comment |

**(a) A capability-rooted ledger.** Re-key the Rosetta ledger from a Python symbol to a
**capability**, with a set of implementations present and a set missing:
`capability → {implementations present} / {missing}`. Under this shape a Python-only capability
renders as **"missing: compiled"** — a hole with a name — rather than as `composition_of_c`, a
bucket whose annotation reads *"standalone-ready."* This is the change that makes the gap
speakable and classifiable; the two current buckets survive inside it as *how* an
implementation realizes a capability, which is a genuinely useful distinction that should not
be lost.

**(b) A C-host capability manifest.** Enumerated and asserted **from the C side** — the C tree
declaring what it provides, checked against the capability ledger. The motivating fact:
**nothing in the tree today would notice if the C implementation lost a capability entirely.**
The Rosetta ratchets enumerate Python and ask whether it reaches C; no test enumerates C. A
manifest closes the reverse direction, and is the thing that would have caught rc262 / rc270 /
rc273 at review time.

> **Status note (rc300, `#938`) — a bounded first step on (b), not its delivery.**
> `srmech/amsc/_c_claims.py` records, per `c_dispatched` op, the `srmech_*` symbols that op's
> dispatch path names, filtered against the symbols *declared in `c/include/srmech.h`*; it is
> checked against the loaded library by `srmech.amsc._native.c_claim_report()`, surfaced as
> `describe()["c_claims"]`, and asserted by `tests/test_c_claim_resolution_rc300.py`.
>
> What this changes in §1.3 mechanism 3: the claim that *"the only test that reads
> `c/include/srmech.h` at all reads it for the version string"* is no longer true, and the claim
> that *"nothing in the tree today would notice if the C implementation lost a capability
> entirely"* is now **partially** false — a lost symbol that a `c_dispatched` op claims is
> detected, named, and fails the suite. That state was previously silent, because ABI matching
> does not cover it: `srmech.h` adds symbols ABI-additively, so a stale build keeps ABI 8, keeps
> `HAS_NATIVE` true, and falls to correct pure paths under a false classification.
>
> What it does **not** do, and why (b) stays open: the direction is still Python-rooted. It asks
> *"is the symbol this Python op claims present?"*, not *"is the C host complete?"*. It cannot
> see a capability C never had a Python claimant for, it says nothing about whether a reached
> symbol **suffices** over the real input domain (the §1.2 / mechanism-2 defect is untouched),
> and its extraction is static, leaving **23 of 263** `c_dispatched` ops with no attributable
> symbol — enumerated in `UNVERIFIABLE_CLAIMS` under a down-only ceiling rather than left
> invisible.

**(c) How a third implementation is additive, not a port.** Under this framing a Go or Rust
implementation is **a third projection of the same capability set**, not a translation of the
Python or C source. It is checked against the capability ledger and the manifest, differentially
against whichever existing implementation serves as oracle for that check, and it inherits the
§4 exemption rule unchanged. Concretely: it does not need to be a line-for-line port of either
tree, and neither existing tree acquires seniority over it. What it must do is realize each
capability over the full input domain with byte-identical results. This is also the test of
whether the framing is real — if a third implementation would have to be "a port of the C one,"
the capability is not actually defined independently of an implementation, and that is a defect
in the capability definition.

## 7. Why this amends ADR-0003 rather than superseding it or landing standalone

**Not a supersede.** All nine of ADR-0003's decisions remain correct and in force; none is
retracted. Superseding would retire nine correct rules and force their re-litigation, and would
lose the memory-feedback trail ADR-0003 consolidates. The rc273 audit's finding was never "0003
is wrong" — it was that 0003's standard was applied strictly to some ops and loosely to others,
with nothing to arbitrate.

**Not standalone-alongside.** The tension is real and must be resolved in writing rather than
left for a reader to notice: ADR-0003 §2.6 fixes Python as the oracle and C as the standalone
deliverable, which is an asymmetric frame. A new ADR that ignored that clause would leave two
documents in force disagreeing about whether an implementation can be primary — the same
unenforced disagreement between two standards that the audit identified as the systemic root
cause (audit §0). §2.2 above states the amendment explicitly.

**Therefore: a new ADR that amends one clause of 0003 and adds governance around it.** ADR-0003
answers *what must be true* (C runs standalone, everything mirrors). ADR-0009 answers *why it
keeps not being true, what the relationship between implementations actually is, what is
exempt, and what a decline means.* ADR-0003 keeps its number, its status, and its content;
its index row and this ADR cross-reference each other.

## 8. Scope honesty — what this ADR does NOT claim

- **It does not assert that srmech currently has multi-implementation parity. It does not.**
  This ADR defines the standard the audit's open gaps are measured against.
- **Current state as verified at v0.9.0rc280** (the audit was taken at rc273 and the tree has
  moved): audit gaps **G4 `integrate`** and **G5 `mint_strand`** are **closed** (rc276, rc277 —
  both now `c_dispatched` with whole-op C entry points). **G6 `amplify` /
  `copy_number_of`** closed at rc281; **G1 `recursive_cut`** closed at **rc284**. **G2
  `genome_from_graph`**, **G3 graph `genome_partition`**, and the **G7** minors
  (`condense`, `decondense`, `active_telomere`, `genes`, `mint_plan`, multi-gene
  `chromosome`) remain **open**.
  > **G1 caveat as written at rc280, and how it resolved.** At rc280, `grep
  > srmech_laplacian_recursive_cut c/include/srmech.h` returned a hit — but the hit was
  > inside a **prose comment** on `srmech_genome_integrate_plasmids` recording that stage 2
  > *"NEVER calls"* it. The symbol name existed only as a reference to its absence. **rc284
  > closed G1**: `srmech_laplacian_recursive_cut` (+ `_arena_bytes`) is now declared in the
  > header, defined in `c/src/srmech_laplacian.c`, bound in `_native.py`, and genuinely
  > dispatched by the op — all four checked mechanically by the rc281 wire-glue ratchet.
  >
  > **What G1 turned out to be is worth recording, because the obvious reading was wrong.**
  > G1 was widely described as needing a Fiedler-vector computation built in C under
  > ADR-0005. It did not: `srmech_laplacian_fiedler_sparse_file` has been native since
  > **rc168**, with the §101 tick already threaded at phase `PARTITIONING`, and
  > `srmech_rational_sqrt` has supplied its only square root since rc45. The missing piece
  > was the **`while pending` recursion around the engine** — the disk-backed queue, the
  > induced-subgraph relabel, the tome lifecycle — plus three absent **PAL** primitives
  > (`mkdir` / `remove` / replacing-`rename`). The gap was I/O and control flow, not
  > mathematics. This is a §1.3-shaped mechanism: the capability looked blocked on the
  > hardest-sounding component, and was actually blocked on the most mundane one.
  >
  > **G1 was the shared dead-end of G2 and G3, so rc284 UNBLOCKS both — but unblocking is
  > not closing.** G3 additionally needs exact-integer participation, the antimode
  > histogram and per-node classify; G2 needs all of G3 plus its in-RAM `_induced_subgraph`
  > relabel, the per-group `graph_to_kernel` → `mint_strand` loop and strand assembly.
- **rc279 and rc280 shipped a new capability surface** (`plasmid_extract`, `section_counts`,
  `conserved_core`, `genome_integrate_plasmids`), taking the ledger from 677 to **680** rows.
  Two are `c_dispatched`, two `composition_of_c`. `section_counts` is the §1.2 instance.
- **It does not claim the diagnosis in §1.3 is complete** — four mechanisms were identified and
  verified; there may be others.
- **It does not implement any of §6.** No ledger is re-keyed, no manifest exists, no vocabulary
  sweep has been performed, and no test has changed as a result of this ADR.
- **It does not commit the project to a Go or Rust implementation.** §6(c) states how one would
  be additive *if* undertaken.
- **It does not resolve the rc273 audit's three open fermatas** (audit §5: the reclassification
  of native-dispatched genome ops; the scope of the systemic ratchet fix; whether G7-minor reads
  owe a C mirror). Those are conductor decisions and are inputs to §6(a), not outputs of this
  ADR.

## 9. Sources

`docs/srmech/notes/c_host_parity_audit_rc273.md` (the motivating audit) ·
ADR-0003 (amended by this ADR) · ADR-0005 (no external math library) ·
ADR-0006 §2.5–2.6 (decline-at-a-ceiling as an anti-pattern; bounded arena + honest decline) ·
ADR-0007 (release engineering) ·
`[[feedback_genome_must_exist_fully_in_c]]` ·
`[[feedback_c_must_be_standalone_complete_no_python_fallback]]` ·
`[[feedback_c_peer_delivered_same_rc_never_split]]` ·
`[[feedback_c_mirror_extends_to_every_composite_not_just_primitive_kernels]]` ·
`[[feedback_name_the_gap_plainly_dont_hedge_or_document_away]]` ·
`[[feedback_dont_ship_partial_unproven_difficulty_is_not_an_excuse]]` ·
`[[reference_two_language_problem_inverted_python_c_different_scales]]`

User direction (2026-07-19): *"it's simply supposed to be a multi source code base. the only
things so far exempt from this parity has been the mcp/claude_sdk layer … there should be a C
native and Python native codebase for srmech that do the exact same thing at different coherency
perspectives, scripting vs native compiled."*
