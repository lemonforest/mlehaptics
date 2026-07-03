"""siona.infer — the grounded inference loop (the five rc1-gate capabilities, F1008–F1012).

route (F1010: declared operators + operand shape; NO similarity thresholds)
  -> ground (F1008: name-weighted + order-carrying encoding over srmech's live tool_schema)
  -> drive (F1009: signature-fit on typed params; F1012: cross-turn operand resolution from memory)
  -> handlers over ONE never-compacted working memory (`feedback_siona_working_memory_never_compacted`),
including ingested linear-map knowledge KERNELS composed exact-rationally (F1012: integer num/den,
srmech ``cyclic.gcd`` Class-I reduction, collapse only at display — no floats mid-cascade).

Encoding standard (PKG-1 bag audit): every content encoding carries ORDER — unigrams + adjacency
bigrams for grounding; position-keyed ``encode_context`` for continuation; positional byte/glyph word
composition. An order-free bundle may only ever be a weighting statistic, never a representation.

Siona's own tool surface registers into srmech's REAL registry (``register_profile_tools`` — F1011),
so one registry serves both surfaces and ``help`` answers from the LIVE schema (Class-H).
"""
import re
import importlib

from .boards import Board, ENGLISH

__all__ = ["Session", "Grounding"]

_WORD = re.compile(r"[^a-z0-9]+")
_LD = re.compile(r"([a-z])([0-9])")
_DL = re.compile(r"([0-9])([a-z])")


def _toks(s):
    s = (s or "").lower()
    s = _LD.sub(r"\1 \2", s)
    s = _DL.sub(r"\1 \2", s)  # klein4 -> klein 4 ; sha256 -> sha 256 (query and name agree)
    return [w for w in _WORD.split(s) if len(w) > 1 or w.isdigit()]


class Grounding:
    """The F1008 utterance->tool grounding index over srmech's live tool_schema (all owners)."""

    def __init__(self, D=8192):
        from srmech.rbs_lm.substrate import ContextSubstrate
        from srmech.amsc import hdc
        self._hdc = hdc
        self.D = D
        self.cs = ContextSubstrate(D=D, hex_chars=16)
        self._vec_cache = {}
        self.refresh()

    def refresh(self):
        """(Re)build the index from the LIVE registry — call after registering new tools."""
        from srmech.amsc import tool_schema as ts
        self.tools = {t.name: t for t in ts.get_tool_schema().tools}
        nt = len(self.tools)
        self._nm = {n: _toks(n.split(".")[-1]) for n in self.tools}
        self._su = {n: _toks(t.summary) for n, t in self.tools.items()}
        docf = {}
        for n in self.tools:
            for w in set(self._nm[n] + self._su[n]):
                docf[w] = docf.get(w, 0) + 1
        func = int(nt * 0.35)
        self._gate = lambda w: 1.0 if docf.get(w, 0) < func else func / docf[w]
        self._idx = [(n, self._enc_tool(n)) for n in self.tools]
        self._byname = dict(self._idx)

    def vec(self, w):
        if w not in self._vec_cache:
            self._vec_cache[w] = self._hdc.klein4_random(
                self.D, seed=(sum((i + 1) * ord(c) for i, c in enumerate(w)) % 80000) + 7)
        return self._vec_cache[w]

    def _bg(self, ws):  # adjacency bigrams — order-carrying, never a bag
        return [self._hdc.klein4_bind(self.vec(a), self.vec(b)) for a, b in zip(ws, ws[1:])]

    def _enc_tool(self, n):
        nmw = self._nm[n]
        suw = [w for w in self._su[n] if self._gate(w) >= 1.0]
        parts = [self.vec(w) for w in nmw] * 3 + self._bg(nmw) * 2  # NAME = identity, weighted (F769)
        parts += [self.vec(w) for w in suw] + self._bg(suw)
        return self.cs.bundle_odd(parts or [self.vec("_")])

    def enc_query(self, u):
        ws = [w for w in _toks(u) if self._gate(w) >= 1.0]
        return self.cs.bundle_odd(([self.vec(w) for w in ws] + self._bg(ws)) or [self.vec("_")])

    def sim(self, a, b):
        q = self._hdc.klein4_similarity(a, b)
        return q.as_float() if hasattr(q, "as_float") else float(q)

    def ground(self, u, k=5, owner=None):
        q = self.enc_query(u)
        sc = ((self.sim(q, v), n) for n, v in self._idx
              if owner is None or self.tools[n].owner == owner)
        top = sorted(sc, reverse=True)[:k]
        # within-family re-rank (the F1008 open lever): if any tool's FULL name-token set is
        # contained in the query, promote the longest such name — rule-based exact coverage over
        # the WHOLE owner index (cheap set-ops; no tuned weights). 'klein 4 similarity' promotes
        # klein4_similarity even when the bundle-sim rank buried it.
        qt = set(_toks(u))
        # coverage relation: exact token OR morphological PREFIX (suffixation: 'cosine' covers 'cos').
        # Chosen by pre-measurement (F1017): prefix-cover keeps the index Gram unchanged (0.271) and
        # the eval at 15/18 while recovering 3/5 alias cases; the byteglyph-vector alternative was
        # REJECTED read-independently (+0.130 index-wide cross-talk AND worse alias, 1/5).
        def covers(t):
            return any(w == t or (len(t) >= 3 and w.startswith(t) and len(w) - len(t) <= 4)
                       for w in qt)
        pool = [n for n in self._byname
                if (owner is None or self.tools[n].owner == owner)
                and self._nm[n] and all(covers(t) for t in self._nm[n])]
        if pool:
            n0 = max(pool, key=lambda n: sum(len(t) for t in self._nm[n]))
            top = [(self.sim(q, self._byname[n0]), n0)] + [(s, n) for s, n in top if n != n0]
        return top[:k]


def _register_self_tools():
    """Register siona's own surface into srmech's registry (F1011). Idempotent."""
    from srmech.amsc import tool_schema as ts
    if any(t.owner == "siona" for t in ts.get_tool_schema().tools):
        return
    from srmech.amsc.tool_schema import ToolEntry, ToolParameter, ToolReturn

    def T(name, summary):
        return ToolEntry(
            name=name, owner="siona", category="siona", summary=summary,
            parameters=(ToolParameter(name="text", type="str", required=False,
                                      summary="utterance remainder"),),
            returns=ToolReturn(type="str"))
    ts.register_profile_tools("siona", [
        T("siona.memory.remember", "Remember a note: store the given text into siona's never-compacted working memory. Aliases: ingest, save, note this."),
        T("siona.memory.recall", "Recall from working memory: retrieve the stored note or driven result most similar to the query text."),
        T("siona.memory.forget", "Forget: with no argument pop the last note; with a query, SURGICALLY graft out the best-matching note (user-directed removal; the MPR attestation trail re-indexes)."),
        T("siona.memory.purge", "Purge ALL working-memory notes and their attestations on explicit request. Learned verbs stay (unlearn per verb)."),
        T("siona.memory.show", "Show the working memory: list every stored note and driven result in order."),
        T("siona.read.define", "Define a concept: depth-read the srmech tool catalog and return the best definition summary for the query."),
        T("siona.read.continue_text", "Continue a text prefix: substrate next-token read from siona's remembered content."),
        T("siona.introspect.help", "List siona's own commands: enumerate the siona tool schema from the live registry (self-introspection, Class H). Serves asks like: what can you do, what are you able to do, list your commands, help."),
        T("siona.read.answer", "Answer a question from remembered knowledge: compose recalled facts with ingested unit-conversion kernels to derive the asked value exactly (celsius to fahrenheit and similar unit questions)."),
        T("siona.knowledge.load", "Load a knowledge instrument by path (an RBS-HDC NDJSON instrument with its title index). Knowledge is user-side data; the wheel ships mechanism only."),
        T("siona.knowledge.acquire", "Acquire a topic from the loaded instrument: look up the title, take the lead, store it as an ATTESTED note (source path + byte offset + sha256 of the record -- Class-A provenance)."),
        T("siona.knowledge.pack", "Pack the acquired attested notes into a persistent Laplacian-encoded store (co-occurrence -> normalized Laplacian -> eigenmodes) written to the given path and verified by reload."),
    ])


class Session:
    """A multi-turn grounded inference session (F1012): one loop, both surfaces, one memory."""

    ACCRETE_K = 3  # accretion guard: k consistent, UNANIMOUS resolutions before a word earns its role

    def __init__(self, board: Board = ENGLISH, D=8192):
        self.board = board
        self.mem = []  # never compacted; grows for the life of the session
        self.learned_verbs = {}   # ACCRETED word->tool (F1018: roles fixed, words evolve by usage)
        self._verb_obs = {}       # accretion tallies: lead-word -> {tool: count}
        self.last_result = None   # the RESULT REGISTER: the actual object a [srmech] turn returned (F1024)
        self.instrument = None    # loaded knowledge instrument (path, index) -- mechanism-not-knowledge:
        self.attestations = []    # knowledge loads by PATH; every acquired fact carries Class-A attestation
        _register_self_tools()
        self.g = Grounding(D=D)
        self._impl = {
            "siona.memory.remember": self._remember, "siona.memory.recall": self._recall,
            "siona.memory.forget": self._forget, "siona.memory.show": self._show,
            "siona.memory.purge": self._purge,
            "siona.read.define": self._define, "siona.read.continue_text": self._continue,
            "siona.introspect.help": self._help, "siona.read.answer": self._answer,
            "siona.knowledge.load": self._k_load, "siona.knowledge.acquire": self._k_acquire,
            "siona.knowledge.pack": self._k_pack,
        }

    # ---- router (F1010: declared operators + operand shape; continue = the default) ----
    def _operands(self, u):
        # floats parse as EXACT rational int-pairs (stay-rational; float() only at the call boundary)
        fls = [(int(a + b), 10 ** len(b)) for a, b in re.findall(r"(-?\d+)\.(\d+)", u)]
        u2 = re.sub(r"-?\d+\.\d+", " ", u)
        # EDGE-PAIR operands: 'a-b' spans become (a,b) tuples (graph ops); consumed before the int pool
        edges = [(int(a), int(b)) for a, b in re.findall(r"\b(\d+)-(\d+)\b", u2)]
        u3 = re.sub(r"\b\d+-\d+\b", " ", u2)
        ints = [int(x) for x in re.findall(r"-?\d+", u3)]
        m = re.search(r"(?:bytes|string|text)\s+[\"']?([a-z]{2,})[\"']?\s*$", u.lower())
        return ints, fls, (m.group(1).encode() if m else None), edges

    def route(self, u):
        b, ws = self.board, _toks(u)
        while ws and ws[0] in b.politeness and not (ws[0] == b.address or ws[0] in b.self_verbs):
            ws = ws[1:]   # paraphrase frames: politeness prefixes are declared operators, consumed here
        if ws and (ws[0] == b.address or ws[0] in b.self_verbs):
            return "self-command"
        ints, fls, byts, edges = self._operands(u)
        if b.has_define(ws) and not (ints or fls or byts or edges):
            return "define"
        if ints or fls or byts or edges:
            return "tool-call"  # operand shape = strong evidence (F1009)
        if ws and ws[0] in b.imperatives:
            return "tool-call"
        if any(w in b.interrogatives for w in ws):
            return "self-command"  # WH-IN-SITU: an interrogative anywhere marks a question
                                   # ('water boils at what fahrenheit' -- the CLI's implicit address);
                                   # grounding selects the read (answer/define/recall). Known caveat:
                                   # relative-pronoun uses ('he knows what he wants') also match.
        return "continue"

    def turn(self, u):
        """Route + dispatch one utterance; returns (intent, tag, output)."""
        r = self.route(u)
        if r == "self-command":
            tool, out = self._drive_self(u)
            return r, "siona.%s" % tool, out
        if r == "tool-call":
            return r, "srmech", self._drive_tool(u)
        if r == "define":
            return r, "define", self._define(self._rem(u))
        return r, "substrate", self._continue(u)

    # ---- the self surface (F1011: declared verb = deterministic dispatch; grounding for verb-less) ----
    def _rem(self, u):
        return " ".join(w for w in _toks(u) if w not in self.board.strip)

    def _drive_self(self, u):
        b, ws = self.board, _toks(u)
        while ws and ws[0] in b.politeness and not (ws[0] == b.address or ws[0] in b.self_verbs):
            ws = ws[1:]
        lead = ws[1] if ws and ws[0] == b.address and len(ws) > 1 else (ws[0] if ws else "")
        if b.homographs and lead in b.homographs:
            # SUPERPOSED homograph (F1018): rung-select by the language vote over the parent boards'
            # operator vocabularies; LOW MARGIN -> ASK, never guess (the conflict-fallback policy).
            senses = b.homographs[lead]
            votes = [sum(1 for w in ws if w != lead and w in parent.operator_vocab())
                     for parent in b.parents]
            best = max(range(len(votes)), key=lambda i: votes[i])
            margin = votes[best] - max((v for i, v in enumerate(votes) if i != best), default=0)
            if margin < 1:
                opts = " | ".join("%s (%s)" % (t.split(".")[-1], bn) for bn, t in senses)
                return lead, "'%s' is ambiguous here -- which sense: %s ?" % (lead, opts)
            pick = senses[best][1]
        elif lead in self.learned_verbs:
            pick = self.learned_verbs[lead]        # ACCRETED verb = earned deterministic dispatch
        elif lead in b.verb_tools:
            pick = b.verb_tools[lead]
        else:  # verb-less ask -> ground by meaning; interrogatives are intent-operators, stripped
            q = " ".join(w for w in ws if w != b.address and w not in b.interrogatives)
            pick = self.g.ground(q, 1, owner="siona")[0][1]
            # ACCRETION (F1018, guarded): an unknown LEAD word tallies its meaning-resolved role; at
            # ACCRETE_K consistent UNANIMOUS resolutions it earns deterministic dispatch. unlearn() reverses.
            if (lead and lead not in b.self_verbs and lead not in b.interrogatives
                    and lead != b.address and lead.isalpha()):
                tally = self._verb_obs.setdefault(lead, {})
                tally[pick] = tally.get(pick, 0) + 1
                if len(tally) == 1 and tally[pick] >= self.ACCRETE_K:
                    self.learned_verbs[lead] = pick
        return self._finish_self(pick, u, ws, b)

    def unlearn(self, verb):
        self.learned_verbs.pop(verb, None)
        self._verb_obs.pop(verb, None)

    def _finish_self(self, pick, u, ws, b):
        if pick.startswith("siona.knowledge."):
            raw = [w for w in u.split() if w.lower() != b.address]
            if raw and raw[0].lower() in ("load", "acquire", "learn", "pack"):
                raw = raw[1:]
            return pick.split(".")[-1], self._impl[pick](" ".join(raw))
        if pick == "siona.memory.remember":
            # notes store UNDOCTORED (F982): raw whitespace words (NOT _toks -- its len>1 filter is an
            # English-privilege artifact that drops Bislama's predicate marker 'i', docf 31/31), minus
            # only the address + the dispatching verb. Reads de-lens; storage never does.
            raw = [w.lower() for w in u.split() if w.lower() != b.address]
            if raw and raw[0] in (b.self_verbs | set(b.verb_tools)):
                raw = raw[1:]
            return pick.split(".")[-1], self._impl[pick](" ".join(raw))
        return pick.split(".")[-1], self._impl[pick](self._rem(u))

    # ---- the drive loop (F1009 + F1012 cross-turn operand resolution) ----
    REF_WORDS = frozenset({"it", "its", "that", "result"})  # the RESULT REGISTER reference operators

    def _fit(self, t, ints, fls, byts, edges=(), ref=None):
        pt = lambda p: p.type.lower().strip()
        reqs = [p for p in t.parameters if p.required]
        if not reqs:
            return 0.0
        intp = sum(1 for p in reqs if pt(p) == "int")
        fltp = sum(1 for p in reqs if pt(p) == "float")
        bytp = sum(1 for p in reqs if "bytes" in pt(p))
        listp = sum(1 for p in reqs if any(k in pt(p) for k in ("list", "sequence", "tuple")))
        refp = sum(1 for p in reqs if ref and ref.lower() in pt(p)
                   and not any(k in pt(p) for k in ("list", "sequence", "tuple")))
        if len(reqs) - intp - fltp - bytp - listp - refp:
            return 0.0
        if refp:
            # exactly ONE carrier slot: duplicating one register into several params is never the
            # intent (caught live: eigenvalues-of-it bound M into pseudo_hermitian(M, M) -> True)
            return 2.0 if refp == 1 else 0.0
        if bytp and byts is None:
            return 0.0
        if fltp > len(fls) + len(ints):  # a float slot may consume an int operand
            return 0.0
        if listp:
            if edges:  # EDGE operands fill tuple-list params; a lone int param named n derives from edges
                return 2.0
            return 0.4 if ints else 0.0
        if intp > len(ints):
            return 0.0
        exact = (intp + fltp == len(ints) + len(fls)) and (bytp > 0) == (byts is not None)
        return 2.0 if exact else 1.0

    def _drive_tool(self, u):
        ints, fls, byts, edges = self._operands(u)
        ref = (type(self.last_result).__name__
               if self.last_result is not None
               and any(w in self.REF_WORDS for w in _toks(u)) else None)
        cands = [n for _, n in self.g.ground(u, 5, owner="srmech")]
        resolved = ""
        if all(self._fit(self.g.tools[n], ints, fls, byts, edges, ref) == 0.0 for n in cands) and self.mem:
            # cross-turn operand resolution: the utterance under-supplies -> recall the referenced note
            kw = self.board.kernel_ops["kernel"]
            topname = self.g._nm[cands[0]]
            q = " ".join(w for w in _toks(u) if not w.isdigit()
                         and w not in self.board.imperatives and w not in topname
                         and w not in ("of", "the", "and"))
            qv = self._enc_note(q)
            note = max((m for m in self.mem if kw not in _toks(m)), default=None,
                       key=lambda m: self.g.sim(qv, self._enc_note(m)))
            if note:
                mem_ints = [int(w) for w in _toks(note) if w.isdigit()]
                ints = mem_ints[:1] + ints
                resolved = ' [operand %s resolved from: "%s"]' % (mem_ints[:1], note)
        scored = sorted(((self._fit(self.g.tools[n], ints, fls, byts, edges, ref), -cands.index(n), n)
                         for n in cands), reverse=True)
        ranked = [n for f, _, n in scored if f > 0] or cands[:1]
        # FAILED-RUN RECOVERY (hardening ii): try fit-positive candidates in order; a raise moves to
        # the next candidate; every attempt is recorded into working memory (nothing hidden).
        attempts = []
        for pick in ranked[:3]:
            fn = self._resolve(pick)
            ba = self._bind_args(pick, u, ints, fls, byts, edges, ref)
            if fn is None or ba is None:
                attempts.append("%s: unbindable" % pick.split(".")[-1])
                continue
            args, kw = ba
            shown = "%s(%s)" % (pick.split(".")[-1], ", ".join(
                [repr(a) if isinstance(a, bytes) else str(a) for a in args]
                + ["%s=%s" % (k, v) for k, v in kw.items()]))
            try:
                res = fn(*args, **kw)
            except Exception as e:
                attempts.append("%s -> ERR %s" % (shown, e))
                self.mem.append("attempt %s = ERR %s" % (shown, e))
                continue
            self.mem.append("%s = %s" % (shown, res))
            self.last_result = res                 # the register holds the OBJECT for the next turn
            note = " [recovered after: %s]" % "; ".join(attempts) if attempts else ""
            return "%s = %s%s%s" % (shown, str(res)[:60], resolved, note)
        return "(no runnable candidate; attempts: %s)" % ("; ".join(attempts) or "none")

    def _resolve(self, dotted):
        parts = dotted.split(".")
        for i in range(len(parts), 0, -1):
            try:
                obj = importlib.import_module(".".join(parts[:i]))
                for p in parts[i:]:
                    obj = getattr(obj, p)
                return obj
            except (ImportError, AttributeError):
                continue
        return None

    def _bind_args(self, pick, u, ints, fls, byts, edges=(), ref=None):
        # NAMED operands: match the tool's OWN declared parameter names in the utterance,
        # both orders ('terms 12' / '12 terms'). Schema-driven — no per-tool code.
        named, ul = {}, u.lower()
        for p in self.g.tools[pick].parameters:
            if any(k in p.type.lower() for k in ("list", "tuple", "sequence", "bytes")):
                continue  # named extraction is for SCALAR params only ('edges 0-1' must not match edges=0)
            nm = re.escape(p.name.lower())
            m = (re.search(r"\b%s\s+(-?\d+(?:\.\d+)?)" % nm, ul)
                 or re.search(r"(-?\d+(?:\.\d+)?)\s+%s\b" % nm, ul))
            if m:
                named[p.name] = m.group(1)
        fq = list(fls)
        args, kw, ii = [], {}, 0
        for p in self.g.tools[pick].parameters:
            tp = p.type.lower().strip()
            if p.name in named:
                v = named[p.name]
                kw[p.name] = float(v) if tp == "float" else int(float(v))  # by NAME (keyword-only safe)
                if "." in v and fq:
                    fq.pop(0)
                elif v.lstrip("-").isdigit() and int(v) in ints:
                    ints = [x for x in ints if x != int(v)] or ints[1:]
                continue
            if not p.required and ii >= len(ints) and not fq:
                break
            if "bytes" in tp:
                if byts is None:
                    return None
                args.append(byts)
            elif tp == "float":
                if fq:
                    num, den = fq.pop(0)
                    args.append(float(num) / float(den))  # exact rational -> float at the CALL boundary only
                elif ii < len(ints):
                    args.append(float(ints[ii])); ii += 1
                else:
                    return None
            elif tp == "int":
                if ii >= len(ints):
                    if p.name == "n" and edges:    # schema-driven: n derives from the edge operands
                        args.append(max(max(a, b) for a, b in edges) + 1)
                        continue
                    return None
                args.append(ints[ii]); ii += 1
            elif any(k in tp for k in ("list", "sequence", "tuple")):
                if edges and "tuple" in tp:
                    args.append(list(edges))       # EDGE-PAIR operands -> Iterable[Tuple[int,int]] params
                else:
                    args.append(ints[ii:]); ii = len(ints)
            elif ref and ref.lower() in tp:
                args.append(self.last_result)      # the RESULT REGISTER fills the carrier-typed param
            elif p.required:
                return None  # Mat/Vec/HV CONSTRUCTION stays out of scope (utterances can't safely build carriers)
        return args, kw

    # ---- handlers ----
    def _remember(self, text):
        self.mem.append(text)
        return "noted (%d items)" % len(self.mem)

    def _enc_note(self, text):
        # HYBRID note encoding (F1021 pre-measurement): token vecs + BYTEGLYPH vecs + order bigrams.
        # Adopted by the pre-committed rule (Gram +0.029 <= +0.05 budget; cross-language 2/2 --
        # 'water' finds the stored 'wota', 'education' finds 'edukesen'; controls unhurt).
        # NOTE-recall only: grounding stays token-exact (byteglyph was REJECTED there, F1017).
        ws = _toks(text)
        glyph = getattr(self.g.cs, "enc_mode", None) == "byteglyph"  # feature-detect: byteglyph
        parts = []                                                    # shipped in srmech 0.9.0rc28+;
        for w in ws:                                                  # on older floors the hybrid
            parts.append(self.g.vec(w))                               # degrades gracefully to
            if glyph:                                                 # token-only (cross-language
                parts.append(self.g.cs.enc(w))                        # spelling bridge unavailable)
        parts += self.g._bg(ws)
        return self.g.cs.bundle_odd(parts or [self.g.vec("_")])

    def _recall(self, text):
        if not self.mem:
            return "(memory empty)"
        qv = self._enc_note(text)
        return "recall: %s" % max(self.mem, key=lambda m: self.g.sim(qv, self._enc_note(m)))



    def _show(self, text=""):
        return "memory (%d): %s" % (len(self.mem), " | ".join(self.mem))

    def _define(self, text):
        s, n = self.g.ground(text, 1, owner="srmech")[0]
        return "%s: %s" % (n.split(".")[-1], (self.g.tools[n].summary or "")[:95])

    def _continue(self, text):
        # position-keyed context (F838) — the commutative-bind bag aliasing is exactly what this avoids
        hdc = self.g._hdc
        pairs = []
        for m in self.mem:
            ws = _toks(m)
            for i in range(2, len(ws)):
                pairs.append(hdc.klein4_bind(self.g.cs.encode_context(ws[i - 2:i]), self.g.vec(ws[i])))
        if not pairs:
            return "(no substrate content yet)"
        M = self.g.cs.bundle_odd(pairs)
        ws = _toks(text)
        if len(ws) < 2:
            return "(prefix too short)"
        probe = hdc.klein4_bind(M, self.g.cs.encode_context(ws[-2:]))
        vocab = sorted({w for m in self.mem for w in _toks(m)})
        return max(vocab, key=lambda w: self.g.sim(probe, self.g.vec(w)))

    def _help(self, text=""):
        from srmech.amsc import tool_schema as ts
        live = [t for t in ts.get_tool_schema().tools if t.owner == "siona"]  # LIVE = Class-H
        return "my commands (%d, from my live schema): %s" % (
            len(live), ", ".join(t.name.split(".")[-1] for t in live))

    # ---- the kernel-composed answer (F1012: exact-rational, stay-rational discipline) ----
    def _parse_kernel(self, m):
        ko, ws = self.board.kernel_ops, _toks(m)
        if ko["kernel"] not in ws:
            return None
        try:
            tgt = ws[ws.index(ko["kernel"]) + 1]
            src = ws[ws.index(ko["is"]) + 1]
            a = int(ws[ws.index(ko["times"]) + 1])
            b = int(ws[ws.index(ko["over"]) + 1])
            c = int(ws[ws.index(ko["plus"]) + 1])
            return (tgt, src, a, b, c)
        except (ValueError, IndexError):
            return None

    def _answer(self, text):
        from srmech.amsc import cyclic
        ws = _toks(text)
        qmark = next((w for w in ws if w in self.board.interrogatives), None)
        tgt = ws[ws.index(qmark) + 1] if qmark and ws.index(qmark) + 1 < len(ws) else None
        if not tgt:
            return "(no asked unit)"
        kern = next((k for k in (self._parse_kernel(m) for m in self.mem) if k and k[0] == tgt), None)
        if not kern:
            return "(no kernel for %s)" % tgt
        _, src, a, b, c = kern
        kw = self.board.kernel_ops["kernel"]
        facts = [m for m in self.mem if src in _toks(m) and kw not in _toks(m)
                 and any(w.isdigit() for w in _toks(m))]
        if not facts:
            return "(no %s fact)" % src
        q = " ".join(w for w in ws if w not in (qmark, tgt))
        fact = max(facts, key=lambda m: self.g.sim(self.g.enc_query(q), self.g.enc_query(m)))
        fws = _toks(fact)
        v = next((int(fws[i - 1]) for i, w in enumerate(fws)
                  if w == src and i > 0 and fws[i - 1].isdigit()), None)
        if v is None:
            return "(no %s value in the fact)" % src
        num, den = v * a + c * b, b                # EXACT rational; no floats mid-cascade
        g = cyclic.gcd(num, den)                   # srmech Class-I reduction
        num, den = num // g, den // g
        shown = str(num) if den == 1 else "%d/%d" % (num, den)
        self.mem.append("%s %s = %s %s (derived from: %s)" % (fact.split()[0], tgt, shown, tgt, fact))
        return ('%s %s (EXACT: (%d*%d + %d*%d)/%d = %d/%d, reduced via srmech gcd; '
                'from the fact "%s" through the kernel)') % (shown, tgt, v, a, c, b, b, num, den, fact)

    # ---- PERSISTENCE (the --persist context instrument; never-compacted, user-directed pruning only) ----
    STATE_FORMAT = "siona-session-state/1"

    def save_state(self, path):
        import json as _json
        with open(path, "w") as f:
            _json.dump({"format": self.STATE_FORMAT, "mem": self.mem,
                        "attestations": self.attestations, "learned_verbs": self.learned_verbs,
                        "instrument": list(self.instrument) if self.instrument else None}, f)

    def load_state(self, path):
        import json as _json
        import os
        if not os.path.isfile(path):
            return 0
        st = _json.load(open(path))
        if st.get("format") != self.STATE_FORMAT:
            return 0
        self.mem = st.get("mem", [])
        self.attestations = st.get("attestations", [])
        self.learned_verbs = st.get("learned_verbs", {})
        inst = st.get("instrument")
        if inst:
            self._impl["siona.knowledge.load"](inst[0])
        return len(self.mem)

    def _forget(self, text=""):
        # no arg: pop the last note. WITH an arg: SURGICAL GRAFT-OUT -- remove the best-matching
        # note on explicit request (user-directed removal is sovereignty, NOT compaction; F811's
        # never-compact ban is on AUTOMATIC truncation).
        if not self.mem:
            return "forgot: (empty)"
        if not text.strip():
            gone_i = len(self.mem) - 1
        else:
            qv = self._enc_note(text)
            gone_i = max(range(len(self.mem)),
                         key=lambda i: self.g.sim(qv, self._enc_note(self.mem[i])))
        gone = self.mem.pop(gone_i)
        kept = []
        for a in self.attestations:                            # re-index the MPR trail
            ni = a.get("note_index")
            if ni == gone_i:
                continue
            if ni is not None and ni > gone_i:
                a = dict(a); a["note_index"] = ni - 1
            kept.append(a)
        self.attestations = kept
        return "grafted out: %s" % gone[:70]

    def _purge(self, text=""):
        n = len(self.mem)
        self.mem = []
        self.attestations = []
        return "purged %d note(s) + their attestations (learned verbs kept; unlearn() per verb)" % n

    # ---- the KNOWLEDGE loop (F1024): acquire -> ATTEST (AMSC MPR) -> pack (Laplacian store) ----
    def _k_load(self, text):
        import os
        path = text.strip()
        if not os.path.isfile(path):
            return "(no instrument at %s)" % path
        index = path.replace("_instrument.ndjson", "_index.json")
        if not os.path.isfile(index):
            return "(no title index at %s)" % index
        from srmech.amsc.format import sha256_bytes
        with open(index, "rb") as f:
            self._instrument_hash = sha256_bytes(f.read())     # collector-descriptor hash, once per load
        self.instrument = (path, index)
        return "instrument loaded: %s (+ title index, sha256=%s). knowledge stays user-side; acquire <topic> to learn." % (
            os.path.basename(path), self._instrument_hash[:12])

    ACQUIRE_RULE = "lead = first 40 whitespace tokens of record['s'] at the indexed byte offset"

    def _k_acquire(self, text):
        if not self.instrument:
            return "(no instrument loaded -- 'load <path>' first)"
        import json as _json
        import datetime
        from dataclasses import asdict
        from srmech.amsc.format import (MPRRecord, sha256_bytes,
                                        validate_mpr_record)   # AMSC: the MPM crystallisation
        from . import bridge
        path, index = self.instrument
        topic = text.strip().lower()
        off = bridge._index(index).get(topic)
        if off is None:
            return "(topic %r not in the instrument)" % topic
        with open(path, "rb") as f:
            f.seek(off)
            raw = f.readline()
        rec = _json.loads(raw)
        lead = " ".join(rec["s"].split()[:40])                 # the lead = the acquirable fact-size read
        import srmech
        mpr = MPRRecord(
            mpr_version="1.0",
            data={"topic": topic, "lead": lead, "byte_offset": off},
            data_schema_id="siona://schema/acquired-lead/1",
            attestation={
                # a local instrument has no DOI; a SELF-DESCRIBING urn (never a fabricated
                # real-looking DOI) -- srmech precedent: pi_digits' labeled placeholder +
                # require_per_row_source_doi=false (record-level parity asked in UPSTREAM #84)
                "source_doi": "urn:siona:local-instrument:no-doi",
                "source_url": "file://" + path,
                "license": "CC-BY-SA-4.0",                     # Wikipedia-derived instrument
                "retrieved_at": datetime.datetime.now(datetime.timezone.utc)
                                .strftime("%Y-%m-%dT%H:%M:%SZ"),
                "response_sha256": sha256_bytes(raw),          # the EXACT record bytes (Class A)
                "parser_version": "srmech %s / siona" % srmech.__version__,
                "parser_rule_hash": sha256_bytes(self.ACQUIRE_RULE.encode()),
                "collector_descriptor_path": index,
                "collector_descriptor_hash": self._instrument_hash,
            },
            rendering={
                "human_readable_name": "simplewiki lead: %s" % topic,
                "cite_as": "Wikipedia contributors, %r, Simple English Wikipedia (CC-BY-SA)" % topic,
                "purpose": "knowledge note acquired into the siona session (attested per MPM)",
            })
        validate_mpr_record(mpr)                               # the REAL AMSC validation gate
        self.mem.append(lead)                                  # acquired knowledge enters working memory
        d = asdict(mpr)
        d["note_index"] = len(self.mem) - 1
        self.attestations.append(d)
        return "acquired %r: \"%s...\" [MPR-ATTESTED sha256=%s offset=%d]" % (
            topic, lead[:48], d["attestation"]["response_sha256"][:12], off)

    def _k_pack(self, text):
        if not self.attestations:
            return "(nothing acquired to pack)"
        import json as _json
        from srmech.amsc import text as stext, laplacian as L
        out = text.strip() or "siona_knowledge_pack.json"
        notes = [self.mem[a["note_index"]] for a in self.attestations]
        docs = [n.split() for n in notes]
        n, edges, weights = stext.cooccurrence_edges(docs, window=2, vocab_size=64)
        tf = {}
        for d in docs:
            for w in d:
                tf[w] = tf.get(w, 0) + 1
        vocab = [w for w, _ in sorted(tf.items(), key=lambda kv: (-kv[1], kv[0]))[:n]]
        Ln = L.normalized_laplacian(n, edges, weights)
        ev, V = L.mat_hermitian_eigendecompose(Ln)
        raw = ev.tolist() if hasattr(ev, "tolist") else list(ev)
        flat = ([raw[i][i] for i in range(len(raw))] if raw and isinstance(raw[0], list)
                and len(raw) == len(raw[0]) else
                [x for row in raw for x in row] if raw and isinstance(raw[0], list) else raw)
        evl = [float(getattr(x, "real", x)) for x in flat]     # display/persistence boundary
        Vl = V.tolist() if hasattr(V, "tolist") else V
        order = sorted(range(n), key=lambda k: evl[k])
        low = [k for k in order if evl[k] > 1e-9][:8]
        store = {"format": "siona-laplacian-pack/1", "vocab": vocab,
                 "eigvals": sorted(evl),
                 "low_modes": [[float(getattr(Vl[i][k], "real", Vl[i][k])) for k in low]
                               for i in range(n)],
                 "notes": notes, "attestations": self.attestations}
        with open(out, "w") as f:
            _json.dump(store, f)
        back = _json.load(open(out))                            # verify by reload
        ok = (back["vocab"] == vocab and len(back["eigvals"]) == n
              and len(back["attestations"]) == len(self.attestations))
        return ("packed %d attested note(s) -> %s (Laplacian store: %d-word vocab, %d low modes, "
                "%d eigvals; reload-verified=%s)") % (len(notes), out, n, len(low), n, ok)
