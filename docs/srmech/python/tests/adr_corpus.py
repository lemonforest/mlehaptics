"""THE shared ADR-corpus parser — one definition, every ADR gate.

v0.9.0rc415 (`#T1098`), the first slice of the ADR-integrity arc.

WHY THIS FILE EXISTS, AND WHY IT EXISTS *FIRST*
===============================================
Four gates were designed against the ``adr/`` corpus in the same research
pass (status coherence, citation integrity, clause instruments, measured
numbers). Each one needs the same five primitives: find the ADR files, split
a status line into its ``(glyph, word)`` pair, find the markdown tables, find
the ``file:line`` citations, and resolve a cited path to something on disk.

Four gates each carrying its own copy of those five is **ADR-0010 Amendment
A.4's own defect** — the amendment that indicts a 12-entry tuple hardcoded in
four places, each copy carrying a hand-written comment asking the next
author to keep it in sync. A convention that four sites agree by is a
convention that eventually stops holding.

The precedent is ``tests/rosetta_roots.py``, which exists for exactly this
reason and which ``tests/conftest.py``,
``tests/test_rosetta_transitive_standalone.py`` and
``notes/_rosetta_inventory.py`` all import rather than re-copy. This module
is that pattern applied to ``adr/``.

⚠️ THIS IS A HELPER MODULE, NOT A TEST MODULE. It is named ``adr_corpus.py``
rather than ``test_adr_corpus.py`` so pytest does not collect it. Its own
correctness is proved by the non-vacuity guards in the gates that import it —
each one asserts a minimum population before it renders any verdict, so a
parser that silently stops observing crashes rather than greens.

WHY THE PARSE IS CLASS-G AND NOT ``re``
=======================================
Everything below is a byte-level scan built from
``srmech.math.search.byte_search`` (Class G) and ``srmech.math.text``
(UAX #29 glyph segmentation), not from ``re``. That is a deliberate test of
the framework's own position: srmech ships no regex surface, and the honest
question is whether the shipped Class-G surface is *sufficient* for the parse
shapes this corpus needs. For markdown tables, status pairs and ``file:line``
citations the answer measured out as **yes**.

It is not free, and the cost is recorded rather than hidden — see
``CAPABILITY GAPS`` at the bottom of this docstring. The rc409 ADR gate this
module replaces the parser of paid stdlib ``re``, as does
``test_selfhosting_import_ban.py``; this module does not, and the
:func:`line_index` / :func:`find_all` helpers below are what that cost bought.

⚠️ **NOTHING IS EXPORTED HERE THAT NO SHIPPED GATE EXERCISES.** The research
pass designed four gates and it is tempting to land all four gates' helpers
at once. Three were written and deleted before commit (a bold-span scanner, an
anchored-prefix test, a line-span reader) because rc415 ships two gates and an
untested helper is a surface claiming coverage it has not got — which is the
defect class this whole arc exists to close. rc416's clause-instrument gate
adds what it needs **and the test that exercises it**, in the same commit.

CAPABILITY GAPS SURFACED BY WRITING THIS (recorded, not worked around)
======================================================================
1. **No ``byte_search_all`` / count / offsets form.** ``srmech.math.search``
   exports exactly ``byte_search`` and ``byte_search_backward``, both
   first/last-hit-only. :func:`find_all` below is the composed loop; every
   gate that needs "every occurrence" would otherwise re-derive it.
2. **No ``start=`` offset on ``byte_search``.** The naive composition
   ``byte_search(hay[base:], needle)`` copies the remaining tail on every
   iteration, which is quadratic. Measured during the research: building a
   newline table for a 1 MB source file that way **did not finish in 120 s**.
   :func:`find_all` therefore slices forward but callers must not use it on
   megabyte inputs; :func:`line_index` is a deliberate ONE-PASS table instead.
3. **No byte-offset → line-number op.** ``line_index`` + ``line_of`` below
   are that primitive, hand-built. It is *the* primitive a citation gate is
   made of.
4. **``byte_search`` returns ``None`` on a miss, not ``-1``**, and the
   contract is undocumented at the call site. Two independent agents
   discovered it by crashing with ``TypeError: '<' not supported between
   instances of 'NoneType' and 'int'``. Every ``byte_search`` call below
   checks ``is None`` explicitly.
5. **No anchored (prefix) mode on Class-D ``match``.** ``match`` is
   contains-anywhere, which is the wrong semantics for a status classifier
   and is a measured false-positive source — ``match(b'a bound that failed
   open', [(b'open', 2)])`` returns ``(True, 2)``, and applied to a whole
   ADR status line it is 100% FP (ADR-0001's header legitimately ends
   *"…gates promotion to ✅ Accepted"*). Every classifier in these gates
   wants the PREFIX, so :func:`status_pair` reads position-first rather than
   asking ``match`` a question it cannot answer.
6. **No regex / pattern capture anywhere in srmech.** Class D ``match`` is a
   first-hit fixed-needle dispatcher and Class G returns one offset; neither
   captures a group. This is the largest gap the arc hit, and the positive
   result is that it was not needed: the Class-G surface parses markdown
   tables, status pairs and ``file:line`` citations without it.
"""

from __future__ import annotations

import bisect
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from srmech.math.search import byte_search
from srmech.math.text import glyph_stream

# ── locations ─────────────────────────────────────────────────────────

#: ``docs/srmech`` — this file lives at ``docs/srmech/python/tests/``.
SR_ROOT = Path(__file__).resolve().parents[2]

#: The ADR directory. Everything in this module is scoped to it.
ADR_DIR = SR_ROOT / "adr"

#: The ADR index / legend / lifecycle front door.
ADR_README = ADR_DIR / "README.md"

#: The repository root, for resolving cited source paths.
REPO_ROOT = SR_ROOT.parents[1]

#: Directory names a cited path must never resolve THROUGH.
#:
#: ⚠️ ``.claude`` / ``worktrees`` are the load-bearing two and they are not
#: hypothetical: a stale session worktree under ``docs/srmech/.claude/
#: worktrees/`` shadows ``tool_schema.py`` and ``srmech.h``, and the first
#: prototype of the citation gate resolved every citation against that DEAD
#: tree — reporting a clean corpus while reading a snapshot months old. A
#: resolver that can silently answer from a stale copy is the "artifact under
#: test was not the artifact under change" defect wearing a different hat.
EXCLUDED_DIR_NAMES = frozenset({
    "__pycache__", ".claude", "worktrees", "build", "_skbuild",
    "site-packages", "node_modules", ".git", "dist", ".venv",
})


# ── Class-G composition helpers (see CAPABILITY GAPS 1-4) ─────────────


def find_all(haystack: bytes, needle: bytes) -> List[int]:
    """Every offset of ``needle`` in ``haystack``, ascending. Class G.

    The composed form of the ``byte_search_all`` srmech does not ship. Slices
    forward each iteration, so it is O(len(haystack) x hits) — fine for the
    ~100 KB ADR files, NOT fine for a megabyte source file. Use
    :func:`line_index` when what you want is a newline table.
    """
    out: List[int] = []
    base = 0
    while base <= len(haystack):
        hit = byte_search(haystack[base:], needle)
        if hit is None:                      # gap 4: None, not -1
            break
        out.append(base + hit)
        base += hit + 1
    return out


def line_index(blob: bytes) -> List[int]:
    """A one-pass table of newline offsets — the O(n) peer of ``find_all``.

    Deliberately NOT ``find_all(blob, b"\\n")``: gap 2 makes that quadratic,
    and it is the difference between ~5 s and not-finishing-in-120 s on a
    1 MB file. This is a hand-built primitive because srmech ships no
    offset -> line op (gap 3).
    """
    return [i for i, byte in enumerate(blob) if byte == 0x0A]


def line_of(index: Sequence[int], offset: int) -> int:
    """The 1-based line number holding byte ``offset``. Gap 3, composed."""
    return bisect.bisect_left(index, offset) + 1



# ── the corpus ────────────────────────────────────────────────────────


def adr_files() -> List[Path]:
    """The ADR markdown files, README excluded, in numeric order.

    The ``[0-9]*.md`` glob is what keeps ``0001-profile-pattern.schema.json``
    (a COMPANION ARTIFACT sharing ADR-0001's number, per the README
    "Conventions" section) out of the population regardless of how many ADRs
    exist — and what keeps ``README.md`` out of the *ADR* population while
    leaving it available to :func:`all_markdown` for citation scanning.
    """
    return sorted(p for p in ADR_DIR.glob("[0-9]*.md"))


def all_markdown() -> List[Path]:
    """Every markdown file under ``adr/``, README INCLUDED.

    The citation gate scans this wider set: ``README.md`` is hand-written
    prose in the same directory and can carry a dead pointer exactly like an
    ADR can. The status gate uses :func:`adr_files` instead, because README
    is the INDEX of that population, not a member of it.
    """
    return adr_files() + [ADR_README]


def adr_number(path: Path) -> str:
    """``"0001"`` from ``0001-profile-pattern.md``."""
    return path.name[:4]


@lru_cache(maxsize=64)
def read_adr(path: Path) -> bytes:
    """The raw bytes of an ADR.

    BYTES, not ``str``, and explicitly so: citation offsets, table scans and
    glyph segmentation all want a stable byte axis, and a ``str`` read on
    Windows under the default ``cp1252`` raises ``UnicodeDecodeError`` on the
    status glyphs before any gate gets to run.
    """
    return path.read_bytes()



@lru_cache(maxsize=64)
def text_lines(blob: bytes) -> List[str]:
    """The blob's lines as ``utf-8`` text. Explicit encoding, always.

    Cached on the BLOB, not the path, so the cache key is the content itself —
    a re-read of a changed file cannot serve a stale split.
    """
    return blob.decode("utf-8").split("\n")


@lru_cache(maxsize=4096)
def _status_pair_cached(text: str) -> Tuple[str, str]:
    """Memoised :func:`status_pair`. UAX #29 segmentation is the hot cost."""
    return _status_pair_uncached(text)


# ── status pairs (CM-7's root fix) ────────────────────────────────────


def status_pair(text: str) -> Tuple[str, str]:
    """Split a status line into its ``(glyph, word)`` PAIR. Memoised.

    See :func:`_status_pair_uncached` for the contract; this is the cached
    front door, because the callers scan every line of a 1,700-line ADR and
    UAX #29 segmentation is the hot cost in the whole gate.
    """
    return _status_pair_cached(text)


def _status_pair_uncached(text: str) -> Tuple[str, str]:
    """Split a status line into its ``(glyph, word)`` PAIR.

    THE ROOT FIX. The shipped rc409 gate's ``_leading_glyph`` returned the
    leading non-ASCII run and **discarded the remainder**, at all three of its
    parse sites. The README legend is literally a glyph->word *mapping*, and
    reducing it to a *set of glyphs* is what let ``(🟢, ACCEPTED)`` —
    a pair the legend does not define — sit live on two surfaces at once with
    the gate green: both surfaces carried the SAME illegal pair, so a
    glyph-only comparison found them in perfect agreement.

    The glyph is the leading extended grapheme cluster per **UAX #29**, taken
    from ``srmech.math.text.glyph_stream`` — the shipped op, against the
    vendored UCD 16.0.0 break table. That retires the rc409 gate's
    hand-reasoning about variation selectors: it matched a *run* of non-ASCII
    specifically because several of these emoji carry U+FE0F as a second
    codepoint and slicing ``[0]`` would compare half a glyph. A grapheme
    cluster is the unit that reasoning was reaching for.

    The word is the first run of ASCII-letter clusters after the glyph.
    Returns ``("", "")`` / ``(glyph, "")`` rather than raising — the callers'
    non-vacuity guards decide whether an empty half is fatal, because "this
    line has no pair" and "this corpus has no pairs" are different failures.
    """
    stripped = text.strip()
    if not stripped:
        return ("", "")

    clusters = glyph_stream(stripped)

    # Skip leading ASCII punctuation / emphasis. The lifecycle line spells its
    # first stage as ``**Status lifecycle:** ⏳ Draft``, so the markdown marker
    # sits BEFORE the glyph on exactly one of the three surfaces this parses.
    # Without this skip that surface silently yields ``("", "Draft")`` and the
    # rank table loses a state -- a legend/lifecycle disagreement invented by
    # the parser rather than present in the corpus.
    idx = 0
    while idx < len(clusters) and _is_ascii(clusters[idx]) \
            and not clusters[idx].isalnum():
        idx += 1

    # The leading run of non-ASCII clusters is the glyph. A RUN, not one
    # cluster: '🗑' followed by a variation selector already segments as one
    # cluster, but a legend item may legitimately pair two symbols.
    glyph_parts: List[str] = []
    while idx < len(clusters) and not _is_ascii(clusters[idx]):
        glyph_parts.append(clusters[idx])
        idx += 1
    glyph = "".join(glyph_parts)

    # Skip separators, then take the first run of ASCII letters.
    while idx < len(clusters) and not clusters[idx].isalpha():
        idx += 1
    word_parts: List[str] = []
    while idx < len(clusters) and clusters[idx].isalpha() and _is_ascii(clusters[idx]):
        word_parts.append(clusters[idx])
        idx += 1

    return (glyph, "".join(word_parts))


def _is_ascii(cluster: str) -> bool:
    """True when every codepoint of the cluster is ASCII."""
    return all(ord(ch) < 0x80 for ch in cluster)


def legend() -> Dict[str, str]:
    """``{glyph: Word}`` — the pairs ``adr/README.md`` DEFINES.

    Split on the ``·`` separator FIRST, then take each item's pair. A naive
    scan over the whole line also harvests the separator itself (U+00B7 is
    non-ASCII), which would silently admit ``·`` as a legal status — a legend
    that accidentally defines its own punctuation.

    Raises rather than returning ``{}`` when the legend line is gone: an
    empty legend makes every legality check vacuous, so it must be loud.
    """
    for line in text_lines(read_adr(ADR_README)):
        if line.startswith("**Status legend:**"):
            body = line[len("**Status legend:**"):]
            out: Dict[str, str] = {}
            for item in body.split("·"):
                glyph, word = status_pair(item)
                if glyph and word:
                    out[glyph] = word
            return out
    raise AssertionError(
        "no '**Status legend:**' line in adr/README.md — the legend is the "
        "only definition of which (glyph, word) pairs are legal, so its "
        "absence makes every legality check vacuous rather than green.")


def lifecycle() -> Dict[str, int]:
    """``{glyph: rank}`` from the README's ``Status lifecycle:`` line.

    The lifecycle line orders the states (``⏳ Draft / 🔄 Proposed →
    🟢 Implementing → ✅ Accepted → 🗑 Superseded``). Rank is the position of
    the ``→``-separated STAGE, so ``⏳`` and ``🔄`` share rank 0 — they are
    alternatives at the same stage, not a sequence.
    """
    for line in text_lines(read_adr(ADR_README)):
        if "Status lifecycle:" not in line:
            continue
        body = line.split("Status lifecycle:", 1)[1]
        out: Dict[str, int] = {}
        for rank, stage in enumerate(body.split("→")):
            for item in stage.split("/"):
                glyph, word = status_pair(item)
                if glyph and word:
                    out.setdefault(glyph, rank)
        if out:
            return out
    raise AssertionError(
        "no 'Status lifecycle:' line in adr/README.md — without it the "
        "ordering of the states is undefined and no rank comparison means "
        "anything.")


# ── markdown structure ────────────────────────────────────────────────


def _is_delimiter_row(cells: List[str]) -> bool:
    """``|---|:--|--:|`` — every cell is dashes with optional colons."""
    if not cells:
        return False
    for cell in cells:
        body = cell.strip()
        if body.startswith(":"):
            body = body[1:]
        if body.endswith(":"):
            body = body[:-1]
        if len(body) < 3 or set(body) != {"-"}:
            return False
    return True


def split_cells(line: str) -> List[str]:
    """Split a markdown table row into cells, honouring backtick code spans.

    A ``|`` inside a code span is DATA, not a delimiter — the ADRs quote
    markdown and shell pipelines at each other constantly. Splitting naively
    silently shifts every downstream cell index by one on those rows.
    """
    cells: List[str] = []
    buf: List[str] = []
    in_code = False
    for ch in line:
        if ch == "`":
            in_code = not in_code
            buf.append(ch)
        elif ch == "|" and not in_code:
            cells.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    cells.append("".join(buf))
    # A markdown row is fenced by leading/trailing pipes; drop the empties.
    if cells and not cells[0].strip():
        cells = cells[1:]
    if cells and not cells[-1].strip():
        cells = cells[:-1]
    return [c.strip() for c in cells]


def tables(blob: bytes) -> List[List[Tuple[int, List[str]]]]:
    """Every markdown table, as a list of ``(line_number, cells)`` rows.

    A TABLE is a maximal run of consecutive ``|``-leading lines containing at
    least one delimiter row. **A lone ``|`` line is prose**, not a table, and
    that distinction is what keeps the row population honest: a naive
    ``^\\|`` scan over this corpus counts materially more lines than there
    are table rows, and the difference is header rows plus pipe-lines that
    sit outside any table.

    Fenced ``` blocks are skipped — the ADRs quote markdown at each other,
    and a quoted table is an EXAMPLE, not a claim this corpus makes.

    Delimiter rows and the header row above them are dropped; what comes back
    is DATA rows only.
    """
    out: List[List[Tuple[int, List[str]]]] = []
    run: List[Tuple[int, List[str]]] = []
    run_has_delim = False
    in_fence = False

    def flush() -> None:
        nonlocal run, run_has_delim
        if run and run_has_delim:
            body = [(n, c) for n, c in run if not _is_delimiter_row(c)]
            # The header is the row immediately above the delimiter; the
            # delimiter's index in the ORIGINAL run tells us how many rows
            # preceded it.
            delim_at = next(i for i, (_, c) in enumerate(run)
                            if _is_delimiter_row(c))
            header_lines = {n for n, _ in run[:delim_at]}
            out.append([(n, c) for n, c in body if n not in header_lines])
        run = []
        run_has_delim = False

    for n, line in enumerate(text_lines(blob), start=1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            flush()
            continue
        if in_fence:
            continue
        if stripped.startswith("|"):
            cells = split_cells(stripped)
            run.append((n, cells))
            if _is_delimiter_row(cells):
                run_has_delim = True
        else:
            flush()
    flush()
    return out



# ── citations ─────────────────────────────────────────────────────────

#: The file-extension tokens a ``path:line`` citation can end its path with.
#: Class-G scans for each; a citation is a hit whose next byte is ``:``.
CITATION_SUFFIXES: Tuple[bytes, ...] = (
    b".py:", b".c:", b".h:", b".toml:", b".md:", b".json:",
    b".yml:", b".yaml:", b".txt:", b".ndjson:", b".cfg:", b".sh:",
)

_PATH_CHARS = frozenset(
    b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    b"_-./"
)


class Citation:
    """One ``path:line`` or ``path:A-B`` pointer found in an ADR."""

    __slots__ = ("adr", "line_no", "path", "start_line", "end_line",
                 "raw", "column")

    def __init__(self, adr: str, line_no: int, path: str,
                 start_line: int, end_line: int, raw: str, column: int):
        self.adr = adr
        self.line_no = line_no          # line WITHIN the ADR
        self.path = path                # the cited path, as written
        self.start_line = start_line    # first cited line in the target
        self.end_line = end_line        # last cited line in the target
        self.raw = raw
        self.column = column            # column WITHIN the ADR line

    def __repr__(self) -> str:          # pragma: no cover - diagnostics
        return (f"<Citation {self.adr}:{self.line_no} -> {self.path}:"
                f"{self.start_line}-{self.end_line}>")


def _read_int(buf: bytes, at: int) -> Tuple[Optional[int], int]:
    """Read a run of digits starting at ``at``; return ``(value, next)``."""
    end = at
    while end < len(buf) and 0x30 <= buf[end] <= 0x39:
        end += 1
    if end == at:
        return (None, at)
    return (int(buf[at:end]), end)


def citations(blob: bytes, adr: str = "") -> List[Citation]:
    """Every ``path:line`` / ``path:A-B`` citation in an ADR. Class G, no regex.

    Two passes:

    1. **Full citations.** For each suffix token in :data:`CITATION_SUFFIXES`,
       every occurrence; walk LEFT over path characters to find the start of
       the path, then read the line number (and an optional ``-B`` range) to
       its right.
    2. **Bare follow-ons.** A ``:NNN`` with no path, attributed to the nearest
       PRECEDING full citation **on the same markdown line**. That form is
       idiomatic in this corpus (*"``foo.py:390-393``; ``resolve_all`` at
       ``:474-485``"*), and a parser that drops it silently under-counts the
       population it is supposed to be checking.

    Attribution is scoped to one markdown line on purpose: a ``:NNN`` in a
    later paragraph belongs to whatever that paragraph is about, and guessing
    across a paragraph break is how a gate invents a citation nobody wrote.
    """
    out: List[Citation] = []
    index = line_index(blob)

    # Pass 1 — full citations.
    for suffix in CITATION_SUFFIXES:
        for hit in find_all(blob, suffix):
            colon = hit + len(suffix) - 1        # offset of the ':'
            start = hit
            while start > 0 and blob[start - 1] in _PATH_CHARS:
                start -= 1
            path = blob[start:colon].decode("utf-8", "replace")
            if not path or path.startswith("."):
                continue
            first, after = _read_int(blob, colon + 1)
            if first is None:
                continue
            last = first
            if after < len(blob) and blob[after:after + 1] == b"-":
                second, after2 = _read_int(blob, after + 1)
                if second is not None and second >= first:
                    last, after = second, after2
            line_no = line_of(index, start)
            bol = index[line_no - 2] + 1 if line_no >= 2 else 0
            out.append(Citation(
                adr, line_no, path, first, last,
                blob[start:after].decode("utf-8", "replace"), start - bol))

    out.sort(key=lambda c: (c.line_no, c.column))

    # Pass 2 — bare ``:NNN`` follow-ons on the same markdown line.
    by_line: Dict[int, List[Citation]] = {}
    for cit in out:
        by_line.setdefault(cit.line_no, []).append(cit)

    extra: List[Citation] = []
    for line_no, sibs in by_line.items():
        bol = index[line_no - 2] + 1 if line_no >= 2 else 0
        eol = index[line_no - 1] if line_no - 1 < len(index) else len(blob)
        raw = blob[bol:eol]
        taken = {(c.column, c.column + len(c.raw)) for c in sibs}
        for at in find_all(raw, b"`:"):
            col = at + 1
            if any(lo <= col < hi for lo, hi in taken):
                continue
            first, after = _read_int(raw, col + 1)
            if first is None:
                continue
            last = first
            if after < len(raw) and raw[after:after + 1] == b"-":
                second, after2 = _read_int(raw, after + 1)
                if second is not None and second >= first:
                    last, after = second, after2
            prior = [c for c in sibs if c.column < col]
            if not prior:
                continue
            owner = prior[-1]
            extra.append(Citation(
                adr, line_no, owner.path, first, last,
                raw[col:after].decode("utf-8", "replace"), col))

    out.extend(extra)
    out.sort(key=lambda c: (c.line_no, c.column))
    return out


def all_citations() -> List[Citation]:
    """Every citation across every markdown file in ``adr/``."""
    out: List[Citation] = []
    for path in all_markdown():
        name = path.name[:4] if path.name != "README.md" else "READ"
        out.extend(citations(read_adr(path), name))
    return out


# ── path resolution ───────────────────────────────────────────────────

#: Roots a bare cited path is tried against, in order. First hit wins.
_SEARCH_ROOTS: Tuple[Path, ...] = (
    SR_ROOT / "python",     # `srmech/...`, `tests/...`, `tools/...`
    SR_ROOT,                # `c/include/...`, `adr/...`, `notes/...`
    REPO_ROOT,              # `docs/srmech/...`
    ADR_DIR,                # a sibling ADR by bare filename
)


def _is_excluded(root: Path, cited: str) -> bool:
    """True when the CITED path descends through an excluded directory.

    ⚠️ Scoped to the cited part, never to the absolute path. The check used to
    test every component of ``root / cited`` and that was wrong in a way this
    repository reproduces on itself: a session worktree lives at
    ``<repo>/.claude/worktrees/<id>/``, so ``root`` ITSELF contains both
    ``.claude`` and ``worktrees`` and every single resolution was refused.
    The gate went red on all 13 index links with the message "resolves to no
    file", which is a false report of a corpus defect — the exact class this
    arc exists to close, produced by the guard written to prevent it.

    What must be refused is a *cited path that reaches into* a stale tree, not
    a repository that happens to be checked out inside one.
    """
    return any(part in EXCLUDED_DIR_NAMES for part in Path(cited).parts)


#: Directories walked to build the suffix index. Bounded on purpose — an
#: unbounded walk of the monorepo would resolve a cited srmech path against a
#: same-named file in a sister subtree.
_INDEXED_TREES: Tuple[Path, ...] = (
    SR_ROOT / "python" / "srmech",
    SR_ROOT / "python" / "tests",
    SR_ROOT / "python" / "tools",
    SR_ROOT / "c",
    SR_ROOT / "adr",
    SR_ROOT / "notes",
)


@lru_cache(maxsize=1)
def _suffix_index() -> Dict[str, Tuple[Path, ...]]:
    """``{path_suffix: (files,)}`` for every ``/``-aligned suffix of every file.

    The corpus does not spell citations as full repo paths. It writes
    ``introspect/tool_schema.py:645`` and ``tool_schema.py:498`` and
    ``srmech.h:5429`` — shortened to whatever is unambiguous to a human
    reader. A resolver that only joins against roots reports **27 of 78**
    citations as dead files when in fact none of those 27 is a dead file, and
    a gate whose V1 arm is 100% false positive is worse than no gate: it
    trains its reader to ignore the arm that matters.
    """
    index: Dict[str, List[Path]] = {}
    for tree in _INDEXED_TREES:
        if not tree.is_dir():
            continue
        for path in tree.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(SR_ROOT)
            if any(part in EXCLUDED_DIR_NAMES for part in rel.parts):
                continue
            parts = rel.parts
            for start in range(len(parts)):
                index.setdefault("/".join(parts[start:]), []).append(path)
    return {k: tuple(v) for k, v in index.items()}


def resolve_candidates(cited: str) -> Tuple[Path, ...]:
    """Every file a cited path could name. Empty = genuinely dead.

    Two stages, exact before fuzzy: a direct join against :data:`_SEARCH_ROOTS`
    wins outright, and only a citation that resolves nowhere exactly falls
    through to the ``/``-aligned suffix index. More than one candidate is
    AMBIGUOUS, which the citation gate reports as its own class rather than
    silently picking the first — picking one is how a gate reads the wrong
    file and reports a clean corpus.
    """
    if not cited or cited.startswith("/"):
        return ()
    if _is_excluded(_SEARCH_ROOTS[0], cited):
        return ()
    for root in _SEARCH_ROOTS:
        candidate = root / cited
        if candidate.is_file():
            return (candidate,)
    return _suffix_index().get(cited.lstrip("./"), ())


def resolve_path(cited: str) -> Optional[Path]:
    """The single file a cited path names, or ``None`` when 0 or >1 match."""
    hits = resolve_candidates(cited)
    return hits[0] if len(hits) == 1 else None


def file_line_count(path: Path) -> int:
    """Number of lines in ``path`` — the EOF bound a citation must respect.

    A file whose last line has no trailing newline still has that line, so
    the count is ``newlines + 1`` unless the file ends ON a newline.
    """
    blob = path.read_bytes()
    if not blob:
        return 0
    n = len(line_index(blob))
    return n if blob.endswith(b"\n") else n + 1



__all__ = [
    "ADR_DIR", "ADR_README", "SR_ROOT", "REPO_ROOT", "EXCLUDED_DIR_NAMES",
    "CITATION_SUFFIXES", "Citation",
    "adr_files", "all_markdown", "adr_number", "read_adr", "text_lines",
    "find_all", "line_index", "line_of", "status_pair", "legend",
    "lifecycle", "tables", "split_cells", "citations", "all_citations",
    "resolve_path", "resolve_candidates", "file_line_count",
]
