"""rc202 — the srmech_class_registry.c codegen drift-catcher (pure Python).

srmech_run_class_method resolves a class NAME to its packaged [class] descriptor
through the compiled-in srmech_class_registry_table — GENERATED from the packaged
class_catalog/*.toml by c/tools/gen_class_registry.py (the rc184 tool-registry
codegen model). This guards that the checked-in generated .c is in lockstep with
the packaged descriptors (re-run -> no diff) and holds every shipped class NAME,
so a stale table can never silently drop a class from the C resolve. Pure Python
(no native lib needed) per [[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]].
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

from srmech.dsl._class_catalog import list_classes

_HERE = Path(__file__).resolve().parent
_C_SRC = _HERE.parent.parent / "c" / "src" / "srmech_class_registry.c"
_CODEGEN = _HERE.parent.parent / "c" / "tools" / "gen_class_registry.py"


def _load_codegen():
    spec = importlib.util.spec_from_file_location("gen_class_registry_rc202", _CODEGEN)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_codegen_is_idempotent() -> None:
    """Re-running the generator reproduces the checked-in table exactly (line-
    ending normalised). If this fails, srmech_class_registry.c is stale."""
    assert _C_SRC.exists(), f"missing generated table {_C_SRC}"
    assert _CODEGEN.exists(), f"missing codegen {_CODEGEN}"
    mod = _load_codegen()
    regenerated = mod.generate().replace("\r\n", "\n")
    on_disk = _C_SRC.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert regenerated == on_disk, (
        "c/src/srmech_class_registry.c is out of date — regenerate with "
        "c/tools/gen_class_registry.py > c/src/srmech_class_registry.c"
    )


def test_generated_table_holds_every_shipped_class() -> None:
    """The generated table registers every packaged class NAME (the resolve keys
    a bare-C host uses) — a coarse sanity pin independent of the native lib."""
    text = _C_SRC.read_text(encoding="utf-8")
    shipped = list_classes()
    assert shipped, "no shipped classes discovered"
    for name in shipped:
        assert f'"{name}"' in text, (
            f"class {name!r} is missing from srmech_class_registry.c — regenerate"
        )


def test_generated_table_is_pure_ascii() -> None:
    """The generated .c is pure ASCII (descriptor bytes baked as decimal ints,
    the header ASCII-only) — MSVC-safe under -Wpedantic / /WX."""
    data = _C_SRC.read_bytes()
    non_ascii = [i for i, b in enumerate(data) if b > 0x7F]
    assert not non_ascii, (
        f"srmech_class_registry.c has {len(non_ascii)} non-ASCII byte(s) at "
        f"offsets {non_ascii[:5]} — the codegen must emit ASCII-only source"
    )
