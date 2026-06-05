# libm-scalar-math retrofit sweep — rc40 (`math.sqrt`) + rc41 residue (`math.{sin,cos,atan2}` / `math.pi`)

**2026-06-05 (srmech v0.7.0rc40).** The §22 discipline closeout: *when srmech
itself ships the scalar primitive, route the scalar fallback through srmech's
own A–N cascade, not libm.* Now that `srmech.amsc.rational.{sqrt,hypot}` (rc35)
and `rational.{sin,cos,tan,atan,atan2}` (rc33) + the `pi_cascade` exist, the
remaining `math.*` scalar calls in shipped srmech are routable. This is the
sibling of the rc32 `abs()`-sweep and the rc33 numpy-math-sweep.

## Full AST audit (26 real `math.*` routable references across 8 files)

A precise AST walk (real `ast.Call` / `ast.Attribute` nodes, ignoring
docstring/comment text) found **26** routable references. Note: `rational.py`,
`pi_cascade.py` and `trigonometry.py` have **zero** real calls — the float-trig
cascades are genuinely libm-free (the grep hits there are all docstrings).

| family | count | sites |
|---|---|---|
| `math.sqrt` | 12 | laplacian.py ×5 (Jacobi), bell.py ×2, octonion.py ×1, sm.py ×3, hypercomplex_dft.py ×1 |
| `math.sin` / `math.cos` / `math.atan2` | 12 | kepler.py ×7, compose.py ×3, hypercomplex_dft.py ×2 |
| `math.pi` | 2 | hypercomplex_dft.py ×1, form_function_rotation.py ×1 |

## rc40 — `math.sqrt` routed (12 sites → `rational.sqrt`)

All 12 sites have provably non-negative arguments (`sm.py` guards `>0`;
`octonion` `sum_sq ≥ 0`; the Jacobi rotations are `√(1+x²) ≥ 1` and `1/√d` under
`if d > 0`), so `rational.sqrt` (which raises on negatives, matching nothing
libm-silent here) is a safe machine-ε drop-in.

- `amsc/laplacian.py` — the 5 cyclic-Jacobi sites (the off-diagonal norm + the
  rotation `t`/`c` angles). **Class L now visibly composes Class N**: the
  eigensolver's leaf root is the Class-N rational sqrt. Verified Jacobi vs
  `numpy.linalg.eigvalsh` = 8.9e-16.
- `qm/bell.py` — the Tsirelson bound `2√2` and `1/√2` constants (bit-exact 0.0).
- `qm/octonion.py` — `octonion_norm` (bit-exact 0.0).
- `qm/sm.py` — Higgs vev `√(μ²/2λ)`, Z-mass `√(g²+g'²)`, Yukawa `1/√2`
  (bit-exact 0.0). (`sm.py` already imported `rational as _srn`.)
- `amsc/cascade/hypercomplex_dft.py` — the `1/√3` normalisation constant
  (bit-exact 0.0).

`import math` was swapped for the rational import in the four modules that used
`math` *only* for sqrt (laplacian/bell/octonion/sm); hypercomplex_dft keeps it
(its `cos`/`sin`/`pi` are rc41 residue).

**Ratchet:** `test_no_math_sqrt_hypot_anywhere_in_srmech` (AST) — `math.sqrt` /
`math.hypot` calls only go DOWN to zero, never up. `cmath.sqrt` (genuine complex
root, e.g. the rc39 `eigvals` 2×2 shift discriminant — no rational peer) and
`np.sqrt` on a bulk array (no scalar-cascade peer for the vectorised op) are NOT
flagged.

## rc41 — STAGED residue (`math.{sin,cos,atan2}` ×12 + `math.pi` ×2)

Routed to a follow-on rc because it is a different primitive family with its own
machine-ε anchor considerations (rc33 had to bump the trig float anchor
`10**12 → 10**15`), and because `kepler.py`'s Kepler-equation solver is an
iterative Newton/Halley loop where trig accuracy gates convergence:

- `amsc/kepler.py` ×7 — `cos`/`sin`/`atan2` in the Kepler solver + true-anomaly.
- `amsc/cascade/compose.py` ×3 — `sin` in the DSL worked examples.
- `amsc/cascade/hypercomplex_dft.py` ×2 + `math.pi` ×1 — the quaternion twiddle.
- `signal_processing/form_function_rotation.py` ×1 — `math.pi`.

rc41 will route these to `rational.{sin,cos,atan2}` + the `pi_cascade`, add the
trig/pi ratchet, and watch the kepler-parity machine-ε tolerances.

## Out of scope (legitimately stays)

- **`cmath.sqrt`** — complex root; no rational complex-sqrt primitive. Scientific
  tier (the rc39 eigvals shift discriminant).
- **`np.sqrt(array)` / `np.cos(array)` etc. on bulk arrays** — vectorised math
  with no scalar-cascade peer; the container/bulk carve (`elementwise_transcendental`
  is the explicit scientific-tier vectorised op). Replacing with a Python loop
  of `rational.*` would be a perf catastrophe and is NOT what the discipline asks.
- **`**0.5`** scalar power-as-root — not surveyed here; a future micro-sweep if any
  appear (none flagged by the routable-`math.*` audit).
