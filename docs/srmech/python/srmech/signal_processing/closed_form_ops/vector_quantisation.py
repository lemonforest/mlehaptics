"""Path A vector quantisation — closed-form codebook lookup.

Identity per the implementation plan §1: VQ IS a Class E (codebook
sorted-key lookup) ∘ Class M (HDC similarity / Hamming for the nearest-
neighbour query) ∘ Class B (TLV byte-canonical form for the code-index
stream) composition.

The closed-form reference uses Euclidean distance to find the nearest
codebook entry for each input vector.

Carrier-removal #564 (rc105): numpy-FREE — the nearest-neighbour query is a
pure-Python argmin over the squared Euclidean distance ``Σ_j (x_j − c_j)²``
(the matmul cross-term trick is unnecessary for an argmin). Inputs coerce
numpy-free via ``tolist()``; encode returns ``list[int]``, decode returns a
list-of-rows. No top-level ``import numpy``.

Path B dual in Phase 6 (Path B codebook as bound-vector address space).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Linde,
Buzo & Gray (1980) LBG algorithm + Gersho & Gray (1992) *Vector
Quantization and Signal Compression*.
"""

from __future__ import annotations

from typing import List

OPERATION_NAME = "vector_quantisation"
CLASS_COMPOSITION = ("E", "M", "B")
PERFORMANCE_HINT = "shallow-cascade-codebook-amortise"
SSOT_CITATION = (
    "Linde, Buzo & Gray (1980), 'An algorithm for vector quantizer design', "
    "IEEE Trans. Commun. 28(1), 84-95. DOI 10.1109/TCOM.1980.1094577 "
    "(Crossref). Gersho & Gray (1992), 'Vector Quantization and Signal "
    "Compression', Kluwer Academic."
)


def _as_rows(a) -> List[List[float]]:
    """Coerce a 2-D array-like to a list-of-rows of float (numpy-free)."""
    raw = a.tolist() if hasattr(a, "tolist") else [list(r) for r in a]
    return [[float(x) for x in r] for r in raw]


def op(
    vectors,
    codebook,
    *,
    decode: bool = False,
    D: int = 8192,
):
    """Vector quantise ``vectors`` against ``codebook`` (numpy-free).

    Encode: returns a ``list[int]`` of codebook indices (one per input vector).
    Decode: returns the reconstructed vectors (``[codebook[i] for i in idx]``).

    Parameters
    ----------
    vectors:
        Encode: ``(n_vec, d)`` array of input vectors (a single ``(d,)`` vector
        is accepted and treated as one row). Decode: array of integer indices.
    codebook:
        ``(n_codes, d)`` array of codebook entries.
    decode:
        If True, return ``codebook[vectors]`` instead of computing indices.
    D:
        Path B dimensionality (Path A unused).

    Returns
    -------
    Encode: ``list[int]`` of length ``n_vec``.
    Decode: list-of-rows ``(n_vec, d)`` of reconstructed vectors.
    """
    cb = _as_rows(codebook)
    if not cb:
        raise ValueError("codebook must be non-empty 2-D")
    d = len(cb[0])

    if decode:
        idx_raw = vectors.tolist() if hasattr(vectors, "tolist") else list(vectors)
        return [list(cb[int(i)]) for i in idx_raw]

    raw = vectors.tolist() if hasattr(vectors, "tolist") else list(vectors)
    if not raw:
        return []
    # Accept a single 1-D vector as one row.
    rows = [[float(x) for x in raw]] if not isinstance(raw[0], (list, tuple)) else _as_rows(raw)
    for r in rows:
        if len(r) != d:
            raise ValueError(
                f"vector dimension {len(r)} != codebook dimension {d}"
            )

    # Class E codebook lookup via Class M nearest-neighbour: argmin of the
    # squared Euclidean distance (no sqrt needed; argmin is invariant under it).
    out: List[int] = []
    for x in rows:
        best_k = 0
        best = None
        for k, c in enumerate(cb):
            dist = 0.0
            for j in range(d):
                diff = x[j] - c[j]
                dist += diff * diff
            if best is None or dist < best:
                best = dist
                best_k = k
        out.append(best_k)
    return out
