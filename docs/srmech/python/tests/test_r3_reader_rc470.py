"""The R3 DECLARATION READER's own gate (rc470, `#T1188`).

An instrument that cannot be shown to return otherwise is not a measurement.
Through rc469 the reader that decides whether a registered op DECLARED its own
inexactness was a closed literal-substring list, and it had no gate of its own
at all — its behaviour was pinned only incidentally, by two blind-spot tests
that asserted it could NOT read things. This file is the reader's own can-fail
proof.

WHAT THE READER IS
==================
``tools/demotion_probe.py``'s :func:`declares_inexactness` answers one question
about a piece of contract prose: does it ADMIT that the op is inexact? It
matches bounded STEMS on WORD BOUNDARIES, PER OCCURRENCE, and refuses an
occurrence that a clause-local cue DENIES.

WHY EACH GROUP EXISTS
=====================
A. **POSITIVE controls** — verbatim in-tree sentences the old reader could not
   read, or could only read by accident. Without these, group B is satisfied by
   a reader that refuses everything.
B. **NEGATIVE controls** — real in-tree DENIALS. Without these, group A is
   satisfied by a reader that accepts everything.
C. **SUBSTRING traps** — real in-tree text where an R3 token occurs INSIDE an
   unrelated word. These are why the patterns carry word boundaries.
D. **The VOCABULARY META-TEST** — every pattern must earn its place on live
   prose. This is the discipline rc470 introduces, and the one most likely to
   go quietly vacuous later; see its own docstring.
E. **THE TOPICAL MISREADS** — every op that reads DECLARED and, on a
   hand-read of its whole contract surface, should not: pinned BY NAME,
   with a reason and a CLASS, because none is refusable by any lexical
   rule. Good news, action required. rc470's fourth commit disclosed
   FOUR and had read only the fifteen ops its own change moved; the
   ledger below is the whole DECLARED set, hand-read.

⚠️ **THE TREE'S ERROR-DIRECTION NAMES, which are the opposite of the intuitive
ones.** The census hunts DEFECTS, so a "positive" is a finding. A real
declaration read as undeclared is therefore a **FALSE POSITIVE** (it reports a
defect that is not there); a keyword in an unrelated or negating sentence read
as declared is a **FALSE NEGATIVE** (it clears a defect that is). Those are the
names ``tools/demotion_probe.py`` disclosures 5 and 9 use, and the ones used
here.

numpy-free. No ``abs()``. No stdlib ``fractions`` / ``math`` / ``decimal``.
"""

from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path

import pytest

_TOOLS = Path(__file__).resolve().parents[1] / "tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

import demotion_probe as _dp  # noqa: E402  (tools/ is on sys.path just above)

from srmech._resolve import resolve_dotted_callable  # noqa: E402
from srmech.introspect.tool_schema import get_tool_schema  # noqa: E402

#: The registry population every census figure in this rc is quoted against.
#: Asserted, never printed: a swallowed resolve exception shrinks the population
#: and every count falls WITHOUT the reader changing, which is the false-green
#: shape this whole rc exists to remove.
N_REGISTERED = 732

#: The READER's own freshness key, PINNED — sha256 over
#: :data:`demotion_probe.R3_READER_SPEC`, MEASURED at 0.9.0rc470. It is
#: asserted BEFORE the bare DECLARED count below, because
#: ``lexical DECLARED is N, not 219`` names an INTEGER where the defect is a
#: READER, and a reader-shaped defect reported as an integer is what rc470's
#: own re-validation spent a session chasing.
#:
#: ⚠️ **NECESSARY, NOT SUFFICIENT — MEASURED.** The digest is over DATA
#: (``R3_READER_SPEC``), so it is blind to a CODE mutant: replace the negation
#: refusal in :func:`demotion_probe.declares_inexactness` with ``if False:``
#: and this literal is UNCHANGED while DECLARED goes **219 -> 246**. That
#: mutant is not hypothetical — it was applied to the SHIPPED file during
#: rc470's own re-validation while a sibling process was importing it, and the
#: 246 was reported as a finding about this file. The two behavioural
#: sentinels in the ledger test are the ONLY check that names it; the pinned
#: signature covers only the class of change that reaches DISK.
_READER_SIGNATURE = (
    "8d17e6517b46d6d165347d50583029b1a919fd252d9089b954ffa79e4c434c50")


def _reader_identity() -> str:
    """WHICH reader answered — printed into every identity failure below.

    A count that disagrees is a claim about a FILE; this names the file, the
    digest of the bytes actually read, the spec digest, and which ``srmech``
    was on the path. Routed through ``srmech.amsc.format.sha256_bytes``, never
    a direct ``hashlib`` call.
    """
    import srmech
    from srmech.amsc.format import sha256_bytes
    blob = Path(_dp.__file__).read_bytes()
    return (f"[reader identity] file={_dp.__file__} "
            f"bytes_sha256={sha256_bytes(blob)} "
            f"reader_signature={_dp.reader_signature()} "
            f"srmech={srmech.__file__}")


def _registry():
    tools = list(get_tool_schema().tools)
    assert len(tools) == N_REGISTERED, (
        f"the registry holds {len(tools)} entries, not {N_REGISTERED}. Every "
        f"per-pattern figure in this file and in the rc470 CHANGELOG entry is "
        f"quoted against that population; re-measure before editing either.")
    out = []
    for e in tools:
        out.append((e.name, resolve_dotted_callable(e.name)))
    assert len(out) == N_REGISTERED
    return out


# ── A — POSITIVE controls ────────────────────────────────────────────────────

def test_group_a_the_full_vocabulary_reads() -> None:
    """Five labels off one sentence — the shape the census actually sees."""
    got = _dp.declares_inexactness(
        "accumulated in float64, accurate to round-off (~1e-15), 1 ulp")
    assert got == ["ulp", "round-off", "float64", "accurate to", "~1e-"], got


def test_group_a_morphology_the_old_reader_could_not_spell() -> None:
    """The CASE control and the MORPHOLOGY control in one.

    ``srmech.math.rational.sqrt`` carries the clearest declaration in the
    package and the rc469 reader returned ``[]`` for it: the list held
    "approximate" and the tree wrote APPROXIMATION, in capitals. Both halves —
    the stem and the fold — are asserted here.
    """
    assert _dp.declares_inexactness(
        "it is an APPROXIMATION of the square root") == ["approximation"]
    assert _dp.declares_inexactness(
        "the Q61 cosine of the ROUNDED angle") == ["rounding"]
    # and the live op, not just the phrase
    own = _dp.declares_inexactness(
        inspect.getdoc(resolve_dotted_callable("srmech.math.rational.sqrt")))
    assert own, "rational.sqrt reads as undeclared again"


def test_group_a_a_stated_bound_in_words_is_a_declaration() -> None:
    """``rational.cos`` — the op the task brief named, verbatim.

    A fixed-precision Class-N series states its error in WORDS, and every
    vocabulary through rc470's fourth commit was blind to it: ``cos``,
    ``sin``, ``exp``, ``tan``, ``cexp``, ``complex_exp``,
    ``kepler.pin_slot`` and both ``bessel`` ops read ``[]``. The ``\\s+``
    in the pattern is load-bearing — the docstrings are hard-wrapped and
    the phrase spans the break, which is why the sentence below carries a
    real newline.
    """
    assert _dp.declares_inexactness(
        "drive ``cos_series_truncate`` / ``sin_series_truncate`` until\n"
        "the truncation remainder is < ``2**-P``") == ["truncation"]
    assert _dp.declares_inexactness(
        "``exp_series_truncate`` sized so the ``2^n``-scaled absolute\n"
        "error is < ``2**-P``") == ["truncation"]
    for name in ("srmech.math.rational.cos", "srmech.math.rational.sin",
                 "srmech.math.rational.exp", "srmech.music.bessel_j_fixed"):
        own = _dp.declares_inexactness(
            inspect.getdoc(resolve_dotted_callable(name)))
        assert own == ["truncation"], (name, own)


def test_group_a_the_cue_dies_at_punctuation() -> None:
    """THE SCOPE CONTROL, and the reason the word class is the stop set.

    ``cascade.autocorrelation`` says "JPL-clean: no recursion, no
    transcendentals), parity to FFT roundoff (~1e-12)". The cue ``no`` must NOT
    reach ``roundoff`` — it is stopped by the ``)`` and the ``,``. Widening the
    intervening word class to ``\\w+`` or ``\\S+`` breaks exactly this.
    """
    got = _dp.declares_inexactness(
        "JPL-clean: no recursion, no transcendentals), parity to FFT "
        "roundoff (~1e-12)")
    assert got == ["round-off", "~1e-"], got


def test_group_a_a_denial_and_a_declaration_in_one_docstring() -> None:
    """PER-OCCURRENCE, not per-docstring. ``hypercomplex_exp`` carries both."""
    got = _dp.declares_inexactness(
        "The components hold exactly, with ``==``, not to a tolerance. "
        "The Q61 cosine of the ROUNDED angle is returned.")
    assert got == ["rounding"], got


# ── B — NEGATIVE controls, each a real in-tree denial ────────────────────────

@pytest.mark.parametrize("text,why", [
    ("The 8x8 matvec (the byte-exact parity contract, not a tolerance).",
     "rc466's synthetic denial — the measured instance behind blind spot 9"),
    ("nothing is rounded and no tolerance is consulted",
     "music.tempers_out — the QUANTIFIER cue"),
    ("6135 divisions, 0 inexact",
     "weight_lattice — the NUMERAL cue"),
    ("the spectral path takes a rank decision, never a float-magnitude "
     "tolerance",
     "dispatch._try_spectral — why the HYPHEN is inside the word class"),
])
def test_group_b_a_denial_is_not_a_declaration(text, why) -> None:
    assert _dp.declares_inexactness(text) == [], why


# ── C — SUBSTRING traps ──────────────────────────────────────────────────────

@pytest.mark.parametrize("text,why", [
    ("see https://example.org/files/FULpnas71.pdf for the source",
     "srmech.biology.genome — a CITATION URL declared an op through rc469, and "
     "the tree spells it with a capital FUL, so this proves the fold AND the "
     "boundary together"),
    ("the record emits {'__float64__': float.hex(x)} as its tag key",
     "op_provenance_hash read as declared via a delegate's JSON TAG KEY"),
    ("the surrounding body and the reusable grounding PRIMITIVE",
     "'round' inside 'surrounding'/'grounding'; 'ulp' is not in either"),
])
def test_group_c_a_substring_is_not_a_word(text, why) -> None:
    assert _dp.declares_inexactness(text) == [], why


def test_group_c_a_truncated_digest_is_not_a_truncation_bound() -> None:
    """THE TRAP that decided the truncation pattern's width.

    ``amsc.format.sha256_bytes`` says "``int(h[:8], 16)`` (a truncated
    32-bit tag)". Under ``\\btruncat\\w*`` that ONE sentence declares 33 ops
    through the delegate follow (24 via ``sha256_bytes``, 9 via the
    private ``_sha256_bytes``), and DECLARED moves 207 -> 278. Under
    ``\\btruncation\\b`` it moves 207 -> 229 and picks up ``huffman``,
    ``hdc_truncation`` and ``harmonic_oscillator_hamiltonian``, which
    truncate a LIST or a BASIS. Both were refused; this is the row that
    goes red if a later rc "regularises" the stem.
    """
    assert _dp.declares_inexactness(
        "``int(h[:8], 16)`` (a truncated 32-bit tag), NOT the digest") == []
    assert _dp.declares_inexactness(
        "the huffman code truncation table") == []
    own = _dp.declares_inexactness(inspect.getdoc(
        resolve_dotted_callable("srmech.amsc.format.sha256_bytes")))
    assert own == [], own


def test_group_c_the_tilde_pattern_must_not_take_a_word_boundary() -> None:
    """EXECUTED, because this one is invisible by inspection.

    ``\\b`` before ``~`` asserts a PRECEDING WORD CHARACTER, so ``\\b~1e-\\d``
    never matches at all. A builder "regularising" that pattern to look like its
    nine neighbours would silently drop every ``~1e-`` declaration in the tree.
    """
    import re
    assert re.search(r"\b~1e-\d", "accurate to ~1e-9 here") is None
    assert re.search(r"(?<![\w~])~1e-\d", "accurate to ~1e-9 here") is not None
    assert _dp.declares_inexactness("accurate to ~1e-9 here") == [
        "accurate to", "~1e-"]


# ── D — the VOCABULARY META-TEST ─────────────────────────────────────────────

def test_group_d_every_pattern_earns_its_place_on_live_prose() -> None:
    """THE WEAK RULE: every pattern must MATCH at least one live registry
    docstring AND SURVIVE negation on at least one.

    THE POPULATION IS NAMED, and it is deliberately narrower than
    :func:`demotion_probe.declaration_hits`: each registered op's OWN docstring,
    with NO delegate follow and NO ``exact=`` arm. The question here is whether
    a PATTERN earns its place in the vocabulary, not whether an OP is declared.

    ⚠️ **The per-pattern COUNTS are deliberately NOT pinned.** Ten exact numbers
    over a 732-op registry would go red on any unrelated docstring edit, which
    is a gate that cries wolf, not a ratchet. They are a measurement for the
    CHANGELOG; the rule asserted here is only that none of the ten is
    decoration. MEASURED at 0.9.0rc470 in exactly this population, after
    negation: ulp 37, round-off 92, rounding 38, tolerance 23, float64 57,
    approximation 13, terminal float lift 8, accurate to 65, ~1e- 17,
    inexact 4, truncation 4.
    *(For contrast, and this is the trap: through the full ``declaration_hits``
    the same sweep gives ulp 44, round-off 109, rounding 39, tolerance 28,
    float64 87, approximation 17, terminal float lift 8, accurate to 72,
    ~1e- 22, inexact 5, truncation 12. Numbers of that shape mean the
    WRONG POPULATION was measured, not a broken reader.)*

    ⚠️ **These figures were WRONG when they were first written, and the
    way they were wrong is the whole case for the printed-not-remembered
    rule.** rc470's fourth commit shipped "ulp 36 … accurate to 64" — a
    sweep taken BEFORE the same commit gave ``cascade.phase_coherent_peak``
    its ACCURACY paragraph, which adds exactly one to those five labels.
    EXECUTED both ways: strip that paragraph in process and the sweep
    returns the shipped numbers; leave it and it returns these. The counts
    are deliberately unpinned, so nothing went red — which is why the
    remedy is a rule about writing them, not a new assertion.

    ⚠️ **The likeliest way this test goes quietly vacuous**: a future rc deletes
    the last op carrying "terminal float lift", and the tempting fix is deleting
    the PATTERN rather than asking whether the phrase left on purpose.
    """
    fns = _registry()
    fired = {}
    for _name, fn in fns:
        for lab in _dp.declares_inexactness(inspect.getdoc(fn) or ""):
            fired[lab] = fired.get(lab, 0) + 1
    dead = [lab for lab, _pat in _dp.R3_PATTERNS if not fired.get(lab)]
    assert not dead, (
        f"R3 patterns that fire on NOTHING in the {N_REGISTERED}-op registry "
        f"after negation: {dead}. Either the prose they were written for has "
        f"left the tree — in which case ask why before deleting the pattern — "
        f"or the pattern is wrong. A vocabulary entry that cannot fire is "
        f"decoration, and this file exists to refuse decoration.")


def test_group_d_the_numeral_cue_is_load_bearing() -> None:
    """The ONE-TOKEN CONTROL for ``NEGATION_CUES``, executed rather than told.

    With ``0|zero`` removed and everything else held, DECLARED moves
    **219 -> 221** on the repaired reader, and the two ops let through both
    say "0 inexact" — an honest ZERO-COUNT, which is the opposite of a
    declaration. rc470's fourth commit measured 207 -> 209 on the reader it
    shipped, and a comment in ``tools/demotion_probe.py`` quoted a third
    pair, 206 -> 208, that reproduced on no tree at all. The +2 is the
    invariant; the BASELINE moves with every reader change, so it is
    asserted as a delta and a NAMED SET below, never as a remembered pair.

    The mutated regex is rebuilt from :data:`demotion_probe.NEG_WORD_CLASS`
    rather than from a literal, so this control cannot silently diverge
    from the reader it is holding everything-else-equal against.
    """
    import re
    fns = _registry()
    before = {n for n, f in fns if _dp.declaration_hits(f)}

    saved_cues, saved_neg = _dp.NEGATION_CUES, _dp._R3_NEG
    try:
        _dp.NEGATION_CUES = saved_cues.replace("|0|zero", "")
        assert _dp.NEGATION_CUES != saved_cues, "the cue spelling moved"
        _dp._R3_NEG = re.compile(
            r"\b(?:" + _dp.NEGATION_CUES + r")\b(?:\s+"
            + _dp.NEG_WORD_CLASS + r"){0,%d}\s*$" % _dp.NEG_REACH)
        after = {n for n, f in fns if _dp.declaration_hits(f)}
    finally:
        _dp.NEGATION_CUES, _dp._R3_NEG = saved_cues, saved_neg

    let_in = sorted(after - before)
    assert let_in == ["srmech.math.weight_lattice.tensor_product_multiplicities",
                      "srmech.math.weight_lattice.weight_multiplicities"], let_in
    assert len(after) - len(before) == 2, (len(before), len(after))
    # and the reader is back as it was
    assert {n for n, f in fns if _dp.declaration_hits(f)} == before


def test_group_d_the_case_policy_is_wired_not_declared() -> None:
    """The knob that was a SPEC MEMBER NO CODE READ — the inverse blind spot.

    ``R3_READER_SPEC`` exists so that no knob can move the reader without
    moving the digest. ``CASE_POLICY`` was in the tuple, but through rc470's
    repair commit :func:`demotion_probe.declares_inexactness` called
    ``.lower()`` under a COMMENT saying ``# CASE_POLICY == "lower"``. A
    constant nothing reads is the mirror-image defect: no mutation of it can
    move a read, so the only thing a gate could prove was that the DIGEST
    moved — which ``test_silent_carrier_demotion_rc463`` did, and which is
    consistent with the reader ignoring the constant entirely.

    Two halves, both EXECUTED:

    1. **The wire carries current.** Set the policy to ``"none"`` and the
       reader stops reading a SHOUTED token; restore it and the token comes
       back. Under the old comment-only fold, both reads are identical.
    2. **The table is CLOSED.** An unknown policy raises AT IMPORT rather than
       falling through to a default fold — which would read the whole tree
       with a fold the freshness key says is not in use. That closedness check
       is a real ``raise ValueError``, NOT a bare ``assert`` (rc433 shape,
       `#T1188`): as first written it WAS an ``assert``, and
       ``tests/test_assert_contract_gate_rc433.py`` caught it on every CI job.
       A ``pytest.raises(AssertionError)`` here would have been certifying an
       import-time guard that ``python -O`` deletes — and worse, this control
       would itself have failed under ``-O``, because ``compile()`` defaults to
       ``optimize=-1`` and INHERITS the caller's flag, so the mutant loses the
       assert too. MEASURED (py3.10, `#T1188`): reconstructing the ``assert``
       form and exec'ing it under ``python3 -O`` gives ``NO EXCEPTION -> GUARD
       ABSENT; CASE_POLICY='upper'``, and the first read then raises a bare
       ``KeyError('upper')`` — ``_FOLDS[CASE_POLICY]`` is a plain subscript
       with no default, so what ``-O`` destroyed was the guard's LEGIBILITY and
       EARLINESS, not a silent wrong answer. The ``raise`` fires identically at
       optimize 0, 1 and 2.

    ⚠️ **HOW HALF 2 IS MEASURED, and the rule it obeys.** The mutant is
    compiled from an IN-MEMORY COPY of the probe's source and exec'd into a
    throwaway namespace. The shipped file is never written. rc470's own
    re-validation mutated ``tools/demotion_probe.py`` IN PLACE three times to
    prove can-fail claims, restoring from a byte copy each time; a sibling
    process imported one of those mutants mid-window and reported its DECLARED
    count as a defect in this file. The restore was byte-exact, so ``git
    diff`` was empty and the only trace was an mtime. Mutate a COPY.
    """
    from pathlib import Path

    # ── half 1: the wire carries current ────────────────────────────────
    assert _dp.CASE_POLICY == "lower", _dp.CASE_POLICY
    assert sorted(_dp._FOLDS) == ["lower", "none"], sorted(_dp._FOLDS)
    assert _dp.declares_inexactness("an APPROXIMATION") == ["approximation"]

    saved = _dp.CASE_POLICY
    try:
        _dp.CASE_POLICY = "none"
        shouted = _dp.declares_inexactness("an APPROXIMATION")
        # the SAME sentence, already lowercase, is unaffected: the fold is the
        # only difference between these two reads, which is what makes this a
        # measurement of the fold rather than of the patterns.
        quiet = _dp.declares_inexactness("an approximation")
    finally:
        _dp.CASE_POLICY = saved

    assert shouted == [], (
        f"CASE_POLICY is not WIRED: with the fold set to 'none' a SHOUTED "
        f"token still reads {shouted}, so declares_inexactness is folding "
        f"case by some route the constant does not decide. {_reader_identity()}")
    assert quiet == ["approximation"], quiet
    assert _dp.CASE_POLICY == "lower", "the policy was not restored"
    assert _dp.declares_inexactness("an APPROXIMATION") == ["approximation"]
    assert _dp.reader_signature() == _READER_SIGNATURE, (
        f"CASE_POLICY is a SPEC MEMBER, so a failure to restore it moves the "
        f"reader signature for every test after this one. {_reader_identity()}")

    # ── half 2: the table is closed — mutate a COPY, never the shipped file ──
    text = Path(_dp.__file__).read_text(encoding="utf-8")
    line = 'CASE_POLICY = "lower"'
    assert text.count(line) == 1, (
        f"the CASE_POLICY assignment is not a single line spelled {line!r}; "
        f"this control cannot target it. {_reader_identity()}")
    mutant = text.replace(line, 'CASE_POLICY = "upper"', 1)
    ns = {"__name__": "demotion_probe__case_policy_mutant",
          "__file__": _dp.__file__}
    with pytest.raises(ValueError, match="names no fold in _FOLDS"):
        exec(compile(mutant, _dp.__file__ + " [COPY: CASE_POLICY=upper]",
                     "exec"), ns)
    # the SHIPPED file is untouched by the above, and still the one we read
    assert Path(_dp.__file__).read_text(encoding="utf-8") == text



# ── E — the TOPICAL MISREAD LEDGER, over the WHOLE DECLARED set ──────────────

#: **Every op that reads DECLARED and, hand-read, should not.**
#:
#: THE CRITERION is the honesty ladder's, verbatim from
#: ``tests/test_silent_carrier_demotion_rc463.py``: *given ONLY the signature
#: and the docstring, and no knowledge of the implementation, can the caller
#: predict that the returned value is not the exact one?* A row belongs here
#: when BOTH halves hold:
#:
#:   1. EVERY surviving R3 occurrence is off-topic — it is not a statement
#:      about THIS op's own numeric accuracy; AND
#:   2. no OTHER sentence in the docstring warns either, R3-token-bearing or
#:      not. Where (1) holds and (2) fails the verdict is substantively RIGHT
#:      and only the label points at the wrong prose, so the op is NOT pinned;
#:      those are named in ``tools/demotion_probe.py`` disclosure 10 instead.
#:      EIGHT, MEASURED per-occurrence on this tree: ``rational.relative_writhe``,
#:      ``coupling.fold_spectrum``, ``rational.hypot``,
#:      ``triality.lean_isa_seventh_primitive``,
#:      ``octonion.octonion_exp_series_truncate``,
#:      ``quaternion.quaternion_exp_series_truncate``, and — rc470's
#:      LAST commit, moved OUT of the ledger below —
#:      ``matrix_cascades.eig_exact`` and
#:      ``matrix_cascades.singular_values_exact``. This list read FIVE and
#:      omitted ``hypot``; the probe's own copy said "Five" and listed six.
#:      ⚠️ ``rational.exp_series_truncate`` is NOT one of them — it reads
#:      ``[]`` (EXECUTED), so "both ``*_exp_series_truncate``" means the
#:      OCTONION and QUATERNION pair, which is why they are now spelled out.
#:
#: ⚠️ **TWO ROWS WERE REMOVED BY rc470's LAST COMMIT, and removal is the
#: rarer of the two legal moves.** ``matrix_cascades.eig_exact`` (pinned
#: HISTORY, the whole class) and ``matrix_cascades.singular_values_exact``
#: (pinned OTHER-OP) both fail half (2) of the criterion above, so they never
#: belonged here: each states its own terminal projection in prose the caller
#: can read BEFORE calling — ``"value": complex,  # the terminal float/complex
#: projection`` and *"``value`` / ``vector`` are the single TERMINAL
#: projections (rotation-last)"* on the first, ``"value": float}  # the single
#: terminal projection (project=True only)`` on the second — and BOTH carry
#: ``project: bool = True`` in the signature. The honesty ladder asks whether
#: the caller can predict *the returned value is not the exact one*, and on
#: both ops the answer is yes, from the docstring alone. So the verdict
#: DECLARED is substantively right and only the matched sentence is off-topic:
#: the LABEL-MISATTRIBUTION class, not this one. ``jordan_form_exact`` was
#: read the same way and STAYS out of the ledger on its own merits — its
#: ``~1e-`` fires on *"``A·P ≈ P·J`` to ~1e-9 in the projected float/complex
#: read-out"*, which IS a statement about this op's own accuracy.
#:
#: ⚠️ **THE NAME.** rc470's fourth commit called these four rows "residual
#: FALSE POSITIVES", which contradicts this file's own error-direction ⚠️
#: above: by that convention an op read as DECLARED when it did not declare is
#: a FALSE **NEGATIVE** (it clears a defect that is there); a FALSE POSITIVE is
#: the opposite direction. Rather than pick a polarity word and be wrong for
#: half the readers, the ledger is named for WHAT IT IS — the reader matched a
#: token whose TOPIC is something other than this op's accuracy.
#:
#: ⚠️ **NONE of these is refusable by any lexical rule, and that is the
#: finding, not an excuse.** The reader is TOPIC-BLIND by construction. The
#: instrument is therefore the reader PLUS this hand-maintained ledger, and a
#: NEW false reading created by NEW prose is invisible until a human reads it
#: — the parametrized test below fires only when a PINNED op stops reading
#: DECLARED, never when a new one starts. Any rc that touches docstrings
#: should re-run the per-occurrence dump over the DECLARED set and diff it
#: against this dict.
#:
#: MEASURED at 0.9.0rc470: 219 DECLARED, 39 pinned here, **180 substantive**.
#: ⚠️ **THE BASELINE IS QUOTABLE ONLY AS A PAIR.** 219 is LEXICAL and
#: regenerable by anyone with this tree; 181 is 222 minus a HAND-MAINTAINED
#: ledger, so it is only as fresh as the last hand-read. Quoting 181 alone
#: implies a measurement the instrument cannot make.
#: The 41 are MOSTLY not a rc470 regression: **35** of them read
#: DECLARED under the rc469 reader too — MEASURED by re-implementing
#: that substring reader from ``git show main:tools/demotion_probe``.
#: ⚠️ Its VOCABULARY is re-used over the SHIPPED, FOLDED delegate
#: walk: main's own walk carries the PEP 709 defect rc470's last
#: commit fixed and reads **202 on CPython <= 3.11, 204 on >= 3.12**,
#: so the published 202 was an interpreter artifact too. Held
#: constant, the figure is **204** on every interpreter. The **six** the widening added are
#: exactly the six topical misreads among the fifteen lexical gains:
#: ``lll_reduce``, ``continued_fraction_convergents``,
#: ``lossy_projection_record``, both ``modulator_constraint*`` and
#: ``encode_aboutness``. The truncation stem and ``rational.sin``'s
#: own bound added NONE — all twelve of those flips are genuine.
_RESIDUAL_TOPIC_MISREADS = {
    # ── EXACTNESS-CLAIM: the sentence that fires ASSERTS exactness ──────────
    "srmech.biology.coupling.signed_sum_squared": (
        "EXACTNESS-CLAIM", "'the small non-negative integer scores are exact "
        "as float64 doubles' — the token is inside the claim that they are "
        "exact"),
    "srmech.biology.genome.genome_content": (
        "EXACTNESS-CLAIM", "delegate _content_turns: 'n_chromosomes + "
        "n_content is exact … an approximate relation would be useless' — a "
        "COUNTERFACTUAL inside an exactness claim; the op returns an int"),
    "srmech.cascade.matrix_cascades.lll_reduce": (
        "EXACTNESS-CLAIM", "three occurrences of 'rounding', every one of "
        "them EXACT nearest-integer rounding of μ, on an op whose first "
        "sentence says 'in EXACT rational arithmetic (no float anywhere)'"),
    "srmech.introspect.op_provenance.op_verdict": (
        "EXACTNESS-CLAIM", "'sound even where the float readouts diverge in "
        "the last ulp' — a ROBUSTNESS claim; the op returns 'EQUAL' or "
        "'UNKNOWN'"),
    "srmech.physics.qm.so9.spin9_spinor_generators": (
        "EXACTNESS-CLAIM", "'entries are dyadic ({0, ±½, ±1}), hence "
        "bit-exact in float64'"),

    # ── OTHER-OP: the sentence is about a DIFFERENT operation ───────────────
    "srmech.cascade.matrix_cascades.lstsq_exact": (
        "OTHER-OP", "'the float lstsq is honest about what it is (it declares "
        "\"to round-off\")' — about :func:`lstsq`, on an op that is exact "
        "over ℚ"),
    "srmech.math.rational.continued_fraction_convergents": (
        "OTHER-OP", "'the BEST rational approximation to the limit value' is "
        "Hardy & Wright Thm 154, a theorem about the CONVERGENTS; the op is "
        "an exact bigint recurrence"),
    "srmech.cascade.octonion_frame_read": (
        "OTHER-OP", "'~1e-15 Sp(1)-invariance' measures "
        ":func:`octonion_laplacian`'s spectrum; this op is 'exact end to end "
        "— no float, no epsilon'"),
    "srmech.music.harmonics.classify_chirality_harmonic": (
        "OTHER-OP", "delegate to_q: 'to approximate to a small denominator "
        "use best_rational instead' — advice about ANOTHER op; this one "
        "returns 1, 2 or 3"),
    "srmech.introspect.op_provenance.reproject": (
        "OTHER-OP", "delegate _canon: 'honestly inexact leaves' is about the "
        "RECORD's float-leaf tagging"),
    "srmech.introspect.op_provenance.lossy_projection_record": (
        "OTHER-OP", "'a VALUE-INEXACT op (a float readout / a series "
        "truncation)' describes the op this record is ABOUT. ⚠️ Fixing that "
        "sentence does NOT turn this row red: the delegate arm then reads "
        "_canon's 'honestly INEXACT leaves' instead — EXECUTED"),
    "srmech.introspect.op_provenance.carry": (
        "OTHER-OP", "'params (e.g. num_terms, tolerance)' and 'None for "
        "unnamed/inexact targets' are both about the CARRIED op"),

    # ── OTHER-CARRIER: the sentence names the EXACT carrier's float peer ────
    "srmech.math.qmat.qmat_rank": (
        "OTHER-CARRIER", "QMat: 'the bigint exact peer of the float64 Mat' / "
        "'collapses to a float64 mat ONLY via to_mat'"),
    "srmech.math.qmat.qmat_det": (
        "OTHER-CARRIER", "QMat, as above; the op returns a Q, never a float"),
    "srmech.math.qmat.qmat_inverse": (
        "OTHER-CARRIER", "QMat, as above; raises rather than returning a "
        "rounded pseudo-inverse"),
    "srmech.math.qmat.qmat_rref": ("OTHER-CARRIER", "QMat, as above"),
    "srmech.math.qmat.qmat_solve": ("OTHER-CARRIER", "QMat, as above"),
    "srmech.math.qmat.qmat_nullspace": ("OTHER-CARRIER", "QMat, as above"),
    "srmech.math.groups.intertwiner_space": (
        "OTHER-CARRIER", "QMat, as above; the op returns an EXACT basis"),
    "srmech.chemistry.deficiency": (
        "OTHER-CARRIER", "QMat, as above; the Feinberg δ is an integer"),
    "srmech.apokatastasis.gosper.gosper": (
        "OTHER-CARRIER", "Poly: 'collapses to a list of float64 ONLY via "
        "to_floats' — the word ONLY makes it an exactness claim"),
    "srmech.apokatastasis.wz_certificate.wz_certificate": (
        "OTHER-CARRIER", "Poly, as above"),
    "srmech.math.poly.poly_from_coeffs": (
        "OTHER-CARRIER", "Poly, as above; a non_compute BUILDER over ints"),
    "srmech.apokatastasis.zeilberger.bipoly_from_coeffs": (
        "OTHER-CARRIER", "Poly, as above"),
    "srmech.math.tripoly.tripoly_from_coeffs": (
        "OTHER-CARRIER", "Poly, as above"),
    "srmech.math.carrier_ladder.poly_project": (
        "OTHER-CARRIER", "Poly, as above"),
    # The two the reader could not SEE until rc470's last commit folded
    # comprehension-nested co_names into the delegate walk: both name Poly
    # only inside a listcomp, so on CPython <= 3.11 they read [] and could not
    # be pinned. Same delegate, same sentence, same class as the six above —
    # pinning them makes via-Poly 8/8, matching via-QMat's 8/8.
    "srmech.apokatastasis.zeilberger.zeilberger": (
        "OTHER-CARRIER", "Poly, as above; the op's OWN docstring says 'Exact "
        "over ℚ (bigint, no magnitude ceiling); no float' and it calls "
        "Poly.from_coeffs, never to_floats"),
    "srmech.apokatastasis.apagodu_zeilberger.apagodu_zeilberger": (
        "OTHER-CARRIER", "Poly, as above; 'Every returned leaf is exact and "
        "closed-form on the ALU'"),

    # ── DISPATCH-TYPE: the sentence is a native-ABI TYPE list ───────────────
    "srmech.cascade.chiral_flip": (
        "DISPATCH-TYPE", "'when HAS_NATIVE is True and seq is a homogeneous "
        "int64 / float64 list' — a C-ABI precondition; the op returns "
        "seq[::-1], type preserved"),
    "srmech.cascade.chiral_dual": (
        "DISPATCH-TYPE", "the srmech_cascade_chiral_dual_f64 precondition"),
    "srmech.cascade.reversal_law_census": (
        "DISPATCH-TYPE", "delegate chiral_flip, as above"),
    "srmech.cascade.anti_automorphism_witnesses": (
        "DISPATCH-TYPE", "delegate chiral_flip, as above"),
    "srmech.cascade.cdr_clean": (
        "DISPATCH-TYPE", "delegate chiral_flip, as above"),
    "srmech.cascade.parallel_sector_dispatch": (
        "DISPATCH-TYPE", "delegate _chiral_dual, as above"),

    # ── SERIALISATION: the sentence is a WIRE / BYTE format ─────────────────
    "srmech.spectral.predict": (
        "SERIALISATION", "delegate _complex128_bytes: 'interleaved "
        "native-endian (re, im) float64 pairs' is a PACKING format for the "
        "content hash. The op IS float — and nothing in its own docstring "
        "says so, which is why this row is a misread in both directions"),
    "srmech.physics.qm.so9.spin8_in_spin9_branching": (
        "SERIALISATION", "delegate _branching_attestation: 'a Class A "
        "content-address over the γ + σ float64 bytes'; the op's own prose "
        "says 'bit-exact' six times"),

    # ── OTHER-DOMAIN: a non-numeric use of an R3 word ───────────────────────
    "srmech.math.hdc.klein4_holographic_encode": (
        "OTHER-DOMAIN", "'3/4 known-erasure tolerance' is CODING theory; the "
        "op returns a uint8 store"),
    "srmech.bus.decode_splice": (
        "OTHER-DOMAIN", "'±1 for clock-skew tolerance' is a TIME window; the "
        "op returns plaintext bytes"),

    # ── LOGICAL-SOUNDNESS: 'approximation' as a LATTICE word ────────────────
    "srmech.biology.genome.modulator_constraint": (
        "LOGICAL-SOUNDNESS", "'an over-approximation' is soundness, not "
        "numeric error"),
    "srmech.biology.genome.modulator_constraint_satisfies": (
        "LOGICAL-SOUNDNESS", "'a sound over-approximation' — arguably a "
        "category R3 should not import at all"),

    # ── REGEX: the sentence is about a PATTERN SPELLING ─────────────────────
    "srmech.rbs_lm.encode_aboutness": (
        "REGEX", "delegate _aboutness_tokens: 'the property it was "
        "approximating' is about a [a-z][0-9] SPELLING"),
}

#: The classes above, so a reader can see the shape of the residual without
#: counting the dict by hand. MEASURED, and asserted below.
_MISREAD_CLASS_COUNTS = {
    "EXACTNESS-CLAIM": 5,
    "OTHER-OP": 7,
    "OTHER-CARRIER": 16,  # +2 at rc470's last commit: the two zeilberger ops
    "DISPATCH-TYPE": 6,
    "SERIALISATION": 2,
    "OTHER-DOMAIN": 2,
    "LOGICAL-SOUNDNESS": 2,
    "REGEX": 1,
}

#: sha256 over the WHOLE folded label map — every DECLARED op paired with the
#: labels it reads, sorted — MEASURED byte-identical on CPython 3.10.21 /
#: 3.11.16 / 3.12.3 / 3.13.15 / 3.14.7 at 0.9.0rc470.
#:
#: ⚠️ **THIS IS THE THREE-VERSION CONVERGENCE ASSERTION, and it exists because
#: the COUNT CANNOT MAKE IT.** rc470's last commit folded comprehension-nested
#: co_names into the delegate walk, which makes DECLARED *membership*
#: convergent BY CONSTRUCTION. It does NOT do the same for the *label*:
#: :func:`declaration_hits` breaks at the first hit-bearing delegate, so
#: ``co_names`` ORDER decides WHICH delegate gets the credit, and **13 of the
#: 573 ops that reach that arm carry two or more hit-bearing delegates**
#: (an identical list on 3.10 and 3.12 — e.g. ``spectral_spine`` and
#: ``relational_structure`` both name ``signed_laplacian`` AND
#: ``symmetric_eigendecompose``). Their labels agree across interpreters TODAY
#: only because the names that changed position happen to be non-hit-bearing
#: and jumped AROUND the hit-bearing pair. That is an accident, not a
#: guarantee — and a bare ``len(declared) == 222`` is blind to it, because
#: DECLARED would stay 222 on every interpreter while the credited delegate
#: silently differed.
#:
#: A single-interpreter test cannot assert a cross-version property on its own.
#: THIS LITERAL IS HOW IT IS ASSERTED ANYWAY: the same digest is checked in
#: every cell of the CI matrix, so a divergence reddens exactly the cell that
#: disagrees. That is the whole mechanism — one pinned literal, checked
#: everywhere.
#:
#: ⚠️ **IF THIS MOVES, SAY WHETHER THE COUNT MOVED WITH IT.** Count AND digest
#: → the DECLARED set changed; re-adjudicate. Digest ALONE → a LABEL moved
#: while membership held, which is either an edited docstring or the ORDER
#: residue above finally biting. The second case is the one this constant was
#: minted to catch; do not re-pin it without reading which delegate changed.
_DECLARED_LABEL_MAP_DIGEST = (
    "06f93439fe15b27f197aef81146b9f88961702db59cbf196b32b3857b372fe6b")


def _declared_label_map_digest(pairs) -> str:
    """sha256 over ``{op: labels}``, sorted — the LABEL map, not the count.

    Routed through ``srmech.amsc.format.sha256_bytes`` — never a direct
    ``hashlib`` call — so native dispatch picks it up transparently.
    """
    from srmech.amsc.format import sha256_bytes
    body = json.dumps({n: list(h) for n, h in sorted(pairs)},
                      sort_keys=True, ensure_ascii=True) + "\n"
    return sha256_bytes(body.encode("utf-8"))


def test_group_e_the_ledger_is_internally_consistent() -> None:
    """The ledger's own arithmetic, so the three quoted counts cannot drift.

    ``lexical DECLARED`` − ``pinned`` = ``substantive``, and every class count
    adds up. This is the assertion that makes the CHANGELOG's three numbers
    regenerable rather than remembered.
    """
    counts = {}
    for cls, _why in _RESIDUAL_TOPIC_MISREADS.values():
        counts[cls] = counts.get(cls, 0) + 1
    assert counts == _MISREAD_CLASS_COUNTS, counts
    assert sum(_MISREAD_CLASS_COUNTS.values()) == len(
        _RESIDUAL_TOPIC_MISREADS) == 41

    # ── (a) the reader ON DISK is the one this ledger was hand-read against ─
    # Names an on-disk spec change. Blind to a code change: see the ⚠️ on
    # _READER_SIGNATURE.
    assert _dp.reader_signature() == _READER_SIGNATURE, (
        f"R3_READER_SPEC has MOVED: reader_signature() is "
        f"{_dp.reader_signature()}, not the pinned {_READER_SIGNATURE}. Every "
        f"count in this file was hand-read against the pinned reader — re-run "
        f"the per-occurrence dump over the DECLARED set and move all three "
        f"numbers together. {_reader_identity()}")

    # ── (b) the LIVE objects are the ones the spec describes ────────────────
    # Names an IN-PROCESS swap — a monkeypatch, a fixture, or group_d's own
    # controlled mutation failing to restore. reader_signature() cannot see
    # any of those: it digests the constants, not the compiled objects.
    neg_from_spec = (r"\b(?:" + _dp.NEGATION_CUES + r")\b(?:\s+"
                     + _dp.NEG_WORD_CLASS + r"){0,%d}\s*$" % _dp.NEG_REACH)
    assert _dp._R3_NEG.pattern == neg_from_spec, (
        f"_R3_NEG is not built from the spec constants IN THIS PROCESS — an "
        f"in-process swap, which the signature cannot see. live="
        f"{_dp._R3_NEG.pattern!r} spec={neg_from_spec!r}. {_reader_identity()}")
    assert [(lab, rx.pattern) for lab, rx in _dp._R3_COMPILED] == list(
            _dp.R3_PATTERNS), (
        f"_R3_COMPILED is not R3_PATTERNS compiled, in this process: "
        f"{[(lab, rx.pattern) for lab, rx in _dp._R3_COMPILED]}. "
        f"{_reader_identity()}")
    assert _dp._R3_SPLIT.pattern == _dp.SENTENCE_SPLIT, (
        f"_R3_SPLIT is not SENTENCE_SPLIT compiled, in this process: "
        f"{_dp._R3_SPLIT.pattern!r}. {_reader_identity()}")

    # ── (c) the reader BEHAVES — the ONLY check that names a CODE mutant ────
    # Both sentences are verbatim shapes from this tree: the first is
    # hypercomplex_dft._phase_coherent_peak_pure's denial (the sentence rc470
    # deliberately left standing), the second is rc467's own APPROXIMATION,
    # which the rc469 reader could not spell. Executed INLINE, here, rather
    # than trusted from another test file in another process.
    denial = _dp.declares_inexactness("the parity contract, not a tolerance")
    assert denial == [], (
        f"the NEGATION REFUSAL IS NOT IN FORCE IN THIS PROCESS: a denial read "
        f"as a declaration, {denial}. Every count below is inflated and the "
        f"defect is the READER, not the number. {_reader_identity()}")
    approx = _dp.declares_inexactness("an APPROXIMATION")
    assert approx == ["approximation"], (
        f"the reader can no longer read a case-folded 'approximation': "
        f"{approx}. Every count below is deflated and the defect is the "
        f"READER, not the number. {_reader_identity()}")

    declared = {n for n, fn in _registry() if _dp.declaration_hits(fn)}
    # ⚠️ THIS WAS A KNOWN OPEN DEFECT AND IS NOW CLOSED — `#T1188`, rc470's
    # last commit. It read 219 on CPython <= 3.11 and 222 on >= 3.12 from ONE
    # unchanged tree, with an IDENTICAL reader_signature and IDENTICAL probe
    # bytes. The ruler did not move; the READING did.
    #
    # MECHANISM, now MEASURED on five real interpreters rather than simulated
    # on one: declaration_hits's third arm followed ONE level of delegate over
    # `fn.__code__.co_names` — a COMPILED artifact answering a question about
    # SOURCE. Through CPython 3.11 a comprehension body compiles to its OWN
    # nested code object with its OWN co_names, so a delegate named only inside
    # a comprehension was invisible to that walk. PEP 709 ("Inlined
    # comprehensions", 3.12) removes the nested object and those names join the
    # enclosing function's, so the SAME code found MORE delegates:
    #
    #   3.10.21 219 | 3.11.16 219 | 3.12.3 222 | 3.13.15 222 | 3.14.7 222
    #
    # A cutover at 3.12 with a measured point on EACH side and no unmeasured
    # interior. (Two earlier rounds recorded 3.11 and 3.13 as unmeasurable.
    # They were one `uv python install 3.11 3.13` away — 2.89s. Declining to
    # measure is a finding; calling unmeasurable something never attempted is
    # not.)
    #
    # THE FIX, applied: tools/demotion_probe.py's _delegate_names() folds
    # comprehension-nested co_names into the walk UNCONDITIONALLY. On >= 3.12
    # it is a STRUCTURAL no-op (0 of 732 ops have any nested comprehension code
    # object left to find, against 839 <listcomp> + 51 <dictcomp> + 9 <setcomp>
    # on 3.10/3.11); on <= 3.11 it recovers exactly the names 3.12 already saw.
    # Convergence is asserted over the WHOLE population, not three counts: the
    # folded label MAP is byte-identical on all five interpreters, all 222
    # rows — see _DECLARED_LABEL_MAP_DIGEST below.
    #
    # THE THREE IT MOVES, hand-read, and it is EXACTLY three (gained 3, lost 0,
    # label-changed 0 over the full 732 on every interpreter):
    #   * zeilberger and apagodu_zeilberger -> FALSE readings. Poly's hit
    #     sentence is "Collapses to a list of float64 only via to_floats" — the
    #     word ONLY makes it an exactness claim about ANOTHER carrier — while
    #     their own docstrings say "Exact over ℚ (bigint, no magnitude
    #     ceiling); no float". PINNED above as OTHER-CARRIER, making via-Poly
    #     8/8 and matching via-QMat's 8/8. Pinning them is possible only
    #     BECAUSE of the fold: pre-fix they read [] on 3.10, and pinning would
    #     have reddened the parametrized misread test there. The fix and the
    #     adjudication are ONE change; neither works alone.
    #   * heat_kernel -> a TRUE declaration. It STANDS as a gain, unpinned.
    #     The rival reading — that _rexp's bound describes a `precision=P`
    #     branch heat_kernel never selects, so the credit is off-topic — rests
    #     on a premise that is FALSE, EXECUTED: rational.exp's DEFAULT branch
    #     is a fixed 18-term Taylor (_EXPLOG_EXP_TERMS = 18) returning a
    #     DYADIC, Q(., 2**59) at x=1.0, differing from the precision=200
    #     reference by 5.8398e-17. A dyadic cannot equal a transcendental, so
    #     the bound is real and the value flowing into heat_kernel IS inexact.
    #     Consistency confirms it: of the 9 ops labelled `truncation (via X)`,
    #     the 3 whose delegate's firing sentence is a precision=P branch the
    #     call site never selects — kepler.pin_slot, rational.tan and
    #     heat_kernel — are ALL unpinned. Pinning one would contradict two
    #     live rulings.
    #
    # WHAT SURVIVES UNFIXED, named so it is not rediscovered as a surprise: the
    # loop BREAKS at the first hit-bearing delegate, so ORDER decides the
    # LABEL while the fold converges MEMBERSHIP by construction. 13 of the 573
    # ops that reach the arm carry >= 2 hit-bearing delegates (an identical
    # list on 3.10 and 3.12); their labels agree today only because the names
    # that changed position are non-hit-bearing. The digest below is what lets
    # a matrix cell SEE a future divergence there — the COUNT alone could not,
    # since DECLARED would stay 222 everywhere while the credited delegate
    # silently differed.
    assert len(declared) == 222, (
        f"lexical DECLARED is {len(declared)}, not 222. Every count in this "
        f"file, in tools/demotion_probe.py's disclosures and in the rc470 "
        f"CHANGELOG entry is quoted against that figure. ⚠️ IF THIS IS 219, "
        f"the comprehension fold in demotion_probe._delegate_names is not "
        f"running: 219 is the PRE-FIX reading of CPython <= 3.11 (MEASURED "
        f"219 on 3.10.21 and 3.11.16, 222 on 3.12.3 / 3.13.15 / 3.14.7 before "
        f"the fold; 222 on all five after). RESTORE THE FOLD rather than "
        f"moving this number — two of the three ops it reveals are PINNED "
        f"misreads above and would fall out of the ledger, reddening the "
        f"parametrized test. The four assertions above have already cleared "
        f"the reader, so this is a DELEGATE-FOLLOW or PROSE change, never a "
        f"reader-vocabulary change. {_reader_identity()}")
    unknown = sorted(set(_RESIDUAL_TOPIC_MISREADS) - declared)
    assert not unknown, f"pinned but not DECLARED: {unknown}"
    assert len(declared) - len(_RESIDUAL_TOPIC_MISREADS) == 181


def test_group_e_the_folded_label_map_is_version_independent() -> None:
    """THE THREE-VERSION CONVERGENCE ASSERTION — see _DECLARED_LABEL_MAP_DIGEST.

    Two claims, and the SECOND is the one the count cannot make:

    1. The comprehension fold is present and STRUCTURALLY inert on >= 3.12.
       ``_delegate_names`` must return the plain ``co_names`` there, because
       PEP 709 leaves no nested comprehension code object to find — measured
       0 of 732 on 3.12.3 / 3.13.15 / 3.14.7, against 839 ``<listcomp>`` +
       51 ``<dictcomp>`` + 9 ``<setcomp>`` on 3.10.21 / 3.11.16. This is a
       no-op BY CONSTRUCTION on the newer interpreters, not by luck.
    2. The whole LABEL MAP hashes to one pinned literal on every interpreter.
       Membership convergence is guaranteed by the fold; label convergence is
       not, and 13 ops have two or more hit-bearing delegates whose order
       decides the credit.
    """
    fold_is_live = hasattr(_dp, "_delegate_names")
    assert fold_is_live, (
        "tools/demotion_probe.py has no _delegate_names: the comprehension "
        "fold has been REMOVED. DECLARED will read 219 on CPython <= 3.11 and "
        "222 on >= 3.12 from one unchanged tree, and two of the ops pinned in "
        f"_RESIDUAL_TOPIC_MISREADS will fall out. {_reader_identity()}")

    # (1) the fold is a STRUCTURAL no-op where PEP 709 already ran
    nested_total = 0
    for _n, fn in _registry():
        code = getattr(fn, "__code__", None)
        if code is None:
            continue
        nested_total += len(_dp._delegate_names(code)) - len(set(code.co_names))
    if sys.version_info >= (3, 12):
        assert nested_total == 0, (
            f"{nested_total} comprehension-nested names were folded on CPython "
            f"{sys.version_info.major}.{sys.version_info.minor}, where PEP 709 "
            f"should have left none. The fold is still CORRECT — it is "
            f"unconditional and idempotent — but its no-op-by-construction "
            f"justification does not hold on this interpreter, so re-measure "
            f"before quoting it. {_reader_identity()}")

    # (2) the LABEL map, not the count
    pairs = [(n, _dp.declaration_hits(fn)) for n, fn in _registry()]
    got = _declared_label_map_digest([(n, h) for n, h in pairs if h])
    assert got == _DECLARED_LABEL_MAP_DIGEST, (
        f"the folded DECLARED label map hashes to {got}, not the pinned "
        f"{_DECLARED_LABEL_MAP_DIGEST}. This is the LABEL map, so it moves "
        f"for a reason the bare count cannot report. FIRST check whether "
        f"len(declared) also moved: if it did, the DECLARED SET changed and "
        f"the ledger above needs re-adjudicating; if it did NOT, a LABEL "
        f"moved while membership held — either an edited delegate docstring, "
        f"or the co_names ORDER residue (13 ops carry >= 2 hit-bearing "
        f"delegates and declaration_hits breaks at the first). Name which "
        f"delegate changed before re-pinning. {_reader_identity()}")


@pytest.mark.parametrize("name", sorted(_RESIDUAL_TOPIC_MISREADS))
def test_group_e_the_pinned_misreads_still_read_as_declared(name) -> None:
    """GOOD NEWS, ACTION REQUIRED — do not simply delete a row.

    If one of these goes RED the op was renamed, its prose was fixed, or the
    reader got smarter. All three are improvements, and all three require
    UPDATING THE LEDGER, disclosure 9 in ``tools/demotion_probe.py`` and the
    rc470 CHANGELOG entry in the same change — not deleting the row. A later
    rc "fixing" these with a cleverer regex would be optimising against
    forty-one hand-picked sentences.
    """
    fn = resolve_dotted_callable(name)
    cls, why = _RESIDUAL_TOPIC_MISREADS[name]
    assert _dp.declaration_hits(fn), (
        f"{name} no longer reads as declared. That is GOOD NEWS AND ACTION "
        f"REQUIRED: this row is a pinned TOPICAL MISREAD [{cls}] ({why}). "
        f"Update disclosure 9 in tools/demotion_probe.py and the rc470 "
        f"CHANGELOG entry in the same change — do not just delete this row.")


def test_group_e_no_pinned_misread_holds_a_demotion_row_at_zero() -> None:
    """THE ONE WAY A MISREAD COULD BE LOAD-BEARING, refused by measurement.

    ``EXPECTED_UNDECLARED_N`` is a strict zero over DEMOTED rows that publish
    no R3 declaration. If a pinned misread carried a DEMOTED row, that zero
    would be held up by a reading this file has just called false — the exact
    shape ``phase_coherent_peak`` had through rc469, where a DELEGATE'S DENIAL
    was the whole declaration on a genuinely demoting op.

    MEASURED over the committed two-cell census: none of the 41 does.
    """
    import json
    from pathlib import Path
    cen = Path(__file__).resolve().parent / "demotion_census.ndjson"
    rows = [json.loads(line) for line in
            cen.read_text(encoding="utf-8").splitlines() if line.strip()]
    data = [r for r in rows if "op" in r]
    assert data, "the census manifest carried no data rows"
    holding = sorted({
        f"{r['op']}::{r['param']}" for r in data
        if r["op"] in _RESIDUAL_TOPIC_MISREADS
        for cell in ("native", "pure")
        if (r.get(cell) or {}).get("verdict") == "DEMOTED"})
    assert not holding, (
        f"a pinned topical misread carries a DEMOTED census row: {holding}. "
        f"EXPECTED_UNDECLARED_N's strict zero would then be held up by a "
        f"reading this file calls false — write the op a real ACCURACY "
        f"paragraph (the rc466 D1 shape) rather than leaving the pin.")



# ── the op rc470 re-declared, D3-style ───────────────────────────────────────

def test_phase_coherent_peak_is_demoted_and_now_says_so() -> None:
    """THE ONE VERDICT rc470 MOVES — and it moves toward honesty, not away.

    Through rc469 this op's ENTIRE declaration was a DELEGATE reading: the token
    ``tolerance`` inside ``_phase_coherent_peak_pure``'s sentence "the parity
    contract, not a tolerance", which denies it. The new reader refuses that,
    correctly, so rc470 gave the op a true ACCURACY paragraph on its own
    docstring (the rc466 D1 shape). The op's BEHAVIOUR is untouched: the witness
    below is the same demotion it always had.

    ⚠️ If the equality goes RED the CARRIER moved — re-read the ACCURACY
    paragraph, because it would then be describing an op that no longer exists.
    """
    from srmech.cascade import phase_coherent_peak as pcp
    F = pcp([[2 ** 53 + 0]])["score"]
    P = pcp([[2 ** 53 + 1]])["score"]
    G = pcp([[2 ** 53 + 2]])["score"]
    assert P == F, (
        f"phase_coherent_peak no longer demotes 2**53+1 onto 2**53 "
        f"({P!r} vs {F!r}) — THE CARRIER MOVED. Re-read the ACCURACY "
        f"paragraph on the op; it now describes something untrue.")
    assert G != F, (
        f"the witness is vacuous: 2**53+2 must stay APART from 2**53, or this "
        f"test would pass on a reader that returns a constant ({G!r} vs {F!r})")

    own = _dp.declares_inexactness(inspect.getdoc(pcp) or "")
    assert own == ["ulp", "round-off", "rounding", "float64", "accurate to"], own
    hits = _dp.declaration_hits(pcp)
    assert hits and not hits[0].endswith(")"), (
        f"phase_coherent_peak's first hit {hits[:1]} is a DELEGATE hit again — "
        f"rc466 rule D1 requires the op's own contract surface, which is what "
        f"inspect.getdoc, help() and the probe read")


def test_the_delegates_denial_is_left_standing() -> None:
    """The delegate sentence is TRUE and rc470 deliberately did not touch it.

    It says the pure and native paths are byte-exact with EACH OTHER — a parity
    contract between two float projections. That is not a claim of exactness,
    and the reader is now right to refuse it as a declaration. Rewriting a true
    sentence to satisfy a reader is the move rc470 exists to stop making.
    """
    from srmech.cascade import hypercomplex_dft as _h
    doc = inspect.getdoc(_h._phase_coherent_peak_pure) or ""
    assert "not a" in doc and "tolerance" in doc, (
        "the delegate's denial was rewritten; rc470's whole point is that the "
        "READER changed and the true prose stayed")
    assert _dp.declares_inexactness(doc) == [], (
        "the delegate's denial reads as a DECLARATION again — the negation "
        "refusal has regressed")
