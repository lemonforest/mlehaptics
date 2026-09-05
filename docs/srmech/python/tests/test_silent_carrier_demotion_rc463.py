"""rc463 (`#T1188`) — the SILENT-CARRIER-DEMOTION ratchet.

THE CLASS PREDICATE, stated once, here, as the gate's own definition:

    An op is a **silent carrier demotion** when it accepts an exact operand
    through its own declared entry, routes it through a float carrier so a
    derived quantity's significand is truncated to 53 bits, returns the rounded
    value with no exception/warning/status, publishes **no accuracy declaration
    a caller could read before calling**, and a carrier that would have computed
    the same quantity exactly already ships.

Five conjuncts: ADMISSION ∘ DEMOTION ∘ SILENCE ∘ NO-R3-DECLARATION ∘
EXACT-PEER-SHIPS.

⚠️ **ADMISSION used to read "decided by the SIGNATURE, not by what Python
happens to accept", and that clause was the defect** (rc465, `#T1188`). A
signature is a DECLARATION; deciding membership by it means an op that declares
``Sequence[float]`` is outside the class however exact the operand it is
actually handed — which is precisely rung **R2** of the honesty ladder below,
the rung this file rates "WEAK … nothing enforces it". Nine ops across
``qm.octonion`` / ``qm.quaternion`` / ``qm.triality`` rounded an exact ℚ operand
for 340-odd releases behind that one annotation. ADMISSION is now decided by
MEASUREMENT: the operand is handed over and the answer is compared.

⚠️ **WHY THIS SHIPPED FOR 118 RELEASES.** rc344 ran a sibling audit on the SAME
family and cleared ``einsum`` in as many words: *"it returns a ``Mat``, so it
never claimed byte-identity."* Every clause of that sentence is true. The
PREDICATE was wrong. rc344 tested

    P_claim: does the op CLAIM exactness while riding float?

and the class above tests

    P_value: does the op ROUND an exact operand without saying so?

``P_claim`` is a strict SUBSET of ``P_value``. ``kron`` failed both and was
fixed; ``einsum`` passes ``P_claim`` and fails ``P_value``, and so rode 118
further releases returning well-formed, plausible, wrong numbers. Layer 3 below
is the clause rc344 did not have, and it asks the complementary question: not
*"does it claim exactness"* but *"does it declare INEXACTNESS"*.

THE HONESTY LADDER (Layer 3's decision procedure). Given ONLY the signature and
the docstring, and no knowledge of the implementation, can the caller predict
that the returned value is not the exact one?

    R1  return-TYPE declaration — "returns a ``Mat``", "-> float".
        **NOT SUFFICIENT.** It names the CONTAINER, not the value. This is
        exactly the rc344 reasoning above.
    R2  parameter ANNOTATION naming float — ``weights: Iterable[float]``.
        WEAK. Decidable pre-call and it does narrow the declared domain, but
        nothing enforces it and the module's own exact route may demand the
        very matrix such a builder cannot produce (measured through rc462:
        ``jacobi_eigvals(dense_laplacian(...), exact=True)`` RAISED).
    R3  an explicit ACCURACY statement ("to round-off (~1 ULP)", "accurate to
        ~1e-9", "terminal float lift") **or** an ``exact=`` opt-in in the
        signature. **SUFFICIENT.**

⚠️ **WHAT THIS GATE CANNOT SEE — required disclosure.** Four gates in this tree
have shipped blind to their own subject (`#T1136`, `#T1138`, `#T1182`, and the
``srmech_svd_f64`` claim gap this rc closes). This one states its blind spots:

 1. ~~**A missing MANIFEST row is invisible.**~~ **CLOSED at rc465 (`#T1188`),
    and closing it is how the size of the hole became known.** The manifest is
    now MEASURED by ``tools/demotion_probe.py`` over every sequence-shaped
    REGISTRY parameter — 703 rows, 427 ops — instead of enumerated by hand. On
    the rc464 surface it found **127 demoting rows over 101 ops, 77 of them
    UNDECLARED over 64 ops**, against the six rows this file carried. Six was
    not a residual, it was a sample, and this bullet is what said so first.
    What remains open is COVERAGE, which the probe states as data rather than
    silence: 305 ``RAISED`` / 52 ``NO_SHAPE`` rows are bindings it could not
    build, each emitted with its reason. rc465-fix (`#T1188`) puts a ratchet
    under the second of those two numbers —
    :data:`CEIL_DEMOTION_UNREACHED` —
    because ``tools/demotion_probe.py``'s own disclosure named that constant as
    the thing bounding its reach and **the constant did not exist anywhere in
    the repo**: a named ratchet with no definition and no assertion, which is
    the "gate that cannot fail" shape this file exists to remove. The LARGER
    unreached class is ``RAISED`` (305 of 703, 43%), and it is deliberately NOT
    ratcheted: a ``RAISED`` row is a real refusal by a real op against a
    synthesised binding, so driving that number down is a question about the
    SHAPE SYNTHESISER, not about the tree, and a down-only ceiling on it would
    ratchet the instrument rather than the library.
 2. **No branch-coverage oracle.** Layer 1 enumerates paths somebody THOUGHT
    OF. ``einsum`` needed six shapes to reach both of its branches and the
    census that found five of them missed the sixth; nothing here proves a
    seventh branch does not exist. This is why Layer 1 is enumerated per PATH
    and not per op.
 3. **It is ONE-DIRECTIONAL.** It catches "exact in, rounded out". It CANNOT
    catch the converse — an op that is exact while its contract calls itself
    approximate. ``kron``'s empty ``preserves: ()`` is exactly that shape.
 4. **It measures through PYTHON only.** A demotion in the C projection that
    the Python path does not share is invisible here.
 5. **Layer 3's vocabulary is a KEYWORD LIST.** Prose declaring inexactness in
    words outside the list reads as undeclared (a false positive — see
    ``declaration_hits``'s one-level delegation follow, which exists because
    ``matrix_cascades.svd`` is documented at its delegate); a keyword in an
    unrelated sentence reads as declared (a false negative). Do NOT "simplify"
    the delegation follow — it was added because running the gate without it
    red-flagged a correctly-documented op. rc466 (`#T1188`) MEASURED the false
    negative: ``odft_summand`` read as declared on *"not a tolerance"* — a
    negation the keyword reader cannot see (``tools/demotion_probe.py``
    disclosure 9; pinned as an instrument fact in
    ``tests/test_declared_inexactness_rc466.py``).

    ⚠️ **And through rc464 it resolved that delegate as ``getattr(_la, name)``**
    — hard-wired to ``srmech.math.laplacian``. So Layer 3 was not merely
    keyword-limited: it was structurally incapable of reading the contract of
    any op outside the one module its six hand-rows came from, which is a large
    part of why the class looked like six. rc465 resolves in ``fn.__globals__``.
 6. **Bit / byte carriers are structurally OUT OF REACH** — TRUE of the byte
    codecs, and **MEASURED FALSE of ``hdc`` at rc465**. ``bundle(vectors:
    Sequence[bytes]) -> bytes`` genuinely admits no 53-bit-significand witness,
    and ``rle`` refuses a 54-bit symbol outright. But this bullet generalised
    that to "57 ``hdc`` tools", and sixteen ``hdc`` rows take FLOAT sequences
    and round the witness: ``loop_conj``, ``loop_conj_hd``, ``loop_inv``,
    ``loop_inv_hd``, ``loop_bind``, ``loop_left_op``, ``loop_right_op``,
    ``loop_associator``, ``cross7``, ``g2_three_form``. Their absence from the
    rc463 manifest was not a domain fact; it was the same blind spot as
    bullet 1. The gate could not distinguish "no witness constructible" from
    "nobody wrote one" — and this bullet is what that inability sounded like
    when it was written down.
 7. **It cannot see the ``preserves`` field**, because that field is empty
    ``()`` on every op in this family INCLUDING exact ``kron``. A gate leaning
    on it would be vacuous.
 8. ⚠️ **THE POPULATION IS READ FROM A COMMITTED MANIFEST, AND ONLY HALF OF
    ITS STALENESS IS GUARDED.** Layers 2-3 no longer re-derive the census —
    that is a deliberate tool run now, for the reasons the Layer-2 header
    gives — so nothing re-measures the tree on its own. The guard is a hash of
    the registry's ``(op name, parameter types, return type)`` triples, which
    moves when an op is added, removed or re-signatured. **It does not move
    when an implementation changes carrier behaviour behind an unchanged
    signature**, which is precisely the class this file exists to find. The
    tree has paid for the identical blind spot once already — the worked-
    example ledger's ``--only-stale`` hashes snippet TEXT, *"and that blind
    spot is exactly how the ℚ-flip defect shipped"* — so it is written here in
    prose rather than left to be rediscovered. What still EXECUTES on every CI
    run is Layer 1: strict-zero exactness against the shipped carriers,
    enumerated per PATH.

numpy-free. No ``abs()`` — ``significand_bits`` uses a Class-K pin-slot branch.
No stdlib ``fractions``.
"""

import sys
from pathlib import Path

import pytest

# rc465 (`#T1188`): the probe is the SHARED instrument (tools/demotion_probe.py),
# imported the way tests/test_frame_scope_rc430.py imports tools/frame_probe.py —
# so this gate and the committed census cannot be separately hand-rolled.
_TOOLS = Path(__file__).resolve().parents[1] / "tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from srmech.cascade import composites as _composites
from srmech.cascade import matrix_cascades as _mc
from srmech.cascade import spectral_cascades as _sc
from srmech.introspect.tool_schema import get_tool_schema
from srmech.math import laplacian as _la
from srmech.math.q import Q
from srmech.math.qmat import QMat

# ── the shared prelude ────────────────────────────────────────────────────────
# ``_eq_exact`` is lifted VERBATIM from tests/test_residue_c_rc155.py:45 rather
# than re-invented. Its whole point is that a Python ``int`` has ``.real`` and
# ``.imag`` and they return ``int``, so nothing is coerced and no arithmetic
# happens — the comparison never passes a value through float64. A ``Q`` also
# has ``.real``/``.imag`` (returning ``Q``), so exact-ℚ results compare cleanly
# against integer oracles without a lift.
#
# ⚠️ The sharpest fact behind this whole file: ``test_residue_c_rc155.py:251``
# compares einsum with ``abs(complex(g) - complex(w)) <= 1e-9`` — living 170
# lines BELOW ``_eq_exact``, in the same file, whose docstring condemns that
# exact comparison as "the float-blind comparison this ratchet shipped with
# through rc343". ``_eq_exact`` was applied to ``kron`` and never to ``einsum``.


def _eq_exact(g, w):
    """VERBATIM from tests/test_residue_c_rc155.py:45."""
    gr = g.real if hasattr(g, "real") else g
    gi = g.imag if hasattr(g, "imag") else 0
    wr = w.real if hasattr(w, "real") else w
    wi = w.imag if hasattr(w, "imag") else 0
    return gr == wr and gi == wi


def significand_bits(n: int) -> int:
    """LIFTED to module scope from test_residue_c_rc155.py:122, where it is
    nested inside a test function and therefore unreachable by any other gate.

    Sign is a **Class-K pin-slot** branch, never an ALU ``abs()``.
    """
    if n < 0:
        n = -n
    if n == 0:
        return 0
    while n % 2 == 0:
        n //= 2
    return n.bit_length()


#: ``2**53 + 1 == 3 * 3002399751580331`` — the smallest positive integer float64
#: cannot represent. Significand 54 bits. The SAME value rc344 pinned for kron.
P = 2 ** 53 + 1
#: A 806-bit MAGNITUDE with a 6-bit significand — the negative control that
#: keeps this a measurement of significand WIDTH, not of operand SCALE.
_HUGE_TINY_SIGNIFICAND = (7 * 2 ** 400) * (9 * 2 ** 400)


def _first_leaf(x):
    """The first scalar of a nested carrier / list, without arithmetic."""
    while True:
        if hasattr(x, "to_lists"):
            x = x.to_lists()
            continue
        if hasattr(x, "tolist"):
            x = x.tolist()
            continue
        if isinstance(x, (list, tuple)):
            if not x:
                return 0
            x = x[0]
            continue
        return x


# ── LAYER 0 — the VACUITY GUARD ───────────────────────────────────────────────
def _discriminating(exact_value) -> bool:
    """True iff this witness COULD have failed. Both clauses are load-bearing."""
    return significand_bits(exact_value) > 53 and float(exact_value) != exact_value


def test_layer0_the_witness_could_have_failed() -> None:
    """An instrument that cannot return otherwise is not a measurement.

    Every row below is guarded by :func:`_discriminating` before it is asserted,
    so the gate cannot go green on a witness that no carrier could have rounded.
    """
    assert _discriminating(P), "the primary witness stopped discriminating"
    assert significand_bits(P) == 54
    assert int(float(P)) == 2 ** 53, "float64 must collapse P to 2**53"


def test_layer0_rejects_a_non_discriminating_witness() -> None:
    """The guard's own non-vacuity, in BOTH directions.

    ``3 * 3 = 9`` is representable, and the 806-bit product is representable
    too DESPITE its magnitude — a fixture chosen for size rather than
    significand width would sail through a naive gate. Both are rejected.
    """
    assert not _discriminating(9), "a representable witness must be rejected"
    assert significand_bits(_HUGE_TINY_SIGNIFICAND) == 6
    assert not _discriminating(_HUGE_TINY_SIGNIFICAND), (
        "an 806-bit MAGNITUDE with a 6-bit significand is exactly representable; "
        "a guard that accepted it would be measuring operand scale, not "
        "significand width")


# ── LAYER 1 — strict-zero exactness, enumerated per PATH ──────────────────────
# ⚠️ PER PATH, NOT PER OP. This is the lesson of the rc463 census and it is
# load-bearing: ``einsum`` demoted on TWO INDEPENDENT code paths — the rc155
# ``mat_matmul`` fast route AND the general ``_accumulate`` fallback, which
# seeded ``acc = 0j`` of its own accord. A one-row-per-op manifest would have
# covered the fast path and left ``'ii->'``, ``'ij->ji'`` and every >=3-operand
# contraction still wrong. Each row names the PATH it reaches.

def _l1_rows():
    """(label, callable, exact_oracle) — every row must be exact, strict zero."""
    return [
        # the rc344 control: this passed before rc463 and must keep passing.
        ("spectral_cascades.kron[int]",
         lambda: _sc.kron([[3]], [[3002399751580331]])[0][0], P),
        ("matrix_cascades.char_poly[int]",
         lambda: _mc.char_poly([[P, 0], [0, 0]])[1], -P),
        # the exact carrier itself.
        ("QMat.matmul", lambda: QMat.from_rows([[3]]).matmul(
            QMat.from_rows([[3002399751580331]]))[0, 0], P),
        ("QMat.trace", lambda: QMat.from_rows([[P, 0], [0, 0]]).trace(), P),
        ("QMat.kron", lambda: QMat.from_rows([[3]]).kron(
            QMat.from_rows([[3002399751580331]]))[0, 0], P),
        # ── einsum, SIX shapes across BOTH branches (rc463's fix) ────────────
        ("einsum['ij,jk->ik'] (fast path: _einsum_pair_via_matmul)",
         lambda: _mc.einsum("ij,jk->ik", [[3]], [[3002399751580331]])[0, 0], P),
        ("einsum['i,i->'] (fast path, rank-0)",
         lambda: _mc.einsum("i,i->", [3], [3002399751580331]), P),
        ("einsum['ii->'] (GENERAL path: the _accumulate fallback)",
         lambda: _mc.einsum("ii->", [[P, 0], [0, 0]]), P),
        ("einsum['ij->ji'] (GENERAL path: a TRANSPOSE, no arithmetic at all)",
         lambda: _mc.einsum("ij->ji", [[P]])[0, 0], P),
        ("einsum['i,i,i->'] (GENERAL path, 3 operands)",
         lambda: _mc.einsum("i,i,i->", [3], [3002399751580331], [1]), P),
        ("einsum['ij,k->ijk'] (rank-3 -> nested list)",
         lambda: _first_leaf(_mc.einsum("ij,k->ijk", [[3]], [3002399751580331])), P),
        ("einsum[QMat operands]",
         lambda: _mc.einsum("ij,jk->ik", QMat.from_rows([[3]]),
                            QMat.from_rows([[3002399751580331]]))[0, 0], P),
        # ── the rest of the rc463 exact rung ─────────────────────────────────
        ("separate_frame_curvature[exact]",
         lambda: _mc.separate_frame_curvature(
             [[3, 0], [0, 1]],
             [[3002399751580331, 0], [0, 1]])["fixed_frame"][0, 0], P),
        ("lstsq_exact",
         lambda: _mc.lstsq_exact([[1], [1]], [P, P])[0], P),
        ("dense_adjacency[exact]",
         lambda: _la.dense_adjacency(2, [(0, 1)], [P], exact=True)[0][1], P),
        ("dense_laplacian[exact]",
         lambda: _la.dense_laplacian(2, [(0, 1)], [P], exact=True)[0][0], P),
        ("signed_laplacian[exact]",
         lambda: _la.signed_laplacian(2, [(0, 1)], [P], exact=True)[0][0], P),
        # honest-exact ops the census confirmed and this gate now holds.
        ("signal_processing.fir[int]",
         lambda: _first_leaf(_sp_fir([3, 0], [3002399751580331])), P),
        ("signal_processing.matched_filter[int]",
         lambda: _first_leaf(_sp_mf([3, 0], [3002399751580331])), P),
        # ── rc466 (`#T1188`): the seventy-row drain's FIX half, one row per
        # PATH, every row executing the exact route. The full per-op gate is
        # tests/test_exact_carrier_drain_rc466.py; these rows are the ones
        # that hold the drain here, in the census's own strict-zero layer, so
        # a re-demotion is red OUTSIDE the roster ceiling forever.
        ("hdc.loop_conj[int]", lambda: _hdc().loop_conj([P] + [0] * 7)[0], P),
        ("hdc.loop_bind[int]", lambda: _hdc().loop_bind([P] + [0] * 7, [1] + [0] * 7)[0], P),
        ("hdc.loop_left_op[int]", lambda: _hdc().loop_left_op([P] + [0] * 7)[0, 0], P),
        ("hdc.loop_right_op[int]", lambda: _hdc().loop_right_op([P] + [0] * 7)[0, 0], P),
        ("hdc.loop_associator[int]",
         lambda: _hdc().loop_associator([0, 0, 0, 0, P, 0, 0, 0], _e8(1), _e8(2))[7], 2 * P),
        ("hdc.cross7[int]", lambda: _hdc().cross7([0, P] + [0] * 6, _e8(2))[3], P),
        ("hdc.g2_three_form[int]", lambda: _hdc().g2_three_form([0, P] + [0] * 6, _e8(2), _e8(3)), P),
        ("hdc.loop_conj_hd[int]", lambda: _hdc().loop_conj_hd([P] + [0] * 7 + _e8(0))[0], P),
        ("hdc.loop_bind_hd[int]",
         lambda: _hdc().loop_bind_hd([P] + [0] * 7 + _e8(0), _e8(0) + _e8(0))[0], P),
        ("hdc.loop_unbind_hd[int]",
         lambda: _hdc().loop_unbind_hd(_e8(0) + _e8(0), [P] + [0] * 7 + _e8(0))[0], P),
        ("hdc.loop_runbind_hd[int]",
         lambda: _hdc().loop_runbind_hd(_e8(0) + _e8(0), [P] + [0] * 7 + _e8(0))[0], P),
        ("cascade.hypercomplex_couple[int, theta=0.0]",
         lambda: _cascade().hypercomplex_couple([P, 0, 0], theta=0.0)[1], P),
        ("cascade.as_oct8[int]", lambda: _cascade().as_oct8([P, 0, 0, 0])[0], P),
        ("cascade.as_quat4[int]", lambda: _cascade().as_quat4([P, 0, 0, 0, 0, 0, 0, 0])[0], P),
        ("cascade.qdft_summand[int, k*m == 0 mod n]",
         lambda: _cascade().qdft_summand([[P, 0, 0, 0]], 0, 0, 1, True, -1, [0.0, 1.0, 0.0, 0.0])[0], P),
        ("cascade.odft_summand[int, k*m == 0 mod n]",
         lambda: _cascade().odft_summand([[P] + [0] * 7], 0, 0, 1, "left", "left_associated", -1,
                                         [0.0, 1.0] + [0.0] * 6, [0.0, 1.0] + [0.0] * 6)[0], P),
        ("cascade.correlation_product[int]",
         lambda: _composites.correlation_product([3, 3002399751580331], 0, 1), P),
        ("cascade.coupled.multiplex_streams[int]",
         lambda: _coupled().multiplex_streams([[P, 2], [3, 4]])["driver"][0], P),
        ("laplacian.klein4_gain_laplacian[exact]",
         lambda: _la.klein4_gain_laplacian(2, [(0, 1)], [P], exact=True)["chi00"][0][0], P),
        ("laplacian.mass_normalized_laplacian[exact, rw]",
         lambda: _la.mass_normalized_laplacian(2, [(0, 1)], [P], masses=[1, 1], kind="rw", exact=True)[0][0], P),
        ("laplacian.mass_normalized_laplacian[exact, symmetric]",
         lambda: _la.mass_normalized_laplacian(2, [(0, 1)], [P], masses=[1, 1], exact=True)[0][0], P),
        ("laplacian.normalized_laplacian[exact, K4: the product root is exact]",
         lambda: _la.normalized_laplacian(4, [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)],
                                          [P] * 6, exact=True)[0][1] * (-3 * P), P),
        ("laplacian.magnetic_laplacian[exact, q=0]",
         lambda: _la.magnetic_laplacian(2, [(0, 1)], [P], q=0, exact=True)[0][0].real * 2, P),
        ("laplacian.quaternion_laplacian[exact]",
         lambda: _la.quaternion_laplacian(2, [(0, 1)], [P], exact=True)[0][0] * 2, P),
        # rc466 review fix: the eigen family's exact route (eig_exact behind
        # exact=, the jacobi_eigvals precedent); read back via as_rational().
        ("laplacian.symmetric_eigendecompose[exact]",
         lambda: _la.symmetric_eigendecompose([[P, 0], [0, 0]], exact=True)[0][1].as_rational(), P),
        ("laplacian.hermitian_eigendecompose[exact]",
         lambda: _la.hermitian_eigendecompose([[P, 0], [0, 0]], exact=True)[0][1].as_rational(), P),
        ("laplacian.fiedler_vector[exact, rank-1 operand: lambda_2 vector (1/P, 1), read as 1/v0]",
         lambda: (1 / _la.fiedler_vector([[1, P], [P, P * P]], exact=True)[0]).as_rational(), P),
        ("laplacian.three_fold_eigvec_groups[exact, rank-1 operand]",
         lambda: (-_la.three_fold_eigvec_groups([[1, P], [P, P * P]], exact=True)["mid"][0][0]).as_rational(), P),
        ("laplacian.klein4_relational_structure[exact, K2]",
         lambda: _la.klein4_relational_structure([(0, 1)], [P], exact=True)["coherence"]["chi00"].as_rational(), 2 * P),
        ("laplacian.elementwise_multiply_complex[int]",
         lambda: _la.elementwise_multiply_complex([P], [1])[0].real, P),
        ("signal_processing.polyphase[int]", lambda: _sp_op("polyphase")([P, 2, 3], [1, 2, 3, 4], L=2)[0], P + 4),
        ("signal_processing.multirate[int identity]", lambda: _sp_op("multirate")([P, 2, 3, 4])[0], P),
        ("signal_processing.multirate[int taps]",
         lambda: _sp_op("multirate")([P, 1, 1], up=2, filter_taps=[1, 1])[0], 2 * P),
        ("signal_processing.farrow[int, mu=0]", lambda: _sp_op("farrow")([0, 1, P, 3])[2], P),
        ("signal_processing.iir[int, a0=1]", lambda: _sp_op("iir")([1, 0, 0], [1], [1, P])[1], -P),
        ("signal_processing.wavelet[int, exact rational at 2 levels]",
         lambda: _sp_op("wavelet")([P, 4, 4, 4], levels=2)[0][0].as_rational() * 2 - 12, P),
        ("relativistic.four_momentum_squared[int]",
         lambda: _qm("relativistic").four_momentum_squared([P, 0, 0, 0]), P * P),
        ("pseudo_hermitian.inner_product_eta[int eta]",
         lambda: _qm("pseudo_hermitian").inner_product_eta([1, 0], [1, 0], [[P, 0], [0, 1]]).real, P),
        ("single_particle.density_matrix[int]",
         lambda: _qm("single_particle").density_matrix([P, 1])[0, 1], P),
        ("quaternion.quaternion_log[int, exact direction]",
         lambda: _qm("quaternion").quaternion_log([0, P, 0, 0])[1]
         - _qm("quaternion").quaternion_log([0, 1, 0, 0])[1] + P, P),
        # ⚠️ `composites.top_k_by_score[int]` WAS a row here and is REMOVED
        # rather than repaired, because no witness for it can fail. Measured
        # at the source: the whole body is
        #     order = sorted(range(n), key=lambda i: sc[i], reverse=largest)
        #     return order[:k]
        # — it performs NO numeric conversion and NO arithmetic, so there is
        # no carrier to demote; the caller's own objects are compared to each
        # other and their indices are returned. The shipped row asserted
        # `top_k_by_score([2**53+1, 2**53], 1)[0] == 0`, which holds whether
        # the scores round or not (a stable sort keeps index 0 on a tie), and
        # its oracle 0 was ALSO the one value Layer 0's vacuity guard skipped.
        # An instrument that cannot return otherwise is not a measurement.
        # This matches the rc462 census, which flagged the op and then
        # RETRACTED the flag; the retraction is the finding, and the way to
        # record it is to not carry a row that pretends to re-check it.
    ]


def _sp_fir(sig, coeffs):
    import srmech.signal_processing as sp
    return sp.fir(sig, coeffs)


# rc466 (`#T1188`) — lazy module handles for the drain rows above (the loop
# family lives in srmech.math.hdc, whose import srmech.cascade triggers).
def _hdc():
    from srmech.math import hdc
    return hdc


def _e8(i):
    return [1 if k == i else 0 for k in range(8)]


def _cascade():
    import srmech.cascade as cascade
    return cascade


def _coupled():
    from srmech.cascade import coupled
    return coupled


def _sp_op(name):
    import importlib
    return importlib.import_module(f"srmech.signal_processing.closed_form_ops.{name}").op


def _qm(name):
    import importlib
    return importlib.import_module(f"srmech.physics.qm.{name}")


def _sp_mf(sig, template):
    import srmech.signal_processing as sp
    return sp.matched_filter(sig, template)


@pytest.mark.parametrize("label,call,want", _l1_rows(),
                         ids=[r[0] for r in _l1_rows()])
def test_layer1_exact_in_exact_out(label, call, want) -> None:
    """STRICT ZERO. Every row here MUST return the exact value."""
    # UNCONDITIONAL since rc463's fix pass. It used to read `if want != 0:`,
    # exempting exactly one row whose oracle was an ORDINAL rather than a
    # value — and that row was the one row the guard therefore could not
    # check, which is precisely where a vacuous row hides. The row is gone,
    # every oracle is now a discriminating VALUE, and the guard is total. The
    # `-want` arm is the Class-K sign pin-slot (char_poly's oracle is -P),
    # written as an explicit branch and never as an ALU `abs()`.
    assert _discriminating(want if want > 0 else -want), (
        f"Layer-0 rejected the witness for {label}: it could not have failed")
    got = call()
    assert _eq_exact(got, want), (
        f"SILENT CARRIER DEMOTION at {label}: got {got!r}, exact value is "
        f"{want!r}. The op accepted an exact operand and returned a rounded "
        f"one. Fix the CARRIER (an exact peer already ships) — do not widen a "
        f"tolerance and do not add the row to CEIL_SILENT_DEMOTION.")


# ── LAYERS 2 & 3 — the COMMITTED census manifest, and the honesty gate over it ─
# rc465 (`#T1188`) — WHAT CHANGED, AND WHY IT HAD TO. TWICE.
#
# **First change.** Through rc464 this section was ``_DEMOTION_MANIFEST``: SIX
# hand-written rows, all six in ``srmech.math.laplacian``, with
# ``CEIL_SILENT_DEMOTION = 6`` pinned to ``len(_DEMOTION_MANIFEST)`` so the
# ceiling could not move without a human editing the list. Blind spot 1 above
# named the hole in as many words — *"a missing MANIFEST row is invisible"* —
# and the ADMISSION conjunct made it worse: membership was decided **by the
# SIGNATURE**, so an op declaring ``Sequence[float]`` was excluded BY
# CONSTRUCTION however exact the operand it was actually handed. That is R2
# shielding, on the rung this file's own ladder rates "WEAK … nothing enforces
# it". A type annotation was standing in for an accuracy contract, and the gate
# was reading the annotation.
#
# The population is now MEASURED by ``tools/demotion_probe.py`` over every
# sequence-shaped REGISTRY parameter. What it found on the rc464 surface:
#
#     rows probed                   703   (over 427 ops)
#     DEMOTED                       127   (over 101 ops)
#       of which UNDECLARED          77   (over  64 ops)   <- rc463 knew 6
#
# Six was not a residual. It was a sample.
#
# ⚠️ **Second change, and it is a PLACEMENT change: a census is not a gate.**
# The first cut called ``_dp.census()`` from this file — re-deriving the entire
# registry-wide population on every CI run, in every cell — and then diffed the
# result against a host-specific pin. Three consecutive commits fought the
# symptoms of that without asking whether the derivation belonged here:
#
#   8be4a95ce  red in every PURE shard, "the artefact did not know which cell
#              it came from"        -> a SECOND per-cell pinned artefact
#   83aa9b74f  `mlse` allocated 7.1 GiB inside the census and killed the runner
#                                   -> a skip
#   08d80a037  windows-latest has no SIGALRM, so the job timed out at 99%
#                                   -> two more skips
#
# Every one of those is a MITIGATION. Green was bought by teaching a census
# which ops to avoid, and the residue was two committed artefacts, a `SLOW_SKIP`
# roster of four ops (six entries across the two cells, retiring 2 measured rows
# in native and 8 in pure), and this file at 852 lines. Worse than the cost: the
# EXPECTED VALUE was per-cell, so the pin measured the HOST rather than the
# code — the same defect class this project keeps finding in its own
# instruments, arrived at from the inside.
#
# Deriving the population is expensive. Checking the invariant is not. So the
# census is now a DELIBERATE TOOL RUN producing ONE committed manifest —
# modelled on `tools/run_worked_examples.py` -> `tests/worked_examples_result.
# ndjson`, the tree's existing precedent for expensive derived state, down to
# the "regenerate with this exact command" message — and this file READS it.
#
#     python3 tools/demotion_probe.py        # in the cell you want to re-measure
#
# MEASURED, the whole point of the change: this file cost **66.18 s (native) /
# 153.80 s (pure)** per CI job and now costs **8.02 s / 7.21 s**, of which every
# test call is <= 0.04 s and the rest is `import srmech`. In the `--forked`
# asserts-live cell it cost the derivation ONCE PER TEST — `pytest-forked` gives
# each test a fresh child, so the module-level cache never survived and 15
# census-consuming tests each paid it in full: ~15 minutes of census, observed
# as +12 m of wall clock on `asserts-live shard 4/4` against the `main`
# baseline. It is now a file read, identically in every cell.
#
# ⚠️ **AND THE TWO PER-CELL ARTEFACTS BECOME ONE — WITHOUT LOSING THE FINDING.**
# The native and pure cells genuinely disagree, and absorbing that into two pins
# is what made it invisible. It is now a NAMED FINDING with its op list, pinned
# in `_DIVERGENT` below and recorded in `meta.divergent`. An op whose answer
# depends on whether `libsrmech` loaded is the `fir` / `matched_filter` class
# rc463 already rated WORSE than a plain demotion: it is two ops wearing one
# name.

import demotion_probe as _dp   # tools/ is on sys.path via the header import
from srmech.amsc.format import sha256_bytes

MANIFEST = Path(__file__).resolve().parent / "demotion_census.ndjson"

#: ⚠️ **THE STALENESS GUARD, AND ITS BLIND SPOT — READ BOTH HALVES.**
#:
#: A gate that only reads a committed file goes stale silently: someone adds a
#: demoting op, nobody re-runs the probe, and the manifest never learns. That is
#: the "checker that verifies one side of a relation" failure this tree has hit
#: repeatedly, so the guard is here and it costs no execution — hash the
#: ``(op name, parameter types, return type)`` triple over the whole registry
#: (:func:`demotion_probe.registry_signature`) and compare it to the hash the
#: manifest recorded when it was measured. That digest moves when an op is
#: ADDED, REMOVED or RE-SIGNATURED, which is exactly what determines
#: demotion-CANDIDACY: the probe picks parameters by their REGISTRY type, binds
#: them from the signature, and files the answer under the return carrier.
#:
#: ⚠️ **IT DOES NOT CATCH AN IMPLEMENTATION CHANGE THAT ALTERS CARRIER
#: BEHAVIOUR WITHOUT CHANGING THE SIGNATURE** — which is the very class this
#: file exists to find. Change `einsum`'s accumulator from `0` to `0j` and this
#: digest does not move; the manifest keeps saying EXACT and the gate keeps
#: saying green.
#:
#: This is written out rather than left implied because **the tree has already
#: paid for the identical blind spot once**, and said so: the worked-example
#: ledger's own note records that ``--only-stale`` *"keys on the SNIPPET-TEXT
#: hash, which does not move when an implementation moves — the blind spot the
#: freshness hook exists for"*, and *"that blind spot is exactly how the ℚ-flip
#: defect shipped"*. The mitigation there — re-run BY NAME with explicit
#: ``--only`` whenever the implementation moved — is the mitigation here:
#: **an rc that changes a numeric carrier must re-run the probe, and no digest
#: will remind it to.** The Layer-1 strict-zero rows below are what actually
#: EXECUTE against the shipped carriers on every CI run; they are the live half
#: of this file and they did not move.
_STALENESS_BLIND_SPOT = (
    "the registry signature does not move when an implementation changes "
    "carrier behaviour behind an unchanged signature")

#: sha256 over the NORMALISED undeclared roster, BOTH columns, one digest:
#: ``"<cell>\t<op>::<param>"`` lines, sorted, newline-joined with a trailing
#: newline, UTF-8. Normalised rather than raw file bytes for the reason
#: ``tests/test_op_name_set_witness_rc361.py`` gives about its own manifest —
#: a CRLF checkout must not make the digest disagree between the Windows and
#: Linux cells.
#:
#: This REPLACES ``CEIL_UNDECLARED_DEMOTION_BY_CELL``, and it is strictly
#: stronger than the ceiling it replaces. A bare ``<= CEIL`` lets a NEW
#: undeclared demoter in whenever an unrelated one drains in the same change;
#: an IDENTITY forbids that in both directions, so a drain and a regression
#: cannot cancel. It is also the two-edit discipline rc361 established: the
#: roster is pinned on disk, the digest is pinned in source, and a careless
#: single-file regeneration cannot pass.
#:
#: Both columns ride ONE digest deliberately. The cells disagree, and a
#: per-cell constant asserted only in its own cell is how the previous cut
#: ended up measuring the host: this one is asserted in FULL in EVERY cell.
#: was: 99c2164df1109c3f7f1c2fd18f4b1592254dfc4ec548f2315558461cd1b7e17b (rc466,
#: the roster at ONE). rc467 (`#T1188`) takes it to ZERO, so this is the digest
#: of an EMPTY roster body -- ``_roster_body`` renders that as b"\n". It is
#: PINNED FROM THE PROBE'S OWN RE-MEASURE in both cells, not from the
#: derivation, so the constant records what was measured rather than what was
#: expected to be measured.
EXPECTED_UNDECLARED_ROSTER_SHA256 = (
    "01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b")

#: Pinned only so the failure message can say "70 -> 71" instead of dumping
#: every key; the ROSTER above is the actual contract. Same relationship
#: ``EXPECTED_N`` has to ``EXPECTED_NAME_SET_SHA256`` in rc361.
#: was: {"native": 1, "pure": 1} (rc466). ZERO at rc467 (`#T1188`) -- the whole
#: roster is drained. DEMOTED itself also moved, 70 -> 69 in BOTH cells, which
#: is a drain BY FIXING and not by narrowing: compensated_sum's harvested
#: witness is [1e10, 1.0, -1e10, 2.0], every leaf integral, so the probe's
#: `exactify` reads it as int and the new exact rung answers it EXACTLY.
EXPECTED_UNDECLARED_N = {"native": 0, "pure": 0}

#: Down-only. ``NO_SHAPE`` rows — parameters the probe could not build ANY
#: candidate binding for, so no carrier verdict was ever reachable. This is the
#: constant ``tools/demotion_probe.py``'s required-disclosure bullet 1 names as
#: "the honest statement of the instrument's reach", and through rc465 it
#: existed ONLY in that sentence: repo-wide grep found exactly one occurrence,
#: the disclosure itself. A named ratchet with no definition and no assertion is
#: the "gate that cannot fail" shape.
#:
#: Lowering it needs nothing; raising it means the probe reaches LESS than it
#: did, which is a regression in the INSTRUMENT and needs saying out loud.
#: Keyed by cell because the two columns are separate measurements — but
#: asserted over BOTH columns in EVERY cell, which is the difference between
#: recording a per-cell fact and pinning a host.
CEIL_DEMOTION_UNREACHED = {"native": 52, "pure": 52}

#: ⚠️ **THE NAMED FINDING** (`#T1188`). Rows whose verdict DEPENDS ON WHETHER
#: ``libsrmech`` LOADED. rc463 rates this class worse than a plain demotion —
#: an op whose answer is decided by which projection happens to be dispatching
#: is two ops wearing one name — and `08d80a037` absorbed it into a second
#: pinned artefact, which is precisely how it stopped being a finding.
#:
#: Pinned by IDENTITY, with each op named, so a NEW divergence is RED. Draining
#: one means making the two projections agree, or declaring the disagreement on
#: the op; it does not mean editing this set to match.
#: MEASURED at rc465 on one tree, both cells, registry signature dba6fa94101f.
#: Each entry is a real op whose ANSWER — or whose refusal — is decided by
#: which projection was loaded. ``iir::a`` is the sharpest: the C path ROUNDS
#: an exact operand that the pure path carries exactly, which is the
#: ``fir`` / ``matched_filter`` shape rc463 names. The ``RAISED`` pairs are the
#: same fact wearing the instrument's clothes — one projection REFUSES a
#: binding the other accepts, which is still two behaviours under one name.
_DIVERGENT: "frozenset[str]" = frozenset({
    # the C path rounds an exact operand the pure path keeps exact
    # one projection reaches a carrier verdict the other never gets to
    "srmech.math.laplacian.klein4_gain_laplacian::gains",     # EXACT / RAISED
    "srmech.biology.coupling.resonant_spectrum_sparse::edges_or_path",  # EXACT / RAISED
    "srmech.math.modular_linalg.crt_combine::moduli",         # RAISED / EXACT
    "srmech.math.hdc.bundle::vectors",                        # RAISED / EXACT
    "srmech.math.hdc.bundle_with_ties::vectors",              # RAISED / EXACT
    "srmech.signal_processing.hdc_truncation::vectors",       # RAISED / EXACT
    "srmech.math.hdc.klein4_bundle_resolve::acc",             # RAISED / INSENSITIVE
    "srmech.math.laplacian.klein4_relational_structure::gains",  # INSENSITIVE / RAISED
    "srmech.math.laplacian.heat_trace::L",                    # INSENSITIVE / RAISED
    "srmech.math.laplacian.heat_trace::t",                    # INSENSITIVE / RAISED
    "srmech.cascade.matrix_cascades.lstsq::a",                # INEXACT_BASE / RAISED
})

#: The ops rc465 FIXED. Strict zero, forever: these carry an exact operand
#: exactly, so a row for any of them in the undeclared roster is a regression,
#: not a debt. Named rather than derived from a module prefix, because a module
#: prefix would silently absorb a NEW op of the same family.
_FIXED_IN_RC465 = frozenset({
    "srmech.physics.qm.octonion.octonion_left_mult",
    "srmech.physics.qm.octonion.octonion_right_mult",
    "srmech.physics.qm.octonion.octonion_conjugate",
    "srmech.physics.qm.octonion.octonion_norm",
    "srmech.physics.qm.quaternion.quaternion_left_mult",
    "srmech.physics.qm.quaternion.quaternion_right_mult",
    "srmech.physics.qm.quaternion.quaternion_conjugate",
    "srmech.physics.qm.quaternion.quaternion_norm",
    "srmech.physics.qm.triality.triality_apply",
})

#: The ops rc466 FIXED (`#T1188`) — the seventy-row drain's FIX half. Strict
#: zero, forever, on the same terms as ``_FIXED_IN_RC465``: each carries an
#: exact operand exactly (an exact CARRIER end to end, or an exact ROUTE with
#: ONE declared bound — the rc465 ``octonion_norm`` shape), with float as the
#: caller's own explicit request. Named, not derived from a module prefix. The
#: three ``*_hd`` siblings were never on the roster (the census filed them
#: INEXACT_BASE behind a float in the OTHER operand) and are pinned here so the
#: family's one entry gate cannot split into two behaviours again.
_FIXED_IN_RC466 = frozenset({
    "srmech.math.hdc.loop_conj",
    "srmech.math.hdc.loop_bind",
    "srmech.math.hdc.loop_inv",
    "srmech.math.hdc.loop_left_op",
    "srmech.math.hdc.loop_right_op",
    "srmech.math.hdc.loop_associator",
    "srmech.math.hdc.cross7",
    "srmech.math.hdc.g2_three_form",
    "srmech.math.hdc.loop_conj_hd",
    "srmech.math.hdc.loop_inv_hd",
    "srmech.math.hdc.loop_bind_hd",
    "srmech.math.hdc.loop_unbind_hd",
    "srmech.math.hdc.loop_runbind_hd",
    "srmech.cascade.hypercomplex_couple",
    "srmech.cascade.cd_couple_working",
    "srmech.cascade.cdr_couple_working",
    "srmech.cascade.cdr_uncouple_working",
    "srmech.cascade.as_oct8",
    "srmech.cascade.as_quat4",
    "srmech.cascade.qdft_summand",
    "srmech.cascade.odft_summand",
    "srmech.cascade.correlation_product",
    "srmech.cascade.coupled.multiplex_streams",
    "srmech.math.laplacian.klein4_gain_laplacian",
    "srmech.math.laplacian.mass_normalized_laplacian",
    "srmech.math.laplacian.normalized_laplacian",
    "srmech.math.laplacian.magnetic_laplacian",
    "srmech.math.laplacian.quaternion_laplacian",
    "srmech.math.laplacian.elementwise_multiply_complex",
    "srmech.math.laplacian.ground_state_flux_response",
    # rc466 review fix: DECLARED at Stage 2, FIXED at the review — the exact
    # peer (eig_exact) ships and jacobi_eigvals already wears it behind exact=.
    "srmech.math.laplacian.hermitian_eigendecompose",
    "srmech.math.laplacian.symmetric_eigendecompose",
    "srmech.math.laplacian.three_fold_eigvec_groups",
    "srmech.math.laplacian.fiedler_vector",
    "srmech.math.laplacian.klein4_relational_structure",
    "srmech.signal_processing.rfft",
    "srmech.signal_processing.stft",
    "srmech.signal_processing.ofdm",
    "srmech.signal_processing.polyphase",
    "srmech.signal_processing.multirate",
    "srmech.signal_processing.farrow",
    "srmech.signal_processing.iir",
    "srmech.signal_processing.wavelet",
    "srmech.physics.qm.relativistic.four_momentum_squared",
    "srmech.physics.qm.pseudo_hermitian.inner_product_eta",
    "srmech.physics.qm.single_particle.density_matrix",
    "srmech.physics.qm.bell.operator_norm",
    "srmech.physics.qm.quaternion.quaternion_log",
})

#: ⚠️ THE ONE ROW rc466 DEFERRED — "exact peer ships, deferred", never declared.
#: ``resonant_spectrum`` returns four faculties in one dict; ``tensions`` and
#: ``force_orders`` have shipped exact peers (``eigvals_exact`` intervals,
#: ``QMat.matmul`` powers) but ``modes`` needs ``eigvec_exact`` with a
#: caller-supplied IRREDUCIBLE minimal polynomial per eigenvalue (the documented
#: rc-E follow-up at ``matrix_cascades.py``) and each eigenvalue lives in its
#: own number field with no compositum carrier, so an exact route today would
#: return exact tensions beside float modes — the mixed-carrier shape rc463
#: names as the defect. It waits on a ``modes`` design, not on effort.
#:
#: Pinned so the debt stays VISIBLE: the row must remain in the undeclared
#: roster of BOTH cells. Draining it by an R3 sentence would convert a defect
#: into documentation (the failure mode `#T1188` names); draining it by a real
#: exact route is GOOD NEWS the gate reports, at which point the op moves to a
#: ``_FIXED_IN_RC4NN`` set. A drain by narrowing admission (the row leaving as
#: ``RAISED``) is refused on the same terms as everywhere else in this file.
#: rc467 (`#T1188`): the ops rc467 drained by FIXING, kept ALONGSIDE
#: ``_FIXED_IN_RC466`` and never merged into it -- that name is imported by
#: ``tests/test_declared_inexactness_rc466.py`` across files, so renaming it
#: breaks a gate in a different module for no gain.
#:
#: ``resonant_spectrum`` is the row rc466 left in the roster on purpose, under
#: a ``_DEFERRED_EXACT_PEER_SHIPS`` pin (deleted here, together with its
#: Layer-3 test) whose stated ground was that the ``modes`` faculty "needs
#: eigvec_exact with a caller-supplied IRREDUCIBLE minimal polynomial per
#: eigenvalue". ``eig_exact`` supplies the irreducible minimal polynomial
#: ITSELF and returned ``vectors_qalg`` at 32246efca -- the very commit the pin
#: was written in -- and the ``_symmetric_eig_exact`` wrapper landed one commit
#: later at c7b5f9501. The pin was stale on the day it was written.
#:
#: ``compensated_sum`` is here for a different reason and is worth separating:
#: it was never in the undeclared ROSTER, because its declaration already
#: PROMISED the exact rung. What was missing was the rung. Its census row moved
#: DEMOTED -> EXACT behind an UNCHANGED signature, which is this instrument's
#: declared blind spot, so it is pinned by name here rather than left to the
#: roster to notice.
_FIXED_IN_RC467 = frozenset({
    "srmech.biology.coupling.resonant_spectrum",
    "srmech.cascade.compensated_sum",
})

#: The rc463 hand-written six, kept as the probe's POSITIVE CONTROL rather than
#: as the population. If the instrument cannot re-find the rows a human found by
#: reading code, it is not measuring — the ``test_layer0`` question asked of the
#: instrument instead of the witness.
_RC463_SIX = (
    ("srmech.math.laplacian.mat_dot", "a"),
    ("srmech.math.laplacian.mat_outer", "a"),
    ("srmech.math.laplacian.mat_matvec", "m"),
    ("srmech.math.laplacian.dense_adjacency", "weights"),
    ("srmech.math.laplacian.dense_laplacian", "weights"),
    ("srmech.math.laplacian.signed_laplacian", "weights"),
)

_REGEN = ("PYTHONPATH=$PWD python3 tools/demotion_probe.py   "
          "# run it ONCE PER CELL; it merges the cell it is run in")

_CACHE: dict = {}


def _manifest():
    """``(meta, rows)`` — read once per session; it is a file read, not a run."""
    if "m" not in _CACHE:
        assert MANIFEST.exists(), (
            f"{MANIFEST.name} is missing. It is a MEASUREMENT, not a generated "
            f"artifact, so nothing regenerates it for you:\n    {_REGEN}")
        _CACHE["m"] = _dp.load_manifest(MANIFEST)
    return _CACHE["m"]


def _cells():
    return _manifest()[0]["cells_measured"]


def _roster_body(rows) -> bytes:
    lines = sorted(f"{c}\t{k}" for c in _cells()
                   for k in _dp.undeclared_keys(rows, c))
    return ("\n".join(lines) + "\n").encode("utf-8")


# ── the manifest's own currency ───────────────────────────────────────────────

def test_the_manifest_carries_both_cells() -> None:
    """One artefact, two columns — the shape that replaced two artefacts.

    A half-measured manifest is not a smaller measurement, it is a file whose
    every per-cell assertion below silently narrows to one cell. That is the
    rc460 ledger defect (a ratchet that went inert and reported itself as one
    routine ``skipped``) and it is refused by name here rather than skipped.
    """
    meta, rows = _manifest()
    assert meta["cells_measured"] == ["native", "pure"], (
        f"the manifest carries only {meta['cells_measured']}. Re-measure the "
        f"missing cell — move srmech/_native/libsrmech.so aside for `pure`, "
        f"build it for `native` — and run:\n    {_REGEN}")
    both = [r for r in rows if r.get("native") and r.get("pure")]
    assert len(both) >= 600, (
        f"only {len(both)} of {len(rows)} rows carry BOTH columns; the two "
        f"halves were measured against different reaches")


def test_the_manifest_is_fresh_against_the_registry_signature() -> None:
    """THE STALENESS GUARD. Costs no execution; declares its own blind spot.

    Every cell's column records the registry signature it was measured against.
    A drift means an op was added, removed or re-signatured since — i.e. the
    demotion-candidate population moved — and the manifest has not been told.

    ⚠️ It cannot see an implementation change behind an unchanged signature.
    See ``_STALENESS_BLIND_SPOT`` above for why that limit is written down
    rather than left for a future reader to discover the way the worked-example
    ledger's ℚ-flip was discovered.
    """
    meta, _ = _manifest()
    live = _dp.registry_signature()
    stale = {c: s for c, s in meta["registry_signature_sha256"].items()
             if s != live}
    assert not stale, (
        f"the census manifest is STALE against the registry: {sorted(stale)} "
        f"measured {[s[:12] for s in stale.values()]} and this tree is "
        f"{live[:12]}. An op was added, removed or re-signatured, so the "
        f"demotion-candidate population moved. Re-measure IN EACH STALE "
        f"CELL:\n    {_REGEN}\n"
        f"Do NOT repoint the digest by hand — it lives in the manifest the "
        f"tool writes.")


def test_the_staleness_guard_is_not_vacuous() -> None:
    """The guard must MOVE for each of the three changes it claims to catch.

    Asserted in process over a MUTATED COPY of the live signature lines, so
    nothing shipped is touched: an op added, an op removed, an op
    re-signatured. Plus the guard and its own witness agreeing, because a
    digest computed over a different list than the one this test mutates would
    make the other three assertions vacuous.

    ⚠️ **The converse is NOT asserted, and cannot be from here.** "It does not
    move when an implementation changes behind an unchanged signature" is the
    declared blind spot (see ``_STALENESS_BLIND_SPOT``), and a body change has
    no representation in a list of signature strings — there is nothing to
    mutate. Saying so is the point: a docstring claiming both halves while
    testing one is the shape this whole file exists to remove.
    """
    def digest(lines):
        return sha256_bytes(("\n".join(sorted(lines)) + "\n").encode("utf-8"))

    base = _dp.registry_signature_lines()
    assert digest(base) == _dp.registry_signature(), (
        "registry_signature() is not the digest of registry_signature_lines(); "
        "the guard and its own witness have come apart")
    assert digest(base + ["srmech.planted.new_op|v:Sequence[float]|Mat"]) \
        != digest(base), "an ADDED op does not move the signature"
    assert digest(base[1:]) != digest(base), \
        "a REMOVED op does not move the signature"
    resigned = [base[0].replace("|", "|extra:Sequence[int],", 1)] + base[1:]
    assert digest(resigned) != digest(base), \
        "a RE-SIGNATURED op does not move the signature"


# ── LAYER 2 — the population, read off the manifest ───────────────────────────

def test_layer2_the_probe_refinds_the_rc463_hand_written_six() -> None:
    """POSITIVE CONTROL. An auto-populating instrument that misses what a human
    already found by reading the code is not an upgrade on the human."""
    _meta, rows = _manifest()
    by_key = {_dp.key(r): r for r in rows}
    for op, param in _RC463_SIX:
        r = by_key.get(f"{op}::{param}")
        assert r is not None, f"the probe did not reach {op}.{param} at all"
        for c in _cells():
            assert r[c]["verdict"] == "DEMOTED", (
                f"{op}.{param} was a hand-verified rc463 demoter and the {c} "
                f"column now reads {r[c]['verdict']} — the ORACLE moved, not "
                f"the op")
            assert r[c].get("declares"), (
                f"{op}.{param} lost its R3 declaration in the {c} column; "
                f"rc463 required all six to carry one")


def test_layer2_the_population_is_not_a_sample() -> None:
    """NON-VACUITY, in the direction this gate actually failed in.

    rc463's ceiling was ``len(_DEMOTION_MANIFEST)``, so it was green over
    whatever list happened to be there. These floors are what stop the
    replacement quietly shrinking back into a sample.
    """
    _meta, rows = _manifest()
    assert len(rows) >= 600, f"only {len(rows)} rows in the manifest"
    assert len({r["op"] for r in rows}) >= 400
    for c in _cells():
        decided = [r for r in rows
                   if r.get(c) and r[c]["verdict"] in ("DEMOTED", "EXACT")]
        assert len(decided) >= 180, (
            f"[{c}] only {len(decided)} rows reached a carrier verdict; the "
            f"probe has narrowed and the roster below is measuring less than "
            f"it says")
        assert len(_dp.demoters(rows, c)) > len(_dp.undeclared(rows, c)), (
            f"[{c}] every measured demoter is undeclared — either Layer 3's "
            f"vocabulary stopped matching anything, or the delegate follow "
            f"broke")


def test_layer2_the_unreached_population_is_ratcheted_down_only() -> None:
    """The probe's REACH, as a ratchet rather than as a sentence.

    ``NO_SHAPE`` is the honest count of parameters the instrument could not
    address at all. Bounded here so the population cannot grow while the gate
    stays green — the failure mode a coverage number carried only in prose has
    no defence against. **Both columns are asserted in every cell**, which is
    what makes this a fact about the tree rather than about the host.
    """
    _meta, rows = _manifest()
    for c in _cells():
        n = len([r for r in rows
                 if r.get(c) and r[c]["verdict"] == "NO_SHAPE"])
        ceil = CEIL_DEMOTION_UNREACHED[c]
        assert n <= ceil, (
            f"[{c}] {n} rows are NO_SHAPE (the probe could build no binding at "
            f"all), ceiling is {ceil}. This ratchet is DOWN-ONLY: the "
            f"instrument reaching LESS than it did is a regression in the "
            f"instrument. Widen `synthesize` rather than the ceiling; each row "
            f"carries its own `reason`.")
        assert n == ceil, (
            f"GOOD NEWS, ACTION REQUIRED: only {n} of {ceil} rows are "
            f"unreachable in the {c} column. Lower "
            f"CEIL_DEMOTION_UNREACHED[{c!r}] to {n} in the SAME change.")


# ── LAYER 3 — the honesty gate, as a pinned ROSTER ────────────────────────────

def test_layer3_the_undeclared_roster_matches_its_pinned_digest() -> None:
    """STRICT IDENTITY over the residual — the half a count cannot do.

    A bare ``<= CEIL`` lets a NEW undeclared demoter in whenever an unrelated
    one drains in the same change. The roster forbids that: membership is
    pinned, so an addition is red even at a lower count, and a drain is red
    until it is RECORDED. Both directions fail; neither can be paid for with
    the other.
    """
    _meta, rows = _manifest()
    got = {c: _dp.undeclared_keys(rows, c) for c in _cells()}
    digest = sha256_bytes(_roster_body(rows))
    counts = {c: len(v) for c, v in got.items()}
    if digest != EXPECTED_UNDECLARED_ROSTER_SHA256:
        delta = []
        for c in _cells():
            want_n = EXPECTED_UNDECLARED_N.get(c)
            delta.append(f"{c}: {counts[c]} (pinned {want_n})")
        sample = {c: v[:6] for c, v in got.items()}
        raise AssertionError(
            "the UNDECLARED carrier-demotion roster moved.\n"
            f"  digest   {digest}\n"
            f"  pinned   {EXPECTED_UNDECLARED_ROSTER_SHA256}\n"
            f"  counts   {'; '.join(delta)}\n"
            f"  sample   {sample}\n"
            "WHICH rows moved is in `git diff tests/demotion_census.ndjson` "
            "— the meta row carries the full roster under `undeclared`, one "
            "key per cell, so the added and removed keys read straight off "
            "the diff. This gate cannot compute them: it holds a digest, not "
            "a previous roster, and holding the roster twice is the "
            "hand-written manifest rc465 removed.\n"
            "If a row was ADDED: fix the carrier (an exact peer ships for most "
            "of this surface) or publish an R3 accuracy statement — do not add "
            "the row to the manifest and move on. If a row DRAINED: good news, "
            "action required — re-pin EXPECTED_UNDECLARED_ROSTER_SHA256 and "
            "EXPECTED_UNDECLARED_N to the values above in the SAME change, so "
            "the gain cannot be given back.")
    assert counts == EXPECTED_UNDECLARED_N, (
        f"the roster digest matches but the counts do not: {counts} vs "
        f"{EXPECTED_UNDECLARED_N}. One of the two pins was edited alone.")


@pytest.mark.parametrize("op", sorted(_FIXED_IN_RC465))
def test_layer3_the_rc465_fixed_family_is_strict_zero(op) -> None:
    """The nine R2-shielded ops rc465 repaired can never re-enter the roster.

    They are not under any ceiling and never will be: each carries an exact
    operand on an exact carrier end to end, with float as the caller's own
    explicit request. A row here is a REGRESSION.
    """
    _meta, rows = _manifest()
    bad = sorted(f"{c}:{_dp.key(r)}" for c in _cells()
                 for r in _dp.undeclared(rows, c) if r["op"] == op)
    assert not bad, (
        f"{op} is demoting again with no accuracy declaration: {bad}. rc465 "
        f"gave it an exact carrier; see tests/test_octonion_exact_carrier_rc465.py")


@pytest.mark.parametrize("op", sorted(_FIXED_IN_RC466))
def test_layer3_the_rc466_fixed_family_is_strict_zero(op) -> None:
    """The forty-eight ops rc466 drained by FIXING can never re-enter the roster
    (forty-three at Stage 1; the five eigen-family ops moved here from the
    DECLARE ledger at the rc466 review, each with an executed ``exact=`` route).

    The committed manifest was re-measured in BOTH cells at Stage 3 of rc466
    (`#T1188`) after the last registry-type edit, so this reads the drain as
    RECORDED; between the Stage-1 commit and that re-measurement it was red by
    design. ``stft::signal`` is the one row expected to remain DEMOTED after
    the fix (a lone 54-bit sample in a zero frame is that sample in every bin,
    and the single terminal float lift rounds it); it drains by its R3 lift
    sentence, and ``stft`` is therefore NOT in this set's roster check but in
    the DECLARE ledger.
    """
    if op == "srmech.signal_processing.stft":
        pytest.skip("stft::signal drains by its terminal-lift R3 sentence (declared), not by the roster")
    _meta, rows = _manifest()
    bad = sorted(f"{c}:{_dp.key(r)}" for c in _cells()
                 for r in _dp.undeclared(rows, c) if r["op"] == op)
    assert not bad, (
        f"{op} is demoting again with no accuracy declaration: {bad}. rc466 "
        f"gave it an exact carrier; see tests/test_exact_carrier_drain_rc466.py")


@pytest.mark.parametrize("op", sorted(_FIXED_IN_RC467))
def test_layer3_the_rc467_fixed_family_is_strict_zero(op) -> None:
    """The two ops rc467 drained by FIXING can never re-enter the roster.

    This test REPLACES ``test_layer3_the_deferred_row_is_still_undeclared_debt``
    -- deleted in the same change as the ``_DEFERRED_EXACT_PEER_SHIPS`` set it
    read, because an empty ``parametrize`` collects zero cases and reports
    SKIPPED, which is a gate that cannot fail rather than a gate that passes.

    That test's own failure message wrote the instruction this change follows:
    *"If it drained by an exact route: GOOD NEWS, ACTION REQUIRED -- move the
    op into a _FIXED_IN_RC4NN set and remove it from _DEFERRED_EXACT_PEER_SHIPS
    in the SAME change."* It also named the two ways of draining that are
    REFUSED, and neither was taken: the route is executed rather than a
    sentence (see ``tests/test_exact_carrier_drain_rc466.py``), and admission
    was widened rather than narrowed -- the row did not leave as ``RAISED``,
    and the default float path is byte-unchanged on both ops.
    """
    _meta, rows = _manifest()
    bad = sorted(f"{c}:{_dp.key(r)}" for c in _cells()
                 for r in _dp.undeclared(rows, c) if r["op"] == op)
    assert not bad, (
        f"{op} is demoting again with no accuracy declaration: {bad}. rc467 "
        f"gave it an exact route; see tests/test_exact_carrier_drain_rc466.py")


def test_the_native_pure_divergence_is_a_named_finding() -> None:
    """⚠️ AN OP WHOSE ANSWER DEPENDS ON WHETHER ``libsrmech`` LOADED.

    rc463 rates this WORSE than a plain demotion: it is two ops wearing one
    name, and no caller can predict which one they get. `08d80a037` responded
    to it by pinning two per-cell artefacts, which made the CI board green and
    the finding invisible — the mitigation this rc replaces. Here the set is
    pinned by IDENTITY, every member named, so a NEW divergence is RED and a
    resolved one has to be recorded.
    """
    _meta, rows = _manifest()
    got = frozenset(_dp.key(r) for r in _dp.divergent(rows))
    new = sorted(got - _DIVERGENT)
    gone = sorted(_DIVERGENT - got)
    detail = {_dp.key(r): f"native={r['native']['verdict']} "
                          f"pure={r['pure']['verdict']}"
              for r in _dp.divergent(rows) if _dp.key(r) in set(new)}
    assert not new, (
        f"{len(new)} op(s) now answer DIFFERENTLY depending on whether "
        f"libsrmech loaded: {detail}. Make the two projections agree, or "
        f"declare the disagreement on the op — do not add the row to "
        f"_DIVERGENT and move on.")
    assert not gone, (
        f"GOOD NEWS, ACTION REQUIRED: {len(gone)} row(s) no longer diverge "
        f"between the cells ({gone}). Remove them from _DIVERGENT in the SAME "
        f"change, so the gain is recorded rather than absorbed.")


# ── the INSTRUMENT's own non-vacuity — in process, nothing committed ──────────

def test_layer3_the_probe_can_return_both_verdicts() -> None:
    """NON-VACUITY of the ORACLE itself, planted in-process, nothing committed.

    An instrument that cannot say DEMOTED is decorative; one that cannot say
    EXACT flags the whole registry and gets switched off. Both directions are
    exercised here on functions written for the purpose, so the proof does not
    depend on any shipped op keeping its current carrier — and it is the one
    part of Layers 2-3 that still EXECUTES the probe, because it is the one
    part that costs microseconds.
    """
    def demotes(v):
        """Returns a float."""                      # R1 only — not a declaration
        return [float(c) for c in v]

    def stays_exact(v):
        return [c for c in v]

    def ignores(v):
        return 7

    d = _dp.probe_param(demotes, {"v": [1, 1]}, "planted.demotes", "v", "list")
    assert d["verdict"] == "DEMOTED", d
    assert _dp.declaration_hits(demotes) == [], (
        "an R1-only contract read as declared; the honesty ladder has collapsed")

    e = _dp.probe_param(stays_exact, {"v": [1, 1]}, "planted.exact", "v", "list")
    assert e["verdict"] == "EXACT", e

    i = _dp.probe_param(ignores, {"v": [1, 1]}, "planted.ignores", "v", "list")
    assert i["verdict"] in ("INSENSITIVE", "UNRESOLVED_AT_WITNESS"), i


def test_layer3_the_delegate_follow_reaches_outside_laplacian() -> None:
    """The single change that made Layer 3 addressable at all.

    rc463 resolved a delegate as ``getattr(_la, name)`` — hard-wired to
    ``srmech.math.laplacian`` — so it could not read the contract of any op
    outside the module its six hand-rows came from. The probe resolves in
    ``fn.__globals__``. Both halves are pinned: the historical false-positive
    it was added for still passes, and an op in another module is now reachable.
    """
    for fn in (_la.mat_norm, _la.mat_svd, _la.jacobi_eigvals,
               _composites.compensated_sum, _mc.lstsq):
        assert _dp.declaration_hits(fn), (
            f"{fn.__name__} carries a real accuracy contract but Layer 3 read "
            f"it as undeclared")

    def outside(v):
        """Delegates to a documented helper."""
        return _documented_helper(v)

    assert _dp.declaration_hits(outside), (
        "the delegate follow no longer resolves in fn.__globals__, so Layer 3 "
        "is confined to one module again")


def _documented_helper(v):
    """Returns a float, accurate to round-off (~1 ULP)."""
    return float(v[0])


# ── LAYER 4 — the CLAIM gate ──────────────────────────────────────────────────
# "Value-faithful to the NumPy X" appeals to an oracle this package CANNOT RUN
# BY POLICY: numpy is absent and must stay absent. Such a clause is not a
# measurement. It may stay only where the SAME sentence bounds it with an
# accuracy qualifier, so a reader learns the limit without needing the oracle.

def _numpy_faithfulness_claims():
    """Every registered ToolEntry sentence claiming NumPy value-faithfulness."""
    out = []
    for tool in get_tool_schema().tools:
        for field in (tool.summary or "", tool.explanation or ""):
            low = field.lower()
            idx = low.find("value-faithful")
            while idx != -1:
                # the claim's own SENTENCE: up to the next period-space.
                end = low.find(". ", idx)
                sentence = field[idx:(end if end != -1 else len(field))]
                if "numpy" in sentence.lower():
                    out.append((tool.name, sentence))
                idx = low.find("value-faithful", idx + 1)
    return out


# ⚠️ The exemption vocabulary has TWO halves and both are load-bearing.
# An accuracy qualifier BOUNDS a live claim. A retraction marker means the
# sentence is *documenting* a claim rather than making one — the same carve-out
# `CLAUDE.md` records for the ref-notation guard, where a bad ref quoted inside
# a code span is legitimate. Without it this gate flags the very prose that
# retires the claim, which is a false positive that would push an author toward
# deleting the explanation instead of the claim.
#: rc465: the R3 vocabulary now has ONE definition, in the probe, and Layer 4
#: reads it from there. It was duplicated here and in the probe for exactly as
#: long as it took to notice — which is the same defect in miniature as the
#: manifest this rc replaced.
_R3_VOCABULARY = _dp.R3_VOCABULARY

_RETRACTION = ("retired", "retracted", "corrected", "no longer", "was false",
               "not bit-identical")


def _claim_is_qualified(sentence: str) -> bool:
    """Does this NumPy-faithfulness sentence BOUND itself, or retract itself?

    ⚠️ **The bare token ``"exact"`` used to be in this list and is REMOVED.**
    It let a claim buy exemption by making a BIGGER one: the sentence
    ``"Value-faithful to the NumPy einsum, and bit-exact."`` contains
    ``exact`` as a substring, so the gate passed it — while it asserts
    BIT-IDENTITY to an oracle this package cannot run by policy, which is
    strictly more than the clause the gate exists to police. An exemption must
    be a BOUND (``to round-off``, ``~1 ULP``, ``accurate to ...``) or a
    RETRACTION; a stronger unrunnable assertion is neither.
    ``test_layer4_a_stronger_claim_cannot_buy_exemption`` is the witness, and
    it is why this predicate is a named function rather than an inline
    comprehension: a gate's own escape hatch needs a test that can reach it.
    """
    low = sentence.lower()
    return any(v in low for v in _R3_VOCABULARY + _RETRACTION)


def test_layer4_every_numpy_faithfulness_claim_is_qualified() -> None:
    """STRICT ZERO on an unqualified appeal to an unrunnable oracle.

    Measured at rc462: four such claims shipped, and ``einsum``'s was
    unqualified — reaching users through ``describe()``, the MCP tool list and
    the compiled-in C registry, on four generated surfaces at once, while the op
    it described silently rounded every exact operand it was handed.
    """
    bad = [(n, s) for n, s in _numpy_faithfulness_claims()
           if not _claim_is_qualified(s)]
    assert bad == [], (
        "unqualified 'value-faithful to NumPy' claims: "
        + "; ".join(f"{n}: {s!r}" for n, s in bad)
        + ". numpy is absent BY POLICY, so this clause appeals to an oracle "
          "the package cannot run. Bound it in the same sentence or retire it.")


def test_layer4_a_stronger_claim_cannot_buy_exemption() -> None:
    """The planted defect for Layer 4's OWN exemption list.

    Through the first rc463 build the list held the bare token ``"exact"``, so
    the first string below — a claim STRONGER than the one being policed, and
    unrunnable for the same reason — exempted itself. The gate is only a gate
    if the escape hatch is smaller than the claim.
    """
    assert not _claim_is_qualified(
        "Value-faithful to the NumPy einsum, and bit-exact."), (
        "a STRONGER unrunnable claim bought exemption from the claim gate; "
        "the exemption vocabulary has drifted back to accepting the bare "
        "token 'exact'")
    assert not _claim_is_qualified(
        "Value-faithful to the NumPy einsum on the exact-ℚ carrier."), (
        "naming a CARRIER is not an accuracy BOUND on the claim")
    # and the two legitimate halves still exempt.
    assert _claim_is_qualified(
        "Value-faithful to the NumPy einsum, to round-off.")
    assert _claim_is_qualified(
        "value-faithfulness to the NumPy einsum; that clause is RETIRED.")


def test_layer4_is_not_vacuous() -> None:
    """The claim gate must actually be reading claims."""
    claims = _numpy_faithfulness_claims()
    assert len(claims) >= 2, (
        f"only {len(claims)} NumPy-faithfulness claims found in the live "
        f"registry; if they were all retired, say so and delete this gate "
        f"rather than leaving it green over an empty set")


# ── the einsum-specific regression, pinned by name ────────────────────────────
def test_the_transpose_that_changed_the_value() -> None:
    """THE witness for the whole class, kept as its own named test.

    ``einsum("ij->ji", [[2**53+1]])`` performs NO ARITHMETIC — it is a pure
    index permutation — and through rc462 it returned a different number than it
    was given. That is the cleanest possible demonstration that the defect is
    the CARRIER, not the algorithm, and it is a witness no arithmetic-shaped
    test would ever have thought to write. Three tests in this tree called
    ``einsum``; all three drew their operands from ``random.gauss(0, 1)``, and
    the largest integer significand in any einsum fixture in the tree was ZERO.
    """
    got = _mc.einsum("ij->ji", [[P]])
    assert isinstance(got, QMat), (
        f"exact operands must return the exact carrier; got {type(got).__name__}")
    assert _eq_exact(got[0, 0], P), f"a transpose changed the value: {got[0, 0]!r}"
    # and the float rung is untouched: a float operand still returns Mat.
    from srmech.math.mat import Mat
    assert isinstance(_mc.einsum("ij->ji", [[1.5]]), Mat)


def test_an_integer_einsum_fixture_now_exists() -> None:
    """The absence this gate exists to end.

    Adding an integer fixture ALONE would still not have caught the defect —
    both hand-written einsum oracles in the tree seed ``total = 0j`` and
    multiply through ``complex(...)``, so the oracle would have rounded
    identically and both sides would have agreed on the wrong value. The fixture
    AND an exact oracle are needed; ``_eq_exact`` is the exact oracle.
    """
    assert significand_bits(P) == 54
    assert _eq_exact(_mc.einsum("i,i->", [3], [3002399751580331]), Q(P, 1))
