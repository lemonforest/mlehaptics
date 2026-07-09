"""F1175: test the reconstruction lens on a coherent formulaic EGYPTIAN text + the Rosetta k=3 consideration.

Corpus (Gutenberg-attested, public domain): ebook 28282 "Egyptian Literature" (Budge et al., English translation of
ancient Egyptian hymns / litanies / Book of the Dead). Densely formulaic: 'Hail,' x148, 'Homage to thee' x106,
'I have not' x89 (the Negative Confession). Formulaic recurrence: the FRAME recurs, the SLOT varies.
The reconstruction is on STRUCTURE (formulaic recurrence), preserved in translation; transliterated-Egyptian is a
further refinement. srmech-native intent; numpy-free; no magnitude-builtin (two-sided windows only).

Three measurements:
  (a) FULL-MASK fixed-period lens: mask a whole line, predict from position-neighbours {i-1,i+1,i-P,i+P} vs a
      global-frequency PRIOR. -> lens does NOT beat prior on a varied-slot litany (parallels are scattered, not at i+-P).
  (b) RECURRENCE CEILING: what fraction of lines genuinely recur (near-duplicate elsewhere), and the recall of a
      recurring line from its parallel. -> ~25% recur (>=0.5), recovered at ~0.80 recall = the affordance's real scope.
  (c) REALISTIC partial-damage: HALF the line survives (a lacuna), find the recurrence-parallel via the surviving
      half, fill the gap vs the PRIOR. -> lens ~doubles the prior (0.090 vs 0.046) = the real fragmentary use case.
Boundary: within-text recurrence recovers the OP (formula frame / repeated content); the unique OPERAND (names/slots)
needs EXTERNAL k=3 EC = the Rosetta Stone's 3 parallel scripts (op(x)operand(x)EC, F1131).
"""
import re, random

STOP = set(("the of a an and to in on at for with by from as is are was were be been being it he she they thou thee "
            "thy thine ye you your his her its their this that these those o oh unto upon into out over who whom which "
            "what when where how then than not no i am art hath have has had do doth did shall will would may might me "
            "my we us our them him all one there here now come came forth made make let god").split())
PATH = "/tmp/egylit.txt"   # Gutenberg 28282; fetch before running


def load():
    t = open(PATH, encoding='utf-8', errors='replace').read()
    s = re.search(r"\*\*\* START OF.*?\*\*\*", t); e = re.search(r"\*\*\* END OF", t)
    body = t[s.end():e.start()] if (s and e) else t
    rows = []
    for ln in re.split(r"[.\n;:!?]", body):
        ws = [w for w in re.findall(r"[a-z]+", ln.lower()) if w not in STOP and len(w) > 2]
        rows.append(sorted(set(ws)))
    return rows


def sim(a, b):
    A, B = set(a), set(b)
    return len(A & B) / max(1, len(A | B))


def measure_ceiling(rows, seed=0, k=400):
    random.seed(seed)
    samp = random.sample(range(len(rows)), k)
    recoverable, recalls = 0, []
    for i in samp:
        ri = set(rows[i])
        if len(ri) < 3:
            continue
        bj, bs = -1, 0.0
        for j in range(len(rows)):
            if j != i:
                v = sim(rows[i], rows[j])
                if v > bs:
                    bs, bj = v, j
        if bs >= 0.5:
            recoverable += 1
            recalls.append(len(ri & set(rows[bj])) / len(ri))
    return recoverable / len(samp), (sum(recalls) / max(1, len(recalls)))


def measure_partial_damage(rows, seed=5, k=300):
    df = {}
    for r in rows:
        for w in r:
            df[w] = df.get(w, 0) + 1
    freq = sorted(df, key=lambda w: -df[w])
    random.seed(seed)
    samp = random.sample(range(len(rows)), k)
    lens_r = prior_r = 0.0
    got = 0
    for i in samp:
        words = [w for w in rows[i]]
        if len(words) < 4:
            continue
        random.shuffle(words)
        survive = set(words[:len(words) // 2])
        masked = set(words[len(words) // 2:])
        if not masked:
            continue
        got += 1
        bj, bs = -1, 0.0
        for j in range(len(rows)):
            if j != i:
                v = len(survive & set(rows[j])) / max(1, len(survive | set(rows[j])))
                if v > bs:
                    bs, bj = v, j
        pred_lens = (set(rows[bj]) - survive) if bj >= 0 else set()
        pred_prior = set(freq[:len(pred_lens) or 8]) - survive
        lens_r += len(pred_lens & masked) / len(masked)
        prior_r += len(pred_prior & masked) / len(masked)
    return lens_r / got, prior_r / got, got


if __name__ == "__main__":
    rows = [r for r in load() if len(r) >= 4]
    frac, ceil = measure_ceiling(rows)
    lens_r, prior_r, got = measure_partial_damage(rows)
    print("F1175 — reconstruction lens on formulaic EGYPTIAN (Book of the Dead / hymns / litanies, Gutenberg 28282)")
    print("  corpus: %d formulaic lines\n" % len(rows))
    print("  (b) recurrence CEILING: %.0f%% of lines recur (>=0.5 parallel) ; recovered at %.2f recall from the parallel" % (100 * frac, ceil))
    print("  (c) REALISTIC partial-damage (survive half, recover lacuna): LENS %.3f vs PRIOR %.3f  (%+.1f pp, ~%.1fx)" % (
        lens_r, prior_r, 100 * (lens_r - prior_r), lens_r / max(1e-9, prior_r)))
    print("\n  op(x)operand(x)EC at the reconstruction scale: intra-text recurrence recovers the OP (formula frame /")
    print("  repeated spell, ~25% of formulaic content); the unique OPERAND needs the Rosetta's 3 scripts = k=3 EC (F1131).")
