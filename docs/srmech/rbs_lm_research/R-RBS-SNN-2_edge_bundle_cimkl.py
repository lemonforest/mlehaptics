#!/usr/bin/env python3
"""R-RBS-SNN-2 — stage 2 of the #197 build: the C·I·M·K·L edge bundle (F326 #1).

Stage 1 (F426) gave a graph of bare adjacencies. Stage 2 makes each coupling a
COMPOSITE memcapacitive object — the relationship is the primary thing, not the node:

  C  direction      sign(src_num − tgt_num): + builds-on (younger→older), − backlink
  I  cyclic lag τ   |Δfinding-number| = the research-time RC constant (Class I)
  M  transduction   hdc.bind(sig_src, sig_tgt) = the A-N classes the edge BRIDGES (xor)
  K  plastic gate   +1 reinforcing (composes/extends) | −1 corrective (corrects/supersedes/
                    refines/falsifies/retracts) — the LTP/LTD sign-switch (F319)
  L  weight/conduct mention-count of tgt in src = the coupling conductance

srmech-first: M = hdc.bind (Class M, byte-xor); K-sign = Class-K pin (never abs());
I = Class-I cyclic lag. No new A-N class. Defensive / no-lineage.

Run:  <clean-venv>/bin/python R-RBS-SNN-2_edge_bundle_cimkl.py   (numpy-free OK)
"""
import re
import glob
import os
from collections import Counter, defaultdict
from srmech.amsc import hdc

HERE = os.path.dirname(os.path.abspath(__file__))
CLASSES = "ABCDEFGHIJKLMN"
CORRECTIVE = re.compile(r'\b(correct|supersed|refin|falsif|retract|wrong|revis|overturn|rejected)', re.I)


def sig_bytes(sig):
    """14-byte one-hot of the operator-signature → the Class-M carrier."""
    return bytes(1 if CLASSES[i] in sig else 0 for i in range(14))


def parse():
    nodes, blob = {}, {}
    for path in sorted(glob.glob(os.path.join(HERE, "R-RBS-LM-FINDING_*.md"))):
        m = re.search(r'FINDING_(\d+)', os.path.basename(path))
        if not m:
            continue
        fid = int(m.group(1))
        text = open(path, encoding='utf-8').read()
        nodes[fid] = set(re.findall(r'Class[- ]([A-N])\b', text))
        blob[fid] = text
    return nodes, blob


def main():
    nodes, blob = parse()
    present = set(nodes)
    edges = []                      # (src, tgt, C, I, M_bytes, K, L)
    for src in nodes:
        text = blob[src]
        # count references to each other finding in src
        refs = Counter(int(r) for r in re.findall(r'\bF(\d{1,3})\b', text))
        for tgt, cnt in refs.items():
            if tgt == src or tgt not in present:
                continue
            C = 1 if src > tgt else -1                          # Class C: build-on vs backlink
            I = abs(src - tgt)                                  # Class I: cyclic lag τ
            M = hdc.bind(sig_bytes(nodes[src]), sig_bytes(nodes[tgt]))   # Class M transduction
            # K plastic sign: corrective if a corrective verb sits near the ref
            window = ' '.join(re.findall(rf'.{{0,60}}F0*{tgt}\b.{{0,40}}', text))
            K = -1 if CORRECTIVE.search(window) else 1          # Class K LTP/LTD gate
            Lw = cnt                                            # Class L weight/conductance
            edges.append((src, tgt, C, I, M, K, Lw))

    # ---- aggregate the bundle ----
    nK_plus = sum(1 for e in edges if e[5] == 1)
    nK_minus = sum(1 for e in edges if e[5] == -1)
    nC_build = sum(1 for e in edges if e[2] == 1)
    nC_back = sum(1 for e in edges if e[2] == -1)
    Ldist = Counter(e[6] for e in edges)
    Ibar = sum(e[3] for e in edges) / len(edges)
    # M: which class-pairs the edges bridge most (popcount of the bind = #classes bridged)
    bridge = Counter()
    for e in edges:
        nbits = sum(bin(b).count('1') for b in e[4])
        bridge[nbits] += 1

    print("=== RBS-SNN stage 2 — the C·I·M·K·L edge bundle ===")
    print(f"directed coupling-bundles: {len(edges)}")
    print(f"\nC (direction): build-on {nC_build} | backlink {nC_back}")
    print(f"K (plastic gate): reinforcing(+) {nK_plus} | CORRECTIVE(−) {nK_minus}"
          f"  ({100*nK_minus/len(edges):.1f}% corrective — the LTP/LTD asymmetry)")
    print(f"I (cyclic lag τ): mean = {Ibar:.1f} findings  (research-time RC constant)")
    print(f"L (conductance): " + " ".join(f"w{w}×{c}" for w, c in sorted(Ldist.items())[:6])
          + (" ..." if len(Ldist) > 6 else ""))
    print(f"M (transduction): #classes an edge bridges (popcount of bind) — "
          + " ".join(f"{k}cls×{v}" for k, v in sorted(bridge.items())))

    # ---- sample bundles (the rich edge objects) ----
    print("\nsample edge bundles (src→tgt :: C I M-bridge K L):")
    def bridged(mb): return ''.join(CLASSES[i] for i in range(14) if mb[i])
    for e in sorted(edges, key=lambda e: (e[5], -e[6]))[:4] + sorted(edges, key=lambda e: -e[6])[:4]:
        s, t, C, I, M, K, Lw = e
        arrow = "builds-on" if C == 1 else "backlink"
        gate = "REINFORCE+" if K == 1 else "CORRECT−"
        print(f"   F{s}→F{t} :: C={arrow:9} I=τ{I:<3} M=bridge[{bridged(M) or '∅'}] K={gate} L=w{Lw}")

    # ---- the corrective edges = the corpus's own self-corrections (feeds stage 3) ----
    corr = [(e[0], e[1]) for e in edges if e[5] == -1]
    print(f"\ncorrective (K=−) edges = the corpus's self-corrections ({len(corr)}): "
          + " ".join(f"F{s}→F{t}" for s, t in corr[:12]) + (" ..." if len(corr) > 12 else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
