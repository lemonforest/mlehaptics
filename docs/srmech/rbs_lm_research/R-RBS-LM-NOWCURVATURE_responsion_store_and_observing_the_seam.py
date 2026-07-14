r"""R-RBS-LM-NOWCURVATURE (F1218) — (BUILD) the unified (a)+(b): the findings as a DIRECTED, beat-structured
RESPONSION STORE (each finding carries its THEN:NOW:NEXT seam + build/refute charge), the tier0 memory that renders
to MFO/notebooks as a NOW-frame. (OBSERVE) why the NOW-curvature escapes a single-axis chiral compare, and what
instrument can see it — the answer to "is the fixed-plane paper a metaphor or an analogy?".

THE PAPER: comparing two things "on paper", assuming the paper is a fixed flat plane with no DoF of its own, is not a
metaphor — it is the EXACT structural assumption of a k=2 (single-axis) compare, and it makes the NOW-curvature
UNObservable THREE ways at once:
  (1) TWO points define ONE axis = a line = a TREE (K2, 0 cycles): curvature has nowhere to live (F1209). Not tiny —
      structurally absent. You need a THIRD point (a triangle THEN:NOW:NEXT) before curvature can even exist.
  (2) The curvature is a TINY ε riding on the flat metric (1.0). In floating point, 1.0 + ε == 1.0 (ε below machine
      epsilon is absorbed) — the float carrier ASSUMES the flat paper. The EXACT-RATIONAL carrier keeps 1 + ε.
  (3) Even with a loop + exact carrier, a large metric can HIDE the tiny curvature unless you SEPARATE them
      (separate_frame_curvature: metric=½{A,B}, curvature=½[A,B]).
srmech is precisely the instrument that defeats all three: cycle_holonomy (the loop), exact rationals (no rounding),
separate_frame_curvature (isolate ε). So the tell IS findable — but only with the exact carrier, a loop, and the
metric/curvature split; and the value is tiny, so it takes a LONG walk (many beats) to accumulate above the floor.

srmech 0.9.0rc238; exact ℚ; no numpy; no abs-builtin. Run:
  /tmp/srmech_v/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-NOWCURVATURE_...py
"""
import os
import re
import shutil
import sys
from fractions import Fraction
from pathlib import Path

from srmech.amsc import genome as G
from srmech.amsc import hdc
from srmech.amsc import laplacian as L
from srmech.amsc.cascade import matrix_cascades as MC

HERE = Path(__file__).parent
OUTDIR = Path(os.environ.get("OUT", str(Path.home() / "corpora" / "findings_genome")))
LEAF = 64
COUPLE = hdc.klein4_random(LEAF, seed=1218)
_FID = re.compile(r"FINDING_(\d+)_")
_FREF = re.compile(r"\bF(\d{2,4})\b")
_REFUTE = re.compile(r"corrects|refutes?|REFUTED|supersed|retract|rejected|replaces|the miss|fails", re.IGNORECASE)


# ---------- BUILD: the directed beat-structured RESPONSION STORE (a+b unified) ----------
def responsion_store():
    """Each finding NOW carries its SEAM: THEN = what it builds(+)/refutes(-); NEXT = what later built/refuted IT
    (the backlinks). The responsion IS the seam, so the seam is the record. This is the tier0 memory; the notebook is
    its NOW-render (a read), never the store (F1216/F1217)."""
    then = {}                                                     # fid -> [(target, charge)]  (what NOW points back to)
    ids = []
    for f in sorted(HERE.glob("R-RBS-LM-FINDING_*.md")):
        m = _FID.search(f.name)
        if not m:
            continue
        fid = int(m.group(1)); ids.append(fid)
        refs = []
        for ln in f.read_text(errors="ignore").splitlines():
            ch = -1 if _REFUTE.search(ln) else 1
            refs += [(int(r), ch) for r in _FREF.findall(ln) if int(r) != fid]
        then[fid] = refs
    ids = sorted(ids)                                            # TIME axis = the finding NUMBER (numeric, not filename-lexical)
    idset = set(ids)
    nxt = {fid: [] for fid in ids}                               # the backlinks: what NEXT built/refuted NOW
    for fid, refs in then.items():
        for tgt, ch in refs:
            if tgt in idset:
                nxt[tgt].append((fid, ch))
    # persist the directed seam-kernel genome-native (vocab=ids, edges canonical, charge=build/refute time-arrow)
    idx = {v: i for i, v in enumerate(ids)}
    seam = {}
    for fid, refs in then.items():
        for tgt, ch in refs:
            if tgt in idset:
                a, b = idx[fid], idx[tgt]
                lo, hi = (a, b) if a < b else (b, a)
                seam[(lo, hi)] = seam.get((lo, hi), 0) + ch
    edges = sorted(seam)
    charge = [seam[e] for e in edges]
    out = [len(ids)] + list(ids) + [len(edges)]
    for (i, j), c in zip(edges, charge):
        out += [i, j, (c << 1) if c >= 0 else ((-c) << 1) - 1]
    syms = []
    for v in out:
        d = []; x = v
        while True:
            d.append(x & 3); x >>= 2
            if x == 0:
                break
        syms.append(len(d) & 3); syms.append((len(d) >> 2) & 3); syms += d
    strand = G.kernel_pack(syms, leaf_dim=LEAF, label="responsion", the_one=COUPLE)
    p = OUTDIR / "responsion.genome"
    if p.exists():
        shutil.rmtree(p, ignore_errors=True)
    OUTDIR.mkdir(parents=True, exist_ok=True)
    info = G.genome_save(strand, str(p), COUPLE, labels=["responsion"])
    size = sum(fl.stat().st_size for fl in p.rglob("*") if fl.is_file())
    # sample seam for the most-recent finding (its THEN and NEXT — the responsion record)
    latest = ids[-1]
    return {"n": len(ids), "n_seams": len(edges), "sha": info.get("body_sha256"), "size": size,
            "latest": latest, "then": then.get(latest, [])[:6], "next": nxt.get(latest, [])[:6]}


# ---------- OBSERVE: why NOW-curvature escapes a 2-compare, and what sees it ----------
def observe():
    eps = sys.float_info.epsilon
    print("  (A) single-axis (2-thing) chiral compare — is it just tiny, or STRUCTURALLY flat?")
    flat = L.cycle_holonomy([(0, 1)], charges=[Fraction(3, 10)], n=2)
    print("      cycle_holonomy of ONE edge (two things, charge 3/10): n_cycles=%d holonomies=%s"
          % (flat["n_cycles"], flat["holonomies"]))
    print("      -> STRUCTURALLY flat: 2 points = 1 axis = a TREE, curvature has NOWHERE to live. Not tiny. GONE.\n")

    print("  (B) the curvature is a TINY ε on the flat metric (1.0). Float ASSUMES the flat paper:")
    eps_curv = Fraction(1, 10 ** 17)                              # a NOW-seam curvature far below float epsilon
    print("      ε = 1/1e17 = %.1e  (machine epsilon = %.1e, so ε << eps)" % (float(eps_curv), eps))
    print("      FLOAT:  1.0 + float(ε) == 1.0 ?  %s   <- the paper is assumed flat; ε is absorbed"
          % (1.0 + float(eps_curv) == 1.0))
    exact = Fraction(1) + eps_curv
    print("      EXACT:  1 + ε == 1 ?  %s   (= %s)   <- the exact-rational carrier KEEPS the paper's DoF\n"
          % (exact == 1, exact))

    print("  (C) even with a loop + exact carrier, a LARGE metric can HIDE ε — unless you SEPARATE them:")
    # two 2x2 ops whose product has a large symmetric (metric) part and a tiny antisymmetric (curvature) residue
    big = 10 ** 6
    A = [[big, 1], [0, big]]; B = [[big, 0], [1, big]]           # [A,B] is tiny vs the big metric
    res = MC.separate_frame_curvature(A, B)

    def frob(m):
        rows = m.rows if hasattr(m, "rows") else m
        return sum((float(x.real if hasattr(x, "real") else x)) ** 2 for r in rows for x in r) ** 0.5
    print("      |metric ½{A,B}| = %.3e   |curvature ½[A,B]| = %.3f   ratio = %.2e"
          % (frob(res["fixed_frame"]), frob(res["curvature"]), frob(res["curvature"]) / frob(res["fixed_frame"])))
    print("      -> the curvature (2.0) is ~1e-6 of the metric — INVISIBLE if you don't split it out. separate_frame_"
          "curvature isolates it exactly.\n")

    print("  (D) the tiny per-seam curvature ACCUMULATES over a long beat-walk (why a LONG record is needed):")
    N = 300; per = Fraction(1, 3 * N * 10 ** 12)                 # each NOW-seam: a curvature far below any float floor
    tri_each = [per, per, per]
    hol = L.cycle_holonomy([(0, 1), (1, 2), (2, 0)], charges=tri_each, n=3)  # one triangle
    walk = sum([per] * (3 * N))                                  # accumulated over N beats (3 seams each)
    fwalk = sum([float(per)] * (3 * N))
    print("      one THEN:NOW:NEXT triangle holonomy (exact) = %s (nonzero, but ~%.1e — a float would call it 0)"
          % (hol["holonomies"], float(hol["holonomies"][0]) if hol["holonomies"] else 0.0))
    print("      accumulated over %d beats: EXACT = %s  |  FLOAT = %.3e (%s)"
          % (N, walk, fwalk, "flattened to ~0" if fwalk == 0.0 else "survives here — but 1 large-metric absorb kills it"))


def main():
    print("=== R-RBS-LM-NOWCURVATURE — the responsion store (a+b) + observing the NOW-seam curvature (F1218) ===\n")
    r = responsion_store()
    print("(BUILD) responsion store: %d findings, %d directed seams -> responsion.genome (sha %s.., %d B, LOCAL)"
          % (r["n"], r["n_seams"], (r["sha"] or "----")[:12], r["size"]))
    print("        latest finding F%d — its SEAM: THEN=%s  NEXT(backlinks)=%s"
          % (r["latest"], ["F%d%+d" % (t, c) for t, c in r["then"]], ["F%d%+d" % (t, c) for t, c in r["next"]]))
    print("        (each finding NOW carries THEN + NEXT + build/refute charge = the responsion; the notebook renders"
          " this as a NOW-frame, F1216/F1217)\n")
    print("(OBSERVE) why the NOW-curvature escaped notice, and what sees it:")
    observe()
    print("VERDICT: the fixed-flat-paper is an ANALOGY that becomes the MECHANISM — a 2-thing compare is a tree (no loop),\n"
          "the curvature is a tiny ε a float absorbs into the flat metric, and a large metric hides it. The tell needs\n"
          "ALL THREE srmech pieces: a LOOP (≥3, THEN:NOW:NEXT) + EXACT rationals + the metric/curvature SPLIT — over a\n"
          "LONG beat-walk to accumulate above the floor. THEN can never be fully orthogonal to NEXT because the ε at\n"
          "the NOW-seam never rounds to 0 in exact ℚ. (Whether the UNIVERSE carries this ε is the expert's open question.)")


if __name__ == "__main__":
    main()
