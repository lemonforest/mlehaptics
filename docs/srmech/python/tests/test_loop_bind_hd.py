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
"""
import numpy as np
import pytest

from srmech.amsc import hdc

BS = 8          # octonion block size = LOOP_DIM
NB = 256        # canonical block count → D = 2048
D = NB * BS
SEED = 811


def _e(i):
    v = np.zeros(BS)
    v[i] = 1.0
    return v


def _rand_unit_blocks(rng, nb=NB):
    b = rng.standard_normal((nb, BS))
    b /= np.linalg.norm(b, axis=1, keepdims=True)
    return b.reshape(-1)


def test_canonical_width_is_2048():
    assert hdc.LOOP_DIM == BS and D == 2048


def test_block_diagonal_no_coupling():
    # block k of loop_bind_hd(x,y) == loop_bind(x_k, y_k) exactly (err 0.0; F289).
    rng = np.random.default_rng(SEED)
    x, y = _rand_unit_blocks(rng), _rand_unit_blocks(rng)
    z = hdc.loop_bind_hd(x, y).reshape(NB, BS)
    xb, yb = x.reshape(NB, BS), y.reshape(NB, BS)
    worst = max(
        float(np.linalg.norm(z[k] - hdc.loop_bind(xb[k], yb[k])))
        for k in (0, 7, 42, 255)
    )
    assert worst == 0.0


def test_block_independence():
    # perturbing one input block changes ONLY that output block (direct sum).
    rng = np.random.default_rng(SEED)
    x, y = _rand_unit_blocks(rng), _rand_unit_blocks(rng)
    z0 = hdc.loop_bind_hd(x, y).reshape(NB, BS)
    y2 = y.copy().reshape(NB, BS)
    y2[3] = -y2[3]            # flip block 3 only
    z1 = hdc.loop_bind_hd(x, y2.reshape(-1)).reshape(NB, BS)
    assert not np.allclose(z1[3], z0[3])                      # block 3 changed
    assert all(np.array_equal(z1[k], z0[k]) for k in (0, 1, 2, 4, 255))  # rest fixed


def test_per_block_product_is_shipped_table():
    # a 2-block HD vector: block0 = e1⊗e2 = +e3, block1 = e2⊗e4 = +e6 (F281 table).
    x = np.concatenate([_e(1), _e(2)])
    y = np.concatenate([_e(2), _e(4)])
    out = hdc.loop_bind_hd(x, y).reshape(2, BS)
    assert np.allclose(out[0], _e(3))
    assert np.allclose(out[1], _e(6))


def test_unbind_recovers_value():
    # unbind_hd(a, loop_bind_hd(a, v)) == v for unit-per-block a (Moufang division).
    rng = np.random.default_rng(SEED)
    a, v = _rand_unit_blocks(rng), _rand_unit_blocks(rng)
    rec = hdc.loop_unbind_hd(a, hdc.loop_bind_hd(a, v))
    assert float(np.linalg.norm(rec - v)) < 1e-12   # F289 anchor: 2.92e-15


def test_length_must_be_multiple_of_eight():
    bad = np.ones(8 * 3 + 1)
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
    rng = np.random.default_rng(20260602)
    for nb in (1, 2, 3, 4, 5, 6, 7, 8, 9, 17, NB):
        x = rng.standard_normal(nb * BS)
        y = rng.standard_normal(nb * BS)
        got = hdc.loop_bind_hd(x, y)
        xb, yb = x.reshape(nb, BS), y.reshape(nb, BS)
        want = np.concatenate([hdc._loop_bind_raw(xb[k], yb[k]) for k in range(nb)])
        assert np.allclose(got, want, rtol=0.0, atol=1e-12), f"nb={nb}"


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
    rng = np.random.default_rng(23)
    rub = lambda: _rand_unit_blocks(rng, d_nb)
    codebook = np.stack([rub() for _ in range(M)])
    cb = codebook / np.linalg.norm(codebook, axis=1, keepdims=True)
    idx = rng.choice(M, size=K, replace=False)
    keys = [rub() for _ in range(K)]
    bundle = np.sum([hdc.loop_bind_hd(keys[i], codebook[idx[i]]) for i in range(K)], axis=0)
    hits = sum(int(np.argmax(cb @ hdc.loop_unbind_hd(keys[i], bundle))) == int(idx[i])
               for i in range(K))
    assert hits == K
