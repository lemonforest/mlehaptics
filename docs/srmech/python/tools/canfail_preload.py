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

THE TWO SANCTIONED SHAPES
-------------------------
1. **``sys.modules`` PRELOAD** (this file, used as a pytest plugin). A mutant
   copy is written OUTSIDE the repo, imported first, and the test module's own
   ``import demotion_probe`` then binds to the copy. Use this when the gate
   imports the module under test at module level, which is the common case::

       python3 tools/canfail_preload.py --module demotion_probe \
           --replace 'if _R3_NEG.search(sent[:m.start()]):' \
                     'if False:  # MUTANT' \
           --out /tmp/canfail
       PYTHONPATH=/mnt/d/GitHub/mlehaptics/docs/srmech/python/tools \
       CANFAIL_DIR=/tmp/canfail CANFAIL_MODULE=demotion_probe \
           python3 -m pytest tests/test_r3_reader_rc470.py -q -p canfail_preload

   ``--out`` MUST be outside the package tree; this file refuses otherwise, so
   a mutant cannot be collected as a test, imported by a sibling process, or
   committed by accident.

2. **COMPILE A COPY INTO A THROWAWAY NAMESPACE**, when the claim is about
   IMPORT-TIME behaviour and no gate needs to run against the mutant. That is
   what ``tests/test_r3_reader_rc470.py``'s
   ``test_group_d_the_case_policy_is_wired_not_declared`` does to prove the
   ``CASE_POLICY`` fold table is closed: read the shipped bytes, substitute one
   line in memory, ``compile`` + ``exec`` into a fresh ``dict``, and assert the
   ``AssertionError``. Nothing is written to disk at all.

WHAT A LANE MUST PRINT BESIDE EVERY FIGURE
-------------------------------------------
This harness makes the mutation safe; it does not make the figure trustworthy
on its own. A figure is trustworthy when the run that printed it can show the
tree it measured was static. So print, beside every number: ``git status
--porcelain`` for the instrument, the instrument's blob hash, and
``srmech.__file__``. Had the sibling lane printed the probe's blob hash beside
its 246, the finding would have named the mutation instead of the integer.
``tools/rc470_figures.py`` is the worked example.

numpy-free. No ``abs()``. Routes every digest through
``srmech.amsc.format.sha256_bytes`` rather than calling ``hashlib`` directly.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List, Sequence, Tuple

#: The package tree a mutant must NOT be written into. A copy that lands inside
#: it is collectable by pytest, importable by any sibling process, and
#: committable by accident — every property this harness exists to remove.
PACKAGE_ROOT = Path(__file__).resolve().parents[1]

#: Env vars the pytest plugin arm reads. Named rather than positional so the
#: same invocation can be pasted into a lane brief unchanged.
ENV_DIR = "CANFAIL_DIR"
ENV_MODULE = "CANFAIL_MODULE"


def source_of(module_name: str) -> Path:
    """The shipped source file for ``module_name`` under ``tools/``.

    Deliberately narrow: this harness mutates TOOLS, which are the modules the
    gates import by name. A gate that needs a mutant of a package module should
    say so in a review rather than acquire it by widening this.
    """
    p = PACKAGE_ROOT / "tools" / (module_name + ".py")
    assert p.is_file(), f"no shipped source at {p}"
    return p


def write_mutant(module_name: str,
                 replacements: Sequence[Tuple[str, str]],
                 out_dir: Path) -> Path:
    """Write a mutant COPY of ``module_name`` into ``out_dir``; return its path.

    Every ``(old, new)`` pair must match EXACTLY ONCE in the source. A pair that
    matches zero times is a stale control that would leave the "mutant"
    identical to the original and turn the whole demonstration green for the
    wrong reason; a pair that matches twice is ambiguous. Both raise.

    ``out_dir`` is refused if it lies inside the package tree.
    """
    out_dir = Path(out_dir).resolve()
    assert PACKAGE_ROOT not in out_dir.parents and out_dir != PACKAGE_ROOT, (
        f"refusing to write a mutant inside the package tree ({out_dir}). "
        f"A mutant under {PACKAGE_ROOT} is collectable by pytest, importable "
        f"by any sibling process, and committable by accident — which is the "
        f"whole class of defect this harness removes.")
    src_path = source_of(module_name)
    text = src_path.read_text(encoding="utf-8")
    for old, new in replacements:
        n = text.count(old)
        assert n == 1, (
            f"the mutation target {old!r} occurs {n} times in "
            f"{src_path} — a control that matches zero times leaves the "
            f"'mutant' identical to the shipped file and the demonstration "
            f"passes for the wrong reason.")
        text = text.replace(old, new, 1)
    out_dir.mkdir(parents=True, exist_ok=True)
    dst = out_dir / (module_name + ".py")
    dst.write_text(text, encoding="utf-8", newline="\n")
    assert src_path.read_text(encoding="utf-8") != text, "the mutant is a no-op"
    return dst


def blob_sha256(path) -> str:
    """sha256 of a file's bytes, routed through the package's own hasher."""
    from srmech.amsc.format import sha256_bytes
    return sha256_bytes(Path(path).read_bytes())


# ── the pytest plugin arm: -p canfail_preload ────────────────────────────────
# Imported by pytest BEFORE it collects, so the injection lands before the test
# module's own ``import demotion_probe`` runs. Silent and inert unless both env
# vars are set, so leaving ``-p canfail_preload`` in a command is not a way to
# accidentally measure a mutant.

_dir = os.environ.get(ENV_DIR)
_mod = os.environ.get(ENV_MODULE)
if _dir and _mod:
    _p = Path(_dir).resolve() / (_mod + ".py")
    assert _p.is_file(), f"{ENV_DIR}={_dir} holds no {_mod}.py"
    sys.path.insert(0, str(Path(_dir).resolve()))
    # the real tools/ stays reachable for the module's own sibling imports
    sys.path.append(str(PACKAGE_ROOT / "tools"))
    __import__(_mod)
    _loaded = sys.modules[_mod]
    sys.stderr.write(
        f"\n[canfail_preload] {_mod} PRELOADED FROM A MUTANT COPY: "
        f"{_loaded.__file__}\n[canfail_preload] the shipped tree is untouched; "
        f"every figure from this run is a MUTANT figure\n")


def _main(argv: List[str]) -> int:
    import argparse
    ap = argparse.ArgumentParser(
        description="Write a mutant COPY of a tools/ module, outside the tree.")
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
          f"  PYTHONPATH={PACKAGE_ROOT / 'tools'} \\\n"
          f"  python3 -m pytest <gate> -q -p canfail_preload -p no:cacheprovider")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(PACKAGE_ROOT))
    raise SystemExit(_main(sys.argv[1:]))
