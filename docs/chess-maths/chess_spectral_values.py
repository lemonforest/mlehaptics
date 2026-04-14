"""
Spectrally Derived Piece Values
================================
Replace magic numbers with values derived from the pieces'
own spectral properties. Three approaches:

1. INTRINSIC: properties of the piece's movement graph
   (λ₂, mean degree, spectral bandwidth, graph energy)

2. PROBE: measure piece-board interaction at specific positions
   (center, starting square, full board) — Steven's atom-probing idea

3. INTERACTION: derive values from the cross-species coupling
   matrix (how each piece relates to every other)
"""

import numpy as np
from scipy.linalg import eigh
import warnings
warnings.filterwarnings('ignore')

def sq(r,c): return r*8+c
def rc(s): return s//8, s%8

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

PIECE_FNS = {'N':knight_targets,'B':bishop_targets,'R':rook_targets,
             'Q':queen_targets,'K':king_targets}

def build_adj(fn):
    A = np.zeros((64,64))
    for r in range(8):
        for c in range(8):
            for tr,tc in fn(r,c): A[sq(r,c),sq(tr,tc)] = 1
    return A

def graph_laplacian(A):
    return np.diag(A.sum(axis=1)) - A

A_GRID = np.zeros((64,64))
for r in range(8):
    for c in range(8):
        for dr,dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr,nc = r+dr,c+dc
            if 0<=nr<8 and 0<=nc<8: A_GRID[sq(r,c),sq(nr,nc)] = 1
L_GRID = graph_laplacian(A_GRID)
EVALS, EVECS = eigh(L_GRID)

# Starting squares
START_SQ = {
    'N': [sq(7,1), sq(7,6)],  # b1, g1
    'B': [sq(7,2), sq(7,5)],  # c1, f1
    'R': [sq(7,0), sq(7,7)],  # a1, h1
    'Q': [sq(7,3)],           # d1
    'K': [sq(7,4)],           # e1
}

# Traditional values for comparison
TRAD_VALUES = {'N': 3, 'B': 3.5, 'R': 5, 'Q': 9, 'K': 4}  
# K=4 here (not 100) — the king's MOVEMENT VALUE, not game-ending value

upper_idx = np.triu_indices(64, k=1)

# Pre-compute piece adjacencies and Laplacians
piece_As = {p: build_adj(fn) for p, fn in PIECE_FNS.items()}
piece_Ls = {p: graph_laplacian(A) for p, A in piece_As.items()}


# ═══════════════════════════════════════════════════════════════
# APPROACH 1: INTRINSIC SPECTRAL VALUES
# Properties of the piece's movement graph, no board context
# ═══════════════════════════════════════════════════════════════

print("="*70)
print("  APPROACH 1: INTRINSIC SPECTRAL VALUES")
print("  (Properties of the movement graph itself)")
print("="*70)

intrinsic = {}

print(f"\n  {'Piece':>6s} {'λ₂':>8s} {'⟨degree⟩':>9s} {'BW':>8s} {'GraphE':>8s} "
      f"{'Tr(L)/2':>8s} {'SpRadius':>9s}")

for p in ['N','B','R','Q','K']:
    A = piece_As[p]
    L = piece_Ls[p]
    evals, _ = eigh(L)
    evals_A = np.sort(np.linalg.eigvals(A).real)
    
    nonzero = evals[evals > 1e-10]
    lambda2 = nonzero[0] if len(nonzero) > 0 else 0
    mean_deg = A.sum(axis=1).mean()
    bandwidth = evals[-1]
    graph_energy = np.sum(np.abs(evals_A))  # sum of |eigenvalues of A|
    trace_half = np.trace(L) / 2  # = number of edges
    spectral_radius = np.max(np.abs(evals_A))  # largest |eigenvalue of A|
    
    intrinsic[p] = {
        'lambda2': lambda2,
        'mean_degree': mean_deg,
        'bandwidth': bandwidth,
        'graph_energy': graph_energy,
        'edges': trace_half,
        'spectral_radius': spectral_radius,
    }
    
    print(f"  {p:>6s} {lambda2:8.3f} {mean_deg:9.2f} {bandwidth:8.2f} "
          f"{graph_energy:8.2f} {trace_half:8.0f} {spectral_radius:9.3f}")

# Normalize each metric to [0, max] and compare to traditional values
print(f"\n  Normalized intrinsic values (traditional value in parentheses):")
print(f"  {'Piece':>6s} {'Trad':>6s} {'λ₂':>6s} {'Degree':>7s} {'BW':>6s} {'Energy':>7s} {'Edges':>6s} {'SpecR':>6s}")

for p in ['N','B','R','Q','K']:
    tv = TRAD_VALUES[p]
    vals = {}
    for metric in ['lambda2','mean_degree','bandwidth','graph_energy','edges','spectral_radius']:
        raw = {pp: intrinsic[pp][metric] for pp in ['N','B','R','Q','K']}
        max_v = max(raw.values())
        vals[metric] = raw[p] / max_v * 9  # scale to match queen=9
    
    print(f"  {p:>6s} {tv:6.1f} {vals['lambda2']:6.2f} {vals['mean_degree']:7.2f} "
          f"{vals['bandwidth']:6.2f} {vals['graph_energy']:7.2f} {vals['edges']:6.2f} {vals['spectral_radius']:6.2f}")


# ═══════════════════════════════════════════════════════════════
# APPROACH 2: PROBE-BASED VALUES (Steven's atom-probing idea)
#
# Place each piece alone at specific positions and measure:
# a) Local fiber norm (rule-space activity)
# b) Laplacian quadratic form of a unit signal (graph smoothness)
# c) Number of reachable squares (raw mobility)
# d) Spectral entropy at that position
#
# Three probes: center, starting square, full-board starting position
# ═══════════════════════════════════════════════════════════════

print(f"\n{'='*70}")
print(f"  APPROACH 2: PROBE-BASED VALUES (atom-probing)")
print(f"  Measure piece properties at center, start, and in full board")
print(f"{'='*70}")

# Local fiber norm
def local_fiber_norm(fn, source_sq):
    r, c = rc(source_sq)
    A_loc = np.zeros((64,64))
    for tr,tc in fn(r,c):
        t = sq(tr,tc)
        A_loc[source_sq, t] = 1; A_loc[t, source_sq] = 1
    C = EVECS.T @ A_loc @ EVECS
    C_off = C.copy(); np.fill_diagonal(C_off, 0)
    return np.linalg.norm(C_off[upper_idx])

# Mobility (reachable squares)
def mobility(fn, source_sq):
    r, c = rc(source_sq)
    return sum(1 for _ in fn(r, c))

# Local graph energy: signal energy through piece Laplacian
def local_laplacian_energy(piece_char, source_sq):
    """Energy of a unit point source at source_sq through piece's Laplacian."""
    sig = np.zeros(64); sig[source_sq] = 1
    return float(sig.T @ piece_Ls[piece_char] @ sig)

print(f"\n  CENTER PROBE (piece alone at d4/e4):")
center = sq(4, 4)  # e4 — one of the 4 most central squares

print(f"  {'Piece':>6s} {'Mobility':>9s} {'FiberNorm':>10s} {'LaplE':>8s}")
center_vals = {}
for p, fn in PIECE_FNS.items():
    mob = mobility(fn, center)
    fib = local_fiber_norm(fn, center)
    lap_e = local_laplacian_energy(p, center)
    center_vals[p] = {'mobility': mob, 'fiber': fib, 'lapl_e': lap_e}
    print(f"  {p:>6s} {mob:9d} {fib:10.4f} {lap_e:8.1f}")

print(f"\n  STARTING SQUARE PROBE (piece at its game-start position):")
print(f"  {'Piece':>6s} {'Square':>8s} {'Mobility':>9s} {'FiberNorm':>10s} {'LaplE':>8s}")
start_vals = {}
for p, fn in PIECE_FNS.items():
    ssq = START_SQ[p][0]  # first starting square
    mob = mobility(fn, ssq)
    fib = local_fiber_norm(fn, ssq)
    lap_e = local_laplacian_energy(p, ssq)
    start_vals[p] = {'mobility': mob, 'fiber': fib, 'lapl_e': lap_e}
    from chess_spectral_values import sq as _  # just to get sqname
    print(f"  {p:>6s} {'abcdefgh'[ssq%8]+str(8-ssq//8):>8s} {mob:9d} {fib:10.4f} {lap_e:8.1f}")

# FULL BOARD PROBE: how much does each piece contribute to the
# total field when all pieces are at starting positions?
print(f"\n  FULL BOARD PROBE (each piece's contribution to starting field):")

# Starting position signal
start_pos = {}
for i in range(8): start_pos[sq(6,i)] = 'P'  # white pawns
for i in range(8): start_pos[sq(1,i)] = 'p'  # black pawns
start_pos.update({sq(7,0):'R',sq(7,7):'R',sq(7,1):'N',sq(7,6):'N',
                  sq(7,2):'B',sq(7,5):'B',sq(7,3):'Q',sq(7,4):'K',
                  sq(0,0):'r',sq(0,7):'r',sq(0,1):'n',sq(0,6):'n',
                  sq(0,2):'b',sq(0,5):'b',sq(0,3):'q',sq(0,4):'k'})

# For each piece type's graph, compute the field gradient
# at each white piece's starting square
print(f"  {'Piece':>6s} {'⟨gradient⟩':>11s} {'⟨|gradient|⟩':>13s} {'Sensitivity':>12s}")

full_board_vals = {}
for p in ['N','B','R','Q','K']:
    L = piece_Ls[p]
    
    # Build the starting signal with unit values (no magic numbers!)
    sig_unit = np.zeros(64)
    for s, piece in start_pos.items():
        sig_unit[s] = 1 if piece.isupper() else -1
    
    # Field gradient: (Lf) at each square
    Lf = L @ sig_unit
    
    # Average gradient at this piece type's starting squares
    gradients = [Lf[s] for s in START_SQ[p]]
    abs_gradients = [abs(Lf[s]) for s in START_SQ[p]]
    
    # Sensitivity: how much does the total field energy change
    # when we remove this piece type from the starting position?
    sig_without = sig_unit.copy()
    for s in START_SQ[p]:
        sig_without[s] = 0
    
    E_full = float(sig_unit.T @ L @ sig_unit)
    E_without = float(sig_without.T @ L @ sig_without)
    sensitivity = E_full - E_without
    
    full_board_vals[p] = {
        'gradient': np.mean(gradients),
        'abs_gradient': np.mean(abs_gradients),
        'sensitivity': sensitivity,
    }
    
    print(f"  {p:>6s} {np.mean(gradients):+11.2f} {np.mean(abs_gradients):13.2f} {sensitivity:12.2f}")


# ═══════════════════════════════════════════════════════════════
# APPROACH 3: INTERACTION-BASED VALUES
#
# For each pair of piece types, measure how strongly they
# interact (coupling strength from §5c). The piece's "value"
# is its total interaction strength with all other pieces.
# ═══════════════════════════════════════════════════════════════

print(f"\n{'='*70}")
print(f"  APPROACH 3: INTERACTION-BASED VALUES")
print(f"  (Value = total coupling strength with other pieces)")
print(f"{'='*70}")

# Use the cross-graph coupling: for a unit signal, 
# how strongly does piece A's graph energy change when piece B is present?

print(f"\n  Cross-piece coupling matrix (unit signal):")
print(f"  {'':>6s}", end='')
for p2 in ['N','B','R','Q','K']: print(f" {p2:>6s}", end='')
print(f" {'Total':>8s}")

coupling_values = {}

for p1 in ['N','B','R','Q','K']:
    L1 = piece_Ls[p1]
    print(f"  {p1:>6s}", end='')
    
    total = 0
    for p2 in ['N','B','R','Q','K']:
        # Place both pieces at center-ish squares
        s1, s2 = sq(4,4), sq(2,3)
        sig = np.zeros(64); sig[s1] = 1; sig[s2] = 1
        sig_1only = np.zeros(64); sig_1only[s1] = 1
        
        E_both = float(sig.T @ L1 @ sig)
        E_alone = float(sig_1only.T @ L1 @ sig_1only)
        coupling = E_both - E_alone
        
        print(f" {coupling:6.1f}", end='')
        total += abs(coupling)
    
    coupling_values[p1] = total
    print(f" {total:8.1f}")


# ═══════════════════════════════════════════════════════════════
# COMPARISON: ALL VALUE SYSTEMS
# ═══════════════════════════════════════════════════════════════

print(f"\n{'='*70}")
print(f"  COMPARISON: ALL VALUE SYSTEMS (normalized to Q=9)")
print(f"{'='*70}")

systems = {
    'Traditional': {p: TRAD_VALUES[p] for p in ['N','B','R','Q','K']},
    'λ₂ (connectivity)': {p: intrinsic[p]['lambda2'] for p in ['N','B','R','Q','K']},
    'Mean degree': {p: intrinsic[p]['mean_degree'] for p in ['N','B','R','Q','K']},
    'Bandwidth': {p: intrinsic[p]['bandwidth'] for p in ['N','B','R','Q','K']},
    'Graph energy': {p: intrinsic[p]['graph_energy'] for p in ['N','B','R','Q','K']},
    'Center mobility': {p: center_vals[p]['mobility'] for p in ['N','B','R','Q','K']},
    'Center fiber': {p: center_vals[p]['fiber'] for p in ['N','B','R','Q','K']},
    'Start sensitivity': {p: full_board_vals[p]['sensitivity'] for p in ['N','B','R','Q','K']},
    'Interaction total': {p: coupling_values[p] for p in ['N','B','R','Q','K']},
}

# Normalize all to queen=9 scale
print(f"\n  {'System':>22s}", end='')
for p in ['N','B','R','Q','K']: print(f" {p:>6s}", end='')
print(f"  {'Rank order':>20s}")

for name, vals in systems.items():
    q_val = vals['Q']
    if abs(q_val) < 1e-10:
        continue
    normalized = {p: v / q_val * 9 for p, v in vals.items()}
    
    # Rank order
    ranked = sorted(normalized.items(), key=lambda x: x[1], reverse=True)
    rank_str = '>'.join(p for p,_ in ranked)
    
    print(f"  {name:>22s}", end='')
    for p in ['N','B','R','Q','K']:
        print(f" {normalized[p]:6.2f}", end='')
    print(f"  {rank_str:>20s}")


# ═══════════════════════════════════════════════════════════════
# CORRELATION WITH TRADITIONAL VALUES
# ═══════════════════════════════════════════════════════════════

print(f"\n{'='*70}")
print(f"  CORRELATION OF EACH SYSTEM WITH TRADITIONAL VALUES")
print(f"{'='*70}")

trad_vec = np.array([TRAD_VALUES[p] for p in ['N','B','R','Q','K']])

print(f"\n  {'System':>22s} {'Pearson r':>10s} {'Rank match':>11s}")

for name, vals in systems.items():
    if name == 'Traditional': continue
    v = np.array([vals[p] for p in ['N','B','R','Q','K']])
    
    # Pearson correlation
    corr = np.corrcoef(v, trad_vec)[0,1]
    
    # Rank correlation (Spearman)
    from scipy.stats import spearmanr
    rho, _ = spearmanr(v, trad_vec)
    
    print(f"  {name:>22s} {corr:+10.4f} {rho:+11.4f}")


# ═══════════════════════════════════════════════════════════════
# THE SPECTRAL VALUE RECOMMENDATION
# ═══════════════════════════════════════════════════════════════

print(f"\n{'='*70}")
print(f"  SPECTRAL VALUE RECOMMENDATION")
print(f"{'='*70}")

# Pick the metric with highest correlation to traditional values
# but also check if it produces better ENCODING properties

# λ₂ is the algebraic connectivity — the most fundamental spectral
# quantity. It measures how well-connected the graph is (Fiedler 1973).
# Let's use it as the base value.

lambda2_values = {p: intrinsic[p]['lambda2'] for p in ['N','B','R','Q','K']}
# Scale so N=3 (traditional reference point for minor pieces)
scale = 3 / lambda2_values['N']
spectral_values = {p: v * scale for p, v in lambda2_values.items()}

print(f"\n  λ₂-based values (scaled to N=3):")
for p in ['N','B','R','Q','K']:
    trad = TRAD_VALUES[p]
    spec = spectral_values[p]
    diff = spec - trad
    print(f"    {p}: spectral = {spec:.2f}, traditional = {trad:.1f}, diff = {diff:+.2f}")

# The king problem: λ₂ gives K=1.09, traditional gives K=4 (movement value).
# The king moves like a short-range queen. Its λ₂ is low because it has
# poor connectivity (can only reach 8 squares from center vs queen's 27).
# But its GAME VALUE is infinite (losing the king = losing).
# 
# Resolution: the king has TWO values:
# - Movement value: λ₂ = 1.09 (weak mover)
# - Game value: ∞ (objective)
# The encoding should use MOVEMENT value for the signal
# and encode king-ness as a separate flag in the quantum numbers.

print(f"\n  RECOMMENDED VALUE SYSTEM:")
print(f"  Use λ₂ (algebraic connectivity) for movement/signal values.")
print(f"  Encode king identity separately through quantum numbers.")
print(f"  This eliminates the K=100 domination problem entirely.")

# Dynamic range comparison
print(f"\n  Dynamic range comparison:")
trad_range = max(TRAD_VALUES.values()) / min(TRAD_VALUES.values())
spec_range = max(spectral_values.values()) / min(spectral_values.values())
magic_range = 100 / 1  # with K=100
print(f"    Magic (K=100):    {magic_range:.0f}x")
print(f"    Traditional (K=4): {trad_range:.1f}x")
print(f"    Spectral (λ₂):    {spec_range:.1f}x")

