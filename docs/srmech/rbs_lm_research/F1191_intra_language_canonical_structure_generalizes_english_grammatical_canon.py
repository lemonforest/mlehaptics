"""F1191 (#243): does the intra-A hidden-canonical-structure generalize from formulaic GENRE (Egyptian, F1190) to the
GRAMMATICAL/collocational canon of a NON-formulaic English narrative?

F1190 (Egyptian offering formula): a knowledge kernel restored the elided GENRE frame (17 frame / 0 operand). Question:
is "hidden canonical structure inside language A" a property of formulaic GENRE, or of LANGUAGE itself? English narrative
has NO genre formula, but it has a grammatical/collocational canon it elides because implied (the function-word scaffold,
agreement, common collocations — "gone to Ø store"). Test the SAME knowledge-kernel mechanism on it.

Three-way decomposition (richer than Egyptian's two-way):
  * GRAMMATICAL FRAME — the function/high-frequency scaffold (discovered as the corpus-attested canon, the knowledge kernel)
  * recurring CONTENT — the spectral FAMILY's consensus (siona.reconstruct.family's algorithm, Class-L)
  * unique OPERAND — the rare content (names, specific nouns) — neither recovers
Prediction: the recoverable structure concentrates in the high-frequency GRAMMATICAL tier, ~zero in the rare OPERAND tier,
for EVERY method — showing the implied/specified (frame/operand) split is GENERAL to language A, not genre-specific — and
the knowledge kernel lifts the grammatical tier specifically (the English analog of 17/0).

Corpus (Gutenberg-attested): A Tale of Two Cities (Charles Dickens, Gutenberg #98). srmech Class-L (signed_laplacian +
symmetric_eigendecompose) for the family step — the same algorithm siona.reconstruct.family packages, here with a
grammar-INCLUSIVE tokenizer (function words KEPT) to test the grammatical canon. numpy-free; no magnitude-builtin;
plain-dict tally.
"""
import re, random
from srmech.amsc import laplacian as L

PATH = "/tmp/gb_98_tale.txt"


def sentences():
    t = open(PATH, encoding="utf-8", errors="replace").read()
    s = re.search(r"\*\*\* START OF.*?\*\*\*", t); e = re.search(r"\*\*\* END OF", t)
    body = t[s.end():e.start()] if (s and e) else t
    out = []
    for raw in re.split(r"[.!?]", body):
        toks = re.findall(r"[a-z]+", raw.lower())               # ALL words kept — function words are the grammatical canon
        if len(set(toks)) >= 8:
            out.append(frozenset(toks))
    return out


def jac(a, b):
    u = len(a | b)
    return len(a & b) / u if u else 0.0


def family_content(surv_c, pool_c, i, K=120, k=12, m=5):
    """siona.reconstruct.family's algorithm (Class-L low-eigenmode local coupling), on CONTENT sets — recovers recurring
    CONTENT parallels (function words excluded from the graph so they don't over-connect every sentence)."""
    sc = sorted((j for j in range(len(pool_c)) if j != i), key=lambda j: -jac(surv_c, pool_c[j]))[:K]
    if not sc:
        return []
    nodes = [surv_c] + [pool_c[j] for j in sc]
    n = len(nodes)
    edges, w = [], []
    for a in range(n):
        for b in range(a + 1, n):
            v = jac(nodes[a], nodes[b])
            if v > 0.0:
                edges.append((a, b)); w.append(v)
    if not edges:
        return sc[:k]
    evals, evecs = L.symmetric_eigendecompose(L.signed_laplacian(n, edges, w))
    evals = [float(x) for x in evals]
    low = [c for c in sorted(range(n), key=lambda c: evals[c]) if evals[c] > 1e-6][:m]
    if not low:
        return sc[:k]
    q = [float(evecs[0][c]) for c in low]
    near = sorted(range(1, n), key=lambda node: sum((float(evecs[node][c]) - q[t]) ** 2 for t, c in enumerate(low)))[:k]
    return [sc[node - 1] for node in near]


def recall(pred, truth):
    return len(set(pred) & truth) / len(truth) if truth else None


if __name__ == "__main__":
    sents = sentences()
    N = len(sents)
    df = {}
    for s in sents:
        for w in s:
            df[w] = df.get(w, 0) + 1
    freq_rank = sorted(df, key=lambda w: (-df[w], w))

    # the knowledge kernel = the GRAMMATICAL/collocational canon, DISCOVERED as the corpus-attested frame (tokens in
    # >= FRAME_FRAC of sentences; a rare content word / name can never clear it — the ratio separates frame from operand)
    FRAME_FRAC = 0.01
    frame = frozenset(w for w in df if df[w] >= FRAME_FRAC * N)
    print("F1191 (#243): intra-A canonical structure — English narrative (A Tale of Two Cities), %d sentences\n" % N)
    print("   knowledge kernel = grammatical/collocational canon (>=%.0f%% of sentences), %d tokens; top:"
          % (100 * FRAME_FRAC, len(frame)))
    print("      %s\n" % " ".join(freq_rank[:28]))

    pool_content = [s - frame for s in sents]                   # content sets (function/frame words removed) for the family
    random.seed(13)
    trials = [i for i in random.sample(range(N), min(90, N)) if len(sents[i]) >= 8]
    modes = ["prior", "family", "knowledge", "family+knowledge"]
    Rbud = {mm: 0.0 for mm in modes}
    Rf = {mm: 0.0 for mm in modes}; Ro = {mm: 0.0 for mm in modes}    # tier-split recall (frame / operand)
    nf = no = 0; got = 0
    lift_frame = lift_operand = 0
    for i in trials:
        full = list(sents[i]); random.shuffle(full)
        survive = frozenset(full[: len(full) // 2]); masked = set(full[len(full) // 2:])
        if len(masked) < 3:
            continue
        got += 1
        b = len(masked)
        surv_c = survive - frame

        fam = family_content(surv_c, pool_content, i)
        wc = {}
        for j in fam:
            for w in pool_content[j]:
                wc[w] = wc.get(w, 0) + 1
        thr = 2 if int(0.30 * max(1, len(fam))) < 2 else int(0.30 * len(fam))
        rk_family = [w for w in sorted(wc, key=lambda w: (-wc[w], w)) if wc[w] >= thr and w not in survive]
        rk_prior = [w for w in freq_rank if w not in survive]
        rk_know = [w for w in freq_rank if w in frame and w not in survive]     # the grammatical canon, freq-ranked
        seen = set(rk_family)
        rk_fk = list(rk_family) + [w for w in rk_know if w not in seen]

        ranked = {"prior": rk_prior, "family": rk_family, "knowledge": rk_know, "family+knowledge": rk_fk}
        for mm in modes:
            Rbud[mm] += recall(ranked[mm][:b], masked)          # equal-budget overall recall

        # tier-split: how the EQUAL-BUDGET guesses (top-|masked|) split between the FRAME tier and the OPERAND tier —
        # i.e. WHERE each method spends its recovery (capped, so it is not the degenerate "the list contains everything")
        fm = masked & frame; om = masked - frame
        if fm:
            nf += 1
            for mm in modes:
                Rf[mm] += recall(ranked[mm][:b], fm)
        if om:
            no += 1
            for mm in modes:
                Ro[mm] += recall(ranked[mm][:b], om)

        extra = (set(rk_fk) & masked) - (set(rk_family) & masked)
        lift_frame += sum(1 for w in extra if w in frame)
        lift_operand += sum(1 for w in extra if w not in frame)

    print("   EQUAL-BUDGET overall recall (capped to |masked| ranked guesses — fair):")
    for mm in modes:
        print("     %-18s   %.3f" % (mm, Rbud[mm] / got))
    print("\n   TIER-SPLIT recall — WHERE each method's recovery lands (the key measurement):")
    print("     mode                 GRAMMATICAL-frame tier    OPERAND (rare-content) tier")
    for mm in modes:
        print("     %-18s   %.3f                     %.3f" % (mm, Rf[mm] / max(1, nf), Ro[mm] / max(1, no)))
    print("\n   knowledge's EXTRA correct-recoveries over family-alone: %d frame-tokens, %d operand-tokens" % (
        lift_frame, lift_operand))
    print("\n  READ: if EVERY method's recall concentrates in the GRAMMATICAL-frame tier and is ~0 in the OPERAND tier,")
    print("  the implied/specified (frame/operand) split is GENERAL to language A — English narrative hides its grammatical")
    print("  canon exactly as Egyptian hid its genre frame — and the knowledge kernel's lift being ~all frame / ~0 operand")
    print("  is the English analog of F1190's 17/0: the kernel restores the elided grammatical canon, never the unique content.")
