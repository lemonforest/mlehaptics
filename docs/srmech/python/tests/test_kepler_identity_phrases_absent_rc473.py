"""The Kepler-identity sentences rc473 removed may not come back on a shipped surface.
(rc473 final round, `#T1188`)

WHAT WAS REMOVED, AND WHY A GATE
--------------------------------
rc473's truth round (commits ``8567c6d8d`` .. ``f915441fb``) and its repair
(``4e9972bab`` .. ``85351a43a``) replaced a family of sentences that asserted the
Antikythera pin-and-slot IS Kepler's equation, or IS the equation of centre, with
what the pure projection measures: one stage ``pin_slot(pi - M, e, 1.0)`` matches
``E - M`` through ``e**2`` and departs at ``e**3``; ``nu - E`` is a doubled stage at
double precision; ``M -> E`` is Newton. The sentences had shipped in the curated
ToolEntry prose, its two generated copies (``_tool_docs.py`` and the compiled-in
``srmech_tool_registry.c``), ``srmech.h``, ``srmech_kepler.c`` and ``kepler.py``.

Two merge-gate lenses then re-planted them (``kepler.py`` "Kepler-equation algebra
IS pin-slot composition."; the curated "SAME shape" clause) and every gate stayed
green. A removal nothing guards is a removal the next prose edit can undo.

WHAT THIS GATE READS
--------------------
The six surfaces above, as bytes, with every whitespace run, comment continuation
mark (``*``, ``#``, ``>``), C string-literal quote and escaped newline treated as a
gap — so a sentence wrapped across a C block comment, a Python docstring or a
JSON-in-C literal still matches. Case-insensitive. STRICT ZERO: these surfaces carry
no correction notes that quote the old sentences (the CHANGELOG does, and is not
scanned).

HOW IT CAN FAIL, IN THE TEST ITSELF
-----------------------------------
* Each phrase must match its own recorded original sentence, and a WRAPPED copy of
  it (a C block comment continuation between every word) — so a phrase that has
  stopped matching what it was written for is reported, not silently passed.
* A POSITIVE control on the real surfaces: the measured replacement sentences are
  found by the same scanner on the same six files, including the compiled
  registry's encoding — a scanner that could not read a surface would report zero
  hits there too, and would look exactly like a clean tree.

numpy-free. No ``abs()``. No ``hashlib``.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

SR_ROOT = Path(__file__).resolve().parents[2]            # docs/srmech

#: The shipped surfaces. The curated SSoT, both generated copies, and the three
#: hand-written sources that carried the family.
SURFACES = (
    "python/srmech/introspect/_tool_docs_curated.py",
    "python/srmech/introspect/_tool_docs.py",
    "c/src/srmech_tool_registry.c",
    "c/include/srmech.h",
    "python/srmech/math/kepler.py",
    "c/src/srmech_kepler.c",
)

#: phrase key -> (the phrase this gate forbids, the ORIGINAL sentence it was cut
#: from, as recorded in rc473's truth-round and truth-repair reports). The original
#: is the control: the phrase must match it.
REMOVED = {
    "algebra_IS_pin_slot": (
        "Kepler-equation algebra IS pin-slot composition",
        "Per [[user_stance_kepler_shape_universal]] + PR #416 F2/F15/F17: "
        "Kepler-equation algebra IS pin-slot composition."),
    "transform_IS_equation_of_centre": (
        "IS the Kepler equation of centre",
        "this transform IS the Kepler equation of centre to second order in "
        "eccentricity epsilon = pin_offset / pin_distance."),
    "output_IS_this_series": (
        "whose output IS this series",
        "pin_slot (same module) is the Antikythera bronze mechanism whose output IS "
        "this series to second order - its worked run measures the departure directly."),
    "bronze_realisation_same_shape": (
        "bronze realisation of the same shape",
        "pin_slot (same module) is the Antikythera bronze realisation of the same "
        "shape, agreeing with this equation to second order in eccentricity, as its "
        "own worked run measures."),
    "agreeing_to_second_order": (
        "agreeing with this equation to second order",
        "the Antikythera bronze realisation of the same shape, agreeing with this "
        "equation to second order in eccentricity"),
    "same_correction_closed_form": (
        "gives the same correction as a closed-form series",
        "equation_of_centre (same module) gives the same correction as a closed-form "
        "series; the run inverts through kepler_solve to measure the second-order "
        "agreement rather than asserting it."),
    "second_order_agreement": (
        "measure the second-order agreement",
        "the run inverts through kepler_solve to measure the second-order agreement "
        "rather than asserting it."),
    "pin_and_slot_IS_kepler_shape": (
        "the pin-and-slot IS the Kepler shape",
        "which is O(eps**2), the measured content of the claim that the pin-and-slot "
        "IS the Kepler shape to second order."),
    "residual_O_eps2": (
        "residual is O(eps**2)",
        "# invert it back - residual is O(eps**2)"),
    "orbital_equation_SAME_shape": (
        "an orbital equation are the SAME shape",
        "or demonstrating that a bronze linkage and an orbital equation are the "
        "SAME shape."),
    "universe_same_algebra": (
        "the universe instantiates the same algebra",
        "the universe instantiates the same algebra via gravitational dynamics."),
    "within_2e_15_bound": (
        "to within 2.0e-15 rad",
        "E + 2 * pin_slot(theta, eps, 1.0) is the true anomaly to within 2.0e-15 rad "
        "for e from 0.0549 to 0.99."),
    "four_significant_figures": (
        "to four significant figures at three different eccentricities",
        "The bronze transform's departure at theta = pi/2 lands on -eps to four "
        "significant figures at three different eccentricities"),
    "computes_the_anomaly": (
        "computes the anomaly rather than approximating a table of it",
        "the mechanism computes the anomaly rather than approximating a table of it"),
    "inverts_the_relation_exactly": (
        "inverts the relation exactly",
        "kepler_solve inverts the relation exactly"),
}

#: Sentences the replacements put on these surfaces, measured. Each must be FOUND
#: on the named surfaces — the scanner's reach, shown on the real files.
PRESENT = {
    "comparing a bronze linkage with Kepler's equation": (
        "python/srmech/introspect/_tool_docs_curated.py",
        "python/srmech/introspect/_tool_docs.py",
        "c/src/srmech_tool_registry.c"),
    "read Kepler-equation algebra as pin-slot composition": (
        "python/srmech/math/kepler.py",
        "c/src/srmech_kepler.c"),
    "read Kepler's equation as pin-slot composition": (
        "c/include/srmech.h",),
}

#: A gap between two words: whitespace, a comment continuation mark, a C string
#: literal boundary, or an escaped newline — ``\n`` in the curated file and
#: ``_tool_docs.py``, and ``\\n`` in ``srmech_tool_registry.c``, where the
#: generator writes a curated newline inside a JSON-in-C literal with its
#: backslash escaped a second time. Until rc473 final repair 1 (`#T1188`) this
#: read ``\\n`` (ONE backslash), and 12 of 15 removed sentences planted in the
#: registry split across its own ``\\n# `` stayed green.
_GAP = r"(?:\s|[*#>\"]|\\+n)+"


def _pattern(phrase: str) -> "re.Pattern[str]":
    return re.compile(_GAP.join(re.escape(w) for w in phrase.split()), re.I)


def _read(rel: str) -> str:
    path = SR_ROOT / rel
    return path.read_text(encoding="utf-8", errors="replace")


def _present_surfaces():
    missing = [rel for rel in SURFACES if not (SR_ROOT / rel).is_file()]
    if missing:
        pytest.skip(f"shipped surfaces absent from this cell: {missing}")
    return {rel: _read(rel) for rel in SURFACES}


def test_no_shipped_surface_carries_a_removed_kepler_identity_sentence() -> None:
    texts = _present_surfaces()
    live = []
    for key, (phrase, _original) in REMOVED.items():
        rx = _pattern(phrase)
        for rel, text in texts.items():
            for match in rx.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                live.append(f"{rel}:{line} [{key}] {match.group(0)[:90]!r}")
    assert not live, (
        f"{len(live)} removed Kepler-identity sentence(s) are back on a shipped "
        "surface:\n  " + "\n  ".join(live)
        + "\n\nrc473 measured each of these false or unbounded and replaced it with "
        "what the pure projection prints (notes/_rc473_truth_kepler_family.py, "
        "notes/_rc473_truth_repair1_kepler.py). Restore the measured sentence; do not "
        "delete the phrase from this gate unless a new measurement makes it true.")


@pytest.mark.parametrize("key", sorted(REMOVED))
def test_each_phrase_matches_its_own_original_sentence_plain_and_wrapped(key) -> None:
    phrase, original = REMOVED[key]
    rx = _pattern(phrase)
    assert rx.search(original), f"{key}: the phrase no longer matches its original"
    wrapped = "/*\n * " + "\n * ".join(original.split()) + "\n */"
    assert rx.search(wrapped), f"{key}: the phrase does not survive a C comment wrap"
    literal = '"' + '"\n        "'.join(original.split(" ")) + '"'
    assert rx.search(literal), f"{key}: the phrase does not survive a C string split"
    # The two escaped-newline encodings the string surfaces carry, byte for byte:
    # a worked-comment newline is `\n# ` in the curated file and _tool_docs.py and
    # `\\n# ` in srmech_tool_registry.c (rc473 final repair 1, `#T1188`).
    curated = "\\n# ".join(original.split())
    assert rx.search(curated), f"{key}: the phrase does not survive the curated escaped newline"
    registry = "\\\\n# ".join(original.split())
    assert rx.search(registry), (
        f"{key}: the phrase does not survive the C registry's escaped newline")
    assert not rx.search("an unrelated sentence about " + phrase.split()[0]), key


def test_the_scanner_reads_every_surface_it_claims_to_scan() -> None:
    texts = _present_surfaces()
    unseen = []
    for sentence, surfaces in PRESENT.items():
        rx = _pattern(sentence)
        for rel in surfaces:
            if not rx.search(texts[rel]):
                unseen.append(f"{rel}: {sentence!r}")
    assert not unseen, (
        "the scanner cannot find the measured replacement sentences on these "
        "surfaces, so a zero there would be blindness, not absence:\n  "
        + "\n  ".join(unseen))
    for rel, text in texts.items():
        assert len(text) > 10000 or rel.endswith("srmech_kepler.c"), (rel, len(text))
