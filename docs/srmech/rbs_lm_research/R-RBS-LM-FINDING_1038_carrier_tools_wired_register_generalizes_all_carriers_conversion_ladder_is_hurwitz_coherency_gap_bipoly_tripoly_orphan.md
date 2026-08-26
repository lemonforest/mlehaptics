# F1038 (user: wire the new carrier tools + explore the carrier conversion ladder) — **(1) THE NEW CARRIER TOOLS ARE WIRED — and the F1024 result-register turned out to GENERALIZE FROM Mat TO EVERY CARRIER for free (it keys on `type(last_result).__name__`, not a Mat special-case): `compute the magnetic laplacian of the edges 0-1 1-2 2-0` → Mat → `compute the heat trace of it at 1` → `heat_trace(Mat, 1.0) = 1.397` (scalar); `compute the unary theta …` → UnaryTheta → `compute the theta coefficients of it with n max 12` → the η/Euler coefficient list. One binding fix: the scalar-union `float | Sequence[float]` bound t=1 as `[1]` (the sequence alternative) → now prefers the scalar branch when a bare scalar is present. (2) THE CARRIER CONVERSION LADDER, MAPPED AND FRAMED: the tool_schema producer/consumer census exposes the coherency gap the user sensed — BiPoly (0 producers / 2 consumers) and TriPoly (0/1) are ORPHAN inputs (the plain non-q Zeilberger/WZ/Apagodu row can't be built; `bipoly_from_coeffs`/`tripoly_from_coeffs` MISSING), and there are no promote/project ops between rungs. THE FRAMING: the carriers ARE Hurwitz/dimension-laddered objects — Poly(1)→BiPoly(2)→TriPoly(3); ℝ→ℂ→ℍ→𝕆→𝕊 (1:2:4:8:16 = the 2:4:8 / 1:3:7:3 structure) — so the conversion ladder IS the embed(promote)/project(drop-trivial-dimension) between adjacent rungs. The register is the translation layer; with promote/project it becomes the conversion ladder. FILED → #1248.**

**Date:** 2026-07-03 · **srmech:** 0.9.0rc113 · **Branch:** `research/rbs-lm-rolling-2` (PR #687); siona synced to PR #1 · **User direction:** "wire the new carrier tools into siona's conversational drive … we have a wonderful arrangement of carriers but we seem to lack some coherency handling between our operations … make like a conversion ladder for carriers like we have for our 1:3:7:3, 2:4:8, mock-theta." · **Files:** `siona/infer.py` (scalar-union binding in _fit + _bind_args), `siona/tests/test_synthesis_wiki_kernel_trig.py` (carrier-chain test), UPSTREAM §86 · **Composes:** F1024 (the register that generalized), F1037 (the rc113 tools), F1027/F1039-to-be (the mock-theta pipeline), the 1:3:7:3 / 2:4:8 partition (CLAUDE.md §1 — the ladder the carriers instantiate), `[[feedback_introspect_srmech_before_python_dispatch]]` (the census IS the introspection that found the gap).

## Grounded (rc113)
```
WIRED (register generalizes, no per-carrier code):
  magnetic laplacian ... -> Mat ; heat trace of it at 1 -> heat_trace(Mat, 1.0) = 1.397  (scalar-union fixed)
  unary theta ...        -> UnaryTheta ; theta coefficients of it n max 12 -> [1,-1,-1,0,0,1,...]
THE COHERENCY MAP (tool_schema census):
  carrier    producers  consumers
  BiPoly        0          2 (zeilberger, wz_certificate)   ORPHAN INPUT
  TriPoly       0          1 (apagodu_zeilberger)           ORPHAN INPUT
  QPoly/QBiPoly/UnaryTheta/EllRatio: have both, thin
  constructors: poly/qpoly/qbipoly_from_coeffs EXIST ; bipoly/tripoly_from_coeffs MISSING
```

## The reading (the framework closure)
- **The carriers are the 1:2:4:8:16 ladder made into types.** Poly/BiPoly/TriPoly is the variable-count
  ladder; ℝ/ℂ/ℍ/𝕆/𝕊 is Cayley–Dickson = the 2:4:8 doubling the notebooks already study. The "coherency
  handling between operations" the user asked for is exactly the **promote/project rungs**: a Poly IS a
  BiPoly with a degree-0 second variable (promote adds it; project drops it iff trivial). The conversion
  ladder for carriers is not a new structure — it is the SAME Hurwitz ladder, applied to the carrier types.
- **The register is already the translation layer**, and it generalized for free — a returned carrier flows
  into the next tool's matching-typed slot regardless of type. Today it passes carriers UNCHANGED; the
  missing piece is srmech promote/project so it can route a lower-rung carrier UP to a higher-rung consumer.
  That is the whole coherency ask (#1248): with it, "give me the sparse form" over a Poly can reach
  `zeilberger` (which wants BiPoly) because a univariate promotes trivially.
- **The gap is precisely located, not vague:** two missing constructors + two promote/project families.
  BiPoly and TriPoly aren't unbuildable by design — the rung is just absent.

## Verdict / next
**The new carrier tools drive conversationally (register generalizes to all carriers; scalar-union binding fixed); the carrier arrangement is mapped as the Hurwitz conversion ladder with the coherency gap located (orphan BiPoly/TriPoly + missing promote/project) and filed → #1248. Suite pending.** Next: on #1248 landing — siona's register auto-promotes a lower carrier to a higher-rung consumer (the conversion ladder as coherency handling); the mock-theta pipeline reaches the non-q Zeilberger row.
