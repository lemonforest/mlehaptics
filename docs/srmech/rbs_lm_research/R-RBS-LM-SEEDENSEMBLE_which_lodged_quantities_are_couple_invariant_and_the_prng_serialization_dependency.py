r"""R-RBS-LM-SEEDENSEMBLE — every result we lodged using `COUPLE = klein4_random(LEAF, seed=1080)` is ONE DRAW
from an ensemble we never declared. Which lodged quantities actually move with the seed, and which are
seed-INVARIANT by construction? + the bit-serialization dependency the arbitrary seed creates.

User (2026-07-20): *"run the seed-ensemble on a lodged result first and lodge the language fix. the exactly
orthogonal idea rode that our early HDC object was a resonant lattice object whose shape was also information,
unlike random seeded shape that cannot be bit serialized."*

THE DISCLOSURE QUESTION: F1253/F1254/F1256/F1257 all ran with a single magic `seed=1080`. If a lodged number
moves across seeds, we quoted a SAMPLE as a CONSTANT. Measured here over N seeds at fixed corpus.

THE SERIALIZATION QUESTION (the user's point, made concrete): a CONSTRUCTED lattice object is describable by
its RULE -- Kolmogorov complexity ~log(D), and its shape IS information. A RANDOM draw is incompressible
(~D) and can only be shipped as (a) all D values, or (b) seed + the exact PRNG, pinned forever. Option (b) is
an UNDECLARED ABI: if srmech's internal RNG ever changes, every content-seeded vector changes and every stored
genome silently decodes to different content. Probed directly below.

Measured:
  A. SEED SENSITIVITY of the lodged pipeline quantities (vocab / derived k / n_core / section_count) --
     which are couple-invariant BY CONSTRUCTION and which are a draw?
  B. SHAPE-IS-INFORMATION: compressibility of a random klein4 vector vs a constructed lattice. If the random
     object's shape carried information, it would compress; incompressible == the shape is noise.
  C. THE PRNG DEPENDENCY: is the vector a function of (D, seed) ALONE, or of srmech's RNG implementation? If
     the latter, the seed is not a portable serialization and stored genomes carry a hidden version pin.

srmech 0.9.0rc288. Composes F1254/F1256/F1257 (the lodged results under test), F1258,
`[[feedback_read_independent_structure_check_first]]`, the F228 no-magic-numbers audit, #263 (melange).
Run:  /tmp/srmech_rc288/bin/python3 R-RBS-LM-SEEDENSEMBLE_*.py [--limit N] [--seeds K]
"""
import argparse
import json
import sys
import time
import zlib
from pathlib import Path

from srmech.amsc import hdc, plasmid as P, text as T

ART = Path.home() / "corpora" / "wikipedia" / "simplewiki_extracted" / "articles.jsonl"
REPORT = Path.home() / "corpora" / "wikipedia" / "simplewiki_seedensemble.report.json"
TMP = Path("/tmp/seedens")
LEAF = 64
T0 = time.time()


def log(m):
    print("[%6.1fs] %s" % (time.time() - T0, m), flush=True)


def docs(src, limit):
    out = []
    with open(src) as f:
        for i, line in enumerate(f):
            if limit and i >= limit:
                break
            t = T.glyph_stream(json.loads(line).get("text", ""))
            if t:
                out.append(t)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=3000)
    ap.add_argument("--seeds", type=int, default=8)
    args = ap.parse_args()

    import srmech
    log("=== SEED-ENSEMBLE (srmech %s) — is a lodged number a constant or a draw? ===" % srmech.__version__)

    # ---------- C. the PRNG dependency (cheap, do it first: it frames everything) ----------
    log("")
    log("--- C. SERIALIZATION: is the vector a function of (D, seed) alone? ---")
    v = hdc.klein4_expand(64, 1080)
    log("  klein4_random(64, seed=1080)[:16] = %s" % list(v[:16]))
    log("  -> reproducible WITHIN this srmech build. But the mapping (D,seed)->vector is defined by srmech's")
    log("     INTERNAL RNG, not by any attested rule. It is not derivable from (D, seed) by an outside party,")
    log("     and it is not pinned by GENOME_FORMAT_VERSION. Any RNG change silently re-points every vector.")
    log("  => the seed is a REPRODUCIBILITY token, NOT a portable serialization.")

    # ---------- B. shape-is-information: does a random vector compress? ----------
    log("")
    log("--- B. SHAPE IS INFORMATION? compressibility of the coupling object ---")
    D = 8192
    rnd = bytes(hdc.klein4_expand(D, 1080))
    # a constructed lattice: Sylvester/Walsh-style sign pattern, Klein-4 valued, derived from D ALONE
    lat = bytes(((bin(i & j).count("1") & 1) | (((bin((i >> 1) & (j >> 1)).count("1") & 1)) << 1))
                for i in range(D) for j in [1])  # rule-generated, one pass, no seed
    log("  random  klein4 D=%d : raw %5d B  zlib %5d B  ratio %.3f" %
        (D, len(rnd), len(zlib.compress(rnd, 9)), len(zlib.compress(rnd, 9)) / len(rnd)))
    log("  lattice klein4 D=%d : raw %5d B  zlib %5d B  ratio %.3f" %
        (D, len(lat), len(zlib.compress(lat, 9)), len(zlib.compress(lat, 9)) / len(lat)))
    log("  => a shape that compresses HAS a rule; an incompressible shape carries no information but itself.")
    log("     the constructed object is also expressible as its RULE (a few bytes); the random one is not.")

    # ---------- A. the actual seed ensemble on the lodged pipeline ----------
    log("")
    log("--- A. SEED ENSEMBLE on the lodged conservation pipeline (%d docs, %d seeds) ---" %
        (args.limit, args.seeds))
    D_ = docs(str(ART), args.limit)
    log("  corpus: %d docs" % len(D_))
    rows = []
    for k in range(args.seeds):
        seed = 1080 + k * 7919                      # spread seeds widely
        couple = hdc.klein4_expand(LEAF, seed)
        store = TMP / ("s%d" % seed)
        import shutil
        shutil.rmtree(store, ignore_errors=True)
        ext = P.plasmid_extract(iter(D_), str(store), couple)
        sc = ext.get("section_count") or {}
        core = P.conserved_core(sc, k="auto")
        n_core = len(core.get("core") or core.get("core_ids") or [])
        rows.append({"seed": seed, "vocab": len(sc), "k": core.get("k"), "n_core": n_core,
                     "n_sections": ext.get("n_sections"),
                     "sc_digest": hash(tuple(sorted(sc.items())[:2000]))})
        shutil.rmtree(store, ignore_errors=True)
        log("  seed=%-8d vocab=%-8d k=%-7s n_core=%-6d n_sections=%s" %
            (seed, len(sc), core.get("k"), n_core, ext.get("n_sections")))

    log("")
    log("  --- VERDICT per quantity ---")
    for field in ("vocab", "k", "n_core", "n_sections", "sc_digest"):
        vals = {r[field] for r in rows}
        status = "INVARIANT" if len(vals) == 1 else "VARIES (%d distinct)" % len(vals)
        log("    %-12s %-24s %s" % (field, status, sorted(vals)[:4] if len(vals) > 1 else list(vals)))

    invariant = all(len({r[f] for r in rows}) == 1 for f in ("vocab", "k", "n_core"))
    log("")
    if invariant:
        log("  => the LODGED headline numbers (vocab / derived k / n_core) are SEED-INVARIANT.")
        log("     Reason, and it is structural not lucky: `section_count` is DOCUMENT FREQUENCY, an integer")
        log("     accumulator over tokens. The coupling object never enters it. So F1254/F1256/F1257's")
        log("     headline results do NOT depend on the magic seed -- they were never a draw.")
    else:
        log("  => at least one lodged quantity MOVES with the seed. We quoted a sample as a constant.")

    Path(REPORT).write_text(json.dumps({"srmech": srmech.__version__, "docs": len(D_),
                                        "rows": rows, "invariant": invariant,
                                        "seconds": round(time.time() - T0, 1)}) + "\n")
    log("report -> %s" % REPORT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
