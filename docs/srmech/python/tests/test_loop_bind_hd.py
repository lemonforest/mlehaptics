"""v0.7.0rc4 — block-octonion HD tiling (#811) + capacity-free vs Klein-4 (#812).

Bit-exact anchors from F289 (commit 82c4f4de / rc4_groundtruth.py), all derived
FROM the shipped loop_bind so the HD tiling agrees by construction:

  - loop_bind_hd = ⊕ of NB independent dim-8 loop_binds; block-DIAGONAL (block k of
    the result == loop_bind of the two k-th 8-blocks; err 0.0e+00, seed 811)
  - per-block product IS the shipped Cayley–Dickson table (e1⊗e2=+e3, e2⊗e4=+e6, …)
  - loop_unbind_hd(a, loop_bind_hd(a, v)) recovers v (err 2.9e-15, unit blocks, seed 811)
  - the capacity MECHANISM (bind K pairs / superpose / unbind / nearest-cosine
    cleanup) retrieves cleanly; the full loop-bind ≥ Klein-4 K=128 verdict is the
    OWNED result in F289/F277 and is not re-run here.

Class-K clean: norms / inner products, never abs().

rc125 (numpy-free, #564): this test is itself numpy-FREE — ``loop_bind_hd`` /
``loop_unbind_hd`` return ``list[float]``; block arithmetic is explicit list
math, norms ride ``mat_norm``, and the random unit blocks come from stdlib
``random.Random`` (no numpy oracle, per
`[[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]`).
"""
import random

import pytest

from srmech.amsc.laplacian import mat_norm
from srmech.amsc import hdc

BS = 8          # octonion block size = LOOP_DIM
NB = 256        # canonical block count → D = 2048
D = NB * BS
SEED = 811


def _e(i):
    v = [0.0] * BS
    v[i] = 1.0
    return v


def _vsub(u, v):
    return [u[i] - v[i] for i in range(len(u))]


def _blocks(flat, nb):
    return [flat[k * BS:(k + 1) * BS] for k in range(nb)]


def _rand_unit_block(rng):
    v = [rng.gauss(0.0, 1.0) for _ in range(BS)]
    nrm = sum(x * x for x in v) ** 0.5
    return [x / nrm for x in v]


def _rand_unit_blocks(rng, nb=NB):
    out = []
    for _ in range(nb):
        out.extend(_rand_unit_block(rng))
    return out


def _standard_normal(rng, n):
    return [rng.gauss(0.0, 1.0) for _ in range(n)]


def test_canonical_width_is_2048():
    assert hdc.LOOP_DIM == BS and D == 2048


def test_block_diagonal_no_coupling():
    # block k of loop_bind_hd(x,y) == loop_bind(x_k, y_k) exactly (err 0.0; F289).
    rng = random.Random(SEED)
    x, y = _rand_unit_blocks(rng), _rand_unit_blocks(rng)
    z = _blocks(hdc.loop_bind_hd(x, y), NB)
    xb, yb = _blocks(x, NB), _blocks(y, NB)
    worst = max(
        mat_norm(_vsub(z[k], hdc.loop_bind(xb[k], yb[k])))
        for k in (0, 7, 42, 255)
    )
    assert worst == 0.0


def test_block_independence():
    # perturbing one input block changes ONLY that output block (direct sum).
    rng = random.Random(SEED)
    x, y = _rand_unit_blocks(rng), _rand_unit_blocks(rng)
    z0 = _blocks(hdc.loop_bind_hd(x, y), NB)
    yb = _blocks(y, NB)
    yb[3] = [-v for v in yb[3]]            # flip block 3 only
    y2 = [v for blk in yb for v in blk]
    z1 = _blocks(hdc.loop_bind_hd(x, y2), NB)
    assert mat_norm(_vsub(z1[3], z0[3])) > 1e-9              # block 3 changed
    assert all(z1[k] == z0[k] for k in (0, 1, 2, 4, 255))   # rest fixed


def test_per_block_product_is_shipped_table():
    # a 2-block HD vector: block0 = e1⊗e2 = +e3, block1 = e2⊗e4 = +e6 (F281 table).
    x = _e(1) + _e(2)
    y = _e(2) + _e(4)
    out = _blocks(hdc.loop_bind_hd(x, y), 2)
    assert mat_norm(_vsub(out[0], _e(3))) < 1e-9
    assert mat_norm(_vsub(out[1], _e(6))) < 1e-9


def test_unbind_recovers_value():
    # unbind_hd(a, loop_bind_hd(a, v)) == v for unit-per-block a (Moufang division).
    rng = random.Random(SEED)
    a, v = _rand_unit_blocks(rng), _rand_unit_blocks(rng)
    rec = hdc.loop_unbind_hd(a, hdc.loop_bind_hd(a, v))
    assert mat_norm(_vsub(rec, v)) < 1e-12   # F289 anchor: 2.92e-15


def test_length_must_be_multiple_of_eight():
    bad = [1.0] * (8 * 3 + 1)
    with pytest.raises(AssertionError):
        hdc.loop_bind_hd(bad, bad)
    with pytest.raises(AssertionError):
        hdc.loop_unbind_hd(bad, bad)


def test_native_hd_batch_parity_all_nb():
    # rc11 F292 #2: the native N-way SIMD HD bind (one srmech_loop_bind_hd_f64
    # call for the whole NB-block array) must match the pure-Python per-block
    # _loop_bind_raw oracle. NB chosen to straddle the AVX W=4 + SSE2 W=2 group
    # sizes AND every remainder (nb mod 4, nb mod 2). On a Pyodide/no-native
    # build loop_bind_hd takes the per-block path — still parity, so the test is
    # unconditional. Bit-exact in practice (the octonion product is +/-/*, no FMA
    # divergence; F292 "parity-trivial, err 0.0"); 1e-12 absorbs any 1-ULP.
    rng = random.Random(20260602)
    for nb in (1, 2, 3, 4, 5, 6, 7, 8, 9, 17, NB):
        x = _standard_normal(rng, nb * BS)
        y = _standard_normal(rng, nb * BS)
        got = hdc.loop_bind_hd(x, y)
        xb, yb = _blocks(x, nb), _blocks(y, nb)
        want = []
        for k in range(nb):
            want.extend(hdc._loop_bind_raw(xb[k], yb[k]))
        assert mat_norm(_vsub(got, want)) < 1e-12, f"nb={nb}"


def test_native_hd_symbol_wired_when_native():
    # when the native lib is loaded it MUST export the rc11 batch symbol (the
    # build wires srmech_loop_bind_hd_f64); _try_native_loop_bind_hd then drives
    # loop_bind_hd. On a pure-Python build there is no symbol and that is fine.
    from srmech.amsc import _native
    if _native.HAS_NATIVE and _native.LIB is not None:
        assert hasattr(_native.LIB, "srmech_loop_bind_hd_f64")


def test_capacity_mechanism_retrieves():
    # bind K key⊗val pairs, superpose, unbind each key, clean up by nearest cosine
    # over an M-item value codebook — all K retrieved. (The full loop ≥ klein4 K=128
    # capacity-free verdict is owned in F289/F277; this is the mechanism sanity.)
    d_nb = 32                       # D = 256 (fast)
    M, K = 16, 4
    rng = random.Random(23)
    codebook = [_rand_unit_blocks(rng, d_nb) for _ in range(M)]
    cb = []
    for row in codebook:
        nrm = sum(x * x for x in row) ** 0.5
        cb.append([x / nrm for x in row])
    idx = rng.sample(range(M), K)
    keys = [_rand_unit_blocks(rng, d_nb) for _ in range(K)]
    n_d = d_nb * BS
    bundle = [0.0] * n_d
    for i in range(K):
        bound = hdc.loop_bind_hd(keys[i], codebook[idx[i]])
        bundle = [bundle[t] + bound[t] for t in range(n_d)]

    def argmax_cosine(query):
        best, best_score = 0, None
        for m in range(M):
            score = sum(cb[m][t] * query[t] for t in range(n_d))
            if best_score is None or score > best_score:
                best, best_score = m, score
        return best

    hits = sum(
        argmax_cosine(hdc.loop_unbind_hd(keys[i], bundle)) == idx[i]
        for i in range(K)
    )
    assert hits == K
