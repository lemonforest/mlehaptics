"""The rc170 non_compute four-way-split ratchet — the orchestration→C phase.

The compute (CEIL_PYTHON_ONLY_DEBT=0), exact-algebra (CEIL_BIGNUM_REFERENCE=0)
and self-hosting (CEIL_C_EXISTS_UNBOUND=0) arcs are CLOSED. ``non_compute`` (the
last un-ceilinged bucket, rc177 annex: 153 rows after extending the ledger walk
to srmech.bus + srmech.dsl) is the honest next frontier: making a bare-C host
(no Python) run the WHOLE apparatus — dispatch, catalogs, IPC, the genome, the
chain-runner, the DSL chain / class interpreter — in C.

This rc splits the ``non_compute`` rows into FOUR honest sub-buckets (the
``non_compute_kind`` field in ``rosetta_classification.ndjson``) and pins the
split (rc177 annex counts):

  owed_orchestration (11) — genuine control/dispatch LOGIC a bare-C host needs;
                            owed-C, DOWN-ONLY (CEIL_NON_COMPUTE_OWED, the phase
                            driver, in test_rosetta_completeness.py). rc177 annex
                            +10: the bus Bio-TOTP cipher stream kernel + the DSL
                            chain / class interpreter; rc178 −1: decode_splice
                            earned its C peer.
  composes_c        (87) — thin: composes existing C, or a pure accessor /
                            constructor / validator; TRANSITIVE-REACHABILITY
                            assert (hides no Python kernel), not a ceiling.
  host_glue         (14) — filesystem / host I/O; tracked, no ceiling.
  dev_tooling       (41) — a bare-C host never needs it; PINNED exempt allowlist.

This file proves the split is COMPLETE (sums to 153), DISJOINT, and TIGHT (the
live owed count == CEIL_NON_COMPUTE_OWED). numpy-free (stdlib json + the shared
conftest live-op walk).
"""
from __future__ import annotations

import json
import os as _os
import sys as _sys
from collections import Counter
from pathlib import Path

# pytest's prepend import-mode does not add a package dir (tests/ has an
# __init__.py) to sys.path on isolated collection — guard the tests dir on first
# (the test_immolation.py / test_rosetta_completeness.py precedent), so the
# sibling `from test_rosetta_completeness import ...` (the SSOT for the ceiling +
# allowlist) and `from conftest import ...` resolve.
_TESTS_DIR = _os.path.dirname(_os.path.abspath(__file__))
if _TESTS_DIR not in _sys.path:
    _sys.path.insert(0, _TESTS_DIR)

from conftest import rosetta_live_objects  # noqa: E402
from test_rosetta_completeness import (  # noqa: E402
    CEIL_NON_COMPUTE_OWED,
    NON_COMPUTE_DEV_TOOLING_EXEMPT,
    _NON_COMPUTE_KINDS,
)

_FIXTURE = Path(__file__).resolve().parent / "rosetta_classification.ndjson"

# The pinned four-way split — the SSOT for this rc's classification. The three
# ratchet tests in test_rosetta_completeness.py (owed ceiling / composes_c
# reachability / dev_tooling allowlist) enforce the semantics; this pins the
# COUNTS so the split stays complete + tight.
# rc171: the 5 op_provenance verdict/carry ops earned C peers → moved
# owed_orchestration → composes_c (owed 20→15, composes_c 65→70; sum stays 114).
# rc172: the catalog registry/kernel/audit batch — 6 catalog ops earned C
# (list_registered_roots / get_local_kernel_state / use_local_kernel /
# clear_local_kernel / attestation_audit → their srmech_catalog_* peers;
# list_attested_sources classified composes_c directly, consistent with the
# already-composes_c get_attested_dataset / get_attested_descriptor) → moved
# owed_orchestration → composes_c (owed 15→9, composes_c 70→76; sum stays 114).
# rc173: the amsc.compose chain-runner PARSE half — parse_chain_spec +
# parse_catalog_chains earned C peers (srmech_chain_spec_parse /
# srmech_chain_catalog_parse) → moved owed_orchestration → composes_c
# (owed 9→7, composes_c 76→78; sum stays 114). resolve_chain / run_chain stay
# owed (arbitrary-op FFI over the live object graph → rc174).
# rc174: the amsc.compose chain-runner RUN LOOP — resolve_chain + run_chain
# earned a C peer (srmech_chain_run runs the whole shipped apparatus — pi /
# series / Friedmann — end-to-end in C to byte-identical OUTPUT; the pure path
# runs any out-of-table op / non-raise policy / @catalog ref) → moved
# owed_orchestration → composes_c (owed 7→5, composes_c 78→80; sum stays 114).
# rc175: the 2 catalog CHAIN-ORCHESTRATION dependents earned C peers
# (list_catalog_chains → srmech_catalog_list_chains; run_catalog_chain →
# srmech_catalog_run_chain, each composing the rc173 parse + rc174 chain-runner)
# → moved owed_orchestration → composes_c (owed 5→3, composes_c 80→82; sum stays
# 114). HONEST SPLIT: dispatch.infer (the F929 router) STAYS owed → rc176 (its
# relationship payloads carry live non-JSON carriers — a multi-carrier FFI arc,
# not one clean rc). The 3 remaining owed = dispatch.infer + the 2 tool_schema
# rows (get_tool_schema / tool_schema_view → built with the host-glue MCP server).
# rc176: dispatch.infer earned a C peer — srmech_infer (the ORCHESTRATION→C
# spine, batch 6; the CARRIER-FFI foundation). The smallest sound foundation:
# the TWO exact-symbolic bignum-carrier rows sharing ONE carrier-FFI marshal
# (cyclic → the_one; sigma-gosper → gosper). srmech_infer detects the row from
# the marshalled operand, dispatches + verifies the C reducer, emits the DECISION
# (the Python caller rebuilds closed_form via the same reducer; native == pure).
# The 5 heavier-carrier rows (wz / spectral / multivar / q / elliptic) fall to
# pure via non-OK (inform-don't-limit) → rc177+. → moved owed_orchestration →
# composes_c (owed 3→2, composes_c 82→83; sum stays 114). The 2 remaining owed =
# the tool_schema pair (get_tool_schema / tool_schema_view — host-glue MCP).
# rc177 (2026-07-08): the ANNEX — extend the ledger walk (_ROOTS) to srmech.bus +
# srmech.dsl (+39 rows: 18 bus + 21 dsl, all non_compute). The +39 split by kind:
# +10 owed_orchestration (the bus Bio-TOTP cipher stream kernel decode_splice /
# pipe + the DSL chain / class interpreter chain / run_toml_chain /
# lookup_cascade_op / build_chain_from_{dict,toml,toml_str} / make_class /
# run_class_method), +3 composes_c (bus connect / serve / channel_id_from_name),
# +12 host_glue (bus discovery/transport/registry-read + DSL catalog/class
# descriptor loaders), +14 dev_tooling (bus cipher-backend / secret-kwargs /
# asyncio-aio wrappers + DSL register/list introspection). Test-infra ONLY (no
# C, no compute-op change); CEIL_NON_COMPUTE_OWED 2 → 12; rc178+ build the annex
# to C + drive the owed count back down. owed 2→12 / composes_c 83→86 /
# host_glue 2→14 / dev_tooling 27→41; sum 114 → 153.
# rc178 (2026-07-08): ANNEX Batch A part 1 — the bus Bio-TOTP wire cipher earned
# its C peer (srmech_hmac_sha256 + srmech_bio_totp_derive_key / keystream_xor /
# decode_splice). decode_splice moved owed_orchestration → composes_c (the DEFAULT
# stdlib HMAC-CTR path is now a thin compose over srmech_sha256 + srmech_json; the
# AES-128-CTR `[crypto]` extra stays Python). owed 12 → 11, composes_c 86 → 87;
# sum stays 153. CEIL_NON_COMPUTE_OWED 12 → 11.
# rc180 (2026-07-08): ANNEX Batch A part 2b — the bus pub/sub earned its C peer
# (PAL mutex + srmech_bus_broadcast / subscribe / pubsub_accept /
# subscriber_count / pipe). The last owed bus row srmech.bus._pipe.pipe moved
# owed_orchestration → composes_c (it now composes the C subscribe + forward).
# BUS FULLY C. owed 11 → 10, composes_c 87 → 88; sum stays 153.
# CEIL_NON_COMPUTE_OWED 11 → 10. ABI 3 → 4.
# rc181 (2026-07-08): ANNEX Batch B part 1 — the DSL chain interpreter FOUNDATION
# earned its C peer (srmech_dsl_chain_run: the F1 carrier-FFI + leaf-dispatch table
# + build_chain_from_dict stage-IR + LINEAR chain.run over the C-backed atoms).
# lookup_cascade_op + build_chain_from_dict moved owed_orchestration → composes_c.
# owed 10 → 8, composes_c 88 → 90; sum stays 153. CEIL_NON_COMPUTE_OWED 10 → 8.
# rc182 (2026-07-08): ANNEX Batch B part 2 — the DSL chain interpreter is COMPLETE.
# The loop/fold/reduce COMBINATORS completing srmech_dsl_chain_run + the TOML
# front-end bridge srmech_dsl_toml_chain_to_json. chain (Chain.run) + run_toml_chain
# + build_chain_from_toml + build_chain_from_toml_str moved owed_orchestration →
# composes_c. owed 8 → 4, composes_c 90 → 94; sum stays 153. CEIL_NON_COMPUTE_OWED
# 8 → 4 (the 4 left = 2 tool_schema + make_class + run_class_method).
# rc183 (2026-07-08): the HOST-GLUE ANNEX — extend the ledger walk (_ROOTS) to
# srmech.mcp + srmech.cli + srmech.llm (+24 rows: 4 mcp + 17 cli + 3 llm). The +24
# split by kind: +11 owed_orchestration (the 4 MCP tool-serving ops + cli.main.main
# / build_parser + the 5 subcommand add_arguments), +9 composes_c (the cli.*.run /
# run_* dispatch bodies over the C bus / C DSL chain / owed serve+class ops),
# +1 host_glue (cli.status.run reads ~/.srmech FS), +3 dev_tooling (the srmech.llm
# Anthropic-agent surface — HONEST-DEFAULT pending a C-agent decision). Test-infra
# ONLY (no C, no compute-op change); CEIL_NON_COMPUTE_OWED 4 → 15; rc184+ build the
# MCP server + CLI dispatch to C + drive the owed count back down. owed 4→15 /
# composes_c 94→103 / host_glue 14→15 / dev_tooling 41→44; sum 153 → 177.
# rc185 (2026-07-08): the tool_schema PROJECTION ops in C (srmech_get_tool_schema /
# srmech_tool_schema_view / srmech_tool_entries_to_mcp_defs over the rc184 const
# table). The 2 tool_schema rows (get_tool_schema / tool_schema_view) + the mcp row
# (tool_entries_to_mcp_defs) moved owed_orchestration → composes_c. owed 15 → 12;
# composes_c 103 → 106; sum stays 177. CEIL_NON_COMPUTE_OWED 15 → 12.
# rc186 (2026-07-08): the MCP-server CONTROL SPINE — the JSON-RPC protocol +
# stdio LOOP in C (srmech_mcp_handle / srmech_mcp_serve_stdio / build_attestation
# over the rc185 tool-defs projection). serve_stdio moved owed_orchestration →
# composes_c: a bare-C host now serves initialize/tools-list/ping/shutdown natively
# (its loop + framing genuinely run in C; tools/call routes to the still-owed
# invoke_tool via inform-don't-limit). owed 12 → 11; composes_c 106 → 107; sum stays
# 177. CEIL_NON_COMPUTE_OWED 12 → 11. The 11 owed left = invoke_tool + serve_http_sse
# + the 2 CLI top-level dispatch ops + the 5 cli subcommand add_arguments + ... .
# rc188 (2026-07-09): the tools/call DISPATCH SPINE — srmech_invoke_tool (+ the
# parsed-args srmech_invoke_tool_json) makes MCP tools/call RUN in C for a clean
# 20-tool batch (registry_find → marshal_arg → signature-shape thunk table →
# serialise; the 383 no-single-kernel tools defer to the pure invoke_tool). invoke_tool
# moved owed_orchestration → composes_c. owed 11 → 10; composes_c 107 → 108; sum stays
# 177. CEIL_NON_COMPUTE_OWED 11 → 10. The 10 owed left = serve_http_sse + the 2 CLI
# top-level dispatch ops + the 5 cli subcommand add_arguments + make_class/run_class_method.
# rc193: the 7 CLI grammar rows (cli.main.{main,build_parser} + the 5 subcommand
# add_arguments) earned their C peer (srmech_cli_parse + srmech_cli_dispatch) →
# owed 10 → 3, composes_c 108 → 115; sum stays 177.
# rc194: the MCP HTTP+SSE transport earned its C peer (srmech_mcp_serve_http_sse +
# the handle-based srmech_mcp_sse_serve/_port/_stop, over the new rc194 TCP PAL,
# composing srmech_mcp_handle). serve_http_sse moved owed_orchestration →
# composes_c → owed 3 → 2, composes_c 115 → 116; sum stays 177.
# rc196 (make_class → C leaf-batch 2, the genome CAP FOUNDATION): genome.encode_shape
# earned its C peer srmech_genome_encode_shape and LEFT non_compute for c_dispatched
# (a pure-integer in-memory compute op that now dispatches to a dedicated C symbol,
# parallel to telomere_tick / gene_express). genome.telomere ALSO earned its C peer
# srmech_genome_telomere but moved composition_of_c → c_dispatched (NOT a non_compute
# row). So ONLY encode_shape leaves this bucket: composes_c 116 → 115; non_compute
# total 177 → 176. CEIL_NON_COMPUTE_OWED stays 2 (make_class / run_class_method are
# the 2 owed; they discharge in rc201/rc202).
# rc201b (make_class → C, engine 2/2): the DSL [class] OBJECT-MODEL engine
# srmech_make_class_run RUNS the object model across ALL route types in C (plain /
# returns=self / mutates / appends / chain over the genome / sed_* domain-leaf
# peers, byte-identical to CatalogClass). make_class moved owed_orchestration →
# composes_c → owed 2 → 1, composes_c 115 → 116; sum stays 176. CEIL 2 → 1. The 1
# owed left = run_class_method (rc202).
# rc205 (gh #1293): carrier_schema — the CARRIER (operand) introspection surface,
# the noun-side dual of tool_schema. ONE new non_compute row (srmech.amsc.
# carrier_schema.carrier_schema), composes_c: it runtime-dispatches to its C peer
# srmech_carrier_schema over the compiled-in srmech_carrier_registry const table
# (canonical JSON byte-identical to the pure path, sha256 hash-ratcheted); the
# pure derivation is the complete fallback. NOT owed_orchestration (CEIL stays 0).
# composes_c 117 -> 118; sum 176 -> 177.
# rc217 (gh #1360): the 3 srmech.math.text ops (tokenize / cooccurrence_edges /
# cooccurrence_topk) were MIS-CLASSIFIED non_compute/composes_c — they are
# genuine pure-Python COMPUTE kernels (the enwiki-encode hot loop) that reach
# no ledger op, so the composes_c transitive walk could not see them (the
# self-contained-kernel hiding spot; closed by the new zero-reach pin in
# test_rosetta_completeness.py). They earned BYTE-IDENTICAL C peers
# (srmech_text_*) and moved non_compute -> c_dispatched: composes_c 118 -> 115;
# non_compute total 177 -> 174.
# rc218 (#826, the PARITY-COMPLETENESS annex): the ledger walk extends to the
# LAST 4 untracked Python-only modules (srmech.spectral / srmech.rbs_lm /
# srmech.introspect / srmech.profile_loader — the +30 rows; 15 compute rows all
# composition_of_c over already-C-backed ops). The +15 non_compute rows split
# +5 composes_c (introspect describe + the 4 pinned zero-reach event/native-
# status accessors) / +6 host_glue (introspect publish/list/by_pid/
# _maybe_auto_publish + the _writer dir/emit pair — ~/.srmech FS I/O) /
# +4 dev_tooling (3 profile_loader + spectral.clear_eigenbasis_cache).
# composes_c 115 → 120, host_glue 15 → 21, dev_tooling 44 → 48; sum 174 → 189.
# CEIL_NON_COMPUTE_OWED stays 0 (no new owed control logic).
# rc225 (user design 2026-07-12): +1 composes_c —
# srmech.amsc.responsion_schema.responsion_schema (the RESPONSION / stored-
# relationship introspection surface, the k=3 edge face binding tool_schema +
# carrier_schema; dispatches to its C peer srmech_responsion_schema over the
# compiled-in const registry — composes_c FROM BIRTH, the rc205 carrier_schema
# precedent). composes_c 120 -> 121; total 189 -> 190.
_EXPECTED_SPLIT = {
    # rc202 discharged the FINAL owed row (run_class_method -> C); owed_orchestration
    # is now EMPTY (a live Counter has no zero key), so it is absent from the split.
    # rc249 (#1390 item 2): +2 composes_c — genome.graph_to_kernel /
    # kernel_to_graph (the directed-graph<->Klein-4 codec; dispatch to the
    # byte-identical C peer srmech_graph_kernel_encode / _decode, the kernel_pack
    # composes_c precedent). composes_c 121 -> 123; total 190 -> 192.
    # rc261 (§95.2 / #1407): +2 composes_c — dsl.build_aliases_from_toml_str /
    # load_aliases_toml (the [[alias]] TOML function-aliasing layer; parse via the C
    # srmech_toml, the build_chain_from_toml_str composes_c precedent). composes_c
    # 123 -> 125. +1 dev_tooling — dsl.alias (pure Python name-binding, a bare-C host
    # never aliases Python fns). dev_tooling 48 -> 49; total 192 -> 195.
    # rc267 (§96 / PR#687 UPSTREAM_NOTES): +2 composes_c — genome.genome_census +
    # genome.genome_registry (the per-genome roll-up + cell census; each composes
    # over the C genome_catalog / srmech_genome_census / srmech_genome_registry).
    # composes_c 125 -> 127; total 195 -> 197.
    # rc271 (§96 / F1251): the VALUE-ALIAS presentation layer (the plasmid/nuclear
    # field-vocabulary rename's opt-in-old-names companion). +1 composes_c —
    # genome.load_type_aliases_toml (parses [genome.type_aliases] via the C
    # srmech_toml, the rc261 load_aliases_toml precedent). composes_c 127 -> 128.
    # +2 dev_tooling — genome.set_type_aliases / clear_type_aliases (pure Python
    # session-state presentation setters; a bare-C host never re-presents the C's
    # canonical plasmid/nuclear output, the rc261 dsl.alias precedent).
    # dev_tooling 49 -> 51; total 197 -> 200.
    # rc278 (§102 / F1252 STAGE 1): +1 composes_c — plasmid.section_counts (the
    # genome-native section-count read; scans the store's sections + composes over
    # the C genome_census / genome_window / kernel_unpack, the genome_census
    # composes_c precedent). plasmid.plasmid_extract is a BUILDER with a whole-op C
    # orchestrator (srmech_genome_plasmid_extract) -> composition_of_c, NOT counted
    # here. composes_c 128 -> 129; total 200 -> 201.
    # rc280 (§102 / F1253): -1 composes_c — plasmid.section_counts EARNED its own
    # whole-op C peer (srmech_genome_section_counts: derive the catalog once, page
    # only each section's node_ids prefix) and now DISPATCHES to it, so it is no
    # longer a Python orchestration over other C ops -> it leaves non_compute for
    # c_dispatched (the conserved_core precedent). composes_c 129 -> 128;
    # total 201 -> 200. The debt moved DOWN: one fewer op a bare-C host must
    # re-orchestrate itself.
    # rc290 (§102 / F1259 / F1260): +1 host_glue — hdc.klein4_random.
    # The Klein-4 mint split by REGIME left the STOCHASTIC regime alone in an
    # op of its own, and it is the one klein4 op with NO C peer. That is a
    # REGIME property, not debt, which is why it lands here and not in
    # python_only_debt: its output is by definition not a function of any
    # input, so there is no kernel to mirror and nothing to differentially
    # test for byte-identity — two implementations of "unpredictable" cannot
    # be compared. A bare-C host needing an unpredictable Klein-4 vector reads
    # its own entropy source, exactly as this reads Python's; host_glue (host
    # I/O, tracked, no ceiling) is the honest sub-bucket. The CAPABILITY every
    # cascade actually consumes — DETERMINISTIC Klein-4 minting — is fully
    # covered in both projections by klein4_expand / _address / _from_one
    # (c_dispatched) and klein4_role (composition_of_c), so no debt ceiling
    # moved. host_glue 21 -> 22; total 200 -> 201.
    # rc292 (§102 / F1259): -1 host_glue — hdc.klein4_random is REMOVED, and
    # the ceiling comes back DOWN with it. host_glue 22 -> 21; total 201 -> 200.
    # rc290's reasoning above was sound about the regime and wrong about the
    # remedy: it argued the op had no C peer because "unpredictable" has
    # nothing to be at parity about, then kept the op. But rc290 closed only
    # the ``seed=`` door — a SEEDED ``rng=`` is just as reproducible, and every
    # real call site was passing one, so the STOCHASTIC bucket was holding an
    # op that in practice ran deterministically. An op whose declared regime
    # does not match its use is not a tracked exception; it is a defect. The
    # honest resolution is removal, not a bucket. Callers draw their own bytes
    # and compose klein4_encode_bytes, which has C parity all the way down.
    # rc297 (`#934`): +1 composes_c — the general N-slot Cayley–Dickson register
    # adds ONE constructor row, ``cascade.cd_register.cd_register``. This is a
    # POPULATION pin, not a debt ceiling, and a non_compute number going UP is
    # the reading that most deserves suspicion, so the evidence is stated rather
    # than left to inference. The row lands in **composes_c (128 -> 129)** and
    # NOT in host_glue (21, UNCHANGED), and ``CEIL_WIRE_GLUE_GAPS`` stays at
    # **10** — so the op family has real C peers reachable through dispatch glue
    # (srmech_cd_navmap / srmech_cd_navigate /
    # srmech_cd_navmap_is_signed_permutation), not a gap wearing a composition
    # label. That distinction IS the difference between composition and a
    # laundered gap. The constructor itself computes nothing (it allocates an
    # empty slot-map and codebook); all compute is in the methods, which route
    # to those three c_dispatched rows — which is why it also carries a
    # justified entry in COMPOSES_C_ZERO_REACH_PINNED.
    # rc308 (#944): +1 composes_c — laplacian.hypercomplex_perspectives (the
    # quaternion_laplacian / magnetic_laplacian eigenvector channel reader; a
    # pure STRUCTURAL split of an already-decomposed carrier — it computes
    # nothing and reaches no ledger op, so it also carries a justified entry in
    # COMPOSES_C_ZERO_REACH_PINNED, the write_packed_graph accessor precedent).
    # composes_c 129 -> 130; total 201 -> 202.
    # rc312 (§Q8/v16): +1 composes_c (genome.upgrade_v15_to_v16 — the v15->v16 on-disk
    # migration op; a pure-Python manifest re-stamp that reaches C via sha256_bytes,
    # sibling-consistent with genome_save/genome_catalog). composes_c 130 -> 131; total 202 -> 203.
    # rc322 (§Q8-FIBER/v17, F-HOLO-MISLOCATED): +2 composes_c (genome.genome_add_fiber +
    # genome.genome_read_fiber — the fiber cap ASSEMBLE / READ ops; each composes the
    # c_dispatched genome_fiber_holonomy + pure cap byte-framing, sibling-consistent with
    # genome_save). composes_c 131 -> 133; total 203 -> 205.
    # rc325 (§𝕆-FIBER/v18): +3 composes_c (genome.genome_octonion_associator — the two-fold
    # associator DEFECT reader, composes the c_dispatched octonion oct_bind fold; +
    # genome.genome_add_octonion_fiber + genome.genome_read_octonion_fiber — the octonion
    # fiber cap ASSEMBLE / READ ops, each composes the c_dispatched genome_octonion_holonomy
    # + pure cap byte-framing, sibling-consistent with the rc322 Q8 fiber ops). composes_c
    # 133 -> 136; total 205 -> 208.
    # rc364 (ADR-0010's first execution slice): the alias layer gets the catalog
    # shape the [class] layer has had since rc39 — a shipped descriptor
    # directory plus a registration API. THREE rows, and the split across them
    # is the part worth reading, because it is NOT the obvious one.
    #
    #   +1 host_glue   — dsl.resolve_alias_descriptor. Name-or-path -> the
    #                    descriptor's Path. This is descriptor FS DISCOVERY,
    #                    the first phrase in the host_glue definition, and a
    #                    capability a bare-C host genuinely owes: it must FIND
    #                    the file before srmech_toml can parse it. The
    #                    load_catalog / load_class_catalog / get_descriptor
    #                    precedent. host_glue 21 -> 22.
    #   +2 dev_tooling — dsl.list_alias_descriptors + dsl.register_alias_dir.
    #                    BROWSE and CONFIGURE. A bare-C host resolves the one
    #                    name it was handed; it never enumerates the
    #                    alternatives and never mutates a process-local search
    #                    path. Exact peers of list_cascade_ops / list_classes
    #                    and register_catalog_dir / register_class_dir, all
    #                    four already dev_tooling. dev_tooling 51 -> 53.
    #   composes_c UNMOVED at 138 — none of the three composes a C op. The
    #                    alias layer's composes_c rows are the rc261 PARSE ops
    #                    (build_aliases_from_toml_str / load_aliases_toml,
    #                    which route through the C srmech_toml); a resolver
    #                    that returns a Path parses nothing.
    #
    # ⚠️ THE DISCRIMINATOR IS *NOT* "DOES IT TOUCH THE FILESYSTEM" — all three
    # do. It is LOAD/GET vs BROWSE/CONFIGURE, and srmech.dsl already encodes
    # that split over the SAME directory: `load_class_catalog` reads it
    # (host_glue), `list_classes` browses it (dev_tooling). rc364 first shipped
    # list_alias_descriptors as host_glue by reasoning from the mechanism (it
    # calls glob) rather than from the capability, which made it the only
    # host_glue `list_*` in srmech.dsl against five dev_tooling siblings. CI
    # reported the count (21 -> 23 / 51 -> 52); the fix was the CLASSIFICATION,
    # not the pin, and the corrected split is 22 / 53. Total 210 -> 213.
    "composes_c": 138,
    "host_glue": 22,
    "dev_tooling": 53,
}
_TOTAL_NON_COMPUTE = 213        # rc364 (ADR-0010 first execution slice): 210 -> 213, the three srmech.dsl alias-catalog rows (resolve_alias_descriptor -> host_glue; list_alias_descriptors + register_alias_dir -> dev_tooling; see the split note above)  # rc325 (§𝕆-FIBER/v18): 205 -> 208, genome.genome_octonion_associator + genome_add_octonion_fiber + genome_read_octonion_fiber (rc322 §Q8-FIBER/v17: 203 -> 205, genome.genome_add_fiber + genome_read_fiber; rc312 §Q8/v16: 202 -> 203, genome.upgrade_v15_to_v16)  # rc345 (task T964): 208 -> 209, genome.genome_content


def _rows():
    return [json.loads(l) for l in _FIXTURE.read_text(encoding="utf-8").splitlines()
            if l.strip()]


def _non_compute_kind_counts() -> Counter:
    return Counter(r["non_compute_kind"] for r in _rows()
                   if r.get("bucket") == "non_compute")


def test_non_compute_total_matches_pin():
    """The non_compute bucket population equals the single living pin
    ``_TOTAL_NON_COMPUTE`` (updated per-rc; 203 at rc312). The exact count lives
    in the constant, not this test's name — the four-way split is pinned to it."""
    n = sum(1 for r in _rows() if r.get("bucket") == "non_compute")
    assert n == _TOTAL_NON_COMPUTE, (
        f"non_compute bucket has {n} rows, expected {_TOTAL_NON_COMPUTE} — the "
        f"four-way split is pinned to this population; reconcile the split if a "
        f"non_compute op was added / removed."
    )


def test_kind_field_only_on_non_compute_rows():
    """Only ``non_compute`` rows carry a ``non_compute_kind`` — the sub-bucket is a
    property OF the non_compute bucket, not of the compute buckets."""
    misplaced = [r["defined_at"] for r in _rows()
                 if r.get("bucket") != "non_compute" and "non_compute_kind" in r]
    assert not misplaced, (
        f"{len(misplaced)} non-non_compute row(s) carry a non_compute_kind field "
        f"(remove it):\n  " + "\n  ".join(sorted(misplaced))
    )


def test_every_non_compute_row_has_a_kind_in_the_four():
    """Every non_compute row is sub-classified into exactly one of the four kinds
    (no row left unclassified — the split is a partition)."""
    bad = [r["defined_at"] for r in _rows()
           if r.get("bucket") == "non_compute"
           and r.get("non_compute_kind") not in _NON_COMPUTE_KINDS]
    assert not bad, (
        f"{len(bad)} non_compute row(s) have a missing / unknown non_compute_kind "
        f"(must be one of {_NON_COMPUTE_KINDS}):\n  " + "\n  ".join(sorted(bad))
    )


def test_four_way_split_matches_pin():
    """The four sub-bucket counts partition the non_compute rows exactly, summing
    to the single living pin ``_TOTAL_NON_COMPUTE`` (updated per-rc; 203 at rc312).
    The exact number lives in the constant, not this test's name."""
    counts = _non_compute_kind_counts()
    # every counted kind is one of the four
    assert set(counts) <= set(_NON_COMPUTE_KINDS), (
        f"unexpected non_compute_kind values: {set(counts) - set(_NON_COMPUTE_KINDS)}"
    )
    assert dict(counts) == _EXPECTED_SPLIT, (
        f"the four-way split drifted: got {dict(counts)}, expected "
        f"{_EXPECTED_SPLIT}. Re-pin _EXPECTED_SPLIT (and the ceiling / allowlist) "
        f"if a non_compute op moved sub-bucket."
    )
    assert sum(counts.values()) == _TOTAL_NON_COMPUTE == sum(_EXPECTED_SPLIT.values()), (
        f"the four sub-buckets must sum to {_TOTAL_NON_COMPUTE}; got "
        f"{sum(counts.values())}."
    )


def test_owed_ceiling_is_tight():
    """CEIL_NON_COMPUTE_OWED equals the LIVE owed_orchestration count — the phase
    driver is pinned tight (a drop must lower it, a rise is a bare-C-host
    regression). Cross-checks the ledger against the ceiling constant."""
    live = set(rosetta_live_objects())
    live_owed = sum(1 for r in _rows()
                    if r.get("bucket") == "non_compute"
                    and r.get("non_compute_kind") == "owed_orchestration"
                    and r["defined_at"] in live)
    assert CEIL_NON_COMPUTE_OWED == live_owed == _EXPECTED_SPLIT.get(
        "owed_orchestration", 0), (
        f"CEIL_NON_COMPUTE_OWED ({CEIL_NON_COMPUTE_OWED}) must equal the live "
        f"owed_orchestration count ({live_owed}) and the pinned "
        f"{_EXPECTED_SPLIT.get('owed_orchestration', 0)} (rc202: owed is EMPTY — "
        f"the everything-to-C program is complete)."
    )


def test_dev_tooling_allowlist_matches_the_split():
    """The pinned dev_tooling allowlist has exactly the dev_tooling count — the
    allowlist IS the dev_tooling sub-bucket (justified, never owed-C)."""
    assert len(NON_COMPUTE_DEV_TOOLING_EXEMPT) == _EXPECTED_SPLIT["dev_tooling"], (
        f"the dev_tooling allowlist has {len(NON_COMPUTE_DEV_TOOLING_EXEMPT)} "
        f"entries, expected {_EXPECTED_SPLIT['dev_tooling']}."
    )
    ledger_dev = {r["defined_at"] for r in _rows()
                  if r.get("bucket") == "non_compute"
                  and r.get("non_compute_kind") == "dev_tooling"}
    assert ledger_dev == set(NON_COMPUTE_DEV_TOOLING_EXEMPT), (
        "the ledger's dev_tooling rows and the pinned allowlist disagree:\n"
        f"  in ledger only: {sorted(ledger_dev - set(NON_COMPUTE_DEV_TOOLING_EXEMPT))}\n"
        f"  in allowlist only: {sorted(set(NON_COMPUTE_DEV_TOOLING_EXEMPT) - ledger_dev)}"
    )
