"""Regression: the ``srmech.amsc.cascade.sedenion_register`` ToolEntry resolves
to a callable even after its same-named submodule is imported.

The factory ``sedenion_register`` and its home module ``sedenion_register.py``
share a name; importing the submodule rebinds the package attribute from the
re-exported function to the MODULE object, so the flat registry name
``srmech.amsc.cascade.sedenion_register`` resolved to a non-callable module and
tripped the W7 schema/signature-drift ratchet
(``test_mcp.py::test_schema_signature_alignment_no_drift``). v0.7.5rc1 makes the
dotted-name resolver prefer the same-named callable defined inside a colliding
module — the "module X re-exports callable X" convention.
"""

from __future__ import annotations

import importlib
import inspect

from srmech.mcp._tools import _resolve_dotted_callable


def test_sedenion_register_resolves_after_submodule_import() -> None:
    # Force the collision: importing the submodule makes Python rebind the
    # package attribute to the MODULE object (shadowing the re-exported factory).
    importlib.import_module("srmech.amsc.cascade.sedenion_register")

    fn = _resolve_dotted_callable("srmech.amsc.cascade.sedenion_register")
    assert callable(fn), "the ToolEntry must resolve to a callable, not a module"
    assert not inspect.ismodule(fn), "must resolve to the factory, not the module"


def test_other_colliding_flat_names_still_resolve() -> None:
    """A non-colliding flat name (no same-named submodule) is unaffected."""
    fn = _resolve_dotted_callable("srmech.amsc.cascade.cd_basis_product")
    assert callable(fn) and not inspect.ismodule(fn)
