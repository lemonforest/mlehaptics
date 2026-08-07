"""srmech.introspect.search — the need-shaped INDEX over the registries.

WHY THIS MODULE EXISTS
======================
The introspect layer's **authored half is at 100% and its derived half was at
0%**. ``ToolEntry.explanation`` and ``ToolEntry.example`` are both populated for
every registered srmech op and held there by a 100% floor
(``tests/test_tool_docs_coverage_rc240.py:52,:62``) — and before this module
**no accessor read either one**. :meth:`ToolSchema.resolve` matches ``name``,
and only whole dotted segments of it: ``resolve("winding_fold")`` hits,
``resolve("winding")`` returns ``None``. So the registry could answer *"what is
the op called ``X``"* and could not answer *"what do you have for X"* — the
question a caller actually arrives with.

This module closes that with ONE accessor. No new system, no new schema, and
no new data: the corpus it indexes is the prose that already ships.

**rc412 (`#T1093`) extends the same finding to the STRUCTURED half.** rc305
added ``ToolEntry.composes`` / ``ToolEntry.preserves``; both ride the wheel and
both are baked into the C registry — and no accessor read either one either.
They are now indexed alongside the prose. The index is the *lesser* half of
that repair and :func:`_op_fields` says why: the primary reader is
:meth:`~srmech.introspect.tool_schema.ToolSchema.composition`, because the
question a caller holding a primitive arrives with — *what is built FROM
this?* — is the REVERSE of a directed edge, and no text index can invert one.

THE CASCADE — every stage is a shipped, registered op
=====================================================
This is not new capability. It is a registered composition of ops that already
ship, which is also what collapses its ADR-0009 story (see PARITY below)::

    E   catalog        get_tool_schema() + carrier_schema()
    F/B render + TLV   srmech.math.tlv.tlv_pack  — one TLV frame per row
    A   content-addr   srmech.amsc.format.sha256_bytes — the corpus witness
    G   byte-search    srmech.math.search.byte_search — tf per frame, df = frames hit
    N   rational       srmech.math.q.Q(N - df, df) — EXACT idf, no float, no log
    G   byte-search    byte_search over the NAME LEAF — the 4x boost
    E   catalog/rank   srmech.cascade.top_k_by_score — accepts exact Q directly

**Float-free end to end**, not merely at the idf stage: ``top_k_by_score``
takes the exact ``Q`` scores without a float cast (verified ``Q(1,3), Q(7,2),
Q(5,4) -> [1, 2, 0]``). There is no ``abs()`` anywhere — the scores are
non-negative by construction because ``tf`` and ``df`` are counts, so no
Class-K pin-slot is needed and none is faked.

The frame join is :func:`srmech.math.tlv.tlv_pack` (Class B) and NOT
``str.join``. That is deliberate and load-bearing: with a bare join the F/B
label on this cascade would be decorative and the cascade-shape claim would be
false. It also buys a real property — TLV framing makes a field boundary
unambiguous, so a needle can never match across two fields that happen to abut.

ADR-0011 — DERIVED ON DEMAND, NOTHING PERSISTED
===============================================
ADR-0011's text on exactly this problem: *"If a legible view is wanted, derive
it on demand through the tool surface; do not persist it."* The frame set is
rebuilt on every call and thrown away. There is no cache file, no pickle and no
process-global memo — which is also why the result can never be stale against a
profile registration that happened one line earlier.

The ``sha256_bytes`` frame digest is ADR-0011's CACHE-vs-WITNESS admissibility
condition satisfied: it is carried out of band on
:attr:`SearchResult.witness`, so a caller that DOES choose to hold a derived
view has something to compare against the source, and disagreement is loud.

WHAT ``why`` AND ``reach`` ARE FOR
==================================
ADR-0012 sets the standard for this surface at AUTONOMOUS COMPOSITION: the
answer has to be actionable **without a second call**. A bare ranked name list
fails that — it tells a caller which row won and not why it won or how to reach
it. So every record carries:

* ``why``   — the FIELD that matched (``explanation``, ``example.worked``,
  ``carrier.description``, ``name``, ``composes``, ``preserves``), so a caller
  can see whether the hit is the op's own subject, a pointer inside a
  neighbour's prose, or a declared structural edge;
* ``reach`` — the importable call form, ready to paste.

``reach`` matters more than it looks. The measured failure it fixes is a
*module-path* error, not a name error: a caller who wants the exact-rational
carrier guesses ``srmech.math.rational.Q`` for ``srmech.math.q.Q``. Returning
the name alone would have left that caller exactly as stuck.

PARITY (ADR-0009)
=================
This op classifies ``non_compute`` / ``composes_c`` — the same bucket the tree
already gives every other registry accessor, including ``get_tool_schema``,
``tool_schema_view``, ``carrier_schema``, ``responsion_schema`` and
``top_k_by_score`` itself. The obligation that attaches to that bucket is
TRANSITIVE STANDALONE-C REACHABILITY (``test_rosetta_completeness.py:1276``),
not a dedicated ``srmech_*`` entry point, and it is satisfied: every ledger op
this reaches is standalone-ready (``tlv_pack`` / ``sha256_bytes`` /
``byte_search`` are ``c_dispatched``; ``get_tool_schema`` / ``carrier_schema``
/ ``top_k_by_score`` are ``non_compute`` leaves). A bare-C host has
``srmech_tool_registry_count/_get/_find``, ``srmech_carrier_registry_*``,
``srmech_byte_search`` and ``srmech_sha256`` — the retrieval half of this
cascade has been executed in C over every entry the registry carries.
(That last clause named a literal entry count until rc412; it had been stale
since the next op landed. ``srmech_tool_registry_count()`` is the number, and
it is the only spelling that cannot go stale.)

This is NOT an exemption claim. ADR-0009 §4 exempts only ``srmech.mcp`` /
``srmech.llm`` and the ``host_glue`` rows, and *"Nothing else is exempt."*
Introspect is not exempt; it simply is not a compute kernel, and the ledger
distinguishes those two things on purpose.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

__all__ = ["SearchResult", "search"]


# ──────────────────────────────────────────────────────────────────────
# Tokenisation
#
# Deliberately NO hand-tuned stoplist. The exact-Q idf gate below already
# suppresses common words harder than a word list does, and it does it from
# the corpus rather than from someone's judgement: a token present in every
# frame scores ``Q(N - N, N) == 0`` EXACTLY, so it contributes nothing at all
# rather than being "downweighted". The research leg that tuned a 14-word
# stoplist also measured the ranks UNCHANGED with it removed, so the list was
# carrying no signal — and a tuned constant that carries no signal is a
# liability, because it looks like it is doing something.
#
# ``_MIN_TOKEN`` is 2, not 1: a single character matches inside almost every
# frame, so df -> N and its idf collapses to ~0 anyway. Dropping it early
# saves the scan rather than changing the answer.
# ──────────────────────────────────────────────────────────────────────
_MIN_TOKEN = 2

#: Occurrence counting saturates here. This is a BOUNDED loop, not a guess:
#: tf is a sub-linear signal (a row that says "rank" 40 times is not 40x more
#: about rank than one that says it 20 times), and the cap keeps the byte
#: scan O(cap) per token/frame pair instead of O(occurrences).
_TF_CAP = 32

#: The name-leaf multiplier. A token appearing in the op's own leaf name is
#: worth 4x the same token buried in prose — ``gcd`` in ``cyclic.gcd`` is the
#: op's subject; ``gcd`` inside another op's SIBLINGS paragraph is a pointer.
_LEAF_BOOST = 4


def _tokenize(text: str) -> Tuple[bytes, ...]:
    """Lowercase alphanumeric runs, as bytes, deduplicated, order-preserving.

    Underscores SPLIT. ``top_k_by_score`` tokenizes to ``top``/``by``/``score``
    on the query side, while the frame keeps the underscored form intact — and
    because the match is a substring scan rather than a word match, the query
    tokens still find it. Splitting the query and not the corpus is what makes
    ``"top k score"`` reach ``top_k_by_score`` without a stemmer.
    """
    out: List[bytes] = []
    seen = set()
    buf: List[str] = []
    for ch in text.lower():
        if ch.isalnum() and ch.isascii():
            buf.append(ch)
            continue
        if buf:
            tok = "".join(buf).encode("ascii")
            buf = []
            if len(tok) >= _MIN_TOKEN and tok not in seen:
                seen.add(tok)
                out.append(tok)
    if buf:
        tok = "".join(buf).encode("ascii")
        if len(tok) >= _MIN_TOKEN and tok not in seen:
            seen.add(tok)
            out.append(tok)
    return tuple(out)


def _count(haystack: bytes, needle: bytes) -> int:
    """Occurrences of ``needle`` in ``haystack``, saturating at :data:`_TF_CAP`.

    Class G. Routed through :func:`srmech.math.search.byte_search` — the
    registered, C-dispatched byte scan — and NOT through ``bytes.count``.
    That is not ceremony: hand-rolling the scan here would make the G stage of
    this cascade a claim rather than a fact, and would hide the op from the
    native-dispatch path a bare-C host uses.
    """
    from ..math.search import byte_search

    found = 0
    start = 0
    limit = len(haystack)
    while start < limit and found < _TF_CAP:
        hit = byte_search(haystack[start:], needle)
        if hit is None:
            break
        found += 1
        start += hit + len(needle)
    return found


# ──────────────────────────────────────────────────────────────────────
# Frame construction — E (catalog) -> F/B (render + TLV) -> A (content-address)
# ──────────────────────────────────────────────────────────────────────

def _as_text(value: Any) -> str:
    """Render a nested registry value as flat, order-stable, searchable text.

    NOT ``json.dumps``, and that is deliberate on two counts.

    **The ban.** ``srmech/_json.py`` is the self-hosted front door, but it is
    the **READ half only** — ``json.dumps`` is explicitly not self-hosted there,
    because ``srmech_json_write_ws`` declines the non-finite floats stdlib
    emits. So the front door genuinely cannot serve a serialise call here, and
    the stdlib import ledger is DOWN-ONLY. The resolution is neither to raise
    the ceiling nor to force the front door: **this call site never needed JSON
    at all.**

    **The quality reason, which is the better one.** The frame is an input to a
    SUBSTRING SCAN, not a wire format. ``json.dumps`` defaults to
    ``ensure_ascii=True``, so it would render ``ℚ`` as ``\\u211a`` and make every
    non-ASCII character in the corpus unsearchable — in a registry whose prose
    is full of ``ℚ``, ``𝕆``, ``Σ`` and ``→``. It would also inject ``{``, ``"``
    and ``:`` noise that no query can ever match. Flattening to bare text keeps
    the characters literal and drops the punctuation.

    Order is made explicit rather than inherited: dict keys are sorted, so the
    frame — and therefore the ``sha256`` witness — is reproducible independently
    of insertion order.
    """
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return " ".join(
            f"{key} {_as_text(value[key])}"
            for key in sorted(value, key=str))
    if isinstance(value, (list, tuple)):
        return " ".join(_as_text(item) for item in value)
    return str(value)


def _op_fields(entry: Any) -> Tuple[Tuple[str, str], ...]:
    """``(label, text)`` pairs for one ToolEntry, in TLV tag order.

    ``example`` is flattened per sub-key so ``why`` can name
    ``example.worked`` specifically — the sub-key that carries the executable
    transcript, and therefore the one whose hit tells a caller the answer is
    a real call and not a description of one.

    ``composes`` / ``preserves`` join the index at rc412 (`#T1093`). They are
    the SAME defect this module was written for, one field-pair later: rc305
    added two structured ToolEntry fields, they ride the wheel, the C
    serialiser bakes them into ``srmech_tool_registry.c`` — and until rc412
    **no accessor read either one**. The only consumers were
    ``ToolEntry.to_jsonable``, the curated merge, and the C emitter, none of
    which is a caller-facing question. Populating an unread field only moves
    a hash, so the reader lands before the rows do.

    An EMPTY field contributes nothing — no label, no bytes, no frame change.
    That is deliberate on two counts: it is the same key-omission
    ``to_jsonable`` and the C serialiser already perform, and it keeps a leaf
    op (for which empty is the *correct* default, ``tool_schema.py``) exactly
    as searchable as it was.

    **What this buys is bounded, and the bound is measured rather than
    guessed.** Over the declared sub-op references shipped at rc412 the
    ``composes`` text wins the ``why`` attribution on NONE of them: a row's
    own prose almost always already names the ops it composes, so the tuple
    adds a frame the corpus was silently missing rather than a new retrieval
    signal. The reader that actually answers a composition question is
    :meth:`~srmech.introspect.tool_schema.ToolSchema.composition`, which also
    carries the REVERSE edge this index cannot express at all.
    """
    fields: List[Tuple[str, str]] = [
        ("name", entry.name or ""),
        ("category", entry.category or ""),
        ("summary", entry.summary or ""),
        ("explanation", entry.explanation or ""),
    ]
    example = entry.example
    if isinstance(example, dict):
        for key in sorted(example):
            fields.append((f"example.{key}", _as_text(example[key])))
    elif example:
        fields.append(("example", _as_text(example)))
    # rc412 (`#T1093`) — the compose/preserve layer becomes reachable. Appended
    # AFTER example so the pre-rc412 field order is untouched for every row
    # that declares neither, which is most of them.
    if entry.composes:
        fields.append(("composes", _as_text(entry.composes)))
    if entry.preserves:
        fields.append(("preserves", _as_text(entry.preserves)))
    return tuple(fields)


def _carrier_fields(name: str, row: Dict[str, Any]) -> Tuple[Tuple[str, str], ...]:
    """``(label, text)`` pairs for one carrier row, in TLV tag order."""
    fields: List[Tuple[str, str]] = [("name", name)]
    for key in ("description", "capability", "example", "ops", "variables"):
        value = row.get(key)
        if value in (None, "", [], {}):
            continue
        fields.append((f"carrier.{key}", _as_text(value)))
    return tuple(fields)


class _Frame:
    """One indexable row: its identity, its TLV blob, and its field split."""

    __slots__ = ("kind", "name", "leaf", "blob", "fields", "reach")

    def __init__(self, kind: str, name: str, leaf: bytes,
                 blob: bytes, fields: Tuple[Tuple[str, bytes], ...],
                 reach: str) -> None:
        self.kind = kind
        self.name = name
        self.leaf = leaf
        self.blob = blob
        self.fields = fields
        self.reach = reach


def _op_reach(name: str) -> str:
    """The importable call form for a registered op.

    Uses the EXPOSED dotted name, not the defining module: ``srmech.cascade.
    top_k_by_score`` is importable as written even though it is defined in
    ``srmech.cascade.composites``, and the exposed path is the one the MCP
    dispatcher resolves.
    """
    if "." not in name:
        return f"import {name}"
    module, _, leaf = name.rpartition(".")
    return f"from {module} import {leaf}"


def _carrier_reach(name: str) -> str:
    """The importable call form for a carrier row.

    Carrier rows carry no module path of their own (a measured gap — the
    string ``srmech.math.q`` occurs zero times in the ``Q`` row), so the
    honest reach is the registry accessor that yields the row, not a guess at
    where the class lives.
    """
    return (f"from srmech.introspect.carrier_schema import carrier_schema; "
            f"carrier_schema()[{name!r}]")


def _build_frames(scope: str) -> Tuple[Tuple[_Frame, ...], str]:
    """Build the frame set and its content-address witness.

    Returns ``(frames, witness)``. Nothing is cached — see the ADR-0011 note
    in the module docstring.
    """
    from ..amsc.format import sha256_bytes
    from ..math.tlv import tlv_pack

    frames: List[_Frame] = []

    if scope in ("all", "ops"):
        from .tool_schema import get_tool_schema, warmup_all

        warmup_all()
        for entry in get_tool_schema().tools:
            pairs = _op_fields(entry)
            frames.append(_frame_from_pairs(
                "op", entry.name, pairs, _op_reach(entry.name), tlv_pack))

    if scope in ("all", "carriers"):
        from .carrier_schema import carrier_schema

        rows = carrier_schema()
        for name in sorted(rows):
            pairs = _carrier_fields(name, rows[name])
            frames.append(_frame_from_pairs(
                "carrier", name, pairs, _carrier_reach(name), tlv_pack))

    # Class A — the corpus content-address. Order-dependent by construction,
    # which is what makes it a witness: any add, removal, reorder or prose
    # edit moves it.
    witness = sha256_bytes(b"".join(f.blob for f in frames))
    return tuple(frames), witness


def _frame_from_pairs(kind: str, name: str,
                      pairs: Tuple[Tuple[str, str], ...],
                      reach: str, tlv_pack: Any) -> _Frame:
    """TLV-pack one row's fields into its frame (Class F render + Class B TLV)."""
    field_bytes: List[Tuple[str, bytes]] = []
    chunks: List[bytes] = []
    for tag, (label, text) in enumerate(pairs, start=1):
        raw = text.lower().encode("utf-8", "replace")
        field_bytes.append((label, raw))
        chunks.append(tlv_pack(tag, raw))
    leaf = name.rpartition(".")[2].lower().encode("utf-8", "replace")
    return _Frame(kind, name, leaf, b"".join(chunks),
                  tuple(field_bytes), reach)


# ──────────────────────────────────────────────────────────────────────
# The public surface
# ──────────────────────────────────────────────────────────────────────

class SearchResult(tuple):
    """The ranked records, plus the corpus witness they were derived from.

    A ``tuple`` SUBCLASS, so every consumer that treats the return value as a
    plain tuple of dicts — indexing, iteration, ``len``, unpacking, JSON
    serialisation — is unaffected. :attr:`witness` rides alongside rather than
    inside the records, which keeps the record shape exactly the five
    documented keys.
    """

    # No ``__slots__``: CPython rejects a nonempty ``__slots__`` on a ``tuple``
    # subclass outright (``TypeError: nonempty __slots__ not supported for
    # subtype of 'tuple'``), because the variable-length tuple storage and a
    # fixed slot table cannot share one layout.

    def __new__(cls, records: Sequence[Dict[str, Any]], witness: str):
        self = super().__new__(cls, tuple(records))
        self.witness = witness
        return self


def search(query: str, *, k: int = 10,
           scope: str = "all") -> "SearchResult":
    """Rank the registries against a NEED, phrased in the words it was felt in.

    This is the inverse of :func:`srmech.introspect.describe`. ``describe()``
    answers *"what is the shape"*; this answers *"I want X"*. They read the
    same corpus and differ only in direction.

    :param query: the need, in natural words. Not a name pattern — reach for
        :meth:`ToolSchema.resolve` when you already know the exact dotted name.
    :param k: how many records to return (clamped to the corpus size).
    :param scope: ``"ops"`` (the 556-row verb registry), ``"carriers"`` (the
        29-row operand/noun registry), or ``"all"`` (the union, default).
    :returns: a :class:`SearchResult` — a tuple of records, highest score
        first, each ``{"kind", "name", "score", "why", "reach"}``:

        * ``kind``  — ``"op"`` or ``"carrier"``
        * ``name``  — the registry key
        * ``score`` — an exact :class:`srmech.math.q.Q`, never a float
        * ``why``   — the field that contributed most (``explanation``,
          ``example.worked``, ``carrier.description``, ``name``, …)
        * ``reach`` — the importable call form

    Rows that match nothing are omitted, so an unanswerable query returns an
    EMPTY result rather than the k least-bad rows. That distinction is the
    whole difference between "we have nothing for this" and "here is some
    noise", and a caller cannot recover it from a padded list.
    """
    if not isinstance(query, str):
        raise TypeError(f"query must be str, got {type(query).__name__}")
    if scope not in ("all", "ops", "carriers"):
        raise ValueError(
            f"scope must be 'all', 'ops' or 'carriers', got {scope!r}")
    if k <= 0:
        raise ValueError(f"k must be positive, got {k}")

    from ..cascade import top_k_by_score
    from ..math.q import Q

    frames, witness = _build_frames(scope)
    tokens = _tokenize(query)
    n_frames = len(frames)
    if not tokens or n_frames == 0:
        return SearchResult((), witness)

    # ── G: term frequency per frame, and document frequency per token ──
    tf: Dict[bytes, List[int]] = {}
    df: Dict[bytes, int] = {}
    for token in tokens:
        counts = [_count(f.blob, token) for f in frames]
        tf[token] = counts
        df[token] = sum(1 for c in counts if c)

    # ── N: EXACT idf as a rational. No float, no log, no epsilon. ──
    # Q(N - df, df) is 0 exactly when a token is in every frame and grows
    # without bound as df -> 1, which is the discrimination shape tf-idf
    # wants — reached here by exact rational arithmetic instead of by a
    # transcendental the substrate would have to approximate.
    idf: Dict[bytes, Any] = {}
    for token in tokens:
        d = df[token]
        if d == 0:
            continue
        idf[token] = Q(n_frames - d, d)
    if not idf:
        return SearchResult((), witness)

    # ── G (again): the name-leaf boost, and ── scoring ──
    zero = Q(0, 1)
    scores: List[Any] = []
    for index, frame in enumerate(frames):
        total = zero
        for token, token_idf in idf.items():
            weight = tf[token][index]
            if weight == 0:
                continue
            leaf_hits = _count(frame.leaf, token)
            if leaf_hits:
                weight += (_LEAF_BOOST - 1) * leaf_hits
            total = total + token_idf * weight
        scores.append(total)

    # ── E: rank. top_k_by_score takes the exact Q scores directly. ──
    ranked = top_k_by_score(scores, k=min(k, n_frames))

    records: List[Dict[str, Any]] = []
    for index in ranked:
        if scores[index] == zero:
            continue  # a non-match; never pad the answer
        frame = frames[index]
        records.append({
            "kind": frame.kind,
            "name": frame.name,
            "score": scores[index],
            "why": _why(frame, idf),
            "reach": frame.reach,
        })
    return SearchResult(records, witness)


#: Characters of matched context carried in ``why``. Wide enough to hold a
#: full import line (``from srmech.math.q import Q``) or a prose pointer with
#: its file:line (``QMat.rank`` (``qmat.py:447``)) — the two shapes measured
#: to carry the answer for the needs that arrive as pointers rather than as
#: their own registry row.
_WHY_CONTEXT = 120


def _why(frame: _Frame, idf: Dict[bytes, Any]) -> str:
    """Name the field that contributed most of this row's score, WITH the
    matched excerpt.

    THE LABEL ALONE IS NOT ENOUGH, and this is the ADR-0012 point rather than
    a nicety. The standard for this surface is AUTONOMOUS COMPOSITION — the
    answer has to be actionable without a second call. ``why="example.worked"``
    names the field and still forces the caller to go read it, which is
    exactly the second call the standard forbids.

    It matters most for the two needs whose answer is not their own registry
    row but a POINTER inside a neighbour's prose:

    * the exact-rational type — the caller's wrong guess is a MODULE PATH
      (``srmech.math.rational.Q`` for ``srmech.math.q.Q``), and the excerpt
      ships the literal ``from srmech.math.q import Q`` that corrects it;
    * matrix rank — no registered op NAME contains ``rank`` (it is a carrier
      method), but ``dense_solve``'s explanation names ``QMat.rank`` with its
      file and line, and the excerpt carries that through.

    A bare label loses both. Computed only for the k winners, never for the
    whole corpus — attribution is the expensive half.
    """
    best_label = ""
    best_raw = b""
    best = None
    for label, raw in frame.fields:
        subtotal = None
        for token, token_idf in idf.items():
            hits = _count(raw, token)
            if not hits:
                continue
            term = token_idf * hits
            subtotal = term if subtotal is None else subtotal + term
        if subtotal is None:
            continue
        if best is None or subtotal > best:
            best = subtotal
            best_label = label
            best_raw = raw
    if not best_label:
        return ""
    excerpt = _excerpt(best_raw, tuple(idf))
    return f"{best_label}: {excerpt}" if excerpt else best_label


def _token_positions(raw: bytes, token: bytes) -> Tuple[int, ...]:
    """Every offset of ``token`` in ``raw``, saturating at :data:`_TF_CAP`.

    Class G. Same registered byte scan as :func:`_count`, retaining the
    offsets instead of discarding them.
    """
    from ..math.search import byte_search

    out: List[int] = []
    start = 0
    limit = len(raw)
    while start < limit and len(out) < _TF_CAP:
        hit = byte_search(raw[start:], token)
        if hit is None:
            break
        out.append(start + hit)
        start += hit + len(token)
    return tuple(out)


def _excerpt(raw: bytes, tokens: Tuple[bytes, ...]) -> str:
    """The ``_WHY_CONTEXT``-wide window of ``raw`` covering the MOST distinct
    query tokens.

    Not the first hit of the strongest token — the densest passage. The
    difference is not cosmetic. These explanations run to a couple of thousand
    characters, so a window pinned to the first occurrence of one token lands
    wherever that token happens to appear first, which is usually a passing
    mention rather than the sentence the caller needs. Selecting for
    query-token COVERAGE puts the window where the query is actually being
    answered.

    Note what this optimises and what it deliberately does not: coverage of
    the QUERY, never proximity to an expected ANSWER. Selecting on the answer
    would tune the excerpt to whatever corpus it was measured against and
    would make the acceptance gate score its own tuning.

    Ties go to the earliest offset, so the excerpt for a given (field, query)
    pair is deterministic.
    """
    marks: List[Tuple[int, bytes]] = []
    for token in tokens:
        for pos in _token_positions(raw, token):
            marks.append((pos, token))
    if not marks:
        return ""
    marks.sort()

    best_start = marks[0][0]
    best_cover = -1
    for anchor, _tok in marks:
        window_end = anchor + _WHY_CONTEXT
        covered = {t for p, t in marks if anchor <= p < window_end}
        if len(covered) > best_cover:
            best_cover = len(covered)
            best_start = anchor

    # Centre the window on the densest run rather than starting at it, so the
    # matched text keeps its left-hand context.
    start = best_start - (_WHY_CONTEXT // 4)
    if start < 0:
        start = 0
    window = raw[start:start + _WHY_CONTEXT]
    text = " ".join(window.decode("utf-8", "replace").split())
    lead = "…" if start > 0 else ""
    tail = "…" if start + _WHY_CONTEXT < len(raw) else ""
    return f"{lead}{text}{tail}"
