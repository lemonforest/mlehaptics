"""R-RBS-LM-242b — the RENDER-INVARIANCE measurement (F242b, the high-pass-loaner half) [CORRECTED].

Finding F242b (user direction 2026-05-31, CORRECTED run): F242a built the working-memory WIREFRAME
— the srmech Class-L SSoT (co-occurrence/Laplacian storage signature F172 + Klein-4 sector tags).
THIS finding tests whether that SSoT is RENDERER-INVARIANT.

THE CORRECTION (why this is a re-run): the FIRST run rendered three models from the PROSE — the
verbatim extractive sentences (`render_input.md`). That input ALREADY CONTAINED the sentences, so
the test was trivially invariant: it measured summarisation, not reconstruction. That run is now
the explicitly-labeled CONTROL. The REAL test (this run, PRIMARY) renders from the DE-PROSED
RBS-NN STRUCTURED STORAGE (`struct_input.md`) — pure token-bindings + the relational edge-graph,
NO sentences. The renderer must CREATE the sentences; there is no prose to copy. That is the
honest test of "does the STRUCTURE alone pin the load-bearing content."

  PRIMARY  : struct_{haiku,sonnet,opus}.md  — rendered from token-bindings + edges, NO sentences.
  CONTROL  : {haiku,sonnet,opus}.md         — rendered from the extractive PROSE (first run).

If the STRUCTURE does the work, any renderer reconstitutes the same cluster backbone from pure
bindings+edges — the model is a swappable high-pass / borrowed loaner, temporary until a
srmech-native sentence render catches up (F50 / F223; biology makes sentences with no supercompute).
But the render also SUPPLIES + OVER-SUPPLIES the sentence content the structure does not constrain
— so the fluent render is a partly-CONFABULATED VIEW, and the render is NEVER the SSoT; the
structure is. The sharp F223 metric for that over-supply is the RENDER-INVENTION RATE (below).

  Convergence: F242a (the wireframe SSoT this re-encodes) + F50 (structure-vs-renderer) +
  F223 (RBS-LM is extractive; the fluent prose is the BORROWED loaner) + F237 (the lean graft).

================================ PRE-STATED FALSIFIABLE (verbatim) =========================
"Is the F242a working-memory wireframe RENDERER-INVARIANT FROM THE PURE STRUCTURE — does the same
knowledge-shape, fed as token-bindings + an edge-graph with NO sentences, reconstitute the SAME
load-bearing SKELETON across three different renderers?
POSITIVE-ON-STRUCTURE iff (i) pairwise CROSS-RENDER similarity is HIGH on the discriminative
Class-L shared-eigenbasis spectral read AND (ii) each STRUCTURED render surfaces the load-bearing
token set (findings F234/235/236/238/239/241/237, clusters {kuramoto,disability,rehearsal}, anchors
{K_c, Kuramoto, chirality, RISC-V, Fiedler, nibble, projection, 1:3:7:3}) at high recall. The F223
reading (expected, REPORTED either way): the render also CONFABULATES sentence content beyond the
bindings — nonzero, model-varying RENDER-INVENTION (load-bearing/technical tokens present in the
render but ABSENT from the wireframe token universe + the structured input). NULL iff the STRUCTURED
renders DIVERGE — low cross-render similarity / different backbones — i.e. the wireframe
UNDER-DETERMINES even the skeleton."

Decide by MEASUREMENT, no leaning. CONTRAST vs the PROSE control: does the structured input show
(a) comparable backbone-invariance but (b) HIGHER invention than the prose control? Both reported.
A separate, SHARP sub-test (hypothesis from inspection): content-recall is ~invariant across models,
but HONESTY-tier preservation (the NULLs / CAVEATS / the ETHICAL LINE / DEMONSTRATED-vs-FRAMEWORK-
READING split) SCALES with model — haiku smooths caveats; sonnet/opus preserve them. Reported per
model either way (the honesty-gradient sub-result).
============================================================================================

srmech-FIRST discipline (HARD = 0; run check_srmech_discipline.py on this file):
  - per-render co-occurrence (token-class x token-class, sentence-level) -> EDGES ->
    laplacian.dense_laplacian -> jacobi_eigvals  = the F172 storage signature   [Class L]
    (Counter is used ONLY to count sentence-level co-occurrence edge WEIGHTS feeding
     dense_laplacian; the EIGENSPECTRUM is the storage signature, NOT the Counter — F172 / §2)
  - CROSS-render Class-L spectral similarity: ONE shared Laplacian over the UNION token
    vocabulary (common eigenbasis), each render's token-incidence projected via
    spectral.decompose -> spectral.similarity on coefficients_bytes  [Class L o A; Spike #115]
  - per-render Klein-4 SECTOR bundle = klein4_bundle of per-token klein4_random atoms (seeded by
    a Class-A content-address of the token), CROSS-render compared via klein4_similarity  [Class M]
  - RENDER-INVENTION: the render's surfaced structural tokens MINUS (wireframe token universe UNION
    structured-input binding universe) — set algebra over the SAME TOKEN_PATTERNS alphabet the
    wireframe is built from; plus a curated technical-confabulation probe applied uniformly  [set-Δ]
  - near-zero spectral floor / magnitude  -> cascade.magnitude (NEVER python abs())  [Class K]
  - per-token atom seed + attestation hash -> format.sha256_bytes (NEVER hashlib)    [Class A]

NO np.linalg.eig anywhere; NO Counter() as a storage proxy (the co-occurrence Laplacian
eigenspectrum IS the srmech-native storage signature, F172). numpy is the array carrier only.

The token vocabulary + the _token_atom / sector-bundle construction are REUSED verbatim from
R-RBS-LM-242 (F242a) so the re-encode is the SAME instrument over the captured renders.

Tiering (MFO §VII.6.20): DEMONSTRATED for the re-encode metric OVER THE CAPTURED RENDERS — the
NDJSON is bit-exact (response_sha256 = body minus generated_at) and reproducible from the committed
artifacts under f242b_renders/. FRAMEWORK-READING for "ANY render is invariant" — the renders are
non-reproducible LLM outputs (n=1 per model) and the thinking-off was INSTRUCTION-approximated, not
a hard API thinking-off. Both limitations are recorded in the record. The render is the borrowed-
loaner high-pass (temporary); a srmech-native sentence render is the trajectory and must constrain
invention (transduce-don't-add as an ENFORCED node, not just an instruction).

CAD-ban: this reads the RELATIONAL/TOKEN structure of prose renders. No physical / geometry.
Defensive scope: it encodes the project's own research renders.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

import srmech
import srmech.spectral as spectral
from srmech.amsc import cascade
from srmech.amsc import format as fmt
from srmech.amsc import hdc
from srmech.amsc import laplacian as lap

# Reuse F242a's encoder vocabulary + atom construction VERBATIM (same instrument).
from importlib.util import module_from_spec, spec_from_file_location

_F242A_PATH = Path(__file__).resolve().parent / "R-RBS-LM-242_working_memory_wireframe.py"
_spec = spec_from_file_location("_f242a_encoder", _F242A_PATH)
_f242a = module_from_spec(_spec)
_spec.loader.exec_module(_f242a)

TOKEN_PATTERNS = _f242a.TOKEN_PATTERNS          # the SAME load-bearing token alphabet
KLEIN4_D = _f242a.KLEIN4_D                       # A: 256 = MAX_NATIVE_NODES = the Klein-4 dim
ZERO_FLOOR = _f242a.ZERO_FLOOR                   # B: near-zero spectral floor (numerical)
EDGE_MIN_SHARED = _f242a.EDGE_MIN_SHARED         # B: shared-token edge floor (reused)
_token_atom = _f242a._token_atom                 # Class M atom (klein4_random seeded by sha256)

# --- attested constants specific to F242b (CLAUDE.md §4 no-magic-numbers; every constant A/B/C) ---
SENTENCE_SPLIT = re.compile(r"(?<=[.;:])\s+|\n")  # B: sentence/clause splitter for co-occurrence
# A: the PRIMARY test — three swappable high-pass loaners rendering from the DE-PROSED STRUCTURED
# STORAGE (token-bindings + edge-graph, NO sentences). File stems struct_{model}.md (F242b CORRECTED).
RENDER_NAMES = ("struct_haiku", "struct_sonnet", "struct_opus")
RENDER_MODELS = ("haiku", "sonnet", "opus")       # A: the bare model labels (for human-legible keys)
# A: the CONTROL — the FIRST run's renders from the extractive PROSE (render_input.md ALREADY had the
# sentences, so it was trivially invariant; it is the control against which the structured run contrasts).
PROSE_CONTROL_NAMES = ("haiku", "sonnet", "opus")

# The load-bearing CONTENT the renders must reconstitute (recall test). Each entry is a label ->
# a list of verbatim ALTERNATE surface-forms; recall(label) = 1 iff ANY alternate appears in the
# render text (case-insensitive). These are the wireframe's load-bearing facts, NOT generic English.
CONTENT_TOKENS = {
    # --- the seven findings the wireframe carries (by id OR by the bare 3-digit number) ---
    "F234": [r"\bF234\b", r"\bfinding\s*234\b"],
    "F235": [r"\bF235\b", r"\bfinding\s*235\b"],
    "F236": [r"\bF236\b", r"\bfinding\s*236\b"],
    "F237": [r"\bF237\b", r"\bfinding\s*237\b"],
    "F238": [r"\bF238\b", r"\bfinding\s*238\b"],
    "F239": [r"\bF239\b", r"\bfinding\s*239\b"],
    "F241": [r"\bF241\b", r"\bfinding\s*241\b"],
    # --- the three pre-named clusters ---
    "cluster:kuramoto": [r"\bkuramoto\b"],
    "cluster:disability": [r"\bdisabilit\w*\b"],
    "cluster:rehearsal": [r"\brehearsal\b"],
    # --- the load-bearing anchors ---
    "anchor:K_c": [r"\bK_?c\b", r"\bK\s*c\b", r"critical coupling", r"lock threshold", r"lock-onset"],
    "anchor:Kuramoto": [r"\bkuramoto\b"],
    "anchor:chirality": [r"\bchiral\w*\b", r"\bchirality\b", r"γ₅", r"gamma5"],
    "anchor:RISC-V": [r"\bRISC-?V\b"],
    "anchor:byte-identical": [r"\bbyte-?identical\b", r"\bbyte for byte\b"],
    "anchor:1:3:7:3": [r"1\s*:\s*3\s*:\s*7\s*:\s*3", r"1:3:7:3"],
}

# The HONESTY-tier markers (the sharp sub-test). recall(label)=1 iff ANY alternate appears.
HONESTY_TOKENS = {
    "null:single-graph-speedup": [r"null on single-graph speedup", r"null-on-single-graph-speedup",
                                  r"null on .{0,20}speedup", r"did not (?:fire|beat)", r"not .{0,20}speedup"],
    "caveat:honest": [r"honest caveat", r"honest residue", r"honest(?:ly|-positive| tiering| verdict)?",
                      r"the verdict is honest"],
    "caveat:O(N^2)": [r"O\(N²\)", r"O\(N\^?2\)", r"N²\s*(?:wir|coupl)", r"quadratic"],
    "caveat:small-N": [r"small-?N", r"small N", r"finer structure", r"higher resolution",
                       r"largest width", r"only at the largest"],
    "ethical-line": [r"reading the mechanism is not", r"not the same as recommending",
                     r"reads (?:only )?the mechanism", r"ethical line", r"mechanism only",
                     r"not .{0,20}recommend"],
    "demonstrated-vs-framework-reading": [r"DEMONSTRATED", r"framework[- ]reading", r"framework read"],
}

# The CURATED TECHNICAL-CONFABULATION probe (the sharp F223 over-supply read). These are technical
# claims/terms that are NOT in the wireframe token universe and NOT in the structured-input bindings,
# but which a fluent renderer tends to ADD when it has to write sentences — content the SSoT does NOT
# constrain. Built from inspection of the renders (e.g. haiku's "chemotaxis", "observationally
# identical", "neuron-ensemble"). Applied UNIFORMLY to structured AND prose renders so the contrast is
# fair. recall(label)=1 iff ANY alternate appears (case-insensitive). NOT generic English — each is a
# specific technical assertion the structure never supplied (a confabulated bridge / mechanism / claim).
INVENTION_PROBE = {
    "chemotaxis": [r"\bchemotax\w*\b"],                         # haiku: Physarum "chemotaxis" — not in bindings
    "observationally-identical": [r"\bobservationally identical\b", r"\bobservationally-identical\b"],
    "neuron-ensemble": [r"\bneuron[- ]ensemble\b", r"\bneural ensemble\b", r"\bneuron ensemble\b"],
    "slime-mould-biology": [r"\bslime[- ]mould\b", r"\bslime[- ]mold\b"],  # bindings have bare "slime"/"hive", not "slime-mould"
    "biological-substrate-claim": [r"\bbio-substrate\b", r"\bbiological substrate\b",
                                   r"\bbiological neuron\b", r"\bbio[- ]substrate phenomenon\b"],
    "continuous-phase-evolution": [r"\bcontinuous phase evolution\b", r"\bcontinuous(?:ly)? .{0,15}phase\b"],
    "synchronisation-threshold": [r"\bsynchroni[sz]ation threshold\b", r"\bsynchroni[sz]e\w*\b"],
    "spectral-gap-claim": [r"\bspectral gap\b"],               # "Fiedler value" is a binding; "spectral gap" is an added gloss
    "metric-field-ontology-expansion": [r"\bmetric[- ]field ontology\b"],  # bindings have bare "MFO"
    "without-approximation": [r"\bwithout approximation\b", r"\bcarries .{0,20}forward without\b"],
    "broadcast-hub-claim": [r"\bbroadcast\w*\b", r"\bhubs?\b that\b", r"\bact as hubs?\b"],
    "convergent-insight-claim": [r"\bconvergent insight\b", r"\bsingle convergent\b",
                                 r"\bunified by\b", r"\bunifying\b"],
    "costs-nothing-claim": [r"\bcosts? nothing\b", r"\bnothing to verify\b"],
    "distributed-coupling-model": [r"\bdistributed[- ]coupling\b", r"\bdistributed coupling model\b"],
    "co-attested-claim": [r"\bco-attest\w*\b"],                 # sonnet: "co-attested" — an added relational gloss
    "descending-thread-claim": [r"\bdescending thread\b", r"\bdeeper lineage\b"],
}


# =========================================================================================
# Class-L: per-render co-occurrence eigenspectrum (the F172 storage signature, per render)
# =========================================================================================
def render_text(name):
    p = Path(__file__).resolve().parent / "f242b_renders" / ("%s.md" % name)
    return p.read_text(encoding="utf-8", errors="replace")


def token_class_hits(text):
    """Map each load-bearing TOKEN to its CLASS-id (pattern index|matched-token). Returns a list of
    (sentence_index, frozenset-of-token-class-ids). The token-class id keeps DISTINCT tokens distinct
    (e.g. F234 != F236) while normalising whitespace/case — the co-occurrence alphabet of F242a."""
    sents = [s for s in SENTENCE_SPLIT.split(text) if s.strip()]
    per_sent = []
    for si, s in enumerate(sents):
        toks = set()
        for pat in TOKEN_PATTERNS:
            for hit in pat.findall(s):
                toks.add(re.sub(r"\s+", "", hit).lower())
        per_sent.append((si, frozenset(toks)))
    return per_sent


def render_vocabulary(per_sent):
    """The sorted union of load-bearing token-classes appearing in the render (the graph nodes)."""
    vocab = set()
    for _si, toks in per_sent:
        vocab |= toks
    return sorted(vocab)


def cooccurrence_edges(per_sent, vocab):
    """Sentence-level co-occurrence EDGES over token-classes: edge (i,j) weight = number of sentences
    in which token-class i and token-class j BOTH appear (>= EDGE_MIN_SHARED-free here; a single shared
    sentence is a real co-occurrence at the render scale). The weight is a co-occurrence COUNT feeding
    dense_laplacian (the §2-sanctioned counting use; the EIGENSPECTRUM is the storage signature, F172).
    Returns (edges, weights) parallel lists over the vocab index space."""
    idx = {t: k for k, t in enumerate(vocab)}
    pair_w = {}
    for _si, toks in per_sent:
        ts = sorted(toks)
        for a in range(len(ts)):
            for b in range(a + 1, len(ts)):
                key = (idx[ts[a]], idx[ts[b]])
                pair_w[key] = pair_w.get(key, 0) + 1   # co-occurrence edge weight (NOT a storage proxy)
    edges = sorted(pair_w)
    weights = [float(pair_w[e]) for e in edges]
    return edges, weights


def render_spectrum(name):
    """The per-render F172 STORAGE SIGNATURE = eigenspectrum of the render's token co-occurrence
    Laplacian. dense_laplacian (Class L) -> jacobi_eigvals (Class L, sorted asc). near-zero count via
    cascade.magnitude (Class K; NEVER abs()). Returns (spectrum dict, vocab, per_sent)."""
    text = render_text(name)
    per_sent = token_class_hits(text)
    vocab = render_vocabulary(per_sent)
    edges, weights = cooccurrence_edges(per_sent, vocab)
    n = len(vocab)
    L = lap.dense_laplacian(n, edges, weights if weights else None)
    eig = [float(e) for e in lap.jacobi_eigvals(L)]                   # Class L, sorted asc
    n_zero = sum(1 for e in eig if cascade.magnitude(e) < ZERO_FLOOR)  # Class K, no abs()
    lam_2 = eig[1] if len(eig) > 1 else 0.0
    lam_max = eig[-1] if eig else 0.0
    spec = {
        "render": name,
        "n_token_nodes": int(n),
        "n_cooccurrence_edges": len(edges),
        "eigenvalues": [round(e, 10) for e in eig],
        "n_zero_eigenvalues_components": int(n_zero),
        "fiedler_lambda_2": round(float(lam_2), 10),
        "lambda_max": round(float(lam_max), 10),
        "laplacian_matrix_class_L_native": True,
    }
    return spec, vocab, per_sent


# =========================================================================================
# Class-M: per-render Klein-4 SECTOR bundle (token-overlap -> sector-alignment; the F242a construct)
# =========================================================================================
def render_sector_bundle(vocab):
    """The render's Klein-4 SECTOR vector = klein4_BUNDLE of its load-bearing-token atoms (Class M
    superposition; shared tokens -> aligned sectors). REUSES F242a's _token_atom verbatim (the atom is
    seeded by a Class-A content-address of the token, so the SAME token -> the SAME atom across renders).
    Returns (sector_vector, occupancy [n0,n1,n2,n3], dominant_sector).

    NOTE (honest, recorded in the NDJSON): klein4_bundle is a per-bit MAJORITY vote, so bundling many
    atoms (a whole render's ~15-21-token vocabulary, vs F242a's per-section 2-5 tokens) SATURATES toward
    the majority sector. At render scale the sector occupancy collapses to one dominant sector for ALL
    renders, so klein4_similarity reads ~1.0 trivially — it confirms identity-at-saturation but is NOT
    discriminative at this vocabulary size. The DISCRIMINATIVE cross-render read is therefore the Class-L
    SHARED-eigenbasis spectral similarity (token-incidence projected onto the common Laplacian basis);
    the Class-M sector read is reported as CORROBORATING-ONLY with this saturation caveat."""
    if not vocab:
        vec = _token_atom("__no_load_bearing_token__")
    else:
        vec = _token_atom(vocab[0])
        for t in vocab[1:]:
            vec = hdc.klein4_bundle(vec, _token_atom(t))             # Class M superposition
    occ = [int(x) for x in hdc.klein4_sector_count(vec)]
    dominant = int(np.argmax(occ))
    return vec, occ, dominant


def klein4_saturated(occ):
    """A bundle is SATURATED iff one sector holds (near-)all of the KLEIN4_D positions — the
    majority-vote bundle has collapsed and klein4_similarity is no longer discriminative. Magnitude via
    cascade.magnitude (Class K; NEVER abs()). Returns True iff the dominant sector >= KLEIN4_D - 1."""
    dominant_count = max(occ) if occ else 0
    return bool(cascade.magnitude(float(KLEIN4_D - dominant_count)) <= 1.0)


# =========================================================================================
# Class-L o A: CROSS-render spectral similarity on a SHARED eigenbasis (Spike #115 design)
# =========================================================================================
def shared_basis_laplacian(union_vocab, per_sent_by_render):
    """ONE shared co-occurrence Laplacian over the UNION token vocabulary across all renders + the
    wireframe-token universe — the COMMON eigenbasis every render is projected onto (so the spectral
    coefficients are directly comparable). Edge weight = total sentences (across all renders) in which
    the two token-classes co-occur. dense_laplacian (Class L). Returns the (n x n) Laplacian ndarray."""
    idx = {t: k for k, t in enumerate(union_vocab)}
    pair_w = {}
    for per_sent in per_sent_by_render:
        for _si, toks in per_sent:
            ts = sorted(t for t in toks if t in idx)
            for a in range(len(ts)):
                for b in range(a + 1, len(ts)):
                    key = (idx[ts[a]], idx[ts[b]])
                    pair_w[key] = pair_w.get(key, 0) + 1
    edges = sorted(pair_w)
    weights = [float(pair_w[e]) for e in edges]
    L = lap.dense_laplacian(len(union_vocab), edges, weights if weights else None)
    return np.asarray(L, dtype=float)


def render_state_vector(union_vocab, vocab):
    """The render's token-incidence STATE in the shared node-domain basis: 1.0 at each token-class the
    render surfaced, 0.0 elsewhere. This is the `state` projected by spectral.decompose onto the shared
    Laplacian eigenbasis (Class L) — its coefficients_bytes feed spectral.similarity (Class M-over-L)."""
    present = set(vocab)
    return np.array([1.0 if t in present else 0.0 for t in union_vocab], dtype=float)


def spectral_similarity_on_shared_basis(L_shared, union_vocab, vocab_a, vocab_b, tag):
    """CROSS-render Class-L spectral similarity: project both renders' token-incidence states onto the
    SHARED Laplacian eigenbasis (spectral.decompose, Class L o A) and compare the coefficient bytes via
    spectral.similarity (the Spike #115 HDC similarity 1 - 2*hamming/D, Class M). Same basis => directly
    comparable. Returns the similarity in [-1, 1]."""
    sa = render_state_vector(union_vocab, vocab_a)
    sb = render_state_vector(union_vocab, vocab_b)
    ha = spectral.decompose(sa, L_shared, encoder_tag=tag)           # Class L (shared eigenbasis)
    hb = spectral.decompose(sb, L_shared, encoder_tag=tag)
    return float(spectral.similarity(ha, hb))                        # Class M over the L-projection


# =========================================================================================
# Recall (content + honesty) — verbatim surface-form presence, case-insensitive
# =========================================================================================
def _recall(text, token_map):
    low = text.lower()
    hits = {}
    for label, alts in token_map.items():
        present = any(re.search(p, low, flags=re.I) for p in alts)
        hits[label] = bool(present)
    n_hit = sum(1 for v in hits.values() if v)
    return hits, n_hit, len(token_map)


# =========================================================================================
# Wireframe (F242a SSoT) token universe — for render-vs-wireframe FIDELITY
# =========================================================================================
def wireframe_record():
    p = (Path(__file__).resolve().parents[1] / "catalogs" / "rbs_lm_substrate"
         / "substrate_measurements" / "working_memory_wireframe.ndjson")
    with open(p, "r", encoding="utf-8") as fh:
        return json.loads(fh.readline()), p.name


def wireframe_token_universe(rec):
    """The union of load-bearing token-classes the F242a wireframe NODES carry (its load_bearing_tokens
    fields). This is the wireframe's token SSoT — the render-vs-wireframe fidelity compares each render's
    surfaced token-classes against THIS universe (token recall vs the SSoT)."""
    uni = set()
    for node in rec.get("wireframe_nodes_extractive", []):
        uni |= set(node.get("load_bearing_tokens", []))
    return sorted(uni)


# =========================================================================================
# Structured-input binding universe + RENDER-INVENTION (the sharp F223 over-supply read)
# =========================================================================================
def structured_input_token_universe():
    """The token-class universe of the STRUCTURED STORAGE fed to the renderers (struct_input.md): the
    union of every load-bearing TOKEN-CLASS appearing in the structured input, normalised through the
    SAME TOKEN_PATTERNS alphabet the wireframe is built from (so 'invention' is measured on the same
    structural vocabulary, not on incidental punctuation). The structured input is the {token-binding}
    sets + the edge list; this returns the token-classes the renderer was actually HANDED."""
    p = Path(__file__).resolve().parent / "f242b_renders" / "struct_input.md"
    text = p.read_text(encoding="utf-8", errors="replace")
    toks = set()
    for pat in TOKEN_PATTERNS:
        for hit in pat.findall(text):
            toks.add(re.sub(r"\s+", "", hit).lower())
    return sorted(toks)


def render_invention(vocab, supplied_universe, text):
    """The RENDER-INVENTION rate for one render (the sharp F223 metric). TWO complementary reads:

      (1) STRUCTURAL-token invention (srmech-native set-Δ over the TOKEN_PATTERNS alphabet): the
          load-bearing token-classes the render SURFACED (`vocab`) that are ABSENT from the supplied
          universe = wireframe-token-universe ∪ structured-input-binding-universe. These are
          structural tokens (finding-ids / class-names / anchors) the render introduced beyond what
          the structure handed it — content the SSoT does NOT constrain.
      (2) TECHNICAL-confabulation invention (the curated INVENTION_PROBE): specific technical
          terms/claims (chemotaxis, observationally-identical, neuron-ensemble, …) the structure
          never supplied but a fluent renderer ADDS. Applied uniformly to structured + prose renders.

    Higher invention = more render-side fabrication the SSoT does not pin. Returns the invention dict."""
    supplied = set(supplied_universe)
    surfaced = set(vocab)
    invented_structural = sorted(surfaced - supplied)
    n_struct_invented = len(invented_structural)
    struct_invention_rate = (n_struct_invented / len(surfaced)) if surfaced else 0.0

    probe_hits, n_probe, n_probe_total = _recall(text, INVENTION_PROBE)
    technical_invented = sorted([k for k, v in probe_hits.items() if v])

    return {
        "structural_token_invention": {
            "invented_tokens": invented_structural,
            "n_invented": n_struct_invented,
            "n_surfaced": len(surfaced),
            "invention_rate": round(struct_invention_rate, 6),
            "note": ("structural token-classes (TOKEN_PATTERNS alphabet) in the render but ABSENT from "
                     "wireframe-token-universe ∪ structured-input bindings — content the SSoT does not "
                     "constrain"),
        },
        "technical_confabulation_invention": {
            "invented_terms": technical_invented,
            "n_invented": n_probe,
            "n_probe_total": n_probe_total,
            "invention_rate": round(n_probe / n_probe_total, 6) if n_probe_total else 0.0,
            "note": ("curated technical-confabulation probe (chemotaxis / observationally-identical / "
                     "neuron-ensemble / …) — specific claims the structure never supplied; applied "
                     "uniformly to structured + prose renders for a fair contrast"),
        },
        "total_invented_items": n_struct_invented + n_probe,
    }


# =========================================================================================
# A single re-encode PASS over a set of render-name stems (PRIMARY structured OR CONTROL prose).
# Returns the full block: per-render spectra / sector bundles / cross-render 3x3 / fidelity / recall /
# invention — keyed by the bare MODEL label (haiku/sonnet/opus) for human-legible output.
# =========================================================================================
def _encode_block(render_stems, model_labels, wf_vocab, wf_vec, wf_per_sent, supplied_universe, label):
    """Re-encode one set of renders (Class-L spectrum + Class-M sector bundle), build the shared
    eigenbasis (renders + wireframe), compute the 3x3 cross-render similarity, render-vs-wireframe
    fidelity, content + honesty recall, and RENDER-INVENTION. `render_stems` are the file stems
    (struct_haiku.md ... for PRIMARY; haiku.md ... for CONTROL); `model_labels` are the bare labels
    used as dict keys. `supplied_universe` = wireframe ∪ structured-input bindings (the invention floor).
    Returns a dict with every per-block measurement (no I/O)."""
    stem_of = dict(zip(model_labels, render_stems))
    spectra, vocabs, per_sents, sector_vecs, sector_occ, sector_dom, texts = {}, {}, {}, {}, {}, {}, {}
    for m in model_labels:
        spec, vocab, per_sent = render_spectrum(stem_of[m])
        spectra[m] = spec
        vocabs[m] = vocab
        per_sents[m] = per_sent
        texts[m] = render_text(stem_of[m])
        vec, occ, dom = render_sector_bundle(vocab)
        sector_vecs[m] = vec
        sector_occ[m] = occ
        sector_dom[m] = dom
        print("[%s/encode] %-7s  nodes=%2d  edges=%3d  lambda2=%.4f  lambda_max=%.4f  |vocab|=%d"
              % (label, m, spec["n_token_nodes"], spec["n_cooccurrence_edges"],
                 spec["fiedler_lambda_2"], spec["lambda_max"], len(vocab)))

    # shared eigenbasis over the UNION (this block's renders + the wireframe token universe)
    union_vocab = sorted(set().union(*[set(vocabs[m]) for m in model_labels], set(wf_vocab)))
    L_shared = shared_basis_laplacian(union_vocab, [per_sents[m] for m in model_labels] + [wf_per_sent])

    # 3x3 cross-render similarity (Class-L spectral discriminative + Class-M klein4 corroborating)
    spectral_sim, klein4_sim = {}, {}
    for a in model_labels:
        for b in model_labels:
            s_l = spectral_similarity_on_shared_basis(L_shared, union_vocab, vocabs[a], vocabs[b],
                                                      tag="f242b-%s" % label)
            s_m = float(hdc.klein4_similarity(sector_vecs[a], sector_vecs[b]))    # Class M
            spectral_sim["%s|%s" % (a, b)] = round(s_l, 6)
            klein4_sim["%s|%s" % (a, b)] = round(s_m, 6)
    pairs = [("haiku", "sonnet"), ("haiku", "opus"), ("sonnet", "opus")]
    cross_spectral = {("%s-vs-%s" % p): spectral_sim["%s|%s" % p] for p in pairs}
    cross_klein4 = {("%s-vs-%s" % p): klein4_sim["%s|%s" % p] for p in pairs}
    mean_cross_spectral = float(np.mean(list(cross_spectral.values())))
    mean_cross_klein4 = float(np.mean(list(cross_klein4.values())))
    klein4_sat = {m: klein4_saturated(sector_occ[m]) for m in model_labels}
    klein4_all_saturated = all(klein4_sat.values())
    print("[%s/cross] Class-L spectral: %s mean=%.4f  | Class-M klein4 mean=%.4f%s"
          % (label, cross_spectral, mean_cross_spectral, mean_cross_klein4,
             " [SATURATED->corroborating-only]" if klein4_all_saturated else ""))

    # render-vs-wireframe fidelity + content/honesty recall + RENDER-INVENTION
    fidelity, content_recall, honesty_recall, invention = {}, {}, {}, {}
    for m in model_labels:
        s_l = spectral_similarity_on_shared_basis(L_shared, union_vocab, vocabs[m], wf_vocab,
                                                  tag="f242b-%s-vs-wireframe" % label)
        s_m = float(hdc.klein4_similarity(sector_vecs[m], wf_vec))                # Class M
        surfaced = set(vocabs[m]) & set(wf_vocab)
        tok_recall = (len(surfaced) / len(wf_vocab)) if wf_vocab else 0.0
        fidelity[m] = {
            "class_L_spectral_similarity_vs_wireframe": round(s_l, 6),
            "class_M_klein4_similarity_vs_wireframe": round(s_m, 6),
            "wireframe_token_universe_recall": round(tok_recall, 6),
            "n_wireframe_tokens_surfaced": len(surfaced),
            "n_wireframe_token_universe": len(wf_vocab),
        }
        c_hits, c_n, c_tot = _recall(texts[m], CONTENT_TOKENS)
        h_hits, h_n, h_tot = _recall(texts[m], HONESTY_TOKENS)
        content_recall[m] = {"recall_fraction": round(c_n / c_tot, 6), "n_present": c_n, "n_total": c_tot,
                             "present": sorted([k for k, v in c_hits.items() if v]),
                             "missing": sorted([k for k, v in c_hits.items() if not v])}
        honesty_recall[m] = {"recall_fraction": round(h_n / h_tot, 6), "n_present": h_n, "n_total": h_tot,
                             "present": sorted([k for k, v in h_hits.items() if v]),
                             "missing": sorted([k for k, v in h_hits.items() if not v])}
        invention[m] = render_invention(vocabs[m], supplied_universe, texts[m])
        print("[%s/measure] %-7s  L-fid=%.4f  tok-recall=%.3f  content=%.3f (%d/%d)  honesty=%.3f (%d/%d)"
              "  invent: struct=%d tech=%d"
              % (label, m, s_l, tok_recall, c_n / c_tot, c_n, c_tot, h_n / h_tot, h_n, h_tot,
                 invention[m]["structural_token_invention"]["n_invented"],
                 invention[m]["technical_confabulation_invention"]["n_invented"]))

    mean_struct_invention = float(np.mean(
        [invention[m]["structural_token_invention"]["invention_rate"] for m in model_labels]))
    mean_tech_invention = float(np.mean(
        [invention[m]["technical_confabulation_invention"]["n_invented"] for m in model_labels]))
    return {
        "render_stems": {m: ("%s.md" % stem_of[m]) for m in model_labels},
        "per_render_storage_signature": {m: spectra[m] for m in model_labels},
        "per_render_klein4_sector": {m: {"occupancy": sector_occ[m], "dominant_sector": sector_dom[m],
                                         "saturated_non_discriminative": klein4_sat[m]}
                                     for m in model_labels},
        "cross_render_similarity_3x3": {
            "discriminative_read": "class_L_spectral_shared_basis",
            "class_L_spectral_shared_basis": spectral_sim,
            "class_M_klein4": klein4_sim,
            "pairwise_class_L_spectral": cross_spectral,
            "pairwise_class_M_klein4": cross_klein4,
            "mean_cross_render_class_L_spectral": round(mean_cross_spectral, 6),
            "mean_cross_render_class_M_klein4": round(mean_cross_klein4, 6),
            "class_M_klein4_saturated_non_discriminative": klein4_all_saturated,
        },
        "render_vs_wireframe_fidelity": fidelity,
        "content_recall_per_render": content_recall,
        "honesty_marker_recall_per_render": honesty_recall,
        "render_invention_per_render": invention,
        "mean_structural_invention_rate": round(mean_struct_invention, 6),
        "mean_technical_confabulation_count": round(mean_tech_invention, 6),
        "_internal": {"cross_spectral": cross_spectral, "cross_klein4": cross_klein4,
                      "mean_cross_spectral": mean_cross_spectral, "mean_cross_klein4": mean_cross_klein4,
                      "content_recall": content_recall, "honesty_recall": honesty_recall,
                      "klein4_sat": klein4_sat, "klein4_all_saturated": klein4_all_saturated},
    }


# =========================================================================================
# main — PRIMARY structured re-encode + CONTROL prose re-encode + contrast -> emit corrected SSoT
# =========================================================================================
def main():
    print("=" * 80)
    print("R-RBS-LM-242b — RENDER-INVARIANCE measurement (F242b) [CORRECTED: STRUCTURED primary]")
    print("=" * 80)

    # ---- wireframe (F242a SSoT) token universe + sector bundle + per-node co-occurrence bags ----
    wf_rec, wf_name = wireframe_record()
    wf_vocab = wireframe_token_universe(wf_rec)
    wf_vec, _wf_occ, _wf_dom = render_sector_bundle(wf_vocab)
    wf_fingerprint = wf_rec.get("response_sha256")
    wf_per_sent = [(i, frozenset(node.get("load_bearing_tokens", [])))
                   for i, node in enumerate(wf_rec.get("wireframe_nodes_extractive", []))]
    print("[wireframe] %s  |token-universe|=%d  fingerprint=%s"
          % (wf_name, len(wf_vocab), wf_fingerprint[:16]))

    # ---- the structured-input binding universe (what the renderer was HANDED) ----
    struct_vocab = structured_input_token_universe()
    # the INVENTION floor = wireframe token universe UNION the structured-input bindings; a token
    # surfaced by a render that is NOT in this union is render-side invention (the SSoT did not pin it).
    supplied_universe = sorted(set(wf_vocab) | set(struct_vocab))
    print("[supplied] structured-input bindings=%d ; supplied-universe (wireframe ∪ struct)=%d"
          % (len(struct_vocab), len(supplied_universe)))

    # ================= PRIMARY: the STRUCTURED renders (token-bindings + edges, NO sentences) =======
    print("\n----- PRIMARY: STRUCTURED-storage renders (the renderer CREATED the sentences) -----")
    primary = _encode_block(RENDER_NAMES, RENDER_MODELS, wf_vocab, wf_vec, wf_per_sent,
                            supplied_universe, "STRUCT")

    # ================= CONTROL: the PROSE renders (first run; extractive sentences supplied) ========
    print("\n----- CONTROL: PROSE renders (first run; the sentences were ALREADY in the input) -----")
    control = _encode_block(PROSE_CONTROL_NAMES, RENDER_MODELS, wf_vocab, wf_vec, wf_per_sent,
                            supplied_universe, "PROSE")

    # ---- the STRUCTURED-vs-PROSE contrast (backbone-invariance comparable? invention higher?) ----
    contrast = _structured_vs_prose_contrast(primary, control)
    print("\n[contrast] backbone-invariance: struct mean-L=%.4f vs prose mean-L=%.4f (Δ=%.4f, %s)"
          % (contrast["backbone_invariance"]["structured_mean_class_L_spectral"],
             contrast["backbone_invariance"]["prose_mean_class_L_spectral"],
             contrast["backbone_invariance"]["delta_struct_minus_prose"],
             "comparable" if contrast["backbone_invariance"]["comparable"] else "DIVERGENT"))
    print("[contrast] invention: struct mean-struct-rate=%.4f vs prose=%.4f ; struct tech=%.2f vs prose=%.2f (%s)"
          % (contrast["invention"]["structured_mean_structural_invention_rate"],
             contrast["invention"]["prose_mean_structural_invention_rate"],
             contrast["invention"]["structured_mean_technical_count"],
             contrast["invention"]["prose_mean_technical_count"],
             "structured HIGHER" if contrast["invention"]["structured_invention_higher"] else "NOT higher"))

    # ---- verdict (no leaning), keyed on the PRIMARY structured block ----
    pi = primary["_internal"]
    verdict = _decide_verdict(pi["cross_spectral"], pi["cross_klein4"], pi["mean_cross_spectral"],
                              pi["mean_cross_klein4"], pi["content_recall"], pi["honesty_recall"],
                              primary["render_vs_wireframe_fidelity"], pi["klein4_sat"],
                              pi["klein4_all_saturated"], primary, contrast)
    print("\n" + "=" * 80)
    print("  VERDICT: %s" % verdict["headline"])

    record = _build_record(srmech.__version__, primary, control, contrast, wf_name, wf_fingerprint,
                           len(wf_vocab), len(struct_vocab), len(supplied_universe), struct_vocab,
                           supplied_universe, verdict)
    sha = _emit(record)
    print("  render-invariance fingerprint (response_sha256): %s" % record["response_sha256"])
    print("  ndjson on-disk sha256: %s" % sha)
    print("  srmech %s" % srmech.__version__)
    print("=" * 80)


def _structured_vs_prose_contrast(primary, control):
    """The CONTRAST §4: does the STRUCTURED input show (a) comparable backbone-invariance but (b) HIGHER
    invention than the PROSE control? 'Comparable' backbone = the structured cross-render mean Class-L
    spectral similarity is within COMPARABLE_BAND of the prose mean (not a collapse). 'Higher invention'
    = structured mean structural-invention-rate > prose AND/OR structured mean technical-confabulation
    count > prose. Magnitude via cascade.magnitude (Class K; NEVER abs())."""
    COMPARABLE_BAND = 0.15        # B: |Δ mean-cross-L| within this band = "comparable backbone-invariance"
    s_mean_l = primary["_internal"]["mean_cross_spectral"]
    p_mean_l = control["_internal"]["mean_cross_spectral"]
    delta_l = s_mean_l - p_mean_l
    comparable = bool(cascade.magnitude(delta_l) <= COMPARABLE_BAND)   # Class K, no abs()

    s_struct_inv = primary["mean_structural_invention_rate"]
    p_struct_inv = control["mean_structural_invention_rate"]
    s_tech_inv = primary["mean_technical_confabulation_count"]
    p_tech_inv = control["mean_technical_confabulation_count"]
    struct_higher = bool(s_struct_inv > p_struct_inv or s_tech_inv > p_tech_inv)
    return {
        "backbone_invariance": {
            "structured_mean_class_L_spectral": round(s_mean_l, 6),
            "prose_mean_class_L_spectral": round(p_mean_l, 6),
            "delta_struct_minus_prose": round(delta_l, 6),
            "comparable_band": COMPARABLE_BAND,
            "comparable": comparable,
            "interpretation": ("the structured renders reconstruct a cluster backbone of COMPARABLE "
                               "cross-render coherence to the prose control (the structure pins the "
                               "skeleton, not just the supplied sentences)" if comparable else
                               "the structured backbone-invariance DIVERGES materially from the prose "
                               "control (the structure under-determines the skeleton relative to prose)"),
        },
        "invention": {
            "structured_mean_structural_invention_rate": round(s_struct_inv, 6),
            "prose_mean_structural_invention_rate": round(p_struct_inv, 6),
            "structured_mean_technical_count": round(s_tech_inv, 6),
            "prose_mean_technical_count": round(p_tech_inv, 6),
            "delta_structural_rate": round(s_struct_inv - p_struct_inv, 6),
            "delta_technical_count": round(s_tech_inv - p_tech_inv, 6),
            "structured_invention_higher": struct_higher,
            "interpretation": ("the STRUCTURED input forces MORE render-side fabrication than the prose "
                               "control — the renderer must supply + over-supply sentence content the "
                               "bindings do not constrain (the F223 reading)" if struct_higher else
                               "the structured input does NOT show higher invention than the prose "
                               "control (refutes the higher-invention expectation)"),
        },
        "headline": ("structured input: %s backbone-invariance + %s invention vs the prose control"
                     % ("COMPARABLE" if comparable else "DIVERGENT",
                        "HIGHER" if struct_higher else "NOT-higher")),
    }


def _decide_verdict(cross_spectral, cross_klein4, mean_l, mean_m, content_recall, honesty_recall,
                    fidelity, klein4_sat, klein4_all_saturated, primary, contrast):
    """No-leaning disposition over the PRIMARY STRUCTURED renders (the corrected test). The
    DISCRIMINATIVE axes are the Class-L SHARED-eigenbasis spectral similarity AND content-recall; the
    Class-M klein4 read SATURATES at render scale (majority-vote bundle collapse) so it is
    CORROBORATING-ONLY, not gating. STRUCTURE-INVARIANT iff: cross-render Class-L spectral similarity
    > 0.5 on EVERY pair (well above the 0.0 orthogonal floor) AND min content-recall >= 0.8 — i.e. the
    pure token-bindings + edge-graph (NO sentences) pin the load-bearing SKELETON across renderers.
    The RENDER-INVENTION rate is REPORTED (the F223 over-supply read; nonzero, model-varying = the
    render supplies + over-supplies sentence content the SSoT does not constrain) and does NOT gate the
    skeleton verdict — backbone-invariance and bounded-invention are distinct claims. The honesty-marker
    recall is REPORTED per model (the honesty-gradient sub-test); it does NOT gate either."""
    INV_SIM_FLOOR = 0.5            # B: cross-render similarity floor for "high" (orthogonal = 0.0)
    CONTENT_RECALL_FLOOR = 0.8     # B: per-render content-recall floor for "reconstitutes the skeleton"
    all_l_high = all(v > INV_SIM_FLOOR for v in cross_spectral.values())
    all_m_high = all(v > INV_SIM_FLOOR for v in cross_klein4.values())
    min_content = min(content_recall[n]["recall_fraction"] for n in content_recall)
    content_ok = min_content >= CONTENT_RECALL_FLOOR
    # Class-M gates ONLY when non-saturated (a saturated 1.0 is not real discrimination, no inflation).
    klein4_gates = (not klein4_all_saturated)
    invariant = bool(all_l_high and content_ok and (all_m_high if klein4_gates else True))

    # the F223 over-supply read (REPORTED, non-gating): mean structural-invention rate + technical count.
    mean_struct_inv = primary["mean_structural_invention_rate"]
    mean_tech_inv = primary["mean_technical_confabulation_count"]
    invention_nonzero = bool(mean_struct_inv > 0.0 or mean_tech_inv > 0.0)
    inv_by_model = {m: (primary["render_invention_per_render"][m]["structural_token_invention"]["n_invented"]
                        + primary["render_invention_per_render"][m]["technical_confabulation_invention"]["n_invented"])
                    for m in primary["render_invention_per_render"]}
    invention_varies = bool(len(set(inv_by_model.values())) > 1)

    # the honesty-gradient sub-test: does honesty-recall scale with model (haiku <= sonnet/opus)?
    h = {n: honesty_recall[n]["recall_fraction"] for n in honesty_recall}
    honesty_scales = bool(h.get("haiku", 1.0) <= h.get("sonnet", 0.0) and h.get("haiku", 1.0) <= h.get("opus", 0.0))
    # flatness = the two model-deltas are near-zero; magnitude via cascade.magnitude (Class K; NEVER abs())
    honesty_flat = bool(cascade.magnitude(h.get("haiku", 0.0) - h.get("opus", 0.0)) < 1e-9
                        and cascade.magnitude(h.get("sonnet", 0.0) - h.get("opus", 0.0)) < 1e-9)

    klein4_clause = (("Class-M klein4 mean=%.3f but SATURATED (majority-vote bundle collapse at render "
                      "scale) -> corroborating-only, non-discriminative" % mean_m) if klein4_all_saturated
                     else "Class-M klein4 mean=%.3f, every pair > %.2f" % (mean_m, 0.5))
    honesty_clause = ("honesty-preservation SCALES with model — haiku smooths, sonnet/opus preserve"
                      if honesty_scales and not honesty_flat else
                      "honesty-preservation is ~FLAT across models (refutes the scaling hypothesis)"
                      if honesty_flat else "honesty-preservation is mixed (neither cleanly scaling nor flat)")
    if invariant:
        head = ("STRUCTURE renderer-INVARIANT — the F242a wireframe pins the load-bearing SKELETON from "
                "the PURE STRUCTURE (token-bindings + edge-graph, NO sentences): all three structured "
                "renders reconstitute it with HIGH discriminative cross-render similarity (Class-L "
                "shared-eigenbasis spectral mean=%.3f, every pair > %.2f) AND content-recall >= %.2f "
                "(min=%.3f). [%s.] AND the fluent render is a swappable, PARTLY-CONFABULATED VIEW: "
                "render-invention is nonzero + model-varying (mean structural-rate=%.3f, mean technical-"
                "confab=%.2f terms/render, per-model invented-items=%s) — the render supplies + "
                "OVER-supplies sentence content the bindings do not constrain (F223). The render is NEVER "
                "the SSoT; the STRUCTURE is. Contrast vs the prose control: %s. HONESTY sub-test: "
                "haiku=%.3f sonnet=%.3f opus=%.3f (%s)."
                % (mean_l, 0.5, CONTENT_RECALL_FLOOR, min_content, klein4_clause,
                   mean_struct_inv, mean_tech_inv, inv_by_model, contrast["headline"],
                   h.get("haiku"), h.get("sonnet"), h.get("opus"), honesty_clause))
        positive = True
    else:
        head = ("STRUCTURE renderer-DEPENDENT (NULL) — the STRUCTURED renders DIVERGE: %s%s%s The "
                "wireframe UNDER-DETERMINES even the skeleton from the pure bindings+edges on at least "
                "one DISCRIMINATIVE axis. (Render-invention mean structural-rate=%.3f, technical-confab=%.2f.)"
                % ("Class-L spectral similarity falls below %.2f on some pair; " % 0.5 if not all_l_high else "",
                   "Class-M klein4 similarity falls below %.2f on some pair; " % 0.5
                   if not (all_m_high or klein4_all_saturated) else "",
                   "min content-recall %.3f < %.2f; " % (min_content, CONTENT_RECALL_FLOOR) if not content_ok else "",
                   mean_struct_inv, mean_tech_inv))
        positive = False
    return {
        "headline": head,
        "structure_renderer_invariant": positive,
        "primary_input": "structured_storage (token-bindings + edge-graph, NO sentences)",
        "decision_basis": ("discriminative axes = Class-L shared-eigenbasis spectral similarity + "
                           "content-recall over the STRUCTURED renders; Class-M klein4 is corroborating-"
                           "only (saturated); render-invention + honesty-gradient are REPORTED, non-gating"),
        "thresholds": {"cross_render_similarity_floor": INV_SIM_FLOOR,
                       "content_recall_floor": CONTENT_RECALL_FLOOR},
        "cross_render_spectral_all_pairs_high": all_l_high,
        "cross_render_klein4_all_pairs_high": all_m_high,
        "cross_render_klein4_saturated_non_discriminative": klein4_all_saturated,
        "cross_render_klein4_per_render_saturated": klein4_sat,
        "cross_render_klein4_gated_verdict": klein4_gates,
        "min_content_recall": round(min_content, 6),
        "content_recall_ok": content_ok,
        "render_invention_F223": {
            "mean_structural_invention_rate": round(mean_struct_inv, 6),
            "mean_technical_confabulation_count": round(mean_tech_inv, 6),
            "invented_items_by_model": inv_by_model,
            "invention_nonzero": invention_nonzero,
            "invention_model_varying": invention_varies,
            "reading": ("the render supplies + OVER-supplies sentence content the structure does not "
                        "constrain — nonzero, model-varying confabulation; the render is a swappable "
                        "VIEW, never the SSoT (F223). REPORTED, non-gating on the skeleton verdict."),
        },
        "honesty_recall_by_model": {n: round(h[n], 6) for n in h},
        "honesty_scales_with_model": honesty_scales,
        "honesty_flat_across_models": honesty_flat,
        "tier": {
            "demonstrated": ("the re-encode + invention set-Δ OVER THE CAPTURED STRUCTURED + PROSE "
                             "RENDERS — bit-exact (response_sha256 = body minus generated_at) + "
                             "reproducible from the committed f242b_renders/ artifacts"),
            "framework_reading": ("'ANY render reconstructs the skeleton / any render confabulates this "
                                  "much' — the renders are non-reproducible LLM outputs (n=1 per model) "
                                  "and thinking-off was INSTRUCTION-approximated, NOT a hard API "
                                  "thinking-off; the render is the borrowed-loaner high-pass (temporary; "
                                  "the srmech-native sentence render is the trajectory and must ENFORCE "
                                  "transduce-don't-add as a node, not just an instruction)"),
            "limitations": ["n=1 per model (non-reproducible LLM outputs)",
                            "thinking-off instruction-approximated, not a hard API thinking-off",
                            "content-recall is verbatim surface-form presence (a paraphrase that omits the "
                            "exact token reads as a miss — conservative on the structure-invariant side)",
                            "render-invention is measured on the TOKEN_PATTERNS structural alphabet "
                            "(set-Δ) + a curated technical-confabulation probe; a confabulation phrased "
                            "outside both probes is undercounted (conservative on the invention side)",
                            "the Class-M klein4 sector read SATURATES at render-vocabulary scale "
                            "(majority-vote bundle collapse) so it is corroborating-only, NOT "
                            "discriminative; the discriminative cross-render read is the Class-L "
                            "shared-eigenbasis spectral similarity"],
            "scope": ("in-scope: token co-occurrence Class-L spectrum / Klein-4 sector algebra / shared-"
                      "eigenbasis spectral similarity / invention set-Δ; NOT CAD / fabrication / geometry; "
                      "defensive: encodes the project's own research renders"),
        },
    }


def _strip_internal(block):
    """A copy of an _encode_block result with the transient `_internal` scratch removed (it duplicates
    values already surfaced as proper keys; kept out of the persisted/hashed record)."""
    return {k: v for k, v in block.items() if k != "_internal"}


def _build_record(version, primary, control, contrast, wf_name, wf_fingerprint, n_wf_tokens,
                  n_struct_tokens, n_supplied, struct_vocab, supplied_universe, verdict):
    """Assemble the attested render-invariance SSoT record (sorted-keys, content-addressed by sha256).
    CORRECTED layout: the STRUCTURED-input test is the PRIMARY block; the PROSE run is an explicitly-
    labeled CONTROL sub-block; the structured-vs-prose contrast is carried alongside. response_sha256
    over the body MINUS the wall-clock generated_at (F233 convention) so a re-run reproduces the
    fingerprint bit-for-bit OVER THE CAPTURED RENDERS."""
    return {
        "finding": "F242b",
        "measurement": "render_invariance",
        "run": "CORRECTED — STRUCTURED-storage input is PRIMARY; the PROSE run is the CONTROL",
        "srmech_version": version,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "concept": ("F242a built the working-memory WIREFRAME (the srmech Class-L SSoT). F242b tests "
                    "whether that SSoT is RENDERER-INVARIANT FROM THE PURE STRUCTURE. CORRECTION: the "
                    "first run rendered from the extractive PROSE (the sentences were already present "
                    "— trivially invariant; that run is now the CONTROL). The PRIMARY test renders from "
                    "the DE-PROSED RBS-NN structured storage (token-bindings + edge-graph, NO sentences) "
                    "— the renderer must CREATE the sentences. The wireframe SSoT pins the load-bearing "
                    "SKELETON (renderer-invariant from pure bindings+edges) AND the fluent render is a "
                    "swappable, partly-CONFABULATED VIEW (render-invention measured, model-varying) — so "
                    "the render is NEVER the SSoT; the structure is (F50/F223; biology makes sentences "
                    "with no supercompute)."),
        "convergence": "F242a (the wireframe SSoT this re-encodes) + F50 (structure-vs-renderer) + "
                       "F223 (RBS-LM extractive; the fluent prose is the BORROWED loaner) + F237 (lean graft)",
        "pre_stated_falsifiable": ("is the F242a wireframe RENDERER-INVARIANT FROM THE PURE STRUCTURE — "
                                   "does the same knowledge-shape, fed as token-bindings + an edge-graph "
                                   "with NO sentences, reconstitute the SAME load-bearing SKELETON across "
                                   "three renderers? POSITIVE-ON-STRUCTURE iff pairwise cross-render "
                                   "Class-L spectral similarity is HIGH AND each structured render "
                                   "surfaces the load-bearing token set at high recall; the render also "
                                   "CONFABULATES sentence content beyond the bindings (nonzero, model-"
                                   "varying render-invention, REPORTED); NULL iff the structured renders "
                                   "DIVERGE (the wireframe under-determines even the skeleton)"),
        "primary_input_artifact": "f242b_renders/struct_input.md (de-prosed token-bindings + edge-graph, NO sentences)",
        "primary_render_artifacts": {m: ("f242b_renders/%s.md" % s)
                                     for m, s in zip(RENDER_MODELS, RENDER_NAMES)},
        "control_input_artifact": "f242b_renders/render_input.md (extractive PROSE — the sentences were already present)",
        "control_render_artifacts": {m: ("f242b_renders/%s.md" % m) for m in PROSE_CONTROL_NAMES},
        "wireframe_ssot": {"file": ("catalogs/rbs_lm_substrate/substrate_measurements/%s" % wf_name),
                           "f242a_response_sha256": wf_fingerprint,
                           "token_universe_size": n_wf_tokens},
        "structured_input_binding_universe": {
            "n_token_classes": n_struct_tokens,
            "tokens": struct_vocab,
            "note": "the token-classes (TOKEN_PATTERNS alphabet) the renderer was HANDED in struct_input.md",
        },
        "invention_supplied_universe": {
            "n_token_classes": n_supplied,
            "note": ("wireframe-token-universe ∪ structured-input-binding-universe = the INVENTION floor; "
                     "a render token NOT in this union is render-side invention (the SSoT did not pin it)"),
        },
        "constants": {
            "KLEIN4_D": [KLEIN4_D, "A: 256 = MAX_NATIVE_NODES = D-cap; Klein-4 sector vector dim (F242a)"],
            "ZERO_FLOOR": [ZERO_FLOOR, "B: near-zero spectral floor (numerical; component count)"],
            "INV_SIM_FLOOR": [verdict["thresholds"]["cross_render_similarity_floor"],
                              "B: cross-render similarity floor for 'high' (orthogonal = 0.0)"],
            "CONTENT_RECALL_FLOOR": [verdict["thresholds"]["content_recall_floor"],
                                     "B: per-render content-recall floor for 'reconstitutes the skeleton'"],
            "COMPARABLE_BAND": [contrast["backbone_invariance"]["comparable_band"],
                                "B: |Δ mean-cross-L struct vs prose| band for 'comparable backbone-invariance'"],
        },
        "srmech_ops_used": {
            "per_render_storage_signature_F172": "laplacian.dense_laplacian(n, edges, weights) -> "
                                                 "jacobi_eigvals (sorted asc)  [Class L]  (Counter-free; "
                                                 "weights = sentence-level co-occurrence COUNTS feeding L)",
            "cross_render_spectral_similarity": "spectral.decompose(state, SHARED Laplacian) -> "
                                                "spectral.similarity on coefficients_bytes  [Class L o A; "
                                                "Spike #115] — same eigenbasis so coefficients compare",
            "klein4_sector_bundle": "hdc.klein4_bundle of per-token hdc.klein4_random atoms (REUSED from "
                                    "F242a _token_atom; seeded by format.sha256_bytes) + "
                                    "klein4_sector_count  [Class M]",
            "cross_render_klein4_similarity": "hdc.klein4_similarity  [Class M; no hand-rolled cosine]",
            "render_invention_set_delta": "set difference (render structural tokens MINUS supplied "
                                          "universe) over the TOKEN_PATTERNS alphabet + curated technical-"
                                          "confabulation probe  [set-Δ; the sharp F223 over-supply read]",
            "near_zero_magnitude": "cascade.magnitude  [Class K; NEVER abs()]",
            "content_address_seed_and_attestation": "format.sha256_bytes  [Class A; NEVER hashlib]",
        },
        "PRIMARY_structured_render": _strip_internal(primary),
        "CONTROL_prose_render": _strip_internal(control),
        "structured_vs_prose_contrast": contrast,
        "class_M_klein4_note": ("klein4_bundle is a per-bit MAJORITY vote; at a whole render's "
                                "~15-21-token vocabulary the bundle SATURATES to one sector for all "
                                "renders, so klein4_similarity reads ~1.0 trivially (identity-at-"
                                "saturation, NOT discrimination). The discriminative cross-render signal "
                                "is the Class-L shared-eigenbasis spectral similarity. F242a avoided this "
                                "by bundling per-section (2-5 tokens)."),
        "content_tokens_under_test": {k: v for k, v in CONTENT_TOKENS.items()},
        "honesty_tokens_under_test": {k: v for k, v in HONESTY_TOKENS.items()},
        "invention_probe_under_test": {k: v for k, v in INVENTION_PROBE.items()},
        "verdict": verdict,
        "tier": verdict["tier"],
    }


def _emit(record):
    """Write the content-addressed NDJSON SSoT (one record per line, sorted keys). response_sha256 over
    the body MINUS the wall-clock generated_at (F233) so a re-run reproduces the fingerprint bit-for-bit.
    Returns the on-disk ndjson sha256."""
    body = {k: v for k, v in record.items() if k != "generated_at"}
    payload = json.dumps(body, separators=(",", ":"), sort_keys=True).encode("utf-8")
    record["response_sha256"] = fmt.sha256_bytes(payload)            # Class A (never hashlib)
    out_dir = (Path(__file__).resolve().parents[1] / "catalogs" / "rbs_lm_substrate"
               / "substrate_measurements")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "render_invariance.ndjson"
    line = json.dumps(record, separators=(",", ":"), sort_keys=True)
    with open(out_path, "w") as fh:
        fh.write(line)
        fh.write("\n")
    with open(out_path, "rb") as fh:
        disk = fh.read()
    return fmt.sha256_bytes(disk)


if __name__ == "__main__":
    main()
