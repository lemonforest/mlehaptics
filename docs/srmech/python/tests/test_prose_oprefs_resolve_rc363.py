"""rc363 (`#T1045`) — every dotted ``srmech.*`` path cited in ToolEntry PROSE
must resolve. The silent half of the introspect surface's op-references.

The gap
=======
`#T930` (``tests/test_class_catalog_oprefs_resolve_930.py``) closed exactly this
question for the packaged ``[class]`` TOML descriptors: each method binds an op
by fully-qualified string, nothing asserted those strings still resolve, and a
rename left the binding orphaned while every other test stayed green. 31 op-refs,
strict-zero, renamed-orphan = red build.

The tool schema has the same shape and, until this rc, none of the guard.
Measured on the rc362 tree, ``srmech.amsc.*`` citations across the introspect
surface split in two:

======================================  =======  ====  ====================
field                                   refs     ops   fails…
======================================  =======  ====  ====================
``example``                             563      341  **loudly** — ``test_worked_examples_execute_rc354`` RUNS these
``summary`` + ``explanation``           **251**  151  **silently** — nothing reads prose
======================================  =======  ====  ====================

``example`` is deliberately **out of scope here**: execution is a strictly
stronger check than resolution, and duplicating it would add cost with no
detection. This gate takes the silent half.

Why it matters beyond tidiness: ADR-0010 (namespace declustering) plans module
MOVES. A move that leaves a stale citation behind produces an introspect payload
that *reads* correct — a plausible dotted path, in prose, next to a real op — and
sends a reader or an agent to a module that no longer exists. ADR-0012 §3 sets
the bar at autonomous composition and says **INCOMPLETE IS AS BAD AS FALSE**; a
wrong path is worse than either. After this gate, a module move cannot leave a
stale citation behind.

The resolution rule, stated
===========================
A dotted path is **RESOLVABLE** iff, taking the LONGEST importable module prefix
and walking the remaining segments with ``getattr``, every segment exists. So
both of these count, and the gate deliberately does not distinguish them:

* ``srmech.math.laplacian`` — a MODULE (135 occurrences tree-wide is the largest
  single citation). A module path is a real reference: ADR-0010 moves modules,
  and a citation of a module that no longer exists is exactly as broken as a
  citation of an op that no longer exists.
* ``srmech.math.laplacian.mat_matmul`` — a module attribute (an op, a class, a
  constant). Deep chains resolve too: ``srmech.math.qmat.QMat.rank`` walks the
  class.

Two extractions are **excluded by rule**, not by allowlist:

* **A filename.** ``srmech.h`` is the C public header, cited 24 times, and is not
  a Python path at all. A two-segment path whose tail is a known source/artifact
  extension is a filename.
* **A wildcard tail.** ``srmech.physics.qm.*`` is a family reference; it is truncated at
  the ``*`` and the remaining module prefix is what gets resolved.

The CLASS-ROOTED extraction (rc407, `#T1076`)
=============================================
The extraction above is anchored at the literal token ``srmech`` — every
candidate must BEGIN there. A reference written the way prose actually writes
it, ``QMat.nullspace``, is therefore never even a candidate, and the
fully-qualified ``srmech.math.qmat.QMat.nullspace`` occurs **0** times in the
tree. So the rc363 gate shipped green at 206 passed while **88 class-rooted
references went ungated**, and that blind spot is why two dead citations
shipped inside the wheel and the compiled C registry:

* ``One.to_numpy`` — a method DELETED in ``4aa75d64a`` — cited as live in
  ``srmech.cascade.the_one``'s summary, contradicting the tree's own
  ``test_no_to_numpy_attribute``;
* ``Mat.buffers`` — which resolves nowhere at all (the attribute is
  ``Mat.buffer``) — in ``srmech.math.laplacian.mat_solve``'s summary.

The class set is **enumerable, not an allowlist** — the same "excluded by rule"
discipline the filename and wildcard exclusions follow. It is derived at run
time: take ``describe()["carriers"]["capabilities"]``, keep the CamelCase keys
(the 6 lowercase ones — ``complex float int octonion quaternion sedenion`` —
are primitives, not classes), and resolve each to a class in ONE
``pkgutil.walk_packages`` sweep. Measured at rc407: 29 keys → 23 classes, all
resolving. Nothing is hand-listed, so a new carrier class is covered the day it
is published rather than the day someone remembers to add it here.

Measured at rc407: **34 distinct / 90 occurrences, 0 unresolved** after the
drains — so this extraction, like the one above, ships **STRICT-ZERO with no
CEIL**. Before the drains it read 35 / 90 with exactly the 2 failures above.
Largest: ``QMat.from_mat`` ×15, ``QMat.from_rows`` ×10, ``QMat.nullspace`` ×8.

**Known false-positive class, accepted.** ``Mat.buffers`` reads as an English
plural, and the drain there was a REWORD, not a rename — so the same shape will
recur. This risk is exactly symmetric with the ``srmech.*`` extraction (a plural
``srmech.foo.bars`` fails identically), and that one has shipped strict-zero at
0 failures since rc363. Strict-zero therefore remains correct; do NOT add a CEIL
to absorb it — write the prose so the reference is real.

What this gate cannot decide
============================
* **It cannot tell a RIGHT path from a merely EXISTING one.** ``srmech.math.hdc``
  resolves whether or not it is the module the sentence is about. Topicality is
  not decidable here — the same distinction the repo's issue-reference discipline
  draws for ``#NNNN``.
* **It does not read every prose surface in the tree.** Docstrings, the
  CHANGELOG, the ADRs and the notebooks are out of scope; this is the ToolEntry
  surface that ships in the wheel and in the compiled-in C registry.
* **``example`` is out of scope**, by the argument above.
* **A bare backticked member with NO class root is invisible to BOTH
  extractions.** The ``to_numpy()`` shape — a member named with no owner, as in
  "the float ``to_matrix()`` / ``to_numpy()`` realisations" — matches neither
  ``\\bsrmech\\.`` nor ``<Class>.``, because there is nothing to resolve it
  against: the same token may be a live method on one class and deleted from
  another. That residual is closed for this one name by
  ``test_mat_carrier_rc69.py::test_no_to_numpy_in_registry_prose``, a
  token-level guard justified by the sibling assertion in that file declaring
  the name deleted tree-wide — NOT by this regex, which cannot be made to see
  it without inventing an owner.

Measured at rc363
=================
**462 occurrences of 199 distinct paths across 236 of 525 ops** in
``summary`` + ``explanation`` — 438 attribute references, 24 module references,
**0 unresolved**. The gate therefore ships **STRICT-ZERO with no CEIL**.

The other ToolEntry prose fields (``parameters[].summary``, ``returns.shape`` /
``returns.summary``) are covered too — 6 occurrences, of which **1 was a genuine
stale citation** found by this gate and fixed in the same rc:
``genome_register_attested``'s ``source`` example read ``'srmech.genome.<name>'``,
a module path that has never existed (the module is ``srmech.biology.genome``).

Pure stdlib + srmech; numpy-free; no ``abs()``.
"""

from __future__ import annotations

import importlib
import re
from typing import Dict, List, Optional, Set, Tuple

import pytest

from srmech.introspect.tool_schema import get_tool_schema, warmup_all

warmup_all()

#: A dotted path rooted at ``srmech``. ``*`` is admitted as a segment so a family
#: reference (``srmech.physics.qm.*``) is CAPTURED and then truncated, rather than
#: silently splitting into a shorter path that happens to resolve.
_DOTTED = re.compile(r"\bsrmech(?:\.(?:\*|[A-Za-z_][A-Za-z0-9_]*))+")

#: Tails that make a two-segment extraction a FILENAME rather than a module path.
#: ``srmech.h`` (the C public header) is the only one in the tree today; the set
#: is written out so the next artifact reference is excluded by the same rule
#: instead of by a new special case.
_FILE_SUFFIXES = frozenset({
    "h", "c", "py", "pyi", "so", "dll", "dylib", "a", "o",
    "toml", "json", "ndjson", "md", "txt", "cfg", "in", "yml", "yaml",
})

#: Tails that make a two-segment extraction a DOMAIN NAME rather than a module
#: path — the peer of ``_FILE_SUFFIXES`` above, and the same rule applied to the
#: other artifact class whose spelling collides with a dotted path.
#:
#: rc408 (`#T1078`): ``srmech.net`` IS the project's website (root ``CLAUDE.md``
#: §2: "PyPI; srmech.net forwards to repo"), and it is written into every
#: genome manifest as the DEFAULT ``source_url`` — so it appears in prose
#: legitimately, and will keep appearing: the whole point of the rc304
#: ``attestation=`` override is to let a caller replace that default with a real
#: source, which cannot be explained without naming it. A domain is
#: syntactically identical to a dotted module path, so the extractor cannot tell
#: them apart and reported ``srmech.net`` as an unresolvable citation. That is a
#: FALSE-POSITIVE CLASS in this gate, not a defect in the prose — the same shape
#: as ``srmech.h``, and fixed by the same mechanism rather than a special case.
#:
#: DELIBERATELY NARROW, in two ways that both matter:
#:   1. It fires ONLY on a TWO-SEGMENT extraction, exactly like ``_FILE_SUFFIXES``.
#:      ``srmech.net.foo`` is still resolved and still fails if dead, so the
#:      exclusion cannot be widened into cover for a real broken citation.
#:   2. ``io`` / ``dev`` / ``ai`` are TLDs but are DELIBERATELY ABSENT: each is a
#:      plausible srmech submodule name, and admitting them would blind the gate
#:      to a genuinely dead ``srmech.io.*``-rooted path. Only TLDs that could not
#:      credibly name a Python submodule of this package are listed.
_DOMAIN_SUFFIXES = frozenset({"net", "com", "org"})

#: The ToolEntry prose fields this gate reads. ``example`` is EXCLUDED — see the
#: module docstring: the rc354 execution gate runs those, which is strictly
#: stronger than resolving them.
_ENTRY_FIELDS = ("summary", "explanation")


def _normalise(raw: str) -> Optional[str]:
    """The dotted path a raw extraction denotes, or ``None`` when the extraction
    is not a Python path at all."""
    segs = raw.split(".")
    if len(segs) == 2 and segs[1] in _FILE_SUFFIXES:
        return None                      # `srmech.h` — a FILE
    if len(segs) == 2 and segs[1] in _DOMAIN_SUFFIXES:
        return None                      # `srmech.net` — a DOMAIN (the website)
    if "*" in segs:
        segs = segs[:segs.index("*")]
    if len(segs) < 2:
        return None                      # bare `srmech` / `srmech.*` — no target
    return ".".join(segs)


def _citations() -> Dict[str, Set[Tuple[str, str]]]:
    """``{dotted path: {(op name, field)}}`` over every prose surface in scope."""
    out: Dict[str, Set[Tuple[str, str]]] = {}
    for tool in get_tool_schema().tools:
        blobs: List[Tuple[str, str]] = [
            (field, getattr(tool, field, None) or "") for field in _ENTRY_FIELDS
        ]
        for param in tool.parameters:
            blobs.append((f"parameters.{param.name}.summary", param.summary or ""))
        if tool.returns is not None:
            blobs.append(("returns.shape",
                          getattr(tool.returns, "shape", "") or ""))
            blobs.append(("returns.summary",
                          getattr(tool.returns, "summary", "") or ""))
        for field, text in blobs:
            for match in _DOTTED.finditer(text):
                dotted = _normalise(match.group(0))
                if dotted is not None:
                    out.setdefault(dotted, set()).add((tool.name, field))
    return out


def _resolves(dotted: str) -> Optional[str]:
    """``"module"`` / ``"attr"`` when the path resolves, ``None`` when it does
    not. The longest importable module prefix wins, then ``getattr`` walks the
    remainder — so a class attribute (``…qmat.QMat.rank``) resolves as well as a
    module-level op."""
    segs = dotted.split(".")
    module = None
    depth = 0
    for i in range(len(segs), 0, -1):
        try:
            module = importlib.import_module(".".join(segs[:i]))
            depth = i
            break
        except Exception:  # noqa: BLE001 — a non-importable prefix is simply not it
            continue
    if module is None:
        return None
    if depth == len(segs):
        return "module"
    obj = module
    for seg in segs[depth:]:
        if not hasattr(obj, seg):
            return None
        obj = getattr(obj, seg)
    return "attr"


_CITATIONS = _citations()


# ── 0. the walk must SELECT ───────────────────────────────────────────────────

def test_the_prose_walk_finds_a_real_population() -> None:
    """A resolution gate over an empty citation set passes by observing nothing
    — the `#T935` lesson `#T930` records in its own words: *a guard that observes
    nothing is a guard that lies*. So the population is pinned first."""
    assert len(get_tool_schema().tools) > 500, "tool registry unexpectedly small"
    assert len(_CITATIONS) >= 150, (
        f"only {len(_CITATIONS)} distinct dotted srmech.* paths found in "
        f"ToolEntry prose — the walk is not seeing the citations")
    occurrences = sum(len(v) for v in _CITATIONS.values())
    assert occurrences >= 350, (
        f"only {occurrences} citation sites found — the walk is not seeing the "
        f"prose")
    ops = {op for sites in _CITATIONS.values() for op, _ in sites}
    assert len(ops) >= 150, (
        f"only {len(ops)} ops carry a dotted srmech.* citation — expected the "
        f"citation habit to be tree-wide")
    # Both resolution KINDS must be present, or the rule that admits module
    # paths is untested.
    kinds = {_resolves(p) for p in _CITATIONS}
    assert "module" in kinds and "attr" in kinds, (
        f"expected both module and attribute citations; got {kinds}")


def test_the_filename_rule_is_exercised_not_theoretical() -> None:
    """``srmech.h`` must actually appear in the prose, or the exclusion rule is
    dead code that would hide a future defect."""
    header_sites = sum(
        len(_DOTTED.findall(getattr(t, f, None) or ""))
        for t in get_tool_schema().tools for f in _ENTRY_FIELDS
    )
    raw_header = [
        m.group(0)
        for t in get_tool_schema().tools for f in _ENTRY_FIELDS
        for m in _DOTTED.finditer(getattr(t, f, None) or "")
        if m.group(0) == "srmech.h"
    ]
    assert header_sites > 0
    assert raw_header, (
        "no `srmech.h` citation found — the filename exclusion in _normalise is "
        "no longer exercised; drop it or find why the C header stopped being "
        "cited")
    assert _normalise("srmech.h") is None
    assert _normalise("srmech.physics.qm.*") == "srmech.physics.qm"
    assert _normalise("srmech.math.laplacian") == "srmech.math.laplacian"


def test_the_domain_rule_is_exercised_and_still_catches_dead_paths() -> None:
    """rc408 (`#T1078`) — the peer of the filename rule, with its COUNTERFACTUAL.

    An exclusion is only safe if it is (a) actually used and (b) narrow enough
    that it cannot swallow a real defect. Both are asserted here, because an
    exclusion that quietly widened would turn this whole gate green for the
    wrong reason — the failure mode a CEIL would have introduced, and the reason
    this was fixed as a decidable rule instead.
    """
    # (a) EXERCISED — `srmech.net` really is cited, so the rule is not dead code.
    #     Scanned over the SAME surfaces `_citations` walks (entry fields AND
    #     parameter summaries AND returns), not just the entry fields: the live
    #     citation is in genome_save's `attestation` PARAMETER summary, and a
    #     narrower scan here would have declared the rule dead while it was in use.
    raw_domain = []
    for t in get_tool_schema().tools:
        blobs = [getattr(t, f, None) or "" for f in _ENTRY_FIELDS]
        blobs += [p.summary or "" for p in t.parameters]
        if t.returns is not None:
            blobs.append(getattr(t.returns, "shape", "") or "")
            blobs.append(getattr(t.returns, "summary", "") or "")
        for text in blobs:
            raw_domain += [m.group(0) for m in _DOTTED.finditer(text)
                           if m.group(0) == "srmech.net"]
    assert raw_domain, (
        "no `srmech.net` citation found — the domain exclusion in _normalise is "
        "no longer exercised; drop it or find why the project website stopped "
        "being named in the attestation prose")
    assert _normalise("srmech.net") is None

    # (b) THE COUNTERFACTUAL, four ways. The rule must NOT have blunted the gate.
    #
    # 1. It is TWO-SEGMENT ONLY: a longer path that merely starts with the
    #    domain is still normalised, still resolved, and still dead.
    assert _normalise("srmech.net.foo") == "srmech.net.foo"
    assert _resolves("srmech.net.foo") is None

    # 2. A two-segment path whose tail is NOT a listed suffix is untouched.
    assert _normalise("srmech.nosuchmodule") == "srmech.nosuchmodule"
    assert _resolves("srmech.nosuchmodule") is None

    # 3. The rc407 DEFECT CLASS still fails — a real module, a dead attribute.
    #    `One.to_numpy` was deleted in 4aa75d64a and cited as live until rc407;
    #    its module-rooted spelling must still be unresolvable.
    assert _resolves("srmech.cascade.one.the_one") == "attr"   # the live peer
    assert _resolves("srmech.cascade.one.to_numpy") is None    # the dead one

    # 4. TLDs that could credibly name a submodule are NOT excluded, so a dead
    #    `srmech.io` / `srmech.dev` citation would still be caught.
    assert "io" not in _DOMAIN_SUFFIXES
    assert "dev" not in _DOMAIN_SUFFIXES
    assert _normalise("srmech.io") == "srmech.io"


# ── 1. THE GATE ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("dotted", sorted(_CITATIONS), ids=sorted(_CITATIONS))
def test_every_prose_oprefs_resolves(dotted: str) -> None:
    """**Strict-zero.** Every dotted ``srmech.*`` path cited in ToolEntry prose
    names an importable module or an attribute reachable from one.

    A rename or a module MOVE that forgets a citation fails here by name, which
    is what makes ADR-0010's decluster safe from the prose side."""
    assert _resolves(dotted) is not None, (
        f"the ToolEntry prose cites {dotted!r}, which no longer resolves to an "
        f"importable module or module attribute — cited at "
        f"{sorted(_CITATIONS[dotted])[:4]}. Update the prose (or restore the "
        f"path); a plausible-but-dead dotted path in a shipped introspect "
        f"payload sends a reader to a module that is not there."
    )


def test_no_unresolved_citation_anywhere() -> None:
    """The same assertion in aggregate, so a collection-time failure of the
    parametrisation cannot make the whole gate vanish silently."""
    dead = sorted(p for p in _CITATIONS if _resolves(p) is None)
    assert not dead, (
        f"{len(dead)} dotted srmech.* path(s) cited in ToolEntry prose do not "
        f"resolve: {dead}")


# ── 2. THE CLASS-ROOTED EXTRACTION (rc407, `#T1076`) ──────────────────────────
#
# See the module docstring. The `srmech.`-anchored extraction above cannot see
# `QMat.nullspace`, which is how `One.to_numpy` and `Mat.buffers` shipped.


def _carrier_classes() -> Dict[str, type]:
    """``{CamelCase name: class}`` for every published carrier capability.

    DERIVED, never hand-listed: the names come from
    ``describe()["carriers"]["capabilities"]`` and are resolved in ONE
    ``pkgutil.walk_packages`` sweep, so a newly-published carrier is gated the
    day it appears in ``describe()`` rather than the day someone edits this
    file. The lowercase keys (``complex``/``float``/``int``/``octonion``/
    ``quaternion``/``sedenion``) are primitive type names, not classes."""
    import pkgutil
    import inspect
    import srmech

    wanted = {
        k for k in srmech.describe()["carriers"]["capabilities"] if k[:1].isupper()
    }
    found: Dict[str, type] = {}
    for info in pkgutil.walk_packages(srmech.__path__, "srmech."):
        try:
            module = importlib.import_module(info.name)
        except Exception:  # noqa: BLE001 — an unimportable module is simply not it
            continue
        for name, obj in vars(module).items():
            if name in wanted and name not in found and inspect.isclass(obj):
                found[name] = obj
    return found


_CARRIER_CLASSES = _carrier_classes()

#: ``Q.numerator`` in prose, but NOT ``srmech.math.q.Q.numerator`` (the dotted
#: extraction above already owns that) and not ``self.Q.foo``. The negative
#: lookbehind on ``[\w.]`` enforces both.
_CLASS_ROOTED = {
    name: re.compile(r"(?<![\w.])" + name + r"\.([A-Za-z_]\w*)")
    for name in _CARRIER_CLASSES
}


def _class_citations() -> Dict[str, Set[Tuple[str, str]]]:
    """``{"Class.member": {(op name, field)}}`` over the same prose fields."""
    out: Dict[str, Set[Tuple[str, str]]] = {}
    for tool in get_tool_schema().tools:
        for field in _ENTRY_FIELDS:
            text = getattr(tool, field, None) or ""
            for name, pattern in _CLASS_ROOTED.items():
                for match in pattern.finditer(text):
                    ref = f"{name}.{match.group(1)}"
                    out.setdefault(ref, set()).add((tool.name, field))
    return out


_CLASS_CITATIONS = _class_citations()


def _class_ref_resolves(ref: str) -> bool:
    """``Class.member`` resolves iff ``member`` is reachable on the class."""
    cls_name, member = ref.split(".", 1)
    return hasattr(_CARRIER_CLASSES[cls_name], member)


def test_the_class_rooted_walk_finds_a_real_population() -> None:
    """A guard that observes nothing is a guard that lies — so pin the
    population before asserting anything about it."""
    assert len(_CARRIER_CLASSES) >= 20, (
        f"only {len(_CARRIER_CLASSES)} carrier classes resolved from "
        f"describe()['carriers']['capabilities'] — the derivation is broken, "
        f"which would silently empty this whole gate")
    assert len(_CLASS_CITATIONS) >= 25, (
        f"only {len(_CLASS_CITATIONS)} distinct class-rooted refs found in "
        f"ToolEntry prose — the walk is not seeing the citations")
    occurrences = sum(len(v) for v in _CLASS_CITATIONS.values())
    assert occurrences >= 70, (
        f"only {occurrences} class-rooted citation sites found — the walk is "
        f"not seeing the prose")
    # The QMat family is the densest citer; if it vanished, the walk broke.
    assert any(r.startswith("QMat.") for r in _CLASS_CITATIONS), (
        "no QMat.* reference found — QMat carries the exact-rational linear-"
        "algebra surface and is cited throughout; the walk is not working")


@pytest.mark.parametrize(
    "ref", sorted(_CLASS_CITATIONS), ids=sorted(_CLASS_CITATIONS)
)
def test_every_class_rooted_proseref_resolves(ref: str) -> None:
    """**Strict-zero.** Every ``Class.member`` cited in ToolEntry prose names an
    attribute that actually exists on that carrier class.

    This is the gate that ``One.to_numpy`` and ``Mat.buffers`` walked past for
    44 rcs, because the rc363 extraction next door required a reference to BEGIN
    at the literal token ``srmech``."""
    cls_name, member = ref.split(".", 1)
    assert _class_ref_resolves(ref), (
        f"the ToolEntry prose cites {ref!r}, but {member!r} is not an attribute "
        f"of {cls_name} ({_CARRIER_CLASSES[cls_name].__module__}) — cited at "
        f"{sorted(_CLASS_CITATIONS[ref])[:4]}. A deleted or misspelled member "
        f"in a shipped introspect payload tells a reader to call something that "
        f"raises AttributeError."
    )


def test_no_unresolved_class_rooted_citation_anywhere() -> None:
    """The aggregate peer, so a collection-time failure cannot silently void the
    parametrised gate above."""
    dead = sorted(r for r in _CLASS_CITATIONS if not _class_ref_resolves(r))
    assert not dead, (
        f"{len(dead)} class-rooted ref(s) cited in ToolEntry prose do not "
        f"resolve: {dead}")
