# #693 — ThetaSum `is_zero` degree bound: can Σe² be tightened to Σ|e|?

**Verdict: NO — UNSOUND. Not adopted. The conservative Σe² is retained.**

This is a *prover-completeness* bound. `ThetaSum.is_zero` is a zero-**prover** for elliptic
functions; the elliptic reduction row (`elliptic_gosper` / `elliptic_zeilberger` /
`elliptic_wz_certificate`) builds on it. An unsound `is_zero` that returns `True` on a
non-zero object is a **false theorem** (it would certify a false elliptic identity). The safe
default is therefore to change **nothing** unless a rigorous soundness proof exists. No such
proof exists — the tighten is provably unsound — so Σe² stays.

## The two bound sites (both use Σe²; neither was changed)

- `srmech/amsc/thetasum.py`
  - `_struct_one_var` (single-variable base case): `k = max(Σe² − 1, 0) + _STRUCT_MARGIN` is the
    **p-order band** for the exact-ℚ q-expansion (`degree = max_term Σ_a e_a(w)²`).
  - `_structural_is_zero._deg`: `d = max_term Σ_a e_a(v)²`; the interpolation substitutes
    **d + 1** nodes (node count).
- C peer `c/src/srmech_thetasum_interp.c` `ti_deg` (`acc += e*e`) — a 1:1 mirror; the base-case
  sizing `ti_one_var_sizing` consumes the same `ti_deg`. Both must stay byte-identical to Python.

(#692 fixed a *different*, adjacent quantity — the **arena / ws_bound** memory sizing, which had
used `max_abs_exp²` and mis-sized against the true `Σe²` band. That is the memory bound; #693 is
the **soundness** degree bound. They are not the same knob.)

## 1. Which quantity the node-count / p-band must bound, and why it is Σe² (not Σ|e|)

The numerator `N` (after clearing the nonzero-elliptic denominator) is a holomorphic-in-ℂ*
theta section. `N ≡ 0` is decided by interpolation in one variable `v` at `D_v + 1` distinct
points, where `D_v` is the **true elliptic degree of `N` in `v`** = the number of zeros per
period annulus = the quasi-periodicity index. The interpolation is COMPLETE (a zero-prover)
**iff** the node count / p-band is `≥ D_v`. Under-provisioning `D_v` makes it under-determined:
a non-zero section can pass, giving a false zero.

**`D_v` = Σ_a e_a²**, proved two independent ways:

**(a) Quasi-periodicity multiplier (the module's own identity).** `ellbase.Theta.canonicalize`
implements, verbatim, `θ(pᵏ·z₀; p) = (−1)ᵏ · p^{−k(k−1)/2} · z₀^{−k} · θ(z₀; p)` (Rosengren
arXiv:1608.06161 Eq. 1.6). For a factor `θ(c·vᵉ·[rest]; p)`, the shift `v ↦ p·v` sends the
argument to `pᵉ·(arg)` (so `k = e`), and the emitted multiplier `z₀^{−e} = (c·vᵉ·[rest])^{−e}`
has **v-exponent −e²**. Over a product `∏_a`, the net v-exponent of the multiplier is `−Σ_a e_a²`.
A function holomorphic on ℂ* with `N(p·v) = C·v^{−D}·N(v)` has exactly `D` zeros per fundamental
annulus (argument principle). Hence `D_v = Σ_a e_a²`. (This is exactly what
`_net_period_multiplier_exps` reads off `canonicalize` to build the quasi-class key.)

**(b) Explicit root count.** `θ(c·vᵉ; p) = 0 ⟺ c·vᵉ ∈ p^ℤ ⟺ vᵉ = pⁿ/c`. In the fundamental
annulus `{|p| ≤ |v| < 1}` there are exactly `|e|` admissible `n`, and each contributes `|e|`
distinct e-th roots (same modulus, `|e|` arguments) ⇒ **e² zeros**, not `|e|`. (`|e|` counts the
*n*-values; each n splits into `|e|` roots.)

Both give `D_v = Σe²`, and it is **tight** (achieved). Since `e² > |e|` for every `|e| ≥ 2`,
`Σ|e| < Σe²` exactly when some argument-exponent has magnitude ≥ 2. `Σ|e|` then sits **below the
true degree** → the interpolation is under-determined → **unsound**. `Σe²` is exactly the degree,
so it is the minimal sound choice. The `_STRUCT_MARGIN = 3` slack happens to shield small cases
but is not a principled part of soundness and is overwhelmed as the exponents grow — soundness
must hold for **all** inputs.

## 2. Is Σ|e| a valid upper bound for that quantity? No.

`Σ|e| ≤ Σe²` (since `|e| ≤ e²` for integers), with equality iff every `|e| ∈ {0, 1}`. So the
tighten only changes any verdict when some `|e| ≥ 2` — and that is *precisely* the regime where
`Σ|e|` drops **below** the true degree `Σe²`. A term carrying an exponent `|e| ≥ 2` genuinely
reaches degree up toward `Σe²`; it does not stay at `Σ|e|`. Tightening is therefore invalid.

## 3. The discriminating counterexample (exact, hand-checkable)

Single variable `x`, one theta per term, exponent `e = 3` ⇒ per-term `Σ|e| = 3`, `Σe² = 9`.
Bands: `k_ABS = max(3−1,0)+3 = 5`, `k_SQ = max(9−1,0)+3 = 11`.

```
N(x) =  2·θ(2x³;p) − 27·θ(3x³;p) + 120·θ(4x³;p) − 250·θ(5x³;p)
       + 270·θ(6x³;p) − 147·θ(7x³;p) +  32·θ(8x³;p)
```

- **Exactly non-zero (two independent exact witnesses):**
  - lowest non-zero (p,x) coefficient of the exact-ℚ q-expansion is at `(p⁶, x⁻⁹)` = **−1/112**.
  - `eval_trunc` at `p=½, x=¾` gives **0.180756** at truncation depth 22 **and** depth 44
    (stable — a genuinely-zero object would be `~|p|^depth ≈ 5.7·10⁻¹⁴`). This is the module's own
    convergence oracle read at more points/depth than any band under discussion.
- **True p-adic order is 6**, sitting in the gap `(k_ABS, k_SQ] = (5, 11]`.
- **Shipped Σe² bound: `is_zero = False`** (correct — the p⁶ coefficient is inside `k_SQ = 11`).
- **Tightened Σ|e| bound: `is_zero = True`** (a **false theorem** — it checks only `p⁰…p⁵` and
  misses the p⁶ term).

That single object is sufficient to reject the tighten. Sibling gap-objects (`e=3`, killing
`p⁰…p⁶` / `p⁰…p⁷`) land at true p-order 10 ∈ (5, 11], same split (Σe² False, Σ|e| True). The
convergence-oracle "gap" family (small at tiny `|p|`) is expected: these sections are *designed*
to vanish to high order, so they are small at the oracle's `|p| ≤ 1/9` points — non-zero-ness is
confirmed by the exact coefficient and by the moderate-`|p|` (½) stable eval above.

## 4. True-positive (known-zero) side is preserved — but irrelevant to the verdict

`ThetaSum.three_term(a,b,c)` and its `x → x²` dilation stay `is_zero == True` under **both**
bands (a tighten cannot break a true-zero — fewer checks still see the exact cancellation). The
Frenkel–Turaev ₁₀E₉ / shipped `is_zero == True` cases likewise remain True. This confirms the
tighten does not disturb the true-positives, but it does not rescue soundness: the failure is on
true-**non-zeros**, above.

## Confidence

**High / decisive.** The degree quantity is derived from the module's own quasi-periodicity
identity (two independent derivations agreeing on `Σe²`, tight), and the unsoundness is
demonstrated by an explicit object with an exact non-zero coefficient AND a stable moderate-`|p|`
evaluation, on which the tightened prover returns a false `True`. For a prover-completeness bound
this clears the bar to *reject*; nothing here approaches the (much higher) bar to *adopt*. The
conservative `Σe²` is kept, at both bound sites and in the C peer.

## Reproduction

`tests/test_thetasum_degree_bound_soundness_693.py` builds the object above from hard-coded
coefficients (no solver) and pins: it is `is_zero == False` under the shipped bound, and its
lowest exact q-expansion coefficient is non-zero — a standing guard that would fail loudly if the
bound were ever tightened to Σ|e|. The generating search is
`scratchpad/probe693*.py` (session artifacts, not committed).
