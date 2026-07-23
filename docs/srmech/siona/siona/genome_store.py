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

**§Q8 — the non-abelian substrate move (ADDITIVE; srmech rc311).** klein4 (V4 = ℤ₂×ℤ₂) is the ABELIAN
shadow: it holds the coset ``q & 3`` but DISCARDS the winding sign. Passing ``element_type=ELEMENT_TYPE_Q8``
couples instead through the NON-abelian order-8 quaternion group Q₈ = {±1,±i,±j,±k} (3-bit turns): a
RIGHT-couple by the group product and a recall by the group INVERSE (the Class-C conjugate). The lift is
π-FAITHFUL — ``q8_project_v4(Q8 recall) == klein4 recall`` bit-for-bit (rc311-P2) — so a Q₈ genome IS a
klein4 genome plus the sign bit V4 threw away. The Q₈ ``one`` (:func:`_coupler_q8`) is RESONANT (a declared
function of ``the_one``, never a seed). The klein4 default path is BYTE-UNTOUCHED. Two functions stay
klein4-only (they fail LOUD on Q8, never silently corrupt): :func:`express` and :func:`add_kernel` — their
srmech primitives (``gene_express`` / ``genome_append``) have no ``element_type`` yet (UPSTREAM ask
§Q8-siona, alongside threading ``element_type`` through the klein4-hardwired ``genome``/``partition``).
"""
import json as _json

import srmech.amsc.genome as _G
from srmech.amsc import hdc as _hdc
from srmech.amsc import cascade as _cascade

# §Q8 (srmech rc311): the genome's element_type selector, re-exported so a caller opts in
# without importing genome internals — ``pack_instrument(..., element_type=ELEMENT_TYPE_Q8)``.
# klein4 (V4 = ℤ₂×ℤ₂, sectors=4) is the ABELIAN default — it holds the coset ``q & 3`` but
# DISCARDS the winding sign, and its byte path is UNTOUCHED. Q8 ({±1,±i,±j,±k}, sectors=8) is
# the NON-abelian quaternion lift: it carries the sign bit V4 throws away, RIGHT-couples by the
# group product and recalls by the group INVERSE (the Class-C conjugate).
ELEMENT_TYPE_KLEIN4 = _G.ELEMENT_TYPE_KLEIN4    # 0 — the abelian shadow (default; byte-untouched)
ELEMENT_TYPE_Q8 = _G.ELEMENT_TYPE_Q8            # 1 — the non-abelian quaternion substrate

__all__ = ["pack_instrument", "load_kernel", "load_instrument", "add_kernel", "LEAF_DIM",
           "ELEMENT_TYPE_KLEIN4", "ELEMENT_TYPE_Q8"]

LEAF_DIM = 256          # srmech LEAF_CAP — the tome width each D-vector chunks into
# F1304: the coupler IS the_one winding (documented as such below). klein4 is a CARRIER; its shape comes
# from the_One or from content, NEVER a random seed (user direction 2026-07-22; F1259/F1302). Was
# klein4_random(seed=0) — a DRAWN seed that is not a resonant instrument, and klein4_random is DELETED at rc297.
_ONE = _cascade.the_one(1, 0)   # sigma=1, theta=0 — siona's canonical the_one


def _coupler(leaf_dim=LEAF_DIM):
    """siona's coupling invariant ``the_one`` — a deterministic Klein-4 leaf of width ``leaf_dim``.
    Pack and recall use the same one; it is also stored in the genome manifest on save."""
    return _hdc.klein4_from_one(_ONE, leaf_dim)   # the_one winding, not a seed (F1304)


# ── §Q8 the non-abelian coupler (N3 resolution) ────────────────────────────────────────────
# srmech ships NO public ``q8_from_one`` minter, and the rc311 TEST mints its Q₈ ``one`` from an
# RNG (``_rand_q8_one``) — which is exactly the F1304/F1259 defect for siona (a coupling routed
# through a seed is a misleading `the_one`). So siona CONSTRUCTS a RESONANT sectors=8 Q₈ ``one``
# as a DECLARED FUNCTION of ``the_one``, never a draw:
#
#   low 2 bits (the V4 coset)  = the EXISTING klein4 coupler ``klein4_from_one(_ONE, D)`` verbatim
#                                → ``q8_project_v4(q8_one) == klein4 one`` EXACTLY (the π-faithful
#                                  shadow; the Q₈ coupler IS the klein4 coupler plus a sign channel)
#   high bit   (the sign)      = bit-0 of a SECOND Class-A content-address of ``the_one``, tagged
#                                for an independent "q8-sign" channel — the winding sign V4 discards
#
# This mirrors ``klein4_from_one`` itself (a Class-A ``klein4_address`` of the One's canonical
# serialisation): a coupling slot is a ROLE, not a representation, so a content-address is the
# CORRECT resonant supplier (structurelessness is the target — see the klein4_from_one docstring).
# Both channels are declared functions of (σ, θ, terms, winding); there is no seed anywhere.
def _q8_sign_preimage():
    """The Class-A preimage of the Q₈ SIGN channel — a canonical serialisation of ``the_one``'s
    constructor integers with a ``"q8-sign"`` domain tag so the sign bit is an INDEPENDENT
    resonant channel from the coset (it carries genuinely new information — a lone sign flip is
    invisible to V4). A declared function of ``the_one``; never a seed (F1304/F1259)."""
    return _json.dumps(
        {"channel": "q8-sign", "sigma": int(_ONE.sigma),
         "theta": [int(_ONE.theta[0]), int(_ONE.theta[1])],
         "terms": int(_ONE.terms), "winding": [int(w) for w in _ONE.winding]},
        sort_keys=True, separators=(",", ":")).encode("utf-8")


def _coupler_q8(leaf_dim=LEAF_DIM):
    """siona's NON-abelian Q₈ coupling invariant — a deterministic sectors=8 leaf of width
    ``leaf_dim``, RESONANT (derived from ``the_one``, never an RNG). Its V4 shadow IS the klein4
    coupler (``q8_project_v4(_coupler_q8(D)) == _coupler(D)``) and its sign channel is a resonant
    Class-A lift of the winding sign klein4 discards. Class-C ∘ Class-A."""
    coset = _coupler(leaf_dim)                                    # sectors=4 {0..3} — the π shadow
    sign_src = _hdc.klein4_address(leaf_dim, _q8_sign_preimage())  # sectors=4 Class-A sign channel
    q8_bytes = bytes(((int(s) & 1) << 2) | int(c)                # sign<<2 | coset  → Q₈ byte {0..7}
                     for c, s in zip(coset, sign_src))
    return _hdc.HV.from_sequence(q8_bytes, sectors=_G.OCT)


def _coupler_for(element_type=ELEMENT_TYPE_KLEIN4, leaf_dim=LEAF_DIM):
    """Pick the coupling ``one`` for ``element_type`` — the klein4 default is byte-untouched."""
    if element_type == ELEMENT_TYPE_Q8:
        return _coupler_q8(leaf_dim)
    return _coupler(leaf_dim)


def _q8_chromosomes(kernels, one):
    """Build a multi-kernel Q₈ strand by concatenating one CHROM-capped, Q₈-right-coupled
    :func:`chromosome` per label (the high-level ``genome()`` is klein4-hardwired — UPSTREAM ask
    §Q8-siona: thread ``element_type`` through ``genome``/``partition``). ``kernels`` is an ordered
    ``{label: leaves}``; the CHROM caps make the strand self-describing for :func:`_q8_partition`."""
    strand = []
    for label, leaves in kernels.items():
        strand.extend(_G.chromosome(leaves, one, label=label, element_type=ELEMENT_TYPE_Q8))
    return strand


def _q8_partition(strand, one, labels=None):
    """Recover ``{label: leaves}`` from a multi-kernel Q₈ strand — the Q₈ peer of the klein4
    :func:`partition` (which raises on Q₈ bytes 4..7 rather than corrupt silently). Splits the
    self-describing strand by CHROM cap (:func:`_split_into_chromosomes`) and Q₈-uncouples each
    segment with the public :func:`recall` (``element_type=Q8`` — the group-inverse decouple,
    native-accelerated). ``labels`` filters+orders the result, matching ``partition``."""
    out = {label: _G.recall(seg, one, element_type=ELEMENT_TYPE_Q8)
           for label, seg in _G._split_into_chromosomes(strand)}
    if labels is not None:
        return {label: out[label] for label in labels if label in out}
    return out


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


def pack_instrument(named_vectors, path, *, leaf_dim=LEAF_DIM, the_one=None,
                    element_type=ELEMENT_TYPE_KLEIN4):
    """Pack an iterable of ``(label, HV)`` into ONE native genome directory at ``path`` (#249).

    Each HV is chunked into aligned leaves and becomes one chromosome of a native strand.
    Returns the srmech manifest ``dict``. Duplicate labels raise upstream; a non-aligned D raises here.

    ``element_type`` selects the coupling substrate (§Q8 / rc311). The default ``ELEMENT_TYPE_KLEIN4``
    is the shipped abelian path — BYTE-UNTOUCHED (``genome()`` + ``genome_save``). ``ELEMENT_TYPE_Q8``
    right-couples each turn through the resonant Q₈ ``one`` (:func:`_coupler_q8`) and stores the 3-bit
    turns on disk via the v16 Q₈ packer (``genome_save(element_type=Q8)``). The HVs must be
    ``sectors=8`` (bytes ``0..7``) for Q8; klein4 content lifts to Q8 by embedding (sign bit 0).
    """
    one = _coupler_for(element_type, leaf_dim) if the_one is None else the_one
    kernels, labels = {}, []
    for label, hv in named_vectors:
        kernels[label] = _leaves(hv, leaf_dim)
        labels.append(label)
    if element_type == ELEMENT_TYPE_KLEIN4:
        strand = _G.genome(kernels, one)
        return _G.genome_save(strand, str(path), one, labels)
    strand = _q8_chromosomes(kernels, one)
    return _G.genome_save(strand, str(path), one, labels, element_type=element_type)


def load_instrument(path, *, the_one=None, element_type=ELEMENT_TYPE_KLEIN4):
    """Recall EVERY kernel — ``{label: flat list}`` — byte-exact via ``genome_load`` + ``partition`` (#249).

    ``element_type`` MUST match the type the genome was packed with. klein4 (default) uses the shipped
    :func:`partition` (UNCHANGED). Q8 uses :func:`_q8_partition` (the group-inverse decouple) — the
    klein4 ``partition`` cannot read Q8 (it raises on bytes 4..7 rather than corrupt silently)."""
    strand, one, labels = _G.genome_load(str(path))
    if element_type == ELEMENT_TYPE_KLEIN4:
        parts = _G.partition(strand, one, labels)
    else:
        parts = _q8_partition(strand, one, labels)
    return {label: _flatten(leaves) for label, leaves in parts.items()}


def load_kernel(path, label, *, the_one=None, element_type=ELEMENT_TYPE_KLEIN4):
    """Recall ONE kernel by label — the exact flat ``list[int]`` (#249). The ``labels`` filter pages
    just this chromosome (the demand-load path — F1094: RAM tracks the expressed subset, not disk).
    ``element_type`` selects the decouple substrate; klein4 (default) is the shipped path UNCHANGED."""
    strand, one, _labels = _G.genome_load(str(path))
    if element_type == ELEMENT_TYPE_KLEIN4:
        parts = _G.partition(strand, one, [label])
    else:
        parts = _q8_partition(strand, one, [label])
    return _flatten(parts[label])


def build_genome(named_genes, *, leaf_dim=LEAF_DIM, the_one=None, label="genome",
                 element_type=ELEMENT_TYPE_KLEIN4):
    """Build a REGULATORY genome — the ALL-POSSIBLE-information object (F1095). Each ``gene`` is
    ``(label, hv)`` (always expressed), ``(label, hv, activator_mask)``, or ``(label, hv, activator, repressor)``
    — the activator/repressor masks are the epigenetic gates (Class-I bit conditions). Returns ``(strand, the_one)``;
    the strand is a multi-gene chromosome. The genome is NOT the story — :func:`express` reads a story/context OUT
    of it per ``cell_state`` (SAME genome, DIFFERENT cell_state → DIFFERENT expressed subset).

    ``element_type`` selects the coupling substrate; the klein4 default is byte-untouched. Q8 threads
    ``element_type`` into :func:`chromosome`'s genes-form (each turn Q₈-right-coupled). NOTE: the
    epigenetic gate MASKS are Class-I klein4 sector conditions — orthogonal to the content
    ``element_type`` — and reading a Q8 genome back is via :func:`express` (klein4-gated only; the Q8
    read-back gap is UPSTREAM ask §Q8-siona: gene_express has no ``element_type``)."""
    one = _coupler_for(element_type, leaf_dim) if the_one is None else the_one
    genes = [((g[0], _leaves(g[1], leaf_dim)) + tuple(g[2:])) for g in named_genes]
    if element_type == ELEMENT_TYPE_KLEIN4:
        return _G.chromosome(genes=genes, coupling=one, label=label), one
    return _G.chromosome(genes=genes, coupling=one, label=label, element_type=element_type), one


def express(strand, cell_state, *, the_one, element_type=ELEMENT_TYPE_KLEIN4):
    """EXPRESS a story/context from the genome (F1095): ``gene_express`` returns only the genes the epigenetic
    ``cell_state`` gates ON → ``{label: flat kernel}``. This is the op⊗operand theorem (the genome's own
    docstring): SAME genome (all-possible), DIFFERENT ``cell_state`` (epigenetic context) → DIFFERENT expressed
    subset (the STORY, or the active CONTEXT). A pure READ — the genome is never mutated. ``cell_state`` is a
    non-negative int (each bit a present condition; Class-I integers, no float; sign stays Class-K).

    Only ``ELEMENT_TYPE_KLEIN4`` is supported: srmech's ``gene_express`` is klein4-hardwired (no
    ``element_type`` param), so it would klein4-uncouple a Q8 strand — a silent corruption. Q8
    expression is UPSTREAM ask §Q8-siona (``gene_express(element_type=)``); until then Q8 fails LOUD."""
    if element_type != ELEMENT_TYPE_KLEIN4:
        raise NotImplementedError(
            "genome_store.express: element_type=Q8 is not supported — srmech's gene_express is "
            "klein4-hardwired (no element_type param) and would silently klein4-uncouple a Q8 "
            "genome. Q8 gene expression awaits an upstream gene_express(element_type=) (UPSTREAM "
            "ask §Q8-siona). Use pack_instrument/load_instrument for Q8 storage + recall.")
    return {lbl: _flatten(lv) for lbl, lv in _G.gene_express(strand, the_one, cell_state)}


def add_kernel(path, label, hv, *, leaf_dim=LEAF_DIM, the_one=None,
               element_type=ELEMENT_TYPE_KLEIN4):
    """Append ONE newly-taught kernel to an existing genome in **O(1)** (F1044 — the helix tail-extends;
    prior bytes are never re-read). The kernel's ``D`` must be a multiple of ``leaf_dim`` (siona's
    D=8192 = 32×256): the raw leaves append header-less, and ``kernel_unpack`` recovers the exact D via
    its §60 back-compat rule (``D = n_leaves × leaf_dim``, no padding). For a D that is NOT a multiple of
    ``leaf_dim`` the self-describing header is required, and there is no public O(1) kernel-append yet
    (UPSTREAM §89) — rebuild with :func:`pack_instrument` in that case. Recall via :func:`load_kernel`.

    Only ``ELEMENT_TYPE_KLEIN4`` is supported: srmech's ``genome_append`` has no ``element_type``
    param (it would klein4-couple the appended turns), so Q8 O(1)-append is UPSTREAM ask §Q8-siona.
    Until then, rebuild a Q8 genome with :func:`pack_instrument` to add a kernel."""
    if element_type != ELEMENT_TYPE_KLEIN4:
        raise NotImplementedError(
            "genome_store.add_kernel: element_type=Q8 is not supported — srmech's genome_append "
            "has no element_type param and would klein4-couple the appended turns. Q8 O(1)-append "
            "awaits an upstream genome_append(element_type=) (UPSTREAM ask §Q8-siona); rebuild the "
            "Q8 genome with pack_instrument to add a kernel.")
    one = _coupler(leaf_dim) if the_one is None else the_one
    flat = list(hv)
    if len(flat) % leaf_dim:
        raise ValueError(
            "add_kernel: D=%d is not a multiple of leaf_dim=%d — O(1) header-less append needs an "
            "aligned D; use pack_instrument (or await the upstream kernel-append, §89)." % (len(flat), leaf_dim))
    leaves = [flat[i:i + leaf_dim] for i in range(0, len(flat), leaf_dim)]
    return _G.genome_append(str(path), label, leaves, one)
