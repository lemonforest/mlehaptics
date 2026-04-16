"""
Shared Subspace Mapping: Full Dimensional Analysis
====================================================
Three nested questions:
1. How many dimensions does each piece's EDGE SET span?
2. How much of that span is SHARED across piece types?
3. What degrees of freedom live in each shared dimension?

Methodology: compute per-edge fiber vectors in the full 2016-dim
space, find per-piece subspaces, then measure their overlap.
"""

import numpy as np
from scipy.linalg import eigh, svd
import warnings
warnings.filterwarnings('ignore')

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
_, EVECS = eigh(L_GRID)

upper_idx = np.triu_indices(64, k=1)  # 2016 elements


def edge_fiber_full(source, target):
    """Full 2016-dim fiber vector for a single edge."""
    A_e = np.zeros((64,64))
    A_e[source, target] = 1; A_e[target, source] = 1
    C = EVECS.T @ A_e @ EVECS
    C_off = C.copy(); np.fill_diagonal(C_off, 0)
    return C_off[upper_idx]


# ═══════════════════════════════════════════════════════════════
# STEP 1: PER-PIECE EDGE SUBSPACE DIMENSIONS
#
# For each piece type, collect ALL edge fibers (full 2016-dim).
# SVD reveals the rank = number of independent fiber directions.
# This is the "true dimensionality" of each piece's rule.
# ═══════════════════════════════════════════════════════════════

print("="*70)
print("  STEP 1: PER-PIECE EDGE FIBER SUBSPACE DIMENSIONALITY")
print("  (How many independent fiber directions per piece type?)")
print("="*70)

piece_edge_matrices = {}  # name → (n_edges × 2016) matrix
piece_edge_labels = {}    # name → list of (source, target, offset) per edge

for pname, fn in PIECE_FNS.items():
    edge_vecs = []
    edge_info = []
    
    for s in range(64):
        r, c = rc(s)
        for tr, tc in fn(r, c):
            t = sq(tr, tc)
            if t > s:  # avoid double-counting undirected edges
                ev = edge_fiber_full(s, t)
                edge_vecs.append(ev)
                edge_info.append((s, t, (tr-r, tc-c)))
    
    piece_edge_matrices[pname] = np.array(edge_vecs)
    piece_edge_labels[pname] = edge_info

print(f"\n  {'Piece':>8s} {'N edges':>8s} {'Fiber dim':>10s}", end='')
print(f" {'σ₁':>8s} {'σ₂':>8s} {'σ₃':>8s} {'σ₅':>8s} {'σ₁₀':>8s} {'90% dims':>9s} {'99% dims':>9s}")

piece_subspaces = {}  # name → (U matrix of top-k right singular vectors)

for pname in ['Knight','King','Bishop','Rook','Queen']:
    M = piece_edge_matrices[pname]
    U_e, S_e, Vt_e = svd(M, full_matrices=False)
    
    # Effective rank
    total_energy = np.sum(S_e**2)
    cumsum = np.cumsum(S_e**2)
    n_90 = np.searchsorted(cumsum, 0.9 * total_energy) + 1
    n_99 = np.searchsorted(cumsum, 0.99 * total_energy) + 1
    full_rank = np.sum(S_e > 1e-10 * S_e[0])
    
    piece_subspaces[pname] = {
        'Vt': Vt_e,
        'S': S_e,
        'rank': full_rank,
        'n_90': n_90,
        'n_99': n_99,
    }
    
    s_vals = [S_e[i] if i < len(S_e) else 0 for i in [0,1,2,4,9]]
    
    print(f"  {pname:>8s} {M.shape[0]:8d} {full_rank:10d}", end='')
    for sv in s_vals:
        print(f" {sv:8.4f}", end='')
    print(f" {n_90:9d} {n_99:9d}")


# ═══════════════════════════════════════════════════════════════
# STEP 2: CROSS-PIECE SUBSPACE OVERLAP
#
# Now we know each piece spans a certain number of dimensions.
# Do these subspaces OVERLAP? If so, what's shared?
#
# Method: compute principal angles between each pair of
# piece subspaces (using their top-k right singular vectors).
# ═══════════════════════════════════════════════════════════════

print(f"\n{'='*70}")
print(f"  STEP 2: CROSS-PIECE SUBSPACE OVERLAP")
print(f"  (Principal angles between piece-type edge fiber subspaces)")
print(f"{'='*70}")

# Use top-k dimensions for each piece (k = 99% rank)
k = 15  # enough to capture 99% for all pieces

print(f"\n  Using top-{k} singular vectors per piece.")
print(f"  Minimum principal angle (degrees) — 0° = shared direction:")
print(f"\n  {'':>8s}", end='')
for p in ['Knight','King','Bishop','Rook','Queen']:
    print(f" {p[:6]:>7s}", end='')
print()

for p1 in ['Knight','King','Bishop','Rook','Queen']:
    print(f"  {p1:>8s}", end='')
    V1 = piece_subspaces[p1]['Vt'][:k].T  # (2016 × k)
    
    for p2 in ['Knight','King','Bishop','Rook','Queen']:
        if p1 == p2:
            print(f"     ---", end='')
            continue
        
        V2 = piece_subspaces[p2]['Vt'][:k].T
        
        # Principal angles via SVD of V1^T V2
        M = V1.T @ V2
        svals = svd(M, compute_uv=False)
        svals = np.clip(svals, -1, 1)
        angles = np.arccos(svals) * 180 / np.pi
        
        min_angle = angles.min()
        print(f" {min_angle:7.1f}", end='')
    print()

# Detailed: how many dimensions are shared at < 5° angle?
print(f"\n  Number of near-shared dimensions (principal angle < 5°):")
for p1 in ['Knight','King','Bishop','Rook','Queen']:
    V1 = piece_subspaces[p1]['Vt'][:k].T
    for p2 in ['Knight','King','Bishop','Rook','Queen']:
        if p1 >= p2: continue
        V2 = piece_subspaces[p2]['Vt'][:k].T
        M = V1.T @ V2
        svals = svd(M, compute_uv=False)
        angles = np.arccos(np.clip(svals, -1, 1)) * 180 / np.pi
        n_shared = np.sum(angles < 5)
        print(f"    {p1:8s} ∩ {p2:8s}: {n_shared} dimensions within 5°")


# ═══════════════════════════════════════════════════════════════
# STEP 3: THE UNIVERSAL EDGE SUBSPACE
#
# Stack ALL edges from ALL piece types. SVD of the combined
# matrix reveals the TOTAL shared+private structure.
# ═══════════════════════════════════════════════════════════════

print(f"\n{'='*70}")
print(f"  STEP 3: UNIVERSAL EDGE FIBER SUBSPACE")
print(f"  (All piece types' edges in one SVD)")
print(f"{'='*70}")

# Stack all edge matrices
all_edges = []
all_labels = []  # (piece_type, source, target, offset)

for pname in ['Knight','King','Bishop','Rook','Queen']:
    M = piece_edge_matrices[pname]
    labels = piece_edge_labels[pname]
    for i, (s, t, offset) in enumerate(labels):
        all_edges.append(M[i])
        all_labels.append((pname, s, t, offset))

all_edge_matrix = np.array(all_edges)
print(f"\n  Total edges across all pieces: {all_edge_matrix.shape[0]}")

U_all, S_all, Vt_all = svd(all_edge_matrix, full_matrices=False)

total_energy = np.sum(S_all**2)
cumsum = np.cumsum(S_all**2)

print(f"\n  Universal singular value spectrum:")
print(f"  {'dim':>5s} {'σ':>10s} {'%energy':>8s} {'cumul':>8s}")
for i in range(min(25, len(S_all))):
    pct = S_all[i]**2 / total_energy * 100
    cum = cumsum[i] / total_energy * 100
    bar = '█' * int(pct)
    print(f"  {i+1:5d} {S_all[i]:10.4f} {pct:7.1f}% {cum:7.1f}% {bar}")

n_90_all = np.searchsorted(cumsum, 0.9 * total_energy) + 1
n_99_all = np.searchsorted(cumsum, 0.99 * total_energy) + 1
full_rank_all = np.sum(S_all > 1e-10 * S_all[0])

print(f"\n  Full rank: {full_rank_all}")
print(f"  90% energy: {n_90_all} dimensions")
print(f"  99% energy: {n_99_all} dimensions")


# ═══════════════════════════════════════════════════════════════
# STEP 4: OFFSET SEPARATION IN THE UNIVERSAL SUBSPACE
#
# Project all edges onto the top-k universal dimensions.
# Can we separate edges by OFFSET TYPE within each piece?
# This directly tests: how many universal dimensions are needed
# to distinguish (2,1) from (-1,2) for the knight, etc.
# ═══════════════════════════════════════════════════════════════

print(f"\n{'='*70}")
print(f"  STEP 4: OFFSET SEPARATION IN UNIVERSAL SUBSPACE")
print(f"  (How many dimensions needed to distinguish offset types?)")
print(f"{'='*70}")

# For the knight: project edges onto top-k universal dims,
# group by offset type, measure separability

knight_offsets_unique = [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]

for n_dims in [3, 5, 8, 12, 15, 20]:
    basis = Vt_all[:n_dims].T  # (2016 × n_dims)
    
    # Project all knight edges
    knight_idx = [i for i, (p,s,t,o) in enumerate(all_labels) if p == 'Knight']
    
    offset_clusters = {}
    for idx in knight_idx:
        pname, s, t, offset = all_labels[idx]
        proj = all_edges[idx] @ basis  # n_dims-dimensional projection
        if offset not in offset_clusters:
            offset_clusters[offset] = []
        offset_clusters[offset].append(proj)
    
    # Compute pairwise offset separability
    # Use centroid distance / average within-cluster spread
    centroids = {o: np.mean(vecs, axis=0) for o, vecs in offset_clusters.items()}
    
    # Average inter-offset centroid distance
    offsets_list = list(centroids.keys())
    inter_dists = []
    for i in range(len(offsets_list)):
        for j in range(i+1, len(offsets_list)):
            d = np.linalg.norm(centroids[offsets_list[i]] - centroids[offsets_list[j]])
            inter_dists.append(d)
    mean_inter = np.mean(inter_dists)
    
    # Average intra-offset spread
    intra_spreads = []
    for o, vecs in offset_clusters.items():
        arr = np.array(vecs)
        centroid = centroids[o]
        spread = np.mean(np.linalg.norm(arr - centroid, axis=1))
        intra_spreads.append(spread)
    mean_intra = np.mean(intra_spreads)
    
    # Separation ratio (like Fisher, but multiclass)
    sep_ratio = mean_inter / (mean_intra + 1e-15)
    
    # Also: can we classify offsets? Check if nearest-centroid works
    correct = 0
    total = 0
    for idx in knight_idx:
        pname, s, t, offset = all_labels[idx]
        proj = all_edges[idx] @ basis
        
        # Nearest centroid
        best_offset = min(centroids.keys(), key=lambda o: np.linalg.norm(proj - centroids[o]))
        if best_offset == offset:
            correct += 1
        total += 1
    
    accuracy = correct / total * 100
    
    print(f"  {n_dims:2d}D: sep_ratio={sep_ratio:.3f}, nearest-centroid accuracy={accuracy:.1f}%")

# Detailed centroid analysis at the best dimension
print(f"\n  Knight offset centroid distances at 15D:")
basis_15 = Vt_all[:15].T

knight_centroids_15 = {}
for idx in [i for i,(p,s,t,o) in enumerate(all_labels) if p=='Knight']:
    pname, s, t, offset = all_labels[idx]
    proj = all_edges[idx] @ basis_15
    if offset not in knight_centroids_15:
        knight_centroids_15[offset] = []
    knight_centroids_15[offset].append(proj)

knight_centroids_15 = {o: np.mean(v, axis=0) for o, v in knight_centroids_15.items()}

print(f"\n  {'':>10s}", end='')
for o in knight_offsets_unique[:4]:
    print(f" ({o[0]:+d},{o[1]:+d})", end='')
print()
for o1 in knight_offsets_unique[:4]:
    print(f"  ({o1[0]:+d},{o1[1]:+d})  ", end='')
    for o2 in knight_offsets_unique[:4]:
        d = np.linalg.norm(knight_centroids_15[o1] - knight_centroids_15[o2])
        print(f" {d:7.4f}", end='')
    print()

# D4 symmetry check: which offsets are equivalent under rotation/reflection?
print(f"\n  D4 symmetry grouping of knight offsets:")
print(f"  Under D4, (2,1) and (1,2) are in the same orbit.")
print(f"  There should be 1 orbit: all 8 offsets are D4-equivalent.")
print(f"  Are the centroids consistent with this symmetry?")

# All knight offsets are one D4 orbit of (2,1)
# Under D4: (2,1)→(1,-2)→(-2,-1)→(-1,2) (90° rotations)
# and reflections: (2,1)→(1,2)→(-2,1)→(-1,-2)
# So all 8 are in one orbit — centroid distances within orbit should be similar

orbit_dists = []
for o1 in knight_offsets_unique:
    for o2 in knight_offsets_unique:
        if o1 >= o2: continue
        d = np.linalg.norm(knight_centroids_15[o1] - knight_centroids_15[o2])
        orbit_dists.append(d)

print(f"  Pairwise centroid distances within D4 orbit:")
print(f"    Mean: {np.mean(orbit_dists):.4f}")
print(f"    Std:  {np.std(orbit_dists):.4f}")
print(f"    Min:  {min(orbit_dists):.4f}")
print(f"    Max:  {max(orbit_dists):.4f}")
print(f"    CV:   {np.std(orbit_dists)/np.mean(orbit_dists):.4f}")


# ═══════════════════════════════════════════════════════════════
# STEP 5: WHAT EACH DIMENSION ENCODES
#
# For each of the top universal dimensions, project all edges
# onto that single dimension and ask: what degree of freedom
# does this dimension separate?
#
# Candidates: piece type, source square, target square, offset,
# offset magnitude, offset angle, source rank, source file,
# color (light/dark)...
# ═══════════════════════════════════════════════════════════════

print(f"\n{'='*70}")
print(f"  STEP 5: WHAT DOES EACH UNIVERSAL DIMENSION ENCODE?")
print(f"  (Correlation with known edge properties)")
print(f"{'='*70}")

# For each edge, compute features
edge_features = {
    'piece_type': [],     # categorical: 0-4
    'source_rank': [],    # 0-7
    'source_file': [],    # 0-7
    'target_rank': [],
    'target_file': [],
    'offset_dr': [],
    'offset_dc': [],
    'offset_magnitude': [],  # sqrt(dr²+dc²)
    'src_centrality': [],    # distance from center
    'tgt_centrality': [],
    'color_change': [],   # 0 = same color, 1 = different
}

piece_type_map = {'Knight':0,'King':1,'Bishop':2,'Rook':3,'Queen':4}

for pname, s, t, (dr, dc) in all_labels:
    rs, cs = rc(s)
    rt, ct = rc(t)
    
    edge_features['piece_type'].append(piece_type_map[pname])
    edge_features['source_rank'].append(rs)
    edge_features['source_file'].append(cs)
    edge_features['target_rank'].append(rt)
    edge_features['target_file'].append(ct)
    edge_features['offset_dr'].append(dr)
    edge_features['offset_dc'].append(dc)
    edge_features['offset_magnitude'].append(np.sqrt(dr**2 + dc**2))
    edge_features['src_centrality'].append(max(abs(rs-3.5), abs(cs-3.5)))
    edge_features['tgt_centrality'].append(max(abs(rt-3.5), abs(ct-3.5)))
    edge_features['color_change'].append((rs+cs+rt+ct) % 2)

# Project all edges onto each universal dimension
projections = all_edge_matrix @ Vt_all[:20].T  # (n_edges × 20)

print(f"\n  Correlation of each universal dimension with edge properties:")
print(f"  (|r| > 0.3 = meaningful correlation)")
print(f"\n  {'Feature':>18s}", end='')
for d in range(10):
    print(f"  dim{d+1:2d}", end='')
print()

for feat_name, feat_vals in edge_features.items():
    fv = np.array(feat_vals, dtype=float)
    print(f"  {feat_name:>18s}", end='')
    for d in range(10):
        proj_d = projections[:, d]
        corr = np.corrcoef(fv, proj_d)[0,1]
        marker = '*' if abs(corr) > 0.3 else ' '
        print(f" {corr:+.3f}{marker}", end='')
    print()

# ═══════════════════════════════════════════════════════════════
# STEP 6: THE BACK-CALCULATION TEST
#
# Steven's question: do we need to back-calculate from edges
# to discover what each dimension carries, or is the structure
# discoverable top-down?
#
# Test: take the universal basis, project a SINGLE piece type's
# edges onto it, and see if the projection retains offset info.
# If yes → the universal basis carries per-offset structure
# that was invisible in the 3D projection.
# If no → offset info is piece-private and requires per-piece basis.
# ═══════════════════════════════════════════════════════════════

print(f"\n{'='*70}")
print(f"  STEP 6: UNIVERSAL vs PIECE-PRIVATE OFFSET STRUCTURE")
print(f"  (Is offset info in the shared basis or only in private dims?)")
print(f"{'='*70}")

for pname in ['Knight', 'King', 'Bishop']:
    edges = piece_edge_matrices[pname]
    labels = piece_edge_labels[pname]
    
    # Collect unique offsets
    offsets = list(set(o for s,t,o in labels))
    if len(offsets) > 12:
        offsets = offsets[:12]  # cap for readability
    
    for n_dims, basis_name, basis_matrix in [
        (10, "Universal-10", Vt_all[:10].T),
        (10, "Private-10", piece_subspaces[pname]['Vt'][:10].T),
    ]:
        # Project and classify
        correct = 0; total = 0
        
        # Build centroids per offset
        offset_groups = {}
        for i, (s,t,o) in enumerate(labels):
            proj = edges[i] @ basis_matrix
            if o not in offset_groups: offset_groups[o] = []
            offset_groups[o].append(proj)
        
        centroids = {o: np.mean(v, axis=0) for o, v in offset_groups.items()}
        
        for i, (s,t,o) in enumerate(labels):
            proj = edges[i] @ basis_matrix
            best = min(centroids.keys(), key=lambda x: np.linalg.norm(proj - centroids[x]))
            if best == o: correct += 1
            total += 1
        
        acc = correct / total * 100
        print(f"  {pname:8s} {basis_name:15s}: offset classification = {acc:.1f}% "
              f"({len(set(o for s,t,o in labels))} offset types)")


# ═══════════════════════════════════════════════════════════════
# SYNTHESIS
# ═══════════════════════════════════════════════════════════════

print(f"\n{'='*70}")
print(f"  SYNTHESIS: THE DIMENSIONAL STRUCTURE OF CHESS RULES")
print(f"{'='*70}")

