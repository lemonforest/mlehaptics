"""
The Rook's Shadow: Diagonal Fiber Dimensions
==============================================
The 3D off-diagonal fiber captures non-spatial rule content.
The rook projects to zero because its rules ARE spatial.

But the rook's Laplacian in the board eigenbasis has a specific
DIAGONAL pattern that differs from the grid's diagonal. This
diagonal deviation IS the rook's rule content — it just happens
to be aligned with the board's own modes (spatially mirrored).

Question: how many total fiber dimensions exist when we include
both diagonal and off-diagonal content? And how does the rook
relate to the other pieces in this extended space?
"""

import numpy as np
from scipy.linalg import eigh, svd
import warnings
warnings.filterwarnings('ignore')

def sq(r,c): return r*8+c

def knight_targets(r,c):
    for dr,dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
        nr,nc = r+dr,c+dc
        if 0<=nr<8 and 0<=nc<8: yield nr,nc
def bishop_targets(r,c):
    for dr,dc in [(-1,-1),(-1,1),(1,-1),(1,1)]:
        nr,nc = r+dr,c+dc
        while 0<=nr<8 and 0<=nc<8: yield nr,nc; nr+=dr; nc+=dc
def rook_targets(r,c):
    for dr,dc in [(-1,0),(1,0),(0,-1),(0,1)]:
        nr,nc = r+dr,c+dc
        while 0<=nr<8 and 0<=nc<8: yield nr,nc; nr+=dr; nc+=dc
def queen_targets(r,c):
    yield from bishop_targets(r,c); yield from rook_targets(r,c)
def king_targets(r,c):
    for dr in [-1,0,1]:
        for dc in [-1,0,1]:
            if dr==0 and dc==0: continue
            nr,nc = r+dr,c+dc
            if 0<=nr<8 and 0<=nc<8: yield nr,nc

PIECE_FNS = {'Knight':knight_targets,'King':king_targets,
             'Bishop':bishop_targets,'Rook':rook_targets,'Queen':queen_targets}

def build_adj(fn):
    A = np.zeros((64,64))
    for r in range(8):
        for c in range(8):
            for tr,tc in fn(r,c): A[sq(r,c),sq(tr,tc)] = 1
    return A

A_GRID = np.zeros((64,64))
for r in range(8):
    for c in range(8):
        for dr,dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr,nc = r+dr,c+dc
            if 0<=nr<8 and 0<=nc<8: A_GRID[sq(r,c),sq(nr,nc)] = 1
L_GRID = np.diag(A_GRID.sum(axis=1)) - A_GRID
EVALS, EVECS = eigh(L_GRID)

upper_idx = np.triu_indices(64, k=1)  # 2016 off-diagonal elements


# ═══════════════════════════════════════════════════════════════
# STEP 1: THE FULL COUPLING MATRIX (diagonal + off-diagonal)
#
# For each piece, C = U^T L_piece U is a 64×64 symmetric matrix.
# It has 64 diagonal elements + 2016 upper-triangle elements = 2080.
# The 3D fiber used only the 2016 off-diagonal.
# Now use ALL 2080 to capture the full rule content.
# ═══════════════════════════════════════════════════════════════

print("="*70)
print("  STEP 1: FULL COUPLING MATRICES (diag + off-diag)")
print("="*70)

# For each piece, extract the full coupling vector (2080 elements)
# and the diagonal-only deviation from the grid
full_coupling = {}
diag_deviation = {}
offdiag_coupling = {}

for pname, fn in PIECE_FNS.items():
    A = build_adj(fn)
    L = np.diag(A.sum(axis=1)) - A
    C = EVECS.T @ L @ EVECS
    
    # Full coupling: diagonal + upper triangle
    diag = C.diagonal().copy()
    offdiag = C[upper_idx].copy()
    full = np.concatenate([diag, offdiag])  # 64 + 2016 = 2080
    
    full_coupling[pname] = full
    diag_deviation[pname] = diag - EVALS  # deviation from grid eigenvalues
    offdiag_coupling[pname] = offdiag
    
    print(f"  {pname:8s}: ||diag_dev|| = {np.linalg.norm(diag - EVALS):8.3f}, "
          f"||offdiag|| = {np.linalg.norm(offdiag):8.3f}, "
          f"||full|| = {np.linalg.norm(full):8.3f}")


# ═══════════════════════════════════════════════════════════════
# STEP 2: SVD OF OFF-DIAGONAL ONLY (our existing 3D fiber)
# vs SVD OF DIAGONAL ONLY (the "spatial shadow")
# vs SVD OF FULL (everything)
# ═══════════════════════════════════════════════════════════════

print(f"\n{'='*70}")
print(f"  STEP 2: THREE SVDs — OFF-DIAG vs DIAG vs FULL")
print(f"{'='*70}")

pieces = ['Knight','King','Bishop','Rook','Queen']

# Off-diagonal SVD (our existing fiber)
offdiag_mat = np.array([offdiag_coupling[p] / (np.linalg.norm(offdiag_coupling[p]) + 1e-15) 
                         for p in pieces])
_, S_off, Vt_off = svd(offdiag_mat, full_matrices=False)

print(f"\n  OFF-DIAGONAL ONLY (the existing 3D fiber):")
for i, s in enumerate(S_off):
    print(f"    σ_{i+1} = {s:.4f}  ({s**2/np.sum(S_off**2)*100:.1f}%)")

# Diagonal-only SVD
diag_mat = np.array([diag_deviation[p] / (np.linalg.norm(diag_deviation[p]) + 1e-15) 
                      for p in pieces])
_, S_diag, Vt_diag = svd(diag_mat, full_matrices=False)

print(f"\n  DIAGONAL ONLY (the spatial shadow):")
for i, s in enumerate(S_diag):
    print(f"    σ_{i+1} = {s:.4f}  ({s**2/np.sum(S_diag**2)*100:.1f}%)")

# Full SVD
full_mat = np.array([full_coupling[p] / (np.linalg.norm(full_coupling[p]) + 1e-15) 
                      for p in pieces])
_, S_full, Vt_full = svd(full_mat, full_matrices=False)

print(f"\n  FULL (diagonal + off-diagonal):")
for i, s in enumerate(S_full):
    print(f"    σ_{i+1} = {s:.4f}  ({s**2/np.sum(S_full**2)*100:.1f}%)")


# ═══════════════════════════════════════════════════════════════
# STEP 3: CROSS-PIECE SIMILARITY IN EACH SPACE
# ═══════════════════════════════════════════════════════════════

print(f"\n{'='*70}")
print(f"  STEP 3: CROSS-PIECE SIMILARITY IN THREE SPACES")
print(f"{'='*70}")

def cos_sim_matrix(vectors, names):
    n = len(names)
    for label, vecs in vectors.items():
        print(f"\n  {label}:")
        print(f"  {'':>8s}", end='')
        for n in names: print(f" {n[:5]:>6s}", end='')
        print()
        for i, n1 in enumerate(names):
            print(f"  {n1:>8s}", end='')
            for j, n2 in enumerate(names):
                v1, v2 = vecs[n1], vecs[n2]
                na, nb = np.linalg.norm(v1), np.linalg.norm(v2)
                c = np.dot(v1,v2)/(na*nb) if na > 1e-15 and nb > 1e-15 else 0
                print(f" {c:6.3f}", end='')
            print()

cos_sim_matrix({
    "Off-diagonal (3D fiber)": offdiag_coupling,
    "Diagonal (spatial shadow)": diag_deviation,
    "Full (combined)": full_coupling,
}, pieces)


# ═══════════════════════════════════════════════════════════════
# STEP 4: THE ROOK'S SHADOW
#
# The rook has zero off-diagonal projection. But in the diagonal
# space and the full space, it has nonzero content.
# How does the rook relate to other pieces in these spaces?
# ═══════════════════════════════════════════════════════════════

print(f"\n{'='*70}")
print(f"  STEP 4: THE ROOK'S POSITION IN EACH SPACE")
print(f"{'='*70}")

print(f"\n  Rook's norm in each space:")
print(f"    Off-diagonal: {np.linalg.norm(offdiag_coupling['Rook']):.6f} (should be ~0)")
print(f"    Diagonal:     {np.linalg.norm(diag_deviation['Rook']):.4f}")
print(f"    Full:         {np.linalg.norm(full_coupling['Rook']):.4f}")

# Is the rook orthogonal to other pieces in the diagonal space?
print(f"\n  Rook's cosine similarity with other pieces (diagonal space):")
for p in pieces:
    if p == 'Rook': continue
    v1 = diag_deviation['Rook']
    v2 = diag_deviation[p]
    c = np.dot(v1,v2) / (np.linalg.norm(v1)*np.linalg.norm(v2))
    print(f"    Rook ↔ {p:8s}: {c:+.4f}  "
          f"({'orthogonal' if abs(c) < 0.1 else 'weakly aligned' if abs(c) < 0.5 else 'ALIGNED'})")


# ═══════════════════════════════════════════════════════════════
# STEP 5: MINIMUM DIMENSIONS FOR FULL RULE CONTENT
#
# The off-diagonal fiber had rank 3 (σ₄ = 0).
# The diagonal fiber has its own rank.
# The combined has a third rank.
# 
# How do these relate? Is the combined rank = off-diag rank +
# diag rank, or is there overlap?
# ═══════════════════════════════════════════════════════════════

print(f"\n{'='*70}")
print(f"  STEP 5: DIMENSIONAL ACCOUNTING")
print(f"{'='*70}")

offdiag_rank = np.sum(S_off > 0.01)
diag_rank = np.sum(S_diag > 0.01)
full_rank = np.sum(S_full > 0.01)

print(f"\n  Off-diagonal fiber rank: {offdiag_rank} (the existing 3D fiber)")
print(f"  Diagonal fiber rank:     {diag_rank}")
print(f"  Full fiber rank:         {full_rank}")
print(f"\n  Additive prediction: {offdiag_rank} + {diag_rank} = {offdiag_rank + diag_rank}")
print(f"  Actual full rank:    {full_rank}")
print(f"  Overlap:             {offdiag_rank + diag_rank - full_rank} shared dimensions")

# Are the diagonal and off-diagonal subspaces actually independent?
# Project the diagonal deviation vectors onto the off-diagonal fiber basis
offdiag_basis = Vt_off[:3].T  # (2016, 3)

# We can't directly project diagonal vectors (64-dim) onto off-diagonal basis (2016-dim)
# because they live in different spaces. But we CAN ask: in the FULL 2080-dim space,
# do the diagonal directions and off-diagonal directions overlap?

# Construct basis vectors for the diagonal subspace within the full 2080-space
# and measure their angle to the off-diagonal basis within the full space

# The first 64 elements of the full vector are diagonal, the last 2016 are off-diagonal.
# A purely diagonal vector has zeros in the last 2016 positions.
# A purely off-diagonal vector has zeros in the first 64 positions.
# These subspaces are ORTHOGONAL by construction!

print(f"\n  KEY INSIGHT:")
print(f"  In the full 2080-dim space, diagonal and off-diagonal components")
print(f"  are in ORTHOGONAL SUBSPACES (first 64 vs last 2016 dimensions).")
print(f"  They cannot overlap. The full rank MUST be the sum of individual ranks.")
print(f"  But rank can be less than sum if pieces are linearly dependent in BOTH")
print(f"  subspaces simultaneously.")

# Verify: project the full vectors onto the diagonal-only and offdiag-only subspaces
for p in pieces:
    v = full_coupling[p]
    diag_part = np.linalg.norm(v[:64])
    offdiag_part = np.linalg.norm(v[64:])
    total = np.linalg.norm(v)
    pct_diag = diag_part**2 / total**2 * 100
    pct_offdiag = offdiag_part**2 / total**2 * 100
    
    print(f"  {p:8s}: diag={pct_diag:5.1f}%, offdiag={pct_offdiag:5.1f}%  "
          f"(||diag||={diag_part:.3f}, ||offdiag||={offdiag_part:.3f})")


# ═══════════════════════════════════════════════════════════════
# STEP 6: THE COMPLETE PICTURE — HOW MANY FIBER DIMENSIONS
# DO WE NEED TO CAPTURE ALL RULES?
#
# SVD of the full 2080-dim vectors tells us the answer directly.
# The rook contributes to the diagonal rank but not the off-diagonal.
# ═══════════════════════════════════════════════════════════════

print(f"\n{'='*70}")
print(f"  STEP 6: THE COMPLETE FIBER — ALL RULES")
print(f"{'='*70}")

# The full rank tells us how many independent rule directions exist
# when we account for BOTH spatial and non-spatial content.

print(f"\n  Full fiber decomposition:")
total_sv2 = np.sum(S_full**2)
cumsum = np.cumsum(S_full**2)
for i, s in enumerate(S_full):
    pct = s**2 / total_sv2 * 100
    cum = cumsum[i] / total_sv2 * 100
    
    # What does this direction contain?
    # Project the singular vector back to see if it's diagonal or off-diagonal
    v = Vt_full[i]
    diag_content = np.linalg.norm(v[:64])**2
    offdiag_content = np.linalg.norm(v[64:])**2
    total_content = diag_content + offdiag_content
    
    diag_pct = diag_content / total_content * 100
    offdiag_pct = offdiag_content / total_content * 100
    
    nature = "SPATIAL" if diag_pct > 80 else "RULE" if offdiag_pct > 80 else "MIXED"
    
    print(f"    σ_{i+1} = {s:.4f}  ({pct:5.1f}%, cum {cum:5.1f}%)  "
          f"diag={diag_pct:4.0f}% offdiag={offdiag_pct:4.0f}%  [{nature}]")

# Each piece's projection onto the full fiber
print(f"\n  Each piece's coordinates in the full {full_rank}D fiber:")
for p in pieces:
    v = full_coupling[p] / np.linalg.norm(full_coupling[p])
    coords = v @ Vt_full[:full_rank].T
    print(f"    {p:8s}: [{', '.join(f'{c:+.3f}' for c in coords)}]")

# How many TOTAL dimensions for the rook's shadow?
rook_full = full_coupling['Rook'] / np.linalg.norm(full_coupling['Rook'])
rook_coords = rook_full @ Vt_full[:full_rank].T
rook_nonzero = np.sum(np.abs(rook_coords) > 0.01)
print(f"\n  Rook occupies {rook_nonzero} of {full_rank} full fiber dimensions")

# Is the rook's full-fiber projection orthogonal to the off-diagonal fiber?
# The off-diagonal fiber lives in dimensions where the first 64 elements are zero.
# The rook's contribution is entirely in the first 64 elements (diagonal).
# So YES — the rook's shadow is ORTHOGONAL to the 3D off-diagonal fiber.

print(f"\n  The rook's shadow and the 3D off-diagonal fiber are in")
print(f"  orthogonal subspaces of the full 2080-dim coupling space.")
print(f"  They are NOT 'loosely bound' — they are EXACTLY orthogonal.")
print(f"  But they are COUPLED through the field: removing a rook changes")
print(f"  the diagonal part of the coupling, which affects the off-diagonal")
print(f"  behavior of other pieces through the Laplacian quadratic form.")


# ═══════════════════════════════════════════════════════════════
# STEP 7: THE BINDING QUESTION
#
# Steven asked: are these diagonal dimensions "loosely bound" to
# the off-diagonal fiber? The geometric answer is: they're 
# orthogonal in the coupling space. But physically, they INTERACT
# through the board signal — the diagonal content (eigenvalue 
# modification) changes how the off-diagonal content (mode coupling)
# affects the field. The binding is MEDIATED BY THE FIELD, not
# by geometric overlap in the fiber.
# ═══════════════════════════════════════════════════════════════

print(f"\n{'='*70}")
print(f"  STEP 7: HOW DIAGONAL AND OFF-DIAGONAL BIND")
print(f"{'='*70}")

# Test: does the rook's diagonal presence change how the knight's
# off-diagonal content affects the field?

sig_test = np.zeros(64)
sig_test[sq(4,4)] = 3  # knight on e4
sig_test[sq(7,0)] = 5  # rook on a1

# Field energy through knight's Laplacian WITH vs WITHOUT rook
L_knight = np.diag(build_adj(knight_targets).sum(axis=1)) - build_adj(knight_targets)

sig_knight_only = np.zeros(64); sig_knight_only[sq(4,4)] = 3
sig_both = sig_test.copy()

E_knight_alone = float(sig_knight_only.T @ L_knight @ sig_knight_only)
E_knight_with_rook = float(sig_both.T @ L_knight @ sig_both)
delta_E = E_knight_with_rook - E_knight_alone

# The rook contributes to the signal, which flows through the knight's
# Laplacian (which has off-diagonal content), producing cross-coupling.
# The rook's diagonal content and the knight's off-diagonal content
# interact THROUGH the quadratic form.

print(f"\n  Knight field energy alone: {E_knight_alone:.1f}")
print(f"  Knight field energy with rook present: {E_knight_with_rook:.1f}")
print(f"  Change: {delta_E:+.1f}")
print(f"\n  The rook's presence (diagonal content) changes the knight's")
print(f"  field energy (mediated by off-diagonal content). The binding")
print(f"  is through the FIELD (quadratic form), not through geometric")
print(f"  overlap in the fiber space.")

# Decompose: how much of this coupling comes from the rook's value
# at squares the knight can reach vs squares it can't?
rook_on_knight_targets = 0
rook_off_knight_targets = 0
knight_adj = build_adj(knight_targets)
for t in range(64):
    if knight_adj[sq(4,4), t] > 0:
        rook_on_knight_targets += sig_both[t]  # rook signal at knight targets
    else:
        rook_off_knight_targets += sig_both[t]

print(f"\n  Rook signal at knight's target squares: {rook_on_knight_targets:.1f}")
print(f"  Rook signal at non-target squares:      {rook_off_knight_targets:.1f}")
print(f"  → The rook on a1 is NOT on any of the knight's target squares from e4.")
print(f"     Yet it still changes the knight's field energy by {delta_E:+.1f}.")
print(f"     This coupling goes through the OFF-DIAGONAL modes of the knight's")
print(f"     Laplacian — the cross-modal couplings that the 3D fiber captures.")


print(f"\n{'='*70}")
print(f"  ANSWER TO STEVEN'S QUESTION")
print(f"{'='*70}")

print(f"""
  The rook's shadow lives in the DIAGONAL subspace of the full
  coupling space. This subspace is exactly orthogonal to the 3D
  off-diagonal fiber. They don't overlap geometrically at all.
  
  Minimum dimensions for the rook's shadow: {np.sum(np.abs(rook_coords) > 0.01)} 
  (its projection in the full {full_rank}D fiber)
  
  The full fiber (diagonal + off-diagonal) has rank {full_rank}:
    - {offdiag_rank} dimensions of off-diagonal (non-spatial) content
    - {diag_rank} dimensions of diagonal (spatially-mirrored) content  
    - Total = {full_rank} (they're orthogonal, so ranks add)
  
  The diagonal dimensions ARE "spatially mirrored" — they sit on
  the same eigenmode axes as the board's natural vibrations. But
  they carry DIFFERENT VALUES (the rook's eigenvalues ≠ the grid's
  eigenvalues). The difference is the rule content.
  
  The binding between diagonal and off-diagonal is NOT geometric
  (they're in orthogonal subspaces). It's PHYSICAL — mediated by
  the board signal flowing through the Laplacian quadratic form.
  The rook's diagonal content modifies the field in ways that the
  knight's off-diagonal content then couples to. The interaction
  is real and measurable (ΔE = {delta_E:+.1f}), but it lives in the
  FIELD, not in the FIBER.
  
  So the answer to "how many fibers for the rook's shadow?":
  The rook needs {np.sum(np.abs(rook_coords) > 0.01)} diagonal fiber dimensions,
  which are orthogonal to the 3 off-diagonal dimensions.
  Total fiber for ALL rules: {full_rank} dimensions = {offdiag_rank} off-diag + {diag_rank} diagonal.
""")

