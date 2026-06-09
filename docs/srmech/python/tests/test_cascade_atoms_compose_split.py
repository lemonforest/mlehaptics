"""Tests for the cascade.atoms / cascade.compose two-tier split.

Per issue #751 (F208 / MS #20 forward-architecture). The single
``srmech.amsc.cascade`` module is split into two tiers:

- :mod:`srmech.amsc.cascade.atoms` — the 6 silicon-able 1:1 ISA
  intrinsics (``pin_slot_at_zero``, ``reorient``, ``magnitude``,
  ``chiral_flip``, ``chiral_dual``, ``net_chirality``).
- :mod:`srmech.amsc.cascade.compose` — the 2 iterative algorithms
  (``cyclic_gcd``, ``best_rational_signed``) + the 2 module constants
  (``DEFAULT_MAX_DENOMINATOR``, ``DEFAULT_FINE_SCALE``).

The flat ``srmech.amsc.cascade.<op>`` public surface must stay
byte-identical (every flat name IS the same object as its submodule
home), ``CASCADE_OPS`` unchanged, and ``srmech.introspect.describe()``
must report 176 tools (174 at rc1 + 1 for the rc2 so(4) stabiliser voxel
+ 1 for the rc3 lean-ISA seventh-primitive voxel).
This is a behaviour-preserving refactor.
"""

from __future__ import annotations

import srmech.amsc.cascade as cascade
import srmech.amsc.cascade.atoms as atoms_mod
import srmech.amsc.cascade.compose as compose_mod


# ----------------------------------------------------------------------
# (a) atoms submodule exposes the 6 silicon-able 1:1 ISA intrinsics
# ----------------------------------------------------------------------


def test_atoms_submodule_imports():
    from srmech.amsc.cascade.atoms import (  # noqa: F401
        pin_slot_at_zero,
        reorient,
        magnitude,
        chiral_flip,
        chiral_dual,
        net_chirality,
    )


# ----------------------------------------------------------------------
# (b) compose submodule exposes the 2 iterative algos + 2 constants
# ----------------------------------------------------------------------


def test_compose_submodule_imports():
    from srmech.amsc.cascade.compose import (  # noqa: F401
        cyclic_gcd,
        best_rational_signed,
        DEFAULT_MAX_DENOMINATOR,
        DEFAULT_FINE_SCALE,
    )


# ----------------------------------------------------------------------
# (c) each flat cascade.<op> IS the same object as the submodule one
# ----------------------------------------------------------------------


def test_flat_atom_ops_are_submodule_objects():
    assert cascade.pin_slot_at_zero is atoms_mod.pin_slot_at_zero
    assert cascade.reorient is atoms_mod.reorient
    assert cascade.magnitude is atoms_mod.magnitude
    assert cascade.chiral_flip is atoms_mod.chiral_flip
    assert cascade.chiral_dual is atoms_mod.chiral_dual
    assert cascade.net_chirality is atoms_mod.net_chirality


def test_flat_compose_ops_are_submodule_objects():
    assert cascade.cyclic_gcd is compose_mod.cyclic_gcd
    assert cascade.best_rational_signed is compose_mod.best_rational_signed


def test_flat_constants_are_submodule_objects():
    assert cascade.DEFAULT_MAX_DENOMINATOR == compose_mod.DEFAULT_MAX_DENOMINATOR
    assert cascade.DEFAULT_FINE_SCALE == compose_mod.DEFAULT_FINE_SCALE


def test_back_compat_aliases_unchanged():
    assert cascade.class_k_pin_slot_at_zero is cascade.pin_slot_at_zero
    assert cascade.class_c_reorient is cascade.reorient
    assert cascade.best_rat_signed is cascade.best_rational_signed


def test_submodules_exposed_as_attributes():
    assert cascade.atoms is atoms_mod
    assert cascade.compose is compose_mod


def test_atom_in_compose_is_same_object():
    # compose imports the atoms it builds over from .atoms — they must be
    # the exact same objects, not copies.
    assert compose_mod.pin_slot_at_zero is atoms_mod.pin_slot_at_zero
    assert compose_mod.reorient is atoms_mod.reorient


# ----------------------------------------------------------------------
# (d) CASCADE_OPS unchanged
# ----------------------------------------------------------------------


def test_cascade_ops_unchanged():
    assert cascade.CASCADE_OPS == (
        "pin_slot_at_zero",
        "reorient",
        "magnitude",
        "best_rational_signed",
        "cyclic_gcd",
        "chiral_flip",
        "chiral_dual",
        "net_chirality",
    )


# ----------------------------------------------------------------------
# (e) introspection tools.total is 179 (174 rc1 + 1 rc2 so(4) stabiliser
#     + 1 rc3 lean-ISA seventh-primitive + 1 rc6 parallel_sector_dispatch
#     + 1 rc9 cascade.kuramoto_step + 1 rc17 klein4_triality_cycle
#     + 1 v0.7.0rc8 cascade.autocorrelation -> 193)
# ----------------------------------------------------------------------


def test_introspect_tools_total_is_210():
    import srmech.introspect as introspect

    assert introspect.describe()["tools"]["total"] == 276


# ----------------------------------------------------------------------
# Behaviour preservation — flat surface still callable + correct
# ----------------------------------------------------------------------


def test_flat_surface_still_callable():
    # Class K pin-slot at zero.
    assert cascade.pin_slot_at_zero(-3.0) == (-1, 3.0)
    # Class K magnitude (no abs()).
    assert cascade.magnitude(-5.0) == 5.0
    # Class C reorient.
    assert cascade.reorient(7, orientation=-1) == -7
    # Class I cyclic gcd (Euclid).
    assert cascade.cyclic_gcd(12, 8) == 4
    # Class K ∘ N ∘ C best-rational-signed.
    assert cascade.best_rational_signed(-0.5) == (-1, 2)
    # Class C chiral flip.
    assert cascade.chiral_flip([1, 2, 3]) == [3, 2, 1]
    # Class C net chirality.
    assert cascade.net_chirality([1, -1, -1]) == 1
