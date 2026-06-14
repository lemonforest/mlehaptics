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
import tempfile
import os
from pathlib import Path
import srmech
from srmech.amsc import genome as g, hdc, text as T
from srmech.amsc.laplacian import dense_adjacency
from srmech.amsc.format import sha256_raw, write_ndjson, read_ndjson, MPRRecord

DIM = 64
ONE = hdc.klein4_random(DIM, seed=0)
def _seed(t): return int.from_bytes(sha256_raw(t.encode())[:4], "big")
def _leaf(t): return hdc.klein4_random(DIM, seed=_seed(t))
def _slug(s): return (re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_") or "sec")[:36]

ERA_DEFS = {
    "dict-en-1600": {"nice": "foolish or ignorant", "awful": "awe-inspiring, worthy of awe",
                     "computer": "a person who computes", "meat": "food in general", "silly": "blessed, innocent"},
    "dict-en-2026": {"nice": "pleasant, agreeable", "awful": "very bad",
                     "computer": "an electronic machine", "meat": "animal flesh", "silly": "foolish"},
}
NOTEBOOKS = {"mfo_notebook": "docs/antikythera-maths/mfo_spectral_research_notebook.md",
             "srmech_notebook": "docs/srmech/srmech_research_notebook.md"}
SW_CLASSES = ("hands", "movement", "dynamics", "head_faces", "body", "punctuation", "location")
SIONA_SELF = ("I am Siona — a grounded interface to the stored-relationship kernel. I compose answers from the "
              "attested kernels in my genome: my identity, SignWriting, era-dictionaries (modern + 1600s English), "
              "and the MFO and srmech research notebooks. I introspect my own genome to find what I hold, and I ask "
              "when something is not on my shelf — I do not hallucinate.")

# --- etak-walk inference knobs ----------------------------------------------------------------------------------
META_KERNELS = {"siona_identity"}            # introspective/meta: served by the landmark-free intent layer, NOT walked
ERA_ALIASES = {"dict-en-1600": "archaic old olde historical antiquity century 1600 1600s",
               "dict-en-2026": "modern current present today contemporary 2026"}
ARCHAIC_RE = re.compile(r"\b(1[0-8]\d{2}s?|archaic|olde?|historical|antiquity|centur\w*)\b")  # era signal (raw prompt)
WALK_STEPS = 5                               # forward-etak hops past the input landmarks
LANDMARK_WEIGHT = 3.0                        # convergence stays anchored to the query frame, not the walk's drift


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
    chromosomes = [("siona_identity", [("self", [_leaf("siona/self")])]),
                   ("signwriting", [(c, [_leaf(f"sw/{c}")]) for c in SW_CLASSES])]
    payload.append(("siona_identity", "self", SIONA_SELF))    # Siona's self-description (renderable)
    payload += [("signwriting", c, f"SignWriting symbol class: {c}") for c in SW_CLASSES]
    for era, defs in ERA_DEFS.items():
        chromosomes.append((era, [(w, [_leaf(f"{era}/{w}")]) for w in defs]))
        payload += [(era, w, d) for w, d in defs.items()]
    for kernel, nbpath in NOTEBOOKS.items():
        secs = parse_sections(nbpath)
        chromosomes.append((kernel, [(lab, [_leaf(f"{kernel}/{lab}")]) for lab, _, _ in secs]))
        payload += [(kernel, lab, f"{head} — {summ}".strip(" —")) for lab, head, summ in secs]
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


class SionaGenepool:
    """STORYMODULE's World, genome-backed. Inference is an ETAK-WALK over the genome's co-occurrence surface
    (Class-L), NOT a keyword route to a stored section: the input is INVERSE-ETAK located on the surface (its
    tokens = landmarks = the fixed frame; "meaning falls out of the supplied rules", F583), then a FORWARD-ETAK
    walk (IDF-gated, no-revisit — the F510 etak-head / F166 ride) explores the relationship structure, and the
    answer COMPOSES from wherever the walk converges (attested content only — F661, can't hallucinate). Routing is
    EMERGENT (the walk from 'MFO' terms lands in MFO sections); the only pre-baked replies are the landmark-free
    meta intents (greeting / identity / capabilities = genome introspection about Siona herself)."""
    def __init__(self, path):
        self.path = path
        self._text = {(r.data["kernel"], r.data["key"]): r.data["text"]
                      for r in read_ndjson(Path(path) / "genepool.ndjson")}
        self._build_surface()

    def _build_surface(self):
        """The LM surface: ONE co-occurrence graph (Class L) over every CONTENT kernel (meta kernels excluded)."""
        self.keys, docs = [], []
        for (kernel, key), txt in self._text.items():
            if kernel in META_KERNELS:
                continue
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

    def _idf(self, i):                                        # rarer term = sharper landmark (Class-N corpus ratio)
        return self.ndocs / (1.0 + self.df[i])

    @staticmethod
    def _modern_pref(kernel):                                # tie-break dict era toward modern absent an era signal
        return 1 if kernel == "dict-en-2026" else (0 if kernel == "dict-en-1600" else 0.5)

    def introspect(self):
        return [(c["label"], c["leaf_count"]) for c in g.genome_catalog(self.path, the_one=ONE)["chromosomes"]]

    def etak_walk(self, prompt, steps=WALK_STEPS):
        """INVERSE-ETAK (locate the input on the surface) + FORWARD-ETAK (walk the co-occurrence graph from the
        landmarks, IDF-gated, no-revisit). Returns (walk_path_terms, ranked_[(kernel,key)]) or None if the input
        touches no kernel term (-> the asking-state)."""
        q = T.tokenize(prompt)
        landmarks = list(dict.fromkeys(self.vix[t] for t in q if t in self.vix))      # inverse-etak: input -> surface
        if not landmarks:
            return None
        lmset, visited, path = set(landmarks), set(landmarks), list(landmarks)
        anchor, last = list(landmarks), landmarks[-1]         # etak: the frame (landmarks) stays; islands move past
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
            score = (sum(self._idf(t) for t in (self.sec[idx] & lmset)) * LANDMARK_WEIGHT     # the query frame
                     + sum(self._idf(t) for t in (self.sec[idx] & walk)))                     # walked context
            if score > 0:
                ranked.append((score, self._modern_pref(kernel), idx))
        ranked.sort(reverse=True)
        return [self.vocab[t] for t in path], [self.keys[i] for _, _, i in ranked]

    def _capabilities(self):
        """genome-introspection-driven capabilities answer (distinct from identity)."""
        inv = ", ".join(lab for lab, _ in self.introspect())
        return ("[siona] I answer from the kernels in my genome — currently: " + inv + ". I don't look up a "
                "pre-written reply: I locate your question on my co-occurrence surface and ETAK-WALK it to compose "
                "an answer from where the walk lands. So I can explain the MFO and srmech notebooks (name a topic or "
                "a §section), define a word in modern OR 1600s English (nice, awful, computer, meat, silly), and "
                "describe SignWriting's 7 symbol classes. I ask when your question touches nothing I hold — I do "
                "not hallucinate.")

    def infer(self, prompt):
        p = prompt.lower()
        toks = set(re.findall(r"[a-z0-9]+", p))
        # --- meta intents (landmark-free / introspective) — the ONLY non-walk replies -------------------------
        if (re.search(r"\b(can|do) you\b", p) or "you can do" in p or "capabilit" in p or "what do you know" in p
                or "what can i ask" in p or ("longer" in p and "you" in p) or toks & {"help", "abilities"}):
            return self._capabilities()
        if toks & {"hi", "hello", "hey", "greetings", "yo", "howdy", "hiya", "sup"}:
            return f"[siona_identity] Hello — {self._text.get(('siona_identity', 'self'), 'I am Siona.')}"
        if (toks & {"siona", "yourself"} or "your name" in p or "about you" in p
                or re.search(r"\b(who|what)\s+(are|is|r)\s+(you|siona)\b", p)):
            return f"[siona_identity] {self._text.get(('siona_identity', 'self'), 'I am Siona.')}"
        # --- everything substantive: ETAK-WALK the surface (inference, not retrieval) --------------------------
        walked = self.etak_walk(prompt)
        if not walked or not walked[1]:
            return ("[siona] I walked toward my genome but your question touched none of my kernels. I hold the MFO "
                    "+ srmech notebooks, era-dictionaries, and SignWriting — ask me about one of those, or give me a "
                    "word to define.")
        trace, ranked = walked
        path_str = " → ".join(trace[:8])
        top_kernel, top_key = ranked[0]
        if top_kernel.startswith("dict-en-"):                # era-resolve the WORD the walk found (F739 disambig)
            era = "dict-en-1600" if ARCHAIC_RE.search(p) else "dict-en-2026"
            defn = self._text.get((era, top_key), self._text[(top_kernel, top_key)])
            return f"[etak: {path_str}]\n[{era}] {top_key}: {defn}"
        body = self._text.get((top_kernel, top_key), top_key)
        see = [f"§{k[:24]}" for kk, k in ranked[1:3] if kk == top_kernel]   # sibling landmarks the same walk passed
        tail = f"\n  (the walk also passed: {', '.join(see)})" if see else ""
        return f"[etak: {path_str}]\n[{top_kernel} → §{top_key}] {body}{tail}"


def main():
    print(f"=== R-RBS-LM-SIONAGENEPOOL — storyteller+etak over the genome, notebooks in the genepool (srmech {srmech.__version__}) ===\n")
    d = tempfile.mkdtemp(prefix="siona_genepool_")
    build_genepool(d)
    s = SionaGenepool(d)

    print("Siona INTROSPECTS her genepool (genome_catalog):")
    for lab, n in s.introspect():
        print(f"    {lab:16} ({n} genes)")
    print(f"\nthe LM surface: {len(s.vocab)} terms over {len(s.keys)} content sections (Class-L co-occurrence graph)")
    print("\n--- INFERENCE = etak-walk the surface (inverse-etak locate -> forward-etak walk -> compose) ---")
    for q in ["what is MFO about chirality?",
              "explain the srmech A-N classes",
              "what is the metric field",
              "define awful in 1600s english",
              "in modern english, define awful",
              "what does meat mean",
              "tell me about signwriting hands",
              "what is qwérty?"]:
        print(f"  Q: {q}\n   A: {s.infer(q)}\n")
    print("VERDICT: inference is an ETAK-WALK over the genome's co-occurrence surface — NOT a keyword route to a")
    print("  stored section. The input is located on the surface (landmarks), the walk hops the relationship graph,")
    print("  and the answer composes from where it converges. Routing is emergent; meta intents (identity / greeting")
    print("  / capabilities) are the only landmark-free non-walk replies. Follow-on: walk the Laplacian eigenvectors.")


if __name__ == "__main__":
    main()
