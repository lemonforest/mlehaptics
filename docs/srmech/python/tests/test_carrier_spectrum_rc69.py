"""carrier_spectrum — the OPERAND-side dual of ``the_one``: the carrier element's harmonic
occupancy under the shift-Laplacian (cyclic Class-I σ-spectrum + quasi-periodic Class-L
p-character blocks) + the BLOCK-DECOMPOSED (non-brute-force) elliptic key-equation solve.

Gates (the no-shell proofs):
  (a) on the canonical Frenkel–Turaev ₈ω₇ ``rk``, ``.cyclic`` + ``.blocks`` expose the
      very-well-poised DOUBLED-BEAT (the x² thetas → the k=±2 σ-eigen-entries) + the pair
      structure (the blocks). Non-trivial.
  (b) THE CRITICAL GATE: on a concrete key equation (``A·σ(Y) − B(x/q)·Y = RHS``), the
      block ``solve_key_equation`` reproduces the DENSE solve EXACTLY (same Y), AND the
      solve is GENUINELY block-decomposed — the per-block partition sizes SUM to the full
      basis with > 1 block, so it cannot be the dense solve relabeled.
  unit: σ preserves the p-character block for 4 canonical carriers → 4 distinct blocks (the
      orthogonality lever).
  parity: Python==C on the spectrum (skipped when the native peer is absent).
"""

import os
import re
import tokenize

import pytest

from srmech.amsc.ellbase import EllMonomial as M, Theta, EllRatio as R, _X, _Q_SYM
from srmech.amsc.thetasum import ThetaSum, _Y, _net_period_multiplier_exps
from srmech.amsc.q import Q
from srmech.amsc import carrier_spectrum as csmod
from srmech.amsc.carrier_spectrum import CarrierSpectrum, carrier_spectrum


def _make_8w7():
    """The canonical Frenkel–Turaev ₈ω₇ term-ratio ``t(n+1)/t(n)`` (``x = qⁿ``,
    ``y = qⁿ``) with the balancing ``bcde = a²q^{n+1}`` (Warnaar Cor 2.2)."""
    xk = M.symbol(_X); q = M.symbol(_Q_SYM); y = M.symbol(_Y)
    a = M.symbol("a"); b = M.symbol("b"); c = M.symbol("c"); d = M.symbol("d")
    e = (a * a * q * y) * (b * c * d).inv()
    poch = [b, c, d, e, y.inv()]
    num = [Theta(a * q * q * xk * xk), Theta(a * xk)]
    den = [Theta(a * xk * xk), Theta(q * xk)]
    for u in poch:
        num.append(Theta(u * xk)); den.append(Theta(a * q * xk * u.inv()))
    return R(q, num=num, den=den)


# ── unit: σ preserves the p-character block for 4 carriers → 4 distinct blocks ──────
def test_sigma_preserves_block_four_distinct():
    """The orthogonality lever: σ (x ↦ q·x) preserves the σ-invariant p-character block,
    and 4 canonical carriers map to 4 DISTINCT blocks (Channel 1 ⊥ Channel 2)."""
    xk = M.symbol(_X); q = M.symbol(_Q_SYM)
    a = M.symbol("a"); b = M.symbol("b")
    carriers = {
        "theta(x)": R(num=[Theta(xk)]),
        "theta(ax)": R(num=[Theta(a * xk)]),
        "theta(x)theta(ax)": R(num=[Theta(xk), Theta(a * xk)]),
        "theta(bx)": R(num=[Theta(b * xk)]),
    }
    labels = {}
    for name, E in carriers.items():
        cs = CarrierSpectrum(E)
        before = sorted(cs.blocks)
        sig = CarrierSpectrum(E.qshift())
        after = sorted(sig.blocks)
        assert before == after, f"σ did NOT preserve the block for {name}"
        labels[name] = tuple(before)
    assert len(set(labels.values())) == 4, "the 4 carriers must give 4 distinct blocks"


# ── (a) the ₈ω₇ spectrum exposes the doubled-beat + pair structure ──────────────────
def test_8w7_cyclic_exposes_doubled_beat():
    """Channel 1 (Class-I): the ₈ω₇ σ-eigenspectrum carries the very-well-poised
    DOUBLED-BEAT — the x² thetas show up as the k = ±2 σ-eigen-entries (non-trivial)."""
    cs = CarrierSpectrum(_make_8w7())
    cyc = cs.cyclic
    assert -2 in cyc, "the VWP doubled-beat (x^-2 theta) must appear as a σ-eigen-entry"
    assert cyc[-2] == "q**-2"
    assert -1 in cyc and cyc[-1] == "q**-1"      # the linear (Pochhammer) factors
    assert 1 in cyc                              # the x^1 den factor (θ(... x ...))


def test_8w7_blocks_nontrivial_pair_structure():
    """Channel 2 (Class-L): the ₈ω₇ p-character block partition is non-trivial — the
    x² doubled-beat thetas occupy their own higher-degree blocks, distinct from the linear
    Pochhammer blocks (the pair structure)."""
    cs = CarrierSpectrum(_make_8w7())
    blocks = cs.blocks
    assert len(blocks) > 1, "the ₈ω₇ must split into several p-character blocks"
    # every numerator+denominator theta is placed in exactly one block; total placed = 14.
    total = sum(len(v) for v in blocks.values())
    assert total == 14, f"all 14 thetas must be placed in a block; got {total}"
    # the x²-degree (doubled-beat) blocks are present and distinct from x¹ blocks.
    x_degrees = set()
    for lab in blocks:
        d = dict(lab)
        x_degrees.add(d.get("x", 0))
    assert len(x_degrees) > 1, "the doubled-beat must give a distinct x-degree block"


# ── (b) THE CRITICAL GATE: block solve == dense solve, genuinely per-block ───────────
def _controlled_key_equation():
    """A controlled key equation ``A·σ(Y) − B(x/q)·Y = RHS`` with a KNOWN multi-block
    solution. A and B(x/q) share the σ-invariant block (B(x/q) is the σ⁻¹ frame of A), so
    the system is block-DIAGONAL over a 3-element, 3-block basis."""
    xk = M.symbol(_X); q = M.symbol(_Q_SYM)
    a = M.symbol("a"); b = M.symbol("b"); c = M.symbol("c")
    A = R(num=(Theta(a * xk * xk), Theta(xk)))
    Bxq = R(num=(Theta(a * q * xk * xk), Theta(q * xk)))   # the σ⁻¹ frame of A (same block)
    basis = [(Theta(b * xk),), (Theta(c * xk),), (Theta(b * xk), Theta(c * xk))]
    known = [Q(2, 1), Q(-3, 1), Q(5, 1)]
    # RHS = L(known Y) so the system is consistent with the known solution.
    rhs = ThetaSum.zero()
    for ci, bb in zip(known, basis):
        rhs = rhs + csmod._apply_L(A, Bxq, bb).scalar_mul(ci)
    return A, Bxq, basis, known, rhs


def test_key_equation_block_equals_dense_and_known():
    """The block solve REPRODUCES the dense solve EXACTLY and recovers the known
    certificate — the no-shell correctness check."""
    A, Bxq, basis, known, rhs = _controlled_key_equation()
    cs = CarrierSpectrum(A)
    dense = cs.solve_key_equation_dense(rhs, a=A, b_xq=Bxq, basis=basis)
    block = cs.solve_key_equation(rhs, a=A, b_xq=Bxq, basis=basis)
    assert dense == known, f"dense solve {dense} != known {known}"
    assert block == known, f"block solve {block} != known {known}"
    assert block == dense, "block solve must reproduce the dense solve EXACTLY"


def test_key_equation_is_genuinely_per_block():
    """THE NO-SHELL PROOF: the solve is genuinely block-DECOMPOSED — the per-block partition
    has > 1 block, each block solves over ONLY its own basis columns, and the per-block
    unknown counts SUM to the full basis (so it cannot be one dense solve relabeled)."""
    A, Bxq, basis, known, rhs = _controlled_key_equation()
    cs = CarrierSpectrum(A)
    block, report = cs.solve_key_equation(rhs, a=A, b_xq=Bxq, basis=basis,
                                          return_report=True)
    assert report["block_decomposed"] is True
    assert report["n_blocks"] > 1, "a genuine multi-block system must have > 1 block"
    # each block solved over only its own columns; the unknown counts sum to the basis.
    per_block = report["blocks"]
    total_unknowns = sum(n_unk for (n_unk, _n_rows) in per_block.values())
    assert total_unknowns == len(basis), (
        f"per-block unknowns {total_unknowns} must SUM to the basis {len(basis)} — "
        "else the block solve is the dense solve in disguise")
    # no single block holds the whole basis (the dense-in-disguise signature).
    assert all(n_unk < len(basis) for (n_unk, _r) in per_block.values()), (
        "no block may hold the entire basis (that would be the dense solve relabeled)")
    assert block == known


def test_8w7_spectrum_blocks_and_cyclic_printable():
    """Gate (a) end-to-end: the public op returns a non-trivial cyclic + blocks dict on the
    ₈ω₇ (the operand-dual read), with the live CarrierSpectrum under 'spectrum'."""
    res = carrier_spectrum(_make_8w7())
    assert res is not None
    assert isinstance(res["spectrum"], CarrierSpectrum)
    assert res["n_blocks"] > 1
    assert len(res["cyclic"]) >= 3               # several distinct σ-eigenvalues
    assert -2 in res["cyclic"]                    # the doubled-beat


# ── operand-coercion + error surface ────────────────────────────────────────────────
def test_lifts_monomial_and_theta():
    """An EllMonomial / Theta operand is lifted to an EllRatio carrier element."""
    assert carrier_spectrum(M.symbol("a")) is not None
    assert carrier_spectrum(Theta(M.symbol(_X))) is not None


def test_non_carrier_raises():
    with pytest.raises(TypeError):
        carrier_spectrum(42)


# ── Python==C parity on the spectrum (skipped when native absent) ───────────────────
def _has_native():
    from srmech.amsc import _native
    return getattr(_native, "has_native_carrier_spectrum", lambda: False)()


@pytest.mark.skipif(not _has_native(),
                    reason="native srmech_carrier_spectrum not loaded "
                           "(pure-Python is the complete alternative)")
def test_python_equals_c_spectrum():
    """Drive BOTH the C and pure paths on the ₈ω₇ and compare the spectrum (channels) —
    do NOT trust the C (the rc67 hardening lesson)."""
    from srmech.amsc import _native
    rk = _make_8w7()
    form = csmod._ratio_to_form(rk)
    c_got = _native.carrier_spectrum_c(form)
    assert c_got is not None
    c_cyclic, c_blocks = c_got
    pure = CarrierSpectrum(rk)
    assert c_cyclic == pure.cyclic
    assert csmod._blocks_match(c_blocks, pure.blocks)


# ── discipline: no numpy / math / abs() in the op source ────────────────────────────
def test_source_is_numpy_math_abs_free():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = os.path.join(here, "srmech", "amsc", "carrier_spectrum.py")
    with tokenize.open(src) as fh:
        text = fh.read()
    assert "import numpy" not in text
    assert "import math" not in text
    assert re.search(r"abs\([^)]", text) is None         # no bare abs() CALL


# ── the ToolEntry is registered + invocable ─────────────────────────────────────────
def test_tool_entry_registered():
    from srmech.amsc import tool_schema
    names = {t.name for t in tool_schema.get_tool_schema().tools}
    assert "srmech.amsc.carrier_spectrum.carrier_spectrum" in names
