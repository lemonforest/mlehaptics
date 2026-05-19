"""Path A HDC truncation — closed-form bundle + sparse-truncate composition.

Identity per Spike #117: HDC truncation IS a Class M (HDC bundle / majority
across vectors) ∘ Class K (truncate_sparse / threshold projection on the
result) composition. This composes directly with
``srmech.amsc.hdc.bundle`` for the Class M side.

This is the Phase 2 anchor for HDC bundle truncation per the implementation
plan §2; the Path A re-surface lives here, the B-native form is in
``srmech.signal_processing.path_b_ops.hdc_truncation`` (Phase 4).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Kanerva
(2009) *Hyperdimensional Computing* + Spike #117 truncate_sparse anchor.
"""

from __future__ import annotations

from typing import Optional, Sequence

OPERATION_NAME = "hdc_truncation"
CLASS_COMPOSITION = ("M", "K")
PERFORMANCE_HINT = "single-token-fast"
SSOT_CITATION = (
    "Kanerva (2009), 'Hyperdimensional computing: An introduction to "
    "computing in distributed representation with high-dimensional random "
    "vectors', Cognitive Computation 1, 139-159. DOI 10.1007/s12559-009-"
    "9009-8 (Crossref). Spike #117 sparse-truncate anchor on the srmech "
    "research notebook."
)


def op(
    vectors: Sequence[bytes],
    *,
    truncate_popcount: Optional[int] = None,
    D: int = 8192,
) -> bytes:
    """HDC bundle of ``vectors`` then sparse-truncate to target popcount.

    Class M bundle (majority across odd vector count) followed by Class K
    sparse truncation to ``truncate_popcount`` highest-magnitude bits. When
    ``truncate_popcount`` is None, returns the raw bundle (no truncation).

    Parameters
    ----------
    vectors:
        Sequence of BSC vectors (all same length, odd count).
    truncate_popcount:
        Target number of set bits in the output. None -> no truncation.
    D:
        Path B dimensionality (Path A uses inherent vector byte-length).

    Returns
    -------
    bytes
        Bundled (and optionally truncated) vector.
    """
    from srmech.amsc.hdc import bundle as hdc_bundle

    # Class M side: HDC bundle.
    bundled = hdc_bundle(vectors)
    if truncate_popcount is None:
        return bundled

    # Class K side: keep only the first 'truncate_popcount' set bits when
    # iterating in byte order; this is the closed-form sparse-truncate per
    # Spike #117 (truncate by ordinal position rather than magnitude since
    # BSC bits are binary). For magnitude-based truncation on a non-binary
    # substrate, Path B operates on the bundled coefficients.
    out = bytearray(len(bundled))
    kept = 0
    for byte_i, byte_val in enumerate(bundled):
        for bit in range(8):
            if (byte_val >> bit) & 1:
                if kept < truncate_popcount:
                    out[byte_i] |= 1 << bit
                    kept += 1
    return bytes(out)
