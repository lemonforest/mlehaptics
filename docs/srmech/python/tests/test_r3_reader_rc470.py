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
E. **The FOUR DISCLOSED RESIDUAL FALSE POSITIVES** — pinned BY NAME, because
   none is refusable by any lexical rule. Good news, action required.

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
    negation: ulp 36, round-off 91, rounding 37, tolerance 23, float64 56,
    approximation 13, terminal float lift 8, accurate to 64, ~1e- 17, inexact 4.
    *(For contrast, and this is the trap: through the full ``declaration_hits``
    the same sweep gives ulp 43, round-off 108, rounding 38, tolerance 28,
    float64 86, approximation 17, terminal float lift 8, accurate to 71,
    ~1e- 22, inexact 5. Numbers of that shape mean the WRONG POPULATION was
    measured, not a broken reader.)*

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

    With ``0|zero`` removed and everything else held, DECLARED moves 207 -> 209
    at rc470, and the two ops let through both say "0 inexact" — an honest
    ZERO-COUNT, which is the opposite of a declaration.
    """
    import re
    fns = _registry()
    before = {n for n, f in fns if _dp.declaration_hits(f)}

    saved_cues, saved_neg = _dp.NEGATION_CUES, _dp._R3_NEG
    try:
        _dp.NEGATION_CUES = saved_cues.replace("|0|zero", "")
        assert _dp.NEGATION_CUES != saved_cues, "the cue spelling moved"
        _dp._R3_NEG = re.compile(
            r"\b(?:" + _dp.NEGATION_CUES + r")\b(?:\s+[-\w'’]+){0,%d}\s*$"
            % _dp.NEG_REACH)
        after = {n for n, f in fns if _dp.declaration_hits(f)}
    finally:
        _dp.NEGATION_CUES, _dp._R3_NEG = saved_cues, saved_neg

    let_in = sorted(after - before)
    assert let_in == ["srmech.math.weight_lattice.tensor_product_multiplicities",
                      "srmech.math.weight_lattice.weight_multiplicities"], let_in
    assert len(after) - len(before) == 2, (len(before), len(after))
    # and the reader is back as it was
    assert {n for n, f in fns if _dp.declaration_hits(f)} == before


# ── E — the FOUR DISCLOSED RESIDUAL FALSE POSITIVES ──────────────────────────

#: Each reads as DECLARED and, in the tree's naming, should not: the prose that
#: fires is about something OTHER than this op's own numeric accuracy. NONE is
#: refusable by any lexical rule — they are pinned, not fixed.
_RESIDUAL_FALSE_POSITIVES = {
    "srmech.rbs_lm.encode_aboutness":
        "the delegate _aboutness_tokens says 'the property it was "
        "approximating', which is about a REGEX SPELLING, not a number",
    "srmech.introspect.op_provenance.lossy_projection_record":
        "'a VALUE-INEXACT op (a float readout / a series truncation)' "
        "describes the op this record is ABOUT, not this op",
    "srmech.biology.genome.modulator_constraint":
        "'an over-approximation' is LOGICAL soundness, not numeric error",
    "srmech.biology.genome.modulator_constraint_satisfies":
        "'a sound over-approximation' is LOGICAL soundness — arguably a "
        "category R3 should not import at all",
}


@pytest.mark.parametrize("name", sorted(_RESIDUAL_FALSE_POSITIVES))
def test_group_e_the_disclosed_residuals_still_read_as_declared(name) -> None:
    """GOOD NEWS, ACTION REQUIRED — do not simply delete this pin.

    If one of these goes RED the op was renamed, its prose was fixed, or the
    reader got smarter. All three are improvements, and all three require
    UPDATING THE DISCLOSURE in ``tools/demotion_probe.py`` and the rc470
    CHANGELOG entry, not deleting the row. A later rc "fixing" these with a
    cleverer regex would be optimising against four hand-picked sentences.
    """
    fn = resolve_dotted_callable(name)
    assert _dp.declaration_hits(fn), (
        f"{name} no longer reads as declared. That is GOOD NEWS AND ACTION "
        f"REQUIRED: this row is a disclosed residual false positive "
        f"({_RESIDUAL_FALSE_POSITIVES[name]}). Update disclosure 9 in "
        f"tools/demotion_probe.py and the rc470 CHANGELOG entry in the same "
        f"change — do not just delete this row.")


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
