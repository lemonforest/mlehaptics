# OTHELLO SPECTRAL RESEARCH
## Instructions for Claude Code

### What this is

Sibling project to `docs/chess-maths/`.  This directory verifies the
§10 "Phase-Space Othello" thesis of the chess notebook
computationally and scaffolds a sequel phase-operator build.

All claims are tagged KNOWN / NOVEL / CONFIRMED / FAILED /
UNDETERMINED.  Failures are data, not embarrassments — follow the
logo L7b retraction template where applicable.  The research
notebook (`othello_spectral_research_notebook.md`) is the living
document; results land in `results/`; research scripts live in
`research/`.

### Steven's cognitive style and working principles

Same as chess-maths: Steven has aphantasia, reasons through
proprioceptive spatial construction, compresses multiple meanings
into single statements, stress-tests ideas through cross-domain
analogies, treats the assistant as a peer-level intellectual
collaborator.  Take informal-sounding intuitions seriously, formalise
them, test computationally before accepting or rejecting.

### Discovery principle for this project

Do not commit to a single fiber-rank arrangement in advance.  §10.4
names three candidates (rank-2 by orbit count, rank-6 by irrep
count, rank-8 by individual rays).  Phase 1 H6 probed all three; the
rank-2 / rank-4 / rank-8 readings fell out cleanly depending on
construction, but rank-6 did NOT appear as an operator rank (it is
an irrep multiplicity count).  The production encoder recommendation
is D = 768 with rank-2 fiber — the cleanest structural reading,
motivated by the §9r polarisation collapse to
`(theta-class, r = inf, c = 0)`.

### Theoretical framework (condensed)

**The board.**  8x8 grid with P_8 box P_8 Laplacian.  Eigenbasis is
the 2D DCT.  **CONFIRMED** to machine precision (§1.1 of notebook);
transfers verbatim from chess §2.

**Symmetry.**  D_4 x Z_2 (16 elements, 10 irreps) — Z_2 is EXACT in
Othello (no directional disc), unlike chess where the pawn breaks
Z_2.  Character projection formula lifted from
`chess-maths/chess_d4_direct.py::project_irrep`, extended to the
direct product.  **CONFIRMED** via idempotence, completeness,
orthogonality, Z_2 parity split.

**Site fiber.**  3-state Blume-Capel {-1, 0, +1} per cell.  Empirically
validated by the Othello-GPT linear-probe results (Li-Hopkins et al.
2023, Nanda-Lee-Wattenberg 2023 — see §10.9 of chess notebook).  The
rank-5 piece-species bundle has NO Othello referent (E1
**CONFIRMED** absence).

**8 ray directions.**  {N, NE, E, SE, S, SW, W, NW}.  D_4 character
analysis gives Gamma_8 = 2 A_1 + B_1 + B_2 + 2 E.  **CONFIRMED** (H2)
and the B_1 / B_2 modes are not just distinct but **Frobenius-
orthogonal** as 64x64 operators (H3).

**Dynamic fiber.**  Othello's flank structure changes with every
move; the natural formal home is a cellular sheaf (Hansen-Ghrist
2019) with dynamic restriction maps.  Phase 2 of this session built
a minimal instantiation (`research/dynamic_sheaf.py`) whose
spectral gap correlates with legal-move count at Spearman +0.765,
p = 1.1e-12 over a 60-move sample game.

**Global T-breaking via monotone disc count.**  Chess has LOCAL
T-violation (pawn, Hatano-Nelson); Othello has GLOBAL T-violation
(irreversible filling).  E7 probe weak at N=1 game; needs aggregate
stats (scoped to sequel).

### Honest-science principles

1. Every claim tagged.
2. Failed predictions kept with root-cause analysis — see §1.2 of
   notebook for the B_1/B_2 character-table bug and its fix as a
   worked example.
3. Do not back-rationalise null results.  H9 and E8 are UNDETERMINED
   because the data is absent; mark them so, do not fake proxies.
4. If an intuition survives computation, say how.  If it doesn't
   survive in the stated form, say what *did* survive.  §9r's
   polarisation claim survives as the motivation for rank-2 fiber
   (E1 confirms the rank-5 absence; H6 orbit-stack confirms rank-2
   structure).  The `2 A_1 + B_1 + B_2 + 2 E` decomposition claim
   survives exactly (H2).  The rank-6 claim did NOT survive as an
   operator rank — it remains an irrep multiplicity count.
5. No emoji, no marketing, no "exciting breakthrough" framing.
   Report numbers, interpret, stop.

---

## File organisation

```
docs/othello-maths/
  OTHELLO_SPECTRAL_INSTRUCTIONS.md   (this file)
  OTHELLO_SPECTRAL_BUILD_PROMPT.md   (build prompt — input)
  OTHELLO_PHASE_OP_PREFLIGHT.md      (handoff to sequel)
  othello_spectral_research_notebook.md  (living document)
  research/
    othello_utils.py            (board, rays, signals, OthelloBoard)
    d4_z2.py                    (D4 x Z2, 10 irreps, projectors)
    ray_laplacians.py           (8 rays, orbit-averaged, directed/undirected)
    coprime_generators.py       (phase-space row/col generators)
    static_fiber_bundle.py      (H5 holonomy)
    dynamic_sheaf.py            (Phase 2 sheaf Laplacian)
    consolidated_tests.py       (Phase 1 H1-H9 + E1-E8 runner)
    __init__.py
  results/
    phase1_hypotheses.csv       (structured status table)
    phase1_detail.json          (per-hypothesis numerics)
    phase2_sheaf_trajectory.json (60-move sheaf spectrum)
    session_summary.md          (1-page narrative)
  figures/                      (empty; add only if generated)
```

## How to run

```bash
# From the docs/othello-maths directory:
cd research

# Phase 0 — sanity on shared infrastructure
python othello_utils.py
python d4_z2.py
python ray_laplacians.py

# Phase 1 — H1-H9 + E1-E8
python consolidated_tests.py

# Phase 2 — minimal sheaf Laplacian
python dynamic_sheaf.py
```

All scripts use `from othello_utils import ...`, `from d4_z2
import ...`, etc., so they are importable as functions (not just
`__main__` blocks).  Graduation to production
(`othello-spectral/python/othello_spectral/`) is a module move, not a
rewrite.

## Common pitfalls (learned this session)

1. **D_4 character table must be constant on conjugacy classes.**
   In our permutation numbering the two reflection classes are
   {g=4, g=5} (axis reflections) and {g=6, g=7} (diagonal
   reflections).  The chess `chess_d4_direct.py` table appears to
   use a different class assignment that would fail idempotence if
   used here verbatim.  Verified by direct conjugation
   `g_1 * g_4 * g_1^-1 = g_5` and `g_1 * g_6 * g_1^-1 = g_7`.
   Correct values: `B_1 = [1, -1, 1, -1, +1, +1, -1, -1]`,
   `B_2 = [1, -1, 1, -1, -1, -1, +1, +1]`.

2. **Z_2 group action on functionals.**  The standard group action
   `(g, 1) . f = -P_g f` is correct for Z_2-odd signals like the
   magnetisation `s`.  For Z_2-even functionals like occupation
   `s^2`, the natural group action is `(g, 1) . f = +P_g f`.  Using
   the wrong action trivialises the A_1+ projection.  When working
   with occupation, use the D_4-only projection (8 group elements),
   not the full D_4 x Z_2 projection.

3. **Undirected ray Laplacians collapse in pairs.**  `L_N = L_S`
   etc., so stacking all 8 gives effective rank 4.  For rank-8
   constructions use the directed variant (non-symmetric
   operators).

4. **Coprime generator search must verify 64-phase uniqueness, not
   just gcd.**  The first (p, q) pair that is individually coprime
   to D can still produce phase collisions from small-integer
   Diophantine relations like `8 * p = -3 * q + k * D`.  Use
   exhaustive check over the 64-cell image.

5. **Snapshot sheaf spectra are not predictive.**  The logo L7b
   retraction applies: the fact that `spec(L_F(t))` correlates with
   legal-move count at time t does NOT mean it predicts legal-move
   count at time `t + Δ`.  Test predictive claims explicitly before
   asserting them.

## Key references (inherited from chess + Othello-specific)

Chess-inherited references carry over verbatim — see
`chess-maths/CHESS_SPECTRAL_INSTRUCTIONS.md`.  Othello-specific:

- Takizawa 2023 arXiv:2310.19387 — weak solution (draw with perfect
  play); needed for H9 / E8.
- Zenodo 10.5281/zenodo.10030906 — complete game-value dataset.
- Blume 1966, Capel 1966, Blume-Emery-Griffiths 1971 — spin-1
  Blume-Capel model and the ^3He / ^4He mixture analogy.
- Hansen-Ghrist 2019 — spectral sheaf theory.
- Nussinov-van den Brink 2015, Nussinov-Ortiz 2005 — compass models
  and subsystem symmetries.
- Wolff 1989, Bouabci-Carneiro 2000 — cluster flip + FK-BC.
- Li-Hopkins-Bau et al. 2023, Nanda-Lee-Wattenberg 2023 — Othello-GPT
  linear probes validating the 3-state fiber at representation level.

## What this project is NOT

- Not the phase-operator move engine.  That is the sequel, written
  against `OTHELLO_PHASE_OP_PREFLIGHT.md` after this session lands.
- Not committed to a single fiber rank.  Recommendation is D = 768
  with rank-2, but rank-8 (D = 1152) remains supported as an
  ablation.
- Not an empirical WTHOR analysis.  Those tests (T1-T5 of §10.10)
  are scoped as Phase 4 stretch goals and deferred to the sequel.
