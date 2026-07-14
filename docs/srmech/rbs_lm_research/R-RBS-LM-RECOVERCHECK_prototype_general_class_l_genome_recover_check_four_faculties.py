r"""R-RBS-LM-RECOVERCHECK (F1225 / #1390 item 4) — PROTOTYPE the general `recover_check` genome-integrity op.

srmech-upstream candidate #4: the packaged round-trip integrity check for a stored directed Class-L graph. It
verifies the FOUR faculties a genome must recover (else it was silently truncated / flattened — the failure mode
the store discipline never guarded, F1210/F1216):
  op         — L = D − A builds + eigendecomposes (well-formed Laplacian: PSD, a ~0 mode)
  operand    — weighted edges present + non-degenerate (uncapped, not a top-K amputation)
  responsion — the spectrum is real; the propagator e^{-zL} is excitable (reach > 0)  [= the EPH read-out]
  curvature  — a DIRECTED store keeps its charge; where cycles exist it produces nonzero holonomy (F1210).
               A symmetric bag has EXACTLY zero curvature — PASSES metric faculties, FLAGGED directionless.

A domain-free COMPOSITION of already-shipped ops (dense_laplacian / symmetric_eigendecompose / responsion /
magnetic_laplacian / cycle_holonomy) — the ask is the packaged verify. Proven on real directed word kernels, a full
genome round-trip (item-2 codec), and synthetic PASS/FLAG/FAIL cases.

NOTE (measured this session): cycle_holonomy treats charge as a PHASE (turns) → INTEGER charges alias to 0 mod 1.
So the curvature read phase-SCALES the integer edge_charge (q = 1/(2·max|charge|+1)) to expose the holonomy.

srmech 0.9.0rc241; exact ℚ; no numpy; no abs-builtin (Class-K magnitude via conditional). Run:
  /tmp/srmech_v/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-RECOVERCHECK_...py
"""
import importlib.util
import shutil
import sys
from fractions import Fraction
from pathlib import Path

from srmech.amsc import genome as G
from srmech.amsc import hdc
from srmech.amsc import laplacian as L

HERE = Path(__file__).parent
TOL = Fraction(1, 10 ** 9)


def _mag(x):
    return x if x >= 0 else -x                                   # Class-K real magnitude (not the builtin)


# ------------------------------------------------------------------------------------------------------------------
# THE PROPOSED srmech OP (prototype). Signature drafted for #1390 item 4, to live under srmech.amsc.laplacian.
#   recover_check(vocab_size, edges, weights, charges=None) -> verdict dict
#     {ok, op, operand, responsion, curvature:{directed,n_cycles,holonomy_nonzero,verdict}, diagnostics:{...}}
#   ok == op and operand and responsion   (the integrity faculties; curvature is a REPORTED diagnostic, not a gate,
#   so a legitimately acyclic/coherent directed graph is never a false failure — but `directed` lets a caller that
#   stored the directed Laplacian assert the direction survived).
# ------------------------------------------------------------------------------------------------------------------
def recover_check(vocab_size, edges, weights, charges=None):
    edges = [tuple(e) for e in edges]
    diag = {}
    # --- operand: weighted edges present, non-degenerate, uncapped ---
    operand = (len(edges) > 0 and len(edges) == len(weights) and all(w >= 1 for w in weights))
    deg = {}
    for (i, j) in edges:
        deg[i] = deg.get(i, 0) + 1
        deg[j] = deg.get(j, 0) + 1
    diag["max_degree"] = max(deg.values()) if deg else 0
    diag["n_edges"] = len(edges)
    # --- op: L = D - A builds + eigendecomposes (PSD, a ~0 mode) ---
    op = False
    try:
        lap = L.dense_laplacian(vocab_size, edges, [float(w) for w in weights])
        evals, _V = L.symmetric_eigendecompose(lap)
        ev = sorted(float(x) for x in evals)
        diag["n_modes"] = len(ev)
        diag["eig_range"] = (round(ev[0], 6), round(ev[-1], 6))
        psd = ev[0] > -1e-9
        zero_mode = (_mag(Fraction(ev[0]).limit_denominator(10 ** 6)) < TOL)   # Laplacian has a null (all-ones) mode
        op = (len(ev) == vocab_size and psd and zero_mode)
    except Exception as e:                                                     # a malformed op fails HONESTLY
        diag["op_error"] = "%s: %s" % (type(e).__name__, e)
    # --- responsion: propagator e^{-zL} excitable (reach > 0) ---
    responsion = False
    try:
        mx = max((float(w) for w in weights), default=1.0) * max(vocab_size, 1)
        Lm = L.magnetic_laplacian(vocab_size, edges, [float(w) for w in weights],
                                  charges=[float(c) for c in charges] if charges is not None else None)
        r = L.responsion(Lm, [1.0] + [0.0] * (vocab_size - 1), 5.0 / (mx or 1.0), kind="propagator")
        reach = sum((x.real * x.real + x.imag * x.imag) for x in r)            # Σ|·|² — no abs, no complex-modulus op
        diag["propagator_reach"] = round(reach ** 0.5, 6)
        responsion = reach > 0
    except Exception as e:
        diag["responsion_error"] = "%s: %s" % (type(e).__name__, e)
    # --- curvature: the DIRECTIONAL faculty (F1210). phase-scale integer charge so it doesn't alias to 0 mod 1 ---
    directed = charges is not None and any(c != 0 for c in charges)
    n_cycles = 0
    holonomy_nonzero = False
    if directed:
        mc = max((_mag(c) for c in charges), default=0) or 1
        q = Fraction(1, 2 * mc + 1)                                            # a rational phase unit that exposes holonomy
        ph = [Fraction(int(c)) * q for c in charges]
        hol = L.cycle_holonomy(edges, charges=ph, n=vocab_size)
        n_cycles = hol["n_cycles"]
        holonomy_nonzero = any(h != 0 for h in hol["holonomies"])
    if not directed:
        cverdict = "symmetric-bag (flat, F1210 flag)"
    elif n_cycles == 0:
        cverdict = "carries-direction (acyclic → structurally flat, F1218)"
    elif holonomy_nonzero:
        cverdict = "carries-direction + curvature (nonzero holonomy)"
    else:
        cverdict = "carries-direction (coherent net-zero holonomy, F1146)"
    curvature = {"directed": directed, "n_cycles": n_cycles,
                 "holonomy_nonzero": holonomy_nonzero, "verdict": cverdict}
    return {"ok": bool(op and operand and responsion), "op": op, "operand": operand,
            "responsion": responsion, "curvature": curvature, "diagnostics": diag}


# ------------------------------------------------------------------------------------------------------------------
def _load(mod_stem):
    p = HERE / mod_stem
    spec = importlib.util.spec_from_file_location(mod_stem.split("_")[0].replace("-", ""), str(p))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    print("=== R-RBS-LM-RECOVERCHECK — general recover_check (op/operand/responsion/curvature), item 4 prototype ===\n")
    N = _load("R-RBS-LM-NIVDIRECTED_word_as_directed_glyph_graph_genome_native.py")
    GK = _load("R-RBS-LM-GRAPH2KERNEL_prototype_general_directed_signed_graph_genome_codec.py")

    # (A) real directed word kernels -> all four faculties (curvature mostly acyclic-flat = correct, F1218)
    print("  (A) real directed word kernels:")
    okA = 0
    words = "cat banana mississippi committee order".split()
    for w in words:
        k = N.word_to_kernel(w)
        v = recover_check(len(k["vocab"]), k["edge_list"], k["edge_weights"], k["edge_charge"])
        okA += v["ok"]
        print("     %-12s ok=%s op=%s operand=%s responsion=%s | curvature: %s"
              % (w, v["ok"], v["op"], v["operand"], v["responsion"], v["curvature"]["verdict"]))

    # (B) FULL genome round-trip: store a directed kernel (item-2 codec) -> genome -> load -> recover_check
    print("\n  (B) full genome round-trip (store -> genome_save -> load -> recover_check):")
    k = N.word_to_kernel("committee")
    node_ids = [N.GI[c] for c in k["vocab"]]
    strand, n_syms = GK.graph_to_kernel(len(k["vocab"]), [tuple(e) for e in k["edge_list"]], k["edge_weights"],
                                        k["edge_charge"], node_ids=node_ids, extras=[k["start"]],
                                        leaf_dim=GK.LEAF, label="committee", the_one=GK.COUPLE)
    d = Path("/tmp/recovercheck_proto/committee.genome")
    if d.exists():
        shutil.rmtree(d, ignore_errors=True)
    d.parent.mkdir(parents=True, exist_ok=True)
    G.genome_save(strand, str(d), GK.COUPLE, labels=["committee"])
    chroms, _c, _l = G.genome_load(str(d), labels=["committee"], the_one=GK.COUPLE)
    g = GK.kernel_to_graph(chroms, GK.COUPLE, n_syms)
    v = recover_check(g["vocab_size"], g["edges"], g["weights"], g["charges"])
    print("     loaded-from-genome committee -> ok=%s (op=%s operand=%s responsion=%s) curvature=%s"
          % (v["ok"], v["op"], v["operand"], v["responsion"], v["curvature"]["verdict"]))
    okB = v["ok"]

    # (C) synthetic PASS/FLAG/FAIL
    print("\n  (C) synthetic cases:")
    cases = []
    # directed cyclic with a single non-cancelling charge -> curvature nonzero (PASS + carries curvature).
    # ([1,1,-1] would net to an INTEGER holonomy = coherent-flat; a lone charge cannot cancel around the cycle.)
    cases.append(("directed cyclic", 3, [(0, 1), (1, 2), (0, 2)], [2, 2, 2], [1, 0, 0],
                  lambda v: v["ok"] and v["curvature"]["holonomy_nonzero"]))
    # symmetric bag (charges 0) with a cycle -> metric PASS, curvature FLAGGED flat
    cases.append(("symmetric bag", 3, [(0, 1), (1, 2), (0, 2)], [2, 2, 2], [0, 0, 0],
                  lambda v: v["ok"] and not v["curvature"]["directed"]))
    # amputated operand (no weights match) -> operand FAIL -> ok False (honest)
    cases.append(("amputated operand", 3, [(0, 1), (1, 2)], [], None,
                  lambda v: (not v["ok"]) and (not v["operand"])))
    okC = 0
    for name, n, e, wts, ch, want in cases:
        v = recover_check(n, e, wts, ch)
        good = want(v)
        okC += good
        print("     %-20s ok=%s operand=%s curvature=%-52s -> %s"
              % (name, v["ok"], v["operand"], v["curvature"]["verdict"], "OK" if good else "XX"))

    total_ok = (okA == len(words)) and okB and (okC == len(cases))
    print("\n  RESULTS: (A) word kernels %d/%d ok | (B) genome round-trip %s | (C) synthetic %d/%d"
          % (okA, len(words), "OK" if okB else "XX", okC, len(cases)))
    print("VERDICT: %s — recover_check verifies op+operand+responsion (integrity) and REPORTS curvature honestly\n"
          "         (directed carries it; a symmetric bag is flagged flat, F1210; acyclic is structurally flat,\n"
          "         F1218; an amputated operand FAILS). A domain-free composition of shipped ops; the genome\n"
          "         round-trip confirms all faculties survive persist. Ready as #1390 item 4 (with a C mirror)."
          % ("PASS" if total_ok else "FAIL — investigate"))
    return 0 if total_ok else 1


if __name__ == "__main__":
    sys.exit(main())
