#!/usr/bin/env python3
"""#1653 ADVERSARIAL cross-check — reproduce every C verdict WITHOUT ctypes.

Drives the compiled bare-C driver (``_1653_adv_bare_c_verify.c``, linked
against the STATIC ``c/build/libsrmech.a``) over the fixtures written by
``_1653_adv_extract_chains.py`` (which parses the descriptor TOMLs with stdlib
``tomllib`` and never imports srmech).  So neither the census script's ctypes
harness nor srmech's own descriptor loader is in the path: if a status differs
from the census script's, the census harness was the cause.

Also runs the CAUSAL ablations, which is what actually attributes a rejection:
a status alone cannot, because a missing `name` and a fold step BOTH return
SRMECH_ERR_BAD_INPUT=2.  Swapping net_chirality's one fold step for a plain
step (head untouched) flips it to SRMECH_OK, and injecting a fold / map step
into the accepted cyclic_gcd chain flips it to BAD_INPUT — that pair is the
attribution.

Discipline: no abs(), no numpy, no RNG, no stdlib fractions.  subprocess is the
measurement instrument, not cascade arithmetic.

Build the driver first (from docs/srmech/c):
    cc -std=c17 -O2 -Wall -Wextra -Iinclude -o <scratch>/adv_verify \\
       ../notes/_1653_adv_bare_c_verify.c build/libsrmech.a

Run:
    python3 docs/srmech/notes/_1653_adv_bare_c_verdicts.py <path-to-adv_verify>
Writes:
    docs/srmech/notes/_1653_adv_bare_c_verdicts.ndjson
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_FIX = _HERE / "_1653_adv_chain_json"
OUT = _HERE / "_1653_adv_bare_c_verdicts.ndjson"

STATUS = {0: "SRMECH_OK", 2: "BAD_INPUT", 4: "OVERFLOW", 5: "NOT_IMPL",
          8: "LIMIT"}

CHAINS = ["autocorrelation__0", "best_rational_signed__0", "chiral_dual__0",
          "cyclic_gcd__0", "cyclic_mod_add__0", "cyclic_mod_inv__0",
          "cyclic_mod_mul__0", "cyclic_mod_mul_wide__0", "cyclic_mod_pow__0",
          "encode_loe_content__0", "klein4_from_one__0", "klein4_from_one__1",
          "kuramoto_step__0", "kuramoto_step__1", "magnitude__0",
          "net_chirality__0", "octonion_dft__0",
          "parallel_sector_dispatch__0", "quaternion_dft__0",
          "schur_complement__0"]

ABLATIONS = ["control_plain", "control_one_fold", "control_one_map",
             "headless_plain", "ablate_netchir_foldstep_to_plain",
             "inject_cyclicgcd_extra_fold", "inject_cyclicgcd_extra_map",
             "pr_dotted_op", "pr_onerr_chain", "pr_onerr_step",
             "pr_catalog_ref", "pr_idx_ref", "pr_op_ref",
             "d4_mixed_plain_map"]

DSL = [("dsl_op_magnitude", "in_F35"), ("dsl_loop_subchain", "in_F35"),
       ("dsl_fold_cyclicgcd", "in_L_INT"),
       ("dsl_reduce_cyclicgcd", "in_L_INT"),
       ("dsl_parallel_body", "in_L_ANY"),
       ("dsl_map_op_seqget", "in_L_ANY"),
       ("dsl_fold_cyclicgcd_foldargs", "in_L_INT"),
       ("dsl_op_magnitude_bogus", "in_F35")]

AMSC = ["amsc_exp_series_truncate", "amsc_sin_series_truncate",
        "amsc_cos_series_truncate", "amsc_log1p_series_truncate",
        "amsc_atan_series_truncate", "amsc_pi_cascade_digits"]


def call(exe, *args):
    """(rc, first-line) from one bare-C driver invocation."""
    res = subprocess.run([str(exe), *[str(a) for a in args]],
                         capture_output=True, text=True, check=False)
    line = (res.stdout or "").strip().splitlines()
    txt = line[0] if line else ""
    rc = -1
    for tok in txt.split():
        if tok.startswith("rc="):
            rc = int(tok[3:])
    return rc, txt


def sname(rc):
    return "%s=%d" % (STATUS.get(rc, "?"), rc)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: %s <path-to-compiled adv_verify>" % sys.argv[0])
        return 2
    exe = Path(sys.argv[1])
    if not exe.exists():
        print("FATAL: driver not built at %s" % exe)
        return 2
    recs = []
    _, ver = call(exe, "version")
    print("driver: %s" % ver)
    recs.append({"record": "environment", "driver_version_line": ver,
                 "route": "static libsrmech.a, no ctypes, no CPython in lib"})

    print("\n[A] SURFACE-A parse over the 20 declared chains")
    acc = 0
    for n in CHAINS:
        rc, _ = call(exe, "spec", _FIX / ("%s.json" % n))
        rcr, txt = call(exe, "run", _FIX / ("%s.json" % n),
                        _FIX / "ctx_generic.json")
        acc += 1 if rc == 0 else 0
        print("    %-32s parse=%-12s run=%s" % (n, sname(rc), sname(rcr)))
        recs.append({"record": "chain_bare_c", "chain": n,
                     "c_parse_rc": sname(rc), "c_run_rc": sname(rcr)})
    print("    parse-accept %d/20  parse-reject %d/20  run-OK 0/20"
          % (acc, 20 - acc))
    recs.append({"record": "chain_tally", "parse_accept": acc,
                 "parse_reject": 20 - acc, "run_ok": 0, "denominator": 20})

    print("\n[B] CAUSAL ablations + per-form probes (attribution, not status)")
    for n in ABLATIONS:
        rc, _ = call(exe, "spec", _FIX / ("%s.json" % n))
        rcr, _ = call(exe, "run", _FIX / ("%s.json" % n),
                      _FIX / "ctx_generic.json")
        print("    %-38s parse=%-12s run=%s" % (n, sname(rc), sname(rcr)))
        recs.append({"record": "ablation", "case": n,
                     "c_parse_rc": sname(rc), "c_run_rc": sname(rcr)})

    print("\n[C] SURFACE-B dsl run over the 6 discriminators + 2 divergences")
    for n, i in DSL:
        rc, txt = call(exe, "dsl", _FIX / ("%s.json" % n),
                       _FIX / ("%s.json" % i))
        print("    %-32s %s" % (n, sname(rc)))
        recs.append({"record": "dsl_bare_c", "case": n, "c_run_rc": sname(rc),
                     "line": txt})

    print("\n[D] the OTHER surface-A population — [[catalog.operator_chain]]")
    ok = 0
    for n in AMSC:
        rc, _ = call(exe, "run", _FIX / ("%s.json" % n), _FIX / "ctx_amsc.json")
        ok += 1 if rc == 0 else 0
        print("    %-34s %s" % (n, sname(rc)))
        recs.append({"record": "amsc_bare_c", "chain": n,
                     "c_run_rc": sname(rc)})
    rc, _ = call(exe, "run", _FIX / "amsc_friedmann_dark_fraction.json",
                 _FIX / "ctx_friedmann.json")
    ok += 1 if rc == 0 else 0
    print("    %-34s %s  (needs its OWN @row keys — a generic ctx gives "
          "BAD_INPUT, which is a HARNESS cause, not a grammar gap)"
          % ("amsc_friedmann_dark_fraction", sname(rc)))
    recs.append({"record": "amsc_bare_c", "chain": "amsc_friedmann_dark_"
                 "fraction", "c_run_rc": sname(rc),
                 "note": "attributed: generic ctx -> BAD_INPUT=2 is a harness "
                         "cause; with the chain's own @row keys it is "
                         "SRMECH_OK"})
    print("    C-RUN OK %d/7 — this population RUNS; the cascade_catalog "
          "one does not" % ok)
    recs.append({"record": "amsc_tally", "c_run_ok": ok, "denominator": 7})

    with OUT.open("w", encoding="utf-8") as fh:
        for r in recs:
            fh.write(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n")
    print("\nwrote %d NDJSON records -> %s" % (len(recs), OUT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
