"""#930 — the ripple gate for the THIRD generated C table (srmech_class_registry.c).

`srmech_class_registry.c` bakes the packaged `[class]` TOML descriptors so a
bare-C host can resolve a class NAME -> descriptor with no interpreter. Two axes
already guard it:

  * `test_class_registry_codegen_rc202.py` pins `.c` == regenerate-from-TOML
    (idempotence) and that the table holds every shipped class NAME.
  * `test_run_class_method_c_rc202.py` pins C NAME->descriptor resolve + C-vs-pure
    dispatch for the shipped classes.

The gap #930 names is one level in: each `[class]` method binds an OP by
fully-qualified string (`op = "srmech.biology.genome.encode_shape"`), and NOTHING
asserted those strings still resolve. Rename the op and the TOML — hence the
baked `.c` — keeps pointing at the old name: the idempotence test still passes
(the `.c` matches the unchanged TOML), but the class binding is orphaned, so C
dispatch silently drops to pure. This test closes that: every op-ref in every
packaged class TOML MUST resolve to an importable `module.attr`, so an op rename
that forgets a class binding is a RED build, not a silent desync.

Pure Python (tomllib/tomli + importlib); no native lib needed.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

try:
    import tomllib  # py3.11+
except ModuleNotFoundError:  # py3.10 floor
    import tomli as tomllib  # type: ignore

_CATALOG_DIR = (
    Path(__file__).resolve().parent.parent
    / "srmech" / "cascade" / "catalogs" / "class_catalog"
)


def _collect_oprefs(node) -> list[str]:
    """Every ``op = "..."`` string anywhere in a descriptor (methods may nest
    op-refs in lists — the SedenionRegister `is_navigable` chain does)."""
    out: list[str] = []
    if isinstance(node, dict):
        for key, val in node.items():
            if key == "op" and isinstance(val, str):
                out.append(val)
            else:
                out.extend(_collect_oprefs(val))
    elif isinstance(node, list):
        for item in node:
            out.extend(_collect_oprefs(item))
    return out


def _all_oprefs() -> list[tuple[str, str]]:
    """(toml_name, op-ref) for every packaged class descriptor."""
    pairs: list[tuple[str, str]] = []
    for toml in sorted(_CATALOG_DIR.glob("*.toml")):
        data = tomllib.loads(toml.read_text(encoding="utf-8"))
        for op in _collect_oprefs(data):
            pairs.append((toml.name, op))
    return pairs


def _resolves(dotted: str) -> bool:
    module, _, attr = dotted.rpartition(".")
    if not module or not attr:
        return False
    try:
        return hasattr(importlib.import_module(module), attr)
    except Exception:
        return False


def test_class_catalog_directory_is_present_and_nonempty():
    """The walk must not silently pass on an empty/missing catalog (a false
    green — the #935 lesson: a guard that observes nothing is a guard that lies)."""
    assert _CATALOG_DIR.is_dir(), f"missing class_catalog dir: {_CATALOG_DIR}"
    tomls = list(_CATALOG_DIR.glob("*.toml"))
    assert tomls, "no packaged [class] TOML descriptors found"
    pairs = _all_oprefs()
    assert len(pairs) >= 20, (
        f"only {len(pairs)} op-refs collected across {len(tomls)} class TOMLs — "
        f"the walk is not seeing the method bindings"
    )


@pytest.mark.parametrize(
    "toml_name,opref",
    _all_oprefs(),
    ids=[f"{n}:{op}" for n, op in _all_oprefs()],
)
def test_every_class_toml_opref_resolves(toml_name: str, opref: str):
    """Every ``op`` a packaged class method binds resolves to an importable
    ``module.attr``. Renaming an op without updating the class TOML orphans the
    binding — C dispatch drops to pure silently; this makes it a red build."""
    assert _resolves(opref), (
        f"{toml_name}: class method binds op {opref!r}, which no longer resolves "
        f"to an importable module.attr — the op was renamed/removed without "
        f"updating this [class] descriptor (and its baked srmech_class_registry.c). "
        f"Regenerate the descriptor + re-run c/tools/gen_class_registry.py."
    )
