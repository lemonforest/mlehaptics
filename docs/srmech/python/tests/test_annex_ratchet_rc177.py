"""The rc177 ANNEX ratchet — the ledger walk extends to srmech.bus + srmech.dsl.

The compute / exact-algebra / self-hosting arcs are closed (all three ceilings
0). The ORCHESTRATION→C phase (rc170+) is now extended, per user direction, to
the IPC **bus** and the cascade-chain / class **DSL interpreter**: a bare-C host
(no Python) must run the WHOLE apparatus incl. the bus + the interpreter. This rc
is TEST-INFRA ONLY — it TRACKS the annex surface (extends ``_ROOTS`` to bus/dsl,
adds the +39 rows, raises ``CEIL_NON_COMPUTE_OWED`` 2 → 12, extends the
dev_tooling allowlist by 14); the annex BUILDS (rc178+) then drive the owed count
back down.

This file pins the annex specifics (the +39 split, the ceiling, the four
sub-bucket totals, bus/dsl in every ledger walk). numpy-free (stdlib json + the
shared conftest live-op walk); bus + dsl must import cleanly numpy-absent.
"""
from __future__ import annotations

import json
import os as _os
import sys as _sys
from collections import Counter
from pathlib import Path

_TESTS_DIR = _os.path.dirname(_os.path.abspath(__file__))
if _TESTS_DIR not in _sys.path:
    _sys.path.insert(0, _TESTS_DIR)

from conftest import _ROSETTA_ROOTS, rosetta_live_objects  # noqa: E402
from test_rosetta_completeness import (  # noqa: E402
    CEIL_NON_COMPUTE_OWED,
    NON_COMPUTE_DEV_TOOLING_EXEMPT,
    _ROOTS,
)

_FIXTURE = Path(__file__).resolve().parent / "rosetta_classification.ndjson"

# The 39 annex rows (18 bus + 21 dsl) — the SSOT for the rc177 annex
# classification (defined_at -> non_compute_kind). These are the ACTUAL canonical
# <module>.<qualname> keys the ledger walk emits (verified against the live walk).
_ANNEX_ROWS = {
    # owed_orchestration (1) — the DSL CLASS interpreter's still-owed row. rc178
    # moved the bus decode_splice owed → composes_c; rc180 moved the bus pipe owed
    # → composes_c (BUS FULLY C); rc181 moved lookup_cascade_op +
    # build_chain_from_dict owed → composes_c (the DSL chain FOUNDATION); rc182
    # moved chain (Chain.run) + run_toml_chain + build_chain_from_toml{,_str} owed
    # → composes_c (the loop/fold/reduce COMBINATORS + the TOML front-ends — the
    # DSL CHAIN interpreter is COMPLETE). rc201b moved make_class owed → composes_c
    # (the [class] OBJECT-MODEL engine srmech_make_class_run runs the object model
    # across ALL route types in C — plain / returns=self / mutates / appends / chain
    # — over the genome / sed_* domain-leaf C peers; byte-identical to CatalogClass).
    # The 1 left: run_class_method (the class-surface interpreter — rc202).
    "srmech.dsl._class_catalog.make_class": "composes_c",
    "srmech.dsl._class_surface.run_class_method": "composes_c",
    # composes_c (11) — compose existing C (sha256 / json / cipher backend / bus
    # pub/sub / the DSL chain F1 carrier-FFI + combinators + the TOML bridge), reach
    # no non-standalone-ready leaf
    "srmech.bus._bio_totp.decode_splice": "composes_c",
    "srmech.bus._client.connect": "composes_c",
    "srmech.bus._server.serve": "composes_c",
    "srmech.bus._bio_totp.channel_id_from_name": "composes_c",
    "srmech.bus._pipe.pipe": "composes_c",
    # rc181: the DSL chain FOUNDATION → C (srmech_dsl_chain_run)
    "srmech.dsl._catalog.lookup_cascade_op": "composes_c",
    "srmech.dsl._toml_chain.build_chain_from_dict": "composes_c",
    # rc182: the DSL chain interpreter COMPLETE — combinators (srmech_dsl_chain_run)
    # + the TOML front-end bridge (srmech_dsl_toml_chain_to_json)
    "srmech.dsl._chain.chain": "composes_c",
    "srmech.dsl._tool_surface.run_toml_chain": "composes_c",
    "srmech.dsl._toml_chain.build_chain_from_toml": "composes_c",
    "srmech.dsl._toml_chain.build_chain_from_toml_str": "composes_c",
    # host_glue (12) — filesystem / host discovery / registry read
    "srmech.bus.list": "host_glue",
    "srmech.bus._discovery.list_endpoints": "host_glue",
    "srmech.bus._discovery.by_name": "host_glue",
    "srmech.bus._event.new_correlation_id": "host_glue",
    "srmech.bus._transport.bus_dir": "host_glue",
    "srmech.bus._transport.is_posix_uds": "host_glue",
    "srmech.bus._transport.transport_kind": "host_glue",
    "srmech.dsl._catalog.load_catalog": "host_glue",
    "srmech.dsl._class_catalog.load_class_catalog": "host_glue",
    "srmech.dsl._toml_chain.load_chain_toml": "host_glue",
    "srmech.dsl._catalog.get_descriptor": "host_glue",
    "srmech.dsl._class_catalog.get_class_descriptor": "host_glue",
    # dev_tooling (14) — a bare-C host never needs it (LLM / dev / asyncio)
    "srmech.bus._bio_totp.cipher_backend_name": "dev_tooling",
    "srmech.bus._params.secret_kwargs": "dev_tooling",
    "srmech.bus.aio.connect": "dev_tooling",
    "srmech.bus.aio.serve": "dev_tooling",
    "srmech.bus.aio.pipe": "dev_tooling",
    "srmech.bus.aio.list_endpoints": "dev_tooling",
    "srmech.dsl._catalog.register_catalog_dir": "dev_tooling",
    "srmech.dsl._class_catalog.register_class_dir": "dev_tooling",
    "srmech.dsl._catalog.list_cascade_ops": "dev_tooling",
    "srmech.dsl._class_catalog.list_classes": "dev_tooling",
    "srmech.dsl._tool_surface.list_catalog_ops": "dev_tooling",
    "srmech.dsl._tool_surface.list_ops": "dev_tooling",
    "srmech.dsl._class_surface.describe_class": "dev_tooling",
    "srmech.dsl._class_surface.list_class_surface": "dev_tooling",
}

# the +39 delta by kind (what the annex ADDS to the pre-rc177 split; rc178 +
# rc180 + rc181 + rc182 each moved within-annex rows owed → composes_c so the split
# is now 2/11/12/14: rc181 moved lookup_cascade_op + build_chain_from_dict →
# composes_c; rc182 moved chain + run_toml_chain + build_chain_from_toml{,_str} →
# composes_c — the DSL CHAIN interpreter is COMPLETE)
# rc202 discharged run_class_method (the last annex owed row) owed -> composes_c,
# so owed_orchestration is now EMPTY across the annex (a live Counter has no zero
# key). The +39 annex split is now 13 composes_c / 12 host_glue / 14 dev_tooling.
_ANNEX_DELTA = {"composes_c": 13, "host_glue": 12, "dev_tooling": 14}
# the FULL split after the annex (pre-rc177 2/83/2/27 + the delta; rc178: owed
# 12→11, composes_c 86→87 as decode_splice earned its C peer; rc180: owed 11→10,
# composes_c 87→88 as the bus pipe earned its C peer — BUS FULLY C; rc181: owed
# 10→8, composes_c 88→90 as the DSL chain FOUNDATION earned its C peer; rc182: owed
# 8→4, composes_c 90→94 as the combinators + TOML front-ends earned C — DSL CHAIN
# interpreter COMPLETE).
# rc183 HOST-GLUE annex (living-pin bump — as rc177 bumped the rc170 pins): the
# +24 mcp/cli/llm rows raise the FULL split to 15/103/15/44 = 177. The bus/dsl
# _ANNEX_ROWS / _ANNEX_DELTA below stay unchanged (they are the rc177 bus/dsl annex
# record); the mcp/cli/llm annex specifics are pinned in test_annex_ratchet_rc183.py.
# rc185 (living-pin bump): the 2 tool_schema rows + the mcp tool_entries_to_mcp_defs
# row earned their C projection peers → owed 15→12, composes_c 103→106 (sum stays
# 177). The bus/dsl _ANNEX_ROWS / _ANNEX_DELTA are untouched (rc185 moves no bus/dsl
# row).
# rc186 (living-pin bump): the MCP-server control spine (JSON-RPC protocol + stdio
# LOOP in C) — serve_stdio earned its C peer → owed 12→11, composes_c 106→107 (sum
# stays 177). The bus/dsl _ANNEX_ROWS / _ANNEX_DELTA are untouched (rc186 moves no
# bus/dsl row; the mcp serve_stdio row is pinned in test_annex_ratchet_rc183.py).
# rc188 (living-pin bump): the tools/call DISPATCH SPINE (srmech_invoke_tool) —
# invoke_tool earned its C peer → owed 11→10, composes_c 107→108 (sum stays 177).
# The bus/dsl _ANNEX_ROWS / _ANNEX_DELTA are untouched (rc188 moves no bus/dsl row;
# the mcp invoke_tool row is pinned in test_annex_ratchet_rc183.py).
# rc193 (living-pin bump): the 7 CLI grammar rows earned their C peer
# (srmech_cli_parse + srmech_cli_dispatch) → owed 10→3, composes_c 108→115 (sum
# stays 177). The bus/dsl _ANNEX_ROWS / _ANNEX_DELTA are untouched (rc193 moves no
# bus/dsl row; the cli rows are pinned in test_annex_ratchet_rc183.py).
# rc194 (living-pin bump): the MCP HTTP+SSE transport earned its C peer
# (srmech_mcp_serve_http_sse + the handle-based serve/port/stop over the new TCP
# PAL) → serve_http_sse owed→composes_c → owed 3→2, composes_c 115→116 (sum stays
# 177). The bus/dsl _ANNEX_ROWS / _ANNEX_DELTA are untouched (rc194 moves no
# bus/dsl row; the mcp serve_http_sse row is pinned in test_annex_ratchet_rc183.py).
# rc196 (make_class → C leaf-batch 2): genome.encode_shape left non_compute for
# c_dispatched (its C peer srmech_genome_encode_shape) → composes_c 116 → 115;
# non_compute total 177 → 176. (genome.telomere also earned a C peer but moved
# composition_of_c → c_dispatched, not a non_compute row.)
# rc202: owed_orchestration EMPTY (run_class_method discharged -> composes_c 117).
# rc205 (gh #1293): +1 composes_c — srmech.introspect.carrier_schema.carrier_schema (the
# CARRIER introspection surface; dispatches to its C peer srmech_carrier_schema
# over the compiled-in const registry). composes_c 117 -> 118; sum 176 -> 177.
# rc217 (gh #1360): the 3 srmech.math.text COMPUTE kernels moved
# non_compute/composes_c -> c_dispatched (they earned byte-identical
# srmech_text_* C peers; the composes_c mis-classification was the
# self-contained-kernel hiding spot). composes_c 118 -> 115; total 177 -> 174.
# rc218 (#826, living-pin bump — the PARITY-COMPLETENESS annex): the ledger
# walk extends to srmech.spectral / srmech.rbs_lm / srmech.introspect /
# srmech.profile_loader (+30 rows; the 15 non_compute rows split +5 composes_c
# / +6 host_glue / +4 dev_tooling; the 15 compute rows are composition_of_c).
# composes_c 115 -> 120, host_glue 15 -> 21, dev_tooling 44 -> 48; total
# 174 -> 189. The bus/dsl _ANNEX_ROWS / _ANNEX_DELTA are untouched (rc218
# moves no bus/dsl row; the rc218 annex specifics are pinned in
# test_rosetta_completeness.py + test_non_compute_ratchet_rc170.py).
# rc225 (user design 2026-07-12): +1 composes_c —
# srmech.amsc.responsion_schema.responsion_schema (the RESPONSION / stored-
# relationship introspection surface, the k=3 edge face binding tool_schema +
# carrier_schema; dispatches to its C peer srmech_responsion_schema over the
# compiled-in const registry — composes_c FROM BIRTH, the rc205 carrier_schema
# precedent). composes_c 120 -> 121; total 189 -> 190. The bus/dsl _ANNEX_ROWS
# / _ANNEX_DELTA are untouched (rc225 moves no bus/dsl row).
# rc362 (ADR-0010 acoustic slice): the walk gains the srmech.music root and its
# NINE ops — and the split moves by exactly +1, not +9. Eight of the nine are
# COMPUTE rows (7 composition_of_c + bessel_j_fixed c_dispatched) and never
# reach this counter; only srmech.music.bell_partials is non_compute, because
# it computes nothing — it returns the Fletcher & Rossing sec. 21.3 tuning
# TARGETS as exact Q constants, the from_bodies / carrier_schema pure-exact-data
# precedent — and it lands composes_c since materialising those Q ratios is a
# reduction through the C-backed Class-I gcd. composes_c 137 -> 138; total
# 209 -> 210. host_glue (21) and dev_tooling (51) are UNMOVED; a music row
# appearing in either would have been a misclassification, not a bump. The
# bus/dsl _ANNEX_ROWS / _ANNEX_DELTA are untouched (rc362 moves no bus/dsl row).
# rc464 (`#T1188`) — a correction to the rc297 note carried in the trailing
# comment below, left in place because it IS the record of what rc297 believed.
# TWO of its clauses were wrong, and they were wrong in opposite directions.
#   (a) "CEIL_WIRE_GLUE_GAPS stays 10". That constant is NOW 0, not 10: the
#       live pin is CEIL_WIRE_GLUE_GAPS = 0 at
#       tests/test_rosetta_transitive_standalone.py:460 with an EMPTY
#       _KNOWN_GLUE_GAPS, asserted == 0 by rc333:294 and rc334:238. It has been
#       repeated verbatim here, in rc183 and in rc170 ever since, which is what
#       makes it stale NOW.
#       ⚠️ rc464 SECOND CORRECTION, to this correction. It first read "is not 10
#       and WAS NOT 10 WHEN THIS WAS WRITTEN", which is false and was measured
#       so: `git log -S "CEIL_WIRE_GLUE_GAPS stays 10"` names 1694b9217 (rc297)
#       as the commit that added the clause, and
#       `git show 1694b9217:tests/test_rosetta_transitive_standalone.py` line
#       437 reads `CEIL_WIRE_GLUE_GAPS = 10`. The value was 11 at rc281, 10 at
#       rc297, and first reached 0 at rc334 (9fc0a68be). So rc297 recorded a
#       TRUE measurement that later went stale, and the correction accused it of
#       a falsehood it did not commit -- inside a block this file calls a
#       measurement log. The rc170 copy of the same correction never carried the
#       false half. Dating a claim you are calling stale is the whole job here.
#   (b) "the family has real C peers reachable through dispatch glue
#       (srmech_cd_navmap / srmech_cd_navigate /
#       srmech_cd_navmap_is_signed_permutation), so this is composition, not a
#       laundered gap". True at rc297, when CD_MAX_DIM was 64. FALSE from rc298
#       (which raised the cap to 256) to rc463, because all three Python
#       wrappers carried a `dim > 64 -> return None` predicate in front of C
#       peers that accept 256 — so above dim 64 the family had C peers that
#       were NOT reachable through dispatch glue, and the justification for
#       this very row was describing a reachability the tree did not have.
#       rc464 respelled the three predicates to `dim > 256`, which makes the
#       sentence true again at every rung the register reaches.
# NEITHER ceiling moves, and the reason is worth keeping: the wire-glue ratchet
# scopes to genome/plasmid + recursive_cut, and its reachability test is an AST
# scan for `srmech_*` NAMES in dispatcher source. A guard that names the right
# symbol and then declines it on a DOMAIN predicate is invisible to a name scan
# by construction — the instrument could not have caught this, which is why it
# survived 165 releases. Recorded here rather than edited into the line below,
# because a ratchet comment is a measurement log.
_FULL_SPLIT = {"composes_c": 140, "host_glue": 21, "dev_tooling": 53}  # rc464 (`#T1188`) REMOVAL half: -2 composes_c (the two non_compute rows of the 16-slot register that CDRegister subsumes -- its CONSTRUCTOR and sed_slots, the STR-to-int slot reshape whose cdr_slots peer is already pinned above. Both leave with the class; nothing is reclassified) 142 -> 140, total 216 -> 214 # rc464 (`#T1188`): +3 composes_c (the three ACCESSORS among the fourteen cdr_* [class]-binding adapters -- cdr_slots, a STR-to-int key reshape with no bounds test to dispatch; cdr_working_block / cdr_carry_block, the two halves of a range PARTITION of [0, dim). All three are zero-REACH and pinned as such in COMPOSES_C_ZERO_REACH_PINNED with their justification. The other ELEVEN adapters in the same family are composition_of_c, because they reach the C mint / bind / bundle / similarity / hamming / cd_navigate kernels -- this is a POPULATION pin moving by three accessors, not a family classified wholesale) 139 -> 142, total 213 -> 216  #  # rc441 (local task T1148): -1 composes_c (srmech.math.tlv.tlv_unpack EARNED its C peer srmech_tlv_unpack and LEFT non_compute for c_dispatched - it was never a composition, its body was struct.unpack_from plus slicing, a self-contained kernel reaching zero ledger ops, which is why the transitive walk could not see it and it sat in COMPOSES_C_ZERO_REACH_PINNED; the rc217 srmech.math.text precedent) 140 -> 139, total 214 -> 213  # rc420 (local task T1114): +1 composes_c (dsl.run_cascade_chain - runs a [cascade] descriptor DECLARED chain through the schema-v2 compose engine; the exact run_toml_chain precedent: a runner that composes whatever the chain names, itself computing nothing) 139 -> 140, total 213 -> 214  # rc411 (): +1 composes_c (introspect.search.search - the need-shaped INDEX over the tool + carrier registries; a pure ACCESSOR plus a rank, reaching only standalone-ready leaves) 138 -> 139, total 212 -> 213  # rc407 (`#T1076`): host_glue 22 -> 21, total 213 -> 212 — srmech.introspect stopped exporting the PRIVATE `_maybe_auto_publish` from its __all__ (it also exported `_PublishHandle`; neither belongs on a public surface). _live_ops() walks __all__, falling back to non-underscore dir(), so an underscore name absent from __all__ is off the tracked surface by BOTH routes and its rosetta_classification.ndjson row went stale. The FUNCTION is untouched and still reached by direct attribute access from srmech/__init__.py:63, which __all__ does not govern — what moved is the PUBLISHED surface, which is what this census counts.  # rc364 ADR-0010 first execution slice: +1 host_glue (dsl.resolve_alias_descriptor — descriptor FS DISCOVERY, the load_catalog / load_class_catalog / get_descriptor precedent: a bare-C host must FIND the file before srmech_toml can parse it) and +2 dev_tooling (dsl.list_alias_descriptors + dsl.register_alias_dir — BROWSE and CONFIGURE; exact peers of list_cascade_ops / list_classes and register_catalog_dir / register_class_dir, all four already dev_tooling). host_glue 21 -> 22, dev_tooling 51 -> 53, composes_c UNMOVED at 138 — none of the three composes a C op. The discriminator is NOT "does it touch the filesystem" (all three do) but LOAD/GET vs BROWSE/CONFIGURE, the split srmech.dsl already encodes over the SAME directory (load_class_catalog reads it = host_glue; list_classes browses it = dev_tooling). rc364 first shipped list_alias_descriptors as host_glue and CI caught it at 23/52; the fix was the CLASSIFICATION, not the pin.  # rc325 §𝕆-FIBER/v18: +3 composes_c (genome.genome_octonion_associator + genome_add_octonion_fiber + genome_read_octonion_fiber, the octonion fiber channel's defect/assemble/read ops) 133 -> 136  # rc322 §Q8-FIBER/v17: +2 composes_c (genome.genome_add_fiber + genome_read_fiber, the fiber cap assemble/read ops) 131 -> 133  # rc312 §Q8/v16: +1 composes_c (genome.upgrade_v15_to_v16, the v15->v16 migration op) 130 -> 131  # rc308 #944: +1 composes_c (laplacian.hypercomplex_perspectives reader) 129 -> 130  # rc261: +2 composes_c (dsl alias TOML) + 1 dev_tooling (dsl.alias)  # rc249 #1390 item 2: +2 genome graph codec  # rc267 §96: +2 composes_c (genome_census + genome_registry)  # rc271 §96/F1251: +1 composes_c (genome.load_type_aliases_toml) + 2 dev_tooling (genome.set/clear_type_aliases)  # rc278 §102/F1252: +1 composes_c (plasmid.section_counts; plasmid_extract is composition_of_c)  # rc280 §102/F1253: -1 composes_c (plasmid.section_counts EARNED the srmech_genome_section_counts C peer -> c_dispatched)  # rc290 §102/F1259: +1 host_glue (hdc.klein4_random — the STOCHASTIC regime, alone after the by-regime split; no C peer BY REGIME, not by debt: its output is not a function of any input, so there is no kernel to mirror and nothing to byte-compare. The deterministic mints klein4_expand/_address/_from_one are c_dispatched and klein4_role is composition_of_c, so no debt ceiling moved.)  # rc292 §102/F1259: -1 host_glue (hdc.klein4_random REMOVED — rc290 closed only the seed= door; a SEEDED rng= is equally reproducible and every real call site passed one, so the STOCHASTIC bucket held an op that ran deterministically. Removal, not a bucket; callers compose klein4_encode_bytes.)  # rc297 `#934`: +1 composes_c (cascade.cd_register.cd_register — the general N-slot Cayley-Dickson register's CONSTRUCTOR row; a POPULATION pin, not a debt ceiling. It lands in composes_c (128 -> 129) and NOT host_glue (21, unchanged), and CEIL_WIRE_GLUE_GAPS stays 10 — the family has real C peers reachable through dispatch glue (srmech_cd_navmap / srmech_cd_navigate / srmech_cd_navmap_is_signed_permutation), so this is composition, not a laundered gap. The constructor computes nothing; all compute is in the methods, which route to those three c_dispatched rows.)  # rc345 (task T964): +1 composes_c (genome.genome_content — the repartition-invariant CONTENT accessor; dispatches to the byte-identical C peer srmech_genome_content, the genome_census/genome_registry composes_c precedent) 136 -> 137
_TOTAL_NON_COMPUTE = 214  # rc464 (`#T1188`) REMOVAL half: -2 composes_c (the two non_compute rows of the 16-slot register that CDRegister subsumes -- its CONSTRUCTOR and sed_slots, the STR-to-int slot reshape whose cdr_slots peer is already pinned above. Both leave with the class; nothing is reclassified) 142 -> 140, total 216 -> 214  # rc464 (`#T1188`): +3 composes_c (the three ACCESSORS among the fourteen cdr_* [class]-binding adapters -- cdr_slots, a STR-to-int key reshape with no bounds test to dispatch; cdr_working_block / cdr_carry_block, the two halves of a range PARTITION of [0, dim). All three are zero-REACH and pinned as such in COMPOSES_C_ZERO_REACH_PINNED with their justification. The other ELEVEN adapters in the same family are composition_of_c, because they reach the C mint / bind / bundle / similarity / hamming / cd_navigate kernels -- this is a POPULATION pin moving by three accessors, not a family classified wholesale) 139 -> 142, total 213 -> 216  # rc441 (local task T1148): -1 composes_c (srmech.math.tlv.tlv_unpack EARNED its C peer srmech_tlv_unpack and LEFT non_compute for c_dispatched - it was never a composition, its body was struct.unpack_from plus slicing, a self-contained kernel reaching zero ledger ops, which is why the transitive walk could not see it and it sat in COMPOSES_C_ZERO_REACH_PINNED; the rc217 srmech.math.text precedent) 140 -> 139, total 214 -> 213    # rc420 (local task T1114): 213 -> 214, dsl.run_cascade_chain (composes_c; see the split note in the annex files)  # rc411 (): +1 composes_c (introspect.search.search - the need-shaped INDEX over the tool + carrier registries; a pure ACCESSOR plus a rank, reaching only standalone-ready leaves) 138 -> 139, total 212 -> 213  # rc407 (`#T1076`): host_glue 22 -> 21, total 213 -> 212 — srmech.introspect stopped exporting the PRIVATE `_maybe_auto_publish` from its __all__ (it also exported `_PublishHandle`; neither belongs on a public surface). _live_ops() walks __all__, falling back to non-underscore dir(), so an underscore name absent from __all__ is off the tracked surface by BOTH routes and its rosetta_classification.ndjson row went stale. The FUNCTION is untouched and still reached by direct attribute access from srmech/__init__.py:63, which __all__ does not govern — what moved is the PUBLISHED surface, which is what this census counts.  # rc364 ADR-0010 first execution slice: 210 -> 213, the three srmech.dsl alias-catalog rows (list_alias_descriptors + resolve_alias_descriptor + register_alias_dir)         # rc362 ADR-0010 acoustic slice: 209 -> 210, srmech.music.bell_partials (the ONLY non_compute row among the nine music ops)  # rc325 §𝕆-FIBER/v18: 205 -> 208, the 3 octonion fiber ops (associator + add + read)  # rc322 §Q8-FIBER/v17: 203 -> 205, genome.genome_add_fiber + genome_read_fiber  # rc312 §Q8/v16: 202 -> 203, genome.upgrade_v15_to_v16  # rc308 `#944`: 201 -> 202, the hypercomplex_perspectives reader row  # rc297 `#934`: 200 -> 201, the cd_register constructor row above  # rc345 (task T964): 208 -> 209, genome.genome_content


def _rows():
    return [json.loads(l) for l in _FIXTURE.read_text(encoding="utf-8").splitlines()
            if l.strip()]


def test_bus_and_dsl_in_every_ledger_walk():
    """The completeness walk (_ROOTS) AND the shared non_compute walk
    (_ROSETTA_ROOTS) both include srmech.bus + srmech.dsl — the extension that
    brings the annex surface into the everything-mirrors ledger."""
    for roots, where in ((_ROOTS, "test_rosetta_completeness._ROOTS"),
                         (_ROSETTA_ROOTS, "conftest._ROSETTA_ROOTS")):
        assert "srmech.bus" in roots and "srmech.dsl" in roots, (
            f"{where} must include srmech.bus + srmech.dsl; got {roots}"
        )


def test_annex_rows_present_with_expected_kinds():
    """All 39 annex rows are in the ledger as non_compute with the pinned
    non_compute_kind (the ACTUAL canonical <module>.<qualname> keys)."""
    by_da = {r["defined_at"]: r for r in _rows()}
    missing = [da for da in _ANNEX_ROWS if da not in by_da]
    assert not missing, f"annex rows missing from the ledger: {sorted(missing)}"
    wrong = []
    for da, kind in _ANNEX_ROWS.items():
        row = by_da[da]
        if row.get("bucket") != "non_compute" or row.get("non_compute_kind") != kind:
            wrong.append(
                f"{da}: got bucket={row.get('bucket')!r} "
                f"kind={row.get('non_compute_kind')!r}, expected non_compute/{kind}"
            )
    assert not wrong, "annex row classification drift:\n  " + "\n  ".join(wrong)


def test_annex_rows_are_live():
    """Every annex row is a LIVE public op (the extended walk surfaces it) — the
    ledger is not carrying a phantom bus/dsl key."""
    live = set(rosetta_live_objects())
    not_live = [da for da in _ANNEX_ROWS if da not in live]
    assert not not_live, (
        f"annex rows not surfaced by the live walk (bus/dsl not in roots, or the "
        f"key drifted): {sorted(not_live)}"
    )


def test_annex_delta_is_39_split_1_12_12_14():
    """The +39 annex rows split exactly 1 owed / 12 composes_c / 12 host_glue /
    14 dev_tooling (rc178 moved decode_splice owed → composes_c; rc180 moved the
    bus pipe owed → composes_c — BUS FULLY C; rc181 moved lookup_cascade_op +
    build_chain_from_dict owed → composes_c — the DSL chain FOUNDATION → C; rc182
    moved chain + run_toml_chain + build_chain_from_toml{,_str} owed → composes_c —
    the DSL CHAIN interpreter COMPLETE; rc201b moved make_class owed → composes_c —
    the DSL CLASS object-model engine RUNS in C across all route types)."""
    counts = Counter(_ANNEX_ROWS.values())
    assert dict(counts) == _ANNEX_DELTA, (
        f"annex +39 split drifted: got {dict(counts)}, expected {_ANNEX_DELTA}"
    )
    assert sum(counts.values()) == 39


def test_full_non_compute_split_matches_pin():
    """The full non_compute ledger split — bus/dsl annex (rc177–182) + the rc183
    mcp/cli/llm host-glue annex — matches the pinned ``_FULL_SPLIT`` and sums to
    the single living pin ``_TOTAL_NON_COMPUTE`` (updated per-rc; 203 at rc312).
    The exact numbers live in the constants, not this test's name."""
    counts = Counter(r["non_compute_kind"] for r in _rows()
                     if r.get("bucket") == "non_compute")
    assert dict(counts) == _FULL_SPLIT, (
        f"full non_compute split drifted: got {dict(counts)}, expected "
        f"{_FULL_SPLIT}"
    )
    assert sum(counts.values()) == _TOTAL_NON_COMPUTE == sum(_FULL_SPLIT.values())


def test_ceil_non_compute_owed_is_0():
    """The phase-driver ceiling is 0 after rc202 — the FINAL owed row
    run_class_method earned its C peer (srmech_run_class_method: NAME->descriptor
    resolve IN C + the rc201 engine + the 4-key wrap, byte-identical to pure). NO
    owed_orchestration row remains: the everything-to-C program is COMPLETE (a
    bare-C host runs the WHOLE apparatus)."""
    assert CEIL_NON_COMPUTE_OWED == 0, (
        f"CEIL_NON_COMPUTE_OWED must be 0 after rc202 (everything-to-C complete); "
        f"got {CEIL_NON_COMPUTE_OWED}"
    )


def test_annex_dev_tooling_keys_in_allowlist():
    """All 14 annex dev_tooling keys are in the pinned NON_COMPUTE_DEV_TOOLING_EXEMPT
    allowlist (a dev_tooling row must be added DELIBERATELY)."""
    annex_dev = {da for da, k in _ANNEX_ROWS.items() if k == "dev_tooling"}
    assert len(annex_dev) == 14
    missing = annex_dev - set(NON_COMPUTE_DEV_TOOLING_EXEMPT)
    assert not missing, (
        f"annex dev_tooling keys not in the allowlist: {sorted(missing)}"
    )


def test_bus_and_dsl_import_numpy_absent():
    """srmech.bus + srmech.dsl import cleanly (the ratchet runs numpy-free)."""
    import importlib
    import srmech.bus  # noqa: F401
    import srmech.dsl  # noqa: F401
    # a numpy import anywhere in the chain would have failed the ratchet's
    # numpy-absent contract; assert the packages are the real ones.
    assert importlib.import_module("srmech.bus") is srmech.bus
    assert importlib.import_module("srmech.dsl") is srmech.dsl
