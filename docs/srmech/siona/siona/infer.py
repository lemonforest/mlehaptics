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
        return sorted(sc, reverse=True)[:k]


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
        T("siona.memory.forget", "Forget the most recent note: pop the last item from siona's working memory."),
        T("siona.memory.show", "Show the working memory: list every stored note and driven result in order."),
        T("siona.read.define", "Define a concept: depth-read the srmech tool catalog and return the best definition summary for the query."),
        T("siona.read.continue_text", "Continue a text prefix: substrate next-token read from siona's remembered content."),
        T("siona.introspect.help", "List siona's own commands: enumerate the siona tool schema from the live registry (self-introspection, Class H). Serves asks like: what can you do, what are you able to do, list your commands, help."),
        T("siona.read.answer", "Answer a question from remembered knowledge: compose recalled facts with ingested unit-conversion kernels to derive the asked value exactly (celsius to fahrenheit and similar unit questions)."),
    ])


class Session:
    """A multi-turn grounded inference session (F1012): one loop, both surfaces, one memory."""

    def __init__(self, board: Board = ENGLISH, D=8192):
        self.board = board
        self.mem = []  # never compacted; grows for the life of the session
        _register_self_tools()
        self.g = Grounding(D=D)
        self._impl = {
            "siona.memory.remember": self._remember, "siona.memory.recall": self._recall,
            "siona.memory.forget": self._forget, "siona.memory.show": self._show,
            "siona.read.define": self._define, "siona.read.continue_text": self._continue,
            "siona.introspect.help": self._help, "siona.read.answer": self._answer,
        }

    # ---- router (F1010: declared operators + operand shape; continue = the default) ----
    def _operands(self, u):
        ints = [int(x) for x in re.findall(r"-?\d+", u)]
        m = re.search(r"(?:bytes|string|text)\s+[\"']?([a-z]{2,})[\"']?\s*$", u.lower())
        return ints, (m.group(1).encode() if m else None)

    def route(self, u):
        b, ws = self.board, _toks(u)
        if ws and (ws[0] == b.address or ws[0] in b.self_verbs):
            return "self-command"
        ints, byts = self._operands(u)
        if b.has_define(ws) and not (ints or byts):
            return "define"
        if ints or byts:
            return "tool-call"  # operand shape = strong evidence (F1009)
        if ws and ws[0] in b.imperatives:
            return "tool-call"
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
        lead = ws[1] if ws and ws[0] == b.address and len(ws) > 1 else (ws[0] if ws else "")
        if lead in b.verb_tools:
            pick = b.verb_tools[lead]
        else:  # verb-less ask -> ground by meaning; interrogatives are intent-operators, stripped
            q = " ".join(w for w in ws if w != b.address and w not in b.interrogatives)
            pick = self.g.ground(q, 1, owner="siona")[0][1]
        return pick.split(".")[-1], self._impl[pick](self._rem(u))

    # ---- the drive loop (F1009 + F1012 cross-turn operand resolution) ----
    def _fit(self, t, ints, byts):
        pt = lambda p: p.type.lower().strip()
        reqs = [p for p in t.parameters if p.required]
        if not reqs:
            return 0.0
        intp = sum(1 for p in reqs if pt(p) == "int")
        bytp = sum(1 for p in reqs if "bytes" in pt(p))
        listp = sum(1 for p in reqs if any(k in pt(p) for k in ("list", "sequence", "tuple")))
        if len(reqs) - intp - bytp - listp:
            return 0.0
        if bytp and byts is None:
            return 0.0
        if listp:
            return 0.4 if ints else 0.0
        if intp > len(ints):
            return 0.0
        return 2.0 if (intp == len(ints) and (bytp > 0) == (byts is not None)) else 1.0

    def _drive_tool(self, u):
        ints, byts = self._operands(u)
        cands = [n for _, n in self.g.ground(u, 5, owner="srmech")]
        resolved = ""
        if all(self._fit(self.g.tools[n], ints, byts) == 0.0 for n in cands) and self.mem:
            # cross-turn operand resolution: the utterance under-supplies -> recall the referenced note
            kw = self.board.kernel_ops["kernel"]
            topname = self.g._nm[cands[0]]
            q = " ".join(w for w in _toks(u) if not w.isdigit()
                         and w not in self.board.imperatives and w not in topname
                         and w not in ("of", "the", "and"))
            note = max((m for m in self.mem if kw not in _toks(m)), default=None,
                       key=lambda m: self.g.sim(self.g.enc_query(q), self.g.enc_query(m)))
            if note:
                mem_ints = [int(w) for w in _toks(note) if w.isdigit()]
                ints = mem_ints[:1] + ints
                resolved = ' [operand %s resolved from: "%s"]' % (mem_ints[:1], note)
        scored = sorted(((self._fit(self.g.tools[n], ints, byts), -cands.index(n), n)
                         for n in cands), reverse=True)
        pick = scored[0][2] if scored[0][0] > 0 else cands[0]
        parts = pick.split(".")
        fn = None
        for i in range(len(parts), 0, -1):
            try:
                obj = importlib.import_module(".".join(parts[:i]))
                for p in parts[i:]:
                    obj = getattr(obj, p)
                fn = obj
                break
            except (ImportError, AttributeError):
                continue
        args, ii = [], 0
        for p in self.g.tools[pick].parameters:
            tp = p.type.lower().strip()
            if not p.required and ii >= len(ints):
                break
            if "bytes" in tp:
                args.append(byts)
            elif tp == "int":
                args.append(ints[ii]); ii += 1
            elif any(k in tp for k in ("list", "sequence", "tuple")):
                args.append(ints[ii:]); ii = len(ints)
        try:
            res = fn(*args)
        except Exception as e:  # captured into memory; recovery loop = hardening backlog
            res = "ERR %s" % e
        self.mem.append("%s%s = %s" % (pick.split(".")[-1], tuple(args), res))
        return "%s%s = %s%s" % (pick.split(".")[-1], tuple(args), str(res)[:60], resolved)

    # ---- handlers ----
    def _remember(self, text):
        self.mem.append(text)
        return "noted (%d items)" % len(self.mem)

    def _recall(self, text):
        if not self.mem:
            return "(memory empty)"
        return "recall: %s" % max(
            self.mem, key=lambda m: self.g.sim(self.g.enc_query(text), self.g.enc_query(m)))

    def _forget(self, text=""):
        return "forgot: %s" % (self.mem.pop() if self.mem else "(empty)")

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
