"""rc466 (`#T1188`) — the SEVENTY-ROW drain: the FIX half, gated.

WHAT THIS FILE IS
=================
rc465 replaced rc463's six hand-written demotion rows with a registry-driven
probe and found the population: **77 undeclared silent carrier demotions**, of
which it fixed nine and labelled seventy as debt (``tests/demotion_census.ndjson``,
``EXPECTED_UNDECLARED_N = {"native": 70, "pure": 71}``). This rc drains that
roster. The judgement was PER OP, and it is recorded per op in the CHANGELOG:
**FIX** (an exact carrier end to end, float as the caller's own request) wherever
an exact peer ships; **DECLARE** (an R3 accuracy sentence a caller can read
before calling) only where the op is float by nature — because declaring an op
that could have been fixed converts a defect into documentation.

This file holds the FIX half: forty-seven roster rows over thirty-nine ops
(plus, since the rc466 review, the five eigen-family rows — ``hermitian_`` /
``symmetric_eigendecompose``, ``three_fold_eigvec_groups``, ``fiedler_vector``,
``klein4_relational_structure`` — which Stage 2 had DECLARED on the ground that
an ``exact=`` route would be "two algorithms of different cost class wearing
one name", a ruling ``jacobi_eigvals(exact=True)`` in the same module already
contradicted; they now carry the keyword, an executed route through
``eig_exact``, and the rows below), plus three unrostered ``hdc`` siblings (``loop_bind_hd`` / ``loop_unbind_hd`` /
``loop_runbind_hd``, which share the same entry gate and demoted identically —
the census filed them ``INEXACT_BASE`` only because the harvested example
carried a float in the OTHER operand) and one hidden roster member
(``odft_summand``, "declared" through rc465 by the NEGATED phrase *"not a
tolerance"*, which the R3 keyword reader counted as a declaration).

THE RULES THE FIXES OBEY (and this file executes)
=================================================
F1  **No keyword without an executed route.** An ``exact=`` parameter drains a
    census row by its mere presence (``tools/demotion_probe.py``'s R3 reader
    counts ``exact= opt-in``), so every keyword builder below has a row that
    RUNS the exact route on the 2**53+1 witness.
F2  **Whole-operand admission**: one float anywhere elects the float route,
    byte-for-byte the shipped behaviour. Mixing carriers mid-computation is the
    defect, not the cure.
F3  **Refusals stay carrier-independent**, and an exact operand never falls
    silently to float — it raises where the exact carrier cannot hold it,
    naming the carrier that could.
F4  **No ``abs()``** — Class-K pin-slot branches throughout.

THE ONE FINDING THIS RC NAMES RATHER THAN HIDES
===============================================
The C compose host (``c/src/srmech_compose_run.c``) has no rational value kind
and its twins of six chain steps coerce to doubles (five at Stage 1; the sixth,
``kuramoto_sin_term``, joined at the rc466 review when the op began forming an
exact phase DIFFERENCE for exact phases — the C twin ``cr_op_kur_sin_term``
reads both phases as doubles). After this rc a declared
chain run over an EXACT input is exact in the Python runner and rounded in the
C host. That is a projection divergence the census cannot see (it probes
Python ops), so it is pinned here BY NAME (:data:`_COMPOSE_HOST_FLOAT_ONLY`)
with a test that runs one exact proof case through BOTH executors and asserts
that the disagreement EXISTS — the co-equal-dual-construction stance: the
disagreement is the finding. The drain path is a Q61-bigint arm in the C host
(an ABI-bump class of change; a later rc).

numpy-free. No ``abs()`` — the significand read is a Class-K pin-slot branch.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from srmech.math.q import Q
from srmech.math.qi import Qi
from srmech.math.qmat import QMat
from srmech.math.mat import Mat

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

#: ``2**53 + 1`` — the smallest positive integer float64 cannot represent.
P = 2 ** 53 + 1
#: Its two neighbours: the float carrier collapses P onto F and keeps G apart.
F = 2 ** 53
G = 2 ** 53 + 2


def _significand_bits(n: int) -> int:
    """Class-K pin-slot on the sign; never an ALU ``abs()``."""
    if n < 0:
        n = -n
    if n == 0:
        return 0
    while n % 2 == 0:
        n //= 2
    return n.bit_length()


def _discriminating(v) -> bool:
    """Layer-0: could this oracle have been rounded? True iff its exact value
    has more than 53 significand bits and the float carrier changes it."""
    if isinstance(v, Q):
        return float(v) != v and (_significand_bits(v.numerator) > 53
                                  or _significand_bits(v.denominator) > 53)
    return _significand_bits(v) > 53 and float(v) != v


def _e(i, n=8):
    return [1 if k == i else 0 for k in range(n)]


def _o(w):
    return [w] + [0] * 7


# The rc467 (`#T1188`) resonant_spectrum witness — the 3-node PATH Laplacian
# with weights (2**53+1, 1). Exact spectrum: 0, a degree-2 algebraic near 3/2,
# and a degree-2 algebraic near 1.8e16. The float route's answers for the first
# two are 0.13144078898136016 and 1.5756659922051879 — wrong by O(0.1) — and
# its resonance list comes back EMPTY.
_RS_PATH3 = [[P, -P, 0], [-P, P + 1, -1], [0, -1, 1]]


# ── LAYER 1 — strict-zero exactness, one row per PATH, every row executes ─────
def _rows():
    from srmech.math import hdc, laplacian as la
    from srmech.cascade import (hypercomplex_couple, cd_couple_working,
                                cdr_couple_working, as_oct8, as_quat4,
                                qdft_summand, odft_summand, correlation_product,
                                compensated_sum)
    from srmech.cascade.coupled import multiplex_streams
    from srmech.signal_processing import _fft_carrier as _fc
    from srmech.signal_processing.closed_form_ops import (stft, ofdm, polyphase,
                                                          multirate, farrow, iir,
                                                          wavelet)
    from srmech.physics.qm.relativistic import four_momentum_squared
    from srmech.physics.qm.pseudo_hermitian import inner_product_eta
    from srmech.physics.qm.single_particle import density_matrix
    from srmech.physics.qm.bell import operator_norm
    from srmech.physics.qm.quaternion import quaternion_log
    from srmech.biology.coupling import resonant_spectrum
    mu4 = [0.0, 1.0, 0.0, 0.0]
    mu8 = [0.0, 1.0] + [0.0] * 6
    return [
        # ── math.hdc — the Cayley-Dickson loop family (13 ops) ───────────────
        ("hdc.loop_conj[int]", lambda: hdc.loop_conj(_o(P))[0], P),
        ("hdc.loop_conj[(num,den) pair]", lambda: hdc.loop_conj([(P, 1)] + [0] * 7)[0], P),
        ("hdc.loop_bind[int]", lambda: hdc.loop_bind(_o(P), _e(0))[0], P),
        ("hdc.loop_bind[dim 4]", lambda: hdc.loop_bind([P, 0, 0, 0], [1, 0, 0, 0])[0], P),
        ("hdc.loop_inv[int]", lambda: hdc.loop_inv(_o(P))[0], Q(1, P)),
        ("hdc.loop_left_op[int]", lambda: hdc.loop_left_op(_o(P))[0, 0], P),
        ("hdc.loop_right_op[int]", lambda: hdc.loop_right_op(_o(P))[0, 0], P),
        ("hdc.loop_associator[int]",
         lambda: hdc.loop_associator([0, 0, 0, 0, P, 0, 0, 0], _e(1), _e(2))[7], 2 * P),
        ("hdc.cross7[int]", lambda: hdc.cross7([0, P] + [0] * 6, _e(2))[3], P),
        ("hdc.g2_three_form[int]", lambda: hdc.g2_three_form([0, P] + [0] * 6, _e(2), _e(3)), P),
        ("hdc.loop_conj_hd[int, 2 blocks]", lambda: hdc.loop_conj_hd(_o(P) + _e(0))[0], P),
        ("hdc.loop_inv_hd[int, 2 blocks]", lambda: hdc.loop_inv_hd(_o(P) + _e(0))[0], Q(1, P)),
        ("hdc.loop_bind_hd[int, 2 blocks] (UNROSTERED)",
         lambda: hdc.loop_bind_hd(_o(P) + _e(0), _e(0) + _e(0))[0], P),
        ("hdc.loop_unbind_hd[int, 2 blocks] (UNROSTERED)",
         lambda: hdc.loop_unbind_hd(_e(0) + _e(0), _o(P) + _e(0))[0], P),
        ("hdc.loop_runbind_hd[int, 2 blocks] (UNROSTERED)",
         lambda: hdc.loop_runbind_hd(_e(0) + _e(0), _o(P) + _e(0))[0], P),
        # ── cascade ──────────────────────────────────────────────────────────
        ("cascade.hypercomplex_couple[int, theta=0.0]",
         lambda: hypercomplex_couple([P, 0, 0], theta=0.0)[1], P),
        ("cascade.hypercomplex_couple[int literal octonion, theta=0.0]",
         lambda: hypercomplex_couple(_o(P), theta=0.0)[0], P),
        ("cascade.as_oct8[int]", lambda: as_oct8([P, 0, 0, 0])[0], P),
        ("cascade.as_quat4[int, 4]", lambda: as_quat4([P, 0, 0, 0])[0], P),
        ("cascade.as_quat4[int, 8 -> 4]", lambda: as_quat4([P, 0, 0, 0, 0, 0, 0, 0])[0], P),
        ("cascade.qdft_summand[int, k*m == 0 mod n, left]",
         lambda: qdft_summand([[P, 0, 0, 0]], 0, 0, 1, True, -1, mu4)[0], P),
        ("cascade.qdft_summand[int, k*m == 0 mod n, right]",
         lambda: qdft_summand([[P, 0, 0, 0]], 0, 0, 1, False, -1, mu4)[0], P),
        ("cascade.odft_summand[int, left]",
         lambda: odft_summand([_o(P)], 0, 0, 1, "left", "left_associated", -1, mu8, mu8)[0], P),
        ("cascade.odft_summand[int, two_sided left_associated]",
         lambda: odft_summand([_o(P)], 0, 0, 1, "two_sided", "left_associated", -1, mu8, mu8)[0], P),
        ("cascade.odft_summand[int, two_sided right_associated]",
         lambda: odft_summand([_o(P)], 0, 0, 1, "two_sided", "right_associated", -1, mu8, mu8)[0], P),
        ("cascade.correlation_product[int]",
         lambda: correlation_product([3, 3002399751580331], 0, 1), P),
        ("cascade.compensated_sum[Q] (the chain's next step)",
         lambda: compensated_sum([Q(P), Q(0)]), P),
        ("cascade.coupled.multiplex_streams[int, roundrobin]",
         lambda: multiplex_streams([[P, 2], [3, 4]])["driver"][0], P),
        ("cascade.coupled.multiplex_streams[int, pickbest]",
         lambda: multiplex_streams([[P, 2], [3, 4]], mode="pickbest")["driver"][0], P),
        ("cascade.coupled.multiplex_streams[int, superpose]",
         lambda: multiplex_streams([[P, 2], [0, 0]], mode="superpose")["driver"][1], Q(2, P)),
        # ── math.laplacian — the five keyword builders + two operand-typed ops ─
        ("laplacian.klein4_gain_laplacian[exact=True]",
         lambda: la.klein4_gain_laplacian(2, [(0, 1)], [P], exact=True)["chi00"][0][0], P),
        ("laplacian.klein4_gain_laplacian[exact=True, chi01 sign]",
         lambda: la.klein4_gain_laplacian(2, [(0, 1)], [P], exact=True)["chi01"][0][1], -P),
        ("laplacian.mass_normalized_laplacian[exact=True, symmetric, masses=1]",
         lambda: la.mass_normalized_laplacian(2, [(0, 1)], [P], masses=[1, 1], exact=True)[0][0], P),
        ("laplacian.mass_normalized_laplacian[exact=True, rw]",
         lambda: la.mass_normalized_laplacian(2, [(0, 1)], [P], masses=[1, 1], kind="rw", exact=True)[0][1], -P),
        ("laplacian.normalized_laplacian[exact=True, K4 with P weights: -1/3 on the nose]",
         lambda: la.normalized_laplacian(4, [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)], [P] * 6,
                                         exact=True)[0][1] * (3 * P), -P),
        ("laplacian.magnetic_laplacian[exact=True, q=0]",
         lambda: la.magnetic_laplacian(2, [(0, 1)], [P], q=0, exact=True)[0][0].real * 2, P),
        ("laplacian.magnetic_laplacian[exact=True, default q=1/4 -> phase i]",
         lambda: la.magnetic_laplacian(2, [(0, 1)], [P], exact=True)[0][1].imag * -2, P),
        ("laplacian.magnetic_laplacian[exact=True, charges]",
         lambda: la.magnetic_laplacian(2, [(0, 1)], [P], charges=[Q(1, 2)], exact=True)[1][0].real * 2, P),
        ("laplacian.quaternion_laplacian[exact=True]",
         lambda: la.quaternion_laplacian(2, [(0, 1)], [P], exact=True)[0][0] * 2, P),
        ("laplacian.quaternion_laplacian[exact=True, off-diagonal block]",
         lambda: la.quaternion_laplacian(2, [(0, 1)], [P], exact=True)[0][4] * -2, P),
        # ── math.laplacian — the eigen family's exact route (rc466 review fix).
        #    Every row reads the exact object back through Qalg.as_rational():
        #    a rational eigenvalue / coordinate IS its Q, no lift anywhere.
        ("laplacian.symmetric_eigendecompose[exact=True, diagonal witness]",
         lambda: la.symmetric_eigendecompose([[P, 0], [0, 0]], exact=True)[0][1].as_rational(), P),
        ("laplacian.symmetric_eigendecompose[exact=True, K2 with weight P: lambda_2 = 2P]",
         lambda: la.symmetric_eigendecompose([[P, -P], [-P, P]], exact=True)[0][1].as_rational(), 2 * P),
        ("laplacian.symmetric_eigendecompose[exact=True, rank-1 [[1,P],[P,P^2]]: the null vector is (-P, 1)]",
         lambda: (-la.symmetric_eigendecompose([[1, P], [P, P * P]], exact=True)[1][0][0]).as_rational(), P),
        ("laplacian.symmetric_eigendecompose[exact=True, rational operand rides the pre-scale]",
         lambda: la.symmetric_eigendecompose([[Q(P, 2), 0], [0, 0]], exact=True)[0][1].as_rational(), Q(P, 2)),
        ("laplacian.hermitian_eigendecompose[exact=True, real-exact operand]",
         lambda: la.hermitian_eigendecompose([[P, 0], [0, 0]], exact=True)[0][1].as_rational(), P),
        ("laplacian.hermitian_eigendecompose[exact=True, Qi with zero imaginary part]",
         lambda: la.hermitian_eigendecompose([[Qi(P, 0), 0], [0, 0]], exact=True)[0][1].as_rational(), P),
        ("laplacian.fiedler_vector[exact=True, rank-1: the lambda_2 vector is (1/P, 1)]",
         lambda: la.fiedler_vector([[1, P], [P, P * P]], exact=True)[0].as_rational(), Q(1, P)),
        ("laplacian.three_fold_eigvec_groups[exact=True, rank-1: the mid band holds the null vector (-P, 1)]",
         lambda: (-la.three_fold_eigvec_groups([[1, P], [P, P * P]], exact=True)["mid"][0][0]).as_rational(), P),
        ("laplacian.klein4_relational_structure[exact=True, K2 weight P: coherence chi00 = 2P]",
         lambda: la.klein4_relational_structure([(0, 1)], [P], exact=True)["coherence"]["chi00"].as_rational(), 2 * P),
        ("laplacian.klein4_relational_structure[exact=True, frustrated triangle: tension chi10 = P]",
         lambda: la.klein4_relational_structure([(0, 1), (1, 2), (2, 0)], [P, P, P], gains=[1, 0, 0],
                                                exact=True)["tension"]["chi10"].as_rational(), P),
        ("laplacian.klein4_relational_structure[exact=True, frustrated triangle: sector_asymmetry lo == hi == P]",
         lambda: la.klein4_relational_structure([(0, 1), (1, 2), (2, 0)], [P, P, P], gains=[1, 0, 0],
                                                exact=True)["sector_asymmetry"][0], P),
        ("laplacian.elementwise_multiply_complex[int, 1-D]",
         lambda: la.elementwise_multiply_complex([P], [1])[0].real, P),
        ("laplacian.elementwise_multiply_complex[int, 2-D]",
         lambda: la.elementwise_multiply_complex([[P, 0], [0, 1]], [[1, 0], [0, 1]])[0][0].real, P),
        # ── signal_processing (the three terminal-lift ROUTES — rfft / stft /
        #    ofdm — are DIFFERENTIAL witnesses and live in their own test below)
        ("signal_processing.polyphase[int, decimation]",
         lambda: polyphase.op([P, 2, 3], [1, 2, 3, 4], L=2)[0], P + 4),
        ("signal_processing.polyphase[int, interpolation]",
         lambda: polyphase.op([P, 1], [1, 1], L=2, mode="interpolation")[0], P),
        ("signal_processing.multirate[int, identity]", lambda: multirate.op([P, 2, 3, 4])[0], P),
        ("signal_processing.multirate[int, int taps]",
         lambda: multirate.op([P, 1, 1], up=2, filter_taps=[1, 1])[0], 2 * P),
        ("signal_processing.farrow[int, mu=0 passthrough]", lambda: farrow.op([0, 1, P, 3])[2], P),
        ("signal_processing.farrow[int, mu=Q(1,2)]",
         lambda: farrow.op([0, P, 1, 2, 0, 0], mu=Q(1, 2))[0], Q(11258999068426241, 4)),
        ("signal_processing.farrow[int, mu=(1,2) pair]",
         lambda: farrow.op([0, P, 1, 2, 0, 0], mu=(1, 2))[0], Q(11258999068426241, 4)),
        ("signal_processing.iir[int, a0 = 1 -> integer output]",
         lambda: iir.op([1, 0, 0], [1], [1, P])[1], -P),
        ("signal_processing.iir[int, a = [P, 1] -> Q output]",
         lambda: iir.op([1, 0, 0], [1], [P, 1])[0], Q(1, P)),
        ("signal_processing.iir[int, biquad cascade]",
         lambda: iir.op([1, 0, 0], [1], [1], biquad_sections=[[1, 0, 0, 1, -P, 0]])[1], P),
        ("signal_processing.wavelet[int, 2 levels -> exact rational]",
         lambda: wavelet.op([P, 4, 4, 4], levels=2)[0][0].as_rational(), Q(P + 12, 2)),
        # ── physics.qm singletons ─────────────────────────────────────────────
        ("relativistic.four_momentum_squared[int]", lambda: four_momentum_squared([P, 0, 0, 0]), P * P),
        ("relativistic.four_momentum_squared[int, spacelike]",
         lambda: four_momentum_squared([0, P, 1, 0]), -P * P - 1),
        ("pseudo_hermitian.inner_product_eta[int eta]",
         lambda: inner_product_eta([1, 0], [1, 0], [[P, 0], [0, 1]]).real, P),
        ("pseudo_hermitian.inner_product_eta[QMat eta]",
         lambda: inner_product_eta([1, 0], [1, 0], QMat.from_rows([[P, 0], [0, 1]])).real, P),
        ("pseudo_hermitian.inner_product_eta[Qi leaf]",
         lambda: inner_product_eta([Qi(0, 1), 0], [Qi(0, P), 0], [[1, 0], [0, 1]]).real, P),
        ("single_particle.density_matrix[int -> QMat]", lambda: density_matrix([P, 1])[0, 1], P),
        ("single_particle.density_matrix[Qi -> rows of Qi]",
         lambda: density_matrix([Qi(P, 1), 1])[0][1].real, P),
        ("quaternion.quaternion_log[int, the direction is exact]",
         lambda: quaternion_log([0, P, 0, 0])[1] - quaternion_log([0, 1, 0, 0])[1] + P, P),
        ("quaternion.quaternion_log[(num,den) pair no longer refused]",
         lambda: quaternion_log([(0, 1), (P, 1), 0, 0])[1] - quaternion_log([0, 1, 0, 0])[1] + P, P),
        # ── biology.coupling — the LAST undeclared demoter (rc467, `#T1188`) ──
        # Both rows RUN the exact route; neither merely observes the keyword.
        # The first is the CENSUS witness itself — demotion_probe synthesises
        # the Mat-shaped operand as the 2x2 identity with the leaf at [0][0]
        # — so the row that drains census row 20 is the row executed here.
        ("coupling.resonant_spectrum[int, the census witness -> exact tension]",
         lambda: resonant_spectrum([[P, 0], [0, 1]], exact=True)["tensions"][1].as_rational(), P),
        ("coupling.resonant_spectrum[int, exact force_orders on the path-3 witness]",
         lambda: resonant_spectrum(_RS_PATH3, exact=True)["force_orders"][1].to_lists()[0][0],
         2 * P * P),
    ]


def _eq_exact(got, want) -> bool:
    if isinstance(got, complex) or isinstance(want, complex):
        return got == want
    return got == want and float(got) == float(want)


@pytest.mark.parametrize("label,call,want", _rows(), ids=[r[0] for r in _rows()])
def test_layer1_exact_in_exact_out(label, call, want) -> None:
    """STRICT ZERO. Every row executes the exact route on a witness the float
    carrier would have rounded, and must return the exact value."""
    assert _discriminating(want if not isinstance(want, int) or want > 0 else -want), (
        f"Layer-0 rejected the witness for {label}: it could not have failed")
    got = call()
    assert _eq_exact(got, want), (
        f"SILENT CARRIER DEMOTION at {label}: got {got!r}, exact value is "
        f"{want!r}. rc466 gave this path an exact carrier — fix the carrier, "
        f"do not widen a tolerance.")


# ── the terminal-lift ROUTES: the operand reaches the exact engine ───────────
def test_the_fft_family_hands_the_operand_to_the_exact_engine() -> None:
    """rfft / stft / ofdm return ``complex`` — a single terminal float lift of an
    exact-until-rotation transform — so the witness is DIFFERENTIAL: through
    rc465 the entry ``complex(x)`` collapsed 2**53+1 onto 2**53 BEFORE the exact
    engine ran, and the two witnesses gave the SAME bins. Now the engine sees
    P, and a bin the lift can represent (Σx = 2**53 for the alternating signal;
    (P + 3)/4 = 2251799813685249 for the OFDM block) comes back distinct from
    the F witness's."""
    from srmech.signal_processing import _fft_carrier as _fc
    from srmech.cascade import spectral_cascades as _sc
    from srmech.signal_processing.closed_form_ops import stft, ofdm
    sig_p = [P, 0, -1, 0, 1, 0, -1, 0]
    sig_f = [F, 0, -1, 0, 1, 0, -1, 0]
    assert _fc.rfft(sig_p)[0] == _sc.fft(sig_p)[0] == 2 ** 53          # the DC bin is exact Σx
    assert _fc.rfft(sig_f)[0] == 2 ** 53 - 1
    assert _fc.rfft(sig_p)[0] != 9007199254740991 + 0j                # the rc465 value
    assert _fc.rfft([P, -1])[0] == 2 ** 53 and _fc.rfft([F, -1])[0] == 2 ** 53 - 1
    win = [1] * 8
    assert stft.op([P, -1, 1, -1, 1, -1, 1, -1], frame_size=8, window=win)[0][0] == 2 ** 53
    assert stft.op([F, -1, 1, -1, 1, -1, 1, -1], frame_size=8, window=win)[0][0] == 2 ** 53 - 1
    # the IFFT lift is float(Σ)/N, so the witness needs Σ float-representable on
    # BOTH sides: Σ_P = P − 1 = 2**53 and Σ_F = 2**53 − 1 are, and they differ.
    assert ofdm.op([P, -1, 0, 0], n_subcarriers=4, cp_length=1)[1] == 2 ** 51
    assert ofdm.op([F, -1, 0, 0], n_subcarriers=4, cp_length=1)[1] == 2 ** 51 - 0.25
    # the float route is unchanged: a float signal takes the float64 carrier
    assert _fc.rfft([1.0, 2.0, 3.0, 4.0]) == [(10 + 0j), (-2 + 2j), (-2 + 0j)]


# ── the exact ROUTES with a declared bound (the octonion_norm shape) ──────────
def test_operator_norm_exact_route_is_within_its_declared_bound() -> None:
    from srmech.physics.qm.bell import operator_norm
    on = operator_norm([[P, 0], [0, 0]])
    assert isinstance(on, Q), type(on)
    d = on - P
    d = d if d >= 0 else -d                           # Class-K pin-slot, no abs()
    assert d <= Q(1, 2 ** 60), f"declared accurate to 2**-64; measured {float(d)}"
    # the two witnesses the float carrier collapses are DISTINCT on this route
    assert on != operator_norm([[F, 0], [0, 0]])
    # a Gaussian-exact Hermitian H rides the real 2n×2n embedding
    g = operator_norm([[0, Qi(0, -P)], [Qi(0, P), 0]])
    dg = g - P
    dg = dg if dg >= 0 else -dg
    assert isinstance(g, Q) and dg <= Q(1, 2 ** 60)
    # a rational H no longer falls to float inside the peer (the rc466 pre-scale)
    r = operator_norm([[Q(1, 2), 0], [0, Q(1, 3)]])
    dr = r - Q(1, 2)
    dr = dr if dr >= 0 else -dr
    assert isinstance(r, Q) and dr <= Q(1, 2 ** 60)


def test_the_eigen_family_exact_route_refuses_rather_than_rounds() -> None:
    """F3 for the five eigen-family ops (rc466 review fix): a float entry, a
    non-symmetric operand and a Gaussian-rational Hermitian operand are REFUSED
    by name on the exact route — never rounded, never silently re-routed to the
    float Jacobi — and the refusals name the carrier that could hold each."""
    from srmech.math import laplacian as la
    with pytest.raises(ValueError, match="EXACT"):
        la.symmetric_eigendecompose([[1.0, 0], [0, 2]], exact=True)
    with pytest.raises(ValueError, match="SYMMETRIC"):
        la.symmetric_eigendecompose([[1, 2], [0, 2]], exact=True)
    with pytest.raises(ValueError, match=r"Q\(λ, i\)"):
        la.hermitian_eigendecompose([[0, Qi(0, -1)], [Qi(0, 1), 0]], exact=True)
    with pytest.raises(ValueError, match="EXACT"):
        la.fiedler_vector([[1.0, 0], [0, 2.0]], exact=True)
    with pytest.raises(ValueError, match="EXACT"):
        la.three_fold_eigvec_groups([[1.0, 0], [0, 2.0]], exact=True)
    with pytest.raises(TypeError, match="exact=True requires EXACT weights"):
        la.klein4_relational_structure([(0, 1)], [1.5], exact=True)   # the builder's own refusal


def test_the_eigen_family_exact_route_orders_and_separates_where_float_cannot() -> None:
    """The two facts that make the route a FIX and not a keyword: (1) the
    exact spectrum of an operand the float route ROUNDS differs from the float
    route's — ``[[2**53+1, 1], [1, 0]]`` has largest eigenvalue
    ``9007199254740994.0`` exactly-then-lifted, ``9007199254740992.0`` rounded
    first; (2) two eigenvalues that TIE at float resolution come back in the
    exact ascending order — ``eig_exact`` returned ``[2**60+2, 2**60+1]`` for
    the diagonal witness before the review fix (measured)."""
    from srmech.math import laplacian as la
    exact_top = la.symmetric_eigendecompose([[P, 1], [1, 0]], exact=True)[0][1].to_float()
    float_top = float(la.symmetric_eigendecompose([[P, 1], [1, 0]])[0][1])
    assert exact_top == 9007199254740994.0 and float_top == 9007199254740992.0
    vals = la.symmetric_eigendecompose([[2 ** 60 + 2, 0], [0, 2 ** 60 + 1]], exact=True)[0]
    assert [v.as_rational() for v in vals] == [2 ** 60 + 1, 2 ** 60 + 2]
    # a balanced sector's tension IS zero on the exact route (the docstring's
    # "0 exactly when balanced", literally true only here)
    k = la.klein4_relational_structure([(0, 1), (1, 2), (2, 0)], [1, 1, 1], exact=True)
    assert k["tension"]["chi00"] == 0 and k["sector_asymmetry"] == (Q(0, 1), Q(0, 1))
    # an irrational pair of mixed tensions comes back as an enclosure of exact Q
    k2 = la.klein4_relational_structure([(0, 1), (1, 2), (2, 0)], [1, 2, 3], gains=[1, 0, 0], exact=True)
    lo, hi = k2["sector_asymmetry"]
    assert isinstance(lo, Q) and isinstance(hi, Q) and lo <= hi and hi - lo < Q(1, 2 ** 62)


# ── rc467 (`#T1188`) — the LAST undeclared silent demoter, drained ───────────
def test_resonant_spectrum_exact_route_drains_the_last_undeclared_demoter() -> None:
    """rc466 drained seventy undeclared silent demoters to ONE and deferred that
    one — ``srmech.biology.coupling.resonant_spectrum::L`` — as "exact peer
    ships, deferred". The deferral's stated ground was that the ``modes``
    faculty "needs eigvec_exact with a caller-supplied IRREDUCIBLE minimal
    polynomial per eigenvalue". ``eig_exact`` supplies the irreducible minimal
    polynomial ITSELF, and this test runs all four faculties over exact
    carriers, so the ground is refuted BY EXECUTION and not by argument.

    The witness is the 3-node PATH Laplacian with weights ``(2**53+1, 1)``.
    Measured on the pure cell of this tree at rc467:

    * float route tensions ``[0.13144078898136016, 1.5756659922051879,
      1.8014398509481988e+16]`` where the exact answers are ``0`` and two
      degree-2 algebraics near ``3/2`` and ``1.8e16`` — the two small tensions
      are wrong by ``O(0.1)``;
    * float route ``resonances == []``;
    * float route ``force_orders[1][0][0] == 1.6225927682921347e+32`` against
      the exact ``2·P²`` whose own float is ``1.622592768292134e+32``.

    Those digits are recorded rather than asserted — a float Jacobi's low bits
    are an implementation detail — but they were measured in BOTH cells and are
    BYTE-IDENTICAL: the C peer ``srmech_resonant_spectrum`` is bound and IS the
    route taken in the native cell, and it returns the same three doubles, the
    same empty resonance list and the same ``1.6225927682921347e+32``. What is
    ASSERTED below is cell-independent all the same — the entry rounding, the
    structural emptiness of the float resonance list, and the exact values.
    """
    from srmech.biology.coupling import resonant_spectrum, _ZERO_TENSION_REL
    from srmech.math.mat import Mat
    from srmech.math.qalg import Qalg
    from srmech.math.qmat import QMat

    out = resonant_spectrum(_RS_PATH3, exact=True)

    # (1) tensions — exact Qalg, ascending, and the zero mode IS zero.
    vals = out["tensions"]
    assert isinstance(vals, list) and len(vals) == 3
    assert all(isinstance(v, Qalg) for v in vals)
    assert vals[0] == 0 and vals[0].as_rational() == 0
    # the two non-zero tensions are a conjugate pair over ONE degree-2 field
    assert vals[1].as_rational() is None and vals[1].m == vals[2].m
    assert len(vals[1].m) == 3                      # degree 2

    # (2) modes — exact eigenLINES, UNNORMALISED, one field per column.
    V = out["modes"]
    assert isinstance(V, list) and len(V) == 3 and all(len(r) == 3 for r in V)
    assert all(isinstance(V[i][j], Qalg) for i in range(3) for j in range(3))
    for j in range(3):                              # A·v == λ·v EXACTLY, per column
        col = [V[i][j] for i in range(3)]
        zero_j = col[0] * 0                         # each column has its OWN field
        for i in range(3):
            got = sum((_RS_PATH3[i][k] * col[k] for k in range(3)), zero_j)
            assert got == vals[j] * col[i]
    # the columns really are in DIFFERENT fields — Qalg refuses to mix them, by
    # name, which is the whole reason the modes faculty is declared per COLUMN.
    with pytest.raises(ValueError, match="requires equal m"):
        V[0][0] + V[0][1]
    col0 = [V[i][0] for i in range(3)]
    nsq0 = sum((c * c for c in col0), col0[0] * 0)
    assert nsq0 == 3 and not nsq0 == 1              # the constant vector, ‖·‖² = 3
    col1 = [V[i][1] for i in range(3)]
    nsq1 = sum((c * c for c in col1), col1[0] * 0)
    assert nsq1.as_rational() is None               # irrational — no unit column here

    # (3) force_orders — QMat powers of the OPERAND, entries plain Q.
    fo = out["force_orders"]
    assert len(fo) == 2 and all(isinstance(m, QMat) for m in fo)
    assert fo[0].to_lists()[0][0] == P
    assert fo[1].to_lists()[0][0] == 2 * P * P
    assert fo[1].to_lists()[0][0] == 162259276829213399420375029252098

    # (4) resonances — ONE record, CERTIFIED by both enclosure endpoints.
    res = out["resonances"]
    assert len(res) == 1
    r = res[0]
    assert set(r) == {"pair", "ratio", "den_coords", "locked",
                      "certified", "ratio_enclosure"}
    assert r["pair"] == (1, 2) and r["certified"] is True
    assert r["ratio_enclosure"] == (r["ratio"], r["ratio"])

    # ── the float route on the SAME operand, for contrast ────────────────────
    fl = resonant_spectrum([[float(x) for x in row] for row in _RS_PATH3])
    # (a) the entry rounding is carrier-structural — true in BOTH cells.
    assert Mat.from_rows([[float(P), 0.0], [0.0, 1.0]]).tolist()[0][0] != P
    # (b) the resonance list is EMPTY, and for a reason that is structural, not
    #     a digit accident: the free-mode floor is RELATIVE, so on this operand
    #     it sits at 1.8e16 · 1e-9 = 1.8e7 and discards a real tension of 3/2.
    assert fl["resonances"] == []
    lam_max = float(fl["tensions"][2])
    assert lam_max * _ZERO_TENSION_REL > 1.0e7 > float(vals[1].to_float())
    # (c) and the census witness itself: exact where the float route rounds.
    assert resonant_spectrum([[P, 0], [0, 1]], exact=True)["tensions"][1].as_rational() == P
    assert float(resonant_spectrum([[float(P), 0.0], [0.0, 1.0]])["tensions"][1]) == 2.0 ** 53


def test_resonant_spectrum_exact_route_refuses_rather_than_rounds() -> None:
    """F3 for the new route: every refusal names ``resonant_spectrum(exact=True)``
    — never the shared laplacian helper's own identity — and a ``Mat`` operand
    is REFUSED rather than silently accepted at 53 bits, because ``Mat`` IS the
    float64 carrier and its rows have already lost the low bit."""
    from srmech.biology.coupling import resonant_spectrum
    from srmech.math.mat import Mat
    for bad in (Mat.from_rows([[float(P), 0.0], [0.0, 1.0]]),
                [[1.0, 0], [0, 1]]):
        with pytest.raises(ValueError, match=r"resonant_spectrum\(exact=True\).*EXACT"):
            resonant_spectrum(bad, exact=True)
    with pytest.raises(ValueError, match=r"resonant_spectrum\(exact=True\).*SYMMETRIC"):
        resonant_spectrum([[1, 2], [3, 4]], exact=True)
    with pytest.raises(ValueError, match=r"resonant_spectrum\(exact=True\).*square"):
        resonant_spectrum([[1, 2, 3], [4, 5, 6]], exact=True)


def test_resonant_spectrum_exact_sign_pin_is_positivity_not_nonzero() -> None:
    """The Class-K sign pin, and why it is POSITIVITY rather than ``!= 0``.

    ``best_rational`` refuses a negative numerator, ``resonant_spectrum``
    validates only squareness and ``orders >= 1``, and an INDEFINITE
    real-symmetric operand is reachable through the public contract. A bare
    ``λ != 0`` test would keep the negative tension and then RAISE inside
    ``best_rational``; the float route never trips it only because its relative
    floor silently drops every non-positive tension. Both routes therefore drop
    it — the exact one by an exact sign read, and without ``abs()``."""
    from srmech.biology.coupling import resonant_spectrum
    ex = resonant_spectrum([[1, 2], [2, 1]], exact=True)
    assert [v.as_rational() for v in ex["tensions"]] == [-1, 3]
    assert ex["resonances"] == []                       # no adjacent POSITIVE pair
    assert resonant_spectrum([[1.0, 2.0], [2.0, 1.0]])["resonances"] == []


def test_resonant_spectrum_exact_reaches_a_rational_operand() -> None:
    """The pre-scale trap, executed. ``eig_exact`` isolates ``B = c·A`` for a
    rational operand, so each ``Qalg``'s minimal polynomial is that of ``c·λ``
    — and ``_symmetric_eig_exact`` DISCARDS the ``denominator_scale``. The
    exact route recovers ``c`` itself (a Class-I LCM of the entry denominators)
    so the sign pin and the bracket-containment check read ``λ.m`` in the right
    scale. Without that, containment fails on the irrational eigenvalues."""
    from srmech.biology import coupling as cp
    from srmech.math import laplacian as la
    from srmech.math.q import Q
    from srmech.cascade.matrix_cascades import eigvals_exact
    rows = [[Q(3, 4), Q(-3, 4), 0], [Q(-3, 4), Q(7, 4), -1], [0, -1, 1]]
    out = cp.resonant_spectrum(rows, orders=2, max_den=64, exact=True)
    assert out["tensions"][0] == 0
    assert len(out["resonances"]) == 1 and out["resonances"][0]["certified"] is True
    assert out["resonances"][0]["ratio"] == (8, 25)
    # the instrument has teeth: the SAME check at the wrong scale REFUSES.
    vals, _ = la._symmetric_eig_exact(rows, "probe")
    ivs = eigvals_exact(rows, return_intervals=True)
    assert cp._denominator_lcm(rows) == 4
    assert [cp._bracket_holds(vals[i], *ivs[i], 4) for i in range(3)] == [True, True, True]
    assert [cp._bracket_holds(vals[i], *ivs[i], 1) for i in range(3)] == [True, False, False]
    # and it discriminates a MISALIGNED bracket, which is what it is there for
    assert cp._bracket_holds(vals[0], *ivs[1], 4) is False


def test_resonant_spectrum_exact_certification_can_fail_and_says_so() -> None:
    """An instrument that cannot return otherwise is not a measurement. At the
    shipped default (``bits=64``) every enclosure in this corpus certifies; at
    ``bits=2`` the enclosure is wider than the gap between two admissible
    rationals, the bounded doubling retry (three further attempts) still cannot
    close it, and the record SAYS ``certified: False`` and carries BOTH anchors
    rather than picking one."""
    from srmech.biology import coupling as cp
    L = [[1, -1, 0, 0, 0], [-1, 2, -1, 0, 0], [0, -1, 2, -1, 0],
         [0, 0, -1, 2, -1], [0, 0, 0, -1, 1]]
    tight = cp._resonant_spectrum_exact(L, 2, 1_000_000, bits=64)
    assert [r["certified"] for r in tight["resonances"]] == [True, True, True]
    loose = cp._resonant_spectrum_exact(L, 2, 1_000_000, bits=2)
    assert [r["certified"] for r in loose["resonances"]] == [False, False, False]
    for r in loose["resonances"]:
        lo, hi = r["ratio_enclosure"]
        assert lo != hi and r["ratio"] == lo


def test_eig_exact_self_validation_is_exact_and_reaches_a_rational_matrix() -> None:
    """The exact peer's own instrument (rc466 review fix): ``eig_exact`` refused
    ``[[2**53+1, 1], [1, 0]]`` as a "factorisation bug" through a FLOAT
    reconstruction at an absolute 1e-7, and TRUNCATED a rational char-poly to
    ``int`` before factoring. Both are executed here as the fixed behaviour."""
    from srmech.cascade import matrix_cascades as mc
    pairs = mc.eig_exact([[P, 1], [1, 0]], project=False)
    assert sum(e["algebraic_multiplicity"] for e in pairs) == 2
    rat = mc.eig_exact([[Q(1, 2), Q(1, 3)], [Q(1, 3), 0]], project=False)
    assert [e["value_qalg"].as_rational() for e in rat] == [Q(-1, 6), Q(2, 3)]
    assert all(e["denominator_scale"] == 6 for e in rat)
    assert "denominator_scale" not in mc.eig_exact([[1, 0], [0, 2]])[0]


def test_char_poly_and_eigvals_exact_reach_a_rational_matrix() -> None:
    """The peer fix that unblocks operator_norm: through rc465 a single Q(1, 2)
    entry fell to a FLOAT Faddeev-LeVerrier and eigvals_exact then RAISED at
    to_q — under a docstring promising Q entries."""
    from srmech.cascade import matrix_cascades as mc
    from srmech.math import laplacian as la
    assert mc.char_poly([[Q(1, 2), 0], [0, 1]]) == [1, Q(-3, 2), Q(1, 2)]
    ivs = mc.eigvals_exact([[Q(1, 2), 0], [0, 1]], return_intervals=True, bits=8)
    assert all(isinstance(lo, Q) and isinstance(hi, Q) for lo, hi in ivs)
    assert ivs[0][0] <= Q(1, 2) <= ivs[0][1] and ivs[1][0] <= 1 <= ivs[1][1]
    assert list(la.jacobi_eigvals([[Q(1, 2), 0], [0, 1]], exact=True)) == [0.5, 1.0]
    # the integer path is byte-identical to before
    assert mc.char_poly([[P, 0], [0, 1]]) == [1, -(P + 1), P]


def test_ground_state_flux_response_reduces_an_exact_flux_mod_1() -> None:
    """The exact half turn Q(2**53+1, 2) and Q(1, 2) are the same phase; through
    rc465 the first read 0.4889 (a rounded phase) and the second 0.5."""
    from srmech.math import laplacian as la
    cyc = [(0, 1), (1, 2), (2, 0)]
    a = la.ground_state_flux_response(3, cyc, fluxes=[Q(P, 2)])[0]
    b = la.ground_state_flux_response(3, cyc, fluxes=[Q(1, 2)])[0]
    assert (a - b if a >= b else b - a) < 1e-12, (a, b)
    # the integer witnesses are ONE flux point (periodicity), all the zero-flux ground state
    v = la.ground_state_flux_response(3, cyc, fluxes=[P, F, G, 0])
    assert all((x if x >= 0 else -x) < 1e-12 for x in v), list(v)
    # a scalar Q flux is a SCALAR (through rc465 it iterated as its (num, den) pair)
    assert isinstance(la.ground_state_flux_response(3, cyc, fluxes=Q(3, 2)), float)


def test_hypercomplex_couple_exact_route_lives_on_the_q61_grid() -> None:
    from srmech.cascade import hypercomplex_couple, cd_couple_working, cd_uncouple_working
    out = hypercomplex_couple([P, 0, 0])
    assert all(isinstance(v, Q) and (2 ** 61) % v.denominator == 0 for v in out)
    # the pass-throughs inherit the carrier
    assert all(isinstance(v, Q) for v in cd_couple_working([P, 0, 0]))
    assert all(isinstance(v, Q) for v in cd_uncouple_working(cd_couple_working([1, 2, 3])))
    # a non-dyadic rational is QUANTISED to the grid, as declared — not refused
    q = hypercomplex_couple([Q(1, 3), 0, 0], theta=0.0)[1]
    d = q - Q(1, 3)
    d = d if d >= 0 else -d
    assert d <= Q(1, 2 ** 61)


# ── F2: one float anywhere → the float route, byte-for-byte ──────────────────
def test_one_float_component_elects_the_float_route() -> None:
    from srmech.math import hdc, laplacian as la
    from srmech.cascade import hypercomplex_couple, as_oct8, correlation_product
    from srmech.cascade.coupled import multiplex_streams
    from srmech.signal_processing.closed_form_ops import farrow, iir
    from srmech.physics.qm.relativistic import four_momentum_squared
    assert hdc.loop_conj([1.0] + [0] * 7) == [1.0, -0.0, -0.0, -0.0, -0.0, -0.0, -0.0, -0.0]
    assert isinstance(hdc.loop_left_op([1.0] + [0] * 7), Mat)
    assert isinstance(hdc.loop_bind([P] + [0] * 7, [1.0] + [0] * 7)[0], float)
    assert isinstance(hypercomplex_couple([1.0, 2, 3])[0], float)
    assert as_oct8([1.0, 2, 3, 4]) == [1.0, 2.0, 3.0, 4.0, 0.0, 0.0, 0.0, 0.0]
    assert correlation_product([1.0, 2], 0, 1) == 2.0
    assert multiplex_streams([[1.0, 2], [3, 4]])["driver"] == [1.0, 4.0]
    assert isinstance(la.klein4_gain_laplacian(2, [(0, 1)], [P])["chi00"], Mat)
    assert farrow.op([0.0, 1.0, 2.0, 3.0], mu=0.0) == [0.0, 1.0, 2.0, 3.0]
    assert farrow.op([0, 1, 2, 3], mu=0.5)[1] == 1.25
    assert iir.op([1.0, 0.0, 0.0, 0.0], [1.0], [1.0, -0.5]) == [1.0, 0.5, 0.25, 0.125]
    assert isinstance(four_momentum_squared([1.0, 0, 0, 0]), float)


# ── F3: refusals stay carrier-independent; an exact operand never falls to float ─
def test_refusals_are_carrier_independent() -> None:
    from srmech.math import hdc, laplacian as la
    from srmech.cascade import as_quat4
    from srmech.physics.qm.quaternion import quaternion_log
    for bad in ([0] * 8, [0.0] * 8):
        with pytest.raises(ZeroDivisionError, match="loop_inv: zero vector has no inverse"):
            hdc.loop_inv(bad)
        with pytest.raises(ZeroDivisionError, match="loop_inv_hd: block 0 is the zero vector"):
            hdc.loop_inv_hd(bad)
    for bad in ([1] * 25, [1.0] * 25):
        with pytest.raises(ValueError, match="positive multiple of 8"):
            hdc.loop_conj_hd(bad)
    # (the power-of-two refusal is _as_loop's own `assert`, which `python -O`
    #  strips — a test may not pin a package contract on it; rc433 gate.)
    # an EXACT operand above CD_MAX_DIM raises — it is never rounded to float
    with pytest.raises(ValueError, match="exceeds CD_MAX_DIM"):
        hdc.loop_bind([1] * 512, [1] * 512)
    assert isinstance(hdc.loop_bind([1.0] * 512, [1.0] * 512)[0], float)   # the float route accepts it
    # … while the single-element HD-misuse refusal keeps ONE text on either carrier
    for bad in ([1] * 512, [1.0] * 512):
        with pytest.raises(ValueError, match="wider than one octonion"):
            hdc.loop_conj(bad)
    for bad in ([1, 0, 0, 0, 0, 0, 0, 5], [1.0, 0, 0, 0, 0, 0, 0, 5]):
        with pytest.raises(ValueError, match="e4..e7 must be zero"):
            as_quat4(bad)
    for bad in ([1, 0], [1.0, 0]):
        with pytest.raises(ValueError, match="must be a 4-vector"):
            quaternion_log(bad)
    # the laplacian builders refuse a float by NAME under exact=True …
    with pytest.raises(TypeError, match="EXACT weights"):
        la.klein4_gain_laplacian(2, [(0, 1)], [1.0], exact=True)
    with pytest.raises(TypeError, match="EXACT masses"):
        la.mass_normalized_laplacian(2, [(0, 1)], [1], masses=[1.0, 1.0], exact=True)
    with pytest.raises(TypeError, match="EXACT gains"):
        la.quaternion_laplacian(2, [(0, 1)], [1], gains=[[1.0, 0, 0, 0]], exact=True)
    with pytest.raises(ValueError, match="UNIT gains"):
        la.quaternion_laplacian(2, [(0, 1)], [1], gains=[[1, 1, 0, 0]], exact=True)
    # … and magnetic_laplacian names the carrier a non-Gaussian phase needs
    with pytest.raises(ValueError, match="Qalg carrier over Phi_3"):
        la.magnetic_laplacian(2, [(0, 1)], [1], q=Q(1, 3), exact=True)


def test_g2_three_form_is_not_cd_three_form() -> None:
    """The exact route is ⟨x, Im(y·z)⟩; cd_three_form is ⟨x, y·z⟩ INCLUDING the
    real slot. They coincide only on Im 𝕆 — substituting one for the other
    would change the shipped function under a carrier fix."""
    from srmech.math import hdc
    from srmech.cascade import cd_three_form
    assert hdc.g2_three_form(_e(0), _e(1), _e(1)) == 0
    assert cd_three_form(_e(0), _e(1), _e(1)) == Q(-1)
    assert hdc.g2_three_form(_e(1), _e(2), _e(3)) == cd_three_form(_e(1), _e(2), _e(3))


def test_the_dft_wrappers_elect_the_float_carrier_at_their_own_entry() -> None:
    """quaternion_dft / octonion_dft are float-declared transforms with a
    C-mirrored op order; they make the float request EXPLICITLY at entry so a
    fixed coercion step cannot turn their accumulator into Q-of-float."""
    from srmech.cascade import quaternion_dft, octonion_dft
    out = quaternion_dft([[P, 0, 0, 0], [1, 2, 3, 4]])
    assert all(isinstance(c, float) for row in out for c in row)
    out = octonion_dft([[P, 0, 0, 0]])
    assert all(isinstance(c, float) for row in out for c in row)


# ── the REGISTRY says both carriers ──────────────────────────────────────────
_RETURNS = {
    "srmech.math.hdc.loop_conj": "list[float] | list[Q]",
    "srmech.math.hdc.loop_bind": "list[float] | list[Q]",
    "srmech.math.hdc.loop_inv": "list[float] | list[Q]",
    "srmech.math.hdc.loop_left_op": "Mat | QMat",
    "srmech.math.hdc.loop_right_op": "Mat | QMat",
    "srmech.math.hdc.loop_associator": "list[float] | list[Q]",
    "srmech.math.hdc.cross7": "list[float] | list[Q]",
    "srmech.math.hdc.g2_three_form": "float | Q",
    "srmech.math.hdc.loop_conj_hd": "list[float] | list[Q]",
    "srmech.math.hdc.loop_inv_hd": "list[float] | list[Q]",
    "srmech.math.hdc.loop_bind_hd": "list[float] | list[Q]",
    "srmech.math.hdc.loop_unbind_hd": "list[float] | list[Q]",
    "srmech.math.hdc.loop_runbind_hd": "list[float] | list[Q]",
    # rc468 (`#T1188`): the exact routes gained an ALGEBRAIC third carrier —
    # the twiddle of a turn that is not a quarter turn is not rational, so a
    # return naming only float and Q was true of two of three live carriers.
    "srmech.cascade.hypercomplex_couple": "list[float] | list[Q] | list[Qalg]",
    "srmech.cascade.cd_couple_working": "list[float] | list[Q]",
    "srmech.cascade.cd_uncouple_working": "list[float] | list[Q]",
    "srmech.cascade.cdr_couple_working": "list[float] | list[Q]",
    "srmech.cascade.cdr_uncouple_working": "list[float] | list[Q]",
    "srmech.cascade.as_oct8": "list[float] | list[Q]",
    "srmech.cascade.as_quat4": "list[float] | list[Q]",
    "srmech.cascade.qdft_summand": "list[float] | list[Q] | list[Qalg]",
    "srmech.cascade.odft_summand": "list[float] | list[Q] | list[Qalg]",
    "srmech.cascade.correlation_product": "float | Q",
    "srmech.cascade.compensated_sum": "float | Q",
    "srmech.math.laplacian.normalized_laplacian": "Mat | list",
    "srmech.math.laplacian.mass_normalized_laplacian": "Mat | list",
    # rc467 (`#T1188`): the ONLY one of the five exact= builders whose
    # exact leaf is Qi and not Q, so it no longer hides in the shared
    # `Mat | list` its four siblings legitimately share.
    "srmech.math.laplacian.magnetic_laplacian": "Mat | list[list[Qi]]",
    "srmech.math.laplacian.quaternion_laplacian": "Mat | list",
    "srmech.math.laplacian.klein4_gain_laplacian": "dict[str, Mat] | dict[str, list]",
    "srmech.math.laplacian.elementwise_multiply_complex": "Mat | Vec | list[Qi] | list[list[Qi]]",
    "srmech.physics.qm.relativistic.four_momentum_squared": "float | Q",
    "srmech.physics.qm.pseudo_hermitian.inner_product_eta": "complex | Qi",
    "srmech.physics.qm.single_particle.density_matrix": "Mat | QMat | list[list[Qi]]",
    "srmech.physics.qm.bell.operator_norm": "float | Q",
    "srmech.physics.qm.quaternion.quaternion_log": "list[float] | list[Q]",
    # rc468 (`#T1188`): both twiddles grew the exact= cyclotomic rung.
    "srmech.physics.qm.quaternion.quaternion_twiddle":
        "list[float] | list[Q] | list[Qalg]",
    "srmech.physics.qm.octonion.octonion_twiddle":
        "list[float] | list[Q] | list[Qalg]",
}


@pytest.mark.parametrize("name,want", sorted(_RETURNS.items()))
def test_the_declared_return_names_both_carriers(name, want) -> None:
    """A caller must be able to read which carrier comes back BEFORE calling. A
    return type naming only ONE of two live carriers is FALSE — a rung below R1."""
    from srmech.introspect.tool_schema import get_tool_schema
    entry = get_tool_schema().lookup(name)
    assert entry is not None, name
    assert entry.returns.type == want, (
        f"{name} declares {entry.returns.type!r}, live carriers are {want!r}")


_KEYWORD_BUILDERS = (
    "srmech.math.laplacian.normalized_laplacian",
    "srmech.math.laplacian.mass_normalized_laplacian",
    "srmech.math.laplacian.magnetic_laplacian",
    "srmech.math.laplacian.quaternion_laplacian",
    "srmech.math.laplacian.klein4_gain_laplacian",
    # rc468 (`#T1188`): the two DFT twiddles. Their exact rung is not a graph
    # builder's — it is a whole different NUMBER FIELD — but the registry
    # obligation is identical: a caller must be able to read which carrier the
    # keyword elects before calling.
    "srmech.physics.qm.quaternion.quaternion_twiddle",
    "srmech.physics.qm.octonion.octonion_twiddle",
)


@pytest.mark.parametrize("name", _KEYWORD_BUILDERS)
def test_every_keyword_builder_declares_exact_in_the_registry(name) -> None:
    """F1's registry half: the ``exact=`` keyword each builder grew is declared,
    typed ``bool``, and its description names the carrier it returns."""
    from srmech.introspect.tool_schema import get_tool_schema
    entry = get_tool_schema().lookup(name)
    ps = {p.name: p for p in entry.parameters}
    assert "exact" in ps and ps["exact"].type == "bool", name
    assert "Q" in (ps["exact"].summary or ""), name


def test_the_couple_turn_selector_declares_its_carrier_too() -> None:
    """rc468 (`#T1188`) — the sibling of the gate above for the ONE exactness
    selector in the tree that is not spelled ``exact``.

    ``hypercomplex_couple(turn=(k, n))`` elects the exact cyclotomic route
    exactly as ``exact=True`` does on the twiddles, but under a different
    name, so no roster in this file or in rc444's census watches it. A
    selector that changes the returned carrier and is invisible to every
    carrier gate is the shape rc463 named; this is its one-line answer."""
    from srmech.introspect.tool_schema import get_tool_schema
    entry = get_tool_schema().lookup("srmech.cascade.hypercomplex_couple")
    ps = {p.name: p for p in entry.parameters}
    assert "turn" in ps, "hypercomplex_couple lost its exact rational-turn selector"
    assert "EXACT" in (ps["turn"].summary or ""), ps["turn"].summary


# -- rc467 (`#T1188`): the POPULATION gate that replaced an instance list -----
#
# rc466 shipped `_KEYWORD_BUILDERS` - five NAMED ops - as the registry half of
# the exact-carrier drain. An instance list can only fail on the instances
# somebody thought to write down, and the five it named were the five that were
# already fine. Asked of the whole REGISTRY instead, the same question found
# five more, and four of them were worse than the one the dossier had named:
#
#   hermitian_eigendecompose::H   RAISED its own exactness refusal (wire-dead)
#   dense_solve::A                returned Q(1, 2**53)  - direct: Q(1, 2**53+1)
#   schur_complement::L           returned Q(2**53 - 1) - direct: Q(2**53)
#   dirichlet_to_neumann::L       returned Q(2**53 - 1) - direct: Q(2**53)
#   triality_companions::g_v      returned Q(9007199254740999, 8) - direct: an
#                                 INTEGER, 1125899906842625
#
# A raise is a defect the caller can see. Those four are SILENT WRONG ANSWERS
# WEARING THE EXACT CARRIER: the wire rounded the operand to float64, the op
# then computed exactly on the rounded number, and the caller got back a `Q` -
# the carrier whose whole meaning is "this is exact" - holding a value that is
# not the answer to the question asked.
#
# The gate below asks the population question, so a NEW `exact=`-bearing op
# that declares a rounding operand is red on the day it lands.


def _exact_leaves(o):
    """Every scalar leaf of a coerced operand, containers unwrapped."""
    if hasattr(o, "tolist"):
        o = o.tolist()
    if isinstance(o, (list, tuple)):
        for x in o:
            yield from _exact_leaves(x)
    else:
        yield o


def _carries(o, target: int) -> bool:
    """True iff ``target`` survived coercion somewhere in ``o``, EXACTLY."""
    # srmech's OWN exact carrier, never stdlib `fractions` -- that module is a
    # BANNED_ENGINE at STRICT ZERO across package, tests AND tools.
    from srmech.math.q import to_q
    for v in _exact_leaves(o):
        try:
            if to_q(v) == Q(target):
                return True
        except (TypeError, ValueError, ZeroDivisionError):
            r = getattr(v, "as_rational", None)
            if r is not None and r() == Q(target):
                return True
    return False


def test_no_exact_bearing_op_declares_an_operand_that_rounds_over_the_wire() -> None:
    """rc467 (`#T1188`) - the POPULATION gate. STRICT ZERO.

    For every registry entry carrying an ``exact`` parameter, every array-shaped
    operand it declares must carry ``2**53 + 1`` through ``coerce_param``
    INTACT. A bare ``Mat`` does not - it is float64 - so the wire hands the
    exact route a rounded operand and the route answers exactly, about the
    wrong matrix.

    This asks about OPERAND SURVIVAL, not return exactness. An op may
    legitimately return a float (that is what a DECLARED demotion is); none may
    legitimately be handed a number its caller did not send."""
    from srmech.introspect.tool_schema import get_tool_schema
    from srmech.mcp._coercion import coerce_param, has_coercer

    target = 2 ** 53 + 1
    witnesses = ([[target, 0], [0, 1]], [target, 1])
    population = [e for e in get_tool_schema().tools
                  if any(p.name == "exact" for p in e.parameters)]
    # The instrument can return otherwise: the population is non-empty, and it
    # is strictly bigger than the five-name list rc466 shipped.
    assert len(population) > len(_KEYWORD_BUILDERS), len(population)

    rounding = []
    for entry in population:
        for prm in entry.parameters:
            if prm.name == "exact" or not has_coercer(prm.type):
                continue
            for w in witnesses:
                try:
                    got = coerce_param(w, prm.type)
                except Exception:
                    continue          # this operand does not take this shape
                if not _carries(got, target):
                    rounding.append("%s::%s (%s)" % (entry.name, prm.name, prm.type))
                break

    assert rounding == [], (
        "these exact=-bearing ops declare an operand that ROUNDS over the "
        "wire, so exact=True computes on a number the caller did not send: "
        + "; ".join(sorted(rounding)))


def test_the_widened_operands_cross_the_wire_and_agree_with_the_direct_call() -> None:
    """rc467 (`#T1188`) - the EXECUTED half. Each widened operand is not merely
    DECLARED wider: it round-trips over the wire and AGREES with the direct
    call. Every wire value asserted below was wrong before this rc."""
    from srmech.mcp import invoke_tool
    from srmech.math import laplacian as _L
    from srmech.physics.qm import triality as _T

    # (a) the four eigen-family routes that RAISED their own exactness refusal
    vals = invoke_tool("srmech.math.laplacian.jacobi_eigvals",
                       {"matrix": [[P, 0], [0, 1]], "exact": True})
    assert [v.as_rational() for v in vals] == [Q(1), Q(P)], vals
    lam, _V = invoke_tool("srmech.math.laplacian.symmetric_eigendecompose",
                          {"L": [[P, 0], [0, 1]], "exact": True})
    assert lam[1].as_rational() == Q(P), lam
    fied = invoke_tool("srmech.math.laplacian.fiedler_vector",
                       {"matrix": [[P, 0], [0, 1]], "exact": True})
    assert all(type(x).__name__ == "Qalg" for x in fied), fied
    grp = invoke_tool("srmech.math.laplacian.three_fold_eigvec_groups",
                      {"L": [[P, 0], [0, 1]], "exact": True})
    assert set(grp) == {"low", "mid", "high"}, sorted(grp)

    # (b) the four that answered exactly, about the WRONG matrix
    Lm = [[P, -1], [-1, 1]]
    assert (invoke_tool("srmech.math.laplacian.schur_complement",
                        {"L": Lm, "boundary_idx": [0], "exact": True})
            == _L.schur_complement(Lm, [0], exact=True))
    assert (invoke_tool("srmech.math.laplacian.dirichlet_to_neumann",
                        {"L": Lm, "boundary_idx": [0], "exact": True})
            == _L.dirichlet_to_neumann(Lm, [0], exact=True))
    assert (invoke_tool("srmech.math.laplacian.dense_solve",
                        {"A": [[P, 0], [0, 1]], "B": [1, 1], "exact": True})
            == _L.dense_solve([[P, 0], [0, 1]], [1, 1], exact=True))
    g8 = [[P if i == j == 0 else (1 if i == j else 0) for j in range(8)]
          for i in range(8)]
    assert (invoke_tool("srmech.physics.qm.triality.triality_companions",
                        {"g_v": g8, "exact": True})[0][0][0]
            == _T.triality_companions(g8, exact=True)[0][0][0] == Q(2 ** 50 + 1))


def test_the_exact_jacobi_route_no_longer_lifts_to_float() -> None:
    """rc467 (`#T1188`) - the SEVENTH residual. jacobi_eigvals(exact=True) ended
    in a terminal float lift that destroyed the exactness the keyword exists to
    supply, while its sibling fiedler_vector had returned list[Qalg] since
    rc466. An op whose sibling ships the exact return is not float by nature,
    so it was FIXED, not declared."""
    from srmech.math.laplacian import jacobi_eigvals, fiedler_vector

    vals = jacobi_eigvals([[P, 0], [0, 1]], exact=True)
    assert [type(v).__name__ for v in vals] == ["Qalg", "Qalg"], vals
    assert vals[1].as_rational() == Q(P), vals[1]      # was 9007199254740992.0

    # an IRRATIONAL spectrum comes back as the algebraic number, not a float:
    # x^3 - 10x^2 + 28x - 22 is irreducible over Q (the docstring's own witness).
    irr = jacobi_eigvals([[2, 1, 1], [1, 3, 1], [1, 1, 5]], exact=True)
    assert all(v.as_rational() is None for v in irr), irr
    assert {v.m for v in irr} == {(-22, 28, -10, 1)}, [v.m for v in irr]

    # the sibling agrees on carrier, which is the argument that decided it
    sib = fiedler_vector([[P, 0], [0, 1]], exact=True)
    assert type(sib[0]).__name__ == type(irr[0]).__name__ == "Qalg"

    # and the DEFAULT float route is untouched
    assert type(jacobi_eigvals([[2.0, 1.0], [1.0, 2.0]])).__name__ == "Vec"


def test_compensated_sum_honours_the_declaration_it_already_shipped() -> None:
    """rc467 (`#T1188`) - the op declared three exact rungs and delivered one.

    The SHIPPED parameter sentence - compiled into
    ``c/src/srmech_tool_registry.c`` and served over MCP since rc466 - reads
    *"the LEAVES select the carrier: integers / Q / [num, den] pairs take the
    EXACT-Q rung, one float anywhere the float64 one"*. Measured before this
    rc, two of those three rungs were false:

      compensated_sum([2**53+1, 1, -2**53])  ->  1.0        (answer: 2)
      compensated_sum([[1, 3], [1, 3]])      ->  TypeError

    The ``s = 0.0`` seed pulled every integer operand onto the float path, so
    an all-exact operand was summed in float64 and silently lost the bit. Only
    the ``Q`` rung worked, and only by accident, through ``Q.__radd__``. The
    op was FIXED rather than the sentence corrected: the exact rung it already
    promised is ten lines, and the shipped ``returns`` sentence ("an exact Q
    for exact values, the compensation term is then identically zero") already
    described the behaviour that was missing."""
    from srmech.cascade.composites import compensated_sum

    # (a) the int rung - the silent wrong answer
    got = compensated_sum([P, 1, -(2 ** 53)])
    assert got == Q(2), got
    assert isinstance(got, Q), type(got).__name__

    # (b) the [num, den] rung - the TypeError
    assert compensated_sum([[1, 3], [1, 3], [1, 3]]) == Q(1)

    # (c) the Q rung, which already worked
    assert compensated_sum([Q(1, 3)] * 3) == Q(1)

    # (d) the compensation term IS identically zero on the exact rung, which
    #     is what the shipped `returns` sentence claims. If it were not, the
    #     sum would not be exact and (a) could not hold at 2**53.
    assert compensated_sum([Q(1, 7)] * 7) == Q(1)

    # (e) ONE float leaf anywhere keeps the byte-identical rc420 float body,
    #     so the autocorrelation chain's pinned float-op order does not move
    assert compensated_sum([1e10, 1.0, -1e10, 2.0]) == 3.0
    assert isinstance(compensated_sum([1, 2, 0.5]), float)
    # NOTE the value, and how it was found. The curated worked example
    # shipped `compensated_sum([0.1] * 10)  # -> 1.0000000000000002` -
    # compiled into srmech_tool_registry.c and served over MCP - and the op
    # returns 1.0, which is the CORRECT Neumaier answer (math.fsum agrees; a
    # naive += gives 0.9999999999999999). Measured identical on both sides of
    # this rc, so the example was wrong when it was written, not broken here.
    # The worked-example ledger does not catch this class: it EXECUTES each
    # snippet and records what it prints, and never compares that against the
    # `# ->` comment the snippet states. Named in the rc467 CHANGELOG.
    assert compensated_sum([0.1] * 10) == 1.0

    # (f) an EMPTY operand has no leaves, so nothing selects a carrier: it
    #     keeps the float 0.0 it has always returned (the curated worked
    #     example asserts exactly this) rather than acquiring a Q silently
    assert compensated_sum([]) == 0.0
    assert isinstance(compensated_sum([]), float)


def test_every_widened_param_type_has_a_coercer_and_a_lexicon_row() -> None:
    from srmech.mcp._coercion import has_coercer
    from srmech.mcp._tools import _TYPE_LEXICON, _ENCODING_HINT
    for ty in ("list[float] | list[Q]", "Optional[list[int | Q | float]]",
               "list[list[float]] | list[list[Q]]",
               "Optional[list[list[float]] | list[list[Q]]]",
               "Mat | Vec | Sequence[int | Q]", "float | Q | Sequence[int | Q | float]",
               "Vec | Sequence[int | Q]", "HV | Sequence[int | Q]", "float | Q",
               "Mat | QMat | Sequence[Sequence[int | Q]]"):
        assert has_coercer(ty), ty
        assert _TYPE_LEXICON.get(ty) in ("array", "number"), ty
        if ty != "float | Q":            # rc363: deliberately hint-free (a number)
            assert ty in _ENCODING_HINT, ty


def test_an_exact_operand_crosses_the_wire_exact() -> None:
    from srmech.mcp import invoke_tool
    assert invoke_tool("srmech.math.hdc.loop_conj", {"x": _o(P)})[0] == Q(P)
    assert isinstance(invoke_tool("srmech.math.hdc.loop_left_op", {"a": _o(P)}), QMat)
    assert invoke_tool("srmech.cascade.hypercomplex_couple",
                       {"streams": [P, 0, 0], "theta": 0.0})[1] == P
    assert invoke_tool("srmech.cascade.correlation_product", {"x": [P, 1], "i": 0, "j": 1}) == P
    assert invoke_tool("srmech.math.laplacian.klein4_gain_laplacian",
                       {"n": 2, "edges": [[0, 1]], "weights": [P], "exact": True})["chi00"][0][0] == P
    assert invoke_tool("srmech.physics.qm.relativistic.four_momentum_squared",
                       {"k": [P, 0, 0, 0]}) == P * P
    assert isinstance(invoke_tool("srmech.physics.qm.single_particle.density_matrix",
                                  {"psi": [P, 1]}), QMat)
    # a [num, den] leaf rides as the exact rational it names
    assert invoke_tool("srmech.signal_processing.farrow",
                       {"signal": [0, P, 1, 2, 0, 0], "mu": [1, 2]})[1] == 7318349394477057
    # and the float route still crosses as floats
    assert isinstance(invoke_tool("srmech.math.hdc.loop_conj",
                                  {"x": [1.0, 0, 0, 0, 0, 0, 0, 0]})[0], float)


# ── THE NAMED FINDING: the C compose host is double-only on five chain steps ──
#: Chain steps whose Python op now carries an exact operand exactly while the C
#: compose host's twin (``c/src/srmech_compose_run.c``) coerces to doubles: a
#: declared chain over an EXACT input is exact in the Python runner and rounded
#: in the C host. Pinned BY NAME so a new member is red and a drained one has to
#: be recorded. ``hypercomplex_couple`` and its pass-throughs are NOT here: their
#: C twin ``srmech_hypercomplex_couple_q61`` IS the exact route.
_COMPOSE_HOST_FLOAT_ONLY = frozenset({
    "srmech.cascade.as_quat4",
    "srmech.cascade.as_oct8",
    "srmech.cascade.qdft_summand",
    "srmech.cascade.odft_summand",
    "srmech.cascade.correlation_product",
    # rc466 review fix: the op forms an exact phase DIFFERENCE for exact phases
    # and rounds it once; cr_op_kur_sin_term reads each phase as a double.
    "srmech.cascade.kuramoto_sin_term",
})


def test_the_compose_host_divergence_is_a_named_finding() -> None:
    """Runs ONE exact proof case (the autocorrelation chain over ``[2**53+1, 1]``)
    through BOTH executors and asserts the disagreement EXISTS: the Python runner
    returns the exact ``Q`` energy ``(2**53+1)**2 + 1`` and the C host a double
    that cannot hold it. An instrument that cannot return otherwise is not a
    measurement — so the Python side is asserted exact and the C side asserted
    unequal, not merely "different"."""
    from _native_gate import require_native
    require_native("the C compose host")
    import test_c_cascade_value_parity_rc450 as harness
    from srmech.cascade import compose as _compose
    from srmech.dsl._cascade_chain import cascade_chain_specs
    variant, spec, entry = cascade_chain_specs("autocorrelation")[0]
    inputs = dict(harness._case_defaults(entry))
    inputs.update({"x": [P, 1]})
    py = harness._py_run(spec, inputs)
    exact_energy = P * P + 1
    assert isinstance(py[0], Q) and py[0] == exact_energy, py
    rc, wire, ok = harness._c_run(harness._chain_only(entry), inputs)
    assert ok and rc == 0, (rc, wire[:80])
    c_val = _compose._reconstruct_value(_compose._srmech_json.loads(wire.decode("utf-8")))
    assert c_val[0] != exact_energy, (
        "the C compose host now carries the exact energy — GOOD NEWS, ACTION "
        "REQUIRED: remove correlation_product from _COMPOSE_HOST_FLOAT_ONLY and "
        "record the drain")
    assert isinstance(c_val[0], float)


def test_compose_host_float_only_members_are_real_chain_steps() -> None:
    """The pinned set names registered ops whose C twin exists — a name that is
    not a chain step would make the pin decorative."""
    from srmech.introspect.tool_schema import get_tool_schema
    schema = get_tool_schema()
    for name in sorted(_COMPOSE_HOST_FLOAT_ONLY):
        assert schema.lookup(name) is not None, name
    csrc = (Path(__file__).resolve().parents[2] / "c" / "src" / "srmech_compose_run.c").read_text(encoding="utf-8")
    for token in ("cr_op_as_quat4", "cr_op_as_oct8", "cr_op_qdft_summand",
                  "cr_op_odft_summand", "cr_a_corr_product", "cr_op_kur_sin_term"):
        assert token in csrc, token
    # the sixth member's divergence, stated in the C twin's own arithmetic:
    # cr_op_kur_sin_term does `s = xj - xi` on doubles (cr_list_at_dbl), and
    # the op now forms the exact difference first. On [2**53+1, 2**53+3] the
    # difference is 2; the doubles are 2**53 and 2**53+4, whose difference is 4.
    from srmech.cascade.composites import kuramoto_sin_term
    from srmech.math import rational
    assert "cr_list_at_dbl(th, i, &xi)" in csrc and "s = xj - xi;" in csrc
    assert kuramoto_sin_term([P, P + 2], 0, 1) == rational.sin(2.0)
    assert rational.sin(float(P + 2) - float(P)) == rational.sin(4.0) != rational.sin(2.0)


# ── the declared DFT chains in the PYTHON runner over an exact sample list ───
def test_the_declared_qdft_chain_in_the_python_runner_over_an_exact_sample() -> None:
    """The chain steps carry an exact sample exactly, so the declared
    ``quaternion_dft`` chain run by the PYTHON runner over an exact sample list
    is exact on the DC bin (its twiddle is the unit on the nose) and STAYS
    exact through ``vec_scale`` whenever ``dft_scale``'s float ``1/n`` is a
    dyadic — ``Q`` absorbs ``1.0`` and ``2**-k`` exactly. ``dft_scale`` has NO
    operand whose leaves could elect a carrier (a bool and an int), so an
    inverse over a non-dyadic ``n`` multiplies the exact accumulator by the
    float64-rounded ``1/n``: a ``Q`` of a rounded scale, the one mixed-carrier
    residue of this drain, DECLARED on ``dft_scale`` and pinned here so that a
    chain-level exact scale is GOOD NEWS the gate reports, never absorbed."""
    import test_c_cascade_value_parity_rc450 as harness
    from srmech.dsl._cascade_chain import cascade_chain_specs
    _variant, spec, entry = cascade_chain_specs("quaternion_dft")[0]
    fwd = dict(harness._case_defaults(entry))
    fwd.update({"x": [[P, 0, 0, 0], [1, 0, 0, 0]], "mu_axis": "i",
                "inverse": False, "left": True})
    out = harness._py_run(spec, fwd)
    assert isinstance(out[0][0], Q) and out[0][0] == P + 1, out[0]   # Σ x[m], exact
    inv2 = dict(fwd)
    inv2["inverse"] = True                                            # n = 2: 1/2 is dyadic
    out = harness._py_run(spec, inv2)
    assert isinstance(out[0][0], Q) and out[0][0] == Q(P + 1, 2), out[0]
    inv3 = dict(fwd)
    inv3.update({"x": [[P, 0, 0, 0], [1, 0, 0, 0], [2, 0, 0, 0]], "inverse": True})
    out = harness._py_run(spec, inv3)                                 # n = 3: 1/3 is not
    assert isinstance(out[0][0], Q), out[0]
    assert out[0][0] != Q(P + 3, 3), (
        "the declared chain now carries an exact 1/3 through dft_scale — GOOD "
        "NEWS, ACTION REQUIRED: retire the mixed-carrier declaration on "
        "dft_scale and turn this assertion into the exact equality")
    # the ONLY difference is the scale: the float 1/3, read exactly, recovers the sum
    assert out[0][0] == Q(P + 3) * Q(*(1.0 / 3.0).as_integer_ratio())
