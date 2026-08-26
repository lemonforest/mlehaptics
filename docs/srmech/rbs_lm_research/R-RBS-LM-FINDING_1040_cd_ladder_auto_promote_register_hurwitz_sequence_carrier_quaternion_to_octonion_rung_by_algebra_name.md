# F1040 (user: wire the cd-ladder auto-promote for the Hurwitz sequence-carrier path) — **the register now auto-promotes on the CAYLEY-DICKSON ladder too, completing the conversion-ladder coverage across BOTH carrier families: a cd element in the register (whose rung IS its length — R1/C2/H4/O8/S16, not a type name) is lifted UP to a Hurwitz consumer's rung via srmech `cd_promote`. Live: `compute the quaternion exp of 0.5` → a rung-4 quaternion in the register → `compute the octonion conjugate of it` → the quaternion is AUTO-PROMOTED 4→8 and `octonion_conjugate` runs on the length-8 octonion (conjugate negates the imaginary parts, exact-ℚ). THE TARGET RUNG IS THE ALGEBRA NAME: "octonion" IS the descriptor's dim-8 rung label (R/C/H/O/S ↔ real/complex/quaternion/octonion/sedenion) — declared, not guessed. siona only promotes UP; the duality-guarded downward projection stays srmech's (a lower-rung op named on a higher-rung register is not a cd bind).**

**Date:** 2026-07-03 · **srmech:** 0.9.0rc117 · **Branch:** `research/rbs-lm-rolling-2` (PR #687); siona synced to PR #1 · **User direction:** "wire the cd-ladder auto-promote for the Hurwitz sequence-carrier path." · **Files:** `siona/infer.py` (`_cd_rung` / `_cd_target` / `_cd_promote_ref`; the cd ref-fit in _fit + the cd bind branch in _bind_args), `siona/tests/` (cd-ladder test) · **Composes:** F1039 (the poly-ladder register auto-promote this parallels — same register, second ladder), #1248/carrier_ladder (the descriptor's `cayley_dickson` rungs), the 2:4:8 / 1:3:7:3 partition (the Hurwitz doubling this walks), `[[user_stance_epicycle_via_gear_plus_pin]]` (hypercomplex as the substrate's own ladder).

## Grounded (rc117)
```
STRUCTURAL DIFFERENCE from the poly ladder: cd carriers are numeric SEQUENCES (tuple/list of Fractions);
  the rung = the LENGTH (power-of-two <= 16), so type(obj).__name__ ('tuple') carries NO rung -- length does.
  Consumers (quaternion/octonion_conjugate/norm/...) accept plain sequences; the 'HV' type is loose.
TARGET RUNG = the op's ALGEBRA NAME: real1 complex2 quaternion4 octonion8 sedenion16 (the descriptor labels).
LIVE:
  'quaternion exp of 0.5'          -> [0.8776, 0.4794, 0, 0]  (rung-4 quaternion, in register)
  'quaternion conjugate of it'     -> quaternion_conjugate([...]) = [0.8776, -0.4794, 0, 0]  (same rung, direct)
  'octonion conjugate of it'       -> cd_promote(quaternion, 8) -> octonion_conjugate(len-8)
                                      = [0.8776, -0.4794, 0,0,0,0,0,0]  (4->8 AUTO-PROMOTED; conj exact)
```

## The reading
- **The register is now a conversion ladder over BOTH families** — the variable-count polynomial ladder (F1039) and the Cayley-Dickson dimension ladder (here). Same one register, same "route a lower carrier UP to the consumer's rung" principle; only the rung SIGNAL differs (poly: the type name; cd: the sequence length + the algebra-name).
- **The algebra name IS the rung, honestly.** Using "octonion" → dim 8 is not a heuristic guess — it is the descriptor's own R/C/H/O/S rung labelling in words. A univariate-vs-bivariate promote and a quaternion-vs-octonion promote are the SAME move (add trivial dimensions) on the two ladders the framework already studies (the 2:4:8 doubling).
- **Up-only, duality-respecting:** siona promotes toward the consumer's rung; it never downgrades (projection is duality-guarded and srmech's). A cd op naming a rung BELOW the register's is simply not treated as a cd bind — no silent collapse.

## Verdict / next
**The cd-ladder auto-promote ships: the register lifts a Hurwitz element UP to a consumer's algebra-named rung (quaternion→octonion 4→8 live, conjugate exact). The conversion ladder is now complete across the poly AND cd carrier families — the register is the translation layer over the whole 1:2:4:8:16 + variable-count structure.** Suite pending. Next: explicit-dim cd promotion ("promote it to a sedenion"); the mock-theta pipeline over the now-reachable non-q Zeilberger row; #1245 (genome) still in dev.
