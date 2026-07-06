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
from .context_shape import ContextShape as _ContextShape
from . import genome_store as _gstore

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
            return any(w == t or (len(t) >= 3 and w.startswith(t) and len(w) - len(t) <= 5)
                       for w in qt)  # cap 5 measured 2026-07-03: recovers hypotenuse->hypot;
                                     # cap-4 pool was empty, cap-5 pool exactly ['hypot']
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
        T("siona.knowledge.study", "Study a topic from the loaded instrument: acquire the FULL bounded article body (up to 400 tokens) as one attested note, so formulas and their verification anchors coexist."),
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
        self.ctx = _ContextShape()                # op(x)operand response-shape context (F1091)
        self.active_mode = ["balanced"]           # reply mode EXPRESSED from the context genome (F1095/F1097)
        self._build_context_genome()
        self._impl = {
            "siona.memory.remember": self._remember, "siona.memory.recall": self._recall,
            "siona.memory.forget": self._forget, "siona.memory.show": self._show,
            "siona.memory.purge": self._purge,
            "siona.read.define": self._define, "siona.read.continue_text": self._continue,
            "siona.introspect.help": self._help, "siona.read.answer": self._answer,
            "siona.knowledge.load": self._k_load, "siona.knowledge.acquire": self._k_acquire,
            "siona.knowledge.study": self._k_study, "siona.knowledge.pack": self._k_pack,
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

    # ---- the LIVE context genome (F1097: express() in s.turn) ----
    _TEACH_BIT, _TERSE_BIT = 0b01, 0b10

    def _build_context_genome(self):
        """Build the reply-MODE genome ONCE (F1095/F1097): 'balanced' always expresses; 'teaching' is gated by
        the TEACH condition, 'concise' by TERSE. The conversation's op(x)operand verbosity (F1091) becomes the
        epigenetic ``cell_state``, so ``gene_express`` selects the active reply mode LIVE in :meth:`turn` — the
        same coherence knob (F1075) realized as genome expression (SAME genome, DIFFERENT cell_state → DIFFERENT mode)."""
        genes = [
            ("balanced", list(self.g.enc_query("balanced measured reply"))),
            ("teaching", list(self.g.enc_query("verbose teaching explanation reasons why")), self._TEACH_BIT),
            ("concise", list(self.g.enc_query("terse concise brief short answer")), self._TERSE_BIT),
        ]
        self._ctx_genome, self._ctx_one = _gstore.build_genome(genes)

    def _express_mode(self, u):
        """Derive the ``cell_state`` from the op(x)operand context and EXPRESS the active reply mode (F1097) —
        the gene_express op⊗operand theorem, live: SAME genome, DIFFERENT cell_state → DIFFERENT expressed mode."""
        eff = self.ctx.shape(u)                   # effective verbosity for THIS turn (running operand + operator)
        cs = self._TEACH_BIT if eff > 0.6 else (self._TERSE_BIT if eff < 0.35 else 0)
        self.active_mode = list(_gstore.express(self._ctx_genome, cs, the_one=self._ctx_one))
        return self.active_mode

    def turn(self, u):
        """Route + dispatch one utterance; returns (intent, tag, output). The reply MODE is expressed LIVE from
        the context genome per the turn's ``cell_state`` (F1097 — ``express()`` in ``s.turn``)."""
        self._express_mode(u)                     # LIVE context genome: op(x)operand cell_state -> reply mode
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
            hits = self.g.ground(q, 5, owner="siona")
            if any(w in b.interrogatives for w in ws):
                # A QUESTION IS A READ: never ground a wh-marked utterance to a write/act
                # tool (caught live: 'april has how many days' -> remember stored the
                # question as a fact; 'chess ... how many players' -> knowledge.load).
                # And a question whose CONTENT words appear in a memory note is a CONTENT
                # question -> recall (caught live: define/continue outranked recall on
                # summary noise while the acquired note held the answer).
                cov = lambda a, c: (a == c or (min(len(a), len(c)) >= 3
                                    and (a.startswith(c) or c.startswith(a))
                                    and len(a) - len(c) in range(-4, 5)))
                content = [w for w in ws if w not in b.interrogatives
                           and w != b.address and w not in b.strip]
                if any(any(cov(w, m) for m in _toks(note))
                       for note in self.mem for w in content):
                    hits = [(1.0, "siona.read.answer")]  # answer derives when a kernel
                                                          # composes; misses fall back to
                                                          # the cited recall inside _answer
                else:
                    READS = ("siona.memory.recall", "siona.memory.show", "siona.read.",
                             "siona.introspect.", "siona.dictionary.")
                    hits = [h for h in hits
                            if any(h[1] == r or h[1].startswith(r) for r in READS)]
            pick = hits[0][1] if hits else "siona.memory.recall"
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
            if raw and raw[0].lower() in ("load", "acquire", "learn", "pack", "study"):
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

    def _ladder(self):
        if getattr(self, "_ladder_cache", None) is None:
            try:
                from srmech.amsc.carrier_ladder import carrier_ladder_descriptor
                self._ladder_cache = carrier_ladder_descriptor()
            except Exception:
                self._ladder_cache = {"carriers": {}, "ladders": {}}
        return self._ladder_cache

    def _accepts(self, tp):
        # the carrier type-names a param accepts (a union 'BiPoly | TriPoly' -> both); case-insensitive
        # because _bind_args lowercases the param type but the descriptor keys are original-case
        return [c for c in self._ladder().get("carriers", {}) if re.search(r"\b%s\b" % c, tp, re.I)]

    CD_NAMES = {"real": 1, "complex": 2, "quaternion": 4, "octonion": 8, "sedenion": 16}

    def _cd_rung(self, obj):
        """The register's Cayley-Dickson rung = its LENGTH (R1/C2/H4/O8/S16), if it is a numeric
        sequence of power-of-two length ≤ 16. Unlike the poly ladder (rung = type), the cd rung is
        the dimension, so type(obj).__name__ ('tuple'/'list') carries no rung -- length does."""
        if isinstance(obj, (list, tuple)) and 1 <= len(obj) <= 16 and (len(obj) & (len(obj) - 1)) == 0:
            try:
                for e in obj:
                    complex(e)
                return len(obj)
            except (TypeError, ValueError):
                return None
        return None

    def _ops_contract(self):
        """#1254 (rc120): the DECLARED per-op carrier contract -- ops[short] = {consumes/produces rung}.
        This is what lets siona READ the rung instead of name-mapping 'octonion'->8."""
        if getattr(self, "_ops_cache", None) is None:
            try:
                from srmech.amsc.carrier_ladder import carrier_ladder_descriptor
                self._ops_cache = carrier_ladder_descriptor().get("ops", {})
            except Exception:
                self._ops_cache = {}
        return self._ops_cache

    def _op_consume_rung(self, tool_name):
        # the consumer's fixed cd rung, READ from the contract (octonion_conjugate -> 8); None if 'any'/absent
        c = self._ops_contract().get(tool_name.split(".")[-1], {}).get("consumes", {})
        return c["rung"] if c.get("ladder") == "cayley_dickson" and isinstance(c.get("rung"), int) else None

    def _cd_target(self, tool_name, u=""):
        # the target Hurwitz rung: an EXPLICIT algebra word or 'to N' in the utterance wins (the user's
        # 'promote it to a sedenion' / 'to 16'), else the op's own ALGEBRA NAME (octonion == dim-8);
        # both are the descriptor's R/C/H/O/S label, not a guess
        toks = _toks(u)
        for i, w in enumerate(toks):
            if w in self.CD_NAMES:
                return self.CD_NAMES[w]
            if w == "to" and i + 1 < len(toks) and toks[i + 1].isdigit() \
                    and int(toks[i + 1]) in (1, 2, 4, 8, 16):
                return int(toks[i + 1])
        r = self._op_consume_rung(tool_name)    # #1254: READ the rung from the declared contract...
        if r is not None:
            return r
        low = tool_name.lower()                  # ...name-map CD_NAMES only as the pre-rc120 fallback
        for k, d in self.CD_NAMES.items():
            if k in low:
                return d
        return None

    def _cd_promote_ref(self, tool_name, u=""):
        """cd-ladder auto-promote (F1040/F1041): the register (a cd element) lifted to the op's rung
        via srmech cd_promote (duality-guarded downward projection stays srmech's -- siona only UP).
        For cd_promote/cd_project ITSELF the register binds AS-IS (the op does the lift; the target
        dim rides the utterance as a separate operand). Returns the sequence, or None if not a cd bind."""
        obj = self.last_result
        rung = self._cd_rung(obj)
        if rung is None:
            return None
        if tool_name.endswith("cd_promote") or tool_name.endswith("cd_project"):
            return list(obj)               # x binds as-is; the op performs the conversion
        tgt = self._cd_target(tool_name, u)
        if tgt is None or tgt < rung:      # no cd op named, or would need a downgrade -> not our bind
            return None
        if tgt == rung:
            return list(obj)               # dims already match -- bind as-is
        from srmech.amsc.cascade import cd_promote    # rung -> tgt (one call handles multi-rung)
        return list(cd_promote(list(obj), tgt))

    def _promote_ref(self, tp):
        """The register AS a conversion ladder (F1039): if a param accepts a carrier that the
        register's carrier can be PROMOTED to (same ladder, higher rung), lift it and return the
        promoted carrier; if it matches directly, return as-is; else None. Duality-guarded
        projection is srmech's; siona only ever promotes UP (never guesses a downward realify)."""
        obj = self.last_result
        if obj is None:
            return None
        src = type(obj).__name__
        if re.search(r"\b%s\b" % re.escape(src), tp, re.I):   # DIRECT match (any carrier,
            return obj                                          # incl. non-ladder Mat/UnaryTheta/Vec/HV)
        L = self._ladder()
        cars, lads = L.get("carriers", {}), L.get("ladders", {})
        want = self._accepts(tp)
        if src not in cars:                  # not a ladder carrier and no direct match -> can't route
            return None
        my = cars[src]
        for tgt in want:                     # a higher rung on the SAME ladder -> promote up
            t = cars.get(tgt, {})
            if t.get("ladder") == my["ladder"] and t["rung"] > my["rung"]:
                import importlib
                fq = lads[my["ladder"]]["promote"]
                mod, fn = fq.rsplit(".", 1)
                promote = getattr(importlib.import_module(mod), fn)
                cur = obj
                for _ in range(t["rung"] - my["rung"]):   # one rung per call
                    cur = promote(cur)
                return cur
        return None

    def _named_params(self, t, u):
        """Utterance-named scalar params ('with 10 terms' / 'terms 10') -- shared by bind AND fit
        (a named optional param CONSUMES an operand, so it counts in the exactness accounting)."""
        named, ul = {}, u.lower()
        for p in t.parameters:
            if any(k in p.type.lower() for k in ("list", "tuple", "sequence", "bytes")):
                continue  # named extraction is for SCALAR params only ('edges 0-1' must not match edges=0)
            nm = re.escape(p.name.lower())
            if p.type.lower().strip() == "str":
                m = re.search(r"\b%s\s+([a-z][a-z0-9_]*)" % nm, ul)
                if m:
                    named[p.name] = m.group(1)
                continue
            m = (re.search(r"\b%s\s+(-?\d+(?:\.\d+)?)" % nm, ul)
                 or re.search(r"(-?\d+(?:\.\d+)?)\s+%s\b" % nm, ul))
            if m:
                named[p.name] = m.group(1)
        return named

    def _fit(self, t, ints, fls, byts, edges=(), ref=None, u=""):
        pt = lambda p: p.type.lower().strip()
        t_name = getattr(t, "name", "")
        reqs = [p for p in t.parameters if p.required]
        if not reqs:
            return 0.0
        named = self._named_params(t, u) if u else {}
        strp = [p for p in reqs if pt(p) == "str"]
        if strp and not all(p.name in named for p in strp):
            return 0.0                          # a required str param binds by NAME or not at all
        reqs = [p for p in reqs if pt(p) != "str"]
        if not reqs and strp:
            return 2.0
        cd_bind = (ref and t_name and self._cd_rung(self.last_result) is not None
                   and (self._cd_target(t_name, u) is not None
                        or t_name.endswith("cd_promote") or t_name.endswith("cd_project"))
                   and any("hv" in pt(p) or any(k in pt(p) for k in ("sequence", "list")) for p in reqs))
        def ref_fits(p):
            tt = pt(p)
            if cd_bind and ("hv" in tt or any(k in tt for k in ("sequence", "list"))):
                return True                         # the cd element fills the Hurwitz operand
            if any(k in tt for k in ("list", "sequence", "tuple")):
                return False
            if ref and ref.lower() in tt:           # direct scalar-carrier-name match
                return True
            return bool(self._accepts(tt)) and self.last_result is not None \
                and self._promote_ref(tt) is not None    # promotable via the poly ladder
        ref_ids = {id(p) for p in reqs if ref and ref_fits(p)}
        refp = len(ref_ids)
        rest = [p for p in reqs if id(p) not in ref_ids]   # a ref-fit param is FILLED by the register,
        intp = sum(1 for p in rest if pt(p) == "int")      # so it is excluded from operand-type counts
        fltp = sum(1 for p in rest if pt(p) == "float")
        bytp = sum(1 for p in rest if "bytes" in pt(p))
        def scalar_union(p):   # 'float | Sequence[float]' with a scalar operand available -> SCALAR
            t = pt(p)
            return ("|" in t and ("float" in t or "int" in t)
                    and any(k in t for k in ("list", "sequence", "tuple"))
                    and bool(fls or ints))
        sun = [p for p in rest if scalar_union(p)]
        fltp = fltp + len(sun)  # the union's scalar alternative counts as a float slot
        listp = sum(1 for p in rest if any(k in pt(p) for k in ("list", "sequence", "tuple"))
                    and not scalar_union(p))
        if len(rest) - intp - fltp - bytp - listp:
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
        named_n = len(named)
        exact = (intp + fltp + named_n == len(ints) + len(fls)) and (bytp > 0) == (byts is not None)
        return 2.0 if exact else 1.0

    def _drive_tool(self, u):
        ints, fls, byts, edges = self._operands(u)
        ref = (type(self.last_result).__name__
               if self.last_result is not None
               and any(w in self.REF_WORDS for w in _toks(u)) else None)
        cands = [n for _, n in self.g.ground(u, 5, owner="srmech")]
        resolved = ""
        if all(self._fit(self.g.tools[n], ints, fls, byts, edges, ref, u) == 0.0 for n in cands) and self.mem:
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
        scored = sorted(((self._fit(self.g.tools[n], ints, fls, byts, edges, ref, u), -cands.index(n), n)
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
        named = self._named_params(self.g.tools[pick], u)
        fq = list(fls)
        args, kw, ii = [], {}, 0
        for p in self.g.tools[pick].parameters:
            tp = p.type.lower().strip()
            if p.name in named:
                v = named[p.name]
                kw[p.name] = (v if tp == "str"
                              else float(v) if tp == "float" else int(float(v)))  # by NAME (kw-only safe)
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
                    if p.name == "dim" and pick.endswith("cd_promote"):   # 'to a sedenion' -> 16
                        d = self._cd_target(pick, u)
                        if d is not None:
                            args.append(d); continue
                    return None
                args.append(ints[ii]); ii += 1
            elif ("|" in tp and ("float" in tp or "int" in tp) and (fq or ii < len(ints))):
                if fq:                             # scalar-union ('float | Sequence[float]') -> SCALAR
                    num, den = fq.pop(0); args.append(float(num) / float(den))
                else:
                    args.append(float(ints[ii])); ii += 1
            elif (ref and ("hv" in tp or any(k in tp for k in ("sequence", "list")))
                  and self._cd_rung(self.last_result) is not None
                  and (self._cd_target(pick, u) is not None
                       or pick.endswith("cd_promote") or pick.endswith("cd_project"))):
                seq = self._cd_promote_ref(pick, u)  # cd-ladder auto-promote UP (BEFORE the int-list fill:
                if seq is None:                       # a cd element in the register wins the sequence param)
                    return None
                args.append(seq)
            elif any(k in tp for k in ("list", "sequence", "tuple")):
                if edges and "tuple" in tp:
                    args.append(list(edges))       # EDGE-PAIR operands -> Iterable[Tuple[int,int]] params
                else:
                    args.append(ints[ii:]); ii = len(ints)
            elif ref and (ref.lower() in tp or self._accepts(tp)):
                promoted = self._promote_ref(tp)   # the register AS a conversion ladder (auto-promote UP)
                if promoted is None:
                    return None
                args.append(promoted)
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

    def _cite(self, i):
        for a in self.attestations:
            if a.get("note_index") == i:
                return " [attested: %s | sha256=%s]" % (
                    a["rendering"]["cite_as"], a["attestation"]["response_sha256"][:12])
        return ""

    def _compare(self, text):
        """MULTI-NOTE SYNTHESIS (the F774 compare op over attested notes): a comparative frame
        names a unit and >=2 topics; each topic resolves to ITS note (attestation topic first --
        month articles mention neighbor months, so token-presence alone mis-pairs), the unit's
        value extracts per-note by the same adjacency read, and the verdict is an EXACT integer
        compare. Misses fall to extraction -> recall."""
        b = self.board
        ws = _toks(text)
        unit = next((ws[i + 1] for i, w in enumerate(ws)
                     if w in b.comparison_words and i + 1 < len(ws)), None)
        if not unit or not self.mem:
            return self._extract(text)
        cov = lambda a, c: (a == c or (min(len(a), len(c)) >= 3
                            and (a.startswith(c) or c.startswith(a))
                            and len(a) - len(c) in range(-4, 5)))
        by_topic = {a["data"]["topic"]: a["note_index"] for a in self.attestations
                    if "data" in a and "topic" in a.get("data", {})}
        found = {}
        for t in ws:
            ni = by_topic.get(t)
            if ni is None:                      # unattested notes: first-token identity only
                ni = next((i for i, n in enumerate(self.mem)
                           if _toks(n) and _toks(n)[0] == t), None)
            if ni is None or t in found:
                continue
            nt = _toks(self.mem[ni])
            for j, w in enumerate(nt):
                if cov(w, unit):
                    for k in (j - 1, j - 2):
                        if k >= 0 and nt[k].isdigit():
                            found[t] = (int(nt[k]), ni)
                            break
                    if t in found:
                        break
        if len(found) < 2:
            return self._extract(text)
        ranked = sorted(found.items(), key=lambda kv: -kv[1][0])
        low_side = any(w in ("fewer", "less", "fewest", "shorter", "smaller") for w in ws)
        winner = ranked[-1][0] if low_side else ranked[0][0]
        parts = " vs ".join("%s: %d %s%s" % (t, v, unit, self._cite(ni)) for t, (v, ni) in ranked)
        return "%s -- exact integer compare: %s" % (winner, parts)

    def _best_note(self, text):
        qv = self._enc_note(text)
        best_i = max(range(len(self.mem)),
                     key=lambda i: self.g.sim(qv, self._enc_note(self.mem[i])))
        cite = ""
        for a in self.attestations:            # an attested note answers WITH its provenance
            if a.get("note_index") == best_i:
                cite = " [attested: %s | sha256=%s]" % (
                    a["rendering"]["cite_as"], a["attestation"]["response_sha256"][:12])
                break
        return best_i, cite

    def _source_filter(self, text):
        """SOURCE-QUALIFIED selection: 'per <src>' restricts recall to notes whose attestation
        names that source (cite_as substring, declared marker, no thresholds). Returns
        (note-index set or None, the text with the qualifier consumed)."""
        ws = text.split()
        b = self.board
        for i, w in enumerate(ws):
            if w.lower() in b.source_markers and i + 1 < len(ws):
                src = ws[i + 1].lower()
                hits = {a["note_index"] for a in self.attestations
                        if src in a.get("rendering", {}).get("cite_as", "").lower()}
                if hits:
                    rest = " ".join(ws[:i] + ws[i + 2:])
                    return hits, rest
                return None, text          # marker present, no attested source -> unfiltered
        return None, text

    def _recall(self, text):
        if not self.mem:
            return "(memory empty)"
        only, text = self._source_filter(text)
        if only is not None:
            qv = self._enc_note(text)
            best_i = max(only, key=lambda i: self.g.sim(qv, self._enc_note(self.mem[i])))
            return "recall: %s%s" % (self.mem[best_i], self._cite(best_i))
        best_i, cite = self._best_note(text)
        out = "recall: %s%s" % (self.mem[best_i], cite)
        # THE CONFLICT SURFACE (F1028 §4 v1): a second note sharing >=2 content words whose
        # attestation names a DIFFERENT source is a PARALLEL SENSE -- reported, never deleted
        # (dual senses survive as structure, the F1006->F1007->rc105 chain at the source level).
        srcs = {a.get("note_index"): a["attestation"].get("source_url", "")
                for a in self.attestations if "attestation" in a}
        s0 = srcs.get(best_i)
        if s0:
            qw = [w for w in _toks(text) if w not in self.board.strip
                  and w not in self.board.interrogatives]
            for j, note in enumerate(self.mem):
                if j != best_i and srcs.get(j) and srcs[j] != s0:
                    if sum(1 for w in set(qw) if w in _toks(note)) >= 2:
                        jc = self._cite(j)
                        out += "\n  PARALLEL SOURCE (differs): %s...%s" % (note[:100], jc)
                        break
        return out

    def _extract(self, text):
        """The F774 closed-op SUB-NOTE EXTRACTION rung: the wh-frame declares the answer's
        SHAPE (a number/ordinal + the asked unit); extraction is a Class-D pattern-match +
        adjacency read over the best attested note -- never generation. Any miss falls to
        the cited whole-note recall (the honest floor)."""
        b = self.board
        if not self.mem or not b.numwords:
            return self._recall(text)
        ws = _toks(text)
        qmark = next((w for w in ws if w in b.interrogatives), None)
        tgt = ws[ws.index(qmark) + 1] if qmark and ws.index(qmark) + 1 < len(ws) else None
        if tgt in b.quantity_words:
            i = ws.index(qmark) + 2
            tgt = ws[i] if i < len(ws) else None
        if not tgt:
            return self._recall(text)
        best_i, cite = self._best_note(text)
        nt = _toks(self.mem[best_i])
        cov = lambda a, c: (a == c or (min(len(a), len(c)) >= 3
                            and (a.startswith(c) or c.startswith(a))
                            and len(a) - len(c) in range(-4, 5)))
        spans = []
        for j, w in enumerate(nt):
            if cov(w, tgt):
                for k in (j - 1, j - 2):       # the modifier sits just before the unit
                    if k >= 0 and (nt[k].isdigit() or nt[k] in b.numwords):
                        spans.append((" ".join(nt[k:j + 1]),
                                      " ".join(nt[max(0, k - 3):j + 3])))
                        break
        if not spans:
            return self._recall(text)          # no answering span -> the honest whole-note floor
        ans, ctx = spans[0]
        more = " (+%d more span%s in the note)" % (len(spans) - 1,
                "s" if len(spans) > 2 else "") if len(spans) > 1 else ""
        return '%s%s -- extracted from: "...%s..."%s' % (ans, more, ctx, cite)



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

    WIKI_KERNEL = re.compile(  # the attested conversion shape in RAW note text (markup-stripped
        # simplewiki): '<tgtword> is <L1> <A> <B> x <L2> <K>' == TGT = A/B * (SRC - K).
        # Single-letter units survive in raw notes (only _toks drops them).
        r"\b([a-z]+) is ([a-z]) (\d+) (\d+) x ([a-z]) (\d+)\b")

    def _wiki_kernel(self, tgt):
        """Find an ATTESTED conversion kernel in acquired notes (preferred over session-ingested:
        attestation beats hand-typed, MPM). Returns (a, b, c, src_word, note_i) for
        TGT = (a*src + c*b)/b -- the exact-rational inversion of 'other = A/B*(TGT - K)' when the
        asked target sits on the SRC side -- plus K self-VERIFIED against the note's own anchor."""
        for i, note in enumerate(self.mem):
            m = self.WIKI_KERNEL.search(note)
            if not m:
                continue
            other, A, B, K = m.group(1), int(m.group(3)), int(m.group(4)), int(m.group(6))
            topic = next((a["data"]["topic"] for a in self.attestations
                          if a.get("note_index") == i and "data" in a), None)
            if not topic:
                continue
            # self-verify K against the same note's anchor fact ('freezes at 32 f'): the offset
            # constant must appear as an attested anchor value, else the parse is rejected.
            if not re.search(r"\b%d %s\b" % (K, m.group(5)), note):
                continue
            if tgt.startswith(topic[:4]) or topic.startswith(tgt[:4]):
                # asked the SRC side: invert other = A/B*(tgt - K)  ->  tgt = B/A*other + K
                return B, A, K, other, i
            if tgt.startswith(other[:4]) or other.startswith(tgt[:4]):
                # asked the TGT side as written: tgt = A/B*src - A/B*K  (c*b form: -K*A over B)
                return A, B, -K * A // B if (K * A) % B == 0 else None, topic, i
        return None

    def _answer(self, text):
        from srmech.amsc import cyclic
        ws = _toks(text)
        if any(w in self.board.comparison_words for w in ws):
            return self._compare(text)          # multi-note synthesis (F774 compare op)
        qmark = next((w for w in ws if w in self.board.interrogatives), None)
        tgt = ws[ws.index(qmark) + 1] if qmark and ws.index(qmark) + 1 < len(ws) else None
        if tgt in self.board.quantity_words:           # 'how MANY days' -> the unit is next
            i = ws.index(qmark) + 2
            tgt = ws[i] if i < len(ws) else None
        if not tgt:
            return self._extract(text)  # honest miss -> extraction tier -> cited recall
        wk = self._wiki_kernel(tgt)                    # attestation beats hand-typed (MPM)
        if wk and wk[2] is not None:
            a, b, c, src, kn_i = wk
        else:
            kern = next((k for k in (self._parse_kernel(m) for m in self.mem) if k and k[0] == tgt),
                        None)
            if not kern:
                return self._extract(text)  # honest miss -> extraction tier -> cited recall
            _, src, a, b, c = kern
            kn_i = None
        kw = self.board.kernel_ops["kernel"]
        facts = [m for m in self.mem if src in _toks(m) and kw not in _toks(m)
                 and any(w.isdigit() for w in _toks(m))]
        if not facts:
            return self._extract(text)  # honest miss -> extraction tier -> cited recall
        q = " ".join(w for w in ws if w not in (qmark, tgt))
        fact = max(facts, key=lambda m: self.g.sim(self.g.enc_query(q), self.g.enc_query(m)))
        fws = _toks(fact)
        v = next((int(fws[i - 1]) for i, w in enumerate(fws)
                  if w == src and i > 0 and fws[i - 1].isdigit()), None)
        if v is None:
            return self._extract(text)  # honest miss -> extraction tier -> cited recall
        num, den = v * a + c * b, b                # EXACT rational; no floats mid-cascade
        g = cyclic.gcd(num, den)                   # srmech Class-I reduction
        num, den = num // g, den // g
        shown = str(num) if den == 1 else "%d/%d" % (num, den)
        self.mem.append("%s %s = %s %s (derived from: %s)" % (fact.split()[0], tgt, shown, tgt, fact))
        prov = ""
        if kn_i is not None:                           # the kernel came from an ACQUIRED note
            prov = " via the kernel acquired from the attested note%s" % self._cite(kn_i)
            if den == 1 and re.search(r"\b%d [a-z]\b" % num, self.mem[kn_i]):
                prov += "; independently CONFIRMED by the article's own anchor value %d" % num
        return ('%s %s (EXACT: (%d*%d + %d*%d)/%d = %d/%d, reduced via srmech gcd; '
                'from the fact "%s"%s)') % (shown, tgt, v, a, c, b, b, num, den, fact,
                                            prov or " through the kernel")

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
        meta = path.replace("_instrument.ndjson", "_instrument.meta.json")  # per-instrument source
        if os.path.isfile(meta):                                            # metadata (license,
            import json as _json                                            # cite-as) -- an
            self._instrument_meta = _json.load(open(meta))                  # instrument declares
        else:                                                               # its OWN provenance
            self._instrument_meta = {"license": "CC-BY-SA-4.0",
                                     "cite_as": "Wikipedia contributors, %r, Simple English Wikipedia (CC-BY-SA)",
                                     "name": "simplewiki"}
        self.instrument = (path, index)
        return "instrument loaded: %s (+ title index, sha256=%s). knowledge stays user-side; acquire <topic> to learn." % (
            os.path.basename(path), self._instrument_hash[:12])

    ACQUIRE_RULE = "lead = first 40 whitespace tokens of record['s'] at the indexed byte offset"

    def _k_study(self, text):
        return self._k_acquire(text, window=400)   # full bounded body -- the kernel AND its
                                                    # verification anchors coexist in one note

    def _k_acquire(self, text, window=40):
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
        lead = " ".join(rec["s"].split()[:window])             # the lead = the acquirable read
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
                "license": self._instrument_meta["license"],
                "retrieved_at": datetime.datetime.now(datetime.timezone.utc)
                                .strftime("%Y-%m-%dT%H:%M:%SZ"),
                "response_sha256": sha256_bytes(raw),          # the EXACT record bytes (Class A)
                "parser_version": "srmech %s / siona" % srmech.__version__,
                "parser_rule_hash": sha256_bytes(self.ACQUIRE_RULE.encode()),
                "collector_descriptor_path": index,
                "collector_descriptor_hash": self._instrument_hash,
            },
            rendering={
                "human_readable_name": "%s: %s" % (self._instrument_meta["name"], topic),
                "cite_as": self._instrument_meta["cite_as"] % topic,
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
