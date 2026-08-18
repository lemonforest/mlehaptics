"""Path A JPEG-like compression — closed-form DCT + Class K threshold + Class B TLV.

Identity per the implementation plan §1: JPEG (lossy block-wise compression)
IS a Class L (DCT-II eigenbasis projection on 8x8 blocks) ∘ Class K (threshold
quantisation) ∘ Class B (TLV byte-canonical form on quantised coefficients)
composition.

The closed-form reference ships the JPEG core algebra (block-wise DCT-II,
uniform quantisation, zigzag/TLV packing) without entropy-coding (which is
Huffman, the separate Phase 2 op). Decode reverses the chain.

rc213 (#753) classification: ``c_dispatched``.  jpeg was deferred at rc144/B6b
out of the exact coder batch as a float-DCT NUMERIC op, then reached C only as
a rc155 ``composition_of_c`` (each block's DCT riding :func:`dct.op` →
``mat_matmul`` — 4 Python-glue dispatches PER BLOCK, rebuilding the cosine
basis per call).  It now has its dedicated numeric C peer: ``op`` dispatches
the WHOLE blocked pipeline — strided block extract → separable 2-D DCT-II over
the caller-built cosine basis → Class-K round-half-even quantise (encode), and
dequantise → 2-D DCT-III → ``1/(2·bs)²`` normalise (decode) — to
``srmech_jpeg_encode_f64`` / ``srmech_jpeg_decode_f64`` (via
``_native.jpeg_{encode,decode}_f64_c``; ONE ctypes crossing for the whole
image) when the native lib is present, and falls back to the complete
numpy-free pure block-DCT cascade below otherwise.  The bases + quant table
stay caller data built once through the byte-exact Class-N ``rational.cos``
cascade (:func:`dct._dct_matrix` — the SAME basis the pure path uses), the
rc149 ``iir`` taps precedent.  NUMERIC (within-tol, not byte-identical): the
stage accumulations may FMA-fuse ~1 ULP on some platforms, so the parity
contract is differential (reldiff ≤ 1e-9 on the reconstructed image; the
quantised integers agree exactly away from rounding boundaries), the F1-FFT /
F2-SVD / B4 numeric-foundation contract.  The sibling Huffman entropy coder
stays the separate c_dispatched op (``srmech_huffman_build_codes``) for the
callers that add it.

Carrier-removal #564 (rc111): numpy-FREE — the last clean DSP carrier flip.
The block transform already runs numpy-free through :func:`dct.op` (rc104,
returns a list-of-lists); jpeg now carries the 2-D image as nested Python
``list``s end-to-end. The quantisation table is a plain list-of-lists, the
Wallace quality scaling is per-element (``int(...)`` is exact floor for the
non-negative ``(luma·scale + 50)/100``), the Class-K quantise is
``round(coeff / qt)`` (Python ``round`` is round-half-to-even — bit-identical
to ``np.round``), and the encode/decode block loops index nested lists
directly. Inputs coerce numpy-free via ``tolist()``; encode returns
list-of-list-of-lists blocks, decode returns a 2-D ``list``. No top-level
``import numpy``. Value-faithful to the prior matrix path (the DCT basis is the
Class-N ``rational.cos`` cascade, value-faithful to ~1e-9).

Path B dual in Phase 6 (Path B DCT + threshold + TLV in bound-vector
pipeline).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Wallace
(1991) + Pennebaker & Mitchell (1993) *JPEG Still Image Data Compression
Standard*.
"""

from __future__ import annotations

from typing import List, Optional

from .dct import op as dct_op

OPERATION_NAME = "jpeg"
CLASS_COMPOSITION = ("L", "K", "B")
PERFORMANCE_HINT = "shallow-cascade-block-amortise"
SSOT_CITATION = (
    "Wallace (1991), 'The JPEG still picture compression standard', Commun. "
    "ACM 34(4), 30-44. DOI 10.1145/103085.103089 (Crossref). Pennebaker & "
    "Mitchell (1993), 'JPEG Still Image Data Compression Standard', Van "
    "Nostrand Reinhold."
)


# Canonical JPEG luminance quantisation table (Annex K, Table K.1) — plain
# list-of-lists (numpy-free, #564).
_JPEG_LUMA_QUANT: List[List[float]] = [
    [16.0, 11.0, 10.0, 16.0, 24.0, 40.0, 51.0, 61.0],
    [12.0, 12.0, 14.0, 19.0, 26.0, 58.0, 60.0, 55.0],
    [14.0, 13.0, 16.0, 24.0, 40.0, 57.0, 69.0, 56.0],
    [14.0, 17.0, 22.0, 29.0, 51.0, 87.0, 80.0, 62.0],
    [18.0, 22.0, 37.0, 56.0, 68.0, 109.0, 103.0, 77.0],
    [24.0, 35.0, 55.0, 64.0, 81.0, 104.0, 113.0, 92.0],
    [49.0, 64.0, 78.0, 87.0, 103.0, 121.0, 120.0, 101.0],
    [72.0, 92.0, 95.0, 98.0, 112.0, 100.0, 103.0, 99.0],
]


def _as_rows(arr) -> List[list]:
    """Coerce an array-like to a list-of-rows numpy-free (``tolist()`` covers
    ndarray AND ``Mat``)."""
    return arr.tolist() if hasattr(arr, "tolist") else [list(r) for r in arr]


def _qt_flat_bs(qt, bs) -> Optional[List[float]]:
    """Flatten the TOP-LEFT ``bs×bs`` submatrix of the quant table (the pure
    per-block path indexes ``qt[r][c]`` for ``r, c < bs``, so a ``bs < 8``
    block size uses the top-left corner of the 8×8 Wallace table). ``None``
    when the table is smaller than ``bs`` — the native path declines and the
    pure path raises its usual ``IndexError`` (behaviour parity)."""
    if len(qt) < bs or any(len(row) < bs for row in qt):
        return None
    return [float(qt[r][c]) for r in range(bs) for c in range(bs)]


def _native_encode(img, h, w, qt, bs):
    """Dispatch the whole encode pipeline to the c_dispatched
    ``srmech_jpeg_encode_f64`` (rc213) — returns the quantised-blocks list (of
    ``bs×bs`` integer list-of-lists) or ``None`` (caller runs the pure path).
    The DCT-II basis is built ONCE through the byte-exact Class-N
    ``rational.cos`` cascade (the SAME basis the pure per-block path uses)."""
    from srmech import _native

    if not _native.has_native_jpeg_f64():
        return None
    from .dct import _dct_matrix

    qt_flat = _qt_flat_bs(qt, bs)
    if qt_flat is None:
        return None
    basis2 = [v for row in _dct_matrix(bs, 2) for v in row]
    img_flat = [v for row in img for v in row]
    flat = _native.jpeg_encode_f64_c(img_flat, h, w, basis2, qt_flat, bs)
    if flat is None:
        return None
    bh = h // bs
    bw = w // bs
    blocks: List[List[List[int]]] = []
    for t in range(bh * bw):
        base = t * bs * bs
        blocks.append(
            [
                [int(flat[base + r * bs + c]) for c in range(bs)]
                for r in range(bs)
            ]
        )
    return blocks


def _native_decode(quant_blocks, bh, bw, qt, bs):
    """Dispatch the whole decode pipeline to the c_dispatched
    ``srmech_jpeg_decode_f64`` (rc213) — returns the reconstructed 2-D image
    ``list`` or ``None`` (caller runs the pure path)."""
    from srmech import _native

    if not _native.has_native_jpeg_f64():
        return None
    from .dct import _dct_matrix

    qt_flat = _qt_flat_bs(qt, bs)
    if qt_flat is None:
        return None
    basis3 = [v for row in _dct_matrix(bs, 3) for v in row]
    q_flat: List[float] = []
    for t in range(bh * bw):
        qb = _as_rows(quant_blocks[t])
        for r in range(bs):
            for c in range(bs):
                q_flat.append(float(qb[r][c]))
    flat = _native.jpeg_decode_f64_c(q_flat, bh, bw, basis3, qt_flat, bs)
    if flat is None:
        return None
    width = bw * bs
    return [
        [flat[r * width + c] for c in range(width)] for r in range(bh * bs)
    ]


def _quant_table(quality: int, quant_table) -> List[List[float]]:
    """Build the 8x8 quantisation matrix."""
    if quant_table is not None:
        return [[float(v) for v in r] for r in _as_rows(quant_table)]
    # Wallace scaling factor.
    scale = 5000.0 / quality if quality < 50 else 200.0 - 2.0 * quality
    # Per-element floor: `(luma·scale + 50)/100` is non-negative, so `int(...)`
    # truncates == floors (matches np.floor); floored to a minimum of 1.0.
    return [
        [max(float(int((v * scale + 50.0) / 100.0)), 1.0) for v in row]
        for row in _JPEG_LUMA_QUANT
    ]


def op(
    image,
    *,
    decode: bool = False,
    quality: int = 50,
    quant_table: Optional[list] = None,
    block_size: int = 8,
    D: int = 8192,
):
    """JPEG-like block-DCT compression / decompression on a 2-D image.

    Parameters
    ----------
    image:
        Encode: 2-D real array (grayscale image). Decode: tuple
        ``(quantised_blocks, shape, quant_table)`` returned by encode.
    decode:
        If True, reverse the chain.
    quality:
        Quality factor 1-100 (Wallace scaling on the canonical table).
    quant_table:
        Optional explicit 8x8 quantisation matrix; overrides ``quality``.
    block_size:
        Block size. JPEG canonical is 8.
    D:
        Path B dimensionality (Path A unused).

    Returns
    -------
    Encode: ``(quantised_blocks, shape, quant_table)`` — ``quantised_blocks`` a
    ``list`` of ``block_size×block_size`` integer list-of-lists, ``quant_table``
    a list-of-lists (numpy-free, #564).
    Decode: 2-D real ``list`` recovering the input image.
    """
    bs = block_size

    if decode:
        quant_blocks, shape, qt_in = image
        qt = [[float(v) for v in r] for r in _as_rows(qt_in)]
        h, w = shape
        bh = h // bs
        bw = w // bs
        # c_dispatched: the whole blocked pipeline through
        # srmech_jpeg_decode_f64 (rc213); pure block-DCT cascade otherwise.
        native = _native_decode(quant_blocks, bh, bw, qt, bs)
        if native is not None:
            return native
        norm = 1.0 / (2.0 * bs) ** 2
        out = [[0.0] * (bw * bs) for _ in range(bh * bs)]
        for i in range(bh):
            for j in range(bw):
                qb = _as_rows(quant_blocks[i * bw + j])
                # Dequantise: multiply by quant_table (element-wise).
                dequant = [[qb[r][c] * qt[r][c] for c in range(bs)] for r in range(bs)]
                # Inverse DCT-II via DCT-III (closed-form Class L); dct_op is
                # numpy-free and returns a list-of-lists.
                recovered = dct_op(
                    dct_op(dequant, dct_type=3, axis=0), dct_type=3, axis=1
                )
                # Apply DCT-III normalisation (1/(2N)^2) into the output block.
                for r in range(bs):
                    orow = out[i * bs + r]
                    rrow = recovered[r]
                    base = j * bs
                    for c in range(bs):
                        orow[base + c] = rrow[c] * norm
        return out

    qt = _quant_table(quality, quant_table)
    rows = _as_rows(image)
    if not rows or not isinstance(rows[0], (list, tuple)):
        raise ValueError("jpeg encode expects a 2-D image")
    img = [[float(v) for v in r] for r in rows]
    h = len(img)
    w = len(img[0])
    if any(len(r) != w for r in img):
        raise ValueError("jpeg encode expects a rectangular 2-D image")
    # Truncate to a multiple of block_size.
    bh = h // bs
    bw = w // bs
    # c_dispatched: the whole blocked pipeline through srmech_jpeg_encode_f64
    # (rc213); pure block-DCT cascade otherwise.
    native = _native_encode(img, h, w, qt, bs)
    if native is not None:
        return native, (bh * bs, bw * bs), qt
    quant_blocks: List[List[List[int]]] = []
    for i in range(bh):
        for j in range(bw):
            block = [
                [img[i * bs + r][j * bs + c] for c in range(bs)] for r in range(bs)
            ]
            # Class L: DCT-II on rows then columns (numpy-free dct_op).
            block_dct = dct_op(
                dct_op(block, dct_type=2, axis=0), dct_type=2, axis=1
            )
            # Class K: quantise via element-wise division + round-half-to-even
            # (Python `round` matches np.round); store as Python ints.
            quantised = [
                [int(round(block_dct[r][c] / qt[r][c])) for c in range(bs)]
                for r in range(bs)
            ]
            quant_blocks.append(quantised)
    return quant_blocks, (bh * bs, bw * bs), qt
