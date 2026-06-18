"""S3 = Aut(V4) triality worked-instance verification (v0.6.0rc19, MS #20).

The continuum-tier worked instance
``srmech/amsc/_research/worked_instances/triality_s3_klein4.toml`` documents
that ``klein4_triality_cycle`` (T) is the order-3 generator of Aut(V4) = S3,
via the automorphism conjugation ``T . XOR_a . T^-1 = XOR_{T(a)}`` (T cyclically
permutes the three order-2 chirality flips iw7 -> g5 -> cpt). The klein4 ops are
kernel-tier (srmech.amsc.hdc) and deliberately NOT in the srmech.dsl cascade
catalog, so this instance is verified HERE in Python against the real ops
(rather than via run_toml_chain). This test IS the worked instance's executable
attestation — the TOML's documented claims are checked against the ops.

#564 (numpy out the door): the random Klein-4 vectors are built with the stdlib
``random.Random`` (ints in {0,1,2,3}) and every op returns an ``HV`` compared
via ``HV.__eq__``. No numpy is imported, so this worked-instance attestation
runs with numpy absent (the substrate-native discipline).
"""
import random
import sys
from pathlib import Path

import srmech
from srmech.amsc import hdc

if sys.version_info >= (3, 11):
    import tomllib as _toml
else:  # pragma: no cover — 3.10 back-port branch
    import tomli as _toml  # type: ignore[no-redef]


_TOML_PATH = (
    Path(srmech.__file__).resolve().parent
    / "amsc" / "_research" / "worked_instances" / "triality_s3_klein4.toml"
)

# XOR-mask <-> named flip (the three V4 translations / order-2 involutions).
_FLIP = {
    1: hdc.klein4_chirality_flip_omega7,  # XOR 1  (iw7)
    2: hdc.klein4_chirality_flip_gamma5,  # XOR 2  (g5)
    3: hdc.klein4_cpt_mirror,             # XOR 3  (cpt)
}


def _T(v):
    return hdc.klein4_triality_cycle(v)


def _T_inv(v):
    return hdc.klein4_triality_cycle(v, inverse=True)


def _rand(seed, D=512):
    r = random.Random(seed)
    return [r.randrange(4) for _ in range(D)]


# --------------------------------------------------------------------------
# The TOML worked-instance artifact ships + is well-formed.
# --------------------------------------------------------------------------

def test_worked_instance_toml_present_and_named():
    assert _TOML_PATH.is_file(), f"worked-instance TOML missing at {_TOML_PATH}"
    with open(_TOML_PATH, "rb") as fh:
        doc = _toml.load(fh)
    wi = doc["worked_instance"]
    assert wi["name"] == "triality_s3_klein4"
    # Aut(V4)=S3 exposes T and T^2 (the order-3 generator); the three flips are
    # the V4 translations T permutes; the conjugation cascade has three legs.
    assert len(wi["aut_v4_s3"]["order_3"]) == 2
    assert set(wi["v4_translations"]) >= {"iw7", "g5", "cpt"}
    assert len(wi["conjugation_cascade"]["cycle"]) == 3


# --------------------------------------------------------------------------
# The group structure: T order 3, the flips order 2, T a V4 homomorphism.
# --------------------------------------------------------------------------

def test_triality_cycle_has_order_three():
    v = _rand(1)
    assert (_T(_T(_T(v))) == v)


def test_square_equals_inverse():
    v = _rand(2)
    assert (_T(_T(v)) == _T_inv(v))


def test_each_flip_is_an_involution():
    v = _rand(3)
    for flip in _FLIP.values():
        assert (flip(flip(v)) == v)


def test_T_is_a_v4_homomorphism():
    # T(u XOR w) == T(u) XOR T(w); klein4_bind IS the XOR group op.
    u, w = _rand(4), _rand(5)
    assert (_T(hdc.klein4_bind(u, w)) == hdc.klein4_bind(_T(u), _T(w)))


# --------------------------------------------------------------------------
# The load-bearing instance: T conjugates each flip into the next.
# T . XOR_a . T^-1 == XOR_{T(a)}, cyclically iw7 -> g5 -> cpt -> iw7.
# --------------------------------------------------------------------------

def test_conjugation_cyclically_permutes_the_three_flips():
    v = _rand(6)
    # T(a): forward 3-cycle 1->2->3->1, so XOR1->XOR2, XOR2->XOR3, XOR3->XOR1.
    for a, t_of_a in ((1, 2), (2, 3), (3, 1)):
        conjugated = _T(_FLIP[a](_T_inv(v)))
        expected = _FLIP[t_of_a](v)
        assert (conjugated == expected), (
            f"T . XOR_{a} . T^-1 must equal XOR_{t_of_a} (the flip-cycle)"
        )


def test_conjugation_named_cycle_iw7_g5_cpt():
    # the same relation in the named-op vocabulary the TOML documents
    v = _rand(7)
    f_iw7, f_g5, f_cpt = _FLIP[1], _FLIP[2], _FLIP[3]
    assert (_T(f_iw7(_T_inv(v))) == f_g5(v))   # iw7 -> g5
    assert (_T(f_g5(_T_inv(v))) == f_cpt(v))   # g5  -> cpt
    assert (_T(f_cpt(_T_inv(v))) == f_iw7(v))  # cpt -> iw7
