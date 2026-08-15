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
reaching users through ``describe()``, the MCP tool list and the compiled-in C
registry. This is the same four-surface reasoning the issue-ref convention rests
on (root ``CLAUDE.md``): a reference that looks authoritative and points nowhere
is worse than no reference, because a reader spends effort resolving it before
concluding the docs are wrong.

STRICT ZERO, and it is affordable: the population is 498 distinct ``srmech.*``
cross-refs package-wide and exactly 2 were stale. This is not a CEIL class.

SCOPE — deliberately narrow, so the gate cannot go vacuously green:
  * only ``srmech.``-prefixed targets. A ``:class:`dict``` or a Sphinx-intersphinx
    reference to another project is not ours to resolve and is skipped.
  * resolution walks the LONGEST importable module prefix, then getattr()s the
    remainder. That accepts ``srmech.math.q.Q.limit_denominator`` (attribute of
    an attribute) without needing to know which part is the module.
  * an unresolvable target is a FAILURE, never a warning.

srmech-LOCAL invariant. This is not a JPL Power-of-Ten rule — Holzmann's list
has exactly ten and ``tests/test_jpl_audit.py`` iterates ``range(1, 11)``.
"""

from __future__ import annotations

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
