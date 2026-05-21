"""Path B HDC truncation — Class K asymptotic-DOF ∘ Class M bundle ∘ Class N gate.

Identity per ``[[user_stance_rotation_is_class_k_pin_slot]]`` + Spike #117
sparse-coding anchor + Spike #179 T6 anchor: HDC truncation IS a Class M
(bundle / majority across vectors) ∘ Class K (asymptotic-DOF threshold-
gate; pin-slot at the substrate-natural sparsity rate) ∘ Class N
(rational substrate-natural threshold) composition.

Spike #117 sparse-coding anchor: HDC bundle truncation preserves
similarity-of-content above the substrate-natural sparsity threshold
``D/N`` where N is the active-channel count.

Spike #179 T6 anchor: bit-exact recovery preserved at threshold rate
≥ D/18 (the substrate-natural sparsity rate for the canonical HDC
substrate; per ``[[user_stance_substrate_natural_encoding_is_shadow_projection]]``
the threshold IS Class N rational at the substrate's natural sparsity).

Path A dual: :func:`srmech.signal_processing.closed_form_ops.hdc_truncation.op`
(Class M bundle then Class K ordinal-position sparse truncate). Both
paths IS the same algebra per
``[[user_stance_identity_not_implementation_discipline]]``; bit-exact D1
algebra-identity for the canonical bundle-and-truncate path on
substrate-natural inputs.

The Path B-native form composes directly with Phase 3's
:mod:`srmech.signal_processing.rbs_hdc_instrument` since HDC bundle /
permute / bind are already Path B-native primitives. The Class N
substrate-natural threshold rate ``D/gcd(stride, D)`` (per Spike #176
T8) provides the asymptotic-DOF gate.

Trauma-informed defensive scope: methodology-research / educational
framing only.

Canonical SSoT
--------------
- Kanerva (2009), 'Hyperdimensional computing: An introduction to
  computing in distributed representation with high-dimensional random
  vectors', Cognitive Computation 1, 139-159. DOI 10.1007/s12559-009-
  9009-8.
- Plate (1995), *Holographic Reduced Representations*, IEEE TNN 6, 623.
- Rachkovskij (2001), Neural Comput. Appl. 9, 322 — sparse distributed
  codes.
- Spike #117 — HDC sparse-truncate anchor.
- Spike #179 T6 — bit-exact recovery at substrate-natural sparsity rate.
"""

from __future__ import annotations

from typing import Optional, Sequence

OPERATION_NAME = "hdc_truncation"
CLASS_COMPOSITION = ("K", "M", "N")
PERFORMANCE_HINT = "single-token-fast"
SSOT_CITATION = (
    "Kanerva (2009), 'Hyperdimensional computing: An introduction to "
    "computing in distributed representation with high-dimensional "
    "random vectors', Cognitive Computation 1, 139-159. DOI 10.1007/"
    "s12559-009-9009-8 (Crossref). Spike #117 sparse-truncate anchor. "
    "Spike #179 T6 — bit-exact recovery at substrate-natural sparsity "
    "rate (anchored)."
)


def op(
    vectors: Sequence[bytes],
    *,
    truncate_popcount: Optional[int] = None,
    D: int = 8192,
    substrate: str = "cyclic",
) -> bytes:
    """Path B HDC bundle + Class K asymptotic-DOF truncate.

    Class M side: HDC bundle (majority across odd vector count) per
    Kanerva 2009. Class K side: sparse-truncate to ``truncate_popcount``
    bits via ordinal-position threshold (Spike #117 anchor; the Class K
    pin-slot acts at the sparsity-rate threshold).

    On substrate-natural inputs the Path B output is D1 algebra-
    identical to Path A's reference. Per Spike #179 T6 anchor, the
    bit-exact recovery threshold lives at the substrate-natural
    sparsity rate (≥ D/18 for the canonical RBS-HDC substrate).

    Parameters
    ----------
    vectors:
        Sequence of BSC vectors (all same length, odd count).
    truncate_popcount:
        Target number of set bits in the output. None -> no truncation
        (raw Class M bundle output).
    D:
        Path B dimensionality hint (default 8192). Used by downstream
        cascade-composition only; the actual bundle length is the
        inherent vector byte-length × 8.
    substrate:
        Substrate label hint. Accepted for API consistency.

    Returns
    -------
    bytes
        Bundled (and optionally truncated) vector. D1 algebra-identical
        to :func:`srmech.signal_processing.closed_form_ops.hdc_truncation.op`.
    """
    from srmech.amsc.hdc import bundle as hdc_bundle

    # Class M side: HDC bundle is Path B-native (Phase 3 surface).
    bundled = hdc_bundle(vectors)
    if truncate_popcount is None:
        return bundled

    # Class K asymptotic-DOF threshold gate: keep the first
    # ``truncate_popcount`` set bits when iterating in byte order. This
    # IS the Class K pin-slot at the substrate-natural sparsity rate
    # per Spike #117 + Spike #179 T6 anchors. On BSC bits the
    # ordinal-position truncate IS the algebra-content threshold (no
    # magnitude information to threshold on; per
    # ``[[user_stance_substrate_natural_encoding_is_shadow_projection]]``
    # the substrate IS bit-discrete).
    out = bytearray(len(bundled))
    kept = 0
    for byte_i, byte_val in enumerate(bundled):
        for bit in range(8):
            if (byte_val >> bit) & 1:
                if kept < truncate_popcount:
                    out[byte_i] |= 1 << bit
                    kept += 1
    return bytes(out)


def _register() -> None:
    """Register Path B HDC truncation with the dispatcher's path_registry."""
    from srmech.signal_processing.path_registry import register
    from srmech.signal_processing._paths import PATH_A, PATH_B
    from srmech.signal_processing.closed_form_ops.hdc_truncation import (
        op as path_a_hdc_truncation,
    )

    register(
        OPERATION_NAME,
        path=PATH_A,
        impl=path_a_hdc_truncation,
        ssot_citation=SSOT_CITATION,
        classes=CLASS_COMPOSITION,
    )
    register(
        OPERATION_NAME,
        path=PATH_B,
        impl=op,
        ssot_citation=SSOT_CITATION,
        classes=CLASS_COMPOSITION,
    )


_register()
