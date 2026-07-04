"""siona.genome_store — pack siona's Klein-4 instrument into a native srmech genome (PKG-3).

Replaces the loose NDJSON+title-index instrument with a single native srmech genome. Each named body
(a tool vector, a stored-kernel article, an F1035 kernel) is a flat **Klein-4 hypervector** of ANY
dimension — siona's is D=8192, ``element_type="klein4"`` → the *identity* codec (F1043 option 2:
siona's kernel IS the 2-bit ``{0,1,2,3}`` symbol, so no element transcoding).

The scaffolding rides srmech's §60 ``kernel_pack``/``kernel_unpack`` (rc123+, the dim-agnostic layer):

  * ``kernel_pack`` chunks each D-vector into ``leaf_dim``-wide leaves (final zero-padded) + a §60
    header (marker ``0x4B``) that SELF-RECORDS the true ``D``, ``element_type`` and ``leaf_dim``.
  * the per-body strands CONCATENATE into ONE multi-chromosome genome with a title→byte-offset manifest.
  * recall pages one chromosome by label (``genome_window``) and ``kernel_unpack`` self-trims to the
    exact ``D`` — **no external length index needed** (W1 closed upstream), for a mixed-dimension corpus.

This is the corrected sparse store: on disk each symbol is bit-packed to **2 bits** (F1044), so an
N-body instrument costs ≈ ``sum(D_i) / 4`` bytes + caps — NOT the dense blow-up the earlier
genome attempt hit. No numpy; no floats; Klein-4 end to end.
"""
import srmech.amsc.genome as _G
from srmech.amsc import hdc as _hdc

__all__ = ["pack_instrument", "load_kernel", "load_instrument", "LEAF_DIM"]

LEAF_DIM = 256          # srmech LEAF_CAP — the tome width each D-vector chunks into
_COUPLER_SEED = 0       # siona's canonical coupling invariant (deterministic; recorded in the manifest)


def _coupler(leaf_dim=LEAF_DIM):
    """siona's coupling invariant ``the_one`` — a deterministic Klein-4 leaf of width ``leaf_dim``.
    Pack and recall use the same one; it is also stored in the genome manifest on save."""
    return _hdc.klein4_random(leaf_dim, seed=_COUPLER_SEED)


def pack_instrument(named_vectors, path, *, leaf_dim=LEAF_DIM, the_one=None):
    """Pack an iterable of ``(label, klein4_HV)`` into ONE native genome directory at ``path``.

    Each HV is a flat Klein-4 kernel of any dimension. Returns the srmech manifest ``dict``
    (``chromosomes`` / ``body_sha256`` / ``leaf_dim`` / ``the_one`` …). Duplicate labels raise upstream.
    """
    one = _coupler(leaf_dim) if the_one is None else the_one
    items = list(named_vectors)
    flat, labels = [], []
    for label, hv in items:
        flat += _G.kernel_pack(hv, leaf_dim=leaf_dim, label=label, the_one=one, element_type="klein4")
        labels.append(label)
    return _G.genome_save(flat, str(path), one, labels)


def load_kernel(path, label, *, the_one=None):
    """Recall ONE kernel by label — the exact flat Klein-4 ``list[int]``, self-trimmed to its true D."""
    one = _coupler() if the_one is None else the_one
    window = _G.genome_window(str(path), label)
    return list(_G.kernel_unpack(window, one))


def load_instrument(path, *, the_one=None):
    """Recall EVERY kernel — ``{label: flat Klein-4 list}`` — reading labels from the genome manifest."""
    catalog = _G.genome_catalog(str(path))
    out = {}
    for entry in catalog.get("chromosomes", []):
        label = entry["label"] if isinstance(entry, dict) else entry
        out[label] = load_kernel(path, label, the_one=the_one)
    return out


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
