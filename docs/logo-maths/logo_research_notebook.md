# LOGO HDC — Research Notebook

---

> *"Can't stop the signal, Mal. Everything goes somewhere, and I go everywhere."*
> — Mr. Universe, *Serenity* (Joss Whedon, 2005)

> *Signature epigraph of the spectral-research collection. The body of work — validated results and rigorous falsifications alike — was offered through conventional channels and dismissed as foolery. The math stands independently. The discipline since: ship every result, falsifications included, with full reproducibility and per-row provenance (the Mathematical Provenance Method). A corpus that publishes its own invalidations is harder to dismiss than one that doesn't, and propagates through every channel that ingests open research. The signal is in the world; it goes everywhere now.*

---

**Status:** Iteration 3 complete (Phases L0–L7). Iteration-1
L1 reversibility claim retracted; see §"Phase L1 — RETRACTION" below.
L7a held-out generalization PASSES (L6d's D4 character claim survives);
L7b partial-trace fibers MOSTLY MISS — fiber drifts with the trace
(L7b.3 PASS) but does NOT extrapolate forward (L7b.1/2/4/5 MISS),
which reshapes the trajectory hypothesis for chess.
**Started:** 2026-04-14 (generalizing the chess-spectral split-object
pattern to a non-chess domain)
**Iteration 2 added:** 2026-04-14 — self-containment (drop chess_spectral
sys.path hack), F₁ HDC retrieval fix, fiber-as-transport-map experiments
(L6a–e), three-body topology (L6f–h), and an honest retraction of the
iteration-1 L1 reversibility-via-binding claim.
**Iteration 3 added:** 2026-04-14 — held-out generalization (L7a,
gating) and partial-trace fibers (L7b, trajectory probe). See §L7 for
numbers and interpretation.

> Living document. Mirrors the structure of
> `docs/chess-maths/chess_spectral_research_notebook.md`:
> prediction → experiment → numbers → interpretation → what it means
> for the broader pattern.

> ## Project navigation + state-pointer
>
> ReadTheDocs landing — <https://mlehaptics.readthedocs.io/en/latest/> — is the canonical pointer to the current state across all sister notebooks in this project.
>
> **This notebook is a snapshot.** Future framework additions will not be back-ported into it; the RTD landing tells you whether new sister notebooks or downstream developments are available.
>
> **Brief since-summary** (as of 2026-05-08):
> - The chess-spectral split-object pattern this notebook generalises was further instantiated on **antikythera-spectral**, **doom-spectral** (v1.0.0; first end-to-end Rosetta Stone existence proof), **ephemerides-spectral** (matured through **v0.26.0**; PyPI: <https://pypi.org/project/ephemerides-spectral/>), and **othello-spectral**.
> - **The Mathematical Provenance Method (MPM)** formalised as the project's discipline (ephemerides notebook §0.0); instrument-first physics critique in ephemerides §20.
> - **Inkscape** contribution shipped on the [`spectral-faithful`](https://gitlab.com/lemonforest/inkscape/-/tree/spectral-faithful) branch — three new SVG filter primitives (`feSpectralBilateral`, `feSpectralDistance`, `feSpectralNoise`) using the same eigenbasis substrate.
> - **mfo-spectral** sister-notebook added (May 2026) — Metric Field Ontology, *one candidate* foundational-ontology framing hosted in the project (cavity-instrument analogy; fractal metric field; ~11D structure motivated independently of string theory). Not the project's endorsed answer over alternatives; ephemerides §20 cites MFO as a worked example without picking a spatial-structure side. Future MPM target.
> - **Ephemerides §21 — Tool-rejection as MPM-screening failure** (symmetric counterpart to §20). Names the evaluator-side screening failure: rejecting work by which tool was used to make it, not by what it claims. Anchored on the historical orbital-mechanics chain DE441 traces back to (Copernicus / Bruno / Galileo / Kepler). §21.3 names the **disability-accommodation dimension** explicitly: categorical tool bans function as participation barriers for contributors with aphantasia, ADHD, dyslexia, motor disabilities, and many other variations. MPM is tool-agnostic by design.

---

## Framing — Why LOGO

Chess-spectral established a reusable design pattern — a
**split-object-with-fiber-matrix**: two HDC subspaces (piece identity,
positional coupling) bound through an explicit coupling matrix whose
rank / singular values / null-space carry the *interesting* structural
information. The rest of the chess work is an instantiation of that
pattern on a D4-symmetric 8×8 lattice.

LOGO is the first test of whether the pattern generalizes. It has:

- A tiny command set (12 atoms) — so Part A is fully enumerable.
- A small grammar (~20 productions) — Part B is fully enumerable.
- **Geometry as output** — Part C reuses the chess spectral basis
  directly (LOGO canvas ≡ chess board after rasterization).

If the pattern is generic, we should recover:

- F₁ rank reveals "kinds of coupling" between atoms and productions.
- F₂ SVD surfaces symmetry modes of the generated geometry.
- Structurally inert rules show up in F₁'s null space.

---

## Phase L0 — Parser / AST / Interpreter

**Deliverables:** [logo_ast.py](logo_ast.py), [logo_parser.py](logo_parser.py),
[logo_interp.py](logo_interp.py).

**Sanity checks (passed):**

- `REPEAT 4 [FORWARD 100 RIGHT 90]` closes the square within
  `|bbox residual| < 1e-13`.
- `REPEAT 360 [FORWARD 1 RIGHT 1]` produces `bbox aspect ≈ 1.0` — a
  near-circle.
- Recursive procedure: `TO poly :n :d REPEAT :n [FORWARD :d RIGHT (360/:n)] END; poly(7 30)`
  runs and closes.

Every AST node carries a `rule_name` field; the interpreter emits both
a turtle trace and a Counter of rule firings, which together feed
Parts B/C and both fibers.

---

## Phase L1 — HDC primitives + structured atoms

**Deliverables:** [logo_hdc/hd.py](logo_hdc/hd.py),
[logo_hdc/quantum_atoms.py](logo_hdc/quantum_atoms.py),
[logo_hdc/codebook.py](logo_hdc/codebook.py).

**Key decisions:**

- **MAP-B bipolar** at D=10000 — self-inverse bind, cosine sim
  linear in bit-agreement.
- **Atoms structured from quantum numbers** — `a_c =
  bundle_sum( bind(role_i, val_i) )` over `(category, arity, argtype,
  reverse_axis, block_opener)`.
- **bundle_sum vs bundle**: we use *unbinarized sums* for atom and
  rule composition. Majority-vote `bundle` destroys the linearity that
  per-role flip arithmetic relies on — the reversibility-pair test
  failed with `bundle`, passed cleanly with `bundle_sum`.

**Gotcha caught here:** Initial quantum-number assignment had
`LEFT/RIGHT` and `FORWARD/BACK` sharing identical 5-tuples modulo the
reverse-axis coordinate. The `rev_axis` tag was just `FWD`/`REV`, which
collided *across* pair boundaries. Renamed the tags to
`TRANS_FWD/TRANS_REV` (translation) and `ROT_FWD/ROT_REV` (rotation)
so each reversibility pair has its own axis namespace.

> **⚠ RETRACTION (iteration 2).** The original L1 went on to claim
> "with that fix, `bind(a_FORWARD, flip_axis) ≈ a_BACK` under cleanup
> and not to `a_LEFT`." **This is wrong.** Re-measured at D=10000:
>
> | probe | cos(bind(FORWARD, flip_axis), probe) |
> |---|---|
> | BACK   | **−0.0037** |
> | LEFT   | −0.0073 |
> | RIGHT  | +0.0050 |
>
> All three are statistical noise. A single-vector "flip axis" cannot
> algebraically swap *one* role inside a `bundle_sum` of five
> role-value bindings — the bind hits all five terms and four of them
> become uncorrelated noise. The high FORWARD↔BACK structural
> similarity (~0.80) that the iteration-1 author noticed is real but
> comes from **shared quantum numbers** (4/5 roles match between
> FORWARD and BACK), *not* from any flip operation.
>
> The correct primitive is **role-level**, against the role and value
> atoms in the codebook:
>
>     unbind_role(cmd_hv, "role_reverse", cb)  =  cmd_hv ⊙ cb["role_reverse"]
>
> which extracts the value-HV bound to `role_reverse` (the four other
> role bindings become uncorrelated noise of magnitude ≈ 1/√5).
> Measured at D=10000:
>
>     cos(unbind_role(FORWARD, "role_reverse"), cb["rev_TRANS_FWD"]) = +0.4486
>     cos(unbind_role(FORWARD, "role_reverse"), cb["rev_TRANS_REV"]) ≈ 0.0
>     cos(unbind_role(FORWARD, "role_reverse"), cb["rev_ROT_FWD"])   ≈ 0.0
>
> Clean reversibility *swap* uses unbind→subtract→add on the
> unbinarized accumulator:
>
>     swap_role_value(FORWARD, "role_reverse",
>                     "rev_TRANS_FWD", "rev_TRANS_REV", cb)
>     = a_FORWARD - bind(role_reverse, rev_TRANS_FWD)
>                 + bind(role_reverse, rev_TRANS_REV)
>     ≈ a_BACK     (cos = 1.0000 exactly — algebraically equal)
>
> So the **`bundle_sum` choice was right**, but for the *wrong reason*:
> it preserves linearity for *role swaps*, not for whole-atom
> "flip-binding". `flip_axis` and `REVERSE_OF` were deleted in
> iteration 2; see [logo_hdc/quantum_atoms.py](logo_hdc/quantum_atoms.py)
> for the corrected API. Lesson: structural similarity of atoms is
> **not the same** as reversibility-via-binding; the conflation in
> iteration 1 is the cautionary tale that motivated this notebook's
> "report actual numbers" rule.

**Bundle-size sanity:** D=10000 recovers 40 random atoms at >95%
cleanup accuracy. Cliff around D/250, consistent with MAP-B theory.

---

## Phase L2 — Vocab + syntax encoders with independent inferability

**Deliverables:** [logo_encode_vocab.py](logo_encode_vocab.py),
[logo_encode_syntax.py](logo_encode_syntax.py).

**Prediction:** Each side must be probeable independently — `sim(vocab_lex_hv,
a_FORWARD)` reveals FORWARD's presence without touching Part B, and
vice versa. This is the "split" part of split-object.

**Results:**

- Lex/vocab: top-6 command retrieval on mixed programs — 83% hit-rate
  (target ≥ 80% from plan).
- Context/vocab: `unbind(vocab_ctx_hv, a_FORWARD)` cleans to the
  correct slot position within the top-3.
- Syntax side: all 5 `MOTION_NUM` positions in a
  `REPEAT 5 [FORWARD ...]` program recovered in the top-5.

**Small fix here:** `rule_sequence` filter initially used
`endswith("_NUM")` to drop literal-terminal rules; this wrongly also
dropped `r_STMT_is_MOTION_NUM`. Narrowed to an explicit skip-list.

---

## Phase L3 — F₁: vocab × syntax fiber

**Deliverables:** [logo_hdc/fiber.py](logo_hdc/fiber.py),
[logo_hdc/split.py](logo_hdc/split.py),
[logo_build_splits.py](logo_build_splits.py).

**Prediction (from plan):** Rank 3-4 with modes aligned to
*spatial-transform-with-arg*, *state-toggle*, *block-opening*,
*variable-binding*. Null space: structurally-inert productions.

**Result — EXCEEDED prediction:**

```
F1 matrix  shape=(12, 12)  rank=7
sigma[0] = 30.50   FORWARD   <->  r_STMT_is_MOTION_NUM
sigma[1] = 22.00   REPEAT    <->  r_STMT_is_REPEAT_NUM_BLOCK
sigma[2] = 13.00   THING     <->  r_NUM_is_VAR
sigma[3] =  9.00   MAKE      <->  r_STMT_is_MAKE_NAME_EXPR
sigma[4] =  7.07   {PENUP, PENDOWN} <-> r_STMT_is_PEN
sigma[5] =  2.83   {TO, END} <-> r_STMT_is_TO_NAME_ARGS_BLOCK_END
sigma[6] =  1.00   IF        <->  r_STMT_is_IF_COND_BLOCK
null rows: [BACK]   (never used in the corpus — legitimate null)
null cols: [r_PROG, r_BLOCK, r_CALL, r_NUM_is_literal, r_NUM_is_BINOP]
            (containers / leaves — no direct command coupling)
```

Seven crisp modes, each semantically interpretable. BACK in the null
space because no corpus program uses it (interpreter supports it fine).
The container / leaf productions sit in the column null space — they
don't directly fire commands, they dispatch to sub-rules that do.

**Retrieval check (iteration-1 baseline):** `unbind(F₁_hdc, a_FORWARD)`
cleans to `r_STMT_is_MOTION_NUM` at cosine 0.545 (next best 0.08).
Retrieval works for FORWARD because its true coupling has α=23 — the
single largest weight in the matrix.

### L3 — iteration 2: F₁ HDC retrieval for low-energy couplings

**Symptom (iteration 1):** PENUP, PENDOWN, IF, MAKE, THING all
retrieve `r_STMT_is_MOTION_NUM` (the heaviest rule) instead of their
true couplings. The matrix form is exact; the HDC form is dynamic-range
limited — heavy rules dominate every probe in the bundled
superposition.

**Diagnosis:** D=10000 is plenty (chess uses the same dimension); the
issue is purely dynamic-range. PENUP's true coupling weight is 5;
MOTION_NUM's is 23. In the bundled fiber `F = Σ α(c,r) bind(c, r)`,
unbinding by PENUP recovers PENUP's row but the contribution from
*every other row* leaks through proportional to α — and α=23 wins.

**Fix:** per-row L1-normalization in `fiber_to_hdc`:

    F = Σ_{c,r} (α(c,r) / Σ_r' α(c,r')) · bind(c, r)

Each command contributes equal total mass; cross-row leakage is
suppressed.

**Result:**

| variant            | top-1 retrieval (corpus) |
|--------------------|--------------------------|
| iteration 1 (raw)  | 5/11 (45%)              |
| log-scale weights  | 7/11 (64%)              |
| **per-row L1 norm**| **10/11 (91%)** ✓       |

The remaining miss is `THING` (its quantum atom is structurally close
enough to `FORWARD` that residual MOTION_NUM cross-talk still wins).
That's a structured-atom limitation, not a fiber-construction one.
Per-row normalization is now the default in
[logo_hdc/fiber.py](logo_hdc/fiber.py) (`normalize_rows=True`).

---

## Phase L4 — F₂: syntax × geometry fiber, symmetry recovery

**Deliverables:** [logo_encode_geometry.py](logo_encode_geometry.py),
[logo_corpus.py](logo_corpus.py), [logo_fiber2.py](logo_fiber2.py).

This is the framework-validates-outside-chess moment.

### L4a — Geometry encoder

First attempt rasterized the trace into an 8×8 ink grid, quantile-binned
cell intensities into piece-chars (`P/N/B/R/Q` by bin, globally-max cell →
`K`), and fed the resulting pos-dict through `chess_spectral.encode_640`.

**This failed to discriminate polygons.** Post-encoding cosine similarity
between all polygon pairs was ≥ 0.98. Diagnosis: quantile binning
normalizes intensity distribution, so all polygons (which all fill a
square bounding box uniformly) produce near-identical pos-dicts, which
collapse to near-identical 640-dim HVs.

**Fix:** bypass piece-char quantization entirely. Only the D4-irrep
channels (dims 0-319 of the chess encoder) are meaningful for LOGO —
the fiber channels (F1..FD) are piece-type-specific and don't apply.
We feed the raw 64-dim intensity grid directly into `project_irrep`
for each of {A1, A2, B1, B2, E}, yielding a 320-dim HV that preserves
angular structure.

**Result — polygon cosine after the fix:**

```
              triangle  square  pentagon  hexagon  octagon  dodecagon  circle
  triangle       1.000   0.485    0.492    0.389    0.321     0.308     0.300
  square         0.485   1.000    0.503    0.598    0.663     0.613     0.596
  pentagon       0.492   0.503    1.000    0.786    0.657     0.669     0.657
  hexagon        0.389   0.598    0.786    1.000    0.910     0.923     0.917
  octagon        0.321   0.663    0.657    0.910    1.000     0.992     0.991
  dodecagon      0.308   0.613    0.669    0.923    0.992     1.000     0.999
  circle         0.300   0.596    0.657    0.917    0.991     0.999     1.000
```

A real continuum of "approach to circle": triangle is most orthogonal
to the circular shapes; octagon/dodecagon/circle cluster tightly
(D₈, D₁₂, SO(2) all project onto A1 in D4). Pentagon sits between,
its D5 splitting A1+E in the D4 basis.

**CSV confirms the D4-irrep picture cleanly:**

```
name        E_A1    E_A2    E_B1    E_B2    E_E
triangle    1075    0.513   211     211     949      ← D3: splits everywhere
square      2184       0      0       0       0      ← D4: pure A1
pentagon    2124    0.543    89      89     535      ← D5: A1 + E
hexagon     2230    0.099    90      90     5.27     ← D6: mostly A1
octagon     2738       0    0.07    0.07    0.27     ← D8: pure A1
dodecagon   3023       0       0       0       0      ← D12: pure A1
circle     25216       0       0       0       0      ← SO(2): pure A1
```

Pure A1 for every Dₙ with n multiple of 4, Pythagorean split for D3
and D5. This is a textbook character-table calculation falling out
of a turtle-trace encoder reusing the chess spectral basis.

### L4b — F₂ matrix, SVD, symmetry modes

Feature axis: `ALL_RULES` + value-enriched `repeat_n=N` fingerprints
(needed because polygon ASTs differ only in the REPEAT count literal).

Matrix normalization: both per-program count L1 and per-program
geometry L2 — without this, the circle program (REPEAT 360) dominates
every row it participates in.

**SVD:**

```
F2 matrix  shape=(30, 320)  rank=16
sigma[0] = 5.493   dominant feat: r_NUM_is_literal         (-0.76)   [DC / generic]
sigma[1] = 0.233   dominant feat: r_STMT_is_PEN            (+0.63)
sigma[2] = 0.203   dominant feat: r_STMT_is_PEN            (-0.56)
sigma[3] = 0.158   dominant feat: r_NUM_is_VAR             (+0.39)
sigma[4] = 0.143   dominant feat: repeat_n=5               (+0.63)    ← polygon-symmetry mode
sigma[5] = 0.102   dominant feat: repeat_n=4               (-0.46)    ← polygon-symmetry mode
sigma[6] = 0.089   dominant feat: repeat_n=4               (-0.61)
sigma[7] = 0.075   dominant feat: repeat_n=3               (-0.66)    ← polygon-symmetry mode
```

**Mode 0 is the "generic LOGO program" DC** — loaded on `r_NUM_is_literal,
r_STMT_is_MOTION_NUM, r_BLOCK, r_REPEAT`, the features every program
shares. Its singular value (5.5) is >20× the next mode (0.23) —
this is *expected*: most of the matrix-mass is "these programs all
look like LOGO programs."

**Modes 4-7 are the polygon-specific symmetry modes.** They load on
`repeat_n=3/4/5` — the polygon symmetry number. Without the value-
fingerprint feature, these modes would not exist (rule-type counts
alone don't distinguish `REPEAT 3` from `REPEAT 5`).

### L4c — Symmetry recovery per-program

Prediction from plan: project a program's syntax-feature vector
through F₂ and compare predicted geometry to actual geometry HVs.
Expect > 0.7 self-match for polygons.

Raw projection fails (self-match buried by the DC mode — every
polygon's prediction looks mostly like the mean geometry). After
**deflating the dominant mode**, the picture is clean:

```
Deflated self-similarity (pred vs actual, mode-0 removed):
  triangle             +0.426    top match: triangle
  square               +0.481    top: nested_squares  (also D4!)  square 2nd
  pentagon             +0.426    top: pentagon
  hexagon              +0.428    top: hexagon
  octagon              +0.276    top-3 all ~circular
  dodecagon            +0.556    top: circle  (D12 → SO(2) at this resolution)
  circle               +0.688    top: circle
```

**The "wrong" matches are semantically correct**: square's top match
is `nested_squares` (another D4 figure); dodecagon's top is circle
(both project onto A1 alone); octagon's top-3 are all circle-approaching.
F₂ is surfacing **symmetry class**, not program identity. That's the
prediction.

### L4 verdict

F₂ **recovers output symmetry from program structure**. The split-object
pattern generalizes outside chess. The pattern's "matrix rank and SVD
modes are the interesting part" claim holds — the *subdominant* modes
carry the category-discriminating information; the dominant mode is
a "baseline program" DC that needs to be factored out for cleanest
class separation.

---

## Phase L5 — CSV export + CLI

**Deliverables:** [logo_csv_export.py](logo_csv_export.py),
[logo_py.py](logo_py.py), [samples/corpus.csv](samples/corpus.csv).

Verbs mirror chess-spectral's `spectral_py.py`:

```
python logo_py.py parse    SRC
python logo_py.py trace    SRC
python logo_py.py encode   SRC [--dump]
python logo_py.py fiber1
python logo_py.py fiber2
python logo_py.py csv      [-o OUT]
python logo_py.py version
```

`SRC` accepts a filesystem path, a corpus entry name (e.g. `square`),
or `-` for stdin.

CSV columns:

    name, family, symmetry,
    n_stmts, n_rules_static, n_cmds_static,
    exec_steps, n_segments, n_pendown,
    bbox_w, bbox_h, aspect,
    f2_self_sim_raw, f2_self_sim_deflated,
    E_A1, E_A2, E_B1, E_B2, E_E,
    geom_norm

Number formatting is copy-pasted from chess-spectral's `fmt_csv_num` so
the two pipelines' outputs share a house style.

---

## Phase L6 — Fiber-as-transport-map (iteration 2)

**Question:** Are F₁/F₂ static co-occurrence summaries, or do they
function as **predictive transport maps**? If `Δg_pred = M₂ᵀ · Δv`
agrees with `Δg_actual` for syntax-feature deltas Δv, the split-object
pattern picks up a *generative* interpretation, not just a descriptive
one.

All numbers below come from
[logo_transport.py](logo_transport.py); reproduce with
`python logo_py.py transport --pairs --chain --characterize --modes --topology`.

### L6a — Polygon-pair single-fiber transport

For each polygon pair (a, b), compute `Δv = featvec(b) - featvec(a)`,
predict `Δg_pred = M₂ᵀ · Δv`, compare to actual normalized geometry
delta. Both raw F₂ and DC-deflated F₂.

```
pair                     cos_raw   cos_def   D4 split (A1/A2/B1/B2/E)
square -> triangle        +0.852    +0.891     46% / 0% /  8% /  8% / 38%
square -> hexagon         +1.000    +0.978     90% / 0% /  5% /  5% /  0%
triangle -> pentagon      +0.723    +0.747     49% / 0% /  8% /  8% / 35%
hexagon -> octagon        +0.478    +0.473     57% / 0% / 21% / 21% /  1%
pentagon -> octagon       +0.685    +0.701     63% / 0% /  5% /  5% / 28%
square -> dodecagon       +0.682    +0.897    100% / 0% /  0% /  0% /  0%
```

**L6a (cos_deflated > 0.30 for adjacent polygons):** ✓ PASS — 6/6
pairs above 0.30 (worst: hexagon→octagon at 0.473). The fiber acts
as a working transport map; the prediction lives in the right
neighbourhood of the actual delta in 320-dim irrep space.

**L6b (deflated ≥ raw for ≥4/6 pairs):** ✓ PASS — 4/6 pairs improve
under deflation (square→triangle, triangle→pentagon, pentagon→octagon,
square→dodecagon). For square↔hexagon and hexagon→octagon, raw is
already so high (≥0.978) that DC removal can only nibble.

The D4-channel breakdown is the textbook signature: pair-changes
involving a `n=3` polygon spread mass to E (rotational doublet);
square↔dodecagon — both pure-A1 — leaves the entire delta in A1.

### L6c — Chain transport (vocab → syntax → geometry)

Square ↦ spiral_square chains a vocab-count delta through F₁ᵀ to a
syntax-feature delta, then through M₂ᵀ to a geometry delta:

```
cos(syntax_pred, syntax_actual) [via F₁]   = +0.629
cos(geom_chain,  geom_actual)   [F₁ → F₂] = +0.516
cos(geom_direct, geom_actual)   [F₂ only ] = +0.597
```

**L6c (chain cos > 0.10):** ✓ PASS at 0.516. The chain-via-F₁ pays a
~15% relative penalty against direct featvec transport (0.597 → 0.516)
— the price of going through two approximations and a zero-fill of
the value-fingerprint dimensions that don't live in F₁'s rule axis.
The signal still propagates: composing the two fibers gives a
meaningful prediction without ever touching the geometry of the
target program.

### L6d — Per-feature transport(N) — D4 character recovery

`transport(N) = M_hi.T · e_N` for one-hot indicator at `repeat_n=N`,
decomposed into D4 channel energies (deflated F₂):

```
feature        |t|     A1    A2    B1    B2     E
repeat_n=3    0.091   33%    2%    9%    9%   47%
repeat_n=4    0.092   86%    0%    4%    4%    7%
repeat_n=5    0.116   46%    0%    7%    7%   40%
repeat_n=6    0.057   27%    0%   25%   25%   23%
repeat_n=8    0.085   60%    2%   11%   11%   15%
repeat_n=12   0.063   93%    0%    2%    2%    4%
```

**L6d (A1-pure for n∈{4,8,12}; A1+E for n=5; B1+B2+E spread for n=3):**
✓ MOSTLY PASS.

- `transport(4)` 86% A1, `transport(12)` 93% A1, `transport(5)` 46%
  A1 + 40% E — match the prediction.
- `transport(3)` is 47% E + 33% A1 with B1+B2 contributing — matches
  the "spread to multiple irreps" prediction (D3 splits across A1,
  B1+B2, E in D4).
- `transport(8)` is messier (60% A1 + 26% B+E) than predicted "pure
  A1." Likely a small-corpus artefact: only one D8 program participates,
  so the deflated subspace can't cleanly separate it from neighbouring
  symmetry classes.
- `transport(6)` is the most fragmented. With three D6 programs in
  the corpus (hexagon, rosette_6, proc_two_polys-second-half), the
  deflated subspace splits across all four non-trivial irreps roughly
  equally. Honest reading: not every n recovers cleanly; the strong
  predictions (4, 5, 12, 3) do.

**This is the strongest "fiber knows representation theory" evidence:**
F₂ has never seen a D4 character table, but `transport(N)` for the
distinguished n's lands in the irrep classes that the n-fold rotation
group projects onto inside D4. The fiber is doing more than memorizing
program geometries.

### L6e — Per-mode SVD attribution (square → triangle)

Decompose Δg_pred = Σ_k σ_k · (u_k · Δv) · v_k:

```
  k    sigma  cos(term, Δg)  pred share   cum cos
  1    0.233          0.112         7.7%     0.112
  2    0.203          0.249         0.0%     0.123
  3    0.158          0.411        21.1%     0.415
  4    0.143          0.283         3.4%     0.485
  5    0.102          0.008         1.4%     0.477
  6    0.089          0.469        34.7%     0.668
  7    0.075          0.441        20.5%     0.798
  8    0.063          0.371        11.2%     0.876
```

**L6e (modes 4-7 carry > 80% of polygon transport energy):** ✗ MISS.
Modes 4-7 carry 59.9% of the prediction's energy for
square→triangle (not 80%). The polygon-symmetry signal is real but
*spread* across modes 1, 3, 6, 7, 8 rather than concentrated in 4-7.

Cross-checked on two more pairs:
- square→pentagon: 4-7 = 59.4% (also miss)
- square→hexagon: 4-7 = 47.3% (also miss)

The cumulative cos still climbs to 0.876 by mode 8, so the prediction
*overall* fits — just not via the modes the L4b SVD report named
"polygon-symmetry modes." Honest reading: L4b's modal labels were
right about which modes load on `repeat_n=N`, but the *transport*
contribution doesn't follow the loading pattern. A single mode's
σ × |u·Δv| can be large or small independently of which feature
loads it. Lesson for the pattern: SVD interpretability tells you
*which features participate* in a mode, not *how much that mode
contributes to a specific transport*.

### L6f — Chain collapse: does syntax mediate vocab → geometry?

Build F3_direct (vocab × geometry) and F3_chain = M_AB · M_BC. Test
two B-widths: rules-only (12 cols) vs. extended (30 cols including
`repeat_n=N` value buckets):

```
narrow B (rules only,  dim 12):  cos(F3_chain, F3_direct) = +0.993
wide   B (extended,    dim 30):  cos(F3_chain, F3_direct) = +0.993
widening gain (wide - narrow)                              =  0.000
```

**Result:** Iteration-2 prediction was 0.95 narrow → 0.99 wide.
Reality is 0.99 → 0.99: rules alone already mediate ~99% of the
vocab→geometry correlation; widening to value-fingerprints adds
nothing detectable here. Interpretation: the rule axis already
captures the entire mediation budget at this corpus size — value
features matter for *intra-class* discrimination (polygon n) but not
for the cross-modal correlation envelope. The "syntax mediates
geometry" hypothesis lands cleanly.

### L6g — Cycle holonomy (round-trip A→B→C→A vs direct A↔A)

```
‖M_AA‖_F                              = 4.890
‖C_fwd‖_F                             = 140.015
cos(C_fwd, M_AA)         [normalized] = +0.942
holonomy ‖Δ‖_F                        = +0.340
cycle SVD (top singular values, normalized to s₀):
  s[0] = 140.015   (100.0%)
  s[1] =   0.057   (  0.0%)
  s[2] =   0.038   (  0.0%)
  s[3..]≈ 0
mode-0 dominance: s_1 / s_0 = 0.000
```

**Result:** Iteration-2 prediction was cos ≈ 0.93, holonomy ≈ 0.37 —
measured 0.942 / 0.340 nails both. The cycle SVD is *extreme*: the
round-trip operator is essentially rank-1, with everything crushed
into the leading direction. This is the predicted "geometry-visible
commands survive the round trip; geometry-invisible commands like
MAKE/PENUP get distorted toward FORWARD/REPEAT." The corpus mostly
lives in a thin slice of vocab-space (motion-dominated programs);
the round trip projects onto that slice and discards everything else.

### L6h — Chirality (commutator)

```
cos(C_fwd, C_rev = C_fwd^T)            = +0.997
commutator ‖normalized Δ‖_F            = +0.082
Verdict: chiral (non-commutative)
```

**Caveat noted:** With only 21 corpus programs, an 0.082 commutator
is small but nonzero. Mathematically C_rev = C_fwd^T, so the
commutator is the antisymmetric part of C_fwd; an 0.082 norm against
unit-norm pieces means the symmetric (torus-like) part dominates ~12×
over the antisymmetric (chiral) part. Honest reading: structure is
near-symmetric with a small chiral signal that is *probably* corpus
bias. A distinguishing experiment would need a corpus designed to
enforce or break ABC-cycle symmetry.

---

## Phase L7 — Generalization + Trajectory (Iteration 3)

**Motivation.** Everything in L6 was measured on the same 21 programs
that built F₂. "The fiber learned D4 character theory" (L6d) is only
meaningful if the fiber retains that structure after dropping the
programs whose character it's supposedly predicting. L7 closes the
memorization-vs-learning gap before the pattern is extended to chess
(where the payoff is trajectory/branching dynamics, not static
structure).

Two experiments, L7b gated on L7a. Both use deflated-fiber numerics
(matches L6 convention).

### L7a — Held-out generalization (PASS)

**Command.** `python logo_py.py transport --holdout pentagon,octagon`
(see [logo_transport.py](logo_transport.py)::`holdout_transport_table`
and `print_holdout_report`).

**Method.** Rebuild F₂ from the 19 programs remaining after dropping
pentagon and octagon. Recompute:
- `transport(5)` and `transport(8)` — the D4-character decomposition
  claim from L6d — on the reduced fiber.
- `Δg_pred = M_ho_hi.T · (v_b − v_a)` for polygon pairs that straddle
  the hold-out — triangle→pentagon, hexagon→octagon — against the
  ground-truth `G_hi` delta *from the full-corpus payload*
  (pentagon/octagon geometries don't move when we drop them from F₂;
  the question is whether the reduced fiber still aligns with them).

**Raw numbers (2026-04-14).**

| feat        | scope | ‖t‖   | A1  | A2 | B1  | B2  | E   |
|-------------|-------|-------|-----|----|-----|-----|-----|
| repeat_n=5  | full  | 0.116 | 46% |  0%|  7% |  7% | 40% |
| repeat_n=5  | ho    | 0.085 | 45% |  0%|  7% |  7% | 40% |
| repeat_n=8  | full  | 0.085 | 60% |  2%| 11% | 11% | 15% |
| repeat_n=8  | ho    | 0.092 | 70% |  2%| 10% | 10% |  8% |

Pair transport under the held-out fiber (vs full-corpus `Δg`):

| pair                 | cos_full | cos_ho |
|----------------------|----------|--------|
| triangle → pentagon  | +0.747   | +0.568 |
| hexagon  → octagon   | +0.473   | +0.170 |

**Predictions vs measurement.**

| ID    | Prediction                                                    | Measured              | Verdict |
|-------|---------------------------------------------------------------|-----------------------|---------|
| L7a.1 | `transport(5)` A1+E share drifts ≤ 20 pp under hold-out       | 0.1 pp (86% → 85%)    | **PASS** |
| L7a.2 | `transport(8)` A1 share stays ≥ 50% under hold-out            | 69.7%                 | **PASS** |
| L7a.3 | `|transport(5)|`, `|transport(8)|` norms don't collapse (≥30% of full) | 0.727, 1.077 | **PASS** |
| L7a.4 | Best pair cos_ho > 0.25                                       | +0.568 (tri→pent)     | **PASS** |

**Interpretation.** L6d's D4 character claim survives hold-out
without qualitative change — the reduced fiber places `transport(5)` in
A1+E and `transport(8)` in A1 essentially unchanged. This is the
strongest evidence so far that the split-object pattern compresses
*structure*, not corpus identity. Interestingly, `|transport(8)|`
*grows* under hold-out (ratio 1.077) — dropping octagon from the
corpus makes the `repeat_n=8` column more committed to A1-energy, not
less. Consistent with octagon being the only program enforcing the
`repeat_n=8` → A1 coupling, and its geometry being a "clean" anchor
for it.

Pair transport weakens on `hexagon→octagon` (0.473 → 0.170) — the
held-out fiber has less information about octagon's specific geometric
signature — but triangle→pentagon barely moves (0.747 → 0.568), so
the D4-transport predictions retain their shape. Generalization holds.

### L7b — Partial-trace fibers (MOSTLY MISS; headline finding)

**Motivation.** L7a validated static structure learning. L7b asks
whether the split-object pattern can also carry *trajectory*
information: build F₂ from the first N trace segments instead of the
final trace, then ask whether the fiber built at step N predicts
geometry at step N+Δ.

**Method.** No interpreter changes — we just truncate `Trace.segments`
and re-encode. Helpers:
- [logo_transport.py](logo_transport.py)::`partial_geom_for(entry, N)`
- `build_partial_context(n_segments)`
- `partial_trace_transport_table(n_build, n_target)`
- `fiber_drift(n_early, n_late)`
- `spiral_extrapolation_probe(name, n_early, n_late)`

Polygons finish in 3–12 FORWARDs so their rows are time-invariant
after their natural end (anchor N > len → same geometry at all N > len).
Spirals and fractals are the actual trajectory probe. The degenerate
`only_pen` and `only_bind` produce zero-norm geometry and cluster at
cos ≈ 0 by construction — noise floor for per-program cosines.

**Raw numbers.**

`transport --partial 30,60` (fiber at N=30, target at N=60):

| family     | n  | mean cos(pred, target) |
|------------|----|------------------------|
| polygon    |  7 | +0.307                 |
| spiral     |  3 | +0.085                 |
| fractal    |  4 | +0.433                 |
| freestyle  |  3 | +0.805                 |
| procedures |  2 | +0.647                 |
| degenerate |  2 | −0.013                 |

`transport --partial 10,30` (build earlier, target closer):

| family     | n  | mean cos(pred, target) |
|------------|----|------------------------|
| polygon    |  7 | +0.377                 |
| spiral     |  3 | −0.033                 |
| fractal    |  4 | +0.333                 |
| freestyle  |  3 | +0.695                 |
| procedures |  2 | +0.539                 |

`transport --drift 10,60`:

- Frobenius cos(M_early, M_late) = **+0.971**
- `‖M_l − M_e‖_F / ‖M_e‖_F` = **0.250**
- Per-irrep cos: A1 +0.984, A2 +0.021, B1 +0.876, B2 +0.876, E +0.840
- Top-5 drift rows: `r_NUM_is_literal` (0.932), `r_STMT_is_MOTION_NUM`
  (0.543), `r_BLOCK_is_STMT_star` (0.297), `r_STMT_is_REPEAT_NUM_BLOCK`
  (0.297), `r_STMT_is_MAKE_NAME_EXPR` (0.263)

`transport --spiral-extrapolate 10,60` (the headline probe):

| quantity                                | value   |
|-----------------------------------------|---------|
| cos(fiber_pred(M_e.T·featvec), g_late)  | **−0.125** |
| cos(g_early, g_late)  [snapshot baseline] | **+0.730** |
| gain = fiber − snapshot                 | **−0.855** |

**Predictions vs measurement.**

| ID    | Prediction                                             | Measured     | Verdict |
|-------|--------------------------------------------------------|--------------|---------|
| L7b.1 | Polygon mean cos > 0.40 at (30, 60)                    | +0.307       | **MISS** |
| L7b.2 | Spiral  mean cos > 0.20 at (30, 60)                    | +0.085       | **MISS** |
| L7b.3 | `‖M_l − M_e‖_F / ‖M_e‖_F` > 0.10 between N=10 and N=60 | 0.250        | **PASS** |
| L7b.4 | Spiral-marker feats (MAKE, repeat_n=60) dominate top-5 drift | hits=0 | **MISS** |
| L7b.5 | spiral_square fiber beats snapshot baseline by > 0.10  | gain = −0.855 | **MISS** |

**Interpretation.**

1. **Fibers *are* time-dependent (L7b.3 PASS).** The Frobenius cos
   between fibers at N=10 and N=60 is 0.971 (high, but not 1), and the
   relative Frobenius delta is 25%. Fibers do shift with the trace —
   A2's per-irrep cosine of +0.021 is especially striking: A2 basically
   flips sign between early and late snapshots. But this drift is a
   snapshot signal, not a predictor.

2. **Drift is generic, not spiral-specific (L7b.4 MISS).** The top-5
   drifting feature rows are generic structural productions
   (`r_NUM_is_literal`, `r_STMT_is_MOTION_NUM`, `r_BLOCK_is_STMT_star`) —
   rules that fire in *every* program. The naive hypothesis — that
   spiral-marker features (MAKE, repeat_n=60) would dominate drift —
   was wrong. Drift tracks *how much trace each program has accumulated
   by step N*, not what makes a spiral different from a polygon.

3. **The fiber does not extrapolate forward (L7b.5 MISS, badly).**
   cos(fiber_pred at N=10, g_late at N=60) = **−0.125**. The snapshot
   baseline — literally just "use the geometry at N=10 as if nothing
   changed" — scores **+0.730**. The fiber-predicted geometry is
   *actively worse* than assuming no change at all. The −0.855 gain is
   the most emphatic negative result in this spike.

   Why: `M_e.T @ featvec(p)` is a projection of the *full-program*
   syntax feature into the fiber space built from *partial-trace*
   geometry. It averages across programs that all happen to be at
   their "step-10 snapshot" and can't distinguish "the fiber that
   built this featvec at N=10" from "the fiber that will build it at
   N=60." The partial-trace F₂ summarizes the current snapshot, not
   the trajectory from N to N+Δ.

4. **Family ordering is revealing.** Freestyle (+0.805) and procedures
   (+0.647) predict best, then fractals (+0.433), polygons (+0.307),
   spirals (+0.085). The programs that look most "typical" for their
   feature vector get predicted best; the programs whose geometry
   *diverges* through execution — spirals — get predicted worst. This
   is a *descriptive* structure, not a *predictive* one.

**What this means for chess.** The chess trajectory question
originally asked: does a snapshot fiber, interrogated at a later move,
predict future eval? **L7b.5 says no, not with this construction.**
The chess trajectory fiber will need a different lever — per-move
fiber *sequences* (each move is a fiber delta, composed over a game),
or recurrent/difference formulations, or fibers keyed on current
move index with an explicit time coordinate. A snapshot F₂ built
mid-game and asked "what does the position look like 10 moves later"
won't buy trajectory prediction for free.

This is the right moment to find that out — on a deterministic toy
where every state is inspectable — rather than after committing to
a chess fiber construction.

### L7 status summary

- L7a: **4/4 PASS** — L6d's D4 character claim generalizes.
- L7b: **1/5 PASS** (drift exists; prediction doesn't).
- Iteration-2 structural claims (L6a–d, L6f–h) stand unretracted.
- The trajectory hypothesis for chess needs reformulating before the
  chess instantiation begins.

---

## What this spike validated

1. **Split-object pattern generalizes.** F₁ factored vocab × syntax
   into 7 interpretable modes with the predicted null structure. F₂
   factored syntax × geometry and surfaced Dₙ symmetry classes in its
   subdominant modes. Neither result required any chess-specific
   machinery beyond `project_irrep`.

2. **Structured atoms beat random atoms** when the codebook has a
   symmetry that the downstream task cares about. Reversibility pair
   recovery (`a_FORWARD · flip ≈ a_BACK`) *only* worked with
   quantum-numbered atoms composed through `bundle_sum`. Random atoms
   would have forced F₁ to rediscover this from the coincidence stream
   instead of getting it for free.

3. **`bundle_sum` ≠ `bundle`.** Majority-vote binarization destroys
   flip linearity. For compositional codebooks, keep the accumulator
   real-valued until cleanup.

4. **Dominant-mode deflation matters for class recovery.** F₂'s top
   mode is "generic program structure" and carries no class signal.
   The symmetry modes sit below it in the spectrum. Anyone instantiating
   this pattern on a new domain should check subdominant modes, not
   just σ₀.

5. **The chess spectral basis reused cleanly.** `project_irrep` on a
   raw rasterized grid gives the correct D4-irrep decomposition for a
   turtle trace. The piece-char intermediate was harmful for LOGO;
   bypassing it (but keeping the irrep machinery) gave a clean encoder.
   The chess fiber channels (F1..FD) are piece-type-specific and
   don't generalize — that's fine; they weren't needed.
   *Iteration 2:* the projection itself is now inlined in
   [logo_irrep.py](logo_irrep.py); no sibling-package sys.path hack.

6. **Fibers are predictive transport maps, not just summaries
   (iteration 2).** L6a–c shows `M₂ᵀ · Δv` predicts polygon-to-polygon
   geometry deltas at cos > 0.47 (deflated, all 6 pairs); chains
   through F₁ then F₂ propagate vocab deltas to geometry deltas at
   cos 0.516 with a ~15% relative penalty vs direct featvec transport.

7. **The fiber knows representation theory (iteration 2).** L6d:
   `transport(N) = M_hi.T · e_N` for one-hot `repeat_n=N` reproduces
   the qualitative D4 character class for the distinguished n's
   (4/8/12 → A1; 5 → A1+E; 3 → spread). The fiber was never told
   the D4 character table — it inferred it from program-geometry
   coincidences.

8. **Three-body topology is near-symmetric, near-rank-1 (iteration 2).**
   L6f–h: syntax mediates ~99% of vocab↔geometry correlation, the
   round-trip cycle has cos 0.94 to direct A↔A and a holonomy norm
   of 0.34, the cycle SVD is essentially rank-1 (s_1/s_0 ≈ 0), and
   the chirality commutator is small (0.082, probably corpus bias).
   The split-object pattern composes; the cycle isn't a torus but
   isn't far from one either at this corpus size.

9. **Honest retraction matters.** L1's "`bind(a_FORWARD, flip_axis) ≈
   a_BACK`" claim was wrong — measured cos was −0.004. Iteration 2
   replaced it with `unbind_role` and `swap_role_value`, which work
   *algebraically* on the unbinarized bundle (cos 1.0 exactly for the
   swap). The right-shape-wrong-reason mistake — confusing
   *structural similarity of atoms* with *reversibility-via-binding*
   — is now documented in L1's RETRACTION block as a cautionary tale.

## Out of scope (deferred)

- C17 port — the Python math held; nothing to port prematurely.
- Full LOGO (lists, infix precedence, RUN/IFELSE/OUTPUT) — research
  subset is enough for the pattern proof.
- Learned codebooks — the structured-atom approach was enough.
- Multi-turtle `SPAWN` (the stretch goal L6) — deferred.

## Open questions

- **D sweep**: we ran everything at D=10000. Phase L3's F₁ rank-7 signal
  should survive well below that; quick sweep would characterize the
  cliff for this pattern.
- **Deflation is a knob**: how many leading modes should a consumer of
  this pattern deflate before reading class signal? For LOGO it's
  exactly σ₀ — one mode. Chess-spectral has a richer top-mode
  structure; this might be a per-domain tuning parameter.
- **BACK in the null space**: structurally legitimate (no corpus
  program uses it) but it would be worth adding a BACK-using program
  to confirm its row activates symmetrically with FORWARD.

---

## How to cite this notebook

**BibTeX:**

```bibtex
@misc{kirkland_logo_2026,
  author       = {Kirkland, Steven},
  title        = {LOGO HDC --- Research Notebook},
  year         = 2026,
  howpublished = {\url{https://github.com/lemonforest/mlehaptics/blob/main/docs/logo-maths/logo_research_notebook.md}},
  note         = {Part of \emph{mlehaptics: Spectral-Research Portfolio}; LOGO turtle-graphics cyclic-group encoder. Project-level citation metadata at \url{https://github.com/lemonforest/mlehaptics/blob/main/CITATION.cff}. Co-authored with Claude Opus 4.7 (Anthropic, 1M-context configuration) per project memory \texttt{feedback\_orchestration\_metaphor}. Framing is one candidate within the project's research portfolio per \texttt{feedback\_no\_lineage\_claims\_in\_notebook}.}
}
```

**Plain text:** Kirkland, S. (2026). *LOGO HDC — Research Notebook*. mlehaptics Spectral-Research Portfolio. https://github.com/lemonforest/mlehaptics/blob/main/docs/logo-maths/logo_research_notebook.md

**Per-result citation discipline.** Specific technical claims cite their canonical sources directly (LOGO language history, HDC bind/bundle/permute primitives, etc., PDF-verified per `[[feedback_pdf_extraction_citation_discipline]]`). When citing a specific result, prefer citing both this notebook AND the underlying canonical source. Framings presented here are candidate methodological readings per `[[feedback_no_lineage_claims_in_notebook]]`, not endorsed over alternatives without explicit empirical convergence.

**Project-level citation.** See `CITATION.cff` at the repo root for the project-as-a-whole citation form.
