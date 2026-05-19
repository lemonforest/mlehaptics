"""Path A JPEG-like compression — closed-form DCT + Class K threshold + Class B TLV.

Identity per the implementation plan §1: JPEG (lossy block-wise compression)
IS a Class L (DCT-II eigenbasis projection on 8x8 blocks) ∘ Class K (threshold
quantisation) ∘ Class B (TLV byte-canonical form on quantised coefficients)
composition.

The closed-form reference ships the JPEG core algebra (block-wise DCT-II,
uniform quantisation, zigzag/TLV packing) without entropy-coding (which is
Huffman, the separate Phase 2 op). Decode reverses the chain.

Path B dual in Phase 6 (Path B DCT + threshold + TLV in bound-vector
pipeline).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Wallace
(1991) + Pennebaker & Mitchell (1993) *JPEG Still Image Data Compression
Standard*.
"""

from __future__ import annotations

from typing import Optional, Tuple

import numpy as np

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


# Canonical JPEG luminance quantisation table (Annex K, Table K.1).
_JPEG_LUMA_QUANT = np.array(
    [
        [16, 11, 10, 16, 24, 40, 51, 61],
        [12, 12, 14, 19, 26, 58, 60, 55],
        [14, 13, 16, 24, 40, 57, 69, 56],
        [14, 17, 22, 29, 51, 87, 80, 62],
        [18, 22, 37, 56, 68, 109, 103, 77],
        [24, 35, 55, 64, 81, 104, 113, 92],
        [49, 64, 78, 87, 103, 121, 120, 101],
        [72, 92, 95, 98, 112, 100, 103, 99],
    ],
    dtype=np.float64,
)


def op(
    image,
    *,
    decode: bool = False,
    quality: int = 50,
    quant_table: Optional[np.ndarray] = None,
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
    Encode: ``(quantised_blocks, shape, quant_table)``.
    Decode: 2-D real array recovering the input image.
    """
    if quant_table is None:
        # Wallace scaling factor
        scale = 5000.0 / quality if quality < 50 else 200.0 - 2.0 * quality
        qt = np.maximum(np.floor((_JPEG_LUMA_QUANT * scale + 50.0) / 100.0), 1.0)
    else:
        qt = np.asarray(quant_table, dtype=np.float64)

    if decode:
        quant_blocks, shape, qt_in = image
        qt = np.asarray(qt_in, dtype=np.float64)
        h, w = shape
        bh = h // block_size
        bw = w // block_size
        out = np.zeros((bh * block_size, bw * block_size), dtype=np.float64)
        for i in range(bh):
            for j in range(bw):
                qb = quant_blocks[i * bw + j]
                # Dequantise: multiply by quant_table
                dequant = qb * qt
                # Inverse DCT-II via DCT-III (closed-form Class L)
                block_recovered = dct_op(dct_op(dequant, dct_type=3, axis=0),
                                          dct_type=3, axis=1)
                # Apply DCT-III normalization (1/(2N))
                norm = 1.0 / (2.0 * block_size) ** 2
                out[
                    i * block_size : (i + 1) * block_size,
                    j * block_size : (j + 1) * block_size,
                ] = block_recovered * norm
        return out

    img = np.asarray(image, dtype=np.float64)
    if img.ndim != 2:
        raise ValueError(f"jpeg encode expects 2-D image; got {img.shape}")
    h, w = img.shape
    # Truncate to multiple of block_size.
    bh = h // block_size
    bw = w // block_size
    quant_blocks = []
    for i in range(bh):
        for j in range(bw):
            block = img[
                i * block_size : (i + 1) * block_size,
                j * block_size : (j + 1) * block_size,
            ]
            # Class L: DCT-II on rows then columns
            block_dct = dct_op(dct_op(block, dct_type=2, axis=0), dct_type=2, axis=1)
            # Class K: quantise via element-wise division + rounding
            quantised = np.round(block_dct / qt).astype(np.int32)
            quant_blocks.append(quantised)
    return quant_blocks, (bh * block_size, bw * block_size), qt
