# Subharmonic / chirality structure in the elliptic-theta carrier — verified findings

> **Research note (2026-06-25).** Carrier-verified facts about how the elliptic-theta
> carrier (`srmech.apokatastasis.ellbase` / `thetasum`) already encodes the overtone/undertone
> (harmonic/subharmonic) = chirality structure. Every claim below is checked by an exact
> gate in the carrier (no float, no eval) — the test that produced it is given so it is
> reproducible. Companion to the elliptic F929 reduction row + the order-tower work.

## 1. The carrier un-fuses *magnitude* (order) from *sign* (chirality)

In the carrier a summation variable is `x = qᵏ`; a theta argument is an `EllMonomial`
whose **x-exponent** carries two independent facts that ordinary signed-number notation
fuses onto one axis:

- **|x-exponent| = the order / rung** (the "power"; how far up/down the tower) — the energy.
- **sign(x-exponent) = the chirality** (overtone `θ(αx)` vs undertone `θ(α/x)`) — which of
  two **equal** partners.

The overtone and undertone of one parameter have **equal |x-exponent|** and differ only
by an orientation **prefactor** (the sign). They are not "big vs small" — that appearance
is purely the `|q|<1` reading; reading `1/q` as the base flips which one looks tiny. Same
content, mirror writing.

*Verified:* `Theta(a*x).canonicalize()` vs `Theta(a/x).canonicalize()` → equal `|x-exp|`,
differing orientation prefactor; the magnitude is untouched.

## 2. The ±-pair is the *equal-partner* object; a lone theta is a lone chirality

The object that holds both chiralities as equal partners is the **±-pair**
`{θ(αx), θ(α/x)}` — it is **invariant under the x↔1/x perspective flip** (overtone and
undertone just swap). A *single* theta is NOT a symmetric object: it carries a definite
chirality and reflects to **its own reciprocal** (the Jacobi reflection — same energy,
flipped sign), not to its twin.

This is exactly why the elliptic-Zeilberger certificate basis must be **±-pairs, not
single thetas**: a single-theta (lone-chirality, odd-count) cert numerator produced
odd-count residuals the Weierstrass reducer (`thetasum._reduce_class`, which decides clean
±-pair products) declined; rebuilding the basis as ±-pairs (even-count, equal-partner)
made the residual reducible with no new reduction math. The recognition (count both
chiralities as equal partners) and the build fix (±-pair basis) are one structure.

*Verified:* the ±-pair `{θ(ax),θ(a/x)}` set is invariant under x↔1/x; the cert columns went
7-θ-odd/declining → 8-θ-even/reducible under the ±-pair basis.

## 3. The reducer's pairing IS a bit-exact monomial square root (the fold)

`thetasum._recover_pairs` pairs two thetas iff their argument product is a **perfect-square
monomial** — it calls `_monomial_sqrt(z₁·z₂)` for the midpoint and bails (`None`) on odd
exponents. So a structure folds onto a rung exactly when it is **bit-exactly
square-rootable** there (even exponents). Odd-exponent structure cannot fold to the same
rung — it is held one rung up.

## 4. The very-well-poised factor `θ(a·x²)` is the *doubled rung*; the base peel is blind to it

`x² = q^{2k}` is the doubling that distinguishes the genuinely non-summable
(very-well-poised, Frenkel–Turaev ₆E₅/₁₀E₉) elliptic terms from merely-balanced products
(which telescope → order-0). The elliptic-Gosper peel (`_x_param` / `_peel_coboundary`),
written for x-exponent **±1** pairs, returns **None** on an x²-pair — it **cannot see the
doubled rung**. So the genuine order-1 case is reachable as *input* (balanced + non-summable
inputs exist and gate-confirm) but is blocked at the *peel*, not the reducer.

The honest "undo" of the doubling is **not** `_monomial_sqrt` (`θ(z²) ≠ (θ(z))^{1/2}`); it
is the **theta duplication / Landen identity** — `θ` at the doubled rung expressed as a
**product** of `θ` at the base rung. Whether that collapse applies is the **fold/hold
switch**: fold (very-well-poised factor re-expresses on the base rung) vs hold (stays at
the doubled rung as the irreducible, genuinely-non-summable residue).

*Verified:* `_x_param(θ(ax²)θ(a/x²))` → `None`; x²-including balanced ratios gate as
`is_elliptic=True, elliptic_gosper=None` (non-summable) yet the op returns `None`.

## 5. A-N reading

- The **sign / chirality** is **Class K** (the pin-slot sign-flip / phase boundary): the
  overtone↔undertone orientation IS the Class-K `±1`, and the chiral-endian flip = Class-K
  sign `(−1)^order` (order-tower).
- The **±-pair carrier** is the natural operand that holds both Class-K orientations as
  equal partners (the "count both chiralities equally" object).
- The **doubling** (base → doubled rung; ×2 in the register / squaring the q-power) is the
  order-tower's next-rung step; its reversibility is the duplication identity, gated by the
  fold/hold (even/odd) condition.

## To reproduce

All checks ran numpy-free against the source tree:
`PYTHONPATH=docs/srmech/python python -c "..."` using
`srmech.apokatastasis.ellbase` (EllMonomial/Theta/EllRatio), `srmech.apokatastasis.thetasum`
(`_recover_pairs`/`_reduce_class`/`_monomial_sqrt`), and
`srmech.apokatastasis.elliptic_gosper` (`_x_param`/`_peel_coboundary`). See the elliptic
F929-row work for the exact term-ratio constructions.

*Durable cross-links: user memory `project_subharmonic_chirality_collapse_thread`,
`project_balanced_theta_product_reduction_foreground`, `project_order_tower_next_rung_tool`.*
