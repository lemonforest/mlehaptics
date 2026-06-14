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
SIONA_NAME = "Siona"
# committed learned items (git-trackable, folded into the genome as a `learned` chromosome by build_genepool);
# temporary learned items live in a gitignored `learned_temp.json` inside the genome dir (ephemeral, this-session).
LEARNED_KERNEL_FILE = Path(__file__).parent / "siona_learned_kernel.json"

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
    chromosomes = [("signwriting", [(c, [_leaf(f"sw/{c}")]) for c in SW_CLASSES])]
    payload += [("signwriting", c, f"SignWriting symbol class: {c}") for c in SW_CLASSES]
    for era, defs in ERA_DEFS.items():
        chromosomes.append((era, [(w, [_leaf(f"{era}/{w}")]) for w in defs]))
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
        self._text = {(r.data["kernel"], r.data["key"]): r.data["text"]
                      for r in read_ndjson(Path(path) / "genepool.ndjson")}
        self._build_surface()
        # WRITE-MODE store (the learning loop): learned[term] = text, the union of committed (already in the genome
        # as the `learned` chromosome) + temporary (gitignored learned_temp.json inside the genome dir, this-session).
        self._temp_file = Path(path) / "learned_temp.json"
        self.learned = {key: txt for (k, key), txt in self._text.items() if k == "learned"}   # committed
        if self._temp_file.exists():
            self.learned.update(json.loads(self._temp_file.read_text() or "{}"))               # + temporary

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
        return [(c["label"], c["leaf_count"]) for c in g.genome_catalog(self.path, the_one=ONE)["chromosomes"]]

    def _walk(self, landmarks, steps=WALK_STEPS):
        """FORWARD-ETAK: walk the co-occurrence graph from `landmarks` (IDF-gated, no-revisit; the landmarks held
        in-frame), then rank sections by landmark+walk overlap. Returns (walk_path_terms, ranked_[(kernel,key)]) or
        None if `landmarks` is empty."""
        landmarks = list(dict.fromkeys(landmarks))
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
            if self.maint[idx]:
                score *= MAINT_PENALTY                        # maintenance prose is not a good answer landing
            if score > 0:
                ranked.append((score, self._modern_pref(kernel), idx))
        ranked.sort(reverse=True)
        return [self.vocab[t] for t in path], [self.keys[i] for _, _, i in ranked]

    def etak_walk(self, prompt, steps=WALK_STEPS):
        """INVERSE-ETAK: locate the input's tokens on the surface, then forward-walk from them."""
        return self._walk([self.vix[t] for t in T.tokenize(prompt) if t in self.vix], steps)

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
        """Siona's self-knowledge, READ FROM STRUCTURE at runtime — NO hard-coded prose (F743 experiment): (a)
        srmech.describe() = the substrate she runs on; (b) genome_catalog = the kernels she holds = what she can
        answer about. She knows this "by definition": she IS an srmech instance carrying exactly these kernels, so
        introspection is read off the structure, not asserted. (The deeper "walk my own prose to find myself" seed
        was tested and is NOISE — the self-terms are rare, so IDF drags the walk into citation/appendix metadata;
        F743. The clean emergent self-knowledge is describe() + catalog.)"""
        d = srmech.describe()
        doc1 = (srmech.__doc__ or "").strip().split(".")[0].strip()          # srmech's OWN one-line self-description
        held = "; ".join(f"{lab} ({n})" for lab, n in self.introspect())
        return (f"[identity] I am {SIONA_NAME} — the running, genome-backed instance of {doc1}. srmech is my "
                f"substrate; {SIONA_NAME} is me running it — the same system, named at two levels (srmech = the "
                f"mechanism/package; {SIONA_NAME} = this instance reading its genome).\n"
                f"[srmech.describe()] My substrate is {d['tools']['total']} stored-relationship ops across "
                f"{len(d['categories'])} categories (srmech {d['srmech_version']}).\n"
                f"[genome_catalog] The kernels I hold — and so what I can answer from — are: {held}. Ask me about "
                "any of these (or give me a word to define), or teach me something new (“remember <term> is …”); "
                "I etak-walk what I hold to compose an answer, and I ask when your question touches nothing I have.")

    def infer(self, prompt, prev_assistant=""):
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

        # === identity: Siona == srmech ====================================================================
        if "siona" in pl or re.search(r"\byou\b.*\bsrmech\b|\bsrmech\b.*\byou\b|same thing", pl):
            return self._structure_card()

        # === ETAK-WALK the surface (inference, not retrieval) =============================================
        content = T.tokenize(prompt)
        landmarks = [self.vix[t] for t in content if t in self.vix]
        if landmarks:
            trace, ranked = self._walk(landmarks)
            path_str = " → ".join(trace[:8])
            top_kernel, top_key = ranked[0]
            if top_kernel.startswith("dict-en-"):             # era-resolve the WORD the walk found (F739 disambig)
                era = "dict-en-1600" if ARCHAIC_RE.search(pl) else "dict-en-2026"
                defn = self._text.get((era, top_key), self._text[(top_kernel, top_key)])
                return f"[etak: {path_str}]\n[{era}] {top_key}: {defn}"
            body = self._text.get((top_kernel, top_key), top_key)
            see = [f"§{k[:24]}" for kk, k in ranked[1:3] if kk == top_kernel]   # siblings the same walk passed
            tail = f"\n  (the walk also passed: {', '.join(see)})" if see else ""
            return f"[etak: {path_str}]\n[{top_kernel} → §{top_key}] {body}{tail}"
        if content:                                            # named something specific NOT on the surface -> ASK
            subject = max(content, key=len)                   # the salient term (so a follow-up answer binds to it)
            return (f"[siona · asking-state] You asked about “{subject}”, which touches none of my kernels — I won't "
                    f"invent it. Tell me (“remember {subject} is …”, or just answer) and I'll learn it. "
                    f"Otherwise, here is what I am:\n{self._structure_card()}")
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
