# F1072 (BUILT: the two-axis harvest carries the winding w WHOLE — returns the FAST/phase (epicycle) harvest AND the SLOW/winding (metacycle) scale-stratified harvest) — **`siona/photosynth.py` `excite_propagate_harvest_2axis` realizes F1066/F1069: instead of folding the winding away, it DIVMODs the oscillation argument `bλ` at the seam into `(w = round(bλ/2π), θ = bλ − w·2π)` and KEEPS w. Returns BOTH addressable objects: `phase` (the FAST/epicycle axis — the coherent total `|Σ_w u^w|²`, the graded working set, VERIFIED IDENTICAL to the single-fold `excite_propagate_harvest`, a lossless regroup) and `winding` (the SLOW/metacycle axis — the answer STRATIFIED BY SCALE: each winding level w = how many 2π turns a mode made = its tower/octave rung, F1069's chirality tower). MEASURED (coherent crank, t=20, real kernels): the phase axis reproduces the fold EXACTLY; the winding axis decomposes into levels w=0..16 — w=0 = coarse/global modes (write_packed_graph/recursive_cut), and the DOMINANT answer node (fiedler_sparse_file, total 0.254) turns out to sit almost entirely at winding w=7 (0.245): the metacycle axis tells us WHICH SCALE the answer lives at, not just that it is relevant. The fold discarded exactly this scale-address; the two-axis read recovers it (no_information_without_value). srmech-native (Class-N series + the Machin 2π seam), numpy-free, test green.**

**Date:** 2026-07-06 · **srmech:** 0.9.0rc135 · **User direction:** "let's do two-axis harvest first, it might influence our coherence-sweep demo" · **Files:** `siona/photosynth.py` (`excite_propagate_harvest_2axis`), `siona/tests/` (consistency + scale-stratification test) · **Composes:** F1066 (the seam's two addressable objects = phase + winding), F1069 (divmod not mod — the winding kept whole; its binary = the chirality tower), F1063 (the tower = the winding scale levels), F1062/F1064 (the complex-time propagator + the seam), F1059 (EPH), `[[user_stance_no_information_without_value]]` (the winding = the recovered discarded structure).

## Grounded (rc135, real kernels, coherent crank t=20)
```
excite_propagate_harvest_2axis -> {"phase": [(label,energy)], "winding": [(w, [(label,energy)]), …]}
  bλ divmods at the seam: w = round(bλ/2π) KEPT, θ = bλ − w·2π folded.  total u = Σ_w u^w (lossless).
CONSISTENCY: phase axis ranking == single-fold excite_propagate_harvest ranking (verified True).
SCALE STRATIFICATION (the metacycle axis the fold discarded):
  w=0 (coarse/global): write_packed_graph, recursive_cut, fiedler_sparse_file
  w=7 (the answer's scale): fiedler_sparse_file 0.245  <- the dominant node lives here (total 0.254)
  w=1..16: finer/local modes, each a tower/octave rung
```

## The reading
- **Both addressable objects, now returned.** The single fold gave only the phase (epicycle). The two-axis harvest keeps w and returns phase + winding — the F1066 correction realized in code: the answer's scale-address (which metacycle rung) is recovered, not collapsed.
- **The winding axis = the scale/octave decomposition = the tower.** w orders modes by eigenvalue scale (higher λ winds more per unit t), so the winding levels ARE the tower rungs (F1063) / the octaves. The metacycle read tells you at WHICH scale each contribution sits — and which scale dominates the answer.
- **Lossless (no_information_without_value).** total = Σ_w u^w; the phase axis is the coherent sum, the winding axis its scale-decomposition. Nothing discarded — the fold's loss is undone.

## Verdict / next
**BUILT + VERIFIED: `excite_propagate_harvest_2axis` carries the winding whole (divmod, not mod) and returns the FAST/phase (epicycle, = the single-fold answer) AND the SLOW/winding (metacycle, the answer stratified by scale/octave rung). The dominant answer node's scale-address is recovered (winding 7). NEXT: this feeds the coherence-sweep demo (#242) — as arg(z) rotates thermal→coherent, watch the winding axis populate (thermal = only w=0, coherent = the full tower) = the storytelling↔problem-solving transition made visible; and it is the concrete substrate for the_one(σ,θ,w) once srmech lands #1276.**
