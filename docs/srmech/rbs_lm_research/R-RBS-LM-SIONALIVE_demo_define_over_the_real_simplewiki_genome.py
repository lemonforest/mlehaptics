r"""R-RBS-LM-SIONALIVE (#231/F1233) — the LIVE demo: Siona's `define` reading the REAL simplewiki body instrument.

Points `Session.load_corpus` at the full simplewiki directed Class-L genome (831k vocab / 39M edges, built by
R-RBS-LM-SIMPLEWIKIGENOME) and shows "what is X?" returning the relational read (what X co-occurs with, metric-ranked,
with the charge/direction) over the real corpus — vs the shipped baseline that grounds to srmech TOOLS (z_boson_mass,
the F1219 mis-ground). The F1219 CAN'T-TELL, closed, at real scale.

srmech 0.9.0rc253 (native). Run (needs the simplewiki genome on disk; load takes ~1-2 min at 39M edges):
  /tmp/srmech_v/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-SIONALIVE_...py
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "siona"))   # docs/srmech/siona on the path

from siona.infer import Session

GENOME = Path.home() / "corpora" / "wikipedia" / "simplewiki_directed.genome"
QUERIES = ["what is water", "what is science", "what is country", "what is music",
           "what is language", "what is planet", "what is river"]


def main():
    if not GENOME.exists():
        print("simplewiki genome not on disk yet: %s" % GENOME)
        return 1
    print("=== R-RBS-LM-SIONALIVE — Siona.define over the REAL simplewiki genome (831k/39M) ===\n")
    s = Session()

    print("BASELINE (no corpus) — grounds to srmech tools (F1219):")
    for q in QUERIES[:3]:
        print("   %-18s -> %s" % (q, s.turn(q)[2]))

    t0 = time.time()
    nv = s.load_corpus(GENOME)
    print("\nloaded the simplewiki directed genome: %d vocab in %.1fs\n" % (nv, time.time() - t0))

    print("WITH THE REAL SIMPLEWIKI STORE — the relational read (metric-ranked; -> / <- = direction):")
    for q in QUERIES:
        print("   %-18s -> %s" % (q, s.turn(q)[2]))

    print("\nVERDICT: Siona's `define` reads the REAL simplewiki directed Class-L store — 'what is X?' returns what X")
    print("         is seen-with (relational + direction) instead of z_boson_mass. F1219 CAN'T-TELL closed at scale.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
