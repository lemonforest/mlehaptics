"""Rendering — Patch-3-compliant projection from HDC angular state to 2D.

Per the build prompt's rendering-agnostic discipline (Patch 3):

    The HDC state captured by the encoder is the complete input to *any*
    rendering of the mechanism's output.  Rendering is a separate,
    static lookup that takes the same dynamic state through different
    radial-parameter tables.  Perspective is the scale invariance.

This module never computes a phase-space anything.  It takes an
encoded state (any of the four ``encode_ant_*`` outputs), decodes
each supported dial through ``dial_decoder``, converts residue -> angle,
and projects through a static radial table to produce ``Dict[dial_name,
(x, y)]``.

Two renderings are provided:

- ``render_dial`` — concentric circular dials at fixed radii, the
  Antikythera physical artefact's display.
- ``render_spatial`` — bodies at scaled orbital radii, the
  orrery/planetarium tradition.

Both consult static defaults: ``DIAL_LAYOUT_FREETH_2021`` and
``ORBITAL_RADII_AU``.
"""

from __future__ import annotations

from typing import Dict, Tuple, Union

import numpy as np

from .encode_ant import DIAL_SPECS, LCMState, supported_dials
from .dial_decoder import decode_dial_dense, decode_dial_lcm


# ---------------------------------------------------------------------------
# Static radial-parameter tables
# ---------------------------------------------------------------------------

DIAL_LAYOUT_FREETH_2021: Dict[str, float] = {
    # Front-dial concentric radii (arbitrary normalised units, qualitatively
    # matching Freeth 2021 figure layout).  Values are illustrative; the exact
    # mm dimensions of the physical artefact are not load-bearing here.
    "Metonic":                              5.0,
    "Callippic":                            4.5,
    "Olympic":                              4.0,
    "Saros":                                3.5,
    "Exeligmos":                            3.0,
    "SiderealMonth":                        2.5,
    "DraconicMonth":                        2.4,
    "LunarAnomaly":                         2.3,
    "Mercury_synodic_period_relation":      6.0,
    "Venus_synodic_period_relation":        6.5,
    "Mars_synodic_period_relation":         7.0,
    "Jupiter_synodic_period_relation":      7.5,
    "Saturn_synodic_period_relation":       8.0,
}

ORBITAL_RADII_AU: Dict[str, float] = {
    # Planetary semi-major axes (AU, IAU values).  Calendar/lunar dials
    # have no spatial-orbit interpretation; we give them small radii
    # qualitative to "Earth-system" so a single render call produces a
    # complete picture.
    "Metonic":                              0.05,
    "Callippic":                            0.06,
    "Olympic":                              0.07,
    "Saros":                                0.08,
    "Exeligmos":                            0.09,
    "SiderealMonth":                        0.10,
    "DraconicMonth":                        0.11,
    "LunarAnomaly":                         0.12,
    "Mercury_synodic_period_relation":      0.387,
    "Venus_synodic_period_relation":        0.723,
    "Mars_synodic_period_relation":         1.524,
    "Jupiter_synodic_period_relation":      5.203,
    "Saturn_synodic_period_relation":       9.537,
}


# ---------------------------------------------------------------------------
# Internal: residue -> angle helper
# ---------------------------------------------------------------------------

def _residue_to_angle(spec, residue_value: int, D: Union[int, str]) -> float:
    """Convert a residue (D-bin or modulus-integer) to radians in [0, 2pi)."""
    if D == "lcm":
        return 2.0 * np.pi * residue_value / spec.cycle_modulus
    return 2.0 * np.pi * residue_value / D


# ---------------------------------------------------------------------------
# Public renderers
# ---------------------------------------------------------------------------

def render_dial(
    state: Union[np.ndarray, LCMState],
    D: Union[int, str],
    dial_layout: Dict[str, float] = None,
) -> Dict[str, Tuple[float, float]]:
    """Render encoded state as concentric-dial pointer (x, y) positions.

    Parameters
    ----------
    state
        Output of ``encode_ant_callippic``, ``encode_ant_packing``,
        ``encode_ant_block_diagonal``, or ``encode_ant_lcm``.
    D
        The encoder's D value (940, 13440, etc.) or the literal string
        ``"lcm"`` for the symbolic LCM encoder.
    dial_layout
        Optional override of ``DIAL_LAYOUT_FREETH_2021``.

    Returns
    -------
    Dict[dial_name -> (x, y)]
    """
    if dial_layout is None:
        dial_layout = DIAL_LAYOUT_FREETH_2021
    return _render_with_radii(state, D, dial_layout)


def render_spatial(
    state: Union[np.ndarray, LCMState],
    D: Union[int, str],
    orbital_radii: Dict[str, float] = None,
    orrery_scale: float = 1.0,
) -> Dict[str, Tuple[float, float]]:
    """Render encoded state as orrery / planetarium spatial positions.

    Differs from ``render_dial`` only in the radial table; the
    underlying angular state is identical.  ``orrery_scale`` is the
    free perspective parameter from the build prompt — it scales all
    radii uniformly without entering the phase-space computation.
    """
    if orbital_radii is None:
        orbital_radii = ORBITAL_RADII_AU
    radii = {k: v * orrery_scale for k, v in orbital_radii.items()}
    return _render_with_radii(state, D, radii)


def _render_with_radii(
    state: Union[np.ndarray, LCMState],
    D: Union[int, str],
    radii: Dict[str, float],
) -> Dict[str, Tuple[float, float]]:
    out: Dict[str, Tuple[float, float]] = {}
    is_lcm = isinstance(state, LCMState)

    for spec in DIAL_SPECS:
        if spec.name not in radii:
            continue
        try:
            if is_lcm:
                residue = decode_dial_lcm(state, spec.name)
                angle = _residue_to_angle(spec, residue, "lcm")
            else:
                if not spec.is_supported(D):
                    continue
                residue = decode_dial_dense(state, spec.name, int(D))
                angle = _residue_to_angle(spec, residue, int(D))
        except Exception:
            continue
        r = radii[spec.name]
        out[spec.name] = (float(r * np.cos(angle)), float(r * np.sin(angle)))
    return out


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

_EPILOG = """\
Examples:
  # Default: dial + orrery + LCM perspective check at REFERENCE_JD+1000:
  python -m research.rendering

  # Dial render only:
  python -m research.rendering --projection dial --jd 1684960.0

  # Orrery render with custom scale (in AU):
  python -m research.rendering --projection orrery --orrery-scale 0.5

References
----------
Patch-3 discipline: encoder produces angular state only;
2D coordinates live exclusively here (rendering layer).
"""


def _make_parser():
    import argparse
    parser = argparse.ArgumentParser(
        prog="python -m research.rendering",
        description=("Patch-3-compliant 2D projections of the encoded "
                     "state.  Encoder produces angular dynamic state; "
                     "this module supplies the dial-style and orrery-"
                     "style 2D coordinates from a fixed lookup table."),
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--projection", default="all",
        choices=("dial", "orrery", "lcm-dial", "all"),
        help="Projection style (default: all).",
    )
    parser.add_argument(
        "--jd", type=float, default=None,
        help="Date as JD (default: REFERENCE_JD + 1000).",
    )
    parser.add_argument(
        "--orrery-scale", type=float, default=1.0,
        help="Scale factor for orrery render (AU; default: 1.0).",
    )
    return parser


def main(argv=None):
    args = _make_parser().parse_args(argv)
    from .encode_ant import (
        REFERENCE_JD, D_PACKING,
        encode_ant_packing, encode_ant_lcm,
    )

    print("rendering -- Patch-3-compliant 2D projections")
    print("=" * 60)
    test_jd = args.jd if args.jd is not None else REFERENCE_JD + 1000.0
    print(f"Test date: JD = {test_jd}")
    print()

    if args.projection in ("dial", "all"):
        state_packing = encode_ant_packing(test_jd)
        pos_dial = render_dial(state_packing, D_PACKING)
        print("Antikythera-style dial render (D=13440 packing):")
        for name, (x, y) in pos_dial.items():
            print(f"  {name:35s} (x, y) = ({x:+.3f}, {y:+.3f})")
        print()

    if args.projection in ("orrery", "all"):
        state_packing = encode_ant_packing(test_jd)
        pos_orrery = render_spatial(state_packing, D_PACKING,
                                    orrery_scale=args.orrery_scale)
        print(f"Orrery-style spatial render "
              f"(D=13440 packing, scale={args.orrery_scale} AU):")
        for name, (x, y) in pos_orrery.items():
            print(f"  {name:35s} (x, y) = ({x:+.4f}, {y:+.4f})  AU")
        print()

    if args.projection in ("lcm-dial", "all"):
        state_lcm = encode_ant_lcm(test_jd)
        pos_lcm_dial = render_dial(state_lcm, "lcm")
        print("LCM symbolic dial render (perspective check):")
        for name, (x, y) in list(pos_lcm_dial.items())[:5]:
            print(f"  {name:35s} (x, y) = ({x:+.3f}, {y:+.3f})")
        if len(pos_lcm_dial) > 5:
            print(f"  ... ({len(pos_lcm_dial) - 5} more)")
        print()

    print("Rendering smoke test complete.")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
