"""rc420 (`#T1114`) — THE NOTEBOOK CURRENCY GATE, tied to LIVE values.

WHY THIS EXISTS — the SSoT drifted 21 rcs with nothing watching
==============================================================
``docs/srmech/srmech_research_notebook.md`` is the declared SSoT for the
A–N vocabulary and for the package's own architecture. At the rc419 tree its
most recent rc mention was **rc399** against a **rc420** HEAD, and **no test
in the repository read it as a currency surface**. Two tests touch the file
and neither is one: ``test_ref_notation_emitted_rc348`` rglobs the subtree to
derive the ``#TNNN`` vocabulary (it reads the notebook for TASK IDS, not for
claims), and ``test_klein4_unbundle_rc172`` merely cites a section in its own
docstring. What that ungated interval cost, measured on the pinned tree:

* **ten dead import statements inside §3.45** — the section titled "USAGE
  EXAMPLES … EXECUTED", whose §3.45.0 exists specifically to record the
  PHANTOM-GAP failure of a reader concluding a capability is absent. Four
  module moves account for all ten (``srmech.qm.*`` → ``srmech.physics.qm.*``
  REMOVED at rc382 with no alias; ``srmech.amsc.cascade.*`` →
  ``srmech.cascade.*``; ``srmech.amsc.poly`` → ``srmech.math.poly``;
  ``srmech.amsc.qmat`` → ``srmech.math.qmat``).
* **a five-way combinator count** that the rc420 kernel widening made false.
* **a cascade-catalog cardinal** whose only statement anywhere was prose.

``[[feedback_ungated_surfaces_trickle_gated_surfaces_race_to_100]]``.

THE THREE PRINCIPLES, INHERITED FROM ``test_readme_currency_rc419``
==================================================================
**1. Never literal-vs-literal.** Every assertion here resolves the LIVE value
— ``len(KERNEL_BUILDERS)``, ``describe()["cascade_catalog"]``,
``len(get_tool_schema().tools)``, ``srmech.__version__``, and for the import
gates the actual :func:`importlib.import_module` — and reads the notebook's
claim out of the shipped file. *A number written as a literal, with no tie to
the value it describes, rots; the same number written as a live lookup
cannot.*

**2. Internal consistency is a SEPARATE test.** The notebook states the
combinator cardinal in five places and the catalog partition in two. At rc418
the README contradicted ITSELF, and a source-only gate would have reported
one failure where there were two independent ones. :func:`
test_the_notebook_does_not_contradict_itself_about_the_combinator_count` and
its catalog peer compare the notebook's sites to EACH OTHER, with no access
to the source.

**3. ★ DATED CITATIONS ARE CARVED OUT — and the carve-out is a POSITIVE
guard, not a hole.** This is the whole design problem, because the notebook is
largely dated per-rc ledgers. *"Editing a dated claim to today's value would
fabricate history, which is a worse defect than the stale cardinal."* So
:func:`test_dated_claims_are_present_verbatim_and_are_never_rewritten` asserts
each protected string is still there, byte-for-byte AND at its exact
occurrence count. An allowlist that merely EXEMPTS is silent when somebody
"fixes" ``describe()`` stays 178`` to 598; an allowlist that ASSERTS goes red.
The notebook already argues for this in its own voice at §3.28.3: *"It is
dated rather than bumped for one reason, stated so the next reader does not
'fix' it."* This file is the mechanism behind that sentence.

The *count* half of that was not there at first draft, and the gate's own
mutation run is what found it: rewriting ONE of the four ``describe()`` stays
178`` bullets left the substring present elsewhere, and the suite reported 20
passed. A guard whose predicate cannot distinguish four occurrences from three
is not guarding four things.

THE DATED/LIVE DISCRIMINATOR, STATED SO IT CAN BE ARGUED WITH
=============================================================
A claim is **DATED** (protected, never rewritten) when it *records a past
state*: a per-rc ledger entry (``rc11 … describe()`` stays 178``), an
as-of-release row (``registers ~87 entries``), or a measurement-provenance
stamp naming the tree a committed artifact was run against (``run against
0.9.0rc420, registry 598`` — the NDJSON files literally carry those stamps, so
bumping the prose would decouple it from the evidence).

A claim is **LIVE** (gated) when it *asserts what is true now of the shipped
tree*: ``the catalog's twenty descriptors partition 20 = 17 executable + 3
leaf``, ``the six Bird-Meertens recursion schemes``, ``describe() gained a
twelfth top-level key``.

The ``Live at rcNNN: …`` form is deliberately in the LIVE class even though it
carries an rc token, because the sentence's own contract is *"this is the live
value, timestamped"* — re-verifying and moving the stamp is correct practice,
not fabricated history. So :func:`test_live_at_rc_stamps_name_the_pinned_
release` pins the token to ``srmech.__version__`` and the number beside it to
the live lookup: they move together or not at all.

WHAT THIS GATE DELIBERATELY DOES **NOT** CHECK
==============================================
* **Measured outputs, per-rc ledger entries, historical rc citations.** See
  principle 3 — these are the protected class, and the only thing asserted
  about them is that they still say what they said.
* **The combinator NAME SET.** The notebook writes the form as ``parallel``
  while the builder is ``Chain.parallel_sectors``, and says so inline. A
  name-set equality would be gating a vocabulary difference, not currency.
  Only the CARDINAL is gated.
* **Prose module names at strict zero.** A dead path *named as dead* is
  correct prose, and the notebook does this constantly and on purpose
  (``~~`srmech.amsc.compose`~~ raises ``ModuleNotFoundError```). The prose
  check is therefore a **down-only CEIL** on the residual — the same shape
  ``test_ref_notation_emitted_rc348`` uses for the same reason — while the
  FENCED-BLOCK check, where a path is presented as runnable, is **strict
  zero**. A code block that does not run is not a citation, it is a defect.
* **The `§3.0` pre-schema YAML sketch.** Its four ``srmech.transforms/kernels/
  lattices.*`` paths have never existed; the notebook says so one line below
  (*"The schema is not committed yet … this is the pre-schema sketch"*). The
  exemption is CONDITIONAL on that sentence still being present — if the
  schema ever lands, the disclaimer goes and the paths must resolve.

WHERE IT RUNS
=============
The notebook sits at ``docs/srmech/``, OUTSIDE ``srmech-ci.yml``'s
``docs/srmech/python/**`` trigger, so this file is registered in
``test_ref_notation_emitted_rc348.SCAN_ROOTS`` and gets its own step in
``.github/workflows/srmech-ref-guard.yml``. Without that step the gate would
be armed and silent on exactly the commits it exists to catch: notebook-only
ones.
"""

from __future__ import annotations

import importlib
import re
from pathlib import Path

import srmech
from srmech.introspect.tool_schema import get_tool_schema, warmup_all

# The live combinator kernel. Sourced from the closure ratchet rather than
# re-derived here, so the two files cannot disagree about what the kernel is:
# that ratchet OWNS the count, and this gate only asks whether the prose
# agrees with it.
from tests.test_combinator_kernel_closure import KERNEL_BUILDERS

_HERE = Path(__file__).resolve()
#: `parents[2]` is `docs/srmech` — declared in SCAN_ROOTS, see module docstring.
_NOTEBOOK = _HERE.parents[2] / "srmech_research_notebook.md"


# ──────────────────────────────────────────────────────────────────────
# LIVE VALUES — every one of these is a lookup, never a literal.
# ──────────────────────────────────────────────────────────────────────

def _text() -> str:
    """The notebook as shipped — what the dated-claim guard reads."""
    return _NOTEBOOK.read_text(encoding="utf-8")


#: A `~~ ~~` run, possibly spanning lines (§3.28's `#T982` strike does).
_STRUCK = re.compile(r"~~.+?~~", re.S)


def _live_prose() -> str:
    """The notebook with every STRUCK run removed.

    This is the discriminator that makes the live-claim scans below correct,
    and the gate's first run proved it is load-bearing: ``_BIRD_MEERTENS``
    matched §3.29.1's *superseded* five-form sentence — which sits three lines
    above the corrected six-form one and is struck through — and reported the
    notebook stale when it was current. Strikethrough is the notebook's OWN
    marker for "this was true and no longer is", i.e. it is precisely the
    dated class, so a live-value scan must not see it. The verbatim
    dated-claim guard still reads :func:`_text`, so the struck text is
    protected at the same time it is ignored here.
    """
    return _STRUCK.sub(" ", _text())


def _live_catalog() -> dict:
    return srmech.describe()["cascade_catalog"]


def _live_op_count() -> int:
    """The basis the notebook's own sentence names: ``len(...tools)``."""
    warmup_all()
    return len(get_tool_schema().tools)


def _live_rc_token() -> str:
    """``rc420`` from ``0.9.0rc420`` — the stamp `Live at rcNNN:` must carry."""
    m = re.search(r"(rc\d+)$", srmech.__version__)
    assert m, (
        f"srmech.__version__ is {srmech.__version__!r}, which carries no rcN "
        f"suffix; the `Live at rcNNN:` stamps have no live value to key on. "
        f"On a clean (non-rc) release this gate needs re-pointing, not "
        f"deleting.")
    return m.group(1)


#: Only the words the notebook actually uses. Kept minimal on purpose — a
#: general number-word parser would start matching prose that is not a claim.
_WORD_CARDINAL = {"five": 5, "six": 6, "seven": 7, "ten": 10, "twenty": 20}
_WORD_ORDINAL = {"tenth": 10, "eleventh": 11, "twelfth": 12, "thirteenth": 13}


# ──────────────────────────────────────────────────────────────────────
# CLAIM PATTERNS — each anchored to a PRESENT-TENSE architecture sentence.
# ──────────────────────────────────────────────────────────────────────

#: §3.49.1 "partition **20 = 17 executable + 3 leaf**"
_PARTITION = re.compile(
    r"\*\*(\d+) = (\d+) executable \+ (\d+) leaf\*\*")

#: §3.28.2 the worked `describe()` literal in the rc10 bullet's live correction
_CATALOG_LITERAL = re.compile(
    r'\{"total":\s*(\d+),\s*"executable":\s*(\d+),\s*"leaf":\s*(\d+)\}')

#: §3.49.1 "The catalog's twenty descriptors partition"
_CATALOG_WORD = re.compile(r"The catalog's (\w+) descriptors")

#: §3.49.6 "carrying `{total, executable, leaf, status, run, enumerate}`"
_CATALOG_KEYS = re.compile(r"carrying \**`?\{([a-z,\s>]+)\}")

#: §3.49.6 "`describe()` gained a twelfth top-level key"
_DESCRIBE_ORDINAL = re.compile(r"`describe\(\)` gained a (\w+) top-level key")

#: §3.29.1 "are the **six Bird-Meertens recursion schemes**, matched 1:1 by
#: exactly six mutually-exclusive TOML stage-discriminators"
_BIRD_MEERTENS = re.compile(
    r"are the \*\*(\w+) Bird-Meertens recursion schemes\*\*, matched 1:1 by "
    r"exactly (\w+) mutually-exclusive TOML stage-discriminators")

#: §3.49.5 heading "The combinator kernel closes at six FORMS"
_CLOSES_AT = re.compile(r"The combinator kernel closes at (\w+) FORMS")

#: §3.29.6 + §3.49 admonition "**Combinator-6**"
_COMBINATOR_N = re.compile(r"\*\*Combinator-(\d+)\*\*")

#: §3.29.1 "total-by-construction at ~~five~~ **six** forms"
_TOTAL_BY_CONSTRUCTION = re.compile(
    r"total-by-construction at (?:~~\w+~~ )?\*\*(\w+)\*\* forms")

#: §3.28 "Live at rc420: … holds **598** entries" / "**Live at rc420: 20 …"
_LIVE_AT = re.compile(r"Live at (rc\d+)[:,]")

#: §3.28 the registry cardinal beside that stamp
_REGISTRY_CARDINAL = re.compile(r"holds \*\*(\d+)\*\* entries")


def _cardinal(word: str) -> int:
    if word.isdigit():
        return int(word)
    assert word.lower() in _WORD_CARDINAL, (
        f"the notebook now spells a gated cardinal as {word!r}, which this "
        f"gate cannot read. Add it to _WORD_CARDINAL; do not drop the "
        f"assertion.")
    return _WORD_CARDINAL[word.lower()]


# ══════════════════════════════════════════════════════════════════════
# 1. CASCADE CATALOG — the live `describe()["cascade_catalog"]`
# ══════════════════════════════════════════════════════════════════════

def test_catalog_partition_sentence_matches_describe() -> None:
    """§3.49.1's `20 = 17 executable + 3 leaf` == the live catalog."""
    live = _live_catalog()
    m = _PARTITION.search(_live_prose())
    assert m, (
        "no '**N = M executable + K leaf**' partition sentence found in the "
        "notebook — §3.49.1 was rephrased and this gate has stopped "
        "observing. Re-point the regex; do not delete the assertion.")
    total, ex, leaf = (int(g) for g in m.groups())
    assert (total, ex, leaf) == (live["total"], live["executable"],
                                 live["leaf"]), (
        f"the notebook says the catalog partitions {total} = {ex} executable "
        f"+ {leaf} leaf; describe()['cascade_catalog'] reports "
        f"{live['total']} = {live['executable']} + {live['leaf']}. §3.49.6 "
        f"says outright that the live count is the SSoT and the prose defers "
        f"to it — so the prose is what moves.")
    assert total == ex + leaf, (
        f"the notebook's own partition does not add up: {ex} + {leaf} != "
        f"{total}. There is no third state (§3.49.1).")


def test_catalog_worked_describe_literal_is_current() -> None:
    """A worked `describe()` literal is OUTPUT, not narrative.

    §3.28.2's rc10 bullet carries `describe()["cascade_catalog"] == {...}`
    inside its live-correction parenthetical. A wrong value there is a
    fabricated result, not a stale citation — the same reading
    ``test_readme_currency_rc419`` applies to the worked ``native_status()``
    transcript.
    """
    live = _live_catalog()
    m = _CATALOG_LITERAL.search(_live_prose())
    assert m, ("the worked describe()['cascade_catalog'] literal is no longer "
               "in the notebook")
    total, ex, leaf = (int(g) for g in m.groups())
    assert (total, ex, leaf) == (live["total"], live["executable"],
                                 live["leaf"]), (
        f"the worked literal prints total={total}, executable={ex}, "
        f"leaf={leaf}; the live describe() reports {live['total']}/"
        f"{live['executable']}/{live['leaf']}.")


def test_catalog_descriptor_word_cardinal_is_current() -> None:
    """"The catalog's **twenty** descriptors" — the spelled-out twin.

    The staleness this gate was built for was a spelled-out one: the subtree
    ``CLAUDE.md`` said "10 TOML descriptors" while the catalog held 20, a
    factor-of-two drift that survived because no gate reads number-words.
    """
    m = _CATALOG_WORD.search(_live_prose())
    assert m, "the 'The catalog's <N> descriptors' sentence has been rephrased"
    assert _cardinal(m.group(1)) == _live_catalog()["total"], (
        f"the notebook spells the catalog {m.group(1)!r} descriptors; the live "
        f"total is {_live_catalog()['total']}.")


def test_catalog_describe_key_set_is_current() -> None:
    """§3.49.6's key list == the live `cascade_catalog` keys, as a SET."""
    m = _CATALOG_KEYS.search(_live_prose())
    assert m, ("§3.49.6 no longer lists the cascade_catalog key set — the "
               "sentence 'carrying {total, executable, leaf, ...}' was "
               "rephrased.")
    claimed = {k.strip() for k in m.group(1).replace("\n", " ")
               .replace(">", " ").split(",") if k.strip()}
    assert claimed == set(_live_catalog()), (
        f"§3.49.6 says describe()['cascade_catalog'] carries {sorted(claimed)}; "
        f"it actually carries {sorted(_live_catalog())}.")


def test_describe_top_level_key_ordinal_is_current() -> None:
    """"gained a **twelfth** top-level key" == `len(describe())`."""
    m = _DESCRIBE_ORDINAL.search(_live_prose())
    assert m, "the 'describe() gained a <Nth> top-level key' claim is gone"
    word = m.group(1).lower()
    assert word in _WORD_ORDINAL, (
        f"the notebook spells the describe() key ordinal {word!r}; add it to "
        f"_WORD_ORDINAL rather than dropping the check.")
    assert _WORD_ORDINAL[word] == len(srmech.describe()), (
        f"the notebook calls cascade_catalog the {word} top-level key of "
        f"describe(); describe() has {len(srmech.describe())} top-level keys "
        f"({sorted(srmech.describe())}).")


# ══════════════════════════════════════════════════════════════════════
# 2. COMBINATOR KERNEL — the live `len(KERNEL_BUILDERS)`
# ══════════════════════════════════════════════════════════════════════

def _combinator_claims(text: str) -> "list[tuple[str, int]]":
    """Every PRESENT-TENSE combinator cardinal in the notebook, as (site, n).

    Callers pass :func:`_live_prose`, not :func:`_text`, and the difference is
    not cosmetic — it was this gate's first red. §3.29.1 keeps the superseded
    FIVE-form sentence three lines above the corrected SIX-form one, struck
    through, *"because the falsification trail is the evidence that the design
    worked"*. A ``re.search`` over the raw file finds the struck one first and
    reports the notebook stale when it is current. Removing struck runs is the
    principled fix rather than a regex tightened to dodge one sentence:
    strikethrough is the notebook's own DATED marker, and the struck text
    stays protected verbatim by
    :func:`test_dated_claims_are_present_verbatim_and_are_never_rewritten`.
    """
    out: "list[tuple[str, int]]" = []
    m = _BIRD_MEERTENS.search(text)
    if m:
        out.append(("§3.29.1 Bird-Meertens schemes", _cardinal(m.group(1))))
        out.append(("§3.29.1 TOML discriminators", _cardinal(m.group(2))))
    m = _CLOSES_AT.search(text)
    if m:
        out.append(("§3.49.5 heading", _cardinal(m.group(1))))
    m = _TOTAL_BY_CONSTRUCTION.search(text)
    if m:
        out.append(("§3.29.1 total-by-construction", _cardinal(m.group(1))))
    for m in _COMBINATOR_N.finditer(text):
        out.append(("Combinator-N label", int(m.group(1))))
    return out


def test_combinator_cardinals_match_the_live_kernel() -> None:
    """Every present-tense "the kernel is N" claim == `len(KERNEL_BUILDERS)`."""
    live = len(KERNEL_BUILDERS)
    claims = _combinator_claims(_live_prose())
    assert len(claims) >= 5, (
        f"only {len(claims)} combinator cardinal(s) located in the notebook "
        f"(expected the five §3.29.1 / §3.29.6 / §3.49 sites). The prose was "
        f"rephrased and this gate has partly stopped observing: "
        f"{[c[0] for c in claims]}")
    wrong = [(site, n) for site, n in claims if n != live]
    assert not wrong, (
        f"the notebook states a combinator cardinal that is not the live "
        f"kernel size {live} (= len(KERNEL_BUILDERS), the closure ratchet's "
        f"own set): {wrong}. The kernel moved 5 -> 6 at rc420 and a seventh "
        f"form would be another CONSCIOUS widening — so if this is red, the "
        f"question is which of the two moved.")


def test_the_notebook_does_not_contradict_itself_about_the_combinator_count(
) -> None:
    """INTERNAL CONSISTENCY — an independent failure from staleness.

    The notebook asserts the combinator cardinal at five separate sites in
    three sections. A reader with no access to the source can catch a
    disagreement between them, which is what makes it its own defect rather
    than a symptom of the source check above — the rc418 README shape, where
    the header said ABI 10 and the bump sentence said 12 -> 13.
    """
    claims = _combinator_claims(_live_prose())
    distinct = {n for _, n in claims}
    assert len(distinct) == 1, (
        f"the notebook contradicts itself about how many combinator forms the "
        f"kernel has: {sorted(claims)}. All sites must agree with each other "
        f"before any of them is compared to the source.")


def test_the_notebook_does_not_contradict_itself_about_the_catalog() -> None:
    """The partition sentence and the worked literal must agree with each
    other, source or no source."""
    text = _text()
    a = _PARTITION.search(text)
    b = _CATALOG_LITERAL.search(text)
    assert a and b, (
        "the notebook no longer carries BOTH the '20 = 17 executable + 3 "
        "leaf' partition sentence and the worked describe() literal; one of "
        "the two surfaces this test compares has been rephrased away.")
    assert tuple(int(g) for g in a.groups()) == tuple(
        int(g) for g in b.groups()), (
        f"§3.49.1 says {a.group(0)} while §3.28.2's worked literal says "
        f"{b.group(0)} — the notebook disagrees with itself.")


# ══════════════════════════════════════════════════════════════════════
# 3. REGISTRY CARDINAL + the `Live at rcNNN` stamps
# ══════════════════════════════════════════════════════════════════════

def test_registry_cardinal_matches_the_live_registry() -> None:
    """§3.28's "holds **598** entries" == `len(get_tool_schema().tools)`.

    The sentence names that exact expression, so the gate resolves that exact
    expression rather than a convenient neighbour.
    """
    m = _REGISTRY_CARDINAL.search(_live_prose())
    assert m, ("§3.28's 'holds **N** entries' live-registry correction is "
               "gone — it was added at rc420 precisely because the sibling "
               "'~87 entries' had been dated since v0.4.0.")
    assert int(m.group(1)) == _live_op_count(), (
        f"the notebook says the registry holds {m.group(1)} entries; "
        f"len(get_tool_schema().tools) is {_live_op_count()}.")


def test_live_at_rc_stamps_name_the_pinned_release() -> None:
    """`Live at rcNNN:` is a LIVE claim wearing a timestamp.

    Moving the stamp when the value is re-verified is correct practice, not
    fabricated history — which is exactly what separates this form from the
    dated ledger entries defended below. Pinning it means the number and its
    stamp can only move together.
    """
    live_rc = _live_rc_token()
    stamps = sorted({m.group(1) for m in _LIVE_AT.finditer(_live_prose())})
    assert stamps, (
        "no `Live at rcNNN:` currency stamp found in the notebook. Two were "
        "added at rc420 (the registry cardinal in §3.28 and the descriptor "
        "count in §3.28.2's rc10 bullet); losing them means the dated ledger "
        "entries beside them no longer carry a live counterweight.")
    assert stamps == [live_rc], (
        f"the notebook carries `Live at ...` stamp(s) {stamps} but the pinned "
        f"tree is {srmech.__version__} ({live_rc}). A `Live at` sentence "
        f"asserts a CURRENT value; re-verify it and move the stamp, or "
        f"demote the sentence to a dated ledger entry — do not leave it "
        f"claiming to be live at a release that is no longer HEAD.")


# ══════════════════════════════════════════════════════════════════════
# 4. FENCED CODE BLOCKS — STRICT ZERO. A block is presented as runnable.
# ══════════════════════════════════════════════════════════════════════

_FROM_IMPORT = re.compile(
    r"^\s*from\s+(srmech(?:\.[A-Za-z_][A-Za-z0-9_]*)*)\s+import\s+(.*)$")
_PLAIN_IMPORT = re.compile(
    r"^\s*import\s+(srmech(?:\.[A-Za-z_][A-Za-z0-9_]*)*)")
_DOTTED_IN_CODE = re.compile(r"\bsrmech(?:\.[A-Za-z_][A-Za-z0-9_]*)+")

#: §3.0's pre-schema YAML sketch. These four have never existed; the notebook
#: says so one line below. The exemption is CONDITIONAL on that sentence — see
#: :func:`test_the_pre_schema_sketch_carveout_is_still_declared`.
_SKETCH_DISCLAIMER = "The schema is not committed yet"
_SKETCH_PATHS = frozenset({
    "srmech.transforms.dct2_2d",
    "srmech.transforms.dct3_2d",
    "srmech.kernels.heat_decay",
    "srmech.lattices.dirichlet_2d",
})


def _fenced_blocks(text: str) -> "list[list[tuple[int, str]]]":
    """The notebook's fenced blocks, as lists of (1-based lineno, line)."""
    blocks: "list[list[tuple[int, str]]]" = []
    cur: "list[tuple[int, str]] | None" = None
    for i, line in enumerate(text.split("\n"), 1):
        s = line.strip()
        if cur is None:
            if s.startswith("```"):
                cur = []
        elif s.startswith("```") and set(s) == {"`"}:
            blocks.append(cur)
            cur = None
        else:
            cur.append((i, line))
    if cur is not None:
        blocks.append(cur)
    return blocks


def _import_statements(text: str) -> "list[tuple[int, str, list[str]]]":
    """(lineno, module, [imported names]) for every srmech import in a block.

    Multi-line ``from x import (a, b,`` continuations are joined, because the
    notebook writes them that way and a line-at-a-time reader would silently
    check only the first name — a gate that observes less than it claims.
    """
    out: "list[tuple[int, str, list[str]]]" = []
    for body in _fenced_blocks(text):
        i, n = 0, len(body)
        while i < n:
            lineno, line = body[i]
            m = _FROM_IMPORT.match(line)
            if m:
                rest, j = m.group(2), i
                while (rest.count("(") > rest.count(")")
                       or rest.rstrip().endswith("\\")) and j + 1 < n:
                    j += 1
                    rest = (rest.rstrip().rstrip("\\") + " "
                            + body[j][1].strip())
                flat = rest.replace("(", " ").replace(")", " ")
                names = [x.strip().split(" as ")[0].strip()
                         for x in flat.split(",")]
                out.append((lineno, m.group(1),
                            [x for x in names if x and x != "*"]))
                i = j + 1
                continue
            m = _PLAIN_IMPORT.match(line)
            if m:
                out.append((lineno, m.group(1), []))
            i += 1
    return out


def _resolves(dotted: str) -> bool:
    """Longest importable module prefix, then attribute-walk the remainder."""
    parts = dotted.split(".")
    mod, idx = None, 0
    for k in range(len(parts), 0, -1):
        try:
            mod = importlib.import_module(".".join(parts[:k]))
            idx = k
            break
        except Exception:
            continue
    if mod is None:
        return False
    obj = mod
    for p in parts[idx:]:
        if not hasattr(obj, p):
            return False
        obj = getattr(obj, p)
    return True


def test_every_srmech_import_in_a_fenced_block_resolves() -> None:
    """STRICT ZERO. Ten of these were dead at the rc419 tree.

    Module AND every imported name — because ``from srmech.cascade import
    sedenion_zero_divisor_witness`` imports a module that exists and a name
    that does not, and a module-only check would call that green.
    """
    stmts = _import_statements(_text())
    assert len(stmts) >= 20, (
        f"only {len(stmts)} srmech import statements found in the notebook's "
        f"fenced blocks (§3.45 alone carries ~20). The block scanner has "
        f"stopped observing — a gate that reads nothing passes everything.")
    broken: "list[str]" = []
    for lineno, module, names in stmts:
        try:
            mod = importlib.import_module(module)
        except Exception as exc:
            broken.append(f"  line {lineno}: import {module} -> "
                          f"{type(exc).__name__}: {exc}")
            continue
        for name in names:
            if hasattr(mod, name):
                continue
            try:
                importlib.import_module(f"{module}.{name}")
            except Exception:
                broken.append(
                    f"  line {lineno}: from {module} import {name} -> no such "
                    f"attribute or submodule")
    assert not broken, (
        "dead import(s) in the notebook's fenced code blocks:\n"
        + "\n".join(broken)
        + "\n\nA fenced block is presented as runnable, so this is strict "
          "zero. If the path MOVED, correct it and record the move (the "
          "§3.45 banner is the pattern); if the op was REMOVED, say so — do "
          "not leave a reader to conclude the capability is absent.")


def test_every_srmech_dotted_path_in_a_fenced_block_resolves() -> None:
    """STRICT ZERO, wider than the import check: attribute chains too.

    ``cd.is_division_algebra_dim`` style usage and bare ``srmech.x.y``
    references inside a block are equally presented as runnable.
    """
    text = _text()
    seen: "dict[str, list[int]]" = {}
    for body in _fenced_blocks(text):
        for lineno, line in body:
            for m in _DOTTED_IN_CODE.finditer(line):
                seen.setdefault(m.group(0), []).append(lineno)
    assert len(seen) >= 15, (
        f"only {len(seen)} distinct srmech.* paths found across the "
        f"notebook's fenced blocks — the scanner has stopped observing.")
    sketch_ok = _SKETCH_DISCLAIMER in text
    bad = []
    for dotted in sorted(seen):
        if _resolves(dotted):
            continue
        if sketch_ok and dotted in _SKETCH_PATHS:
            continue
        bad.append(f"  {dotted}  (lines {sorted(set(seen[dotted]))})")
    assert not bad, (
        "unresolvable srmech.* path(s) in the notebook's fenced blocks:\n"
        + "\n".join(bad))


def test_the_pre_schema_sketch_carveout_is_still_declared() -> None:
    """The §3.0 carve-out is conditional, and this is the condition.

    The four sketch paths are exempt ONLY while the notebook says the schema
    is uncommitted. If §3.0's YAML is ever promoted to a real descriptor
    format, that sentence goes and the paths become gated like everything
    else — the exemption cannot outlive its justification.
    """
    text = _text()
    if _SKETCH_DISCLAIMER not in text:
        unresolved = sorted(p for p in _SKETCH_PATHS if not _resolves(p))
        assert not unresolved, (
            f"the notebook no longer says {_SKETCH_DISCLAIMER!r}, so §3.0's "
            f"YAML is being presented as a committed schema — but these paths "
            f"still do not resolve: {unresolved}.")
        return
    live = sorted(p for p in _SKETCH_PATHS if _resolves(p))
    assert not live, (
        f"§3.0 still calls itself a pre-schema sketch, but {live} now "
        f"resolve. Shrink _SKETCH_PATHS to what is genuinely unbuilt — an "
        f"exemption covering a live path hides real drift.")


# ══════════════════════════════════════════════════════════════════════
# 5. PROSE MODULE NAMES — down-only CEIL on the residual
# ══════════════════════════════════════════════════════════════════════

#: A banner declaring a whole subsection's paths dated. The in-tree pattern —
#: the §3.28 and §3.45 blockquotes both use it — is to name the live prefix in
#: the banner and leave the rows as the release record they are.
_BANNER = re.compile(
    r"PATH CURRENCY|AS-SHIPPED-THEN, not as-importable-now", re.I)
_HEADING = re.compile(r"^#{2,6} ")

#: A line that marks its own path dead, or declares itself a dated record.
#: These are DECIDABLE from the line alone, which is why they are rules and
#: not an allowlist.
_MARKED = re.compile(
    r"REMOVED|RETIRED|ModuleNotFoundError|no longer exist|SUPERSEDED|"
    r"WISHLIST|does not exist|is dead|dead too|stale|"
    r"as-of|as-of-rc|it STAYS|dated rather than bumped|"
    r"still says|would ship a call", re.I)

_CODE_SPAN = re.compile(r"`([^`\n]+)`")
_DOTTED_TOK = re.compile(r"^srmech(?:\.[A-Za-z_][A-Za-z0-9_]*)+$")

#: MEASURED on the rc420 integration branch, after this gate's own first run
#: found and fixed the ELEVENTH. Every survivor is a dated narrative naming a
#: path that has since moved — a v0.4.0 Phase-C1 table row (763 · 771 · 838),
#: a verdict-ledger row (1729), a v0.5.0 release bullet (5437 · 5532), a §3.30
#: / §3.42–§3.43 spike record (5818 · 6394 · 6414 · 6426). They are NOT
#: defects; they are the pre-convention residual, and the only correct fix is
#: the in-tree PATH CURRENCY banner applied section by section — never a batch
#: rewrite, which would fabricate history at scale.
#:
#: The one that LEFT is the shape this check exists for: §3.8.3:844 said the
#: composition engine *"lives at `srmech.amsc.compose`"* — present tense, a
#: live-architecture claim, and dead since ADR-0010. §3.29.1 already carried
#: the identical correction; nothing had ever compared the two. DOWN ONLY.
_PROSE_DEAD_PATH_CEIL = 10


def _prose_lines(text: str) -> "list[tuple[int, str]]":
    """Notebook lines OUTSIDE fenced blocks, with blockquote runs joined.

    A `>` blockquote is one paragraph; the §3.45 banner wraps its
    `srmech.amsc.poly` -> **srmech.math.poly** mapping across a line break, and
    a line-at-a-time reader would see the dead half without the arrow that
    marks it dead.
    """
    out: "list[tuple[int, str]]" = []
    inblock = False
    pending: "tuple[int, list[str]] | None" = None
    for i, line in enumerate(text.split("\n"), 1):
        s = line.strip()
        if s.startswith("```"):
            inblock = not inblock
            continue
        if inblock:
            continue
        if s.startswith(">"):
            if pending is None:
                pending = (i, [])
            pending[1].append(s)
            continue
        if pending is not None:
            out.append((pending[0], " ".join(pending[1])))
            pending = None
        out.append((i, line))
    if pending is not None:
        out.append((pending[0], " ".join(pending[1])))
    return out


def _banner_spans(text: str) -> "list[tuple[int, int]]":
    """(start, end) line ranges governed by a path-currency banner."""
    lines = text.split("\n")
    spans = []
    for i, line in enumerate(lines, 1):
        if _BANNER.search(line):
            j = i + 1
            while j <= len(lines) and not _HEADING.match(lines[j - 1]):
                j += 1
            spans.append((i, j))
    return spans


def _prose_dead_paths(text: str) -> "list[tuple[int, str, str]]":
    """Dead `srmech.*` code spans in prose that no structural rule excuses."""
    spans = _banner_spans(text)
    residual = []
    for lineno, line in _prose_lines(text):
        toks = [m.group(1).strip() for m in _CODE_SPAN.finditer(line)]
        dead = [t for t in toks if _DOTTED_TOK.match(t) and not _resolves(t)]
        if not dead:
            continue
        live_here = [t for t in toks if _DOTTED_TOK.match(t) and _resolves(t)]
        for tok in dead:
            if any(a <= lineno < b for a, b in spans):
                continue                       # covered by a currency banner
            if f"~~`{tok}`" in line or f"~~{tok}~~" in line:
                continue                       # struck through
            if _MARKED.search(line):
                continue                       # marked dead / self-declared dated
            if line.lstrip().startswith("|") and live_here:
                continue                       # an old -> new mapping table row
            residual.append((lineno, tok, line.strip()[:150]))
    return residual


def test_dead_module_paths_in_prose_stay_on_a_down_only_ceiling() -> None:
    """A dead path NAMED AS DEAD is correct prose; the rest is residual.

    Strict zero is wrong here and the reason is the same one that shaped
    ``test_ref_notation_emitted_rc348``: the decidable class gets strict zero
    (fenced blocks, above), and the pre-convention residual gets a ceiling
    that only ever goes DOWN. Every entry is a dated narrative whose correct
    fix is the in-tree banner pattern, applied a section at a time — not a
    batch rewrite, which would fabricate history at scale.
    """
    residual = _prose_dead_paths(_text())
    assert len(residual) <= _PROSE_DEAD_PATH_CEIL, (
        f"{len(residual)} dead srmech.* module path(s) in notebook prose, "
        f"ceiling {_PROSE_DEAD_PATH_CEIL}:\n"
        + "\n".join(f"  line {ln}: {tok}\n      {ctx}"
                    for ln, tok, ctx in residual)
        + "\n\nEither mark the path dead where it is written, or cover the "
          "subsection with a PATH CURRENCY banner naming the live prefix.")


def test_the_prose_ceiling_is_not_slack() -> None:
    """A ceiling far above the count is a ratchet that ratchets nothing."""
    residual = _prose_dead_paths(_text())
    assert len(residual) >= _PROSE_DEAD_PATH_CEIL - 2, (
        f"the prose residual has drained to {len(residual)} against a ceiling "
        f"of {_PROSE_DEAD_PATH_CEIL}. Lower the ceiling to "
        f"{len(residual)} in the same commit — that is what makes it "
        f"down-only rather than decorative.")


# ══════════════════════════════════════════════════════════════════════
# 6. ★ THE DATED-CLAIM ALLOWLIST — a POSITIVE guard, not a hole
# ══════════════════════════════════════════════════════════════════════

#: (verbatim string, why it must never be rewritten). Each is a record of a
#: PAST state. Asserting presence — rather than merely exempting the number —
#: is what makes this an instrument: a currency sweep that "fixes" one of
#: these to today's value goes RED here, which is the correct outcome, because
#: fabricating history is a worse defect than a stale cardinal.
#: The count is not decoration. A presence check on this list was MEASURED to
#: be a false green: ``describe()`` stays 178`` appears FOUR times (the
#: rc11/rc12/rc13/rc14 ledger bullets), so ``claim in text`` still holds after
#: three of the four have been "fixed" to 598 — this gate's own mutation run
#: rewrote one and reported 20 passed.
#: ``[[feedback_an_instrument_that_cannot_return_otherwise_is_not_a_measurement]]``
#: — an instrument that cannot tell 4 from 3 is not measuring what it names.
_DATED_CLAIMS = (
    ("`describe()` stays 178", 4,
     "the v0.6.0-line per-rc ledger (rc11/rc12/rc13/rc14). The registry is at "
     "598 today; bumping these would erase the record of what each voxel "
     "added. FOUR copies -- the count is the whole point of this row."),
    ("**as-of-the-v0.6.0-line, and it STAYS at 178 here**", 1,
     "§3.28.3 states the dated-claim discipline in the notebook's own voice — "
     "'stated so the next reader does not fix it'."),
    ('The "10" is **as-of-rc10** and STAYS', 1,
     "the rc10 descriptor count. The live value is carried beside it as a "
     "`Live at rcNNN` correction, which is the shape this whole gate "
     "defends: date the record, pin the live value separately."),
    ("registers ~87 entries", 1,
     "the v0.4.0 tool-schema cardinal, explicitly labelled As-of-v0.4.0."),
    ("**ABI version: 3** throughout the v0.6.0 line", 1,
     "the ABI is 13 today; 'throughout the v0.6.0 line' scopes the claim in "
     "its own words."),
    ("was FIVE through rc419", 1,
     "the combinator kernel's pre-widening size. The falsification trail IS "
     "the evidence that the closure ratchet worked."),
    ("run against 0.9.0rc420, registry 598", 1,
     "a measurement-provenance stamp. The committed NDJSON under notes/ "
     "carries the same stamp in its `env` record, so bumping the prose would "
     "decouple the claim from the artifact that proves it."),
    ("MEASURED at v0.9.0rc420", 1,
     "a measurement stamp on the moved-paths table."),
)


def test_dated_claims_are_present_verbatim_and_are_never_rewritten() -> None:
    """★ The carve-out, inverted into a guard.

    ``test_readme_currency_rc419`` states the principle — *"editing a dated
    claim to today's value would fabricate history, which is a worse defect
    than the stale cardinal"* — and leaves those claims alone. The notebook is
    largely dated ledgers, so leaving them alone is not enough: something has
    to notice when a well-meaning currency pass rewrites one. This does.
    """
    text = _text()
    wrong = [(claim, n, text.count(claim), why)
             for claim, n, why in _DATED_CLAIMS if text.count(claim) != n]
    assert not wrong, (
        "dated claim(s) rewritten or dropped in the notebook:\n"
        + "\n".join(f"  {claim!r}\n      expected {n} occurrence(s), found "
                    f"{got}\n      protected because: {why}"
                    for claim, n, got, why in wrong)
        + "\n\nIf one of these was rewritten to a current value, REVERT it: a "
          "per-rc ledger entry records what was true THEN. If the surrounding "
          "prose was legitimately restructured, re-point this list in the "
          "same commit and say which claim moved where.")


def test_the_dated_claims_are_actually_stale_or_the_carveout_is_vacuous(
) -> None:
    """A carve-out protecting values that happen to be CURRENT proves nothing.

    ``[[feedback_an_instrument_that_cannot_return_otherwise_is_not_a_
    measurement]]``: if 178 ever equalled the live registry, this list would
    be defending nothing and the reader could not tell.
    """
    live_ops = _live_op_count()
    assert live_ops != 178, (
        "the live registry is now 178, so the protected `describe() stays "
        "178` ledger entries no longer demonstrate the dated/live "
        "distinction. Re-point this check at a claim that is still stale.")
    assert len(KERNEL_BUILDERS) != 5, (
        "the combinator kernel is back to five, so 'was FIVE through rc419' "
        "is no longer a dated claim. Re-point.")


# ══════════════════════════════════════════════════════════════════════
# 7. RETRO-CHECK — a gate that would not have caught the defect that
#    motivated it is not the gate.
# ══════════════════════════════════════════════════════════════════════

#: Verbatim rc419 text, reproduced rather than described, so this fails if a
#: predicate is ever loosened past the point where the original defect slips.
_RC419_COMBINATOR = (
    "The cascade DSL's control-flow combinators — `then` (apply) / `loop` "
    "(bounded iterate) / `fold` (catamorphism-with-seed) / `reduce` "
    "(catamorphism) / `parallel` (Klein-4 map-fan-out) — are the **five "
    "Bird-Meertens recursion schemes**, matched 1:1 by exactly five "
    "mutually-exclusive TOML stage-discriminators."
)

#: The ten dead §3.45 imports as they stood at rc419, verbatim.
_RC419_DEAD_IMPORTS = """```python
from srmech.qm.gauge import (su3_generators, su3_gell_mann_matrices)
from srmech.qm.sm import electroweak_summary, ckm_matrix
from srmech.qm.so8 import g2_subalgebra, so8_adjoint_basis
from srmech.qm.triality import triality_automorphism
from srmech.amsc.cascade import cd_basis_product, cd_navmap
from srmech.amsc.cascade.matrix_cascades import einsum
from srmech.amsc.cascade import is_division_algebra_dim
from srmech.amsc.cascade import autocorrelation, top_k_by_score
from srmech.amsc.poly import poly_from_coeffs
from srmech.amsc.qmat import QMat
```"""


def test_the_gate_would_have_fired_on_the_rc419_combinator_sentence() -> None:
    """The five-form sentence, run through the SHIPPED predicate."""
    m = _BIRD_MEERTENS.search(_RC419_COMBINATOR)
    assert m, ("the Bird-Meertens regex no longer matches the rc419 wording, "
               "so the retro-check has stopped demonstrating anything")
    assert _cardinal(m.group(1)) == 5 and _cardinal(m.group(2)) == 5
    assert _cardinal(m.group(1)) != len(KERNEL_BUILDERS), (
        "the live kernel is back to five; re-point this retro-check at the "
        "historical value.")


def test_the_gate_would_have_fired_on_the_rc419_dead_imports() -> None:
    """All ten §3.45 imports, run through the SHIPPED block+import scanner."""
    stmts = _import_statements(_RC419_DEAD_IMPORTS)
    assert len(stmts) == 10, (
        f"the fenced-block import scanner extracted {len(stmts)} of the 10 "
        f"rc419 statements — it has stopped observing the shape it was "
        f"written for.")
    dead = [mod for _, mod, _ in stmts if not _resolves(mod)]
    assert len(dead) == 10, (
        f"only {len(dead)} of the 10 rc419 imports read as dead against the "
        f"live tree: {sorted(set(m for _, m, _ in stmts) - set(dead))} now "
        f"resolve. If a path was restored, drop it from this fixture; do not "
        f"weaken the assertion.")


def test_the_notebook_is_reachable_at_all() -> None:
    """The whole file is vacuous if the notebook is not where it is expected.

    A gate keyed on a path that does not exist reports green forever — the
    false-green shape every ratchet in this suite is written to refuse.
    """
    assert _NOTEBOOK.is_file(), f"notebook not found at {_NOTEBOOK}"
    assert len(_text()) > 100_000, (
        f"{_NOTEBOOK} is only {len(_text())} bytes — that is not the SSoT "
        f"notebook and every assertion above is measuring the wrong file.")
