"""rc213 (#753) — the jpeg numeric block-DCT pipeline C peer.

``closed_form_ops.jpeg`` — the float-DCT NUMERIC op deferred at rc144/B6b out
of the exact coder batch, reclassified ``composition_of_c`` at rc155 (each
block's DCT riding ``dct.op`` → ``mat_matmul``, 4 Python-glue dispatches PER
BLOCK) — moves ``composition_of_c → c_dispatched`` over its dedicated blocked
C peer ``srmech_jpeg_encode_f64`` / ``srmech_jpeg_decode_f64`` (ONE ctypes
crossing for the whole image). This suite proves:

1. **VALUE oracles** — jpeg computes the mathematically-correct pipeline,
   independent of the C-vs-pure question: a constant image transforms to a
   DC-only block (DC = 4·bs²·v, the separable 2-D DCT-II of a constant); the
   high-quality encode→decode round-trip recovers the image within
   quantisation error; non-multiple-of-``bs`` dimensions truncate to whole
   blocks.
2. **NATIVE == PURE (differential)** — each path matches its own forced-pure
   fallback (native OFF via monkeypatch):
   - the DECODED image to reldiff ≤ 1e-9 — a **differential NUMERIC** contract
     (float DCT), **NOT** byte-identity: the stage accumulations can FMA-fuse
     ~1 ULP on some platforms (macOS clang), the SAME classification as the
     F1 FFT / F2 SVD / B4 numeric batches;
   - the quantised ENCODE blocks exactly (integer outputs) — guarded by a
     precondition assert that every pre-quantise coefficient of the fixture
     sits ≥ 1e-6 away from a round-half-even boundary, so the exact-equality
     assertion is robust under the ≤ 1e-9 float contract (a fixture that
     drifted onto a boundary would fail the precondition, not flake the
     parity).

With native absent, forced-pure == default so the differential tests are
trivially green — they still guard that the pure path is complete and the
dispatch wiring does not change the value.

This module is **numpy-free** (a test for a numpy-free surface must itself be
numpy-free) — the reference maths is stdlib ``math`` / ``random`` only.
"""

from __future__ import annotations

import math
import random

from srmech.amsc import _native
from srmech.signal_processing.closed_form_ops import dct, jpeg

# native availability (the differential tests run regardless — with native
# absent, forced-pure == default so reldiff is trivially 0).
_HAS_JPEG = _native.has_native_jpeg_f64()


# ----------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------

def _rand_image(h, w, seed, lo=0, hi=255):
    rng = random.Random(seed)
    return [[float(rng.randint(lo, hi)) for _ in range(w)] for _ in range(h)]


def _reldiff_2d(a, b):
    """max|a-b| / max|a| over two equal-shape 2-D real arrays."""
    scale = max((abs(v) for row in a for v in row), default=1.0) or 1.0
    worst = 0.0
    for ra, rb in zip(a, b):
        for va, vb in zip(ra, rb):
            d = abs(va - vb)
            if d > worst:
                worst = d
    return worst / scale


def _pure_scaled_coefficients(img, quality, bs):
    """The pre-quantise ``block_dct/qt`` values via the PURE block-DCT cascade
    (jpeg's own dct.op + quant table) — used to assert the fixture sits away
    from round-half-even boundaries before demanding exact integer parity."""
    qt = jpeg._quant_table(quality, None)
    h = len(img)
    w = len(img[0])
    out = []
    for i in range(h // bs):
        for j in range(w // bs):
            block = [
                [img[i * bs + r][j * bs + c] for c in range(bs)]
                for r in range(bs)
            ]
            bd = dct.op(dct.op(block, dct_type=2, axis=0), dct_type=2, axis=1)
            out.extend(
                bd[r][c] / qt[r][c] for r in range(bs) for c in range(bs)
            )
    return out


def _assert_away_from_round_boundary(scaled, eps=1e-6):
    """Precondition: no fixture coefficient within ``eps`` of a half-integer
    (the round-half-even boundary), so a ≤1e-9 native-vs-pure float drift can
    NEVER flip a quantised integer — the exact-equality parity is then a
    robust assertion, not a flake."""
    for s in scaled:
        frac = s - math.floor(s)
        assert abs(frac - 0.5) > eps, (
            f"fixture coefficient {s!r} sits within {eps} of a rounding "
            f"boundary — pick a different seed"
        )


# ======================================================================
# VALUE oracles (independent of the C-vs-pure question)
# ======================================================================

def test_jpeg_constant_image_is_dc_only():
    """A constant image is the DCT-II DC eigenvector: every quantised block is
    DC-only with DC = round(4·bs²·v / qt[0][0]) (the separable 2-D transform
    puts 2·bs·v per axis at k = 0 and ~0 elsewhere)."""
    bs = 8
    v = 3.0
    ones = [[1.0] * bs for _ in range(bs)]  # qt == 1: no quantisation
    img = [[v] * 16 for _ in range(16)]
    blocks, shape, qt = jpeg.op(img, quant_table=ones)
    assert shape == (16, 16)
    assert len(blocks) == 4
    dc = round(4.0 * bs * bs * v)
    for qb in blocks:
        assert qb[0][0] == dc, qb[0][0]
        off = [
            qb[r][c] for r in range(bs) for c in range(bs) if (r, c) != (0, 0)
        ]
        assert all(x == 0 for x in off), off


def test_jpeg_roundtrip_recovers_image():
    """High-quality encode→decode recovers the image within quantisation
    error (the rc155 value oracle, kept as the pipeline-shape guard)."""
    img = _rand_image(16, 16, seed=11)
    blocks, shape, qt = jpeg.op(img, quality=90)
    rec = jpeg.op((blocks, shape, qt), decode=True)
    assert shape == (16, 16)
    mse = sum(
        (img[i][j] - rec[i][j]) ** 2 for i in range(16) for j in range(16)
    ) / 256.0
    assert mse < 25.0, mse


def test_jpeg_truncates_to_whole_blocks():
    """Non-multiple-of-bs dimensions truncate to whole blocks (JPEG canonical
    behaviour of this closed-form core)."""
    img = _rand_image(19, 21, seed=5)
    blocks, shape, qt = jpeg.op(img, quality=75)
    assert shape == (16, 16)
    assert len(blocks) == 4
    rec = jpeg.op((blocks, shape, qt), decode=True)
    assert len(rec) == 16 and len(rec[0]) == 16


# ======================================================================
# NATIVE == PURE (differential; the B4 within-tol contract)
# ======================================================================

def test_jpeg_encode_native_matches_pure(monkeypatch):
    """The c_dispatched encode (srmech_jpeg_encode_f64) produces the SAME
    quantised integer blocks as the forced-pure block-DCT cascade — exact on
    a fixture asserted away from rounding boundaries (see module docstring)."""
    img = _rand_image(16, 24, seed=213)
    _assert_away_from_round_boundary(
        _pure_scaled_coefficients(img, quality=50, bs=8)
    )
    disp_blocks, disp_shape, disp_qt = jpeg.op(img, quality=50)
    monkeypatch.setattr(_native, "HAS_NATIVE", False)  # force pure path
    pure_blocks, pure_shape, pure_qt = jpeg.op(img, quality=50)
    assert disp_shape == pure_shape == (16, 24)
    assert disp_qt == pure_qt
    assert disp_blocks == pure_blocks


def test_jpeg_decode_native_matches_pure(monkeypatch):
    """The c_dispatched decode (srmech_jpeg_decode_f64) matches the forced-pure
    block-DCT cascade on the reconstructed image to reldiff ≤ 1e-9."""
    img = _rand_image(24, 16, seed=99)
    enc = jpeg.op(img, quality=80)
    disp = jpeg.op(enc, decode=True)
    monkeypatch.setattr(_native, "HAS_NATIVE", False)  # force pure path
    pure = jpeg.op(enc, decode=True)
    assert _reldiff_2d(pure, disp) < 1e-9, "jpeg decode native!=pure"


def test_jpeg_roundtrip_native_equals_pure_roundtrip(monkeypatch):
    """End-to-end: the fully-dispatched round-trip equals the fully-pure
    round-trip within tol (encode integers equal away from boundaries + decode
    within-tol ⇒ the composition is within-tol)."""
    img = _rand_image(16, 16, seed=42)
    _assert_away_from_round_boundary(
        _pure_scaled_coefficients(img, quality=60, bs=8)
    )
    enc_d = jpeg.op(img, quality=60)
    rec_d = jpeg.op(enc_d, decode=True)
    monkeypatch.setattr(_native, "HAS_NATIVE", False)
    enc_p = jpeg.op(img, quality=60)
    rec_p = jpeg.op(enc_p, decode=True)
    assert enc_d[0] == enc_p[0]
    assert _reldiff_2d(rec_p, rec_d) < 1e-9, "jpeg roundtrip native!=pure"


def test_jpeg_explicit_quant_table_and_bs4_native_matches_pure(monkeypatch):
    """The explicit quant_table + non-canonical block_size=4 path also
    dispatches + matches pure (integers exact away from boundaries; decode
    within-tol)."""
    bs = 4
    qt = [[2.0, 3.0, 5.0, 7.0],
          [3.0, 4.0, 6.0, 8.0],
          [5.0, 6.0, 9.0, 11.0],
          [7.0, 8.0, 11.0, 13.0]]
    img = _rand_image(12, 8, seed=7)
    disp_blocks, disp_shape, _ = jpeg.op(img, quant_table=qt, block_size=bs)
    dec_in = (disp_blocks, disp_shape, qt)
    disp_rec = jpeg.op(dec_in, decode=True, block_size=bs)
    monkeypatch.setattr(_native, "HAS_NATIVE", False)  # force pure path
    pure_blocks, pure_shape, _ = jpeg.op(img, quant_table=qt, block_size=bs)
    pure_rec = jpeg.op(dec_in, decode=True, block_size=bs)
    assert disp_shape == pure_shape == (12, 8)
    assert disp_blocks == pure_blocks
    assert _reldiff_2d(pure_rec, disp_rec) < 1e-9


def test_jpeg_bs4_quality_table_submatrix_native_matches_pure(monkeypatch):
    """block_size=4 with a QUALITY-derived table: the pure per-block path
    indexes the TOP-LEFT 4×4 submatrix of the 8×8 Wallace table, so the native
    path must flatten that same submatrix (row stride bs, not 8) — the rc213
    stride-regression guard."""
    bs = 4
    img = _rand_image(8, 12, seed=17)
    disp_blocks, disp_shape, disp_qt = jpeg.op(img, quality=70, block_size=bs)
    disp_rec = jpeg.op((disp_blocks, disp_shape, disp_qt), decode=True,
                       block_size=bs)
    monkeypatch.setattr(_native, "HAS_NATIVE", False)  # force pure path
    pure_blocks, pure_shape, pure_qt = jpeg.op(img, quality=70, block_size=bs)
    pure_rec = jpeg.op((pure_blocks, pure_shape, pure_qt), decode=True,
                       block_size=bs)
    assert disp_shape == pure_shape == (8, 12)
    assert disp_qt == pure_qt
    assert disp_blocks == pure_blocks
    assert _reldiff_2d(pure_rec, disp_rec) < 1e-9


def test_native_wrapper_declines_cleanly_when_absent(monkeypatch):
    """With native forced off, the wrappers return None (the dispatch contract:
    the caller falls back to the complete pure cascade — never an exception)."""
    monkeypatch.setattr(_native, "HAS_NATIVE", False)
    assert _native.has_native_jpeg_f64() is False
    assert _native.jpeg_encode_f64_c([0.0] * 64, 8, 8, [0.0] * 64,
                                     [1.0] * 64, 8) is None
    assert _native.jpeg_decode_f64_c([0.0] * 64, 1, 1, [0.0] * 64,
                                     [1.0] * 64, 8) is None
