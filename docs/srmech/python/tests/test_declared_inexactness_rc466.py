"""rc466 (`#T1188`) — the SEVENTY-ROW drain: the DECLARE half, gated.

WHAT THIS FILE IS
=================
``tests/test_exact_carrier_drain_rc466.py`` holds the FIX half of the drain.
This file holds the DECLARE half: the twelve ops the rc466 plan judged
float-by-nature (FBN) or exact-object-without-a-shipped-op (NPO), each given a
TRUE accuracy sentence on its OWN docstring. (Seventeen at Stage 2: the five
eigen-family ops — ``hermitian_`` / ``symmetric_eigendecompose``,
``three_fold_eigvec_groups``, ``fiedler_vector``, ``klein4_relational_structure``
— were moved to the FIX half at the rc466 review, which found Stage 2's reason
for declaring them, "two algorithms of different cost class wearing one name",
contradicted by ``jacobi_eigvals(exact=True)`` in the same module; they now
carry an ``exact=`` route through ``eig_exact`` and executed rows in
``tests/test_exact_carrier_drain_rc466.py``.) The judgement was per op and the
kind is recorded per op below, because the failure mode this stage guards
against is *declaring an op that could have been fixed* — converting a defect
into documentation. An NPO row therefore names the exact object AND the
missing op (its drain path); an FBN row names the transcendental / iterative /
π-un-cancelled quantity that makes an exact carrier impossible.

THE RULES THE DECLARATIONS OBEY (and this file executes)
========================================================
D1  **The sentence is on the op's OWN docstring** and carries at least one
    verbatim token of ``tools/demotion_probe.py``'s ``R3_VOCABULARY``. The
    probe's one-level delegate follow is not relied on: the op's own docstring
    is what ``inspect.getdoc`` / ``help()`` and the probe's
    ``declaration_hits`` read. (Corrected TWICE. rc466: this line said
    ``describe()`` and the MCP tool list emit the op's own text — the MCP tool
    list emits its FIRST paragraph only, ``tools/gen_tool_docs.py``'s
    ``_clean_doc``, so the accuracy paragraph does not reach the wire.
    rc467 (`#T1188`): naming ``describe()`` there at all was wrong — MEASURED,
    it returns 27,350 bytes of COUNTS, carrying no op name, no summary, no
    docstring and no digest of any kind. Emitting the accuracy paragraphs on
    the wire remains a named residual.)
D2  **No DECLARE op grew an ``exact=`` keyword.** The R3 reader counts
    ``exact= opt-in`` as a declaration by its mere presence, so a keyword
    without an executed route would drain a census row for free (rule F1 of
    the FIX half, read backwards).
D3  **Every sentence's factual claims are EXECUTED here** — the entry
    projection witness, the ``P == F`` collapse each sentence quotes, the
    ``G != F`` sensitivity that makes the collapse a demotion rather than a
    flat function, and the two code changes tied to DECLARE ops (the Class-K
    integral-offset branch in ``sinc_interp._sinc`` and the entry-projection
    removals in ``cross_spectral`` / ``wiener`` / ``spectral_subtraction`` /
    ``multitaper``).
D4  **Two instrument blind spots measured this stage are pinned as FACTS**, not
    fixed: scalar registry parameters are never probed (``rational.sin`` rounds
    a ``Q`` argument and the probe emits no row), and the keyword reader cannot
    read negation (*"not a tolerance"* counts as a declaration). A test that
    pins a blind spot goes RED the day the instrument learns — which is the
    day the disclosure must be rewritten, not the day the test is deleted.

THE ONE REFUSAL MADE CARRIER-INDEPENDENT ON THE WAY
====================================================
Writing the ``recover_check`` sentence meant measuring the native/pure
divergence the census pins for its ``::charges`` rows. It was not what the
plan recorded ("the pure cell refuses, the native peer returns a value"):
BOTH cells refused a ``|x| >= 2**55`` phase, with DIFFERENT exception texts —
the native scalar peer's did not name the argument, the pure cascade's did —
and the array kernel ``srmech_elementwise_transcendental`` returned ``0.0``
for such an element with its status discarded. ``rational.cos`` / ``sin`` now
refuse at one bound (:data:`srmech.math.rational.Q61_TRIG_RANGE`) with one
text BEFORE dispatch, and ``elementwise_transcendental`` guards the array
kernel at the dispatch boundary; the C kernel's status discard is named as a
C follow-up. Both are executed below in the cell this process runs in.

numpy-free. No ``abs()`` — every magnitude is a Class-K pin-slot branch.
"""

from __future__ import annotations

import inspect
import sys
from pathlib import Path

import pytest

_TOOLS = Path(__file__).resolve().parents[1] / "tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

import demotion_probe as _dp  # noqa: E402  (tools/ is on sys.path just above)

from srmech._resolve import resolve_dotted_callable  # noqa: E402
from srmech.math.q import Q  # noqa: E402

#: ``2**53 + 1`` — the smallest positive integer float64 cannot represent — and
#: its two neighbours: the float carrier collapses P onto F and keeps G apart.
P = 2 ** 53 + 1
F = 2 ** 53
G = 2 ** 53 + 2

#: The DECLARE ledger: ``op -> (kind, drain path or None)``. FBN = float by
#: nature; NPO = the exact object is representable in a shipped carrier but no
#: shipped op computes this composite — the drain path names the missing op.
_DECLARED_IN_RC466 = {
    # ── signal_processing ────────────────────────────────────────────────
    "srmech.signal_processing.spectrogram": (
        "NPO", "the ring norm X_k·conj(X_k) of an exact_dft bin (an element of "
               "Z[zeta_N]^+) / an STFT that returns exact frames"),
    "srmech.signal_processing.cross_spectral": ("FBN", None),   # Hann + float average
    "srmech.signal_processing.multitaper": ("FBN", None),       # irrational tapers
    "srmech.signal_processing.wiener": ("FBN", None),           # |X|², eps-floor, S/(S+N)
    "srmech.signal_processing.spectral_subtraction": ("FBN", None),  # sqrt/atan2/cos/sin
    "srmech.signal_processing.sinc_interp": ("FBN", None),      # π un-cancelled
    "srmech.signal_processing.jpeg": (
        "NPO", "an ORDERED exact real carrier for the round-half-even quantiser: "
               "Sturm-style isolating intervals on a real embedding of Q(zeta_32)^+"),
    # ── math.laplacian ───────────────────────────────────────────────────
    # (the five eigen-family entries that stood here at Stage 2 are FIXED
    # since the rc466 review — see the module docstring)
    "srmech.math.laplacian.fiedler_sparse": ("FBN", None),             # power iteration
    "srmech.math.laplacian.elementwise_transcendental": ("FBN", None), # transcendental
    "srmech.math.laplacian.recover_check": ("FBN", None),              # threshold verdict
    "srmech.math.laplacian.recover_check_spectral": ("FBN", None),
    # ── cascade ──────────────────────────────────────────────────────────
    "srmech.cascade.kuramoto_sin_term": ("FBN", None),                 # the DIFFERENCE is float64 (exact first since the review fix)
}


def _own_tokens(fn) -> list:
    doc = (inspect.getdoc(fn) or "").lower()
    return [d for d in _dp.R3_VOCABULARY if d in doc]


# ── D1 / D2: the declaration is on the op, and it is a sentence, not a keyword ─
@pytest.mark.parametrize("name", sorted(_DECLARED_IN_RC466))
def test_the_declaration_is_on_the_ops_own_docstring(name) -> None:
    fn = resolve_dotted_callable(name)
    own = _own_tokens(fn)
    assert own, (
        f"{name}: no R3 token in the op's OWN docstring — the probe's delegate "
        f"follow may still read it as declared, but describe() emits this text")
    assert "accuracy (rc466" in (inspect.getdoc(fn) or "").lower(), (
        f"{name}: the rc466 accuracy paragraph is missing from the op docstring")
    hits = _dp.declaration_hits(fn)
    assert hits and not hits[0].endswith(")"), (
        f"{name}: the probe's first hit {hits[:1]} is a delegate hit, not the "
        f"op's own — D1 requires the op's own contract surface")


@pytest.mark.parametrize("name", sorted(_DECLARED_IN_RC466))
def test_no_declared_op_gained_an_exact_keyword(name) -> None:
    fn = resolve_dotted_callable(name)
    assert "exact" not in inspect.signature(fn).parameters, (
        f"{name}: an exact= keyword drains a census row by its mere presence "
        f"(R3 reader: 'exact= opt-in'); a DECLARE op must not carry one")
    assert "exact= opt-in" not in _dp.declaration_hits(fn)


def test_every_npo_row_names_its_drain_path() -> None:
    for name, (kind, path) in _DECLARED_IN_RC466.items():
        assert kind in ("FBN", "NPO"), name
        if kind == "NPO":
            assert path and len(path) > 40, (
                f"{name}: an NPO declaration without a named drain path is a "
                f"float-by-nature claim in disguise")
        else:
            assert path is None, name


def test_the_declared_family_is_registered_and_disjoint_from_the_fix_set() -> None:
    from srmech.introspect.tool_schema import get_tool_schema
    names = {e.name for e in get_tool_schema().tools}
    missing = sorted(set(_DECLARED_IN_RC466) - names)
    assert not missing, f"DECLARE ledger names ops the registry does not: {missing}"
    import test_silent_carrier_demotion_rc463 as gate  # noqa: F401  (tests/ dir)
    overlap = set(_DECLARED_IN_RC466) & set(gate._FIXED_IN_RC466)
    assert overlap == {"srmech.signal_processing.stft"} or not overlap, (
        f"an op cannot be both FIXED and DECLARED in one rc: {sorted(overlap)}")


# ── D3: the sentences' claims, executed ───────────────────────────────────────
def test_spectrogram_squares_the_terminal_lift() -> None:
    from srmech.signal_processing.closed_form_ops import spectrogram
    op = spectrogram.op
    win = [1] * 4
    assert op([P, 0, 0, 0], frame_size=4, window=win) == op([F, 0, 0, 0], frame_size=4, window=win)
    assert op([G, 0, 0, 0], frame_size=4, window=win) != op([F, 0, 0, 0], frame_size=4, window=win)


def test_cross_spectral_reads_the_record_as_given_and_lifts_before_the_product() -> None:
    from srmech.signal_processing.closed_form_ops import cross_spectral
    op = cross_spectral.op
    a = op([P, 0, 0], [1, 0, 0], frame_size=4)
    assert a == op([F, 0, 0], [1, 0, 0], frame_size=4), "the cross-product is float"
    assert a != op([G, 0, 0], [1, 0, 0], frame_size=4)
    assert isinstance(a[1][0], complex)
    # the windowed (Welch) path accepts an integer record without an entry cast
    freqs, csd = op(list(range(1, 11)), [1, 0] * 5, frame_size=4)
    assert len(freqs) == len(csd) == 4


def test_multitaper_entry_projection_removal_changes_nothing() -> None:
    from srmech.signal_processing.closed_form_ops import multitaper
    sig = [P, 1, 2, 3, 4, 5, 6, 7]
    assert multitaper.op(sig) == multitaper.op([float(v) for v in sig]), (
        "the first operation on every sample is a multiply by an irrational "
        "taper, so an int signal and its float64 projection must agree byte-for-byte")


def test_wiener_and_spectral_subtraction_forward_transforms_are_exact_until_rotation() -> None:
    from srmech.signal_processing.closed_form_ops import wiener, spectral_subtraction
    for mod in (wiener, spectral_subtraction):
        out_p = mod.op([P] + [1] * 7, [0.0] * 8)
        out_f = mod.op([F] + [1] * 7, [0.0] * 8)
        assert out_p != out_f, (
            f"{mod.OPERATION_NAME}: the signal is used as given since rc466 — the "
            f"exact-until-rotation transform must separate P from F")
        assert all(isinstance(v, float) for v in out_p)


def test_sinc_kernel_is_exact_at_integral_offsets_and_transcendental_elsewhere() -> None:
    from srmech.signal_processing.closed_form_ops import sinc_interp
    s = sinc_interp._sinc
    assert s(0.0) == 1.0
    assert s(1.0) == 0.0 and s(-3.0) == 0.0 and s(7) == 0.0, (
        "through rc465 _sinc(1.0) was 3.892866406999617e-17; the Class-K "
        "integral-offset branch returns exact 0.0")
    assert s(0.5) != 0.0 and s(0.5) == pytest.approx(0.6366197723675814, abs=1e-12)
    idx = [0.0, 1.0, 2.0, 3.0, 4.0]
    assert sinc_interp.op([0, 0, 1, 0, 0], idx, idx) == [0j, 0j, 1 + 0j, 0j, 0j], (
        "the module docstring's identity oracle is TRUE only since rc466")
    got = sinc_interp.op([P, 0, 1, 0, 0], idx, idx)
    assert got == [complex(P), 0j, 1 + 0j, 0j, 0j]
    assert got[0].real == float(F), "signal is projected to complex at the entry (declared)"


def test_jpeg_quantised_blocks_collapse_p_onto_f() -> None:
    from srmech.signal_processing.closed_form_ops import jpeg
    ramp = [[r * 8 + c for c in range(8)] for r in range(8)]
    with_p = [row[:] for row in ramp]
    with_p[0][0] = P
    with_f = [row[:] for row in ramp]
    with_f[0][0] = F
    assert jpeg.op(with_p) == jpeg.op(with_f)


def test_eigen_family_entry_projection_witness() -> None:
    """The DEFAULT route's sentence, still true after the review fix moved the
    five ops to the FIX half: the float Jacobi rounds the operand at the entry.
    The exact route's rows live in tests/test_exact_carrier_drain_rc466.py."""
    from srmech.math import laplacian as la
    assert float(la.hermitian_eigendecompose([[P, 0], [0, 0]])[0][1]) == float(F)
    assert float(la.symmetric_eigendecompose([[P, 0], [0, 0]])[0][1]) == float(F)
    assert float(la.symmetric_eigendecompose([[G, 0], [0, 0]])[0][1]) == float(G)
    # the in-contract diagonal witness is INSENSITIVE for the eigenvector ops
    assert list(la.fiedler_vector([[P, 0], [0, 1]])) == list(la.fiedler_vector([[G, 0], [0, 1]]))


def test_elementwise_transcendental_rounds_the_argument_before_the_cascade() -> None:
    from srmech.math import laplacian as la
    ct = la.elementwise_transcendental
    assert ct([P], "cos")[0] == ct([F], "cos")[0]
    assert ct([G], "cos")[0] != ct([F], "cos")[0]


def test_kuramoto_sin_term_forms_the_difference_exactly_then_rounds_it_once() -> None:
    """rc466 review fix: the exact difference first (one rounding, of the
    DIFFERENCE), so an exactly representable difference is the sine of that
    difference — through the Stage-3 head each phase was rounded separately and
    ``[2**53+1, 2**53+3]`` returned ``sin(4)``, the wrong SIGN for ``sin(2)``.
    What stays declared: the difference itself rounds past 53 bits."""
    from srmech.cascade.composites import kuramoto_sin_term, kuramoto_step
    from srmech.math import rational
    assert kuramoto_sin_term([P, P + 2], 0, 1) == rational.sin(2.0)
    assert kuramoto_sin_term([P, P + 2], 0, 1) != rational.sin(4.0)
    assert kuramoto_sin_term([P, 0], 0, 1) == kuramoto_sin_term([F, 0], 0, 1), (
        "the DIFFERENCE −(2**53+1) still rounds: that is the declared demotion")
    assert kuramoto_sin_term([G, 0], 0, 1) != kuramoto_sin_term([F, 0], 0, 1)
    assert isinstance(kuramoto_sin_term([P, 0], 0, 1), Q)
    # a float phase on either side keeps the rc420 float64 difference, byte for byte
    assert kuramoto_sin_term([0.5, 1.25], 0, 1) == rational.sin(1.25 - 0.5)
    assert kuramoto_sin_term([P, 1.0], 0, 1) == rational.sin(1.0 - float(P))
    # the reason the OUTPUT stays declared: rational.sin reads a Q as float64
    assert rational.sin(Q(P, 1)) == rational.sin(F)
    assert rational.sin(G) != rational.sin(F)
    # kuramoto_step coerces its phases to float BEFORE the term op, so its
    # projections cannot disagree on a wide phase (the C peer reads doubles)
    assert kuramoto_step([P, P + 2], [0, 0], coupling=1.0, dt=0.1) == \
        kuramoto_step([float(P), float(P + 2)], [0, 0], coupling=1.0, dt=0.1)


# ── the refusal made carrier-independent while writing the recover sentence ───
def test_q61_trig_range_refusal_is_one_text_in_this_cell() -> None:
    from srmech.math import laplacian as la, rational
    x = 5.659390201622752e+16                       # the census's ::charges phase
    assert rational.Q61_TRIG_RANGE == 2.0 ** 55
    assert la._Q61_TRIG_RANGE is rational.Q61_TRIG_RANGE, "one bound, imported"
    want = f"cos: |x| too large for the Q61 octant reduction; got {x}"
    with pytest.raises(ValueError, match="too large for the Q61 octant reduction") as e1:
        rational.cos(x)
    assert str(e1.value) == want, "the native branch used to raise a different text"
    with pytest.raises(ValueError) as e2:
        la.elementwise_transcendental([x], "cos")
    assert str(e2.value) == want, (
        "through rc465 the native array kernel returned 0.0 here, silently")
    with pytest.raises(ValueError, match="^cos: ") as e3:
        la.elementwise_transcendental([x], "exp_i")
    assert str(e3.value) == want
    with pytest.raises(ValueError, match="^sin: "):
        la.elementwise_transcendental([1.0, -x], "sin")
    # just inside the bound both projections still compute
    assert float(rational.cos(2.0 ** 55 - 4096)) == pytest.approx(-0.01972221735596597, abs=1e-15)
    assert la.elementwise_transcendental([2.0 ** 54 * 1.5], "cos")[0] == pytest.approx(
        0.9950331994381186, abs=1e-15)
    # and the recover faculty reports the ONE text through its diagnostics leaf
    r = la.recover_check(3, [(0, 1), (1, 2), (2, 0)], [1, 1, 1], charges=[P, 0, 0])
    assert r["responsion"] is False
    assert r["diagnostics"]["responsion_error"].startswith(
        "ValueError: cos: |x| too large for the Q61 octant reduction; got ")


# ── D4: the two blind spots, pinned as measured instrument facts ──────────────
def test_blind_spot_8_scalar_parameters_are_never_probed() -> None:
    """``rational.sin`` rounds a ``Q`` argument to float64 and the probe emits NO
    row for it, because :func:`demotion_probe.probe_op` enumerates sequence-shaped
    parameters only. Pinned, not fixed: a scalar-parameter probe is a different
    instrument. If this goes RED the probe has learned scalars — rewrite
    disclosure 8 in ``tools/demotion_probe.py`` in the same change."""
    from srmech.introspect.tool_schema import get_tool_schema
    from srmech.math import rational
    ent = {e.name: e for e in get_tool_schema().tools}["srmech.math.rational.sin"]
    assert [p.type for p in ent.parameters] == ["float", "int"]
    assert rational.sin(Q(P, 1)) == rational.sin(Q(F, 1)), "the demotion the probe cannot see"
    assert _dp.probe_op(ent, {}) == [], "the probe now addresses scalar parameters"


def test_blind_spot_9_the_keyword_reader_cannot_read_negation() -> None:
    """The measured instance behind ``odft_summand``'s rc465 'declaration'. If
    this goes RED the reader has learned negation — rewrite disclosure 9 and the
    rc463 gate's blind-spot 5 paragraph in the same change."""

    def negated():
        """The 8x8 matvec (the byte-exact parity contract, not a tolerance)."""

    assert _dp.declaration_hits(negated) == ["tolerance"], (
        "a negated keyword no longer counts as a declaration — the disclosure "
        "in tools/demotion_probe.py is now stale")
