"""rc156 — C standalone-complete honor: the no-scratch size caps are GONE.

Two pre-rc154 caps were compiled-in problem-SIZE rejections with NO scratch to
arena-size — the kernels already write only into caller-supplied memory, so the
caps gratuitously refused larger valid problems a C-only / MCU host could serve:

  * ``SRMECH_EXACT_DFT_MAX_N 4096`` — exact integer DFT (writes caller out_re/im).
  * ``SRMECH_HDC_MAX_BUNDLE_N 257`` — BSC / polar / klein4 batch bundle (scalar
    counters over a caller-resident pointer array).

rc156 lifts both C caps and removes the Python ``MAX_BUNDLE_N`` pre-bound (which
also strangled the otherwise-uncapped pure-Python loop). This test proves, at
sizes the old caps forbade:

  1. the native C accepts the larger problem (no OVERFLOW), and
  2. native == the pure-Python alternative (bit-for-bit).

Per [[feedback_c_must_be_standalone_complete_no_python_fallback]]. numpy-free.
"""

import array

from srmech.amsc import _native
from srmech.amsc import hdc
from srmech.amsc.cascade import exact_dft as edft


# ---------------------------------------------------------------------------
# exact-DFT: N = 8192 > old SRMECH_EXACT_DFT_MAX_N (4096)
# ---------------------------------------------------------------------------

def _pure_dft_bin(re, im, n, k):
    """The negacyclic exact-DFT coefficient X[k] (re_vec, im_vec), len n/2."""
    h = n // 2
    xr = [0] * h
    xi = [0] * h
    for idx in range(n):
        j = (idx * k) % n
        sign = 1
        if j >= h:                       # Class K: ζ^{N/2} = -1
            j -= h
            sign = -1
        xr[j] += sign * re[idx]
        xi[j] += sign * im[idx]
    return xr, xi


def test_exact_dft_over_old_cap_native_accepts_and_matches_pure():
    n = 8192                              # one power-of-two past the old 4096 cap
    re = [((i * 3) % 7) - 3 for i in range(n)]   # small ints → int64-safe
    im = [((i * 5) % 5) - 2 for i in range(n)]

    if _native.HAS_NATIVE and hasattr(_native.LIB, "srmech_exact_dft_i64"):
        # HONOR: the C kernel no longer rejects N > 4096 — it returns a spectrum.
        native = edft._exact_dft_core_native(re, im, n, False)
        assert native is not None, "native exact-DFT must accept N=8192 (cap lifted)"
        assert len(native) == n
        # native == pure on a handful of non-trivial bins (full pure DFT is O(N^2)).
        for k in (0, 1, 2, 3, 17, n - 1):
            pr, pi = _pure_dft_bin(re, im, n, k)
            assert native[k][0] == pr and native[k][1] == pi, f"bin {k} native!=pure"

    # The PUBLIC op returns the same spectrum whether native is present or forced-pure.
    saved = _native.HAS_NATIVE
    try:
        full_native = edft.exact_dft(re)        # native when present
        _native.HAS_NATIVE = False
        full_pure = edft.exact_dft(re)          # complete pure alternative
    finally:
        _native.HAS_NATIVE = saved
    # Compare the bins we can afford (both are ExactSpectrum = list of (re,im) pairs).
    for k in (0, 1, 2, 3, 17, n - 1):
        assert full_native[k] == full_pure[k], f"public bin {k} native!=pure"


# ---------------------------------------------------------------------------
# HDC batch bundle: n_vectors > old SRMECH_HDC_MAX_BUNDLE_N (257)
# ---------------------------------------------------------------------------

def _mk_bsc_vectors(n_vectors, n_bytes, seed=1):
    vecs = []
    x = seed
    for _ in range(n_vectors):
        b = bytearray(n_bytes)
        for i in range(n_bytes):
            x = (x * 1103515245 + 12345) & 0xFFFFFFFF
            b[i] = (x >> 16) & 0xFF
        vecs.append(bytes(b))
    return vecs


def test_bsc_bundle_over_old_cap_native_matches_pure():
    n_vectors = 301                       # odd, well past the old 257 cap
    vecs = _mk_bsc_vectors(n_vectors, 8, seed=7)

    out_native = hdc.bundle(vecs)         # native when present, else pure
    saved = _native.HAS_NATIVE
    try:
        _native.HAS_NATIVE = False
        out_pure = hdc.bundle(vecs)       # the complete pure alternative
    finally:
        _native.HAS_NATIVE = saved
    assert out_native == out_pure
    assert len(out_native) == 8


def test_bundle_with_ties_over_old_cap_runs():
    # bundle_with_ties is pure-Python; the rc156 point is the Python pre-bound is
    # gone, so an even count of 300 (> 257) is accepted, not a ValueError.
    vecs = _mk_bsc_vectors(300, 8, seed=11)
    majority, ties = hdc.bundle_with_ties(vecs)
    assert len(majority) == 8 and len(ties) == 8


def test_native_batch_bundles_accept_over_old_cap():
    """Standalone-C honor for all three batch bundles: srmech_hdc_bundle /
    _polar_bundle / _klein4_bundle must return OK (not OVERFLOW) for n_vectors > 257."""
    if not _native.HAS_NATIVE:
        return
    import ctypes
    lib = _native.LIB
    n_vectors = 301
    n_bytes = 4

    # BSC bundle (uint8 byte-packed, odd count).
    vecs = _mk_bsc_vectors(n_vectors, n_bytes, seed=3)
    buf_t = ctypes.c_uint8 * n_bytes
    bufs = [buf_t.from_buffer_copy(v) for v in vecs]
    parr = (ctypes.POINTER(ctypes.c_uint8) * n_vectors)(
        *(ctypes.cast(b, ctypes.POINTER(ctypes.c_uint8)) for b in bufs)
    )
    out = (ctypes.c_uint8 * n_bytes)()
    rc = lib.srmech_hdc_bundle(parr, n_vectors, n_bytes, out)
    assert rc == _native.SRMECH_OK, f"srmech_hdc_bundle rc={rc} for n_vectors=301"

    # polar bundle (int8 {-1,0,+1}).
    pv = [bytes(((j + k) % 3) - 1 & 0xFF for j in range(n_bytes)) for k in range(n_vectors)]
    pbuf_t = ctypes.c_int8 * n_bytes
    pbufs = [pbuf_t.from_buffer_copy(v) for v in pv]
    pparr = (ctypes.POINTER(ctypes.c_int8) * n_vectors)(
        *(ctypes.cast(b, ctypes.POINTER(ctypes.c_int8)) for b in pbufs)
    )
    pout = (ctypes.c_int8 * n_bytes)()
    rc = lib.srmech_polar_bundle(pparr, n_vectors, n_bytes, pout)
    assert rc == _native.SRMECH_OK, f"srmech_polar_bundle rc={rc} for n_vectors=301"

    # klein4 bundle (uint8 {0,1,2,3}).
    kv = [bytes((j + k) % 4 for j in range(n_bytes)) for k in range(n_vectors)]
    kbuf_t = ctypes.c_uint8 * n_bytes
    kbufs = [kbuf_t.from_buffer_copy(v) for v in kv]
    kparr = (ctypes.POINTER(ctypes.c_uint8) * n_vectors)(
        *(ctypes.cast(b, ctypes.POINTER(ctypes.c_uint8)) for b in kbufs)
    )
    kout = (ctypes.c_uint8 * n_bytes)()
    rc = lib.srmech_klein4_bundle(kparr, n_vectors, n_bytes, kout)
    assert rc == _native.SRMECH_OK, f"srmech_klein4_bundle rc={rc} for n_vectors=301"
