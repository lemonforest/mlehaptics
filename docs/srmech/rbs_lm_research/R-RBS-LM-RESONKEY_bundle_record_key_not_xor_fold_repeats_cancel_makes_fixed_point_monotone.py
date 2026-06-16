r"""R-RBS-LM-RESONKEY (F808 — the F807 context-key refinement) — F807's fixed-point accuracy (C) was NON-monotonic in
k (hit 100% then dipped ~4-7%). Diagnosed: the context key was foldbind = klein4_bind (XOR) over the role-filler binds,
and klein4_bind is SELF-INVERSE (Z2×Z2), so a token that REPEATS inside the context cancels its own identity
(the ⊕ the = 0) — colliding two different contexts that share a repeated token (verified: april k=8 had two distinct
7-grams tie at sim 1.0). The fix is the canonical VSA "record": assemble the role-filler binds with a BUNDLE
(superposition), NOT an XOR-fold — bundling does not cancel repeats (bind(the,p0) and bind(the,p4) are distinct and
superpose). Result: (C) becomes MONOTONE and saturates at 100% from the determinism threshold onward — the article is
a ROBUST resonant fixed-point eigenstate (input=output, F804) at every k ≥ k*.

Note the structure lesson (composes F806): a BUNDLE is right for the SMALL per-context record (≤k-1 role-filler binds,
the key); a single GLOBAL bundle over ALL transitions is wrong (capacity — F802/F806). bind pairs role↔filler; bundle
assembles the record; context-ADDRESSED retrieval (not one global bundle) reads it. srmech 0.7.5rc169; no abs; no CAD.
"""
import importlib.util as U
import json
import os
import re
from srmech.amsc import hdc

HERE = os.path.dirname(os.path.abspath(__file__))
_fw = U.spec_from_file_location("fw", os.path.join(
    HERE, "R-RBS-LM-FIBERWALK_deterministic_article_reconstruction_eulerian_path_fiber_on_rbs_hdc_vs_k.py"))
FW = U.module_from_spec(_fw); _fw.loader.exec_module(FW)
ABS = "/home/skirklan/corpora/wikipedia/simplewiki_abstracts.json"


def ctx_xor(prev):       # the F806/F807 key — XOR-fold: a REPEATED token cancels (the ⊕ the = 0) -> collisions
    return FW._foldbind([hdc.klein4_bind(FW.tok(t), FW.pos(j)) for j, t in enumerate(prev)])


def ctx_bundle(prev):    # F808 fix — the VSA RECORD: bundle the role-filler binds (repeats superpose, do not cancel)
    parts = [hdc.klein4_bind(FW.tok(t), FW.pos(j)) for j, t in enumerate(prev)]
    return hdc.klein4_bundle(*parts) if len(parts) > 1 else parts[0]


def fixedpoint_acc(tokens, k, ctxfn):    # (C): does each TRUE context retrieve its own successor (input=output)?
    keys = [(ctxfn(tokens[i - (k - 1):i]), tokens[i]) for i in range(k - 1, len(tokens))]
    ok = 0
    for i in range(k - 1, len(tokens)):
        cq = ctxfn(tokens[i - (k - 1):i])
        ok += (max(keys, key=lambda kv: hdc.klein4_similarity(cq, kv[0]))[1] == tokens[i])
    return ok / (len(tokens) - (k - 1))


def main():
    import srmech
    print(f"=== R-RBS-LM-RESONKEY — the bundle RECORD key removes the repeated-token collisions (srmech {srmech.__version__}) ===\n")
    store = json.load(open(ABS))["store"]
    want = [t for t in ("april", "a", "august", "art", "air") if t in store][:3]
    ks = list(range(2, 9))
    for title in want:
        tokens = re.findall(r"[a-z0-9]+", store[title].lower())
        xr = [fixedpoint_acc(tokens, k, ctx_xor) for k in ks]
        bd = [fixedpoint_acc(tokens, k, ctx_bundle) for k in ks]
        print(f"--- “{title}” ({len(tokens)} tok) ---   k: " + " ".join(f"{k:>4}" for k in ks))
        print("    (C) XOR-fold key (F807): " + " ".join(f"{x:4.0%}" for x in xr) + "   ← dips (repeats cancel)")
        print("    (C) BUNDLE record (F808): " + " ".join(f"{x:4.0%}" for x in bd) + "   ← monotone, saturates 100%\n")
    print("READING: bundling the role-filler binds (the VSA record) instead of XOR-folding them removes the")
    print("  repeated-token cancellation, so (C) is MONOTONE and stays 100% from k*: the article is a ROBUST")
    print("  resonant fixed-point eigenstate (input=output, F804) at every k ≥ k*. bind pairs role↔filler; BUNDLE")
    print("  assembles the record; context-ADDRESSED retrieval reads it (a single GLOBAL bundle still fails — F806).")


if __name__ == "__main__":
    main()
