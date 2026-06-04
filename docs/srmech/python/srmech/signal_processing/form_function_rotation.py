"""Path B core — form-function rotation (Class A ∘ Class C ∘ Class M).

Phase 3 of the RBS-HDC-LoE dual-path architecture per the implementation plan
``docs/srmech/notes/rbs_hdc_loe_implementation_plan_2026-05-19.md``.

This module ships the operational composition canonised in Spike #176
(``rotation IS Class K pin-slot``) + Spike #173 (chess natural-stride
substrate). Per
``[[user_stance_form_function_rotation_is_a_c_m_composition]]`` +
``[[user_stance_rotation_is_class_k_pin_slot]]``:

- Class A — SHA-256 content-addressing yields a content-determined
  rotation stride.
- Class C — cyclic permute on Z/D applies the stride.
- Class M — HDC bind composes the rotated vector with substrate content.

Per ``[[user_stance_rotation_is_class_k_pin_slot]]`` (Spike #176 H1
CONFIRMED 6/6 at machine ε) rotation IS Class K pin-slot projection.
Two simultaneously-true views per the dual-level ontology:

- Cyclic (Z/N) substrate — phase operator with Class N rational order;
  magnitudes invariant under cyclic shift (DFT shift theorem). The
  Class K identity surfaces here as the linear phase ramp
  ``exp(-2π·i·k·m/N)``.
- Linear-windowed substrate — bin leakage = free cross-coupling. The
  cyclic shift breaks the windowed segment's phase reference, producing
  the leakage user named.

Per ``[[user_stance_cascade_lives_on_circles]]`` (Spike #24 bonus 9 +
Spike #176 T5): directed Class C orientation on Class I cyclic groups
produces unit-circle eigenvalues at machine ε. Cascade composition
(``k1 + k2 + k3 mod N``) yields another unit-circle cyclic shift —
``Im^2 + Re^2 = 1`` is an algebraic identity, not an approximation.

Per ``[[user_stance_cascade_lives_on_circles]]`` cascade composition of
rotations preserves circularity exactly: Spike #176 T5 reports
``residual ≤ 2.2e-16`` (machine ε).

Strict-spec discipline (Phase 3)
--------------------------------
- HDC width ``D = 8192`` bits (1024 bytes) per conductor decision #6;
  optional ``D`` parameter accepted (Spike #173 chess natural strides
  {5, 7, -8} demonstrate substrate-natural-stride composability at
  arbitrary substrates).
- Cyclic permute is bit-exact reversible via inverse stride
  (Spike #176 T4 recovery error = 0.0).
- Class N cycle order is ``D / gcd(stride, D)`` (Spike #176 T8).
- bind-permute commutativity: ``M.permute(M.bind(a, b), k) ==
  M.bind(M.permute(a, k), M.permute(b, k))`` at all chess natural
  strides (Spike #173 T4: 273 pair cells + 36 triple cells bit-exact).
- Z-DNA chirality involution: ``M.permute(M.permute(v, k), -k) == v``
  (Spike #173 T5: 14/14 involution round-trips).

Identity-not-implementation (Phase 3)
-------------------------------------
Per ``[[user_stance_identity_not_implementation_discipline]]`` rotation
IS Class K (per Spike #176 H1); this module does not implement rotation
as a separate primitive class — it composes the existing Class A + C +
M primitives in a canonical pattern. Class K's identity is
operationalised by the rotation cascade.

Trauma-informed defensive scope
-------------------------------
Per ``[[feedback_trauma_informed_defensive_scope]]``: rotation
operations are mathematical / structural. No targeting or capability-
assessment claims; civilian-comms / educational / methodology-research
framing only.

Canonical SSoT
--------------
- Spike #176 — rotation IS Class K pin-slot (H1 CONFIRMED 6/6 tests at
  machine ε); ``docs/srmech/notes/spike176_fft_rotation_bin_leakage_prototype.py``.
- Spike #173 — chess natural-stride cross-substrate verification (D2
  orthogonality at noise floor; bind-permute commutativity bit-exact);
  ``docs/srmech/notes/spike173_chess_rules_rbs_hdc_prototype.py``.
- Spike #172 — DNA helical-pitch substrate.
- Spike #177 — pin-slot-resonate music-box.
- Plate (1995) *Holographic Reduced Representations*, IEEE TNN 6, 623.
- Kanerva (2009) *Hyperdimensional Computing*, Cognitive Computation 1, 139.
- Oppenheim & Schafer (2010) *Discrete-Time Signal Processing* (3rd ed.) —
  DFT shift theorem (cyclic phase factor exp(-2πi·k·m/N)).
- Implementation plan: ``docs/srmech/notes/rbs_hdc_loe_implementation_plan_2026-05-19.md``.
"""

from __future__ import annotations

import hashlib
import math
from typing import Iterable, Tuple

from srmech.amsc import hdc as _M
from srmech.amsc import cyclic as _I

from ._paths import D_DEFAULT, D_MIN, D_MAX

__all__ = [
    "form_function_rotate",
    "inverse_form_function_rotate",
    "verify_rotation_class_n_cycle_order",
    "cascade_compose_rotations",
    # Constants / metadata
    "OPERATION_NAME",
    "CLASS_COMPOSITION",
    "PERFORMANCE_HINT",
    "SSOT_CITATION",
    "compute_content_stride",
]

OPERATION_NAME = "form_function_rotate"
CLASS_COMPOSITION = ("A", "C", "M")
PERFORMANCE_HINT = "path-b-native"
SSOT_CITATION = (
    "Spike #176 (rotation IS Class K pin-slot, H1 CONFIRMED 6/6 at "
    "machine epsilon) + Spike #173 (chess natural-stride D2 orthogonality "
    "+ bind-permute commutativity bit-exact); Oppenheim & Schafer (2010) "
    "Discrete-Time Signal Processing (DFT shift theorem)."
)


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────


def _validate_D(D: int) -> int:
    """Validate D parameter; return number of bytes (D / 8)."""
    if not isinstance(D, int):
        raise TypeError(f"D must be int; got {type(D).__name__}")
    if D < D_MIN:
        raise ValueError(f"D must be >= {D_MIN}; got {D}")
    if D > D_MAX:
        raise ValueError(f"D must be <= {D_MAX}; got {D}")
    if D % 8 != 0:
        raise ValueError(f"D must be a multiple of 8; got {D}")
    return D // 8


def compute_content_stride(content: bytes, *, D: int = D_DEFAULT) -> int:
    """Compute the content-determined rotation stride (Class A).

    Per Spike #176 form-function-rotation discipline: stride is
    ``SHA-256(content)[0:8]`` interpreted as little-endian uint64,
    modulo D. Deterministic in ``content``; same content always
    produces same stride.

    Parameters
    ----------
    content:
        Content bytes to address.
    D:
        Modulus (HDC bit-dimension). Default 8192.

    Returns
    -------
    int
        Stride in ``[0, D)``.
    """
    _validate_D(D)
    digest = hashlib.sha256(content).digest()
    val = int.from_bytes(digest[:8], "little")
    return val % D


# ──────────────────────────────────────────────────────────────────────
# Core operations
# ──────────────────────────────────────────────────────────────────────


def form_function_rotate(
    content: bytes,
    *,
    D: int = D_DEFAULT,
    stride: int | None = None,
) -> bytes:
    """Form-function rotate ``content`` by content-determined stride.

    Composition: Class A (SHA-256 -> stride) ∘ Class C (cyclic permute
    by stride) ∘ Class M (the permute itself is a Class M operation
    over Class C content).

    Two stride modes per
    ``[[user_stance_rotation_is_class_k_pin_slot]]``:

    - ``stride is None`` (default) — content-determined stride via
      :func:`compute_content_stride` (Class A; Spike #176 anchor). The
      stride is intrinsic to the content; rotating the same content
      always uses the same stride.
    - ``stride is int`` — substrate-natural stride (Class N rational).
      Useful for substrate-portable transmission per
      ``[[user_stance_substrate_natural_encoding_is_shadow_projection]]``
      and Spike #173's chess-natural strides {5, 7, -8} or Spike #172's
      DNA helical pitches {21, 11, -12}.

    Bit-exact reversibility per Spike #176 T4 (recovery error = 0.0):
    apply :func:`inverse_form_function_rotate` with the same stride
    to recover ``content`` exactly.

    Parameters
    ----------
    content:
        Input bytes. Must have length ``D / 8``.
    D:
        HDC dimension in bits. Default 8192.
    stride:
        If ``None``, use content-determined stride. If int, use
        substrate-natural stride directly. Negative strides supported
        (chirality / left-handed analog per Spike #173 T5).

    Returns
    -------
    bytes
        Rotated content; same length as input.

    Raises
    ------
    ValueError
        If ``content`` length does not match ``D / 8``.
    """
    n_bytes = _validate_D(D)
    if len(content) != n_bytes:
        raise ValueError(
            f"form_function_rotate: content length {len(content)} != "
            f"expected D/8 = {n_bytes} bytes"
        )
    if stride is None:
        stride = compute_content_stride(content, D=D)
    if not isinstance(stride, int):
        raise TypeError(
            f"form_function_rotate: stride must be int or None; "
            f"got {type(stride).__name__}"
        )
    # Class C ∘ Class M cyclic permute. permute reduces stride mod D
    # internally; we don't pre-reduce so negative strides preserve
    # chirality semantics (Spike #173 T5).
    return _M.permute(content, stride)


def inverse_form_function_rotate(
    rotated: bytes,
    *,
    D: int = D_DEFAULT,
    stride: int,
) -> bytes:
    """Inverse rotation — bit-exact recovery per Spike #176 T4.

    Applies ``M.permute`` with negated stride. Per Spike #173 T5
    chirality involution: ``permute(permute(v, k), -k) == v`` bit-exact
    (14/14 involution round-trips on the 14-class operator roster).

    Unlike :func:`form_function_rotate`, this function does NOT accept
    ``stride=None`` — the inverse must be computed against a known
    forward stride. Callers using the content-determined forward mode
    should capture the stride via :func:`compute_content_stride` before
    calling the inverse.

    Parameters
    ----------
    rotated:
        Bytes produced by :func:`form_function_rotate`.
    D:
        HDC dimension in bits. Default 8192.
    stride:
        Forward stride to invert. Negation handled internally.

    Returns
    -------
    bytes
        Recovered content; ``form_function_rotate(... stride=k)`` then
        ``inverse_form_function_rotate(... stride=k)`` returns the
        original bit-exact.

    Raises
    ------
    ValueError
        If ``rotated`` length does not match ``D / 8``.
    """
    n_bytes = _validate_D(D)
    if len(rotated) != n_bytes:
        raise ValueError(
            f"inverse_form_function_rotate: rotated length {len(rotated)} != "
            f"expected D/8 = {n_bytes} bytes"
        )
    if not isinstance(stride, int):
        raise TypeError(
            f"inverse_form_function_rotate: stride must be int; "
            f"got {type(stride).__name__}"
        )
    return _M.permute(rotated, -stride)


def verify_rotation_class_n_cycle_order(
    stride: int,
    D: int = D_DEFAULT,
) -> int:
    """Return the Class N cycle order of a rotation by ``stride`` mod D.

    Per Spike #176 T8: the additive order of ``stride`` in Z/D is
    ``D / gcd(stride, D)``. Applying ``form_function_rotate`` this many
    times in sequence returns to identity bit-exact (cyclic closure).

    Parameters
    ----------
    stride:
        Rotation stride. Negative strides reduce identically (additive
        order is gcd-determined; sign-independent).
    D:
        Modulus (HDC bit-dimension). Default 8192.

    Returns
    -------
    int
        Cycle order ``D / gcd(stride, D)``; integer in ``[1, D]``.

    Raises
    ------
    ValueError
        If ``D`` is invalid (per :func:`_validate_D`).
    """
    _validate_D(D)
    if not isinstance(stride, int):
        raise TypeError(
            f"verify_rotation_class_n_cycle_order: stride must be int; "
            f"got {type(stride).__name__}"
        )
    # gcd is well-defined for negative inputs; magnitude via
    # Class-K sign-branch (no abs()) to match Class N rational order semantics.
    g = _I.gcd((stride if stride >= 0 else -stride) if stride != 0 else D, D)
    return D // g


def cascade_compose_rotations(
    strides: Iterable[int],
    *,
    D: int = D_DEFAULT,
) -> Tuple[int, complex]:
    """Compose a cascade of rotations; return (mod-D stride, unit-circle
    eigenvalue).

    Per ``[[user_stance_cascade_lives_on_circles]]`` (Spike #24 bonus
    9; Spike #176 T5): cascade composition of cyclic shifts produces
    unit-circle eigenvalues at machine ε. Each rotation by stride k_i
    has eigenvalues ``exp(-2π·i·k_i·m/D)``; the cascade composes
    additively in stride space (mod D), and the resulting eigenvalue
    of the composed operator is ``exp(-2π·i·(sum k_i)·m/D)`` — still
    on the unit circle by algebraic identity ``|exp(iθ)| = 1``.

    Spike #176 T5 numerical anchor: ``residual = |Im(λ)^2 + Re(λ)^2 -
    1| ≤ 2.2e-16`` (machine ε) for representative eigenvalues at
    composed stride.

    This function returns the composed stride (mod D) and the
    fundamental-mode (m=1) eigenvalue ``exp(-2π·i·stride/D)`` as a
    Python ``complex``. Higher-mode eigenvalues at composed stride k
    are ``exp(-2π·i·k·m/D)`` for m in [0, D).

    Parameters
    ----------
    strides:
        Iterable of rotation strides to compose (any signs).
    D:
        Modulus (HDC bit-dimension). Default 8192.

    Returns
    -------
    (int, complex)
        ``(composed_stride_mod_D, fundamental_eigenvalue)``. The
        eigenvalue lies on the unit circle to machine epsilon.

    Raises
    ------
    ValueError
        If ``strides`` is empty.
    """
    _validate_D(D)
    strides_list = list(strides)
    if not strides_list:
        raise ValueError(
            "cascade_compose_rotations: strides iterable must be non-empty"
        )
    bad = [s for s in strides_list if not isinstance(s, int)]
    if bad:
        raise TypeError(
            f"cascade_compose_rotations: all strides must be int; "
            f"got non-int values {bad!r}"
        )
    composed = 0
    for s in strides_list:
        composed = (composed + s) % D
    # Fundamental-mode eigenvalue lambda_1 = exp(-2*pi*i * composed / D).
    theta = -2.0 * math.pi * composed / D
    eig = complex(math.cos(theta), math.sin(theta))
    return composed, eig


# ──────────────────────────────────────────────────────────────────────
# Module-load registration of Path B form-function-rotation with
# path_registry
# ──────────────────────────────────────────────────────────────────────


def _register_form_function_rotation() -> None:
    """Register the Path B form-function-rotation core op with the
    dispatcher's path_registry at module-load time.

    Registers ``form_function_rotate`` as a Path B-side op under its
    canonical operation name. Path A's ``form_function_rotate`` (if
    landed in Phase 4+) would register under the same name on the
    Path A side; Phase 3 ships Path B only.

    Registration is idempotent (per-callable identity).
    """
    from .path_registry import register  # lazy import
    from ._paths import PATH_B as _PATH_B

    register(
        OPERATION_NAME,
        path=_PATH_B,
        impl=form_function_rotate,
        ssot_citation=SSOT_CITATION,
        classes=CLASS_COMPOSITION,
    )


_register_form_function_rotation()
