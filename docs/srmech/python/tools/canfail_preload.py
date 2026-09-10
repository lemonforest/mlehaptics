r"""THE SANCTIONED CAN-FAIL HARNESS — mutate a COPY, never the shipped tree.

A gate that cannot be shown to return otherwise is not a measurement, so every
gate in this package owes a CAN-FAIL demonstration: break the thing it measures
and watch it go red. The obvious way to do that is to edit the shipped source,
run the gate, and restore from a byte copy. **That way is the hazard, and this
file exists because it produced a phantom finding inside rc470's own
re-validation.**

WHAT HAPPENED (rc470, ``#T1188``, and the reason this ships)
-----------------------------------------------------------
Three validation lanes ran concurrently in ONE working tree. One of them proved
the CHANGELOG's can-fail claim by rewriting ``tools/demotion_probe.py`` in
place — replacing the negation refusal with ``if False:`` — running the gate,
and restoring from a byte copy with an md5 check. A sibling lane issued its
first ``pytest`` SIXTEEN SECONDS into that window, imported the mutant, and
reported *"lexical DECLARED is 246, not 219"* as a defect in the gate. It was
not one. The restore was byte-exact, so ``git diff`` was empty afterwards and
the only trace was an mtime. It happened three times in thirty-two minutes.

A finding that can only be produced by the validation apparatus is the
apparatus's defect. **THE RULE, and it is not a preference:**

    A can-fail mutation is applied to a COPY of the source. The shipped tree is
    never written in order to prove that a gate can fail.

There is no measurement that requires the shipped file to change — every
can-fail figure in the rc470 entry reproduces through this harness with the
tree untouched (EXECUTED).

⚠️ rc471 (`#T1188`) — THIS FILE ARGUED AGAINST ITS OWN rc471 SHAPE
==================================================================
Through rc470, :func:`source_of` carried a reasoned REFUSAL of package modules:

    *"Deliberately narrow: this harness mutates TOOLS, which are the modules the
    gates import by name. A gate that needs a mutant of a package module should
    say so in a review rather than acquire it by widening this."*

**rc471 IS that review, and it OVERTURNS the refusal rather than working around
it.** The record, so a later reader is not left guessing whether the narrowing
was forgotten or reversed:

* **What the refusal got right.** ``tools/`` modules are imported by bare name,
  so a ``sys.path`` shim reaches them. Widening the SAME mechanism to package
  modules would have been unsound — see the next bullet — and refusing it was
  the correct call *for that mechanism*.
* **What changed.** The rest of the "ALU All The Way" arc mutates
  ``srmech/math/rational.py`` and its siblings. Those are DOTTED names, and no
  amount of ``sys.path`` manipulation delivers one: ``PathFinder`` resolves
  ``srmech.math.rational`` through ``srmech.math.__path__``, so a directory on
  ``sys.path`` holding ``srmech.math.rational.py`` exposes **nothing
  importable** — three ``ImportError``s, measured. So the widening is not the
  one the refusal declined; it is a DIFFERENT MECHANISM (:class:`MutantFinder`,
  a ``sys.meta_path`` entry) that the refusal never ruled on.
* **Why the new mechanism is stronger, not weaker.** ``PathFinder`` is LAST in
  ``sys.meta_path``, so a finder at index 0 outranks any ``sys.path`` a gate
  sets — including an unconditional module-level ``sys.path.insert(0, PY_ROOT)``,
  which is the hostile case a path shim loses to.

THE TWO SANCTIONED SHAPES
-------------------------
1. **``sys.meta_path`` INJECTION** (this file, used as a pytest plugin). A
   mutant copy is written OUTSIDE the repo and a finder is installed that
   answers for exactly the named modules; the test module's own ``import`` then
   binds to the copy. Use this when the gate imports the module under test at
   module level, which is the common case::

       python3 tools/canfail_preload.py --module srmech.math.rational \
           --replace 'OLD' 'NEW' --out /tmp/canfail
       CANFAIL_DIR=/tmp/canfail CANFAIL_MODULE=srmech.math.rational \
           python3 -m pytest tests/test_rational_parity.py -q -p canfail_preload

   ⚠️ **The injection happens AT IMPORT TIME, not before it.** Through rc470
   this file preloaded the mutant into ``sys.modules`` ahead of collection, and
   the CHANGELOG states the rule that way (*"injected into sys.modules before
   the test module imports it"*). A meta-path finder cannot preload a package
   submodule — importing ``srmech.math.rational`` early would import ``srmech``
   and ``srmech.math`` with it, which is precisely the state
   :func:`install` refuses. So the finder waits, and the FIRST importer gets
   the mutant. The observable contract is unchanged; the mechanism is not.

   ``--out`` MUST be outside the package tree; this file refuses otherwise, so
   a mutant cannot be collected as a test, imported by a sibling process, or
   committed by accident. The mutant KEEPS THE DOTS in its filename
   (``srmech.math.rational.py``) — a second, free safety property: a directory
   holding only that file exposes nothing importable even if it does end up on
   ``sys.path``.

2. **COMPILE A COPY INTO A THROWAWAY NAMESPACE**, when the claim is about
   IMPORT-TIME behaviour and no gate needs to run against the mutant. That is
   what ``tests/test_r3_reader_rc470.py``'s
   ``test_group_d_the_case_policy_is_wired_not_declared`` does to prove the
   ``CASE_POLICY`` fold table is closed: read the shipped bytes, substitute one
   line in memory, ``compile`` + ``exec`` into a fresh ``dict``, and assert the
   ``ValueError`` (a real ``raise``, promoted from a bare ``assert`` under the
   rc433 `#T1131`/`#T1188` discipline — a closedness guard certified via
   ``pytest.raises(AssertionError)`` would be one `python -O` strips).
   Nothing is written to disk at all.

⚠️ THE FAILURE MODE THIS HARNESS MUST REFUSE OUT LOUD
=====================================================
A can-fail harness that mutates NOTHING reports **green on every gate in the
arc**, and it reports it in the same words a real pass uses. It happened during
rc471's own research phase: a report's "proof" command named ``-p
canfail_pkg_proto``, a file that is a LIBRARY with no pytest hook, so pytest
loaded it, ran nothing of it, and printed **33 passed**. Nobody could tell that
from a real 33.

So this file refuses LOUDLY, on stderr, with a distinct nonzero exit, in TWO
states — and each refusal has its own can-fail in
``tests/test_canfail_preload_pkg_rc471.py``:

**(a) the target is ALREADY in ``sys.modules``.** The finder is never
consulted, every import binds the SHIPPED module, and the gate passes for the
wrong reason. This one fired on a real accident inside the prototype.

**(b) the plugin ran and MUTATED NOTHING.** Checked at
``pytest_sessionfinish``: every configured target must be in ``sys.modules``
with ``__file__`` equal to its mutant. If not, the run's tally is meaningless,
so the banner goes to stderr and the exit status is forced to
``pytest.ExitCode.USAGE_ERROR``. **Assert on the banner, never on the tally** —
the tally is exactly what a silent false green gets right.

WHAT A LANE MUST PRINT BESIDE EVERY FIGURE
-------------------------------------------
This harness makes the mutation safe; it does not make the figure trustworthy
on its own. A figure is trustworthy when the run that printed it can show the
tree it measured was static. So print, beside every number: ``git status
--porcelain`` for the instrument, the instrument's blob hash, and
``srmech.__file__``. Had the sibling lane printed the probe's blob hash beside
its 246, the finding would have named the mutation instead of the integer.
``tools/rc470_figures.py`` (on ``tools/figure_run.py``) is the worked example.

numpy-free. No ``abs()``. Routes every digest through
``srmech.amsc.format.sha256_bytes`` rather than calling ``hashlib`` directly.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

#: The package tree a mutant must NOT be written into. A copy that lands inside
#: it is collectable by pytest, importable by any sibling process, and
#: committable by accident — every property this harness exists to remove.
PACKAGE_ROOT = Path(__file__).resolve().parents[1]

#: Env vars the pytest plugin arm reads. Named rather than positional so the
#: same invocation can be pasted into a lane brief unchanged.
#: ``CANFAIL_MODULE`` takes ONE name or a comma-separated list.
ENV_DIR = "CANFAIL_DIR"
ENV_MODULE = "CANFAIL_MODULE"


def source_of(module_name: str) -> Path:
    """The shipped source file for ``module_name``.

    A **dotted** name is a PACKAGE module and resolves under
    :data:`PACKAGE_ROOT` (``srmech.math.rational`` →
    ``srmech/math/rational.py``); a **bare** name is a ``tools/`` module, which
    is how the gates import their instruments.

    ⚠️ Through rc470 this function refused the dotted form on the record. The
    refusal, and rc471's reversal of it, are set out in the module docstring —
    it is a REVERSAL after review, not a narrowing that was forgotten.
    """
    if "." in module_name:
        parts = module_name.split(".")
        if not all(parts) or any(s in (os.sep, os.altsep) for s in parts):
            raise ValueError(
                f"{module_name!r} is not a dotted module name")
        p = PACKAGE_ROOT.joinpath(*parts).with_suffix(".py")
    else:
        p = PACKAGE_ROOT / "tools" / (module_name + ".py")
    if not p.is_file():
        raise FileNotFoundError(f"no shipped source at {p}")
    return p


def write_mutant(module_name: str,
                 replacements: Sequence[Tuple[str, str]],
                 out_dir: Path) -> Path:
    """Write a mutant COPY of ``module_name`` into ``out_dir``; return its path.

    Every ``(old, new)`` pair must match EXACTLY ONCE in the source. A pair that
    matches zero times is a stale control that would leave the "mutant"
    identical to the original and turn the whole demonstration green for the
    wrong reason; a pair that matches twice is ambiguous. Both raise.

    ``out_dir`` is refused if it lies inside the package tree. The refusal keys
    on ``out_dir``, never on ``module_name``, so it is identical for a dotted
    target and a bare one.

    The mutant filename KEEPS THE DOTS (``srmech.math.rational.py``). That is
    deliberate: such a directory exposes nothing importable on ``sys.path``, so
    the only route to the mutant is the finder :func:`install` puts in place.
    """
    out_dir = Path(out_dir).resolve()
    if PACKAGE_ROOT in out_dir.parents or out_dir == PACKAGE_ROOT:
        raise ValueError(
            f"refusing to write a mutant inside the package tree ({out_dir}). "
            f"A mutant under {PACKAGE_ROOT} is collectable by pytest, "
            f"importable by any sibling process, and committable by accident "
            f"— which is the whole class of defect this harness removes.")
    src_path = source_of(module_name)
    text = src_path.read_text(encoding="utf-8")
    for old, new in replacements:
        n = text.count(old)
        if n != 1:
            raise ValueError(
                f"the mutation target {old!r} occurs {n} times in "
                f"{src_path} — a control that matches zero times leaves "
                f"the 'mutant' identical to the shipped file and the "
                f"demonstration passes for the wrong reason.")
        text = text.replace(old, new, 1)
    out_dir.mkdir(parents=True, exist_ok=True)
    dst = out_dir / (module_name + ".py")
    dst.write_text(text, encoding="utf-8", newline="\n")
    if src_path.read_text(encoding="utf-8") == text:
        raise RuntimeError(
            f"the mutant written to {dst} is byte-identical to {src_path}: "
            f"every replacement matched and none of them changed anything. "
            f"A no-op mutant greens every gate it is handed.")
    return dst


def blob_sha256(path) -> str:
    """sha256 of a file's bytes, routed through the package's own hasher."""
    from srmech.amsc.format import sha256_bytes
    return sha256_bytes(Path(path).read_bytes())


# ── the sys.meta_path arm ────────────────────────────────────────────────────

class MutantFinder:
    """A ``sys.meta_path`` finder that answers for exactly the named modules.

    Why a finder rather than a ``sys.path`` shim, measured:

    * A dotted name is unreachable by ``sys.path``. ``PathFinder`` resolves
      ``srmech.math.rational`` through the PARENT package's ``__path__``, so a
      directory holding ``srmech.math.rational.py`` delivers nothing.
    * ``PathFinder`` is LAST in ``sys.meta_path``. A finder at index 0
      therefore outranks a gate that does an unconditional module-level
      ``sys.path.insert(0, PY_ROOT)`` — the hostile case a shim loses to.
    * ``spec.parent`` is derived from the FULL dotted name, so the mutant loads
      with ``__package__ == 'srmech.math'`` and its own ``from .. import
      _native`` / ``from . import cyclic`` resolve to the REAL package objects.
      Nothing else in the package is replaced.
    """

    def __init__(self, targets: Mapping[str, Path]):
        self.targets: Dict[str, Path] = {
            name: Path(p).resolve() for name, p in targets.items()}
        #: fullname → mutant path, recorded when the finder actually answers.
        self.answered: Dict[str, str] = {}

    def find_spec(self, fullname, path=None, target=None):
        mutant = self.targets.get(fullname)
        if mutant is None:
            return None
        self.answered[fullname] = str(mutant)
        return importlib.util.spec_from_file_location(fullname, str(mutant))

    # kept for symmetry with the stdlib finder protocol
    def invalidate_caches(self) -> None:  # pragma: no cover - nothing cached
        return None


#: The finder this process installed, if any. Read by the pytest hooks.
INSTALLED: Optional[MutantFinder] = None


def install(targets: Mapping[str, Path]) -> MutantFinder:
    """Put a :class:`MutantFinder` at the FRONT of ``sys.meta_path``.

    Refuses LOUDLY — never returns a finder that cannot work:

    * an EMPTY target map. A harness with nothing to mutate greens every gate.
    * a target ALREADY in ``sys.modules``. The finder would never be consulted,
      every import would bind the shipped module, and the gate would pass for
      the wrong reason with no trace at all.
    * a target with no shipped source (a typo in ``CANFAIL_MODULE``), and a
      mutant file that is not there.
    """
    global INSTALLED
    if not targets:
        raise RuntimeError(
            "canfail_preload.install() was given NO targets. A can-fail "
            "harness that mutates nothing reports green on every gate, in the "
            "same words a real pass uses — which is the exact silent false "
            "green this file refuses.")
    already = sorted(n for n in targets if n in sys.modules)
    if already:
        raise RuntimeError(
            f"canfail_preload.install() REFUSES: {already} already in "
            f"sys.modules. The finder is consulted only on a FIRST import, so "
            f"every later import would bind the SHIPPED module and the gate "
            f"would pass for the wrong reason. Import canfail_preload (or pass "
            f"-p canfail_preload) BEFORE anything imports the target.")
    resolved: Dict[str, Path] = {}
    for name, mutant in targets.items():
        source_of(name)                       # refuses a name with no source
        mutant = Path(mutant).resolve()
        if not mutant.is_file():
            raise RuntimeError(
                f"canfail_preload.install() REFUSES: no mutant for {name} at "
                f"{mutant}. Write it with write_mutant() first.")
        resolved[name] = mutant
    finder = MutantFinder(resolved)
    sys.meta_path.insert(0, finder)
    INSTALLED = finder
    sys.stderr.write(
        f"\n[canfail_preload] meta-path finder INSTALLED for "
        f"{sorted(resolved)}\n[canfail_preload] the shipped tree is untouched; "
        f"every figure from this run is a MUTANT figure\n")
    return finder


def mutated(finder: Optional[MutantFinder] = None) -> Dict[str, str]:
    """``{fullname: loaded file}`` for every target ACTUALLY loaded from a mutant.

    The direct question, asked of ``sys.modules`` rather than of the finder's
    own bookkeeping: a finder can answer and the import still fail.
    """
    finder = finder if finder is not None else INSTALLED
    if finder is None:
        return {}
    out: Dict[str, str] = {}
    for name, mutant in finder.targets.items():
        mod = sys.modules.get(name)
        loaded = getattr(mod, "__file__", None) if mod is not None else None
        if loaded and Path(loaded).resolve() == mutant:
            out[name] = loaded
    return out


def parse_env(dir_value: str, module_value: str) -> Dict[str, Path]:
    """``CANFAIL_DIR`` + ``CANFAIL_MODULE`` → ``{fullname: mutant path}``.

    ``CANFAIL_MODULE`` takes ONE name or a comma-separated list — the multi-
    target form the rc470 prototype exercised through a dict and never through
    the env interface it documented. Both are exercised now; see
    ``tests/test_canfail_preload_pkg_rc471.py``.
    """
    root = Path(dir_value).resolve()
    names = [n.strip() for n in module_value.split(",") if n.strip()]
    if not names:
        raise RuntimeError(
            f"{ENV_MODULE}={module_value!r} names no module. A can-fail run "
            f"with no target mutates nothing and greens every gate.")
    return {name: root / (name + ".py") for name in names}


# ── the pytest plugin arm: -p canfail_preload ────────────────────────────────
# Imported by pytest BEFORE it collects, so the finder is in place before the
# test module's own imports run. Silent and inert unless both env vars are set,
# so leaving ``-p canfail_preload`` in a command is not a way to accidentally
# measure a mutant.

_dir = os.environ.get(ENV_DIR)
_mod = os.environ.get(ENV_MODULE)
if _dir and _mod:
    install(parse_env(_dir, _mod))


def pytest_report_header(config) -> List[str]:
    """Name the mutants in the run's own header — never only on stderr."""
    if INSTALLED is None:
        return []
    return [f"canfail_preload: MUTANT run, targets {sorted(INSTALLED.targets)}"]


def pytest_sessionfinish(session, exitstatus) -> None:
    """REFUSAL (b): the plugin ran and MUTATED NOTHING.

    A can-fail harness that mutates nothing prints a tally indistinguishable
    from a real pass. So the tally is not the verdict here — the loaded
    ``__file__`` of each target is. A target that never came from its mutant
    forces the exit status, with the banner on stderr.
    """
    if INSTALLED is None:
        return
    got = mutated(INSTALLED)
    missing = sorted(set(INSTALLED.targets) - set(got))
    if not missing:
        return
    import pytest
    sys.stderr.write(
        f"\n[canfail_preload] REFUSING THIS RUN: {missing} was never loaded "
        f"from a mutant.\n[canfail_preload] Nothing was mutated, so the tally "
        f"above measures the SHIPPED tree and is NOT a can-fail result. "
        f"A harness that mutates nothing reports green on every gate in the "
        f"same words a real pass uses.\n[canfail_preload] Check that the gate "
        f"actually imports {missing}, and that -p canfail_preload names THIS "
        f"module.\n")
    session.exitstatus = int(pytest.ExitCode.USAGE_ERROR)


def _main(argv: List[str]) -> int:
    import argparse
    ap = argparse.ArgumentParser(
        description="Write a mutant COPY of a module, outside the tree. "
                    "A dotted name is a package module; a bare name is a "
                    "tools/ module.")
    ap.add_argument("--module", required=True)
    ap.add_argument("--replace", nargs=2, action="append", metavar=("OLD", "NEW"),
                    required=True)
    ap.add_argument("--out", required=True)
    ns = ap.parse_args(argv)
    dst = write_mutant(ns.module, [tuple(r) for r in ns.replace], Path(ns.out))
    src = source_of(ns.module)
    print(f"shipped : {src}")
    print(f"          sha256 {blob_sha256(src)}")
    print(f"mutant  : {dst}")
    print(f"          sha256 {blob_sha256(dst)}")
    print(f"\nrun the gate against it with:\n"
          f"  {ENV_DIR}={Path(ns.out).resolve()} {ENV_MODULE}={ns.module} \\\n"
          f"  python3 -m pytest <gate> -q -p canfail_preload -p no:cacheprovider")
    print(f"\n(a dotted target needs NO PYTHONPATH: the mutant is delivered by a "
          f"sys.meta_path finder, not by sys.path. A bare tools/ target needs "
          f"PYTHONPATH={PACKAGE_ROOT / 'tools'} only if the gate imports other "
          f"tools/ modules.)")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(PACKAGE_ROOT))
    raise SystemExit(_main(sys.argv[1:]))
