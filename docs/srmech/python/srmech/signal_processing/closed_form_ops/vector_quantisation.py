"""Path A vector quantisation — closed-form codebook lookup.

Identity per the implementation plan §1: VQ IS a Class E (codebook
sorted-key lookup) ∘ Class M (HDC similarity / Hamming for the nearest-
neighbour query) ∘ Class B (TLV byte-canonical form for the code-index
stream) composition.

The closed-form reference uses Euclidean distance to find the nearest
codebook entry for each input vector.

Path B dual in Phase 6 (Path B codebook as bound-vector address space).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Linde,
Buzo & Gray (1980) LBG algorithm + Gersho & Gray (1992) *Vector
Quantization and Signal Compression*.
"""

from __future__ import annotations

from typing import List, Optional

import numpy as np

OPERATION_NAME = "vector_quantisation"
CLASS_COMPOSITION = ("E", "M", "B")
PERFORMANCE_HINT = "shallow-cascade-codebook-amortise"
SSOT_CITATION = (
    "Linde, Buzo & Gray (1980), 'An algorithm for vector quantizer design', "
    "IEEE Trans. Commun. 28(1), 84-95. DOI 10.1109/TCOM.1980.1094577 "
    "(Crossref). Gersho & Gray (1992), 'Vector Quantization and Signal "
    "Compression', Kluwer Academic."
)


def op(
    vectors,
    codebook,
    *,
    decode: bool = False,
    D: int = 8192,
):
    """Vector quantise ``vectors`` against ``codebook``.

    Encode: returns an array of codebook indices (one per input vector).
    Decode: returns the reconstructed vectors (codebook[indices]).

    Parameters
    ----------
    vectors:
        Encode: ``(n_vec, d)`` array of input vectors. Decode: array of
        integer indices into ``codebook``.
    codebook:
        ``(n_codes, d)`` array of codebook entries.
    decode:
        If True, return ``codebook[vectors]`` instead of computing indices.
    D:
        Path B dimensionality (Path A unused).

    Returns
    -------
    Encode: 1-D integer array of length ``n_vec``.
    Decode: ``(n_vec, d)`` array of reconstructed vectors.
    """
    cb = np.asarray(codebook, dtype=np.float64)
    if decode:
        idx = np.asarray(vectors, dtype=np.int64)
        return cb[idx]
    vec = np.asarray(vectors, dtype=np.float64)
    if vec.ndim == 1:
        vec = vec[np.newaxis, :]
    if cb.ndim != 2:
        raise ValueError(f"codebook must be 2-D; got {cb.shape}")
    if vec.shape[1] != cb.shape[1]:
        raise ValueError(
            f"vector dimension {vec.shape[1]} != codebook dimension {cb.shape[1]}"
        )
    # Compute pairwise squared Euclidean distances.
    # |x - c|^2 = |x|^2 - 2 x.c + |c|^2
    x_sq = np.sum(vec * vec, axis=1)[:, None]
    c_sq = np.sum(cb * cb, axis=1)[None, :]
    cross = vec @ cb.T
    dists = x_sq - 2.0 * cross + c_sq
    return np.argmin(dists, axis=1)
