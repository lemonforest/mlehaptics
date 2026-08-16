"""rc440 (`#T1147`) — THE PREIMAGE-CONTRACT GATE: prose vs the LIVE key set.

WHY A SECOND README GATE, WHEN rc419 ALREADY SHIPPED ONE
========================================================
``test_readme_currency_rc419.py`` keys the shipped PyPI long-description on
**live values** and it is a good gate. It did **not** catch this defect, and the
reason is structural rather than an oversight: every assertion it makes is
against a **COUNT** — the registry total, the ABI integer, the version string.
A count-shaped gate can only ever see count-shaped drift.

The defect it could not see is a **CONTRACT**: ``klein4_from_one`` builds its
Class-A preimage from a fixed set of KEYS, rc438 added a fourth one, and every
sentence in the tree that ENUMERATES those keys — including the one on the PyPI
project page, which is the first srmech text most readers ever see — went on
saying three. No count moved. Nothing was stale by an integer. The prose simply
described a different function than the one that ships.

This is the same family as `#T1138` and the JPL Rule-1 / Rule-5 blind spots: **a
gate blind to its own subject class.** The fix is not another cardinal. It is to
make the ENUMERATION itself the pinned quantity, against the key set the shipped
op actually assembles.

WHAT "LIVE" MEANS HERE — MEASURED BY EXECUTION, NOT BY READING THE SOURCE
=========================================================================
:func:`live_preimage_keys` does not grep ``hdc.py`` for a dict literal. It
**runs** :func:`~srmech.math.hdc.klein4_from_one` with the JSON serialiser
swapped for a recorder, and reads back the dict the op actually handed to
:func:`~srmech.math.hdc.klein4_address`. A source-scraping gate would go blind
the moment the fields were assembled by a helper or a comprehension; an
execution-keyed one cannot, because the preimage is the thing it observes.

Two regimes are captured, because the contract is **CONDITIONAL** and that is
the whole subtlety of this defect:

    REST   ``{"sigma", "terms", "theta"}``            -- an unwound One
    WOUND  ``{"sigma", "terms", "theta", "winding"}`` -- a non-rest triad

Both halves are pinned. A fifth constructor input reds this file whichever way
it is added: unconditionally, and the REST set grows; conditionally, and the
WOUND-minus-REST set grows.

WHY THE PROSE MUST CARRY THE CONDITION, NOT JUST THE LONGER LIST
================================================================
The tempting fix for the rc439 text was to write "(sigma, theta, terms,
winding)" everywhere. **That is a second falsehood, not a repair.** rc438 emits
``winding`` only when the triad is non-rest — mirroring ``One._to_jsonable()``'s
own branch, which is precisely what keeps an unwound One byte-identical to every
release before rc438. For a One at rest, three keys ARE the whole preimage, and
the README's own worked example (``the_one(1, 1, 4)``) is exactly such a One.
So the governed prose is required to name the base three AND to name the
conditional key with a visible condition; asserting only the union would let a
blanket four-key sentence pass.

DELIBERATELY NOT ASSERTED: the surrounding narrative rc numbers and the historical
"1 of 729 / 729 of 729" measurements. Those are dated citations in the
``test_adapter_count_prose_rc409`` carve-out sense — editing them to today's
values would fabricate history, which is worse than a stale citation.
"""

from __future__ import annotations

import json as _stdlib_json
import re
from pathlib import Path

import pytest

import srmech.math.hdc as hdc
from srmech.cascade.one import the_one

#: repo-relative anchors. ``parents[2]`` is ``docs/srmech``; the C registry is a
#: GENERATED, COMPILED-IN surface and is governed here for the rc348 reason —
#: that sweep stopped at source and left 15 false links live in the wheel.
SR_ROOT = Path(__file__).resolve().parents[2]
README = SR_ROOT / "python" / "README.md"
HDC_SRC = SR_ROOT / "python" / "srmech" / "math" / "hdc.py"
CURATED = (SR_ROOT / "python" / "srmech" / "introspect"
           / "_tool_docs_curated.py")
GENERATED = SR_ROOT / "python" / "srmech" / "introspect" / "_tool_docs.py"
C_REGISTRY = SR_ROOT / "c" / "src" / "srmech_tool_registry.c"

D = 64

#: The One the README's own worked example builds — at REST by construction.
REST_ONE = lambda: the_one(1, 1, 4)                         # noqa: E731
#: The same One wound. Any non-rest triad exercises the conditional branch.
WOUND_ONE = lambda: the_one(1, 1, 4, w=(1, 0, 0))           # noqa: E731


class _PreimageRecorder:
    """A stand-in for ``hdc._json`` that records what the op serialises.

    Only ``dumps`` is exercised by :func:`~srmech.math.hdc.klein4_from_one`; the
    recorder delegates to the stdlib so the op's real bytes are unchanged and
    the observation cannot alter the value under test.
    """

    def __init__(self) -> None:
        self.seen: list = []

    def dumps(self, obj, **kwargs):
        self.seen.append(dict(obj))
        return _stdlib_json.dumps(obj, **kwargs)


def live_preimage_keys(one) -> frozenset:
    """The key set ``klein4_from_one`` ACTUALLY assembles for ``one``.

    Measured by running the shipped op, not by reading its source.

    The native fast path is forced off for the duration: it returns finished
    bytes from C without ever building the Python dict, so under a loaded
    ``.so`` there would be nothing to observe. That is not a parity dodge — the
    C peer applies the SAME non-rest branch on the same wire (ABI 15), and
    ``test_klein4_winding_preimage_rc438.py`` is the gate that proves it. Here
    the pure body IS the readable statement of the contract.
    """
    rec = _PreimageRecorder()
    real_json, real_native = hdc._json, hdc._klein4_from_one_native
    try:
        hdc._json = rec
        hdc._klein4_from_one_native = lambda *a, **k: None
        hdc.klein4_from_one(one, D)
    finally:
        hdc._json, hdc._klein4_from_one_native = real_json, real_native
    assert len(rec.seen) == 1, (
        f"expected exactly one Class-A preimage serialisation per call; the "
        f"recorder saw {len(rec.seen)}. The op's shape changed and this gate "
        f"has stopped observing what it claims to — re-point it, do not "
        f"delete the assertion.")
    return frozenset(rec.seen[0])


def rest_keys() -> frozenset:
    return live_preimage_keys(REST_ONE())


def wound_keys() -> frozenset:
    return live_preimage_keys(WOUND_ONE())


def prose_matches_live(prose_keys: frozenset, live_keys: frozenset) -> bool:
    """THE PREDICATE, named once so the falsification can run the real one.

    Every prose assertion below and the falsification at the bottom go through
    this same function. That is the point: a falsification that re-implements
    the check proves something about the copy, not about the shipped gate.
    """
    return prose_keys == live_keys


def _tokens(enumeration: str) -> frozenset:
    """Normalise a prose enumeration to comparable key tokens.

    Greek is folded to the field names the preimage uses, so prose is free to
    write ``σ``/``sigma`` and ``θ``/``theta`` interchangeably. Anything that is
    not a recognised key name is dropped rather than compared — this gate pins
    WHICH KEYS are named, not how a sentence is punctuated.
    """
    fold = {"σ": "sigma", "θ": "theta", "n": "terms", "w": "winding"}
    out = set()
    for raw in re.split(r"[,/()\s]+", enumeration):
        tok = raw.strip("`*_.'\"").lower()
        tok = fold.get(tok, tok)
        if tok in {"sigma", "theta", "terms", "winding"}:
            out.add(tok)
    return frozenset(out)


# ── the live contract itself ───────────────────────────────────────────────


def test_the_live_preimage_is_conditional_on_the_winding() -> None:
    """The measured contract, both regimes. Everything below keys on this.

    This is the assertion an added constructor input trips first. It is stated
    as an exact set on purpose: a subset check would let a fifth key in
    silently, which is the entire failure mode this file exists for.
    """
    assert rest_keys() == frozenset({"sigma", "terms", "theta"}), (
        f"klein4_from_one's REST preimage is {sorted(rest_keys())}, not the "
        f"three keys every governed prose surface enumerates. If a constructor "
        f"input was added, UPDATE THE PROSE (README.md, hdc.py's docstring, "
        f"_tool_docs_curated.py and the regenerated registry) in the same "
        f"change — that is what this gate is for.")
    assert wound_keys() == frozenset({"sigma", "terms", "theta", "winding"}), (
        f"klein4_from_one's WOUND preimage is {sorted(wound_keys())}. The "
        f"conditional key set moved; the governed prose must move with it.")
    assert wound_keys() - rest_keys() == frozenset({"winding"}), (
        "the conditional part of the preimage is no longer exactly "
        f"{{'winding'}}; it is {sorted(wound_keys() - rest_keys())}.")


def test_the_conditional_branch_is_real_not_decorative() -> None:
    """A conditional the op does not actually take is not a contract.

    Without this, ``rest_keys() != wound_keys()`` could hold for a reason
    unrelated to the winding, and the prose condition would be unfalsifiable.
    """
    assert rest_keys() != wound_keys(), (
        "the rest and wound preimages have the same key set — the rc438 "
        "non-rest branch is gone, and every conditional sentence this gate "
        "governs is now wrong in the other direction.")
    rest_hv = hdc.klein4_from_one(REST_ONE(), D).tobytes()
    wound_hv = hdc.klein4_from_one(WOUND_ONE(), D).tobytes()
    assert rest_hv != wound_hv, (
        "a wound One and an unwound One mint the SAME coupling — the rc438 "
        "defect has regressed (measured then: 1 distinct value out of 729).")


# ── the governed prose surfaces ────────────────────────────────────────────


def test_readme_enumerates_the_live_rest_key_set() -> None:
    """The PyPI long-description's coupling comment names the REST keys.

    The README's own example builds a One at rest, so the base enumeration must
    be exactly the rest key set — not the union, which would be false there.
    """
    text = README.read_text(encoding="utf-8")
    m = re.search(r"preimage is exactly \(([^)]*)\)", text)
    assert m, ("python/README.md no longer states the coupling's REST preimage "
               "as 'preimage is exactly (...)'. The sentence was rephrased and "
               "this gate has stopped observing — re-point the regex; do not "
               "delete the assertion.")
    assert prose_matches_live(_tokens(m.group(1)), rest_keys()), (
        f"python/README.md enumerates {sorted(_tokens(m.group(1)))} as the "
        f"coupling preimage; the live REST preimage is {sorted(rest_keys())}. "
        f"This text ships as the PyPI long-description.")


def test_the_readme_code_comment_itself_carries_the_condition() -> None:
    """THE COMMENT ON THE SNIPPET — where the defect actually lived.

    DEFENCE IN DEPTH, and the measurement says so rather than the intent.
    The two sibling tests already reach this comment, because the phrases they
    anchor on ("preimage is exactly …", "a WOUND One adds …") live inside it.
    **Measured** by re-planting the rc439 comment with this test deselected:
    **3 tests still go red**, so the file was never blind here. What this test
    adds is a different predicate on the same surface — it BANS the specific
    rc290-through-rc439 phrasing outright and requires a regime word within the
    comment block itself, rather than checking a rephrasing against the live key
    set. A rewrite that satisfied the token comparison while dropping the
    condition would pass the siblings and fail here.

    It is kept, and this docstring is worth reading, because an earlier draft of
    this very docstring claimed the siblings were blind — an artefact of a
    re-plant that silently did nothing (see
    :func:`test_the_gate_would_have_fired_on_the_rc439_text`). The claim was
    checked by deselecting this test and re-measuring, which is the only reason
    it is not still written here as fact.
    """
    text = README.read_text(encoding="utf-8")
    i = text.find("coupling = klein4_from_one(")
    assert i != -1, ("python/README.md no longer contains the genome snippet's "
                     "`coupling = klein4_from_one(` line — this gate has "
                     "stopped observing its subject.")
    comment = "\n".join(
        ln for ln in text[:i].rsplit("```python", 1)[-1].splitlines()
        if ln.lstrip().startswith("#"))
    assert comment, "the coupling line carries no explanatory comment at all"
    assert not re.search(r"DERIVED from \(\s*sigma\s*,\s*theta\s*,\s*terms\s*\)",
                         comment), (
        "the README's coupling comment states the preimage as an "
        "UNCONDITIONAL '(sigma, theta, terms)'. That is the rc290-through-rc439 "
        "text this rc exists to correct: true of the One in the snippet, false "
        "of a wound one, and it ships as the PyPI long-description.")
    assert re.search(r"\bREST\b", comment), (
        "the coupling comment does not say which REGIME its enumeration "
        "describes. The One in the snippet is at rest, where three keys are "
        "complete — say so, or the sentence is wrong for every wound One.")
    for key in wound_keys() - rest_keys():
        assert re.search(rf"\b{key}\b", comment), (
            f"the coupling comment never mentions {key!r}, which the live "
            f"preimage carries whenever the triad is non-rest.")


def test_readme_names_the_conditional_key_with_its_condition() -> None:
    """The other half: the wound-only key, and a visible condition.

    Asserting only the union would let a blanket four-key sentence pass, and
    that sentence is false for the example the README actually runs.
    """
    text = README.read_text(encoding="utf-8")
    conditional = wound_keys() - rest_keys()
    for key in conditional:
        assert re.search(rf"a WOUND One adds\b[^.]*\b{key}\b", text), (
            f"python/README.md does not say that a WOUND One adds {key!r} to "
            f"the preimage. The live wound key set is {sorted(wound_keys())}; "
            f"the rest set is {sorted(rest_keys())}.")
    assert re.search(r"non-rest condition One\._to_jsonable\(\) branches on",
                     text), (
        "python/README.md states the extra key without naming the CONDITION. "
        "An unconditional four-key sentence is its own falsehood — the "
        "example's own One is at rest, where three keys are complete.")


def test_hdc_docstring_enumerates_conditionally() -> None:
    """``klein4_from_one``'s own promise — the sentence that shipped wrong.

    It read "three canonical constructor integers" from rc290 through rc439,
    while the rc438 block *in the same docstring* quoted that promise as having
    been "false of every wound One". The docstring contradicted itself, which
    is the rc418 shape ``test_readme_does_not_contradict_itself_about_abi``
    was written for — caught here on a different surface.
    """
    src = HDC_SRC.read_text(encoding="utf-8")
    assert "three canonical constructor integers" not in src, (
        "srmech/math/hdc.py has re-acquired the unconditional 'three canonical "
        "constructor integers' promise. The op reads four declared inputs from "
        "a wound One; the sentence must carry the condition.")
    for key in wound_keys() - rest_keys():
        assert re.search(rf"plus the {key} triad when and only when", src), (
            f"hdc.klein4_from_one's promise no longer names {key!r} with its "
            f"non-rest condition. Live wound keys: {sorted(wound_keys())}.")


@pytest.mark.parametrize(
    "path",
    [CURATED, GENERATED, C_REGISTRY],
    ids=["curated-ssot", "generated-tool-docs", "compiled-c-registry"],
)
def test_the_generated_and_compiled_surfaces_carry_no_flat_enumeration(
        path: Path) -> None:
    """rc348's lesson: a sweep that stops at source does not reach the wheel.

    ``_tool_docs.py`` is generated from the curated SSOT and
    ``srmech_tool_registry.c`` bakes the merged prose into a C const table that
    is COMPILED IN and served by ``describe()`` and the MCP tool list. rc348
    measured **15 false links live in published artifacts** because a sweep
    checked only the hand-written side. All three are governed together, and
    the parametrisation is deliberate — a single combined assertion would let
    one surface drift while another masked it.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    assert "three canonical constructor integers" not in text, (
        f"{path.name} still advertises klein4_from_one as a function of "
        f"'three canonical constructor integers'. The live wound preimage is "
        f"{sorted(wound_keys())}. If this is the generated file or the C "
        f"registry, fix the curated SSOT and re-run "
        f"`python3 tools/regen_all.py` — do not hand-edit a generated file.")


# ── the retro-check: it must fail on the text it was written for ───────────


def test_the_gate_would_have_fired_on_the_rc439_text() -> None:
    """A gate that would not have caught its own motivating defect is not one.

    The rc439 strings are reproduced VERBATIM and driven through the SHIPPED
    predicates, so loosening a predicate to the point where the original defect
    slips past fails HERE rather than silently.
    """
    rc439_readme = ("# rc290: the coupling is DERIVED from (sigma, theta, "
                    "terms) — no magic seed.")
    m = re.search(r"DERIVED from \(([^)]*)\)", rc439_readme)
    assert m, "the historical README enumeration no longer parses"
    planted = _tokens(m.group(1))
    assert planted == frozenset({"sigma", "theta", "terms"}), planted
    # It matches the REST contract — which is exactly why the flat sentence
    # LOOKED right — and fails the WOUND one, which is the defect.
    assert planted == rest_keys()
    assert planted != wound_keys(), (
        "the live wound preimage now equals the rc439 three-key enumeration, "
        "so this retro-check no longer demonstrates anything — the rc438 fix "
        "has been reverted, or this gate has gone blind.")
    # And the condition-half predicate rejects it outright: the rc439 text
    # names no condition and no fourth key.
    assert not re.search(r"a WOUND One adds\b", rc439_readme)
    assert not re.search(r"non-rest condition One\._to_jsonable\(\) branches on",
                         rc439_readme)

    rc439_hdc = ("    DECLARED FUNCTION of the ``One``'s three canonical "
                 "constructor integers,")
    assert "three canonical constructor integers" in rc439_hdc, (
        "the docstring predicate stopped matching the historical text")


def test_a_fifth_constructor_input_would_red_the_prose() -> None:
    """FALSIFICATION of this file's headline claim, through the REAL predicate.

    The claim is *"adding a fifth constructor input reds the prose
    automatically"*. It is proven by running :func:`prose_matches_live` — the
    same function every assertion above calls — against a live key set carrying
    one more key than the prose names. Re-implementing the comparison here would
    only prove something about the copy.

    Both ways a fifth input could arrive are covered, because they land in
    different halves of the contract.
    """
    readme = README.read_text(encoding="utf-8")
    m = re.search(r"preimage is exactly \(([^)]*)\)", readme)
    assert m, "the README enumeration no longer parses"
    shipped_prose = _tokens(m.group(1))

    # (a) added UNCONDITIONALLY -> it joins the REST key set.
    grown_rest = frozenset(rest_keys() | {"curvature"})
    assert not prose_matches_live(shipped_prose, grown_rest), (
        "the shipped README enumeration still 'matches' a rest key set that "
        "gained a fifth key — the predicate has been loosened and this gate no "
        "longer does the one thing it exists for.")
    assert prose_matches_live(shipped_prose, rest_keys()), (
        "sanity: the shipped prose must match the ACTUAL rest key set, or the "
        "negative above is passing for the wrong reason.")

    # (b) added CONDITIONALLY -> it joins only the wound set, and the
    #     conditional half of the prose is what must name it.
    grown_conditional = frozenset(wound_keys() | {"curvature"}) - rest_keys()
    named = {k for k in grown_conditional
             if re.search(rf"a WOUND One adds\b[^.]*\b{k}\b", readme)}
    assert named != grown_conditional, (
        "the README already names every key of a conditional set it has never "
        "seen — the conditional-half predicate is not discriminating.")
    assert named == (wound_keys() - rest_keys()), (
        "the README names a different conditional key set than the live one: "
        f"prose {sorted(named)} vs live {sorted(wound_keys() - rest_keys())}.")


def test_the_recorder_observes_the_real_op_not_a_copy() -> None:
    """LIVENESS: the instrument must be able to return otherwise.

    An observation harness that silently stopped observing would make every
    assertion above vacuously green — the ``BodyReadProbe.assert_live()``
    lesson. So the recorder is shown to actually fire, and the bytes it
    observes are shown to be the op's real output.
    """
    rec = _PreimageRecorder()
    assert rec.seen == [], "a fresh recorder must start empty"
    real_json, real_native = hdc._json, hdc._klein4_from_one_native
    try:
        hdc._json = rec
        hdc._klein4_from_one_native = lambda *a, **k: None
        observed = hdc.klein4_from_one(WOUND_ONE(), D)
    finally:
        hdc._json, hdc._klein4_from_one_native = real_json, real_native
    assert len(rec.seen) == 1 and rec.seen[0], (
        "the recorder did not fire — every preimage assertion in this file "
        "would have been vacuous.")
    assert observed.tobytes() == hdc.klein4_from_one(WOUND_ONE(), D).tobytes(), (
        "the recorded call produced different bytes than the unobserved one, "
        "so the instrument is perturbing its subject.")
