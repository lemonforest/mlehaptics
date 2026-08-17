#!/usr/bin/env python3
"""gh #1653 — THE SYMBOL GAP, ENUMERATED PER OP. Not one lumped row.

The gap ledger's first cut carried a single row reading "29 of 43 ops have no C
symbol". That row WAS the skip. srmech's own brief rejects exactly this move:

    "'Binding-layer concern' is NOT a legitimate skip-class directive — it's a
     recurrence vector for soft-MVP carve-outs that this project has explicitly
     rejected."   (docs/srmech/CLAUDE.md)

A missing symbol IS the C/Python parity gap. It is not a deferral note about one.
So every op named by a shipped cascade descriptor gets its own row, its own
resolution, and its own disposition. User direction 2026-08-17: "skipping missing
symbols vs fixing a bug we found — missing symbols for python/C parity."

⚠️ THE NAIVE COUNT WAS WRONG IN BOTH DIRECTIONS, which is why per-op matters.
   Matching ``srmech_<op>`` exactly found 6 of 43 and called 37 missing. Probing
   by CONCEPT instead of by spelling resolves most of them: ``render_template``
   is ``srmech_template_render`` (present, argument-order-transposed name),
   ``seq_get`` is ``srmech_vec_get``, ``sha256_bytes`` is ``srmech_sha256_hex``.
   A spelling-based census would have filed ~20 phantom symbol gaps AND still
   missed the real ones.

⚠️ AND THE REAL SHAPE IS NOT "MISSING", IT IS FOUR DIFFERENT THINGS:

   DIRECT    a C symbol exists at the SAME granularity. Pure dispatch-arm work.
   COARSER   C ships the WHOLE op but not the cascade STEP. This is the finding
             the lumped row hid: C has ``srmech_octonion_dft``, while the
             descriptor decomposes that DFT into ``odft_summand`` +
             ``odft_resolve_mu`` + ``dft_scale`` + ``dft_sigma``. The capability
             is present; the GRANULARITY is not. And gh #1653 asks for
             config-driven cascade execution IN C — the descriptor must drive
             the steps — so calling the coarse symbol is NOT parity, it is
             bypassing the grammar the issue exists to make executable.
   FRAMING   no math at all (``pair``, ``str_concat``, ``seq_len``). These want
             an INTERPRETER PRIMITIVE inside the runner, not an exported symbol.
             Filing them as "missing exports" would inflate the count with work
             that must not be done as exports.
   ABSENT    no C at any granularity. The genuine parity holes.

Discipline: no ALU-magnitude idiom, no numpy, no RNG. Read-only; writes NDJSON.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRM = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(SRM, "python"))
OUT = os.path.join(HERE, "_1653_symbol_gap.ndjson")

DIRECT, COARSER, FRAMING, ABSENT = "DIRECT", "COARSER", "FRAMING", "ABSENT"

#: op -> (resolution, C symbol or the reason there is none, note)
#: Hand-classified against `nm` output; the script RE-VERIFIES every named
#: symbol below actually exists, so a rename upstream fails this file rather
#: than silently turning a DIRECT row into a fiction.
RESOLUTION = {
    # ── DIRECT: same granularity, dispatch-arm work only ────────────────────
    "best_rational":  (DIRECT, "srmech_best_rational", "exact-name match"),
    "mint_vector":    (DIRECT, "srmech_mint_vector", "exact-name match"),
    "mod_add":        (DIRECT, "srmech_mod_add", "SHIPPED in this rc"),
    "mod_mul":        (DIRECT, "srmech_mod_mul", "SHIPPED in this rc"),
    "mod_pow":        (DIRECT, "srmech_mod_pow", "SHIPPED in this rc (bigint square-and-multiply)"),
    "mod_inv":        (DIRECT, "srmech_mod_inv",
                       "SHIPPED in this rc, but the ONLY cyclic op still on the "
                       "uint64 wire — no bigint extended-Euclid exists. See the "
                       "gap ledger's bigint_modinv row."),
    "mod_mul_wide":   (DIRECT, "srmech_mod_mul",
                       "SHIPPED in this rc; SAME arm as mod_mul, because 'wide' "
                       "named the absence of a cap and bigint has no cap"),
    "gcd":            (DIRECT, "srmech_bigint_gcd", "SHIPPED in this rc; bigint-native"),
    "vec_add":        (DIRECT, "srmech_vec_add", "exact-name match"),
    "vec_scale":      (DIRECT, "srmech_vec_scale", "exact-name match"),
    "render_template": (DIRECT, "srmech_template_render",
                        "NAME TRANSPOSED — a spelling census files this as missing"),
    "sha256_bytes":   (DIRECT, "srmech_sha256_hex", "Class A; the anchor op"),
    "sha256_raw":     (DIRECT, "srmech_sha256_hex", "same export, raw digest read"),
    "chiral_flip":    (DIRECT, "srmech_cascade_chiral_flip_i64", "+_f64 peer"),
    "pin_slot_at_zero": (DIRECT, "srmech_cascade_pin_slot_at_zero_f64",
                         "Class K pin-slot"),
    "reorient":       (DIRECT, "srmech_cascade_reorient_i64", "+_f64 peer"),
    "permute":        (DIRECT, "srmech_hdc_permute", "Class M"),
    "parallel_sector_dispatch": (DIRECT, "srmech_cascade_parallel_sector_dispatch",
                                 "Klein-4 four-sector"),
    "autocorrelation": (DIRECT, "srmech_autocorrelation_f64", "needs CR_DBL"),
    "seq_get":        (DIRECT, "srmech_vec_get", "Vec carrier only; generic seq is FRAMING"),
    "seq_len":        (DIRECT, "srmech_vec_buf_len", "Vec carrier only"),
    "orientation_compose": (DIRECT, "srmech_cascade_reorient_i64",
                            "Class C sign compose over the reorient export"),

    # ── COARSER: C has the WHOLE op, not the cascade STEP ───────────────────
    "odft_summand":     (COARSER, "srmech_octonion_dft", "step of the whole DFT"),
    "odft_resolve_mu":  (COARSER, "srmech_octonion_dft", "step of the whole DFT"),
    "dft_scale":        (COARSER, "srmech_octonion_dft", "shared by o/q DFT chains"),
    "dft_sigma":        (COARSER, "srmech_octonion_dft", "shared by o/q DFT chains"),
    "qdft_summand":     (COARSER, "srmech_quaternion_dft", "step of the whole DFT"),
    "qdft_resolve_mu":  (COARSER, "srmech_quaternion_dft", "step of the whole DFT"),
    "kuramoto_sin_term": (COARSER, "srmech_cascade_kuramoto_step_f64", "per-term step"),
    "kuramoto_gen_term": (COARSER, "srmech_cascade_kuramoto_step_general_f64",
                          "per-term step of the GENERAL kernel"),
    "kuramoto_gen_out":  (COARSER, "srmech_cascade_kuramoto_step_general_f64", "per-osc out"),
    "kuramoto_out_simple": (COARSER, "srmech_cascade_kuramoto_step_f64", "per-osc out"),
    "kuramoto_inv_n":    (COARSER, "srmech_cascade_kuramoto_step_f64", "the 1/N factor"),
    "correlation_product": (COARSER, "srmech_autocorrelation_f64", "step of the whole autocorr"),

    # ── FRAMING: wants an interpreter primitive, NOT an exported symbol ─────
    "pair":         (FRAMING, None, "builds a 2-tuple; pure structure"),
    "str_concat":   (FRAMING, None, "string join"),
    "byte_slice":   (FRAMING, None, "buffer window"),
    "int_parse_le": (FRAMING, None, "little-endian read from a byte window"),
    "utf8_encode":  (FRAMING, None, "str -> bytes"),
    "as_quat4":     (FRAMING, None, "a 4-wide VIEW of a carrier, not a computation"),
    "as_oct8":      (FRAMING, None, "an 8-wide VIEW of a carrier, not a computation"),

    # ── ABSENT: no C at any granularity — the genuine parity holes ──────────
    "schur_complement": (ABSENT, None,
                         "⚠️ NO srmech_schur* / _dirichlet* / _neumann* symbol "
                         "EXISTS. docs/srmech/CLAUDE.md lists 'the Schur-complement "
                         "/ Dirichlet-to-Neumann Class-L op' among what SHIPPED in "
                         "the v0.7.x arc, against a stated commitment of 'full C "
                         "parity for every primitive class, no exceptions'. This is "
                         "a Class-L op that is Python-only, and the orientation "
                         "brief does not say so."),
    "compensated_sum":  (ABSENT, None, "Kahan/Neumaier summation; no C peer"),
    "f64_add":          (ABSENT, None, "needs CR_DBL before it can even be typed"),
    "dead_band":        (ABSENT, None, "Class-K threshold; srmech_three_fold_bands "
                                       "is a DIFFERENT op, not this one"),
    "scale_round_half_even": (ABSENT, None, "banker's rounding; no C peer"),
    "bind":             (ABSENT, None, "the chain's Class-M bind; srmech_ellbase_bind_* "
                                       "is the ELLBASE bind, a different op — a "
                                       "substring match pairs them wrongly"),
}


def main():
    lib = os.path.join(SRM, "c", "build", "libsrmech.a")
    syms = subprocess.run(["nm", "-g", "--defined-only", lib],
                          capture_output=True, text=True).stdout
    exported = set(re.findall(r"\bT (srmech_[A-Za-z0-9_]+)", syms))

    # RE-VERIFY every claimed symbol. A rename upstream must fail here rather
    # than leave a DIRECT row asserting a symbol that no longer exists.
    fictional = sorted({s for _, s, _ in RESOLUTION.values()
                        if s and s not in exported})
    assert not fictional, (
        "these rows name C symbols that are NOT exported: %s — the resolution "
        "map has gone stale against the library" % fictional)

    from srmech.dsl import _cascade_chain as _cc
    from srmech.dsl import _catalog as _cat
    catalog = _cat.load_catalog()

    def walk(steps):
        for st in steps or []:
            if not isinstance(st, dict):
                continue
            yield st
            for key in ("body", "sub_chain"):
                if isinstance(st.get(key), list):
                    for sub in walk(st[key]):
                        yield sub

    used = {}
    for name in sorted(catalog):
        try:
            entries = _cc._chain_entries(catalog[name])
        except Exception:
            continue
        for entry in entries:
            for st in walk(entry.get("steps")):
                for key in ("op", "fold_op", "reduce_op", "parallel_body", "map_op"):
                    val = st.get(key)
                    if isinstance(val, str):
                        used.setdefault(val.rpartition(".")[2], set()).add(name)

    unclassified = sorted(set(used) - set(RESOLUTION))
    assert not unclassified, (
        "these ops are used by a shipped descriptor and are classified nowhere: "
        "%s — every op gets a row, that is the whole point of this file"
        % unclassified)

    rows, tally = [], {}
    for op in sorted(used):
        res, sym, note = RESOLUTION[op]
        tally[res] = tally.get(res, 0) + 1
        rows.append(dict(op=op, resolution=res, c_symbol=sym, note=note,
                         used_by=sorted(used[op])))

    print("gh #1653 SYMBOL GAP — %d ops used by shipped descriptors" % len(rows))
    print()
    for res, blurb in ((DIRECT, "a C symbol exists at the SAME granularity — dispatch-arm work"),
                       (COARSER, "C ships the WHOLE op, not the cascade STEP"),
                       (FRAMING, "no math — wants an interpreter primitive, NOT an export"),
                       (ABSENT, "no C at any granularity — the genuine parity holes")):
        sel = [r for r in rows if r["resolution"] == res]
        print("%s (%d) — %s" % (res, len(sel), blurb))
        for r in sel:
            print("    %-22s %s" % (r["op"], r["c_symbol"] or "—"))
        print()
    print("tally:", json.dumps(tally, sort_keys=True))
    print("NEEDS A NEW C SYMBOL (ABSENT only):",
          sorted(r["op"] for r in rows if r["resolution"] == ABSENT))

    with open(OUT, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
        fh.write(json.dumps({"record": "summary", "ops": len(rows),
                             "tally": tally}, sort_keys=True) + "\n")
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
