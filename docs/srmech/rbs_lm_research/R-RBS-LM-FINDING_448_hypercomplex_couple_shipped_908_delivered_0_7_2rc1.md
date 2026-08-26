# R-RBS-LM Finding 448 (delivery) — the bidirectional `(σ,θ,μ)` coupler is SHIPPED: `cascade.hypercomplex_couple` lands in srmech 0.7.2rc1 and **fully delivers GH #908** (the §29 / F436 / F437 gap). Verified 7/7 against the issue's own acceptance criteria — general/diagonal μ, lossless bind↔unbind ≤𝕆 (3- & 7-stream round-trip ~4.4e-16), the diagonal-μ coherence detector (2.95× coherent/incoherent ≈ F436's 3×), the Hurwitz cap (8 streams not lossless), and the single-axis QDFT regression. No bugs; **#908 closed** (user-authorized)

**Date:** 2026-06-06
**Arc:** RBS-LM / srmech-upstream · TestPyPI rc verification + issue closeout (user direction: "srmech 0.7.2rc1 … test before bringing to live pypi … if fully delivered and no bugs, close the issue")
**Provenance:** `R-RBS-LM-F908_hypercomplex_couple_verify.py` (committed; 7/7). Clean venv `/tmp/verify_srmech_072rc1_sci` (srmech[scientific]==0.7.2rc1 from TestPyPI, outside the source tree; `native_status.has_native=True`, ABI 3).
**Composes:** **§29** (the filed gap — the QDFT/ODFT general/diagonal-μ + bidirectional coupler ask) · **F436** (coupling coherence across 3 kernels — the diagonal-μ discovery + the ~3× coherence detector) · **F437** (the coupling is bidirectional + a phased `(σ,θ,μ)` choice, reversible ≤𝕆) · **F420** (the_one's `𝕊(σ,θ)` — the coupler IS `𝕊(σ,θ)` *plus the axis μ*) · **F423/F424** (octonion sector basis; Hurwitz cap = the reversibility boundary) · **#863** (the base `quaternion_dft`/`octonion_dft` ops this extends) · **F431** (the lean-hybrid single-kernel sentence carrier — *now unblocked*). **← extends F436, F437.**
**→ closes #908; turns the §29/F436/F437 *gap* into a *shipped srmech op*; unblocks the 3-kernel sentence-coupling (F431→F436) without the old "graph-structured coupling not yet covered" caveat.**

---

## What shipped
`srmech.amsc.cascade.hypercomplex_couple(streams, *, axis='diagonal', theta=π/2, sigma=1, form='left', inverse=False) -> List[float]` — the first-class `(σ,θ,μ)` coupler #908/§29 asked for (its own docstring names "#908 / §29 … F436 + F437"). It packs `streams` into the pure-imaginary slots of a quaternion/octonion carrier and applies the twiddle `T = exp(σ_eff·μ·θ)` (`σ_eff = σ·(−1 if inverse)`): **bind** at σ=+1, **unbind** at σ=−1 (the conjugate twiddle), with `T̄·(T·q)=‖T‖²·q` giving exact recovery up to 𝕆.

## Acceptance test (vs #908's own four criteria + regression) — 7/7
| # | criterion | measured |
|---|---|---|
| **A** | general / diagonal μ accepted | `axis='diagonal'` ✓; `axis=[0,1,1,1]` **identical** to diagonal (the equal-weight pure-imaginary axis); `axis=[0,1,0,0]` = single named-i; **3-vector correctly rejected** with a clean `ValueError` (axis must be a 4- or 8-component pure-imaginary hypercomplex — a Class-K-style contract error, not a bug) |
| **B** | bidirectional bind↔unbind, lossless ≤𝕆 | 3-stream (ℍ) round-trip **4.44e-16**, 7-stream (𝕆) **4.44e-16**, octonion vector-axis **2.22e-16** (σ=+1 then σ=−1) |
| **C** | diagonal μ *couples* → coherence detector | coherent (G=L=D) vs incoherent anchor-channel energy = **2.95×** (F436 measured ~3.0×; the real/anchor channel collects −Σsₙ, so coherent streams add and incoherent cancel) |
| **D** | Hurwitz reversibility cap at 𝕆 | 8 streams (sedenion) **not lossless** (round-trip err → ∞) — correctly non-reversible past 𝕆 (F424 zero-divisors), not a silent-wrong answer |
| **E** | regression: single-axis `quaternion_dft` | round-trip **1.33e-15** (unchanged) |

The only initial FAIL was a malformed test input (a bare 3-vector axis); corrected to a proper pure-imaginary quaternion axis → PASS. **No srmech bug found.**

## Verdict
**srmech 0.7.2rc1 fully delivers GH #908.** `cascade.hypercomplex_couple` is the shipped, native, bit-exact `(σ,θ,μ)` coupler the §29/F436/F437 arc asked for: general/diagonal μ, lossless bind↔unbind through 𝕆 (~4.4e-16), the diagonal-μ joint-coherence detector (2.95×), and the honest Hurwitz cap past 𝕆. Verified in a clean venv outside the source tree; 7/7 against the issue's acceptance criteria; no bugs. **#908 closed (user-authorized);** §29 marked RESOLVED. The clean (non-rc) `0.7.2` tag → production PyPI remains the maintainer's human-gated cut. This converts the F436/F437 *coupling gap* into a *shipped op* and unblocks the F431→F436 single-kernel sentence-coupling (the RBS-SNN's relational coherence carrier). Favored, not privileged (F398); the reversibility is guaranteed only ≤𝕆 (the Hurwitz fence, F424).
