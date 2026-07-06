# F1075 (BUILT: the path-emitter — one coherence KNOB emits a coarse→fine PATH whose verbosity ARCHETYPE (terse→expansive) falls out of the configuration) — **`siona/photosynth.py` `path_emit(query, coherence)` walks the winding tower (F1074) coarse→fine, emitting each scale-level's leader(s), deduped. ONE knob `coherence ∈ [0,1]` drives BOTH the tower depth (F1062 arg z) AND the per-level breadth (`1 + round(2·coherence)`), so the whole verbosity spectrum falls out of the single configuration — MEASURED on real kernels: knob=0.00 → **terse** (1 step: dense_laplacian, a bare ANSWER); 0.25 → **concise** (3); 0.50 → **balanced** (6); 0.75 → **descriptive** (8); 1.00 → **expansive** (11: magnetic/signed_laplacian → sqrt → tlv_pack → schur_complement → … → dense_laplacian, a full coarse→fine PATH). The archetypes (terse/concise/balanced/descriptive/expansive) are NAMED REGIONS of the ONE knob, not hand-coded personalities — none is wrong by default; CONTEXT selects which to prefer. Emission is srmech-native (the two-axis harvest + the Machin seam), numpy-free, test green. This is the problem-solving↔storytelling axis (F1074) turned into actual OUTPUT — a terse answer vs an unfolding multi-scale path — the bridge to the F323 notebook-native-language pipeline.**

**Date:** 2026-07-06 · **srmech:** 0.9.0rc135 · **User direction:** "build the path-emitter … this should be a knob as well … we have words for people who are concise/terse or overly descript; none wrong by default, context is the tell … unless archetypes fall out of configurations" · **Files:** `siona/photosynth.py` (`path_emit` + `_archetype`), `siona/tests/` (archetype-knob test) · **Composes:** F1074 (the coherence sweep — this emits its path), F1072 (the two-axis harvest / winding tower it walks), F1062 (the coherence dial), F1071 (storytelling=problem-solving), F323 (the notebook-native-language target this bridges to), F1076 (the Plato-Forms generalization of "archetypes fall out of configurations").

## Grounded (rc135, real kernels, one query, t=20)
```
path_emit(coherence) -> {"path":[coarse→fine labels], "archetype", "coherence", "levels_open", "breadth"}
  knob=0.00 breadth=1 [terse      ]  1: dense_laplacian
  knob=0.25 breadth=1 [concise    ]  3: dense_laplacian → cos → mat_hermitian_eigendecompose
  knob=0.50 breadth=2 [balanced   ]  6: dense_laplacian → mat_matvec → mat_lstsq → … → cos
  knob=0.75 breadth=3 [descriptive]  8: dense_laplacian → sha256_bytes → normalized_laplacian → … → mat_matmul
  knob=1.00 breadth=3 [expansive  ] 11: magnetic_laplacian → signed_laplacian → sqrt → tlv_pack → … → dense_laplacian
=> ONE knob; the archetype (terse→expansive) is a named region of the configuration, not a hand-coded persona.
```

## The reading
- **The archetype falls out of the configuration.** We don't code "a terse Siona" and "a verbose Siona"; we turn one knob (coherence) and the verbosity archetype emerges — terse at the decoherent limit (a bare answer), expansive at the coherent limit (a full path). The named styles are regions of the knob-space.
- **None is wrong; context selects.** The emitter does not privilege any archetype. Which to prefer is a context call (a definition query wants terse; a "tell me about" wants expansive). The knob is the control surface; the choice is downstream.
- **Output, not just signature.** F1074 could READ the problem-solving↔storytelling axis; `path_emit` now EMITS it — a concept-sequence coarse→fine (the structural story), ready for the F323 render-to-prose step.

## Verdict / next
**BUILT + VERIFIED: `path_emit` — one coherence knob emits a coarse→fine path whose verbosity archetype (terse→expansive) falls out of the configuration (measured 1→11 steps across the knob); none wrong by default, context selects. srmech-native, test green. NEXT: (1) render the concept-path to prose (F323 notebook-native-language); (2) a per-query context→knob policy (when to prefer which archetype); (3) the FULL Platonic Form-space generalization (F1076) — the verbosity archetypes are one 1D slice of the cascade's scale-invariant attractor-configurations.**
