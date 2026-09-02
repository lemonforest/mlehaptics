"""rc463 (`#T1188`) — the SILENT-CARRIER-DEMOTION ratchet.

THE CLASS PREDICATE, stated once, here, as the gate's own definition:

    An op is a **silent carrier demotion** when it accepts an exact operand
    through its own declared entry, routes it through a float carrier so a
    derived quantity's significand is truncated to 53 bits, returns the rounded
    value with no exception/warning/status, publishes **no accuracy declaration
    a caller could read before calling**, and a carrier that would have computed
    the same quantity exactly already ships.

Five conjuncts: ADMISSION (decided by the SIGNATURE, not by what Python happens
to accept) ∘ DEMOTION ∘ SILENCE ∘ NO-R3-DECLARATION ∘ EXACT-PEER-SHIPS.

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

 1. **A missing MANIFEST row is invisible.** The gate asserts over the rows it
    HAS. It has no oracle telling it a row is absent, so every registered tool
    not enumerated below is outside it, silently. That is the same shape as a
    checker verifying one side of a relation.
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
    ``_declaration_hits``'s one-level delegation follow, which exists because
    ``matrix_cascades.svd`` is documented at its delegate); a keyword in an
    unrelated sentence reads as declared (a false negative). Do NOT "simplify"
    the delegation follow — it was added because running the gate without it
    red-flagged a correctly-documented op.
 6. **Bit / byte carriers are structurally OUT OF REACH.** 57 ``hdc`` tools and
    the byte-domain DSP codecs admit no 53-bit-significand witness BY
    CONSTRUCTION (``bundle(vectors: Sequence[bytes]) -> bytes``;
    ``rle`` refuses a 54-bit symbol outright). Their absence from the manifest
    is a DOMAIN fact — but the gate cannot distinguish "no witness
    constructible" from "nobody wrote one", and it does not pretend to.
 7. **It cannot see the ``preserves`` field**, because that field is empty
    ``()`` on every op in this family INCLUDING exact ``kron``. A gate leaning
    on it would be vacuous.

numpy-free. No ``abs()`` — ``significand_bits`` uses a Class-K pin-slot branch.
No stdlib ``fractions``.
"""

import inspect

import pytest

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


# ── LAYER 2 — the down-only CEIL over the pre-existing residual ───────────────
#: Ops that still route an exact operand through a float carrier. **DOWN ONLY.**
#: Seeded at the rc463 measured value. Fixing an op must LOWER this number;
#: nothing may raise it. Every row here is ALSO required to pass Layer 3 — a
#: demotion that declares nothing is a strict-zero violation, not a legal row.
#:
#: rc463: 6. All six are ``srmech.math.laplacian`` carrier / builder ops. The
#: rc462 census counted TEN; four left the class in this rc — ``einsum`` and
#: ``separate_frame_curvature`` were FIXED (they now return exact carriers on
#: exact operands), and ``signal_processing.fir`` / ``matched_filter`` were
#: **never in it**: re-measured here, both return the exact Python ``int``
#: ``9007199254740993`` on the census's own witness, so those two rows were a
#: mis-measurement and are recorded as such rather than quietly dropped.
CEIL_SILENT_DEMOTION = 6

#: (label, callable, exact_oracle, the op object Layer 3 reads)
_DEMOTION_MANIFEST = [
    ("laplacian.mat_dot",
     lambda: _la.mat_dot([3], [3002399751580331]), P, "mat_dot"),
    ("laplacian.mat_outer",
     lambda: _first_leaf(_la.mat_outer([3], [3002399751580331])), P, "mat_outer"),
    ("laplacian.mat_matvec",
     lambda: _first_leaf(_la.mat_matvec([[3]], [3002399751580331])), P,
     "mat_matvec"),
    ("laplacian.dense_adjacency[default float rung]",
     lambda: _la.dense_adjacency(2, [(0, 1)], [P])[0][1], P, "dense_adjacency"),
    ("laplacian.dense_laplacian[default float rung]",
     lambda: _la.dense_laplacian(2, [(0, 1)], [P])[0][0], P, "dense_laplacian"),
    ("laplacian.signed_laplacian[default float rung]",
     lambda: _la.signed_laplacian(2, [(0, 1)], [P])[0][0], P, "signed_laplacian"),
]


def _measured_demoters():
    """The manifest rows that ACTUALLY demote right now, re-measured."""
    out = []
    for label, call, want, opname in _DEMOTION_MANIFEST:
        assert _discriminating(want), f"Layer-0 rejected the witness for {label}"
        if not _eq_exact(call(), want):
            out.append((label, opname))
    return out


def test_layer2_demotion_ceiling_is_down_only() -> None:
    """The residual DRAINS; it never grows.

    This is what lets an rc ship one carrier fix without being blocked by every
    op that has not been fixed yet — and what stops a new op joining the class
    unnoticed even if it is honestly documented.
    """
    live = _measured_demoters()
    assert len(live) <= CEIL_SILENT_DEMOTION, (
        f"{len(live)} silent carrier demotions, ceiling is "
        f"{CEIL_SILENT_DEMOTION}. New: {[n for n, _ in live]}. This ratchet is "
        f"DOWN-ONLY — fix the carrier, do not raise the ceiling.")
    if len(live) < CEIL_SILENT_DEMOTION:
        pytest.fail(
            f"GOOD NEWS, ACTION REQUIRED: only {len(live)} of "
            f"{CEIL_SILENT_DEMOTION} manifest rows still demote "
            f"({[n for n, _ in live]}). Lower CEIL_SILENT_DEMOTION to "
            f"{len(live)} in the SAME change, so the drain is recorded.")


def test_layer2_the_manifest_is_not_empty() -> None:
    """A CEIL over an empty manifest would be a green that measures nothing."""
    assert len(_DEMOTION_MANIFEST) == CEIL_SILENT_DEMOTION


# ── LAYER 3 — the HONESTY gate (the clause rc344's audit did not have) ────────
#: R3 vocabulary. A closed keyword list — see blind spot 5 in the module
#: docstring. Do NOT simplify it.
_R3_VOCABULARY = (
    "ulp", "to round-off", "round-off", "tolerance", "float64", "approximate",
    "terminal float lift", "accurate to", "~1e-",
)


def _declaration_hits(fn):
    """Every R3 marker reachable from ``fn``'s own contract surface.

    Reads the docstring, the signature (an ``exact=`` opt-in IS an R3
    declaration), and — one level deep — the docstring of a delegate the body
    names. ⚠️ **The delegation follow is not optional.**
    ``matrix_cascades.svd`` reads UNDECLARED at the wrapper while its delegate
    ``laplacian.mat_svd`` carries a full accuracy contract; without this the
    gate red-flags a correctly-documented op. Found by running the gate, not by
    reasoning about it.
    """
    doc = (inspect.getdoc(fn) or "").lower()
    hits = [d for d in _R3_VOCABULARY if d in doc]
    try:
        if "exact" in inspect.signature(fn).parameters:
            hits.append("exact= opt-in")
    except (TypeError, ValueError):
        pass
    if not hits:
        code = getattr(fn, "__code__", None)
        for name in (code.co_names if code is not None else ()):
            delegate = getattr(_la, name, None)
            if delegate is None or delegate is fn or not callable(delegate):
                continue
            ddoc = (inspect.getdoc(delegate) or "").lower()
            hits += [f"{d} (via {name})" for d in _R3_VOCABULARY if d in ddoc]
            if hits:
                break
    return hits


@pytest.mark.parametrize("label,opname",
                         [(r[0], r[3]) for r in _DEMOTION_MANIFEST],
                         ids=[r[0] for r in _DEMOTION_MANIFEST])
def test_layer3_every_demoter_declares_that_it_demotes(label, opname) -> None:
    """STRICT ZERO. An op that demotes must SAY SO before it is called.

    This is the layer that makes "fixed" and "honestly declared" both acceptable
    outcomes, and it is precisely the question rc344 did not ask.
    """
    fn = getattr(_la, opname)
    hits = _declaration_hits(fn)
    assert hits, (
        f"{label} routes an exact operand through a float carrier and publishes "
        f"NO accuracy declaration. A return-TYPE statement ('returns a Mat') is "
        f"rung R1 and is NOT sufficient — it names the container, not the value. "
        f"Either fix the carrier or add an R3 declaration (an accuracy phrase, "
        f"or an exact= opt-in).")


def test_layer3_can_return_otherwise() -> None:
    """NON-VACUITY, executable in CI, with no repo mutation committed.

    A gate that cannot go red is not a measurement. Rather than describing a
    mutation, this plants one in-process: a function that demotes exactly as the
    real ones do, and whose docstring makes only an R1 (return-type) claim.
    Layer 3 must reject it. If this ever passes, ``_declaration_hits`` has
    become permissive and the whole layer is decorative.
    """
    def r1_only(a, b):
        """Returns a float."""            # R1: the container, not the value.
        return float(a) * float(b)

    def r3_declared(a, b):
        """Returns a float, accurate to round-off (~1 ULP)."""
        return float(a) * float(b)

    assert not _eq_exact(r1_only(3, 3002399751580331), P), (
        "the planted demoter stopped demoting — the mutation is no longer a "
        "witness and this non-vacuity proof is vacuous")
    assert _declaration_hits(r1_only) == [], (
        "Layer 3 accepted an R1-only contract; the ladder has collapsed and "
        "the gate would now pass the exact defect rc344 shipped")
    assert _declaration_hits(r3_declared), (
        "Layer 3 rejected a genuine R3 declaration — it is now a false-positive "
        "machine, which is how a gate gets narrowed away")


def test_layer3_does_not_false_positive_on_a_delegating_wrapper() -> None:
    """The delegation follow, pinned. ``matrix_cascades.svd`` is documented at
    its delegate ``laplacian.mat_svd``; a Layer-3 that did not follow one level
    would call a correctly-documented op undeclared."""
    for fn in (_la.mat_norm, _la.mat_svd, _la.jacobi_eigvals,
               _composites.compensated_sum, _mc.lstsq):
        assert _declaration_hits(fn), (
            f"{fn.__name__} carries a real accuracy contract but Layer 3 read "
            f"it as undeclared")


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
