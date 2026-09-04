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
    under the second of those two numbers — :data:`CEIL_DEMOTION_UNREACHED` —
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
    red-flagged a correctly-documented op.

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

numpy-free. No ``abs()`` — ``significand_bits`` uses a Class-K pin-slot branch.
No stdlib ``fractions``.
"""

import inspect
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


# ── LAYERS 2 & 3 — the AUTO-POPULATED census, and the honesty gate over it ────
# rc465 (`#T1188`) — WHAT CHANGED, AND WHY IT HAD TO.
#
# Through rc464 this section was ``_DEMOTION_MANIFEST``: SIX hand-written rows,
# all six in ``srmech.math.laplacian``, with ``CEIL_SILENT_DEMOTION = 6`` pinned
# to ``len(_DEMOTION_MANIFEST)`` so the ceiling could not move without a human
# editing the list. Blind spot 1 above named the hole in as many words — *"a
# missing MANIFEST row is invisible"* — and the ADMISSION conjunct made it
# worse than that: membership was decided **by the SIGNATURE**, so an op
# declaring ``Sequence[float]`` was excluded BY CONSTRUCTION however exact the
# operand it was actually handed. That is R2 shielding, on the rung this file's
# own ladder rates "WEAK … nothing enforces it". A type annotation was standing
# in for an accuracy contract, and the gate was reading the annotation.
#
# The population is now MEASURED by ``tools/demotion_probe.py`` over every
# sequence-shaped REGISTRY parameter — one instrument, two consumers, the
# ``frame_probe`` discipline. What it found on the rc464 surface:
#
#     rows probed                   703   (over 427 ops)
#     DEMOTED                       127   (over 101 ops)
#       of which UNDECLARED          77   (over  64 ops)   <- rc463 knew 6
#
# Six was not a residual. It was a sample.
#
# ⚠️ **THE CEILING BELOW IS NEW DEBT, AND IT IS NOT A RETREAT TO A COUNTER.**
# rc463's six rows were all DECLARED — they passed Layer 3 — so its strict-zero
# on undeclared demotion was true of the rows it had. rc465 cannot fix or
# declare 57 ops in one release, so the residual is bounded two ways at once,
# and the roster is the stronger of the two:
#
#   * ``_undeclared_keys`` is pinned as an EQUALITY against the committed
#     census. A new undeclared demoter is RED even if another drained in the
#     same rc, so the ceiling cannot be paid for with unrelated progress —
#     which is exactly the failure mode a bare count has.
#   * ``CEIL_UNDECLARED_DEMOTION`` is the visible down-only integer, and it
#     drains: an rc that fixes an op must LOWER it in the same change.
#
# THE DRAIN PATH, PER FAMILY, measured (rows, post-fix):
#
#   21  srmech.signal_processing     the DSP float pipeline. Drain = a declared
#                                    accuracy sentence per op; these are
#                                    genuinely float-carrier ops and the honest
#                                    outcome is R3, not an exact route.
#   17  srmech.math.laplacian        the dense float carrier. Six ops already
#                                    declare (they are the rc463 manifest); the
#                                    rest drain the same way, and several have
#                                    an ``exact=`` peer already shipping.
#   16  srmech.math.hdc              the loop family. Drain = an R3 sentence
#                                    naming the exact peers ``cascade.cd_mult``
#                                    / ``cd_conjugate``, which ship.
#    9  srmech.cascade               the couple/uncouple + qdft summand family.
#                                    ``cd_uncouple_working`` already declares;
#                                    its siblings copy that sentence.
#    7  the singles (biology.coupling, cascade.coupled, physics.qm.bell,
#       pseudo_hermitian, quaternion_log, relativistic, single_particle)
#
# What rc465 DID drain, by fixing the carrier rather than declaring it: the
# nine R2-shielded ops of ``qm.octonion`` / ``qm.quaternion`` / ``qm.triality``
# (77 -> 70 rows, 64 -> 57 ops). They are held at STRICT ZERO below and can
# never re-enter the roster.

import demotion_probe as _dp   # tools/ is on sys.path via the header import

#: Down-only. The number of (op, parameter) rows that ROUND an exact operand
#: and publish no R3 accuracy declaration. Seeded at the rc465 post-fix
#: measurement. **Fixing or declaring an op must LOWER this in the same
#: change**; nothing may raise it.
CEIL_UNDECLARED_DEMOTION = 70

#: Down-only. ``NO_SHAPE`` rows — parameters the probe could not build ANY
#: candidate binding for, so no carrier verdict was ever reachable. This is the
#: constant ``tools/demotion_probe.py``'s required-disclosure bullet 1 names as
#: "the honest statement of the instrument's reach ... what
#: ``CEIL_DEMOTION_UNREACHED`` ratchets down", and through rc465 it existed
#: ONLY in that sentence: repo-wide grep found exactly one occurrence, the
#: disclosure itself. Defined and asserted here (rc465-fix, `#T1188`).
#: Lowering it needs nothing; raising it means the probe reaches LESS than it
#: did, which is a regression in the instrument and needs saying out loud.
CEIL_DEMOTION_UNREACHED = 52

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

_LIVE_CACHE = {}


def _live_census():
    """The live census, run ONCE per session (it is a ~5 minute measurement)."""
    if "rows" not in _LIVE_CACHE:
        _LIVE_CACHE["rows"] = _dp.census()
    return _LIVE_CACHE["rows"]


def _key(row):
    return f"{row['op']}::{row['param']}"


def _undeclared_keys(rows):
    return frozenset(_key(r) for r in _dp.undeclared(rows))


def test_layer2_the_committed_census_matches_the_live_one() -> None:
    """The artefact cannot go stale while the gate stays green.

    This is the lesson rc465's D2 half paid for elsewhere in the same release:
    ``tools/frame_probe.py`` promised that its gate and its census "cannot
    drift apart by being separately hand-rolled", and they drifted anyway —
    by the census simply never being re-run while the ceiling moved nine times.
    A shared import is not enough; the committed measurement has to be
    COMPARED.
    """
    meta, _ = _dp.load_census()
    live = _dp.by_verdict(_live_census())
    assert meta["by_verdict"] == live, (
        "tests/demotion_census_rc465.ndjson is stale — regenerate with "
        "`python3 tools/demotion_probe.py` and commit it in the same change.\n"
        f"  committed: {meta['by_verdict']}\n  live:      {live}")


def test_layer2_the_probe_refinds_the_rc463_hand_written_six() -> None:
    """POSITIVE CONTROL. An auto-populating instrument that misses what a human
    already found by reading the code is not an upgrade on the human."""
    rows = {(_key(r)): r for r in _live_census()}
    for op, param in _RC463_SIX:
        r = rows.get(f"{op}::{param}")
        assert r is not None, f"the probe did not reach {op}.{param} at all"
        assert r["verdict"] == "DEMOTED", (
            f"{op}.{param} was a hand-verified rc463 demoter and the probe now "
            f"reads {r['verdict']} — the ORACLE moved, not the op")
        assert r.get("declares"), (
            f"{op}.{param} lost its R3 declaration; rc463 required all six to "
            f"carry one")


def test_layer2_the_population_is_not_a_sample() -> None:
    """NON-VACUITY, in the direction this gate actually failed in.

    rc463's ceiling was ``len(_DEMOTION_MANIFEST)``, so it was green over
    whatever list happened to be there. These floors are what stop the
    replacement quietly shrinking back into a sample.
    """
    rows = _live_census()
    assert len(rows) >= 600, f"only {len(rows)} rows probed"
    assert len({r["op"] for r in rows}) >= 400
    decided = [r for r in rows if r["verdict"] in ("DEMOTED", "EXACT")]
    assert len(decided) >= 180, (
        f"only {len(decided)} rows reached a carrier verdict; the probe has "
        f"narrowed and the roster below is measuring less than it says")
    assert len(_dp.demoters(rows)) > len(_dp.undeclared(rows)), (
        "every measured demoter is undeclared — either Layer 3's vocabulary "
        "stopped matching anything, or the delegate follow broke")


def test_layer3_the_undeclared_roster_is_exactly_what_is_committed() -> None:
    """STRICT IDENTITY over the residual — the half a count cannot do.

    A bare ``<= CEIL`` lets a NEW undeclared demoter in whenever an unrelated
    one drains in the same change. The roster forbids that: membership is
    pinned, so an addition is red even at a lower count.
    """
    _, committed = _dp.load_census()
    want = _undeclared_keys(committed)
    got = _undeclared_keys(_live_census())
    new = sorted(got - want)
    gone = sorted(want - got)
    assert not new, (
        f"{len(new)} NEW undeclared carrier demotion(s): {new}. Fix the carrier "
        f"(an exact peer ships for most of this surface) or publish an R3 "
        f"accuracy statement — do not add the row to the census and move on.")
    assert not gone, (
        f"GOOD NEWS, ACTION REQUIRED: {len(gone)} row(s) left the undeclared "
        f"class ({gone}). Regenerate tests/demotion_census_rc465.ndjson and "
        f"LOWER CEIL_UNDECLARED_DEMOTION to {len(got)} in the SAME change, so "
        f"the drain is recorded rather than absorbed.")


def test_layer2_the_unreached_population_is_ratcheted_down_only() -> None:
    """The probe's REACH, as a ratchet rather than as a sentence.

    ``NO_SHAPE`` is the honest count of parameters the instrument could not
    address at all. It is bounded here so the population cannot grow while the
    gate stays green — the failure mode a coverage number carried only in prose
    has no defence against.
    """
    rows = _live_census()
    unreached = [r for r in rows if r["verdict"] == "NO_SHAPE"]
    assert len(unreached) <= CEIL_DEMOTION_UNREACHED, (
        f"{len(unreached)} rows are NO_SHAPE (the probe could build no binding "
        f"at all), ceiling is {CEIL_DEMOTION_UNREACHED}. This ratchet is "
        f"DOWN-ONLY: the instrument reaching LESS than it did is a regression "
        f"in the instrument. Widen `synthesize` rather than the ceiling; each "
        f"row carries its own `reason`.")
    if len(unreached) < CEIL_DEMOTION_UNREACHED:
        pytest.fail(
            f"GOOD NEWS, ACTION REQUIRED: only {len(unreached)} of "
            f"{CEIL_DEMOTION_UNREACHED} rows are unreachable. Lower "
            f"CEIL_DEMOTION_UNREACHED to {len(unreached)} in the SAME change.")


def test_layer3_the_undeclared_ceiling_is_down_only() -> None:
    """The visible ratchet. Down only; a raise is not a legal edit."""
    live = _dp.undeclared(_live_census())
    assert len(live) <= CEIL_UNDECLARED_DEMOTION, (
        f"{len(live)} undeclared carrier demotions, ceiling is "
        f"{CEIL_UNDECLARED_DEMOTION}. This ratchet is DOWN-ONLY.")
    if len(live) < CEIL_UNDECLARED_DEMOTION:
        pytest.fail(
            f"GOOD NEWS, ACTION REQUIRED: only {len(live)} of "
            f"{CEIL_UNDECLARED_DEMOTION}. Lower CEIL_UNDECLARED_DEMOTION to "
            f"{len(live)} in the SAME change.")


@pytest.mark.parametrize("op", sorted(_FIXED_IN_RC465))
def test_layer3_the_rc465_fixed_family_is_strict_zero(op) -> None:
    """The nine R2-shielded ops rc465 repaired can never re-enter the roster.

    They are not under the ceiling and never will be: each carries an exact
    operand on an exact carrier end to end, with float as the caller's own
    explicit request. A row here is a REGRESSION.
    """
    bad = [_key(r) for r in _dp.undeclared(_live_census()) if r["op"] == op]
    assert not bad, (
        f"{op} is demoting again with no accuracy declaration: {bad}. rc465 "
        f"gave it an exact carrier; see tests/test_octonion_exact_carrier_rc465.py")


def test_layer3_the_probe_can_return_both_verdicts() -> None:
    """NON-VACUITY of the ORACLE itself, planted in-process, nothing committed.

    An instrument that cannot say DEMOTED is decorative; one that cannot say
    EXACT flags the whole registry and gets switched off. Both directions are
    exercised here on functions written for the purpose, so the proof does not
    depend on any shipped op keeping its current carrier.
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
