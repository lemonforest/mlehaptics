"""qm.hurwitz — the Hurwitz Fano-plane cross-derivation + the Hurwitz [class].

History: rc50 shipped qm.hurwitz.hurwitz_matrix, a numpy 14×14 float builder
that DUPLICATED srmech.amsc.cascade.One.to_matrix (both float-cast the SAME
exact cascade the_one). rc75 (#564) DISSOLVED that numpy-Rosetta-peer: there
was never supposed to be a continuous-float peer (float SUMS error every op).
The Hurwitz operator is now declared the class-from-TOML way (`Hurwitz` [class],
method `generate` binding the EXACT op srmech.amsc.cascade.the_one); the float
14×14 is the opt-in lossy One.to_matrix export, never a separate named op.

What survives in srmech.qm.hurwitz: `hurwitz_planes` — the GENUINE
cross-derivation of the oriented Fano planes from octonion_mult_table (not a
float restatement; an exact integer-tuple structure read from the attested
table). hurwitz.py is now numpy-free at the top level (carrier ratchet
decrement); hurwitz_planes' full numpy-free reachability follows when
qm.octonion flips (the octonion table is still numpy until then).
"""

import pytest

from srmech.amsc.cascade.one import FANO_PLANES


# ── the Hurwitz [class] over the EXACT the_one (numpy-free, zero Python) ──

def test_hurwitz_class_is_the_exact_the_one():
    from srmech.dsl import make_class
    from srmech.amsc.cascade import the_one

    Hurwitz = make_class("Hurwitz")
    one_via_class = Hurwitz().generate(sigma=1, theta_num=1, theta_den=4, terms=24)
    one_direct = the_one(1, 1, 4, terms=24)
    # The 14 EXACT (num,den) rationals are bit-for-bit identical — no float, no
    # numpy, no error summation; the class IS the exact op under the Hurwitz name.
    assert one_via_class.to_flat_rational() == one_direct.to_flat_rational()
    assert type(one_via_class).__name__ == "One"


def test_hurwitz_class_registered_in_catalog():
    from srmech.dsl._class_catalog import load_class_catalog
    load_class_catalog.cache_clear()
    assert "Hurwitz" in load_class_catalog()


def test_hurwitz_matrix_op_dissolved():
    # The numpy float duplicate is gone (the dissolution); only the exact peers
    # remain (the_one / One.to_matrix as the opt-in float export).
    import srmech.qm.hurwitz as h
    assert not hasattr(h, "hurwitz_matrix")
    assert h.__all__ == ["hurwitz_planes"]


# ── the planes are DERIVED from the octonion table (the genuine op) ────
# (octonion_mult_table is still numpy until qm.octonion flips → skip numpy-free.)

def test_hurwitz_planes_derived_from_octonion_table():
    pytest.importorskip("numpy")  # octonion table is numpy until qm.octonion flips
    from srmech.qm.hurwitz import hurwitz_planes
    planes = hurwitz_planes()
    # ℂ: none; ℍ: {1,2,3} → (1,2,+1); 𝕆: the 3 Fano triples through e₇.
    assert planes == ((), ((1, 2, 1),), ((1, 6, -1), (2, 5, 1), (3, 4, 1)))
    assert tuple(len(p) for p in planes) == (0, 1, 3)


def test_cascade_fano_planes_match_table_derived_bit_exact():
    pytest.importorskip("numpy")
    from srmech.qm.hurwitz import hurwitz_planes
    # The cascade form HARDCODES FANO_PLANES; the qm op DERIVES them from
    # octonion_mult_table. They must be identical (the structure cross-derivation).
    assert FANO_PLANES == hurwitz_planes()
