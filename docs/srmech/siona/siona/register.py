"""siona.register — classify a statement's KNOWLEDGE REGISTER (#252, F1098/F1099).

The register axis is richer than binary fact/fiction — three DISCRETE condition bits, plus one EMERGENT case
we must *find* (the user's four knowledge types):

    NARRATIVE (story-form)   ATTESTED (verifiable-true)   FORMAL (proof 'dress')
    ---------------------------------------------------------------------------
    FICTION  = NARRATIVE                                       a story, not claimed true
    FACT     =              ATTESTED                           attested non-fiction (empirical)
    MATH     =              ATTESTED            FORMAL          attested theory — SAME register as FACT, different DRESS
    PARABLE  = the EMERGENT case: couples to BOTH the NARRATIVE web AND the ATTESTED/lesson web —
               truth THROUGH metaphor (Aesop's fables, the prodigal son). It is NOT a clean bit; it EMERGES as a
               GRADED truth-content, and it must be FOUND — the coupling flags DUAL coherence, and here the k=2
               "not cohesive" signal (F1098) is the SIGNATURE, not an error.

**Genome header room (user question — abundant).** Discrete registers ride the ``0x67`` REGULATORY-GENE
activator/repressor mask (the register IS a cell_state gating condition — ``gene_express``, F1095; NO header
format change). The PARABLE's graded truth+metaphor mix rides the ``0x64`` GRADED-GENE — a rational expression
LEVEL in ``[0,1]`` (``gene_express_levels``): exactly the header room a mixed/emergent register needs. The
``0x4B`` kernel-header ``element_type`` ENUM is the precedent that declared classification already lives in the
header. So: discrete → regulatory activator bits; emergent/graded → the graded gene.

**Inference (the user's ask).** PRIMARY anchor = the attestation source-type (certain). FALLBACK for an
un-attested statement = couple-for-coherence (R-RBS-LM-250 Class-L shape) + a k=3 knowledge-kernel tie-break
(F291/F334 — k=2 detects, k=3 corrects): a CLEAN winner → a discrete register; a DUAL coherence (near-tie to the
narrative AND the attested side) → PARABLE, the emergence, a graded blend. Reported as a lean + honest DEGREE;
low degree → flag, never assert (F552). Register, not truth: Siona reports an attested register, not a verdict.

srmech-native: Class-M ``klein4_similarity`` coupling; Class-I integer register bits. numpy-free.
"""
import re as _re

from srmech.amsc import hdc as _hdc
from srmech.amsc import laplacian as _L

__all__ = ["classify", "classify_spectral", "coupling_coherence", "REGISTER_BITS",
           "NARRATIVE", "ATTESTED", "FORMAL", "DISCRETE"]

NARRATIVE, ATTESTED, FORMAL = 0b001, 0b010, 0b100
#: the DISCRETE registers as gene_express cell_state activator masks (0x67 regulatory gene)
DISCRETE = {"fiction": NARRATIVE, "fact": ATTESTED, "math": ATTESTED | FORMAL}
REGISTER_BITS = {"NARRATIVE": NARRATIVE, "ATTESTED": ATTESTED, "FORMAL": FORMAL}


def _web_coherence(qv, kernels, k):
    """How coherently a statement couples to one register's web = mean of its top-k klein4 similarities."""
    sims = sorted((_hdc.klein4_similarity(qv, kv).as_float() for kv in kernels), reverse=True)[:k]
    return round(sum(sims) / len(sims), 3) if sims else 0.0


def classify(statement, webs, grounder, *, k=3, dual_floor=0.18, balance_margin=0.06, undiff_band=0.05):
    """Classify a statement's knowledge register by coupling it to each register's web (F1099).

    ``webs``: ``{register: [exemplar kernels]}`` (the attested seed of each register). Returns a dict:
      * an UNDIFFERENTIATED coupling (all coherences within ``undiff_band``) → ``{"register": "undetermined"}``
        — the HONEST outcome when the measure cannot separate the registers (F552). MEASURED: the plain Class-M
        ``klein4_similarity`` coupling IS flat (~0.26 for every pair, spread ~0.02) → it CANNOT classify register;
        that is the F1099 falsification, and the reason the principled measure is the Class-L Laplacian spectral
        SHAPE (R-RBS-LM-250) + the k=3 knowledge-kernel tie-break, NOT surface similarity.
      * a CLEAN discrete winner → ``{"register": <fiction|fact|math>, "emergent": False, "degree": …}``.
      * DUAL coherence (narrative-side AND attested-side both genuinely ≥ ``dual_floor`` and within
        ``balance_margin``) → ``{"register": "parable", "emergent": True, "graded": <balance in [0,1]>}`` — the
        FOUND emergence (truth through metaphor; the 0x64 graded-gene case). Only fires on a DIFFERENTIATING
        signal, never on a flat one.
    ``degree`` = the top-vs-second coherence margin; low ⇒ honest "don't know", not an assertion (F552)."""
    qv = grounder.enc_query(statement)
    coh = {reg: _web_coherence(qv, kernels, k) for reg, kernels in webs.items()}
    spread = (max(coh.values()) - min(coh.values())) if coh else 0.0
    if spread < undiff_band:                          # FLAT coupling — the measure cannot separate registers (F1099)
        return {"register": "undetermined", "emergent": False, "spread": round(spread, 3), "coherence": coh,
                "note": "flat coupling; needs the Class-L spectral measure (R-RBS-LM-250) or the attestation anchor"}
    narr = max((coh[r] for r in coh if DISCRETE.get(r, 0) & NARRATIVE), default=0.0)   # narrative-side coherence
    att = max((coh[r] for r in coh if DISCRETE.get(r, 0) & ATTESTED), default=0.0)     # attested-side coherence
    # EMERGENCE: a parable couples to BOTH sides, balanced — truth through metaphor (found, not declared).
    # gap = (max − min) is the Class-K pin-slot magnitude of the difference (cascade-honest sign discipline).
    if narr >= dual_floor and att >= dual_floor and (max(narr, att) - min(narr, att)) < balance_margin:
        graded = round(min(narr, att) / max(narr, att, 1e-9), 2)     # graded truth-content balance (the 0x64 level)
        return {"register": "parable", "emergent": True, "graded": graded, "coherence": coh}
    ranked = sorted(coh.items(), key=lambda kv: kv[1], reverse=True)
    top, second = ranked[0], (ranked[1][1] if len(ranked) > 1 else 0.0)
    return {"register": top[0], "emergent": False, "degree": round((top[1] - second) / (top[1] or 1.0), 2),
            "coherence": coh}


# ---------------------------------------------------------------------------------------------------------------
# The Class-L SPECTRAL coupling (F1100) — the CONTINUOUS-FORM measure the flat klein4_similarity coupling (F1099)
# lacked. Per the user: the register is NOT an inherent label; it is a CONTINUOUS MATH SHAPE we choose to call
# fact/fiction. Duality gives BOTH answers: the CONTINUOUS-FORM answer (this spectral coherence) AND the
# BIT-EXACT op(x)operand answer (the emergent base-2 register). BASE-2 (the fact/fiction bit) is EMERGENT from
# COMPARING TWO shapes (k=2) — it is not the substrate; confusing the universe with base-2 is the error. So
# ``classify_spectral`` returns BOTH: the continuous λ₂ coherences AND the emergent discrete register.

#: minimal function-word stoplist — common words bridge EVERY web (spurious coupling), so coupling must be by
#: CONTENT (F1100). A first cut; the principled version routes through siona's measured aboutness-gate (F768).
_STOP = frozenset(("the", "and", "for", "that", "with", "his", "her", "its", "into", "across", "can", "are",
                   "was", "were", "has", "had", "his", "she", "him", "they", "them", "this", "these", "those",
                   "from", "out", "off", "over", "under", "onto", "upon", "each", "any", "all", "but", "not"))


def _words(text):
    return [w for w in _re.split(r"[^a-z0-9]+", (text or "").lower()) if len(w) > 2 and w not in _STOP]


def coupling_coherence(statement, web_texts):
    """COUPLE the statement with a register's web into ONE co-occurrence graph and return the Class-L Laplacian
    ALGEBRAIC CONNECTIVITY (the Fiedler value λ₂) — the CONTINUOUS measure of how cohesively they couple (F1100,
    the user's 'couple for compare'; R-RBS-LM-250). A shared word is a shared NODE that bridges the statement's
    sub-graph to the web's, so λ₂ rises when they cohere and stays near zero when they don't (F1098's
    'not cohesive' flag, now continuous). numpy-free; Class-L ``dense_laplacian`` + ``symmetric_eigendecompose``."""
    best = 0.0
    stmt_words = _words(statement)
    for wt in web_texts:                             # couple to EACH sentence separately — a multi-sentence web is
        nodes, edges = {}, set()                     # disconnected (λ₂→0 for the whole); the best single coupling is the signal
        nid = lambda w: nodes.setdefault(w, len(nodes))
        for ws in (stmt_words, _words(wt)):
            for a, b in zip(ws, ws[1:]):
                if a != b:
                    i, j = nid(a), nid(b)
                    edges.add((min(i, j), max(i, j)))
        n = len(nodes)
        shared = set(stmt_words) & set(_words(wt))
        if n < 3 or not edges or not shared:
            continue                                 # no shared CONTENT word ⇒ no coupling (disconnected, λ₂=0)
        evals, _ = _L.symmetric_eigendecompose(_L.dense_laplacian(n, sorted(edges), [1.0] * len(edges)))
        ev = sorted(float(e) for e in evals)
        best = max(best, ev[1] if len(ev) > 1 else 0.0)   # λ₂ — algebraic connectivity of this coupled pair
    return round(best, 4)


def classify_spectral(statement, web_texts, *, dual_floor=1e-3, balance_margin=0.15):
    """Class-L SPECTRAL register classify (F1100) — returns BOTH answers, per attested duality:

      * ``continuous`` — ``{register: λ₂}``: the CONTINUOUS-FORM coherence of coupling the statement to each
        register's web (the substrate answer; the shape we CHOOSE to call fact/fiction — intent is not inherent).
      * ``register`` — the EMERGENT base-2 answer: which web couples most coherently (a k=2 comparison over the
        continuous shapes); PARABLE when the narrative-side and attested-side λ₂ are BOTH high and balanced (the
        graded emergence). ``degree`` = the λ₂ margin (top vs second, relative) — low ⇒ honest 'undetermined'.

    ``web_texts``: ``{register: [exemplar sentence, …]}``. Base-2 is emergent-from-comparison, never the substrate."""
    coh = {reg: coupling_coherence(statement, texts) for reg, texts in web_texts.items()}
    ranked = sorted(coh.items(), key=lambda kv: kv[1], reverse=True)
    top, second = ranked[0], (ranked[1][1] if len(ranked) > 1 else 0.0)
    narr = max((coh[r] for r in coh if DISCRETE.get(r, 0) & NARRATIVE), default=0.0)
    att = max((coh[r] for r in coh if DISCRETE.get(r, 0) & ATTESTED), default=0.0)
    hi = max(coh.values()) if coh else 0.0
    if hi <= dual_floor:
        return {"register": "undetermined", "continuous": coh, "emergent": False}
    # PARABLE emergence: coheres to BOTH sides, balanced (relative gap small) — the graded truth-content
    if narr > dual_floor and att > dual_floor and (max(narr, att) - min(narr, att)) / max(narr, att) < balance_margin:
        return {"register": "parable", "emergent": True,
                "graded": round(min(narr, att) / max(narr, att), 2), "continuous": coh}
    return {"register": top[0], "emergent": False,
            "degree": round((top[1] - second) / (top[1] or 1.0), 2), "continuous": coh}
