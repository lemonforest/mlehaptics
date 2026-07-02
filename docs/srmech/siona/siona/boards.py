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

__all__ = ["Board", "ENGLISH", "load_board"]


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

    def has_define(self, ws):
        return any(tuple(ws[: len(f)]) == f for f in self.define_frames)


ENGLISH = Board(
    name="english",
    address="siona",
    define_frames=(("what", "is"), ("what", "are"), ("define",), ("describe",),
                   ("meaning", "of"), ("tell", "me", "about"), ("who", "is"),
                   ("who", "was"), ("explain",)),
    self_verbs=frozenset({"remember", "recall", "forget", "ingest", "save", "show"}),
    verb_tools={"remember": "siona.memory.remember", "ingest": "siona.memory.remember",
                "save": "siona.memory.remember", "recall": "siona.memory.recall",
                "forget": "siona.memory.forget", "show": "siona.memory.show"},
    imperatives=frozenset({"list", "compute", "calculate", "run", "apply", "register",
                           "enumerate", "build", "generate", "encode", "decode",
                           "measure", "verify", "hash"}),
    interrogatives=frozenset({"what", "who", "when", "where", "how", "why"}),
    # NOTE: 'the' is NOT stripped — remembered notes store the FULL text (no doctoring the
    # SSoT, F982; high-frequency tokens are the continuation walk's curvature, F849/F853).
    strip=frozenset({"siona", "remember", "recall", "forget", "ingest", "save", "show",
                     "define", "continue", "list", "help", "that", "your", "please"}),
    kernel_ops={"kernel": "kernel", "is": "is", "times": "times", "over": "over", "plus": "plus"},
)


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
    )
