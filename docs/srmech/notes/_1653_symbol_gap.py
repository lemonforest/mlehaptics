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

CLOSED = "CLOSED_IN_THIS_RC"
FILED = "FILED_AS_NEW_ITEM"
DECLINED = "DECLINED_WITH_REASON"

#: Ops whose closure would WIDEN A DISCRIMINATOR SET — a new carrier kind, a new
#: descriptor value kind, a new step form. The standing rule is that such a
#: change must close its projection gap IN THE SAME CHANGE, so the flag is what
#: makes that cost visible at scoping time rather than at implementation time.
#: Everything not listed is False: a dispatch arm over an existing carrier.
NEW_TYPE = {
    "schur_complement": True,      # dense-matrix carrier (Mat)
    "byte_slice": True,            # byte-buffer carrier
    "utf8_encode": True,           # byte-buffer carrier
    "sha256_raw": True,            # raw digest is bytes, not the hex string
    "as_quat4": True,              # a 4-wide carrier VIEW
    "as_oct8": True,               # an 8-wide carrier VIEW
    "pair": True,                  # the chain-run wire has no `t` (tuple) kind
    "bind": True,                  # HV carrier
    "odft_summand": True,          # list[list[float]] — the `l` kind is FLAT
    "odft_resolve_mu": True,
    "qdft_summand": True,
    "qdft_resolve_mu": True,
    "dft_scale": True,
    "dft_sigma": True,
    "parallel_sector_dispatch": True,   # mapping carrier + the @op namespace
}

#: Ops the review's Amendment-2 disposition is held elsewhere for, so this file
#: does not claim them. schur_complement's DOC defect (docs/srmech/CLAUDE.md
#: asserting C parity it does not have) is claimed by the docs/publish session
#: for the next docs rc — explicitly "leave it out of the C build scope". The C
#: SYMBOL remains this issue's to file, and does; only the doc fix is theirs.
CLAIMED_ELSEWHERE = {
    "schur_complement": "the CLAUDE.md parity claim is the docs session's "
                        "(next docs rc); the missing C symbol stays filed here",
}

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

    # Dead config fails rather than sitting inert: a NEW_TYPE / CLAIMED_ELSEWHERE
    # key naming something that is not an op used by a descriptor is a typo or a
    # stale entry, and either way it silently flags nothing. (Caught one on the
    # first run — `encode_loe_content`, which is a CHAIN, not an op.)
    for label, table in (("NEW_TYPE", NEW_TYPE),
                         ("CLAIMED_ELSEWHERE", CLAIMED_ELSEWHERE)):
        phantom = sorted(set(table) - set(used))
        assert not phantom, (
            "%s names %s, which no shipped descriptor uses as an op — a stale "
            "or mistyped key flags nothing and reads as though it does"
            % (label, phantom))

    unclassified = sorted(set(used) - set(RESOLUTION))
    assert not unclassified, (
        "these ops are used by a shipped descriptor and are classified nowhere: "
        "%s — every op gets a row, that is the whole point of this file"
        % unclassified)

    # Which ops the C dispatch ACTUALLY handles now — read from the source, so
    # `disposition` is measured rather than declared and cannot drift.
    csrc = open(os.path.join(SRM, "c", "src", "srmech_compose_run.c"),
                encoding="utf-8").read()
    dispatched = set(re.findall(r'memcmp\(op,\s*"([a-z0-9_]+)"', csrc))
    dispatched |= set(re.findall(r'memcmp\(op \+ \([^)]*\),\s*"([a-z0-9_]+)"', csrc))
    dispatched |= set(re.findall(r'memcmp\(op \+ \(opl - \d+u\), "([a-z0-9_]+)"', csrc))
    # the fold body table is a separate dispatch surface
    dispatched |= {"orientation_compose"} if "orientation_compose" in csrc else set()

    rows, tally, disp_tally = [], {}, {}
    for op in sorted(used):
        res, sym, note = RESOLUTION[op]
        tally[res] = tally.get(res, 0) + 1
        disposition = CLOSED if op in dispatched else FILED
        row = dict(op=op, resolution=res, c_symbol=sym, note=note,
                   used_by=sorted(used[op]),
                   disposition=disposition,
                   is_new_type=bool(NEW_TYPE.get(op, False)))
        if op in CLAIMED_ELSEWHERE:
            row["claimed_elsewhere"] = CLAIMED_ELSEWHERE[op]
        disp_tally[disposition] = disp_tally.get(disposition, 0) + 1
        rows.append(row)

    # ADR-0009 §5: exactly one disposition per row, and only the three names.
    for r in rows:
        assert r["disposition"] in (CLOSED, FILED, DECLINED), r["op"]
        assert isinstance(r["is_new_type"], bool), r["op"]

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
    print("tally by resolution:", json.dumps(tally, sort_keys=True))
    print("tally by DISPOSITION:", json.dumps(disp_tally, sort_keys=True),
          " (measured from the C dispatch source, not declared)")
    print("is_new_type TRUE (closure widens a discriminator set):",
          sum(1 for r in rows if r["is_new_type"]))
    print("NEEDS A NEW C SYMBOL (ABSENT only):",
          sorted(r["op"] for r in rows if r["resolution"] == ABSENT))

    with open(OUT, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
        fh.write(json.dumps({"record": "summary", "ops": len(rows),
                             "tally": tally, "by_disposition": disp_tally,
                             "new_type_count": sum(1 for r in rows
                                                   if r["is_new_type"])},
                            sort_keys=True) + "\n")
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
