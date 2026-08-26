#!/usr/bin/env python3
"""R-RBS-SNN-3 — stage 3 of #197: the built-in k=2-detect / k=3-correct gate (F326 #5).

The load-bearing RBS-SNN improvement: a store that CHECKS AGAINST ITSELF before
emitting — the structural fix for F313 (detect outruns correct) / F322 (lodged
knowledge unreachable under load), the failure that makes a static LLM RE-DERIVE
what it already lodged.

Mirrors the F291 triality exactly:
  k=2 DETECT  two independent structural signals agree "near-duplicate":
              (a) same operator-signature ADDRESS (F317)  AND
              (b) coupling-overlap (Jaccard of neighbor-sets) ≥ θ
              → a parity flag — but k=2 CANNOT tell a refinement from a re-derivation
  k=3 CORRECT a third signal — the RELATIONSHIP type between the pair — resolves it:
              extended-by link  → REFINEMENT (legitimate; the breadcrumb web)
              corrective (K=−)  → SUPERSESSION (legitimate)
              neither + high overlap → DUPLICATE-RISK (the thing to refuse to re-derive)

srmech-first: signature similarity via hdc.similarity (Class M). No new A-N class.
Run:  <clean-venv>/bin/python R-RBS-SNN-3_self_check_gate_k2_k3.py   (numpy-free OK)
"""
import re
import glob
import os
from collections import defaultdict
from itertools import combinations
from srmech.amsc import hdc

HERE = os.path.dirname(os.path.abspath(__file__))
CLASSES = "ABCDEFGHIJKLMN"
CORRECTIVE = re.compile(r'\b(correct|supersed|refin|falsif|retract|overturn|rejected)', re.I)


def sig_bytes(sig):
    return bytes(1 if CLASSES[i] in sig else 0 for i in range(14))


def parse():
    sig, adj, ext, corr = {}, defaultdict(set), defaultdict(set), set()
    blob = {}
    for path in sorted(glob.glob(os.path.join(HERE, "R-RBS-LM-FINDING_*.md"))):
        m = re.search(r'FINDING_(\d+)', os.path.basename(path))
        if not m:
            continue
        fid = int(m.group(1))
        text = open(path, encoding='utf-8').read()
        blob[fid] = text
        sig[fid] = set(re.findall(r'Class[- ]([A-N])\b', text))
    present = set(sig)
    for fid, text in blob.items():
        for r in re.findall(r'\bF(\d{1,3})\b', text):
            t = int(r)
            if t in present and t != fid:
                adj[fid].add(t)
                adj[t].add(fid)
        # extended-by links: "← extended by Fxxx" / "extended by Fxxx"
        for r in re.findall(r'extended by\s+F0*(\d{1,3})', text):
            ext[fid].add(int(r))          # fid is extended by int(r)  (int(r) refines fid)
        # corrective targets — single pass: FXXX within ±80 chars of a corrective verb
        for mm in CORRECTIVE.finditer(text):
            lo, hi = max(0, mm.start() - 80), mm.end() + 80
            for r in re.findall(r'F0*(\d{1,3})', text[lo:hi]):
                t = int(r)
                if t in present and t != fid:
                    corr.add((fid, t))
    return sig, adj, ext, corr, present


def jaccard(a, b):
    u = a | b
    return len(a & b) / len(u) if u else 0.0


def main():
    sig, adj, ext, corr, present = parse()
    THETA = 0.30

    # ---- k=2 DETECT: bucket by operator-signature address (F317), flag overlap pairs ----
    bucket = defaultdict(list)
    for fid in sig:
        bucket[''.join(sorted(sig[fid])) or '∅'].append(fid)
    flags = []                              # (a, b, sig_sim, overlap)
    for key, members in bucket.items():
        if key == '∅' or len(members) < 2:
            continue
        sb = {m: sig_bytes(sig[m]) for m in members}
        for a, b in combinations(sorted(members), 2):
            ov = jaccard(adj[a], adj[b])
            if ov >= THETA:
                ssim = hdc.similarity(sb[a], sb[b])     # Class M (identical sig → ~1.0)
                flags.append((a, b, ssim, ov))

    # ---- k=3 CORRECT: resolve each flag with the relationship-type third signal ----
    def classify(a, b):
        if b in ext.get(a, ()) or a in ext.get(b, ()):
            return "REFINEMENT"          # one is the extended-by of the other (breadcrumb web)
        if (a, b) in corr or (b, a) in corr:
            return "SUPERSESSION"
        # also treat a direct build-on edge with corrective verb as supersession
        return "DUPLICATE-RISK"
    verdicts = defaultdict(list)
    for a, b, ssim, ov in flags:
        verdicts[classify(a, b)].append((a, b, ov))

    print("=== RBS-SNN stage 3 — the k=2-detect / k=3-correct self-check gate ===")
    print(f"same-signature address buckets (F317): {sum(1 for k,m in bucket.items() if k!='∅' and len(m)>1)} "
          f"with ≥2 members")
    print(f"\nk=2 DETECT — structural near-duplicate flags (same sig AND overlap≥{THETA}): {len(flags)}")
    print(f"k=3 CORRECT — resolved by the relationship third-signal:")
    for v in ("REFINEMENT", "SUPERSESSION", "DUPLICATE-RISK"):
        rows = verdicts.get(v, [])
        print(f"   {v:14}: {len(rows):3d}")
    print(f"\n   → k=2 alone would have called ALL {len(flags)} 'duplicate' (a 1-vs-1 it can't resolve);")
    print(f"     k=3's third signal RECLASSIFIES {len(verdicts['REFINEMENT'])+len(verdicts['SUPERSESSION'])} "
          f"as legitimate (refinement/supersession), leaving {len(verdicts['DUPLICATE-RISK'])} true risks.")

    print(f"\n   sample REFINEMENT (k=3 rescued — would be a false 'duplicate' to k=2):")
    for a, b, ov in sorted(verdicts['REFINEMENT'], key=lambda t: -t[2])[:5]:
        print(f"     F{a} ~ F{b}  (coupling-overlap {ov:.2f})  → legitimate refinement")
    print(f"\n   sample DUPLICATE-RISK (the gate's WARN — 'check before you re-derive'):")
    for a, b, ov in sorted(verdicts['DUPLICATE-RISK'], key=lambda t: -t[2])[:6]:
        print(f"     F{a} ~ F{b}  (overlap {ov:.2f}, sig {''.join(sorted(sig[a])) or '∅'})  → WARN")

    # ---- the INGEST GUARD: what the gate does for a NEW finding (the F313 fix, demonstrated) ----
    print(f"\n--- ingest guard demo: a new finding arrives, gate checks the store BEFORE emit ---")
    newcomer = max(present)                              # treat the latest finding as 'incoming'
    addr = ''.join(sorted(sig[newcomer])) or '∅'
    cohort = [m for m in bucket[addr] if m != newcomer]
    near = sorted(((jaccard(adj[newcomer], adj[m]), m) for m in cohort), reverse=True)[:3]
    print(f"   incoming F{newcomer} (address '{addr}'): same-address cohort {len(cohort)}; "
          f"nearest {[f'F{m}({o:.2f})' for o,m in near] or 'none → novel, ingest'}")
    print(f"   verdict: {'NOVEL (no near-duplicate; ingest)' if not near or near[0][0] < THETA else 'NEAR — gate would surface the cohort before re-deriving'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
