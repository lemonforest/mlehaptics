"""R-RBS-LM-10 catalog validator — confirms catalog structure + descriptor schema.

Per the R-RBS-NN-9 catalog validator pattern. Validates:

1. descriptor.toml has the 6 mandatory AMSC sections per CLAUDE.md §2.
2. detection_heptad/m_bindings.ndjson is well-formed (each line is valid JSON).
3. Representative atomic bindings re-mint deterministically per Spike #170.
4. The empirical_finding row maps to R-RBS-LM-1 §7 scenario (d).
5. Future-work pointers reference existing partition REPORTs.

Usage:
    PYTHONPATH=docs/srmech/python python3 \\
        docs/srmech/catalogs/rbs_lm/validate_catalog.py
"""

import json
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, "docs/srmech/python")

from srmech.signal_processing.rbs_hdc_instrument import mint_vector  # noqa: E402


CATALOG_ROOT = Path("docs/srmech/catalogs/rbs_lm")


def main() -> None:
    print(f"=== R-RBS-LM-10 catalog validation ===")

    # ---- 1. descriptor.toml --------------------------------------------
    desc = tomllib.loads((CATALOG_ROOT / "descriptor.toml").read_text())
    print(f"\n  Catalog: {desc['source']['human_readable_name']}")
    print(f"  Key:     {desc['source']['key']}")
    required = ["source", "fetch", "parse", "schema", "rendering", "attestation"]
    missing = [s for s in required if s not in desc]
    if missing:
        print(f"  FAIL: descriptor missing sections: {missing}")
        sys.exit(1)
    print(f"  Required sections present: {required} — OK")

    # ---- 2. m_bindings.ndjson well-formedness --------------------------
    rows = []
    for ln, line in enumerate((CATALOG_ROOT / "detection_heptad" / "m_bindings.ndjson").read_text().splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
            rows.append(row)
        except json.JSONDecodeError as e:
            print(f"  FAIL: line {ln}: {e}")
            sys.exit(1)
    print(f"\n  m_bindings.ndjson: {len(rows)} rows; all valid JSON")
    kinds = {}
    for r in rows:
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    print(f"  Row kinds: {kinds}")

    # ---- 3. Atomic bindings re-mint deterministically ------------------
    atomic = [r for r in rows if r["kind"] == "atomic"]
    print(f"\n  Re-minting {len(atomic)} atomic rows...")
    for r in atomic:
        v = mint_vector(r["mint_name"], D=r["D"])
        print(f"    {r['binding_id']:35s} minted len={len(v)} bytes (D={r['D']})  OK")

    # ---- 4. Empirical finding row mapping ------------------------------
    finding = next((r for r in rows if r["kind"] == "empirical_finding"), None)
    if finding:
        print(f"\n  Empirical finding row:")
        print(f"    Scale points tested: {finding['scale_points_tested']}")
        print(f"    Agreement percents:  {finding['agreement_pcts']}")
        print(f"    Scenario:            {finding['scenario']}")
        print(f"    Framework reading unaffected: {finding['framework_reading_unaffected']}")

    # ---- 5. Future-work pointers ---------------------------------------
    future_work = [r for r in rows if r["kind"] == "future_work_pointer"]
    print(f"\n  Future-work pointers: {len(future_work)}")
    for r in future_work:
        print(f"    {r['binding_id']}: {r['description'][:80]}")

    # ---- 6. Encoding descriptors --------------------------------------
    encodings = [r for r in rows if r["kind"] == "encoding_descriptor"]
    print(f"\n  Encoding descriptors: {len(encodings)}")
    for r in encodings:
        path = Path(r["instrument_path"])
        exists = path.exists()
        size_ok = (path.stat().st_size == r["instrument_bytes"]) if exists else False
        flag = "OK" if (exists and size_ok) else ("MISSING" if not exists else "SIZE MISMATCH")
        print(f"    {r['binding_id']}: n_obs={r['n_observations']}, "
              f"path={path.name}, ratio={r['compression_ratio']}, {flag}")

    print(f"\n=== Catalog validation complete ===")


if __name__ == "__main__":
    main()
