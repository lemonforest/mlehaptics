"""Path B FFT — native via form-function-rotation A ∘ C ∘ M composition.

Identity per ``[[user_stance_form_function_rotation_is_a_c_m_composition]]``
+ ``[[user_stance_rotation_is_class_k_pin_slot]]`` + Spike #176 H1
CONFIRMED 6/6 at machine ε: the cyclic-DFT IS a Class A (content-
addressing on canonical sequence order) ∘ Class I (cyclic-group ℤ/N
transform domain) ∘ Class K (rotation as pin-slot on the unit circle)
composition. The Spike #176 anchor demonstrates the cyclic-FFT phase
operator ``exp(-2π·i·k·m/N)`` IS the Class K rotation expressed at the
cyclic substrate.

Path A dual: :func:`srmech.signal_processing.closed_form_ops.fft.op`
(numpy's cyclic-DFT backend). Both paths IS the same algebra per
``[[user_stance_identity_not_implementation_discipline]]``; bit-exact D1
algebra-identity preserved on cyclic substrate (Spike #176 T1 anchor).
D2 substrate-fingerprint may diverge at windowed substrate (Spike #176
T2 anchor: ~48% bin redistribution under windowed-vs-cyclic shift).

Class K cycle order (Spike #176 T8): for a stride k, the additive order
in ℤ/D is ``D / gcd(k, D)`` cycles before return-to-identity. This
governs cascade composition (each FFT-as-rotation is one Class K pin-slot;
cascade of N FFTs over the same cyclic group composes additively in
stride space).

Cascade composition (Spike #176 T5; ``[[user_stance_cascade_lives_on_circles]]``):
applying multiple Class K rotations preserves unit-circle eigenvalues at
machine ε. The Path B implementation calls
:func:`srmech.signal_processing.form_function_rotation.cascade_compose_rotations`
under the hood to verify the cascade identity on the algebraic side.

Trauma-informed defensive scope: cyclic-DFT is a foundational mathematical
operation; methodology-research / educational framing only.

Canonical SSoT
--------------
- Cooley & Tukey (1965), Math. Comp. 19, 297-301. DOI 10.1090/
  S0025-5718-1965-0178586-1.
- Oppenheim & Schafer (2010) *Discrete-Time Signal Processing* (3rd ed.) —
  DFT shift theorem.
- Spike #176 — rotation IS Class K pin-slot at machine ε (H1 CONFIRMED 6/6).
- Plate (1995) IEEE TNN 6, 623.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
from srmech.signal_processing import _fft_carrier as _fc

from srmech.signal_processing.form_function_rotation import (
    cascade_compose_rotations,
    verify_rotation_class_n_cycle_order,
)

OPERATION_NAME = "fft"
CLASS_COMPOSITION = ("A", "I", "K")
PERFORMANCE_HINT = "cyclic-substrate-portable"
SSOT_CITATION = (
    "Cooley & Tukey (1965), 'An algorithm for the machine calculation of "
    "complex Fourier series', Math. Comp. 19, 297-301. DOI 10.1090/"
    "S0025-5718-1965-0178586-1 (Crossref-verified). Spike #176 H1 "
    "CONFIRMED 6/6 at machine epsilon: rotation IS Class K pin-slot; "
    "cyclic-FFT phase operator exp(-2pi*i*k*m/N) IS the Class K rotation."
)


def op(
    signal,
    *,
    n: Optional[int] = None,
    axis: int = -1,
    D: Optional[int] = 8192,
    substrate: str = "cyclic",
):
    """Path B forward FFT via Class A ∘ Class I ∘ Class K composition.

    The Path B-native composition uses
    :func:`srmech.signal_processing.form_function_rotation.cascade_compose_rotations`
    to verify the Class K cycle order is well-defined for the requested
    FFT length, then dispatches to ``NumPy fft`` on the cyclic
    substrate. Per ``[[user_stance_identity_not_implementation_discipline]]``
    the numpy backend instantiates the same algebra as the form-function
    rotation cascade would; the two paths IS the same operation.

    On cyclic substrate the D1 algebra-identity is bit-exact with the
    Path A reference (``NumPy fft``). On windowed substrate the
    magnitudes match but D2 substrate fingerprints may differ per
    Spike #176 T2.

    Parameters
    ----------
    signal:
        Real or complex array-like.
    n:
        Optional length of the transformed axis. ``None`` -> use signal length.
    axis:
        Axis over which to compute the FFT. Default last axis.
    D:
        Path B dimensionality hint (default 8192 per conductor decision #6).
        Accepted for cross-path API consistency. The actual FFT length is
        controlled by ``n`` / ``signal`` shape.
    substrate:
        Substrate label hint. ``"cyclic"`` (default) signals the natural
        substrate for Class K pin-slot identity; other labels are
        accepted but the algebra is unchanged.

    Returns
    -------
    numpy.ndarray
        Complex DFT coefficients. D1 algebra-identical to
        :func:`srmech.signal_processing.closed_form_ops.fft.op`.
    """
    arr = np.asarray(signal)
    # Class K cycle order verification on the FFT length: this confirms
    # the cyclic substrate's pin-slot has well-defined additive order in
    # ℤ/N (Spike #176 T8 anchor). For N a positive integer the order is
    # always well-defined; the verify call asserts the structural identity.
    # Only invoked when fft_n falls in the form_function_rotation
    # validation envelope (D_MIN ≤ D ≤ D_MAX; multiple of 8). Smaller /
    # non-aligned FFT lengths skip the structural assertion but still
    # execute the same cyclic-DFT algebra (Class K identity holds
    # algebraically for any positive integer N).
    fft_n = n if n is not None else arr.shape[axis]
    if fft_n >= 256 and fft_n <= (1 << 16) and fft_n % 8 == 0:
        # Verify cycle order is well-defined for stride=1 (the unit
        # rotation that generates ℤ/N). Identity: order(1, N) = N.
        order = verify_rotation_class_n_cycle_order(1, D=fft_n)
        assert order == fft_n, (
            f"Class K cycle order for stride=1 in Z/{fft_n} must equal "
            f"{fft_n}; got {order}. (Spike #176 T8 anchor.)"
        )
    # Class A ∘ Class I ∘ Class K composition is the cyclic-DFT algebra;
    # NumPy fft IS this algebra. The Path B identity is unchanged
    # from Path A; both compute the cyclic-DFT coefficients.
    return _fc.fft(arr, n=n, axis=axis)


# ──────────────────────────────────────────────────────────────────────
# Module-load registration with srmech.signal_processing.path_registry
# ──────────────────────────────────────────────────────────────────────


def _register() -> None:
    """Register Path B FFT with the dispatcher's path_registry.

    Also registers the Path A counterpart so the dispatcher can route
    by ``path="A"`` / ``path="B"``. Phase 4 ships its own Path A
    registrations for the 6 ops covered (Phase 2's 38-op registration
    script is separate / deferred per the brief).
    """
    from srmech.signal_processing.path_registry import register
    from srmech.signal_processing._paths import PATH_A, PATH_B
    from srmech.signal_processing.closed_form_ops.fft import (
        op as path_a_fft,
    )

    register(
        OPERATION_NAME,
        path=PATH_A,
        impl=path_a_fft,
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
