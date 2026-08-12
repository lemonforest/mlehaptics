#!/usr/bin/env python3
"""P1 — the NOTATION-CARRIER census (rc426 research spike, read-only).

Pre-registered question
=======================
Does srmech ship ANY carrier or op that names a NOTATION object (staff /
clef / score / sheet / tablature / neume / stave / notation)?  rc424 measured
"0 of 605 ops naming a relational music-theory object" before adding 6.  This
script asks the same question of the NOTATION layer, one rung up from the
relations layer, and reports the number rather than asserting it.

Three separate censuses, because they are three separate claims:

  C1  carriers   — every entry of ``introspect.carrier_schema()``
  C2  ops        — every entry of ``introspect.tool_schema.get_tool_schema()``
  C3  EDO leak   — which shipped music ops hard-wire a modulus, i.e. which are
                   CHART-scoped (convention-bearing) rather than CARRIER-scoped
                   (frame-free).  A hard-wired 12 is a WESTERN CHART constant.

Homograph discipline
====================
rc424's own changelog records a homograph (MUSIC = MUltiple SIgnal
Classification) that hid an op from search for its whole life.  So this census
separates SURFACE HITS from CONFIRMED HITS: a token match is a candidate, and
every candidate is emitted with its context so the classification is auditable
rather than asserted.  Known landmines, pre-registered:

  "note"     — Python prose ("note that ...", ``Note:`` docstring section)
  "scale"    — scaling / rescale / scale factor, everywhere in numerics
  "interval" — confidence interval, interval arithmetic
  "octave"   — vs "octonion"  (prefix collision under sloppy matching)
  "key"      — dict key, sort key, cache key
  "measure"  — measure theory / measurement
  "bar"      — bar chart, error bar
  "rest"     — the rest of, REST API
  "staff"    — no known collision
  "clef"     — no known collision

Outputs one NDJSON record per finding to
``_p1_notation_carrier_census_rc426.ndjson``.

Run:
    PYTHONPATH=docs/srmech/python python3 docs/srmech/notes/_p1_notation_carrier_census_rc426.py
"""
from __future__ import annotations

import json
import os
import re
import sys

import srmech
from srmech.introspect.carrier_schema import carrier_schema
from srmech.introspect.tool_schema import get_tool_schema, warmup_all

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "_p1_notation_carrier_census_rc426.ndjson")

# ── the vocabulary, split by how trustworthy a bare token match is ──────────

#: Tokens with NO known homograph in a numerics codebase.  A hit here is a
#: real notation reference until shown otherwise.
CLEAN = (
    "clef", "staff", "stave", "notation", "sheet music", "tablature",
    "neume", "solfege", "solfège", "sargam", "maqam", "jianpu", "gongche",
    "shruti", "swara", "raga", "makam", "jins", "ajnas", "byzantine",
    "chiavette", "score sheet", "manuscript", "key signature",
    "time signature", "accidental", "ledger line", "barline",
)

#: Tokens that DO collide.  Every hit must be inspected; the record carries
#: the collision reason so nothing is silently counted.
DIRTY = {
    "note": "docstring 'Note:' section; prose 'note that'",
    "scale": "scaling / scale factor / rescale",
    "interval": "confidence interval; interval arithmetic",
    "octave": "prefix-collides with 'octonion' under sloppy matching",
    "key": "dict key / sort key / cache key",
    "measure": "measure theory; 'measurement'",
    "bar": "bar chart; error bar",
    "rest": "'the rest of'; REST API",
    "score": "score function; z-score",
    "pitch": "pitch (angle) in aerospace; pitch of a helix",
    "chord": "chord of a circle / graph chord",
    "mode": "mode of operation; statistical mode",
    "tone": "tone mapping",
    "voice": "voice/vocal",
    "temperament": "no known collision, but low frequency — verify",
}

#: The music-RELATIONAL vocabulary rc424 added.  Counted separately: these
#: are RELATIONS (how two pitches stand), NOT NOTATION (how a pitch is
#: written).  Conflating the two is the whole risk of this census.
RELATIONAL = (
    "just_limit", "comma_of_chain", "tempers_out", "interval_vector",
    "normal_order", "prime_form",
)


def _blob(entry) -> str:
    """Every prose surface of a ToolEntry, lowercased, as one string."""
    parts = [entry.name, entry.summary or "", entry.explanation or ""]
    for p in entry.parameters or ():
        parts.append(p.name)
        parts.append(p.summary or "")
    ex = entry.example or {}
    if isinstance(ex, dict):
        parts.append(str(ex.get("why", "")))
    return " ".join(parts).lower()


def _hits(text: str, tokens) -> list:
    out = []
    for t in tokens:
        # word-boundary match so 'octave' cannot be found inside 'octonion'
        # and 'note' cannot be found inside 'notebook' / 'denote'
        if re.search(r"(?<![a-z])" + re.escape(t) + r"(?![a-z])", text):
            out.append(t)
    return out


def main() -> int:
    print("srmech.__file__    =", srmech.__file__)
    print("srmech.__version__ =", srmech.__version__)
    try:
        import numpy  # noqa: F401
        print("!! numpy PRESENT — measurement environment is wrong")
    except ImportError:
        print("numpy              = ABSENT (correct)")
    print()

    recs = []

    def emit(**kw):
        kw.setdefault("srmech_version", srmech.__version__)
        recs.append(kw)

    # ── C1 — the carrier census ────────────────────────────────────────────
    cs = carrier_schema()
    print(f"C1  carriers: {len(cs)}")
    carrier_clean = {}
    carrier_dirty = {}
    for name, spec in sorted(cs.items()):
        blob = json.dumps(spec, default=str).lower()
        c = _hits(blob, CLEAN)
        d = _hits(blob, DIRTY)
        if c:
            carrier_clean[name] = c
        if d:
            carrier_dirty[name] = d
    print(f"    names/descriptions matching a CLEAN notation token : "
          f"{len(carrier_clean)}  {carrier_clean}")
    print(f"    matching a DIRTY (homograph-prone) token           : "
          f"{len(carrier_dirty)}")
    for n, d in sorted(carrier_dirty.items()):
        print(f"      {n:24s} {d}")
    emit(finding="C1_carrier_census",
         n_carriers=len(cs),
         carrier_names=sorted(cs),
         n_clean_notation_hits=len(carrier_clean),
         clean_hits=carrier_clean,
         n_dirty_hits=len(carrier_dirty),
         dirty_hits=carrier_dirty,
         verdict=("EMPTY — no carrier names a notation object"
                  if not carrier_clean else "NONEMPTY — inspect"))

    # ── C2 — the op census ────────────────────────────────────────────────
    warmup_all()
    tools = get_tool_schema().tools
    print(f"\nC2  ops: {len(tools)}")
    op_clean, op_dirty, name_hits = {}, {}, {}
    for e in tools:
        blob = _blob(e)
        c = _hits(blob, CLEAN)
        d = _hits(blob, DIRTY)
        nc = _hits(e.name.lower().replace("_", " ").replace(".", " "),
                   CLEAN + tuple(DIRTY))
        if c:
            op_clean[e.name] = c
        if d:
            op_dirty[e.name] = d
        if nc:
            name_hits[e.name] = nc
    print(f"    ops whose PROSE matches a CLEAN notation token : {len(op_clean)}")
    for n, h in sorted(op_clean.items()):
        print(f"      {n:58s} {h}")
    print(f"    ops whose NAME matches any music token         : {len(name_hits)}")
    for n, h in sorted(name_hits.items()):
        print(f"      {n:58s} {h}")
    print(f"    ops whose PROSE matches a DIRTY token          : {len(op_dirty)}"
          "   (homograph-prone; not counted as notation)")
    emit(finding="C2_op_census",
         n_ops=len(tools),
         n_ops_prose_clean_notation=len(op_clean),
         ops_prose_clean_notation=op_clean,
         n_ops_name_any_music_token=len(name_hits),
         ops_name_any_music_token=name_hits,
         n_ops_prose_dirty=len(op_dirty),
         verdict=("EMPTY — no op names a notation object"
                  if not op_clean else "NONEMPTY — inspect"))

    # ── C2b — the music namespace, enumerated ─────────────────────────────
    music_ops = sorted(e.name for e in tools if ".music." in e.name)
    rel_ops = [n for n in music_ops
               if n.rsplit(".", 1)[-1] in RELATIONAL]
    print(f"\nC2b srmech.music.* registered ops: {len(music_ops)}")
    for n in music_ops:
        tag = "RELATIONAL" if n in rel_ops else "acoustic"
        print(f"      [{tag:10s}] {n}")
    emit(finding="C2b_music_namespace",
         n_music_ops=len(music_ops),
         music_ops=music_ops,
         n_relational=len(rel_ops),
         relational_ops=rel_ops,
         n_notation_ops=0 if not op_clean else len(op_clean))

    # ── C3 — the EDO / modulus leak census ────────────────────────────────
    # Which shipped music ops are parametric in their modulus (CARRIER-shaped,
    # frame-free) and which hard-wire one (CHART-shaped, convention-bearing)?
    import inspect

    from srmech.music import relations as rel

    print("\nC3  modulus parametricity of the rc424 relational lane")
    print(f"    module constant _EDO12 = {rel._EDO12}")
    # ⚠️ The FIRST version of this classifier read each function's OWN source
    # only, and reported ``normal_order`` as "CARRIER (no modulus at all)".
    # That was WRONG: normal_order's body never types ``_EDO12``, but it calls
    # ``_as_pcs`` and ``_spans``, and BOTH hard-wire it.  The correction is
    # kept visible rather than silently patched, because the shape of the
    # error is the finding: a modulus assumption reaches a public op through
    # a PRIVATE HELPER, so a non-transitive audit under-reports it.
    helpers = {}
    for h in ("_as_pcs", "_interval_class", "_invert", "_spans"):
        helpers[h] = "_EDO12" in inspect.getsource(getattr(rel, h))
    tainted = {h for h, v in helpers.items() if v}

    rows = []
    for fn_name in RELATIONAL:
        fn = getattr(rel, fn_name)
        sig = inspect.signature(fn)
        params = list(sig.parameters)
        src = inspect.getsource(fn)
        direct = "_EDO12" in src
        # transitive closure, one hop, over the tainted private helpers, plus
        # a second hop for prime_form -> normal_order
        via = sorted(h for h in tainted if h in src)
        if fn_name == "prime_form" and "normal_order" in src:
            via = sorted(set(via) | {"normal_order(->" + ",".join(
                sorted(h for h in tainted
                       if h in inspect.getsource(rel.normal_order))) + ")"})
        reaches_edo12 = direct or bool(via)
        param_modulus = [p for p in params
                         if p.lower() in ("edo", "modulus", "mod", "period")]
        if reaches_edo12:
            lane = "CHART (ℤ/12 hard-wired)"
        elif param_modulus:
            lane = "CARRIER-parametric (caller supplies the modulus)"
        else:
            lane = "CARRIER (no modulus at all — ℚ⁺ lane)"
        rows.append({"op": fn_name, "params": params,
                     "body_uses_hardwired_EDO12": direct,
                     "reaches_EDO12_via_helpers": via,
                     "reaches_EDO12": reaches_edo12,
                     "caller_movable_modulus": param_modulus,
                     "lane": lane})
        print(f"      {fn_name:18s} params={params!s:34s} "
              f"direct={'Y' if direct else 'n'} via={via!s:34s} {lane}")
    print(f"      private helpers hard-wiring _EDO12: {helpers}")
    n_chart = sum(1 for r in rows if r["lane"].startswith("CHART"))
    emit(finding="C3_modulus_leak_census",
         edo12_constant=rel._EDO12,
         rows=rows,
         private_helpers_hardwiring_edo12=helpers,
         n_chart_scoped=n_chart,
         n_carrier_scoped=len(rows) - n_chart,
         verdict=(f"{n_chart}/{len(rows)} shipped relational ops are "
                  "CHART-scoped (ℤ/12 hard-wired); the remainder are the "
                  "frame-free ℚ⁺ / parametric-EDO lane"))

    # ── C4 — is the ℤ/12 a DECLARED chart or an UNMARKED assumption? ──────
    # A hard-wired 12 is only a defect if the op does not SAY it is a chart.
    doc = rel.__doc__ or ""
    declares = {
        "names the modular lane explicitly": "ℤ/12" in doc or "Z/12" in doc,
        "names the frequency lane explicitly": "ℚ⁺" in doc or "Q+" in doc,
        "says the two lanes DISAGREE": "DO NOT AGREE" in doc.upper(),
        "names a non-12 EDO anywhere in the module":
            bool(re.search(r"\bedo\b", inspect.getsource(rel), re.I)),
    }
    print("\nC4  does the module DECLARE its chart?")
    for k, v in declares.items():
        print(f"      {'YES' if v else 'NO ':4s} {k}")
    emit(finding="C4_chart_declared",
         declarations=declares,
         verdict=("DECLARED — the 12 is a named lane, not a silent assumption"
                  if all(declares.values()) else "PARTIAL — inspect"))

    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        for r in recs:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"\nwrote {len(recs)} records -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
