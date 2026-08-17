"""srmech.biology.plasmid — F1252 / §102: the TWO-STAGE genome encode.

**STAGE 1 (EXTRACT, rc278)** — :func:`plasmid_extract` / :func:`section_counts`: the
plasmid-native sectional graph-L store. **STAGE 2 (ORGANIZE, rc279)** —
:func:`conserved_core` / :func:`genome_integrate_plasmids` / :func:`add_plasmid`:
CONSERVE (derive ``k`` from the section-count distribution) -> PROMOTE (mint the
induced core subgraph) -> MERGE (fold the retained plasmids in). Stage 2 NEVER calls
``recursive_cut`` and never re-extracts, which is what removes the monolithic
from-scratch partition from the encode path. Stage 2's own honest-scope note (the
conservation-vs-participation convergence is PENDING validation on the real corpus)
sits above the stage-2 section below.

The first half of the two-stage genome encode (design:
``docs/srmech/notes/f1252_two_stage_encode_design.md``). Each ingest DOCUMENT
becomes ONE Tier-1 **plasmid chromosome** — its LOCAL window co-occurrence graph,
encoded to a §89/v6 KERNEL chromosome (Klein-4 leaves, a ``0x6B`` kernel telomere,
**no** centromere) and APPENDED (§v12 O(1) HEAD-only) to a single ``sections/``
genome directory. This RETIRES the loose monolithic
``simplewiki_directed_sparse_kernel.json`` at the graph-L layer: instead of
dumping one 916 MB JSON re-extracted every re-encode, adding a document appends
ONE bounded plasmid section + bumps its head
(:mod:`[[feedback_persist_genome_native_not_loose_json]]` one layer up).

**GLOBAL node-ids (the conservation precondition).** A document's co-occurrence is
inherently LOCAL (a window inside ONE document — the whole graph is complete +
self-contained at extract time, no other document needed; D1). Its edges use LOCAL
node indices ``[0, m)``, but the section's ``node_ids`` label table maps each local
index to a GLOBAL vocab id (via an append-only global ``vocab``) — so a word shared
across sections carries the SAME id. :func:`section_counts` reads that GLOBAL table
back per section; the integer ``section_count[node]`` (how many distinct sections a
node appears in) is what stage-2 (rc279) reads for the conservation ≥ k promotion.
The counts are SSoT-derivable from the sections themselves (their node_ids) — the
genome-native persistence (the sections ARE the store), re-derived on read like the
``.fai`` manifest, never a loose sidecar.

**C-native, genome-must-exist-in-C.** The heavy per-section compute
(``graph_kernel_encode`` → the §89 KERNEL-region build → ``genome_append``) is ONE
bare-C orchestrator ``srmech_genome_plasmid_extract``; the co-occurrence peer
(``srmech_text_cooccurrence_topk`` / ``_extract``) is the other standalone stage-1 C
peer a host composes upstream. So ``cooccurrence_topk`` → ``plasmid_extract`` is the
whole stage-1 stack in C, zero Python. This Python surface DISPATCHES the whole
section to that peer when ``HAS_NATIVE``; the pure body (``_graph_kernel_encode`` +
``genome_append_kernel``) is the complete numpy-free alternative + BYTE-PARITY
oracle. Append-only / streaming: add a doc → append one plasmid section + bump the
count, never re-extract. §101: the progress tick fires between whole SECTIONS
(``phase=EXTRACTING``), so a cancel truncates at a valid chromosome boundary — a
partial section is never left. All arithmetic integer/exact (Class-N); no ``abs()``;
no numpy/math/fractions.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

from .. import _native
from . import genome as _genome
# Bare imports of the composed genome ledger ops (so the rosetta reachability walk
# SEES that the plasmid surface reaches C-backed peers — a `_genome.op()` module-
# attribute call is opaque to the walker; a bare-name reference resolves).
from .genome import genome_census, genome_window, kernel_unpack
from ..math.text import cooccurrence_topk

__all__ = ["plasmid_extract", "section_counts", "conserved_core",
           "genome_integrate_plasmids", "add_plasmid", "SectionCountsCancelled"]

#: The label of the shared VOCAB chromosome (the karyotype index) — a KERNEL
#: chromosome in the SAME store carrying the global word -> id table so a reader
#: re-anchors the sections' GLOBAL node_ids. Distinct from the ``sec*`` sections.
VOCAB_LABEL = "__vocab__"

_PHASE_EXTRACTING = _native.SRMECH_PHASE_EXTRACTING
_PHASE_INTEGRATING = _native.SRMECH_PHASE_INTEGRATING
_PHASE_MINTING = _native.SRMECH_PHASE_MINTING
_PROGRESS_STRUCT_SIZE = _native.PROGRESS_STRUCT_SIZE
_STATUS_OK = "ok"
_STATUS_CANCELLED = "cancelled"


def _coupling_block_bytes(coupling) -> bytes:
    """The ``leaf_dim`` raw bytes of the coupling invariant ``coupling`` — the exact
    bytes ``genome_append`` couples each turn through (the C peer's ``coupling``)."""
    return bytes(_genome._leaf_blocks([coupling])[0])


def _bytes_to_klein4(blob: bytes) -> List[int]:
    """UTF-8 ``blob`` -> a flat Klein-4 symbol list (each byte -> 4 sectors, high
    lanes first) — the genome-native (uniformly-Klein-4) vocab-blob encoding."""
    syms: List[int] = []
    for b in blob:
        syms.append((b >> 6) & 3)
        syms.append((b >> 4) & 3)
        syms.append((b >> 2) & 3)
        syms.append(b & 3)
    return syms


def _klein4_to_bytes(syms: Sequence[int]) -> bytes:
    """Inverse of :func:`_bytes_to_klein4` — 4 Klein-4 symbols -> 1 byte (the exact
    ``kernel_unpack``-trimmed stream, so no padding tail)."""
    out = bytearray()
    for i in range(0, len(syms) - 3, 4):
        out.append(((int(syms[i]) & 3) << 6) | ((int(syms[i + 1]) & 3) << 4)
                   | ((int(syms[i + 2]) & 3) << 2) | (int(syms[i + 3]) & 3))
    return bytes(out)


def _resolve_vocab(vocab):
    """A mutable GLOBAL vocab (append-only). ``vocab=None`` -> a fresh empty vocab;
    a list -> reuse it (streaming across calls). Returns ``(words, index)`` — the
    index -> token list + the token -> index dict."""
    words: List[str] = list(vocab) if vocab is not None else []
    index: Dict[str, int] = {w: i for i, w in enumerate(words)}
    return words, index


def _intern(words: List[str], index: Dict[str, int], tok: str) -> int:
    """Append-only intern of ``tok`` into the global vocab; returns its GLOBAL id."""
    g = index.get(tok)
    if g is None:
        g = len(words)
        index[tok] = g
        words.append(tok)
    return g


def _encode_section_syms(vocab_size, edges, weights, node_ids):
    """The section's flat Klein-4 symbol stream (the #1390 graph->kernel codec over
    the LOCAL co-occurrence graph; charges all 0 = undirected; the GLOBAL id table
    rides as ``node_ids``). Dispatches to the C codec, else the pure body."""
    charges = [0] * len(edges)                      # co-occurrence is undirected
    return _genome._graph_kernel_encode(
        vocab_size, [tuple(e) for e in edges], list(weights), charges,
        list(node_ids), [])


def _seed_first_section(store, label, vocab_size, edges, weights, node_ids,
                        coupling, attestation=None):
    """The FIRST section into a FRESH store: encode + ``genome_save`` (creates the
    dir + manifest). Same in the native + pure paths (the C append peer requires an
    existing store). Returns the manifest ``data`` dict."""
    syms = _encode_section_syms(vocab_size, edges, weights, node_ids)
    strand = _genome.kernel_pack(syms, leaf_dim=len(list(coupling)), label=label,
                                 coupling=coupling)
    # `#T1108`: provenance enters the two-stage pipeline exactly ONCE, here at the
    # SEED. Every later section append, the vocab refresh (remove + append) and the
    # stage-2 promotion are IN-PLACE on this same store, so they carry it forward
    # for free rather than each needing a parameter of their own.
    return _genome.genome_save(strand, store, coupling, attestation=attestation)


def _append_section(store, label, vocab_size, edges, weights, node_ids, coupling,
                    dim, data):
    """Append ONE plasmid section to the EXISTING store. Native: the whole
    ``graph_kernel_encode -> §89 region -> genome_append`` runs in the C
    orchestrator (O(1) HEAD read/write). Pure: ``_graph_kernel_encode`` +
    ``genome_append_kernel`` (byte-identical section). Returns the threaded catalog
    ``data`` (pure) or ``None`` (native — re-derived once at the end)."""
    n_syms = _native.genome_plasmid_extract_c(
        vocab_size, [tuple(e) for e in edges], list(weights), None,
        list(node_ids), [], str(store), label, dim,
        _coupling_block_bytes(coupling))
    if n_syms is not None:
        return None                                 # C appended; catalog derived later
    syms = _encode_section_syms(vocab_size, edges, weights, node_ids)
    # Thread the catalog dict for O(1) appends (``data`` is the genome_save/append
    # return in the pure path); ``None`` (e.g. a first pure append after a native
    # one) falls to a cold O(1)-head read.
    return _genome.genome_append_kernel(
        store, label, syms, coupling=coupling, catalog=data)


def _write_vocab_chromosome(store, words, coupling) -> None:
    """Write (or refresh) the shared VOCAB chromosome (the karyotype index) — the
    global word->id table as a genome-native KERNEL chromosome. Idempotent: an
    existing vocab chromosome is excised first, so a re-run over a grown vocab keeps
    ONE vocab chromosome. Skipped for an empty vocab."""
    if not words:
        return
    syms = _bytes_to_klein4("\n".join(words).encode("utf-8"))
    census = genome_census(store, coupling=coupling)
    labels = {c["label"] for c in census["chromosomes"]}
    if VOCAB_LABEL in labels:
        _genome.genome_remove(store, VOCAB_LABEL, coupling=coupling)
    _genome.genome_append_kernel(store, VOCAB_LABEL, syms, coupling=coupling,
                                 catalog=None)


def plasmid_extract(docs, section_store, coupling, *, vocab=None, window=2, k=20,
                    cap_slack=4, label_prefix="sec", progress=None,
                    attestation=None) -> dict:
    """STAGE 1 EXTRACT — stream ``docs`` into APPEND-ONLY plasmid sections.

    Each document (a token sequence) becomes ONE Tier-1 plasmid chromosome: its
    LOCAL window co-occurrence graph (:func:`srmech.math.text.cooccurrence_topk`,
    ``window`` / top-``k`` / ``cap_slack``), encoded to a §89 KERNEL chromosome with
    GLOBAL node-ids (via the append-only ``vocab``), APPENDED to ``section_store``
    (a genome directory) in O(1). The first document SEEDS the store
    (``genome_save``); the rest append. A shared VOCAB chromosome (the karyotype
    index) is written so a reader re-anchors the GLOBAL ids.

    ``coupling`` — the coupling invariant (its length is the store's ``leaf_dim``,
    which must be >= 52 so the §89 uniformly-Klein-4 kernel header fits one leaf).
    ``vocab`` — a mutable global word list (append-only; ``None`` starts fresh),
    RETURNED grown so a later call streams more documents onto the SAME id space.
    ``progress`` — a Python-only ``ev -> bool`` callback (NOT a wire param); it fires
    between whole SECTIONS with ``phase=EXTRACTING``, ``done=sections so far``,
    ``total=n docs`` — a truthy return CANCELS cleanly (the sections appended so far
    are complete chromosomes; ``status="cancelled"``, no partial section).

    Returns ``{"section_store", "vocab", "section_count", "n_sections", "sections",
    "status"}`` — ``section_count`` the ``{global_id: n_sections}`` integer
    accumulator stage-2 promotes on. No ``abs()``; the whole op is
    genome-native (no loose JSON). Byte-identical whether native or pure."""
    store = Path(section_store)
    dim = len(list(coupling))
    if dim < 52:
        raise ValueError(
            f"plasmid_extract: leaf_dim (len(coupling)) is {dim}; the §89 KERNEL "
            f"section header needs leaf_dim >= 52 (a plasmid section is a kernel "
            f"chromosome). Use a wider coupling.")
    doc_list = [list(d) for d in docs]              # a section per document (D1)
    n_docs = len(doc_list)
    words, index = _resolve_vocab(vocab)
    section_count: Dict[int, int] = {}
    labels: List[str] = []
    data = None
    status = _STATUS_OK
    store_exists = _genome._is_genome_dir(store)
    # continue the section numbering from the store's existing sections (streaming:
    # a later call onto the SAME store appends sec{N}, sec{N+1}, … — never collides).
    base_index = 0
    if store_exists:
        base_index = sum(1 for c in genome_census(
            store, coupling=coupling)["chromosomes"] if c["label"] != VOCAB_LABEL)
    for i, tokens in enumerate(doc_list):
        if progress is not None and progress({
                "struct_size": _PROGRESS_STRUCT_SIZE, "phase": _PHASE_EXTRACTING,
                "done": i, "total": n_docs}):
            status = _STATUS_CANCELLED
            break
        cooc = cooccurrence_topk([tokens], window=window, k=k, cap_slack=cap_slack)
        local_words = cooc["vocab"]
        global_ids = [_intern(words, index, w) for w in local_words]
        label = f"{label_prefix}{base_index + len(labels)}"
        if not store_exists:
            data = _seed_first_section(store, label, len(local_words),
                                       cooc["edges"], cooc["weights"], global_ids,
                                       coupling, attestation)
            store_exists = True
        else:
            data = _append_section(store, label, len(local_words), cooc["edges"],
                                   cooc["weights"], global_ids, coupling, dim, data)
        labels.append(label)
        for g in global_ids:                        # O(section) integer accumulator
            section_count[g] = section_count.get(g, 0) + 1
    _write_vocab_chromosome(store, words, coupling)
    return {"section_store": str(store), "vocab": words,
            "section_count": section_count, "n_sections": len(labels),
            "sections": labels, "status": status}


def _section_entries(store, coupling):
    """``(leaf_dim, coupling, entries)`` — the store's catalog derived **ONCE**, plus
    its PLASMID section entries in census order (the VOCAB karyotype chromosome
    excluded) (§102/rc280).

    Every per-section read below takes a pre-derived ``entry`` for the same reason
    :func:`section_counts` does: :func:`genome_window` / :func:`genome_census` each
    re-derive the whole catalog, which on a v12 head-only manifest re-reads and
    re-Merkle-folds the ENTIRE body. Doing that inside a P-section loop is O(P × body)
    — quadratic in corpus size — and it dominated the measured cost far more than any
    per-section decode did."""
    data = _genome._catalog_data(Path(store), coupling)
    leaf_dim = int(data["leaf_dim"])
    one = _genome._resolve_coupling(data, coupling)
    entries = [c for c in data["chromosomes"] if c["label"] != VOCAB_LABEL]
    return leaf_dim, one, entries


def _section_leaves(store, label, coupling, entry=None, leaf_dim=None, f=None):
    """One section's stored coupled DATA turns. With a pre-derived catalog ``entry``
    this pages the region directly (O(section)); without one it falls back to
    :func:`genome_window`, which re-derives the catalog (O(body)) — pass an entry
    whenever reading more than one section.

    ``f`` — an ALREADY-OPEN body handle (rc282); pass the loop's handle so a P-section
    read costs ONE open of ``turns.bin`` rather than P."""
    if entry is not None and leaf_dim is not None:
        return _genome._region_leaves(Path(store), entry, leaf_dim, f)
    return genome_window(store, label, coupling=coupling)


def _read_section_graph(store, label, coupling, entry=None, leaf_dim=None, f=None):
    """Decode ONE plasmid section back to its directed-graph dict (the LOCAL edges +
    the GLOBAL ``node_ids`` table). Pages the section's coupled leaves, rebuilds the
    KERNEL strand (prepending the section's kernel telomere so ``kernel_unpack``
    reads the §89 header), and decodes.

    This is the FULL decode — it is what :func:`_section_global_edges` needs (the
    edges ARE its payload). :func:`section_counts` deliberately does NOT come through
    here any more: it only ever wanted ``node_ids``, which the §89 payload places
    before the edges, so it uses the targeted prefix read instead."""
    leaves = _section_leaves(store, label, coupling, entry, leaf_dim, f)
    dim = len(list(coupling))
    strand = [_genome._kernel_telomere(label, dim=dim)] + list(leaves)
    syms = kernel_unpack(strand, coupling)
    return _genome._graph_kernel_decode(syms)


class SectionCountsCancelled(Exception):
    """A ``progress`` tick CANCELLED a :func:`section_counts` scan (§101 / rc280).

    **Why a raise and not a partial return.** When a cancelled ENCODE stops early, the
    chromosomes written so far are a valid, readable, SHORTER genome — so those ops
    return a clean partial with ``status="cancelled"``. A count has no such property:
    a partial count is not a smaller valid count, it is a WRONG one. Every downstream
    read — :func:`conserved_core`'s antimode walk, the ``>= k`` promotion — would
    silently derive a different threshold from an under-counted histogram, and nothing
    in the result would reveal it. So the cancel is RAISED: a caller cannot mistake a
    truncated scan for a completed one. The counts accumulated so far ride on
    ``.counts`` (with ``.done`` / ``.total``) for a caller that wants to inspect or
    resume them, but they are handed over as explicitly partial."""

    def __init__(self, done, total, counts):
        super().__init__(
            f"section_counts: cancelled by the progress tick after {done} of {total} "
            f"sections. A PARTIAL count is not a valid count — it would shift every "
            f"downstream conservation threshold — so it is raised, not returned; the "
            f"counts accumulated so far are on .counts")
        self.done = done
        self.total = total
        self.counts = counts


def section_counts(section_store, *, coupling=None, progress=None) -> dict:
    """Derive ``{global_id: n_sections}`` — how many distinct PLASMID sections each
    GLOBAL node appears in — by scanning the store's sections' GLOBAL ``node_ids``
    tables. The genome-native, SSoT read stage-2 (rc279) promotes on: a node is
    CONSERVED iff its section-occurrence count >= k (a plain integer accumulator, no
    spectral solve). The VOCAB chromosome (the karyotype index) is excluded.

    **rc280 — the scan reads only what it needs (§102 / F1253).** Two costs made this
    the ~22-hour path the field measured at 240,881 sections (~0.33 s/section):

    1. **The catalog was re-derived per section.** A v12 HEAD-ONLY manifest stores no
       chromosome table — :func:`genome.genome_window` derives it by scanning the WHOLE
       body and re-folding its Merkle chain, and it did that once PER SECTION. That is
       O(P × whole body): quadratic in corpus size, and it dominated everything else.
       The catalog is now derived **once** for the whole scan and the per-section reads
       page against it.
    2. **Every section's full graph was decoded** — edges, weights and charges — to
       reach a ``node_ids`` table that the §89 payload puts BEFORE all of them
       (``[vocab_size, n_node_ids] + node_ids + …``). The read is now TARGETED
       (:func:`genome._section_node_ids`): it pages only the node_ids prefix of the
       region and never touches the edge bytes, so per-section cost is O(node_ids)
       rather than O(section). **No format change was needed** — the sections were
       already self-describing, ``quad_turn`` uncouples each leaf independently of
       every other, and the region's leading-cap integrity bound sits in the first
       block, so a prefix pays exactly the same bound as a whole-region read.

    Together the scan goes from O(P² × body) to O(P × node_ids). The counts are
    **byte-identical** to the full-decode derivation — that equivalence is the SSoT
    check and is pinned by the rc280 test.

    ``progress`` — a Python-only ``ev -> bool`` callback (NOT a wire param); it fires
    between whole SECTIONS with ``phase=EXTRACTING``, ``done=sections scanned so far``,
    ``total=P``. A truthy return raises :class:`SectionCountsCancelled` (a partial
    count is not a valid count — see that class).

    **This is still the deliberate fallback, not the hot path.** :func:`plasmid_extract`
    returns ``section_count`` as a free streamed accumulator; pass it straight to
    :func:`genome_integrate_plasmids` and no scan happens at all. This op exists to
    RESUME against a store you did not just build, and to VERIFY the accumulator
    against the on-disk SSoT. Dispatches the whole scan to the
    ``srmech_genome_section_counts`` C peer when ``HAS_NATIVE`` (a bare-C host derives
    the counts end-to-end); the pure body is the numpy-free alternative + byte-parity
    oracle. Integer/exact (Class-N); no ``abs()``;"""
    store = Path(section_store)
    # ONE catalog derivation for the WHOLE scan (rc280 fix 1). Deriving it here and
    # paging every section against it is what removes the O(P × body) quadratic —
    # genome_window would re-derive it on every single call.
    leaf_dim, one, entries = _section_entries(store, coupling)
    total = len(entries)
    # rc306 (task #899): the C peer takes a caller arena instead of a 32 MiB static
    # one (which capped the corpus at ~11k sections). Size it from the store —
    # body_len = turns.bin bytes, n_chroms = the plasmid sections + the excluded
    # vocab karyotype — so the catalog arena scales with the corpus with no cap.
    try:
        body_len = (store / _genome._BODY_NAME).stat().st_size
    except OSError:
        body_len = None
    native = _native.genome_section_counts_c(
        str(store), _coupling_block_bytes(one), leaf_dim, progress,
        body_len=body_len, n_chroms=len(entries) + 1)
    if native is not None:
        ids, cnts, done, cancelled = native
        counts = {int(v): int(c) for v, c in zip(ids, cnts)}
        if cancelled:
            raise SectionCountsCancelled(int(done), total, counts)
        return counts
    counts: Dict[int, int] = {}
    # ONE open of turns.bin for the WHOLE scan (rc282 fix). rc280 removed this scan's
    # quadratic and left a syscall constant: _read_region_prefix opened the body on
    # every call and _section_node_ids calls it in a growth loop, so the pass paid a
    # measured 2.0 opens PER SECTION — ~481,762 opens extrapolated to the 240,881-
    # section field store. Holding the handle makes it 1, independent of P.
    with _genome._open_body_ro(Path(store) / _genome._BODY_NAME) as f:
        for i, entry in enumerate(entries):
            if progress is not None and progress({
                    "struct_size": _PROGRESS_STRUCT_SIZE, "phase": _PHASE_EXTRACTING,
                    "done": i, "total": total}):
                raise SectionCountsCancelled(i, total, counts)
            seen = set()                            # a node counts ONCE per section
            for nid in _genome._section_node_ids(store, entry, leaf_dim, one, f):
                seen.add(int(nid))
            for nid in seen:
                counts[nid] = counts.get(nid, 0) + 1
    return counts


# ─────────────────────────────────────────────────────────────────────────────
#  STAGE 2 — ORGANIZE (rc279, §102 / F1252)
#
#  CONSERVE -> PROMOTE -> MERGE. The step that structurally REMOVES the monolithic
#  from-scratch `recursive_cut` from the encode path: stage 2 is a merge + promote
#  over sections that stage 1 ALREADY structured, never a global spectral solve.
#
#  THE CONSERVATION CRITERION AND ITS OPEN QUESTION (honest scope — read this).
#  A node is CONSERVED iff its SECTION-COUNT (how many distinct plasmid sections it
#  appears in) is >= k. This is a *different discriminator* from F1250's global
#  cross-community participation antimode: participation measures cross-COMMUNITY
#  boundary mass on the whole graph; conservation measures cross-DOCUMENT sharing.
#  **Their equivalence has NOT been measured** — the real simplewiki corpus was not
#  available to this rc — so stage 2 is NOT claimed to be a byte-equivalent refactor
#  of `genome_from_graph`, and the convergence of the two reads is **PENDING
#  validation on the real corpus**. What IS proven here: the incremental organize
#  replaces the from-scratch monolithic partition; the cost is O(|E|) incremental
#  against O(D * |E| * log n) from-scratch; the shape is the biology-exact F1251
#  core/accessory split; and `k` is DERIVED from the data (below), never tuned.
# ─────────────────────────────────────────────────────────────────────────────


def _count_histogram(counts):
    """``(hist, max_count)`` — ``hist[c]`` = how many nodes have section_count ``c``.
    Pure integer cardinalities; no float, no ``abs()`` (a count has no sign)."""
    mx = 0
    for c in counts:
        if c > mx:
            mx = c
    hist = [0] * (mx + 1)
    for c in counts:
        hist[c] += 1
    return hist, mx


def _conserved_side_argmax(hist, lo, hi):
    """The bin of the maximum count in ``hist[lo:hi+1]`` (lowest index on a tie) — the
    dominant mode of ONE SIDE of an antimode gap. Mirrors :func:`genome._side_argmax`."""
    best = lo
    for b in range(lo, hi + 1):
        if hist[b] > hist[best]:
            best = b
    return best


def _conserved_side_modes(hist, max_count):
    """PRECOMPUTE both flanking modes for every possible gap in ONE pass each:
    ``pre[b]`` = argmax over ``hist[0..b]``, ``suf[b]`` = argmax over
    ``hist[b..max_count]``, both lowest-index-on-tie (so they agree exactly with
    :func:`_conserved_side_argmax`).

    Why this matters: the real corpus histogram is heavy-tailed, with a maximum count
    in the hundreds of thousands and ~1.7k occupied bins. Re-scanning a side per gap
    would be O(gaps * max_count) — hundreds of millions of reads for ONE derivation.
    Two prefix passes make the whole antimode walk O(max_count). Pure integer."""
    pre = [0] * (max_count + 1)
    suf = [0] * (max_count + 1)
    best = 0
    for b in range(max_count + 1):
        if hist[b] > hist[best]:
            best = b                                # strict > keeps the LOWEST index
        pre[b] = best
    best = max_count
    for b in range(max_count, -1, -1):
        if hist[b] >= hist[best]:
            best = b                                # >= walking down keeps the LOWEST
        suf[b] = best
    return pre, suf


def _conserved_antimode(hist, max_count):
    """MEASURE the ANTIMODE of the section-count histogram — **this is why ``k`` is an
    OUTPUT OF THE DATA, not a magic constant**.

    The count-domain mirror of the rc272 participation antimode
    (:func:`genome._partition_antimode`): same gap walk, same qualifying predicate,
    same widest-gap tie-break. Walks the GAPS between consecutive OCCUPIED count-bins;
    a gap qualifies iff it is at least one bin WIDE (a genuine empty separation, not
    adjacent bins) and the dominant mode on EACH side is a real mode (>= 2 nodes).
    BIMODAL -> split at the WIDEST qualifying gap (ties -> the larger smaller-mode,
    then the lower bin), with ``k = lo + 1`` (the empty gap makes ``>= lo+1`` and
    ``>= hi`` the same node set).

    **Note the INVERSION vs participation.** There HIGH participation = a
    community-bridging shared service = PLASMID. Here HIGH section-count = shared
    across many plasmid sections = the CONSERVED NUCLEAR core. The metric flips
    direction; the antimode discipline does not.

    UNIMODAL (no qualifying gap) -> ONE-DNA-TYPE: ``bimodal`` False, ``k`` 0 — the
    split is NOT forced (the F1250 discipline). Pure integer; deterministic; no float,
    no ``abs()``."""
    best_lo = best_w = best_sm = 0
    found = False
    prev = None
    pre, suf = _conserved_side_modes(hist, max_count)
    for b in range(max_count + 1):
        if hist[b] == 0:
            continue
        if prev is not None and b - prev >= 2:
            plo = pre[prev]                          # == _conserved_side_argmax(0, prev)
            phi = suf[b]                             # == _conserved_side_argmax(b, max)
            sm = hist[plo] if hist[plo] < hist[phi] else hist[phi]
            w = b - prev
            if sm >= 2 and (not found or w > best_w
                            or (w == best_w and sm > best_sm)):
                best_lo, best_w, best_sm, found = prev, w, sm, True
        prev = b
    if not found:
        return {"bimodal": False, "k": 0, "threshold": None, "gap": 0}
    return {"bimodal": True, "k": best_lo + 1, "threshold": best_lo, "gap": best_w}


#: ``k="auto"`` — ATTEMPT the antimode derivation, and HONESTLY DECLINE (no core, no
#: manufactured threshold) when the distribution admits no qualifying split. The
#: canonical spelling; ``k=None`` is accepted as its alias.
K_AUTO = "auto"

#: ``k_source`` values on the :func:`conserved_core` result — the provenance of the
#: threshold, so a caller can never mistake a POLICY choice for a MEASURED one.
K_DERIVED = "derived"      # a qualifying antimode was MEASURED; k is an output of the data
K_DECLINED = "declined"    # no qualifying antimode; NO k manufactured (one-DNA-type)
K_POLICY = "policy"        # a caller-supplied k — a STATED POLICY CHOICE the caller owns


def conserved_core(section_count, *, k=K_AUTO) -> dict:
    """CONSERVE (STAGE 2 step 1) — read the section-count distribution and return the
    CONSERVED CORE node set + the threshold ``k`` **derived from the data**.

    ``section_count`` is the ``{global_id: n_sections}`` integer accumulator
    :func:`plasmid_extract` returns for free (or :func:`section_counts` re-derives). A
    node is CONSERVED iff its count is ``>= k`` -> it joins the NUCLEAR core; the rest
    stay accessory PLASMID. Expect the ASYMMETRIC minority core (~16/84 — F1251), not
    a 50/50 split.

    **``k`` IS DERIVED OR DECLINED — NEVER MANUFACTURED.** With ``k="auto"`` (the
    default; ``None`` is an accepted alias) this MEASURES the ANTIMODE of the
    section-count histogram — the same walk and qualifying predicate as the rc272
    participation antimode, applied in the count domain (see
    :func:`_conserved_antimode`; note the metric INVERSION — high count = nuclear).
    If no qualifying antimode exists the result is ``k_source="declined"``: an EMPTY
    core, ``k=0``, ``one_dna_type=True``, and **no threshold is invented**.

    **This decline is a first-class outcome, not a failure — and the real corpus takes
    it.** F1253 measured the section-count curve over the full simplewiki store
    (1,100,189 ids, 240,881 sections): singleton 64.6 %, >=2 35.4 %, >=5 14.5 %, >=10
    8.4 %, >=25 4.3 %, >=50 2.7 %, >=100 1.7 % — successive ratios ~2.4, 1.7, 2.0,
    1.6, 1.6 decay SMOOTHLY. That is a heavy-tailed, near-power-law shape, and **a
    scale-free distribution has no characteristic scale, hence no natural antimode**.
    On such a curve this function correctly declines. Reporting "no natural split in
    this distribution" IS the finding; manufacturing a `k` to fill the silence would
    not be.

    Passing an explicit integer ``k`` yields ``k_source="policy"`` — a **stated policy
    choice the CALLER owns**, never presented as measured. In particular, choosing a
    ``k`` because it reproduces F1251's ~16 % core fraction would be **post-hoc
    numerology**, not a derivation: on the F1253 curve ``k>=5`` gives 14.5 % against
    an attested ~16 %, but that correspondence is threshold-dependent and is NOT used
    here to select ``k``.

    Returns ``{"k", "k_source", "bimodal", "one_dna_type", "core", "accessory",
    "n_core", "n_accessory", "histogram", "threshold", "gap"}`` — ``core`` /
    ``accessory`` are sorted GLOBAL id lists (a canonical order, so the organize is
    deterministic), and ``k_source`` is one of :data:`K_DERIVED` / :data:`K_DECLINED`
    / :data:`K_POLICY`.
    Dispatches the whole read to the ``srmech_genome_conserved_core`` C peer when
    ``HAS_NATIVE`` (a bare-C host runs the CONSERVE step end-to-end); the pure body is
    the numpy-free alternative + parity oracle. Class-N exact integer arithmetic; no
    float, no ``abs()``, no spectral solve."""
    ids = sorted(int(v) for v in section_count)
    counts = [int(section_count[v]) for v in ids]
    auto = k is None or k == K_AUTO
    if not auto and (not isinstance(k, int) or isinstance(k, bool) or k < 1):
        raise ValueError(
            f"conserved_core: k must be a positive int, {K_AUTO!r}, or None; got {k!r}")
    hist, max_count = _count_histogram(counts)
    am = _conserved_antimode(hist, max_count)        # measured ONCE (O(max_count))
    native = _native.genome_conserved_core_c(ids, counts, -1 if auto else k)
    if native is not None:
        core, k_used, bimodal = native
    else:
        if auto:
            k_used, bimodal = am["k"], am["bimodal"]
        else:
            k_used, bimodal = k, True
        core = [v for v, c in zip(ids, counts) if bimodal and k_used > 0 and c >= k_used]
    # k_source is the THRESHOLD'S PROVENANCE — so a caller can never mistake a stated
    # policy choice for a measured one, nor a decline for a derivation.
    if not auto:
        k_source = K_POLICY
    elif bimodal:
        k_source = K_DERIVED
    else:
        k_source = K_DECLINED           # no qualifying antimode -> NO k manufactured
    core_set = set(core)
    accessory = [v for v in ids if v not in core_set]
    return {"k": k_used, "k_source": k_source, "bimodal": bool(bimodal),
            "one_dna_type": not bimodal, "core": list(core), "accessory": accessory,
            "n_core": len(core), "n_accessory": len(accessory), "histogram": hist,
            "threshold": am["threshold"], "gap": am["gap"]}


def _section_labels(store, coupling) -> List[str]:
    """The store's PLASMID section labels in census order (the VOCAB karyotype
    chromosome excluded).

    **NOT cheap, despite what this docstring claimed before rc280.** It was described
    as "an O(1)-HEAD manifest read that does not touch section bodies". That is false
    on a v12 HEAD-ONLY manifest, which stores no chromosome table: ``genome_census``
    derives one by reading the ENTIRE body and re-folding its Merkle chain. One call is
    O(body); a call per section is the O(P × body) quadratic rc280 removed. Prefer
    :func:`_section_entries`, which pays that cost ONCE and hands back the entries the
    per-section reads page against."""
    census = genome_census(store, coupling=coupling)
    return [c["label"] for c in census["chromosomes"] if c["label"] != VOCAB_LABEL]


def _section_strand(store, label, coupling, dim, entry=None, leaf_dim=None, f=None):
    """One plasmid section's full chromosome STRAND (its kernel telomere + coupled
    leaves) — what :func:`genome.integrate` splices as a provirus. Pass a pre-derived
    catalog ``entry`` when looping over sections (§102/rc280 — see
    :func:`_section_entries`)."""
    leaves = _section_leaves(store, label, coupling, entry, leaf_dim, f)
    return [_genome._kernel_telomere(label, dim=dim)] + list(leaves)


def _section_global_edges(store, label, coupling, entry=None, leaf_dim=None, f=None):
    """One section's edges as ``[(u_global, v_global, weight), ...]`` — its LOCAL edge
    indices resolved through its GLOBAL ``node_ids`` table (the id space stage 1
    established so a word shared across sections carries the SAME id).

    This one genuinely needs the WHOLE section (the edges are the payload), so the
    rc280 targeted prefix read does not apply here — but the catalog-once fix does,
    via ``entry``."""
    graph = _read_section_graph(store, label, coupling, entry, leaf_dim, f)
    nid = [int(x) for x in graph["node_ids"]]
    return [(nid[int(i)], nid[int(j)], int(w))
            for (i, j), w in zip(graph["edges"], graph["weights"])]


def _core_weight_from_sections(sections, core_set):
    """Accumulate the induced CORE subgraph as ``{(u, v): summed_weight}`` over an
    iterable of per-section global edge lists, keeping only edges with BOTH endpoints
    conserved. Summing the per-section multiplicities makes the result ORDER-FREE — so
    the incremental and from-scratch paths agree exactly, whatever order the sections
    were accumulated in. Integer only; no ``abs()``."""
    weight: Dict[tuple, int] = {}
    for edges in sections:
        for (u, v, w) in edges:
            if u in core_set and v in core_set:
                key = (u, v)
                weight[key] = weight.get(key, 0) + w
    return weight


def _core_packed(core_nodes, core_weight, coupling, dim, label="core"):
    """Encode the induced CORE subgraph to a §89 KERNEL chromosome — the ALREADY-PACKED
    but NOT-YET-MINTED strand. PROMOTION (the ``0x58`` centromere) is the ORGANIZE
    step's job, so the C orchestrator can perform it via its own
    ``srmech_genome_mint_strand`` call and the two paths stay byte-identical.

    Edges are emitted in CANONICAL sorted order over the GLOBAL ids and remapped to
    LOCAL indices with ``node_ids`` carrying the global table — the same convention the
    sections use, and deterministic regardless of accumulation order."""
    local = {v: i for i, v in enumerate(core_nodes)}
    keys = sorted(core_weight)
    edges = [(local[u], local[v]) for (u, v) in keys]
    weights = [core_weight[key] for key in keys]
    syms = _encode_section_syms(len(core_nodes), edges, weights, core_nodes)
    return _genome.kernel_pack(syms, leaf_dim=dim, label=label, coupling=coupling)


def _organize_native(core_strand, section_strands, coupling, dim, progress):
    """DISPATCH the whole ORGANIZE (mint the core + fold the plasmids, ticking between
    whole chromosomes) to the ``srmech_genome_integrate_plasmids`` C peer. Returns
    ``(strand, n_integrated, cancelled)`` or ``None`` to fall back to the pure fold."""
    core_blocks = _genome._leaf_blocks(core_strand) if core_strand else []
    sec_blocks = [_genome._leaf_blocks(s) for s in section_strands]
    if any(len(b) != dim for blocks in sec_blocks for b in blocks):
        return None
    if any(len(b) != dim for b in core_blocks):
        return None
    return _native.genome_integrate_plasmids_c(
        b"".join(core_blocks), len(core_blocks),
        b"".join(b"".join(blocks) for blocks in sec_blocks),
        [len(blocks) for blocks in sec_blocks], dim,
        _coupling_block_bytes(coupling), progress)


def genome_integrate_plasmids(section_store, coupling, *, section_count=None, k=K_AUTO,
                              core_edges=None, out_path=None, progress=None) -> dict:
    """STAGE 2 ORGANIZE — sections -> a minted NUCLEAR CORE + retained PLASMIDS.

    The op that structurally removes the monolithic from-scratch partition from the
    encode path: it CONSERVES (read the section-count distribution, derive ``k``),
    PROMOTES (mint the induced core subgraph via :func:`genome.mint_strand` — the
    ``0x58`` centromere), and MERGES (fold the retained plasmid sections in via
    :func:`genome.integrate`). **`recursive_cut` is never called and nothing is ever
    re-extracted.**

    **PASS ``section_count`` — IT IS FREE, AND THE ALTERNATIVE IS NOT.**
    :func:`plasmid_extract` already returns ``section_count`` as a streamed integer
    accumulator built during the append pass, costing nothing extra. Chaining
    stage 1 -> stage 2 should hand it straight through::

        ext = plasmid_extract(docs, store, coupling)
        org = genome_integrate_plasmids(store, coupling,
                                        section_count=ext["section_count"])

    When ``section_count`` is omitted this falls back to :func:`section_counts`, which
    RE-DERIVES the counts by decoding **every section body** — an O(P * section) full
    re-scan measured at ~0.33 s/section downstream (hours at corpus scale). That
    fallback exists for RESUMING against a store you did not just build, and for
    VERIFYING the accumulator against the on-disk SSoT — it is the deliberate slow
    path, never the hot one. Same for ``core_edges``: supply the per-section global
    edge lists (as :func:`add_plasmid` maintains them) to skip the core-harvest read
    entirely; omit it and the sections are read ONCE to harvest the core subgraph.

    ``k=None`` DERIVES the conservation threshold from the section-count distribution's
    antimode (see :func:`conserved_core`) — it is an output of the data, never tuned.
    A UNIMODAL distribution yields ONE-DNA-TYPE: no core is promoted and the plasmids
    are folded as-is (the split is not forced).

    ``progress`` is a Python-only ``ev -> bool`` callback (NOT a wire param). It fires
    between whole CHROMOSOMES: once with ``phase=MINTING`` for the core promote, then
    per section with ``phase=INTEGRATING`` (``done`` = sections merged, ``total`` = P).
    There is no scan phase when ``section_count`` is supplied — the fast path does no
    counting work to report. A truthy return CANCELS cleanly: the returned strand is
    the minted core plus the sections merged so far — a valid, readable shorter
    organized genome, truncated at a chromosome boundary, and ``out_path`` is NOT
    written.

    Returns ``{"strand", "k", "bimodal", "one_dna_type", "core", "counts": {"nuclear",
    "plasmid"}, "n_sections", "n_integrated", "histogram", "status"}``. Dispatches the
    mint + fold to the ``srmech_genome_integrate_plasmids`` C peer when ``HAS_NATIVE``
    (byte-identical to the pure fold — the parity contract); a bare-C host runs stage 2
    end-to-end via that peer. Integer/exact; no ``abs()``.

    **Honest scope:** the conservation criterion (section-count >= k) is a DIFFERENT
    discriminator from F1250's global participation antimode, and **their convergence
    is PENDING validation on the real corpus** — it is not claimed here."""
    store = Path(section_store)
    dim = len(list(coupling))
    # rc280: derive the catalog ONCE for every read below (the labels, the optional
    # core-subgraph harvest, and the strand fold). Each of those used to re-derive it
    # per section — three separate O(P × body) quadratics on one call.
    leaf_dim, _one, entries = _section_entries(store, coupling)
    labels = [e["label"] for e in entries]
    counts = dict(section_count) if section_count is not None else section_counts(
        store, coupling=coupling)                    # the deliberate fallback
    split = conserved_core(counts, k=k)
    core_nodes = split["core"]
    # rc282: ONE held body handle for BOTH per-section loops below (the edge harvest
    # and the strand fold) — each used to re-open turns.bin per section.
    with _genome._open_body_ro(Path(store) / _genome._BODY_NAME) as f:
        if core_nodes:
            if core_edges is None:
                core_edges = [_section_global_edges(store, e["label"], coupling, e,
                                                    leaf_dim, f)
                              for e in entries]
            core_weight = _core_weight_from_sections(core_edges, set(core_nodes))
            core_strand = _core_packed(core_nodes, core_weight, coupling, dim)
        else:
            core_strand = []                       # ONE-DNA-TYPE: no core promoted
        section_strands = [_section_strand(store, e["label"], coupling, dim, e,
                                           leaf_dim, f)
                           for e in entries]
    strand, n_integrated, cancelled = _organize(
        core_strand, section_strands, coupling, dim, progress)
    status = _STATUS_CANCELLED if cancelled else _STATUS_OK
    if out_path is not None and not cancelled:
        # `#T1108`: this is the ONE plasmid write that lands in a DIFFERENT
        # directory, so carry-forward cannot reach it from `out_path`. It DERIVES
        # the block from the section store it was built out of — the corpus is the
        # same corpus, so the source is the same source.
        _genome.genome_save(
            strand, out_path, coupling,
            attestation=_genome._on_disk_source_attestation(section_store) or None)
    return {"strand": strand, "k": split["k"], "k_source": split["k_source"],
            "bimodal": split["bimodal"],
            "one_dna_type": split["one_dna_type"], "core": core_nodes,
            "counts": {"nuclear": split["n_core"], "plasmid": split["n_accessory"]},
            "n_sections": len(labels), "n_integrated": n_integrated,
            "histogram": split["histogram"], "status": status}


def _organize(core_strand, section_strands, coupling, dim, progress):
    """PROMOTE + MERGE. Dispatches to the C orchestrator when possible, else folds in
    pure Python. ``(strand, n_integrated, cancelled)``.

    The pure fold is the ACCUMULATED concatenation, which is exactly
    ``genome.integrate``'s ``at=None`` tail-append composed over the sections
    (associativity) — the rc279 test pins that equivalence against a literal
    :func:`genome.integrate` fold, so the fast accumulation is not a shortcut around
    the primitive but a proven-equal form of it."""
    total = len(section_strands)
    # §101 C-REALITY (the design's rc279 resolution of the parity-audit concern): the
    # tick is handed THROUGH to the C orchestrator, so the heartbeat + cancel are the
    # C loop's own — not a Python driver hook wrapped around an opaque C call.
    native = _organize_native(core_strand, section_strands, coupling, dim, progress)
    if native is not None:
        return native
    if core_strand and progress is not None and progress({
            "struct_size": _PROGRESS_STRUCT_SIZE, "phase": _PHASE_MINTING,
            "done": 0, "total": 1}):
        return [], 0, True
    # PROMOTE — the pure mirror of the C orchestrator's mint_strand call: the packed
    # core becomes a Tier-2 NUCLEAR chromosome (0x58 centromere, metacentric split).
    strand = _genome.mint_strand(core_strand, coupling) if core_strand else []
    for i, sec in enumerate(section_strands):
        if progress is not None and progress({
                "struct_size": _PROGRESS_STRUCT_SIZE, "phase": _PHASE_INTEGRATING,
                "done": i, "total": total}):
            return strand, i, True
        strand = strand + list(sec)                # == integrate(strand, sec) at=None
    return strand, total, False


def add_plasmid(section_store, coupling, tokens, *, state, k=K_AUTO, window=2,
                top_k=20, cap_slack=4, label_prefix="sec", cache_edges=True,
                progress=None) -> dict:
    """INCREMENTAL STAGE 1 + 2 — add ONE document to an organized genome.

    The incremental face of the two-stage encode, and the reason there is no
    monolithic block left to be blind inside. Adding a document is:

    1. **stage-1 append** — extract its LOCAL co-occurrence graph and append ONE
       plasmid section (:func:`plasmid_extract`; O(doc), O(1) HEAD rewrite);
    2. **count bump** — ``section_count[node] += 1`` over the new section, O(section);
    3. **core delta** — re-derive ``k``, and re-mint ONLY the small conserved core.

    **A global ``recursive_cut`` is never run and no document is ever re-extracted.**
    Every plasmid section, and the core when it did not change, stay byte-untouched.

    ``state`` is the running organize state this function threads — pass ``None`` to
    start, then feed back the returned ``state`` on each subsequent call. It carries
    ``{"section_count", "vocab", "labels", "core", "k", "sections"}``. With
    ``cache_edges`` (default) the per-section GLOBAL edge lists are kept in ``state``,
    so a threshold crossing re-filters them in memory and NOTHING is re-read from
    disk; the cost is O(|E|) resident. Set ``cache_edges=False`` to trade that memory
    back for a re-read of the store when the core membership changes (the counts and
    the fast path are unaffected either way).

    Returns ``{"strand", "state", "section", "k", "core_changed", "counts",
    "n_sections", "status", ...}`` — the organized genome after the add.

    **Equivalence contract (pinned by the rc279 test):** calling ``add_plasmid`` D
    times over D documents produces a BYTE-IDENTICAL organized genome to one
    :func:`genome_integrate_plasmids` over the same D sections. The incremental rule
    is EXACT, not an approximation: the core subgraph sums per-section edge
    multiplicities and emits them in canonical sorted order, so it is independent of
    the order in which sections were accumulated. Integer/exact; no
    ``abs()``."""
    store = Path(section_store)
    dim = len(list(coupling))
    st = dict(state) if state else {"section_count": {}, "vocab": [], "labels": [],
                                    "core": [], "k": 0, "sections": []}
    ext = plasmid_extract([tokens], store, coupling, vocab=st["vocab"], window=window,
                          k=top_k, cap_slack=cap_slack, label_prefix=label_prefix)
    label = ext["sections"][-1]
    st["vocab"] = ext["vocab"]
    st["labels"] = list(st["labels"]) + [label]
    # rc334 (§102 G7, #887) — the WHOLE-OP native dispatch closing the LAST genome
    # wire-glue gap: srmech_genome_add_plasmid runs the CONSERVE (merge the counts +
    # conserved_core) + ORGANIZE (harvest + pack the core off disk, then fold the
    # organized strand) half END-TO-END in C over the store the stage-1 append (above)
    # just extended. The prior section-count accumulator + the new section's global
    # node_ids marshal IN, the byte-identical strand + the new {section_count, core, k}
    # state marshal OUT. The pure body below is the complete byte-identical alternative.
    _auto = k is None or k == K_AUTO
    _k_valid = _auto or (isinstance(k, int) and not isinstance(k, bool) and k >= 1)
    if _k_valid:
        try:
            _body_len = (store / _genome._BODY_NAME).stat().st_size
        except OSError:
            _body_len = None
        native = _native.genome_add_plasmid_c(
            store, coupling, dim, -1 if _auto else int(k),
            st["section_count"], list(ext["section_count"].keys()),
            list(st.get("core") or []),
            body_len=_body_len, n_chroms=len(st["labels"]) + 1,
            progress=progress) if _body_len is not None else None
        if native is not None:
            (strand, counts, core_nodes, k_used, bimodal, core_changed,
             n_integrated, cancelled) = native
            st["section_count"] = counts
            st["core"], st["k"] = list(core_nodes), k_used
            if cache_edges:
                leaf_dim, _one, entries = _section_entries(store, coupling)
                with _genome._open_body_ro(Path(store) / _genome._BODY_NAME) as f:
                    new_edges = _section_global_edges(
                        store, label, coupling,
                        {e["label"]: e for e in entries}.get(label), leaf_dim, f)
                st["sections"] = list(st["sections"]) + [new_edges]
            k_source = (K_POLICY if not _auto
                        else (K_DERIVED if bimodal else K_DECLINED))
            n_core = len(core_nodes)
            return {"strand": strand, "state": st, "section": label, "k": k_used,
                    "k_source": k_source, "core_changed": core_changed,
                    "core": list(core_nodes), "bimodal": bimodal,
                    "one_dna_type": not bimodal,
                    "counts": {"nuclear": n_core, "plasmid": len(counts) - n_core},
                    "n_sections": len(st["labels"]), "n_integrated": n_integrated,
                    "status": _STATUS_CANCELLED if cancelled else _STATUS_OK}
    counts = dict(st["section_count"])             # O(section) integer bump
    for node, bump in ext["section_count"].items():
        counts[node] = counts.get(node, 0) + bump
    st["section_count"] = counts
    # rc280: one catalog derivation serves the new section's edge read AND (when the
    # core moved, or the edge cache is off) every re-read + the strand fold below.
    leaf_dim, _one, entries = _section_entries(store, coupling)
    by_label = {e["label"]: e for e in entries}
    # rc282: ONE held body handle for the new section's edge read AND both per-section
    # loops below — each of those used to re-open turns.bin once per section.
    with _genome._open_body_ro(Path(store) / _genome._BODY_NAME) as f:
        new_edges = _section_global_edges(store, label, coupling, by_label.get(label),
                                          leaf_dim, f)
        if cache_edges:
            st["sections"] = list(st["sections"]) + [new_edges]
        split = conserved_core(counts, k=k)
        core_nodes = split["core"]
        core_changed = list(core_nodes) != list(st.get("core") or [])
        st["core"], st["k"] = list(core_nodes), split["k"]
        if core_nodes:
            if cache_edges:
                sections = st["sections"]
            else:
                sections = [_section_global_edges(store, lb, coupling,
                                                  by_label.get(lb), leaf_dim, f)
                            for lb in st["labels"]]
            core_weight = _core_weight_from_sections(sections, set(core_nodes))
            core_strand = _core_packed(core_nodes, core_weight, coupling, dim)
        else:
            core_strand = []
        section_strands = [_section_strand(store, lb, coupling, dim,
                                           by_label.get(lb), leaf_dim, f)
                           for lb in st["labels"]]
    strand, n_integrated, cancelled = _organize(
        core_strand, section_strands, coupling, dim, progress)
    return {"strand": strand, "state": st, "section": label, "k": split["k"],
            "k_source": split["k_source"],
            "core_changed": core_changed, "core": core_nodes,
            "bimodal": split["bimodal"], "one_dna_type": split["one_dna_type"],
            "counts": {"nuclear": split["n_core"], "plasmid": split["n_accessory"]},
            "n_sections": len(st["labels"]), "n_integrated": n_integrated,
            "status": _STATUS_CANCELLED if cancelled else _STATUS_OK}
