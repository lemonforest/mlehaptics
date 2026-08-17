#!/usr/bin/env python3
"""ADVERSARIAL re-derivation of every headline count in
``_1653_chain_census_rc444.ndjson`` — computed from the RECORDS, never from the
script's own ``summary.tally``.  Any claim I cannot reproduce from the per-chain
records is REFUTED.

Read-only.  No numpy / RNG / abs() / fractions.
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PY_ROOT = os.path.abspath(os.path.join(HERE, "..", "python"))
if PY_ROOT not in sys.path:
    sys.path.insert(0, PY_ROOT)

NDJSON = os.path.join(HERE, "_1653_chain_census_rc444.ndjson")

CLAIMED = {
    "executable_chains": 18,
    "chain_variants": 20,
    "leaf_descriptors": 3,
    "catalog_total": 21,
    "c_chain_run_accept": 0,
    "c_chain_run_reject": 18,
    "c_chain_run_reject_variants": 20,
    "c_chain_spec_parse_accept": 11,
    "c_chain_spec_parse_reject": 7,
    "c_chain_catalog_parse_agrees_with_spec_parse": 18,
    "c_toml_front_end_accept": 16,
    "c_toml_front_end_reject": 2,
    "c_dsl_chain_run_accept": 0,
    "byte_identical_python_vs_c": 0,
    "unattributed": 0,
    "python_ok_descriptor_inputs_only": 17,
    "python_ok_with_rc420_gate_case_defaults": 18,
    "shipped_chain_c_eligible_true": 0,
    "shipped_run_chain_native_ran": 0,
    "positive_controls_c_accepted_and_byte_identical": 2,
    "step_forms_python": 3,
    "step_forms_c_chain_run": 1,
    "step_forms_c_spec_parse": 1,
    "step_instances_plain": 115,
    "step_instances_map": 14,
    "step_instances_fold": 5,
    "chains_with_map_or_fold": 6,
    "chains_all_plain": 12,
    "ref_namespaces_python": 7,
    "ref_namespaces_c": 4,
    "variants_using_at_idx": 7,
    "variants_using_at_bind": 7,
    "variants_using_at_op": 1,
    "distinct_ops_used": 47,
    "ops_outside_c_run_table": 47,
    "c_run_op_table_size": 10,
    "ops_rosetta_c_dispatched": 15,
    "ops_rosetta_composition_of_c": 31,
    "ops_rosetta_non_compute": 1,
    "op_table_only_reachable_chains": 11,
    "op_table_only_reachable_distinct_ops": 23,
    "op_table_only_reachable_ops_already_c_dispatched": 14,
}


def main():
    recs = [json.loads(ln) for ln in open(NDJSON, encoding="utf-8")]
    env = [r for r in recs if r["record"] == "environment"][0]
    chains = [r for r in recs if r["record"] == "chain"]
    summary = [r for r in recs if r["record"] == "summary"][0]

    variants = [(c["chain"], v) for c in chains for v in c["variants"]]

    got = {}
    got["executable_chains"] = len(chains)
    got["chain_variants"] = len(variants)
    got["leaf_descriptors"] = len(env["leaf"])
    got["catalog_total"] = env["catalog_total"]

    # ── C run accept/reject, re-derived from the RAW per-case rcs, not from
    #    the script's roll-up booleans.
    def variant_run_accepted(v):
        if v["c_chain_run_structure_probe"].get("rc") != 0:
            return False
        return all(pc.get("rc") == 0 for pc in v["c_chain_run_per_case"])

    got["c_chain_run_reject_variants"] = sum(
        1 for _n, v in variants if not variant_run_accepted(v))
    got["c_chain_run_accept"] = sum(
        1 for c in chains if all(variant_run_accepted(v) for v in c["variants"]))
    got["c_chain_run_reject"] = len(chains) - got["c_chain_run_accept"]

    got["c_chain_spec_parse_accept"] = sum(
        1 for c in chains
        if all(v["c_spec_parse"].get("rc") == 0 for v in c["variants"]))
    got["c_chain_spec_parse_reject"] = (
        len(chains) - got["c_chain_spec_parse_accept"])

    got["c_chain_catalog_parse_agrees_with_spec_parse"] = sum(
        1 for c in chains
        if all((v["c_chain_catalog_parse"].get("rc") == 0)
               == (v["c_spec_parse"].get("rc") == 0) for v in c["variants"]))

    got["c_toml_front_end_accept"] = sum(
        1 for c in chains if c["c_toml_front_end"].get("rc") == 0)
    got["c_toml_front_end_reject"] = len(chains) - got["c_toml_front_end_accept"]

    got["c_dsl_chain_run_accept"] = sum(
        1 for _n, v in variants if v["c_dsl_chain_run"].get("rc") == 0)

    got["byte_identical_python_vs_c"] = sum(
        1 for c in chains if all(variant_run_accepted(v) for v in c["variants"]))

    got["unattributed"] = sum(1 for c in chains if c["unattributed"])

    got["python_ok_descriptor_inputs_only"] = sum(
        1 for c in chains if all(v["python"]["ok"] for v in c["variants"]))
    got["python_ok_with_rc420_gate_case_defaults"] = sum(
        1 for c in chains
        if all(v["python_with_test_defaults"]["ok"] for v in c["variants"]))

    got["shipped_chain_c_eligible_true"] = sum(
        1 for c in chains
        if all(v["shipped_gate"].get("c_eligible") is True
               for v in c["variants"]))
    got["shipped_run_chain_native_ran"] = sum(
        1 for c in chains
        if all(v["shipped_gate"].get("run_chain_native") == "NATIVE_RAN"
               for v in c["variants"]))

    ctls = env["positive_controls"]
    got["positive_controls_c_accepted_and_byte_identical"] = sum(
        1 for c in ctls if c["c_run_rc"] == 0 and c["byte_identical"])

    got["step_forms_python"] = len(env["py_step_forms"])
    got["step_forms_c_chain_run"] = len(env["c_run_step_forms"])
    got["step_forms_c_spec_parse"] = len(env["c_parse_step_forms"])

    for form in ("plain", "map", "fold"):
        got["step_instances_" + form] = sum(
            v["profile"]["step_forms"][form] for _n, v in variants)

    got["chains_with_map_or_fold"] = sum(
        1 for c in chains
        if any(v["profile"]["step_forms"]["map"]
               or v["profile"]["step_forms"]["fold"] for v in c["variants"]))
    got["chains_all_plain"] = sum(
        1 for c in chains
        if all(v["profile"]["step_forms"]["map"] == 0
               and v["profile"]["step_forms"]["fold"] == 0
               for v in c["variants"]))

    got["ref_namespaces_python"] = len(env["py_ref_namespaces"])
    got["ref_namespaces_c"] = len(env["c_ref_namespaces"])

    for ns in ("idx", "bind", "op"):
        got["variants_using_at_" + ns] = sum(
            1 for _n, v in variants
            if ns in v["profile"]["ref_namespaces"])

    c_table = set(env["c_run_op_table"])
    got["c_run_op_table_size"] = len(c_table)
    ops_seen = set()
    for _n, v in variants:
        ops_seen.update(v["profile"]["ops"])
    got["distinct_ops_used"] = len(ops_seen)
    got["ops_outside_c_run_table"] = len(
        [o for o in ops_seen if o not in c_table])

    ros = summary["rosetta"]["per_op"]
    for label, key in (("c_dispatched", "ops_rosetta_c_dispatched"),
                       ("composition_of_c", "ops_rosetta_composition_of_c"),
                       ("non_compute", "ops_rosetta_non_compute")):
        got[key] = sum(1 for o in ros.values() if o["bucket"] == label)

    # ── the op-table-only reachable set: chains the C PARSE accepts.
    reach = [c for c in chains
             if all(v["c_spec_parse"].get("rc") == 0 for v in c["variants"])]
    got["op_table_only_reachable_chains"] = len(reach)
    reach_ops = set()
    for c in reach:
        for v in c["variants"]:
            reach_ops.update(v["profile"]["ops"])
    got["op_table_only_reachable_distinct_ops"] = len(reach_ops)
    got["op_table_only_reachable_ops_already_c_dispatched"] = sum(
        1 for o in reach_ops
        if ros.get(o, {}).get("bucket") == "c_dispatched")

    # ── report
    bad, ok = [], []
    for k in sorted(CLAIMED):
        if k not in got:
            bad.append((k, CLAIMED[k], "NOT_RE_DERIVED"))
        elif got[k] != CLAIMED[k]:
            bad.append((k, CLAIMED[k], got[k]))
        else:
            ok.append(k)
    print("CONFIRMED %d/%d claimed counts re-derived from the per-chain records"
          % (len(ok), len(CLAIMED)))
    for k, claimed, mine in bad:
        print("  MISMATCH %-52s claimed=%s  re-derived=%s" % (k, claimed, mine))

    # ── arithmetic partition checks
    print()
    print("PARTITION CHECKS")
    checks = [
        ("catalog_total == executable + leaf",
         got["catalog_total"], got["executable_chains"] + got["leaf_descriptors"]),
        ("chains == run_accept + run_reject",
         got["executable_chains"],
         got["c_chain_run_accept"] + got["c_chain_run_reject"]),
        ("chains == parse_accept + parse_reject",
         got["executable_chains"],
         got["c_chain_spec_parse_accept"] + got["c_chain_spec_parse_reject"]),
        ("chains == toml_accept + toml_reject",
         got["executable_chains"],
         got["c_toml_front_end_accept"] + got["c_toml_front_end_reject"]),
        ("chains == all_plain + with_map_or_fold",
         got["executable_chains"],
         got["chains_all_plain"] + got["chains_with_map_or_fold"]),
        ("distinct_ops == rosetta c_disp + comp_of_c + non_compute",
         got["distinct_ops_used"],
         got["ops_rosetta_c_dispatched"] + got["ops_rosetta_composition_of_c"]
         + got["ops_rosetta_non_compute"]),
        ("rosetta per_op cardinality == distinct_ops",
         len(ros), got["distinct_ops_used"]),
        ("step_instances total == sum over variants of n_steps_total",
         got["step_instances_plain"] + got["step_instances_map"]
         + got["step_instances_fold"],
         sum(v["profile"]["n_steps_total"] for _n, v in variants)),
        ("reachable_c_dispatched <= rosetta_c_dispatched total",
         got["op_table_only_reachable_ops_already_c_dispatched"] <= got[
             "ops_rosetta_c_dispatched"], True),
        ("variants >= chains (each chain has >=1)",
         got["chain_variants"] >= got["executable_chains"], True),
    ]
    part_bad = 0
    for label, lhs, rhs in checks:
        good = lhs == rhs
        part_bad += 0 if good else 1
        print("  %-58s %s   (%s vs %s)"
              % (label, "OK" if good else "FAIL", lhs, rhs))

    # ── the map/fold variant-union sanity check that looked contradictory
    mf_variants = [(n, v["variant"]) for n, v in variants
                   if v["profile"]["step_forms"]["map"]
                   or v["profile"]["step_forms"]["fold"]]
    mf_chains = sorted({n for n, _v in mf_variants})
    print()
    print("map/fold variant union = %d variants over %d chains: %s"
          % (len(mf_variants), len(mf_chains), mf_variants))
    both = [(n, v["variant"]) for n, v in variants
            if v["profile"]["step_forms"]["map"]
            and v["profile"]["step_forms"]["fold"]]
    print("variants carrying BOTH map and fold: %d %s" % (len(both), both))

    # ── multi-variant chains (where the 18 -> 20 comes from)
    multi = [(c["chain"], c["n_variants"]) for c in chains
             if c["n_variants"] > 1]
    print("multi-variant chains: %s  (sum of n_variants = %d)"
          % (multi, sum(c["n_variants"] for c in chains)))

    print()
    print("VERDICT: %s" % ("ALL CONFIRMED" if not bad and not part_bad
                           else "%d count mismatches, %d partition failures"
                                % (len(bad), part_bad)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
