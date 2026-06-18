"""Path B real-input FFT — half-spectrum native via A ∘ I ∘ K composition.

Real-input specialisation of
:func:`srmech.signal_processing.path_b_ops.fft.op`. For real ``signal``
the full DFT is Hermitian-symmetric (``X[N-k] = conj(X[k])``); ``rfft``
materialises only the non-redundant first ``N//2 + 1`` bins. Per
UPSTREAM_NOTES §1.1 (RBS-LM research subtree, surfaced by R-RBS-LM-49z):
49 Method B and similar bit-string FFT cascades take real input (bipolar
bits in {-1, +1}) and previously used the full ``fft`` at 2× compute and
2× memory. ``rfft`` closes that gap — **algebra-identical** on the
retained bins, not a correctness change (49z confirmed bit-identical
parity to bare numpy using the full FFT).

Identity per ``[[user_stance_form_function_rotation_is_a_c_m_composition]]``
+ ``[[user_stance_rotation_is_class_k_pin_slot]]`` + Spike #176 H1
CONFIRMED 6/6 at machine ε: the cyclic-DFT IS a Class A (content-
addressing on canonical sequence order) ∘ Class I (cyclic-group ℤ/N
transform domain) ∘ Class K (rotation as pin-slot on the unit circle)
composition. ``rfft`` is that composition on the **real-symmetric
half-substrate**: the Hermitian conjugate-symmetry ``X[N-k] = conj(X[k])``
IS the reflection the Class K pin-slot already encodes, so only the
independent half need be materialised.

Path A dual: :func:`srmech.signal_processing.closed_form_ops.rfft.op`
(numpy's real-input half-spectrum backend). Both paths IS the same
algebra per ``[[user_stance_identity_not_implementation_discipline]]``;
the rFFT bins equal the first ``N//2 + 1`` bins of the full FFT bit-
exact on the cyclic substrate.

Trauma-informed defensive scope: real-input DFT is a foundational
mathematical operation; methodology-research / educational framing only.

Canonical SSoT
--------------
- Cooley & Tukey (1965), Math. Comp. 19, 297-301. DOI 10.1090/
  S0025-5718-1965-0178586-1.
- Oppenheim & Schafer (2010) *Discrete-Time Signal Processing* (3rd ed.)
  §8.6 — real-sequence DFT symmetry.
- Spike #176 — rotation IS Class K pin-slot at machine ε (H1 CONFIRMED 6/6).
- UPSTREAM_NOTES §1.1 (RBS-LM) — documented rfft gap.
"""

from __future__ import annotations

from typing import Optional

from srmech.signal_processing import _fft_carrier as _fc

from srmech.signal_processing.form_function_rotation import (
    verify_rotation_class_n_cycle_order,
)

OPERATION_NAME = "rfft"
CLASS_COMPOSITION = ("A", "I", "K")
PERFORMANCE_HINT = "cyclic-substrate-portable-real-input"
SSOT_CITATION = (
    "Cooley & Tukey (1965), 'An algorithm for the machine calculation of "
    "complex Fourier series', Math. Comp. 19, 297-301. DOI 10.1090/"
    "S0025-5718-1965-0178586-1 (Crossref-verified). Real-input Hermitian "
    "half-spectrum per Oppenheim & Schafer (2010) DTSP (3rd ed.) §8.6. "
    "Spike #176 H1 CONFIRMED 6/6: rotation IS Class K pin-slot; the "
    "Hermitian conjugate-symmetry IS the pin-slot reflection."
)


def op(
    signal,
    *,
    n: Optional[int] = None,
    axis: int = -1,
    D: Optional[int] = 8192,
    substrate: str = "cyclic",
):
    """Path B forward rFFT via Class A ∘ Class I ∘ Class K on the real half.

    Verifies the Class K cycle order is well-defined for the FFT length
    (Spike #176 T8), then dispatches to ``NumPy rfft`` on the cyclic
    substrate. Per ``[[user_stance_identity_not_implementation_discipline]]``
    the numpy backend instantiates the same algebra the form-function
    rotation cascade would, restricted to the non-redundant half.

    On cyclic substrate the retained bins are bit-exact with the first
    ``N//2 + 1`` bins of the full Path B ``fft`` (and the Path A
    ``rfft`` reference).

    Parameters
    ----------
    signal:
        Real array-like.
    n:
        Optional length of the transformed axis. ``None`` -> use signal
        length. Output length along ``axis`` is ``n // 2 + 1``.
    axis:
        Axis over which to compute the rFFT. Default last axis.
    D:
        Path B dimensionality hint (default 8192). Accepted for cross-path
        API consistency; the FFT length is set by ``n`` / ``signal`` shape.
    substrate:
        Substrate label hint. ``"cyclic"`` (default) signals the natural
        substrate for the Class K pin-slot identity; other labels are
        accepted but the algebra is unchanged.

    Returns
    -------
    numpy.ndarray
        Complex half-spectrum DFT coefficients (bins ``0 .. N//2``).
        D1 algebra-identical to
        :func:`srmech.signal_processing.closed_form_ops.rfft.op`.
    """
    # numpy-free length: a numpy array carries its own ``.shape``; a plain
    # sequence uses ``len`` (no numpy import needed at this layer).
    _len = signal.shape[axis] if hasattr(signal, "shape") else len(signal)
    # Class K cycle-order verification on the FFT length (Spike #176 T8):
    # for stride=1 the additive order in ℤ/N is exactly N. Only invoked
    # inside the form_function_rotation validation envelope (256 ≤ N ≤
    # 2^16, multiple of 8); other lengths skip the structural assertion
    # but execute the same cyclic-DFT algebra (Class K identity holds for
    # any positive integer N).
    fft_n = n if n is not None else _len
    if fft_n >= 256 and fft_n <= (1 << 16) and fft_n % 8 == 0:
        order = verify_rotation_class_n_cycle_order(1, D=fft_n)
        assert order == fft_n, (
            f"Class K cycle order for stride=1 in Z/{fft_n} must equal "
            f"{fft_n}; got {order}. (Spike #176 T8 anchor.)"
        )
    # Class A ∘ Class I ∘ Class K composition on the real-symmetric half:
    # NumPy rfft IS this algebra restricted to the non-redundant bins.
    return _fc.rfft(signal, n=n, axis=axis)


# ──────────────────────────────────────────────────────────────────────
# Module-load registration with srmech.signal_processing.path_registry
# ──────────────────────────────────────────────────────────────────────


def _register() -> None:
    """Register Path B rFFT (and its Path A counterpart) with path_registry.

    Mirrors the ``fft`` module's dual registration so the dispatcher can
    route ``op_name="rfft"`` by ``path="A"`` / ``path="B"``. ``rfft`` is a
    post-Phase-4 addition (UPSTREAM_NOTES §1.1) — like ``pi_cascade`` it is
    NOT part of the frozen ``PATH_B_MVP_OPS`` roster.
    """
    from srmech.signal_processing.path_registry import register
    from srmech.signal_processing._paths import PATH_A, PATH_B
    from srmech.signal_processing.closed_form_ops.rfft import (
        op as path_a_rfft,
    )

    register(
        OPERATION_NAME,
        path=PATH_A,
        impl=path_a_rfft,
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
