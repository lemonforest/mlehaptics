"""
Gemini's Many-Body Fiber Encoder: Full Test Battery
=====================================================
Testing the quadratic-form-weighted local fiber encoding.
"""

import numpy as np
from scipy.linalg import eigh, svd
from scipy.fft import dctn
import warnings
warnings.filterwarnings('ignore')

# ─── Standard preamble ───
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
    for dr,dc in [(-1,0),(1,0),(0,-1),(0,4)]:
        nr,nc = r+dr,c+dc
        while 0<=nr<8 and 0<=nc<8: yield nr,nc; nr+=dr; nc+=dc
# FIX: rook had a typo (0,4) — correcting to (0,1)
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

A_GRID = np.zeros((64,64))
for _r in range(8):
    for _c in range(8):
        for _dr,_dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            _nr,_nc = _r+_dr, _c+_dc
            if 0<=_nr<8 and 0<=_nc<8: A_GRID[sq(_r,_c),sq(_nr,_nc)] = 1
L_GRID = graph_laplacian(A_GRID)
EVALS_GRID, EVECS_GRID = eigh(L_GRID)

# ─── Shared fiber basis (§7) ───
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

# ─── Gemini's encoder ───

def local_fiber_matrix(fn, source_sq, U=EVECS_GRID):
    r, c = rc(source_sq)
    A_loc = np.zeros((64,64))
    for tr,tc in fn(r,c):
        t = sq(tr,tc)
        A_loc[source_sq, t] = 1
        A_loc[t, source_sq] = 1
    C_loc = U.T @ A_loc @ U
    C_off = C_loc.copy(); np.fill_diagonal(C_off, 0)
    return C_off[upper_idx], C_off

def encode_position_gemini(pos):
    """Gemini's many-body encoder: fiber weighted by field interaction energy."""
    sig = np.zeros(64)
    for si, pchar in pos.items():
        sig[si] = VALS[pchar]
    gft = EVECS_GRID.T @ sig
    
    total_fiber_3d = np.zeros(3)
    for si, pchar in pos.items():
        pkey = pchar.upper()
        if pkey in SHORT_PFNS and pkey != 'P':
            fn = SHORT_PFNS[pkey]
            loc_vec, C_off_matrix = local_fiber_matrix(fn, si)
            
            # The quadratic form: field energy flowing through local rule geometry
            interaction_energy = float(gft.T @ C_off_matrix @ gft)
            
            # Project geometry into 3D, scale by interaction energy
            proj = loc_vec @ fiber_basis
            total_fiber_3d += interaction_energy * proj
    
    return np.concatenate((gft, total_fiber_3d))

# Also keep Grok's encoder for comparison
def local_fiber_3d_grok(fn, source_sq):
    loc_vec, _ = local_fiber_matrix(fn, source_sq)
    return loc_vec @ fiber_basis

def encode_position_grok(pos):
    """Grok's encoder: fiber weighted by piece value (additive)."""
    sig = np.zeros(64)
    for si, pchar in pos.items():
        sig[si] = VALS[pchar]
    gft = EVECS_GRID.T @ sig
    
    fiber_3d = np.zeros(3)
    for si, pchar in pos.items():
        pkey = pchar.upper()
        if pkey in SHORT_PFNS and pkey != 'P':
            fiber_3d += VALS[pchar] * local_fiber_3d_grok(SHORT_PFNS[pkey], si)
    
    return np.concatenate((gft, fiber_3d))


# ═══════════════════════════════════════════════════════════════
# TEST 1: MANY-BODY INTERACTION (the test Grok's encoder failed)
# ═══════════════════════════════════════════════════════════════

print("="*70)
print("  TEST 1: MANY-BODY INTERACTION")
print("  (Does enc(A+B) ≠ enc(A) + enc(B)? Grok's version was additive.)")
print("="*70)

test_pairs = [
    ('N', sq(4,4), 'B', sq(2,3), "Knight e4 + Bishop d6"),
    ('R', sq(7,0), 'R', sq(7,7), "Rook a1 + Rook h1"),
    ('Q', sq(7,3), 'K', sq(7,4), "Queen d1 + King e1"),
    ('N', sq(4,4), 'N', sq(3,2), "Knight e4 + Knight c5"),
    ('N', sq(4,4), 'R', sq(7,0), "Knight e4 + Rook a1"),
]

print(f"\n  {'Configuration':30s} {'||enc_joint||':>12s} {'||enc_sum||':>12s} {'||diff||':>10s} {'%non-add':>10s}")

for p1, s1, p2, s2, desc in test_pairs:
    enc_joint = encode_position_gemini({s1: p1, s2: p2})
    enc_a = encode_position_gemini({s1: p1})
    enc_b = encode_position_gemini({s2: p2})
    enc_sum = enc_a + enc_b
    
    diff = enc_joint - enc_sum
    diff_norm = np.linalg.norm(diff)
    joint_norm = np.linalg.norm(enc_joint)
    pct = diff_norm / joint_norm * 100 if joint_norm > 0 else 0
    
    # GFT part vs fiber part
    gft_diff = np.linalg.norm(diff[:64])
    fiber_diff = np.linalg.norm(diff[64:])
    
    print(f"  {desc:30s} {joint_norm:12.2f} {np.linalg.norm(enc_sum):12.2f} {diff_norm:10.4f} {pct:9.1f}%")
    print(f"  {'':30s} GFT diff: {gft_diff:.4f}, Fiber diff: {fiber_diff:.4f}")

print(f"\n  Comparison with Grok's additive encoder:")
for p1, s1, p2, s2, desc in test_pairs[:3]:
    enc_g_joint = encode_position_grok({s1: p1, s2: p2})
    enc_g_sum = encode_position_grok({s1: p1}) + encode_position_grok({s2: p2})
    grok_diff = np.linalg.norm(enc_g_joint - enc_g_sum)
    
    enc_m_joint = encode_position_gemini({s1: p1, s2: p2})
    enc_m_sum = encode_position_gemini({s1: p1}) + encode_position_gemini({s2: p2})
    gemini_diff = np.linalg.norm(enc_m_joint - enc_m_sum)
    
    print(f"    {desc:30s}: Grok ||diff||={grok_diff:.6f}, Gemini ||diff||={gemini_diff:.4f}")


# ═══════════════════════════════════════════════════════════════
# TEST 2: FISHER DISCRIMINANT — LEGAL vs ILLEGAL
# ═══════════════════════════════════════════════════════════════

print(f"\n{'='*70}")
print(f"  TEST 2: FISHER DISCRIMINANT — LEGAL vs ILLEGAL MOVES")
print(f"{'='*70}")

# For a single piece on empty board, the Gemini encoder's interaction_energy
# is gft^T C_off gft where gft comes from one piece only.
# Compare to Grok's version on the same test.

test_configs = [
    ('N', knight_targets, [(4,4), (0,0), (3,3)]),
    ('B', bishop_targets, [(4,4), (5,2)]),
    ('R', rook_targets, [(4,4), (7,0)]),
    ('K', king_targets, [(4,4), (0,0)]),
]

for piece_char, target_fn, sources in test_configs:
    pname = {'N':'Knight','B':'Bishop','R':'Rook','K':'King'}[piece_char]
    
    fisher_grok = []
    fisher_gemini = []
    
    for sr, sc in sources:
        src = sq(sr,sc)
        legal = set(sq(tr,tc) for tr,tc in target_fn(sr,sc))
        
        for encoder_name, encoder_fn in [("Grok", encode_position_grok), ("Gemini", encode_position_gemini)]:
            enc_before = encoder_fn({src: piece_char})
            
            legal_fiber_norms = []
            illegal_fiber_norms = []
            
            for dst in range(64):
                if dst == src: continue
                enc_after = encoder_fn({dst: piece_char})
                delta = enc_after - enc_before
                fn_norm = np.linalg.norm(delta[64:])
                
                if dst in legal:
                    legal_fiber_norms.append(fn_norm)
                else:
                    illegal_fiber_norms.append(fn_norm)
            
            ml, sl = np.mean(legal_fiber_norms), np.std(legal_fiber_norms)
            mi, si = np.mean(illegal_fiber_norms), np.std(illegal_fiber_norms)
            pooled = (sl**2 + si**2) / 2
            f_score = (ml - mi)**2 / pooled if pooled > 1e-15 else 0
            
            if encoder_name == "Grok":
                fisher_grok.append(f_score)
            else:
                fisher_gemini.append(f_score)
    
    print(f"\n  {pname}:")
    print(f"    Grok fiber Fisher:   {np.mean(fisher_grok):8.4f}  → {'YES' if np.mean(fisher_grok) > 1 else 'weak' if np.mean(fisher_grok) > 0.1 else 'NO'}")
    print(f"    Gemini fiber Fisher: {np.mean(fisher_gemini):8.4f}  → {'YES' if np.mean(fisher_gemini) > 1 else 'weak' if np.mean(fisher_gemini) > 0.1 else 'NO'}")


# ═══════════════════════════════════════════════════════════════
# TEST 3: FISHER WITH MULTI-PIECE CONTEXT
#
# The Gemini encoder's advantage should show up when OTHER
# pieces are on the board (because interaction_energy depends
# on the global field). Test: knight on e4 with 3 supporting 
# pawns, vs same knight without pawns.
# ═══════════════════════════════════════════════════════════════

print(f"\n{'='*70}")
print(f"  TEST 3: FISHER WITH BOARD CONTEXT")
print(f"  (Does adding pieces improve legal/illegal separation?)")
print(f"{'='*70}")

contexts = [
    ("Empty board", {}),
    ("3 pawns", {sq(6,3): 'P', sq(6,4): 'P', sq(6,5): 'P'}),
    ("Full middlegame", {
        sq(7,4): 'K', sq(7,3): 'Q', sq(7,0): 'R', sq(4,2): 'B',
        sq(6,3): 'P', sq(4,4): 'P', sq(6,5): 'P',
        sq(0,4): 'k', sq(0,3): 'q', sq(0,0): 'r', sq(0,2): 'b',
        sq(2,5): 'n', sq(1,3): 'p', sq(3,4): 'p', sq(1,5): 'p',
    }),
]

src = sq(5, 5)  # f3
legal = set(sq(tr,tc) for tr,tc in knight_targets(5, 5))

for ctx_name, ctx_pieces in contexts:
    for enc_name, enc_fn in [("Grok", encode_position_grok), ("Gemini", encode_position_gemini)]:
        pos_base = dict(ctx_pieces)
        pos_base[src] = 'N'
        
        enc_before = enc_fn(pos_base)
        
        legal_fn = []
        illegal_fn = []
        
        for dst in range(64):
            if dst == src or dst in ctx_pieces: continue
            pos_after = dict(ctx_pieces)
            pos_after[dst] = 'N'
            enc_after = enc_fn(pos_after)
            delta = enc_after - enc_before
            fn = np.linalg.norm(delta[64:])
            
            if dst in legal:
                legal_fn.append(fn)
            else:
                illegal_fn.append(fn)
        
        ml, sl = np.mean(legal_fn), np.std(legal_fn)
        mi, si = np.mean(illegal_fn), np.std(illegal_fn)
        pooled = (sl**2 + si**2) / 2
        f_score = (ml - mi)**2 / pooled if pooled > 1e-15 else 0
        
        sep = "YES" if f_score > 1 else "weak" if f_score > 0.1 else "NO"
        print(f"  {enc_name:6s} + {ctx_name:20s}: Fisher={f_score:8.4f} ({sep})")


# ═══════════════════════════════════════════════════════════════
# TEST 4: POSITION QUALITY
# ═══════════════════════════════════════════════════════════════

print(f"\n{'='*70}")
print(f"  TEST 4: POSITION QUALITY DISCRIMINATION")
print(f"{'='*70}")

test_positions = [
    ("Knight outpost e5", {sq(3,4): 'N', sq(6,3): 'P', sq(6,5): 'P'}, "Good"),
    ("Knight rim a1", {sq(7,0): 'N', sq(6,3): 'P', sq(6,5): 'P'}, "Bad"),
    ("Bishop pair active", {sq(5,2): 'B', sq(5,5): 'B'}, "Good"),
    ("Bishop hemmed", {sq(7,2): 'B', sq(6,1): 'P', sq(6,3): 'P'}, "Bad"),
    ("Central king (EG)", {sq(3,3): 'K', sq(4,4): 'P'}, "Good"),
    ("Back rank king", {sq(7,4): 'K', sq(6,3): 'P', sq(6,4): 'P', sq(6,5): 'P'}, "Bad"),
]

print(f"\n  {'Position':25s} {'Q':>3s} {'GFT':>8s} {'Fiber(Grok)':>12s} {'Fiber(Gemini)':>14s}")

for desc, pieces, q in test_positions:
    eg = encode_position_grok(pieces)
    em = encode_position_gemini(pieces)
    print(f"  {desc:25s} {q:>3s} {np.linalg.norm(eg[:64]):8.2f} {np.linalg.norm(eg[64:]):12.4f} {np.linalg.norm(em[64:]):14.4f}")

print(f"\n  Pairwise comparison (same piece, good vs bad):")
for i in range(0, len(test_positions), 2):
    _, pos_g, _ = test_positions[i]
    _, pos_b, _ = test_positions[i+1]
    
    for enc_name, enc_fn in [("Grok", encode_position_grok), ("Gemini", encode_position_gemini)]:
        eg = enc_fn(pos_g)
        eb = enc_fn(pos_b)
        fiber_diff = np.linalg.norm(eg[64:] - eb[64:])
        cos_f = np.dot(eg[64:], eb[64:]) / (np.linalg.norm(eg[64:])*np.linalg.norm(eb[64:])+1e-15)
        same = np.allclose(eg[64:], eb[64:], atol=1e-10)
        print(f"    {enc_name:6s} {test_positions[i][0][:15]:15s} vs {test_positions[i+1][0][:15]:15s}: "
              f"cos={cos_f:+.4f}, diff={fiber_diff:.4f}, identical={same}")


# ═══════════════════════════════════════════════════════════════
# TEST 5: PIECE-SQUARE TABLE CORRELATION
# ═══════════════════════════════════════════════════════════════

print(f"\n{'='*70}")
print(f"  TEST 5: PIECE-SQUARE TABLE CORRELATION")
print(f"{'='*70}")

known_knight = np.array([
    [-50,-40,-30,-30,-30,-30,-40,-50],
    [-40,-20,  0,  0,  0,  0,-20,-40],
    [-30,  0, 10, 15, 15, 10,  0,-30],
    [-30,  5, 15, 20, 20, 15,  5,-30],
    [-30,  0, 15, 20, 20, 15,  0,-30],
    [-30,  5, 10, 15, 15, 10,  5,-30],
    [-40,-20,  0,  5,  5,  0,-20,-40],
    [-50,-40,-30,-30,-30,-30,-40,-50],
], dtype=float)

for enc_name, enc_fn in [("Grok", encode_position_grok), ("Gemini", encode_position_gemini)]:
    fiber_map = np.zeros((8,8))
    for r in range(8):
        for c in range(8):
            enc = enc_fn({sq(r,c): 'N'})
            fiber_map[r,c] = np.linalg.norm(enc[64:])
    
    corr = np.corrcoef(fiber_map.flatten(), known_knight.flatten())[0,1]
    print(f"  {enc_name:6s} knight fiber ↔ PST: r = {corr:+.4f}")
    
    if enc_name == "Gemini":
        fn = fiber_map / fiber_map.max() if fiber_map.max() > 0 else fiber_map
        print(f"         Gemini fiber activity map:")
        for r in range(8):
            print(f"           {8-r} ", end='')
            for c in range(8):
                print(f" {int(fn[r,c]*9)}", end='')
            print()
        print(f"             a b c d e f g h")


# ═══════════════════════════════════════════════════════════════
# TEST 6: SENSITIVITY TO BOARD CONTEXT
#
# The whole point of the quadratic form weighting: the SAME
# piece on the SAME square should encode DIFFERENTLY depending
# on what other pieces are around it.
# ═══════════════════════════════════════════════════════════════

print(f"\n{'='*70}")
print(f"  TEST 6: CONTEXT SENSITIVITY")
print(f"  (Same piece, same square, different board — should differ)")
print(f"{'='*70}")

# Knight on e4 with different surrounding material
contexts = [
    ("Alone", {sq(4,4): 'N'}),
    ("+Pawns", {sq(4,4): 'N', sq(6,3): 'P', sq(6,5): 'P'}),
    ("+Queen", {sq(4,4): 'N', sq(7,3): 'Q'}),
    ("+Enemy", {sq(4,4): 'N', sq(2,3): 'b', sq(3,4): 'p'}),
    ("Crowded", {sq(4,4): 'N', sq(7,3): 'Q', sq(7,0): 'R', sq(0,3): 'q', sq(0,0): 'r'}),
]

print(f"\n  Knight on e4 in different contexts:")
print(f"  {'Context':12s} {'Fiber(Grok)':>12s} {'Fiber(Gemini)':>14s} {'Gemini 3D':>30s}")

grok_fibers = []
gemini_fibers = []

for ctx_name, pos in contexts:
    eg = encode_position_grok(pos)
    em = encode_position_gemini(pos)
    gf = eg[64:]
    mf = em[64:]
    grok_fibers.append(gf)
    gemini_fibers.append(mf)
    
    print(f"  {ctx_name:12s} {np.linalg.norm(gf):12.4f} {np.linalg.norm(mf):14.4f} "
          f"[{mf[0]:+.2f},{mf[1]:+.2f},{mf[2]:+.2f}]")

# Check: are the Grok encodings context-dependent?
grok_unique = len(set(tuple(np.round(f, 8)) for f in grok_fibers))
gemini_unique = len(set(tuple(np.round(f, 4)) for f in gemini_fibers))

print(f"\n  Grok unique fiber vectors:  {grok_unique}/{len(contexts)}")
print(f"  Gemini unique fiber vectors: {gemini_unique}/{len(contexts)}")

# Pairwise distances
print(f"\n  Pairwise fiber distances (Gemini):")
for i in range(len(contexts)):
    for j in range(i+1, len(contexts)):
        d = np.linalg.norm(gemini_fibers[i] - gemini_fibers[j])
        print(f"    {contexts[i][0]:10s} vs {contexts[j][0]:10s}: {d:.4f}")


# ═══════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════

print(f"\n{'='*70}")
print(f"  PROGRESS REPORT: THREE ENCODERS COMPARED")
print(f"{'='*70}")

print(f"""
  Test                    Global(§8)  Grok(local)  Gemini(many-body)
  ─────────────────────   ──────────  ───────────  ─────────────────
  Many-body interaction   N/A         FAIL(add.)   ???
  Fisher (knight)         0.000       0.612        ???
  Position quality        FAIL        FIXED        ???
  PST correlation (N)     NaN         +0.971       ???
  Context sensitivity     FAIL        partial      ???
  
  (??? = results from this run — see above)
""")

