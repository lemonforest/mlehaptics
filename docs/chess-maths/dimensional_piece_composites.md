# Dimensional piece composites and the shadow-realization hierarchy

**Status:** Informal reflection, worth revisiting when the chess-spectral encoder work has settled. Written alongside the Oana-Chiru reference-implementation port (`python-chess4d-oana-chiru`) while thinking about whether a dimension-consistent chess family is possible.

**Relationship to prior notebook findings:** This extends the spectral decomposition work (rank-5 fiber bundle, D₄ irrep decomposition, cross-piece fiber coupling) and the LOGO HDC generalization spike. Specifically, it proposes that the shadow-mode structure in the 2D rook extends to a **hierarchy of shadow realizations** across dimensions, where each additional dimension activates spectral components that were present-but-unrealized at the dimension below.

---

## 1. The question that prompted this

Working through the Oana-Chiru 4D chess ruleset raised two related questions:

1. Does the 4D game project cleanly to 2D (i.e., is 4D chess "2D chess with extra coordinates")?
2. Can 2D chess lift cleanly to 3D/4D as a genuine homomorphism, where new rules exist "like the rook shadow effect"?

The first answer is no — Oana-Chiru's multi-king structure, its starting layout, and the 4D king's Hamming-3 and Hamming-4 move components all break projection. The second answer is partially yes, and examining *why partially* surfaces the structural claim in this document.

## 2. The central claim

**A single chess piece, analyzed in the symmetry-adapted spectral basis, decomposes into multiple irreducible components. The number of components strictly grows with board dimension. Higher-dimensional pieces are "composites" whose component structure becomes individually visible (and, at specific dimensions, geometrically realizable) at higher d.**

This is not "one piece becomes many pieces" in the literal game-object sense. The piece remains a single atomic unit at the move-semantics level. What grows with dimension is the *number of irreducible representations* the piece's move graph decomposes into under the board's symmetry group.

## 3. Concrete decomposition counts

The symmetry groups of the cube and hypercube scale dramatically with dimension:

| d | Board | Symmetry group | Order | Irrep count |
|---|-------|----------------|-------|-------------|
| 2 | K₈ □ K₈ | D₄ | 8 | 5 (A₁, A₂, B₁, B₂, E) |
| 3 | K₈ □ K₈ □ K₈ | B₃ = S₃ ⋉ (ℤ/2)³ | 48 | 10 |
| 4 | K₈ □ K₈ □ K₈ □ K₈ | B₄ = S₄ ⋉ (ℤ/2)⁴ | 384 | 20 |

A 2D rook's move graph decomposes into the 5 D₄ irreps. A 4D rook decomposes under B₄ into up to 20 components. Same piece type, same displacement semantics ("move along a single axis"), but the structural fingerprint is radically richer at higher d.

The rook is the simplest case because it's a pure Cartesian product of K₈ factors. The bishop, knight, and king decompose differently — the knight especially so, since it admits no product-graph structure (per §3.8 of Oana-Chiru, noted as the only piece whose move graph is not decomposable via Cartesian or parity structure).

## 4. Shadow realizations at each dimension

The spectral decomposition reveals modes that carry structural information the raw adjacency doesn't visibly support. This is the **shadow effect** — identified in the chess-spectral notebook as the rook's diagonal signature appearing in the off-diagonal Laplacian modes despite the rook making no diagonal moves.

Generalizing:

- **d=2.** The rook has shadow diagonal modes in D₄'s E irrep. These modes are spectrally present but geometrically unrealized — no legal 2D rook move follows them. The "shadow" is a latent component the rules don't activate.

- **d=3.** Going 2D→3D activates some previously-latent modes. A 3D king, under Chebyshev-1 adjacency, legally makes moves that were shadows in 2D — specifically the corner-type moves with Hamming distance 3 (simultaneously changing x, y, and z by ±1). These require three axes, so they can't exist in 2D; at d=3 they become newly realizable.

- **d=4.** Going 3D→4D activates further components. The 4D king includes Hamming-3 and Hamming-4 moves (4D notebook, §"Dimension-sensitive king in 4D"). The trihedral stepper (HD=3) and tetrahedral stepper (HD=4) are named as candidate pieces — they're geometric primitives that the named piece vocabulary under-specifies by exactly two classes at d=4. These are the d=4-specific shadow realizations.

**The pattern:** each dimension lifts a specific set of previously-suppressed irrep components into geometric realizability. Lower-d pieces are "ground states" whose higher-d components are dormant; higher-d pieces have those components active.

## 5. The composite-particle analogy

The physics analog that fits cleanest is **composite particles under symmetry group action**, which is the framing the spectral chess research notebook already uses (Hubbard 1963, Weyl 1912).

A proton is one particle, but decomposes into quark degrees of freedom that transform under SU(3). You don't say "the proton is three entangled quarks" in the quantum-entanglement sense, because it's a single bound state. But the quark decomposition is the correct way to analyze how the proton behaves under SU(3) transformations — its structural fingerprint under the symmetry.

A 4D rook is structurally in the same position: one piece, bound state, decomposes into B₄ irrep components that individually carry physical meaning (mobility, parity-split behavior, fiber coupling to other pieces) but aren't independent pieces.

## 6. Why "entanglement" is almost right

The intuition "higher-d pieces must be entangled" is operationally correct but technically imprecise.

**Why it's operationally correct:** a move by a 4D piece is a single physical event, but in the irrep decomposition it shifts amplitude across multiple components simultaneously. You can't update one irrep channel independently of the others without breaking the move's semantic meaning. That's structurally analogous to how entangled states can't be evolved factor-by-factor.

**Why it's technically imprecise:** in quantum mechanics, entanglement means a state that can't be written as a tensor product of component states — the components are correlated in a way no local description captures. The chess piece's irrep components *can* be written as a tensor product in the symmetry-adapted basis (that's what the decomposition does). What's happening is "the move operator doesn't diagonalize in the irrep basis," which is a different phenomenon.

**Where genuine entanglement-analog structure does live:** between pieces, not within a piece. The cross-piece fiber bundle in the chess-spectral work — the rank-3 off-diagonal shared fiber plus the rank-5 total fiber — encodes *inter-piece* structural correlation that doesn't factor cleanly into single-piece descriptions. Two pieces' states genuinely correlate through the board geometry in a way that's closer to the quantum notion.

This distinction suggests two different research directions:
- **Intra-piece structure** (what this doc describes): decomposition of one piece's move graph under the board symmetry group. Composite-particle analog. Dimensional hierarchy.
- **Inter-piece structure** (the fiber bundle work): correlation between different piece types through shared geometric coupling. Entanglement-analog. Already well-characterized in the existing notebook.

## 7. Consequences for a dimension-consistent ruleset

If a chess family is designed so that d=2 chess embeds cleanly as the d=2 slice of a d=3 game, and d=3 embeds as the d=3 slice of a d=4 game, several consequences follow from the spectral decomposition rather than from designer taste:

1. **2D pieces are ground-state projections.** The 2D rook is the d=2-restricted version of the d=4 rook. The 2D bishop is the 4D bishop confined to a single coordinate plane. A 2D king is a 4D king with its Hamming-3 and Hamming-4 components suppressed.

2. **New pieces at each dimension are determined by irrep theory, not invented.** The trihedral stepper at d=4 isn't an arbitrary design choice — it's what you get when the 4D king's B₄ decomposition includes a Hamming-3 component that wasn't expressible at d ≤ 3. The "new pieces at dimension d" are exactly the irreps that become geometrically realizable at that d.

3. **Promotion could be dimensional.** Speculative but internally consistent: a pawn reaching the far rank in d dimensions promotes by having its higher-d components activated. A 2D pawn promoting on the 8th rank becomes a 3D queen — meaning it gains access to the Z-axis movement component that was previously dormant. The piece doesn't duplicate; its suppressed components come online.

4. **The spectral analysis becomes the design document.** Rather than designing higher-d rules and then analyzing them spectrally (what was done for Oana-Chiru), the spectral structure at d dictates what rules must exist at d+1 for the dimensional embedding to be a clean homomorphism.

## 8. Why Oana-Chiru is not an instance of this family

Worth stating explicitly, since the temptation to read Oana-Chiru as "the 4D lift of 2D chess" is strong. Oana-Chiru breaks the dimensional-embedding property in specific ways:

- **Starting position is incompatible.** The central 2×2 slice-block contains 2D-like starting arrays, but the surrounding 60 slices also contain pieces (the white-only, black-only, and empty sets per §3.3). Restricting the 4D start to any single (z, w) slice does not recover the 2D start.

- **Multi-king mechanic is a design choice, not a dimensional consequence.** Nothing in the spectral decomposition of B₄ irreps forces 28 kings per side. That count comes from the specific starting-layout density, and a dimensionally-consistent ruleset would have one king per side at every d.

- **Pawn axis orientation is 4D-introduced.** Y-orientation vs W-orientation is a choice Oana-Chiru made to preserve the Y↔W symmetry. In a dimensionally-consistent ruleset, pawn forward direction would need to emerge from the same spectral principle that introduces new pieces at each dimension — not from an axis-assignment rule.

Oana-Chiru is a rigorous and internally consistent 4D ruleset, but it's designed for "stress-testing move generation and visualization under dense conditions" (per the paper's §3.3), not for dimensional compatibility.

## 9. Open questions

- **What is the 3D intermediate?** The spectral decomposition at d=3 has 10 irreps. Which become newly realizable at d=3 (vs. still-suppressed-until-d=4)? A clean answer would tell us what "3D chess pieces" exist in the dimensional-consistent family beyond the 2D set.

- **Does the hierarchy terminate?** At what d do we stop getting genuinely new pieces? The irrep count grows factorially (|B_d| = d! · 2^d, number of irreps grows similarly), so the hierarchy extends indefinitely in principle — but do the new pieces stay "interesting" as geometric objects, or do they become pathological (moves with no intuitive analog)?

- **Promotion as dimensional lift.** If a 2D pawn promotes to a 3D queen, what are the intermediate promotion types? Does a pawn promote to a 2.5D piece (whatever that would mean), or is the jump discrete? The spectral framework might give a principled answer.

- **HDC encoding implications.** The existing 640-dim HDC encoding (5 D₄ irreps × 3 symmetric fiber + 1 antisymmetric + 1 diagonal, each × 64 eigenmodes) is calibrated to d=2. What's the natural d=3 encoding? The d=4 encoding at 40,960 dimensions already exists in the encoder; could a dimensionally-consistent family use *one* HDC basis that handles all d by zeroing-out components below the relevant dimension?

- **Does this connect to the sub-add move graph literature?** The Cesarz et al. paper cited in Oana-Chiru (reference [4]) studies "sub-add" move graphs on ℤᵐₙ, which sounds like it could be the right mathematical framework. Worth a deeper read when returning to this.

## 10. Short form

- A single chess piece decomposes into multiple irreducible spectral components under the board's symmetry group.
- The number of components grows with dimension (5 at d=2, 10 at d=3, 20 at d=4).
- Higher-dimensional pieces are "composites" whose components become individually geometrically realizable at specific dimensions.
- "Entanglement" is operationally apt but technically is non-diagonalization of the move operator in the irrep basis.
- Composite-particle-under-symmetry is the clean physics analog.
- A dimension-consistent chess family is possible, with new pieces at each d determined by irrep theory rather than design taste.
- Oana-Chiru is not an instance of this family — its starting position and multi-king mechanic break dimensional embedding — but it's a rigorous d=4 ruleset that provided the prompting.

---

*Cross-references:*
- `chess_spectral_research_notebook.md` — foundational spectral decomposition, rank-5 fiber bundle, cross-piece coupling
- `chess_spectral_4d_notebook.md` — 4D encoder validation, trihedral/tetrahedral stepper gap finding
- `logo_research_notebook.md` — pattern-validation spike proving the split-object/fiber-matrix construction generalizes
- `hoodoos/oana-chiru-2026.pdf` (in `python-chess4d-oana-chiru` repo) — the 4D ruleset that prompted these questions
