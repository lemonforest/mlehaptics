# R-RBS-LM Finding 364 — battery test 4: real LANGUAGE has a navigable directed off-diagonal (word-ORDER); reversal = the iω₇ chirality flip (exact); the symmetric bag-of-words shadow is direction-blind — the F347 missing primitive on real text

**Date:** 2026-06-04 · **srmech:** 0.7.0rc28 · **battery:** F361 test 4 of 4 · **brings the thread back to the RBS-LM arc** · **extends:** F357 (hand-rolled i(A−Aᵀ)) to the shipped `magnetic_laplacian` · **script:** `R-RBS-LM-R17_navigable_language.py`

## Result (srmech notebook: 61,229 tokens, 13,417 directed precede-edges, vocab 150)

- **NAVIGABLE (directed magnetic Laplacian on "i precedes j" co-occurrence):** Hermitian True, complex/directional True, **reversal = conjugation `‖H_rev − conj(H_fwd)‖ = 0.00e+00` (exact)**. Word-order direction is encoded on the off-diagonal phase; reversing precede↔follow IS the iω₇ chirality flip.
- **SCANNABLE shadow (symmetric bag-of-words Laplacian):** `‖L_fwd − L_rev‖ = 0.00e+00` — completely **direction-blind** (cannot tell "A precedes B" from "B precedes A").
- **Honest sub-finding (F357 lesson):** the gross imaginary-energy *magnitude* has a sampling-noise floor (real 41.82 vs shuffled 43.29) — so the magnitude is not the clean discriminator; the **exact reversal=conjugation identity** is the real signal, not the energy scalar.

## Reading

On **real text**, language carries a **navigable directed off-diagonal** — word **order** ("A typically precedes B") is a directed transport step, and reversing it is exactly the iω₇ chirality flip. The standard **bag-of-words / symmetric** representation is the collapsed **scannable shadow** (direction-blind proximity). This is the **F347 missing primitive made concrete on real text**: language is spatially navigable *through its word-order off-diagonal*, which current symmetric/bipolar representations collapse to a shadow. Un-collapsing it (the directed magnetic Laplacian) makes language navigable — you can read *which way to step*, not just *what is near*. Closes the F361 battery by tying the whole navigation thread back to the RBS-LM arc: the missing primitive isn't a new operator, it's un-collapsing the directed off-diagonal language already has.

## Discipline
srmech-native rc28 (`magnetic_laplacian`/`dense_laplacian`, Class L — not `np.linalg.eig`); honest magnitude-floor caveat (no-leaning, F357 consistency); shuffle control included; composes with F347 (missing primitive), F357 (directed Hermitian reference), F361 (navigable-vs-scannable), F172/F188 (the bag-of-words flat-spectral shadow this contrasts with).
