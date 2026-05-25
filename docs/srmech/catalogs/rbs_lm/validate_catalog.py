"""R-RBS-LM-13 catalog validator — compute_from_source schema.

Validates:

1. descriptor.toml has the 6 mandatory AMSC sections per CLAUDE.md §2,
   plus the new [fetch.compute_from_source] block (R-RBS-LM-12 §4).
2. research_notes.ndjson (the metadata sidecar) is well-formed.
3. Adapter-resolution status — checks whether the srmech-side
   `compute_from_source` adapter is implemented yet; if not, reports
   GATED rather than FAIL (the catalog is intentionally forward-spec'd
   per R-RBS-LM-12 §6).

Usage:
    PYTHONPATH=docs/srmech/python python3 \\
        docs/srmech/catalogs/rbs_lm/validate_catalog.py
"""

import json
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, "docs/srmech/python")


CATALOG_ROOT = Path("docs/srmech/catalogs/rbs_lm")


def main() -> None:
    print(f"=== R-RBS-LM-13 catalog validation (compute_from_source schema) ===")

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

    # ---- 2. compute_from_source-specific schema ------------------------
    if desc["fetch"]["adapter"] != "compute_from_source":
        print(f"  WARNING: this catalog's adapter is "
              f"'{desc['fetch']['adapter']}', not 'compute_from_source' "
              f"— validator expected the v0.5 schema")
    else:
        print(f"\n  compute_from_source schema:")
        cfs = desc["fetch"].get("compute_from_source", {})
        for field in ["source_model", "corpus_locator", "encoder_module", "encoder_version"]:
            val = cfs.get(field, "(missing)")
            print(f"    {field}: {val}")
        params = cfs.get("encoder_params", {})
        print(f"    encoder_params:")
        for field, val in params.items():
            print(f"      {field} = {val}")
        # All 4 top-level fields required
        for field in ["source_model", "corpus_locator", "encoder_module", "encoder_version"]:
            if field not in cfs:
                print(f"  FAIL: [fetch.compute_from_source] missing {field}")
                sys.exit(1)
        print(f"    — required fields present — OK")

    # ---- 3. research_notes.ndjson well-formedness ----------------------
    notes_path = CATALOG_ROOT / "research_notes.ndjson"
    if notes_path.exists():
        rows = []
        for ln, line in enumerate(notes_path.read_text().splitlines(), 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"  FAIL: research_notes.ndjson line {ln}: {e}")
                sys.exit(1)
        print(f"\n  research_notes.ndjson: {len(rows)} rows; all valid JSON")
        kinds = {}
        for r in rows:
            kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
        print(f"  Row kinds: {kinds}")
    else:
        print(f"\n  research_notes.ndjson: not present (optional sidecar)")

    # ---- 4. Adapter-resolution status ---------------------------------
    print(f"\n  Adapter resolution check:")
    try:
        from srmech.amsc.adapters import compute_from_source  # noqa: F401
        print(f"    compute_from_source adapter: IMPLEMENTED  (srmech package side)")
        print(f"    Catalog is fully validatable + runnable.")
    except ImportError:
        print(f"    compute_from_source adapter: NOT YET IMPLEMENTED (GATED)")
        print(f"    Catalog is FORWARD-SPEC'D per R-RBS-LM-12 §6 — schema valid;")
        print(f"    adapter resolution awaits srmech v0.5.0rc release.")
        print(f"    The srmech-fix session plan is documented in R-RBS-LM-12 §6.")

    # ---- 5. produced/ directory ---------------------------------------
    produced_dir = CATALOG_ROOT / "produced"
    if produced_dir.exists():
        produced_files = list(produced_dir.iterdir())
        if produced_files:
            print(f"\n  produced/ directory: {len(produced_files)} locally-computed artefacts")
            for f in produced_files:
                print(f"    {f.name}: {f.stat().st_size} bytes")
        else:
            print(f"\n  produced/ directory: empty (no adapter runs yet)")
    else:
        print(f"\n  produced/ directory: not yet created (will be created by adapter on first run)")

    print(f"\n=== Catalog validation complete ===")


if __name__ == "__main__":
    main()
