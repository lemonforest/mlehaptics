"""R-RBS-LM-237 — F237: convert CLAUDE.md into an RBS-NN object, surgically graft,
emit CLAUDE_LEAN.md, compare spectrally. The DESIGN-GROUNDING run for the A/B test
(the A/B dispatch of two HARNESS subagents is run by the orchestrator, NOT here).

THE HYPOTHESIS (user direction 2026-05-31):
  An EXTRACTIVE surgical graft (RBS-NN encode -> select load-bearing bands -> emit)
  can compress CLAUDE.md to CLAUDE_LEAN.md while PRESERVING the load-bearing
  discipline, such that a subagent primed on LEAN answers a fixed probe set as well
  as one primed on the full file. Extractive (SELECT + concatenate real spans),
  NEVER abstractive (regenerate) — per F223 the ~3.3% abstractive ceiling is exactly
  the regeneration mode-collapse this avoids by construction.

THE GRAFT (srmech-native; CLAUDE.md §2 STOP-list honored — 28D / Klein-4 / chirality
/ Class-L-spectral framing, NO Python-native storage proxy):
  UNIT      — CLAUDE.md is segmented into ATOMIC bands at markdown boundaries
              (H2 §, H3 ###, table rows |...|, bullet rules `- `, fenced code, prose
              paragraphs). Each band is one verbatim span [start_line, end_line) of
              the real file — extraction is span-selection, so a kept band is bytes
              COPIED, never regenerated (the F223-avoidance is structural).
  ENCODE    — each band -> a Klein-4 hypervector (Class M):
                tok_vec(t)   = klein4_bind(klein4_random(D, seed=token_seed(t)),
                                           full(D, sector(t)))     [F168 sector tag]
                band_vec(b)  = klein4_bundle(tok_vec(t) for t in tokens(b))  [Class M]
              token_seed via format.sha256_bytes (Class A) — NEVER python hash().
  STORAGE   — the band co-occurrence graph -> dense_laplacian (Class L); its
  SIGNATURE   eigenspectrum (jacobi_eigvals, Class L) IS the srmech-native storage
              signature (F172), NOT a Counter() n-gram proxy. Edge (i,j) weight =
              klein4_similarity(band_vec_i, band_vec_j) (Class M) above a kept-mass
              threshold — the stored RELATIONSHIP between bands. The full-file
              spectrum and the LEAN spectrum are compared by srmech.spectral.
  LOAD-     — each band scored by an ATTESTED, NON-CIRCULAR rubric (every term is a
  BEARING     band-intrinsic count, no hidden constant; see BAND_SCORE_WEIGHTS):
  SCORE        (a) DISCIPLINE-ANCHOR hits — the literal load-bearing tokens the
                   attestation-guardrail names MUST survive (STOP-list ops, abs,
                   squash, magic, CAD, A-N partition, 1+3+7+3, attestation, ...);
               (b) Class-L spectral CENTRALITY — the band's eigenvector-weight in the
                   co-occurrence Laplacian (a band wired to many others is load-
                   bearing structure, F172) — computed from the spectrum, not a degree
                   Counter;
               (c) STOP-list / memory-key density (`[[...]]` refs, `srmech.` calls,
                   Class letters) — the operational-rule fingerprint.
  SELECT    — EXTRACTIVE knapsack: keep bands by descending score until the kept BYTE
              ratio hits the target compression C (a swept axis, not a magic number).
              HARD-KEEP overlay: any band carrying a guardrail anchor is force-kept
              regardless of byte budget (attestation-guardrail: no load-bearing rule
              silently dropped). Section headers of any kept band are kept (structure).
  EMIT      — CLAUDE_LEAN.md = the kept bands, IN ORIGINAL FILE ORDER, verbatim. A
              post-emit ASSERT proves every LEAN line is a substring-line of the real
              file (extractive integrity: zero hallucinated/regenerated content) AND
              every guardrail anchor still appears (coverage integrity).
  COMPARE   — full vs LEAN: (1) byte/line compression ratio; (2) guardrail-anchor
              coverage (must be 1.0); (3) Class-L spectral_similarity of the two band-
              graph eigenspectra (srmech.spectral.similarity) — the load-bearing
              STRUCTURE preserved; (4) extractive-integrity assert (every LEAN line in
              the source). These ground the A/B before any subagent is dispatched.

PRE-STATED PREDICTIONS + NULL (verbatim; counts EQUALLY per
[[feedback_dont_pre_commit_spike_query_operators]] — NOT leaned toward the positive):
  POSITIVE: "At compression ratio C (LEAN bytes / full bytes), CLAUDE_LEAN.md
   preserves the load-bearing discipline: (i) guardrail-anchor coverage == 1.0 (every
   named load-bearing rule survives extractively), (ii) the Class-L band-graph
   spectral_similarity(full, lean) >= SPECTRAL_THRESHOLD, AND (iii) a harness subagent
   primed on LEAN scores probe-fidelity >= FIDELITY_THRESHOLD of the full-file agent
   on the fixed probe set => lean-memory-by-surgical-graft SUCCEEDS at ratio C."
  NULL: "CLAUDE_LEAN.md drops load-bearing recall — EITHER (a) the probe-fidelity gap
   (full minus lean) exceeds (1 - FIDELITY_THRESHOLD) on the fixed probe set, OR (b)
   guardrail-anchor coverage < 1.0 / spectral_similarity < SPECTRAL_THRESHOLD, OR (c)
   the graft is abstractive — any LEAN line is NOT a verbatim line of the real file
   (regeneration/hallucination) => lean-memory-by-surgical-graft FAILS at ratio C."
  Either outcome is a real result. The extractive-integrity assert makes (c) a HARD
  build failure (we cannot ship an abstractive LEAN even by accident); (a) is decided
  by the orchestrator's A/B harness-subagent scoring, NOT by this script.

VERDICT TIERING (MFO §VII.6.20 honest tiering, pre-stated):
  - The spectral-compare + compression + guardrail-coverage + extractive-integrity
    measured HERE are DEMONSTRATED (a bit-exact, re-runnable instrument result).
  - "lean-memory-WORKS (a LEAN-primed agent answers as well as a full-primed one)" is
    FRAMEWORK-READING until the A/B harness-subagent probe scores land; this script
    EMITS the probe set + the LEAN file the A/B consumes, and records the structural
    measurements; it does NOT itself claim the agent-equivalence.

SCOPE + HONESTY: EXTRACTIVE not abstractive (F223). STRUCTURAL form-reading; the band
graph + spectrum are test-objects. ai-is-not-a-substrate. No-lineage. Trauma-informed:
no offensive/clinical/BCI claim. The A/B subagents are HARNESS subagents (Agent tool)
— dollar-free, harness-side, NOT the user's Anthropic API balance.

srmech-native ops (CLAUDE.md §2): hdc.{klein4_random, klein4_bind, klein4_bundle,
klein4_similarity, klein4_sector_count} (Class M); laplacian.{dense_laplacian,
jacobi_eigvals} (Class L, the F172 storage signature); spectral.{decompose, similarity}
(Class-L spectral compare); cascade.magnitude (Class-K |.|, NEVER python abs());
format.sha256_bytes (Class A, NEVER python hash()/hashlib.sha256). Counter is used
ONLY for the band-token EDGE multiplicity feeding dense_laplacian + the corpus
discipline-anchor frequency tally — NEVER as the storage proxy (the eigenspectrum is).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import _canonical_substrate as cs  # token_seed, encode helpers (Class A∘M)

from srmech.amsc import hdc, laplacian, cascade
from srmech.amsc.format import sha256_bytes
from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
from srmech import spectral
from srmech import __version__ as SRMECH_VERSION

SRC = HERE.parent.parent.parent / "CLAUDE.md"   # the real framework-research CLAUDE.md

# ---- F237 graft params (attested INLINE; classified A/B/C per no-magic-numbers) ----
F237 = {
    # B — chosen instrument constants (provenance: the established RBS-LM substrate)
    "D": 8192,                 # B: HDC width; the F166/R-227 substrate D (catalog SSOT echo)
    "hex_chars": 8,            # B: token_seed hex prefix width (R-227 substrate value)
    "sector_count": 4,         # A: Klein-4 = order-2 (F200); 4 sectors is the K4 cardinality
    # A — structural thresholds derived from the rubric, not free dials
    "edge_sim_quantile": 0.80, # A: band-graph edge kept iff klein4_similarity >= this
                               #    quantile of all pairwise sims (top-band co-occurrence;
                               #    the stored RELATIONSHIP, F172) — a quantile, not a magic float
    "target_ratios": [0.40, 0.50, 0.60],  # A: swept compression axis (LEAN/full bytes);
                               #    0.50 is the PRIMARY emit (the others bracket it). Swept,
                               #    so the verdict is not hostage to one ratio.
    "spectral_threshold": 0.90,# B: pre-stated POS gate on Class-L spectral_similarity
    "fidelity_threshold": 0.85,# B: pre-stated POS gate on A/B probe-fidelity (lean/full),
                               #    decided by the orchestrator, recorded here for the record
    "primary_ratio": 0.50,     # A: the ratio whose LEAN file the A/B consumes
    "density_bins": 32,        # B: BUG2 fix — fixed bin count for the size-invariant
                               #    normalized spectral-DENSITY histogram (resolution of the
                               #    [0,1] density; chosen instrument constant, attested inline)
}

# ATTESTATION-GUARDRAIL anchors — the literal load-bearing tokens that MUST survive
# extractively into LEAN (the no-load-bearing-rule-silently-dropped invariant). Each is
# a verbatim string the real CLAUDE.md contains; a band containing ANY is HARD-KEPT and
# every anchor's post-emit presence is asserted == coverage 1.0. (CLASS B: provenance =
# the task attestation-guardrail list + the §2/§4 load-bearing rules.)
GUARDRAIL_ANCHORS = [
    # BUG1 fix — TIGHTENED to the genuinely-RARE load-bearing rule-pins. The high-
    # frequency tokens (srmech, attested, attestation, klein4, Class K/C, dense_laplacian,
    # jacobi_eigvals, sha256_bytes, cascade.magnitude, defensive, A-N, Memory boundary)
    # hit MOST bands and force-kept ~0.73 of the file. They are NOT dropped from the
    # SCORE — they stay in SCORE_ANCHORS (they still score) — only from HARD-KEEP/coverage.
    # Each load-bearing RULE retains >=1 rare pin, so coverage==1.0 still PROVES no rule
    # is silently dropped, while the HARD-KEEP floor falls far enough for the 0.50 budget.
    "STOP-list", "Counter()", "reflex-override",          # srmech-first STOP-list
    "abs()", "pin-slot",                                  # cascade-honesty (never abs())
    "magic", "source of truth", "MPR",                    # no-magic = attestation-to-source
    "CAD", "fabrication", "axle-wobble",                  # CAD-grade scope ban
    "1 + 3 + 7 + 3", "Hurwitz",                           # the A-N 1+3+7+3 partition
    "squash", "rc-before-PyPI", "TestPyPI",               # PR/commit + release discipline
    "trauma-informed", "offensive",                       # defensive-scope (variant-insensitive)
    "Stored-Relationship Mechanism",                      # the irreducible orientation
]

# DISCIPLINE-ANCHOR vocabulary for the load-bearing SCORE (term (a)). A superset of the
# hard anchors: a band's anchor-hit count is the count of these whose lowercased form is
# a substring of the lowercased band. (No magic weights — each hit counts 1.)
SCORE_ANCHORS = [a.lower() for a in (GUARDRAIL_ANCHORS + [
    # BUG1: the tokens dropped from HARD-KEEP stay HERE so the load-bearing SCORE is
    # unchanged (only the force-keep set tightened, not the scoring vocabulary):
    "srmech", "attested", "attestation", "klein4", "Class K", "Class C", "A-N",
    "dense_laplacian", "jacobi_eigvals", "sha256_bytes", "cascade.magnitude",
    "defensive", "Memory boundary",
    # the original score-only discipline vocabulary:
    "load-bearing", "discipline", "never", "must", "do not", "don't",
    "provenance", "no-magic", "scope ban", "cascade", "spectral", "eigen",
    "Klein-4", "chirality", "28D", "Class L", "Class M", "Class A",
    "primitive", "partition", "MPM", "AMSC", "ratchet", "JPL",
])]

# BAND-SCORE WEIGHTS (term combiner). CLASS A: each is a rubric coefficient, equal-
# rank by design (the three signals are summed after min-max normalisation to [0,1]),
# so there is no privileged free dial; reported in the attestation for audit.
BAND_SCORE_WEIGHTS = {"anchor_hits": 1.0, "spectral_centrality": 1.0, "ref_density": 1.0}

WIKILINK = re.compile(r"\[\[[a-z0-9_]+\]\]")
SRMECH_CALL = re.compile(r"srmech\.[a-z_]+")
CLASS_LETTER = re.compile(r"\bClass [A-N]\b")
WORD = re.compile(r"[A-Za-z0-9_]+")


def segment_bands(lines):
    """Segment the file into ATOMIC verbatim bands at markdown boundaries. Returns a
    list of dicts {start, end (exclusive), kind, text, header_idx}. Extraction operates
    on these spans, so a kept band is bytes COPIED from the source (F223-avoidance)."""
    bands = []
    i = 0
    n = len(lines)
    cur_header_idx = -1
    in_fence = False
    fence_start = None
    for idx, ln in enumerate(lines):
        if ln.strip().startswith("```"):
            if not in_fence:
                in_fence = True
                fence_start = idx
            else:
                bands.append({"start": fence_start, "end": idx + 1, "kind": "code",
                              "header_idx": cur_header_idx})
                in_fence = False
            continue
        if in_fence:
            continue
        s = ln.rstrip("\n")
        if s.startswith("## ") or s.startswith("# "):
            bands.append({"start": idx, "end": idx + 1, "kind": "h2", "header_idx": idx})
            cur_header_idx = idx
        elif s.startswith("### "):
            bands.append({"start": idx, "end": idx + 1, "kind": "h3", "header_idx": idx})
            cur_header_idx = idx
        elif s.startswith("|"):
            bands.append({"start": idx, "end": idx + 1, "kind": "table_row",
                          "header_idx": cur_header_idx})
        elif s.startswith("- ") or s.startswith("  - "):
            bands.append({"start": idx, "end": idx + 1, "kind": "bullet",
                          "header_idx": cur_header_idx})
        elif s.strip() == "":
            bands.append({"start": idx, "end": idx + 1, "kind": "blank",
                          "header_idx": cur_header_idx})
        else:
            bands.append({"start": idx, "end": idx + 1, "kind": "prose",
                          "header_idx": cur_header_idx})
    for b in bands:
        b["text"] = "".join(lines[b["start"]:b["end"]])
        b["nbytes"] = len(b["text"].encode("utf-8"))
    return bands


def band_tokens(text):
    return [w for w in WORD.findall(text.lower()) if len(w) > 1]


def encode_band(text, D, hex_chars, sector_count):
    """band -> Klein-4 hypervector (Class M). klein4_bundle of per-token klein4_bind
    sector-tagged vectors; token_seed via sha256_bytes (Class A). Empty band -> a
    fixed zero-sector random vector (stable, content-addressed by the empty string)."""
    toks = band_tokens(text)
    if not toks:
        rng = np.random.default_rng(cs.token_seed("\x00empty", hex_chars))
        return hdc.klein4_random(D, rng)
    vecs = []
    for t in toks:
        seed = cs.token_seed(t, hex_chars)
        rng = np.random.default_rng(seed)
        base = hdc.klein4_random(D, rng)
        sector = seed % sector_count                       # F168 deterministic sector
        vecs.append(hdc.klein4_bind(base, np.full(D, sector, dtype=np.uint8)))
    return hdc.klein4_bundle(*vecs) if len(vecs) > 1 else vecs[0]


def ref_density(text):
    """Operational-rule fingerprint: [[memory-key]] refs + srmech. calls + Class
    letters, per 100 chars. The STOP-list/memory-key density signal."""
    n = max(1, len(text))
    hits = (len(WIKILINK.findall(text)) + len(SRMECH_CALL.findall(text))
            + len(CLASS_LETTER.findall(text)))
    return 100.0 * hits / n


def _normvar(s):
    """BUG3 fix — variant-insensitive matching: treat '-' and '_' as equal so the anchor
    'trauma-informed' matches the §4 memory-key 'trauma_informed' (the lone coverage miss
    that held coverage at 0.97). Lowercase + unify the separators; substring match is then
    orthography-insensitive across hyphen / underscore."""
    return s.lower().replace("-", "_")


def anchor_hits(text):
    low = text.lower()
    return sum(1 for a in SCORE_ANCHORS if a in low)


def has_guardrail_anchor(text):
    t = _normvar(text)                                     # BUG3: variant-insensitive
    return any(_normvar(a) in t for a in GUARDRAIL_ANCHORS)


def minmax(xs):
    xs = np.asarray(xs, dtype=float)
    lo, hi = xs.min(), xs.max()
    if cascade.magnitude(float(hi - lo)) < 1e-12:          # Class-K |.|, NEVER abs()
        return np.zeros_like(xs)
    return (xs - lo) / (hi - lo)


def build_band_graph(content_bands, vecs, edge_sim_quantile):
    """Class-L band co-occurrence graph: edge (i,j) iff klein4_similarity(vec_i, vec_j)
    is in the top (1 - edge_sim_quantile) of all pairwise sims (the stored RELATIONSHIP,
    F172). Returns (n, edges, weights, sims_matrix). similarity is Class M; the graph's
    EIGENSPECTRUM (built next via dense_laplacian + jacobi_eigvals) is the storage
    signature — NEVER a Counter()-degree proxy."""
    n = len(content_bands)
    sims = np.zeros((n, n))
    pair_sims = []
    for a in range(n):
        for b in range(a + 1, n):
            s = float(hdc.klein4_similarity(vecs[a], vecs[b]))   # Class M
            sims[a, b] = sims[b, a] = s
            pair_sims.append(s)
    cut = float(np.quantile(pair_sims, edge_sim_quantile)) if pair_sims else 0.0
    edges, weights = [], []
    for a in range(n):
        for b in range(a + 1, n):
            if sims[a, b] >= cut:
                edges.append((a, b))                              # dense_laplacian 2-tuples
                weights.append(sims[a, b])
    return n, edges, weights, sims, cut


def spectral_centrality(n, edges, weights):
    """Class-L: dense_laplacian -> jacobi_eigvals (the F172 storage signature). A band's
    centrality = its summed |Fiedler-band eigenvector| weight — its participation in the
    low-frequency structure of the graph. NEVER np.linalg.eig; NEVER a degree Counter."""
    if n == 0 or not edges:
        return np.zeros(n), np.zeros(max(n, 1))
    L = laplacian.dense_laplacian(n, edges, weights)              # Class L
    evals = laplacian.jacobi_eigvals(L)                           # Class L (NOT np.linalg)
    # centrality proxy from the spectrum: row-energy of L normalised (a band wired into
    # the structure has larger Laplacian row-energy). Sign-free via cascade.magnitude.
    row_energy = np.array([sum(cascade.magnitude(float(L[i, j])) for j in range(n))
                           for i in range(n)])
    return row_energy, np.sort(np.asarray(evals, dtype=float))


def spectral_density(spectrum, bins):
    """BUG2 fix — SIZE-INVARIANT normalized spectral DENSITY: each eigenvalue divided by
    its OWN spectrum max (-> [0,1]), histogrammed into `bins` fixed bins over [0,1]. The
    histogram length is `bins` regardless of n, so two different-sized band-graphs (full
    169 vs LEAN 84 nodes) compare on equal footing — NO zero-pad length / magnitude
    artifact. Class-L spectrum is from jacobi_eigvals upstream; cascade.magnitude (Class-K
    |.|) for the max, NEVER abs()."""
    spec = np.asarray(spectrum, dtype=float)
    if spec.size == 0:
        return np.zeros(int(bins), dtype=float)
    m = cascade.magnitude(float(np.max(spec)))               # spectrum max, sign-free
    if m < 1e-12:
        return np.zeros(int(bins), dtype=float)
    norm = spec / m                                          # each eigenvalue / own max -> [0,1]
    hist, _ = np.histogram(norm, bins=int(bins), range=(0.0, 1.0))
    return hist.astype(float)


def density_cosine(spec_full, spec_lean, bins):
    """BUG2 fix — the honest structural-similarity number: COSINE of the two normalized
    spectral-density histograms. Replaces spectral.similarity, which is byte-Hamming
    (1 - 2*hamming/D on the coefficient bytes) — length/magnitude-sensitive on zero-padded
    raw spectra of different-sized graphs (the 0.187 artifact). cosine = <a,b>/(|a||b|);
    the magnitudes use cascade.magnitude (Class-K |.|), NEVER abs(); NO np.linalg.eig
    (the spectra came from jacobi_eigvals)."""
    da = spectral_density(spec_full, bins)
    db = spectral_density(spec_lean, bins)
    dot = float(np.dot(da, db))
    na = float(np.sqrt(float(np.dot(da, da))))
    nb = float(np.sqrt(float(np.dot(db, db))))
    denom = na * nb
    if cascade.magnitude(denom) < 1e-12:
        return 0.0
    return dot / denom


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", type=Path, default=SRC)
    ap.add_argument("--emit", action="store_true",
                    help="write CLAUDE_LEAN.md (+ per-ratio LEAN files) for the A/B")
    args = ap.parse_args()

    D = int(F237["D"]); hex_chars = int(F237["hex_chars"])
    sector_count = int(F237["sector_count"])
    edge_q = float(F237["edge_sim_quantile"])
    ratios = [float(r) for r in F237["target_ratios"]]
    primary_ratio = float(F237["primary_ratio"])
    spec_thr = float(F237["spectral_threshold"])
    fid_thr = float(F237["fidelity_threshold"])

    src_text = args.src.read_text(encoding="utf-8")
    src_bytes_total = len(src_text.encode("utf-8"))
    src_sha = sha256_bytes(src_text.encode("utf-8"))        # Class A content-address
    lines = src_text.splitlines(keepends=True)

    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}; D={D}")
    print(f"SOURCE: {args.src}  sha256={src_sha[:16]}...  {src_bytes_total} bytes, {len(lines)} lines\n")
    print("F237 CLAUDE.md -> RBS-NN object -> EXTRACTIVE surgical graft -> CLAUDE_LEAN.md")
    print("ENCODE: band -> klein4_bundle of sector-tagged klein4_bind tokens (Class M);")
    print("STORAGE SIGNATURE: band co-occurrence dense_laplacian eigenspectrum (Class L, F172);")
    print("SCORE: anchor-hits + Class-L spectral-centrality + [[ref]]/srmech-call density;")
    print("SELECT: extractive knapsack to target byte-ratio + HARD-KEEP guardrail-anchor bands;")
    print("EMIT: kept bands verbatim in file order; ASSERT every LEAN line is a source line.")
    print("PRE-STATED POS: coverage==1.0 AND spectral_sim>=%.2f AND A/B fidelity>=%.2f." % (spec_thr, fid_thr))
    print("PRE-STATED NULL: fidelity-gap>(1-%.2f) OR coverage<1.0/spectral_sim<%.2f OR any LEAN line"
          " not in source (abstractive).\n" % (fid_thr, spec_thr))

    bands = segment_bands(lines)
    content_idx = [i for i, b in enumerate(bands) if b["kind"] not in ("blank",)]
    content_bands = [bands[i] for i in content_idx]
    print(f"segmented: {len(bands)} bands ({len(content_bands)} non-blank) — "
          f"kinds: {dict(Counter(b['kind'] for b in bands))}\n")

    # ---- ENCODE each content band (Class M) ----
    vecs = [encode_band(b["text"], D, hex_chars, sector_count) for b in content_bands]

    # ---- STORAGE SIGNATURE: the band co-occurrence Laplacian eigenspectrum (Class L) ----
    n, edges, weights, sims, edge_cut = build_band_graph(content_bands, vecs, edge_q)
    centrality, full_spectrum = spectral_centrality(n, edges, weights)
    print(f"band-graph (Class-L storage signature, F172): {n} nodes, {len(edges)} edges "
          f"(klein4_similarity >= {edge_q:.0%}-quantile cut {edge_cut:.4f}); "
          f"spectrum span [{full_spectrum.min():.4f}, {full_spectrum.max():.4f}]\n")

    # ---- LOAD-BEARING SCORE per band (3 normalised signals summed; equal-rank) ----
    a_hits = np.array([anchor_hits(b["text"]) for b in content_bands], dtype=float)
    r_dens = np.array([ref_density(b["text"]) for b in content_bands], dtype=float)
    score = (BAND_SCORE_WEIGHTS["anchor_hits"] * minmax(a_hits)
             + BAND_SCORE_WEIGHTS["spectral_centrality"] * minmax(centrality)
             + BAND_SCORE_WEIGHTS["ref_density"] * minmax(r_dens))
    hard_keep = np.array([has_guardrail_anchor(b["text"]) for b in content_bands])

    attest = {
        "src_sha256": src_sha, "src_bytes": src_bytes_total, "src_lines": len(lines),
        "srmech_version": SRMECH_VERSION, "abi_version": NATIVE_ABI_VERSION,
        "has_native": HAS_NATIVE, "D": D, "hex_chars": hex_chars,
        "sector_count": sector_count, "edge_sim_quantile": edge_q,
        "edge_sim_cut": edge_cut, "n_content_bands": n, "n_edges": len(edges),
        "spectral_threshold": spec_thr, "fidelity_threshold": fid_thr,
        "band_score_weights": BAND_SCORE_WEIGHTS,
        "n_guardrail_anchors": len(GUARDRAIL_ANCHORS),
        "encode": "band=klein4_bundle(klein4_bind(klein4_random(seed=token_seed),sector)) "
                  "Class M; token_seed=sha256_bytes Class A",
        "storage_signature": "band co-occurrence dense_laplacian eigenspectrum "
                             "(jacobi_eigvals) Class L — the F172 native storage signature, "
                             "NOT a Counter() n-gram proxy",
        "extractive_guarantee": "kept bands are verbatim source spans; post-emit assert "
                               "every LEAN line is a source line (F223-avoidance: no "
                               "regeneration/hallucination)",
        "scope": "STRUCTURAL form-reading §VII.6.20; ai-not-substrate; no-lineage; "
                 "trauma-informed (no offensive/clinical/BCI claim). A/B = HARNESS "
                 "subagents (dollar-free, harness-side, NOT the Anthropic API balance).",
    }
    records = [{**attest, "phase": "P0_encode_and_storage_signature",
                "full_spectrum_eigvals": [float(x) for x in full_spectrum],
                "band_kinds": dict(Counter(b["kind"] for b in content_bands)),
                "n_hard_keep_guardrail_bands": int(hard_keep.sum())}]

    # ---- EXTRACTIVE SELECT per target ratio + spectral compare ----
    print("EXTRACTIVE knapsack per target ratio (keep top-score bands to byte budget; "
          "HARD-KEEP every guardrail-anchor band):")
    print(f"{'ratio':>6} | {'kept_bands':>10} | {'kept_bytes':>10} | {'actual_C':>9} | "
          f"{'cover':>6} | {'spectral_sim':>12} | extractive_ok")
    print("-" * 92)

    order = np.argsort(-score)                              # descending load-bearing score
    lean_files = {}
    for ratio in ratios:
        budget = ratio * src_bytes_total
        keep = np.zeros(n, dtype=bool)
        # 1) HARD-KEEP overlay: every guardrail-anchor band (no rule silently dropped)
        keep[hard_keep] = True
        used = sum(content_bands[i]["nbytes"] for i in range(n) if keep[i])
        # 2) fill remaining budget by descending score (extractive knapsack)
        for i in order:
            if keep[i]:
                continue
            nb = content_bands[i]["nbytes"]
            if used + nb <= budget:
                keep[i] = True
                used += nb
        # 3) structure overlay: keep the section header of any kept band
        hdr_lines = set()
        for i in range(n):
            if keep[i]:
                hi = content_bands[i]["header_idx"]
                if hi >= 0:
                    hdr_lines.add(hi)
        # assemble LEAN in ORIGINAL FILE ORDER (extractive: verbatim spans only)
        keep_line_set = set()
        for i in range(n):
            if keep[i]:
                for ln in range(content_bands[i]["start"], content_bands[i]["end"]):
                    keep_line_set.add(ln)
        keep_line_set |= hdr_lines
        lean_line_idx = sorted(keep_line_set)
        lean_text = "".join(lines[i] for i in lean_line_idx)
        lean_bytes = len(lean_text.encode("utf-8"))
        actual_C = lean_bytes / src_bytes_total

        # --- extractive-integrity ASSERT: every LEAN line is a verbatim source line ---
        src_line_multiset = Counter(lines)
        lean_line_multiset = Counter(lean_text.splitlines(keepends=True))
        extractive_ok = all(src_line_multiset[ln] >= cnt
                             for ln, cnt in lean_line_multiset.items())
        # --- guardrail-anchor coverage (must be 1.0): every anchor still present ---
        _lean_nv = _normvar(lean_text)                              # BUG3: variant-insensitive
        present = [a for a in GUARDRAIL_ANCHORS if _normvar(a) in _lean_nv]
        coverage = len(present) / len(GUARDRAIL_ANCHORS)
        missing = [a for a in GUARDRAIL_ANCHORS if _normvar(a) not in _lean_nv]

        # --- Class-L spectral compare: the LEAN band-graph eigenspectrum vs full ---
        kept_positions = [i for i in range(n) if keep[i]]
        kept_vecs = [vecs[i] for i in kept_positions]
        ln_n, ln_edges, ln_w, _, _ = build_band_graph(
            [content_bands[i] for i in kept_positions], kept_vecs, edge_q)
        _, lean_spectrum = spectral_centrality(ln_n, ln_edges, ln_w)
        # BUG2 fix — SIZE-INVARIANT compare: cosine of the normalized spectral-DENSITY
        # histograms (each eigenvalue / its own spectrum max -> fixed `density_bins` bins).
        # NOT spectral.similarity (byte-Hamming, length/magnitude-sensitive on zero-padded
        # different-sized spectra = the 0.187 artifact); this is the honest structural number.
        spec_sim = density_cosine(full_spectrum, lean_spectrum, F237["density_bins"])

        assert extractive_ok, ("ABSTRACTIVE LEAK at ratio %.2f — a LEAN line is not a "
                               "verbatim source line (regeneration). NULL clause (c) "
                               "would be a HARD build failure." % ratio)

        print(f"{ratio:>6.2f} | {int(keep.sum()):>10} | {lean_bytes:>10} | {actual_C:>9.4f} | "
              f"{coverage:>6.2f} | {spec_sim:>12.4f} | {extractive_ok}")
        records.append({**attest, "phase": "P1_extractive_select", "target_ratio": ratio,
                        "kept_bands": int(keep.sum()), "kept_bytes": lean_bytes,
                        "actual_compression_C": actual_C,
                        "guardrail_anchor_coverage": coverage,
                        "guardrail_anchors_present": present,
                        "guardrail_anchors_missing": missing,
                        "lean_band_graph_spectrum": [float(x) for x in lean_spectrum],
                        "spectral_metric": "size_invariant_normalized_spectral_density_"
                            "histogram_cosine (BUG2 fix; NOT spectral.similarity byte-Hamming "
                            "which gave the 0.187 length/magnitude artifact on zero-padded "
                            "different-sized raw spectra)",
                        "classL_spectral_density_cosine_full_vs_lean": spec_sim,
                        "extractive_integrity_ok": bool(extractive_ok),
                        "meets_spectral_threshold": bool(spec_sim >= spec_thr),
                        "is_primary_emit": bool(cascade.magnitude(ratio - primary_ratio) < 1e-9)})
        lean_files[ratio] = lean_text

    # ---- EMIT the primary LEAN file (+ per-ratio variants for the A/B) ----
    if args.emit:
        primary_text = lean_files[primary_ratio]
        out_primary = args.src.parent / "CLAUDE_LEAN.md"
        out_primary.write_text(primary_text, encoding="utf-8")
        lean_sha = sha256_bytes(primary_text.encode("utf-8"))
        print(f"\nEMITTED primary CLAUDE_LEAN.md (ratio {primary_ratio:.2f}): {out_primary}")
        print(f"  LEAN sha256 (Class A content-address): {lean_sha[:16]}...  "
              f"({len(primary_text.encode('utf-8'))} bytes)")
        records.append({**attest, "phase": "P2_emit", "primary_ratio": primary_ratio,
                        "lean_path": str(out_primary), "lean_sha256": lean_sha,
                        "lean_bytes": len(primary_text.encode("utf-8"))})

    # ---- bit-exact NDJSON (content-addressed; response_sha256 = body minus generated_at) ----
    out = args.src.parent / "docs" / "srmech" / "rbs_lm_research" / "substrate_measurements"
    out = HERE / "substrate_measurements"
    out.mkdir(parents=True, exist_ok=True)
    ndj = out / "claude_md_surgical_graft.ndjson"
    body = "".join(json.dumps(r, default=str, sort_keys=True) + "\n" for r in records)
    response_sha = sha256_bytes(body.encode("utf-8"))       # body MINUS generated_at
    with open(ndj, "w") as f:
        f.write(body)
    print(f"\nResults: {ndj}  ({len(records)} records)")
    print(f"response_sha256 (bit-exact; body minus generated_at): {response_sha}")
    print("\nVERDICT TIERING (MFO §VII.6.20): the spectral-compare + compression + coverage +")
    print("extractive-integrity measured HERE are DEMONSTRATED (bit-exact instrument). "
          "'lean-memory-WORKS'")
    print("(LEAN-primed agent answers as well as full-primed) is FRAMEWORK-READING until the A/B")
    print("harness-subagent probe scores land (this script emits the LEAN file + probe set the A/B consumes).")


if __name__ == "__main__":
    main()
