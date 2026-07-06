"""siona.genome_store — pack siona's Klein-4 instrument into a native srmech genome (PKG-3 / #249).

Replaces the loose NDJSON+title-index instrument with a single native srmech genome. Each named body
(a tool vector, a stored-kernel article, an F1035 kernel) is a flat **Klein-4 hypervector** — siona's is
D=8192 — chunked into ``leaf_dim``-wide leaves and packed as ONE telomere-capped chromosome of a native
srmech ``genome()`` strand. Recall reads the strand back and splits it by inline CHROM cap via
``partition`` — the byte-exact multi-kernel round-trip::

    partition(genome({label: leaves}, one), one) == {label: leaves}

**#249 fix (F1084/F1087/F1094).** The earlier store packed via ``kernel_pack`` and recalled via
``genome_window`` + ``kernel_unpack`` — which the rc135 v11 format's per-chromosome CHROM cap made
MISCOUNT (D=8192 came back 8448: the cap leaf counted as data, on BOTH ``kernel_unpack`` and ``recall``).
The native ``genome()``/``partition`` path — the one Siona's own imitation tier SHOWED us (``siona.introspect``
mined ``partition(genome({…}), one) == {…}`` from srmech's docstring) — round-trips BYTE-EXACT. Siona's
D=8192 is a multiple of ``leaf_dim=256``, so the leaves flatten back to exactly D with NO trim; a non-aligned
D raises (mixed-dimension self-describing recall awaits the upstream cap fix, UPSTREAM §90).

Still the sparse store: on disk each symbol is bit-packed (F1044), so an N-body instrument costs
≈ ``sum(D_i) / 4`` bytes + caps. And it stays demand-loadable — the point of F1094: disk weight climbs with
the corpus, but working RAM need not, because ``partition`` can page a labelled subset. No numpy; no floats;
Klein-4 end to end.
"""
import srmech.amsc.genome as _G
from srmech.amsc import hdc as _hdc

__all__ = ["pack_instrument", "load_kernel", "load_instrument", "add_kernel", "LEAF_DIM"]

LEAF_DIM = 256          # srmech LEAF_CAP — the tome width each D-vector chunks into
_COUPLER_SEED = 0       # siona's canonical coupling invariant (deterministic; recorded in the manifest)


def _coupler(leaf_dim=LEAF_DIM):
    """siona's coupling invariant ``the_one`` — a deterministic Klein-4 leaf of width ``leaf_dim``.
    Pack and recall use the same one; it is also stored in the genome manifest on save."""
    return _hdc.klein4_random(leaf_dim, seed=_COUPLER_SEED)


def _leaves(hv, leaf_dim):
    """Chunk a flat Klein-4 HV into ``leaf_dim``-wide leaves (the Class-A tome width). D must be aligned —
    the native ``chromosome`` binds each full-width leaf through ``the_one`` (a short final leaf can't bind)."""
    flat = [int(x) for x in hv]
    if len(flat) % leaf_dim:
        raise ValueError(
            "genome_store: D=%d is not a multiple of leaf_dim=%d — the native genome()/partition round-trip "
            "needs aligned leaves; mixed-D self-describing recall awaits the upstream cap fix (UPSTREAM §90)."
            % (len(flat), leaf_dim))
    return [flat[i:i + leaf_dim] for i in range(0, len(flat), leaf_dim)]


def _flatten(leaves):
    """Concatenate a kernel's recovered leaves back to the flat D-vector (int Klein-4 symbols)."""
    return [int(x) for leaf in leaves for x in leaf]


def pack_instrument(named_vectors, path, *, leaf_dim=LEAF_DIM, the_one=None):
    """Pack an iterable of ``(label, klein4_HV)`` into ONE native genome directory at ``path`` (#249).

    Each HV is chunked into aligned leaves and becomes one chromosome of a native ``genome()`` strand.
    Returns the srmech manifest ``dict``. Duplicate labels raise upstream; a non-aligned D raises here.
    """
    one = _coupler(leaf_dim) if the_one is None else the_one
    kernels, labels = {}, []
    for label, hv in named_vectors:
        kernels[label] = _leaves(hv, leaf_dim)
        labels.append(label)
    strand = _G.genome(kernels, one)
    return _G.genome_save(strand, str(path), one, labels)


def load_instrument(path, *, the_one=None):
    """Recall EVERY kernel — ``{label: flat Klein-4 list}`` — byte-exact via ``genome_load`` + ``partition`` (#249)."""
    strand, one, labels = _G.genome_load(str(path))
    parts = _G.partition(strand, one, labels)
    return {label: _flatten(leaves) for label, leaves in parts.items()}


def load_kernel(path, label, *, the_one=None):
    """Recall ONE kernel by label — the exact flat Klein-4 ``list[int]`` (#249). ``partition``'s ``labels``
    filter pages just this chromosome (the demand-load path — F1094: RAM tracks the expressed subset, not disk)."""
    strand, one, _labels = _G.genome_load(str(path))
    parts = _G.partition(strand, one, [label])
    return _flatten(parts[label])


def build_genome(named_genes, *, leaf_dim=LEAF_DIM, the_one=None, label="genome"):
    """Build a REGULATORY genome — the ALL-POSSIBLE-information object (F1095). Each ``gene`` is
    ``(label, hv)`` (always expressed), ``(label, hv, activator_mask)``, or ``(label, hv, activator, repressor)``
    — the activator/repressor masks are the epigenetic gates (Class-I bit conditions). Returns ``(strand, the_one)``;
    the strand is a multi-gene chromosome. The genome is NOT the story — :func:`express` reads a story/context OUT
    of it per ``cell_state`` (SAME genome, DIFFERENT cell_state → DIFFERENT expressed subset)."""
    one = _coupler(leaf_dim) if the_one is None else the_one
    genes = [((g[0], _leaves(g[1], leaf_dim)) + tuple(g[2:])) for g in named_genes]
    return _G.chromosome(genes=genes, the_one=one, label=label), one


def express(strand, cell_state, *, the_one):
    """EXPRESS a story/context from the genome (F1095): ``gene_express`` returns only the genes the epigenetic
    ``cell_state`` gates ON → ``{label: flat Klein-4 kernel}``. This is the op⊗operand theorem (the genome's own
    docstring): SAME genome (all-possible), DIFFERENT ``cell_state`` (epigenetic context) → DIFFERENT expressed
    subset (the STORY, or the active CONTEXT). A pure READ — the genome is never mutated. ``cell_state`` is a
    non-negative int (each bit a present condition; Class-I integers, no float; sign stays Class-K)."""
    return {lbl: _flatten(lv) for lbl, lv in _G.gene_express(strand, the_one, cell_state)}


def add_kernel(path, label, hv, *, leaf_dim=LEAF_DIM, the_one=None):
    """Append ONE newly-taught kernel to an existing genome in **O(1)** (F1044 — the helix tail-extends;
    prior bytes are never re-read). The kernel's ``D`` must be a multiple of ``leaf_dim`` (siona's
    D=8192 = 32×256): the raw leaves append header-less, and ``kernel_unpack`` recovers the exact D via
    its §60 back-compat rule (``D = n_leaves × leaf_dim``, no padding). For a D that is NOT a multiple of
    ``leaf_dim`` the self-describing header is required, and there is no public O(1) kernel-append yet
    (UPSTREAM §89) — rebuild with :func:`pack_instrument` in that case. Recall via :func:`load_kernel`."""
    one = _coupler(leaf_dim) if the_one is None else the_one
    flat = list(hv)
    if len(flat) % leaf_dim:
        raise ValueError(
            "add_kernel: D=%d is not a multiple of leaf_dim=%d — O(1) header-less append needs an "
            "aligned D; use pack_instrument (or await the upstream kernel-append, §89)." % (len(flat), leaf_dim))
    leaves = [flat[i:i + leaf_dim] for i in range(0, len(flat), leaf_dim)]
    return _G.genome_append(str(path), label, leaves, one)
