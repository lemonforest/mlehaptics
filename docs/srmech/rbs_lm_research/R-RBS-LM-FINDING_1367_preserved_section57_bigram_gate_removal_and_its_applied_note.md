# F1367 — **preserved: RBS-LM §57 — the baked-in bigram-count candidate layer replaced by a resonator over the bounded atom set, at 100% grounded recall; the code change reached this branch, its APPLIED note did not**

Consolidation record (2026-09-14). Source: local branch `fix/rbs-lm-bigram-resonator-s57`, one commit on no remote: `00abf81c3` (2026-06-17).

## What the commit found (its own words)

- The count-based bigram gate (`Counter` / `bigram_counts` / `next_after`) *"was a statistical-LM contaminant in what is otherwise a pure Class-M resonance inference path"*. It is removed in both the research origin `_rbs_lm_inference.py` and the package mirror `srmech/rbs_lm/inference.py`. The candidate set becomes the resonator over the substrate's own bounded atom codebook: `probe = klein4_unbind(M, encode_context(context[-k:]))` → `sim_k4_batch(probe, vocab_vecs)` → softmax. Per §56, `temperature <= 0` gives greedy argmax.
- **Acceptance** (*"the honest-risk gate — grounded next-token recovery from M ALONE, no n-gram gate, per-tome"*): **100%** greedy recall — 27/27, 57/57, 57/57, 117/117 over vocab ∈ {30,60,60,120} at D ∈ {16384,16384,32768,32768} — and the autoregressive `infer(T=0)` reproduces the grounded continuation. *"Recall did NOT degrade at per-tome scale."*
- Scope note, as written: numpy in that module is outside §57 and left untouched. The APPLIED note adds that the spec's "numpy-free already" line did not match the file at the time.

## Where it lives on PR #687

- The same §57 removal reached this branch as `c4b7d707a` (*"srmech 0.8.2rc1: §57 RBS-LM bigram-gate removal + numpy/Counter STOP-list ratchet"*, 2026-06-17). At `4db51be25` neither file contains `bigram_counts` or `next_after`, and F1286 / F1287 later reworked both files. All three paths DIFFER, so nothing was cherry-picked.
- The commit's appended **"APPLIED (2026-06-17, branch `fix/rbs-lm-bigram-resonator-s57`)"** paragraph in `UPSTREAM_NOTES.md` §57, which carries the acceptance figures above, is **not** in this branch's `UPSTREAM_NOTES.md`. Its only copy is the archive: `preserved_branches/fix__rbs-lm-bigram-resonator-s57/`.

## DIFFERS

- `docs/srmech/python/srmech/rbs_lm/inference.py` — the same removal landed through `c4b7d707a`, and the file has changed further since.
- `docs/srmech/rbs_lm_research/_rbs_lm_inference.py` — the same removal landed through `c4b7d707a`; F1287 (`52de8979e`) later repointed this local copy onto `srmech.rbs_lm`.
- `docs/srmech/rbs_lm_research/UPSTREAM_NOTES.md` — the file grew by later sections and lacks this commit's APPLIED note.

Branch safe to delete once this commit is on origin: yes

Integrated 2026-09-14: see F1373.
