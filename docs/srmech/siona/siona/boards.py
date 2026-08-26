"""siona.boards — the language-BOARD layer (PKG-1; F649 / R-RBS-LM-54 Rosetta architecture).

A *board* is a per-language **declared operator profile**: the closed-class intent markers (address,
self-verbs, define/interrogative frames, imperatives, kernel operator slots) a router needs to route
utterances in that language. **Content never lives here** — operators are declared (reserved keywords
per language, `feedback_operators_declared_operands_by_meaning`); operands route by *meaning* on the
byte/glyph substrate (srmech ``ContextSubstrate`` ``enc_mode='byteglyph'``, script-agnostic).

**English is board #1, not the architecture** (R-RBS-LM-25 extended: the operator lexicons are
per-language profiles too). The shared-invariant IR *above* boards is the Rosetta layer — the
architecture ni-Vanuatu sand drawing instantiates as a living ~80-language exemplar (F649).
Dignity-first: the lineage reaches this package as an attested structural exemplar and a pointer to
the living tradition — the content is held by the Ni-Vanuatu community; it is never shipped as data.
"""
from dataclasses import dataclass

__all__ = ["Board", "ENGLISH", "load_board", "merge_boards"]


@dataclass(frozen=True)
class Board:
    """A per-language declared operator profile (swappable; the router runs unchanged)."""
    name: str
    address: str                 # the agent-address token ("siona ..." on the English board)
    define_frames: tuple         # token-tuples: define/interrogative operator frames (utterance-initial)
    self_verbs: frozenset        # self-command verbs (deterministic dispatch to the siona self surface)
    verb_tools: dict             # self-verb -> registered siona tool name (the deterministic layer)
    imperatives: frozenset       # no-operand tool-call verbs (utterance-initial)
    interrogatives: frozenset    # intent-operators stripped from GROUNDING queries (handlers still get them)
    strip: frozenset             # operator/filler tokens stripped from handler text arguments
    kernel_ops: dict             # declared linear-map kernel slots: keys kernel/is/times/over/plus -> board words
    homographs: dict = None
    quantity_words: frozenset = frozenset()  # 'how MANY days' -- the unit follows the quantity word
    numwords: frozenset = frozenset()        # closed number/ordinal vocabulary (attested per board)
    comparison_words: frozenset = frozenset()  # 'which has MORE days' -- multi-note synthesis marker
    source_markers: frozenset = frozenset()    # 'PER mfo ...' -- source-qualified sense selection      # merged boards: verb -> ((board_name, tool), ...) -- SUPERPOSED senses (F1018)
    parents: tuple = ()          # merged boards: the parent boards; their operator vocabs drive the rung vote
    politeness: frozenset = frozenset()  # PARAPHRASE frames: politeness/hedge prefix tokens, stripped before routing

    def operator_vocab(self):
        # the board's declared operator surface -- drives the language-rung vote on merged boards (F1018)
        return (set(self.strip) | self.self_verbs | self.imperatives | self.interrogatives
                | {w for f in self.define_frames for w in f} | {self.address})

    def has_define(self, ws):
        return any(tuple(ws[: len(f)]) == f for f in self.define_frames)


ENGLISH = Board(
    name="english",
    address="siona",
    define_frames=(("what", "is"), ("what", "are"), ("define",), ("describe",),
                   ("meaning", "of"), ("tell", "me", "about"), ("who", "is"),
                   ("who", "was"), ("explain",)),
    self_verbs=frozenset({"remember", "recall", "forget", "ingest", "save", "show",
                          "load", "acquire", "learn", "pack", "purge", "study"}),
    politeness=frozenset({"please", "could", "would", "can", "you", "kindly", "hey"}),
    quantity_words=frozenset({"many", "much"}),
    comparison_words=frozenset({"more", "fewer", "less", "most", "fewest",
                                "longer", "shorter", "larger", "smaller", "bigger"}),
    source_markers=frozenset({"per"}),
    numwords=frozenset({  # the English closed number/ordinal class (linguistic, not tuned)
        "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
        "eleven", "twelve", "twenty", "thirty", "forty", "fifty", "hundred", "thousand",
        "first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth",
        "ninth", "tenth", "eleventh", "twelfth"}),
    verb_tools={"remember": "siona.memory.remember", "ingest": "siona.memory.remember",
                "save": "siona.memory.remember", "recall": "siona.memory.recall",
                "forget": "siona.memory.forget", "show": "siona.memory.show",
                "load": "siona.knowledge.load", "acquire": "siona.knowledge.acquire",
                "learn": "siona.knowledge.acquire", "pack": "siona.knowledge.pack", "purge": "siona.memory.purge",
                "study": "siona.knowledge.study"},
    imperatives=frozenset({"list", "compute", "calculate", "run", "apply", "register",
                           "enumerate", "build", "generate", "encode", "decode",
                           "measure", "verify", "hash"}),
    interrogatives=frozenset({"what", "who", "when", "where", "how", "why", "which", "whose"}),
    # NOTE: 'the' is NOT stripped — remembered notes store the FULL text (no doctoring the
    # SSoT, F982; high-frequency tokens are the continuation walk's curvature, F849/F853).
    strip=frozenset({"siona", "remember", "recall", "forget", "ingest", "save", "show",
                     "define", "continue", "list", "help", "that", "your", "please"}),
    kernel_ops={"kernel": "kernel", "is": "is", "times": "times", "over": "over", "plus": "plus"},
)


def merge_boards(a, b, name=None):
    """Merge two boards into a BILINGUAL (code-switching) profile — the union of the declared
    operator classes. Returns ``(board, conflicts)``.

    THE CONFLICT RULE (the framework's own principle extended to code-switching): when the two
    boards map the SAME verb to DIFFERENT tools (e.g. English ``save``->remember vs Bislama
    ``save``->recall, the attested homograph), the verb's dispatch is no longer deterministic —
    it is DROPPED from ``verb_tools`` (but kept in ``self_verbs`` so it still routes
    self-command) and falls through to grounding: **operators declared; when declarations
    collide, operands decide** (selection by meaning on the siona surface).
    """
    conflicts = {}
    vt = dict(a.verb_tools)
    for k, v in b.verb_tools.items():
        if k in vt and vt[k] != v:
            conflicts[k] = ((a.name, vt[k]), (b.name, v))   # SUPERPOSED senses (F1018): kept, rung-selected
            del vt[k]
        elif k not in vt:
            vt[k] = v
    board = Board(
        name=name or "%s+%s" % (a.name, b.name),
        address=a.address,
        define_frames=tuple(dict.fromkeys(a.define_frames + b.define_frames)),
        self_verbs=a.self_verbs | b.self_verbs,
        verb_tools=vt,
        imperatives=a.imperatives | b.imperatives,
        interrogatives=a.interrogatives | b.interrogatives,
        strip=a.strip | b.strip,
        kernel_ops=dict(a.kernel_ops),     # first board's kernel slots (documented choice)
        homographs=conflicts, parents=(a, b), politeness=a.politeness | b.politeness,
    )
    return board, conflicts


def load_board(path):
    """Load a per-language :class:`Board` from a TOML descriptor.

    The board-swap test (PKG-1 §testing): author a second-language descriptor and the router runs
    unchanged with the swapped profile — proving the English lexicon is a *profile*, not core.
    """
    import tomllib
    with open(path, "rb") as f:
        d = tomllib.load(f)
    b = d["board"]
    return Board(
        name=b["name"], address=b["address"],
        define_frames=tuple(tuple(x) for x in b["define_frames"]),
        self_verbs=frozenset(b["self_verbs"]), verb_tools=dict(b["verb_tools"]),
        imperatives=frozenset(b["imperatives"]), interrogatives=frozenset(b["interrogatives"]),
        strip=frozenset(b["strip"]), kernel_ops=dict(b["kernel_ops"]),
        politeness=frozenset(b.get("politeness", ())),
    )
