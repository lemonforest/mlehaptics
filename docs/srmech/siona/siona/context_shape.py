"""siona.context_shape — the user's response-shape context as op(x)operand (F1091).

The user's key question: when a normally-CONCISE conversation hits one turn of "help me understand this better",
does that flip the WHOLE context into teaching mode? Answer: NO — because the context is op(x)operand, not flat.

  * the RUNNING context is the OPERAND — the user's persistent preference (verbosity/coherence, slowly learned).
  * the CURRENT turn is the OPERATOR — a momentary request that MODULATES the operand for THIS turn only.
  * ``shape(turn) = operator(operand)`` — a single "help me understand" gives a locally-verbose answer WITHOUT
    overwriting the running operand. Running-context + current-turn are ONE op(x)operand object, not two states
    to reconcile. Only if the modulation PERSISTS across turns does the operand slowly drift (learning).

This is the same op⊗operand cascade as everywhere else (F1061), and the effective value it returns IS the
terse↔descriptive coherence knob (F1075) — so the same dial drives storytelling↔problem-solving, teach↔answer,
and now running-preference↔current-request. Language couples to the USER, not privileged English (F1091).
"""
import unicodedata

try:
    from siona.introspect import TIERS
except Exception:                                              # keep importable stand-alone
    TIERS = {}

__all__ = ["ContextShape", "tier_of", "fold_accents"]


def fold_accents(s):
    """Accent-fold (F1091): ``epistēmē`` → ``episteme`` — so ancient terms match WITHOUT the marks a user won't
    type. The mark is a rendering nicety; the word is the same relationship (`[[user_stance_imaginary_does_not_mean_unreal]]`)."""
    return "".join(c for c in unicodedata.normalize("NFD", str(s)) if unicodedata.category(c) != "Mn").lower()


def tier_of(name):
    """Look up a learning tier by EITHER tongue, accent-insensitively (F1090/F1091): ``phronesis`` == ``phronēsis``
    == ``articulated`` all resolve. Returns ``(key, {ancient, modern, knows})`` or ``(None, None)``."""
    f = fold_accents(name)
    for key, d in TIERS.items():
        if f in {fold_accents(key), fold_accents(d.get("ancient", "")), fold_accents(d.get("modern", ""))}:
            return key, d
    for key, d in TIERS.items():                               # substring fall-back (e.g. 'techne' in 'techne·mimesis')
        if f and f in fold_accents(d.get("ancient", "")):
            return key, d
    return None, None


class ContextShape:
    """The user's response-shape context as op(x)operand (F1091). ``verbosity`` ∈ [0,1] is the coherence knob
    (F1075): 0 = terse/concise, 1 = expansive/teaching. The RUNNING value is the OPERAND (persistent); each
    ``shape(turn)`` applies the turn's OPERATOR locally and returns the EFFECTIVE knob for that turn — without
    flipping the operand. The operand only drifts (learns) when a modulation persists."""

    _TEACH = ("help me understand", "explain", "why", "teach", "in detail", "elaborate", "walk me through",
              "more detail", "i don't understand", "confused", "how does")
    _TERSE = ("just", "briefly", "concise", "short", "tldr", "quick", "one line", "in a word")

    def __init__(self, verbosity=0.4, learn=0.15):
        self.verbosity = float(verbosity)                     # the RUNNING operand (persistent preference)
        self.learn = float(learn)                             # how fast the operand drifts if a bias persists

    @classmethod
    def _operator(cls, turn_text):
        t = fold_accents(turn_text)
        if any(k in t for k in cls._TEACH):
            return +0.5                                       # a teaching request → local verbose boost
        if any(k in t for k in cls._TERSE):
            return -0.4
        return 0.0

    def shape(self, turn_text):
        """op(x)operand: return the EFFECTIVE verbosity for THIS turn (operator applied to the running operand),
        then let the operand drift only slowly toward the modulation (so one turn does NOT flip the context)."""
        op = self._operator(turn_text)
        effective = min(1.0, max(0.0, self.verbosity + op))   # LOCAL: what this turn gets
        self.verbosity = min(1.0, max(0.0, self.verbosity + self.learn * op))   # PERSISTENT: drifts only if repeated
        return effective
