#!/usr/bin/env python3
"""gh #1653 — CROSS-CHECK for the bare-C host (_1653_barec_host_rc444.c), rc444.

This script is NOT part of the bare-C proof. The proof is the C binary, which
has no Python in its process. This is the independent verification that the C
host's own TOML -> JSON marshalling is a FAITHFUL MIRROR of the Python
projection, so that a surface-A rejection reported by the C host cannot be an
artefact of the host's marshalling.

Two things are checked, both against the C host's NDJSON output:

  (1) SPEC-HASH PARITY. For every cascade_catalog chain the C parse gate
      ACCEPTS, the C host emitted the Class-A sha256 of the normalized spec
      srmech_chain_spec_parse produced. Here we build the SAME chain dict the
      Python projection builds (srmech/dsl/_cascade_chain.py:118-127), run the
      PURE srmech.cascade.compose.parse_chain_spec, re-normalize to the exact
      shape the C peer emits ({name, on_error, returns, steps:[{class_id,
      on_error, op}], summary} — see compose.py:378-397
      _chain_spec_from_native, which is the contract), canonical-dump it and
      hash it. Equal hashes => the C host handed the C gate the same object the
      Python engine parses.

  (2) THE REFERENCE VALUES the C host cannot produce. For every declared chain
      variant, run the Python projection and record its value (or its
      exception). This is the byte-for-byte comparison column that is EMPTY on
      surface A because C returns no value there; recording it here makes the
      absence explicit rather than implied.

Discipline: no abs(), no numpy, no RNG, no stdlib fractions, no float
arithmetic. Exact ints / exact Q only. Reads shipped source; writes only its
own NDJSON under docs/srmech/notes/.

Run (from docs/srmech/python):
    python3 ../notes/_1653_barec_host_verify_rc444.py <path-to-barec-ndjson>
"""

from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import srmech                                            # noqa: E402
from srmech.amsc.format import sha256_bytes              # noqa: E402  (Class A)
from srmech.cascade import compose as _compose           # noqa: E402
from srmech.dsl import _cascade_chain as _cc             # noqa: E402
from srmech.dsl._catalog import load_catalog             # noqa: E402

OUT = pathlib.Path(__file__).with_suffix(".ndjson")

# Mirrored READ-ONLY from tests/test_cascade_catalog_executable_rc420.py:253-258.
# TOML cannot spell None, so kuramoto_step.general's optional inputs live in the
# test file rather than in the descriptor. Recorded with provenance; not edited.
CASE_DEFAULTS = {
    "kuramoto_step": {"adjacency": None, "alpha": 0.0,
                      "pin_anchor": None, "pin_strength": 1.0},
}


def canonical(obj) -> bytes:
    """The exact byte form srmech_json_write_ws implements."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")


def normalized_spec(spec) -> dict:
    """The normalized dict shape the C peer emits (compose.py:378-397)."""
    return {
        "name": spec.name,
        "on_error": spec.on_error,
        "returns": spec.returns,
        "steps": [{"class_id": s.class_id, "on_error": s.on_error, "op": s.op}
                  for s in spec.steps],
        "summary": spec.summary,
    }


def chain_dicts():
    """(op, variant, chain_dict) for every declared [[cascade.chain]] entry,
    built the way srmech/dsl/_cascade_chain.py:118-127 builds it."""
    out = []
    for name, desc in sorted(load_catalog().items()):
        casc = desc.get("cascade", {})
        for entry in _cc._chain_entries(desc):
            variant = entry.get("variant", "default")
            out.append((name, variant, {
                "name": f"{name}.{variant}",
                "summary": entry.get("summary",
                                     casc.get("purpose", name)),
                "returns": entry.get("returns", ""),
                "steps": entry.get("steps", []),
            }, entry))
    return out


def c_hashes(path: pathlib.Path) -> dict:
    """{op -> [spec_sha256, ...]} from the bare-C host's NDJSON, in order."""
    got: dict = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("section") != "A" or "spec_sha256" not in rec:
            continue
        got.setdefault(rec["op"], []).append(rec["spec_sha256"])
    return got


def main() -> int:
    nd = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if nd is None or not nd.is_file():
        print("usage: _1653_barec_host_verify_rc444.py <barec-host.ndjson>")
        return 2
    ch = c_hashes(nd)
    rows = []
    st = srmech.native_status()
    rows.append({"kind": "environment", "srmech_version": srmech.__version__,
                 "has_native": bool(st.get("has_native")),
                 "abi": st.get("abi_version"),
                 "barec_ndjson": str(nd)})
    seen: dict = {}
    n_hash_cmp = n_hash_ok = n_val_ok = n_val_raise = 0
    for op, variant, cd, _entry in chain_dicts():
        idx = seen.get(op, 0)
        seen[op] = idx + 1
        rec = {"kind": "chain", "op": op, "variant": variant,
               "chain_name": cd["name"], "n_steps": len(cd["steps"])}
        # (1) spec-hash parity
        try:
            spec = _compose.parse_chain_spec(cd)
            py_sha = sha256_bytes(canonical(normalized_spec(spec)))
            rec["py_parse"] = "ok"
        except Exception as exc:                       # noqa: BLE001
            py_sha = None
            rec["py_parse"] = f"{type(exc).__name__}: {exc}"
        c_list = ch.get(op, [])
        c_sha = c_list[idx] if idx < len(c_list) else ""
        rec["c_spec_sha256"] = c_sha
        rec["py_spec_sha256"] = py_sha or ""
        if c_sha and py_sha:
            n_hash_cmp += 1
            rec["spec_hash_match"] = (c_sha == py_sha)
            if c_sha == py_sha:
                n_hash_ok += 1
        else:
            rec["spec_hash_match"] = None
            rec["spec_hash_note"] = ("C parse gate rejected this chain, so it "
                                     "emitted no spec hash — nothing to compare")
        # (2) the reference value C never produces on surface A
        pcs = _entry.get("proof_cases", []) if isinstance(_entry, dict) else []
        inputs = dict(pcs[0].get("inputs", {})) if pcs else {}
        merged = dict(CASE_DEFAULTS.get(op, {}))
        merged.update(inputs)
        rec["proof_case_inputs"] = json.loads(json.dumps(inputs, default=repr))
        rec["used_test_side_defaults"] = bool(CASE_DEFAULTS.get(op))
        try:
            val = _cc.run_cascade_chain(op, merged, variant=variant)
            rec["py_value_repr"] = repr(val)
            rec["py_value_status"] = "ok"
            n_val_ok += 1
        except Exception as exc:                       # noqa: BLE001
            rec["py_value_repr"] = ""
            rec["py_value_status"] = f"{type(exc).__name__}: {exc}"
            n_val_raise += 1
        rows.append(rec)
    rows.append({"kind": "summary",
                 "chain_variants": sum(1 for r in rows if r["kind"] == "chain"),
                 "descriptors_with_a_chain": len(seen),
                 "spec_hashes_compared": n_hash_cmp,
                 "spec_hashes_matching": n_hash_ok,
                 "python_values_ok": n_val_ok,
                 "python_values_raised": n_val_raise})
    OUT.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows),
                   encoding="utf-8")
    print(f"spec hashes: {n_hash_ok}/{n_hash_cmp} match | "
          f"python values: {n_val_ok} ok, {n_val_raise} raised")
    print(f"wrote {OUT}")
    return 0 if n_hash_cmp and n_hash_ok == n_hash_cmp else 1


if __name__ == "__main__":
    raise SystemExit(main())
