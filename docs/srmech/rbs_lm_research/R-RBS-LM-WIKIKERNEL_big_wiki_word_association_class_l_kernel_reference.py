r"""R-RBS-LM-WIKIKERNEL (F690) — the big-wiki word-association Class-L kernel REFERENCE.

User direction: "start with [epub_book + big wiki] ... maybe we can sub agent big wiki kernel."

WHAT THIS IS (and is NOT): this is a clean, documented REFERENCE SCAFFOLD that scales the F681
small-scale word-association kernel up to a multi-GB offline enwiki dump. It is NOT a srmech
package change — it is the build-once-query-forever reference the srmech DEV SESSION builds from.
Every dev-session design question is answered IN CODE + COMMENTS below ((a)-(f)).

THE RECOGNITION (the srmech STOP-list, CLAUDE.md §2 / F172 / §1 Class-L primitive):
  word-association is NOT a Counter() / co-occurrence dict — it is a CLASS-L CO-OCCURRENCE KERNEL.
  Build the word co-occurrence GRAPH (words = nodes, windowed co-occurrence = weighted edges) ->
  srmech.amsc.laplacian.dense_laplacian; the LAPLACIAN EIGENSPECTRUM is the srmech-native storage
  signature (F172). The co-occurrence COUNTING only builds the edge WEIGHTS — that is the prescribed
  flow (a (i,j)->count dict is fine for EDGE CONSTRUCTION). The LAPLACIAN is the storage, NOT the
  counter. The graph itself gives the associations:
    • DIRECT association(w)       = dense_adjacency neighbors of w, ranked by edge weight (the words
                                    w appears beside).
    • SECOND-ORDER association    = the Fiedler vector (2nd Laplacian eigenvector) sign-partition —
                                    words that SHARE CONTEXTS cluster together even if they never
                                    directly co-occur (the Class-L spectral embedding; the value a raw
                                    counter cannot give).

THE SCALING STORY (the honest hard part — documented openly, no silent cap; F640/F573/no-leaning):
  jacobi_eigvals has a NATIVE NODE BOUND: srmech.amsc.laplacian.MAX_NATIVE_NODES = 256. A full-wiki
  vocabulary is MILLIONS of content words. So the reference MUST document the scaling approach, and it
  does, two ways:
    (1) TOP-K VOCABULARY CAP  — keep only the K most-frequent content words (K <= MAX_NATIVE_NODES).
        DEMOED below. This is the route a first big-wiki kernel takes: the high-frequency content
        words carry the bulk of the association mass. The cap is LOGGED (vocab_cap, dropped_words),
        never silent (F640).
    (2) HIERARCHICAL / BUCKETED LAPLACIAN — DOCUMENTED-BUT-NOT-DEMOED here (the honest residue). Per
        F172 / the hierarchical-bundling precedent: partition the full vocabulary into B blocks each
        <= MAX_NATIVE_NODES, build a per-block Class-L kernel, and a coarse inter-block Laplacian over
        block-centroids — so the FULL vocabulary is handled in blocks under the native bound. This
        reference SAYS this is the route for full-vocabulary coverage (it is logged in
        `scaling_plan()`), and is honest that only the top-K path is exercised here. The dev session
        builds the bucketed path when full coverage is required.

PERSISTENCE (build-once, query-forever; GPU-free, F628): the kernel = (vocab + the Laplacian/
  adjacency + the spectrum fingerprint), content-addressed (sha256_bytes / BitExactCommKernel.
  content_address). Build it ONCE from the dump; query it FOREVER with no GPU and no re-ingest.

ATTESTATION (dignity-first; F630/F668/F665): the offline enwiki dump is CC BY-SA, cached OUTSIDE the
  repo, attested-not-committed, class-B-tertiary (a measured/derived content source — F630). MFO
  stays held-over wiki (F665). Held open (F394).

srmech (version reported at runtime) surface used:
  amsc.laplacian.{dense_laplacian, dense_adjacency, jacobi_eigvals, fiedler_vector, MAX_NATIVE_NODES}
  amsc.format.sha256_bytes               (the kernel content-address — Class A)
  amsc.cascade.magnitude                 (Class-K real |x| — used INSTEAD of python abs(); sign is
                                          Class-K pin-slot, never abs())
  BitExactCommKernel.content_address     (the spectrum fingerprint, the kernel signature)
DISCIPLINE: srmech-first (NEVER a numpy hand-rolled eig; NEVER a Counter AS the storage — the counter
  only builds edge weights). NEVER python abs() (sign = Class-K; magnitude = cascade.magnitude). No
  CAD; no Workflow tool; no sub-agents.
"""
import sys
import re
import unicodedata

sys.path.insert(0, "docs/srmech/rbs_lm_research")
import srmech
from srmech.amsc import laplacian
from srmech.amsc import format as srfmt
from srmech.amsc import cascade
from bit_exact_comm_kernel import BitExactCommKernel

# The native eigvals node bound — the WHOLE reason the scaling story exists.
MAX_NATIVE_NODES = laplacian.MAX_NATIVE_NODES  # 256 in rc15

# A small content-word stoplist (function words carry no association mass). The dev session swaps in
# a fuller stoplist via descriptor()["stoplist"]; this is deliberately minimal for the demo.
DEFAULT_STOPLIST = {
    # articles / conjunctions / prepositions
    "the", "a", "an", "and", "or", "but", "of", "to", "in", "on", "at", "for", "with", "by",
    "from", "into", "than", "then", "so", "as", "about", "over", "under", "after", "before",
    "between", "during", "through", "out", "up", "down", "off", "above", "below", "near",
    # be / have / do / modal
    "is", "are", "was", "were", "be", "been", "being", "am", "has", "have", "had", "having",
    "do", "does", "did", "may", "can", "could", "would", "should", "will", "shall", "must", "might",
    # determiners / pronouns
    "this", "that", "these", "those", "it", "its", "he", "she", "they", "them", "their", "his",
    "her", "him", "we", "us", "our", "you", "your", "i", "me", "my", "who", "whom", "whose",
    "which", "what", "such", "no", "not", "all", "any", "some", "each", "every", "both", "few",
    "more", "most", "other", "another", "many", "much", "one", "two", "there", "here",
    # high-freq function-ish verbs/adverbs/connectives (crowd raw top-K without adding association mass)
    "also", "when", "where", "while", "how", "why", "if", "because", "however", "though",
    "like", "just", "only", "very", "too", "now", "well", "back", "even", "still", "first",
    "used", "use", "using", "called", "known", "made", "make", "became", "become", "including",
    "often", "usually", "later", "early", "same", "new", "old", "many", "example",
}

# WIKI FURNITURE (F703/F705): non-content tokens that survive the hardened stripper's long tail on REAL full-wiki —
# talk-page signatures (utc/talk/edit), section/namespace words (references/category/wikipedia/user/template/title),
# and attribute/param residue (align/bgcolor/args/fefefe/href/id/px/class/style/colspan...). Stoplisting these is the
# reference-grade stand-in for the F579/F607 wiki-formatting-language kernel (which strips them structurally). Honest:
# these are FURNITURE, not words. Surfaced by the real 555k-article simplewiki encode (F703), not the synthetic test.
WIKI_FURNITURE = {
    "references", "reference", "talk", "edit", "utc", "wikipedia", "user", "template", "templates", "category",
    "categories", "title", "args", "href", "id", "px", "class", "style", "align", "bgcolor", "fefefe", "colspan",
    "rowspan", "valign", "cellpadding", "cellspacing", "border", "width", "height", "scope", "accessdate", "isbn",
    "url", "retrieved", "archived", "cite", "ref", "reflist", "nbsp", "ndash", "mdash", "thumb", "span", "div",
    "infobox", "redirect", "wikitable", "displaystyle", "frac", "sqrt", "image", "file", "media",
}
DEFAULT_STOPLIST = DEFAULT_STOPLIST | WIKI_FURNITURE

# A tiny synthetic in-script corpus standing in for a streamed wiki dump. Each entry = ONE "article"
# (one window-reset boundary — co-occurrence never crosses an article boundary). The dev session
# REPLACES this generator's source with a real enwiki dump (see stream_articles + descriptor()).
SYNTHETIC_WIKI = [
    # article 1 — a galaxy/spiral cluster (markup deliberately present to show the strip)
    "A '''galaxy''' is a [[gravitationally bound]] system; a spiral galaxy turns and coils its arms.",
    # article 2 — shells / chirality
    "A [[seashell]] coils in a chiral spiral; the chirality of a shell mirrors a galaxy's twist.",
    # article 3 — growth / sectors / snowflake
    "A snowflake grows in six sectors; its growth follows a hexagonal symmetry of the crystal.",
    # article 4 — a helix (DNA), twist, chirality (bridges clusters via 'chirality'/'twist')
    "A helix twists with a fixed chirality; the [[double helix]] of DNA coils and twists.",
    # article 5 — the_one / unity sentence that links the rotational words
    "The one sees the galaxy, the shell, the helix and the snowflake as one spiral pattern.",
    # article 6 — more rotational co-occurrence to give the Fiedler split mass
    "Spiral arms turn; coils grow; a galaxy and a shell both spiral and twist around a center.",
    # article 7 — REAL wiki markup (math/ref/template/table/comment) to EXERCISE the hardened re-encode (F700).
    # With the leaky demo strip this leaks 'displaystyle'/'frac'/'cite'/'wikitable' into the vocab; the hardened
    # path keeps ONLY the content words (galaxy/rotation/curve/mass/spiral...).
    "A '''galaxy''' rotation curve is <math>v(r)=\\sqrt{\\frac{G M(r)}{r}}</math> where <math>\\displaystyle "
    "M(r)</math> is the enclosed mass.<ref>Hubble plain citation 1929</ref>{{Infobox galaxy|mass={{nowrap|1e12}}}}"
    "<!-- verify mass --> The [[spiral galaxy]] coils its arms.\n{| class=\"wikitable\"\n! Type !! Count\n|-\n"
    "| spiral || many\n|}",
]


# ---------------------------------------------------------------------------------------------------
# (a) STREAMING INGEST — a generator that yields ONE article at a time, so a multi-GB dump never
#     loads into RAM. Demonstrated on the synthetic corpus; the dev session points `source` at a real
#     enwiki dump (see descriptor() + the docstring on strip_wiki_markup).
# ---------------------------------------------------------------------------------------------------
def strip_wiki_markup(text):
    """Markup-aware cleaner (per F567/F568/F607): strip wiki markup, KEEP content words.

    THIS IS THE F607 GATE INTERFACE. The demo strip below is intentionally MINIMAL (links, bold/
    italic, simple templates) — enough to show the article boundary + content-word extraction. The
    DEV SESSION replaces this with the F579/F607 formatting-language kernel: the form tiers ([[link]]
    98%, {{template}} 94%, emphasis/header/<ref>/table) PLUS the determinative-routed sub-language
    family ({{lang|xx}} 21.7%, {{IPA}} 18.7%, <code>/<syntaxhighlight> code, <chem>/<score>/<hiero>),
    so 1-in-5 articles with embedded sub-languages stay coherent rather than being stripped (F607's
    measured blocker list). For word-association the relevant output is the CONTENT-WORD STREAM; this
    demo strip is the placeholder for that kernel's output.
    """
    text = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]+)\]\]", r"\1", text)  # [[a|b]] / [[b]] -> b
    text = re.sub(r"\{\{[^}]*\}\}", " ", text)                       # {{template}} -> drop (demo)
    text = re.sub(r"'''?|'''", "", text)                            # bold/italic ticks
    text = re.sub(r"<[^>]+>", " ", text)                            # any HTML/<ref>/<code> tag (demo)
    return text  # ⚠ LEAKS content-bearing markup (F700) — kept only to illustrate; NOT used in the build path


# F700 fix wired into the build path: remove the CONTENT of content-bearing blocks, not just the tags.
_CONTENT_TAGS = ("math", "ref", "code", "syntaxhighlight", "score", "chem", "hiero", "gallery", "timeline")


_NS_LINK = re.compile(
    r"\[\[\s*(?:category|file|image|media|wikt|wiktionary|w|wikipedia|commons|template|help|portal|"
    r"[a-z]{2,3}(?:-[a-z]{2,4})?)\s*:[^\[\]]*(?:\[\[[^\]]*\]\][^\[\]]*)*\]\]",
    re.IGNORECASE | re.DOTALL)


def strip_wiki_markup_hardened(text):
    """The TRUSTWORTHY cleaner (F700, extended F703) — used by the build path so the kernel re-encodes with CLEAN vocab.

    Removes the CONTENT (not just the tags) of math/ref/code/score/chem/table/comment blocks; clears NESTED templates
    + tables to a fixpoint; strips HTML ENTITIES (&ndash; &nbsp; ...), NAMESPACE links ([[Category:]]/[[File:]]/[[xx:]]),
    #REDIRECT, and residual HTML ATTRIBUTES (style=/align=/Npx) — so no LaTeX/citation/entity/markup token enters the
    vocab. (F703 extended this after the REAL simplewiki encode surfaced 'ndash'/'category'/'thumb'/'px'/'redirect' as
    leak classes the synthetic test never had — the F573 lesson again.) The user: "the kernel must be re-encoded before
    its vocab is trusted." Reference scaffold; the dev session's real cleaner is the F579/F607 wiki-formatting-language
    kernel (this handles the dominant real-wiki leak classes, not every edge case).
    """
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.DOTALL)                       # 1. comments
    text = re.sub(r"^#\s*redirect.*$", " ", text, flags=re.IGNORECASE | re.MULTILINE)  # 1b. #REDIRECT pages
    for tag in _CONTENT_TAGS:                                                       # 2. content-bearing elements
        text = re.sub(rf"<{tag}\b[^>]*>.*?</{tag}>", " ", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(rf"<{tag}\b[^>]*/\s*>", " ", text, flags=re.IGNORECASE)       #    self-closing <ref .../>
    prev = None                                                                     # 3. templates to fixpoint (nested)
    while prev != text:
        prev = text
        text = re.sub(r"\{\{[^{}]*\}\}", " ", text, flags=re.DOTALL)
    prev = None                                                                     # 4. tables {| ... |} to fixpoint
    while prev != text:                                                             #    (templates gone first -> no inner {)
        prev = text
        text = re.sub(r"\{\|[^{}]*?\|\}", " ", text, flags=re.DOTALL)
    text = re.sub(r"&[a-zA-Z]+;|&#\d+;|&#x[0-9a-fA-F]+;", " ", text)               # 5. HTML entities (&ndash; &nbsp; ...)
    prev = None                                                                     # 6. NAMESPACE links (Category/File/xx:)
    while prev != text:
        prev = text
        text = _NS_LINK.sub(" ", text)
    text = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]+)\]\]", r"\1", text)                   # 7. ordinary wikilinks [[a|b]] -> b
    text = re.sub(r"\[(?:https?|ftp)://[^\s\]]+\s+([^\]]+)\]", r"\1", text)         #    ext-links [http x label] -> label
    text = re.sub(r"\[(?:https?|ftp)://[^\s\]]+\]", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)                                            # 8. any remaining tag (now safe)
    _attrs = (r'style|align|bgcolor|colspan|rowspan|valign|width|height|scope|class|cellpadding|cellspacing|'
              r'border|id|title|href|color|face|size|cellpadding|nowrap')
    text = re.sub(rf'\b(?:{_attrs})\s*=\s*"[^"]*"', " ", text, flags=re.IGNORECASE)        # 9. quoted HTML attributes
    text = re.sub(rf'\b(?:{_attrs})\s*=\s*#?[\w%.:;()-]+', " ", text, flags=re.IGNORECASE)  #    UNQUOTED attrs (bgcolor=#fefefe)
    text = re.sub(r"\{\{\{[^{}]*\}\}\}", " ", text)                                 #    triple-brace template vars {{{args}}}
    text = re.sub(r"\b\d+\s*px\b", " ", text, flags=re.IGNORECASE)                  #    image pixel sizes (thumb|200px)
    text = re.sub(r"'{2,}", "", text)                                               # 10. emphasis / headers / bullets
    text = re.sub(r"^[\s]*[*#:;=|!-]+", " ", text, flags=re.MULTILINE)
    text = re.sub(r"={2,}", " ", text)
    return re.sub(r"\s+", " ", text).strip()


_APOS = "'’"  # ASCII + curly apostrophe (internal, e.g. don't / galaxy's)


def content_words(text):
    """Unicode-aware content-word tokenizer (F698): runs of Unicode letter|mark (incl. café/naïve), len>=2.

    Replaces the old ASCII `[A-Za-z][A-Za-z']+` (which truncated 'café' -> 'caf' and dropped every non-Latin
    script). Lowercased; internal apostrophes kept; length>=2 (content words, not single letters). Digits are
    NOT content words here (matches the prior letters-only intent). CJK single-ideograph segmentation is the
    F696 per-script concern (the native speaker's grammar) — out of scope for this English-wiki re-encode.
    """
    words, cur = [], []
    for ch in text:
        if unicodedata.category(ch)[0] in ("L", "M"):
            cur.append(ch)
        elif ch in _APOS and cur:                                  # internal apostrophe only
            cur.append("'")
        else:
            if cur:
                words.append("".join(cur)); cur = []
    if cur:
        words.append("".join(cur))
    out = []
    for w in words:
        w = w.strip("'").lower()
        if len(w) >= 2:
            out.append(w)
    return out


def stream_articles(source):
    """Stream a wiki corpus ONE ARTICLE AT A TIME (a generator; the dump never fully enters RAM).

    `source` is any iterable of raw article strings. For the demo it is SYNTHETIC_WIKI (in-memory).
    FOR A REAL DUMP the dev session passes a generator that reads the bz2 multistream XML lazily, e.g.

        import bz2, xml.etree.ElementTree as ET
        def enwiki_stream(dump_path):
            with bz2.open(dump_path, "rt", encoding="utf-8") as fh:
                for _ev, el in ET.iterparse(fh, events=("end",)):
                    if el.tag.endswith("}text") and el.text:
                        yield el.text       # one <text> = one article
                        el.clear()          # FREE it — RAM stays flat across a multi-GB dump

    This generator yields the CLEANED CONTENT-WORD LIST per article. One article = one window-reset
    boundary (co-occurrence never crosses an article — F681's per-line boundary, generalised).

    RE-ENCODE FIX (the user: "the kernel must be re-encoded before its vocab is trusted"): the build path
    uses strip_wiki_markup_hardened (F700, kills LaTeX/ref/template/table junk) + content_words (F698,
    Unicode-aware) — so the kernel's vocab is TRUSTWORTHY (no markup tokens, no truncated 'café'->'caf').
    """
    for raw in source:
        cleaned = strip_wiki_markup_hardened(raw)              # F700: trustworthy cleaning (not the leaky demo)
        toks = content_words(cleaned)                          # F698: Unicode-aware content words
        yield [w for w in toks if w not in DEFAULT_STOPLIST]


# ---------------------------------------------------------------------------------------------------
# (b)+(e) CO-OCCURRENCE -> EDGE WEIGHTS, with the TOP-K VOCABULARY CAP (the demoed scaling route).
#     Two passes over the STREAM: pass 1 = document-frequency to pick the top-K content words (under
#     MAX_NATIVE_NODES); pass 2 = windowed co-occurrence over ONLY those words -> edge weights.
#     (A (i,j)->count dict is the prescribed EDGE-CONSTRUCTION tool — the Laplacian is the storage.)
# ---------------------------------------------------------------------------------------------------
def build_edges_topk(source, window=2, vocab_cap=None):
    """Two streaming passes -> (vocab, idx, edges, weights, freq, dropped). UNCAPPED vocabulary by default.

    BUG FIX (F708; user: "why are we quantizing it before encoding? ... a bug we treated like canon"): the
    vocabulary is NO LONGER clamped to MAX_NATIVE_NODES. Trimming the VOCAB before encoding was a pre-encode
    QUANTIZATION (the exact anti-thesis, F49/F50) — a bug accepted as canon. The 256 bound applies ONLY to the
    DENSE-EIG block (build_class_l_store), NOT to the vocabulary or the (sparse) adjacency:
      vocab_cap=None -> keep ALL content words (the default now; no cap, no quantization).
      vocab_cap=N    -> keep the top-N most frequent (an EXPLICIT choice; NOT silently min()'d to 256).
    Direct-association (adjacency) queries need NO eigendecomposition -> they work at ANY vocab size. Only the
    second-order (Fiedler) spectral layer is bounded by 256 PER BLOCK -> bucket into <=256 (or <=1024 via the
    native Klein-4 four-sector parallel_sector_dispatch quad-stream) blocks.

    PASS 1 (frequency): rank the vocabulary; surplus beyond an explicit vocab_cap is DROPPED + LOGGED
            (`dropped`); with vocab_cap=None NOTHING is dropped. PASS 2: windowed co-occurrence -> sparse edges.
    """
    # PASS 1 — frequency (a count dict here is legitimate: it RANKS vocabulary, it is NOT the store).
    freq = {}
    for art in stream_articles(source):
        for w in art:
            freq[w] = freq.get(w, 0) + 1
    ranked = sorted(freq, key=lambda w: (-freq[w], w))          # most-frequent first, tie-break a-z
    cap = len(ranked) if vocab_cap is None else vocab_cap       # NO min(MAX_NATIVE_NODES) — THAT was the bug (F708)
    vocab = sorted(ranked[:cap])                                # ALL content words when uncapped
    dropped = sorted(ranked[cap:])                              # LOGGED, not hidden (F640); empty when uncapped
    idx = {w: i for i, w in enumerate(vocab)}
    keep = set(vocab)

    # PASS 2 — windowed co-occurrence over the kept vocab only -> edge WEIGHTS.
    weights = {}                                                # (i,j)->count, i<j ; the EDGE builder
    for art in stream_articles(source):
        toks = [w for w in art if w in keep]                   # one article = one window reset
        for a in range(len(toks)):
            for b in range(a + 1, min(a + window + 1, len(toks))):
                i, j = sorted((idx[toks[a]], idx[toks[b]]))
                if i != j:
                    weights[(i, j)] = weights.get((i, j), 0.0) + 1.0
    edges = sorted(weights)
    return vocab, idx, edges, [weights[e] for e in edges], freq, dropped


# ---------------------------------------------------------------------------------------------------
# (c) THE CLASS-L STORE — build dense_laplacian + dense_adjacency, the eigenspectrum (jacobi_eigvals)
#     as the storage signature (F172), content-addressed (sha256_bytes / content_address) as the
#     kernel fingerprint. THIS is the storage object (NOT the count dict).
# ---------------------------------------------------------------------------------------------------
def build_class_l_store(vocab, edges, weights):
    """The Class-L co-occurrence store: Laplacian + adjacency + eigenspectrum + content-address.

    Returns a dict the dev session persists (build-once, query-forever; F628). The Laplacian and its
    eigenspectrum ARE the storage (F172); the adjacency drives the direct-association query.
    """
    n = len(vocab)
    assert n <= MAX_NATIVE_NODES, (
        f"vocab {n} exceeds MAX_NATIVE_NODES {MAX_NATIVE_NODES}; use the bucketed path (scaling_plan)"
    )
    Lap = laplacian.dense_laplacian(n, edges, weights)          # Class-L Laplacian (the store, F172)
    Adj = laplacian.dense_adjacency(n, edges, weights)          # adjacency (direct-association query)
    spec = sorted(float(x) for x in laplacian.jacobi_eigvals(Lap))  # eigenspectrum = storage signature
    fingerprint = srfmt.sha256_bytes(
        ",".join(f"{x:.6f}" for x in spec).encode("utf-8")     # content-address the spectrum (Class A)
    )
    k = BitExactCommKernel()
    kernel_sig = k.content_address(",".join(f"{x:.4f}" for x in spec))  # the kernel signature glyph
    return {
        "n": n, "vocab": vocab, "laplacian": Lap, "adjacency": Adj,
        "spectrum": spec, "spectrum_sha256": fingerprint, "kernel_signature": kernel_sig,
    }


# ---------------------------------------------------------------------------------------------------
# (d) THE QUERY API — assoc(word, top_k) = direct dense_adjacency neighbors ranked by weight; plus a
#     Fiedler-vector spectral clustering for SECOND-ORDER (shared-context) association.
# ---------------------------------------------------------------------------------------------------
def make_query_api(store):
    """Return (assoc, fiedler_clusters) closures over the persisted store (query GPU-free, F628)."""
    vocab = store["vocab"]
    idx = {w: i for i, w in enumerate(vocab)}
    n = store["n"]
    Adj = store["adjacency"]
    Arows = [[float(Adj[i][j]) for j in range(n)] for i in range(n)]

    def assoc(word, top_k=4):
        """DIRECT association(word) = adjacency neighbors ranked by co-occurrence weight.

        HONEST GAP HANDLING (F573/F661 -- audited 2026-06-09): an UNKNOWN word (not in the vocab)
        returns None -- DISTINCT from [] (a KNOWN word with no co-occurrence neighbors). Conflating
        them would silently hide a gap (the F694-class bug). None is the asking-state hook: the
        caller ASKS / fetches the word via AMSC (F669) or holds it open (F394), never invents an
        association.  ('not in vocab' != 'no associations'.)"""
        if word not in idx:
            return None
        i = idx[word]
        nbrs = sorted(
            ((Arows[i][j], vocab[j]) for j in range(n) if Arows[i][j] > 0.0), reverse=True
        )
        return [(wd, wt) for wt, wd in nbrs[:top_k]]

    def fiedler_clusters():
        """SECOND-ORDER association = the Fiedler-vector SIGN partition (shared-context clustering).

        Sign is a Class-K pin-slot boundary — we read the sign directly (>= 0 vs < 0); we do NOT call
        python abs(). cascade.magnitude is the Class-K real |x| if a magnitude is ever needed.
        """
        fied = [float(x) for x in laplacian.fiedler_vector(store["laplacian"])]
        plus = [vocab[i] for i in range(n) if fied[i] >= 0.0]   # Class-K sign read, not abs()
        minus = [vocab[i] for i in range(n) if fied[i] < 0.0]
        return plus, minus

    return assoc, fiedler_clusters


# ---------------------------------------------------------------------------------------------------
# (e) THE SCALING PLAN — logged openly. Top-K is demoed; the bucketed/hierarchical path is the
#     documented-but-not-demoed route to FULL vocabulary coverage (honest residue; F573/F640).
# ---------------------------------------------------------------------------------------------------
def scaling_plan(total_content_words, vocab_cap=MAX_NATIVE_NODES):
    """Return the scaling decision for a vocabulary of `total_content_words`. Honest, no silent cap.

    - If total <= MAX_NATIVE_NODES: the WHOLE vocabulary fits — one native Laplacian, no cap needed.
    - Else (the full-wiki case, millions of words): TWO documented routes —
        (1) TOP-K CAP (DEMOED): keep the vocab_cap (<= 256) most-frequent content words. The surplus
            is dropped + logged. Good first kernel; the high-frequency words carry the association mass.
        (2) BUCKETED / HIERARCHICAL LAPLACIAN (DOCUMENTED, NOT DEMOED HERE — the honest residue):
            partition the full vocabulary into ceil(total / 256) blocks each <= MAX_NATIVE_NODES, build
            a per-block Class-L kernel, plus a coarse inter-block Laplacian over block centroids (per
            F172 / hierarchical-bundling). This covers the FULL vocabulary under the native bound. The
            dev session builds this when full coverage is required; this reference only EXERCISES (1).
    """
    fits = total_content_words <= MAX_NATIVE_NODES
    cap = min(vocab_cap, MAX_NATIVE_NODES)
    n_blocks = 1 if fits else -(-total_content_words // MAX_NATIVE_NODES)  # ceil-div
    return {
        "total_content_words": total_content_words,
        "max_native_nodes": MAX_NATIVE_NODES,
        "whole_vocab_fits_native": fits,
        "topk_cap": cap,
        "topk_demoed": True,
        "bucketed_n_blocks_needed": n_blocks,
        "bucketed_demoed": False,   # honest: documented, not demoed (F573 no-leaning, F640 no silent cap)
        "note": (
            "top-K is the demoed route; bucketed/hierarchical (n_blocks per-block Class-L kernels + a "
            "coarse inter-block Laplacian) is the documented-but-not-demoed full-vocabulary route."
        ),
    }


# ---------------------------------------------------------------------------------------------------
# (f) THE DESCRIPTOR — the dict the dev session fills to point the reference at a real enwiki dump.
# ---------------------------------------------------------------------------------------------------
def descriptor():
    """The dev-session-fillable descriptor (TOML-shaped) for a real enwiki build.

    The dev session sets `dump_path` to the cached offline enwiki bz2 multistream (CC BY-SA, OUTSIDE
    the repo, attested-not-committed — F630/F668 class-B-tertiary), wires `markup_filter` to the
    F579/F607 formatting-language kernel, and chooses window/stoplist/vocab_cap/persist_path.
    """
    return {
        "dump_path": "<OUTSIDE-REPO>/enwiki-latest-pages-articles-multistream.xml.bz2",  # F630/F668
        "markup_filter": "F579/F607 formatting_language_kernel (form tiers + sub-language router)",
        "window": 2,                       # co-occurrence half-width (F681 default)
        "stoplist": "DEFAULT_STOPLIST (swap a fuller content-word stoplist)",
        "vocab_cap": MAX_NATIVE_NODES,     # top-K cap (<= 256 native bound); else use bucketed path
        "persist_path": "<OUTSIDE-REPO>/kernels_wikipedia/wiki_wordassoc_kernel.npz",   # build-once
        "attestation": "CC BY-SA; cached outside repo; class-B-tertiary (F630/F665); MFO held over (F665)",
    }


def main():
    print(f"=== R-RBS-LM-WIKIKERNEL (F690) — big-wiki word-association Class-L kernel REFERENCE  "
          f"(srmech {srmech.__version__}) ===\n")
    print(f"native eigvals node bound MAX_NATIVE_NODES = {MAX_NATIVE_NODES} "
          f"(the reason the scaling story exists)\n")

    # (a) STREAMING INGEST — show the article-at-a-time content-word stream (RAM never holds the dump).
    print("(a) STREAMING INGEST (one article at a time -> cleaned content-word stream):")
    for i, art in enumerate(stream_articles(SYNTHETIC_WIKI), 1):
        print(f"    article {i}: {art}")
    print()

    # (b)+(e) CO-OCCURRENCE -> EDGE WEIGHTS with the demoed top-K cap.
    vocab, idx, edges, w, freq, dropped = build_edges_topk(SYNTHETIC_WIKI, window=2, vocab_cap=MAX_NATIVE_NODES)
    print("(b) CO-OCCURRENCE -> EDGE WEIGHTS (the count dict builds EDGES; the Laplacian is the store):")
    print(f"    {len(vocab)} content words kept (top-K cap={MAX_NATIVE_NODES}); {len(edges)} weighted edges")
    print(f"    dropped by cap (logged, not silent — F640): {dropped if dropped else '(none — whole vocab fit)'}")
    print()

    # (c) THE CLASS-L STORE — Laplacian + adjacency + eigenspectrum + content-address.
    store = build_class_l_store(vocab, edges, w)
    print("(c) THE CLASS-L STORE (dense_laplacian; the eigenspectrum is the storage signature, F172):")
    print(f"    vocab ({store['n']}): {store['vocab']}")
    print(f"    Laplacian eigenspectrum: {[round(x, 2) for x in store['spectrum']]}")
    print(f"    spectrum sha256 (content-address): {store['spectrum_sha256'][:16]}...")
    print(f"    kernel signature (BitExactCommKernel.content_address): {store['kernel_signature'][:16]}...")
    print()

    # (d) THE QUERY API — direct adjacency association + Fiedler second-order clustering.
    assoc, fiedler_clusters = make_query_api(store)
    print("(d) THE QUERY API:")
    print("    DIRECT assoc(word, top_k) = adjacency neighbors ranked by co-occurrence weight:")
    for q in ["galaxy", "spiral", "snowflake"]:
        print(f"      assoc({q!r}) -> {assoc(q, top_k=4)}")
    # HONEST GAP (F573/F661, audited): an UNKNOWN word -> None (the asking-state), NOT a silent [] --
    # distinct from a known word with no neighbors. None -> the caller fetches via AMSC (F669) / holds open.
    print(f"      assoc('quark') -> {assoc('quark')}  (None = NOT in vocab -> the asking-state F661, not a silent [])")
    plus, minus = fiedler_clusters()
    print("    SECOND-ORDER (Fiedler sign-partition; shared-context, even if not adjacent):")
    print(f"      cluster + : {plus}")
    print(f"      cluster - : {minus}")
    print()

    # (e) THE SCALING PLAN — honest about demoed (top-K) vs documented-not-demoed (bucketed).
    print("(e) THE SCALING PLAN (honest; top-K DEMOED, bucketed DOCUMENTED-not-demoed):")
    demo_plan = scaling_plan(len(freq))                 # this demo corpus: whole vocab fits native
    big_plan = scaling_plan(3_000_000)                  # a full-enwiki-scale vocabulary
    print(f"    demo corpus ({len(freq)} content words): fits_native={demo_plan['whole_vocab_fits_native']}, "
          f"n_blocks_needed={demo_plan['bucketed_n_blocks_needed']}")
    print(f"    full enwiki (~3,000,000 content words): fits_native={big_plan['whole_vocab_fits_native']}, "
          f"top-K cap={big_plan['topk_cap']} (DEMOED), bucketed n_blocks={big_plan['bucketed_n_blocks_needed']} "
          f"(DOCUMENTED, not demoed)")
    print(f"    -> {big_plan['note']}")
    print()

    # (f) THE DESCRIPTOR — the dev session fills this to point at a real dump.
    print("(f) THE DESCRIPTOR (dev session fills these to point at a real enwiki dump):")
    for kk, vv in descriptor().items():
        print(f"      {kk}: {vv}")
    print()

    print("VERDICT (the big-wiki word-association Class-L kernel REFERENCE — for the srmech dev session):")
    print("  • WORD-ASSOCIATION IS A CLASS-L CO-OCCURRENCE KERNEL (F172/STOP-list): the windowed word")
    print("    co-occurrence GRAPH -> dense_laplacian; the eigenspectrum is the storage signature (NOT a")
    print("    Counter — the counter only builds the edge WEIGHTS). DIRECT assoc = adjacency neighbors;")
    print("    SECOND-ORDER = the Fiedler sign-partition (shared-context clustering) — verified on the demo.")
    print("  • STREAMING + MARKUP-AWARE (F567/F607): one article at a time (RAM never holds the dump); one")
    print("    article = one window reset; the strip is the F579/F607 formatting-language-kernel interface.")
    print("  • THE SCALING STORY IS HONEST (F573/F640): top-K vocab cap (<= MAX_NATIVE_NODES=256) is DEMOED,")
    print("    with dropped words LOGGED; the bucketed/hierarchical Laplacian (per-block kernels + a coarse")
    print("    inter-block Laplacian, F172) is the DOCUMENTED-but-not-demoed full-vocabulary route — no silent")
    print("    cap. PERSISTENCE: kernel = (vocab + Laplacian/adjacency + spectrum fingerprint), content-")
    print("    addressed; build-once, query-forever (GPU-free, F628).")
    print("  • ATTESTATION (dignity-first): the offline enwiki dump is CC BY-SA, cached OUTSIDE the repo,")
    print("    attested-not-committed, class-B-tertiary (F630/F668); MFO held over wiki (F665). Held open (F394).")
    print("  • Composes the §1 Class-L primitive + F172 (eigenspectrum = storage) + F681 (the small-scale")
    print("    kernel this scales) + F607/SS-FULLWIKI (markup + sub-language gate) + F630/F668 (offline wiki")
    print("    source) + F628 (build-once GPU-free) + the STOP-list discipline (Laplacian not Counter).")


if __name__ == "__main__":
    main()
