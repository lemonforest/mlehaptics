"""THE registry-completeness ratchet (`#T1101`, v0.9.0rc416).

Every callable a public module puts in its ``__all__`` either resolves to a
``ToolEntry`` or sits on a DOCUMENTED, DOWN-ONLY allowlist. A new one that does
neither fails here, at the moment of omission.

WHY THIS EXISTS — the defect is measured, not imagined
======================================================
``srmech.biology.coupling.fold_identity`` shipped in ``coupling.__all__`` from
`#T723` and carried NO ``ToolEntry`` until rc414 — roughly 300 rcs. All seven of
its coupling siblings had one. The consequence was not "it was undocumented":

* it was absent from ``describe()``, from the MCP tool list, and from every
  registry-driven census;
* ``srmech.introspect.search`` could not return it at any ``k``, in any
  phrasing, because the index is BUILT from the registry;
* and — this is the part that makes it a defect rather than a gap — of the
  other 559 registry rows, the number whose ``summary`` / ``explanation`` /
  ``example`` / ``parameters`` / ``returns`` / ``composes`` / ``preserves``
  mention the token ``fold_identity`` anywhere is **ZERO**. The row a composer
  would land on instead, ``fold_encode_recoverable``, has a well-written
  SIBLINGS paragraph naming ``fold_encode`` / ``fold_spectrum`` /
  ``fractal_spectrum`` and omitting the one op that answers *"can this be
  gated?"*.

So the surface the project designated as its API contract returned a SILENT
FALSE NEGATIVE, and a research leg read it and concluded ``RecoverableFold``
"cannot be gated" while its purpose-built three-valued gate sat 215 lines below
the line being read. An op invisible to introspection is, for an LLM consumer,
an op that does not exist
(``[[project_introspect_surface_is_the_api_contract_not_documentation]]``).

Nothing about that is a documentation problem, which is why the fix is a gate
and not prose. It is mechanically decidable, it lives in one file, and it fires
the moment the omission is written rather than 300 rcs later.

THE RETRO-CHECK IS THE ACCEPTANCE CRITERION
===========================================
A gate that would not have caught the defect that motivated it is not the gate.
:func:`test_the_ratchet_would_have_fired_on_fold_identity_pre_rc414` runs the
predicate against ``coupling.py`` and ``tool_schema.py`` AS THEY WERE at
``966ce2dcb^`` — the commit before rc414 registered the op — reading them out of
git rather than trusting a remembered claim, and asserts the predicate reports
``fold_identity`` MISSING there while reporting it COVERED at HEAD. If git is
unavailable the test SKIPS loudly rather than passing.

SCOPE — what "public surface point" means, exactly
==================================================
For every module whose dotted path has no ``_``-prefixed component, and every
non-``_`` name in its ``__all__`` that resolves to a **callable that is not a
class and not a module** and whose ``__module__`` is inside ``srmech``:

* if the DEFINING module is itself public and exports the same name, the pair
  is counted THERE and nowhere else — the registry homes ops by defining
  module (ADR-0010), so a package-level re-export is the same op at a second
  path, not a second op;
* otherwise the re-export IS the public surface point (this is what keeps an
  op defined in a private ``_impl`` module and re-exported publicly in scope).

Three exclusions, each because a DIFFERENT registry owns the answer:

* **classes** — the operand/noun surface is ``carrier_schema()``, not the tool
  registry, and ``describe()["tools"]["covers"]`` says so verbatim;
* **modules** — a submodule bound into a package ``__all__`` is a namespace
  re-export, not a callable;
* **non-callables** — a constant is not an op.

Coverage is by OBJECT IDENTITY (``id(obj)``), never by leaf name. Name matching
would have accepted 11 false pairs at rc416 — ``srmech.bus.list`` "covered" by
``srmech.introspect.list``, ``srmech.signal_processing.lookup`` "covered" by
``srmech.introspect.naming.lookup`` — which is the exact shape of laundering
this ratchet exists to refuse.

THE ALLOWLIST IS THE RISK SURFACE
=================================
A bare-name allowlist is the silent-exemption shape this project has found
repeatedly. So every entry carries a REASON CODE from a CLOSED set, and every
code carries an EXIT CONDITION — what would remove entries bearing it. Two of
the five codes are additionally MACHINE-CHECKED against the path they claim to
describe (:func:`test_reason_codes_match_the_surface_they_claim`), so an entry
cannot wear a cheap label to escape the expensive one.

The largest bucket is deliberately named ``OPEN_REGISTRATION`` and is
deliberately not an exemption. It is DEBT: 125 of the 184 seeded entries are
ops whose registration decision has simply never been made. Calling that
"exempt" would be the discharge; calling it debt is what makes the ceiling
mean something as it drains.
"""
from __future__ import annotations

import importlib
import inspect
import pkgutil
import subprocess
from pathlib import Path
from typing import Dict, Set, Tuple

import pytest

import srmech
from srmech.introspect.tool_schema import get_tool_schema, warmup_all

# ── the reason-code vocabulary — a CLOSED set, each with an exit condition ───

#: ADR-0009 §4 exempts ``srmech.mcp`` and ``srmech.llm`` BY NAME ("Nothing else
#: is exempt"). These are the JSON-RPC / Anthropic wire adapters; a tool row
#: describing the thing that serves tool rows is circular.
#: EXITS WHEN: ADR-0009 §4's exemption list changes. Machine-checked.
ADR0009_EXEMPT = "ADR0009_EXEMPT"

#: argparse wiring under ``srmech.cli`` — ``add_arguments`` / ``run`` /
#: ``run_<verb>`` pairs that a parser calls, never a composer. They take an
#: ``argparse.Namespace`` and return a process exit code, so a ToolEntry's
#: ``parameters`` / ``returns`` contract has nothing to say about them.
#: EXITS WHEN: the CLI grows a callable-op contract (a subcommand that takes
#: and returns values rather than a Namespace and a status). Machine-checked.
CLI_SUBCOMMAND = "CLI_SUBCOMMAND"

#: mutates process-global registry / cache / alias state: ``register*``,
#: ``unregister*``, ``clear*``, ``lock_*`` / ``unlock_*``, ``reset_*``,
#: ``warmup_all``, ``load_extension_file``, ``use_local_kernel``,
#: ``set_type_aliases``. Registering the registrar inside the registry it
#: mutates is the circularity; more practically, these have no value contract
#: — their whole effect is on state a later call observes.
#: EXITS WHEN: the registry gains a self-describing mutator row shape (an
#: entry whose ``returns`` can honestly say "the registry, mutated").
REGISTRY_MUTATOR = "REGISTRY_MUTATOR"

#: the AMSC adapter PROTOCOL: one uniform ``(fetch, parse)`` pair per adapter
#: class, plus the ``get_adapter`` / ``run`` / ``attest`` dispatch trio. Seven
#: modules each export a function called ``parse``; seven registry rows called
#: ``parse`` is not an answer a composer can act on. What a composer needs is
#: a row for the DISPATCHER, keyed by descriptor.
#: EXITS WHEN: the dispatcher earns a row that names the adapter classes in
#: its ``parameters`` — at which point the seven pairs stay unregistered ON
#: PURPOSE and move to a stated design, not a gap.
PROTOCOL_UNIFORM = "PROTOCOL_UNIFORM"

#: ⚠️ DEBT, NOT AN EXEMPTION. A public op whose registration decision has
#: never been made. Every entry here is a live ``fold_identity``-shaped risk:
#: reachable by import, invisible to ``describe()``, ``search`` and MCP.
#: EXITS WHEN: someone writes the ``ToolEntry``. That is the whole exit
#: condition, and it is why this bucket is counted separately below.
OPEN_REGISTRATION = "OPEN_REGISTRATION"

_REASON_CODES = frozenset({ADR0009_EXEMPT, CLI_SUBCOMMAND, REGISTRY_MUTATOR,
                           PROTOCOL_UNIFORM, OPEN_REGISTRATION})

#: The mutator verbs ``REGISTRY_MUTATOR`` is allowed to cover. Closed, so a
#: future entry cannot claim the code by inventing a verb.
_MUTATOR_PREFIXES = ("register", "unregister", "clear", "lock_dispatch_table",
                     "unlock_dispatch_table", "reset_", "load_extension_file",
                     "warmup_all", "use_local_kernel", "set_type_aliases",
                     "load_type_aliases_toml", "emit_if_publishing")


# ── the scope predicate ──────────────────────────────────────────────────────

def _public_modules() -> Dict[str, object]:
    """Every importable module whose dotted path has no ``_`` component."""
    names = {"srmech"} | {
        mi.name
        for mi in pkgutil.walk_packages(srmech.__path__, prefix="srmech.")
        if not any(p.startswith("_") for p in mi.name.split(".")[1:])
    }
    out = {}
    for name in sorted(names):
        try:
            out[name] = importlib.import_module(name)
        except Exception:                                      # noqa: BLE001
            continue          # an optional-dependency module is not surface
    return out


def public_surface() -> Dict[str, int]:
    """``{"<public.path>": id(obj)}`` — the in-scope public callables."""
    mods = _public_modules()
    alls = {n: tuple(getattr(m, "__all__", ()) or ()) for n, m in mods.items()}
    scope: Dict[str, int] = {}
    for name, exported in alls.items():
        module = mods[name]
        for leaf in exported:
            if leaf.startswith("_"):
                continue
            obj = getattr(module, leaf, None)
            if obj is None or inspect.ismodule(obj) or isinstance(obj, type):
                continue
            if not callable(obj):
                continue
            owner = getattr(obj, "__module__", "") or ""
            if not owner.startswith("srmech"):
                continue
            if owner != name and owner in alls and leaf in alls[owner]:
                continue          # counted at its defining module instead
            scope[f"{name}.{leaf}"] = id(obj)
    return scope


def registered_object_ids() -> Set[int]:
    """``{id(obj)}`` for every name the tool registry carries.

    Identity, not name. A ``ToolEntry`` name that cannot be resolved is itself
    a defect and is surfaced by
    :func:`test_every_tool_entry_name_resolves_to_a_live_object`.
    """
    warmup_all()
    out: Set[int] = set()
    for entry in get_tool_schema().tools:
        module, _, leaf = entry.name.rpartition(".")
        try:
            out.add(id(getattr(importlib.import_module(module), leaf)))
        except Exception:                                      # noqa: BLE001
            continue
    return out


def unaccounted(allowlist: Dict[str, str]) -> Tuple[str, ...]:
    """Public surface points that have NEITHER a ToolEntry NOR an allowlist row."""
    covered = registered_object_ids()
    return tuple(sorted(path for path, oid in public_surface().items()
                        if oid not in covered and path not in allowlist))


# ── (a) the DOWN-ONLY allowlist ─────────────────────────────────────────────
#
# ⚠️ DOWN-ONLY. ``CEIL_REGISTRY_GAPS`` below pins the length and a test asserts
# it never grows. An entry leaves this list by landing a ``ToolEntry`` (then
# DELETE the row and LOWER the ceiling). NEVER add an entry to make a failing
# build pass — a new public op with no ToolEntry is the exact regression this
# ratchet exists to catch, and it is the regression that cost 300 rcs once.
#
# Seeded at the MEASURED residual against v0.9.0rc415 (registry 560, native
# ABI 12): 744 in-scope public callables, 184 of them uncovered. Every row is
# a real measurement, not an inherited number.
#
# By code:  OPEN_REGISTRATION 125 · REGISTRY_MUTATOR 24 · PROTOCOL_UNIFORM 19
#           · CLI_SUBCOMMAND 12 · ADR0009_EXEMPT 4
_KNOWN_REGISTRY_GAPS: Dict[str, str] = {
    # ── srmech.amsc.adapters ──
    'srmech.amsc.adapters.attest': PROTOCOL_UNIFORM,
    'srmech.amsc.adapters.get_adapter': PROTOCOL_UNIFORM,
    'srmech.amsc.adapters.run': PROTOCOL_UNIFORM,
    # ── srmech.amsc.adapters.csv_bulk ──
    'srmech.amsc.adapters.csv_bulk.fetch': PROTOCOL_UNIFORM,
    'srmech.amsc.adapters.csv_bulk.parse': PROTOCOL_UNIFORM,
    # ── srmech.amsc.adapters.geotiff_bbox ──
    'srmech.amsc.adapters.geotiff_bbox.fetch': PROTOCOL_UNIFORM,
    'srmech.amsc.adapters.geotiff_bbox.parse': PROTOCOL_UNIFORM,
    # ── srmech.amsc.adapters.html_scraper ──
    'srmech.amsc.adapters.html_scraper.fetch': PROTOCOL_UNIFORM,
    'srmech.amsc.adapters.html_scraper.parse': PROTOCOL_UNIFORM,
    # ── srmech.amsc.adapters.json_api ──
    'srmech.amsc.adapters.json_api.fetch': PROTOCOL_UNIFORM,
    'srmech.amsc.adapters.json_api.parse': PROTOCOL_UNIFORM,
    # ── srmech.amsc.adapters.literature_curated ──
    'srmech.amsc.adapters.literature_curated.fetch': PROTOCOL_UNIFORM,
    'srmech.amsc.adapters.literature_curated.parse': PROTOCOL_UNIFORM,
    # ── srmech.amsc.adapters.netcdf_grid ──
    'srmech.amsc.adapters.netcdf_grid.fetch': PROTOCOL_UNIFORM,
    'srmech.amsc.adapters.netcdf_grid.parse': PROTOCOL_UNIFORM,
    # ── srmech.amsc.adapters.substrate_parameterization ──
    'srmech.amsc.adapters.substrate_parameterization.config_for':
        PROTOCOL_UNIFORM,
    'srmech.amsc.adapters.substrate_parameterization.fetch': PROTOCOL_UNIFORM,
    'srmech.amsc.adapters.substrate_parameterization.parse': PROTOCOL_UNIFORM,
    'srmech.amsc.adapters.substrate_parameterization.parse_substrate_config':
        PROTOCOL_UNIFORM,
    # ── srmech.amsc.catalog ──
    'srmech.amsc.catalog.attestation_audit': OPEN_REGISTRATION,
    'srmech.amsc.catalog.clear_local_kernel': REGISTRY_MUTATOR,
    'srmech.amsc.catalog.get_attested_descriptor': OPEN_REGISTRATION,
    'srmech.amsc.catalog.get_local_kernel_state': OPEN_REGISTRATION,
    'srmech.amsc.catalog.iter_attested_dataset': OPEN_REGISTRATION,
    'srmech.amsc.catalog.list_registered_roots': OPEN_REGISTRATION,
    'srmech.amsc.catalog.use_local_kernel': REGISTRY_MUTATOR,
    # ── srmech.amsc.descriptor ──
    'srmech.amsc.descriptor.discover_descriptors': OPEN_REGISTRATION,
    'srmech.amsc.descriptor.load_descriptor': OPEN_REGISTRATION,
    'srmech.amsc.descriptor.render_template': OPEN_REGISTRATION,
    # ── srmech.amsc.format ──
    'srmech.amsc.format.sha256_hex': OPEN_REGISTRATION,
    'srmech.amsc.format.sha256_raw': OPEN_REGISTRATION,
    'srmech.amsc.format.validate_mpr_record': OPEN_REGISTRATION,
    'srmech.amsc.format.write_ndjson': OPEN_REGISTRATION,
    # ── srmech.amsc.gap_suggester ──
    'srmech.amsc.gap_suggester.register_classifier': REGISTRY_MUTATOR,
    'srmech.amsc.gap_suggester.register_probes': REGISTRY_MUTATOR,
    'srmech.amsc.gap_suggester.suggest_gap_collections': OPEN_REGISTRATION,
    # ── srmech.apokatastasis.eisenstein ──
    'srmech.apokatastasis.eisenstein.eisenstein': OPEN_REGISTRATION,
    # ── srmech.apokatastasis.ellbase ──
    'srmech.apokatastasis.ellbase.elliptic_lagrange_basis': OPEN_REGISTRATION,
    # ── srmech.apokatastasis.eta_quotient ──
    'srmech.apokatastasis.eta_quotient.eta_quotient': OPEN_REGISTRATION,
    # ── srmech.apokatastasis.modular_forms_ring ──
    'srmech.apokatastasis.modular_forms_ring.modular_forms_ring':
        OPEN_REGISTRATION,
    # ── srmech.apokatastasis.quasimodular_forms_ring ──
    'srmech.apokatastasis.quasimodular_forms_ring.eisenstein_e2':
        OPEN_REGISTRATION,
    'srmech.apokatastasis.quasimodular_forms_ring.quasimodular_forms_ring':
        OPEN_REGISTRATION,
    # ── srmech.biology.genome ──
    'srmech.biology.genome.clear_type_aliases': REGISTRY_MUTATOR,
    'srmech.biology.genome.load_type_aliases_toml': REGISTRY_MUTATOR,
    'srmech.biology.genome.set_type_aliases': REGISTRY_MUTATOR,
    # ── srmech.bus ──
    'srmech.bus.bus_dir': OPEN_REGISTRATION,
    'srmech.bus.channel_id_from_name': OPEN_REGISTRATION,
    'srmech.bus.cipher_backend_name': OPEN_REGISTRATION,
    'srmech.bus.connect': OPEN_REGISTRATION,
    'srmech.bus.is_posix_uds': OPEN_REGISTRATION,
    'srmech.bus.list': OPEN_REGISTRATION,
    'srmech.bus.new_correlation_id': OPEN_REGISTRATION,
    'srmech.bus.pipe': OPEN_REGISTRATION,
    'srmech.bus.secret_kwargs': OPEN_REGISTRATION,
    'srmech.bus.serve': OPEN_REGISTRATION,
    'srmech.bus.transport_kind': OPEN_REGISTRATION,
    # ── srmech.bus.aio ──
    'srmech.bus.aio.connect': OPEN_REGISTRATION,
    'srmech.bus.aio.list_endpoints': OPEN_REGISTRATION,
    'srmech.bus.aio.pipe': OPEN_REGISTRATION,
    'srmech.bus.aio.serve': OPEN_REGISTRATION,
    # ── srmech.cascade ──
    'srmech.cascade.cd_add': OPEN_REGISTRATION,
    'srmech.cascade.cd_basis': OPEN_REGISTRATION,
    'srmech.cascade.left_mult_matrix': OPEN_REGISTRATION,
    # ── srmech.cascade.compose ──
    'srmech.cascade.compose.greedy_bipartite_alignment': OPEN_REGISTRATION,
    # ── srmech.cascade.matrix_cascades ──
    'srmech.cascade.matrix_cascades.eig_exact': OPEN_REGISTRATION,
    'srmech.cascade.matrix_cascades.eigvec_exact': OPEN_REGISTRATION,
    'srmech.cascade.matrix_cascades.eigvec_exact_float': OPEN_REGISTRATION,
    'srmech.cascade.matrix_cascades.factor_integer_poly': OPEN_REGISTRATION,
    'srmech.cascade.matrix_cascades.jordan_chains_exact': OPEN_REGISTRATION,
    'srmech.cascade.matrix_cascades.jordan_form_exact': OPEN_REGISTRATION,
    'srmech.cascade.matrix_cascades.separate_frame_curvature':
        OPEN_REGISTRATION,
    # ── srmech.cascade.one ──
    'srmech.cascade.one.one_dim': OPEN_REGISTRATION,
    'srmech.cascade.one.one_flat_rational': OPEN_REGISTRATION,
    'srmech.cascade.one.one_grammar_slots': OPEN_REGISTRATION,
    'srmech.cascade.one.one_imag_dims': OPEN_REGISTRATION,
    'srmech.cascade.one.one_matrix': OPEN_REGISTRATION,
    'srmech.cascade.one.one_partition': OPEN_REGISTRATION,
    'srmech.cascade.one.one_plane_counts': OPEN_REGISTRATION,
    'srmech.cascade.one.separate_winding_curvature': OPEN_REGISTRATION,
    'srmech.cascade.one.to_scalar': OPEN_REGISTRATION,
    'srmech.cascade.one.winding_tower': OPEN_REGISTRATION,
    # ── srmech.cascade.parallel ──
    'srmech.cascade.parallel.sectorize': OPEN_REGISTRATION,
    # ── srmech.cascade.sedenion_register ──
    'srmech.cascade.sedenion_register.sed_carry': OPEN_REGISTRATION,
    'srmech.cascade.sedenion_register.sed_clean': OPEN_REGISTRATION,
    'srmech.cascade.sedenion_register.sed_correct': OPEN_REGISTRATION,
    'srmech.cascade.sedenion_register.sed_couple_working': OPEN_REGISTRATION,
    'srmech.cascade.sedenion_register.sed_is_navigable': OPEN_REGISTRATION,
    'srmech.cascade.sedenion_register.sed_materialize': OPEN_REGISTRATION,
    'srmech.cascade.sedenion_register.sed_navigate': OPEN_REGISTRATION,
    'srmech.cascade.sedenion_register.sed_navmap': OPEN_REGISTRATION,
    'srmech.cascade.sedenion_register.sed_read_unbind': OPEN_REGISTRATION,
    'srmech.cascade.sedenion_register.sed_slots': OPEN_REGISTRATION,
    'srmech.cascade.sedenion_register.sed_uncouple_working': OPEN_REGISTRATION,
    'srmech.cascade.sedenion_register.sed_write': OPEN_REGISTRATION,
    # ── srmech.cli ──
    'srmech.cli.main': CLI_SUBCOMMAND,
    # ── srmech.cli.bus ──
    'srmech.cli.bus.add_arguments': CLI_SUBCOMMAND,
    'srmech.cli.bus.run': CLI_SUBCOMMAND,
    'srmech.cli.bus.run_list': CLI_SUBCOMMAND,
    'srmech.cli.bus.run_pipe': CLI_SUBCOMMAND,
    'srmech.cli.bus.run_send': CLI_SUBCOMMAND,
    'srmech.cli.bus.run_serve': CLI_SUBCOMMAND,
    'srmech.cli.bus.run_tap': CLI_SUBCOMMAND,
    # ── srmech.cli.dsl ──
    'srmech.cli.dsl.add_arguments': CLI_SUBCOMMAND,
    'srmech.cli.dsl.run': CLI_SUBCOMMAND,
    # ── srmech.cli.mcp ──
    'srmech.cli.mcp.add_arguments': CLI_SUBCOMMAND,
    'srmech.cli.mcp.run': CLI_SUBCOMMAND,
    # ── srmech.dsl ──
    'srmech.dsl.alias': OPEN_REGISTRATION,
    'srmech.dsl.build_aliases_from_toml_str': OPEN_REGISTRATION,
    'srmech.dsl.build_chain_from_dict': OPEN_REGISTRATION,
    'srmech.dsl.build_chain_from_toml': OPEN_REGISTRATION,
    'srmech.dsl.build_chain_from_toml_str': OPEN_REGISTRATION,
    'srmech.dsl.chain': OPEN_REGISTRATION,
    'srmech.dsl.get_class_descriptor': OPEN_REGISTRATION,
    'srmech.dsl.get_descriptor': OPEN_REGISTRATION,
    'srmech.dsl.list_alias_descriptors': OPEN_REGISTRATION,
    'srmech.dsl.list_cascade_ops': OPEN_REGISTRATION,
    'srmech.dsl.list_classes': OPEN_REGISTRATION,
    'srmech.dsl.load_aliases_toml': OPEN_REGISTRATION,
    'srmech.dsl.load_catalog': OPEN_REGISTRATION,
    'srmech.dsl.load_chain_toml': OPEN_REGISTRATION,
    'srmech.dsl.load_class_catalog': OPEN_REGISTRATION,
    'srmech.dsl.lookup_cascade_op': OPEN_REGISTRATION,
    'srmech.dsl.make_class': OPEN_REGISTRATION,
    'srmech.dsl.register_alias_dir': REGISTRY_MUTATOR,
    'srmech.dsl.register_catalog_dir': REGISTRY_MUTATOR,
    'srmech.dsl.register_class_dir': REGISTRY_MUTATOR,
    'srmech.dsl.resolve_alias_descriptor': OPEN_REGISTRATION,
    'srmech.dsl.run_class_method': OPEN_REGISTRATION,
    # ── srmech.introspect ──
    'srmech.introspect.describe_shape': OPEN_REGISTRATION,
    'srmech.introspect.emit_if_publishing': REGISTRY_MUTATOR,
    'srmech.introspect.introspect_dir': OPEN_REGISTRATION,
    'srmech.introspect.native_status': OPEN_REGISTRATION,
    'srmech.introspect.parse': OPEN_REGISTRATION,
    'srmech.introspect.serialize': OPEN_REGISTRATION,
    # ── srmech.introspect.tool_schema ──
    'srmech.introspect.tool_schema.load_extension_file': REGISTRY_MUTATOR,
    'srmech.introspect.tool_schema.register_profile_tools': REGISTRY_MUTATOR,
    'srmech.introspect.tool_schema.register_tool': REGISTRY_MUTATOR,
    'srmech.introspect.tool_schema.unregister_profile_tools': REGISTRY_MUTATOR,
    'srmech.introspect.tool_schema.warmup_all': REGISTRY_MUTATOR,
    # ── srmech.math.q ──
    'srmech.math.q.to_q': OPEN_REGISTRATION,
    # ── srmech.mcp ──
    'srmech.mcp.invoke_tool': ADR0009_EXEMPT,
    'srmech.mcp.serve_http_sse': ADR0009_EXEMPT,
    'srmech.mcp.serve_stdio': ADR0009_EXEMPT,
    'srmech.mcp.tool_entries_to_mcp_defs': ADR0009_EXEMPT,
    # ── srmech.profile_loader ──
    'srmech.profile_loader.list_profiles': OPEN_REGISTRATION,
    'srmech.profile_loader.profile': OPEN_REGISTRATION,
    'srmech.profile_loader.reset_for_testing': REGISTRY_MUTATOR,
    # ── srmech.rbs_lm ──
    'srmech.rbs_lm.encode_bigram_l1': OPEN_REGISTRATION,
    'srmech.rbs_lm.encode_sentence_l3': OPEN_REGISTRATION,
    'srmech.rbs_lm.encode_skeleton_l2': OPEN_REGISTRATION,
    'srmech.rbs_lm.encode_word_k4': OPEN_REGISTRATION,
    'srmech.rbs_lm.sim_k4_batch': OPEN_REGISTRATION,
    'srmech.rbs_lm.token_seed': OPEN_REGISTRATION,
    # ── srmech.rbs_lm.grounding ──
    'srmech.rbs_lm.grounding.ground_tool_schema': OPEN_REGISTRATION,
    # ── srmech.signal_processing.cascade_dispatcher ──
    'srmech.signal_processing.cascade_dispatcher.begin_cascade':
        OPEN_REGISTRATION,
    'srmech.signal_processing.cascade_dispatcher.current_cascade':
        OPEN_REGISTRATION,
    'srmech.signal_processing.cascade_dispatcher.dispatch': OPEN_REGISTRATION,
    'srmech.signal_processing.cascade_dispatcher.end_cascade':
        OPEN_REGISTRATION,
    'srmech.signal_processing.cascade_dispatcher.is_dispatch_table_locked':
        OPEN_REGISTRATION,
    'srmech.signal_processing.cascade_dispatcher.lock_dispatch_table':
        REGISTRY_MUTATOR,
    'srmech.signal_processing.cascade_dispatcher.resolve_path':
        OPEN_REGISTRATION,
    'srmech.signal_processing.cascade_dispatcher.unlock_dispatch_table':
        REGISTRY_MUTATOR,
    # ── srmech.signal_processing.form_function_rotation ──
    'srmech.signal_processing.form_function_rotation.cascade_compose_rotations':
        OPEN_REGISTRATION,
    'srmech.signal_processing.form_function_rotation.compute_content_stride':
        OPEN_REGISTRATION,
    'srmech.signal_processing.form_function_rotation.form_function_rotate':
        OPEN_REGISTRATION,
    'srmech.signal_processing.form_function_rotation.'
    'inverse_form_function_rotate': OPEN_REGISTRATION,
    'srmech.signal_processing.form_function_rotation.'
    'verify_rotation_class_n_cycle_order': OPEN_REGISTRATION,
    # ── srmech.signal_processing.path_registry ──
    'srmech.signal_processing.path_registry.clear_registry': REGISTRY_MUTATOR,
    'srmech.signal_processing.path_registry.has_path': OPEN_REGISTRATION,
    'srmech.signal_processing.path_registry.lookup': OPEN_REGISTRATION,
    'srmech.signal_processing.path_registry.register': REGISTRY_MUTATOR,
    'srmech.signal_processing.path_registry.register_lazy_loader':
        REGISTRY_MUTATOR,
    'srmech.signal_processing.path_registry.registered_ops': OPEN_REGISTRATION,
    # ── srmech.signal_processing.profiling ──
    'srmech.signal_processing.profiling.cell_grid': OPEN_REGISTRATION,
    'srmech.signal_processing.profiling.clear_records': REGISTRY_MUTATOR,
    'srmech.signal_processing.profiling.iter_records': OPEN_REGISTRATION,
    'srmech.signal_processing.profiling.record_profile': OPEN_REGISTRATION,
    # ── srmech.signal_processing.rbs_hdc_instrument ──
    'srmech.signal_processing.rbs_hdc_instrument.decode_loe_fingerprint':
        OPEN_REGISTRATION,
    'srmech.signal_processing.rbs_hdc_instrument.encode_loe_content':
        OPEN_REGISTRATION,
    'srmech.signal_processing.rbs_hdc_instrument.mint_cascade_composition':
        OPEN_REGISTRATION,
    'srmech.signal_processing.rbs_hdc_instrument.mint_class_operator':
        OPEN_REGISTRATION,
    'srmech.signal_processing.rbs_hdc_instrument.mint_stance_fingerprint':
        OPEN_REGISTRATION,
    'srmech.signal_processing.rbs_hdc_instrument.mint_vector':
        OPEN_REGISTRATION,
    # ── srmech.spectral ──
    'srmech.spectral.clear_eigenbasis_cache': REGISTRY_MUTATOR,
}

#: DOWN-ONLY ceiling on the allowlist. Seeded at the MEASURED rc416 residual —
#: 184 of 744 in-scope public callables. This number may only DECREASE. It goes
#: down by DELETING a row (the op earned its ``ToolEntry``), never by widening
#: the scope predicate: narrowing the scope to make the number fall is the
#: laundering move, and :func:`test_the_scope_predicate_still_sees_the_surface`
#: is the floor that refuses it.
CEIL_REGISTRY_GAPS = 184

#: DOWN-ONLY sub-ceiling on the DEBT bucket specifically. The other four codes
#: are stated design positions; this one is *"nobody decided"*, and it is the
#: number that says how much ``fold_identity``-shaped risk is still live.
CEIL_OPEN_REGISTRATION = 125

#: FLOOR on the in-scope population. Not a pin — a floor, so a legitimate new
#: op raises it without ceremony while a scope predicate that quietly stops
#: observing goes red. rc416 measured 744.
FLOOR_SCOPE_POPULATION = 700


# ── 1. the ratchet ──────────────────────────────────────────────────────────

def test_every_public_all_callable_is_registered_or_an_acknowledged_gap():
    """THE ratchet: a name in a public ``__all__`` with no ``ToolEntry`` and no
    allowlist row FAILS here.

    The fix is to write the ``ToolEntry``. Adding an allowlist row is the
    other option and it is deliberately expensive: it needs a reason code from
    the closed set AND it raises a down-only ceiling, which is a regression
    rather than a fix.
    """
    missing = unaccounted(_KNOWN_REGISTRY_GAPS)
    assert not missing, (
        "public __all__ callable(s) resolve to NO ToolEntry and sit on NO "
        "documented allowlist row — they are importable and invisible to "
        "describe(), search() and the MCP tool list (the fold_identity "
        "shape):\n  " + "\n  ".join(missing)
        + "\n\nRegister the op (preferred), or — only with a reason code from "
          "the closed set — add it to _KNOWN_REGISTRY_GAPS and RAISE "
          "CEIL_REGISTRY_GAPS, which is a regression, not a fix.")


def test_registry_gap_ceiling_is_down_only():
    """DOWN-ONLY, the ``CEIL_WIRE_GLUE_GAPS`` shape."""
    assert len(_KNOWN_REGISTRY_GAPS) == CEIL_REGISTRY_GAPS, (
        f"allowlist holds {len(_KNOWN_REGISTRY_GAPS)} rows against a ceiling "
        f"of {CEIL_REGISTRY_GAPS}. This ratchet is DOWN-ONLY: registering an "
        f"op should DELETE its row and LOWER the ceiling.")


def test_open_registration_debt_is_down_only():
    """The DEBT sub-ceiling. ``OPEN_REGISTRATION`` is not an exemption — it is
    the count of public ops whose registration nobody has decided, i.e. the
    live ``fold_identity``-shaped population."""
    debt = [p for p, c in _KNOWN_REGISTRY_GAPS.items()
            if c == OPEN_REGISTRATION]
    assert len(debt) == CEIL_OPEN_REGISTRATION, (
        f"OPEN_REGISTRATION debt is {len(debt)} against a ceiling of "
        f"{CEIL_OPEN_REGISTRATION}. Re-labelling debt as one of the four "
        f"design codes to make this fall is the discharge this file exists "
        f"to refuse; register the op instead.")


def test_allowlist_entries_are_still_gaps():
    """Keeps the allowlist honest in the other direction: an op that has
    QUIETLY earned a ``ToolEntry`` must be DELETED from here (and the ceiling
    lowered), not left sitting on a list claiming to be invisible."""
    covered = registered_object_ids()
    surface = public_surface()
    closed = sorted(p for p in _KNOWN_REGISTRY_GAPS
                    if p in surface and surface[p] in covered)
    assert not closed, (
        "allowlisted op(s) now HAVE a ToolEntry — delete the row(s) and lower "
        "CEIL_REGISTRY_GAPS:\n  " + "\n  ".join(closed))


def test_allowlist_has_no_stale_rows():
    """An allowlist row naming a path that is no longer public surface is a
    dead exemption. Deleting the op is a legitimate way to close a gap, so this
    reports the row rather than tolerating it."""
    surface = public_surface()
    stale = sorted(p for p in _KNOWN_REGISTRY_GAPS if p not in surface)
    assert not stale, (
        "allowlist row(s) name paths that are no longer in scope (renamed, "
        "removed, or dropped from __all__) — delete them and lower "
        "CEIL_REGISTRY_GAPS:\n  " + "\n  ".join(stale))


# ── 2. the allowlist's REASONS are checked, not merely written ──────────────

def test_every_allowlist_row_carries_a_reason_from_the_closed_set():
    """A bare-name allowlist is the silent-exemption shape. Every row carries a
    code, and the code vocabulary is closed so a future row cannot invent an
    exemption by naming one."""
    bad = sorted(f"{p} -> {c!r}" for p, c in _KNOWN_REGISTRY_GAPS.items()
                 if c not in _REASON_CODES)
    assert not bad, (
        "allowlist row(s) carry a reason outside the closed set "
        f"{sorted(_REASON_CODES)}:\n  " + "\n  ".join(bad))


def test_reason_codes_match_the_surface_they_claim():
    """Two of the five codes are decidable from the path, so they are CHECKED.

    Without this an entry could wear ``CLI_SUBCOMMAND`` — a stated design
    position with a narrow exit condition — to avoid wearing
    ``OPEN_REGISTRATION``, which is counted as debt and drained. The cheap
    label has to be unavailable, not merely discouraged.
    """
    wrong = []
    for path, code in sorted(_KNOWN_REGISTRY_GAPS.items()):
        module, _, leaf = path.rpartition(".")
        is_wire = (module.startswith("srmech.mcp")
                   or module.startswith("srmech.llm"))
        is_cli = module == "srmech.cli" or module.startswith("srmech.cli.")
        is_adapter = module.startswith("srmech.amsc.adapters")
        is_mutator = any(leaf.startswith(v) for v in _MUTATOR_PREFIXES)
        if code == ADR0009_EXEMPT and not is_wire:
            wrong.append(f"{path}: ADR0009_EXEMPT but not under mcp/llm")
        if is_wire and code != ADR0009_EXEMPT:
            wrong.append(f"{path}: under mcp/llm but coded {code}")
        if code == CLI_SUBCOMMAND and not is_cli:
            wrong.append(f"{path}: CLI_SUBCOMMAND but not under srmech.cli")
        if is_cli and code != CLI_SUBCOMMAND:
            wrong.append(f"{path}: under srmech.cli but coded {code}")
        if code == PROTOCOL_UNIFORM and not is_adapter:
            wrong.append(f"{path}: PROTOCOL_UNIFORM outside amsc.adapters")
        if code == REGISTRY_MUTATOR and not is_mutator:
            wrong.append(f"{path}: REGISTRY_MUTATOR but {leaf!r} is not one of "
                         f"the documented mutator verbs")
    assert not wrong, ("allowlist reason code(s) do not describe their path:\n  "
                       + "\n  ".join(wrong))


# ── 3. the scope predicate cannot quietly stop observing ────────────────────

def test_the_scope_predicate_still_sees_the_surface():
    """NON-VACUITY. A ratchet whose scope silently empties is green forever.

    The floor is deliberately a FLOOR and not a pin: a new op raises the
    population without a test edit, while a walker that stops importing, or a
    predicate narrowed to make the ceiling fall, goes red.
    """
    surface = public_surface()
    assert len(surface) >= FLOOR_SCOPE_POPULATION, (
        f"only {len(surface)} in-scope public callables found; rc416 measured "
        f"744. The scope predicate has stopped observing, or the walk is "
        f"failing to import.")
    assert len(registered_object_ids()) >= 500, (
        "the tool registry resolved fewer than 500 live objects — warmup or "
        "resolution is broken, which would make every 'covered' verdict a "
        "false negative in the SAFE direction and hide real gaps.")


def test_every_tool_entry_name_resolves_to_a_live_object():
    """Coverage is by object identity, so an unresolvable ``ToolEntry`` name
    would silently cover nothing. rc416 measured 560/560 resolvable."""
    warmup_all()
    broken = []
    for entry in get_tool_schema().tools:
        module, _, leaf = entry.name.rpartition(".")
        try:
            getattr(importlib.import_module(module), leaf)
        except Exception as exc:                               # noqa: BLE001
            broken.append(f"{entry.name}: {type(exc).__name__}")
    assert not broken, (
        "ToolEntry name(s) do not resolve to a live object — the registry "
        "advertises something that cannot be reached:\n  "
        + "\n  ".join(broken))


def test_coverage_is_by_identity_not_by_leaf_name():
    """The laundering this predicate refuses, stated as a test.

    Leaf-name matching would have declared 11 rc416 surface points covered by
    an unrelated op of the same leaf name. The pair below is real: the bus's
    ``list`` and introspect's ``list`` are different functions, and a name
    match would have called the first one registered.
    """
    surface = public_surface()
    covered = registered_object_ids()
    bus_list = surface.get("srmech.bus.list")
    assert bus_list is not None, "srmech.bus.list left the public surface"
    assert bus_list not in covered, (
        "srmech.bus.list is now genuinely registered — good; re-point this "
        "test at another same-leaf pair or delete it with its allowlist row.")
    names = {e.name.rpartition('.')[2] for e in get_tool_schema().tools}
    assert "list" in names, (
        "no registered op has the leaf name 'list' any more, so this test no "
        "longer demonstrates the identity-vs-name distinction")


# ── 4. THE RETRO-CHECK — it must fire on the defect that motivated it ───────

_RC414_REGISTRATION = "966ce2dcb"        # 'register fold_identity' (rc414)
_COUPLING = "docs/srmech/python/srmech/biology/coupling.py"
_TOOL_SCHEMA = "docs/srmech/python/srmech/introspect/tool_schema.py"


def _git_show(rev_path):
    """``git show <rev>:<path>`` as text, or ``None`` when git cannot answer."""
    root = Path(__file__).resolve().parents[3]
    try:
        out = subprocess.run(["git", "show", rev_path], cwd=str(root),
                             capture_output=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    return out.stdout.decode("utf-8", "replace")


def test_the_ratchet_would_have_fired_on_fold_identity_pre_rc414():
    """THE ACCEPTANCE CRITERION. A gate that would not have caught the defect
    that motivated it is not the gate.

    Read out of git rather than remembered: at ``966ce2dcb^`` — the commit
    before rc414 registered the op — ``fold_identity`` is in
    ``coupling.__all__`` and its name appears NOWHERE in ``tool_schema.py``.
    That is precisely the predicate this file asserts on: in ``__all__``, not
    in the registry. At HEAD both halves have flipped.

    SKIPS loudly rather than passing when git is unavailable — a retro-check
    that silently degrades to green is worse than no retro-check.
    """
    pre = f"{_RC414_REGISTRATION}^"
    coupling_before = _git_show(f"{pre}:{_COUPLING}")
    schema_before = _git_show(f"{pre}:{_TOOL_SCHEMA}")
    if coupling_before is None or schema_before is None:
        pytest.skip(f"git cannot read {pre} (shallow clone or no git); the "
                    f"retro-check cannot run here and is NOT asserted green")

    # (i) it WAS on the public surface — in coupling.__all__, at that revision.
    namespace: dict = {}
    exec(compile("__all__ = " + coupling_before.split("__all__ = ", 1)[1]
                 .split("]", 1)[0] + "]", "<coupling_all>", "exec"), namespace)
    assert "fold_identity" in namespace["__all__"], (
        f"fold_identity is not in coupling.__all__ at {pre} — the retro-check "
        f"is pointed at the wrong revision")

    # (ii) and it had NO ToolEntry: the registry source never named it.
    assert "fold_identity" not in schema_before, (
        f"tool_schema.py already mentions fold_identity at {pre}; "
        f"{_RC414_REGISTRATION} is not the registration commit")

    # (iii) so the predicate — "in __all__, absent from the registry" — is
    #       exactly TRUE there. Both halves have flipped at HEAD:
    schema_now = Path(__file__).resolve().parents[1].joinpath(
        "srmech/introspect/tool_schema.py").read_text(encoding="utf-8")
    assert "fold_identity" in schema_now
    surface = public_surface()
    key = "srmech.biology.coupling.fold_identity"
    assert key in surface, "fold_identity left the public surface"
    assert surface[key] in registered_object_ids(), (
        "fold_identity is on the public surface and NOT registered at HEAD — "
        "rc414's registration has regressed")
    assert key not in _KNOWN_REGISTRY_GAPS, (
        "fold_identity must never be allowlisted — it is the motivating "
        "defect, not an accepted gap")


def test_the_ratchet_NAMES_fold_identity_with_rc414s_registration_undone():
    """The retro-check, RUN rather than read.

    The test above proves the pre-rc414 SOURCE satisfied the predicate. This
    one executes the predicate itself against that state: take the live
    covered-object set, remove exactly the one id rc414 added, and assert the
    ratchet's own ``unaccounted`` reports ``fold_identity`` — by name, in its
    failure text. That is the sentence a reviewer at rc113 would have seen.

    Undoing one id is the faithful reconstruction: rc414 changed nothing else
    about this op — ``coupling.__all__`` already listed it, the function
    already existed, and the diff was a ``ToolEntry`` in ``tool_schema.py``.
    """
    from srmech.biology.coupling import fold_identity

    key = "srmech.biology.coupling.fold_identity"
    covered = registered_object_ids()
    assert id(fold_identity) in covered, "rc414's registration has regressed"
    covered.discard(id(fold_identity))          # rc414 undone

    would_fire = sorted(path for path, oid in public_surface().items()
                        if oid not in covered and path not in _KNOWN_REGISTRY_GAPS)
    assert would_fire == [key], (
        "with rc414's registration undone the ratchet must name exactly "
        f"fold_identity and nothing else; it named {would_fire}")


# ── 5. the INJECTION proof — an added __all__ name goes red ────────────────

def test_an_injected_unregistered_all_entry_goes_red():
    """The gate is not merely always-green: a public ``__all__`` gaining a name
    with no ``ToolEntry`` FAILS.

    Injected into a real public module's live ``__all__`` and reverted in a
    ``finally``, so the check runs against the same predicate the shipped
    ratchet uses rather than a re-implementation of it.
    """
    import srmech.math.text as target

    def _injected_op(x):                       # a plausible new public op
        return x

    _injected_op.__module__ = target.__name__
    original = tuple(target.__all__)
    try:
        target._injected_op_rc416 = _injected_op
        target.__all__ = list(original) + ["_injected_op_rc416"]
        # an underscore name is off the surface by design — no fire yet
        assert not [m for m in unaccounted(_KNOWN_REGISTRY_GAPS)
                    if "injected" in m], (
            "an underscore-prefixed __all__ entry must stay off the surface")

        target.injected_op_rc416 = _injected_op
        target.__all__ = list(original) + ["injected_op_rc416"]
        missing = unaccounted(_KNOWN_REGISTRY_GAPS)
        assert "srmech.math.text.injected_op_rc416" in missing, (
            "the ratchet did NOT fire on a public __all__ name with no "
            f"ToolEntry — it is green by construction. Saw: {missing}")
    finally:
        target.__all__ = list(original)
        for attr in ("_injected_op_rc416", "injected_op_rc416"):
            if hasattr(target, attr):
                delattr(target, attr)
    assert not unaccounted(_KNOWN_REGISTRY_GAPS), (
        "the injection was not cleanly reverted")


def test_an_injected_class_or_constant_does_not_fire():
    """The three scope exclusions are real, not incidental. A class belongs to
    ``carrier_schema()`` and a constant is not an op, so neither is this
    ratchet's business — and if either fired, the allowlist would have to
    absorb the whole carrier and constant surface to stay green."""
    import srmech.math.text as target

    class _Injected:                            # a class, not an op
        pass

    original = tuple(target.__all__)
    try:
        target.InjectedCarrierRc416 = _Injected
        target.INJECTED_CONST_RC416 = 42
        target.__all__ = list(original) + ["InjectedCarrierRc416",
                                           "INJECTED_CONST_RC416"]
        assert not [m for m in unaccounted(_KNOWN_REGISTRY_GAPS)
                    if "Injected" in m or "INJECTED" in m], (
            "a class or a constant fired the ratchet; the scope is CALLABLES "
            "that are not classes")
    finally:
        target.__all__ = list(original)
        for attr in ("InjectedCarrierRc416", "INJECTED_CONST_RC416"):
            if hasattr(target, attr):
                delattr(target, attr)
