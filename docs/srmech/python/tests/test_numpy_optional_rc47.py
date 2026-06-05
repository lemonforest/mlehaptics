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
    """AST ratchet (broadened rc48 for #882): NO module under ``srmech/amsc/**``
    — the numpy-free cascade core — may ``import numpy`` at module top level. A
    top-level numpy import makes the module crash raw on a plain (numpy-free)
    install instead of importing and gating cleanly via the ``lazy_numpy``
    proxy. rc47's hardcoded list missed ``amsc/hdc.py`` (+ coupling / harmonics
    / cascade.matrix_cascades); walking the whole subtree closes that hole."""
    import ast

    pkg = pathlib.Path(srmech.__file__).resolve().parent
    files = [pkg / "__init__.py", pkg / "_scientific.py"]
    files += sorted((pkg / "amsc").rglob("*.py"))
    offenders = []
    for p in files:
        if not p.is_file():
            continue
        rel = p.relative_to(pkg).as_posix()
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
        "amsc cascade-core modules import numpy at top level (crash raw on a "
        f"plain install — use srmech._scientific.lazy_numpy): {sorted(set(offenders))}"
    )


def test_amsc_core_modules_import_without_numpy(monkeypatch):
    """Behavioral guard (#882): with numpy unavailable, the mixed amsc modules
    (hdc / coupling / harmonics / cascade.matrix_cascades) still IMPORT, the
    Klein-4 HV-carrier path runs numpy-free, and an ndarray op raises the clean
    ``[scientific]`` hint (not a raw ``ModuleNotFoundError``)."""
    import builtins
    import importlib

    real_import = builtins.__import__

    def _no_numpy(name, *a, **k):
        if name == "numpy" or name.startswith("numpy."):
            raise ModuleNotFoundError("No module named 'numpy'")
        return real_import(name, *a, **k)

    targets = [
        "srmech.amsc.hdc", "srmech.amsc.coupling", "srmech.amsc.harmonics",
        "srmech.amsc.cascade.matrix_cascades",
    ]
    for m in list(sys.modules):
        if m == "numpy" or m.startswith("numpy.") or m in targets:
            monkeypatch.delitem(sys.modules, m, raising=False)
    monkeypatch.setattr(builtins, "__import__", _no_numpy)

    hdc = importlib.import_module("srmech.amsc.hdc")          # must not raise
    for name in targets[1:]:
        importlib.import_module(name)                          # must not raise

    # Klein-4 HV-carrier path is genuinely numpy-free.
    hv = hdc.klein4_random(64, seed=1)
    assert type(hv).__name__ == "HV"
    assert hdc.klein4_similarity(hv, hv) == 1.0
    assert type(hdc.klein4_bind(hv, hdc.klein4_random(64, seed=2))).__name__ == "HV"

    # A bipolar (ndarray) op raises the actionable [scientific] hint, not a raw
    # numpy ModuleNotFoundError.
    with pytest.raises(ImportError) as exc:
        hdc.polar_random(16, seed=1)
    assert "srmech[scientific]" in str(exc.value)
