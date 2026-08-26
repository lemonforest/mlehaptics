"""reproduce.py — re-run the recent srmech-native experiments and DIFF each output
against its committed baseline. The "get ready for rcN" harness.

When a fixed rcN srmech package arrives (with the §10 srmech-mcp fixes + whatever
else lands), run this in a CLEAN venv OUTSIDE the source tree against the new rc:

    /path/to/rcN-venv/bin/python reproduce.py            # all
    /path/to/rcN-venv/bin/python reproduce.py 134 135     # subset by substring

For each experiment it re-runs the script, then compares the freshly-written NDJSON
against the git-committed baseline (HEAD), dropping ONLY the fields that legitimately
change across a version bump (srmech_version / abi_version / has_native / timing).
Everything else — every measured number AND the catalog descriptor_hash — must match.

  REPRODUCED  → determinism held across the version bump (the discipline's promise).
  CHANGED     → rcN changed a result; investigate (intended package change vs regression).
  ERROR       → the script failed under rcN (a break to report upstream).

Our recent work uses the srmech PACKAGE (Class-L Laplacian eigendecomp, seedable
klein4_random, hash) — insulated from the §10 MCP-wrapper bugs — so REPRODUCED is
the expectation unless rcN alters package math.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
MEAS = HERE.parent / "catalogs" / "rbs_lm_substrate" / "substrate_measurements"
GIT_MEAS = "docs/srmech/catalogs/rbs_lm_substrate/substrate_measurements"

# fields that legitimately change across a version bump — excluded from comparison
DROP = {"srmech_version", "abi_version", "has_native", "build_seconds", "parser_version"}

MANIFEST = [
    ("R-RBS-LM-126_context_state_encoder_capacity.py", "inference_step1_context.ndjson"),
    ("R-RBS-LM-127_context_conditioned_distribution.py", "inference_step2_distribution.ndjson"),
    ("R-RBS-LM-128_temperature_coherence_diversity.py", "inference_step3_temperature.ndjson"),
    ("R-RBS-LM-129_autoregressive_inference_loop.py", "inference_step4_loop.ndjson"),
    ("R-RBS-LM-130_instantiable_substrate_demo.py", "inference_step5_instrument.ndjson"),
    ("R-RBS-LM-131_emergent_perplexity_resolution_depth.py", "emergent_perplexity_resolution_depth.ndjson"),
    ("R-RBS-LM-132_storage_vs_expression_two_axis.py", "storage_vs_expression_two_axis.ndjson"),
    ("R-RBS-LM-133_translation_invariance_core_test.py", "translation_invariance_core.ndjson"),
    ("R-RBS-LM-134_srmech_native_spectral_invariance.py", "srmech_native_spectral_invariance.ndjson"),
    ("R-RBS-LM-135_isolate_content_storage_envelope_and_chirality.py", "isolate_content_storage.ndjson"),
]


def _norm(records):
    return [{k: v for k, v in r.items() if k not in DROP} for r in records]


def _git_baseline(relname):
    try:
        out = subprocess.run(["git", "show", f"HEAD:{GIT_MEAS}/{relname}"],
                             cwd=str(HERE), capture_output=True, text=True, check=True).stdout
        return [json.loads(l) for l in out.splitlines() if l.strip()]
    except subprocess.CalledProcessError:
        return None


def main():
    try:
        import srmech
        ver = srmech.__version__
    except Exception as e:  # noqa
        ver = f"(import failed: {e})"
    only = [a for a in sys.argv[1:]]
    print(f"reproduce.py — srmech {ver}\n")

    results = []
    for script, nd in MANIFEST:
        if only and not any(o in script for o in only):
            continue
        baseline = _git_baseline(nd)
        run = subprocess.run([sys.executable, str(HERE / script)],
                             capture_output=True, text=True, timeout=1200)
        if run.returncode != 0:
            tail = (run.stderr.strip().splitlines() or ["(no stderr)"])[-1]
            results.append((script, "ERROR", tail[:70]))
            continue
        new = [json.loads(l) for l in (MEAS / nd).read_text().splitlines() if l.strip()]
        if baseline is None:
            results.append((script, "NO-BASELINE", f"recorded {len(new)}"))
            continue
        a, b = _norm(baseline), _norm(new)
        if a == b:
            results.append((script, "REPRODUCED", f"{len(b)} records bit-exact"))
        else:
            if len(a) != len(b):
                results.append((script, "CHANGED", f"record count {len(a)}→{len(b)}"))
            else:
                i = next((j for j in range(len(a)) if a[j] != b[j]), 0)
                keys = [k for k in (set(a[i]) | set(b[i])) if a[i].get(k) != b[i].get(k)]
                results.append((script, "CHANGED", f"rec {i}: {keys[:4]}"))

    print(f"{'script':>54} | {'status':>11} | detail")
    print("-" * 100)
    for s, st, d in results:
        print(f"{s[:54]:>54} | {st:>11} | {d}")
    n_ok = sum(1 for _, st, _ in results if st == "REPRODUCED")
    print(f"\n{n_ok}/{len(results)} reproduced bit-exact (version/timing fields excluded).")
    if any(st == "CHANGED" for _, st, _ in results):
        print("CHANGED → a result moved under this srmech; investigate intended-change vs regression.")
    if any(st == "ERROR" for _, st, _ in results):
        print("ERROR → a script broke under this srmech; report upstream.")


if __name__ == "__main__":
    main()
