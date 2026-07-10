"""F1196 (#243): the RESPONSION made measurable — is definiteness a scene-locked phase cycle (the intrinsic k=3 third
factor) or a frequency/drift cline (k=2 + amplitude only)?

Reframe (user correction + fable reconciliation): the F1192-F1195 thread ran the k=2 form op(x)operand and mislabeled the
residual "external → the expert". The framework's unit is op(x)operand(x)RESPONSION (k=3): op(x)operand DETECTS, the
responsion CORRECTS and is INTRINSIC (an attractor-contraction to a cyclic phase-lock slot, F1186). Fable located it: the
determiner slot is a Class-K pin-slot / phase boundary, and first-mention "the" is an ACCOMMODATION (the reader's model
CONSTRUCTS the referent) — the responsion firing at the text↔reader coupling. It is a 3-cell split: DETECT (anaphoric
"the", prior referent) / RESPONSION (accommodation "the", constructed) / EXTERNAL (encyclopedic "the sun/King", small,
routes to the expert).

THE TEST (fable's design): P(the | first-mention-WITHIN-SCENE, τ) should RISE with τ (tokens-since-scene-break) and RESET
at scene breaks — a sawtooth. The discriminant vs the frequency/drift NULL: permute the break locations (gap-shuffle:
preserve count + spacing), recompute the sawtooth amplitude (point-biserial r between τ and is-"the"), 1000×. TRUE-break r
above the 95th percentile of the permuted null ⇒ phase-locked responsion (a cline CANNOT reset; only a phase-locked
oscillator resets). TRUE ≈ permuted ⇒ amplitude/drift only. The frequency worry becomes the null, and the reset beats it.

Corpus: 3 novels (#98 Dickens / #829 Swift / #1342 Austen), scenes = chapter breaks + paragraph-initial temporal shifters;
narration only (skip dialogue). Pre-registered: Gulliver low early-scene P(the) + steep ramp; Dickens high even early +
sharp reset. Integer counts; ratios; log2/sqrt at display only; no magnitude-builtin; plain dicts (no Counter).
"""
import re, random, math

NOVELS = [("Dickens #98", "/tmp/gb_98_tale.txt"), ("Swift #829", "/tmp/gb_829_gulliver.txt"),
          ("Austen #1342", "/tmp/gb_1342_pride.txt")]

FUNCTION = set((
    "the a an this that these those i you he she it we they me him her us them my your his its our their mine yours hers "
    "ours theirs myself yourself himself herself itself ourselves themselves who whom whose which what of in on at by for "
    "with from to into onto upon over under above below between among through during before after since until about "
    "against without within along across behind beyond beside near off out up down and or but nor so yet as if than "
    "because while although though unless whereas whether when where why how is am are was were be been being have has had "
    "do does did will would shall should can could may might must ought not no too very just only also then there here now "
    "thus hence however moreover indeed all any some each every none both few many much more most less least several "
    "enough such same other another one two").split())

SHIFTERS = [re.compile(p) for p in (
    r"the next\b", r"the following\b", r"that (morning|evening|night|day|afternoon|same|very)\b", r"meanwhile\b",
    r"at (length|last|this moment|that moment|this time|that time)\b", r"on the (following|next|morning|evening)\b",
    r"after (a|some|this|that|these|breakfast|dinner|supper|which)\b", r"next (day|morning|evening|week)\b",
    r"(soon|presently|shortly) \b", r"one (day|morning|evening|night|afternoon)\b", r"in the (morning|evening|meantime)\b",
    r"some (days|time|weeks|months|hours|years) (later|after|passed|afterwards)\b",
    r"a (few )?(days|weeks|months|hours|minutes) (later|after|passed|afterwards|elapsed)\b",
    r"it was (now|not long|about|already)\b", r"early (the )?(next )?morning\b",
    r"(two|three|four|several) (days|weeks|months|hours|years)\b")]
CHAP = re.compile(r"^(chapter|letter|volume|part|book)\b", re.I)
ROMAN = re.compile(r"^[ivxlcdm]+\.?$", re.I)


def is_content(w):
    return len(w) >= 3 and w not in FUNCTION and w.isalpha()


def is_scene_break(para):
    st = para.strip()
    head = st.lower()[:40]
    if CHAP.match(st) or ROMAN.match(st) or (len(st) < 40 and st.isupper() and len(st) > 2):
        return True
    return any(rgx.match(head) for rgx in SHIFTERS)


def tokenize_body(path):
    """→ (toks, breaks): toks = [(word, in_dialogue)]; breaks = sorted scene-start token indices."""
    raw = open(path, encoding="utf-8", errors="replace").read()
    s = re.search(r"\*\*\* START OF.*?\*\*\*", raw); e = re.search(r"\*\*\* END OF", raw)
    body = raw[s.end():e.start()] if (s and e) else raw
    toks, breaks = [], []
    for para in re.split(r"\n[ \t]*\n", body):
        if not para.strip():
            continue
        if is_scene_break(para):
            breaks.append(len(toks))
        in_q = False; cur = []
        for ch in para.lower():
            if ch == "“":
                in_q = True
            elif ch == "”":
                in_q = False
            elif ch == '"':
                in_q = not in_q
            if "a" <= ch <= "z":
                cur.append(ch)
            elif cur:
                toks.append(("".join(cur), in_q)); cur = []
        if cur:
            toks.append(("".join(cur), in_q))
    if not breaks or breaks[0] != 0:
        breaks = [0] + breaks
    return toks, breaks


def events_of(toks, breaks):
    """first-mention-WITHIN-SCENE nouns introduced by the/a(n) in NARRATION → [(is_the, tau, pos)]."""
    bset = set(breaks)
    seen = set(); start = 0; ev = []
    for i, (w, dlg) in enumerate(toks):
        if i in bset:
            seen = set(); start = i
        if w in ("the", "a", "an") and not dlg:
            head = None
            for j in range(i + 1, min(i + 4, len(toks))):
                if is_content(toks[j][0]):
                    head = toks[j][0]; break
            if head is not None and head not in seen:
                ev.append((1 if w == "the" else 0, i - start, i))
        if is_content(w):
            seen.add(w)
    return ev


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return 0.0
    sx = sum(xs); sy = sum(ys); sxx = sum(x * x for x in xs); syy = sum(y * y for y in ys)
    sxy = sum(x * y for x, y in zip(xs, ys))
    den2 = (n * sxx - sx * sx) * (n * syy - sy * sy)
    return (n * sxy - sx * sy) / math.sqrt(den2) if den2 > 0 else 0.0


def taus_from_breaks(positions, bks):
    """tau = pos − nearest preceding break, merge-walked (positions & bks both ascending)."""
    out = []; k = 0; K = len(bks)
    for p in positions:
        while k + 1 < K and bks[k + 1] <= p:
            k += 1
        out.append(p - bks[k])
    return out


def gap_shuffle(breaks, N, rng):
    pts = sorted(set(breaks) | {0})
    gaps = [pts[i + 1] - pts[i] for i in range(len(pts) - 1)] + [N - pts[-1]]
    rng.shuffle(gaps)
    fake = []; c = 0
    for g in gaps[:-1]:
        c += g; fake.append(c)
    return [0] + fake


if __name__ == "__main__":
    import sys
    novels = NOVELS
    if len(sys.argv) > 1:                                   # pre-registered replication: pass fresh novel paths
        novels = [(p.split("/")[-1], p) for p in sys.argv[1:]]
    print("F1196 (#243): the responsion as a scene-locked phase cycle vs a frequency/drift cline\n")
    NPERM = 1000
    for name, path in novels:
        toks, breaks = tokenize_body(path)
        N = len(toks)
        ev = events_of(toks, breaks)
        is_the = [e[0] for e in ev]; tau = [e[1] for e in ev]; pos = [e[2] for e in ev]
        base = sum(is_the) / len(is_the)
        # the ramp: P(the) by tau bin
        edges = [0, 50, 100, 200, 400, 10 ** 9]
        ramp = []
        for b in range(len(edges) - 1):
            sub = [is_the[i] for i in range(len(ev)) if edges[b] <= tau[i] < edges[b + 1]]
            ramp.append((sum(sub) / len(sub), len(sub)) if sub else (0.0, 0))
        r_true = pearson(tau, is_the)
        # scene-OPENING statistic: P(the) among the first W tokens after a break (accommodation-at-open, inverted phase)
        W = 50
        op_num = sum(is_the[i] for i in range(len(ev)) if tau[i] < W)
        op_den = sum(1 for i in range(len(ev)) if tau[i] < W)
        open_true = op_num / op_den if op_den else 0.0
        # NULL: gap-shuffled break locations (drift/frequency null — a cline cannot reset). Test BOTH the linear ramp r
        # and the opening-bump P(the|tau<W) against the same break-permutation null, in one pass.
        rng = random.Random(31)
        ge_r = ge_op = 0
        for _ in range(NPERM):
            fake = gap_shuffle(breaks, N, rng)
            tp = taus_from_breaks(pos, fake)
            if pearson(tp, is_the) >= r_true:
                ge_r += 1
            on = sum(is_the[i] for i in range(len(ev)) if tp[i] < W)
            od = sum(1 for i in range(len(ev)) if tp[i] < W)
            if od and (on / od) >= open_true:
                ge_op += 1
        pval = (ge_r + 1) / (NPERM + 1)
        p_open = (ge_op + 1) / (NPERM + 1)
        # drift control: does P(the) track GLOBAL position instead? (stationary cline signature)
        r_drift = pearson(pos, is_the)
        print("  %-13s  %d scenes, %d first-mention events, base P(the)=%.2f" % (name, len(breaks), len(ev), base))
        print("     P(the) by tau-bin [0,50) [50,100) [100,200) [200,400) [400+):  " +
              "  ".join("%.2f(n%d)" % (p, n) for p, n in ramp))
        print("     ramp  r(tau,is_the) = %+.3f  null p=%.3f  %s" % (
            r_true, pval, "ramp PHASE-LOCKED" if pval < 0.05 else "ramp within null"))
        print("     scene-OPEN P(the|tau<%d) = %.2f vs base %.2f   permuted-break null p = %.3f   %s" % (
            W, open_true, base, p_open, "OPENING-BUMP beats null (scene-locked, inverted phase)"
            if p_open < 0.05 else "within null"))
        print("     global-position drift r(pos, is_the) = %+.3f  (the stationary-cline signature)\n" % r_drift)
    print("  READ: r(tau,is_the) > 0 AND below-0.05 permuted-null p ⇒ the definiteness signal RESETS at real scene breaks")
    print("  = a phase-locked RESPONSION (the intrinsic k=3 third factor, the_one cyclic phase-lock), NOT a stationary")
    print("  frequency/drift cline (which would show r(pos) but no scene-reset and a null-band r(tau)). Pre-registered:")
    print("  Swift/Gulliver low early-bin P(the) + steep ramp; Dickens high even in [0,50) + sharp reset.")
