#!/usr/bin/env python3
"""ADVERSARIAL cross-check helper for #1653 — INDEPENDENT chain-JSON extraction.

Deliberately does NOT import srmech.  Reads the 21 packaged cascade_catalog
TOML descriptors with stdlib ``tomllib`` only and writes one JSON file per
declared ``[[cascade.chain]]`` block, in the shape
``srmech_chain_spec_parse`` documents (``{name, summary, returns, steps}``).

Purpose: the bare-C driver (``_1653_adv_bare_c_verify.c``) then calls the
static ``libsrmech.a`` with these files, so the C verdicts are reproduced with
NEITHER the census script's ctypes harness NOR srmech's own descriptor loader
in the path.  Also writes four hand-built ABLATION cases that isolate CAUSE:

  ablate_netchir_foldstep_to_plain.json — net_chirality with its ONE fold step
      swapped for a plain step; everything else identical.
  inject_cyclicgcd_extra_fold.json      — cyclic_gcd (accepted) plus one fold
      step appended.
  inject_cyclicgcd_extra_map.json       — cyclic_gcd plus one map step.
  headless_plain.json                   — a plain chain with `name` DELETED,
      to prove the head check and the step check return the same status and so
      cannot be told apart by status alone.

No abs(), no numpy, no RNG, no stdlib fractions.  Pure enumeration + JSON.

Run:
    python3 docs/srmech/notes/_1653_adv_extract_chains.py
"""

from __future__ import annotations

import json
import sys
import tomllib
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_CAT = (_HERE.parent / "python" / "srmech" / "cascade" / "catalogs"
        / "cascade_catalog")
_OUT = _HERE / "_1653_adv_chain_json"

PLAIN = {"class": "N", "op": "rational_add", "args": {}}
FOLD = {"fold_class": "C", "fold_op": "reorient", "fold_init": 1,
        "over": "@input.xs"}
MAP = {"map_over": "@input.xs", "index": "i",
       "body": [{"class": "N", "op": "rational_add", "args": {}}]}


def chain_blocks(doc):
    """The declared [[cascade.chain]] blocks of one descriptor document."""
    casc = doc.get("cascade")
    if not isinstance(casc, dict):
        return []
    blocks = casc.get("chain")
    if blocks is None:
        return []
    if isinstance(blocks, dict):
        blocks = [blocks]
    return [b for b in blocks if isinstance(b, dict)]


def spec_of(name, idx, block):
    """The {name, summary, returns, steps} object the C peer documents."""
    return {"name": "%s.%d" % (name, idx),
            "summary": str(block.get("summary", "")),
            "returns": str(block.get("returns", "")),
            "steps": block.get("steps", [])}


def main() -> int:
    _OUT.mkdir(exist_ok=True)
    tomls = sorted(_CAT.glob("*.toml"))
    print("descriptor TOMLs found: %d" % len(tomls))
    manifest = []
    n_chain = 0
    for path in tomls:
        with path.open("rb") as fh:
            doc = tomllib.load(fh)
        blocks = chain_blocks(doc)
        for i, blk in enumerate(blocks):
            spec = spec_of(path.stem, i, blk)
            out = _OUT / ("%s__%d.json" % (path.stem, i))
            out.write_bytes(json.dumps(spec, sort_keys=True).encode("utf-8"))
            manifest.append([path.stem, i, len(spec["steps"]), out.name])
            n_chain += 1
        if not blocks:
            manifest.append([path.stem, -1, 0, "LEAF-no-chain-block"])
    print("declared [[cascade.chain]] blocks: %d" % n_chain)
    print("descriptors with >=1 chain block: %d"
          % len({m[0] for m in manifest if m[1] >= 0}))
    print("descriptors with NO chain block: %s"
          % sorted({m[0] for m in manifest if m[1] < 0}))

    # ── ablations: isolate CAUSE, not correlation ────────────────────────────
    with (_CAT / "net_chirality.toml").open("rb") as fh:
        nc = chain_blocks(tomllib.load(fh))[0]
    nc_spec = spec_of("net_chirality", 0, nc)
    swapped = dict(nc_spec)
    swapped["steps"] = [PLAIN if ("fold_op" in s) else s
                        for s in nc_spec["steps"]]
    (_OUT / "ablate_netchir_foldstep_to_plain.json").write_bytes(
        json.dumps(swapped, sort_keys=True).encode("utf-8"))

    with (_CAT / "cyclic_gcd.toml").open("rb") as fh:
        cg = chain_blocks(tomllib.load(fh))[0]
    cg_spec = spec_of("cyclic_gcd", 0, cg)
    for tag, extra in (("fold", FOLD), ("map", MAP)):
        inj = dict(cg_spec)
        inj["steps"] = list(cg_spec["steps"]) + [extra]
        (_OUT / ("inject_cyclicgcd_extra_%s.json" % tag)).write_bytes(
            json.dumps(inj, sort_keys=True).encode("utf-8"))

    headless = {"summary": "s", "returns": "r", "steps": [PLAIN]}
    (_OUT / "headless_plain.json").write_bytes(
        json.dumps(headless, sort_keys=True).encode("utf-8"))
    (_OUT / "control_plain.json").write_bytes(
        json.dumps({"name": "c", "summary": "s", "returns": "r",
                    "steps": [PLAIN]}, sort_keys=True).encode("utf-8"))
    (_OUT / "control_one_fold.json").write_bytes(
        json.dumps({"name": "c", "summary": "s", "returns": "r",
                    "steps": [FOLD]}, sort_keys=True).encode("utf-8"))
    (_OUT / "control_one_map.json").write_bytes(
        json.dumps({"name": "c", "summary": "s", "returns": "r",
                    "steps": [MAP]}, sort_keys=True).encode("utf-8"))
    print("wrote %d JSON files -> %s" % (len(list(_OUT.glob('*.json'))), _OUT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
