"""0.9.0rc16 — the exact-Q61 ``hypercomplex_couple`` C-host peer is bit-exact.

rc16 rewrote the (σ,θ,μ) coupler off the float ``Mat`` octonion-matvec onto an
EXACT fixed-width **Q61 octonion multiply** (Cayley–Dickson structure constants
``cd_basis_product`` ∘ the Q61 fixed-point multiply ∘ Class-C sign orientation),
so a C-only host reproduces the couple byte-for-byte
(``srmech_hypercomplex_couple_q61``) — the stay-rational NORTH STAR, no float
boundary except the final projection. This closes the rc12
``sed_couple``/``sed_uncouple`` → ``hypercomplex_couple`` transitive-ratchet
allowlist.

Two contracts:
  * **Behaviour (native OR pure)** — the public ``hypercomplex_couple`` still
    binds + reverses (F436 coherence / F437 reversibility) within float
    tolerance, proving the float→exact-then-project rewrite did not change the
    shipped numerics meaningfully.
  * **Bit-parity (platform wheel only)** — the native couple returns the SAME
    Q61 int8 as the pure ``_octo_mult_q61`` reference, byte-for-byte.

Numpy-free by construction; asserted numpy-absent so it PASSES (not skips) on
the numpy-absent matrix.
"""

import importlib.util

import pytest

from srmech.amsc import _native
from srmech.amsc.cascade import hypercomplex_dft as _hc
from srmech.amsc.cascade.hypercomplex_dft import (
    hypercomplex_couple,
    _couple_q61,
    _octo_mult_q61,
    _to_q61,
    _q61_int,
    _Q61_ONE,
)
from srmech.amsc.rational import cos as _rcos, sin as _rsin

_HAS_NATIVE_COUPLE = _native.has_native_hypercomplex_couple()
_native_only = pytest.mark.skipif(
    not _HAS_NATIVE_COUPLE,
    reason="srmech_hypercomplex_couple_q61 native peer not loaded (pure wheel)")

# stream rosters across the ℍ (≤3) and 𝕆 (4–7) packings.
_ROSTERS = [
    [1.0, 0.0, 0.0],
    [0.5, -0.25, 0.75],
    [1.0, 1.0, 1.0],
    [0.3, 0.6, -0.9, 0.2],
    [1.0, -1.0, 0.5, -0.5, 0.25, -0.25, 0.125],
    [0.0, 0.0, 0.0],
]


def test_numpy_is_absent_so_this_runs_not_skips():
    assert importlib.util.find_spec("numpy") is None, (
        "this couple C-parity ratchet must run on the numpy-ABSENT matrix")


# ── behaviour: F437 reversibility (native OR pure — the shipped contract) ──

@pytest.mark.parametrize("streams", _ROSTERS)
@pytest.mark.parametrize("form", ["left", "right"])
def test_couple_uncouple_round_trips(streams, form):
    """``couple(couple(q, σ=+1), σ=-1)`` recovers the carrier up to ‖T‖²=1
    (unit twiddle) — the division-algebra identity T̄·(T·q)=q on ℍ/𝕆 (F437).
    Compared slot-for-slot against the packed carrier ``q`` itself."""
    q, octonion = _hc._pack_streams(streams)           # internal 8-length carrier
    ref = list(q) if octonion else list(q[:4])         # projected like the public op
    bound = hypercomplex_couple(streams, theta=0.7, form=form, sigma=1)
    back = hypercomplex_couple(bound, theta=0.7, form=form, sigma=-1)
    assert len(back) == len(ref)
    for got, want in zip(back, ref):
        assert abs(got - want) < 1e-9


@pytest.mark.parametrize("form", ["left", "right"])
def test_diagonal_bind_collects_coherence_into_anchor(form):
    """F436: a quarter-turn diagonal bind of coherent streams folds ``−Σsₙ``
    into the real/anchor channel (coherent add)."""
    streams = [0.4, 0.4, 0.4]
    out = hypercomplex_couple(streams, theta=1.5707963267948966,
                              axis="diagonal", form=form, sigma=1)
    # anchor channel magnitude tracks the coherent sum (sign per form/orientation)
    assert abs(abs(out[0]) - abs(sum(streams)) / (3 ** 0.5)) < 1e-9


# ── the pure Q61 core is self-consistent (native OR pure) ──

@pytest.mark.parametrize("streams", _ROSTERS)
@pytest.mark.parametrize("form", ["left", "right"])
def test_couple_q61_matches_explicit_reference(streams, form):
    """``_couple_q61`` equals an INDEPENDENT explicit twiddle⊗octonion built from
    the same Q61 primitives — pins the couple core to its definition."""
    q, octonion = _hc._pack_streams(streams)
    mu = _hc._resolve_mu("diagonal", octonion=octonion)
    s_q61 = [_to_q61(v) for v in q]
    mu_q61 = [_to_q61(v) for v in mu]
    eff = 0.9
    # explicit reference twiddle T = cos eff + sin eff·μ (Q61)
    cos = _q61_int(_rcos(eff))
    sin = _q61_int(_rsin(eff))
    from srmech.amsc.rational import _q61_fxmul
    tw = [cos] + [_q61_fxmul(sin, mu_q61[i]) for i in range(1, 8)]
    ref = _octo_mult_q61(tw, s_q61) if form == "left" else _octo_mult_q61(s_q61, tw)
    got = _couple_q61(s_q61, mu_q61, eff, form=form)
    assert got == ref


# ── bit-parity: native couple == pure Q61 reference, byte-for-byte (wheel) ──

@_native_only
@pytest.mark.parametrize("streams", _ROSTERS)
@pytest.mark.parametrize("form", ["left", "right"])
def test_native_couple_byte_identical_to_pure(streams, form):
    """The native ``hypercomplex_couple_q61_c`` returns the SAME 8 Q61 ints as
    the pure ``_octo_mult_q61`` twiddle path — byte-for-byte (no float)."""
    q, octonion = _hc._pack_streams(streams)
    mu = _hc._resolve_mu("diagonal", octonion=octonion)
    s_q61 = [_to_q61(v) for v in q]
    mu_q61 = [_to_q61(v) for v in mu]
    eff = 0.9
    cos = _q61_int(_rcos(eff))
    sin = _q61_int(_rsin(eff))
    from srmech.amsc.rational import _q61_fxmul
    tw = [cos] + [_q61_fxmul(sin, mu_q61[i]) for i in range(1, 8)]
    ref = _octo_mult_q61(tw, s_q61) if form == "left" else _octo_mult_q61(s_q61, tw)
    native = _native.hypercomplex_couple_q61_c(
        s_q61, mu_q61, eff, form == "left")
    assert native == ref
