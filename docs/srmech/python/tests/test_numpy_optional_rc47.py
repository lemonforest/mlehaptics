"""v0.7.0rc47 — numpy is an OPTIONAL dependency (the scientific-tier capstone).

The §22 + C-transpile arcs made the Class-N cascade core (srmech.amsc.* + the
native C surface) numpy-free. rc47 demotes numpy from a hard dependency to the
``scientific`` extra. These tests pin that contract deterministically (they run
with numpy PRESENT in CI):

1. both pyprojects declare numpy under ``[project.optional-dependencies]
   .scientific`` and NOT under ``[project] dependencies``;
2. the ``_scientific.require_numpy`` gate returns numpy when present, and raises
   an actionable ``ImportError`` (mentioning ``srmech[scientific]``) when not.
"""
import pathlib
import sys

import pytest

try:  # py3.11+ stdlib; tomli backport on 3.10
    import tomllib as _toml
except ModuleNotFoundError:  # pragma: no cover
    import tomli as _toml

import srmech
from srmech._scientific import require_numpy

_PYPROJECT_DIR = pathlib.Path(srmech.__file__).resolve().parents[1]


def _load(name):
    path = _PYPROJECT_DIR / name
    with open(path, "rb") as fh:
        return _toml.load(fh)


@pytest.mark.parametrize("name", ["pyproject.toml", "pyproject-pure.toml"])
def test_numpy_is_optional_not_a_hard_dependency(name):
    data = _load(name)
    project = data["project"]
    hard = " ".join(project.get("dependencies", []))
    assert "numpy" not in hard, f"{name}: numpy must NOT be a hard dependency"
    scientific = project["optional-dependencies"]["scientific"]
    assert any("numpy" in dep for dep in scientific), (
        f"{name}: numpy must be declared under the [scientific] extra"
    )


@pytest.mark.parametrize("name", ["pyproject.toml", "pyproject-pure.toml"])
def test_dev_and_tests_extras_still_pull_numpy(name):
    # CI runs the full suite (which exercises the scientific tier) from [dev];
    # the [tests] extra must stay self-sufficiently runnable too.
    extras = _load(name)["project"]["optional-dependencies"]
    for key in ("dev", "tests"):
        assert any("numpy" in dep for dep in extras[key]), (
            f"{name}: the [{key}] extra must include numpy (the suite needs it)"
        )


def test_require_numpy_returns_module_when_present():
    np = require_numpy("srmech.qm")
    assert np is sys.modules["numpy"]


def test_require_numpy_raises_actionable_hint_when_absent(monkeypatch):
    # Simulate a numpy-absent install without uninstalling: a None entry in
    # sys.modules makes ``import numpy`` raise ImportError.
    monkeypatch.setitem(sys.modules, "numpy", None)
    with pytest.raises(ImportError) as exc:
        require_numpy("srmech.signal_processing")
    msg = str(exc.value)
    assert "srmech.signal_processing" in msg
    assert "srmech[scientific]" in msg
    assert "scientific tier" in msg


def test_cascade_core_modules_do_not_import_numpy_at_top_level():
    """AST ratchet: the numpy-free cascade core must not ``import numpy`` at
    module top level (that would silently re-hard-depend numpy via the base
    import chain). Mirrors the no-abs / no-libm AST ratchets."""
    import ast

    core = [
        "__init__.py",
        "amsc/rational.py",
        "amsc/cyclic.py",
        "amsc/laplacian.py",
        "amsc/cascade/__init__.py",
        "_scientific.py",
    ]
    pkg = pathlib.Path(srmech.__file__).resolve().parent
    offenders = []
    for rel in core:
        p = pkg / rel
        if not p.is_file():
            continue
        tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
        for node in ast.walk(tree):
            # only flag MODULE-LEVEL imports (col_offset == 0); lazy imports
            # inside functions are fine.
            if isinstance(node, ast.Import) and node.col_offset == 0:
                if any(a.name == "numpy" or a.name.startswith("numpy.")
                       for a in node.names):
                    offenders.append(rel)
            elif isinstance(node, ast.ImportFrom) and node.col_offset == 0:
                if node.module and node.module.split(".")[0] == "numpy":
                    offenders.append(rel)
    assert not offenders, (
        "cascade-core modules import numpy at top level (breaks numpy-optional "
        f"base import): {sorted(set(offenders))}"
    )
