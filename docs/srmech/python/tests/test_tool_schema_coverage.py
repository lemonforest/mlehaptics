"""Coverage audit: every public callable in srmech.amsc.* and srmech.qm.*
has a registered tool-schema entry.

Task #220 — every operation surfaces via ``srmech.amsc.tool_schema`` so an
LLM consumer can discover the full callable surface without reading the
implementation. This test is the ratchet that keeps the tool-schema
extension in sync with the operations layer.

Exempt modules (intentionally not surfaced via tool-schema):

- ``srmech.amsc.tool_schema`` — the schema-API itself.
- ``srmech.amsc._native`` — ctypes shim (covered indirectly via
  ``srmech.amsc.format.sha256_bytes`` and ``read_ndjson``).
- ``srmech.amsc.gap_suggester`` — profile-loader internals; not a
  primitive operation.
- ``srmech.amsc.adapters`` — adapter package (per-source, surfaced via
  the bridge entries, not per-callable).
- ``srmech.amsc.attested`` — data subtree, not callables.
- ``srmech.profile_loader`` — profile-system internals.

Plus a small allowlist of catalog/descriptor helpers that the original
``_register_amsc_tools()`` already surfaces under their primary bridge
entries (``list_attested_sources``, ``get_attested_dataset``, etc.).
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from typing import Set

import pytest

import srmech.amsc
import srmech.qm
from srmech.amsc.tool_schema import get_tool_schema


# Modules / submodule prefixes intentionally not audited.
_EXEMPT_MODULE_PREFIXES = (
    "srmech.amsc.tool_schema",
    "srmech.amsc._native",
    "srmech.amsc.gap_suggester",
    "srmech.amsc.adapters",
    "srmech.amsc.attested",
)

# Specific functions that exist for backwards compatibility, profile-loader
# wiring, or as helpers that wrap a primary entry already registered.
_EXEMPT_FUNCTION_NAMES = frozenset({
    # catalog.* — additional helpers that compose `list_attested_sources`,
    # `get_attested_dataset`, `register_attested_root` (already registered).
    "srmech.amsc.catalog.list_registered_roots",
    "srmech.amsc.catalog.use_local_kernel",
    "srmech.amsc.catalog.clear_local_kernel",
    "srmech.amsc.catalog.get_local_kernel_state",
    "srmech.amsc.catalog.get_attested_descriptor",
    "srmech.amsc.catalog.attestation_audit",
    "srmech.amsc.catalog.iter_attested_dataset",
    # descriptor.* — TOML loader helpers around descriptor_hash (registered).
    "srmech.amsc.descriptor.load_descriptor",
    "srmech.amsc.descriptor.render_template",
    "srmech.amsc.descriptor.discover_descriptors",
    # format.* — validate / write helpers around sha256_bytes + read_ndjson
    # (already registered).
    "srmech.amsc.format.validate_mpr_record",
    "srmech.amsc.format.write_ndjson",
    # cascade.* — back-compat aliases of canonical names already registered
    # (the precursor's call-site names; see srmech.amsc.cascade).
    "srmech.amsc.cascade.class_k_pin_slot_at_zero",  # = pin_slot_at_zero
    "srmech.amsc.cascade.class_c_reorient",          # = reorient
    "srmech.amsc.cascade.best_rat_signed",           # = best_rational_signed
    # cascade.atoms.* / cascade.compose.* — the two-tier split (#751 / F208).
    # These submodules are the new canonical *homes* of the cascade ops, but
    # the tool-schema registers each op under its STABLE flat public name
    # ``srmech.amsc.cascade.<op>`` (introspection stability per #751) — which
    # IS registered. The submodule-dotted names are the same objects re-
    # exported flat, so they are exempt here exactly like the aliases above.
    "srmech.amsc.cascade.atoms.pin_slot_at_zero",
    "srmech.amsc.cascade.atoms.reorient",
    "srmech.amsc.cascade.atoms.magnitude",
    "srmech.amsc.cascade.atoms.chiral_flip",
    "srmech.amsc.cascade.atoms.chiral_dual",
    "srmech.amsc.cascade.atoms.net_chirality",
    "srmech.amsc.cascade.compose.cyclic_gcd",
    "srmech.amsc.cascade.compose.best_rational_signed",
})


def _walk_public_callables(pkg) -> Set[str]:
    """Return dotted-path names of every public top-level callable in
    `pkg` and its submodules."""
    out: Set[str] = set()
    prefix = pkg.__name__ + "."
    for finder, name, ispkg in pkgutil.walk_packages(pkg.__path__, prefix):
        if any(name.startswith(p) for p in _EXEMPT_MODULE_PREFIXES):
            continue
        try:
            mod = importlib.import_module(name)
        except Exception:
            continue
        for fn_name, fn in inspect.getmembers(mod, inspect.isfunction):
            if fn_name.startswith("_"):
                continue
            # Skip re-exports: only count if the function is defined here.
            if getattr(fn, "__module__", None) != mod.__name__:
                continue
            dotted = f"{mod.__name__}.{fn_name}"
            out.add(dotted)
    return out


def test_amsc_public_callables_have_tool_entries():
    """Every public function in srmech.amsc.* (minus exemptions) is
    registered in the tool schema."""
    schema = get_tool_schema()
    registered = {t.name for t in schema.tools}
    callables = _walk_public_callables(srmech.amsc)
    missing = sorted(callables - registered - _EXEMPT_FUNCTION_NAMES)
    assert not missing, f"Missing tool-schema entries for srmech.amsc:\n  " + "\n  ".join(missing)


def test_qm_public_callables_have_tool_entries():
    """Every public function in srmech.qm.* is registered in the tool schema."""
    schema = get_tool_schema()
    registered = {t.name for t in schema.tools}
    callables = _walk_public_callables(srmech.qm)
    missing = sorted(callables - registered)
    assert not missing, f"Missing tool-schema entries for srmech.qm:\n  " + "\n  ".join(missing)


def test_tool_schema_entries_have_required_fields():
    """Every entry has non-empty name / owner / summary, and a parameters
    tuple that is well-typed."""
    schema = get_tool_schema()
    for t in schema.tools:
        assert t.name and "." in t.name, f"empty/invalid name: {t.name!r}"
        assert t.owner, f"empty owner in {t.name}"
        assert t.summary, f"empty summary in {t.name}"
        assert isinstance(t.parameters, tuple), (
            f"parameters not tuple in {t.name}: {type(t.parameters)}"
        )
        for p in t.parameters:
            assert p.name, f"empty param name in {t.name}"
            assert p.type, f"empty param type in {t.name}.{p.name}"


def test_tool_schema_owner_is_srmech_for_builtins():
    """All builtin entries have owner='srmech' (profile entries would
    have a different owner; we only register srmech-owned here)."""
    schema = get_tool_schema()
    for t in schema.tools:
        assert t.owner == "srmech", (
            f"Unexpected owner {t.owner!r} on builtin entry {t.name}"
        )


def test_tool_schema_view_is_jsonable():
    """The view dict is JSON-serialisable round-trip clean."""
    import json
    from srmech.amsc.tool_schema import tool_schema_view

    view = tool_schema_view()
    s = json.dumps(view, sort_keys=True)
    assert len(s) > 1000  # non-trivial registry
    round_trip = json.loads(s)
    assert round_trip == view


def test_tool_schema_total_count_meets_floor():
    """Coverage floor: at least ~80 entries (14-class primitives + qm ops
    + bridge entries). Ratchet test — count is allowed to grow but not
    silently drop."""
    schema = get_tool_schema()
    assert len(schema.tools) >= 80, (
        f"Tool-schema count fell below floor: {len(schema.tools)} < 80"
    )


def test_no_duplicate_tool_names():
    """Each tool entry has a unique dotted name."""
    schema = get_tool_schema()
    names = [t.name for t in schema.tools]
    duplicates = {n for n in names if names.count(n) > 1}
    assert not duplicates, f"Duplicate tool entries: {sorted(duplicates)}"


def test_tool_schema_categories_match_module_structure():
    """Sanity-check that categories track the module they belong to."""
    schema = get_tool_schema()
    for t in schema.tools:
        # name is e.g. 'srmech.amsc.cyclic.gcd' or 'srmech.qm.spin.pauli_matrices'
        parts = t.name.split(".")
        # category is a free-form taxonomy hint; just ensure it's a
        # plausible match for one of the path components or a known
        # bridge category.
        plausible = (
            t.category in parts
            or t.category.startswith("qm.")  # qm.* operations layer
            or t.category in ("format", "descriptor", "catalog")
        )
        assert plausible, (
            f"category {t.category!r} doesn't match module path "
            f"{t.name!r}"
        )
