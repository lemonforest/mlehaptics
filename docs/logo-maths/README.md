# logo-maths — HDC split-object pattern applied to LOGO

Python research spike that generalizes the chess-spectral
split-object-with-fiber-matrix pattern to a new domain. See
[logo_research_notebook.md](logo_research_notebook.md) for the full
experimental log and [../../docs/chess-maths/chess_spectral_research_notebook.md](../chess-maths/chess_spectral_research_notebook.md)
for the pattern's original write-up.

**Iteration 2 added (2026-04-14):** self-containment, F₁ HDC retrieval
fix (45% → 91% top-1), fiber-as-transport-map experiments (L6a–e),
three-body topology (L6f–h), and a retraction of iteration-1's L1
"reversibility via single-vector flip" claim.

**Iteration 3 added (2026-04-14):** held-out generalization (L7a,
4/4 PASS — L6d's D4 character claim survives the memorization gate)
and partial-trace fibers (L7b, 1/5 PASS — fibers drift with trace
length but do NOT extrapolate forward; snapshot baseline beats
fiber-prediction by 0.855 cos on spiral_square). The trajectory
hypothesis for chess needs reformulating before porting.

## Layout

```
logo_ast.py               AST node dataclasses + walk()
logo_parser.py            tokenizer + recursive-descent parser
logo_interp.py            tree-walk interpreter → Trace + rule firings
logo_irrep.py             D4 irrep projection (8 perms + char table) — self-contained
logo_hdc/
    hd.py                 MAP-B primitives (atom, bind, bundle_sum, sim, ...)
    quantum_atoms.py      Part A: command atoms + role-level unbind/swap
    codebook.py           Part B: structured rule HVs
    split.py              SplitObject (left + right + fiber)
    fiber.py              build_fiber_matrix, svd_report, fiber_to_hdc
                          (fiber_to_hdc has per-row L1 normalization, default on)
logo_encode_vocab.py      Part A encoder: program → vocab_lex/vocab_ctx HVs
logo_encode_syntax.py     Part B encoder: program → syn_lex/syn_ctx HVs
logo_encode_geometry.py   Part C encoder: trace → 320-dim D4-irrep HV
logo_corpus.py            21 hand-curated LOGO programs by family/symmetry
logo_build_splits.py      Corpus → F₁ coincidence stream
logo_fiber2.py            Syntax × geometry fiber; value-enriched features
logo_transport.py         Fiber-as-transport-map experiments + 3-body topology
logo_csv_export.py        Per-program CSV emitter (now with transport columns)
logo_py.py                CLI (parse / trace / encode / fiber1 / fiber2 / transport / csv)
samples/                  Generated artifacts (CSV, etc.)
```

## CLI quick-ref

```
python logo_py.py parse      square        # dump the AST
python logo_py.py trace      square        # turtle trace JSON
python logo_py.py encode     square        # channel-energy summary
python logo_py.py fiber1                   # F₁ SVD + per-row-normalized HDC retrieval
python logo_py.py fiber2                   # F₂ SVD + per-program self-sim
python logo_py.py transport                # polygon-pair transport table (default)
python logo_py.py transport --chain        # vocab → syntax → geometry chain
python logo_py.py transport --characterize # per-feature transport(N) D4 split
python logo_py.py transport --modes        # per-SVD-mode attribution
python logo_py.py transport --topology     # chain-collapse, holonomy, chirality
python logo_py.py transport --holdout pentagon,octagon    # L7a: rebuild fiber without those programs
python logo_py.py transport --partial 30,60               # L7b: fiber at N=30 predicting g at N=60
python logo_py.py transport --drift 10,60                 # L7b: fiber drift between anchors
python logo_py.py transport --spiral-extrapolate 10,60    # L7b.5: fiber vs snapshot baseline
python logo_py.py csv -o samples/corpus.csv
```

`src` args accept a filesystem path, a corpus entry name, or `-` for
stdin. The transport flags can be combined; `--pairs` accepts a
custom `a,b;c,d` list.

## Predictions tested

| Phase | Prediction | Outcome |
|-------|-----------|---------|
| L1 (iter 1) | `bind(a_FORWARD, flip) ≈ a_BACK` after cleanup | ✗ RETRACTED — measured cos −0.004 vs BACK; replaced with role-level `unbind_role` / `swap_role_value` (cos 1.0 exact for the swap) |
| L2 | Part A and Part B independently inferable | ✓ ≥ 80% cleanup on both |
| L3 | F₁ rank 3-4, interpretable modes, nullspace = inert rules | ✓ rank 7 (exceeded), modes semantic, nullspace correct |
| L3 (iter 2) | F₁ HDC retrieval recovers low-energy couplings | ✓ 5/11 → 10/11 with per-row L1 normalization |
| L4 | F₂ surfaces program output symmetry | ✓ in subdominant modes (after DC-mode deflation) |
| L4 | Polygon D4-irrep decomposition matches theory | ✓ pure A1 for Dₙ with n multiple of 4, A1+E split for D3/D5 |
| L6a (iter 2) | cos(Δg_pred_deflated, Δg_actual) > 0.30 for adjacent polygons | ✓ 6/6 pairs (worst 0.473) |
| L6b (iter 2) | deflated transport ≥ raw transport for ≥ 4/6 pairs | ✓ 4/6 |
| L6c (iter 2) | chain transport cos > 0.10 (square → spiral_square) | ✓ 0.516 |
| L6d (iter 2) | transport(N) qualitatively recovers D4 character class | ✓ for 4/12/5/3; messier for 8 and 6 (small-corpus artefact) |
| L6e (iter 2) | modes 4-7 carry > 80% of polygon transport energy | ✗ MISS — 47-60% across pairs; signal spread across modes 1, 3, 6, 7, 8 |
| L6f (iter 2) | chain collapse: cos ≈ 0.95 narrow → 0.99 wide | ≈ 0.99 / 0.99; rules already saturate the mediation budget at this corpus size |
| L6g (iter 2) | cycle holonomy cos ≈ 0.93, ‖Δ‖ ≈ 0.37 | ✓ 0.942 / 0.340 (rank-1 cycle SVD: s_1/s_0 ≈ 0) |
| L6h (iter 2) | small chirality commutator (corpus-bias caveat) | 0.082 — near-symmetric with small chiral signal |
| L7a.1 (iter 3) | `transport(5)` A1+E share drifts ≤ 20pp under holdout(pentagon,octagon) | ✓ 0.1pp (86% → 85%) |
| L7a.2 (iter 3) | `transport(8)` A1 fraction ≥ 50% under holdout | ✓ 69.7% (actually *grows* from 60%) |
| L7a.3 (iter 3) | `|transport(5/8)|` norms don't collapse (≥ 30% of full) | ✓ 0.727 / 1.077 |
| L7a.4 (iter 3) | Pair cos under held-out fiber > 0.25 | ✓ triangle→pentagon +0.568 |
| L7b.1 (iter 3) | Polygon mean cos(pred, target) > 0.40 at (30, 60) | ✗ +0.307 |
| L7b.2 (iter 3) | Spiral  mean cos(pred, target) > 0.20 at (30, 60) | ✗ +0.085 |
| L7b.3 (iter 3) | Fiber drift `‖M_l − M_e‖_F / ‖M_e‖_F` > 0.10 between N=10 and N=60 | ✓ 0.250 |
| L7b.4 (iter 3) | Spiral-marker features (MAKE, repeat_n=60) dominate top-5 drift | ✗ generic structural rules dominate |
| L7b.5 (iter 3) | spiral_square: fiber-pred beats snapshot baseline by > 0.10 | ✗ **gain = −0.855** (fiber actively worse than "use earlier snapshot") |

## Dependencies

`numpy`. That's it. The spike is fully self-contained — no
sibling-package imports, no sys.path manipulation. The D4 projection
lives in [logo_irrep.py](logo_irrep.py).
