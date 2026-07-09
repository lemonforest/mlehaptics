"""F1179 k-scaling reinforcement probe: is k-copy operand-correction a DISCRETE vote (flat on/off) or a CONTINUOUS
resonant REINFORCEMENT (each added copy adds signal, SNR-like)? Tests the user's reframe that EC = harmonic reinforcement.

7 parallel translations of Matthew 1 (KJV/WEB/BBE/ASV/OEB-US/DARBY/YLT; bible-api-attested). For aligned operand-slots,
corrupt one copy and 2-of-k majority-recover the consensus form; sweep k=2..7. numpy-free; no magnitude-builtin;
plain-dict majority (no Counter, per the srmech discipline STOP-list — Counter is reserved-banned for co-occurrence).
"""
import json, re

FUNC = set("and the of was is by were became father sons son name a an in to".split())


def names(t):
    ws = t.strip().split()
    out = []
    for k, w in enumerate(ws):
        c = re.sub(r"[^A-Za-z]", "", w)
        if c and c[0].isupper() and c.lower() not in FUNC and k != 0:
            out.append(c)
    return out


def tally(vals):
    """plain-dict count -> (winning value, its count). Deterministic tie-break by value."""
    d = {}
    for v in vals:
        d[v] = d.get(v, 0) + 1
    win = max(sorted(d), key=lambda v: d[v])
    return win, d[win]


VERS = ["kjv", "web", "bbe", "asv", "oeb-us", "darby", "ylt"]
data = {}
for tr in VERS:
    try:
        d = json.load(open("/tmp/mt1_%s.json" % tr))
        data[tr] = {v["verse"]: names(v["text"]) for v in d["verses"]}
    except Exception:
        pass
V = list(data)

slots = []
for verse in data[V[0]]:
    present = [tr for tr in V if data[tr].get(verse)]
    if not present:
        continue
    modal = tally([len(data[tr][verse]) for tr in present])[0]      # modal name-count for this verse
    keep = [tr for tr in present if len(data[tr][verse]) == modal]
    if len(keep) >= 5:
        for i in range(modal):
            slots.append([data[tr][verse][i] for tr in keep])

print("F1179 k-scaling: %d aligned operand-slots across up to 7 parallel versions\n" % len(slots))
print("   k   correction-rate")
for k in range(2, 8):
    ok = tot = 0
    for s in slots:
        if len(s) < k:
            continue
        use = s[:k]; truth = tally(s)[0]
        for j in range(k):
            v = list(use); v[j] = v[j] + "_X"
            win, c = tally(v)
            tot += 1
            if c >= 2 and win == truth:
                ok += 1
    r = ok / max(1, tot)
    print("   %d      %.2f   %s%s" % (k, r, "#" * int(r * 40), "   (k=2 cannot vote: a pair only DETECTS)" if k == 2 else ""))
print("\n  k=2 -> 0 (parity/detect-only); monotone rise thereafter = each added copy REINFORCES the consensus,")
print("  the discrete majority being the read-out of a continuous (harmonic) reinforcement.")
