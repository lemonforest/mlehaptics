"""
D4 Equivariant Encoding: Direct Projection Approach
=====================================================
Instead of decomposing eigenvectors into irreps (requires
degenerate subspace alignment), directly project the board
SIGNAL onto each irrep using character-weighted averaging.

For irrep μ with character χ_μ:
  f_μ = (d_μ / |G|) Σ_{g∈D4} χ_μ(g)* · P_g f

where d_μ is the irrep dimension and P_g is the permutation.

This bypasses the eigenvector alignment problem entirely
because it operates on the SIGNAL, not the eigenvectors.
(Serre 1977, §2.6: character projection formula)
"""

import numpy as np
from scipy.linalg import eigh
import warnings
warnings.filterwarnings('ignore')

def sq(r,c): return r*8+c
def rc(s): return s//8, s%8
def sqname(s): return 'abcdefgh'[s%8] + str(8 - s//8)

VALS = {'P':1,'N':3,'B':3.5,'R':5,'Q':9,'K':100,
        'p':-1,'n':-3,'b':-3.5,'r':-5,'q':-9,'k':-100}

# D4 permutations
def make_perm(g):
    p = np.zeros(64, dtype=int)
    for r in range(8):
        for c in range(8):
            if g==0: nr,nc=r,c
            elif g==1: nr,nc=c,7-r
            elif g==2: nr,nc=7-r,7-c
            elif g==3: nr,nc=7-c,r
            elif g==4: nr,nc=r,7-c
            elif g==5: nr,nc=7-r,c
            elif g==6: nr,nc=c,r
            elif g==7: nr,nc=7-c,7-r
            p[sq(r,c)] = sq(nr,nc)
    return p

D4_PERMS = [make_perm(g) for g in range(8)]

# Character table
#
# Element ordering (matches D4_PERMS above):
#   g=0 identity, g=1 C4 (90 CCW), g=2 C2 (180), g=3 C4^-1 (90 CW),
#   g=4 sigma_v (reflect across vertical axis, col-flip),
#   g=5 sigma_h (reflect across horizontal axis, row-flip),
#   g=6 sigma_d (reflect across main diagonal),
#   g=7 sigma_d' (reflect across anti-diagonal).
#
# Conjugacy classes under this ordering (verified by direct
# conjugation, see PATCH 6 audit note in §9a of the notebook):
#   {0}, {1, 3}, {2}, {4, 5}, {6, 7}
# Each row below must be constant on each class.
#
# CORRECTED 2026-04-23 (PATCH 6 audit, Othello Phase 1c).  Prior
# values had B1 = [1,-1,1,-1,1,-1,1,-1] and B2 = [1,-1,1,-1,-1,1,-1,1]
# which failed class-constancy on classes (4,5) and (6,7) and gave
# identical-looking energies for B1 and B2 at many positions
# (e.g. both = 2545.375 at the starting position, against the true
# values 0.000 and 4140.500).  See CHANGELOG.md and §9a audit note.
CHARS = {
    'A1': [1, 1, 1, 1, 1, 1, 1, 1],
    'A2': [1, 1, 1, 1,-1,-1,-1,-1],
    'B1': [1,-1, 1,-1, 1, 1,-1,-1],  # axis reflections +1, diagonal -1
    'B2': [1,-1, 1,-1,-1,-1, 1, 1],  # axis reflections -1, diagonal +1
    'E':  [2, 0,-2, 0, 0, 0, 0, 0],
}

def board_signal(pos):
    s = np.zeros(64)
    for si, p in pos.items(): s[si] = VALS[p]
    return s

def project_irrep(sig, irrep_name):
    """Project signal onto irrep μ using character formula.
    Returns the projected 64-dim signal component."""
    chars = CHARS[irrep_name]
    dim_mu = 2 if irrep_name == 'E' else 1
    projected = np.zeros(64)
    for g_idx, perm in enumerate(D4_PERMS):
        sig_g = sig[perm]  # apply g to signal
        projected += chars[g_idx] * sig_g
    return (dim_mu / 8) * projected

def encode_d4(pos):
    """D4-equivariant encoding: project onto each irrep.
    Returns dict of 64-dim vectors, one per irrep.
    A1 component is INVARIANT under all D4 operations."""
    sig = board_signal(pos)
    return {name: project_irrep(sig, name) for name in CHARS}

def encode_flat(pos):
    """Flat 512-dim: concatenate all D4-transformed signals."""
    sig = board_signal(pos)
    return np.concatenate([sig[perm] for perm in D4_PERMS])

def cosine(a, b):
    na,nb = np.linalg.norm(a), np.linalg.norm(b)
    return float(np.dot(a,b)/(na*nb)) if na>1e-15 and nb>1e-15 else 0


# ═══════════════════════════════════════════════════════════════
# TEST 1: SYMMETRY INVARIANCE
# ═══════════════════════════════════════════════════════════════

print("="*70)
print("  TEST 1: D4 SYMMETRY — DIRECT PROJECTION")
print("="*70)

pos_orig = {sq(3,4):'N', sq(7,4):'K', sq(6,3):'P'}

# Generate ALL D4 transforms of the position
d4_positions = {}
for g_idx, perm in enumerate(D4_PERMS):
    new_pos = {}
    for s, p in pos_orig.items():
        new_pos[int(perm[s])] = p
    d4_positions[f'g{g_idx}'] = new_pos

pos_diff = {sq(7,0):'N', sq(0,4):'K', sq(1,5):'P'}

print(f"\n  A₁ component (should be IDENTICAL for all D4 transforms):")
enc_orig_A1 = project_irrep(board_signal(pos_orig), 'A1')
for gname, gpos in d4_positions.items():
    enc_g_A1 = project_irrep(board_signal(gpos), 'A1')
    c = cosine(enc_orig_A1, enc_g_A1)
    diff = np.linalg.norm(enc_orig_A1 - enc_g_A1)
    print(f"    {gname}: cos = {c:+.6f}, ||diff|| = {diff:.2e}  "
          f"[{'INVARIANT ✓' if diff < 1e-10 else 'BROKEN ✗'}]")

enc_diff_A1 = project_irrep(board_signal(pos_diff), 'A1')
c_diff = cosine(enc_orig_A1, enc_diff_A1)
print(f"    diff: cos = {c_diff:+.6f}  (different position, should be low)")

print(f"\n  Full irrep decomposition — symmetry behavior:")
for irrep in ['A1','A2','B1','B2','E']:
    enc_o = project_irrep(board_signal(pos_orig), irrep)
    
    # Check against all D4 transforms
    invariant_count = 0
    equivariant_count = 0
    for gname, gpos in d4_positions.items():
        enc_g = project_irrep(board_signal(gpos), irrep)
        diff = np.linalg.norm(enc_o - enc_g)
        if diff < 1e-10:
            invariant_count += 1
        elif abs(cosine(enc_o, enc_g)) > 0.99:
            equivariant_count += 1
    
    print(f"  {irrep}: invariant under {invariant_count}/8, equivariant under {equivariant_count}/8")


# ═══════════════════════════════════════════════════════════════
# TEST 2: 320-DIM ENCODING (5 irreps × 64 dims)
#
# Each irrep projects the signal into a 64-dim subspace.
# Concatenating all 5 gives 320 dims. But A1 has special status:
# it's the D4-INVARIANT part. For evaluation, use ONLY A1.
# For full encoding, use all 5.
# ═══════════════════════════════════════════════════════════════

print(f"\n{'='*70}")
print(f"  TEST 2: INVARIANT ENCODING (A₁ only) vs FULL (320-dim)")
print(f"{'='*70}")

def encode_A1(pos):
    """64-dim D4-invariant encoding."""
    return project_irrep(board_signal(pos), 'A1')

def encode_320(pos):
    """320-dim full D4-equivariant encoding."""
    enc = encode_d4(pos)
    return np.concatenate([enc[name] for name in ['A1','A2','B1','B2','E']])

# Symmetry test
print(f"\n  Encoding similarity for D4-related positions:")
print(f"  {'':>15s} {'A₁ (64d)':>10s} {'Full (320d)':>12s} {'Raw (64d)':>10s}")

for gname, gpos in list(d4_positions.items())[:4]:
    s_a1 = cosine(encode_A1(pos_orig), encode_A1(gpos))
    s_full = cosine(encode_320(pos_orig), encode_320(gpos))
    s_raw = cosine(board_signal(pos_orig), board_signal(gpos))
    print(f"  orig vs {gname:>5s} {s_a1:+10.4f} {s_full:+12.4f} {s_raw:+10.4f}")

s_a1_d = cosine(encode_A1(pos_orig), encode_A1(pos_diff))
s_full_d = cosine(encode_320(pos_orig), encode_320(pos_diff))
s_raw_d = cosine(board_signal(pos_orig), board_signal(pos_diff))
print(f"  orig vs diff  {s_a1_d:+10.4f} {s_full_d:+12.4f} {s_raw_d:+10.4f}")


# ═══════════════════════════════════════════════════════════════
# TEST 3: POSITION EVALUATION WITH D4 INVARIANCE
# ═══════════════════════════════════════════════════════════════

print(f"\n{'='*70}")
print(f"  TEST 3: POSITION QUALITY WITH D4-INVARIANT ENCODING")
print(f"{'='*70}")

test_positions = [
    ("Knight outpost e5", {sq(3,4):'N',sq(6,3):'P',sq(6,5):'P',sq(7,4):'K'}, "Good"),
    ("Knight rim a1", {sq(7,0):'N',sq(6,3):'P',sq(6,5):'P',sq(7,4):'K'}, "Bad"),
    ("Centralized king", {sq(3,3):'K',sq(4,4):'P'}, "Good"),
    ("Back rank king", {sq(7,4):'K',sq(6,3):'P',sq(6,4):'P',sq(6,5):'P'}, "Bad"),
]

print(f"\n  {'Position':25s} {'Q':>4s} {'A₁ norm':>9s} {'Full norm':>10s}")
for desc, pos, q in test_positions:
    a1_n = np.linalg.norm(encode_A1(pos))
    full_n = np.linalg.norm(encode_320(pos))
    print(f"  {desc:25s} {q:>4s} {a1_n:9.4f} {full_n:10.4f}")

print(f"\n  Pairwise (good vs bad):")
for i in range(0, len(test_positions), 2):
    eg = encode_A1(test_positions[i][1])
    eb = encode_A1(test_positions[i+1][1])
    c = cosine(eg, eb)
    d = np.linalg.norm(eg - eb)
    print(f"  {test_positions[i][0][:18]:18s} vs {test_positions[i+1][0][:18]:18s}: "
          f"A₁ cos={c:+.4f}, diff={d:.4f}")


# ═══════════════════════════════════════════════════════════════
# TEST 4: ASSOCIATIVE MEMORY WITH D4 INVARIANCE
# ═══════════════════════════════════════════════════════════════

print(f"\n{'='*70}")
print(f"  TEST 4: ASSOCIATIVE MEMORY — D4-INVARIANT vs FULL")
print(f"{'='*70}")

library = {
    "Sicilian": {sq(4,4):'P',sq(6,3):'P',sq(7,1):'N',sq(7,5):'B',sq(7,4):'K',
                 sq(3,2):'p',sq(1,3):'p',sq(0,1):'n',sq(0,5):'b',sq(0,4):'k'},
    "French":   {sq(4,4):'P',sq(6,3):'P',sq(7,6):'N',sq(7,2):'B',sq(7,4):'K',
                 sq(3,4):'p',sq(1,3):'p',sq(0,6):'n',sq(0,2):'b',sq(0,4):'k'},
    "EG_KR":    {sq(7,4):'K',sq(7,0):'R',sq(0,4):'k'},
    "EG_KQ":    {sq(7,4):'K',sq(7,3):'Q',sq(0,4):'k'},
}

queries = {
    "Sicilian~": {sq(4,4):'P',sq(6,3):'P',sq(5,5):'N',sq(7,5):'B',sq(7,4):'K',
                  sq(3,2):'p',sq(1,3):'p',sq(2,5):'n',sq(0,5):'b',sq(0,4):'k'},
    "EG_KR~":    {sq(3,3):'K',sq(4,0):'R',sq(0,4):'k'},
    "EG_KQ~":    {sq(3,3):'K',sq(4,3):'Q',sq(0,4):'k'},
}

# Test both A1-only and full encoding
for enc_name, enc_fn in [("A₁ (64d)", encode_A1), ("Full (320d)", encode_320)]:
    lib_enc = {n: enc_fn(p) for n,p in library.items()}
    
    print(f"\n  {enc_name}:")
    print(f"  {'Query':>12s} {'Best':>10s} {'Sim':>8s} {'2nd':>10s} {'Gap':>6s}")
    
    for qname, qpos in queries.items():
        qenc = enc_fn(qpos)
        ranked = sorted(lib_enc.items(), key=lambda x: cosine(qenc, x[1]), reverse=True)
        s1 = cosine(qenc, ranked[0][1])
        s2 = cosine(qenc, ranked[1][1])
        print(f"  {qname:>12s} {ranked[0][0]:>10s} {s1:+8.4f} {ranked[1][0]:>10s} {s1-s2:6.3f}")

# THE KEY TEST: retrieve a ROTATED version of a library position
print(f"\n  Rotation-invariant retrieval test:")
print(f"  (Can we find the Sicilian even if the board is rotated?)")

sicilian_rot90 = {}
perm_90 = D4_PERMS[1]
for s, p in library["Sicilian"].items():
    sicilian_rot90[int(perm_90[s])] = p

for enc_name, enc_fn in [("A₁ (64d)", encode_A1), ("Full (320d)", encode_320), ("Raw (64d)", lambda p: board_signal(p))]:
    lib_enc = {n: enc_fn(p) for n,p in library.items()}
    qenc = enc_fn(sicilian_rot90)
    ranked = sorted(lib_enc.items(), key=lambda x: cosine(qenc, x[1]), reverse=True)
    s1 = cosine(qenc, ranked[0][1])
    
    print(f"  {enc_name:>15s}: Sicilian(rot90°) → {ranked[0][0]:>10s} (sim={s1:+.4f})")


# ═══════════════════════════════════════════════════════════════
# SYNTHESIS
# ═══════════════════════════════════════════════════════════════

print(f"\n{'='*70}")
print(f"  SYNTHESIS")
print(f"{'='*70}")

print(f"""
  The direct character-projection approach works:
  
  1. A₁ projection IS genuinely D4-invariant (||diff|| < 1e-10
     for all 8 D4 transforms). This means rotated/reflected
     positions produce IDENTICAL A₁ encodings — not similar,
     IDENTICAL.
  
  2. The full 320-dim encoding (5 irreps × 64 dims) is 
     D4-EQUIVARIANT: it transforms predictably under D4,
     preserving relative distances between positions.
  
  3. For position RETRIEVAL: A₁ alone should retrieve rotated
     versions of stored positions, because the encoding is
     invariant. The 320-dim full encoding preserves more info
     but is NOT rotation-invariant.
  
  4. The natural HDC dimension becomes:
     D = 320 = 5 × 64 = (number of D4 irreps) × (board eigenmodes)
     This is smaller than 512 but has the correct mathematical 
     structure — each block of 64 transforms as a specific irrep.
     
  5. For 512: pad 320 to 512 with the fiber channels
     D = 320 + 3×64 = 320 + 192 = 512
     where the 3 extra blocks carry the 3 fiber directions,
     each projected through the full 64-dim signal space.
     This gives D = 512 = 2⁹ with EVERY dimension physically
     meaningful: 5 symmetry channels + 3 fiber channels, each
     64-dim.
     
  BUT 5+3 = 8, and 8×64 = 512. The magic multiple IS 8,
  and it decomposes as |D4| = 5 irreps + 3 fiber dimensions.
  The group theory and the fiber bundle meet at exactly D=512.
""")

