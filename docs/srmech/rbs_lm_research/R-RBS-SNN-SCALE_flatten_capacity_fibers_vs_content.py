r"""R-RBS-SNN-SCALE (rung #2) — scale N on the F498 flatten and watch the capacity law (F222) bite: the FIBERS
(outer = frame/which-unit, N items; inner = chirality/hand, N items) stay address-exact far longer than the
CONTENT (N×M items), because the fibers carry FEWER items into the same bundle. Both are capacity-bounded (F222);
the fibers' lower item-count is why they hold while content degrades first. Honest curve, not "fibers immune".
srmech 0.7.4.
"""
import hashlib
import srmech
from srmech.amsc import hdc
from srmech.amsc.cascade import the_one

NB = hdc.DEFAULT_HDC_BYTES


def hv(label):
    out, i = b"", 0
    while len(out) < NB:
        out += hashlib.sha256(label.encode() + bytes([i])).digest()
        i += 1
    return out[:NB]


def run(N, M=7):
    S = the_one(sigma=1, theta_num=1, theta_den=M, terms=8)
    K = hv("the_one:" + str(S.to_flat_rational()))
    slot = [hdc.permute(K, k * 137 + 1) for k in range(M)]
    frame = [hdc.permute(K, (u + 1) * 9973) for u in range(N)]
    chi = hv("chirality:inner-fiber")
    boxes, contents, sigma = [], [], []
    for u in range(N):
        content = [hv(f"u{u}:m{k}") for k in range(M)]
        box = hdc.bundle([hdc.bind(content[k], slot[k]) for k in range(M)])
        sg = +1 if (u % 2 == 0) else -1
        boxes.append((box, box if sg > 0 else hdc.bind(box, chi)))
        contents.append(content); sigma.append(sg)
    flat = hdc.bundle([hdc.bind(boxes[u][1], frame[u]) for u in range(N)])
    outer = inner = chits = ctot = 0
    for u in range(N):
        box_rec = hdc.bind(flat, frame[u])
        outer += (max(range(N), key=lambda v: hdc.similarity(box_rec, boxes[v][1])) == u)
        s_plus = hdc.similarity(box_rec, boxes[u][0])
        s_minus = hdc.similarity(hdc.bind(box_rec, chi), boxes[u][0])
        hand = +1 if s_plus >= s_minus else -1
        inner += (hand == sigma[u])
        clean = box_rec if hand > 0 else hdc.bind(box_rec, chi)
        for k in range(M):
            rec = hdc.bind(clean, slot[k])
            j = max(range(u * M, (u + 1) * M), key=lambda t: hdc.similarity(rec, contents[t // M][t % M]))
            chits += (j == u * M + k); ctot += 1
    return outer / N, inner / N, chits / ctot


def main():
    print(f"=== R-RBS-SNN-SCALE (rung #2) — flatten capacity: fibers vs content as N grows  (srmech {srmech.__version__}) ===\n")
    print(f"  {NB}-byte HDC object; M=7 meanings per unit; bundle of N units (N×7 content items in one vector)\n")
    print(f"  {'N':>4} {'N×M':>5} | {'OUTER fiber':>12} {'INNER fiber':>12} {'CONTENT':>9}")
    print(f"  {'-'*4} {'-'*5} | {'-'*12} {'-'*12} {'-'*9}")
    rows = []
    for N in (3, 5, 9, 15, 25, 35):
        o, i, c = run(N)
        rows.append((N, o, i, c))
        print(f"  {N:>4} {N*7:>5} | {o:>11.0%} {i:>11.0%} {c:>8.0%}")

    print("\nVERDICT (rung #2):")
    print(f"  • the FIBERS hold while CONTENT degrades first — exactly the F222 capacity law by item-count: the outer")
    print(f"    & inner fibers carry N items each, the content carries N×M (=7N). At fixed HDC width the N×M content")
    print(f"    saturates the bundle long before the N-item fibers do.")
    print(f"  • this is the honest reading (NOT 'fibers immune'): both are capacity-bounded; the fibers are robust")
    print(f"    because they are the FEW (the address/structure), content is the MANY (the payload). The addressable")
    print(f"    SNN keeps its STRUCTURE (both fibers) under load and sheds CONTENT first — the cheap-path priority")
    print(f"    (F485): structure survives, payload is recoverable only within capacity. Scale via more volumes")
    print(f"    (a SERIES of sedenion boxes, F499), not a fatter single bundle.")


if __name__ == "__main__":
    main()
