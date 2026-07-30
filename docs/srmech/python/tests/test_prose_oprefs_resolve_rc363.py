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

* ``srmech.amsc.laplacian`` — a MODULE (135 occurrences tree-wide is the largest
  single citation). A module path is a real reference: ADR-0010 moves modules,
  and a citation of a module that no longer exists is exactly as broken as a
  citation of an op that no longer exists.
* ``srmech.amsc.laplacian.mat_matmul`` — a module attribute (an op, a class, a
  constant). Deep chains resolve too: ``srmech.amsc.qmat.QMat.rank`` walks the
  class.

Two extractions are **excluded by rule**, not by allowlist:

* **A filename.** ``srmech.h`` is the C public header, cited 24 times, and is not
  a Python path at all. A two-segment path whose tail is a known source/artifact
  extension is a filename.
* **A wildcard tail.** ``srmech.qm.*`` is a family reference; it is truncated at
  the ``*`` and the remaining module prefix is what gets resolved.

What this gate cannot decide
============================
* **It cannot tell a RIGHT path from a merely EXISTING one.** ``srmech.amsc.hdc``
  resolves whether or not it is the module the sentence is about. Topicality is
  not decidable here — the same distinction the repo's issue-reference discipline
  draws for ``#NNNN``.
* **It does not read every prose surface in the tree.** Docstrings, the
  CHANGELOG, the ADRs and the notebooks are out of scope; this is the ToolEntry
  surface that ships in the wheel and in the compiled-in C registry.
* **``example`` is out of scope**, by the argument above.

Measured at rc363
=================
**462 occurrences of 199 distinct paths across 236 of 525 ops** in
``summary`` + ``explanation`` — 438 attribute references, 24 module references,
**0 unresolved**. The gate therefore ships **STRICT-ZERO with no CEIL**.

The other ToolEntry prose fields (``parameters[].summary``, ``returns.shape`` /
``returns.summary``) are covered too — 6 occurrences, of which **1 was a genuine
stale citation** found by this gate and fixed in the same rc:
``genome_register_attested``'s ``source`` example read ``'srmech.genome.<name>'``,
a module path that has never existed (the module is ``srmech.amsc.genome``).

Pure stdlib + srmech; numpy-free; no ``abs()``.
"""

from __future__ import annotations

import importlib
import re
from typing import Dict, List, Optional, Set, Tuple

import pytest

from srmech.amsc.tool_schema import get_tool_schema, warmup_all

warmup_all()

#: A dotted path rooted at ``srmech``. ``*`` is admitted as a segment so a family
#: reference (``srmech.qm.*``) is CAPTURED and then truncated, rather than
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
    assert _normalise("srmech.qm.*") == "srmech.qm"
    assert _normalise("srmech.amsc.laplacian") == "srmech.amsc.laplacian"


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
