"""rc407 (`#T1076`) — a front door owns its EXCEPTION contract, not just its
happy path.

The gap
=======
``srmech._json`` re-exported ``load`` / ``loads`` and nothing else:
``dir(srmech._json)`` public was ``['Any', 'annotations', 'load', 'loads']``
and ``hasattr(_json, 'JSONDecodeError')`` was **False**. ``srmech._toml`` was
identical, with ``TOMLDecodeError`` likewise absent.

But ``srmech._json.loads('{bad')`` raises a genuine ``json.JSONDecodeError``.
So the front door PROPAGATED an error type it did not NAME, and a caller could
not write ``except`` around it without importing the very module the ban exists
to remove. Four package files did exactly that — two importing ``json`` and two
re-running the whole ``tomllib`` / ``tomli`` version branch — for no other
purpose than to spell an exception in an ``except`` clause. They already parsed
through the front door.

Why a drain and not an allowance
================================
Allowancing those four with ``_EXC_TYPE_ALIAS`` was the obvious alternative and
is the WRONG one: ``_unallowed()`` filters by **FILE**, not by hit, so an
allowance exempts every ``json`` import in those 500+-line adapters forever.
``test_no_allowance_has_gone_stale`` only asks "does it still import";
``test_no_banned_import_is_dead`` only asks "is the name used"; the rc401 gate
counts READ calls only; and there is **no write-half ratchet** on the 64
``dumps`` sites. A future ``json.dumps`` added to either file would be invisible
to every guard. The drain has no such exposure.

This is a deliberate DEPARTURE from the tomllib precedent, which kept such
aliases as named necessities. The justification is the front-door contract
itself — and "breaking means fixing": design the correct thing rather than shim
around the break.

Pure stdlib + srmech; numpy-free; no ``abs()``.
"""

from __future__ import annotations

import pytest

from srmech import _json as srmech_json
from srmech import _toml as srmech_toml


def test_json_front_door_names_the_error_it_raises():
    """``_json.JSONDecodeError`` IS the class ``_json.loads`` actually raises.

    **Fails before rc407** with ``AttributeError``. Asserted by RAISING, not by
    comparing against ``json.JSONDecodeError`` — a look-alike alias would pass
    that comparison while failing the only thing a caller cares about."""
    assert hasattr(srmech_json, "JSONDecodeError"), (
        "srmech._json does not name the exception it raises; a caller must "
        "import stdlib json to catch it, which is the banned import this front "
        "door exists to remove")
    with pytest.raises(srmech_json.JSONDecodeError):
        srmech_json.loads("{bad json")


def test_toml_front_door_names_the_error_it_raises():
    """The peer assertion for ``_toml``. **Fails before rc407.**"""
    assert hasattr(srmech_toml, "TOMLDecodeError"), (
        "srmech._toml does not name the exception it raises; a caller must "
        "re-run the tomllib/tomli version branch just to spell the type")
    with pytest.raises(srmech_toml.TOMLDecodeError):
        srmech_toml.loads("a = ")


def test_the_aliases_are_the_backend_types_not_new_classes():
    """The alias must be the SAME class the backend raises.

    A freshly-declared ``class JSONDecodeError(Exception)`` would satisfy the
    tests above (the front door would raise its own type) while silently
    breaking every caller that still catches the stdlib one. Pin identity."""
    import json as _stdlib_json

    assert srmech_json.JSONDecodeError is _stdlib_json.JSONDecodeError

    # The TOML backend is version-branched: tomllib on 3.11+, the tomli
    # backport on 3.10. Bind from whichever one this interpreter selected,
    # rather than hard-coding either.
    backend = srmech_toml._stdlib_backend()
    assert srmech_toml.TOMLDecodeError is backend.TOMLDecodeError


@pytest.mark.parametrize(
    "relpath, banned",
    [
        ("srmech/amsc/adapters/literature_curated.py", "json"),
        ("srmech/amsc/adapters/substrate_parameterization.py", "json"),
        ("srmech/amsc/descriptor.py", "tomllib"),
        ("srmech/profile_loader.py", "tomllib"),
    ],
)
def test_the_four_exception_alias_importers_are_drained(relpath, banned):
    """None of the four still imports the banned module to name an exception.

    Source-level, because that is what the ban ledger counts (IMPORT
    STATEMENTS), and because the behavioural half is already covered above."""
    import ast
    from pathlib import Path

    path = Path(__file__).resolve().parent.parent / relpath
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name.split(".")[0])
                if alias.asname:
                    imported.add(alias.asname)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])

    assert banned not in imported, (
        f"{relpath} still imports {banned!r}. It parses through the srmech "
        f"front door already, so the import can only be naming an exception "
        f"type — use srmech._json.JSONDecodeError / "
        f"srmech._toml.TOMLDecodeError instead.")


def test_native_json_locals_are_gone_and_uses_still_resolve():
    """``srmech/_native/__init__.py``'s five function-local ``import json as
    _json`` are drained — and the seven uses they fed still resolve.

    This pairing is the point. The five were NOT independently deletable: the
    module-level import at ``:70`` binds ``json``, not ``_json``, and no
    module-level ``_json`` exists anywhere in the file, so deleting the imports
    alone raises ``NameError`` at every one of the seven call sites. The drain
    repoints them onto the module-level ``json`` — the same module object, so
    behaviour is identical.
    """
    import ast
    from pathlib import Path

    path = (Path(__file__).resolve().parent.parent
            / "srmech" / "_native" / "__init__.py")
    tree = ast.parse(path.read_text(encoding="utf-8"))

    local_aliases = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
        if alias.name == "json" and alias.asname == "_json"
    ]
    assert not local_aliases, (
        f"{len(local_aliases)} `import json as _json` statement(s) remain")

    dangling = [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "_json"
    ]
    assert not dangling, (
        f"`_json.` is still referenced at lines {dangling}, but nothing binds "
        f"the name any more — these would raise NameError at runtime. Repoint "
        f"them onto the module-level `json`.")

    # The module-level binding the uses were repointed onto must still exist.
    top_level = {
        alias.asname or alias.name
        for node in tree.body if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert "json" in top_level, (
        "the module-level `import json` is gone, so the repointed uses have "
        "nothing to resolve against")
