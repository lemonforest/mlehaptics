#!/usr/bin/env python3
"""ADVERSARIAL step 2 — dump the EXACT chain JSON + ctx JSON the census fed to
``srmech_chain_run``, so a BARE-C driver (no ctypes, no Python) can re-derive the
rejections independently.

Writes plain files under ``_1653_adv_barec/``.  Read-only w.r.t. srmech.
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PY_ROOT = os.path.abspath(os.path.join(HERE, "..", "python"))
if PY_ROOT not in sys.path:
    sys.path.insert(0, PY_ROOT)

from srmech.dsl import _cascade_chain as _cc      # noqa: E402
from srmech.dsl import _catalog as _cat           # noqa: E402

OUT = os.path.join(HERE, "_1653_adv_barec")

# (descriptor, variant) picked to exercise BOTH distinct C reject paths:
#   cyclic_gcd    — all-plain steps, C PARSE ACCEPTS, run dies in cr_dispatch
#                   -> expect run rc=5 SRMECH_ERR_NOT_IMPL   (:616)
#   net_chirality — step 0 is a FOLD, so it has no "op" string at all
#                   -> expect run rc=2 SRMECH_ERR_BAD_INPUT   (:723)
#                   and parse rc=2 (co_build_step)
#   octonion_dft  — map + fold + @idx/@bind refs, the deepest chain
#                   -> run rc=5 (step 0 is plain + out of table), parse rc=2
PICKS = (("cyclic_gcd", "default"),
         ("net_chirality", "default"),
         ("octonion_dft", "default"))


def main():
    os.makedirs(OUT, exist_ok=True)
    catalog = _cat.load_catalog()
    manifest = []
    for name, want_variant in PICKS:
        desc = catalog[name]
        entries = _cc._chain_entries(desc)
        for entry in entries:
            v = str(entry.get("variant", "default"))
            if v != want_variant:
                continue
            chain = {
                "name": "%s.%s" % (name, v),
                "summary": str(entry.get("summary", "")),
                "returns": str(entry.get("returns", "")),
                "on_error": "raise",
                "steps": entry.get("steps", []),
            }
            cases = entry.get("proof_cases", []) or []
            inputs = dict((cases[0].get("inputs") or {})) if cases else {}
            ctx = {"row": None, "inputs": inputs}
            probe = {"row": None, "inputs": {}}
            base = "%s__%s" % (name, v)
            for suffix, obj in (("chain", chain), ("ctx", ctx),
                                ("probe", probe)):
                path = os.path.join(OUT, "%s.%s.json" % (base, suffix))
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(json.dumps(obj, ensure_ascii=False))
            step0 = (chain["steps"] or [{}])[0]
            manifest.append({
                "descriptor": name, "variant": v, "base": base,
                "n_steps_top": len(chain["steps"]),
                "step0_keys": sorted(step0.keys()),
                "step0_has_op": "op" in step0,
                "step0_op": step0.get("op"),
                "step0_class": step0.get("class"),
            })
    with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as fh:
        fh.write(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    for m in manifest:
        print("%-28s step0_has_op=%-5s step0_op=%-22s keys=%s"
              % (m["base"], m["step0_has_op"], m["step0_op"], m["step0_keys"]))
    print("wrote %d chains to %s" % (len(manifest), OUT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
