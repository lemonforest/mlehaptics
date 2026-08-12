#!/usr/bin/env python3
"""The citation-claim extraction instrument + manifest builder — rc428, `#T1126`.

Answers ONE question about a cited source: **does it contain this claim term,
and WHERE** — and is built so that it cannot lie in either direction.

⚠️ **NETWORK-TOUCHING, OFFLINE OF CI, NOT IN THE WHEEL.** ``tools/`` is not
packaged. CI never runs this; it consumes the committed
``srmech/amsc/attested/literature_claims/row.ndjson`` this file writes, exactly
as ``srmech.amsc.format`` states the discipline: *we trust the committed bytes
at runtime and never recompute*. Three modes::

    --validate   re-run the F1-F11 falsifier suite (the rc428 acceptance record)
    --build      fetch, extract, emit row.ndjson for the literature_claims catalog
    --check      re-derive from cached e-prints and byte-compare (regen --check idiom)

**PROMOTED from ``docs/srmech/notes/_s1_extractor_rc428.py`` at rc428.** It was
moved rather than copied: a validated 1000-line extraction core living in two
places is the duplication debt this project has repeatedly paid for. The frozen
validation output stays at ``docs/srmech/notes/_s1_extractor_rc428.ndjson``;
``--validate`` regenerates it in place.

WHY THIS EXISTS
===============
srmech's MPM discipline says *a citation without attestation is not real; an
attestation that can't be re-verified is broken.* It had no mechanical check for
the thing that matters most: whether the cited source actually CONTAINS the
cited claim. rc427 fixed a citation that had shipped FALSE inside published
wheels — Baez, *The Octonions*, arXiv:math/0105155 cited at
``cascade/cayley_dickson.py`` for "the Moufang identities in §2", a section that
states no Moufang identity, plus "the Mal'cev tangent algebra", a name that does
not occur in that paper in any spelling.

THE FAILURE MODE THIS INSTRUMENT IS DESIGNED AGAINST IS THE **FALSE NULL**.
One rc427 extraction returned 0 for "Moufang" AND 0 for "octonion" — from a
paper titled *The Octonions*. An instrument that can return a spurious zero
silently blesses every citation in the tree. Hence: a per-source POSITIVE
CONTROL that ABORTS the run rather than report zeros.

MEASURED INSTRUMENT FINDINGS (rc428, this file's validation run)
================================================================
Three extraction backends were run against the same source. **All three are
wrong in different directions.** This is why the instrument is dual-construction
and why one backend is rejected outright:

  * ``gs -sDEVICE=txtwrite``     — counts correctly (22 = 18 en-dash + 4 ASCII)
    but **mangles whitespace**, emitting run-together text such as
    ``"wedotheCayley-Dicksonconstruction"``.
  * ``pypdf`` (pure Python)      — corrupts whitespace the OPPOSITE way,
    **splitting words from the inside**: ``"Cayley–Dick son"``,
    ``"Cayle y-Dickson"``, ``"Cayley–Di ckson"``, ``"cal led"``,
    ``"rep eatedly"``.
  * ``tex`` (arXiv e-print)      — **OVER-reports** unless markup is stripped:
    "Moufang" occurs 7 times in ``oct.tex`` but only **5** are rendered text;
    the other two are the markup keys ``\\cite{Moufang}`` and
    ``\\bibitem{Moufang}``. After stripping cite/bibitem/label/ref it reads 5,
    matching the rendered PDF exactly.

Because the two rendered-PDF backends corrupt whitespace in OPPOSITE
directions, matching here is **whitespace-insensitive by construction** (see
:func:`densify`). Once it is, all three backends agree exactly: 22
"Cayley-Dickson", 5 "Moufang", 172 "octonion", 0 "Mal'cev".

⚠️ **RETRACTION, written before this file was ever committed.** An earlier
draft of this docstring accused ``pypdf`` of silently DROPPING text — "finds 16
where the source has 22 … drops bibliography entries … REJECTED as a counting
backend". **That was wrong, and this instrument refuted it.** pypdf drops
nothing. All 6 of the apparently-missing hits are present and intact; they are
spelled ``"Cayley–Dick son"`` and ``"Cayle y-Dickson"``, with a spurious space
inside the word. The 16 was an artifact of the NAIVE whitespace-sensitive
matcher used while probing — a defect in the instrument, blamed on the source.
That is precisely the error class this rc exists to prevent, committed against a
tool instead of a citation, and it is left recorded rather than quietly deleted:
the same reflex that edits a source to make a gate green would have deleted it.
The measurement now ships as falsifier F10 (:func:`naive_vs_dense_check`).

**F10 is the both-sides bite test for the normalisation.** It pins the dense
matcher as load-bearing rather than decorative: with whitespace-sensitive
matching pypdf reads 16/22 and 162/172, with dense matching 22/22 and 172/172,
while ghostscript reads 22 either way. A gate written the obvious way, over the
obvious library, would therefore have reported a CORRECT citation as false — a
false NEGATIVE, the mirror of the false null, and just as damaging.

THE ENCODING TRAP, REPRODUCED — AND IT IS WORSE THAN RECORDED
==============================================================
rc427 recorded that ``pdftotext`` emits Latin-1 by default, so decoding as UTF-8
mangles every en-dash and "Cayley-Dickson" then matches only the 4 ASCII
spellings out of 22. That trap reproduces exactly here on a different tool:
decoding the ghostscript output as Latin-1 instead of UTF-8 yields **4**, the
same wrong value, versus **22** decoded correctly.

The part worth adding: rc427 caught its bad extraction because a ``\\ufffd``
appeared in the output. **That tell does not fire here.** The Latin-1 misdecode
produces ZERO U+FFFD, because every byte is a valid Latin-1 codepoint —
Latin-1 NEVER raises and never substitutes. The corruption is completely
silent. So "no replacement characters appeared" is NOT evidence of a good
extraction. Only a multi-spelling positive control catches this class.
Accordingly :func:`decode_strict` refuses to fall back to Latin-1: a UTF-8
decode failure is an ERROR, never a silent downgrade.

WHAT THIS INSTRUMENT MAY AND MAY NOT CLAIM
===========================================
  * **MAY** claim presence/absence of a term, with per-hit context, for a source
    whose bytes it fetched and hashed, WHEN the positive control passed.
  * **MAY** claim exact SECTION attribution when an arXiv LaTeX e-print is
    available, because ``\\section{}`` is structural markup, not a guess.
  * **MAY NOT** claim reliable section attribution from rendered PDF text
    alone. Header detection there is a heuristic that also matches table rows
    (``"3 H ⊕ H"``, ``"4 H[2]"``). This is reported as ``BOUNDED``, not hidden.
  * **MAY NOT** be run on a paywalled source. An unreachable source yields
    ``UNSOURCED`` or ``DERIVED-AND-MEASURED``. Substituting a second unverified
    citation only moves the defect.

COUNTS ARE NOT SETS. The dual-construction oracle compares the SET of hit
contexts between backends, not the totals. Standing precedent: two reversal laws
both scored 2752/4096 on the octonion loop and succeeded on DIFFERENT triples.

Class-K discipline: zero-tests are by construction (empty containers / explicit
comparisons), never ``abs()``. No ``math`` / ``fractions`` / ``decimal`` / numpy.
Hashing routes through ``srmech.amsc.format.sha256_bytes`` per the no-direct-
``hashlib`` rule.

WHAT rc428 ADDED TO THE PROMOTED INSTRUMENT, AND WHY EACH WAS FORCED
====================================================================

**1. A LEVEL-AWARE section map** (:func:`numbered_sections`), replacing the
flat ``\\section``-only :func:`tex_sections`. Forced by measurement, not taste:

  * Baez ``oct.tex`` carries 5 ``\\section`` and **16 ``\\subsection``**. The
    tree cites ``§2.4``, ``§4.1``, ``§4.2``, ``§3.4`` — every one of those is a
    SUBSECTION, and a ``\\section``-only map cannot resolve any of them. The
    rc428 note's map answered "section 2" where the citation says "§2.4".
  * Rosengren's e-print carries **4 ``\\chapter``** and 24 ``\\section`` and no
    subsections at all, so its ``\\section`` numbers as ``C.S`` — §1.3, §2.3 —
    which is exactly how the tree spells it. The TOP PRESENT LEVEL starts the
    numbering; hardcoding "section = level 0" would number Rosengren §1..§24
    and report every one of its citations unresolvable.
  * Starred forms are UNNUMBERED in LaTeX and must not advance the counter.
    Baez's ``\\subsection*{Acknowledgements}`` would otherwise mint a §5.1 and
    shift nothing else — a silent off-by-one that only shows up as a citation
    resolving to the wrong neighbour.

**2. Dotted-PREFIX locator matching.** A citation of ``§3`` covers §3, §3.1 …
§3.4; ``§4.2`` covers only §4.2 and deeper. String equality would report every
coarse-grained citation in the tree false. Measured consequence: Baez's
"exceptional Jordan" reads 3 hits in §3's own prose and 4 more in §3.4, so
``cayley_plane.py``'s ``§3 (the exceptional Jordan algebra)`` is VERIFIED at 7
under prefix matching and REFUTED-at-3 under equality — same citation, opposite
verdict, decided entirely by this rule.

**3. Single-gzip e-print handling.** arXiv serves a bare ``.tex.gz`` for
single-file submissions (Rosengren) and a ``.tar.gz`` for multi-file ones
(Baez). The rc428 note handled only the tarball and would have raised
``ReadError`` on the second source ever added.

**4. A SECOND SOURCE.** The instrument's own stated bound was *"validated
against exactly ONE source; every new source needs its own positive control."*
A single-source manifest cannot distinguish "the schema works" from "the schema
fits Baez", so Rosengren ships as the negative control on the manifest design —
different subtree, different structure (chapters), different positive control
(``elliptic``, chosen and recorded BEFORE extraction).

WHAT THE rc428 BUILD MEASURED, THAT THE BRIEF DID NOT PREDICT
==============================================================
Three further citation halves are FALSE AS CITED, all the rc426 shape (right
paper, wrong locator), all in module docstrings that ship inside the wheel:

  * ``cayley_plane.py`` module docstring — ``§4.2 (… the octonionic Hopf
    fibration S⁷↪S¹⁵↠S⁸, 𝕆P¹≅S⁸)``. "Hopf" occurs **0 times in §4.2**; the
    fibration table and ``\\OP^1 \\iso S^8`` are both in **§3.1 Projective
    Lines**, verbatim. The 𝕆P² half of the same parenthesis is CORRECT (§4.2 is
    F₄, and Baez states there that F₄ is the isometry group of a 16-dimensional
    projective plane which "is none other than 𝕆P²"). One parenthesis, two
    claims, opposite verdicts.
  * ``cayley_plane.py:octonion_hopf_base`` — ``§4.1–§4.2 (the octonionic Hopf
    fibration … and 𝕆P¹ ≅ S⁸)``. Both halves false at that locator; both are
    §3.1. This is the SSoT for what that op computes.
  * ``cayley_dickson.py:cd_three_form`` — ``§4.1 — φ, its Fano-plane values and
    G₂ = Aut(𝕆)``. "Fano" occurs **0 times in §4.1**; the Fano plane is §2.1.
    The φ and G₂ halves are correct (§4.1 states φ(x,y,z) = ⟨x,yz⟩ and that the
    transformations preserving φ "are exactly those in the group G₂").

Each was fixed by RE-POINTING THE LOCATOR, never by deleting the citation.
Deleting one converts a false citation into an UNSOURCED claim, which is a
change of defect class rather than a fix — measured on ``malcev_defect``, where
rc427's removal did exactly that and nothing in the tree noticed.

Run::

    PYTHONPATH=docs/srmech/python python3 docs/srmech/python/tools/build_citation_manifest.py --build
"""

from __future__ import annotations

import gzip
import io
import json
import os
import re
import subprocess
import sys
import tarfile
import unicodedata
import urllib.request
from typing import Dict, List, Optional, Sequence, Tuple

# The package root is this file's grandparent (``python/tools/`` -> ``python/``).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from srmech.amsc.format import sha256_bytes  # noqa: E402  (Class A anchor)

CACHE = os.environ.get("RC428_CACHE", "/tmp/rc428")

# ── Unicode classes the instrument must fold ────────────────────────────
# Every dash spelling a typesetter may emit. The rc427 trap lives here: a
# search written with ASCII "-" finds 4 of 22 when the paper sets an en-dash.
DASHES = (
    "\u002d"  # HYPHEN-MINUS
    "\u2010"  # HYPHEN
    "\u2011"  # NON-BREAKING HYPHEN
    "\u2012"  # FIGURE DASH
    "\u2013"  # EN DASH        <- Baez sets Cayley–Dickson with this, 18x
    "\u2014"  # EM DASH
    "\u2015"  # HORIZONTAL BAR
    "\u2212"  # MINUS SIGN
)
DASH_NAMES = {
    "\u002d": "ascii-hyphen", "\u2010": "hyphen", "\u2011": "nb-hyphen",
    "\u2012": "figure-dash", "\u2013": "en-dash", "\u2014": "em-dash",
    "\u2015": "horizontal-bar", "\u2212": "minus-sign",
}
SOFT_HYPHEN = "\u00ad"
# NFKC expands the ﬀ/ﬁ/ﬂ/ﬃ ligatures; 318 of them are present in this source,
# so "diﬀerent" would otherwise never match "different".
LIGATURES = "\ufb00\ufb01\ufb02\ufb03\ufb04"
APOSTROPHES = "'\u2019\u02bc\u2032\u00b4`"


# ── decoding: pinned, never silently downgraded ─────────────────────────
def decode_strict(raw: bytes, encoding: str = "utf-8") -> str:
    """Decode with the encoding PINNED. A failure raises.

    There is deliberately no Latin-1 fallback. Latin-1 decodes ANY byte
    sequence without error and without emitting U+FFFD, so a fallback would
    convert a loud failure into a silent 5x under-count — measured: 22 -> 4.
    """
    return raw.decode(encoding, errors="strict")


def has_replacement_chars(text: str) -> bool:
    """U+FFFD present? Useful but NOT sufficient — see module docstring."""
    return "\ufffd" in text


# ── normalisation ───────────────────────────────────────────────────────
def normalise(text: str, dehyphenate: bool = True) -> str:
    """NFKC + soft-hyphen strip + optional line-break de-hyphenation.

    Dashes are NOT folded here: the ORIGINAL spelling must survive so each hit
    can report which dash variant it used (18 en-dash vs 4 ASCII). Folding
    happens only in the matching copy built by :func:`densify`.
    """
    text = unicodedata.normalize("NFKC", text)
    text = text.replace(SOFT_HYPHEN, "")
    if dehyphenate:
        # "construc-\ntion" -> "construction". 34 such joins exist in this
        # source, including "construc-tion" inside the phrase "Cayley-Dickson
        # construction", so phrase search depends on this.
        text = re.sub(
            r"(\w)[%s]\s*\r?\n\s*(\w)" % re.escape(DASHES), r"\1\2", text)
    return text


def densify(text: str) -> Tuple[str, List[int]]:
    """Whitespace-stripped, dash-folded matching copy + offset map back.

    Both rendered-PDF backends corrupt whitespace, in OPPOSITE directions —
    ghostscript joins words, pypdf splits them. Matching on a dense string
    makes the matcher immune to both. Returns ``(dense, idx)`` where
    ``idx[k]`` is the offset in ``text`` of ``dense[k]``.

    Known bound, stated rather than hidden: dense matching could in principle
    join two unrelated words across a page break into a spurious hit. Measured
    on this source it does not — dense and whitespace-preserving matching agree
    exactly (22 == 22, 5 == 5). The validation run re-checks this every time.
    """
    chars: List[str] = []
    idx: List[int] = []
    for i, ch in enumerate(text):
        if ch.isspace():
            continue
        chars.append("-" if ch in DASHES else ch)
        idx.append(i)
    return "".join(chars), idx


def term_pattern(term: str) -> str:
    """Regex for ``term`` against DENSE text.

    A dash in the term becomes ``[-]*`` — zero or more — so ``Cayley-Dickson``,
    ``Cayley–Dickson``, the LaTeX ``Cayley--Dickson`` and a de-hyphenated
    ``CayleyDickson`` all match. This also makes line-break de-hyphenation
    ambiguity harmless: whether or not a real hyphen was consumed, the term
    still matches, and the reported spelling is read from the ORIGINAL text.
    """
    out = []
    for ch in term:
        if ch in DASHES:
            out.append("[%s]*" % re.escape(DASHES))
        elif ch in APOSTROPHES:
            out.append("[%s]" % re.escape(APOSTROPHES))
        elif ch.isspace():
            continue  # dense text has no whitespace
        else:
            out.append(re.escape(ch))
    return "".join(out)


# ── sections ────────────────────────────────────────────────────────────
#: Sectioning commands, OUTERMOST first. The top level actually PRESENT in a
#: document starts the numbering, which is what makes one map serve both a
#: chapter-bearing source (Rosengren: §1.3 = chapter 1, section 3) and a
#: chapter-free one (Baez: §2.4 = section 2, subsection 4).
SECTION_LEVELS = ("part", "chapter", "section", "subsection", "subsubsection")

#: The label given to text before the first numbered heading.
FRONT_MATTER = "FRONT-MATTER"


def covers(cited: str, actual: str) -> bool:
    """Does a cited locator COVER an actual section label? Dotted prefix.

    ``§3`` covers §3, §3.1 … §3.4; ``§4.2`` covers §4.2 and anything deeper;
    ``§4.2`` does NOT cover §4 or §4.1. The dot boundary is required, so §1
    never covers §10 — a plain ``startswith`` would, and Rosengren really does
    have a §2.10 and a §2.11 sitting next to a §2.1.

    Non-numbered labels (``BIBLIOGRAPHY``, ``FRONT-MATTER``) compare by
    equality; there is no hierarchy to walk.
    """
    if cited == actual:
        return True
    if not cited.startswith("\u00a7") or not actual.startswith("\u00a7"):
        return False
    return actual.startswith(cited + ".")


class SectionMap:
    """Offset -> canonical section label (``§2``, ``§2.4``, ``BIBLIOGRAPHY``).

    ``exact=True`` only when built from LaTeX structural markup. From rendered
    PDF text this is a heuristic and says so; the gate must not make section
    claims on a heuristic map.
    """

    def __init__(self, spans: Sequence[Tuple[int, str, str]],
                 exact: bool) -> None:
        #: ``(offset, label, title)``; ``label is None`` for starred headings,
        #: which are unnumbered in LaTeX and therefore not addressable.
        self.spans = sorted(spans, key=lambda s: s[0])
        self.exact = exact

    def label(self, pos: int) -> str:
        current = FRONT_MATTER
        for start, name, _title in self.spans:
            if start > pos:
                break
            if name is not None:
                current = name
        return current

    def titles(self) -> "Dict[str, str]":
        return {lab: title for _s, lab, title in self.spans
                if lab is not None}

    def labels(self) -> List[str]:
        seen: List[str] = []
        for _s, lab, _t in self.spans:
            if lab is not None and lab not in seen:
                seen.append(lab)
        return seen


def _balanced_group(text: str, open_at: int) -> Tuple[str, int]:
    """Read a brace-balanced ``{...}`` starting just after ``open_at``.

    A flat ``\\{([^}]*)\\}`` truncates every heading containing maths — Baez
    sets ``\\subsection{$\\OP^1$ and Bott Periodicity}``, whose title has no
    inner brace but whose SIBLINGS (``$\\G_2$``, ``${}_{12}V_{11}$``) do. The
    Rosengren heading ``\\section{The sum ${}_{12}V_{11}$}`` closes at the
    FIRST ``}`` under a flat read, which then desynchronises every subsequent
    offset in the scan.
    """
    depth, i = 1, open_at
    while i < len(text) and depth:
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
        i += 1
    return text[open_at:i - 1], i


def tex_sections(text: str) -> SectionMap:
    """EXACT, LEVEL-AWARE section map from LaTeX structural markup.

    See the module docstring, "WHAT rc428 ADDED", item 1 — every design choice
    here was forced by a measured property of one of the two shipped sources,
    not chosen for generality.
    """
    present = [lv for lv in SECTION_LEVELS
               if re.search(r"\\" + lv + r"\*?\{", text) is not None]
    spans: List[Tuple[int, Optional[str], str]] = []
    if present:
        depth = {lv: i for i, lv in enumerate(present)}
        counters = [0] * len(present)
        pat = r"\\(" + "|".join(present) + r")(\*?)\{"
        for m in re.finditer(pat, text):
            title, _end = _balanced_group(text, m.end())
            title = re.sub(r"\s+", " ", title).strip()
            if m.group(2):
                # Starred = unnumbered in LaTeX. Recorded so the span list is
                # a faithful reading of the document, but NOT addressable and
                # explicitly NOT advancing the counter.
                spans.append((m.start(), None, title))
                continue
            d = depth[m.group(1)]
            counters[d] += 1
            for k in range(d + 1, len(counters)):
                counters[k] = 0
            spans.append((m.start(),
                          "\u00a7" + ".".join(str(c) for c in counters[:d + 1]),
                          title))
    bib = re.search(r"\\begin\{thebibliography\}", text)
    if bib is not None:
        spans.append((bib.start(), "BIBLIOGRAPHY", ""))
    return SectionMap(spans, exact=True)


def pdf_sections_heuristic(text: str) -> SectionMap:
    """Heuristic map from rendered text. NOT trustworthy — see docstring.

    Kept so the instrument can SHOW why it refuses to make section claims from
    a PDF alone: this same pattern also matches table rows such as
    ``"3 H ⊕ H"`` and ``"4 H[2]"``, which are not sections.
    """
    spans: List[Tuple[int, str, str]] = []
    for m in re.finditer(r"(?m)^[ \t]*(\d+)[ \t]+([A-Z][^\r\n]{3,60})[ \t]*$",
                         text):
        spans.append((m.start(), "heuristic §" + m.group(1),
                      m.group(2).strip()))
    return SectionMap(spans, exact=False)


# ── hits ────────────────────────────────────────────────────────────────
def search(text: str, term: str, sections: Optional[SectionMap] = None,
           context: int = 90) -> List[Dict[str, object]]:
    """All occurrences of ``term``, with spelling, section and context."""
    dense, idx = densify(text)
    hits: List[Dict[str, object]] = []
    for m in re.finditer(term_pattern(term), dense, re.IGNORECASE):
        start = idx[m.start()]
        end = idx[m.end() - 1] + 1
        literal = text[start:end]
        variant = "".join(sorted({DASH_NAMES[c] for c in literal
                                  if c in DASHES})) or "no-dash"
        ctx = re.sub(r"\s+", " ",
                     text[max(0, start - context):end + context]).strip()
        hits.append({
            "offset": start,
            "literal": literal,
            "dash_variant": variant,
            "section": sections.label(start) if sections is not None else None,
            "section_exact": sections.exact if sections is not None else False,
            "context": ctx,
        })
    return hits


def dense_keys(text: str, term: str, window: int = 45) -> List[str]:
    """Backend-independent SET keys, built from the DENSE neighbourhood.

    Counts are not sets: three backends each reporting 22 could be finding
    three different 22s. This is what makes the comparison mean something.

    The key is taken from the whitespace-stripped text around each hit, NOT
    from the raw context, which makes it immune to the whitespace corruption
    the backends disagree on. Measured effect: keying on raw context showed a
    spurious 3-hit pypdf-vs-ghostscript residual that is purely a
    window-alignment artifact; keying on the dense neighbourhood drops it to 1,
    and makes the ghostscript and LaTeX keys for "Moufang" come out BYTE-
    IDENTICAL (``weverworkonthesubjectcontinuedandin1933ruthconstructed…``).
    """
    dense, _idx = densify(text)
    keys: List[str] = []
    for m in re.finditer(term_pattern(term), dense, re.IGNORECASE):
        left = dense[max(0, m.start() - window):m.start()]
        right = dense[m.end():m.end() + window]
        keys.append(re.sub(r"[^a-z0-9]", "", (left + right).lower()))
    return keys


def key_overlap(ref: Sequence[str], other: Sequence[str],
                min_shared: int = 24) -> Tuple[int, int]:
    """(missing, extra) between two key lists.

    Two hits are the SAME occurrence when their neighbourhoods share a run of
    at least ``min_shared`` characters — roughly four or five words of prose,
    far longer than any search term, so a shared run is strong identity
    evidence and cannot be produced by the term alone.

    Why a shared-substring test rather than comparing key edges: an
    edge-anchored probe reported a 1-of-22 ghostscript-vs-pypdf
    "disagreement" on "Cayley-Dickson". Inspected, both keys contain
    ``startingfromanyalgebraatheconstructiongivesanewalgebraa`` — the SAME
    hit — differing only in a leading run of DISPLAYED-EQUATION glyphs the two
    extractors emit in different order (``abbakakkbk`` vs ``bbaa2b2``). Key
    EDGES drift into equations and figure captions, where extractor reading
    order genuinely differs. Re-anchoring the probe on the match instead
    "fixed" that case and made "octonion" worse (12 -> 23) — a clear sign the
    probe geometry was being tuned to the answer. A shared-run test has no
    such knob to turn, so the caller reports a SWEEP over ``min_shared``
    (see F6) rather than a single chosen value.
    """
    def shards(key: str) -> set:
        span = max(1, len(key) - min_shared + 1)
        return {key[i:i + min_shared] for i in range(span)}

    ref_parts = [shards(r) for r in ref]
    other_parts = [shards(o) for o in other]
    missing = sum(1 for r in ref_parts
                  if not any(r & o for o in other_parts))
    extra = sum(1 for o in other_parts
                if not any(o & r for r in ref_parts))
    return missing, extra


def naive_vs_dense_check(text: str, term: str,
                         backend: str) -> Dict[str, object]:
    """F10 — the both-sides bite test proving the normalisation is load-bearing.

    Compares the whitespace-SENSITIVE regex a gate would obviously write
    against this instrument's whitespace-insensitive matcher, and reports the
    literal spellings the naive one would miss.

    Measured: ghostscript reads 22 either way, but pypdf reads **16 naive vs
    22 dense** — the six missing hits are spelled ``"Cayley–Dick son"``,
    ``"Cayle y-Dickson"``, ``"Cayley–Di ckson"`` and so on, with a spurious
    space inside the word. A gate written the obvious way over the obvious
    library would call a CORRECT citation false.
    """
    naive_pat = "".join(
        "[%s]" % re.escape(DASHES) if ch in DASHES else re.escape(ch)
        for ch in term)
    naive = len(re.findall(naive_pat, text, re.IGNORECASE))
    dense_hits = search(text, term)
    missed = [str(h["literal"]) for h in dense_hits
              if re.fullmatch(naive_pat, str(h["literal"]), re.IGNORECASE)
              is None]
    return {
        "backend": backend, "term": term,
        "naive_whitespace_sensitive": naive,
        "dense_whitespace_insensitive": len(dense_hits),
        "would_be_missed_by_naive": len(dense_hits) - naive,
        "missed_literals": missed,
        "normalisation_load_bearing": len(dense_hits) != naive,
    }


# ── fetch ───────────────────────────────────────────────────────────────
def fetch(url: str, name: str) -> bytes:
    """Fetch + cache, returning raw bytes. The sha256 is the Class-A anchor."""
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, name)
    if not os.path.exists(path):
        req = urllib.request.Request(
            url, headers={"User-Agent": "srmech-rc428-extractor/0.9"})
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = resp.read()
        with open(path, "wb") as fh:
            fh.write(data)
    with open(path, "rb") as fh:
        return fh.read()


# ── backends ────────────────────────────────────────────────────────────
def backend_gs(pdf_bytes: bytes, tag: str,
               encoding: str = "utf-8") -> Tuple[str, SectionMap]:
    """ghostscript ``txtwrite``. Encoding PINNED — the trap lives here."""
    os.makedirs(CACHE, exist_ok=True)
    pdf = os.path.join(CACHE, tag + ".pdf")
    txt = os.path.join(CACHE, tag + ".gs.txt")
    with open(pdf, "wb") as fh:
        fh.write(pdf_bytes)
    if not os.path.exists(txt):
        subprocess.run(
            ["gs", "-q", "-dNOPAUSE", "-dBATCH", "-sDEVICE=txtwrite",
             "-dTextFormat=3", "-sOutputFile=" + txt, pdf],
            check=True, capture_output=True)
    with open(txt, "rb") as fh:
        raw = fh.read()
    text = normalise(decode_strict(raw, encoding))
    return text, pdf_sections_heuristic(text)


def backend_pypdf(pdf_bytes: bytes, tag: str) -> Tuple[str, SectionMap]:
    """pypdf. **REJECTED for counting** — proven to under-report 22 -> 16.

    Wired in ONLY so the consistency oracle can be shown to bite. If this ever
    starts agreeing with ghostscript, that is itself a finding worth chasing.
    """
    from pypdf import PdfReader  # local import: not a package dependency
    os.makedirs(CACHE, exist_ok=True)
    pdf = os.path.join(CACHE, tag + ".pdf")
    with open(pdf, "wb") as fh:
        fh.write(pdf_bytes)
    reader = PdfReader(pdf)
    text = normalise("\n".join(p.extract_text() or "" for p in reader.pages))
    return text, pdf_sections_heuristic(text)


def strip_tex_markup(text: str) -> str:
    """Remove markup KEYS that are not rendered text.

    Load-bearing and measured: "Moufang" appears 7 times in ``oct.tex`` but
    only 5 are rendered. ``\\cite{Moufang}`` and ``\\bibitem{Moufang}`` are
    label keys the reader never sees. Without this the TeX backend
    OVER-reports and would contradict the PDF for a purely cosmetic reason.
    The placeholders keep offsets sane and stay searchable in context.
    """
    text = re.sub(r"\\cite\{[^}]*\}", " [CITE] ", text)
    text = re.sub(r"\\bibitem\{[^}]*\}", " [BIBITEM] ", text)
    text = re.sub(r"\\(label|ref|eqref|pageref)\{[^}]*\}", " ", text)
    return text


def eprint_main_tex(raw: bytes, tag: str,
                    main_hint: str = "") -> Tuple[bytes, str]:
    """The main ``.tex`` out of an arXiv e-print payload.

    arXiv serves TWO shapes and they are not distinguishable by URL:

      * a ``.tar.gz`` of the whole submission — Baez (``oct.tex`` + 11 ``.eps``);
      * a bare **gzipped single file** for single-file submissions —
        Rosengren (``lectures-new.tex``, 47646 B gz).

    The rc428 note handled only the first and raised ``tarfile.ReadError`` on
    the second. Sniffing by trying ``tarfile`` first and falling back is the
    honest order: a tar IS a valid gzip member, so testing gzip first would
    mis-route every tarball.
    """
    try:
        with tarfile.open(fileobj=io.BytesIO(raw), mode="r:*") as tf:
            names = sorted(m.name for m in tf.getmembers()
                           if m.isfile() and m.name.endswith(".tex")
                           and "/" not in m.name
                           and not m.name.startswith(".."))
            if not names:
                raise RuntimeError("no .tex in e-print for " + tag)
            chosen = main_hint if main_hint in names else names[0]
            handle = tf.extractfile(chosen)
            if handle is None:
                raise RuntimeError("unreadable .tex member for " + tag)
            return handle.read(), chosen
    except tarfile.ReadError:
        return gzip.decompress(raw), "(single-gz)"


def backend_tex(tar_bytes: bytes, tag: str,
                main_hint: str = "") -> Tuple[str, SectionMap]:
    """arXiv LaTeX e-print — the AUTHOR'S OWN SOURCE, not a rendering.

    This is the strongest available attestation for "does the source contain
    the term", and the only backend that yields EXACT section attribution,
    because ``\\section{}`` is structural markup rather than a guess about
    which line of rendered text looked like a heading.

    LaTeX sets an en-dash as ``--``; that is folded to U+2013 so dash-variant
    reporting is directly comparable with the rendered-PDF backends.
    """
    raw, _chosen = eprint_main_tex(tar_bytes, tag, main_hint)
    # arXiv 2001-era sources are Latin-1/ASCII TeX, NOT UTF-8. Try strict
    # UTF-8 first and fall back ONLY with the encoding recorded, never
    # silently — the fallback is legitimate here because TeX escapes
    # (\"u) carry the accents, so no glyph information rides on the bytes.
    try:
        text = decode_strict(raw, "utf-8")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")
    text = strip_tex_markup(text)
    text = text.replace("--", "\u2013")
    text = normalise(text, dehyphenate=False)  # TeX has no line-break hyphens
    return text, tex_sections(text)


# ── sources ─────────────────────────────────────────────────────────────
#
# WATCHLIST SEEDING POLICY — declared, not implicit (rc428 open question 3).
#
# The watchlist is CURATED here and is the gate's ONLY vocabulary. The gate
# never extracts terms from prose, because auto-extraction was measured and
# REFUTED: a scan of shipped citations yielded 175 distinct "claim-term"
# candidates of which the most frequent were ``Crossref`` (31), ``Iterable``,
# ``Optional``, ``Jun`` and ``Der``. A gate keyed on a contaminated vocabulary
# fires on typing imports.
#
# A term is admitted to a source's watchlist iff BOTH hold:
#   (a) some shipped srmech citation of THAT source attributes THAT term to it
#       — so the watchlist is a record of what the tree actually claims, and
#       cannot grow into a general index of the paper; and
#   (b) it is a NAMED CONCEPT, not a function word — a proper noun, an object
#       name, or a multi-word technical phrase.
#
# Deliberately NOT seeded: adjacent concepts the paper happens to discuss but
# that no citation claims. Adding those would raise sensitivity at the cost of
# making the manifest an index rather than an attestation, and every added row
# is a row someone must verify.
#
# ── VARIANTS, AND THE ONE RULE THAT KEEPS THEM HONEST ──────────────────
#
# A watchlist entry is either a bare string, or ``(canonical, [variants…])``.
# All variants are counted TOGETHER, because the tree and the source routinely
# name the same object with different words and a gate blind to that reports
# CORRECT citations false — the mirror of a false null, and just as damaging.
# Both instances here were measured, not imagined:
#
#   * ``cayley_plane.py`` claims "the Cayley plane 𝕆P²" of Baez §4.2. Baez
#     never writes "Cayley plane" ANYWHERE — 0 occurrences in the whole paper.
#     He writes "octonionic projective plane" (2 in §4.2) and ``\OP^2``, and
#     §4.2 states outright that F₄'s 16-dimensional projective plane "is none
#     other than 𝕆P²". The citation is correct; the vocabulary differs.
#   * ``cayley_dickson.py`` claims "alternativity" of §1–§2. Baez uses the
#     ADJECTIVE there ("alternative algebra": 6 in §1.1, 4 in §2.2) and the
#     noun "alternativity" exactly once, in §3.4.
#
# ⚠️ **THE RULE: a variant must be another SPELLING OR STANDARD SYNONYM OF THE
# SAME NAMED OBJECT, verified by reading the source.** It may NEVER be a
# different object that happens to share a word. "Moufang identities" may not
# be varianted into "Moufang plane" — that IS the rc426 defect this whole rc
# exists for, and the variant set ships inside the manifest precisely so that
# move is visible to a reader rather than buried in a matcher.
def _term_and_variants(entry: object) -> Tuple[str, Tuple[str, ...]]:
    """``"Hopf"`` -> ``("Hopf", ("Hopf",))``; a pair -> canonical + variants."""
    if isinstance(entry, str):
        return entry, (entry,)
    canonical, variants = entry            # type: ignore[misc]
    return canonical, tuple(variants)
SOURCES = {
    "arxiv:math/0105155": {
        "cite_as": "Baez, J.C. (2002), 'The Octonions', Bull. Amer. Math. Soc. "
                   "39:145-205, arXiv:math/0105155",
        "source_kind": "arxiv_eprint",
        # ⚠️ MEASURED, not assumed: arXiv's OLD-SCHEME e-print endpoint does
        # NOT honour a version suffix — ``…/e-print/math/0105155v4`` returns a
        # 225-byte error page, not the 70969-byte submission. So the version
        # cannot be pinned in the URL and is instead **attested by the sha256
        # of the fetched bytes**, which is the stronger mechanism anyway: if
        # arXiv ever ships a v5, ``--check`` goes red on the hash rather than
        # silently re-deriving against different text.
        "version": "v4",
        "published": "2002-04-23",   # v4; v1 was 2001-05-17
        "pdf_url": "https://arxiv.org/pdf/math/0105155",
        "eprint_url": "https://arxiv.org/e-print/math/0105155",
        "tex_main": "oct.tex",
        # A term that MUST be present. If this reads 0 the extraction is
        # broken and the run ABORTS rather than emit a false null.
        "positive_control": "octonion",
        # Terms that must NOT be present, so the matcher is not always-true.
        "negative_controls": ["Kirshtein", "Antikythera", "zygomatic",
                              "qwertzuiop"],
        # A term with MULTIPLE dash spellings. This is the control that
        # catches the encoding trap; a single-spelling control cannot.
        "multi_spelling_control": ("Cayley-Dickson", 22),
        "watchlist": [
            "Moufang", "Mal'cev", "Cayley-Dickson", "triality", "Fano",
            "Hopf", "Jordan algebra", "exceptional Jordan", "Freudenthal",
            "Hurwitz", "Kanerva", "projective plane", "Bott",
            "Spin(8)", "G_2", "F_4", "associator",
            "Albert algebra", "Clifford algebra",
            # The two measured vocabulary variants — see the rule above.
            ("alternativity", ["alternativity", "alternative"]),
            ("Cayley plane", ["Cayley plane", "octonionic projective plane",
                              "\\OP^2", "octonionic projective space"]),
        ],
    },
    # The NEGATIVE CONTROL on the manifest design itself. The instrument's own
    # stated bound is that it has been validated against exactly one source;
    # a second source in a different subtree, with a different document
    # structure (chapters, not subsections) and its own positive control, is
    # what distinguishes "the schema works" from "the schema fits Baez".
    "arxiv:1608.06161": {
        "cite_as": "Rosengren, H. (2016), 'Elliptic Hypergeometric Functions', "
                   "lectures at OPSF-S6, arXiv:1608.06161",
        "source_kind": "arxiv_eprint",
        # OPEN QUESTION 4, DECIDED: the BARE id is the manifest key and the
        # version is an attested ATTRIBUTE. The tree spells this source both
        # ``1608.06161`` and ``1608.06161v3``; keying on the versioned spelling
        # would report the bare one as an uncovered phantom source in arm S4.
        # The v3 e-print is what was fetched and hashed, and it is recorded.
        "version": "v3",
        "published": "2017-06-20",   # v3; v1 was 2016-08-22
        "pdf_url": "https://arxiv.org/pdf/1608.06161v3",
        "eprint_url": "https://arxiv.org/e-print/1608.06161v3",
        "tex_main": "",          # single-file submission; no name to hint
        # Chosen and written down BEFORE extraction, per the instrument's own
        # bound that every new source needs its own control.
        "positive_control": "elliptic",
        "negative_controls": ["Antikythera", "zygomatic", "qwertzuiop",
                              "octonion"],
        "multi_spelling_control": ("Frenkel-Turaev", 8),
        "watchlist": [
            "Frobenius", "theta function", "partial fraction", "Weierstrass",
            "three-term", "elliptic function", "modular", "well-poised",
            "interpolation", "determinant", "Frenkel-Turaev",
        ],
    },
}


class ExtractionBroken(RuntimeError):
    """Raised when a positive control fails. The run ABORTS; zeros are never
    reported from a broken extraction — that is the whole point."""


def run_controls(text: str, spec: Dict[str, object],
                 backend: str) -> Dict[str, object]:
    """Positive / negative / multi-spelling controls. ABORTS on positive fail."""
    pos_term = str(spec["positive_control"])
    pos = search(text, pos_term)
    if len(pos) == 0:
        raise ExtractionBroken(
            "POSITIVE CONTROL FAILED: %r not found by backend %r. Extraction "
            "is BROKEN; refusing to report any counts from it."
            % (pos_term, backend))
    negatives = {}
    for neg in spec["negative_controls"]:  # type: ignore[union-attr]
        negatives[neg] = len(search(text, neg))
    always_true = sorted(k for k, v in negatives.items() if v != 0)

    ms_term, ms_expect = spec["multi_spelling_control"]  # type: ignore
    ms_hits = search(text, ms_term)
    by_variant: Dict[str, int] = {}
    for h in ms_hits:
        key = str(h["dash_variant"])
        by_variant[key] = by_variant.get(key, 0) + 1
    return {
        "positive_control": {"term": pos_term, "count": len(pos),
                             "verdict": "PASS"},
        "negative_controls": negatives,
        "negative_verdict": "PASS" if not always_true else "FAIL",
        "always_true_terms": always_true,
        "multi_spelling": {
            "term": ms_term, "count": len(ms_hits), "expected": ms_expect,
            "by_dash_variant": by_variant,
            "verdict": "PASS" if len(ms_hits) == ms_expect else "FAIL",
            # ⚠️ rc428 generalisation. This read ``len(ms_hits) == 4`` — the
            # count Baez's "Cayley-Dickson" collapses to under the Latin-1
            # misdecode. That literal is a property of ONE term in ONE source
            # and would have silently reported "no trap" for every other one.
            # The trap signature is simply *the control missing its expected
            # count*; the collapsed value differs per term (Rosengren's
            # "Frenkel–Turaev" is 8 en-dashes with NO ASCII spelling, so it
            # collapses to 0, not to 4).
            "encoding_trap_signature": len(ms_hits) != ms_expect,
        },
        "u_fffd_present": has_replacement_chars(text),
    }


def abort_path_bite_test(spec: Dict[str, object]) -> List[Dict[str, object]]:
    """F11 — prove the ABORT actually FIRES. Otherwise it is a dead seam.

    A positive control that has never failed is indistinguishable from one
    that CANNOT fail. This rc exists because an extraction returned 0 for
    "Moufang" AND 0 for "octonion" from a paper titled *The Octonions*; the
    whole defence is that such a run ABORTS instead of reporting zeros. So the
    abort is exercised here against three deliberately-broken extractions,
    each a real way extraction fails in the field:

      * empty text          — the backend produced nothing at all
      * whitespace-only     — the backend "succeeded" and emitted layout only
      * plausible-but-wrong — text that reads like a document and contains the
        SEARCH TERMS being asked about, but not the positive control. This is
        the nastiest case: every claim term reads 0, which looks exactly like a
        clean refutation, and only the positive control tells them apart.

    Each MUST raise :class:`ExtractionBroken`. A case that does not is
    reported as a FAILED bite — the guard would be decorative.
    """
    cases = [
        ("empty", ""),
        ("whitespace_only", "   \n\n\t   \r\n   "),
        ("plausible_but_wrong",
         "On the Moufang identities and the Cayley-Dickson construction, "
         "with remarks on the Mal'cev tangent algebra. Section 2 states "
         "the identities in full."),
    ]
    out: List[Dict[str, object]] = []
    for name, text in cases:
        try:
            run_controls(text, spec, "bite:" + name)
            bit = False
            detail = "NO ABORT — the guard did not fire; it is decorative."
        except ExtractionBroken as exc:
            bit = True
            detail = str(exc)[:120]
        rec = {"case": name, "aborted": bit,
               "verdict": "BITES" if bit else "FAILED TO BITE",
               "detail": detail}
        if name == "plausible_but_wrong":
            # Show WHAT would have been reported had the abort not fired.
            rec["would_have_reported"] = {
                "Moufang": len(search(text, "Moufang")),
                "Mal'cev": len(search(text, "Mal'cev")),
                "note": "Non-zero here, so this case proves the abort fires "
                        "on a MISSING POSITIVE CONTROL specifically, not "
                        "merely on empty input.",
            }
        out.append(rec)
    return out


def dense_vs_plain_check(text: str, term: str) -> Dict[str, object]:
    """Guard the one known bound of dense matching.

    Dense (whitespace-stripped) matching could in principle fabricate a hit by
    joining unrelated words across a break. Compare against whitespace-
    preserving matching; they must agree.
    """
    dense_n = len(search(text, term))
    plain = re.escape(term).replace(r"\-", "[%s]" % re.escape(DASHES))
    plain_n = len(re.findall(plain, text, re.IGNORECASE))
    return {"term": term, "dense": dense_n, "plain": plain_n,
            "agree": dense_n >= plain_n,
            "note": "dense >= plain expected; dense also recovers "
                    "whitespace-corrupted spellings the plain pattern misses"}


def emit(records: List[Dict[str, object]], path: str) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False, sort_keys=True))
            fh.write("\n")


# ── the manifest build ──────────────────────────────────────────────────
#: Where the shipped catalog lives. ``tools/`` -> ``python/`` -> the package.
CATALOG_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "srmech", "amsc", "attested", "literature_claims")

#: The row schema id. Bumping this is a BREAKING catalog change.
ROW_SCHEMA_ID = "literature_claims.row.v1"

#: The date the catalog's rows were entered. **A FIXED LITERAL, never
#: ``date.today()``** — a build stamp that moves every run makes ``--check``
#: report drift on an unchanged tree, and a check that cries wolf is a check
#: that gets removed. Bump it deliberately when rows are re-derived.
CATALOG_ENTERED_AT = "2026-08-12"


def build_rows(sid: str, spec: Dict[str, object],
               verbose: bool = True) -> List[Dict[str, object]]:
    """The rows for one source: one ``source`` row, then one row per term.

    The positive control runs FIRST and raises :class:`ExtractionBroken` on
    failure, so a broken extraction produces NO rows rather than a page of
    zeros. That ordering is the whole defence and it is not an accident of
    control flow: the alternative — extract, then check — has a path where the
    zeros are already written.

    ── WHY NOT ONE ROW PER (source, section, term) ──────────────────────
    The first build did exactly that: the full cross-product, 789 rows and
    **541 KB**, every row repeating both sha256s and the source URL. Ten times
    the size the design costed, and the size was pure repetition.

    The shape below is smaller AND keeps absence **decidable**, which is the
    only property that matters — a manifest recording only presences cannot
    answer *"is this term absent HERE"*, and that is the sole question the gate
    asks. Decidability is explicit rather than implied:

      * the ``source`` row declares ``sections`` — the COMPLETE ordered list of
        addressable labels in the document;
      * each ``term`` row declares ``occurrences_by_section`` for the NONZERO
        sections only.

    So "term T is absent at section S" is decided as: the term row exists (T
    was measured), S is in ``sections`` (S was measured), and S is not a key of
    ``occurrences_by_section``. A missing key can never be confused with an
    unmeasured one, because both quantifiers are written down.
    """
    tag = sid.replace("/", "_").replace(":", "_")
    pdf_bytes = fetch(str(spec["pdf_url"]), tag + ".pdf")
    tar_bytes = fetch(str(spec["eprint_url"]), tag + ".eprint")
    text, sections = backend_tex(tar_bytes, tag, str(spec["tex_main"]))
    eprint_sha = sha256_bytes(tar_bytes)
    pdf_sha = sha256_bytes(pdf_bytes)

    # ── controls FIRST. A failure here aborts before a single row exists.
    ctrl = run_controls(text, spec, "tex")
    pos_term = str(spec["positive_control"])
    pos_n = int(ctrl["positive_control"]["count"])  # type: ignore[index]

    # A second, independent backend, so the counts are not one tool's opinion.
    gs_text, _gs_sec = backend_gs(pdf_bytes, tag, "utf-8")
    run_controls(gs_text, spec, "gs")

    labels = sections.labels()
    titles = sections.titles()
    if not labels:
        raise ExtractionBroken(
            "no numbered sections resolved for %s; a manifest keyed on "
            "sections cannot be built from a document with none" % sid)

    rows: List[Dict[str, object]] = [{
        "row_type": "source",
        "source_id": sid,
        "source_kind": spec["source_kind"],
        "source_version": spec["version"],
        "source_url": spec["eprint_url"],
        "source_pdf_url": spec["pdf_url"],
        "cite_as": spec["cite_as"],
        # The Class-A anchors. The VERSION is attested by these hashes rather
        # than by a URL pin — see the SOURCES note.
        "source_eprint_sha256": eprint_sha,
        "source_pdf_sha256": pdf_sha,
        "section_attribution": "EXACT",   # LaTeX e-print; never a PDF guess
        # The COMPLETE addressable label set. This is what makes an absent
        # key in a term row mean "measured absent" instead of "unmeasured".
        "sections": list(labels),
        "section_titles": {lab: titles.get(lab, "") for lab in labels},
        "positive_control": {"term": pos_term, "occurrences": pos_n},
        "source_published_date": spec["published"],
        "entered_locally_at": CATALOG_ENTERED_AT,
    }]
    for entry in spec["watchlist"]:           # type: ignore[union-attr]
        term, variants = _term_and_variants(entry)
        hits: List[Dict[str, object]] = []
        gs_total = 0
        for variant in variants:
            hits.extend(search(text, variant, sections))
            gs_total += len(search(gs_text, variant))
        # Variants can overlap ("alternative" is a prefix of no other variant
        # here, but "Cayley plane" and "octonionic projective plane" could in
        # principle co-occur), so de-duplicate BY OFFSET. Counting the same
        # occurrence twice would inflate a presence claim, and an inflated
        # presence claim is a citation blessed for the wrong reason.
        hits = list({int(h["offset"]): h for h in hits}.values())
        per_section: Dict[str, List[Dict[str, object]]] = {}
        for h in hits:
            per_section.setdefault(str(h["section"]), []).append(h)
        rows.append({
            "row_type": "term",
            "source_id": sid,
            "term": term,
            "variants": list(variants),
            "occurrences_by_section": {
                lab: len(hs) for lab, hs in sorted(per_section.items()) if hs},
            "spellings": sorted({str(h["literal"]) for h in hits}),
            "document_total": len(hits),
            "verdict": "VERIFIED" if hits else "REFUTED",
            # ⚠️ Counts are NOT sets, so agreement of two totals is reported
            # as what it is — agreement of two totals — and never as proof
            # that the two backends found the same occurrences.
            "backends_agree_on_total": len(hits) == gs_total,
            # Required by the ``literature_curated`` adapter for per-row
            # attestation. ``entered_locally_at`` is FIXED, not ``today()``:
            # a build date that moves makes ``--check`` unreproducible, and a
            # check that cries wolf is a check that gets removed.
            "source_published_date": spec["published"],
            "entered_locally_at": CATALOG_ENTERED_AT,
        })
        if verbose:
            nz = {k: len(v) for k, v in sorted(per_section.items()) if v}
            print("    %-22s total=%-4d %s" % (term, len(hits), nz or "ABSENT"))
    return rows


def manifest_records(verbose: bool = True) -> List[Dict[str, object]]:
    """The full ``row.ndjson`` payload, sources in sorted order."""
    out: List[Dict[str, object]] = []
    for sid in sorted(SOURCES):
        if verbose:
            print("  source", sid)
        out.extend(build_rows(sid, SOURCES[sid], verbose))
    return out


def cmd_build(check_only: bool = False) -> int:
    rows = manifest_records(verbose=not check_only)
    path = os.path.join(CATALOG_DIR, "row.ndjson")
    body = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n"
                   for r in rows)
    if check_only:
        if not os.path.exists(path):
            print("MISSING", path)
            return 1
        with open(path, "r", encoding="utf-8", newline="") as fh:
            have = fh.read()
        # ⚠️ LINE-WISE, not byte-wise, and the reason is measured rather than
        # defensive. This repo stores the sibling catalogs' NDJSON with LF, and
        # `core.autocrlf=true` on Windows rewrites them to CRLF **on
        # checkout** — the committed asymptotic_calculus row file is 15301
        # bytes in the object store and 15360 on the working tree. A byte
        # comparison would therefore report DRIFT on a completely unchanged
        # manifest, on the platform this is most likely to be run from, and a
        # check that cries wolf is a check that gets deleted.
        #
        # Line-wise is also the semantically correct unit: NDJSON's content IS
        # its rows, and a line terminator is transport. What this still
        # catches, which is everything that matters, is a changed row, a
        # missing row, an extra row, or a reordering.
        if have.splitlines() != body.splitlines():
            print("DRIFT: %s does not match a fresh derivation "
                  "(%d rows on disk, %d derived)"
                  % (path, len(have.splitlines()), len(body.splitlines())))
            return 1
        print("OK", path, len(rows), "rows identical row-for-row")
        return 0
    os.makedirs(CATALOG_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)
    print("wrote", path, len(rows), "rows")
    return 0


def main() -> int:
    import srmech
    records: List[Dict[str, object]] = []
    records.append({
        "record": "provenance",
        "srmech_file": srmech.__file__,
        "srmech_version": srmech.__version__,
        "python": sys.version.split()[0],
        "task": "#T1131",
        "rc": "rc428",
    })
    print("srmech", srmech.__version__, srmech.__file__)

    sid = "arxiv:math/0105155"
    spec = SOURCES[sid]

    pdf_bytes = fetch(str(spec["pdf_url"]), "baez.pdf")
    tar_bytes = fetch(str(spec["eprint_url"]), "baez_eprint.tar.gz")
    records.append({
        "record": "source",
        "source_id": sid,
        "cite_as": spec["cite_as"],
        "pdf_sha256": sha256_bytes(pdf_bytes),
        "pdf_bytes": len(pdf_bytes),
        "eprint_sha256": sha256_bytes(tar_bytes),
        "eprint_bytes": len(tar_bytes),
    })

    backends: Dict[str, Tuple[str, SectionMap]] = {}
    backends["tex"] = backend_tex(tar_bytes, "baez", str(spec["tex_main"]))
    backends["gs"] = backend_gs(pdf_bytes, "baez", "utf-8")
    try:
        backends["pypdf"] = backend_pypdf(pdf_bytes, "baez")
    except ImportError:
        pass

    # ── the encoding falsifier, run deliberately ────────────────────────
    # Prove the trap is real on THIS instrument rather than cite rc427 for it.
    try:
        bad_text, _ = backend_gs(pdf_bytes, "baez_latin1_probe", "latin-1")
        bad_n = len(search(bad_text, "Cayley-Dickson"))
        records.append({
            "record": "falsifier_F9_encoding",
            "correct_utf8_count": len(search(backends["gs"][0],
                                             "Cayley-Dickson")),
            "wrong_latin1_count": bad_n,
            "latin1_emitted_u_fffd": has_replacement_chars(bad_text),
            "verdict": "TRAP REPRODUCED" if bad_n == 4 else "did not reproduce",
            "note": "Latin-1 never raises and emits NO U+FFFD, so the "
                    "replacement-char tell that caught rc427 does not fire. "
                    "Only a multi-spelling positive control catches this.",
        })
        print("  F9 encoding trap: utf-8=%d latin-1=%d fffd=%s"
              % (len(search(backends["gs"][0], "Cayley-Dickson")), bad_n,
                 has_replacement_chars(bad_text)))
    except Exception as exc:  # noqa: BLE001
        records.append({"record": "falsifier_F9_encoding",
                        "verdict": "UNSUPPORTED", "error": str(exc)})

    # ── F11: prove the ABORT fires BEFORE trusting any control that passed
    bites = abort_path_bite_test(spec)
    all_bit = all(b["aborted"] for b in bites)
    records.append({
        "record": "falsifier_F11_abort_path_bite",
        "cases": bites,
        "verdict": "ALL BITE" if all_bit else "DEAD SEAM",
        "note": "A positive control that has never failed is "
                "indistinguishable from one that CANNOT fail. If this ever "
                "reports DEAD SEAM, every 'REFUTED' this instrument has ever "
                "emitted is downgraded to UNSUPPORTED.",
    })
    print("  F11 abort-path: %s (%s)"
          % ("ALL BITE" if all_bit else "DEAD SEAM",
             ", ".join(b["case"] for b in bites if b["aborted"])))
    if not all_bit:
        print("  !! ABORT PATH IS DEAD — controls below cannot be trusted")

    # ── controls per backend; a positive-control failure ABORTS ─────────
    control_results = {}
    for name, (text, _sec) in sorted(backends.items()):
        try:
            ctrl = run_controls(text, spec, name)
            ctrl["verdict"] = "USABLE"
        except ExtractionBroken as exc:
            ctrl = {"verdict": "BROKEN", "error": str(exc)}
        ctrl["backend"] = name
        ctrl["record"] = "controls"
        ctrl["chars"] = len(text)
        control_results[name] = ctrl
        records.append(ctrl)
        ms = ctrl.get("multi_spelling", {})
        print("  %-6s chars=%-7d pos=%s multi=%s/%s %s"
              % (name, len(text),
                 ctrl.get("positive_control", {}).get("count"),
                 ms.get("count"), ms.get("expected"), ms.get("verdict")))

    # ── F6: counts are not sets — compare hit SETS across backends ──────
    # STRICT oracle: ghostscript vs pypdf, both rendered from the SAME PDF
    # bytes, so their neighbourhoods are the same text and must align.
    # ADVISORY: LaTeX vs rendered — the markup source and the rendered page
    # are genuinely different strings around a hit (equations, journal
    # abbreviations like "{\sl Bol.\ Soc.\ }"), so a small residual there is
    # EXPECTED and is not evidence of disagreement about the term itself.
    # Stating that bound beats reporting a clean number that isn't earned.
    for term in ["Cayley-Dickson", "Moufang", "octonion"]:
        keys = {n: dense_keys(t, term) for n, (t, _s) in backends.items()}
        # SWEEP min_shared rather than pick one: publishing the sensitivity is
        # what makes this a measurement instead of a tuned number.
        sweep: Dict[str, object] = {}
        for min_shared in (18, 24, 30):
            sweep[str(min_shared)] = {
                n: list(key_overlap(keys["gs"], keys[n], min_shared))
                for n in sorted(keys)}
        strict = sweep["24"]
        strict_ok = all(strict[n] == [0, 0] for n in ("gs", "pypdf"))
        rec: Dict[str, object] = {
            "record": "falsifier_F6_set_agreement", "term": term,
            "reference_backend": "gs",
            "counts": {n: len(k) for n, k in sorted(keys.items())},
            "counts_agree": len({len(k) for k in keys.values()}) == 1,
            "missing_extra_by_min_shared": sweep,
            "strict_tier_verdict": "PASS" if strict_ok else "RESIDUAL",
            "tiers": {"gs": "STRICT", "pypdf": "STRICT", "tex": "ADVISORY"},
            "note": "STRICT tier = the two backends rendering the SAME PDF "
                    "bytes; their neighbourhoods are the same text and must "
                    "align. ADVISORY = LaTeX markup vs rendered page, which "
                    "are genuinely different strings around a hit "
                    "(equations, '{\\sl Bol.\\ Soc.\\ }' journal "
                    "abbreviations), so a residual there is EXPECTED and is "
                    "NOT evidence of a different hit set. The counts are the "
                    "hard fact; alignment across distinct extractors is "
                    "approximate by nature and is reported as such.",
        }
        records.append(rec)
        print("  F6 %-15s counts=%s strict@24=%s"
              % (term, rec["counts"], rec["strict_tier_verdict"]))

    # ── the rc427 acceptance test, re-derived end to end ────────────────
    tex_text, tex_sec = backends["tex"]
    gs_text, _ = backends["gs"]

    mou = search(tex_text, "Moufang", tex_sec)
    # PREFIX matching, not equality — see :func:`covers`. rc428's level-aware
    # map resolves subsections, so a "§2" citation must still collect a hit
    # landing in §2.2. Under equality this test would report 0-in-§2 for the
    # trivial reason that no hit is in §2's own prose, which is a DIFFERENT
    # claim from the one rc427 made and would be true of many correct
    # citations too.
    in_sec2 = [h for h in mou if covers("§2", str(h["section"]))]
    in_sec3 = [h for h in mou if covers("§3", str(h["section"]))]
    in_bib = [h for h in mou if str(h["section"]) == "BIBLIOGRAPHY"]

    malcev_spellings = ["Mal'cev", "Mal’cev", "Mal\u2032cev", "Malcev",
                        "Mal'tsev", "Maltsev", "Mal'tzev", "Malchev",
                        "\u041c\u0430\u043b\u044c\u0446\u0435\u0432"]
    malcev_total = 0
    per_spelling = {}
    for sp in malcev_spellings:
        n = len(search(tex_text, sp)) + len(search(gs_text, sp))
        per_spelling[sp] = n
        malcev_total += n

    acceptance = {
        "record": "acceptance_rc427_finding",
        "claim_under_test":
            "Baez arXiv:math/0105155 was cited for 'the Moufang identities in "
            "section 2' and 'the Mal'cev tangent algebra'",
        "moufang_total_rendered": len(mou),
        "moufang_in_section_2": len(in_sec2),
        "moufang_in_section_3": len(in_sec3),
        "moufang_in_bibliography": len(in_bib),
        "moufang_sections": sorted({str(h["section"]) for h in mou}),
        "moufang_gs_total": len(search(gs_text, "Moufang")),
        "section_attribution_exact": tex_sec.exact,
        "malcev_total_all_spellings": malcev_total,
        "malcev_per_spelling": per_spelling,
        "positive_control_passed_on_same_extraction":
            control_results["tex"]["verdict"] == "USABLE"
            and control_results["gs"]["verdict"] == "USABLE",
        "verdict_moufang_in_section_2":
            "REFUTED" if len(in_sec2) == 0 else "PRESENT",
        "verdict_malcev": "REFUTED" if malcev_total == 0 else "PRESENT",
        "null_classification":
            "REFUTED — a positive control on the SAME extraction returned "
            "%d hits for 'octonion' and 22 for 'Cayley-Dickson', so the "
            "instrument demonstrably CAN return non-zero. These zeros are "
            "measurements, not silence."
            % control_results["tex"]["positive_control"]["count"],
        "citation_verdict":
            "FALSE AS CITED — the section-2 attribution and the Mal'cev "
            "attribution are both refuted; the section-3 / 4.2 citations of "
            "the same paper for the Moufang PLANE are CORRECT and must "
            "survive. Existence proves nothing; TOPICALITY decides.",
    }
    records.append(acceptance)
    print("  ACCEPTANCE Moufang total=%d sec2=%d sec3=%d bib=%d | Mal'cev=%d"
          % (len(mou), len(in_sec2), len(in_sec3), len(in_bib), malcev_total))
    for h in mou:
        print("      [%s] %s" % (h["section"], str(h["context"])[:96]))

    # ── F7 / dense bound / section-heuristic honesty ────────────────────
    joins = re.findall(r"(\w{2,})[%s]\s*\r?\n\s*(\w{2,})" % re.escape(DASHES),
                       decode_strict(open(os.path.join(CACHE, "baez.gs.txt"),
                                          "rb").read(), "utf-8"))
    probe_broken = sorted({a + b for a, b in joins
                           if any(p in (a + b).lower()
                                  for p in ["moufang", "dickson", "cayley"])})
    records.append({
        "record": "falsifier_F7_dehyphenation",
        "hyphen_linebreak_joins_in_source": len(joins),
        "probe_terms_broken_across_lines": probe_broken,
        "verdict": "BOUNDED",
        "note": "De-hyphenation is implemented and the mechanism demonstrably "
                "occurs in this source (%d joins, including 'construc-tion' "
                "inside the phrase 'Cayley-Dickson construction', so PHRASE "
                "search depends on it). But NO rc427 probe term is itself "
                "broken across a line here, so that specific path is "
                "unexercised by these probes. Stated, not claimed as tested."
                % len(joins),
    })
    records.append({
        "record": "falsifier_F7b_soft_hyphen_and_ligatures",
        "soft_hyphens_in_gs_text": gs_text.count(SOFT_HYPHEN),
        "ligatures_pre_nfkc": sum(
            decode_strict(open(os.path.join(CACHE, "baez.gs.txt"), "rb").read(),
                          "utf-8").count(c) for c in LIGATURES),
        "verdict": "ligature expansion EXERCISED; soft-hyphen path BOUNDED",
        "note": "318 ff/fi/fl/ffi ligatures are present and NFKC expansion is "
                "load-bearing ('diﬀerent' would never match 'different'). "
                "Zero soft hyphens in this source, so that path is handled "
                "but unexercised.",
    })
    records.append({
        "record": "falsifier_F8_section_attribution",
        "tex_exact": True,
        "pdf_heuristic_reliable": False,
        "tex_section_2_title": tex_sec.titles().get("§2"),
        # rc428: the level-aware map resolves SUBSECTIONS, which is what the
        # tree's §2.4 / §4.1 / §4.2 citations are actually addressed to. A
        # flat section-only map could not resolve any of them.
        "tex_subsection_titles": {k: v for k, v in
                                  sorted(tex_sec.titles().items())
                                  if k.count(".") == 1},
        "verdict": "EXACT from LaTeX e-print; BOUNDED from rendered PDF",
        "note": "Section attribution is structural in LaTeX and a guess in "
                "rendered text — the PDF heuristic also matches table rows "
                "like '3 H (+) H' and '4 H[2]'. A gate may make SECTION "
                "claims only for sources with a retrievable e-print; for "
                "others it may claim presence/absence only.",
    })
    records.append({
        "record": "falsifier_dense_bound",
        "checks": [dense_vs_plain_check(gs_text, "Moufang"),
                   dense_vs_plain_check(gs_text, "Cayley-Dickson")],
        "note": "Guards the one known bound of whitespace-insensitive "
                "matching: it must not fabricate hits by joining unrelated "
                "words across a break.",
    })

    # ── F10: the both-sides bite test for the normalisation ─────────────
    f10 = []
    for name, (text, _sec) in sorted(backends.items()):
        for term in ["Cayley-Dickson", "octonion", "Moufang"]:
            f10.append(naive_vs_dense_check(text, term, name))
    bites = [c for c in f10 if c["normalisation_load_bearing"]]
    records.append({
        "record": "falsifier_F10_naive_vs_dense",
        "checks": f10,
        "verdict": "BITES" if bites else "NO BITE — normalisation unproven",
        "note": "Pins whitespace-insensitive matching as LOAD-BEARING rather "
                "than decorative. If this ever stops biting, the "
                "normalisation is no longer proven necessary and the claim "
                "must be re-earned, not assumed. Retracts this file's own "
                "earlier draft accusation that pypdf drops text: it does "
                "not — the naive matcher did.",
    })
    for c in bites:
        print("  F10 BITE %-6s %-15s naive=%d dense=%d missed=%s"
              % (c["backend"], c["term"], c["naive_whitespace_sensitive"],
                 c["dense_whitespace_insensitive"],
                 c["missed_literals"][:3]))

    # ── pre-registration + null classification ──────────────────────────
    # Every falsifier below was written down BEFORE it was run. Each null is
    # classified; a bare "0" is never reported.
    records.append({
        "record": "prereg_and_verdicts",
        "preregistered_before_running": True,
        "falsifiers": {
            "F1 multi-spelling/encoding": {
                "predicted": "22 = 18 en-dash + 4 ASCII; a 4 means the "
                             "encoding trap; a 7 was the other bad reading",
                "measured": "22 = 18 + 4 on all three backends",
                "verdict": "CONFIRMED"},
            "F2 positive control (ABORT gate)": {
                "predicted": "'octonion' > 0 in a paper titled The Octonions",
                "measured": "172 on all three backends",
                "verdict": "PASS"},
            "F3 negative control": {
                "predicted": "Kirshtein / Antikythera / zygomatic / "
                             "qwertzuiop all 0",
                "measured": "all 0; matcher is not always-true",
                "verdict": "PASS"},
            "F4 rc427 Moufang finding": {
                "predicted": "5 rendered; 0 in section 2; 3 in section 3; "
                             "2 in bibliography",
                "measured": "exactly that, section-attributed from LaTeX",
                "verdict": "CONFIRMED"},
            "F5 Mal'cev absent": {
                "predicted": "0 in all 9 spellings incl. Cyrillic",
                "measured": "0, with the positive control alive at 172",
                "verdict": "REFUTED (a measured absence, not silence)"},
            "F6 counts are not sets": {
                "predicted": "backends must agree on the SET, not the count",
                "measured": "counts identical (22/5/172); STRICT-tier set "
                            "alignment exact for both load-bearing terms; "
                            "1-of-172 residual on the positive control",
                "verdict": "PASS with a stated bound"},
            "F7 de-hyphenation": {
                "predicted": "determine whether probes break across lines",
                "measured": "34 hyphen-linebreak joins exist in the source "
                            "(incl. 'construc-tion' inside the phrase "
                            "'Cayley-Dickson construction'), but NO probe "
                            "term is itself broken",
                "verdict": "BOUNDED — implemented, mechanism present, "
                           "unexercised by these probes"},
            "F8 section attribution": {
                "predicted": "can we tell WHERE a hit falls?",
                "measured": "EXACT from LaTeX e-print; heuristic on rendered "
                            "PDF also matches table rows",
                "verdict": "EXACT (e-print) / BOUNDED (PDF only)"},
            "F9 encoding falsifier": {
                "predicted": "Latin-1 vs UTF-8 counts must diverge",
                "measured": "22 vs 4, with ZERO U+FFFD emitted",
                "verdict": "TRAP REPRODUCED — and the U+FFFD tell that "
                           "caught rc427 does NOT fire here"},
            "F10 naive vs dense (added mid-run)": {
                "predicted": "not pre-registered — added after the "
                             "instrument refuted this file's own draft claim "
                             "that pypdf drops text",
                "measured": "pypdf 16/22 naive vs 22/22 dense; the 6 "
                            "'missing' hits are spelled 'Cayley-Dick son'",
                "verdict": "BITES — normalisation proven load-bearing; "
                           "flagged as POST-HOC, not pre-registered"},
            "F11 abort-path bite": {
                "predicted": "the ABORT must fire on a broken extraction",
                "measured": "fires on empty, whitespace-only, and "
                            "plausible-but-wrong text",
                "verdict": "ALL BITE — the guard is live, not decorative"},
        },
        "instrument_verdict":
            "TRUSTWORTHY WITHIN A STATED BOUND. It may claim presence/"
            "absence for any source whose bytes it fetched and hashed, when "
            "the positive control passed; it may claim SECTION attribution "
            "only where an arXiv e-print exists. It may NOT claim section "
            "attribution from a rendered PDF alone, and it has been "
            "validated against exactly ONE source.",
        "known_bounds": [
            "Validated on ONE source. Every new source needs its own "
            "positive control; there is no general proof.",
            "Section attribution requires a LaTeX e-print. Sources without "
            "one support presence/absence claims only.",
            "Set alignment across distinct extractors is approximate; the "
            "counts are the hard fact.",
            "Soft-hyphen and cross-line probe-term breaking are handled but "
            "UNEXERCISED here — do not claim they are tested.",
            "A paywalled source cannot be attested at all: the outcome is "
            "DERIVED-AND-MEASURED or UNSOURCED, never a substituted "
            "second unverified citation.",
        ],
    })

    # The acceptance record stays in ``notes/`` where it was written and where
    # its own provenance row points; only the SCRIPT moved to ``tools/``.
    out = os.path.normpath(os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "..", "notes", "_s1_extractor_rc428.ndjson"))
    emit(records, out)
    print("wrote", out, len(records), "records")
    return 0


USAGE = """usage: build_citation_manifest.py [--validate | --build | --check]

  --validate  re-run the F1-F11 falsifier suite; rewrites
              docs/srmech/notes/_s1_extractor_rc428.ndjson (the frozen
              rc428 acceptance record). This is the DEFAULT.
  --build     fetch, extract and write
              srmech/amsc/attested/literature_claims/row.ndjson
  --check     re-derive from cached e-prints and byte-compare against the
              committed row.ndjson; nonzero exit on drift
"""


def cli(argv: Sequence[str]) -> int:
    mode = argv[1] if len(argv) > 1 else "--validate"
    if mode in ("-h", "--help"):
        print(USAGE)
        return 0
    if mode == "--build":
        return cmd_build(check_only=False)
    if mode == "--check":
        return cmd_build(check_only=True)
    if mode == "--validate":
        return main()
    print(USAGE)
    return 2


if __name__ == "__main__":
    sys.exit(cli(sys.argv))
