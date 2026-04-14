"""
Spectral Fiber Encoder v3: Dual-Channel Design
================================================
Combines geometric fiber (Grok's insight: position-dependent rule structure)
with interaction fiber (many-body coupling via local field gradient).

Design rationale:
- Grok's encoder captures WHERE the piece is in rule-space (geometry)
  but misses HOW it interacts with other pieces (additive).
- Gemini's encoder captures INTERACTION but has 7-million:1 dynamic
  range from the quadratic form, degrading geometric signal.

Solution: separate channels for geometry and interaction.

Channel 1 (geometric): value × local_fiber_3d
  → Clean position-dependent rule structure (r=0.97 PST correlation)
  → Additive by construction — this is fine, geometry IS additive.

Channel 2 (interaction): local_field_gradient × local_fiber_3d
  → Many-body coupling via LINEAR field gradient, not quadratic form.
  → The gradient g_k = Σ_{j∈targets(k)} f_j is "what material does
    this piece see from here?" — directly interpretable.
  → Linear in signal f → bounded dynamic range.
  → Zero when piece is alone (no targets occupied) → clean baseline.
  → Non-additive: adding piece B changes f, which changes g_k for A.

Theoretical grounding:
  From §5c: ΔQ_G = -2v·(L_G f)_k + v²·d_k
  The coupling term -2v·(Lf)_k depends on the field gradient.
  For the local version: (A_loc · f)_k approximates the local field
  gradient — the sum of signal values at reachable squares.
  This is the spectral formalization of "piece activity" in chess.

Total encoding: 64 (GFT) + 3 (geometric) + 3 (interaction) = 70 dims.
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
FIBER_BASIS = Vt_fib[:3].T  # (2016, 3)

# ─── Pre-compute local fiber projections and adjacency rows ───
# Cache these — they're position-dependent but board-independent.
LOCAL_FIBER_3D = {}  # (piece_char, square) → 3D vector
LOCAL_ADJ_ROWS = {}  # (piece_char, square) → 64-element adjacency row

for pchar, fn in SHORT_PFNS.items():
    for s in range(64):
        r, c = rc(s)
        # Local adjacency
        A_loc = np.zeros((64,64))
        for tr,tc in fn(r,c):
            t = sq(tr,tc)
            A_loc[s,t] = 1
            A_loc[t,s] = 1
        LOCAL_ADJ_ROWS[(pchar, s)] = A_loc[s]  # which squares are reachable
        
        # Local fiber → 3D projection
        C_loc = EVECS_GRID.T @ A_loc @ EVECS_GRID
        C_off = C_loc.copy(); np.fill_diagonal(C_off, 0)
        LOCAL_FIBER_3D[(pchar, s)] = C_off[upper_idx] @ FIBER_BASIS

print(f"Pre-computed local fibers and adjacency for {len(LOCAL_FIBER_3D)} (piece, square) pairs.")


# ═══════════════════════════════════════════════════════════════
# THE ENCODER
# ═══════════════════════════════════════════════════════════════

def encode_v3(pos):
    """
    70-dimensional encoding:
      [0:64]  — GFT coefficients (board spectral signal)
      [64:67] — geometric fiber (value × local_fiber_3d)
      [67:70] — interaction fiber (local_gradient × local_fiber_3d)
    """
    # Board signal
    sig = np.zeros(64)
    for si, pchar in pos.items():
        sig[si] = VALS[pchar]
    
    gft = EVECS_GRID.T @ sig
    
    geo_fiber = np.zeros(3)
    int_fiber = np.zeros(3)
    
    for si, pchar in pos.items():
        pkey = pchar.upper()
        if pkey not in SHORT_PFNS:
            continue  # skip pawns (no fiber rule yet)
        
        fib_3d = LOCAL_FIBER_3D[(pkey, si)]
        
        # Channel 1: Geometric — value-weighted rule structure
        geo_fiber += VALS[pchar] * fib_3d
        
        # Channel 2: Interaction — field gradient through local rule
        # g_k = Σ_{j∈targets(k)} f_j = adjacency_row · signal
        # This is "what material does this piece see from here?"
        adj_row = LOCAL_ADJ_ROWS[(pkey, si)]
        gradient = float(adj_row @ sig)
        int_fiber += gradient * fib_3d
    
    return np.concatenate((gft, geo_fiber, int_fiber))


# Also keep previous encoders for comparison
def encode_grok(pos):
    sig = np.zeros(64)
    for si, pchar in pos.items(): sig[si] = VALS[pchar]
    gft = EVECS_GRID.T @ sig
    fiber = np.zeros(3)
    for si, pchar in pos.items():
        pkey = pchar.upper()
        if pkey in SHORT_PFNS:
            fiber += VALS[pchar] * LOCAL_FIBER_3D[(pkey, si)]
    return np.concatenate((gft, fiber))

def encode_gemini(pos):
    sig = np.zeros(64)
    for si, pchar in pos.items(): sig[si] = VALS[pchar]
    gft = EVECS_GRID.T @ sig
    fiber = np.zeros(3)
    for si, pchar in pos.items():
        pkey = pchar.upper()
        if pkey not in SHORT_PFNS: continue
        _, C_off = _gemini_local(SHORT_PFNS[pkey], si)
        E = float(gft.T @ C_off @ gft)
        fiber += E * (LOCAL_FIBER_3D[(pkey, si)])  # approximate
    return np.concatenate((gft, fiber))

def _gemini_local(fn, source_sq):
    r, c = rc(source_sq)
    A_loc = np.zeros((64,64))
    for tr,tc in fn(r,c):
        t = sq(tr,tc)
        A_loc[source_sq, t] = 1; A_loc[t, source_sq] = 1
    C_loc = EVECS_GRID.T @ A_loc @ EVECS_GRID
    C_off = C_loc.copy(); np.fill_diagonal(C_off, 0)
    return C_off[upper_idx], C_off


# ═══════════════════════════════════════════════════════════════
# FULL TEST BATTERY
# ═══════════════════════════════════════════════════════════════

def fisher(legal_vals, illegal_vals):
    ml, sl = np.mean(legal_vals), np.std(legal_vals)
    mi, si = np.mean(illegal_vals), np.std(illegal_vals)
    pooled = (sl**2 + si**2) / 2
    return (ml - mi)**2 / pooled if pooled > 1e-15 else 0


# ─── TEST 1: MANY-BODY INTERACTION ───

print(f"\n{'='*70}")
print(f"  TEST 1: MANY-BODY INTERACTION")
print(f"{'='*70}")

test_pairs = [
    ('N', sq(4,4), 'B', sq(2,3), "Knight+Bishop"),
    ('R', sq(7,0), 'R', sq(7,7), "Rook+Rook"),
    ('Q', sq(7,3), 'K', sq(7,4), "Queen+King"),
    ('N', sq(4,4), 'N', sq(3,2), "Knight+Knight"),
    ('N', sq(4,4), 'R', sq(7,0), "Knight+Rook"),
]

print(f"\n  {'Config':20s} {'Grok%':>7s} {'Gemini%':>9s} {'v3 geo%':>9s} {'v3 int%':>9s} {'v3 total%':>10s}")

for p1,s1,p2,s2,desc in test_pairs:
    joint = {s1:p1, s2:p2}
    
    for enc_name, enc_fn, n_fiber in [("Grok", encode_grok, 3), ("v3", encode_v3, 6)]:
        ej = enc_fn(joint)
        ea = enc_fn({s1:p1})
        eb = enc_fn({s2:p2})
        diff = ej - (ea + eb)
        pct_total = np.linalg.norm(diff) / np.linalg.norm(ej) * 100 if np.linalg.norm(ej) > 0 else 0
        
        if enc_name == "v3":
            geo_diff = np.linalg.norm(diff[64:67])
            int_diff = np.linalg.norm(diff[67:70])
            geo_pct = geo_diff / (np.linalg.norm(ej[64:67]) + 1e-15) * 100
            int_pct = int_diff / (np.linalg.norm(ej[67:70]) + 1e-15) * 100
    
    # Gemini (approximate — using similar quadratic approach)
    ej_gem = encode_gemini(joint)
    ea_gem = encode_gemini({s1:p1})
    eb_gem = encode_gemini({s2:p2})
    gem_pct = np.linalg.norm(ej_gem - (ea_gem+eb_gem)) / (np.linalg.norm(ej_gem)+1e-15) * 100
    
    # Grok
    ej_grok = encode_grok(joint)
    ea_grok = encode_grok({s1:p1})
    eb_grok = encode_grok({s2:p2})
    grok_pct = np.linalg.norm(ej_grok - (ea_grok+eb_grok)) / (np.linalg.norm(ej_grok)+1e-15) * 100
    
    # v3
    ej_v3 = encode_v3(joint)
    ea_v3 = encode_v3({s1:p1})
    eb_v3 = encode_v3({s2:p2})
    diff_v3 = ej_v3 - (ea_v3 + eb_v3)
    v3_pct = np.linalg.norm(diff_v3) / (np.linalg.norm(ej_v3)+1e-15) * 100
    geo_pct = np.linalg.norm(diff_v3[64:67]) / (np.linalg.norm(ej_v3[64:67])+1e-15) * 100
    int_pct = np.linalg.norm(diff_v3[67:70]) / (np.linalg.norm(ej_v3[67:70])+1e-15) * 100
    
    print(f"  {desc:20s} {grok_pct:6.1f}% {gem_pct:8.1f}% {geo_pct:8.1f}% {int_pct:8.1f}% {v3_pct:9.1f}%")

# Verify: geo channel is additive, interaction is not
print(f"\n  v3 design check: geo channel additive? int channel non-additive?")
ej = encode_v3({sq(4,4):'N', sq(2,3):'B'})
ea = encode_v3({sq(4,4):'N'})
eb = encode_v3({sq(2,3):'B'})
geo_add = np.allclose(ej[64:67], ea[64:67]+eb[64:67], atol=1e-10)
int_add = np.allclose(ej[67:70], ea[67:70]+eb[67:70], atol=1e-10)
print(f"    Geometric channel additive: {geo_add} (expected: True)")
print(f"    Interaction channel additive: {int_add} (expected: False)")


# ─── TEST 2: FISHER DISCRIMINANT ───

print(f"\n{'='*70}")
print(f"  TEST 2: FISHER DISCRIMINANT — LEGAL vs ILLEGAL")
print(f"{'='*70}")

piece_tests = [
    ('N', knight_targets, [(4,4),(0,0),(3,3)], "Knight"),
    ('B', bishop_targets, [(4,4),(5,2)], "Bishop"),
    ('R', rook_targets, [(4,4),(7,0)], "Rook"),
    ('K', king_targets, [(4,4),(0,0)], "King"),
]

# Solo piece
print(f"\n  Single piece on empty board:")
print(f"  {'Piece':>8s} {'Grok':>8s} {'Gemini':>8s} {'v3 geo':>8s} {'v3 int':>8s} {'v3 comb':>8s}")

for pchar, tfn, sources, pname in piece_tests:
    fishers = {k: [] for k in ['grok','gemini','v3_geo','v3_int','v3_comb']}
    
    for sr,sc in sources:
        src = sq(sr,sc)
        legal = set(sq(tr,tc) for tr,tc in tfn(sr,sc))
        
        for enc_name, enc_fn in [("grok",encode_grok),("gemini",encode_gemini),("v3",encode_v3)]:
            enc_src = enc_fn({src: pchar})
            legal_f = []; illegal_f = []
            legal_g = []; illegal_g = []
            legal_i = []; illegal_i = []
            legal_c = []; illegal_c = []
            
            for dst in range(64):
                if dst == src: continue
                enc_dst = enc_fn({dst: pchar})
                delta = enc_dst - enc_src
                
                if enc_name == "v3":
                    gn = np.linalg.norm(delta[64:67])
                    inn = np.linalg.norm(delta[67:70])
                    cn = np.linalg.norm(delta[64:70])
                    if dst in legal:
                        legal_g.append(gn); legal_i.append(inn); legal_c.append(cn)
                    else:
                        illegal_g.append(gn); illegal_i.append(inn); illegal_c.append(cn)
                else:
                    fn = np.linalg.norm(delta[64:])
                    if dst in legal:
                        legal_f.append(fn)
                    else:
                        illegal_f.append(fn)
            
            if enc_name == "grok":
                fishers['grok'].append(fisher(legal_f, illegal_f))
            elif enc_name == "gemini":
                fishers['gemini'].append(fisher(legal_f, illegal_f))
            else:
                fishers['v3_geo'].append(fisher(legal_g, illegal_g))
                fishers['v3_int'].append(fisher(legal_i, illegal_i))
                fishers['v3_comb'].append(fisher(legal_c, illegal_c))
    
    row = f"  {pname:>8s}"
    for k in ['grok','gemini','v3_geo','v3_int','v3_comb']:
        v = np.mean(fishers[k])
        row += f" {v:8.3f}"
    print(row)

# With context
print(f"\n  Knight on f3 with board context:")
contexts = [
    ("Empty", {}),
    ("3 pawns", {sq(6,3):'P',sq(6,4):'P',sq(6,5):'P'}),
    ("Middlegame", {sq(7,4):'K',sq(7,3):'Q',sq(7,0):'R',sq(4,2):'B',
                    sq(6,3):'P',sq(4,4):'P',sq(6,5):'P',
                    sq(0,4):'k',sq(0,3):'q',sq(0,0):'r',sq(0,2):'b',
                    sq(2,5):'n',sq(1,3):'p',sq(3,4):'p',sq(1,5):'p'}),
]

src = sq(5,5)
legal = set(sq(tr,tc) for tr,tc in knight_targets(5,5))

print(f"  {'Context':>12s} {'Grok':>8s} {'Gemini':>8s} {'v3 geo':>8s} {'v3 int':>8s} {'v3 comb':>8s}")

for ctx_name, ctx in contexts:
    results = {}
    for enc_name, enc_fn in [("Grok",encode_grok),("Gemini",encode_gemini),("v3",encode_v3)]:
        pos_src = dict(ctx); pos_src[src] = 'N'
        enc_src = enc_fn(pos_src)
        
        legal_f=[]; illegal_f=[]; legal_g=[]; illegal_g=[]
        legal_i=[]; illegal_i=[]; legal_c=[]; illegal_c=[]
        
        for dst in range(64):
            if dst == src or dst in ctx: continue
            pos_dst = dict(ctx); pos_dst[dst] = 'N'
            delta = enc_fn(pos_dst) - enc_src
            
            if enc_name == "v3":
                gn = np.linalg.norm(delta[64:67])
                inn = np.linalg.norm(delta[67:70])
                cn = np.linalg.norm(delta[64:70])
                (legal_g if dst in legal else illegal_g).append(gn)
                (legal_i if dst in legal else illegal_i).append(inn)
                (legal_c if dst in legal else illegal_c).append(cn)
            else:
                fn = np.linalg.norm(delta[64:])
                (legal_f if dst in legal else illegal_f).append(fn)
        
        if enc_name == "Grok":
            results['Grok'] = fisher(legal_f, illegal_f)
        elif enc_name == "Gemini":
            results['Gemini'] = fisher(legal_f, illegal_f)
        else:
            results['v3_geo'] = fisher(legal_g, illegal_g)
            results['v3_int'] = fisher(legal_i, illegal_i)
            results['v3_comb'] = fisher(legal_c, illegal_c)
    
    print(f"  {ctx_name:>12s} {results['Grok']:8.3f} {results['Gemini']:8.3f} "
          f"{results['v3_geo']:8.3f} {results['v3_int']:8.3f} {results['v3_comb']:8.3f}")


# ─── TEST 3: POSITION QUALITY ───

print(f"\n{'='*70}")
print(f"  TEST 3: POSITION QUALITY DISCRIMINATION")
print(f"{'='*70}")

test_positions = [
    ("Knight outpost e5", {sq(3,4):'N',sq(6,3):'P',sq(6,5):'P'}, "Good"),
    ("Knight rim a1", {sq(7,0):'N',sq(6,3):'P',sq(6,5):'P'}, "Bad"),
    ("Bishop pair", {sq(5,2):'B',sq(5,5):'B'}, "Good"),
    ("Bishop hemmed", {sq(7,2):'B',sq(6,1):'P',sq(6,3):'P'}, "Bad"),
    ("Central king", {sq(3,3):'K',sq(4,4):'P'}, "Good"),
    ("Back rank king", {sq(7,4):'K',sq(6,3):'P',sq(6,4):'P',sq(6,5):'P'}, "Bad"),
]

print(f"\n  {'Position':20s} {'Q':>3s} {'Geo norm':>9s} {'Int norm':>9s} {'Geo 3D':>24s} {'Int 3D':>24s}")

for desc, pieces, q in test_positions:
    enc = encode_v3(pieces)
    geo = enc[64:67]; intr = enc[67:70]
    print(f"  {desc:20s} {q:>3s} {np.linalg.norm(geo):9.4f} {np.linalg.norm(intr):9.4f} "
          f"[{geo[0]:+.3f},{geo[1]:+.3f},{geo[2]:+.3f}] "
          f"[{intr[0]:+.3f},{intr[1]:+.3f},{intr[2]:+.3f}]")

print(f"\n  Pairwise: v3 geometric vs interaction channel separation:")
for i in range(0, len(test_positions), 2):
    _, pg, _ = test_positions[i]
    _, pb, _ = test_positions[i+1]
    eg = encode_v3(pg); eb = encode_v3(pb)
    
    geo_cos = np.dot(eg[64:67],eb[64:67])/(np.linalg.norm(eg[64:67])*np.linalg.norm(eb[64:67])+1e-15)
    int_cos = np.dot(eg[67:70],eb[67:70])/(np.linalg.norm(eg[67:70])*np.linalg.norm(eb[67:70])+1e-15)
    geo_diff = np.linalg.norm(eg[64:67]-eb[64:67])
    int_diff = np.linalg.norm(eg[67:70]-eb[67:70])
    
    print(f"    {test_positions[i][0][:15]:15s} vs {test_positions[i+1][0][:15]:15s}: "
          f"geo cos={geo_cos:+.3f} diff={geo_diff:.4f}, "
          f"int cos={int_cos:+.3f} diff={int_diff:.4f}")


# ─── TEST 4: PIECE-SQUARE TABLE CORRELATION ───

print(f"\n{'='*70}")
print(f"  TEST 4: PIECE-SQUARE TABLE CORRELATION")
print(f"{'='*70}")

known_knight = np.array([
    [-50,-40,-30,-30,-30,-30,-40,-50],[-40,-20,0,0,0,0,-20,-40],
    [-30,0,10,15,15,10,0,-30],[-30,5,15,20,20,15,5,-30],
    [-30,0,15,20,20,15,0,-30],[-30,5,10,15,15,10,5,-30],
    [-40,-20,0,5,5,0,-20,-40],[-50,-40,-30,-30,-30,-30,-40,-50]], dtype=float)

known_bishop = np.array([
    [-20,-10,-10,-10,-10,-10,-10,-20],[-10,0,0,0,0,0,0,-10],
    [-10,0,5,10,10,5,0,-10],[-10,5,5,10,10,5,5,-10],
    [-10,0,10,10,10,10,0,-10],[-10,10,10,10,10,10,10,-10],
    [-10,5,0,0,0,0,5,-10],[-20,-10,-10,-10,-10,-10,-10,-20]], dtype=float)

print(f"\n  {'Piece':>6s} {'Grok':>8s} {'Gemini':>8s} {'v3 geo':>8s} {'v3 int':>8s}")

for pchar, known, pname in [('N',known_knight,'Knight'),('B',known_bishop,'Bishop')]:
    maps = {}
    for enc_name, enc_fn, sl in [("Grok",encode_grok,slice(64,67)),
                                  ("Gemini",encode_gemini,slice(64,67)),
                                  ("v3_geo",encode_v3,slice(64,67)),
                                  ("v3_int",encode_v3,slice(67,70))]:
        m = np.zeros((8,8))
        for r in range(8):
            for c in range(8):
                enc = enc_fn({sq(r,c): pchar})
                m[r,c] = np.linalg.norm(enc[sl])
        maps[enc_name] = m
    
    corrs = {k: np.corrcoef(maps[k].flatten(), known.flatten())[0,1] for k in maps}
    print(f"  {pname:>6s} {corrs['Grok']:+8.3f} {corrs['Gemini']:+8.3f} "
          f"{corrs['v3_geo']:+8.3f} {corrs['v3_int']:+8.3f}")


# ─── TEST 5: CONTEXT SENSITIVITY ───

print(f"\n{'='*70}")
print(f"  TEST 5: CONTEXT SENSITIVITY")
print(f"  (Same piece, same square, different surroundings)")
print(f"{'='*70}")

contexts = [
    ("Alone", {sq(4,4):'N'}),
    ("+Pawns", {sq(4,4):'N',sq(6,3):'P',sq(6,5):'P'}),
    ("+Queen", {sq(4,4):'N',sq(7,3):'Q'}),
    ("+Enemy", {sq(4,4):'N',sq(2,3):'b',sq(3,4):'p'}),
    ("Crowded", {sq(4,4):'N',sq(7,3):'Q',sq(7,0):'R',sq(0,3):'q',sq(0,0):'r'}),
]

print(f"\n  {'Context':10s} {'Grok fib':>9s} {'v3 geo':>9s} {'v3 int':>9s} {'v3 int 3D':>28s}")

v3_ints = []
for ctx_name, pos in contexts:
    eg = encode_grok(pos)
    ev = encode_v3(pos)
    grok_n = np.linalg.norm(eg[64:])
    geo_n = np.linalg.norm(ev[64:67])
    int_n = np.linalg.norm(ev[67:70])
    int_v = ev[67:70]
    v3_ints.append(int_v)
    
    print(f"  {ctx_name:10s} {grok_n:9.4f} {geo_n:9.4f} {int_n:9.4f} "
          f"[{int_v[0]:+.4f},{int_v[1]:+.4f},{int_v[2]:+.4f}]")

# Check uniqueness and dynamic range
grok_range = max(np.linalg.norm(encode_grok(c[1])[64:]) for c in contexts) / \
             (min(np.linalg.norm(encode_grok(c[1])[64:]) for c in contexts) + 1e-15)

v3_int_norms = [np.linalg.norm(v) for v in v3_ints]
v3_nonzero = [n for n in v3_int_norms if n > 1e-10]
v3_range = max(v3_nonzero) / min(v3_nonzero) if len(v3_nonzero) > 1 else float('inf')

print(f"\n  Dynamic range (max/min fiber norm across contexts):")
print(f"    Grok:     {grok_range:.1f}x")
print(f"    v3 int:   {v3_range:.1f}x")

# Gemini for comparison
gem_norms = [np.linalg.norm(encode_gemini(c[1])[64:]) for c in contexts]
gem_nonzero = [n for n in gem_norms if n > 1e-10]
gem_range = max(gem_nonzero) / min(gem_nonzero) if len(gem_nonzero) > 1 else float('inf')
print(f"    Gemini:   {gem_range:.1f}x")

# Interaction channel should be zero when alone, nonzero with context
alone_int = np.linalg.norm(encode_v3({sq(4,4):'N'})[67:70])
crowd_int = np.linalg.norm(encode_v3(contexts[-1][1])[67:70])
print(f"\n  Interaction channel sanity:")
print(f"    Alone: {alone_int:.6f} (should be ~0: no targets occupied)")
print(f"    Crowded: {crowd_int:.4f} (should be >> 0: many targets occupied)")


# ─── TEST 6: DYNAMIC RANGE ───

print(f"\n{'='*70}")
print(f"  TEST 6: DYNAMIC RANGE COMPARISON")
print(f"{'='*70}")

# Encode the full middlegame position
full_pos = {
    sq(7,4):'K',sq(7,3):'Q',sq(7,0):'R',sq(4,2):'B',
    sq(5,5):'N',sq(6,3):'P',sq(4,4):'P',sq(6,5):'P',
    sq(0,4):'k',sq(0,3):'q',sq(0,0):'r',sq(0,2):'b',
    sq(2,5):'n',sq(1,3):'p',sq(3,4):'p',sq(1,5):'p',
}

for enc_name, enc_fn in [("Grok",encode_grok),("Gemini",encode_gemini),("v3",encode_v3)]:
    enc = enc_fn(full_pos)
    gft_n = np.linalg.norm(enc[:64])
    fib_n = np.linalg.norm(enc[64:])
    ratio = fib_n / gft_n
    
    extra = ""
    if enc_name == "v3":
        geo_n = np.linalg.norm(enc[64:67])
        int_n = np.linalg.norm(enc[67:70])
        extra = f"  (geo={geo_n:.2f}, int={int_n:.2f})"
    
    print(f"  {enc_name:6s}: GFT={gft_n:.2f}, fiber={fib_n:.2f}, ratio={ratio:.4f}{extra}")


# ═══════════════════════════════════════════════════════════════
# PROGRESS REPORT
# ═══════════════════════════════════════════════════════════════

print(f"\n{'='*70}")
print(f"  PROGRESS REPORT")
print(f"{'='*70}")

