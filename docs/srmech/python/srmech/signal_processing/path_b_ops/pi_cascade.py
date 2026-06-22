"""Path B pi_cascade — RBS-HDC instrument cyclic-substrate composition.

Identity per ``[[user_stance_pi_as_projection]]`` (π as cascade-emergent
projection from integer-cyclic substrate) + Spike #176
``[[user_stance_rotation_is_class_k_pin_slot]]`` (rotation IS Class K) +
Spike #170 (RBS-HDC instrument as LoE-bearing substrate at D=8192) +
``[[user_stance_cascade_lives_on_circles]]`` (cascade composition of
cyclic shifts produces unit-circle eigenvalues at machine ε).

The underlying ``srmech.amsc.rational.pi_cascade_digits`` primitive
computes π via the **two-sided Pfaff–Archimedes chiral pair** (rc20):
a *circumscribed* bound ``a`` falling ↓ to π (the harmonic mean,
``aₙ₊₁ = 2·aₙ·bₙ/(aₙ+bₙ)``) and an *inscribed* bound ``b`` rising ↑ to π
(the geometric mean, ``bₙ₊₁ = √(aₙ₊₁·bₙ)`` — the ONE √ per step), from
``a₀ = 2√3`` and ``b₀ = 3``. The two are a chiral pair — the same cycle
run with opposite orientation — and the bracket invariant ``b < π < a``
holds at every step, so π is the midpoint ``(a + b)/2`` (the old naive
linear single-bound hexagon-doubling form was removed in rc20). For the
canonical exact-substrate π digit stream (bit-exact body, ONE terminal
rotation) use ``srmech.amsc.rational.pi_chudnovsky_digits`` — the digit
SSoT the chiral pair is cross-checked against.

The Path B implementation lives on the **RBS-HDC bound-vector substrate
at D=8192**:

1. **Class K cycle order verification** (Spike #176 T8). Each
   polygon-doubling step n → 2n in the chiral pair IS a Class K pin-slot
   rotation on a cyclic substrate ℤ/n. We verify that for representative
   n in the cascade (n=6, 12, 24, ...), the additive order in ℤ/D is
   well-defined: ``verify_rotation_class_n_cycle_order(n, D=8192) =
   D / gcd(n, D)``. This anchors the cyclic-substrate identity.

2. **Class M HDC bind on cascade content**. The decimal-digit content
   of π (as bytes) is bound into the D=8192 HDC instrument via
   ``form_function_rotate`` with content-determined stride
   (``compute_content_stride``). The bind is bit-exact reversible
   (Spike #176 T4: recovery error = 0.0); it does not modify the
   cascade output, but anchors that the content IS HDC-bindable on
   the substrate.

3. **Class N rational** + **Class I cyclic** + **Class C cascade**
   underlying — Path B inherits these from the same
   ``srmech.amsc.rational.pi_cascade_digits`` primitive that Path A
   uses. Per
   ``[[user_stance_identity_not_implementation_discipline]]``: both
   paths INSTANTIATE the same pi-cascade composition; the dispatcher
   chooses substrate (algebra-native vs. RBS-HDC-native), never
   identity. D1 algebra-content is bit-exact between the two paths.

The Path B "win" is **cascade-portability**: when pi_cascade is one
step in a longer cascade (``begin_cascade`` context), the Path B
output content can be bound into adjacent HDC ops (Class M
bind/bundle/permute) without re-encoding. The Path A output is a
decimal string requiring a fresh content-addressing pass to enter
the HDC substrate.

Trauma-informed defensive scope: methodology-research / educational
framing only. π is a foundational mathematical constant.

Canonical SSoT
--------------
- Spike #170 — LoE-as-RBS-HDC R1 (14/14 mint determinism at D=8192;
  the instrument is LoE-bearing).
- Spike #176 — rotation IS Class K pin-slot at machine ε (H1 CONFIRMED
  6/6); T4 round-trip identity (recovery error = 0.0); T8 cycle order
  ``D / gcd(stride, D)``.
- ``[[user_stance_pi_as_projection]]`` — π is cascade-emergent from
  integer-cyclic substrate.
- ``[[user_stance_cascade_lives_on_circles]]`` — Spike #24 bonus 9
  cascade composition preserves unit-circle eigenvalues.
- ``[[user_stance_identity_not_implementation_discipline]]`` — Path A
  and Path B both instantiate the same algebra; D1 bit-exact.
- Milestone #4 — underlying ``srmech.amsc.rational.pi_cascade_digits``
  primitive (rc13 cap=1000; rc20 two-sided Pfaff–Archimedes chiral pair).
- ``srmech.amsc.rational.pi_chudnovsky_digits`` — the canonical
  exact-substrate π digit SSoT the chiral pair is cross-checked against
  (rc19).
- Archimedes, *Measurement of a Circle* (c. 250 BCE), as reformulated by
  J. F. Pfaff (1800) into the recurrent harmonic/geometric mean pair.
"""

from __future__ import annotations

from typing import Optional

from srmech.amsc.rational import pi_cascade_digits as _amsc_pi_cascade_digits

from srmech.signal_processing.form_function_rotation import (
    compute_content_stride,
    form_function_rotate,
    inverse_form_function_rotate,
    verify_rotation_class_n_cycle_order,
)

OPERATION_NAME = "pi_cascade"
CLASS_COMPOSITION = ("N", "I", "C", "K", "M")
PERFORMANCE_HINT = "rbs-hdc-substrate-native"
SSOT_CITATION = (
    "Spike #170 (LoE-as-RBS-HDC R1, D=8192); Spike #176 (rotation IS "
    "Class K at machine epsilon; T4 round-trip identity; T8 cycle "
    "order D/gcd(k,D)); [[user_stance_pi_as_projection]] (pi "
    "cascade-emergent from integer-cyclic substrate); "
    "[[user_stance_cascade_lives_on_circles]] (Spike #24 bonus 9). "
    "Underlying primitive: srmech.amsc.rational.pi_cascade_digits "
    "(rc13 cap=1000, Milestone #4)."
)


# Representative cyclic-substrate sample strides for Class K cycle-order
# verification. Each is a n-gon vertex count along Archimedes's cascade
# (6 → 12 → 24 → 48 → 96 → 192). For each of these strides k, in the
# D=8192 substrate the additive order is D / gcd(k, D). The verification
# anchors that the cyclic-substrate identity holds on the RBS-HDC
# substrate (Class K + Class I).
_ARCHIMEDES_CASCADE_STRIDES = (6, 12, 24, 48, 96, 192)


def _verify_path_b_substrate_identity(D: int) -> dict:
    """Verify Class K cycle-order identity on Archimedes cascade strides.

    For each n in ``_ARCHIMEDES_CASCADE_STRIDES``, asserts that the
    cycle order in ℤ/D equals ``D / gcd(n, D)``. This anchors the
    Path B substrate identity — the RBS-HDC bound-vector at D=8192
    inherits the cyclic-substrate algebra by construction.

    Returns the (stride, cycle_order) pairs as a metadata dict for
    optional inspection by the benchmark.
    """
    from srmech.amsc.cyclic import gcd
    pairs: dict = {}
    for k in _ARCHIMEDES_CASCADE_STRIDES:
        order = verify_rotation_class_n_cycle_order(k, D=D)
        expected = D // gcd(k, D)
        assert order == expected, (
            f"Class K cycle-order identity broken: order({k}, D={D}) "
            f"= {order}, expected {expected}"
        )
        pairs[k] = order
    return pairs


def _verify_class_m_hdc_bind_roundtrip(
    content: bytes,
    *,
    D: int,
) -> bool:
    """Verify Class M HDC bind on cascade content is bit-exact reversible.

    Path B identity anchor (Spike #176 T4): bind ``content`` into the
    D-bit RBS-HDC substrate via content-determined ``form_function_rotate``,
    then invert. Recovery error must be 0.0 (bit-exact).

    Path A does NOT do this — Path A produces the decimal-string
    output directly. The Class M HDC bind anchor is Path B's
    distinguishing substrate operation, even though both paths emit
    the same final π string.
    """
    n_bytes = D // 8
    # Pad or truncate the content to D/8 bytes for HDC bind.
    if len(content) < n_bytes:
        padded = content + b"\x00" * (n_bytes - len(content))
    else:
        padded = content[:n_bytes]
    stride = compute_content_stride(padded, D=D)
    rotated = form_function_rotate(padded, D=D, stride=stride)
    recovered = inverse_form_function_rotate(rotated, D=D, stride=stride)
    return recovered == padded


def op(
    num_digits: int,
    *,
    max_cascade_depth: Optional[int] = None,
    precision_bits: Optional[int] = None,
    D: int = 8192,
    verify_substrate: bool = True,
) -> str:
    """Compute π to ``num_digits`` decimal digits via Path B substrate.

    Path B composition (per
    ``[[user_stance_identity_not_implementation_discipline]]``):

    1. Verify Class K cycle-order identity on Archimedes cascade
       strides in the D-bit substrate (Spike #176 T8). This anchors
       that the cyclic-substrate algebra is well-defined on the
       RBS-HDC instrument.
    2. Compute the cascade content via the same underlying primitive
       (``srmech.amsc.rational.pi_cascade_digits``) — both paths IS the
       same algebra, the dispatcher routes between substrates.
    3. Verify Class M HDC bind round-trip on the cascade content
       (Spike #176 T4) — the π content is HDC-bindable on the D=8192
       substrate.

    The actual decimal digits are bit-exact identical to Path A; the
    Path B distinction is the substrate identity verification + HDC
    bind anchor.

    Parameters
    ----------
    num_digits:
        Number of decimal digits to emit after the decimal point.
        Must satisfy ``0 <= num_digits <= 1000`` (rc13 cap).
    max_cascade_depth:
        Optional override of the cascade doubling depth. ``None`` =
        auto-scaled from ``num_digits`` per the rc13 linear scaling.
    precision_bits:
        Optional override of the scaled-integer precision. ``None`` =
        auto-scaled from ``num_digits``.
    D:
        RBS-HDC bound-vector dimension (default 8192 per conductor
        decision #6). Used for the Class K cycle-order and Class M
        HDC bind verifications.
    verify_substrate:
        If True (default), runs the Class K + Class M substrate
        identity verifications. Set False to skip the substrate
        verifications when benchmarking pure computation cost (Path B
        cost = Path A cost + substrate verification cost).

    Returns
    -------
    str
        Decimal expansion ``"3.141592...."`` — exactly ``num_digits``
        digits. D1 algebra-identical to
        :func:`srmech.signal_processing.closed_form_ops.pi_cascade.op`.
    """
    # ── Step 1: Class K cycle-order identity on Archimedes cascade ──
    if verify_substrate:
        _verify_path_b_substrate_identity(D=D)

    # ── Step 2: Compute π cascade content via underlying primitive ──
    # Path A and Path B both IS the same cascade composition per
    # [[user_stance_identity_not_implementation_discipline]]; the
    # substrate choice does not modify the algebra-content output.
    pi_str = _amsc_pi_cascade_digits(
        num_digits,
        max_cascade_depth=max_cascade_depth,
        precision_bits=precision_bits,
    )

    # ── Step 3: Class M HDC bind round-trip on cascade content ──
    if verify_substrate:
        content_bytes = pi_str.encode("ascii")
        ok = _verify_class_m_hdc_bind_roundtrip(content_bytes, D=D)
        assert ok, (
            "Path B Class M HDC bind round-trip failed; "
            "Spike #176 T4 identity broken on pi_cascade content."
        )

    return pi_str


# ──────────────────────────────────────────────────────────────────────
# Module-load registration with srmech.signal_processing.path_registry
# ──────────────────────────────────────────────────────────────────────


def _register() -> None:
    """Register Path B pi_cascade with the dispatcher's path_registry.

    Also imports the Path A counterpart module so its module-level
    ``_register()`` fires (registering Path A pi_cascade). Both paths
    are then available to the dispatcher.
    """
    from srmech.signal_processing.path_registry import register
    from srmech.signal_processing._paths import PATH_A, PATH_B
    # Importing the closed_form_ops.pi_cascade module triggers its own
    # module-load _register() call which registers Path A.
    from srmech.signal_processing.closed_form_ops.pi_cascade import (
        op as path_a_pi_cascade,
    )

    register(
        OPERATION_NAME,
        path=PATH_A,
        impl=path_a_pi_cascade,
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
