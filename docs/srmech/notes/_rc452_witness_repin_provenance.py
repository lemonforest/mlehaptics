#!/usr/bin/env python3
"""rc452 (gh #1653) — the generating code for the `WITNESS_RC416` re-pin.

    cd docs/srmech/python && PYTHONPATH=. python3 ../notes/_rc452_witness_repin_provenance.py

WHY THIS FILE EXISTS
====================
`tests/test_search_glyph_tokenizer_rc416.py` pins a sha256 over the whole
search corpus. The registry-ripple phase registered three ops, which moves that
digest — and the handed-over working tree bumped all 76
``describe()["tools"]["total"]`` count-pins but NOT this digest, taking three
tests red. Re-pinning a digest is exactly the move that gate's own message warns
can convert a real contract break into a silent one, so the re-pin is only
honest if determinism and causation were both MEASURED first. Per
``[[feedback_computational_provenance_discipline]]`` the measurement ships with
the number.

WHAT IT MEASURES, AND WHAT WOULD HAVE FALSIFIED THE RE-PIN
==========================================================
1. DETERMINISM — the corpus digest under four PYTHONHASHSEEDs, with all three
   derivation paths cross-checked inside each run. **Falsifier:** any two runs
   disagreeing, or any path disagreeing with the witness, would mean the
   ADR-0011 witness contract is broken and the correct action is to fix the
   frame build, NOT to re-pin.
2. CAUSATION — the op-frame NAME set against the pre-registration population
   committed in ``tests/registered_op_names.txt`` at the branch head.
   **Falsifier:** any ADDED name other than the three registered ops, or any
   REMOVED name, or a carrier count away from 29, would mean something beyond
   the declared change moved the corpus.

Emits NDJSON (one record per line) per
``[[feedback_ndjson_over_bloated_json]]``.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SEEDS = ("0", "13", "271", "9999")
NEW = (
    "srmech.amsc.descriptor.render_template",
    "srmech.amsc.format.sha256_raw",
    "srmech.signal_processing.mint_vector",
)


def _one_run() -> str:
    """Digest + counts + the three-path agreement, inside ONE process."""
    import srmech.introspect.search as S
    from srmech.amsc.format import sha256_bytes

    ops, _ = S._build_frames("ops")
    carriers, _ = S._build_frames("carriers")
    both, witness = S._build_frames("all")
    recomputed = sha256_bytes(b"".join(f.blob for f in both))
    live = S.search("rank", k=1).witness
    return json.dumps({
        "record": "determinism",
        "n_ops": len(ops),
        "n_carriers": len(carriers),
        "n_all": len(both),
        "witness": witness,
        "paths_agree": bool(recomputed == witness == live),
    }, sort_keys=True)


def main() -> int:
    if "--one" in sys.argv:
        print(_one_run())
        return 0

    here = Path(__file__).resolve()
    rows = []
    for seed in SEEDS:
        out = subprocess.run(
            [sys.executable, str(here), "--one"],
            capture_output=True, text=True,
            env={**__import__("os").environ, "PYTHONHASHSEED": seed,
                 "PYTHONPATH": "."},
        )
        if out.returncode != 0:
            print(out.stderr[-2000:], file=sys.stderr)
            return 1
        rec = json.loads(out.stdout.strip().splitlines()[-1])
        rec["seed"] = seed
        rows.append(rec)
        print(json.dumps(rec, sort_keys=True))

    # ── causation ────────────────────────────────────────────────────────
    import srmech.introspect.search as S
    head = subprocess.run(
        ["git", "show", "HEAD:docs/srmech/python/tests/registered_op_names.txt"],
        capture_output=True, text=True,
        cwd=str(here.parents[3]),
    ).stdout
    old = {l.strip() for l in head.splitlines() if l.strip()}
    ops, _ = S._build_frames("ops")
    carriers, _ = S._build_frames("carriers")
    live = {f.name for f in ops}
    added = sorted(live - old)
    touched = sorted(f.name for f in carriers
                     if any(n in f.blob.decode("utf-8", "replace")
                            for n in added))
    print(json.dumps({
        "record": "causation",
        "n_head_names": len(old),
        "n_live_op_frames": len(live),
        "added": added,
        "removed": sorted(old - live),
        "n_carriers": len(carriers),
        "carrier_frames_mentioning_added": touched,
    }, sort_keys=True))

    digests = {r["witness"] for r in rows}
    print(json.dumps({
        "record": "verdict",
        "deterministic": len(digests) == 1,
        "all_paths_agree": all(r["paths_agree"] for r in rows),
        "frame_counts_equal": len({r["n_all"] for r in rows}) == 1,
        "causation_is_exactly_the_registrations": added == sorted(NEW),
        "witness": sorted(digests)[0] if len(digests) == 1 else None,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
