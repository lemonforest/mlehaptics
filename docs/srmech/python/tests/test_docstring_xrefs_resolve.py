"""Every ``:func:`srmech.…``` cross-reference in a docstring must RESOLVE.

SURFACED FROM OUTSIDE (2026-08-14). A Siona-side script drove the cascade-chain
surface — ``register_catalog_dir`` → ``list_cascade_ops`` → ``get_descriptor``
→ ``run_cascade_chain`` — and read the docstrings on the way through. One of
them pointed at a function that does not exist:

    srmech/dsl/_catalog.py:389   :func:`srmech.cli.dsl.ops`

``srmech.cli.dsl`` is real; the callable is ``run_ops``. ``ops`` is the CLI
SUBCOMMAND string, which appears correctly two lines later as ``srmech dsl
ops``. The reference had never resolved. A second, different shape sat in
``srmech/_resolve.py``: ``:mod:`srmech.tests.test_resolve_dotted_callable_rc413```
— the test file EXISTS, but at ``tests/``, BESIDE the package, never inside it,
so ``srmech.tests.*`` is not importable and never was.

WHY THIS IS A SHIPPED DEFECT, NOT TIDINESS. Docstrings here are not local
commentary — they are emitted into generated files and travel inside the wheel,
reaching users through the MCP tool list and the compiled-in C
registry. This is the same four-surface reasoning the issue-ref convention rests
on (root ``CLAUDE.md``): a reference that looks authoritative and points nowhere
is worse than no reference, because a reader spends effort resolving it before
concluding the docs are wrong.

STRICT ZERO, and it is affordable: the population is 498 distinct ``srmech.*``
cross-refs package-wide and exactly 2 were stale. This is not a CEIL class.
(Re-measured at rc445: 510 distinct across 1445 sites, 0 unresolvable.)

SCOPE — deliberately narrow, so the gate cannot go vacuously green:
  * only ``srmech.``-prefixed targets. A ``:class:`dict``` or a Sphinx-intersphinx
    reference to another project is not ours to resolve and is skipped.
  * resolution walks the LONGEST importable module prefix, then getattr()s the
    remainder. That accepts ``srmech.math.q.Q.limit_denominator`` (attribute of
    an attribute) without needing to know which part is the module.
  * an unresolvable target is a FAILURE, never a warning.

THE SECOND ARM (rc445, `#T1153`) — UNQUALIFIED retired-namespace references.
The check above can only see a target spelled ``srmech.<something>``. That is
exactly why it stayed green through nine dead references to the ``qm``
namespace: they are written UNQUALIFIED — ``qm.octonion`` rather than
:mod:`srmech.physics.qm.octonion` — so the first arm never looks at them, and
``import srmech.qm`` has raised ``ModuleNotFoundError`` since ADR-0010 removed
the old path outright at rc382 (moved to ``srmech.physics.qm`` at rc381, no
alias, per the no-legacy-path discipline).

So the arm is: a backticked dotted token whose HEAD is a retired top-level
srmech namespace must be fully qualified or removed. That set is finite and
enumerable from the ADRs (:data:`RETIRED_TOP_LEVEL`), which is what keeps this
decidable — it is a SET-membership check on a name, not a judgement about
prose. Deleting a word cannot satisfy it; only deleting the whole reference
can, and that is visible in review.

⚠️ HISTORY NOTES ARE EXEMPT, and the exemption is not cosmetic: a move-note of
the form ``old -> new`` is the CORRECT way to record that a path died, and a
naive scanner false-positives on it. ``srmech/physics/__init__.py`` carries
exactly such a note (``srmech.qm.spin`` -> ``srmech.physics.qm.spin``) and it
must survive. :func:`_is_history_note` implements the carve-out, and
``test_the_history_note_exemption_is_real`` proves it both ways so the
exemption cannot silently widen into "any line mentioning qm".

srmech-LOCAL invariant. This is not a JPL Power-of-Ten rule — Holzmann's list
has exactly ten and ``tests/test_jpl_audit.py`` iterates ``range(1, 11)``.
"""

from __future__ import annotations

import ast
import importlib
import pathlib
import re

import pytest

#: ``:role:`target``` where role is any of the Python domain roles the tree uses.
XREF = re.compile(
    r":(?:func|meth|mod|class|attr|data|exc):`~?([A-Za-z_][A-Za-z0-9_.]*)`"
)

#: Non-vacuity floor. If the walk collapses — a bad root, an exclusion swallowing
#: the tree, a regex that stops matching — the count craters and this fires
#: LOUD rather than reporting a clean corpus. Measured 498 distinct at rc434;
#: the floor is set well below so ordinary churn does not trip it, and it exists
#: only to catch a collapse. Raise it if the corpus grows a lot; never lower it
#: to make a red run green.
MIN_DISTINCT_XREFS = 300

_PKG = pathlib.Path(__file__).resolve().parent.parent / "srmech"


def _resolves(ref: str) -> bool:
    """Does ``ref`` name a real module, or an attribute reachable from one?"""
    parts = ref.split(".")
    for cut in range(len(parts), 1, -1):
        try:
            obj = importlib.import_module(".".join(parts[:cut]))
        except Exception:            # not importable at this depth — try shorter
            continue
        try:
            for attr in parts[cut:]:
                obj = getattr(obj, attr)
            return True
        except AttributeError:
            return False             # module resolved; the attribute path did not
    return False


def _harvest():
    """Return ``(sites, distinct)`` for every srmech-targeted xref in the package."""
    sites, distinct = [], {}
    for path in sorted(_PKG.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        src = path.read_text(encoding="utf-8", errors="replace")
        for m in XREF.finditer(src):
            ref = m.group(1)
            if not ref.startswith("srmech."):
                continue
            if ref not in distinct:
                distinct[ref] = _resolves(ref)
            sites.append((path, src[:m.start()].count("\n") + 1, ref))
    return sites, distinct


def test_every_srmech_docstring_xref_resolves():
    """STRICT ZERO — a cross-reference that points nowhere ships in the wheel."""
    sites, distinct = _harvest()
    bad = [(p, ln, r) for p, ln, r in sites if not distinct[r]]
    assert not bad, (
        "docstring cross-references that do not resolve:\n"
        + "\n".join(
            f"  {p.relative_to(_PKG.parent)}:{ln}  ->  {r}" for p, ln, r in bad
        )
        + "\n\nThese are emitted into generated files and ship inside the wheel. "
        "Fix the reference, or drop the role and write the target as a literal "
        "path in double backticks when it is not an importable Python name "
        "(a test module under tests/ is NOT importable as srmech.tests.*)."
    )


def test_the_corpus_is_not_empty():
    """A collapsed walk must FAIL, not report a clean tree.

    Without this, an exclusion or a broken root turns the strict-zero above into
    a vacuous pass — the failure mode that makes a gate worse than no gate.
    """
    _sites, distinct = _harvest()
    assert len(distinct) >= MIN_DISTINCT_XREFS, (
        f"only {len(distinct)} distinct srmech.* cross-refs found; expected at "
        f"least {MIN_DISTINCT_XREFS}. The walk collapsed — this is a broken "
        f"instrument, not a clean corpus."
    )


# ---------------------------------------------------------------------------
# SECOND ARM — unqualified references to a RETIRED top-level srmech namespace.
# ---------------------------------------------------------------------------

#: Top-level names that WERE importable as ``srmech.<name>`` and are not any
#: more. Enumerated from the ADRs, not guessed.
#:
#:   * ``qm`` — ADR-0010 (namespace declustering) moved the whole subpackage to
#:     ``srmech.physics.qm`` at v0.9.0rc381 and REMOVED ``srmech.qm`` outright
#:     at rc382 (clean break, no alias). MEASURED: ``import srmech.qm`` raises
#:     ``ModuleNotFoundError``.
#:
#: ADR-0010's other moves (``apokatastasis`` / ``math`` / ``biology`` /
#: ``cascade``) were ADDITIONS of a new parent, not retirements of an old
#: top-level name, so nothing else belongs here yet. Add a name ONLY when
#: ``srmech.<name>`` has actually stopped importing — the control test below
#: asserts exactly that, so a wrong entry fails loudly instead of widening the
#: gate into prose policing.
RETIRED_TOP_LEVEL = ("qm",)

#: A backticked dotted token headed by a retired namespace. Both the ``role``
#: form (:mod:`qm.x`) and the bare double/single-backtick prose form.
_RETIRED_ALT = "|".join(re.escape(n) for n in RETIRED_TOP_LEVEL)
RETIRED_REF = re.compile(
    r"(?::(?:func|meth|mod|class|attr|data|exc):)?"
    r"``?((?:%s)\.[A-Za-z_][A-Za-z0-9_.]*)``?" % _RETIRED_ALT
)

#: ``old -> new`` (or ``old → new``) on the same line: a move NOTE, which is the
#: correct way to record a dead path and must not be flagged.
_HISTORY = re.compile(r"(?:->|→|=>)")


def _is_history_note(line: str) -> bool:
    """Is ``line`` a ``X -> Y`` move note rather than a live reference?"""
    return bool(_HISTORY.search(line))


def _docstring_lines():
    """Yield ``(path, lineno_in_docstring_text, line)`` for every package docstring."""
    for path in sorted(_PKG.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        src = path.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(src)
        except SyntaxError:                       # pragma: no cover - loud below
            raise AssertionError(f"{path} does not parse; the scan is broken")
        holders = [tree] + [
            n for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        ]
        for holder in holders:
            doc = ast.get_docstring(holder, clean=False)
            if not doc:
                continue
            start = getattr(holder, "lineno", 1)
            for offset, line in enumerate(doc.splitlines()):
                yield path, start + offset, line


def _retired_hits():
    hits = []
    for path, lineno, line in _docstring_lines():
        if _is_history_note(line):
            continue
        for m in RETIRED_REF.finditer(line):
            hits.append((path, lineno, m.group(1), line.strip()))
    return hits


def test_no_unqualified_reference_to_a_retired_namespace():
    """STRICT ZERO. ``qm.octonion`` is not a name; ``srmech.qm`` does not exist.

    This is the arm the fully-qualified check above CANNOT have: it never looks
    at a token that does not start with ``srmech.``, which is precisely how nine
    dead ``qm.*`` references survived it.
    """
    hits = _retired_hits()
    assert not hits, (
        "docstring references headed by a RETIRED top-level srmech namespace:\n"
        + "\n".join(
            f"  {p.relative_to(_PKG.parent)}:{ln}  ->  {tok}\n      {line}"
            for p, ln, tok, line in hits
        )
        + "\n\nWrite the FULL live path (e.g. `srmech.physics.qm.octonion`) so "
        "the resolution gate above can see it, or drop the reference. A "
        "history note of the form `old -> new` is exempt and is the right way "
        "to record that a path died."
    )


def test_every_retired_name_really_is_retired():
    """The roster must name paths that ACTUALLY stopped importing.

    Without this the roster is an opinion, and a wrong entry would turn a
    name-resolution gate into prose policing.
    """
    for name in RETIRED_TOP_LEVEL:
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module(f"srmech.{name}")


def test_the_history_note_exemption_is_real():
    """Both directions, so the carve-out cannot quietly widen.

    ``srmech/physics/__init__.py`` carries a genuine move note. An instrument
    that flags it is wrong; an instrument that exempts every line merely
    MENTIONING the namespace is useless.
    """
    assert _is_history_note("``srmech.qm.spin`` -> ``srmech.physics.qm.spin``")
    assert _is_history_note("qm.octonion → srmech.physics.qm.octonion")
    assert not _is_history_note("``qm.octonion`` carries float64 octonions")


def test_the_arm_would_have_fired_on_the_rc444_text():
    """Retro-check against the verbatim rc444 lines, per this tree's pattern.

    A gate that passes on the text it was written for is not the gate.
    """
    rc444 = [
        "``qm.quaternion`` carries float64",
        "the SAME generative cocycle ``qm.octonion`` builds its structure from",
        "Composes the rc109 foundation: ``qm.quaternion.quaternion_twiddle``",
        "``qm.single_particle`` used in rc117) — never numpy ``@``",
    ]
    for line in rc444:
        assert not _is_history_note(line), line
        assert RETIRED_REF.search(line), f"the arm would have MISSED: {line}"


def test_the_retired_scan_is_not_vacuous():
    """The docstring walk must actually visit a corpus.

    Same non-vacuity reasoning as ``test_the_corpus_is_not_empty``: a collapsed
    walk would make the strict zero above meaningless.
    """
    n = sum(1 for _ in _docstring_lines())
    assert n >= 20_000, (
        f"only {n} docstring lines visited; the AST walk collapsed. This is a "
        f"broken instrument, not a clean corpus."
    )


@pytest.mark.parametrize(
    "ref, expected, why",
    [
        ("srmech.cli.dsl.run_ops", True, "the real callable behind `srmech dsl ops`"),
        ("srmech.cli.dsl.ops", False, "the SUBCOMMAND name — never a Python name"),
        ("srmech.tests.test_resolve_dotted_callable_rc413", False,
         "tests/ lives BESIDE the package, so srmech.tests.* is not importable"),
        ("srmech.dsl.list_cascade_ops", True, "re-exported on the subpackage"),
        ("srmech.math.rational.best_rational", True, "a plain module-level func"),
        ("srmech.math.rational.best_rational_XXX", False, "module ok, attr absent"),
        ("srmech.no_such_subpackage.thing", False, "no such module at any depth"),
    ],
)
def test_resolver_discriminates(ref, expected, why):
    """The resolver must return BOTH answers, including on the two REAL defects.

    A checker that cannot say "no" is not a checker. The two False rows that name
    `cli.dsl.ops` and `srmech.tests.*` are the exact strings this gate was written
    for: they are kept as live negative controls so a future "simplification" of
    the resolver that silently accepts them turns this red.
    """
    assert _resolves(ref) is expected, why
