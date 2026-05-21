"""Path A pi_cascade — algebra-substrate-native Archimedes hexagon-doubling.

Identity per ``[[user_stance_pi_as_projection]]`` + Spike #32 (PR #460
confirmed across hexagon / square / triangle substrates with AST-verified
zero ``math.pi`` invocations): the decimal expansion of π is the
**downstream projection** of the substrate-level cascade composition.

The Path A implementation is a thin wrapper over the existing
``srmech.amsc.rational.pi_cascade_digits`` (Milestone #4; rc13 cap = 1000
digits, depth/precision auto-scaled per
``_pi_cascade_auto_params``). It exposes the canonical Archimedes
hexagon-doubling cascade as a Path A signal-processing op so the
dual-path dispatcher can route ``op_name="pi_cascade"`` calls through
the closed-form algebra side.

Class composition ``("N", "I", "C")``:

- **Class N** — rational arithmetic (numerator/denominator integer
  representation of the half-perimeter ladder; rational-bounded √ at
  ``precision_bits`` scale).
- **Class I** — cyclic-group ℤ/n substrate (the n-gon's vertex count
  doubles n=6 → 12 → 24 → ... with hexagon-doubling identity
  s²_{2n} = 2 − √(4 − s²_n)).
- **Class C** — cascade-orientation (the depth-th iterate of the
  doubling map is the Path A op; identity-not-implementation: the
  cascade-shape IS π's substrate-level content per
  ``[[user_stance_pi_spectral_shape_scalar_invariant]]``).

Path B dual ships in :mod:`srmech.signal_processing.path_b_ops.pi_cascade`
(RBS-HDC instrument + form-function rotation, composing Class K rotation
+ Class M HDC bind on the dimension-D substrate). Both paths IS the same
pi-emergence per ``[[user_stance_identity_not_implementation_discipline]]``;
D1 algebra-identity is bit-exact for the same ``num_digits`` request.

Trauma-informed defensive scope: π is a foundational mathematical
constant; methodology-research / educational framing only.

Canonical SSoT
--------------
- Milestone #4 — pi_cascade_digits ship anchor (rc13 cap=1000).
- Spike #32 — cascade emergence confirmed across hexagon / square /
  triangle substrates (PR #460).
- ``[[user_stance_pi_as_projection]]`` — π is cascade-emergent from
  integer-cyclic substrate; scalar value is the projection artifact.
- ``[[user_stance_pi_spectral_shape_scalar_invariant]]`` — cascade-shape
  is π's substrate-invariant identity.
- Archimedes, *Measurement of a Circle* (c. 250 BCE) — the hexagon-
  doubling cascade itself (n=6 → 12 → 24 → 48 → 96 → ...).
- ``docs/srmech/notes/pi_cascade_digits_benchmark_2026-05-17.md`` —
  wall-time benchmark baseline (rc12 cap=50; rc13 expanded to 1000).
"""

from __future__ import annotations

from typing import Optional

from srmech.amsc.rational import pi_cascade_digits as _amsc_pi_cascade_digits

OPERATION_NAME = "pi_cascade"
CLASS_COMPOSITION = ("N", "I", "C")
PERFORMANCE_HINT = "algebra-substrate-native"
SSOT_CITATION = (
    "Milestone #4; [[user_stance_pi_as_projection]]; Spike #32 "
    "(pi as spectral shape; cascade-emergent across hexagon/square/"
    "triangle substrates, PR #460). Underlying primitive: "
    "srmech.amsc.rational.pi_cascade_digits (rc13 cap=1000)."
)


def op(
    num_digits: int,
    *,
    max_cascade_depth: Optional[int] = None,
    precision_bits: Optional[int] = None,
    D: int = 8192,
) -> str:
    """Compute π to ``num_digits`` decimal digits via Path A cascade.

    Thin wrapper over :func:`srmech.amsc.rational.pi_cascade_digits`.
    The ``D`` kwarg is accepted for cross-path API consistency with the
    dual-path dispatcher; the Path A closed-form algebra does not use
    it (D parameterises the RBS-HDC bound-vector substrate on Path B).

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
        Path B dimensionality hint (default 8192). Accepted for
        cross-path API consistency; not used by the Path A algebra.

    Returns
    -------
    str
        Decimal expansion ``"3.141592...."`` — exactly ``num_digits``
        digits after the decimal point.
    """
    # D is accepted but unused on Path A (closed-form algebra substrate).
    del D  # silence linter; documented above
    return _amsc_pi_cascade_digits(
        num_digits,
        max_cascade_depth=max_cascade_depth,
        precision_bits=precision_bits,
    )


# ──────────────────────────────────────────────────────────────────────
# Module-load registration with srmech.signal_processing.path_registry
# ──────────────────────────────────────────────────────────────────────


def _register() -> None:
    """Register Path A pi_cascade with the dispatcher's path_registry.

    Phase 4 + Spike #184 pattern: Path A registration lives in the
    closed_form_ops module (not in the Phase 2 38-op script) when the
    op is added by a spike. Path B counterpart registers separately
    in :mod:`srmech.signal_processing.path_b_ops.pi_cascade`.
    """
    from srmech.signal_processing.path_registry import register
    from srmech.signal_processing._paths import PATH_A

    register(
        OPERATION_NAME,
        path=PATH_A,
        impl=op,
        ssot_citation=SSOT_CITATION,
        classes=CLASS_COMPOSITION,
    )


_register()
