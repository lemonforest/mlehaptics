#!/usr/bin/env python3
"""
chess_spectral_consolidated.py
==============================
Consolidated code reproducing all claims in the research notebook:
"Chess as a Spectral Lattice Fermion System"

Run: python3 chess_spectral_consolidated.py
Requirements: numpy >= 1.24, scipy >= 1.10
Time: ~45 seconds on modern CPU
"""

import numpy as np
from scipy.linalg import eigh, svd
from scipy.fft import dctn
import sys

# ═══════════════════════════════════════════════════════════════
# COMMON UTILITIES
# ═══════════════════════════════════════════════════════════════

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
        nr,nc = r+dr, c+dc
        while 0<=nr<8 and 0<=nc<8: yield nr,nc; nr+=dr; nc+=dc

def queen_targets(r,c):
    yield from bishop_targets(r,c); yield from rook_targets(r,c)

def king_targets(r,c):
    for dr in [-1,0,1]:
        for dc in [-1,0,1]:
            if dr==0 and dc==0: continue
            nr,nc = r+dr, c+dc
            if 0<=nr<8 and 0<=nc<8: yield nr,nc

PIECE_FNS = {'Knight':knight_targets, 'King':king_targets,
             'Bishop':bishop_targets, 'Rook':rook_targets, 'Queen':queen_targets}

def build_adjacency(fn):
    A = np.zeros((64,64))
    for r in range(8):
        for c in range(8):
            for tr,tc in fn(r,c): A[sq(r,c),sq(tr,tc)] = 1
    return A

def graph_laplacian(A):
    return np.diag(A.sum(axis=1)) - A

# Board grid graph (vacuum Hamiltonian)
A_GRID = np.zeros((64,64))
for _r in range(8):
    for _c in range(8):
        for _dr,_dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            _nr,_nc = _r+_dr, _c+_dc
            if 0<=_nr<8 and 0<=_nc<8:
                A_GRID[sq(_r,_c), sq(_nr,_nc)] = 1
L_GRID = graph_laplacian(A_GRID)
EVALS_GRID, EVECS_GRID = eigh(L_GRID)

# ═══════════════════════════════════════════════════════════════
# SECTION 2: Board = Grid Graph, eigenvectors = 2D cosines
# ═══════════════════════════════════════════════════════════════

def test_section_2():
    print("\n" + "="*70)
    print("  SECTION 2: Board Grid Graph Eigenvalues = Kronecker Sum")
    print("="*70)
    
    path_evals = np.array([2*(1 - np.cos(np.pi*k/8)) for k in range(8)])
    predicted = np.sort(np.add.outer(path_evals, path_evals).flatten())
    actual = np.sort(EVALS_GRID)
    error = np.linalg.norm(predicted - actual)
    
    status = "PASS" if error < 1e-12 else "FAIL"
    print(f"  Kronecker sum prediction error: {error:.2e}  [{status}]")
    return error < 1e-12

# ═══════════════════════════════════════════════════════════════
# SECTION 3: Piece Resonant Structures
# ═══════════════════════════════════════════════════════════════

def test_section_3():
    print("\n" + "="*70)
    print("  SECTION 3: Piece Spectra & Cross-Piece Orthogonality")
    print("="*70)
    
    all_pass = True
    
    # Per-piece spectral properties
    print(f"\n  {'Piece':8s} {'Comp':>5s} {'λ₂':>8s} {'λ_max':>8s} {'Degree':>12s} {'Regular':>8s}")
    for name, fn in PIECE_FNS.items():
        A = build_adjacency(fn)
        L = graph_laplacian(A)
        evals, _ = eigh(L)
        n_comp = np.sum(np.abs(evals) < 1e-10)
        nonzero = evals[evals > 1e-10]
        lambda2 = nonzero[0] if len(nonzero) > 0 else 0
        d = A.sum(axis=1)
        is_reg = np.std(d) < 0.01
        print(f"  {name:8s} {n_comp:5d} {lambda2:8.3f} {evals[-1]:8.3f} [{int(d.min()):2d},{int(d.max()):2d}]     {str(is_reg):>8s}")
    
    # Verify specific claims
    A_bishop = build_adjacency(bishop_targets)
    evals_bishop, _ = eigh(graph_laplacian(A_bishop))
    bishop_comp = np.sum(np.abs(evals_bishop) < 1e-10)
    assert bishop_comp == 2, f"Bishop should have 2 components, got {bishop_comp}"
    print(f"\n  Bishop 2 components: PASS")
    
    A_rook = build_adjacency(rook_targets)
    rook_deg = A_rook.sum(axis=1)
    assert np.std(rook_deg) < 0.01, "Rook should be regular"
    assert rook_deg[0] == 14, f"Rook degree should be 14, got {rook_deg[0]}"
    print(f"  Rook regular (d=14): PASS")
    
    # Cross-piece DCT orthogonality
    src = (4, 4)
    piece_spectra = {}
    for name, fn in PIECE_FNS.items():
        mob = np.zeros((8,8))
        for tr,tc in fn(src[0], src[1]): mob[tr,tc] = 1.0
        piece_spectra[name] = dctn(mob, type=2, norm='ortho')
    
    print(f"\n  DCT cross-piece cosine similarity:")
    names = list(PIECE_FNS.keys())
    for i, n1 in enumerate(names):
        for j, n2 in enumerate(names):
            if j <= i: continue
            s1 = piece_spectra[n1].flatten()
            s2 = piece_spectra[n2].flatten()
            cos = np.dot(s1,s2) / (np.linalg.norm(s1) * np.linalg.norm(s2))
            print(f"    {n1:8s}-{n2:8s}: {cos:.4f}", end='')
            if n1 == 'Knight':
                if abs(cos) > 0.001:
                    print("  [FAIL - expected ~0]")
                    all_pass = False
                else:
                    print("  [PASS - orthogonal]")
            elif n1 == 'Bishop' and n2 == 'Rook':
                if abs(cos) > 0.001:
                    print("  [FAIL - expected ~0]")
                    all_pass = False
                else:
                    print("  [PASS - orthogonal]")
            else:
                print()
    
    return all_pass

# ═══════════════════════════════════════════════════════════════
# SECTION 4: Lattice Fermion Model
# ═══════════════════════════════════════════════════════════════

def test_section_4():
    print("\n" + "="*70)
    print("  SECTION 4: Quantum Numbers & Perturbation Theory")
    print("="*70)
    
    all_pass = True
    
    # Quantum number uniqueness
    quantum_numbers = {}
    for name, fn in PIECE_FNS.items():
        A = build_adjacency(fn)
        L = graph_laplacian(A)
        evals, _ = eigh(L)
        evals_A = np.sort(np.linalg.eigvals(A).real)
        pos = evals_A[evals_A > 0.01]; neg = -evals_A[evals_A < -0.01]
        n_match = min(len(pos), len(neg))
        sym_err = np.linalg.norm(np.sort(pos)[:n_match] - np.sort(neg)[:n_match]) if n_match > 0 else float('inf')
        n_comp = np.sum(np.abs(evals) < 1e-10)
        d = A.sum(axis=1)
        nonzero = evals[evals > 1e-10]
        qn = (int(sym_err < 0.01), n_comp, int(np.std(d) < 0.01),
              round(float(nonzero[0]) if len(nonzero) > 0 else 0, 3),
              round(float(evals[-1]), 2))
        quantum_numbers[name] = qn
        print(f"  {name:8s}: {qn}")
    
    tuples = list(quantum_numbers.values())
    unique = len(set(tuples)) == len(tuples)
    print(f"\n  All tuples unique: {unique}  [{'PASS' if unique else 'FAIL'}]")
    if not unique: all_pass = False
    
    # Weyl perturbation bound
    print(f"\n  Weyl perturbation bounds:")
    for name, fn in PIECE_FNS.items():
        A = build_adjacency(fn)
        L = graph_laplacian(A)
        V = L - L_GRID
        evals_piece, _ = eigh(L)
        max_shift = np.max(np.abs(evals_piece - EVALS_GRID))
        weyl_bound = np.linalg.norm(V, 2)
        holds = max_shift <= weyl_bound + 1e-10
        print(f"    {name:8s}: Δλ_max={max_shift:.3f} ≤ {weyl_bound:.3f}  [{'PASS' if holds else 'FAIL'}]")
        if not holds: all_pass = False
    
    # Many-body correlation
    print(f"\n  Many-body correlation test (rook graph, pieces at d4 and f6):")
    A_rook = build_adjacency(rook_targets)
    L_rook = graph_laplacian(A_rook)
    evals_free, _ = eigh(L_rook)
    
    def build_adj_removed(fn, removed):
        A = np.zeros((64,64))
        for r in range(8):
            for c in range(8):
                s = sq(r,c)
                if s in removed: continue
                for tr,tc in fn(r,c):
                    t = sq(tr,tc)
                    if t not in removed: A[s,t] = 1
        return A
    
    sq_A, sq_B = sq(4,3), sq(2,5)
    eA, _ = eigh(graph_laplacian(build_adj_removed(rook_targets, {sq_A})))
    eB, _ = eigh(graph_laplacian(build_adj_removed(rook_targets, {sq_B})))
    eAB, _ = eigh(graph_laplacian(build_adj_removed(rook_targets, {sq_A, sq_B})))
    
    correlation = (eAB - evals_free) - ((eA - evals_free) + (eB - evals_free))
    ratio = np.linalg.norm(correlation) / np.linalg.norm(eAB - evals_free)
    print(f"    Correlation/total ratio: {ratio:.1%}")
    print(f"    Non-additive: {'PASS' if ratio > 0.5 else 'FAIL'} (expected ~85%)")
    if ratio < 0.5: all_pass = False
    
    return all_pass

# ═══════════════════════════════════════════════════════════════
# SECTION 5: Capture as Annihilation
# ═══════════════════════════════════════════════════════════════

def test_section_5():
    print("\n" + "="*70)
    print("  SECTION 5: Capture Energy Decomposition")
    print("="*70)
    
    all_pass = True
    
    src, dst = sq(4,4), sq(2,3)
    before = np.zeros(64); before[src] = 3; before[dst] = -3.5
    after = np.zeros(64); after[dst] = 3
    
    delta_cap = EVECS_GRID.T @ (after - before)
    
    move_only = np.zeros(64); move_only[dst] = 3; move_only[src] = -3
    annihilate_only = np.zeros(64); annihilate_only[dst] = 3.5
    
    move_comp = EVECS_GRID.T @ move_only
    annihilate_comp = EVECS_GRID.T @ annihilate_only
    
    recon_error = np.linalg.norm(delta_cap - (move_comp + annihilate_comp))
    print(f"  Reconstruction error: {recon_error:.2e}  [{'PASS' if recon_error < 1e-12 else 'FAIL'}]")
    if recon_error > 1e-12: all_pass = False
    
    E_move = np.linalg.norm(move_comp)**2
    E_annihilate = np.linalg.norm(annihilate_comp)**2
    E_total = np.linalg.norm(delta_cap)**2
    E_cross = E_total - E_move - E_annihilate
    
    print(f"  Movement:     {E_move/E_total*100:5.1f}%")
    print(f"  Annihilation: {E_annihilate/E_total*100:5.1f}%")
    print(f"  Cross-term:   {E_cross/E_total*100:5.1f}%")
    print(f"  Cross-term dominant: {'PASS' if E_cross > E_move and E_cross > E_annihilate else 'FAIL'}")
    
    cos_ma = np.dot(move_comp, annihilate_comp) / (np.linalg.norm(move_comp) * np.linalg.norm(annihilate_comp))
    print(f"  cos(move, annihilate) = {cos_ma:.4f} (expected ≈ 0.707 = 1/√2)")
    
    return all_pass

# ═══════════════════════════════════════════════════════════════
# SECTION 5b/5c: Global Field Coupling
# ═══════════════════════════════════════════════════════════════

def test_section_5bc():
    print("\n" + "="*70)
    print("  SECTION 5b/5c: Global Field Coupling & Conservation")
    print("="*70)
    
    all_pass = True
    VALS = {'P':1,'N':3,'B':3.5,'R':5,'Q':9,'K':100,
            'p':-1,'n':-3,'b':-3.5,'r':-5,'q':-9,'k':-100}
    
    position = {
        sq(7,4): 'K', sq(7,3): 'Q', sq(7,0): 'R', sq(4,2): 'B',
        sq(5,5): 'N', sq(6,3): 'P', sq(4,4): 'P', sq(6,5): 'P',
        sq(0,4): 'k', sq(0,3): 'q', sq(0,0): 'r', sq(0,2): 'b',
        sq(2,5): 'n', sq(1,3): 'p', sq(3,4): 'p', sq(1,5): 'p',
    }
    
    def bsig(pieces):
        s = np.zeros(64)
        for si, p in pieces.items(): s[si] = VALS[p]
        return s
    
    sig = bsig(position)
    
    # Build piece Laplacians
    pL = {}
    pfns = {'N':knight_targets,'B':bishop_targets,'R':rook_targets,
            'Q':queen_targets,'K':king_targets}
    for pc, fn in pfns.items():
        A = build_adjacency(fn)
        pL[pc] = graph_laplacian(A)
    
    # Test 1: Analytical decomposition exactness
    print(f"\n  Analytical decomposition ΔQ = -2v·(Lf)_k + v²·d_k:")
    max_err = 0
    for si, piece in position.items():
        v = VALS[piece]
        Lf = pL['N'] @ sig
        predicted = -2*v*Lf[si] + v**2 * pL['N'][si,si]
        sa = bsig({s:p for s,p in position.items() if s != si})
        actual = float(sa.T @ pL['N'] @ sa) - float(sig.T @ pL['N'] @ sig)
        max_err = max(max_err, abs(actual - predicted))
    print(f"    Max error across all 16 pieces: {max_err:.1e}  [{'PASS' if max_err < 1e-10 else 'FAIL'}]")
    if max_err > 1e-10: all_pass = False
    
    # Test 2: Coupling field matrix rank
    coupling_mat = np.array([pL[p] @ sig for p in ['N','B','R','Q','K']])
    _, S_c, _ = svd(coupling_mat, full_matrices=False)
    pct_s1 = S_c[0]**2 / np.sum(S_c**2) * 100
    print(f"\n  Coupling field matrix:")
    print(f"    σ₁ captures {pct_s1:.1f}% of coupling  [{'PASS' if pct_s1 > 90 else 'FAIL'}]")
    print(f"    σ₅ = {S_c[4]:.4f}  [{'PASS' if S_c[4] < 0.01 else 'FAIL'}]")
    if pct_s1 < 90: all_pass = False
    if S_c[4] > 0.01: all_pass = False
    
    # Test 3: Cross-piece correlations > 0.8
    print(f"\n  Cross-piece coupling correlations (all should be > 0.8):")
    cf = {p: pL[p] @ sig for p in ['N','B','R','Q','K']}
    min_corr = 1.0
    for p1 in ['N','B','R','Q','K']:
        for p2 in ['N','B','R','Q','K']:
            if p1 >= p2: continue
            c = np.corrcoef(cf[p1], cf[p2])[0,1]
            min_corr = min(min_corr, c)
    print(f"    Minimum pairwise correlation: {min_corr:.3f}  [{'PASS' if min_corr > 0.8 else 'FAIL'}]")
    if min_corr < 0.8: all_pass = False
    
    # Test 4: Conservation for non-king pieces
    print(f"\n  Energy conservation test (non-king pieces, total across all graphs):")
    E_full = sum(float(sig.T @ pL[p] @ sig) for p in ['N','B','R','Q','K'])
    max_pct_change = 0
    for si, piece in position.items():
        if piece.upper() == 'K': continue
        sa = bsig({s:p for s,p in position.items() if s != si})
        E_after = sum(float(sa.T @ pL[p] @ sa) for p in ['N','B','R','Q','K'])
        pct = abs(E_after - E_full) / E_full * 100
        max_pct_change = max(max_pct_change, pct)
    print(f"    Max |ΔE|/E for non-king captures: {max_pct_change:.2f}%  [{'PASS' if max_pct_change < 1.0 else 'FAIL'}]")
    if max_pct_change > 1.0: all_pass = False
    
    # Test 5: Coupling sensitivity DCT compression
    from scipy.fft import dctn
    print(f"\n  Coupling sensitivity DCT compression:")
    for pc in ['N','B','R','Q','K']:
        sens = (-2 * pL[pc] @ sig).reshape(8,8)
        spec = dctn(sens, type=2, norm='ortho')
        energy = spec**2
        flat = np.sort(energy.flatten())[::-1]
        total = flat.sum()
        cumsum = np.cumsum(flat)
        n90 = np.searchsorted(cumsum, 0.9*total) + 1
        print(f"    {pc}: {n90}/64 modes for 90%", end='')
        print(f"  [{'PASS' if n90 <= 20 else 'FAIL'}]")
        if n90 > 20: all_pass = False
    
    return all_pass

# ═══════════════════════════════════════════════════════════════
# SECTION 6: Rules in Own Dimensions
# ═══════════════════════════════════════════════════════════════

def test_section_6():
    print("\n" + "="*70)
    print("  SECTION 6: Rule Dimension Independence")
    print("="*70)
    
    all_pass = True
    
    # Scale invariance of bipartiteness
    print(f"\n  Knight bipartiteness across board sizes:")
    def knight_NxN(r,c,N):
        for dr,dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
            nr,nc = r+dr,c+dc
            if 0<=nr<N and 0<=nc<N: yield nr,nc
    
    for N in [5, 6, 8, 10, 12]:
        n = N*N; A = np.zeros((n,n))
        for r in range(N):
            for c in range(N):
                for tr,tc in knight_NxN(r,c,N): A[r*N+c, tr*N+tc] = 1
        evals_A = np.sort(np.linalg.eigvals(A).real)
        pos = evals_A[evals_A > 0.01]; neg = -evals_A[evals_A < -0.01]
        nm = min(len(pos), len(neg))
        err = np.linalg.norm(np.sort(pos)[:nm] - np.sort(neg)[:nm]) if nm > 0 else float('inf')
        bp = err < 0.01
        print(f"    N={N:2d}: bipartite={bp}  [{'PASS' if bp else 'FAIL'}]")
        if not bp: all_pass = False
    
    # Spatial vs abstract decomposition
    print(f"\n  Spatial vs abstract content:")
    for name, fn in PIECE_FNS.items():
        A = build_adjacency(fn)
        L = graph_laplacian(A)
        C = EVECS_GRID.T @ L @ EVECS_GRID
        diag_E = np.sum(C.diagonal()**2)
        total_E = np.sum(C**2)
        offdiag_E = total_E - diag_E
        pct_rule = offdiag_E / total_E * 100
        print(f"    {name:8s}: board={100-pct_rule:5.1f}%, rule={pct_rule:5.1f}%")
    
    # Rook should have 0% rule content
    A_rook = build_adjacency(rook_targets)
    L_rook = graph_laplacian(A_rook)
    C_rook = EVECS_GRID.T @ L_rook @ EVECS_GRID
    C_off = C_rook.copy(); np.fill_diagonal(C_off, 0)
    rook_rule = np.linalg.norm(C_off)
    print(f"\n  Rook off-diagonal norm: {rook_rule:.6f}  [{'PASS' if rook_rule < 1e-10 else 'FAIL'}]")
    if rook_rule > 1e-10: all_pass = False
    
    return all_pass

# ═══════════════════════════════════════════════════════════════
# SECTION 7: Rank-3 Fiber Bundle
# ═══════════════════════════════════════════════════════════════

def test_section_7():
    print("\n" + "="*70)
    print("  SECTION 7: Rank-3 Shared Fiber Bundle")
    print("="*70)
    
    all_pass = True
    upper_idx = np.triu_indices(64, k=1)
    fibers = {}
    
    for name, fn in PIECE_FNS.items():
        A = build_adjacency(fn)
        L = graph_laplacian(A)
        C = EVECS_GRID.T @ L @ EVECS_GRID
        C_off = C.copy(); np.fill_diagonal(C_off, 0)
        fibers[name] = C_off[upper_idx]
    
    # Rook fiber should be zero
    rook_norm = np.linalg.norm(fibers['Rook'])
    print(f"  Rook fiber norm: {rook_norm:.6f}  [{'PASS' if rook_norm < 1e-10 else 'FAIL'}]")
    if rook_norm > 1e-10: all_pass = False
    
    # SVD of non-trivial fibers
    non_trivial = [n for n in PIECE_FNS if np.linalg.norm(fibers[n]) > 0.01]
    fiber_mat = np.array([fibers[n]/np.linalg.norm(fibers[n]) for n in non_trivial])
    U_f, S_f, Vt_f = svd(fiber_mat, full_matrices=False)
    
    print(f"\n  Singular values of stacked fibers:")
    for i, s in enumerate(S_f):
        print(f"    σ_{i+1} = {s:.4f}  ({s**2/np.sum(S_f**2)*100:.1f}%)")
    
    effective_rank = np.sum(S_f > 0.01)
    print(f"\n  Effective rank: {effective_rank}")
    print(f"  Pieces with fiber: {len(non_trivial)}")
    print(f"  Rank < pieces: {effective_rank < len(non_trivial)}  [{'PASS' if effective_rank < len(non_trivial) else 'FAIL'}]")
    if effective_rank >= len(non_trivial): all_pass = False
    
    # Bishop-Queen fiber identity
    cos_bq = np.dot(fibers['Bishop'], fibers['Queen']) / (
        np.linalg.norm(fibers['Bishop']) * np.linalg.norm(fibers['Queen']))
    print(f"\n  Bishop-Queen fiber cosine: {cos_bq:.4f}  [{'PASS' if abs(cos_bq - 1.0) < 0.001 else 'FAIL'}]")
    if abs(cos_bq - 1.0) > 0.001: all_pass = False
    
    # Queen = Bishop + Rook adjacency identity
    A_queen = build_adjacency(queen_targets)
    A_bishop = build_adjacency(bishop_targets)
    A_rook = build_adjacency(rook_targets)
    A_sum = np.clip(A_bishop + A_rook, 0, 1)
    queen_identity = np.allclose(A_queen, A_sum)
    print(f"  A_queen = clip(A_bishop + A_rook): {queen_identity}  [{'PASS' if queen_identity else 'FAIL'}]")
    if not queen_identity: all_pass = False
    
    # Holonomy test
    def local_fiber(fn, source_sq):
        r, c = source_sq // 8, source_sq % 8
        A_loc = np.zeros((64,64))
        for tr,tc in fn(r,c):
            A_loc[source_sq, sq(tr,tc)] = 1
            A_loc[sq(tr,tc), source_sq] = 1
        C_loc = EVECS_GRID.T @ A_loc @ EVECS_GRID
        C_off = C_loc.copy(); np.fill_diagonal(C_off, 0)
        return C_off[upper_idx]
    
    loop = [sq(4,0), sq(2,1), sq(0,2), sq(1,4), sq(3,3), sq(4,1)]
    fibs = [local_fiber(knight_targets, s) for s in loop]
    holonomy = np.dot(fibs[0], fibs[-1]) / (np.linalg.norm(fibs[0]) * np.linalg.norm(fibs[-1]))
    print(f"\n  Holonomy (start-end similarity): {holonomy:.4f}")
    print(f"  Non-trivial: {abs(holonomy - 1.0) > 0.01}  [{'PASS' if abs(holonomy - 1.0) > 0.01 else 'FAIL'}]")
    if abs(holonomy - 1.0) <= 0.01: all_pass = False
    
    return all_pass

# ═══════════════════════════════════════════════════════════════
# RUN ALL TESTS
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    results = {}
    for name, test_fn in [
        ("Section 2: Grid Graph", test_section_2),
        ("Section 3: Piece Spectra", test_section_3),
        ("Section 4: Lattice Fermion", test_section_4),
        ("Section 5: Capture Annihilation", test_section_5),
        ("Section 5b/5c: Field Coupling", test_section_5bc),
        ("Section 6: Rule Dimensions", test_section_6),
        ("Section 7: Fiber Bundle", test_section_7),
    ]:
        try:
            results[name] = test_fn()
        except Exception as e:
            print(f"\n  ERROR in {name}: {e}")
            results[name] = False
    
    print("\n" + "="*70)
    print("  FINAL RESULTS")
    print("="*70)
    all_pass = True
    for name, passed in results.items():
        status = "PASS ✓" if passed else "FAIL ✗"
        print(f"  {name:40s}  [{status}]")
        if not passed: all_pass = False
    
    print(f"\n  Overall: {'ALL TESTS PASSED' if all_pass else 'SOME TESTS FAILED'}")
    sys.exit(0 if all_pass else 1)
