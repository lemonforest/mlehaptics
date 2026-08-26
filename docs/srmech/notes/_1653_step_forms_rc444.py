#!/usr/bin/env python3
"""#1653 pre-rcN research — the AUTHORITATIVE STEP-FORM INVENTORY, both projections.

Measures, at srmech 0.9.0rc444 / native ABI 17, EVERY step form the config-driven
chain grammar accepts on the Python side and what the C projection does with it.

TWO GRAMMARS, NOT ONE.  The issue says "the config-driven cascade surface"; there
are two distinct step grammars behind that phrase and they have OPPOSITE parity
shapes, so a single number cannot describe both:

  SURFACE A — ``[[cascade.chain.steps]]`` (ADR-0002/ADR-0008 schema v1/v2), the
    engine in ``srmech/cascade/compose.py``.  THIS is the grammar the 21 packaged
    cascade_catalog descriptors actually declare their chains in.  C peers:
    ``srmech_chain_spec_parse`` / ``srmech_chain_catalog_parse``
    (``c/src/srmech_compose.c``) + ``srmech_chain_run`` /
    ``srmech_catalog_run_chain`` (``c/src/srmech_compose_run.c``).

  SURFACE B — ``[[stage]]`` (the srmech.dsl chain-spec), the dispatcher in
    ``srmech/dsl/_toml_chain.py`` + the builder in ``srmech/dsl/_chain.py``.
    C peer: ``srmech_dsl_chain_run`` (+ the TOML front end
    ``srmech_dsl_toml_chain_to_json``), both in ``c/src/srmech_dsl_chain_run.c``.

HARNESS-CONFOUND DISCIPLINE.  Every C verdict below is the ACTUAL
``srmech_status_t`` from a direct ctypes call on the shipped ``libsrmech.so``,
arena-sized with the symbol's own ``*_arena_bytes`` helper, using the SAME JSON
shape the shipped Python dispatcher marshals.  Each C entry point is first
exercised with a POSITIVE CONTROL that must return SRMECH_OK; if a control
fails the script says so and refuses to attribute anything, because a rejection
from a mis-sized arena or a wrong payload shape is worthless.

MEASURED HARNESS ARTEFACT worth recording: a naive "strip the offending steps and
re-parse" reduction reports a SPURIOUS rejection, because deleting a step
RENUMBERS the surviving ``@step[N]`` references and trips the static bounds check.
The reduction used here preserves indices by substituting a trivially-valid
filler step, which is why per-step isolation resolves cleanly.

Discipline: no abs() (Class-K pin-slot ops are called by NAME where a magnitude is
wanted), no numpy, no RNG, no stdlib fractions, exact integers only.  ctypes is
the measurement instrument, not cascade arithmetic.

Run:
    cd docs/srmech/python && python3 ../notes/_1653_step_forms_rc444.py
Writes:
    docs/srmech/notes/_1653_step_forms_rc444.ndjson
"""

from __future__ import annotations

import ctypes
import json
import os
import sys
from pathlib import Path

# ── locate the source tree (this script lives in docs/srmech/notes/) ──────────
_HERE = Path(__file__).resolve().parent
_PY = _HERE.parent / "python"
if str(_PY) not in sys.path:
    sys.path.insert(0, str(_PY))

import srmech                                              # noqa: E402
from srmech import _native                                 # noqa: E402
from srmech.cascade import compose as CO                   # noqa: E402
from srmech.dsl import _catalog as DCAT                    # noqa: E402
from srmech.dsl import _cascade_chain as DCC               # noqa: E402
from srmech.dsl import _toml_chain as DTOML                # noqa: E402
from srmech.dsl import chain as dsl_chain                  # noqa: E402
from srmech.dsl._chain import _NATIVE_MISS                 # noqa: E402

OUT = _HERE / "_1653_step_forms_rc444.ndjson"

STATUS = {0: "SRMECH_OK", 1: "NULL_ARG", 2: "BAD_INPUT", 3: "IO",
          4: "OVERFLOW", 5: "NOT_IMPL", 6: "INTERNAL", 8: "LIMIT"}


def sname(rc: int) -> str:
    return f"{STATUS.get(rc, '?')}={rc}"


# ── raw C callers (each mirrors the shipped Python dispatcher's marshalling) ──

def c_chain_spec_parse(chain_dict):
    """srmech_chain_spec_parse — SURFACE A parse+validate. -> (rc, text|None)."""
    lib = _native.LIB
    p = json.dumps(chain_dict, ensure_ascii=False).encode("utf-8")
    nb = int(lib.srmech_chain_spec_parse_arena_bytes(len(p)))
    ws = (ctypes.c_char * nb)()
    cap = 2 * len(p) + 8192
    out = (ctypes.c_char * cap)()
    ol = ctypes.c_size_t()
    rc = lib.srmech_chain_spec_parse(p, len(p), ws, nb, out, cap,
                                     ctypes.byref(ol))
    return rc, (out.raw[:ol.value].decode("utf-8") if rc == 0 else None)


def c_chain_catalog_parse(schema_version, chains):
    """srmech_chain_catalog_parse — SURFACE A catalog-level parse."""
    lib = _native.LIB
    payload = {"chain_schema_version": schema_version,
               "operator_chain": chains}
    p = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    nb = int(lib.srmech_chain_catalog_parse_arena_bytes(len(p)))
    ws = (ctypes.c_char * nb)()
    cap = 2 * len(p) + 8192
    out = (ctypes.c_char * cap)()
    ol = ctypes.c_size_t()
    rc = lib.srmech_chain_catalog_parse(p, len(p), ws, nb, out, cap,
                                        ctypes.byref(ol))
    return rc, (out.raw[:ol.value].decode("utf-8") if rc == 0 else None)


def c_chain_run(chain_dict, ctx):
    """srmech_chain_run — SURFACE A run loop. -> (rc, value-descriptor|None)."""
    lib = _native.LIB
    cj = json.dumps(chain_dict, ensure_ascii=False).encode("utf-8")
    xj = json.dumps(ctx, ensure_ascii=False).encode("utf-8")
    nb = int(lib.srmech_chain_run_arena_bytes(len(cj), len(xj)))
    ws = (ctypes.c_char * nb)()
    cap = max(nb // 2, 16384)
    out = (ctypes.c_char * cap)()
    ol = ctypes.c_size_t()
    rc = lib.srmech_chain_run(cj, len(cj), xj, len(xj), ws, nb, out, cap,
                              ctypes.byref(ol))
    return rc, (out.raw[:ol.value].decode("utf-8") if rc == 0 else None)


def c_dsl_chain_run(stages, input_desc, name="probe"):
    """srmech_dsl_chain_run — SURFACE B run loop. -> (rc, F1 descriptor|None)."""
    lib = _native.LIB
    cj = json.dumps({"chain": {"name": name}, "stage": stages},
                    ensure_ascii=False).encode("utf-8")
    ij = json.dumps(input_desc, ensure_ascii=False).encode("utf-8")
    nb = int(lib.srmech_dsl_chain_run_arena_bytes(len(cj), len(ij)))
    ws = (ctypes.c_char * nb)()
    cap = max(nb // 2, 16384)
    out = (ctypes.c_char * cap)()
    ol = ctypes.c_size_t()
    rc = lib.srmech_dsl_chain_run(cj, len(cj), ij, len(ij), ws, nb, out, cap,
                                  ctypes.byref(ol))
    return rc, (out.raw[:ol.value].decode("utf-8") if rc == 0 else None)


def c_dsl_toml_to_json(toml_src: bytes):
    """srmech_dsl_toml_chain_to_json — the bare-C-host TOML front end."""
    lib = _native.LIB
    nb = int(lib.srmech_dsl_toml_chain_to_json_arena_bytes(len(toml_src)))
    ws = (ctypes.c_char * nb)()
    cap = 8 * len(toml_src) + 65536
    out = (ctypes.c_char * cap)()
    ol = ctypes.c_size_t()
    rc = lib.srmech_dsl_toml_chain_to_json(toml_src, len(toml_src), ws, nb,
                                           out, cap, ctypes.byref(ol))
    return rc, (out.raw[:ol.value].decode("utf-8") if rc == 0 else None)


# ── surface-A probe helpers ───────────────────────────────────────────────────

A_HEAD = {"name": "probe", "summary": "s", "returns": "r"}
A_PLAIN = {"class": "N", "op": "rational_add", "args": {"a": [1, 2],
                                                       "b": [1, 3]}}
A_FILLER = {"class": "N", "op": "rational_add", "args": {}}
A_CTX = {"row": {"a": [1, 2]}, "inputs": {"a": [1, 2], "seq": [1, 2, 3]}}


def a_chain(steps, **kw):
    d = dict(A_HEAD)
    d["steps"] = steps
    d.update(kw)
    return d


def a_python_parses(steps, **kw):
    """(ok, detail) for the PYTHON validator on surface A (pure path forced by
    routing through parse_chain_spec, whose native arm defers on any v2 form)."""
    try:
        spec = CO.parse_chain_spec(a_chain(steps, **kw))
        kinds = sorted({type(s).__name__ for s in spec.steps})
        return True, ",".join(kinds)
    except Exception as exc:                        # noqa: BLE001
        return False, f"{type(exc).__name__}: {str(exc)[:110]}"


def b_python_builds(stage, run_input=None, do_run=False):
    """(ok, detail) for the PYTHON dispatcher on surface B."""
    try:
        ch = DTOML.build_chain_from_dict({"chain": {"name": "probe"},
                                          "stage": [stage]})
    except Exception as exc:                        # noqa: BLE001
        return False, f"BUILD {type(exc).__name__}: {str(exc)[:110]}"
    if not do_run:
        return True, "build-ok"
    try:
        return True, f"run-ok {ch.run(run_input)!r}"
    except Exception as exc:                        # noqa: BLE001
        return False, f"RUN {type(exc).__name__}: {str(exc)[:110]}"


# ── the form inventory ───────────────────────────────────────────────────────
# Each entry: (surface, form, kind, python_src, c_src, probe-key)
#
# `kind`:
#   "discriminator" — a key whose PRESENCE selects how the step executes.
#   "parameter"     — a key read only AFTER a discriminator has selected a form.
#   Reference namespaces are classified "parameter": they are arg-VALUE grammar,
#   not step selectors; they are listed because C recognises a strict subset and
#   an unrecognised namespace rejects the whole step.

records = []


def emit(**kw):
    records.append(kw)


def main() -> int:
    lib_ok = _native.HAS_NATIVE and _native.LIB is not None
    print("=" * 78)
    print("#1653 STEP-FORM INVENTORY — srmech %s / native ABI %s / has_native=%s"
          % (srmech.__version__, _native.NATIVE_ABI_VERSION, _native.HAS_NATIVE))
    print("=" * 78)
    if not lib_ok:
        print("FATAL: no native library bound; every C verdict would be "
              "UNATTRIBUTED. Aborting.")
        return 2

    # ── POSITIVE CONTROLS ────────────────────────────────────────────────────
    print("\n[0] POSITIVE CONTROLS (a failure here invalidates every C verdict)")
    controls = {}
    rc, txt = c_chain_spec_parse(a_chain([A_PLAIN]))
    controls["srmech_chain_spec_parse"] = (rc, txt is not None)
    print("    srmech_chain_spec_parse      %s" % sname(rc))
    rc2, val2 = c_chain_run(a_chain([A_PLAIN]), A_CTX)
    controls["srmech_chain_run"] = (rc2, val2)
    print("    srmech_chain_run             %s  -> %s" % (sname(rc2), val2))
    rc3, val3 = c_chain_catalog_parse(1, [a_chain([A_PLAIN])])
    controls["srmech_chain_catalog_parse"] = (rc3, val3 is not None)
    print("    srmech_chain_catalog_parse   %s" % sname(rc3))
    rc4, val4 = c_dsl_chain_run([{"op": "magnitude"}], {"k": "f", "v": -3.5})
    controls["srmech_dsl_chain_run"] = (rc4, val4)
    print("    srmech_dsl_chain_run         %s  -> %s" % (sname(rc4), val4))
    rc5, val5 = c_dsl_toml_to_json(b'[chain]\nname = "t"\n[[stage]]\n'
                                   b'op = "magnitude"\n')
    controls["srmech_dsl_toml_chain_to_json"] = (rc5, val5)
    print("    srmech_dsl_toml_chain_to_json %s -> %s" % (sname(rc5), val5))
    all_ok = all(v[0] == 0 for v in controls.values())
    print("    ALL CONTROLS OK: %s" % all_ok)
    emit(record="controls", all_ok=all_ok,
         detail={k: sname(v[0]) for k, v in controls.items()})
    if not all_ok:
        print("FATAL: a control failed — refusing to attribute rejections.")
        return 2

    # ── SURFACE A: the compose / [[cascade.chain.steps]] grammar ─────────────
    print("\n[1] SURFACE A — [[cascade.chain.steps]] (compose.py, ADR-0008 v1/v2)")
    print("    the grammar the 21 packaged cascade_catalog descriptors USE")

    map_step = {"map_over": "@input.seq", "index": "k",
                "bind": {"s": "@input.seq"}, "body": [dict(A_PLAIN)]}
    fold_step = {"fold_class": "I", "fold_op": "gcd", "fold_init": 0,
                 "over": "@input.seq"}

    a_probes = [
        # (form, kind, python_src, c_src, steps, chain_kw, note)
        ("plain (class+op+args)", "discriminator", "compose.py:630-659",
         "srmech_compose.c:287-319 co_build_step; "
         "srmech_compose_run.c:713-730 cr_run_steps",
         [dict(A_PLAIN)], {}, "the v1 step form"),
        ("map (map_over+body)", "discriminator", "compose.py:662-719 "
         "_parse_map_step",
         "srmech_compose.c:299-303 (co_build_step demands class+op+args); "
         "srmech_compose_run.c:722-724",
         [dict(A_PLAIN), map_step], {}, "schema-v2 indexed map"),
        ("fold (fold_class+fold_op+fold_init+over)", "discriminator",
         "compose.py:722-770 _parse_fold_step",
         "srmech_compose.c:299-303; srmech_compose_run.c:722-724",
         [fold_step], {}, "schema-v2 catamorphism"),
        ("class", "parameter", "compose.py:636-641",
         "srmech_compose.c:105-110 co_class_valid (parse); NEVER read by "
         "srmech_compose_run.c:713-730 (run)",
         [dict(A_PLAIN)], {}, "classification, not addressing"),
        ("op (bare)", "parameter", "compose.py:642 + :1192-1211",
         "srmech_compose.c:299-303 (any string); "
         "srmech_compose_run.c:581-617 cr_dispatch (10-op table)",
         [dict(A_PLAIN)], {}, "resolved via the A-N letter registry"),
        ("op (dotted)", "parameter", "compose.py:1189-1191 + :804-829",
         "srmech_compose.c:301 accepts any string; "
         "srmech_compose_run.c:616 NOT_IMPL (no import arm in C)",
         [{"class": "N", "op": "srmech.math.rational.rational_add",
           "args": {"a": [1, 2], "b": [1, 3]}}], {}, "v2 BLK-REGMAP addressing"),
        ("args", "parameter", "compose.py:643-648",
         "srmech_compose.c:304-307; srmech_compose_run.c:725",
         [dict(A_PLAIN)], {}, ""),
        ("on_error (chain-level, non-raise)", "parameter", "compose.py:572-577",
         "srmech_compose.c:344-354 accepts all 3 policies; "
         "srmech_compose_run.c:703-704 accepts ONLY \"raise\"",
         [dict(A_PLAIN)], {"on_error": "warn_return_none"}, ""),
        ("on_error (step-level)", "parameter", "compose.py:649-654",
         "srmech_compose.c:270-284 co_step_on_error accepts; "
         "srmech_compose_run.c:718-719 rejects any non-null",
         [dict(A_PLAIN, on_error="warn_return_none")], {}, ""),
        ("index (map)", "parameter", "compose.py:681-687",
         "srmech_compose.c: absent (no map arm)",
         [{"map_over": "@input.seq", "index": "k", "body": [dict(A_PLAIN)]}],
         {}, ""),
        ("bind (map)", "parameter", "compose.py:688-696",
         "srmech_compose.c: absent (no map arm)",
         [{"map_over": "@input.seq", "bind": {"s": "@input.seq"},
           "body": [dict(A_PLAIN)]}], {}, ""),
        ("body (map)", "parameter", "compose.py:697-702 + :714-717",
         "srmech_compose.c: absent (no map arm)",
         [{"map_over": "@input.seq", "body": [dict(A_PLAIN)]}], {}, ""),
        ("map_over (map)", "parameter", "compose.py:674-680",
         "srmech_compose.c: absent (no map arm)",
         [{"map_over": "@input.seq", "body": [dict(A_PLAIN)]}], {}, ""),
        ("fold_class", "parameter", "compose.py:734-739",
         "srmech_compose.c: absent (no fold arm)", [fold_step], {}, ""),
        ("fold_op", "parameter", "compose.py:740",
         "srmech_compose.c: absent (no fold arm)", [fold_step], {}, ""),
        ("fold_init", "parameter", "compose.py:748-751",
         "srmech_compose.c: absent (no fold arm)", [fold_step], {}, ""),
        ("over (fold)", "parameter", "compose.py:741-747",
         "srmech_compose.c: absent (no fold arm)", [fold_step], {}, ""),
        ("fold_args", "parameter", "compose.py:752-761",
         "srmech_compose.c: absent (no fold arm)",
         [dict(fold_step, fold_args=["a", "b"])], {}, "rc420 kw-only fold fix"),
        ("@row.<path>", "parameter", "compose.py:151-154 + :862-867",
         "srmech_compose.c:144 co_match_namespace; "
         "srmech_compose_run.c cr_resolve_ref",
         [{"class": "N", "op": "rational_add",
           "args": {"a": "@row.a", "b": [1, 3]}}], {}, ""),
        ("@input.<path>", "parameter", "compose.py:151-154 + :868-869",
         "srmech_compose.c:145 co_match_namespace",
         [{"class": "N", "op": "rational_add",
           "args": {"a": "@input.a", "b": [1, 3]}}], {}, ""),
        ("@step[N].output", "parameter", "compose.py:151-154 + :870-887",
         "srmech_compose.c:146 + :190-213 co_scan_path; "
         "srmech_compose_run.c:280-286",
         [dict(A_PLAIN), {"class": "N", "op": "rational_mul",
                          "args": {"a": "@step[0].output", "b": [1, 3]}}],
         {}, ""),
        ("@catalog.<row>.<col>", "parameter", "compose.py:151-154 + :893-924",
         "srmech_compose.c:147 accepts the namespace; "
         "srmech_compose_run.c:288 returns NULL -> defer",
         [{"class": "N", "op": "rational_add",
           "args": {"a": "@catalog.foo.bar", "b": [1, 3]}}], {}, ""),
        # @idx / @bind are legal ONLY inside a map body, so the Python verdict is
        # taken in MAP SCOPE (a plain-step probe would report a spurious
        # python_accepts=False — the unbound-name guard, not a grammar gap).
        ("@idx.<name>", "parameter", "compose.py:151-157 + :303-315",
         "srmech_compose.c:135-149 co_match_namespace knows only "
         "row/input/step/catalog",
         [{"map_over": "@input.seq", "index": "k",
           "body": [{"class": "N", "op": "rational_add",
                     "args": {"a": "@idx.k", "b": [1, 3]}}]}], {},
         "v2-only; legal ONLY inside a map body (probed in map scope)"),
        ("@bind.<name>", "parameter", "compose.py:151-157 + :316-323",
         "srmech_compose.c:135-149 co_match_namespace",
         [{"map_over": "@input.seq", "bind": {"s": "@input.seq"},
           "body": [{"class": "N", "op": "rational_add",
                     "args": {"a": "@bind.s", "b": [1, 3]}}]}], {},
         "v2-only; legal ONLY inside a map body (probed in map scope)"),
        ("@op.<dotted.path>", "parameter", "compose.py:151-157 + :324-330",
         "srmech_compose.c:135-149 co_match_namespace",
         [{"class": "N", "op": "rational_add",
           "args": {"a": "@op.srmech.math.rational.gcd", "b": [1, 3]}}], {},
         "v2-only op-as-value"),
    ]

    a_tally = {"discriminator": {}, "parameter": {}}
    print("    %-42s %-13s %-9s %-11s %-11s %s" %
          ("form", "kind", "py", "C-parse", "C-run", "verdict"))
    for (form, kind, psrc, csrc, steps, ckw, note) in a_probes:
        py_ok, py_detail = a_python_parses(steps, **ckw)
        rc_p, _ = c_chain_spec_parse(a_chain(steps, **ckw))
        rc_r, val_r = c_chain_run(a_chain(steps, **ckw), A_CTX)
        if rc_p == 0 and rc_r == 0:
            status = "executes"
        elif rc_p == 0:
            status = "parses_rejects"
        else:
            status = "unrecognised"
        a_tally[kind][status] = a_tally[kind].get(status, 0) + 1
        print("    %-42s %-13s %-9s %-11s %-11s %s" %
              (form[:42], kind[:13], "yes" if py_ok else "NO",
               sname(rc_p), sname(rc_r), status))
        emit(record="form", surface="A_cascade_chain_steps", form=form,
             kind=kind, python_accepts=py_ok, python_src=psrc,
             python_detail=py_detail, c_status=status, c_src=csrc,
             c_parse_rc=sname(rc_p), c_run_rc=sname(rc_r),
             c_run_value=val_r, note=note,
             evidence=("srmech_chain_spec_parse -> %s; srmech_chain_run -> %s"
                       % (sname(rc_p), sname(rc_r))))

    # chain_schema_version is a CATALOG-level key, probed via its own peer
    py_v2 = True
    try:
        CO.parse_catalog_chains({"catalog": {"chain_schema_version": 2,
                                             "operator_chain":
                                                 [a_chain([dict(A_PLAIN)])]}})
    except Exception as exc:                        # noqa: BLE001
        py_v2 = False
        v2_detail = f"{type(exc).__name__}: {exc}"
    else:
        v2_detail = "accepted"
    rc_v1, _ = c_chain_catalog_parse(1, [a_chain([dict(A_PLAIN)])])
    rc_v2, _ = c_chain_catalog_parse(2, [a_chain([dict(A_PLAIN)])])
    print("    %-42s %-13s %-9s v1=%-6s v2=%s" %
          ("chain_schema_version (catalog)", "parameter",
           "yes" if py_v2 else "NO", sname(rc_v1), sname(rc_v2)))
    emit(record="form", surface="A_cascade_chain_steps",
         form="chain_schema_version (catalog-level)", kind="parameter",
         python_accepts=py_v2, python_src="compose.py:124 + :1450-1461",
         python_detail=v2_detail,
         c_status="parses_rejects",
         c_src="srmech_compose.c:513 (+:675) and srmech_compose_run.c:868 "
               "hard-require ver->u.i == 1",
         c_parse_rc=f"v1={sname(rc_v1)} v2={sname(rc_v2)}", c_run_rc="n/a",
         c_run_value=None,
         note="Python SUPPORTED_SCHEMA_VERSIONS == (1, 2); C accepts ONLY 1",
         evidence="srmech_chain_catalog_parse(schema=1) -> %s, (schema=2) -> %s"
                  % (sname(rc_v1), sname(rc_v2)))
    a_tally["parameter"]["parses_rejects"] = \
        a_tally["parameter"].get("parses_rejects", 0) + 1
    print("    SURFACE-A TALLY  discriminators: %s" % a_tally["discriminator"])
    print("                     parameters:     %s" % a_tally["parameter"])
    emit(record="surface_tally", surface="A_cascade_chain_steps",
         discriminators=a_tally["discriminator"],
         parameters=a_tally["parameter"],
         headline="C implements 1 of 3 step forms (plain executes; map and "
                  "fold are unrecognised)")

    # ── SURFACE B: the dsl / [[stage]] grammar ──────────────────────────────
    print("\n[2] SURFACE B — [[stage]] (dsl/_toml_chain.py + dsl/_chain.py)")
    L_INT = {"k": "l", "v": [{"k": "i", "v": 12}, {"k": "i", "v": 18}]}
    L_ANY = {"k": "l", "v": [{"k": "i", "v": 1}, {"k": "i", "v": 2}]}
    F35 = {"k": "f", "v": -3.5}

    b_probes = [
        ("op", "discriminator", "_toml_chain.py:225/:248-256 (+ _chain.py:217 "
         "then)", "srmech_dsl_chain_run.c:835-839 -> :537-565 "
         "dsl_leaf_dispatch (7-op table)",
         {"op": "magnitude"}, F35, -3.5, "7 C-backed unary atoms"),
        ("loop_n + sub_chain", "discriminator",
         "_toml_chain.py:226/:258-286 (+ _chain.py:252 loop)",
         "srmech_dsl_chain_run.c:637 disc table -> :657-678 dsl_run_loop",
         {"loop_n": 3, "sub_chain": [{"op": "magnitude"}]}, F35, -3.5,
         "DCR_MAX_LOOP_N / DCR_MAX_SUBCHAIN_DEPTH bounded"),
        ("fold_init + fold_op", "discriminator",
         "_toml_chain.py:227/:288-312 (+ _chain.py:282 fold)",
         "srmech_dsl_chain_run.c:637 -> :682-706 dsl_run_fold -> :603-620 "
         "dsl_binary_dispatch (cyclic_gcd ONLY)",
         {"fold_init": 0, "fold_op": "cyclic_gcd"}, L_INT, [12, 18], ""),
        ("reduce_op", "discriminator",
         "_toml_chain.py:228/:325-333 (+ _chain.py:318 reduce)",
         "srmech_dsl_chain_run.c:637 -> :710-732 dsl_run_reduce -> :603-620 "
         "(cyclic_gcd ONLY)",
         {"reduce_op": "cyclic_gcd"}, L_INT, [12, 18], ""),
        ("parallel_body", "discriminator",
         "_toml_chain.py:229/:335-365 (+ _chain.py:340 parallel_sectors)",
         # ⚠️ THE CHECKED-IN .ndjson BESIDE THIS FILE IS THE rc444 CAPTURE
         # AND IS DELIBERATELY NOT REGENERATED. Re-running this probe against an
         # rc455 library rewrites 40 of its 55 rows — the library has gained
         # capabilities across many unrelated forms since rc444, so a
         # regeneration would silently re-date a record whose whole identity is
         # the release in its filename. Only THIS SOURCE line is corrected, so
         # the description of the C source is true today while the capture stays
         # what it captured. Re-run the probe to see current behaviour.
         "srmech_dsl_chain_run.c: RECOGNISED and RUN since rc455 "
         "(dsl_run_parallel; the four sector duals evaluated SERIALLY). This "
         "row read ':791-793 returns SRMECH_ERR_NOT_IMPL by design "
         "(host-thread fan-out)' / 'deliberate deferral' until then — the "
         "justification was retracted, not the measurement",
         {"parallel_body": "chiral_flip", "n_sectors": 4,
          "combine": "bundle"}, L_ANY, [1, 2], "runs in C (rc455)"),
        ("map_op", "discriminator",
         "_toml_chain.py:230/:314-323 (+ _chain.py:413 map_indexed)",
         "srmech_dsl_chain_run.c:639 disc table -> :755-781 "
         "dsl_run_map_indexed -> :738-745 (seq_get body ONLY)",
         {"map_op": "srmech.cascade.leaves.seq_get"}, L_ANY, [1, 2],
         "rc420 SIXTH form"),
        ("fold_args", "parameter", "_toml_chain.py:302-311 -> _chain.py:284 "
         "arg_names",
         "srmech_dsl_chain_run.c:682-706 dsl_run_fold NEVER reads fold_args "
         "(no closed-key-set check)",
         {"fold_init": 0, "fold_op": "cyclic_gcd", "fold_args": ["a", "b"]},
         L_INT, [12, 18], "SILENTLY IGNORED by C — see the divergence block"),
        ("n_sectors", "parameter", "_toml_chain.py:343-347",
         "srmech_dsl_chain_run.c: never read (the parallel form defers first)",
         {"parallel_body": "chiral_flip", "n_sectors": 2}, L_ANY, [1, 2], ""),
        ("combine", "parameter", "_toml_chain.py:352-359",
         "srmech_dsl_chain_run.c: never read (the parallel form defers first)",
         {"parallel_body": "chiral_flip", "combine": "mean"}, L_ANY, [1, 2],
         ""),
        ("sub_chain (alone)", "parameter", "_toml_chain.py:259-262 "
         "(loop requires BOTH)",
         "srmech_dsl_chain_run.c:637 disc table hit -> :666 NOT_IMPL "
         "(sub_chain without loop_n)",
         {"sub_chain": [{"op": "magnitude"}]}, F35, -3.5, ""),
        ("op kwarg: orientation", "parameter", "_toml_chain.py:246 forwarded",
         "srmech_dsl_chain_run.c:308 leaf_reorient reads it",
         {"op": "reorient", "orientation": -1}, {"k": "i", "v": 5}, 5, ""),
        ("op kwarg: max_denominator", "parameter",
         "_toml_chain.py:246 forwarded",
         "srmech_dsl_chain_run.c:366 leaf_best_rational reads it",
         {"op": "best_rational_signed", "max_denominator": 10},
         {"k": "f", "v": 0.5}, 0.5, ""),
        ("op kwarg: fine_scale", "parameter", "_toml_chain.py:246 forwarded",
         "srmech_dsl_chain_run.c:367 leaf_best_rational reads it",
         {"op": "best_rational_signed", "fine_scale": 1000},
         {"k": "f", "v": 0.5}, 0.5, ""),
        ("op kwarg: any OTHER name", "parameter",
         "_toml_chain.py:246 forwarded to the op (TypeError if unknown)",
         "srmech_dsl_chain_run.c:537-565: no leaf validates its key set; "
         "unknown keys are IGNORED",
         {"op": "magnitude", "bogus": 1}, F35, -3.5,
         "LIVE C-accepts/Python-rejects divergence"),
    ]

    # The mechanical rule (rc==0 -> executes, else check the discriminator
    # table) is WRONG for four rows, so each is stated explicitly rather than
    # inferred.  A key C never reads is "unrecognised" EVEN IF the enclosing
    # step returns SRMECH_OK — that is precisely the silent-ignore hazard.
    B_STATUS_OVERRIDE = {
        "fold_args": "unrecognised",
        "n_sectors": "unrecognised",
        "combine": "unrecognised",
        "sub_chain (alone)": "parses_rejects",
        "parallel_body": "parses_rejects",
        "op kwarg: any OTHER name": "unrecognised",
    }

    b_tally = {"discriminator": {}, "parameter": {}}
    print("    %-34s %-13s %-9s %-11s %-30s %s" %
          ("form", "kind", "py-build", "C-run", "C value", "verdict"))
    for (form, kind, psrc, csrc, stage, in_desc, py_in, note) in b_probes:
        py_ok, py_detail = b_python_builds(stage, py_in, do_run=True)
        rc, val = c_dsl_chain_run([stage], in_desc)
        status = B_STATUS_OVERRIDE.get(
            form, "executes" if rc == 0 else "unrecognised")
        print("    %-34s %-13s %-9s %-11s %-30s %s" %
              (form[:34], kind[:13], "yes" if py_ok else "NO", sname(rc),
               str(val)[:30], status))
        b_tally[kind][status] = b_tally[kind].get(status, 0) + 1
        emit(record="form", surface="B_dsl_stage", form=form, kind=kind,
             python_accepts=py_ok, python_src=psrc, python_detail=py_detail,
             c_status=status, c_src=csrc, c_run_rc=sname(rc), c_run_value=val,
             note=note,
             evidence="srmech_dsl_chain_run([%s]) -> %s value=%s"
                      % (json.dumps(stage, sort_keys=True), sname(rc), val))
    print("    SURFACE-B TALLY  discriminators: %s" % b_tally["discriminator"])
    print("                     parameters:     %s" % b_tally["parameter"])
    emit(record="surface_tally", surface="B_dsl_stage",
         discriminators=b_tally["discriminator"],
         parameters=b_tally["parameter"],
         headline="C implements 5 of 6 step forms (op / loop / fold / reduce / "
                  "map_op execute; parallel_body parses-and-rejects by "
                  "design). NONE unrecognised.")

    # negative-shape controls for surface B (Python rejects; C must too)
    print("\n    negative-shape controls (Python REJECTS; C should not accept)")
    for label, stage, in_desc in [
        ("no discriminator", {"foo": 1}, F35),
        ("loop_n without sub_chain", {"loop_n": 3}, F35),
        ("MIXED op + fold_op", {"op": "magnitude", "fold_op": "cyclic_gcd",
                                "fold_init": 0}, F35),
    ]:
        py_ok, py_detail = b_python_builds(stage)
        rc, val = c_dsl_chain_run([stage], in_desc)
        agree = (not py_ok) and rc != 0
        print("      %-28s py=%-3s C=%-14s agree=%s" %
              (label, "yes" if py_ok else "NO", sname(rc), agree))
        emit(record="negative_control", surface="B_dsl_stage", label=label,
             stage=stage, python_accepts=py_ok, python_detail=py_detail,
             c_rc=sname(rc), c_value=val, agree=agree)

    # ── the measured PARITY DIVERGENCES ─────────────────────────────────────
    print("\n[3] MEASURED C-ACCEPTS / PYTHON-REJECTS DIVERGENCES")

    # D1 — unknown op kwarg on a C-backed DSL leaf, via the SHIPPED builder.
    print("    D1 unknown op kwarg on a C-backed leaf, SHIPPED Python builder:")
    d1 = []
    for op, val, kw in [("magnitude", -3.5, {"bogus": 1}),
                        ("magnitude", -3.5, {"max_denominator": 10}),
                        ("reorient", 5, {"orientation": -1, "bogus": 1}),
                        ("pin_slot_at_zero", -3.5, {"bogus": 1}),
                        ("chiral_flip", [1, 2, 3], {"bogus": 1}),
                        ("net_chirality", [1, -1, 1], {"bogus": 1}),
                        ("autocorrelation", [1.0, 2.0], {"bogus": 1}),
                        ("best_rational_signed", 0.5, {"bogus": 1})]:
        ch = dsl_chain("probe").then(op, **kw)
        nat = ch._run_native(val)
        native_ran = nat is not _NATIVE_MISS
        try:
            pure = repr(getattr(srmech.cascade, op)(val, **kw))
            pure_ok = True
        except Exception as exc:                    # noqa: BLE001
            pure = type(exc).__name__
            pure_ok = False
        diverges = native_ran and not pure_ok
        d1.append({"op": op, "kwargs": kw, "native_ran": native_ran,
                   "native_value": None if not native_ran else nat,
                   "pure": pure, "diverges": diverges})
        print("      %-22s %-34s native=%-14s pure=%s  DIVERGES=%s" %
              (op, json.dumps(kw, sort_keys=True),
               "MISS" if not native_ran else repr(nat), pure, diverges))
    emit(record="divergence", id="D1",
         title="unknown op kwarg on a C-backed DSL leaf is SILENTLY IGNORED",
         reachable_via="the shipped Python builder "
                       "(chain().then(op, **kw).run(v)) with HAS_NATIVE=True",
         python_src="_chain.py:112-123 _then_native_desc copies EVERY scalar "
                    "kwarg into the C stage IR; _chain.py:555-556 forwards "
                    "them to the op on the pure path",
         c_src="srmech_dsl_chain_run.c:537-565 dsl_leaf_dispatch — no leaf "
               "validates its key set",
         n_probed=len(d1), n_diverging=sum(1 for r in d1 if r["diverges"]),
         cases=d1)

    # D2 — fold_args silently dropped on the bare-C host TOML->IR->run path.
    print("    D2 fold_args on the bare-C host path (TOML -> IR -> run):")
    toml_src = (b'[chain]\nname = "t"\n[[stage]]\nfold_init = 0\n'
                b'fold_op = "cyclic_gcd"\nfold_args = ["x", "y"]\n')
    rc_t, ir = c_dsl_toml_to_json(toml_src)
    d2 = {"toml_to_json_rc": sname(rc_t), "ir": ir}
    if rc_t == 0:
        lib = _native.LIB
        cj = ir.encode("utf-8")
        ij = json.dumps(L_INT).encode("utf-8")
        nb = int(lib.srmech_dsl_chain_run_arena_bytes(len(cj), len(ij)))
        ws = (ctypes.c_char * nb)()
        cap = max(nb // 2, 16384)
        out = (ctypes.c_char * cap)()
        ol = ctypes.c_size_t()
        rc_r = lib.srmech_dsl_chain_run(cj, len(cj), ij, len(ij), ws, nb, out,
                                        cap, ctypes.byref(ol))
        d2["run_rc"] = sname(rc_r)
        d2["run_value"] = (out.raw[:ol.value].decode("utf-8")
                           if rc_r == 0 else None)
    py_ok, py_detail = b_python_builds(
        {"fold_init": 0, "fold_op": "cyclic_gcd", "fold_args": ["x", "y"]},
        [12, 18], do_run=True)
    d2["python_accepts"] = py_ok
    d2["python_detail"] = py_detail
    d2["diverges"] = (d2.get("run_rc") == "SRMECH_OK=0") and not py_ok
    print("      TOML->IR %s ; C run %s value=%s ; Python %s" %
          (d2["toml_to_json_rc"], d2.get("run_rc"), d2.get("run_value"),
           py_detail))
    print("      DIVERGES=%s" % d2["diverges"])
    emit(record="divergence", id="D2",
         title="fold_args is silently dropped by the C DSL fold",
         reachable_via="a bare-C host: srmech_dsl_toml_chain_to_json -> "
                       "srmech_dsl_chain_run (NOT via the Python builder, "
                       "which gates arg_names is None at _chain.py:313)",
         python_src="_toml_chain.py:302-311 ; _chain.py:311-315",
         c_src="srmech_dsl_chain_run.c:682-706 dsl_run_fold",
         detail=d2)

    # D3 — bare map_op body name accepted by C, rejected by Python.
    print("    D3 bare map_op body name:")
    rc_b, val_b = c_dsl_chain_run([{"map_op": "seq_get"}], L_ANY)
    py_b, py_bd = b_python_builds({"map_op": "seq_get"})
    print("      C=%s value=%s ; Python=%s (%s)  DIVERGES=%s" %
          (sname(rc_b), val_b, py_b, py_bd[:60], rc_b == 0 and not py_b))
    emit(record="divergence", id="D3",
         title="bare map_op body name 'seq_get' runs in C but is not a "
               "catalog name in Python",
         reachable_via="a bare-C host TOML chain spec",
         python_src="_catalog.py:411-416 lookup_cascade_op (bare names must "
                    "be catalog names)",
         c_src="srmech_dsl_chain_run.c:738-745 dsl_map_body_is_seq_get "
               "matches the BARE spelling too",
         c_rc=sname(rc_b), c_value=val_b, python_accepts=py_b,
         python_detail=py_bd, diverges=(rc_b == 0 and not py_b))

    # D4 — MIXED v1+v2 step on surface A: C accepts and DROPS the map.
    print("    D4 MIXED plain+map step on surface A:")
    mixed = [dict(A_PLAIN, map_over="@input.seq", body=[dict(A_PLAIN)])]
    rc_mp, _ = c_chain_spec_parse(a_chain(mixed))
    rc_mr, val_mr = c_chain_run(a_chain(mixed), A_CTX)
    py_m, py_md = a_python_parses(mixed)
    guarded = CO._chain_has_v2_forms(a_chain(mixed))
    print("      C parse=%s run=%s value=%s ; Python=%s ; "
          "_chain_has_v2_forms guard=%s" %
          (sname(rc_mp), sname(rc_mr), val_mr, py_m, guarded))
    emit(record="divergence", id="D4",
         title="a step carrying BOTH the plain skeleton and map keys parses "
               "AND RUNS in C with the map form silently discarded",
         reachable_via="a bare-C host (the Python arm is guarded by "
                       "compose._chain_has_v2_forms, measured True here)",
         python_src="compose.py:611-623 _parse_step mutual-exclusion; "
                    "compose.py:419-474 _chain_has_v2_forms guard",
         c_src="srmech_compose.c:287-319 co_build_step is a REQUIRED-KEYS "
               "check, not a closed-key-set check",
         c_parse_rc=sname(rc_mp), c_run_rc=sname(rc_mr), c_run_value=val_mr,
         python_accepts=py_m, python_detail=py_md,
         python_first_guard_active=guarded,
         diverges=(rc_mr == 0 and not py_m))

    # ── the shipped-descriptor census (what the gap COSTS today) ────────────
    print("\n[4] SHIPPED cascade_catalog CENSUS — what the gap costs at rc444")
    cat = DCAT.load_catalog()
    MAPK, FOLDK = CO._MAP_KEYS, CO._FOLD_KEYS

    def step_forms(steps, acc=None):
        acc = acc if acc is not None else {"plain": 0, "map": 0, "fold": 0}
        for st in steps:
            if not isinstance(st, dict):
                continue
            if any(k in st for k in MAPK):
                acc["map"] += 1
                step_forms(st.get("body", []), acc)
            elif any(k in st for k in FOLDK):
                acc["fold"] += 1
            else:
                acc["plain"] += 1
        return acc

    def collect_ops(steps, out):
        for st in steps:
            if not isinstance(st, dict):
                continue
            if any(k in st for k in MAPK):
                collect_ops(st.get("body", []), out)
            elif any(k in st for k in FOLDK):
                out.add(str(st.get("fold_op")))
            else:
                out.add(str(st.get("op")))
        return out

    def fatal_features(steps, path=""):
        """Every C-fatal feature of a step list, with the C source line."""
        hits = []
        for i, st in enumerate(steps):
            p = f"{path}steps[{i}]"
            if any(k in st for k in MAPK):
                hits.append([p, "map step form",
                             "srmech_compose.c:299-303"])
                hits += fatal_features(st.get("body", []), p + ".body.")
                continue
            if any(k in st for k in FOLDK):
                hits.append([p, "fold step form",
                             "srmech_compose.c:299-303"])
                continue
            cls = str(st.get("class", ""))
            if not (len(cls) == 1 and "A" <= cls <= "N"):
                hits.append([p, f"class={cls!r}",
                             "srmech_compose.c:105-110"])
            refs = []
            _walk_refs(st.get("args", {}), refs)
            for ns in refs:
                if ns in ("idx", "bind", "op", "MALFORMED"):
                    hits.append([p, f"@{ns} reference namespace",
                                 "srmech_compose.c:135-149"])
        return hits

    chains = []
    for name in sorted(cat):
        try:
            specs = DCC.cascade_chain_specs(name)
        except ValueError:
            continue
        for (variant, spec, entry) in specs:
            cd = {"name": f"{name}.{variant}",
                  "summary": str(entry.get("summary", "")),
                  "returns": str(entry.get("returns", "")),
                  "steps": entry.get("steps", [])}
            rc_p, _ = c_chain_spec_parse(cd)
            ops = collect_ops(cd["steps"], set())
            forms = step_forms(cd["steps"])
            # per-step isolation: index-preserving filler reduction
            per_step = []
            for i, st in enumerate(cd["steps"]):
                probe = [dict(A_FILLER)] * i + [st]
                rc_i, _ = c_chain_spec_parse({**A_HEAD, "steps": probe})
                per_step.append({"i": i, "rc": sname(rc_i)})
            chains.append({
                "chain": cd["name"], "n_steps": len(cd["steps"]),
                "forms": forms, "n_ops": len(ops),
                "ops_in_c_run_table": sorted(ops & CO._RUN_C_OPS),
                "n_dotted_ops": sum(1 for o in ops if "." in o),
                "c_parse_rc": sname(rc_p),
                "c_run_eligible": CO._chain_c_eligible(spec),
                "has_v2_forms": CO._chain_has_v2_forms(cd),
                "fatal_features": fatal_features(cd["steps"]),
                "per_step_c_parse": per_step,
            })

    n_chains = len(chains)
    n_acc = sum(1 for c in chains if c["c_parse_rc"] == "SRMECH_OK=0")
    n_run = sum(1 for c in chains if c["c_run_eligible"])
    desc_reject = sorted({c["chain"].rsplit(".", 1)[0] for c in chains
                          if c["c_parse_rc"] != "SRMECH_OK=0"})
    desc_all = sorted({c["chain"].rsplit(".", 1)[0] for c in chains})
    desc_accept = [d for d in desc_all if d not in desc_reject]
    tot_steps = sum(c["n_steps"] for c in chains)
    tot_forms = {"plain": 0, "map": 0, "fold": 0}
    for c in chains:
        for k in tot_forms:
            tot_forms[k] += c["forms"][k]
    print("    descriptors=%d (executable=%d leaf=%d) declared chains=%d"
          % (len(cat), len(desc_all), len(cat) - len(desc_all), n_chains))
    print("    steps (incl. nested map bodies): plain=%d map=%d fold=%d "
          "(total %d)" % (tot_forms["plain"], tot_forms["map"],
                          tot_forms["fold"],
                          sum(tot_forms.values())))
    print("    C PARSE  (srmech_chain_spec_parse): accept %d/%d chains, "
          "%d/%d descriptors" % (n_acc, n_chains, len(desc_accept),
                                 len(desc_all)))
    print("    C RUN    (srmech_chain_run):        eligible %d/%d chains"
          % (n_run, n_chains))
    print("    descriptors REJECTED by the C parse peer (%d): %s"
          % (len(desc_reject), ", ".join(desc_reject)))
    for c in chains:
        if c["c_parse_rc"] != "SRMECH_OK=0":
            firsts = c["fatal_features"][:3]
            print("      %-34s %s  first-fatal: %s" %
                  (c["chain"], c["c_parse_rc"],
                   "; ".join(f"{f[0]} {f[1]}" for f in firsts)))
    emit(record="catalog_census", descriptors=len(cat),
         executable_descriptors=len(desc_all),
         leaf_descriptors=len(cat) - len(desc_all),
         declared_chains=n_chains, top_level_steps=tot_steps,
         step_forms_incl_nested=tot_forms,
         total_steps_incl_nested=sum(tot_forms.values()),
         c_parse_accept_chains=n_acc, c_parse_reject_chains=n_chains - n_acc,
         c_parse_accept_descriptors=len(desc_accept),
         c_parse_reject_descriptors=len(desc_reject),
         c_run_eligible_chains=n_run,
         descriptors_accepted=desc_accept, descriptors_rejected=desc_reject,
         per_chain=chains)

    # ── the DSL kernel-table census ────────────────────────────────────────
    print("\n[5] SURFACE B kernel-table coverage over the 21 catalog names")
    C_UNARY = ["magnitude", "reorient", "pin_slot_at_zero",
               "best_rational_signed", "chiral_flip", "net_chirality",
               "autocorrelation"]
    C_BINARY = ["cyclic_gcd"]
    C_MAPBODY = ["seq_get"]
    names = sorted(cat)
    unary_hit = [n for n in names if n in C_UNARY]
    binary_hit = [n for n in names if n in C_BINARY]
    covered = sorted(set(unary_hit) | set(binary_hit))
    uncovered = [n for n in names if n not in covered]
    exec_names = desc_all
    exec_covered = [n for n in exec_names if n in covered]
    print("    C unary leaf table (srmech_dsl_chain_run.c:537-565): %d names"
          % len(C_UNARY))
    print("    C binary body table (:603-620): %s" % C_BINARY)
    print("    C map body table (:738-745): %s (not a catalog name)"
          % C_MAPBODY)
    print("    catalog names with a C DSL kernel: %d/%d -> %s"
          % (len(covered), len(names), covered))
    print("    of the %d EXECUTABLE descriptors: %d covered, %d not"
          % (len(exec_names), len(exec_covered),
             len(exec_names) - len(exec_covered)))
    # prove each unary-table name actually EXECUTES
    live = {}
    for op, desc in [("magnitude", {"k": "f", "v": -3.5}),
                     ("reorient", {"k": "i", "v": 5}),
                     ("pin_slot_at_zero", {"k": "f", "v": -3.5}),
                     ("best_rational_signed", {"k": "f", "v": 0.5}),
                     ("chiral_flip", {"k": "l", "v": [{"k": "i", "v": 1},
                                                      {"k": "i", "v": 2}]}),
                     ("net_chirality", {"k": "l", "v": [{"k": "i", "v": 1},
                                                        {"k": "i", "v": -1}]}),
                     ("autocorrelation", {"k": "l", "v": [{"k": "f", "v": 1.0},
                                                          {"k": "f",
                                                           "v": 2.0}]})]:
        stage = {"op": op}
        if op == "reorient":
            stage["orientation"] = -1
        rc, val = c_dsl_chain_run([stage], desc)
        live[op] = {"rc": sname(rc), "value": val}
        print("      %-22s %-14s %s" % (op, sname(rc), val))
    emit(record="dsl_kernel_census", c_unary_table=C_UNARY,
         c_binary_table=C_BINARY, c_map_body_table=C_MAPBODY,
         catalog_names=len(names), covered=covered, uncovered=uncovered,
         executable_descriptors=len(exec_names),
         executable_covered=exec_covered,
         executable_uncovered=[n for n in exec_names if n not in covered],
         live_unary_runs=live)

    # ── the OTHER surface-A population: [[catalog.operator_chain]] ──────────
    # The C run loop's op table (_RUN_C_OPS) is Class-N-only, which is the
    # population it was BUILT for.  Measuring it here stops "0 of 20" from
    # being read as a broken runner: the runner is fully live, it is simply
    # aimed at a different descriptor population.
    print("\n[6] the OTHER surface-A population — [[catalog.operator_chain]]")
    import glob
    from srmech import _toml as _srm_toml
    amsc = []
    for p in sorted(glob.glob(str(_PY / "srmech" / "amsc" / "attested" / "*"
                                  / "descriptor.toml"))):
        try:
            d = _srm_toml.loads(open(p, encoding="utf-8").read())
        except Exception:                           # noqa: BLE001
            continue
        rows = (d.get("catalog") or {}).get("operator_chain") or []
        for c in rows:
            spec = CO.parse_chain_spec(c)
            el = CO._chain_c_eligible(spec)
            amsc.append({"descriptor": Path(p).parent.name,
                         "chain": c["name"], "n_steps": len(spec.steps),
                         "schema": d["catalog"].get("chain_schema_version"),
                         "c_run_eligible": el})
            print("      %-38s steps=%-2d c_run_eligible=%s"
                  % (c["name"], len(spec.steps), el))
    n_el = sum(1 for r in amsc if r["c_run_eligible"])
    print("    [[catalog.operator_chain]] rows: %d ; C-run eligible: %d"
          % (len(amsc), n_el))
    emit(record="amsc_operator_chain_census", rows=len(amsc),
         c_run_eligible=n_el, per_chain=amsc,
         note="the C run loop is FULLY live on the population it was built "
              "for (all Class-N pi / *_series_truncate / rational_* ops); the "
              "0-of-20 cascade_catalog figure is an OP-TABLE coverage fact, "
              "not a broken runner")

    # ── #T1142: map_op missing from _COMPOSITE_OP_KEYS ─────────────────────
    print("\n[7] #T1142 cross-check — _COMPOSITE_OP_KEYS at rc444")
    keys = DCAT._COMPOSITE_OP_KEYS
    disc_py = ("op", "loop_n/sub_chain", "fold_init/fold_op", "reduce_op",
               "parallel_body", "map_op")
    print("    _catalog.py:151 _COMPOSITE_OP_KEYS = %r" % (keys,))
    print("    map_op present: %s   (the Python dispatcher has %d "
          "discriminators)" % ("map_op" in keys, len(disc_py)))
    emit(record="t1142_crosscheck",
         composite_op_keys=list(keys),
         map_op_in_composite_op_keys=("map_op" in keys),
         python_discriminators=list(disc_py),
         python_src="dsl/_catalog.py:151 (validation) vs "
                    "dsl/_toml_chain.py:225-244 (dispatch)",
         c_src="srmech_dsl_chain_run.c:637-639 dsl_stage_is_combinator "
               "(7 keys, INCLUDING map_op)",
         note="C's discriminator table is COMPLETE (7 keys incl. map_op); "
              "the Python COMPOSITE VALIDATOR is the one missing map_op, so "
              "a [composite] stage referencing an unknown map_op body is "
              "NOT caught at load. This gap is Python-side, not C-side.")

    # ── environment record + write ─────────────────────────────────────────
    emit(record="environment", srmech_version=srmech.__version__,
         has_native=_native.HAS_NATIVE,
         native_abi=_native.NATIVE_ABI_VERSION,
         expected_abi=getattr(_native, "EXPECTED_ABI_VERSION", None),
         engine_schema_version=CO.ENGINE_SCHEMA_VERSION,
         supported_schema_versions=list(CO.SUPPORTED_SCHEMA_VERSIONS),
         c_run_op_table=sorted(CO._RUN_C_OPS),
         cwd=os.getcwd(), script=str(Path(__file__).resolve()))

    with open(OUT, "w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n")
    print("\nwrote %d NDJSON records -> %s" % (len(records), OUT))
    return 0


def _walk_refs(a, out):
    """Collect the namespace of every ``@`` reference in an args tree."""
    if isinstance(a, str) and a.startswith("@"):
        m = CO._REFERENCE_PATTERN.match(a)
        out.append(m.group(1) if m else "MALFORMED")
    elif isinstance(a, dict):
        for v in a.values():
            _walk_refs(v, out)
    elif isinstance(a, (list, tuple)):
        for v in a:
            _walk_refs(v, out)


if __name__ == "__main__":
    sys.exit(main())
