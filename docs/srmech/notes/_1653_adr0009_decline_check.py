#!/usr/bin/env python3
"""Cross-check every number in `_1653_adr0009_decline_list.md` against the
measurement that produced it.

gh #1653 item 7.  A decline list whose figures drift from its own measurements is
a comment, not a ledger row — which is the exact failure mode ADR-0009 §5 names.
This script is the guard: it reads the measured NDJSON and asserts that the
prose agrees with it, row by row.

Run:  cd docs/srmech/python && python3 ../notes/_1653_adr0009_decline_check.py
Exit 0 iff every check passes.  Re-run it after ANY edit to the list.
"""
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
VERIFY = _HERE / "_1653_adr0009_decline_verify.ndjson"
ROWS = _HERE / "_1653_adr0009_decline_rows.ndjson"
DOC = _HERE / "_1653_adr0009_decline_list.md"

CHECKS = []


def chk(label, cond):
    CHECKS.append((label, bool(cond)))


def main():
    for p in (VERIFY, ROWS, DOC):
        if not p.exists():
            print("MISSING %s" % p)
            return 1
    nd = {}
    for line in VERIFY.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            nd.setdefault(r.get("probe"), []).append(r)
    rows = [json.loads(l) for l in ROWS.read_text(encoding="utf-8").splitlines() if l.strip()]
    doc = DOC.read_text(encoding="utf-8")

    p1 = nd["P1"][0]
    chk("ADR-0009 §5 span is 221-237", p1["span_lines"] == [221, 237]
        and "lines 221–237" in doc)
    chk("§5 content hash quoted in the doc", p1["sha256"] in doc)
    chk("§5 length quoted", p1["char_len"] == 1145 and "1145 characters" in doc)
    chk("all three §5-mandated fields present in §5", p1["all_mandated_present"])

    p2 = nd["P2"][0]
    chk("no decline ledger exists in the tree", p2["ledger_exists_for_declines"] is False)
    chk("files scanned quoted", "%d,%03d" % divmod(p2["files_scanned"], 1000) in doc)
    chk("ROSETTA_LEDGER has the do-not-mirror precedent and no ADR-0009 mention",
        p2["rosetta_ledger"]["has_do_not_mirror_gate"]
        and not p2["rosetta_ledger"]["mentions_ADR_0009"])

    forms = {r["form"]: r for r in nd["P3"] if r.get("record") == "surface_a_form"}
    chk("plain form is the live positive control", forms["plain"]["c_run"] == "OK=0")
    chk("map declines at parse AND run", forms["map"]["c_parse"] == "BAD_INPUT=2"
        and forms["map"]["c_run"] == "BAD_INPUT=2")
    chk("fold declines at parse AND run", forms["fold"]["c_parse"] == "BAD_INPUT=2"
        and forms["fold"]["c_run"] == "BAD_INPUT=2")

    p4 = nd["P4"][0]
    chk("namespaces 7 python / 4 c-parse / 3 c-run",
        (len(p4["python_namespaces"]), len(p4["c_parse_namespaces"]),
         len(p4["c_run_namespaces"])) == (7, 4, 3))
    chk("@catalog parses then fails at run",
        p4["probes"]["catalog"]["c_parse"] == "OK=0"
        and p4["probes"]["catalog"]["c_run"] == "BAD_INPUT=2")
    chk("@input and @row are live controls",
        p4["probes"]["input_CONTROL"]["c_run"] == "OK=0"
        and p4["probes"]["row"]["c_run"] == "OK=0")

    p5 = nd["P5"][0]
    chk("run carrier has no float kind", p5["has_float_kind"] is False)
    chk("single-scalar attribution: int OK, float/bool decline",
        p5["cells"]["single_scalar_CONTROL_int"]["c_run"] == "OK=0"
        and p5["cells"]["single_scalar_float"]["c_run"] == "BAD_INPUT=2"
        and p5["cells"]["single_scalar_bool"]["c_run"] == "BAD_INPUT=2")
    chk("10 float-carrying variants quoted", p5["n_variants_carrying_a_float"] == 10
        and "**10** of the 20 shipped variants" in doc)
    chk("kind 'f' raises on the python side",
        "unknown chain-run value descriptor kind 'f'" in nd["P5b"][0]["kind_f_result"])

    p6 = nd["P6"][0]
    chk("catalog parse v1 OK / v2 BAD_INPUT", p6["c_catalog_parse_v1"] == "OK=0"
        and p6["c_catalog_parse_v2"] == "BAD_INPUT=2")
    chk("18 of 18 descriptors declare schema version 2", p6["n_declaring_2"] == 18)
    chk("python supports (1, 2)", p6["python_supported"] == [1, 2])

    p7 = nd["P7"][0]
    chk("C TOML front end reads 19 of 21, rejecting exactly the two nan/inf files",
        p7["c_ok_count"] == 19 and p7["total"] == 21
        and p7["c_rejected"] == ["best_rational_signed", "magnitude"])
    chk("tomllib reads all 21", p7["python_tomllib_rejected"] == [])
    chk("nan/inf attribution", p7["synthetic"]["finite"] == "OK=0"
        and p7["synthetic"]["nan"] == "BAD_INPUT=2"
        and p7["synthetic"]["inf"] == "BAD_INPUT=2")

    p8 = nd["P8"][0]
    # rc455: parallel_body RUNS in C (dsl_run_parallel), so the P8 capture this
    # reads is a DATED rc444 record and this assertion is re-scoped to the two
    # controls. The "NOT_IMPL=5" half is retained ONLY as the historical value
    # the capture holds; re-running the probe against an rc455 library answers
    # OK=0, which is the point of the row above it in the gap ledger.
    chk("two Surface-B controls pass (parallel_body was NOT_IMPL at rc444; it "
        "RUNS in C from rc455)",
        p8["control_leaf"] == "OK=0" and p8["control_loop_n"] == "OK=0"
        and p8["parallel_body"] in ("NOT_IMPL=5", "OK=0"))
    chk("threading is available on this host", p8["plat_has_threads"] == 1)
    chk("sector dispatch is public and loadable",
        p8["symbols"]["srmech_cascade_parallel_sector_dispatch"]["in_header"]
        and p8["symbols"]["srmech_cascade_parallel_sector_dispatch"]["in_lib"])
    chk("srmech_plat_* is internal-only (the D-10 correction)",
        p8["plat_in_public_header"] is False and p8["plat_in_internal_header"] is True)

    p9 = nd["P9"][0]
    chk("no descriptor-directory loader in the public header",
        p9["header_descriptor_loader_symbols"] == [])
    chk("13 srmech_catalog_* exports", len(p9["srmech_catalog_exports"]) == 13)
    chk("map_op still absent from _COMPOSITE_OP_KEYS",
        p9["map_op_in_composite_keys"] is False)

    p10 = nd["P10"][0]
    chk("op table 10 / 47 used / 47 outside / 15 c_dispatched",
        (p10["c_run_table_size"], p10["distinct_ops_used"],
         p10["ops_outside_table"], p10["ops_with_c_dispatched_row"]) == (10, 47, 47, 15))

    p11 = nd["P11"][0]
    chk("arena min is cyclic_gcd.default, max is klein4_from_one.wound",
        p11["min_name"] == "cyclic_gcd.default"
        and p11["max_name"] == "klein4_from_one.wound")
    # exact-integer band, so no ALU-magnitude idiom is needed to compare
    lo, hi = 17_57 * 1048576 // 100, 17_59 * 1048576 // 100
    chk("arena max 17.58 MB quoted", lo <= p11["max_bytes"] <= hi
        and "17.58 MB" in doc)

    p16 = nd["P16"][0]
    chk("20 body ops, 16 without a C symbol",
        p16["distinct_body_ops"] == 20 and p16["n_without_symbol"] == 16)
    chk("map bounds depth 2 / body 19",
        p16["shipped_map_max_nesting_depth"] == 2
        and p16["shipped_map_max_body_len"] == 19)
    chk("Surface-B coverage 8 of 21 and 5 of 18",
        len(p16["surfaceB_catalog_names_in_c_tables"]) == 8
        and len(p16["surfaceB_executable_in_c_tables"]) == 5)

    chk("the arena decline is CLEAN under four undersized workspaces",
        nd["P17"][0]["decline_is_clean"] is True)

    p18 = nd["P18"][0]
    chk("11 parse-accept / 9 parse-reject / 0 run-accept",
        (p18["parse_accept"], p18["parse_reject"], p18["run_accept"]) == (11, 9, 0))
    chk("7 variants blocked only by the op table",
        len(p18["op_table_is_the_only_blocker"]) == 7)
    chk("4 parse-accepting variants carry a float",
        len(p18["parse_accepting_with_a_float"]) == 4)

    p13 = nd["P13"][0]
    chk("all three #T1146 cells are silent-accept BUGS",
        all(c["verdict"] == "BUG_silent_accept" for c in p13["cells"]))
    chk("#T1146 is recorded as NOT a decline", p13["is_a_decline"] is False)
    chk("the doc says do not launder the bug into the list",
        "Do not launder it into this list" in doc)

    chk("_c_claims 271 rows / 22 unverifiable",
        nd["P14"][0]["claim_rows"] == 271 and nd["P14"][0]["unverifiable"] == 22)
    chk("the routing gate has all three guards",
        nd["P15"][0]["requires_class_N"] and nd["P15"][0]["requires_run_c_ops"]
        and nd["P15"][0]["isinstance_guard"])
    chk("no stale source anchors", nd["PZ"][0]["stale_anchor_count"] == 0)

    dec = [r for r in rows if r["record"] == "decline_row"]
    exc = [r for r in rows if r["record"] == "not_a_decline"]
    ceil = [r for r in rows if r["record"] == "ceiling"]
    chk("11 decline rows in the NDJSON", len(dec) == 11)
    chk("every decline row names present + missing implementations",
        all(r["implementations_present"] and r["implementations_missing"] for r in dec))
    chk("every decline row states a permanence", all(r["permanence"] for r in dec))
    chk("every decline row states a technical reason", all(r["why_declined"] for r in dec))
    chk("every decline row states what would close it", all(r["to_close"] for r in dec))
    chk("no exclusion is marked as a decline", all(r["is_a_decline"] is False for r in exc))
    chk("every ceiling is DOWN_ONLY", all(r["direction"] == "DOWN_ONLY" for r in ceil))
    chk("every NDJSON row id appears in the doc",
        all(("### %s " % r["id"]) in doc or ("**%s**" % r["id"]) in doc for r in dec))

    banned = "a" + "bs("            # never spell the ALU-magnitude token literally
    chk("no ALU-magnitude idiom in the doc", banned not in doc)

    bad = [c for c in CHECKS if not c[1]]
    for label, ok in CHECKS:
        print(("  ok   " if ok else "  FAIL ") + label)
    print()
    print("CONSISTENCY: %d/%d pass, %d FAIL" % (len(CHECKS) - len(bad), len(CHECKS), len(bad)))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
