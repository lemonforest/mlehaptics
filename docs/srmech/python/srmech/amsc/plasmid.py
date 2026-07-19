"""srmech.amsc.plasmid — F1252 / §102 STAGE 1 (EXTRACT): the plasmid-native
sectional graph-L store.

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

from . import _native
from . import genome as _genome
# Bare imports of the composed genome ledger ops (so the rosetta reachability walk
# SEES that the plasmid surface reaches C-backed peers — a `_genome.op()` module-
# attribute call is opaque to the walker; a bare-name reference resolves).
from .genome import genome_census, genome_window, kernel_unpack
from .text import cooccurrence_topk

__all__ = ["plasmid_extract", "section_counts"]

#: The label of the shared VOCAB chromosome (the karyotype index) — a KERNEL
#: chromosome in the SAME store carrying the global word -> id table so a reader
#: re-anchors the sections' GLOBAL node_ids. Distinct from the ``sec*`` sections.
VOCAB_LABEL = "__vocab__"

_PHASE_EXTRACTING = _native.SRMECH_PHASE_EXTRACTING
_PROGRESS_STRUCT_SIZE = _native.PROGRESS_STRUCT_SIZE
_STATUS_OK = "ok"
_STATUS_CANCELLED = "cancelled"


def _the_one_block_bytes(the_one) -> bytes:
    """The ``leaf_dim`` raw bytes of the coupling invariant ``the_one`` — the exact
    bytes ``genome_append`` couples each turn through (the C peer's ``the_one``)."""
    return bytes(_genome._leaf_blocks([the_one])[0])


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
                        the_one):
    """The FIRST section into a FRESH store: encode + ``genome_save`` (creates the
    dir + manifest). Same in the native + pure paths (the C append peer requires an
    existing store). Returns the manifest ``data`` dict."""
    syms = _encode_section_syms(vocab_size, edges, weights, node_ids)
    strand = _genome.kernel_pack(syms, leaf_dim=len(list(the_one)), label=label,
                                 the_one=the_one)
    return _genome.genome_save(strand, store, the_one)


def _append_section(store, label, vocab_size, edges, weights, node_ids, the_one,
                    dim, data):
    """Append ONE plasmid section to the EXISTING store. Native: the whole
    ``graph_kernel_encode -> §89 region -> genome_append`` runs in the C
    orchestrator (O(1) HEAD read/write). Pure: ``_graph_kernel_encode`` +
    ``genome_append_kernel`` (byte-identical section). Returns the threaded catalog
    ``data`` (pure) or ``None`` (native — re-derived once at the end)."""
    n_syms = _native.genome_plasmid_extract_c(
        vocab_size, [tuple(e) for e in edges], list(weights), None,
        list(node_ids), [], str(store), label, dim, _the_one_block_bytes(the_one))
    if n_syms is not None:
        return None                                 # C appended; catalog derived later
    syms = _encode_section_syms(vocab_size, edges, weights, node_ids)
    # Thread the catalog dict for O(1) appends (``data`` is the genome_save/append
    # return in the pure path); ``None`` (e.g. a first pure append after a native
    # one) falls to a cold O(1)-head read.
    return _genome.genome_append_kernel(
        store, label, syms, the_one=the_one, catalog=data)


def _write_vocab_chromosome(store, words, the_one) -> None:
    """Write (or refresh) the shared VOCAB chromosome (the karyotype index) — the
    global word->id table as a genome-native KERNEL chromosome. Idempotent: an
    existing vocab chromosome is excised first, so a re-run over a grown vocab keeps
    ONE vocab chromosome. Skipped for an empty vocab."""
    if not words:
        return
    syms = _bytes_to_klein4("\n".join(words).encode("utf-8"))
    census = genome_census(store, the_one=the_one)
    labels = {c["label"] for c in census["chromosomes"]}
    if VOCAB_LABEL in labels:
        _genome.genome_remove(store, VOCAB_LABEL, the_one=the_one)
    _genome.genome_append_kernel(store, VOCAB_LABEL, syms, the_one=the_one,
                                 catalog=None)


def plasmid_extract(docs, section_store, the_one, *, vocab=None, window=2, k=20,
                    cap_slack=4, label_prefix="sec", progress=None) -> dict:
    """STAGE 1 EXTRACT — stream ``docs`` into APPEND-ONLY plasmid sections.

    Each document (a token sequence) becomes ONE Tier-1 plasmid chromosome: its
    LOCAL window co-occurrence graph (:func:`srmech.amsc.text.cooccurrence_topk`,
    ``window`` / top-``k`` / ``cap_slack``), encoded to a §89 KERNEL chromosome with
    GLOBAL node-ids (via the append-only ``vocab``), APPENDED to ``section_store``
    (a genome directory) in O(1). The first document SEEDS the store
    (``genome_save``); the rest append. A shared VOCAB chromosome (the karyotype
    index) is written so a reader re-anchors the GLOBAL ids.

    ``the_one`` — the coupling invariant (its length is the store's ``leaf_dim``,
    which must be >= 52 so the §89 uniformly-Klein-4 kernel header fits one leaf).
    ``vocab`` — a mutable global word list (append-only; ``None`` starts fresh),
    RETURNED grown so a later call streams more documents onto the SAME id space.
    ``progress`` — a Python-only ``ev -> bool`` callback (NOT a wire param); it fires
    between whole SECTIONS with ``phase=EXTRACTING``, ``done=sections so far``,
    ``total=n docs`` — a truthy return CANCELS cleanly (the sections appended so far
    are complete chromosomes; ``status="cancelled"``, no partial section).

    Returns ``{"section_store", "vocab", "section_count", "n_sections", "sections",
    "status"}`` — ``section_count`` the ``{global_id: n_sections}`` integer
    accumulator stage-2 promotes on. numpy-free; no ``abs()``; the whole op is
    genome-native (no loose JSON). Byte-identical whether native or pure."""
    store = Path(section_store)
    dim = len(list(the_one))
    if dim < 52:
        raise ValueError(
            f"plasmid_extract: leaf_dim (len(the_one)) is {dim}; the §89 KERNEL "
            f"section header needs leaf_dim >= 52 (a plasmid section is a kernel "
            f"chromosome). Use a wider the_one.")
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
            store, the_one=the_one)["chromosomes"] if c["label"] != VOCAB_LABEL)
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
                                       the_one)
            store_exists = True
        else:
            data = _append_section(store, label, len(local_words), cooc["edges"],
                                   cooc["weights"], global_ids, the_one, dim, data)
        labels.append(label)
        for g in global_ids:                        # O(section) integer accumulator
            section_count[g] = section_count.get(g, 0) + 1
    _write_vocab_chromosome(store, words, the_one)
    return {"section_store": str(store), "vocab": words,
            "section_count": section_count, "n_sections": len(labels),
            "sections": labels, "status": status}


def _read_section_graph(store, label, the_one):
    """Decode ONE plasmid section back to its directed-graph dict (the LOCAL edges +
    the GLOBAL ``node_ids`` table). Pages the section's coupled leaves
    (:func:`genome_window`), rebuilds the KERNEL strand (prepending the section's
    kernel telomere so ``kernel_unpack`` reads the §89 header), and decodes."""
    leaves = genome_window(store, label, the_one=the_one)
    dim = len(list(the_one))
    strand = [_genome._kernel_telomere(label, dim=dim)] + list(leaves)
    syms = kernel_unpack(strand, the_one)
    return _genome._graph_kernel_decode(syms)


def section_counts(section_store, *, the_one=None) -> dict:
    """Derive ``{global_id: n_sections}`` — how many distinct PLASMID sections each
    GLOBAL node appears in — by SCANNING the store's sections (their GLOBAL
    ``node_ids`` tables). The genome-native, SSoT read stage-2 (rc279) promotes on:
    a node CONSERVED iff its section-occurrence count >= k (a plain integer
    accumulator, no spectral solve). The VOCAB chromosome (the karyotype index) is
    excluded. Integer/exact; no ``abs()``; numpy-free."""
    store = Path(section_store)
    census = genome_census(store, the_one=the_one)
    counts: Dict[int, int] = {}
    for chrom in census["chromosomes"]:
        label = chrom["label"]
        if label == VOCAB_LABEL:
            continue
        graph = _read_section_graph(store, label, the_one)
        seen = set()                                # a node counts ONCE per section
        for nid in graph["node_ids"]:
            seen.add(int(nid))
        for nid in seen:
            counts[nid] = counts.get(nid, 0) + 1
    return counts
