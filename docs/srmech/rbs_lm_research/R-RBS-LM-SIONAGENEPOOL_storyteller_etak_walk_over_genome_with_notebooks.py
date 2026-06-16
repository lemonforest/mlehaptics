r"""R-RBS-LM-SIONAGENEPOOL (F739-followon) — wire the storyteller + etak-walk into the genome, and put the
FOUNDATIONAL MFO + srmech research notebooks into Siona's genepool. srmech 0.7.5rc149.

WHAT THIS DOES:
  1. Builds the full Siona GENEPOOL genome on disk: siona_identity · signwriting (F735) · dict-en-1600 +
     dict-en-2026 (F739 era-dictionaries) · **mfo_notebook** + **srmech_notebook** (each section = a GENE).
  2. A genome-BACKED storyteller World whose knowledge IS the genepool — it INTROSPECTS (genome_catalog), routes a
     prompt to a chromosome, and ETAK-WALKS it (page the chromosome's genes, navigate to the section that matches),
     then RENDERS, or ASKS on a gap (F661 carries). This is STORYMODULE's World, genome-backed (the SIONASERVER /v1
     would import THIS instead of its hardcoded demo shelf).

ETAK-WALK (F704 "thinking is a grounded walk, not a trace") — inference, NOT retrieval: a co-occurrence surface
(Class-L adjacency, srmech.amsc.text.cooccurrence_edges + laplacian.dense_adjacency) is built over ALL content
kernels — that IS the LM surface. The input is INVERSE-ETAK located on it (its tokens = landmarks = the fixed
frame), then a FORWARD-ETAK walk (IDF-gated, no-revisit — the F510 etak-head / F166 ride) hops the co-occurrence
graph, and the answer COMPOSES from the sections the walk converges on. Routing is EMERGENT (no keyword if-else;
'MFO' walks to MFO sections, 'awful' to the dict). Remaining follow-on: walk the Laplacian EIGENVECTORS (Fiedler /
spectral etak-head), not just the adjacency neighbours — and deep per-paragraph encoding (the WIKIKERNEL pipeline).

NOTEBOOKS-AS-KERNELS (honest scope): each notebook's `## ` sections become GENES (content-addressed leaves); the
renderable text (heading + first content line) is MPR-attested payload (NDJSON, the AMSC content layer). So the
genome holds the notebook's introspectable SECTIONAL STRUCTURE; full per-paragraph deep-encoding is the WIKIKERNEL
follow-on. The MFO (ontology) + srmech (mechanism) notebooks are now in Siona's foundational genepool.

Run (rc149 venv, numpy-free), from the worktree root:
  /tmp/srmech_rc149/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-SIONAGENEPOOL_...py
No abs(); no CAD; research-subtree scaffold (NOT a package edit).
"""
import re
import json
import tempfile
import os
import importlib.util as _U
from pathlib import Path
import srmech
from srmech.amsc import genome as g, hdc, text as T
from srmech.amsc.laplacian import dense_adjacency
from srmech.amsc.format import sha256_raw, write_ndjson, read_ndjson, MPRRecord

# F764: the markup grammar is a GENOME language-layer FORM vocabulary (Class-B/F), not a one-off script — Siona
# UNDERSTANDS markup (the F762 correction). __file__-based import so it resolves regardless of cwd.
_mk_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "R-RBS-LM-MARKUPGRAMMAR_class_bf_form_layer_understand_not_strip.py")
_mk_spec = _U.spec_from_file_location("markupgrammar", _mk_path)
MK = _U.module_from_spec(_mk_spec); _mk_spec.loader.exec_module(MK)
# F796: the dep-FREE rule kernels (Python/C/LaTeX — our own grammars, no ast/sympy/pycparser). A genome language-layer
# component (sibling to the markup grammar): Siona carries the construct→A-N vocabulary AND structurally reads code/math.
_rk_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "R-RBS-LM-RULEKERNELS_dep_free_python_c_latex_grammars_for_siona.py")
_rk_spec = _U.spec_from_file_location("rulekernels", _rk_path)
RK = _U.module_from_spec(_rk_spec); _rk_spec.loader.exec_module(RK)

# F764: the genepool CHROMOSOME-SET schema version. The handler's stale-check only watches NOTEBOOK drift, so adding a
# language-layer chromosome (ni-vanuatu F761, markup F764) did NOT force a persisted-genome rebuild — Siona kept
# serving a pre-language-layer genome. This sentinel closes that gap: build_genepool stamps it; the handler rebuilds
# when the persisted stamp differs. BUMP THIS whenever the chromosome set changes.
GENEPOOL_SCHEMA_VERSION = "F796-langlayer+markup+intent+codegrammar"

DIM = 64
ONE = hdc.klein4_random(DIM, seed=0)
def _seed(t): return int.from_bytes(sha256_raw(t.encode())[:4], "big")
def _leaf(t): return hdc.klein4_random(DIM, seed=_seed(t))
def _slug(s): return (re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_") or "sec")[:36]

# === THE LANGUAGE LAYER (F761) ====================================================================================
# ni-Vanuatu = the ABSTRACT TRANSLATION LAYER (the byte/glyph-level, language-AGNOSTIC base where any language can
# inference — R-RBS-LM-25 strip-English-privilege / R-RBS-LM-54 Rosetta). SignWriting sits at the SAME level (the
# signed projection of the same abstract translations). A surface language (English) is BUILT FROM this base: a word
# is the glyph-composition of its letters, so it is a PROJECTION of ni-Vanuatu, not an independent random token.
GLYPHS = "abcdefghijklmnopqrstuvwxyz'- "          # the ni-Vanuatu abstract glyph alphabet (the universal base)
GLYPH_SET = set(GLYPHS)
_GLYPH_CACHE = {}
def _glyph(ch):                                                                  # one abstract base vector per glyph (memoized)
    v = _GLYPH_CACHE.get(ch)
    if v is None:
        v = _GLYPH_CACHE[ch] = hdc.klein4_random(DIM, seed=_seed("niv/" + ch))
    return v
def _posrole(i): return hdc.klein4_random(DIM, seed=_seed(f"niv/pos/{i}"))       # position role (order-preserving bind)
def _word_hv(w):
    """A surface word built FROM the ni-Vanuatu glyph base: bundle of character-BIGRAM binds (Class M ∘ glyphs).
    Bigrams (adjacent-glyph binds) make the projection EDIT-ROBUST — a misspelling/inflection shares most bigrams, so
    it resolves to the same abstract content (F762). Words sharing substrings share substrate; not a fresh random leaf."""
    chars = [c for c in w.lower() if c in GLYPH_SET] or ["x"]
    if len(chars) == 1:
        return _glyph(chars[0])
    parts = [hdc.klein4_bind(_glyph(chars[i]), _glyph(chars[i + 1])) for i in range(len(chars) - 1)][:32]
    return hdc.klein4_bundle(*parts)

ERA_DEFS = {
    "dict-en-1600": {"nice": "foolish or ignorant", "awful": "awe-inspiring, worthy of awe",
                     "computer": "a person who computes", "meat": "food in general", "silly": "blessed, innocent"},
    "dict-en-2026": {"nice": "pleasant, agreeable", "awful": "very bad",
                     "computer": "an electronic machine", "meat": "animal flesh", "silly": "foolish"},
}
NOTEBOOKS = {"mfo_notebook": "docs/antikythera-maths/mfo_spectral_research_notebook.md",
             "srmech_notebook": "docs/srmech/srmech_research_notebook.md"}
SW_CLASSES = ("hands", "movement", "dynamics", "head_faces", "body", "punctuation", "location")
SIONA_NAME = "Siona"
# committed learned items (git-trackable, folded into the genome as a `learned` chromosome by build_genepool);
# temporary learned items live in a gitignored `learned_temp.json` inside the genome dir (ephemeral, this-session).
LEARNED_KERNEL_FILE = Path(__file__).parent / "siona_learned_kernel.json"
# the WIKI knowledge chromosome (title -> abstract, attested CC-BY-SA per-article; built by R-RBS-LM-WIKIINGEST).
# It is a SCALABLE side-store (term-index lookup, Class-E style), NOT on the dense O(vocab^2) etak-walk surface —
# that is how it scales from this first batch to the full enwiki abstracts dump. Lives outside the repo.
WIKI_KERNEL_FILE = Path.home() / "corpora" / "wikipedia" / "wiki_knowledge_kernel.ndjson"
# the UNCAPPED relational tier (F754): word -> top-K co-occurrence neighbours for ALL ~213k vocab (compact, 32MB,
# built by R-RBS-LM-WIKIASSOC). Siona "knows the words" relationally; the input-ride (F753) steers over it.
ASSOC_FILE = Path.home() / "corpora" / "wikipedia" / "simplewiki_assoc.json"
# the DIRECTED + TYPED relation tier (F757): subject -> its strongest directed out-edges (objects that FOLLOW it =
# what it does / leads to / has) with the FRAME word labelling the edge. The rung beyond the undirected assoc: the
# input-ride (F753) can FLIP the answer by relation (a steer word matching a stored relation label surfaces those edges).
RELATIONS_FILE = Path.home() / "corpora" / "wikipedia" / "simplewiki_relations.json"
# the real DEFINITION tier (F760): title -> the lead-sentence gloss of each simplewiki article ("what X IS"), so a
# definition question gets a definition, not a relations dump. The EXACT definition side-store (pairs with assoc/relations).
GLOSS_FILE = Path.home() / "corpora" / "wikipedia" / "simplewiki_glosses.json"
# F788: the FULL-COVERAGE lead-PARAGRAPH abstract store (finishes F745's documented scale path: 216k abstracts, ≤3
# sentences). The richer-answer tier: "what is X" -> the crisp lead sentence (gloss); "tell me about/explain X" or
# "tell me more" (depth=long, F763) -> this fuller abstract. Built by R-RBS-LM-WIKIABSTRACT; CC-BY-SA simplewiki.
ABSTRACT_FILE = Path.home() / "corpora" / "wikipedia" / "simplewiki_abstracts.json"
# F791: the spectral-clumped TOME-TREE + WEB (F789/#1, built by R-RBS-LM-FULLCLUMP via the rc166 native §51) — the
# uncapped, spectrally-navigable smallwiki. {tomes: [[word…]], paths: [L/R tree address], web: {tome: [[other,wt,a,b]]}}.
# etak navigation: FIND (word→tome) → RIDE (the clump) → ZOOM (parent = siblings sharing path[:-1]) → WEB-HOP (bridge).
# F792: prefer the FRESH windowed-co-occurrence tree (clean source) for navigation; fall back to the assoc tree
# (fuller 90k coverage, noisier) for words outside the fresh common-word core.
TOME_TREE_FILE = Path.home() / "corpora" / "wikipedia" / "simplewiki_tome_tree_fresh.json"
TOME_TREE_FALLBACK = Path.home() / "corpora" / "wikipedia" / "simplewiki_tome_tree.json"

# NOTE (F743 experiment): there is NO hard-coded SIONA_SELF blurb, no _capabilities() prose, and no identity/
# greeting/capabilities regexes. Siona's self-knowledge is read from STRUCTURE at runtime — srmech.describe()
# (the substrate she runs on) + genome_catalog (the kernels she holds). RESULT: introspection IS emergent for
# those two (accurate, auto-updating); the deeper "walk my own prose to find myself" was tested and is NOISE (rare
# self-terms drag the walk into citation/appendix metadata), so it is NOT in the live card. See F743.

# --- etak-walk inference knobs ----------------------------------------------------------------------------------
ERA_ALIASES = {"dict-en-1600": "archaic old olde historical antiquity century 1600 1600s",
               "dict-en-2026": "modern current present today contemporary 2026"}
ARCHAIC_RE = re.compile(r"\b(1[0-8]\d{2}s?|archaic|olde?|historical|antiquity|centur\w*)\b")  # era signal (raw prompt)
WALK_STEPS = 5                               # forward-etak hops past the input landmarks
LANDMARK_WEIGHT = 3.0                        # convergence stays anchored to the query frame, not the walk's drift
# a section whose rendered text is notebook-MAINTENANCE (sweep/cite/appendix/milestone prose, not framework content)
# is demoted as an answer-landing — that prose reads as "fractured" and is about the document, not the subject.
MAINTENANCE_RE = re.compile(r"swept|back-?sweep|breadcrumb|closeout|how to cite|regenerat|milestone|queued|lagged"
                            r"|cross-?referenc|landed-where|roadmap|open thread", re.I)
MAINT_PENALTY = 0.15
# DELEXICAL / function words that must NOT ROUTE a query (F751): in a tiny corpus a word like "made" can look rare
# (df=1) and so IDF-amplify into a sharp-but-meaningless landmark (e.g. "how is kombucha made" -> the one section
# with "made"). These stay in the kernels (knowledge), they just can't be the routing anchor. (Principled successor:
# judge salience against the big wiki corpus once wired; this hand-set is the immediate, honest fix.)
ROUTING_STOPLIST = frozenset(
    "made make makes making made use used uses using call called calls know known knows knew based base find found "
    "finds given give gives gave get gets got getting way ways thing things kind sort type types lot like likes "
    "also well much many more most some any other another how why does did doing done need needs want wants let "
    "tell told say said see seen look looks put take takes go goes come comes work works "
    "answer answers question questions response responses reply replies explanation "
    # F787: exclusion/addition CONNECTIVES + scaffolding adverbs — function-word OPERATORS (F770), never topics.
    # ("else"/"besides" HAVE co-occurrence entries so _recognized() wrongly counted them as topics -> the F776 phrase
    # decline fired on "what else is in ketchup besides tomatoes". They are operators, consumed not routed.)
    "else besides beside except apart aside excluding versus others "
    "often sometimes usually always inside within "
    "explain describe overview "
    "navigate explore nearby neighbourhood neighborhood cluster walk near around"
    .split())   # F766/F787/F788/F791: scaffolding + connectives + about/nav-verbs, not topics
# F752: the FRAME channel — function words ARE the sentence structure (intent), the thing F751 stoplisted for ROUTING.
# Read them (on the RAW prompt; tokenize drops most) to classify the question TYPE so a how-made ≠ a what-is ≠ a phrase.
INTENT_RE = (
    ("process",    re.compile(r"\bhow\b.{0,30}\b(made|make|making|done|do|work|works|built|build|create[sd]?|"
                              r"grow[ns]?|form(ed|s)?|produced?|happen[s]?|brew|ferment)\b")),
    ("quantity",   re.compile(r"\bhow\s+(many|much|big|old|far|long|tall|fast)\b")),
    ("definition", re.compile(r"\b(what\s+(is|are|s|r)|what'?s|define|definition|meaning|who\s+(is|are|was|were))\b")),
    ("cause",      re.compile(r"\bwhy\b")),
    ("place",      re.compile(r"\bwhere\b")),
    ("time",       re.compile(r"\bwhen\b")),
)
# F763: the ELABORATION meta-signal — an answer-DEPTH axis ORTHOGONAL to intent. Like markup (F762), a request for a
# longer/shorter answer is a meta-signal Siona must COMPREHEND, not discard: "tell me more / in detail" -> deepen the
# answer; "briefly / in short" -> trim to the core. Read on the RAW prompt; controls k-edges + walk-steps + attach-extra.
ELABORATION_RE = (
    ("short", re.compile(r"\b(brief(ly)?|in brief|in short|in summary|short(er)?\s+(answer|version)|shortly|tl;?dr|"
                         r"one\s+(line|sentence|word)|just\s+(the|tell|give|a)|concise(ly)?|keep it short|"
                         r"quick(ly)?\s+answer|in a\s+(word|sentence|nutshell)|summar(y|ise|ize|izing|ising)|simply put)\b")),
    ("long",  re.compile(r"\b(tell me more|more detail|(in|more)\s+depth|in detail|elaborate|expand(\s+on)?|go on|"
                         r"say more|at length|long(er)?\s+(answer|version)|more about|everything\s+(about|on)|go deeper|"
                         r"deeper|expound|comprehensive|thorough(ly)?|full(er)?\s+(explanation|detail)|"
                         r"explain\s+(more|further|in\s+(more\s+)?detail))\b")),
)
# F763: the elaboration META-WORDS — content-ish tokens that appear inside elaboration phrases ("in DETAIL", "go DEEPER").
# Per the markup principle (F762): once _depth COMPREHENDS the signal, these are CONSUMED — stripped from the TOPIC
# channel so they never mis-route as content (e.g. "tomato in detail" must not read as the two topics tomato+detail).
ELABORATION_WORDS = frozenset(
    "detail details detailed depth elaborate elaboration briefly tldr concise concisely thorough thoroughly "
    "comprehensive comprehensively expound deeper expand expansion fuller longer shorter summary summarize "
    "summarise summarised summarized lengthy".split())
# F766: the INTENT DICTIONARY — word -> DEFINITION, the meaning substrate for the depth read. Lives in the genome as a
# `dict-intent` chromosome (same shape as dict-en). The depth ANCHORS are built from a few SEED definitions; every other
# entry then SELF-CLASSIFIES by definition-overlap (meaning), so "use definitions, not a keyword list" (user 2026-06-15):
# adding a word+definition auto-places it by meaning — no hand-tagged long/short. Defs are written so the content words
# cluster (long: detail/explain/more/full/complete; short: short/few/words/brief/main/points).
INTENT_DICT = {
    # --- the "more detail" family (longer answer) ---
    "elaborate": "to explain in more detail and add more information",
    "expound": "to explain something fully in detail",
    "expand": "to add more detail and make the answer larger",
    "detail": "a fuller account with more information",
    "detailed": "having much detail and full information",
    "thorough": "complete and done with attention to full detail",
    "comprehensive": "complete and covering everything in full detail",
    "exhaustive": "complete and including every detail",
    "verbose": "using many more words and detail than needed",
    "lengthy": "long and containing much detail",
    "extensive": "large in scope and covering much detail",
    "expansive": "broad and covering much in detail",
    "deepen": "to go into more depth and detail",
    "full": "complete with all the detail",
    "fuller": "more complete with more detail",
    "elaboration": "an explanation given in more detail",
    # --- the "less / shorter" family (shorter answer) ---
    "brief": "short and using few words",
    "concise": "short and clear using few words",
    "succinct": "short and clearly stated in few words",
    "terse": "very short and using few words",
    "short": "brief and using few words",
    "summary": "a short account giving only the main points",
    "summarize": "to give a short account of the main points",
    "summarise": "to give a short account of the main points",
    "condense": "to make shorter and more concise",
    "gist": "the short main point",
    "overview": "a short general account of the main points",
    "simple": "plain and short, not detailed",
}
# SEEDS: a few clear words per pole whose definitions BUILD the anchors; the rest self-classify by overlap.
LONG_SEEDS = ("elaborate", "detail", "thorough", "comprehensive")
SHORT_SEEDS = ("brief", "concise", "short", "summary")
DEPTH_MARGIN = 0.04                            # calibration floor (type-B, a measured separation gap; not magic)
NEGATORS = frozenset("not no never without dont isnt arent cant cannot less".split())   # frame-channel polarity flip
# F769: LOCALE layer of the language kernel — en_GB/en_US (etc.) spelling-convention variants -> the store-canonical
# spelling. This OVERRIDES a glyph mis-rank for SYSTEMATIC variants (a locality authority), but is itself overridden by
# OBSERVED USER USAGE (context/learned): localities are not the authority when the user's own input suggests another.
# Seed table (the language-kernel hook); a full bidirectional, configurable locale inventory is the data scale-up.
LOCALE_CANON = {
    "colour": "color", "flavour": "flavor", "honour": "honor", "favour": "favor", "neighbour": "neighbor",
    "labour": "labor", "behaviour": "behavior", "centre": "center", "theatre": "theater", "metre": "meter",
    "litre": "liter", "fibre": "fiber", "organise": "organize", "realise": "realize", "analyse": "analyze",
    "catalogue": "catalog", "defence": "defense", "grey": "gray", "aluminium": "aluminum", "programme": "program",
}
# F774: relational/comparison CUE words — OPERATORS (consumed from the topic channel, not routed). They trigger the
# closed-op REASONER over ≥2 topics: COMPARE -> solve-for (needs a sourced attribute, else honest decline F408);
# RELATE -> derive (intersect the two topics' held relation/co-occurrence neighbour-sets = the shared property).
COMPARE_CUES = frozenset("bigger smaller larger taller shorter heavier lighter faster slower older younger than "
                         "greater longer compare versus vs".split())
RELATE_CUES = frozenset("common share shared between difference differ relate related relation relationship link "
                        "connect connection both similar similarity".split())
# F787: the CONTENTS / "what ELSE" frame — a multi-item LIST question about ONE subject (its held neighbours), with an
# optional EXCLUSION ("besides Y"). This is NOT a definition (single sentence) and NOT a 2-topic compare/relate — it is
# "list what I hold near X, minus Y". Answers from relations + co-occurrence, honestly framed (held neighbours, not a
# verified contents/ingredient list). Fixes the "what else is in ketchup besides tomatoes" -> phrase-decline bug.
CONTENTS_RE = re.compile(
    r"\bwhat(?:'?s)?\s+(?:else|other|others|more)\b"                          # what else / what other / what more
    r"|\bwhat(?:'?s| is| are)\s+(?:in|inside)\b"                              # what is in / what's in
    r"|\b(?:besides|apart\s+from|other\s+than|aside\s+from|except|excluding)\b"  # an exclusion connective anywhere
    r"|\bingredients?\b|\bmade\s+(?:of|from|with)\b")                         # contents / composition words
EXCLUDE_RE = re.compile(r"\b(?:besides|apart\s+from|other\s+than|aside\s+from|except|excluding|not)\s+([a-z]+)")
# F788: the ABOUT frame — an open "tell me about / explain / describe X" wants the fuller ABSTRACT (≤3 sentences),
# NOT the crisp one-line definition that "what is X" wants. (depth=="long" (tell me more, F763) also serves it.)
ABOUT_RE = re.compile(r"\b(?:tell\s+\w+\s+about|tell\s+about|all\s+about|more\s+about|explain|describe|overview\s+of)\b")
# F798: the ANAPHORA frame — a follow-up whose only "subject" is a pronoun ("what can IT be used for", "tell me more
# about THEM") carries the PRIOR turn's topic forward. Without it, salient is empty and the turn misroutes to the
# identity card (the reported "what can it be used for" → [identity] bug). Fires conservatively (only when THIS turn
# names no recognized topic of its own — an explicit topic always wins).
ANAPHORA_RE = re.compile(r"\b(?:it|its|they|them|their|theirs|that|this|those|these|one|ones)\b")
# F798: the USES frame — "what can X be used for/with", "what is X used for", "use of X", "what does X go with". This
# is the same kind of multi-item neighbour LIST as CONTENTS (F787), just framed as USES; routes to the held relations +
# co-occurrence neighbours (honestly: what X appears WITH, NOT a verified list of uses).
USES_RE = re.compile(r"\b(?:used?\s+(?:for|with|in|as|to)\b|uses?\s+of\b|what\s+can\s+\w+\s+(?:be\s+)?(?:used|do)\b|"
                     r"good\s+for\b|useful\s+for\b|go(?:es)?\s+(?:with|in)\b|pair(?:ed|s)?\s+with\b|works?\s+with\b)")
# F799: self-PROVENANCE — "where is your source code / are you open source / where can I find you". Answered from her
# self-knowledge (she IS the srmech package + version), not a notebook etak-walk and not a fabricated URL.
PROVENANCE_RE = re.compile(r"\bsource\s*code\b|\byour\s+code\b|\brepo(?:sitory)?\b|\bgit(?:hub|lab)\b|\bpypi\b|"
                           r"\bopen[\s-]?source\b|where\s+do\s+you\s+live\b|"
                           r"where\s+(?:can\s+i\s+)?(?:find|download|install)\s+you\b")
# F799: the running CONTEXT must carry the conversation's CONTENT, not Siona's own rendering scaffolding — her prior
# answers are fed back verbatim, so her [bracketed] parse-lines/tags ([input-ride …], [siona · …], [etak: …]) and her
# citation/honest-note parentheticals ((source: …, CC-BY-SA), (related: …)) are stripped first, else framing words
# (input/ride/topic/steer/definition/source/simplewiki) pollute the context instead of real content. A content
# parenthetical like "(Solanum lycopersicum)" carries NO scaffold marker, so it survives.
SCAFFOLD_PAREN_RE = re.compile(r"\([^()]*?(?:CC-BY-SA|simplewiki|source:|related:|co-occurrence|derived|honest|"
                               r"these are|the walk|RELATIONS|not a verified|won'?t invent|asking-state)[^()]*\)", re.I)
# F791: the NAVIGATE frame — walk the spectral-clumped tome-tree (FIND→RIDE→ZOOM→WEB-HOP) instead of defining.
NAV_RE = re.compile(r"\b(?:navigate|explore|nearby|neighbou?rhood|what'?s\s+near|near\s+to|close\s+to|"
                    r"cluster\s+(?:of|around|for)|related\s+cluster|walk\s+(?:from|the)|what'?s\s+around)\b")
# F796: a pasted CODE / MATH fragment -> the dep-free rule kernel reads its A-N structure (Python/C/LaTeX; no interpreter).
CODE_INPUT_RE = re.compile(r"\bdef\s+\w+\s*\(|\b(?:int|void|char|float|double|long)\s+\w+\s*\(|\{[^}]*;|#include|"
                           r"\\(?:frac|sqrt|sum|int|cdot|times|alpha|beta)\b|\$[^$]+\$|[A-Za-z0-9]\s*\^\s*[\w{]")
# F753: the COUPLING weight. The input-ride parses the query into a SUBJECT (content noun -> routes) + STEER (the
# relation/frame words, incl. delexical ones F751 keeps out of routing) — and the steer BIASES kernel convergence
# (the frame becomes a direction of travel), coupling the input-walk to the kernel-walk. Subject anchors; steer nudges.
STEER_WEIGHT = 1.0


def parse_sections(path, cap=48, maxchars=700):
    """## headings -> [(section_label, heading, summary)]; summary = the section's first paragraph(s), trimmed to a
    sentence boundary (~maxchars) so renders are not cut mid-word."""
    lines = Path(path).read_text(errors="replace").splitlines()
    secs = []
    for idx, ln in enumerate(lines):
        if ln.startswith("## "):
            heading = ln[3:].strip()
            buf = []
            for j in range(idx + 1, len(lines)):
                t = lines[j].strip()
                if t.startswith("## "):
                    break                                 # next section
                if t and not t.startswith(("#", "|", "```", "<!--")):
                    buf.append(t)
                if sum(len(x) + 1 for x in buf) > maxchars:
                    break
            summ = " ".join(buf)[:maxchars]
            cut = max(summ.rfind(". "), summ.rfind("? "), summ.rfind("! "))
            if cut > 120:
                summ = summ[:cut + 1]                     # trim to a clean sentence end
            secs.append((f"{len(secs):02d}_{_slug(heading)}", heading, summ))
    return secs[:cap]


def build_genepool(path):
    payload = []                                              # MPR rows: the renderable text (AMSC content layer)
    # NO siona_identity chromosome — identity is not baked; it is read from srmech.describe() + genome_catalog at run.
    # === THE LANGUAGE LAYER (F761) — abstract translation base + its signed sibling, then surface languages on top ===
    # ABSTRACT level: ni-Vanuatu (the language-agnostic glyph base) + SignWriting (its signed projection), SAME level.
    chromosomes = [("ni-vanuatu", [(ch.strip() or "space", [_glyph(ch)]) for ch in GLYPHS])]
    payload += [("ni-vanuatu", ch.strip() or "space",
                 f"abstract translation glyph '{ch}' — the language-agnostic base every language projects from") for ch in GLYPHS]
    chromosomes.append(("signwriting", [(c, [_leaf(f"sw/{c}")]) for c in SW_CLASSES]))   # same level: the SIGNED form
    payload += [("signwriting", c, f"SignWriting symbol class: {c} (the signed form of the abstract translation)") for c in SW_CLASSES]
    # MARKUP (F764): the Class-B/F FORM vocabulary the language layer UNDERSTANDS (sibling to SignWriting — both are
    # framing layers). Markup is comprehended (unwrapped + edges extracted), never stripped (F762). The grammar IS in
    # the genome now, not a one-off script: each form-class is a gene; understand_markup() is its operational read.
    chromosomes.append(("markup", [(c, [_leaf(f"markup/{c}")]) for c in MK.MARKUP_FORM_CLASSES]))
    payload += [("markup", c, f"markup form-class '{c}' — a Class-B/F framing form the language layer UNDERSTANDS "
                 f"(a separable form layer comprehended, never stripped; link forms also yield relationship edges)")
                for c in MK.MARKUP_FORM_CLASSES]
    # F796: the code-grammar chromosome — the dep-FREE Python/C/LaTeX rule kernels' construct→A-N vocabulary (RK), so
    # Siona HOLDS the rule-kernel knowledge (a programming/math language is a closed grammar ENCODED, no interpreter dep).
    chromosomes.append(("code-grammar", [(con, [_leaf(f"code/{con}")]) for con in RK.CONSTRUCT_CLASSES]))
    payload += [("code-grammar", con, f"code/math construct '{con}' → {cls} — {gloss} (dep-free rule kernel, F795/F796)")
                for con, (cls, gloss) in RK.CONSTRUCT_CLASSES.items()]
    # dict-intent (F766): the INTENT word→definition dictionary — the meaning substrate the depth read uses (anchors are
    # built from seed definitions; entries self-classify by definition-overlap). Genome-native, same shape as dict-en.
    chromosomes.append(("dict-intent", [(w, [_word_hv(w)]) for w in INTENT_DICT]))
    payload += [("dict-intent", w, d) for w, d in INTENT_DICT.items()]
    # SURFACE level: English — each word BUILT FROM the ni-Vanuatu glyph base (_word_hv), a projection not a random leaf.
    for era, defs in ERA_DEFS.items():
        chromosomes.append((era, [(w, [_word_hv(w)]) for w in defs]))
        payload += [(era, w, d) for w, d in defs.items()]
    for kernel, nbpath in NOTEBOOKS.items():
        secs = parse_sections(nbpath)
        chromosomes.append((kernel, [(lab, [_leaf(f"{kernel}/{lab}")]) for lab, _, _ in secs]))
        payload += [(kernel, lab, f"{head} — {summ}".strip(" —")) for lab, head, summ in secs]
    if LEARNED_KERNEL_FILE.exists():                          # committed learned items -> a first-class `learned` gene-set
        learned = json.loads(LEARNED_KERNEL_FILE.read_text() or "{}")
        if learned:
            chromosomes.append(("learned", [(t, [_leaf(f"learned/{t}")]) for t in learned]))
            payload += [("learned", t, txt) for t, txt in learned.items()]
    strand = g.genome(chromosomes=[(lab, genes) for lab, genes in chromosomes], the_one=ONE)
    g.genome_save(strand, path, ONE, [lab for lab, _ in chromosomes])
    rows = [MPRRecord(mpr_version="1.0",
                      data={"kernel": k, "key": key, "text": txt},
                      data_schema_id="rbslm://schema/siona_genepool/v1",
                      attestation={"retrieved_at": "2026-06-14T00:00:00Z",
                                   "response_sha256": sha256_raw(f"{k}/{key}/{txt}".encode()).hex(),
                                   "license": "CC0", "parser_version": f"srmech {srmech.__version__}"},
                      rendering={"name": f"{k}:{key}", "purpose": "genepool kernel content", "cite_as": k})
            for k, key, txt in payload]
    write_ndjson(Path(path) / "genepool.ndjson", rows)
    (Path(path) / "genepool.schema").write_text(GENEPOOL_SCHEMA_VERSION)   # F764: chromosome-set stamp (forces rebuild on change)


class SionaGenepool:
    """STORYMODULE's World, genome-backed. Inference is an ETAK-WALK over the genome's co-occurrence surface
    (Class-L), NOT a keyword route to a stored section: the input is INVERSE-ETAK located on the surface (its
    tokens = landmarks = the fixed frame; "meaning falls out of the supplied rules", F583), then a FORWARD-ETAK
    walk (IDF-gated, no-revisit — the F510 etak-head / F166 ride) explores the relationship structure, and the
    answer COMPOSES from wherever the walk converges (attested content only — F661, can't hallucinate). Routing is
    EMERGENT (the walk from 'MFO' terms lands in MFO sections). There are NO hard-coded replies at all (F743): even
    "who/what are you" / "what can you do" are answered by `_structure_card()` — read from srmech.describe() +
    genome_catalog. Inference path: substantive tokens that hit the surface → walk; tokens that hit nothing →
    asking-state + structure-card; no substantive tokens at all → structure-card. Self-knowledge is introspected
    from the structure she is, never asserted."""
    def __init__(self, path):
        self.path = path
        self._danchors = None                                 # F766: lazy cache for the (long, short) depth anchors
        self._text = {(r.data["kernel"], r.data["key"]): r.data["text"]
                      for r in read_ndjson(Path(path) / "genepool.ndjson")}
        self._build_surface()
        # WRITE-MODE store (the learning loop): learned[term] = text, the union of committed (already in the genome
        # as the `learned` chromosome) + temporary (gitignored learned_temp.json inside the genome dir, this-session).
        self._temp_file = Path(path) / "learned_temp.json"
        self.learned = {key: txt for (k, key), txt in self._text.items() if k == "learned"}   # committed
        if self._temp_file.exists():
            self.learned.update(json.loads(self._temp_file.read_text() or "{}"))               # + temporary
        # WIKI knowledge chromosome — a scalable side-store (term-index), loaded from its own ndjson (not the strand)
        self.wiki, self.wiki_title, self.wiki_cite, self.wiki_toks, self.wiki_idx = {}, {}, {}, {}, {}
        if WIKI_KERNEL_FILE.exists():
            for r in read_ndjson(WIKI_KERNEL_FILE):
                k = r.data["key"]
                self.wiki[k] = r.data["text"]
                self.wiki_title[k] = r.data.get("title", k)
                self.wiki_cite[k] = (r.rendering or {}).get("cite_as", f"Wikipedia: {self.wiki_title[k]}")
                tt = {self._norm(w) for w in T.tokenize(self.wiki_title[k])}
                xt = {self._norm(w) for w in T.tokenize(r.data["text"])}
                self.wiki_toks[k] = (tt, xt)
                for w in tt | xt:
                    self.wiki_idx.setdefault(w, set()).add(k)
        # WIKI-ASSOC tier (F754): word -> top-K co-occurrence neighbours, UNCAPPED (~213k words). The relational layer
        # ("Siona knows the words") + the surface the input-ride (F753) steers over. Compact (32MB), loaded once.
        self.assoc, self.assoc_freq = {}, {}
        if ASSOC_FILE.exists():
            _a = json.loads(ASSOC_FILE.read_text())
            self.assoc = _a.get("assoc", {})
            self.assoc_freq = _a.get("freq", {})
        # DIRECTED + TYPED relation tier (F757): subject -> [[object, count, relation], ...] top-K directed out-edges.
        self.relations = {}
        self.rel_labels = set()                               # the relation-label vocabulary (for the input-ride steer)
        if RELATIONS_FILE.exists():
            self.relations = json.loads(RELATIONS_FILE.read_text()).get("subjects", {})
            for edges in self.relations.values():
                for _o, _c, r in edges:
                    if r != "→":
                        self.rel_labels.add(r)
        # the DEFINITION side-store (F760): title -> lead-sentence gloss ("what X IS").
        self.glosses = {}
        if GLOSS_FILE.exists():
            self.glosses = json.loads(GLOSS_FILE.read_text()).get("store", {})
        # F788: the full-coverage lead-PARAGRAPH abstract store (richer answers; "tell me about / explain X")
        self.abstracts = {}
        if ABSTRACT_FILE.exists():
            self.abstracts = json.loads(ABSTRACT_FILE.read_text()).get("store", {})
        # F791/F792: the spectral-clumped tome-tree(s) for navigation. Layered: the FRESH windowed-co-occurrence tree
        # (clean, common-word core) wins; the assoc tree (fuller 90k, noisier) fills the gaps. word_tome: word→(tree,tome).
        self.nav_trees, self.word_tome = [], {}
        for src in (TOME_TREE_FILE, TOME_TREE_FALLBACK):
            if not src.exists():
                continue
            tt = json.loads(src.read_text())
            ti = len(self.nav_trees)
            tree = {"tomes": tt.get("tomes", []), "paths": tt.get("paths", []),
                    "web": {int(k): v for k, v in tt.get("web", {}).items()},
                    "src": tt.get("source", src.stem)}
            self.nav_trees.append(tree)
            for tome_id, ws in enumerate(tree["tomes"]):
                for w in ws:
                    self.word_tome.setdefault(w, (ti, tome_id))   # first tree (fresh) wins

    def _build_surface(self):
        """The LM surface: ONE co-occurrence graph (Class L) over every kernel Siona holds — nothing excluded."""
        self.keys, docs = [], []
        for (kernel, key), txt in self._text.items():
            tag = ERA_ALIASES.get(kernel, kernel.replace("_", " ").replace("-", " "))
            docs.append(T.tokenize(f"{tag} {key} {txt}"))    # doc = kernel/era tag + key + content (routing emerges)
            self.keys.append((kernel, key))
        self.vocab = sorted({t for d in docs for t in d})
        self.vix = {t: i for i, t in enumerate(self.vocab)}
        n, edges, weights = T.cooccurrence_edges(docs, window=4, vocab=self.vocab)
        self.A = dense_adjacency(n, edges, weights)           # term×term co-occurrence = the navigable surface
        self.df, self.sec = [0] * n, []
        for d in docs:
            st = {self.vix[t] for t in d}
            self.sec.append(st)
            for i in st:
                self.df[i] += 1
        self.ndocs = len(docs)
        self.maint = [bool(MAINTENANCE_RE.search(self._text[k])) for k in self.keys]   # demote maintenance prose

    def _idf(self, i):                                        # rarer term = sharper landmark (Class-N corpus ratio)
        return self.ndocs / (1.0 + self.df[i])

    @staticmethod
    def _modern_pref(kernel):                                # tie-break dict era toward modern absent an era signal
        return 1 if kernel == "dict-en-2026" else (0 if kernel == "dict-en-1600" else 0.5)

    def introspect(self):
        # the genome STRAND (chromosomes actually IN turns.bin — Siona's persistent self) ...
        cat = [(c["label"], c["leaf_count"]) for c in g.genome_catalog(self.path, the_one=ONE)["chromosomes"]]
        # ... vs the wiki SIDE-STORES (external knowledge loaded alongside, NOT baked into the genome — labelled
        # honestly so they don't read as chromosomes; F759.1). They are the exact-retrieval tier; the genome carries self.
        if getattr(self, "glosses", None):
            cat.append(("wiki·definition [side-store]", len(self.glosses)))
        if getattr(self, "abstracts", None):
            cat.append(("wiki·abstract-full [side-store]", len(self.abstracts)))   # F788: ≤3-sentence, full coverage
        if getattr(self, "wiki", None):
            cat.append(("wiki·abstract [side-store]", len(self.wiki)))
        if getattr(self, "assoc", None):
            cat.append(("wiki·assoc [side-store]", len(self.assoc)))
        if getattr(self, "relations", None):
            cat.append(("wiki·relations [side-store]", len(self.relations)))
        return cat

    @staticmethod
    def _norm(w):                                             # crude singular fold so 'dragons' matches 'dragon'
        return w[:-1] if w.endswith("s") and len(w) > 3 else w

    @staticmethod
    def _intent(pl):                                          # the FRAME channel: question TYPE from function-word OPERATORS
        if CONTENTS_RE.search(pl):                            # F800 (the srmech way): a declared OPERATOR cue maps to its
            return "contents"                                # intent OPERAND label — so "what's in X" reads 'contents' and
        if USES_RE.search(pl):                                # "what can X be used for" reads 'uses', not the fallback 'phrase'.
            return "uses"                                     # (operators-declared; the cue REGEX is the operator, the label its operand)
        for name, rx in INTENT_RE:
            if rx.search(pl):
                return name
        return "phrase"                                      # no question frame -> a phrase / word-list

    def _depth(self, pl):
        """The answer-DEPTH meta-signal, TWO tiers (F119/F529 shape): (1) F763 crisp KEYWORD anchors (fast, phrase-aware
        — 'tell me more', 'in detail'); (2) F766 MEANING anchor — any prompt word in the intent DICTIONARY is scored by
        DEFINITION-OVERLAP to the long/short anchors, so a synonym we never hand-listed ('exhaustive'/'succinct')
        self-classifies by MEANING, with a frame-channel NEGATION flip ('not brief'→long). Returns (depth, how) so the
        path is legible. Runs on the UNDERSTOOD form (Pass 2, F765) — meaning, not the raw surface."""
        for name, rx in ELABORATION_RE:                       # (1) keyword fast-path — crisp + phrase-aware
            mt = rx.search(pl)
            if mt:
                pre = re.findall(r"[a-z']+", pl[:mt.start()])[-3:]
                if any(t in NEGATORS for t in pre):           # frame-channel polarity flip ('do not be brief'→long)
                    return ("long" if name == "short" else "short"), "keyword(neg)"
                return name, "keyword"
        long_a, short_a = self._depth_anchors()               # (2) meaning anchor (definitions, not a keyword list)
        if long_a is None:
            return "normal", ""
        toks = re.findall(r"[a-z']+", pl)
        long_best = short_best = 0.0
        long_word = short_word = None
        for i, w in enumerate(toks):
            mv = self._word_meaning(w)
            if mv is None:
                continue
            ls = hdc.klein4_similarity(mv, long_a)
            ss = hdc.klein4_similarity(mv, short_a)
            if any(t in NEGATORS for t in toks[max(0, i - 3):i]):     # frame-channel polarity flip ('not detailed'→short)
                ls, ss = ss, ls
            if ls - ss >= DEPTH_MARGIN and ls > long_best:
                long_best, long_word = ls, w
            elif ss - ls >= DEPTH_MARGIN and ss > short_best:
                short_best, short_word = ss, w
        if long_best > short_best:
            return "long", f"meaning:{long_word}"
        if short_best > long_best:
            return "short", f"meaning:{short_word}"
        return "normal", ""

    def _def_bundle(self, words):
        """Class-M bundle of the content-word leaves across the given intent words' DEFINITIONS — definition-overlap in
        HV space = shared content words = MEANING similarity (uses _leaf per content word, NOT the glyph _word_hv: this
        is meaning, not form). Built with the rc155 streaming klein4_bundle_accumulate."""
        acc = None
        for w in words:
            for t in re.findall(r"[a-z]+", INTENT_DICT.get(w, "")):
                if t not in ROUTING_STOPLIST and len(t) >= 3:
                    acc = hdc.klein4_bundle_accumulate(acc, _leaf(t))
        return hdc.klein4_bundle_resolve(acc) if acc is not None else None

    def _depth_anchors(self):
        """F766: build the (long, short) depth anchors ONCE from the SEED definitions; every other dict entry then
        self-classifies by overlap to these (so the dictionary grows by meaning, not by hand-tagged polarity)."""
        if self._danchors is None:
            self._danchors = (self._def_bundle(LONG_SEEDS), self._def_bundle(SHORT_SEEDS))
        return self._danchors

    def _word_meaning(self, w):                               # F766: an intent word's meaning HV = its definition bundle
        return self._def_bundle([w]) if w in INTENT_DICT else None

    def _recognized(self, t):                                # does this content word have a home in any kernel?
        return (t in self.vix) or (self._norm(t) in self.wiki_idx) or (t in self.assoc) or \
               (self._norm(t) in self.assoc) or \
               any(t == k or t.startswith(k) or k.startswith(t) for k in self.learned)

    def _routable(self, t):
        """F765: does this token resolve to an ANSWER tier AS-IS (deep-kernel / gloss / relation / assoc, lemma-folded)?
        Distinct from _recognized, which also counts the loose wiki_idx abstract index — so _recognized can be True for
        a token that still routes NOWHERE (e.g. 'volcanoe' matches wiki_idx but is no gloss/relation/assoc key, and
        would dead-end). Pass-1 comprehension (etak FIND) runs on the NOT-routable tokens, so a variant gets understood
        into its canonical form and reaches the meaning tiers."""
        lt = self._lemma(t)
        return (t in self.vix or t in self.glosses or lt in self.glosses
                or lt in self.relations or lt in self.assoc or t in self.assoc)

    def _assoc_related(self, word, steer=(), k=8):
        """The UNCAPPED relational tier: word -> its co-occurrence neighbours (F754), re-ranked toward the input-ride
        STEER (neighbours shared with the relation come first) — the input-ride walking the association graph (F753)."""
        nbrs = self.assoc.get(word) or self.assoc.get(self._norm(word)) or []
        if not nbrs:
            return []
        shared = set()
        for s in steer:                                      # input-ride steer: 2-hop — boost neighbours the relation also has
            shared |= set(self.assoc.get(s, ())) | set(self.assoc.get(self._norm(s), ()))
        if shared:
            nbrs = sorted(nbrs, key=lambda n: n not in shared)   # stable: steer-shared neighbours first
        return nbrs[:k]

    def _lemma(self, w):
        """Prefer the SINGULAR form if a store holds it (tomatoes→tomato, dishes→dish) — kills the plural sense-split
        (plural 'tomatoes' co-occurs with the Rotten-Tomatoes review site; singular 'tomato' with the food)."""
        cands = ([w[:-2]] if w.endswith("es") and len(w) > 4 else []) + ([w[:-1]] if w.endswith("s") and len(w) > 3 else [])
        for c in cands:
            if c in self.relations or c in self.assoc:
                return c
        return w

    def _directed_relations(self, word, steer=(), ctx_bundle=None, k=6):
        """The DIRECTED + TYPED tier (F757): subject -> its strongest directed out-edges [[object, count, relation], …].
        Input-ride (F753): a steer word matching a relation label surfaces those edges first. F759: the running-context
        RBS-HDC bundle (Klein-4, built via the rc155 `klein4_bundle_accumulate`) re-ranks objects toward the conversation."""
        edges = self.relations.get(word) or self.relations.get(self._norm(word)) or []
        if not edges:
            return []
        st = set(steer) | {self._norm(s) for s in steer}
        csim = {o: hdc.klein4_similarity(ctx_bundle, _leaf(o)) for o, _c, _r in edges} if ctx_bundle is not None else {}
        edges = sorted(edges, key=lambda e: (e[2] not in st if st else True, -csim.get(e[0], 0.0)))
        return edges[:k]

    def _relation_walk(self, subject, steer=(), ctx_bundle=None, anchor=(), steps=4):
        """ETAK-WALK the directed RELATION graph (F759 story-builder), STEER-GATED to stop drift (F760): each hop may
        only step to a node within the SUBJECT's own neighbourhood ∪ the running context (`anchor`). Without the gate
        the walk wandered off-topic (tomato → sauce → made → debut → album); the gate keeps it subject-coherent.
        Returns (path, first-hop edges)."""
        first = self._directed_relations(subject, steer, ctx_bundle)
        allowed = {o for o, _c, _r in first} | set(self.assoc.get(subject, ()) or self.assoc.get(self._norm(subject), ())) | set(anchor)
        path, cur, seen = [subject], subject, {subject}
        for _ in range(steps):
            nxt = next((o for o, _c, _r in self._directed_relations(cur, steer, ctx_bundle)
                        if o not in seen and o in allowed), None)            # GATE: stay in the subject's topic/context
            if not nxt:
                break
            path.append(nxt); seen.add(nxt); cur = nxt
        return path, first

    def _relate_topics(self, a, b, k=10):
        """F774 DERIVE (closed op): the commonality of two topics = the INTERSECTION of their held relation +
        co-occurrence neighbour-sets. A determinate set-op over RETRIEVED facts — attestable, never invented (so the
        coherence is a RESULT of solving, not forced; F775). Ranks shared nodes that are in BOTH relation tiers first,
        then mixed, then assoc-only. Returns the shared neighbours (≤k)."""
        def nbrs(w):
            rel = {o for o, _c, _r in (self.relations.get(w) or self.relations.get(self._norm(w)) or [])}
            asc = set(self.assoc.get(w) or self.assoc.get(self._norm(w)) or [])
            return rel, asc
        ra, aa = nbrs(a)
        rb, ab = nbrs(b)
        shared = (ra | aa) & (rb | ab)
        shared.discard(a); shared.discard(b)
        return sorted(shared, key=lambda s: (not (s in ra and s in rb), s not in (ra | rb)))[:k]

    def _resolve_entity(self, topics, want_abstract):
        """F790: a multi-word ENTITY = adjacent topics named TOGETHER (as a phrase) in ONE subject's gloss/abstract
        (e.g. the binomial "solanum lycopersicum" appears verbatim in tomato's lead). Resolve to that subject + serve
        its definition/abstract instead of the ≥2-topic phrase-decline. Returns (subject, body, src) or None.
        Candidates = the topics + their gloss/abstract-having co-occurrence neighbours (cheap — not all 216k)."""
        phrase = " ".join(topics)
        cands, seen = [], set()
        for t in topics:
            if t in self.glosses or t in self.abstracts:
                cands.append(t)
            for nb in (self.assoc.get(t) or self.assoc.get(self._norm(t)) or [])[:25]:
                if nb in self.glosses or nb in self.abstracts:
                    cands.append(nb)
        for s in cands:
            if s in seen:
                continue
            seen.add(s)
            text = (self.abstracts.get(s) or self.glosses.get(s) or "").lower()
            if phrase in text:                       # the queried tokens appear AS A PHRASE in this subject's definition
                if want_abstract and s in self.abstracts:
                    return s, self.abstracts[s], "lead abstract (≤3 sentences)"
                return s, self.glosses.get(s) or self.abstracts[s], "lead sentence"
        return None

    def _navigate(self, subj):
        """F791/F792: etak-navigate the layered tome-tree(s). FIND the subject's leaf tome (fresh tree preferred, assoc
        fallback) → RIDE (its clump) → ZOOM (parent = sibling tomes sharing path[:-1]) → WEB-HOP (strongest cut-edge
        bridge). Returns (tome, ride, parent, hops, tree, src) or None if the subject isn't in any clumped vocab."""
        loc = self.word_tome.get(subj) or self.word_tome.get(self._norm(subj))
        if loc is None:
            return None
        ti, t = loc
        tree = self.nav_trees[ti]
        tomes, paths, web = tree["tomes"], tree["paths"], tree["web"]
        ride = [w for w in tomes[t] if w != subj][:10]
        pre = paths[t][:-1] if paths[t] else ""
        parent, seen = [], set()
        for i, p in enumerate(paths):
            if i != t and p.startswith(pre):
                for w in tomes[i]:
                    if w not in seen:
                        seen.add(w); parent.append(w)
        return t, ride, parent[:10], web.get(t, []), tree, tree["src"]

    @staticmethod
    def _relation_story(subject, edges):
        """Compose the directed edges into a sentence (reads as an answer, not a bare neighbour list)."""
        adj = [o for o, _c, r in edges if r == "→"]
        framed = [f"{r} {o}" for o, _c, r in edges if r != "→"]
        bits = (["relates to " + ", ".join(adj)] if adj else []) + (["; ".join(framed)] if framed else [])
        return (f"{subject.capitalize()} — " + "; ".join(bits) + ".") if bits else f"{subject.capitalize()}."

    def _abstract_resolve(self, word, floor=0.45):
        """INFERENCE THROUGH THE ABSTRACT LAYER (F762): an unknown SURFACE token is encoded to the ni-Vanuatu glyph
        base (_word_hv) and matched to the nearest KNOWN word by Klein-4 similarity IN THE ABSTRACT GLYPH SPACE — so a
        misspelling / inflection / other-language form resolves to the same abstract content (R-RBS-LM-25/54 realized).
        Bounded by a 2-glyph prefix bucket so the scan stays cheap."""
        if len(word) < 3:
            return None
        wv = _word_hv(word)
        cands = [c for c in self.glosses if len(c) >= 3 and c[:2] == word[:2]] or \
                [c for c in self.relations if len(c) >= 3 and c[:2] == word[:2]]
        best, bs = None, floor
        for c in cands[:2500]:
            sm = hdc.klein4_similarity(wv, _word_hv(c))
            if sm > bs and c != word:
                bs, best = sm, c
        return (best, bs) if best else None

    def _understand(self, unknown, context_words=()):
        """PASS 1 — UNDERSTAND the input into English (etak FIND; F765/F769). Comprehend each UNRECOGNIZED content token
        into its canonical form via an AUTHORITY hierarchy (F769) — biology-faithful TRANSCRIPTION, kept SEPARATE from
        Pass-2 TRANSLATION. Returns {surface: (canonical, how)}; unresolved tokens absent. Runs FIRST so the meaning
        tiers ride on the understood form."""
        out = {}
        for w in unknown:
            r = self._resolve_canonical(w, context_words)
            if r:
                out[w] = r                           # (canonical, how) — how ∈ {usage, locale, glyph}
        return out

    def _closest(self, w, words, gate):
        """The EDIT-CLOSEST word in `words` to w within `gate` edits (None if none qualifies). The edit-distance RANK
        that fixes the glyph mis-rank (tomatto→tomato edit-1 beats tomatto→tomatillo edit-3)."""
        best, bd = None, gate + 1
        for u in words:
            if u == w:
                continue
            d = self._edit_distance(w, u)
            if d < bd:
                bd, best = d, u
        return best if (best is not None and bd <= gate) else None

    def _resolve_canonical(self, w, context_words=()):
        """F769/F771 — resolve a typo/variant by a DECLARED ORDERED AUTHORITY CHAIN, not hardcoded branches (F770:
        declare the structure). The order IS the language's abstraction stack read MOST-SPECIFIC-FIRST (F771): USAGE
        (this conversation — the user's own words) > LOCALE (language-specific convention) > GLYPH (the ni-Vanuatu
        UNIVERSAL base, lowest BECAUSE most universal). First layer that resolves wins; returns (canonical, how).
        Extensible: insert a layer in AUTHORITY_CHAIN (e.g. a future per-user DIALECT layer between usage and locale)."""
        if len(w) < 3:
            return None
        gate = max(2, len(w) // 3)
        AUTHORITY_CHAIN = (                                   # specific → universal; declared, ordered, extensible
            ("usage",  lambda: self._usage_resolve(w, context_words, gate)),   # the user's own context/learned spelling
            ("locale", lambda: self._locale_resolve(w, gate)),                 # en_GB/en_US convention (dormant on both-spelling corpora, F769)
            ("glyph",  lambda: self._glyph_resolve(w, gate)),                  # the universal ni-Vanuatu base — last resort
        )
        for name, attempt in AUTHORITY_CHAIN:
            cand = attempt()
            if cand:
                return (cand, name)
        return None

    def _usage_resolve(self, w, context_words, gate):
        """USAGE layer (F769, highest): the user's OWN established spelling — a word from the running context or the
        learned store, edit-close + routable. 'Localities are not the authority when the user's input suggests another.'"""
        usage = [u for u in (set(context_words) | set(self.learned)) if self._routable(u)]
        return self._closest(w, usage, gate)

    def _locale_resolve(self, w, gate):
        """LOCALE layer (F769): a known en_GB/en_US spelling-convention variant -> the store-canonical, edit-close."""
        loc = LOCALE_CANON.get(w)
        return loc if (loc and self._routable(loc) and self._edit_distance(w, loc) <= gate) else None

    def _glyph_resolve(self, w, gate, floor=0.45):
        """GLYPH layer (F769/F771, LOWEST — the ni-Vanuatu universal base): edit-CLOSEST among the glyph-PLAUSIBLE
        candidates (not the glyph-top, which mis-ranks tomatto→tomatillo, F767), edit-gated (no hallucinated comprehension)."""
        wv = _word_hv(w)
        cands = [c for c in self.glosses if len(c) >= 3 and c[:2] == w[:2]] or \
                [c for c in self.relations if len(c) >= 3 and c[:2] == w[:2]]
        plausible = [c for c in cands[:2500] if c != w and hdc.klein4_similarity(wv, _word_hv(c)) >= floor]
        return self._closest(w, plausible, gate)

    @staticmethod
    def _edit_distance(a, b):
        """Levenshtein distance (cheap for short tokens; no abs()). Gates Pass-1 comprehension to typos/variants only."""
        if a == b:
            return 0
        prev = list(range(len(b) + 1))
        for i, ca in enumerate(a, 1):
            cur = [i]
            for j, cb in enumerate(b, 1):
                cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (0 if ca == cb else 1)))
            prev = cur
        return prev[-1]

    @staticmethod
    def _fmt_rel(edges):                                      # render directed-typed out-edges: "rel→obj" or "→obj"
        return ", ".join(f"{r}→{o}" if r != "→" else f"→{o}" for o, _c, r in edges)

    def wiki_lookup(self, prompt, steer=()):
        """Scalable broad-knowledge lookup over the WIKI side-store: query terms -> article via the term-index,
        scored title-overlap×3 + text-overlap + STEER-overlap (F753: the relation/frame words bias which article)."""
        q = {self._norm(w) for w in T.tokenize(prompt) if w not in ROUTING_STOPLIST}   # F751: no delexical routing
        if not q or not self.wiki:
            return None
        st = {self._norm(w) for w in steer}                   # F753: the relation/frame steer (delexical OK here)
        cand = set().union(*(self.wiki_idx.get(t, set()) for t in q)) if q else set()
        best, best_sc = None, 0
        for k in cand:
            tt, xt = self.wiki_toks[k]
            sc = 3 * len(q & tt) + len(q & xt) + STEER_WEIGHT * len(st & xt)   # steer nudges, doesn't route
            if sc > best_sc:
                best_sc, best = sc, k
        return best if best_sc >= 3 else None                 # require a real title/term hit, not one stray word

    def _walk(self, landmarks, steps=WALK_STEPS, steer=()):
        """FORWARD-ETAK: walk the co-occurrence graph from `landmarks` (IDF-gated, no-revisit; the landmarks held
        in-frame), then rank sections by landmark + walk + STEER overlap (F753: the input-ride's relation/frame words
        bias convergence — the frame as a direction of travel). Returns (walk_path_terms, ranked_[(kernel,key)]) or
        None if `landmarks` is empty."""
        landmarks = list(dict.fromkeys(landmarks))
        if not landmarks:
            return None
        steerset = set(steer)
        lmset = set(landmarks)                                # convergence anchor (×LANDMARK_WEIGHT) = the SUBJECT only
        seed = list(dict.fromkeys(list(landmarks) + [i for i in steer if i not in lmset]))  # F753: walk FROM subject+relation
        visited, path = set(seed), list(seed)                 # the steer DIRECTS travel (toward the relation), not just scores
        anchor, last = list(seed), seed[-1]                   # etak: the frame (subject+steer) stays; islands move past
        for _ in range(steps):
            nbr = {}
            for i in dict.fromkeys(anchor + [last]):
                for j, wt in enumerate(self.A[i].tolist()):   # proximity gate = the co-occurrence row
                    if wt and j not in visited:
                        nbr[j] = nbr.get(j, 0.0) + wt * self._idf(j)
            if not nbr:
                break
            nxt = max(nbr, key=nbr.get)
            path.append(nxt); visited.add(nxt); last = nxt
        walk = set(path)
        ranked = []
        for idx, (kernel, key) in enumerate(self.keys):
            score = (sum(self._idf(t) for t in (self.sec[idx] & lmset)) * LANDMARK_WEIGHT     # the query frame (route)
                     + sum(self._idf(t) for t in (self.sec[idx] & walk))                      # walked context
                     + sum(self._idf(t) for t in (self.sec[idx] & steerset)) * STEER_WEIGHT)  # F753: relation steer
            if self.maint[idx]:
                score *= MAINT_PENALTY                        # maintenance prose is not a good answer landing
            if score > 0:
                ranked.append((score, self._modern_pref(kernel), idx))
        ranked.sort(reverse=True)
        return [self.vocab[t] for t in path], [self.keys[i] for _, _, i in ranked]

    def etak_walk(self, prompt, steps=WALK_STEPS):
        """INVERSE-ETAK: locate the input's tokens on the surface, then forward-walk from them."""
        return self._walk([self.vix[t] for t in T.tokenize(prompt)
                           if t in self.vix and t not in ROUTING_STOPLIST], steps)

    # --- write-mode: the learning loop (ask -> accept -> temp -> commit-to-kernel) -----------------------------
    @staticmethod
    def _parse_teach(body):
        """'dragon is a mythical creature' / 'dragon = …' / 'dragon: …' -> (term, definition)."""
        for sep in (" = ", ": ", " is ", " are ", " means "):
            low = body.lower()
            if sep in low:
                i = low.index(sep)
                term = re.sub(r"^(a|an|the)\s+", "", body[:i].strip().strip('“”"\'')).lower()[:40]
                return term, body[i + len(sep):].strip()
        return None, None

    def _committed_terms(self):
        if LEARNED_KERNEL_FILE.exists():
            try:
                return set(json.loads(LEARNED_KERNEL_FILE.read_text() or "{}"))
            except ValueError:
                return set()
        return set()

    def learn(self, term, text):
        """Accept an answer into TEMPORARY memory (gitignored, this-session). Answers immediately; not yet a kernel."""
        term = term.strip().lower()[:40]
        self.learned[term] = text.strip()
        tmp = json.loads(self._temp_file.read_text() or "{}") if self._temp_file.exists() else {}
        tmp[term] = text.strip()
        self._temp_file.write_text(json.dumps(tmp, indent=2))
        return term

    def _resolve_learned(self, term):
        """Find the actual learned key for a user term — exact, else loose (plural/prefix), like learned-lookup."""
        term = re.sub(r"^(a|an|the)\s+", "", term.strip().strip('“”"\'')).lower()
        if term in self.learned:
            return term
        if len(term) >= 3:
            return next((t for t in self.learned if t.startswith(term) or term.startswith(t)), None)
        return None

    def commit_kernel(self, term):
        """Promote a temp item into the COMMITTED learned kernel (git-trackable; a real gene on next genome bake)."""
        term = self._resolve_learned(term)
        if term is None:
            return None
        kern = json.loads(LEARNED_KERNEL_FILE.read_text() or "{}") if LEARNED_KERNEL_FILE.exists() else {}
        kern[term] = self.learned[term]
        LEARNED_KERNEL_FILE.write_text(json.dumps(kern, indent=2, ensure_ascii=False))
        if self._temp_file.exists():                          # it has graduated out of temp
            tmp = json.loads(self._temp_file.read_text() or "{}")
            tmp.pop(term, None)
            self._temp_file.write_text(json.dumps(tmp, indent=2))
        return term

    def _structure_card(self):
        """Siona's self-knowledge, built the srmech way — a DECLARED operator-template (the connective FRAME = form,
        F654 / operators-declared-operands-by-meaning) filled with SOURCED operands (the FACTS, read from
        srmech.describe() + genome_catalog at runtime — F743, never a baked self-blurb). Every content OPERAND is
        grounded in the ni-Vanuatu glyph base (_word_hv = byte→glyph, the universal base F613/F761), and the
        self-description is CONTENT-ADDRESSED over that glyph signature (sha256 = Class A) — so the card is sourced as
        RBS-LM glyph + attestable, NOT free English. (F800. The deeper 'walk my own prose to find myself' seed was
        tested and is NOISE — self-terms are rare, IDF drags the walk into citation metadata; F743.)"""
        d = srmech.describe()
        doc1 = (srmech.__doc__ or "").strip().split(".")[0].strip()          # srmech's OWN one-line self-description (sourced)
        catalog = self.introspect()                                          # (label, leaf_count) per chromosome (sourced)
        ops, cats, ver = d["tools"]["total"], len(d["categories"]), d["srmech_version"]
        held = "; ".join(f"{lab} ({n})" for lab, n in catalog)
        # the OPERANDS = the content words of the self-description; each grounded in the ni-Vanuatu glyph base, then the
        # whole bundle CONTENT-ADDRESSED (Class A) — the self-description is sourced AS glyph, not asserted as English.
        operands = [SIONA_NAME, "srmech"] + re.findall(r"[a-z]+", doc1.lower()) + [lab for lab, _ in catalog]
        glyph_sig = hdc.klein4_bundle(*[_word_hv(w) for w in operands])      # operands -> ni-Vanuatu glyph base, bundled (Class M)
        addr = sha256_raw(bytes(bytearray(int(x) & 255 for x in glyph_sig))).hex()[:12]   # Class-A content-address of the glyph signature
        return (f"[identity] I am {SIONA_NAME} — the running, genome-backed instance of {doc1}. srmech is my "
                f"substrate; {SIONA_NAME} is me running it — the same system, named at two levels (srmech = the "
                f"mechanism/package; {SIONA_NAME} = this instance reading its genome).\n"
                f"[srmech.describe()] My substrate is {ops} stored-relationship ops across {cats} categories "
                f"(srmech {ver}).\n"
                f"[genome_catalog] The kernels I hold — and so what I can answer from — are: {held}. Ask me about "
                "any of these (or give me a word to define), or teach me something new (“remember <term> is …”); "
                "I etak-walk what I hold to compose an answer, and I ask when your question touches nothing I have.\n"
                f"[glyph-sourced] {len(operands)} content operands grounded in the ni-Vanuatu glyph base (byte→glyph, "
                f"F613); self-description content-address {addr} (Class A). The frame is declared operators (form); the "
                f"facts are sourced operands — describe() + genome_catalog, glyph-grounded, not free English.")

    def _prev_topic(self, prev_assistant, context):
        """F798: the PRIOR turn's subject, for anaphora carry-forward ("what can IT be used for" → the last topic).
        Prefer the prior answer's input-ride parse line ('topic [...]'); then its '[siona · TIER] subject:' head; then
        the earliest prior content word that still has a kernel home. Returns a lemma'd token or None."""
        src = prev_assistant or ""
        m = re.search(r"topic\s*\[\s*'([^']+)'", src) or re.search(r"\]\s*([a-z][a-z0-9 ]*?):\s", src)
        if m:
            cand = self._lemma(m.group(1).strip().split()[-1].lower())
            if self._recognized(cand):
                return cand
        for t in re.findall(r"[a-z]+", self._context_content(context).lower()):   # F799: scaffolding stripped, not a framing word
            if t not in ROUTING_STOPLIST and len(t) >= 3:
                lt = self._lemma(t)
                if self._recognized(lt):
                    return lt
        return None

    def _context_content(self, context):
        """F799: the running context must reflect the CONVERSATION's content, NOT Siona's own rendering scaffolding.
        Her prior answers are fed back verbatim, so strip her framing first: every [bracketed] segment (parse-lines +
        tags: [input-ride …], [siona · …], [etak: …], [anaphora: …], notebook §-refs) and her citation/honest-note
        parentheticals ((source: …, CC-BY-SA), (related: …)). A content parenthetical like (Solanum lycopersicum)
        has no scaffold marker, so it survives. The remaining prose + the user's words are the real content."""
        s = context or ""
        for _ in range(6):                                       # collapse NESTED brackets innermost-first: the parse line is
            s2 = re.sub(r"\[[^\[\]]*\]", " ", s)                 # [input-ride: … topic ['x'] · steer ['y']] — strip ['x']/['y']
            if s2 == s:                                          # then the now-flat outer bracket, else "· steer ·" leaks through
                break
            s = s2
        s = SCAFFOLD_PAREN_RE.sub(" ", s)                        # drop citation / honest-note parentheticals (keep (Solanum …))
        return s

    def _provenance_card(self):
        """F799: a self-PROVENANCE question ("where is your source code / are you open source"). Honest + grounded:
        her source IS the srmech package she runs on (name + version, read from describe()); she's an open research
        package, not a hidden model; but she does NOT hold a repository URL as an attested fact, so she won't
        fabricate one (no-hallucination; F743 no baked-in self-answers — read from structure, point at what she IS)."""
        d = srmech.describe()
        doc1 = (srmech.__doc__ or "").strip().split(".")[0].strip()
        return (f"[siona · provenance] My source IS the srmech package — {doc1} (srmech {d['srmech_version']}). I'm an "
                f"open research package, not a hidden model: the mechanism I run on is the package itself, locatable "
                f"by its name, “srmech” ({d['tools']['total']} stored-relationship ops across {len(d['categories'])} "
                f"categories). I hold my package identity + version — but I do NOT hold a specific repository URL as an "
                f"attested fact, so I won't fabricate one; look up the “srmech” package to find the code.")

    def infer(self, prompt, prev_assistant="", context=""):
        p = prompt.strip()
        pl = p.lower()
        toks = set(re.findall(r"[a-z0-9]+", pl))

        # === WRITE-MODE: the learning loop (teach -> temp; commit -> kernel; list) =========================
        m = re.match(r"\s*(?:learn|remember|teach)\b[:,]?\s+(?:me\s+)?(?:that\s+)?(.+)", p, re.I | re.S)
        if m:
            term, text = self._parse_teach(m.group(1))
            if term and text:
                self.learn(term, text)
                return (f"[siona · learned (temp)] Got it — “{term}”: {text}\n  Held in TEMPORARY memory "
                        f"(this session, gitignored). Say “commit {term}” to keep it in my kernel.")
            return "[siona] Teach me as:  remember <term> is <definition>   (or  <term> = <definition>)."
        m = re.match(r"\s*(commit|save|keep)\s+(?:to\s+kernel\s+)?(.+?)\s*$", p, re.I)
        if m:
            asked = m.group(2).strip().strip('“”"\'')
            committed = self.commit_kernel(asked)             # loose-resolves singular/plural/prefix
            if committed:
                return (f"[siona · committed] “{committed}” is now in my learned KERNEL (git-trackable; becomes a "
                        f"permanent gene on my next genome bake). It survives restart now, not just this session.")
            if m.group(1).lower() == "commit":
                return f"[siona] Nothing in temporary memory called “{asked}”. Teach me first: remember {asked} is …"
        if ("learned" in toks or "taught" in toks) and (toks & {"what", "show", "list"} or pl in ("learned", "what have you learned")):
            if not self.learned:
                return "[siona] I haven't been taught anything yet. Teach me: remember <term> is <definition>."
            com = self._committed_terms()
            rows = [f"{t} [{'kernel' if t in com else 'temp'}]: {v[:60]}" for t, v in self.learned.items()]
            return "[siona · learned] " + "; ".join(rows)

        # === conversational ACCEPT: a declarative reply to my last asking-state ===========================
        if prev_assistant and "asking-state" in prev_assistant and not p.endswith("?"):
            am = re.search(r'about\s+[“"\'](.+?)[”"\']', prev_assistant)
            if am and len(toks) >= 1:
                term = am.group(1).strip().split()[-1].lower()    # the subject I asked about
                self.learn(term, p)
                return (f"[siona · learned (temp)] Thank you — “{term}”: {p}\n  Held in TEMPORARY memory; say "
                        f"“commit {term}” to keep it in my kernel.")

        # === learned-first lookup (temp + committed; loose prefix match for plurals) ======================
        hit = next((t for t in self.learned
                    if t in pl or any(w == t or w.startswith(t) or t.startswith(w) for w in toks if len(w) >= 3)),
                   None)
        if hit:
            tier = "kernel" if hit in self._committed_terms() else "temp"
            return f"[siona · learned ({tier})] {hit}: {self.learned[hit]}"

        # === F799 self-PROVENANCE: "where is your source code / are you open source" -> answer from her self-knowledge
        # (she IS the srmech package + version), not a notebook etak-walk and not a fabricated URL. Before identity.
        if re.search(r"\b(?:you|your|yourself)\b", pl) and PROVENANCE_RE.search(pl):
            return self._provenance_card()
        # === identity: Siona == srmech ====================================================================
        if "siona" in pl or re.search(r"\byou\b.*\bsrmech\b|\bsrmech\b.*\byou\b|same thing", pl):
            return self._structure_card()

        # === SENTENCE PARSE (F752): TOPIC channel (content) + FRAME channel (function words = intent) ======
        content = T.tokenize(prompt)
        salient = [t for t in content if t not in ROUTING_STOPLIST and t not in ELABORATION_WORDS
                   and t not in INTENT_DICT and t not in COMPARE_CUES and t not in RELATE_CUES]   # candidate topics (F763/F766/F774: meta+cue words consumed, not routed)
        recognized = [t for t in salient if self._recognized(t)]                 # topics with a kernel home
        unrecognized = [t for t in salient if t not in recognized]
        # === PASS 1 — UNDERSTAND into English (etak FIND, F765; biology's TRANSCRIPTION stage) =============
        # Comprehend the UNRECOGNIZED surface tokens into canonical English FIRST, as a distinct action, BEFORE any
        # meaning is derived (Pass 2 = TRANSLATION). So a misspelling/variant ("tomatto") becomes "tomato" up front and
        # the full meaning machinery (gloss + relations + depth) rides on the understood form — not just the last fallback.
        unroutable = [t for t in salient if not self._routable(t)]                    # F765: comprehend tokens that route to NO
        ctx_words = set(re.findall(r"[a-z]+", self._context_content(context).lower()))  # F769/F799: observed usage, Siona's scaffolding stripped
        understood = self._understand(unroutable, ctx_words)                           # answer tier (not merely _recognized-False)
        if understood:
            salient = [understood[t][0] if t in understood else t for t in salient]   # re-render in canonical English
            recognized = [t for t in salient if self._recognized(t)]                  # re-derive on the UNDERSTOOD tokens
            unrecognized = [t for t in salient if t not in recognized]
        understood_note = (("[understood: " + ", ".join(f"{s}→{c} ({how})"            # F769: how ∈ usage/locale/glyph
                            for s, (c, how) in understood.items()) + "]\n") if understood else "")
        # === F798 ANAPHORA carry-forward: a follow-up whose only subject is a pronoun ("what can IT be used for") has
        # empty salient and used to misroute to the identity card. Inherit the PRIOR turn's topic (server threads it as
        # prev_assistant + context). Conservative: only when THIS turn names no recognized topic of its own.
        anaphora_note = ""
        if not recognized and ANAPHORA_RE.search(pl):
            prior = self._prev_topic(prev_assistant, context)
            if prior:
                salient = [prior] + [t for t in salient if self._lemma(t) != prior]
                recognized = [prior]
                anaphora_note = f"[anaphora: {ANAPHORA_RE.search(pl).group(0)} → {prior}]\n"
        intent = self._intent(pl)                                               # the question TYPE (frame channel)
        depth, depth_how = self._depth(pl)                                      # F763/F766: DEPTH (keyword fast-path OR meaning anchor)
        k_rel, k_assoc, walk_steps, attach_extra = {                            # depth -> answer-shaping knobs (comprehend, not discard)
            "short":  (3, 4, 2, False),                                         # trim to the core; suppress the trailing related-notes
            "normal": (6, 8, 4, True),                                          # the standard answer (current behaviour)
            "long":   (12, 12, 6, True),                                        # deepen: more edges, longer walk, attach BOTH rel+assoc
        }[depth]
        # F753 steer = relation/frame words from the RAW prompt (T.tokenize strips function words, so the topic channel
        # never sees "from"/"than"; the steer channel must read raw). A steer word is in the deep-kernel vocab OR a known
        # relation label (F757, so "from"/"than" flip the directed tier even though they aren't deep-kernel tokens).
        raw = re.findall(r"[a-z]+", prompt.lower())
        steer_terms = [t for t in raw if t not in salient and t not in ELABORATION_WORDS and t not in INTENT_DICT  # F763/F766: meta-words fully consumed

                       and (t in self.vix or t in self.rel_labels)]
        steer_idx = [self.vix[t] for t in steer_terms if t in self.vix]           # kernel-walk seeds need a vix index
        # F759 running-context: content words from PRIOR turns -> a Klein-4 RBS-HDC context bundle (built with the rc155
        # streaming klein4_bundle_accumulate) + a context steer. Biases the answer toward the conversation; makes the
        # SAME query differ once context accrues. The context object IS the running conversation, folded holographically.
        ctx_terms = [t for t in dict.fromkeys(re.findall(r"[a-z]+", self._context_content(context).lower()))
                     if t not in ROUTING_STOPLIST and len(t) >= 3                          # F799: strip Siona's own scaffolding first —
                     and (t in self.relations or t in self.assoc or t in self.vix)][:12]   # context = CONVERSATION content, not framing
        ctx_bundle = None
        for t in ctx_terms:
            ctx_bundle = hdc.klein4_bundle_accumulate(ctx_bundle, _leaf(t))
        ctx_bundle = hdc.klein4_bundle_resolve(ctx_bundle) if ctx_bundle is not None else None
        self._ctx = ctx_terms                                                    # the running-context object (introspectable)
        eff_steer = steer_terms + [t for t in ctx_terms if t not in steer_terms]  # context nudges the input-ride
        parse = (anaphora_note + understood_note                                # F798 anaphora + F765 PASS 1 (understand) above PASS 2 (ride)
                 + f"[input-ride: {intent} · topic {recognized or '—'}"
                 + (f" · detail {depth} ({depth_how})" if depth != "normal" else "")   # F763/F766: show depth + HOW (keyword vs meaning)
                 + (f" · steer {steer_terms}" if steer_terms else "")
                 + (f" · context {ctx_terms}" if ctx_terms else "") + "]")
        new_note = f"\n  (not on my shelf: {', '.join(unrecognized)})" if unrecognized else ""
        proc_note = ("\n  (you asked HOW it's made/works — I hold what it IS, not the process)"
                     if intent in ("process", "quantity") else "")
        # F788: an open "tell me about / explain X" (or depth=long, "tell me more") wants the fuller ABSTRACT.
        want_abstract = (depth == "long") or bool(ABOUT_RE.search(pl))
        ab_subj = next((self._lemma(t) for t in sorted(salient, key=len, reverse=True)
                        if self._lemma(t) in self.abstracts), None)

        # === F796 RULE-KERNEL frame: a pasted CODE / MATH fragment -> read its A-N structure with our OWN dep-free
        # grammar (Python/C/LaTeX; NO ast/sympy/pycparser). The structural, symbol-invariant read — a closed grammar
        # ENCODED (the chess/LOGO route), not borrowed from a host interpreter.
        if CODE_INPUT_RE.search(prompt) or "|||" in prompt:
            if "|||" in prompt:                                   # F797: compare two fragments by A-N signature
                fa, fb = prompt.split("|||", 1)
                try:
                    s, ca, cb, verdict = RK.compare(fa, fb)
                except Exception:
                    s = None
                if s is not None:
                    return (f"{parse}\n[siona · rule-kernel compare] structural similarity {s:+.3f} → they have {verdict}.\n"
                            f"  (A: {', '.join(ca) or '—'} | B: {', '.join(cb) or '—'} — symbol- AND language-invariant "
                            f"A-N signatures from Siona's own grammars, no interpreter; the algorithm, not the surface — F797)")
            try:
                lang, cls, desc = RK.structural_read(prompt)
            except Exception:
                cls = None
            if cls:
                return (f"{parse}\n[siona · rule-kernel] {desc}.\n"
                        f"  (A-N construct classes: {', '.join(cls)} — parsed by Siona's own {lang} grammar, no "
                        f"ast/sympy/pycparser; a symbol-invariant structural signature, the chess/LOGO route — F795/F796)")

        # === F791 NAVIGATE frame: walk the spectral-clumped tome-tree (FIND→RIDE→ZOOM→WEB-HOP) — the navigable smallwiki.
        if self.word_tome and NAV_RE.search(pl):
            cand = [self._lemma(t) for t in salient if self._lemma(t) in self.word_tome or t in self.word_tome]
            # prefer a REAL subject (has a gloss/relation), then the longer word — not a noise token in the tome vocab
            cand.sort(key=lambda w: (w in self.glosses or w in self.relations, len(w)), reverse=True)
            subj = cand[0] if cand else None
            if subj:
                nav = self._navigate(subj)
                if nav:
                    t, ride, parent, hops, tree, src = nav
                    hopline = ""
                    if hops:
                        o, _wt, ba, bb = hops[0]
                        hopline = (f"\n  WEB-HOP → tome #{o} (bridge {ba}~{bb}): {', '.join(tree['tomes'][o][:8])}")
                    return (f"{parse}\n[siona · navigate] “{subj}” sits in tome #{t} of the spectral-clumped smallwiki "
                            f"({src} source, native §51).\n  RIDE (this clump): {', '.join(ride) or '(alone)'}\n"
                            f"  ZOOM OUT (parent clump): {', '.join(parent) or '(top)'}{hopline}\n"
                            f"  (clumps-of-clumps + cut-edge web over the simplewiki co-occurrence graph, CC-BY-SA){new_note}")

        # === F787 CONTENTS frame: "what else / what's in X (besides Y)" -> LIST the subject's held neighbours, minus Y.
        # A multi-item list (not a single-sentence definition); fires before the 2-topic reasoner so "what else is in
        # ketchup besides tomatoes" lists ketchup's neighbours (vinegar, sauce, …) excluding tomato — instead of the
        # phrase-decline. Honestly framed: held relations + co-occurrence, NOT a verified contents/ingredient list.
        uses_frame = bool(USES_RE.search(pl)) and not CONTENTS_RE.search(pl)  # F798: "what can it be used for/with" = a USES list
        if recognized and (CONTENTS_RE.search(pl) or uses_frame):
            subject = self._lemma(recognized[0])                              # the container/topic (prompt-order first)
            excl = {self._lemma(o) for o in EXCLUDE_RE.findall(pl)}           # named after besides/except/…
            excl |= {self._lemma(t) for t in recognized[1:]}                  # any other named topic excluded too
            excl.add(subject)
            seen, items = set(), []
            for o in self._assoc_related(subject, eff_steer, k=16):           # co-occurrence neighbours (freq-ranked)
                lo = self._lemma(o)
                if lo not in excl and lo not in ROUTING_STOPLIST and len(lo) >= 3 and lo not in seen:
                    seen.add(lo); items.append(o)
            for o, _c, _r in self._directed_relations(subject, eff_steer, ctx_bundle, k=10):  # + typed relation objects
                lo = self._lemma(o)
                if lo not in excl and lo not in ROUTING_STOPLIST and len(lo) >= 3 and lo not in seen:
                    seen.add(lo); items.append(o)
            exwords = ", ".join(sorted(excl - {subject}))
            if uses_frame:                                                    # F798: USES list — "what X is used with"
                if items:
                    return (f"{parse}\n[siona · uses] “{subject}” is used with / appears with: {', '.join(items[:10])}."
                            f"\n  (RELATIONS + co-occurrence neighbours — what “{subject}” appears WITH in simplewiki, "
                            f"NOT a verified list of uses; CC-BY-SA){new_note}")
                return (f"{parse}\n[siona · uses] I hold nothing about what “{subject}” is used with beyond its lead "
                        f"sentence. I won't invent its uses.{new_note}")
            lead = f"Besides {exwords}, what" if exwords else "What"
            if items:
                return (f"{parse}\n[siona · contents] {lead} I hold near “{subject}”: "
                        f"{', '.join(items[:10])}.\n  (these are RELATIONS + co-occurrence neighbours — what “{subject}” "
                        f"appears WITH in simplewiki, NOT a verified contents/ingredient list; CC-BY-SA){new_note}")
            return (f"{parse}\n[siona · contents] {('Besides ' + exwords + ', ') if exwords else ''}I hold nothing"
                    f" more about “{subject}” than its lead sentence. I won't invent its other contents.{new_note}")

        # === REASONER (F774): ≥2 topics + a relational/comparison CUE -> closed-op problem-solving over RETRIEVED facts
        # (more than find+ride). Coherence as a RESULT of solving (F775); no-confabulation (closed ops don't invent,
        # F767); bounded by what's sourced (honest decline, F408). Inference ORCHESTRATES the exact set/compare ops.
        topics = list(dict.fromkeys(self._lemma(t) for t in recognized))
        if len(topics) >= 2:
            a, b = topics[0], topics[1]
            cues = set(re.findall(r"[a-z]+", pl))
            if cues & COMPARE_CUES:                                  # SOLVE-FOR: needs a sourced comparable ATTRIBUTE
                return (f"{parse}\n[siona · reasoned (solve-for)] To compare “{a}” and “{b}” I'd need a stored MEASURE of "
                        f"that attribute for both — I hold relationships, not measured quantities, so I won't invent a "
                        f"comparison.\n  (honest decline: the premise isn't sourced — F408; give me the measures and I can solve it)")
            if cues & RELATE_CUES:                                   # DERIVE: intersect the two topics' held neighbour-sets
                shared = self._relate_topics(a, b)
                if shared:
                    return (f"{parse}\n[siona · reasoned (derive)] “{a}” and “{b}” both relate to: {', '.join(shared)}\n"
                            f"  (derived: the intersection of their held relations + co-occurrence neighbours — what they "
                            f"share in what I hold, not invented; simplewiki, CC-BY-SA){new_note}")
                return (f"{parse}\n[siona · reasoned (derive)] I hold both “{a}” and “{b}” but find NO shared relationship "
                        f"between them in my stores — I won't invent one.{new_note}")
            # F790: multi-word ENTITY (no cue) — is the queried phrase named TOGETHER in one subject's definition?
            # (e.g. "solanum lycopersicum" appears verbatim in tomato's lead -> answer about tomato, not the decline.)
            ent = self._resolve_entity(topics, want_abstract)
            if ent:
                s, body, src = ent
                return (f"{parse}\n[siona · entity] {s}: {body}\n"
                        f"  (“{' '.join(topics)}” is named in {s}'s definition — that's the entity it refers to; "
                        f"source: simplewiki {src}, CC-BY-SA){new_note}")
        # word-salad / ambiguous: a PHRASE (no question frame) naming ≥2 distinct recognized topics, no cue -> ask which
        if intent == "phrase" and len(set(self._norm(t) for t in recognized)) >= 2:
            return (f"{parse}\n[siona] That reads as several things ({', '.join(recognized)}) with no question — "
                    f"which one do you mean, or what about them?{new_note}")

        # === ETAK-WALK the DEEP surface (inference, not retrieval) ========================================
        # F788: an open "tell me about X" whose subject HAS a wiki abstract skips the (terse) deep-kernel walk so the
        # richer abstract wins (e.g. "tell me about computer" -> the wiki abstract, not the dict-en seed "an electronic machine").
        landmarks = [self.vix[t] for t in salient if t in self.vix]
        if landmarks and not (want_abstract and ab_subj):
            trace, ranked = self._walk(landmarks, steer=steer_idx)   # F753: couple the input-ride to the kernel walk
            path_str = " → ".join(trace[:8])
            top_kernel, top_key = ranked[0]
            if top_kernel.startswith("dict-en-"):             # era-resolve the WORD the walk found (F739 disambig)
                era = "dict-en-1600" if ARCHAIC_RE.search(pl) else "dict-en-2026"
                defn = self._text.get((era, top_key), self._text[(top_kernel, top_key)])
                return f"{parse}\n[etak: {path_str}]\n[{era}] {top_key}: {defn}{proc_note}{new_note}"
            body = self._text.get((top_kernel, top_key), top_key)
            see = [f"§{k[:24]}" for kk, k in ranked[1:3] if kk == top_kernel]   # siblings the same walk passed
            tail = f"\n  (the walk also passed: {', '.join(see)})" if see else ""
            return f"{parse}\n[etak: {path_str}]\n[{top_kernel} → §{top_key}] {body}{tail}{proc_note}{new_note}"
        # the real DEFINITION tier (F760): the lead sentence of the simplewiki article = "what X IS". Fires before the
        # relations tiers so a definition question gets a definition, not a relations dump. _lemma folds plural→singular.
        gsub = next((t for t in sorted(salient, key=len, reverse=True)
                     if t in self.glosses or self._lemma(t) in self.glosses), None)
        if gsub:
            gk = gsub if gsub in self.glosses else self._lemma(gsub)
            rel_note = ""
            if attach_extra:                                              # F763: short depth answers with the bare definition
                drel = self._directed_relations(self._lemma(gk), eff_steer, ctx_bundle, k=k_rel)
                bits = [self._fmt_rel(drel)] if drel else []
                if depth == "long":                                       # deepen: attach the assoc neighbours too
                    arel = self._assoc_related(self._lemma(gk), eff_steer, k=k_assoc)
                    if arel:
                        bits.append(", ".join(arel))
                rel_note = f"\n  (related: {'; '.join(bits)})" if bits else ""
            # F788: "what is X" -> the crisp lead sentence; "tell me about/explain X" or depth=long -> the fuller
            # abstract (≤3 sentences). The single-sentence answer was the DEFINITION tier; richer asks get the abstract.
            if want_abstract and gk in self.abstracts:
                body, src = self.abstracts[gk], "simplewiki lead abstract (≤3 sentences)"
            else:
                body, src = self.glosses[gk], "simplewiki lead sentence"
            # F794: "be detailed" is NOT a static sentence-cap — detail opens the viewport's other DEGREES OF FREEDOM.
            # On depth=long, open the SPECTRAL-NEIGHBOURHOOD DOF (the F791/F792 tome-tree) on top of the abstract +
            # relations: detail = abstract(text axis) + relations(relational axis) + clump/web(community axis). The
            # forgotten DOF are the navigation facets, not more sentences on one axis. (NOW-dynamic cross-turn
            # escalation — "still too brief" → open the next DOF — is the follow-on; needs conversation state.)
            dof = ""
            if depth == "long":
                nav = self._navigate(self._lemma(gk))
                if nav:
                    _t, ride, _par, hops, _tr, _s = nav
                    br = f"; bridges to {hops[0][2]}~{hops[0][3]}" if hops else ""
                    if ride:
                        dof = f"\n  (deeper — another facet, its spectral neighbourhood: {', '.join(ride[:8])}{br})"
            return (f"{parse}\n[siona · definition] {gk}: {body}\n"
                    f"  (source: {src}, CC-BY-SA){proc_note}{new_note}{rel_note}{dof}")
        # not in the DEEP kernels or glosses -> the broad WIKI abstract, ENRICHED with relations (directed if held, F757)
        wk = self.wiki_lookup(prompt, steer=eff_steer)
        if wk:
            title = self._lemma(self.wiki_title[wk].lower())
            rel_note = ""
            if attach_extra:                                            # F763: short depth answers with the bare abstract
                drel = self._directed_relations(title, eff_steer, ctx_bundle, k=k_rel)   # F757/F759: directed + ctx-re-ranked
                arel = self._assoc_related(title, eff_steer, k=k_assoc)
                bits = []
                if drel:
                    bits.append("relations: " + self._fmt_rel(drel))
                if arel and (depth == "long" or not drel):              # long shows BOTH; normal falls back to assoc
                    bits.append("related: " + ", ".join(arel))
                rel_note = ("\n  (" + "; ".join(bits) + ")") if bits else ""
            return (f"{parse}\n[siona · wiki] {self.wiki_title[wk]}: {self.wiki[wk]}\n"
                    f"  (source: {self.wiki_cite[wk]}, CC-BY-SA){proc_note}{new_note}{rel_note}")
        # honest framing: a relations answer to a DEFINITION question is associations, NOT a held dictionary definition
        def_note = ("\n  (these are relations I hold — what it's near/does — not a dictionary definition)"
                    if intent == "definition" else "")
        # the DIRECTED + TYPED tier (F757) + the F759 STORY-BUILDER: etak-walk the relation graph into a path + a
        # composed sentence (not a flat dump). _lemma folds plural→singular; ctx_bundle re-ranks by running context.
        dsub = next((t for t in sorted(salient, key=len, reverse=True) if self._lemma(t) in self.relations), None)
        if dsub:
            key = self._lemma(dsub)
            path, _first = self._relation_walk(key, eff_steer, ctx_bundle, anchor=ctx_terms, steps=walk_steps)
            edges = self._directed_relations(key, eff_steer, ctx_bundle, k=k_rel)   # F763: the story honors answer depth
            return (f"{parse}\n[etak: {' → '.join(path)}]\n[siona] {self._relation_story(key, edges)}"
                    f"{proc_note}{new_note}{def_note}\n"
                    f"  (relations: {self._fmt_rel(edges)}; what follows {key} in simplewiki, CC-BY-SA)")
        # the UNCAPPED relational tier (F754): subject in the ~213k assoc graph -> its neighbours, steered (input-ride)
        asub = next((t for t in sorted(salient, key=len, reverse=True) if self._lemma(t) in self.assoc), None)
        if asub:
            key = self._lemma(asub)
            rel = self._assoc_related(key, eff_steer, k=k_assoc)           # F763: neighbour count honors answer depth
            return (f"{parse}\n[siona · relations] “{key}” is associated with: {', '.join(rel)}{proc_note}{new_note}{def_note}\n"
                    f"  (co-occurrence neighbours from the simplewiki relational kernel, CC-BY-SA)")
        if salient:                                            # named something specific in NO kernel. PASS 1 (F765) already
            subject = max(salient, key=len)                    # tried to comprehend it into canonical English; if it still
            # routed to no tier, it is GENUINELY unknown (not a misspelling/variant — those Pass 1 already understood and
            # handed to the gloss/relation tiers above, with the full depth treatment). So this is the honest terminal.
            return (f"{parse}\n[siona · asking-state] You asked about “{subject}”, which touches none of my kernels — "
                    f"I won't invent it. Tell me (“remember {subject} is …”, or just answer) and I'll learn it.")
        # F798: a pronoun we could NOT resolve (no prior topic in the conversation) is an unresolved REFERENCE, not a
        # "who are you" — answer with the asking-state, don't misroute to the identity card.
        if ANAPHORA_RE.search(pl):
            pron = ANAPHORA_RE.search(pl).group(0)
            return (f"[siona · asking-state] You said “{pron}”, but nothing earlier in our conversation for it to refer "
                    f"to. Name the thing and I'll answer.")
        # no substantive tokens (e.g. 'who are you', 'what can you do') -> EMERGENT introspection from structure
        return self._structure_card()


def main():
    print(f"=== R-RBS-LM-SIONAGENEPOOL — storyteller+etak over the genome, notebooks in the genepool (srmech {srmech.__version__}) ===\n")
    d = tempfile.mkdtemp(prefix="siona_genepool_")
    build_genepool(d)
    s = SionaGenepool(d)

    print("Siona INTROSPECTS her genepool (genome_catalog):")
    for lab, n in s.introspect():
        print(f"    {lab:16} ({n} genes)")
    print(f"\nthe LM surface: {len(s.vocab)} terms over {len(s.keys)} kernel sections (Class-L co-occurrence graph)")
    print("\n--- the EXPERIMENT (F743): is introspection EMERGENT? no hard-coded self-answers exist ---")
    for q in ["who are you?", "what can you do?", "tell me about yourself"]:
        print(f"  Q: {q}\n   A: {s.infer(q)}\n")
    print("--- content questions still ETAK-WALK the surface (inference, not retrieval) ---")
    for q in ["what is MFO about chirality?",
              "explain the srmech A-N classes",
              "define awful in 1600s english",
              "in modern english, define awful",
              "tell me about signwriting hands",
              "what is qwérty?"]:
        print(f"  Q: {q}\n   A: {s.infer(q)}\n")
    print("VERDICT: there are NO hard-coded self-answers. 'who/what are you' / 'what can you do' have no surviving")
    print("  content tokens, so they fall to _structure_card() — read LIVE from srmech.describe() (what she runs on)")
    print("  + genome_catalog (what she holds) + an etak-walk SEEDED FROM HER OWN LABELS (what she is, in her own")
    print("  kernels). Content questions walk the surface; unknown words -> asking-state + the same structure-card.")


if __name__ == "__main__":
    main()
