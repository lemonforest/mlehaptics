"""
Local Fiber Encoder: Full Test Battery
=======================================
Testing Grok's local fiber implementation against our original
failure cases. Every test that failed in Section 8 gets re-run.
"""

import numpy as np
from scipy.linalg import eigh, svd
from scipy.fft import dctn
import warnings
warnings.filterwarnings('ignore')

# ─── Standard preamble (from consolidated.py) ───
def sq(r,c): return r*8+c
def rc(s): return s//8, s%8
def sqname(s): return 'abcdefgh'[s%8] + str(8 - s//8)

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
SHORT_PFNS = {'N':knight_targets,'B':bishop_targets,'R':rook_targets,
              'Q':queen_targets,'K':king_targets}
VALS = {'P':1,'N':3,'B':3.5,'R':5,'Q':9,'K':100,
        'p':-1,'n':-3,'b':-3.5,'r':-5,'q':-9,'k':-100}

def build_adjacency(fn):
    A = np.zeros((64,64))
    for r in range(8):
        for c in range(8):
            for tr,tc in fn(r,c): A[sq(r,c),sq(tr,tc)] = 1
    return A

def graph_laplacian(A):
    return np.diag(A.sum(axis=1)) - A

# Board eigenbasis
A_GRID = np.zeros((64,64))
for _r in range(8):
    for _c in range(8):
        for _dr,_dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            _nr,_nc = _r+_dr, _c+_dc
            if 0<=_nr<8 and 0<=_nc<8: A_GRID[sq(_r,_c),sq(_nr,_nc)] = 1
L_GRID = graph_laplacian(A_GRID)
EVALS_GRID, EVECS_GRID = eigh(L_GRID)

# ─── Build shared fiber basis (§7 reproduction) ───
upper_idx = np.triu_indices(64, k=1)
fibers_global = {}
for name in ['Knight','King','Bishop','Queen']:
    A = build_adjacency(PIECE_FNS[name])
    L = graph_laplacian(A)
    C = EVECS_GRID.T @ L @ EVECS_GRID
    C_off = C.copy(); np.fill_diagonal(C_off, 0)
    fibers_global[name] = C_off[upper_idx]

fiber_mat = np.array([fibers_global[n]/np.linalg.norm(fibers_global[n])
                      for n in fibers_global])
_, S_fib, Vt_fib = svd(fiber_mat, full_matrices=False)
fiber_basis = Vt_fib[:3].T  # (2016, 3)

print(f"Fiber basis constructed. Singular values: {S_fib[0]:.4f}, {S_fib[1]:.4f}, {S_fib[2]:.4f}, {S_fib[3]:.4f}")
print(f"Rank-3 confirmed: σ₄ = {S_fib[3]:.6f}")

# ─── Local fiber encoder (Grok's implementation, verified) ───

def local_fiber_vec(fn, source_sq):
    """Local coupling from a single source square."""
    r, c = rc(source_sq)
    A_loc = np.zeros((64,64))
    for tr,tc in fn(r,c):
        t = sq(tr,tc)
        A_loc[source_sq, t] = 1
        A_loc[t, source_sq] = 1
    C_loc = EVECS_GRID.T @ A_loc @ EVECS_GRID
    C_off = C_loc.copy(); np.fill_diagonal(C_off, 0)
    return C_off[upper_idx]

def local_fiber_3d(fn, source_sq):
    """Project local fiber onto the shared 3D basis."""
    return local_fiber_vec(fn, source_sq) @ fiber_basis

def encode_position(pos):
    """67-dimensional encoding: 64 GFT + 3 rule-fiber coords."""
    sig = np.zeros(64)
    for si, pchar in pos.items():
        sig[si] = VALS[pchar]
    gft = EVECS_GRID.T @ sig
    
    fiber_3d = np.zeros(3)
    for si, pchar in pos.items():
        pkey = pchar.upper()
        if pkey in SHORT_PFNS:
            fiber_3d += VALS[pchar] * local_fiber_3d(SHORT_PFNS[pkey], si)
    
    return np.concatenate((gft, fiber_3d))


# ═══════════════════════════════════════════════════════════════
# TEST 1: FISHER DISCRIMINANT — LEGAL vs ILLEGAL MOVE SEPARATION
#
# The EXACT test that failed in Section 8.
# For a knight on e4, compute the 67-dim encoding delta for
# ALL 63 possible destinations. Measure whether legal moves
# cluster separately from illegal ones.
#
# Fisher criterion: J = |μ_legal - μ_illegal|² / (σ²_legal + σ²_illegal)
# J > 1 → separable. J > 4 → strongly separable.
# ═══════════════════════════════════════════════════════════════

print(f"\n{'='*70}")
print(f"  TEST 1: FISHER DISCRIMINANT — LEGAL vs ILLEGAL MOVES")
print(f"  (The exact test that failed for the global encoder)")
print(f"{'='*70}")

# Test each piece type from multiple source squares
test_configs = [
    ('N', knight_targets, [(4,4), (0,0), (3,3), (7,7)]),
    ('B', bishop_targets, [(4,4), (0,0), (5,2)]),
    ('R', rook_targets, [(4,4), (7,0), (3,3)]),
    ('K', king_targets, [(4,4), (0,0), (3,5)]),
    ('Q', queen_targets, [(4,4), (7,3)]),
]

for piece_char, target_fn, source_positions in test_configs:
    piece_name = {'N':'Knight','B':'Bishop','R':'Rook','K':'King','Q':'Queen'}[piece_char]
    
    all_fisher_gft = []
    all_fisher_fiber = []
    all_fisher_total = []
    
    for sr, sc in source_positions:
        src = sq(sr, sc)
        legal_targets = set(sq(tr,tc) for tr,tc in target_fn(sr, sc))
        
        pos_before = {src: piece_char}
        enc_before = encode_position(pos_before)
        
        legal_deltas = []
        illegal_deltas = []
        legal_gft_norms = []
        illegal_gft_norms = []
        legal_fiber_norms = []
        illegal_fiber_norms = []
        
        for dst in range(64):
            if dst == src: continue
            
            pos_after = {dst: piece_char}
            enc_after = encode_position(pos_after)
            delta = enc_after - enc_before
            
            gft_norm = np.linalg.norm(delta[:64])
            fiber_norm = np.linalg.norm(delta[64:])
            total_norm = np.linalg.norm(delta)
            
            if dst in legal_targets:
                legal_deltas.append(delta)
                legal_gft_norms.append(gft_norm)
                legal_fiber_norms.append(fiber_norm)
            else:
                illegal_deltas.append(delta)
                illegal_gft_norms.append(gft_norm)
                illegal_fiber_norms.append(fiber_norm)
        
        # Fisher discriminant for each metric
        for name, legal_vals, illegal_vals in [
            ("GFT", legal_gft_norms, illegal_gft_norms),
            ("Fiber", legal_fiber_norms, illegal_fiber_norms),
        ]:
            ml, sl = np.mean(legal_vals), np.std(legal_vals)
            mi, si = np.mean(illegal_vals), np.std(illegal_vals)
            pooled_var = (sl**2 + si**2) / 2
            fisher = (ml - mi)**2 / pooled_var if pooled_var > 1e-15 else 0
            
            if name == "GFT":
                all_fisher_gft.append(fisher)
            else:
                all_fisher_fiber.append(fisher)
        
        # Full 67-dim Fisher using vector means
        legal_arr = np.array(legal_deltas)
        illegal_arr = np.array(illegal_deltas)
        mu_legal = legal_arr.mean(axis=0)
        mu_illegal = illegal_arr.mean(axis=0)
        # Simplified multivariate Fisher: use Mahalanobis-like measure
        diff = mu_legal - mu_illegal
        total_fisher = np.linalg.norm(diff)**2 / (
            np.mean(np.sum((legal_arr - mu_legal)**2, axis=1)) + 
            np.mean(np.sum((illegal_arr - mu_illegal)**2, axis=1)) + 1e-15)
        all_fisher_total.append(total_fisher)
    
    avg_gft = np.mean(all_fisher_gft)
    avg_fiber = np.mean(all_fisher_fiber)
    avg_total = np.mean(all_fisher_total)
    
    sep_gft = "YES" if avg_gft > 1 else "weak" if avg_gft > 0.1 else "NO"
    sep_fiber = "YES" if avg_fiber > 1 else "weak" if avg_fiber > 0.1 else "NO"
    sep_total = "YES" if avg_total > 1 else "weak" if avg_total > 0.1 else "NO"
    
    print(f"\n  {piece_name} (averaged over {len(source_positions)} source squares):")
    print(f"    GFT Fisher:       {avg_gft:8.4f}  → {sep_gft}")
    print(f"    Fiber Fisher:     {avg_fiber:8.4f}  → {sep_fiber}")
    print(f"    Total 67D Fisher: {avg_total:8.4f}  → {sep_total}")

# Deep dive: knight e4, show every destination
print(f"\n  {'─'*60}")
print(f"  Deep dive: Knight on e4 — all 63 destinations")
print(f"  {'─'*60}")

src = sq(4,4)
legal = set(sq(tr,tc) for tr,tc in knight_targets(4,4))
enc_src = encode_position({src: 'N'})

legal_fibers = []
illegal_fibers = []

print(f"\n  {'Dst':>4s} {'Legal':>6s} {'GFT Δ':>8s} {'Fiber Δ':>8s} {'Total Δ':>8s} {'Fiber 3D':>24s}")
for dst in range(64):
    if dst == src: continue
    enc_dst = encode_position({dst: 'N'})
    delta = enc_dst - enc_src
    gn = np.linalg.norm(delta[:64])
    fn = np.linalg.norm(delta[64:])
    tn = np.linalg.norm(delta)
    is_legal = dst in legal
    marker = " ←" if is_legal else ""
    fiber_vec = delta[64:]
    
    if is_legal:
        legal_fibers.append(fn)
    else:
        illegal_fibers.append(fn)
    
    # Only print legal moves and a sample of illegals
    if is_legal or dst in [sq(3,3), sq(3,4), sq(3,5), sq(5,4), sq(4,3), sq(0,0), sq(7,7)]:
        print(f"  {sqname(dst):>4s} {'LEGAL' if is_legal else '':>6s} {gn:8.4f} {fn:8.4f} {tn:8.4f} "
              f"[{fiber_vec[0]:+.4f},{fiber_vec[1]:+.4f},{fiber_vec[2]:+.4f}]{marker}")

print(f"\n  Legal fiber norms:  min={min(legal_fibers):.4f}, max={max(legal_fibers):.4f}, "
      f"mean={np.mean(legal_fibers):.4f} ± {np.std(legal_fibers):.4f}")
print(f"  Illegal fiber norms: min={min(illegal_fibers):.4f}, max={max(illegal_fibers):.4f}, "
      f"mean={np.mean(illegal_fibers):.4f} ± {np.std(illegal_fibers):.4f}")

# Overlap analysis: do the distributions separate?
from itertools import combinations
legal_set = sorted(legal_fibers)
illegal_set = sorted(illegal_fibers)
# What fraction of illegals have fiber norm within the legal range?
legal_range = (min(legal_fibers), max(legal_fibers))
n_overlap = sum(1 for x in illegal_fibers if legal_range[0] <= x <= legal_range[1])
print(f"  Illegal moves within legal fiber range: {n_overlap}/{len(illegal_fibers)} "
      f"({n_overlap/len(illegal_fibers)*100:.1f}%)")


# ═══════════════════════════════════════════════════════════════
# TEST 2: POSITION QUALITY — DOES THE ENCODING DISTINGUISH
# GOOD FROM BAD POSITIONS?
#
# The exact test that failed in Section 8 (knight e5 vs a1
# produced identical encodings with global fiber).
# ═══════════════════════════════════════════════════════════════

print(f"\n{'='*70}")
print(f"  TEST 2: POSITION QUALITY DISCRIMINATION")
print(f"  (Do good and bad positions encode differently?)")
print(f"{'='*70}")

test_positions = [
    ("Knight on ideal outpost e5",
     {sq(3,4): 'N', sq(6,3): 'P', sq(6,5): 'P'}, "Good"),
    ("Knight on rim a1",
     {sq(7,0): 'N', sq(6,3): 'P', sq(6,5): 'P'}, "Bad"),
    ("Bishop pair on open diags",
     {sq(5,2): 'B', sq(5,5): 'B'}, "Good"),
    ("Bishop hemmed by pawns",
     {sq(7,2): 'B', sq(6,1): 'P', sq(6,3): 'P'}, "Bad"),
    ("Rook on open file d1",
     {sq(7,3): 'R'}, "Good"),
    ("Rook in corner blocked",
     {sq(7,0): 'R', sq(7,1): 'N', sq(6,0): 'P'}, "Bad"),
    ("Centralized king (endgame)",
     {sq(3,3): 'K', sq(4,4): 'P'}, "Good"),
    ("King on back rank",
     {sq(7,4): 'K', sq(6,3): 'P', sq(6,4): 'P', sq(6,5): 'P'}, "Bad"),
]

print(f"\n  {'Position':35s} {'Qual':>5s} {'GFT':>8s} {'Fiber':>8s} {'Total':>8s} {'Fiber 3D':>24s}")

good_fibers = []
bad_fibers = []
good_totals = []
bad_totals = []

for desc, pieces, quality in test_positions:
    enc = encode_position(pieces)
    gn = np.linalg.norm(enc[:64])
    fn = np.linalg.norm(enc[64:])
    tn = np.linalg.norm(enc)
    fv = enc[64:]
    
    print(f"  {desc:35s} {quality:>5s} {gn:8.2f} {fn:8.2f} {tn:8.2f} "
          f"[{fv[0]:+.2f},{fv[1]:+.2f},{fv[2]:+.2f}]")
    
    if quality == "Good":
        good_fibers.append(fn)
        good_totals.append(tn)
    else:
        bad_fibers.append(fn)
        bad_totals.append(tn)

print(f"\n  Good positions: fiber mean={np.mean(good_fibers):.2f} ± {np.std(good_fibers):.2f}")
print(f"  Bad positions:  fiber mean={np.mean(bad_fibers):.2f} ± {np.std(bad_fibers):.2f}")

# Pairwise comparison (same piece type, good vs bad)
print(f"\n  Pairwise good-vs-bad comparison (same piece type):")
for i in range(0, len(test_positions), 2):
    desc_g, pos_g, _ = test_positions[i]
    desc_b, pos_b, _ = test_positions[i+1]
    enc_g = encode_position(pos_g)
    enc_b = encode_position(pos_b)
    
    fiber_diff = np.linalg.norm(enc_g[64:] - enc_b[64:])
    gft_diff = np.linalg.norm(enc_g[:64] - enc_b[:64])
    cos_fiber = np.dot(enc_g[64:], enc_b[64:]) / (np.linalg.norm(enc_g[64:])*np.linalg.norm(enc_b[64:])+1e-15)
    
    print(f"    {desc_g[:20]:20s} vs {desc_b[:20]:20s}")
    print(f"      GFT diff: {gft_diff:.4f}, Fiber diff: {fiber_diff:.4f}, Fiber cos: {cos_fiber:.4f}")
    same = np.allclose(enc_g[64:], enc_b[64:], atol=1e-10)
    print(f"      Fiber identical? {same}  {'← STILL BROKEN' if same else '← FIXED'}")


# ═══════════════════════════════════════════════════════════════
# TEST 3: PIECE-SQUARE TABLE CORRELATION
#
# For each piece type, compute the fiber norm at every square.
# Correlate with known piece-square table heuristics.
# ═══════════════════════════════════════════════════════════════

print(f"\n{'='*70}")
print(f"  TEST 3: PIECE-SQUARE TABLE CORRELATION")
print(f"  (Does fiber activity predict known positional values?)")
print(f"{'='*70}")

known_tables = {
    'N': np.array([
        [-50,-40,-30,-30,-30,-30,-40,-50],
        [-40,-20,  0,  0,  0,  0,-20,-40],
        [-30,  0, 10, 15, 15, 10,  0,-30],
        [-30,  5, 15, 20, 20, 15,  5,-30],
        [-30,  0, 15, 20, 20, 15,  0,-30],
        [-30,  5, 10, 15, 15, 10,  5,-30],
        [-40,-20,  0,  5,  5,  0,-20,-40],
        [-50,-40,-30,-30,-30,-30,-40,-50],
    ], dtype=float),
    'B': np.array([
        [-20,-10,-10,-10,-10,-10,-10,-20],
        [-10,  0,  0,  0,  0,  0,  0,-10],
        [-10,  0,  5, 10, 10,  5,  0,-10],
        [-10,  5,  5, 10, 10,  5,  5,-10],
        [-10,  0, 10, 10, 10, 10,  0,-10],
        [-10, 10, 10, 10, 10, 10, 10,-10],
        [-10,  5,  0,  0,  0,  0,  5,-10],
        [-20,-10,-10,-10,-10,-10,-10,-20],
    ], dtype=float),
}

print(f"\n  {'Piece':>6s} {'Correlation':>12s} {'Interpretation':>30s}")

for pchar, known in known_tables.items():
    fn = SHORT_PFNS[pchar]
    fiber_map = np.zeros((8,8))
    for r in range(8):
        for c in range(8):
            fib_3d = local_fiber_3d(fn, sq(r,c))
            fiber_map[r,c] = np.linalg.norm(fib_3d)
    
    corr = np.corrcoef(fiber_map.flatten(), known.flatten())[0,1]
    interp = "STRONG" if corr > 0.7 else "MODERATE" if corr > 0.4 else "WEAK" if corr > 0.1 else "NONE"
    print(f"  {pchar:>6s} {corr:+12.4f} {interp:>30s}")
    
    # Print the fiber map for visual inspection
    fn_norm = fiber_map / fiber_map.max() if fiber_map.max() > 0 else fiber_map
    print(f"         Fiber activity map:")
    for r in range(8):
        print(f"           {8-r} ", end='')
        for c in range(8):
            print(f" {int(fn_norm[r,c]*9)}", end='')
        print()
    print(f"             a b c d e f g h")


# ═══════════════════════════════════════════════════════════════
# TEST 4: MULTI-PIECE INTERACTION
#
# Does the local fiber encoding capture many-body effects?
# Place two pieces, compare encoding to sum of individual
# encodings. The difference = non-additive interaction term.
# ═══════════════════════════════════════════════════════════════

print(f"\n{'='*70}")
print(f"  TEST 4: MANY-BODY INTERACTION IN LOCAL FIBER ENCODING")
print(f"  (Does encoding capture non-additive piece interactions?)")
print(f"{'='*70}")

test_pairs = [
    ('N', sq(4,4), 'B', sq(2,3), "Knight e4 + Bishop d6"),
    ('R', sq(7,0), 'R', sq(7,7), "Rook a1 + Rook h1"),
    ('Q', sq(7,3), 'K', sq(7,4), "Queen d1 + King e1"),
    ('N', sq(4,4), 'N', sq(3,2), "Knight e4 + Knight c5"),
]

print(f"\n  {'Configuration':30s} {'||enc(A+B)||':>12s} {'||enc(A)+enc(B)||':>18s} {'||diff||':>10s} {'%non-add':>10s}")

for p1, s1, p2, s2, desc in test_pairs:
    # Joint encoding
    enc_joint = encode_position({s1: p1, s2: p2})
    
    # Individual encodings summed
    enc_a = encode_position({s1: p1})
    enc_b = encode_position({s2: p2})
    enc_sum = enc_a + enc_b
    
    diff = enc_joint - enc_sum
    diff_norm = np.linalg.norm(diff)
    joint_norm = np.linalg.norm(enc_joint)
    sum_norm = np.linalg.norm(enc_sum)
    
    # Focus on fiber part
    fiber_diff = np.linalg.norm(diff[64:])
    fiber_joint = np.linalg.norm(enc_joint[64:])
    
    pct = diff_norm / joint_norm * 100 if joint_norm > 0 else 0
    
    print(f"  {desc:30s} {joint_norm:12.4f} {sum_norm:18.4f} {diff_norm:10.4f} {pct:9.1f}%")

print(f"\n  GFT part is exactly additive (linear in signal).")
print(f"  Fiber part: is it additive or does it capture interactions?")

for p1, s1, p2, s2, desc in test_pairs:
    enc_joint = encode_position({s1: p1, s2: p2})
    enc_a = encode_position({s1: p1})
    enc_b = encode_position({s2: p2})
    
    fiber_joint = enc_joint[64:]
    fiber_sum = enc_a[64:] + enc_b[64:]
    fiber_diff_norm = np.linalg.norm(fiber_joint - fiber_sum)
    
    additive = np.allclose(fiber_joint, fiber_sum, atol=1e-10)
    print(f"    {desc:30s}: fiber additive={additive}, ||diff||={fiber_diff_norm:.6f}")


# ═══════════════════════════════════════════════════════════════
# TEST 5: ROOK FIBER SANITY CHECK
#
# Grok claims rook a1→e1 has fiber Δ = 0.880.
# We proved the rook has ZERO global fiber.
# Test: does the LOCAL fiber sum to zero across all rook edges?
# ═══════════════════════════════════════════════════════════════

print(f"\n{'='*70}")
print(f"  TEST 5: ROOK LOCAL FIBER AGGREGATE CHECK")
print(f"  (Local fibers should sum to zero for the rook)")
print(f"{'='*70}")

# Sum local fibers across all 64 squares for each piece
for piece_name, fn in SHORT_PFNS.items():
    total_local = np.zeros(3)
    for s in range(64):
        total_local += local_fiber_3d(fn, s)
    
    print(f"  {piece_name}: sum of local fiber 3D = [{total_local[0]:+.4f}, {total_local[1]:+.4f}, {total_local[2]:+.4f}]"
          f"  ||sum|| = {np.linalg.norm(total_local):.4f}")

# Individual rook local fibers (sample)
print(f"\n  Rook local fiber norms at individual squares:")
rook_local_norms = []
for s in range(64):
    fib = local_fiber_3d(rook_targets, s)
    rook_local_norms.append(np.linalg.norm(fib))

print(f"    Mean: {np.mean(rook_local_norms):.4f}")
print(f"    Std:  {np.std(rook_local_norms):.4f}")
print(f"    Min:  {min(rook_local_norms):.4f}  Max: {max(rook_local_norms):.4f}")
print(f"    All zero? {all(n < 1e-10 for n in rook_local_norms)}")
print(f"\n    → Individual rook local fibers are {'zero' if all(n < 1e-10 for n in rook_local_norms) else 'NONZERO'}")
print(f"      (Nonzero locals that sum to zero = cancellation artifact)")
print(f"      (Nonzero locals that don't sum to zero = the basis doesn't capture rook nullity)")


# ═══════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════

print(f"\n{'='*70}")
print(f"  SUMMARY: LOCAL FIBER ENCODER TEST BATTERY")
print(f"{'='*70}")

