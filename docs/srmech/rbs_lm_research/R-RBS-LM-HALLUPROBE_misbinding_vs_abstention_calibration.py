r"""R-RBS-LM-HALLUPROBE (F767) — can we still claim "no hallucination"? A falsification/characterization probe.

User next-question (2026-06-15): "maybe we can't claim no hallucination if it's inherent in synaptic neural net
inference. would be good to discover."

THE DISTINCTION (F765): Siona cannot CONFABULATE (fabricate content — she returns only stored, attested strings), but
she CAN MISBIND — retrieve REAL attested content and bind it to the WRONG query (the nearest-neighbour failure mode:
NN always returns a nearest item unless an abstention threshold says "none"). 'flibbertigibbet'->'fleetwood' was
misbinding, not confabulation. So "no hallucination" is really "(retrieval-only content) + (CALIBRATED ABSTENTION)".

THIS PROBE measures the abstention calibration. Pass-1 comprehension (F765 _understand) accepts a resolution iff
sim >= FLOOR and edit_distance(w, canonical) <= RATIO*len(w). We sweep (FLOOR, RATIO) over three input classes and
tabulate, per cell:
  • near-miss (typo of a KNOWN word, intended canonical given):
        CORRECT  = resolved to the intended canonical (good comprehension)
        MISBIND  = resolved to a DIFFERENT word, confidently (a hallucination)
        ABSTAIN  = not accepted -> honest asking-state (safe, but a missed typo)
  • genuinely-unknown (a real word NOT in any store, NOT a typo of a known word):
        MISBIND  = force-comprehended into some store word (a hallucination)
        ABSTAIN  = declined (CORRECT)
  • known (a store word): trivially routable -> answered (coverage sanity check).
DISCOVERS: is there a (FLOOR, RATIO) where near-miss CORRECT is high AND unknown MISBIND ~0? If yes, misbinding is
SUPPRESSIBLE by calibration. If raising the gate kills near-miss comprehension before it kills unknown-misbind, the
tradeoff is inherent. Efficient: ONE _abstract_resolve(floor=0) per word gives the top candidate + sim; the grid is
cheap arithmetic over that.

srmech 0.7.5rc155. Klein-4 HDC similarity (srmech-native); edit distance pure-Python (no abs); no CAD. Run from worktree root:
  /tmp/srmech_rc155/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-HALLUPROBE_misbinding_vs_abstention_calibration.py
"""
import importlib.util as U

_spec = U.spec_from_file_location("sgp", "docs/srmech/rbs_lm_research/R-RBS-LM-SIONAGENEPOOL_storyteller_etak_walk_over_genome_with_notebooks.py")
SGP = U.module_from_spec(_spec); _spec.loader.exec_module(SGP)
GENOME_DIR = "docs/srmech/rbs_lm_research/.siona_genepool"

# candidate input pools — verified against THIS genome at run time (routable? typo's canonical present?).
KNOWN_CANDS = ["tomato", "volcano", "computer", "music", "planet", "earth", "science", "water",
               "mountain", "animal", "country", "language", "history", "ocean", "island"]
# near-miss: (typo, intended_canonical) — typos preserve the 2-char prefix (so the canonical is in the resolver bucket).
NEARMISS_CANDS = [("tomatto", "tomato"), ("volcanoe", "volcano"), ("computre", "computer"), ("muisc", "music"),
                  ("planit", "planet"), ("earht", "earth"), ("scince", "science"), ("watter", "water"),
                  ("mountian", "mountain"), ("contry", "country"), ("histroy", "history"), ("islnd", "island"),
                  ("languag", "language"), ("oceann", "ocean"), ("anmal", "animal")]
# genuinely-unknown: rare REAL English words (filtered at run time to those NOT routable but force-comprehensible).
UNKNOWN_CANDS = ["flibbertigibbet", "perspicacious", "defenestration", "sesquipedalian", "borborygmus",
                 "callipygian", "eleemosynary", "pusillanimous", "grandiloquent", "obstreperous",
                 "mellifluous", "perfidious", "lugubrious", "rambunctious", "cantankerous",
                 "persnickety", "discombobulate", "absquatulate", "bamboozle", "kerfuffle"]

FLOORS = [0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70]
RATIOS = [0.50, 0.35, 0.25, 0.15]          # edit_distance / len(word) acceptance ceiling (lower = stricter)


def main():
    print(f"=== R-RBS-LM-HALLUPROBE — misbinding vs abstention calibration (srmech {SGP.srmech.__version__}) ===\n")
    W = SGP.SionaGenepool(GENOME_DIR)
    hdc, ed = SGP.hdc, SGP.SionaGenepool._edit_distance

    # resolve each word ONCE (floor=0 -> the true top candidate), record (top, sim, edit, len)
    def probe(w):
        ab = W._abstract_resolve(w, floor=0.0)
        if not ab:
            return None
        c, s = ab
        return {"w": w, "top": c, "sim": s, "edit": ed(w, c), "len": len(w)}

    known = [w for w in KNOWN_CANDS if W._routable(w)]
    near = [(t, c, probe(t)) for t, c in NEARMISS_CANDS if W._routable(c) and not W._routable(t)]
    near = [(t, c, p) for t, c, p in near if p]                      # must force-comprehend to something
    unknown = [(w, probe(w)) for w in UNKNOWN_CANDS if not W._routable(w)]
    unknown = [(w, p) for w, p in unknown if p]                      # force-comprehensible -> the dangerous case

    print(f"input classes (verified vs this genome): known={len(known)}  near-miss={len(near)}  unknown={len(unknown)}\n")
    print("near-miss resolutions (top candidate, sim, edit-distance):")
    for t, c, p in near:
        flag = "→correct" if p["top"] == c else f"→MISBIND({p['top']})"
        print(f"  {t:10}→{c:9} got {p['top']:10} sim={p['sim']:.2f} edit={p['edit']} {flag}")
    print("\nunknown resolutions (the misbinding hazard):")
    for w, p in unknown:
        print(f"  {w:16} → {p['top']:12} sim={p['sim']:.2f} edit={p['edit']} (edit/len={p['edit']/p['len']:.2f})")

    def accept(p, floor, ratio):
        return p["sim"] >= floor and p["edit"] <= ratio * p["len"]

    print("\n=== CALIBRATION GRID: near-miss CORRECT% / unknown MISBIND% (want high / ~0) ===")
    header = "FLOOR\\RATIO  " + "  ".join(f"{r:>14.2f}" for r in RATIOS)
    print(header)
    best = None
    for f in FLOORS:
        cells = []
        for r in RATIOS:
            nm_correct = sum(1 for _t, c, p in near if accept(p, f, r) and p["top"] == c)
            nm_misbind = sum(1 for _t, c, p in near if accept(p, f, r) and p["top"] != c)
            uk_misbind = sum(1 for _w, p in unknown if accept(p, f, r))
            corr_pct = 100.0 * nm_correct / max(1, len(near))
            uk_pct = 100.0 * uk_misbind / max(1, len(unknown))
            cells.append(f"{corr_pct:5.0f}/{uk_pct:<4.0f}(mb{nm_misbind})")
            # "best" = maximise near-miss correct subject to zero unknown-misbind (and zero near-miss-misbind)
            score = (uk_misbind == 0 and nm_misbind == 0, nm_correct, -f)
            if best is None or score > best[0]:
                best = (score, f, r, nm_correct, nm_misbind, uk_misbind)
        print(f"  {f:.2f}     " + "  ".join(f"{c:>14}" for c in cells))
    print("  (cell = near-miss CORRECT% / unknown MISBIND% (mb = near-miss mis-resolutions))")

    _, bf, br, bnc, bnm, buk = best
    print(f"\nBEST clean cell: FLOOR={bf:.2f} RATIO={br:.2f} -> near-miss correct {bnc}/{len(near)} "
          f"({100*bnc/max(1,len(near)):.0f}%), near-miss misbind {bnm}, unknown misbind {buk}.")
    print(f"current live gate (F765): FLOOR=0.45, RATIO≈0.33 (edit<=max(2,len//3)).")
    print("\nVERDICT (read the grid): if a cell reaches high near-miss-correct WITH unknown-misbind=0, misbinding is")
    print("SUPPRESSIBLE by calibrated abstention -> the honest claim 'no confabulation; misbinding gated by abstention'")
    print("holds. If raising the gate zeroes unknown-misbind only by also collapsing near-miss-correct, the tradeoff is")
    print("inherent (a precision/coverage frontier), and the claim must name where on the frontier we sit.")


if __name__ == "__main__":
    main()
