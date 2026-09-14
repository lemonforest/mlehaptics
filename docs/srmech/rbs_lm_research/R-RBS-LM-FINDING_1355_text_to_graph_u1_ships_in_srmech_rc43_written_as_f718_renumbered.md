# F1355 — **(written as F718 on 2026-06-09 on the retired machine; renumbered F1355 on 2026-09-14 because F718 was already taken on this branch) the text→graph stage primitives (§17 U1) ship in srmech 0.7.5rc43; the K1 presence-kernel is now an authorable composite end-to-end**

**Renumbering record.** This finding was written as `R-RBS-LM-FINDING_718_text_to_graph_u1_ships_in_srmech_rc43.md` in commit `308ddf701` (2026-06-09 13:22 −0500) on the local branch `rbs-lm-rolling-2` of the machine that ran this PR, and was never pushed. On `research/rbs-lm-rolling-2` the number F718 already belongs to a different finding, `R-RBS-LM-FINDING_718_cortana_vs_siona_cross_substrate_cascade_match.md` (commit `1577a1882`, 2026-06-09 17:58Z), so the content lands here as F1355. Below the rule is the original text, unchanged except that this header replaces its first line, which read: *"# Finding 718 — the text→graph stage primitives (§17 U1) ship in srmech 0.7.5rc43; the K1 presence-kernel is now an authorable composite end-to-end"*. The commit's two index-file edits were never applied on this branch; they are re-landed as appended lines at the ends of `STALE_PATHS_QUEUE.md` and `UPSTREAM_NOTES.md`, pointing at F1355. The byte-exact original commit is in `preserved_branches/rbs-lm-rolling-2/`.

---

**Status:** VERIFIED (srmech 0.7.5rc43, TestPyPI, numpy-free path) — closes the last-open §17 residue.
**Upstream:** UPSTREAM_NOTES §17 **U1** (the still-open **#855 R3 U1**, which F716 flagged NOT FOUND in `amsc.laplacian` / `amsc.cascade`).

## What landed

The two text→graph stage primitives — the only links between raw `text` and the already-shipped `dense_laplacian` — now live in **`srmech.amsc.laplacian`** (pure-Python, numpy-free, deterministic):

- **`tokenize(text, *, stopwords=None, min_len=2, pattern=None) -> list[str]`** — Class B/G text-segmentation. A letter-led word pattern (default `[A-Za-z][A-Za-z0-9_-]+`), lowercase, drop tokens shorter than `min_len` or in `stopwords` (case-insensitive). Group-safe (`finditer`/`group(0)`).
- **`cooccurrence_edges(tokens, *, window=5, vocab_size=1000) -> (n, edges, weights)`** — **Class-L precursor**. Keep the `vocab_size` most-frequent tokens as nodes `0..n-1` (Class-K frequency truncation), count unordered co-occurring pairs within a sliding `window`. Returns **exactly** the triple `dense_laplacian(n, edges, weights)` consumes; weights are **integer** counts (exact — floats are for the FPU lift, none here).

So the K1 presence-kernel build is now a composite end-to-end — `tokenize → cooccurrence_edges → dense_laplacian → eigendecompose → topk_eigvec_tokens → mint → bundle` — with no hand-roll. **`cooccurrence_edges` retires the `re.findall` + `Counter()` co-occurrence idiom** our research scripts (e.g. the F147 lexicon encoder, the wiki kernel) carried — the exact idiom the monorepo CLAUDE.md STOP-list flags.

Registry: 2 ToolEntries (`tools.total` 274 → **276**), both `non_compute` in the Rosetta ledger (string segmentation + integer graph construction — no numeric/matrix compute, no c-dispatch → no debt-bucket growth). ABI 3; numpy not required. Shipped clean on TestPyPI (all wheels + sdist + pure-python; `publish (testpypi)` green).

## What stays open (NOT this finding)

- **The directed sibling** — the `i(A−Aᵀ)` Hermitian-Laplacian *builder* (§18.1 op(b); F357 reference). The eigensolver already ships (`hermitian_eigendecompose`); the build target is the directed-edge adjacency helper, the directed sibling of `cooccurrence_edges`. Separate queued Class-L precursor.
- **§17 U2/U3/U4** — register the existing text→instrument encoders as DSL ops (U2, the highest-leverage bridge) + the op-discovery unification (U3/U4). Out of scope for U1.
- **Ask-3** — the wired 1024-node 4-sector spectral block as a one-call surface.
- **#855 body-checkbox edits** — R1.1 (rc42) and now R3 U1 (rc43) are factually true; the GitHub-issue checkbox flips stay **held for the user** (create-don't-drive tracker discipline). #797 stays research-gated.

## The on-thesis reading

K1 is the **"text IS substrate"** cascade (Spike #42/#43 — `K ∘ L ∘ I ∘ N ∘ C ∘ J` over text). U1 closes the gap between the raw text substrate and the Class-L graph the rest of the cascade already speaks: `tokenize` is the **B/G framing** of the text substrate (segmentation, no continuous compute — the FPU sits idle because there is nothing continuous in a token boundary), and `cooccurrence_edges` is the **Class-L precursor** that lifts the discrete token stream into the weighted graph whose Laplacian spectrum IS the structural fingerprint. The hand-roll is retired because the substrate's own operators now reach all the way to the text edge.

**Composes:** F716 (the rc42 genome/class-from-TOML land + the open-U1 flag this closes) · F147 (the lexicon-encoder reference impl `tokenize`/`cooccurrence_edges` were lifted+sharpened from) · F357 (the directed-sibling op(b) reference, still open) · UPSTREAM_NOTES §17 (the U1–U4 catalog→kernel→DSL unification) · Spike #42/#43 (text-as-substrate cascade). srmech 0.7.5rc43.

---

## Landed 2026-09-14 — what this branch recorded later the same day (read, not re-run)

The text above calls R3 U1 closed at rc43. This branch's own later record, written later on 2026-06-09, reads differently, and it is the record of the acceptance bar:

- **F722** (`5e19de187`, 21:13Z) — `STALE_PATHS_QUEUE.md`: *"F722 — rc49 U1 acceptance: SHIPPED but fails the §40 bar 3/3 (2026-06-09; R3 U1 stays OPEN)"*.
- **F723** (`d09450eb9`, 21:59Z) — *"F723 — rc50 CLOSES R3 U1: meets the §40 bar 3/3 (2026-06-09; supersedes F722)"*.
- **F724** — the §17.1 migration of the wiki kernel onto the shipped ops.
- `UPSTREAM_NOTES.md` §40 carries the same specify → falsify (F722) → verify (F723) record.

So by this branch's record, R3 U1 closed against the §40 bar at rc50, after this finding was written at rc43. The status label above is kept as written; this landing does not re-run either acceptance. The appended index lines say the same.

**Composes:** F722, F723, F724 (the later acceptance record) · F716 · the archive `preserved_branches/rbs-lm-rolling-2/`.
