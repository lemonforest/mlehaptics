"""R-RBS-LM-148 — Cross-navigation Part 2: grammar(A) walked via logic(B).

Lodges Finding 205.

THE QUESTION (per ROADMAP live-queue #189; F165 §6.3; F163 §9)
--------------------------------------------------------------
Can a kernel built from one domain (grammar = A) be navigated / steered
by a kernel from another domain (logic = B)? Concretely: does conditioning
the eigvec-rank walk in kernel A on a B-derived anchor change or improve
the walk vs (i) a within-A baseline (no cross anchor) and (ii) a
random-anchor control?

This is the R-RBS-LM-54 Rosetta-stone machinery (54f DOMAIN anchor /
54g ride / 54k cross-kernel triangulation) applied across two genuinely
different DOMAINS, instead of within the poetry/prose family. F163's
null reframed this as STRUCTURAL PLAY (F163 §9): not a claim that mixing
"logics" transfers meaning, but a measurement of what coherent structure
emerges when grammar's sector hierarchy is walked under logic's adjacency.

PRE-STATED NULL (the falsifier, stated before running)
-------------------------------------------------------
H0: the B-anchor-conditioned walk is INDISTINGUISHABLE from the
    random-anchor control (|B-anchor metric - random-anchor metric|
    within the per-condition noise band, and no consistent sign).
    => no real cross-domain steering; the logic kernel is doing nothing
       a random kernel of matched size would not do.
We do NOT lean toward the alternative. A null here is a real result and
is reported as such. We also report a within-A baseline (steering by A's
OWN structure) and a random-EMISSION floor (frequency-weighted draw), so
the three conditions are bracketed top and bottom.

THE WALK METRIC (pre-stated, srmech-native — Class M)
-----------------------------------------------------
Hold out grammar (A) probe fragments. For each condition we run the same
ride: each probe token walks its top-k dominant A-eigvec ranks, the chosen
ranks emit A-vocabulary tokens. The CONDITION only changes WHICH ranks are
walked (the steering). We then bundle the emitted tokens into one BSC
hypervector (srmech.amsc.hdc.bundle, Class M) and measure its similarity
(srmech.amsc.hdc.similarity, Class M Hamming-BSC) to the held-out grammar
TARGET signature (the bundle of the target fragment's own top tokens).
metric = sim(emit_bundle, grammar_target_bundle).
Higher = the steered walk lands closer to genuine held-out grammar.

CONDITIONS
----------
  (a) B-anchor-conditioned : rank selection steered by the A->B find-cascade
        alignment — each A-eigvec's similarity to its best-matching LOGIC
        eigvec re-weights which A-ranks the token walks. Logic's structure
        conditions the grammar walk.
  (b) within-A baseline    : rank selection by A's own |eigvec[token]|^2
        (the plain 54g dominant-rank ride; no cross anchor).
  (c) random-anchor control: rank selection steered by a RANDOM anchor
        kernel of matched size (same construction as the B-anchor path but
        the per-A-rank weights are a seeded random permutation of the
        B-anchor weights — kills the logic content, keeps the shape).
  floor: random-EMISSION (frequency-weighted draw from A-vocab; the 54k
        baseline) — the absolute bottom any walk must beat to mean anything.

SRMECH-FIRST (CLAUDE.md §2)
---------------------------
  Class L : srmech.amsc.laplacian.{dense_laplacian, hermitian_eigendecompose}
            (co-occurrence Laplacian + eigenspectrum; NO np.linalg.eig*)
  Class M : srmech.amsc.hdc.{bundle, similarity}  + signal_processing.mint_vector
            (BSC bundle / Hamming similarity; NO hand-rolled cosine/softmax)
  Class A : srmech.amsc.format.sha256_bytes (content-hash of each corpus,
            for the attestation block; NO hashlib.sha256)
numpy is used only as srmech's array glue (argsort / random draw / mean).
Counter() is used only to accumulate co-occurrence EDGE WEIGHTS that feed
dense_laplacian, and emitted-token tallies that feed hdc.bundle — never as
a storage proxy.

DATA (tiny + attestable; provenance in the NDJSON attestation block)
--------------------------------------------------------------------
  grammar (A) = McGuffey First + Second Eclectic Reader  (the R-RBS-LM-73
                substrate of record). Project Gutenberg PG 14640 + PG 14668,
                public domain (US), fetched to /tmp.
  logic   (B) = Lewis Carroll, "Symbolic Logic" (1896) + "The Game of Logic"
                (1886). Project Gutenberg PG 28696 + PG 4763, public domain.
                Genuine syllogism / logical-connective prose ("No son of mine
                is dishonest; ... Hence it is a Conclusion ...").
Both are REAL public-domain corpora (not synthetic). sha256 of each stripped
body is recorded in the attestation. If a file is missing the script prints
the exact curl command and STOPS (no silent fallback).
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np

import srmech
from srmech.amsc.laplacian import dense_laplacian, hermitian_eigendecompose
from srmech.amsc.hdc import bundle, similarity
from srmech.amsc.format import sha256_bytes
from srmech.signal_processing import mint_vector


HERE = Path(__file__).parent
OUT_DIR = (HERE.parent / "catalogs" / "rbs_lm_substrate" / "substrate_measurements")
OUT_NDJSON = OUT_DIR / "r148_cross_nav.ndjson"

SEED = 20260530
D = 8192                      # BSC dimension (Class M)
KERNEL_N_EIGVECS = 160        # vocab cap / max eigvecs per kernel
M_PER_EIGVEC = 21             # top tokens per eigvec row
COOCC_DIST = 5                # co-occurrence window
TOP_K_RANKS = 3               # ranks each probe token walks
TOP_N_EMIT = 7                # tokens emitted per chosen rank
N_PROBE_FRAGMENTS = 6
HOLDOUT_FRACTION = 0.12

# --- corpora (real, public-domain; fetched to /tmp) ---
GRAMMAR_FILES = [
    {"path": "/tmp/mcguffey_pg14640.txt", "pg": 14640, "label": "McGuffey First Reader"},
    {"path": "/tmp/mcguffey_pg14668.txt", "pg": 14668, "label": "McGuffey Second Reader"},
]
LOGIC_FILES = [
    {"path": "/tmp/logic_pg28696.txt", "pg": 28696, "label": "Carroll Symbolic Logic"},
    {"path": "/tmp/logic_pg4763.txt",  "pg": 4763,  "label": "Carroll Game of Logic"},
]
GUTENBERG_URL = "https://www.gutenberg.org/cache/epub/{id}/pg{id}.txt"

STOPWORDS_EN = set("""
the a an and or but if then else of in on at to for with by from as is are
was were be been being have has had having do does did doing done will
would shall should may might can could not no this that these those it its
they them their there here he she we us our you your i me my mine yours
which what who whom whose where when why how all any some none many much
more most less few several each every both either neither so such only also
than just too very etc ie eg via vs per pre post sub super o thee thou thy ye
hath said say let us our
""".split())


# ----------------------------------------------------------------------
# text -> kernel (Class L eigvec table) + Class M per-row bundle
# ----------------------------------------------------------------------
_MINT_CACHE = {}


def mint(token):
    v = _MINT_CACHE.get(token)
    if v is None:
        v = mint_vector(token, D=D)
        _MINT_CACHE[token] = v
    return v


MAX_BUNDLE_N = 257  # srmech bundle wants an odd count; chunk large sets


def bsc_bundle(tokens):
    """Bundle a list of tokens into one BSC vector via Class M hdc.bundle.
    Hierarchical so it scales past MAX_BUNDLE_N; pads to odd count."""
    vecs = [mint(t) for t in tokens]
    if not vecs:
        return mint("__empty__")
    if len(vecs) == 1:
        return vecs[0]
    if len(vecs) <= MAX_BUNDLE_N:
        if len(vecs) % 2 == 0:
            vecs = vecs + [vecs[0]]
        return bundle(vecs)
    chunk = MAX_BUNDLE_N - 2
    partials = []
    for i in range(0, len(vecs), chunk):
        ch = vecs[i:i + chunk]
        if len(ch) % 2 == 0:
            ch = ch + [ch[0]]
        partials.append(bundle(ch))
    if len(partials) % 2 == 0:
        partials = partials + [partials[0]]
    return bundle(partials)


def tokenize(text):
    raw = re.findall(r"[A-Za-z][A-Za-z0-9'-]*[A-Za-z0-9]|[A-Za-z]", text)
    return [t.lower() for t in raw if t.lower() not in STOPWORDS_EN and len(t) >= 2]


def strip_gutenberg(text):
    s = re.search(r"\*\*\* START OF (THE )?PROJECT GUTENBERG", text)
    e = re.search(r"\*\*\* END OF (THE )?PROJECT GUTENBERG", text)
    if s:
        text = text[s.end():]
    if e:
        text = text[:e.start()]
    return text.strip()


def chunk_text(text, n_chunks=64):
    raw = re.split(r"\n\s*\n+", text)
    out, cur, sz = [], [], 0
    target = max(len(text) // n_chunks, 800)
    for c in raw:
        cur.append(c)
        sz += len(c)
        if sz >= target:
            out.append("\n".join(cur))
            cur = []
            sz = 0
    if cur:
        out.append("\n".join(cur))
    return out


def build_kernel(text):
    """Return (table, vocab, idx_map, freq). table rows carry the FULL real
    eigvec (Class L) and a Class M BSC bundle of the row's top tokens."""
    chunks = chunk_text(text)
    filt = [tokenize(c) for c in chunks]
    all_t = [t for toks in filt for t in toks]
    freq = Counter(all_t)                      # edge/freq tally only (feeds Class L / draw)
    N = min(KERNEL_N_EIGVECS, len(freq))
    if N < 8:
        return None, None, None, None
    vocab = [t for t, _ in freq.most_common(N)]
    idx_map = {t: i for i, t in enumerate(vocab)}
    edges = Counter()
    for toks in filt:
        idx = [idx_map[t] for t in toks if t in idx_map]
        for i in range(len(idx)):
            for j in range(i + 1, min(i + COOCC_DIST, len(idx))):
                a, b = idx[i], idx[j]
                if a == b:
                    continue
                edges[(min(a, b), max(a, b))] += 1
    if not edges:
        return None, None, None, None
    L = dense_laplacian(N, list(edges.keys()), [float(w) for w in edges.values()])
    ev, evc = hermitian_eigendecompose(L)      # Class L; NO np.linalg.eig*
    table = []
    for k in range(len(ev) - 1, -1, -1):
        eigvec = evc[:, k].real
        mag_sq = eigvec * eigvec
        top_idx = np.argsort(-mag_sq)[:M_PER_EIGVEC]
        top_tokens = [vocab[i] for i in top_idx]
        table.append({
            "rank": len(ev) - 1 - k,
            "eigval": float(np.real(ev[k])),
            "top_tokens": top_tokens,
            "bundle": bsc_bundle(top_tokens),   # Class M
            "eigvec_full": eigvec,
        })
    return table, vocab, idx_map, freq


# ----------------------------------------------------------------------
# find-cascade: align A-table rows -> best B-table rows (Class M similarity)
# ----------------------------------------------------------------------
def cross_alignment(table_A, table_B):
    """For each A row, similarity to its best-matching B row (greedy unique).
    Returns dict A_pos -> (B_pos, sim). Class M Hamming-BSC similarity."""
    nA, nB = len(table_A), len(table_B)
    sim = np.zeros((nA, nB))
    for i in range(nA):
        bi = table_A[i]["bundle"]
        for j in range(nB):
            sim[i, j] = similarity(bi, table_B[j]["bundle"])
    used = set()
    align = {}
    a_order = sorted(range(nA), key=lambda i: -sim[i].max())
    for i in a_order:
        cands = [(j, sim[i, j]) for j in range(nB) if j not in used]
        if not cands:
            continue
        bj, s = max(cands, key=lambda x: x[1])
        used.add(bj)
        align[i] = (bj, float(s))
    return align


# ----------------------------------------------------------------------
# the steered ride. weight_fn(token_idx_in_A_vocab, anchor_table) -> per-A-rank weights
# ----------------------------------------------------------------------
def rank_weights_withinA(table_A, vocab_idx):
    """(b) within-A: weight each A-rank by |eigvec[token]|^2 (plain 54g ride)."""
    return np.array([float(row["eigvec_full"][vocab_idx] ** 2) for row in table_A])


def rank_weights_steered(table_A, vocab_idx, steer_per_rank):
    """(a)/(c): within-A magnitude MULTIPLIED by a per-A-rank steering weight.
    For (a) steer = the A->B alignment similarity of that A-rank (logic content).
    For (c) steer = a seeded random permutation of the SAME similarities (shape
    kept, content destroyed)."""
    base = np.array([float(row["eigvec_full"][vocab_idx] ** 2) for row in table_A])
    return base * steer_per_rank


def ride(table_A, idx_map_A, probe_text, weight_vector_fn):
    """Walk each probe token's top-k A-ranks (chosen by weight_vector_fn),
    emit A-vocab tokens from those ranks. Returns Counter of emitted tokens."""
    emitted = Counter()
    for atok in tokenize(probe_text):
        vi = idx_map_A.get(atok)
        if vi is None:
            continue
        w = weight_vector_fn(vi)
        order = np.argsort(-w)
        for rank_pos in order[:TOP_K_RANKS]:
            if w[rank_pos] <= 1e-12:
                break
            for t in table_A[rank_pos]["top_tokens"][:TOP_N_EMIT]:
                emitted[t] += 1.0
    return emitted


# ----------------------------------------------------------------------
# probe split + grammar target signature (Class M)
# ----------------------------------------------------------------------
def split_holdout(text):
    n = len(text)
    split = int(n * (1 - HOLDOUT_FRACTION))
    train, holdout = text[:split], text[split:]
    chunks = []
    csz = max(len(holdout) // N_PROBE_FRAGMENTS, 1500)
    for i in range(0, len(holdout), csz):
        ch = holdout[i:i + csz]
        if len(ch) >= 600:
            chunks.append(ch)
        if len(chunks) >= N_PROBE_FRAGMENTS:
            break
    return train, chunks


def target_signature(probe_text, vocab_A_set):
    """Class M bundle of the probe fragment's own most-frequent A-vocab tokens.
    This is the genuine held-out grammar target the walk should land near."""
    toks = [t for t in tokenize(probe_text) if t in vocab_A_set]
    if not toks:
        return None, 0
    top = [t for t, _ in Counter(toks).most_common(40)]
    return bsc_bundle(top), len(top)


def emit_metric(emitted, target_bundle, top_n=40):
    """metric = Class M similarity(bundle(top emitted tokens), grammar target)."""
    if not emitted or target_bundle is None:
        return 0.0
    top = [t for t, _ in emitted.most_common(top_n)]
    return float(similarity(bsc_bundle(top), target_bundle))


# ----------------------------------------------------------------------
def ensure_files(spec):
    missing = [s for s in spec if not Path(s["path"]).exists() or Path(s["path"]).stat().st_size == 0]
    if missing:
        print("BLOCKED — missing corpus file(s). Fetch (public domain) then re-run:", file=sys.stderr)
        for s in missing:
            print(f'  curl -fsSL "{GUTENBERG_URL.format(id=s["pg"])}" -o {s["path"]}', file=sys.stderr)
        sys.exit(99)


def load_corpus(spec):
    bodies, attest = [], []
    for s in spec:
        raw = Path(s["path"]).read_text(encoding="utf-8", errors="replace")
        body = strip_gutenberg(raw)
        bodies.append(body)
        attest.append({
            "label": s["label"], "gutenberg_pg": s["pg"],
            "source_url": GUTENBERG_URL.format(id=s["pg"]),
            "body_chars": len(body),
            "body_sha256": sha256_bytes(body.encode("utf-8")),   # Class A
        })
    return "\n\n".join(bodies), attest


def main():
    rng = np.random.default_rng(SEED)
    print(f"=== R-RBS-LM-148 — cross-navigation Part 2: grammar(A) walked via logic(B) ===")
    print(f"srmech: {srmech.__version__}")

    ensure_files(GRAMMAR_FILES)
    ensure_files(LOGIC_FILES)

    grammar_text, grammar_attest = load_corpus(GRAMMAR_FILES)
    logic_text, logic_attest = load_corpus(LOGIC_FILES)

    print("\n--- corpora ---")
    for a in grammar_attest + logic_attest:
        print(f"  {a['label']:<26s} PG{a['gutenberg_pg']:<6d} {a['body_chars']:>7d} chars  sha256={a['body_sha256'][:12]}…")

    # Build kernel A (grammar): train on 88%, hold out 12% as probes/targets.
    train_A, probes = split_holdout(grammar_text)
    table_A, vocab_A, idx_A, freq_A = build_kernel(train_A)
    # Kernel B (logic): full text (it is the navigator, not the probe source).
    table_B, vocab_B, idx_B, freq_B = build_kernel(logic_text)
    if table_A is None or table_B is None:
        print("BLOCKED — kernel build failed (corpus too small after filtering).", file=sys.stderr)
        sys.exit(98)
    vocab_A_set = set(vocab_A)
    print(f"\nkernel A (grammar): {len(table_A)} eigvecs, vocab {len(vocab_A)}; {len(probes)} held-out probes")
    print(f"kernel B (logic):   {len(table_B)} eigvecs, vocab {len(vocab_B)}")

    # A->B find-cascade alignment (Class M). The per-A-rank similarity to its
    # best LOGIC eigvec IS the logic-derived steering content.
    align_AB = cross_alignment(table_A, table_B)
    steer_logic = np.array([max(align_AB.get(i, (None, 0.0))[1], 0.0) for i in range(len(table_A))])
    # Normalize to mean 1 so steering re-weights without changing overall scale.
    if steer_logic.sum() > 0:
        steer_logic = steer_logic / steer_logic.mean()
    else:
        steer_logic = np.ones(len(table_A))
    mean_align = float(np.mean([s for (_, s) in align_AB.values()])) if align_AB else 0.0
    print(f"A->B mean cross-alignment similarity: {mean_align:+.4f}")

    # (c) random-anchor: a seeded permutation of the SAME steering weights
    # (kills which-A-rank-maps-to-logic content, keeps the weight distribution).
    steer_random = steer_logic.copy()
    rng.shuffle(steer_random)

    # frequency-weighted draw floor (54k baseline).
    fw = np.array([freq_A.get(t, 1) for t in vocab_A], dtype=float)
    fw = fw / fw.sum()

    # ---- run all conditions over the held-out grammar probes ----
    rows = {"b_withinA": [], "a_Banchor": [], "c_random_anchor": [], "floor_freqdraw": []}
    per_probe = []
    for pi, probe in enumerate(probes):
        tgt_bundle, tgt_n = target_signature(probe, vocab_A_set)
        if tgt_bundle is None:
            continue

        # (b) within-A baseline
        emit_b = ride(table_A, idx_A, probe, lambda vi: rank_weights_withinA(table_A, vi))
        m_b = emit_metric(emit_b, tgt_bundle)

        # (a) B-anchor-conditioned (logic steers the A walk)
        emit_a = ride(table_A, idx_A, probe,
                      lambda vi: rank_weights_steered(table_A, vi, steer_logic))
        m_a = emit_metric(emit_a, tgt_bundle)

        # (c) random-anchor control
        emit_c = ride(table_A, idx_A, probe,
                      lambda vi: rank_weights_steered(table_A, vi, steer_random))
        m_c = emit_metric(emit_c, tgt_bundle)

        # floor: frequency-weighted random emission of matched size
        n_emit = max(sum(emit_b.values()), 1)
        draw = rng.choice(len(vocab_A), size=int(min(n_emit, 1200)), p=fw, replace=True)
        emit_f = Counter(vocab_A[i] for i in draw)
        m_f = emit_metric(emit_f, tgt_bundle)

        rows["b_withinA"].append(m_b)
        rows["a_Banchor"].append(m_a)
        rows["c_random_anchor"].append(m_c)
        rows["floor_freqdraw"].append(m_f)
        per_probe.append({"probe": pi, "target_n": tgt_n,
                          "a_Banchor": m_a, "b_withinA": m_b,
                          "c_random_anchor": m_c, "floor_freqdraw": m_f})

    def stat(key):
        v = np.array(rows[key])
        return float(v.mean()), float(v.std(ddof=1)) if len(v) > 1 else 0.0, len(v)

    m_a, s_a, n = stat("a_Banchor")
    m_b, s_b, _ = stat("b_withinA")
    m_c, s_c, _ = stat("c_random_anchor")
    m_f, s_f, _ = stat("floor_freqdraw")

    # ---- verdict against the PRE-STATED null ----
    d_a_vs_c = m_a - m_c                              # cross-steer effect vs random anchor
    d_a_vs_b = m_a - m_b                              # cross-steer effect vs within-A
    noise = max(s_a, s_c) / max(n ** 0.5, 1)          # SE-scale band
    # sign-free magnitude of the effect = the Class-K pin-slot fold (|x| = sqrt(x^2)),
    # NOT python abs(); the SIGN of d_a_vs_c is read separately below (Class C).
    mag_a_vs_c = (d_a_vs_c * d_a_vs_c) ** 0.5
    distinguishable = mag_a_vs_c > 2 * noise           # 2-SE separation gate

    print("\n=== RESULTS (Class M similarity of steered-walk emission to held-out grammar target) ===")
    print(f"  (a) B-anchor (logic-steered) : {m_a:+.4f}  ± {s_a:.4f}  (n={n})")
    print(f"  (b) within-A baseline        : {m_b:+.4f}  ± {s_b:.4f}")
    print(f"  (c) random-anchor control    : {m_c:+.4f}  ± {s_c:.4f}")
    print(f"  floor: freq-weighted draw    : {m_f:+.4f}  ± {s_f:.4f}")
    print(f"\n  Δ (a−c) B-anchor vs random-anchor : {d_a_vs_c:+.4f}   (2·SE band ≈ {2*noise:.4f})")
    print(f"  Δ (a−b) B-anchor vs within-A      : {d_a_vs_b:+.4f}")

    if not distinguishable:
        verdict = ("NULL (H0 NOT REJECTED): the B-anchor (logic-steered) walk is "
                   "INDISTINGUISHABLE from the random-anchor control (|Δ| within the "
                   "2·SE band). No real cross-domain steering — the logic kernel does "
                   "nothing a random kernel of matched size would not. Framework-reading.")
        tier = "FRAMEWORK-READING"
    elif d_a_vs_c > 0:
        verdict = (f"CROSS-STEERING POSITIVE: logic-anchored walk beats random-anchor by "
                   f"{d_a_vs_c:+.4f} (> 2·SE). Logic's structure measurably steers the "
                   f"grammar walk toward held-out grammar. vs within-A: {d_a_vs_b:+.4f}.")
        tier = "DEMONSTRATED" if d_a_vs_b > 2 * noise else "FRAMEWORK-READING"
    else:
        verdict = (f"CROSS-STEERING NEGATIVE: logic-anchored walk is WORSE than the "
                   f"random-anchor control by {d_a_vs_c:+.4f} (< -2·SE) — logic steering "
                   f"actively degrades the grammar walk vs a shape-matched random anchor.")
        tier = "DEMONSTRATED"

    print(f"\n=== VERDICT [{tier}] ===\n  {verdict}")

    # ---- write NDJSON ----
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    recs = []
    recs.append({
        "finding": "F205", "experiment": "R-RBS-LM-148", "record": "attestation",
        "title": "cross-navigation Part 2 — grammar(A) walked via logic(B)",
        "attestation": {
            "tool": f"srmech=={srmech.__version__}",
            "interpreter": "/home/skirklan/.venvs/srmech/bin/python3 (native ON)",
            "seed": SEED, "D": D,
            "ops": ("Class L srmech.amsc.laplacian.{dense_laplacian,hermitian_eigendecompose}; "
                    "Class M srmech.amsc.hdc.{bundle,similarity} + signal_processing.mint_vector; "
                    "Class A srmech.amsc.format.sha256_bytes"),
            "grammar_kernel_A": grammar_attest,
            "logic_kernel_B": logic_attest,
            "params": {"KERNEL_N_EIGVECS": KERNEL_N_EIGVECS, "M_PER_EIGVEC": M_PER_EIGVEC,
                       "COOCC_DIST": COOCC_DIST, "TOP_K_RANKS": TOP_K_RANKS,
                       "TOP_N_EMIT": TOP_N_EMIT, "HOLDOUT_FRACTION": HOLDOUT_FRACTION,
                       "n_probes": n},
            "predecessors": ["F165", "F163", "F44-F50 (R-53)", "R-54f", "R-54g", "R-54k", "F164", "F73"],
            "scope": ("MFO VII.6.20 form-reading only; STRUCTURAL PLAY per F163 §9 — no claim "
                      "that logic transfers meaning into grammar; no doctrinal claims; texts are "
                      "structural test-objects; no abs(); no np.linalg.eig*; no hashlib.sha256; "
                      "no hand-rolled cosine (Class M similarity); Counter only feeds Laplacian/bundle"),
            "PR": "#687 STAYS DRAFT",
        },
    })
    recs.append({
        "finding": "F205", "experiment": "R-RBS-LM-148", "record": "prestated_null",
        "H0": ("the B-anchor (logic-steered) walk is INDISTINGUISHABLE from the random-anchor "
               "control: |metric_a - metric_c| within the 2*SE noise band => no cross-domain steering"),
        "metric": "Class M similarity(bundle(top emitted A-tokens), held-out grammar target bundle)",
        "decision_gate": "distinguishable iff |Δ(a−c)| > 2·SE(across probes)",
    })
    recs.append({
        "finding": "F205", "experiment": "R-RBS-LM-148", "record": "cross_alignment",
        "A_to_B_mean_similarity": mean_align,
        "steer_logic_mean": 1.0, "steer_logic_max": float(steer_logic.max()),
        "n_A_eigvecs": len(table_A), "n_B_eigvecs": len(table_B),
        "vocab_A": len(vocab_A), "vocab_B": len(vocab_B),
    })
    recs.append({
        "finding": "F205", "experiment": "R-RBS-LM-148", "record": "conditions",
        "a_Banchor": {"mean": m_a, "std": s_a, "n": n},
        "b_withinA": {"mean": m_b, "std": s_b},
        "c_random_anchor": {"mean": m_c, "std": s_c},
        "floor_freqdraw": {"mean": m_f, "std": s_f},
        "delta_a_minus_c": d_a_vs_c, "delta_a_minus_b": d_a_vs_b,
        "two_SE_band": 2 * noise, "distinguishable": bool(distinguishable),
    })
    for p in per_probe:
        recs.append({"finding": "F205", "experiment": "R-RBS-LM-148", "record": "per_probe", **p})
    recs.append({
        "finding": "F205", "experiment": "R-RBS-LM-148", "record": "verdict",
        "tier": tier, "verdict": verdict,
        "null_rejected": bool(distinguishable),
    })

    with open(OUT_NDJSON, "w") as fh:
        for r in recs:
            fh.write(json.dumps(r) + "\n")
    print(f"\nNDJSON: {OUT_NDJSON}  ({len(recs)} records)")


if __name__ == "__main__":
    main()
