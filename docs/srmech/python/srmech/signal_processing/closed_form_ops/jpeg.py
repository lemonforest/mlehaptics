"""Path A JPEG-like compression — closed-form DCT + Class K threshold + Class B TLV.

Identity per the implementation plan §1: JPEG (lossy block-wise compression)
IS a Class L (DCT-II eigenbasis projection on 8x8 blocks) ∘ Class K (threshold
quantisation) ∘ Class B (TLV byte-canonical form on quantised coefficients)
composition.

The closed-form reference ships the JPEG core algebra (block-wise DCT-II,
uniform quantisation, zigzag/TLV packing) without entropy-coding (which is
Huffman, the separate Phase 2 op). Decode reverses the chain.

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


def _quant_table(quality: int, quant_table) -> List[List[float]]:
    """Build the 8x8 quantisation matrix (numpy-free)."""
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
