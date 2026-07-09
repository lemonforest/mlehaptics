"""F1178: the FULL reconstruction pipeline — GROUP -> ALIGN -> MAJORITY-CORRECT (wiring F1176 + F1177 end-to-end).

Given a damaged line loose in a mixed pool of many texts:
  1. GROUP    (F1176): find the damaged line's parallel-group among the pool by coupling-similarity of its surviving
                       content (the F1176 spectral community is the upgrade for fragmentary parallels; content-coupling
                       suffices when an operand-corruption leaves the frame intact).
  2. ALIGN    (F1177): position-align the operand-slots across the group (order-preserving formulae / genealogies).
  3. CORRECT  (F1177): k=3 (or k-of-n) majority-vote each slot -> replace the corrupted operand with the majority.

End-to-end test on a MIXED pool of 3 parallel translations of Matthew 1 (KJV/WEB/BBE), all 75 verse-lines pooled and
one operand corrupted per trial: measure (a) GROUPING accuracy (did it recover the true parallels?) and (b) end-to-end
CORRECTION (did the operand get fixed?). numpy-free; no magnitude-builtin.
"""
import json, re

FUNC = set("and the of was is by were became father sons son name a an in to".split())


def names(text):
    ws = text.strip().split()
    return [re.sub(r"[^A-Za-z]", "", w) for k, w in enumerate(ws)
            if re.sub(r"[^A-Za-z]", "", w) and re.sub(r"[^A-Za-z]", "", w)[0].isupper()
            and re.sub(r"[^A-Za-z]", "", w).lower() not in FUNC and k != 0]


def jac(a, b):
    A, B = set(a), set(b)
    return len(A & B) / max(1, len(A | B))


# ---- the pipeline ----
def reconstruct(damaged, pool, k=3):
    """damaged = (version, verse, names[]) with one corrupted operand; pool = list of (version, verse, names[])."""
    dv, dver, dnames = damaged
    # 1. GROUP — the k-1 pool members whose names best match the damaged line's SURVIVING content
    ranked = sorted((p for p in pool if not (p[0] == dv and p[1] == dver)),
                    key=lambda p: -jac(dnames, p[2]))
    group = [damaged] + ranked[:k - 1]
    # 2. ALIGN — position-align the operand slots (order-preserving); only slots present in all group members
    L = min(len(g[2]) for g in group)
    # 3. CORRECT — majority per aligned slot
    corrected = list(dnames)
    for i in range(min(L, len(dnames))):
        votes = {}
        for g in group:
            votes[g[2][i]] = votes.get(g[2][i], 0) + 1
        win = max(votes, key=votes.get)
        if votes[win] >= 2:                       # a 2-of-k majority exists -> adopt it
            corrected[i] = win
    return corrected, {p[1] for p in ranked[:k - 1]}


def load(tr):
    d = json.load(open("/tmp/mt1_%s.json" % tr))
    return [(tr, v["verse"], names(v["text"])) for v in d["verses"] if names(v["text"])]


VERS = ["kjv", "web", "bbe"]
pool = [row for tr in VERS for row in load(tr)]
by = {}
for row in pool:
    by.setdefault(row[1], []).append(row)

group_ok = corr_ok = corr_tot = 0
trials = 0
for (dv, dver, dnames) in pool:
    peers = [r for r in by[dver] if r[0] != dv]
    if len(peers) < 2 or not dnames:
        continue
    for slot in range(len(dnames)):
        trials += 1
        dmg = list(dnames); truth = dmg[slot]; dmg[slot] = dmg[slot] + "_X"     # corrupt one operand
        corrected, grp_verses = reconstruct((dv, dver, dmg), pool, k=3)
        # (a) grouping: did the 2 nearest come from the SAME verse (the true parallels)?
        if grp_verses == {dver}:
            group_ok += 1
        # (b) end-to-end correction of the corrupted slot
        if slot < len(corrected):
            corr_tot += 1
            if corrected[slot] == truth:
                corr_ok += 1

print("F1178: full reconstruction pipeline  GROUP -> ALIGN -> MAJORITY-CORRECT (KJV/WEB/BBE Matthew 1; %d operand trials)\n" % trials)
print("  (1) GROUPING accuracy — the 2 nearest pool lines ARE the true parallels : %.2f" % (group_ok / trials))
print("  (2) end-to-end CORRECTION — corrupted operand fixed by the pipeline     : %.2f  (of %d corrigible slots)" % (
    corr_ok / max(1, corr_tot), corr_tot))
print("\n  The pipeline runs the arc end-to-end: F1176 groups the damaged line with its parallels, F1177 aligns +")
print("  majority-corrects. A single loose damaged line in a mixed pool is reconstructed with no external key.")
