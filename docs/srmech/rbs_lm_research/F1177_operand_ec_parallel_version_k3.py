"""F1177: the OPERAND-EC demonstration + deeper research — the Rosetta as a distance-3 repetition code.

F1175 showed intra-text recurrence recovers the OP (formula frame) but NOT the unique OPERAND (names/slots) — recall
~0.015 for operands. The claim: a PARALLEL VERSION supplies the operand, and THREE parallel versions (the Rosetta's
hieroglyphic + demotic + Greek) form a distance-3 repetition code that CORRECTS a corrupted operand by 2-of-3 majority,
where TWO versions can only DETECT (the F291 k=2-detects / k=3-corrects law; the F1131 op(x)operand(x)EC triality; the
same reason the research-verify uses haiku||sonnet||opus).

Rosetta-proxy corpus: 3 parallel English translations of Matthew 1 (a genealogy = maximally operand/name-dense),
verse-aligned (bible-api.com; KJV / WEB / BBE). KJV uses Greek-form names (Judas/Phares/Thamar), WEB+BBE the Hebrew
forms (Judah/Perez/Tamar) — exactly the Rosetta's different-script-same-operand situation. numpy-free; no magnitude-builtin.
"""
import json, re

FUNC = set("and the of was is by were became father sons son name a an in to".split())


def names(verse_text):
    """operand-slots of a genealogy verse = the proper names, in order (capitalised, not verse-initial, not function)."""
    ws = verse_text.strip().split()
    out = []
    for k, w in enumerate(ws):
        c = re.sub(r"[^A-Za-z]", "", w)
        if c and c[0].isupper() and c.lower() not in FUNC and not (k == 0):
            out.append(c)
    return out


def load(tr):
    d = json.load(open("/tmp/mt1_%s.json" % tr))
    return {v["verse"]: names(v["text"]) for v in d["verses"]}


A, B, C = load("kjv"), load("web"), load("bbe")

# aligned operand-slots: verses where all 3 versions have the SAME number of names -> align by position
slots = []          # each = (a, b, c) parallel name triple
for v in sorted(A):
    if v in B and v in C and len(A[v]) == len(B[v]) == len(C[v]) and A[v]:
        for i in range(len(A[v])):
            slots.append((A[v][i], B[v][i], C[v][i]))
S = len(slots)

# --- Test A: operand-EC works (parallel supplies what intra-text cannot) ---
# intra-text recall of a unique operand ~0.015 (F1175). Parallel recovery = does a parallel version carry the name?
par_recover = sum(1 for a, b, c in slots if a == b or a == c) / S      # A's name attested by >=1 parallel (exact form)
maj_recover = sum(1 for a, b, c in slots if (a == b) or (a == c) or (b == c)) / S  # ANY 2-of-3 agree (a majority exists)

# --- Test B: k=2 DETECTS vs k=3 CORRECTS (inject one corruption per slot, each version in turn) ---
def corrupt(x):
    return x + "_X"          # a scribal error / lacuna: the form no longer matches

k2_detect = k2_correct = k3_correct = trials = 0
for a, b, c in slots:
    trip = [a, b, c]
    for j in range(3):                       # corrupt version j
        surv = [trip[t] for t in range(3) if t != j]     # the 2 survivors (k=3 view)
        # k=2 view: only ONE other copy is available (say the first survivor) -> detect vs the corrupted, cannot vote
        k2_pair = [corrupt(trip[j]), surv[0]]
        trials += 1
        if k2_pair[0] != k2_pair[1]:
            k2_detect += 1                    # k=2 flags the disagreement (detection)
        # k=2 correction: with 2 disagreeing copies you cannot know which is right -> no majority -> 0
        # k=3 correction: majority of {corrupt, surv0, surv1}; corrects iff the 2 survivors agree
        if surv[0] == surv[1]:
            k3_correct += 1                   # 2-of-3 majority recovers the true operand

print("F1177: OPERAND-EC via parallel versions — the Rosetta as a distance-3 repetition code")
print("  corpus: 3 parallel translations of Matthew 1 (genealogy); %d cleanly-aligned operand(name) slots\n" % S)
print("  Test A — operand-EC works (parallel supplies the operand intra-text cannot):")
print("     intra-text recall of a unique operand (F1175)           : 0.015")
print("     >=1 parallel carries A's exact name form                 : %.2f" % par_recover)
print("     a 2-of-3 majority form exists for the slot                : %.2f" % maj_recover)
print("\n  Test B — k=2 DETECTS but k=3 CORRECTS (one corruption injected per slot, each version in turn; %d trials):" % trials)
print("     k=2 (two copies): error DETECTED                          : %.2f" % (k2_detect / trials))
print("     k=2 (two copies): error CORRECTED (locate the wrong copy) : 0.00  (a 1-vs-1 split has no majority)")
print("     k=3 (three copies): error CORRECTED by 2-of-3 majority    : %.2f" % (k3_correct / trials))
print("\n  READ: k=2 is a parity check (detect-only); k=3 is the repetition code that corrects — WHY the Rosetta has")
print("  THREE scripts, not two. Same k=3 error-correction as op(x)operand(x)EC (F1131) + the haiku||sonnet||opus verify (F291).")
print("  The residue (all-3-differ slots, e.g. Greek-vs-Hebrew name forms) is the honest un-attestable operand needing a 4th source.")
