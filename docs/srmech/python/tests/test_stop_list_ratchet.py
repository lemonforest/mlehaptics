"""STOP-list ratchet — numpy and ``collections.Counter`` / ``defaultdict`` are
BANNED in srmech source, and any new real code use fails this test (CI red).

User direction (2026-06-17, emphatic): "I need numpy and counter to always fail
to force you to use srmech." numpy is also blocked at the pip-install layer (a
machine-level ``global.constraint`` pinning ``numpy==0``), but that cannot stop
a *stdlib* import — ``collections.Counter`` / ``defaultdict`` are always
importable. So the enforcement that "makes them fail" is this source ratchet:
the same mechanical-tripwire discipline as ``test_jpl_audit.py`` and the numpy
carrier ratchet.

Why these are banned:
  * **numpy** — srmech is numpy-FREE (the rc69–rc134 carrier-removal arc). Every
    numpy idiom has a framework-native carrier (:class:`srmech.amsc.hv.HV` /
    :class:`srmech.amsc.mat.Mat` + the native dense kernels, ``rational.*`` for
    transcendentals). A new ``import numpy`` / ``np.`` reverses that work.
  * **Counter / defaultdict** — the hand-rolled ``Counter()`` co-occurrence
    idiom is the CLAUDE.md STOP-list contaminant (a statistical-LM tell). The
    framework answer is the attested cascade surface: ``cooccurrence_topk`` /
    ``dense_laplacian`` for counts→edges, the Class-M resonator over ``M`` for
    grounding (see ``srmech.amsc.text`` and the §57 ``rbs_lm.inference`` fix).

This is **AST-based**: it flags real import statements, attribute access
(``np.…``), and name references (``Counter(...)`` / ``defaultdict(...)``) — and
naturally IGNORES docstring / comment prose (those are string/comment tokens,
not AST ``Import`` / ``Name`` / ``Attribute`` nodes), so a docstring that *names*
the banned idiom to explain the discipline does not trip the ratchet.

Scope: ``srmech/`` package source only (NOT ``tests/`` — test code may still use
numpy as a differential ORACLE for an unflipped module per the sanctioned
exception). The list of offenders only ever goes to ZERO and stays there.
"""
from __future__ import annotations

import ast
import pathlib

import srmech

# Banned import targets.
_BANNED_IMPORT_MODULES = ("numpy",)                       # import numpy[.*] / from numpy[.*] import …
_BANNED_FROM_COLLECTIONS = frozenset({"Counter", "defaultdict"})
# Banned bare names (attribute roots / call targets) in executable code.
_BANNED_NAMES = frozenset({"np", "numpy", "Counter", "defaultdict"})


def _srmech_source_files() -> list[pathlib.Path]:
    """Every ``*.py`` under the installed/served ``srmech`` package (no cache)."""
    root = pathlib.Path(srmech.__file__).resolve().parent
    return [p for p in root.rglob("*.py") if "__pycache__" not in p.parts]


def _violations_in(path: pathlib.Path) -> list[str]:
    """AST-scan one file; return human-readable violation strings (empty if clean)."""
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(path))
    out: list[str] = []
    for node in ast.walk(tree):
        # `import numpy` / `import numpy as np` / `import numpy.linalg`
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "numpy" or alias.name.startswith("numpy."):
                    out.append(f"{path.name}:{node.lineno}: import {alias.name}")
        # `from numpy[.*] import …` and `from collections import Counter/defaultdict`
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod == "numpy" or mod.startswith("numpy."):
                out.append(f"{path.name}:{node.lineno}: from {mod} import …")
            if mod == "collections":
                for alias in node.names:
                    if alias.name in _BANNED_FROM_COLLECTIONS:
                        out.append(
                            f"{path.name}:{node.lineno}: from collections import {alias.name}"
                        )
        # bare name reference in executable code (np.x / numpy.x / Counter(...) /
        # defaultdict(...) / a stale `-> np.ndarray` non-stringized annotation)
        elif isinstance(node, ast.Name) and node.id in _BANNED_NAMES:
            out.append(f"{path.name}:{node.lineno}: name `{node.id}` referenced")
        # `collections.Counter` / `collections.defaultdict` attribute access
        elif isinstance(node, ast.Attribute) and node.attr in _BANNED_FROM_COLLECTIONS:
            base = node.value
            if isinstance(base, ast.Name) and base.id == "collections":
                out.append(f"{path.name}:{node.lineno}: collections.{node.attr}")
    return out


def test_no_numpy_or_counter_in_srmech_source():
    """ZERO real code uses of numpy / Counter / defaultdict anywhere in srmech/.

    This is the down-only tripwire: it must stay at zero. If it fails, route the
    work through the framework-native carriers/cascades instead of reaching for
    numpy or a hand-rolled Counter — that is the whole point of the ratchet.
    """
    files = _srmech_source_files()
    assert files, "found no srmech source files to scan (package layout changed?)"

    all_violations: list[str] = []
    for path in files:
        all_violations.extend(_violations_in(path))

    assert not all_violations, (
        "STOP-list violations found in srmech source (numpy / Counter / "
        "defaultdict are BANNED — use the framework-native carriers + cascades "
        "instead). Offenders:\n  " + "\n  ".join(sorted(all_violations))
    )
