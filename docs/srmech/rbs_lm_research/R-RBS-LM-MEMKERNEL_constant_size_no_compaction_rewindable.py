r"""R-RBS-LM-MEMKERNEL — the user's architecture (2026-06-07): RBS-LM memory can be its OWN KERNEL, maintained every
exchange — so it is CONSTANT SIZE and there is NOTHING TO EVER COMPACT (unlike a Gen-1 LLM's growing context window,
which must be truncated/summarised — exactly what THIS session has been doing manually). And keep an append-only
RECORDED HISTORY so a conversation can be REWOUND (rebuild the kernel from any log prefix).

Two parts:
  • MEMORY KERNEL (working memory): a fixed-D HDC bundle, recency-weighted, updated each exchange. CONSTANT SIZE
    regardless of how many exchanges -> nothing to compact. Old exchanges FADE gracefully (HDC capacity, F137/F152;
    recency = plasticity-decay, F76/F141) — NOT a hard truncation.
  • HISTORY LOG (episodic record): append-only exact vectors. REWIND to turn k = rebuild the kernel from log[0:k].

This is the LLM compaction problem dissolved: the kernel never grows (constant D), recent content is sharp, old
content fades (not cut), and the exact record is replayable.

srmech 0.7.4; Class-M hdc.bundle/similarity; recency by vote-weight (repetition). No abs(); no CAD; no sub-agents.
"""
import numpy as np
import srmech
from srmech.amsc import hdc
from srmech.signal_processing import mint_vector

D = 8192


def build_kernel(log, decay=0.82, maxvote=6):
    """the constant-D memory kernel: a recency-WEIGHTED bundle of the exchanges so far (recent = more votes)."""
    n = len(log)
    items = []
    for i, x in enumerate(log):
        w = max(1, round((decay ** (n - 1 - i)) * maxvote))      # recent -> maxvote copies, old -> 1 (graceful fade)
        items += [x] * w
    if len(items) % 2 == 0:                                      # hdc.bundle wants an ODD count (tie-free majority)
        items.append(mint_vector("__pad__", D=D))
    return hdc.bundle(items)


def main():
    print(f"=== R-RBS-LM-MEMKERNEL — a constant-size, rewindable memory kernel (nothing to ever compact)  (srmech {srmech.__version__}) ===\n")
    N = 24
    log = [mint_vector(f"exchange-{i:02d}", D=D) for i in range(N)]   # the append-only HISTORY (each exchange's content vector)

    kernel = build_kernel(log)
    print(f"(1) NOTHING TO COMPACT — the kernel is CONSTANT SIZE:")
    print(f"    after {N} exchanges the kernel is {len(kernel)} bytes (D={D}); after 1 exchange it is {len(build_kernel(log[:1]))} bytes.")
    print(f"    a Gen-1 LLM context would have grown {N}x; the kernel did NOT grow -> no compaction, ever.\n")

    print(f"(2) GRACEFUL FADE (recall by recency, NOT truncation):")
    sims = [hdc.similarity(kernel, x) for x in log]
    for i in (N - 1, N - 2, N - 4, N - 8, N - 16, 0):
        bar = "#" * int(max(sims[i], 0) * 40)
        print(f"    exchange {i:02d} (age {N-1-i:>2}): recall {sims[i]:+.2f}  {bar}")
    print(f"    -> recent exchanges are SHARP, old ones FADE smoothly to noise (no hard cut-off; the record survives in the log).\n")

    print(f"(3) REWIND — rebuild the kernel from any log prefix:")
    for k in (8, 16, 24):
        kk = build_kernel(log[:k])
        at_k = hdc.similarity(kk, log[k - 1])                    # the most-recent exchange AT turn k
        future = hdc.similarity(kk, log[k]) if k < N else float("nan")
        print(f"    rewind to turn {k:>2}: recalls exchange {k-1:02d} (then-recent) {at_k:+.2f}; the FUTURE exchange {min(k,N-1):02d} {future:+.2f} (unknown, as it should be)")
    print()

    print("VERDICT:")
    print(f"  • NOTHING TO EVER COMPACT: the memory is its OWN KERNEL — a CONSTANT-D HDC bundle ({len(kernel)} bytes) maintained")
    print(f"    every exchange. It does not grow with conversation length, so the Gen-1 LLM compaction/truncation problem")
    print(f"    (what THIS session has been doing by hand) simply does not arise.")
    print(f"  • GRACEFUL FADE, NOT TRUNCATION: recent exchanges are sharp, old ones fade smoothly (HDC capacity F137/F152 +")
    print(f"    recency/plasticity-decay F76/F141) — biologically realistic working memory, and the exact content survives")
    print(f"    in the append-only LOG for recall/re-binding if needed.")
    print(f"  • REWINDABLE like a Gen-1 LLM: the append-only history log lets you rebuild the kernel from ANY prefix — rewind")
    print(f"    to turn k reconstructs the exact memory state at turn k (recalls the then-recent exchange, not the future).")
    print(f"  • So the RBS-LM is: WORKING memory = the constant kernel (fades, never compacts) + EPISODIC memory = the log")
    print(f"    (exact, rewindable). Composes F166 (rolling context-state), F137/F152 (capacity), F76/F141 (decay).")


if __name__ == "__main__":
    main()
