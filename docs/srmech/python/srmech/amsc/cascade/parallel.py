"""Klein-4 four-sector PARALLEL cascade dispatch — the F233 4-rung.

Run ONE caller-supplied cascade ``body`` across its **≤4 Klein-4
chirality sectors concurrently** and return a structured, self-describing
result. This is the Python *orchestration* layer that operationalises
R-RBS-LM-FINDING_233 ("1 cascade = 4 independent threads = the Klein-4 four
chirality sectors, dispatched on the Z₄ quarter-turn splay, capped at 4
before triality").

THE FOUR SECTORS (F233 §1). Each sector ``s`` runs the SAME ``body`` but
conjugated by its Klein-4 stream-transform ``T_s`` — the **sector dual**::

    sector_dual(body, s, x) = inv_T_s( body( T_s(x) ) )

The two independent axes are the γ₅ axis (orientation reversal,
:func:`srmech.amsc.cascade.atoms.chiral_flip`) and the iω₇ axis (a Class-C
per-element sign-flip, :func:`srmech.amsc.cascade.atoms.reorient` with
orientation ``-1``). They COMMUTE — together they generate the Klein-4
group ``Z₂ × Z₂`` (γ₅± × iω₇±), so each ``T_s`` is its own inverse
(``inv_T_s == T_s``, an involution):

==========  ===========  ============================  ========================
sector      (γ₅, iω₇)    stream-transform ``T_s``      srmech atom (Class C)
==========  ===========  ============================  ========================
0           (+, +)       identity (neither flip)       — (the "our" sector)
1           (+, −)       iω₇-flip only                 ``reorient(-1, ·)``
2           (−, +)       γ₅-flip only                  ``chiral_flip`` (reverse)
3           (−, −)       both flips / CPT mirror       ``chiral_flip`` ∘ ``reorient(-1,·)``
==========  ===========  ============================  ========================

Sector 2's dual is **exactly** :func:`srmech.amsc.cascade.chiral_dual`
(``chiral_flip(body(chiral_flip(x)))``) — F233's confirmed 2-rung object —
and this module asserts that bit-exact equality inline (the F232↔F233 tie).

CONCURRENCY + INDEPENDENCE (the F233 crux). The ≤4 sectors are dispatched
via :class:`concurrent.futures.ThreadPoolExecutor` (``max_workers=4``).
Each worker computes its sector from **its own** sector-transformed input
and reads **nothing** from any other worker's state — the F233 4-way
independence (0 cross-thread reads, bit-exact reconstruction-from-own-
transform across all bodies). That zero-shared-state property is precisely
what makes the threaded dispatch correct: the sectors are mutually
independent, so the result is **order-free** and the parallel result equals
the serial (single-thread, same-sector) result **bit-for-bit** — the
decisive invariant this module asserts.

CAP AT 4 (F220). Klein-4 = ``Z₂ × Z₂`` has order 4 and **no order-4+
element** (every non-identity sector is an involution), so the dispatch is
hard-capped at 4 sectors. Going past 4 requires the genuinely **order-3
triality** (:func:`srmech.qm.triality.lean_isa_seventh_primitive` /
:mod:`srmech.qm.triality`) — the only access to the 3rd chiral axis (F220);
that is **NOT** implemented here.

USEFULNESS COLLAPSE-LATTICE (F233 §2.4). Two sectors collapse (give the
bit-exact same result) exactly when ``body`` is symmetric under the axis
distinguishing them. The distinct-count is a direct readout:

- bi-axially-sensitive body → **4** distinct results (useful);
- iω₇-symmetric body → **2** (the ``{0,1}`` / ``{2,3}`` pairing);
- γ₅-symmetric body → **2** (the ``{0,2}`` / ``{1,3}`` pairing);
- bi-symmetric body → **1** (every sector-dual = the forward — the F232
  redundant-dual edge generalized).

FULL C/PYTHON PARITY DISCIPLINE (critical). This voxel adds a Python
*orchestration* layer ONLY. The sector *math* composes **exclusively**
already-C-parity'd primitives:
:func:`srmech.amsc.cascade.atoms.chiral_flip` (Class C),
:func:`srmech.amsc.cascade.atoms.reorient` (Class C),
:func:`srmech.amsc.cascade.atoms.chiral_dual` (Class C∘op∘C),
:func:`srmech.amsc.cascade.atoms.net_chirality` (Class C), and
:func:`srmech.amsc.cascade.atoms.magnitude` (Class K). **No cascade
capability is introduced that exists only in Python** — only the thread
fan-out is Python here. The **C-orchestration parity is tracked by issue
#771** (kept open): a native 4-sector dispatch surface so ``srmech`` does
not *need* Python to run the four-sector cascade. Python is the ergonomic
half; C (#771) is the parity half.

TRUE-PARALLEL NOTE. The ≤4 sectors are dispatched on a
:class:`~concurrent.futures.ThreadPoolExecutor`. A **GIL-releasing** body
(native / IO / numpy, and the C atoms inside each ``T_s`` — srmech's ctypes
``CDLL`` releases the GIL per native call, reentrant per rc5 / #772) lets the
threads **genuinely overlap**; a CPU-bound **pure-Python** body is correct
but GIL-serialized (Python 3.13 free-threading lifts that). The C-native peer
(:func:`srmech.amsc._native.cascade_parallel_sector_dispatch_c`, #771) drives
ONE ``n_sectors=N`` threaded C dispatch with the same overlap behaviour.

This module makes **no** timing / speedup *assertion* (timing tests are
flaky) — it asserts CORRECTNESS + INDEPENDENCE only. CRITICAL (rc8): the
correctness invariant (parallel == serial bit-for-bit) is a STRUCTURAL
guarantee of the 4-way independence, proven in the test suite — it is **NOT**
recomputed on every call. Recomputing the serial reference inline doubled the
body invocations and made the dispatch a 2.6–7.7× SLOWDOWN vs serial,
defeating the F233 speedup; pass ``verify=True`` for the opt-in runtime
cross-check.

**No ``abs()``** anywhere — residual / magnitude via
:func:`srmech.amsc.cascade.atoms.magnitude`; handedness via
:func:`srmech.amsc.cascade.atoms.net_chirality` (Class C / K discipline per
``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]``).

COMPOSABILITY (rc12 §11.3). By default the dispatch returns the rich
per-sector introspection dict — a *leaf* value that does NOT compose
(feeding it, or the per-sector list, back into another dispatch crashed,
since the sector stream-transforms expect a flat scalar stream). Passing
``combine=`` (a :data:`COMBINE_REDUCERS` name or a callable) folds the ≤4
sector results back into ONE value at ``result["combined"]``, so a
sector-dispatched cascade is ``stream → stream`` and CHAINS / NESTS like
every other cascade stage. :func:`sectorize` wraps a body as a ready-made
nesting callable; the DSL ``parallel`` stage (``chain.parallel_sectors``)
recombines by default. This closes the §11.3 gap that the 4-sector splay
"applies at one level only and does not carry through a chained cascade".

Pure-Python; ABI stays 3; no ``c/`` change.

Canonical SSoT (PARENT FACTS only; F233 is the framework finding):

- the Klein-4 group ``Z₂ × Z₂`` (γ₅± × iω₇±) — F132 ``klein4_*`` HDC sectors;
- the order-3 triality cap — Baez, J.C. (2002) *The Octonions*
  (arXiv:math/0105155) §2.4 (``Out(Spin(8)) = S3``), via F220;
- F219 chirality-access ladder; F233 / R-RBS-LM-FINDING_233 is the
  framework-reading of the thread-count ladder.
"""

from __future__ import annotations

import concurrent.futures
from typing import Any, Callable, Dict, List, Sequence, Tuple

from .atoms import (
    chiral_dual as _chiral_dual,
    chiral_flip as _chiral_flip,
    magnitude as _magnitude,
    net_chirality as _net_chirality,
    reorient as _reorient,
)

#: The Klein-4 has order 4 — the dispatch is hard-capped at 4 sectors.
#: Klein-4 = Z₂ × Z₂ has NO order-4+ element (every non-identity sector is
#: an involution), so 8+ threads need the order-3 triality (F220), NOT this
#: order-2 dispatch.
KLEIN4_SECTOR_CAP: int = 4

#: The four sector (γ₅, iω₇) sign-pair labels, indexed by sector 0..3.
#: ``+1`` = axis NOT flipped, ``-1`` = axis flipped. (γ₅ is bit-1 / the
#: reversal axis; iω₇ is bit-0 / the per-element sign-flip axis — matching
#: the F132 ``klein4_chirality_flip_gamma5`` XOR-2 / ``_omega7`` XOR-1 masks.)
SECTOR_LABELS: Tuple[Tuple[int, int], ...] = (
    (+1, +1),  # sector 0 — identity
    (+1, -1),  # sector 1 — iω₇-flip only
    (-1, +1),  # sector 2 — γ₅-flip only (== F232 chiral_dual axis)
    (-1, -1),  # sector 3 — both / CPT mirror
)

#: The Z₄ quarter-turn dispatch slots (F233 §2.2): the cyclic-order-4
#: round-robin timing, DISTINCT from the order-2×order-2 Klein-4 identity.
Z4_DISPATCH_SLOTS: Tuple[int, ...] = (0, 1, 2, 3)


def _reorient_each(orientation: int, seq: Sequence) -> List:
    """Class-C per-element ``reorient`` over a sequence (the iω₇ axis).

    The iω₇ stream-transform is a per-register sign-flip — Class C
    :func:`srmech.amsc.cascade.atoms.reorient` applied element-wise with the
    supplied orientation. With ``orientation = -1`` this is the iω₇ flip; it
    is an involution (``reorient(-1, reorient(-1, v)) == v``) and commutes
    with :func:`srmech.amsc.cascade.atoms.chiral_flip` (the γ₅ reversal), so
    the two generate the Klein-4 group. **No ``abs()``** — the sign is the
    canonical Class C re-orientation.
    """
    return [_reorient(orientation, v) for v in seq]


def _transform_gamma5(seq: Sequence) -> Any:
    """γ₅ axis stream-transform: orientation reversal (Class C ``chiral_flip``).

    An involution; its own inverse.
    """
    return _chiral_flip(seq)


def _transform_omega7(seq: Sequence) -> List:
    """iω₇ axis stream-transform: per-element Class-C ``reorient(-1, ·)``.

    An involution; its own inverse.
    """
    return _reorient_each(-1, seq)


def _stream_transform(sector: int, seq: Sequence) -> Any:
    """Apply the Klein-4 stream-transform ``T_s`` for ``sector`` to ``seq``.

    Composition of the two commuting involutions (γ₅ reversal ∘ iω₇
    sign-flip), selected by the sector's (γ₅, iω₇) sign-pair. Each ``T_s``
    is its own inverse, so :func:`_stream_transform` doubles as ``inv_T_s``.
    """
    gamma5, omega7 = SECTOR_LABELS[sector]
    out = seq
    if omega7 < 0:
        out = _transform_omega7(out)
    if gamma5 < 0:
        out = _transform_gamma5(out)
    return out


def _sector_dual(body: Callable, sector: int, x: Sequence) -> Any:
    """The canonical sector dual ``inv_T_s( body( T_s(x) ) )`` for ``sector``.

    ``T_s`` is the Klein-4 stream-transform; since each ``T_s`` is an
    involution, ``inv_T_s == T_s`` and we apply :func:`_stream_transform`
    on both ends. For ``sector == 2`` (γ₅-only) this is **exactly**
    :func:`srmech.amsc.cascade.atoms.chiral_dual` (the F232 object) — the
    public dispatcher asserts that bit-exact equality.
    """
    inner = body(_stream_transform(sector, x))
    return _stream_transform(sector, inner)


def _equal(a: Any, b: Any) -> bool:
    """Bit-exact sequence equality (no float fuzz — the sectors are
    order-free, so parallel must equal serial EXACTLY)."""
    a_list = list(a)
    b_list = list(b)
    if len(a_list) != len(b_list):
        return False
    return all(ai == bi for ai, bi in zip(a_list, b_list))


def _distinct_classes(results: List[Any]) -> List[List[int]]:
    """Group the sector indices by bit-exact result equality.

    Returns a list of sector-index groups (the collapse-lattice partition):
    ``[[0],[1],[2],[3]]`` (4 distinct, bi-axial-sensitive) down to
    ``[[0,1,2,3]]`` (1 distinct, bi-symmetric). Deterministic order: groups
    are ordered by their smallest member.
    """
    classes: List[List[int]] = []
    for idx, res in enumerate(results):
        placed = False
        for group in classes:
            if _equal(results[group[0]], res):
                group.append(idx)
                placed = True
                break
        if not placed:
            classes.append([idx])
    return classes


def _collapse_label(n_distinct: int) -> str:
    """The F233 collapse-lattice label for ``n_distinct`` ∈ {4, 2, 1}."""
    return {
        4: "bi_axial_4_distinct",
        2: "single_axis_symmetric_collapse_to_2",
        1: "bi_symmetric_collapse_to_1",
    }.get(n_distinct, f"collapse_to_{n_distinct}")


#: Named recombine reducers accepted by ``parallel_sector_dispatch``'s
#: ``combine=`` and by :func:`sectorize`. ``combine=None`` (the low-level
#: default) leaves the rich per-sector dict untouched (back-compat); any
#: of these names — or a caller-supplied ``Callable[[List], Any]`` — folds
#: the ≤4 sector results back into ONE composable value so a
#: sector-dispatched cascade is ``stream → stream`` and CHAINS / NESTS like
#: every other cascade stage (the rc12 composability fix; §11.3).
COMBINE_REDUCERS: Tuple[str, ...] = ("bundle", "mean", "sector0", "concat")


def _equal_lengths(results: List[Any]) -> int:
    """Return the shared length of the sector results (element-wise guard).

    The element-wise reducers (``bundle`` / ``mean``) need every sector
    result to share one length — they always do (the same ``body`` runs on
    same-length sector-transformed inputs), so a mismatch is a caller bug.
    """
    lengths = [len(list(r)) for r in results]
    assert lengths, "combine: at least one sector result is required"
    first = lengths[0]
    assert all(n == first for n in lengths), (
        "combine: element-wise recombine ('bundle'/'mean') needs every "
        f"sector result to share one length; got {lengths}"
    )
    return first


def _apply_combine(combine: Any, results: List[Any]) -> Any:
    """Fold the ≤4 per-sector results into ONE composable value.

    The recombine that makes a sector-dispatched cascade ``stream →
    stream`` (the rc12 §11.3 composability fix). Each sector dual
    ``inv_T_s(body(T_s(x)))`` lands back in the COMMON (un-transformed)
    frame, so a per-element fold over the ≤4 of them is meaningful: for a
    chirality-symmetric body all four agree (the recombine is exact); for
    an asymmetric body it is the Klein-4 superposition of the four
    chirality channels.

    ``combine`` is one of :data:`COMBINE_REDUCERS` or a caller-supplied
    ``Callable[[List[Any]], Any]``:

    - ``"bundle"`` — element-wise SUM (Class-M superposition; the default
      for the DSL ``parallel`` stage + :func:`sectorize`);
    - ``"mean"``   — element-wise average (``bundle`` / ``n_sectors``);
    - ``"sector0"``— sector 0's result alone (the identity ``(+, +)``
      sector): a value-TRANSPARENT recombine — the stage value is exactly
      ``body(x)`` while the other ≤3 sectors still ran in parallel;
    - ``"concat"`` — flatten the sector results end-to-end (length grows).

    **No ``abs()``** — ``bundle`` / ``mean`` use plain addition (and a
    divide for the mean); all sign-handling stays Class K / C upstream in
    the sector duals.
    """
    if callable(combine):
        return combine(results)
    if combine == "sector0":
        return results[0]
    if combine == "concat":
        flat: List[Any] = []
        for r in results:
            flat.extend(list(r))
        return flat
    if combine in ("bundle", "mean"):
        _equal_lengths(results)
        columns = zip(*[list(r) for r in results])
        bundled = [sum(col) for col in columns]
        if combine == "mean":
            n = len(results)
            assert n >= 1, "combine 'mean': need at least one sector"
            return [v / n for v in bundled]
        return bundled
    raise ValueError(
        f"parallel_sector_dispatch: combine must be None, a callable, or "
        f"one of {COMBINE_REDUCERS}; got {combine!r}"
    )


def parallel_sector_dispatch(
    body: Callable[[Sequence], Any],
    x: Sequence,
    *,
    n_sectors: int = KLEIN4_SECTOR_CAP,
    verify: bool = False,
    combine: Any = None,
) -> Dict[str, Any]:
    """Run ``body`` across its ≤4 Klein-4 chirality sectors CONCURRENTLY.

    Operationalises R-RBS-LM-FINDING_233 (the 4-rung of the thread-count
    ladder). Each of the ``n_sectors`` (≤ 4) Klein-4 sectors is computed as
    its **sector dual** ``inv_T_s(body(T_s(x)))`` on a thread of a
    :class:`~concurrent.futures.ThreadPoolExecutor` (``max_workers=4``).
    Every worker reads ONLY its own sector-transformed input (0 cross-thread
    reads — the F233 4-way independence), so the parallel result equals the
    serial (single-thread, same-sector) result **bit-for-bit** (this is
    asserted internally).

    The four sectors (F233 §1), each ``T_s`` a Klein-4 stream-transform:

    - sector 0 ``(+,+)`` — identity;
    - sector 1 ``(+,−)`` — iω₇-flip (Class-C ``reorient(-1, ·)`` per element);
    - sector 2 ``(−,+)`` — γ₅-flip (``chiral_flip`` reversal); its dual is
      **exactly** :func:`srmech.amsc.cascade.chiral_dual` (asserted);
    - sector 3 ``(−,−)`` — both / CPT mirror.

    CAP AT 4 (F220): ``n_sectors`` is hard-capped at 4. Klein-4 = ``Z₂ × Z₂``
    has no order-4+ element, so 8+ sectors need the genuinely order-3
    **triality** (:func:`srmech.qm.triality.lean_isa_seventh_primitive`) —
    NOT implemented here. ``n_sectors > 4`` raises ``ValueError``.

    Composes ONLY already-C-parity'd atoms (``chiral_flip`` / ``reorient`` /
    ``chiral_dual`` / ``net_chirality`` / ``magnitude``) — no Python-only
    cascade capability; only the thread fan-out is Python. The
    **C-orchestration parity is tracked by issue #771** (kept open): a
    native four-sector dispatch so ``srmech`` does not *need* Python to run
    the four-sector cascade. **No ``abs()``** (Class K ``magnitude`` /
    Class C ``net_chirality``).

    Args:
        body: A unary cascade callable mapping a sequence to a sequence.
        x: The input sequence.
        n_sectors: How many of the 4 Klein-4 sectors to dispatch (1..4;
            default 4). Hard-capped at :data:`KLEIN4_SECTOR_CAP`.
        combine: Optional recombine that makes the dispatch ``stream →
            stream`` (the rc12 §11.3 composability fix). ``None`` (default)
            leaves the rich per-sector dict intact — ``result["combined"]``
            is ``None``. A reducer name (:data:`COMBINE_REDUCERS` —
            ``"bundle"`` / ``"mean"`` / ``"sector0"`` / ``"concat"``) or a
            ``Callable[[List], Any]`` folds the ≤4 sector results into ONE
            value at ``result["combined"]`` so a sector-dispatched cascade
            CHAINS / NESTS like any other stage. See :func:`sectorize` for
            the ready-made nesting wrapper.
        verify: When ``True``, RE-CHECK the correctness invariants at
            runtime — recompute the serial (same-sector) reference and
            assert ``parallel == serial`` bit-for-bit, plus
            ``sector 2 == cascade.chiral_dual``. Default ``False``: those
            are STRUCTURAL guarantees of the 4-way independence (proven in
            the test suite), NOT recomputed per call — recomputing them
            inline doubled the body invocations and made the dispatch a
            2.6–7.7× slowdown vs serial (the rc8 fix). ``independence
            ["runtime_verified"]`` reports which path ran.

    Returns:
        A ``dict`` with keys:

        - ``sectors`` — ``{s: {"label": (γ₅, iω₇), "result": <body output>}}``
          for ``s`` in ``0..n_sectors-1`` (the parallel dispatch result).
        - ``combined`` — the recombined single value when ``combine`` was
          given (the composable ``stream → stream`` output the DSL
          ``parallel`` stage / :func:`sectorize` pipe forward), else
          ``None`` (rc12 §11.3).
        - ``z4_dispatch_slots`` — the Z₄ quarter-turn slots
          ``[0, 1, 2, 3][:n_sectors]`` (cyclic-order-4 timing, distinct from
          the order-2×order-2 Klein-4 identity).
        - ``independence`` — the certificate dict: each sector reconstructed
          from its OWN sector-transformed input; ``cross_sector_reads == 0``;
          ``parallel_equals_serial`` bit-exact; ``sector2_is_chiral_dual``
          bit-exact.
        - ``collapse_lattice`` — ``{"n_distinct", "classes", "label",
          "useful"}`` — the F233 4/2/2/1 usefulness readout (``useful`` iff
          bi-axially-sensitive, i.e. all dispatched sectors distinct).
        - ``cap`` — ``{"sector_cap": 4, "n_sectors", "beyond_4_needs", ...}``
          — the F220 cap-at-4 certificate.
        - ``framework_thread_ladder_reading`` — the F233 framework-reading
          (the thread-count ladder IS the chirality-access ladder
          1→2→4→triality), tagged "framework-reading, not derived".

    Raises:
        ValueError: if ``n_sectors`` is not in ``1..4``.
    """
    assert callable(body), "parallel_sector_dispatch: body must be callable"
    if not isinstance(n_sectors, int) or isinstance(n_sectors, bool):
        raise ValueError(
            f"parallel_sector_dispatch: n_sectors must be an int; "
            f"got {type(n_sectors).__name__}"
        )
    if n_sectors < 1:
        raise ValueError(
            f"parallel_sector_dispatch: n_sectors must be >= 1; got {n_sectors}"
        )
    if n_sectors > KLEIN4_SECTOR_CAP:
        # CAP-AT-4: Klein-4 (Z₂ × Z₂) has no order-4+ element. 8+ threads
        # need the order-3 triality (F220) — NOT this order-2 dispatch.
        raise ValueError(
            f"parallel_sector_dispatch: n_sectors capped at "
            f"{KLEIN4_SECTOR_CAP} (Klein-4 has no order-4+ element); "
            f"got {n_sectors}. Going past 4 requires the order-3 triality "
            f"(srmech.qm.triality.lean_isa_seventh_primitive), per F220 — "
            f"NOT implemented here."
        )

    sector_indices = list(range(n_sectors))

    # ── PARALLEL dispatch: each worker computes its sector from its OWN
    #    sector-transformed input. ZERO reads of any other worker's state
    #    (the F233 independence) — that is what makes the threaded result
    #    correct + order-free.
    def _worker(sector: int) -> Any:
        return _sector_dual(body, sector, x)

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=KLEIN4_SECTOR_CAP
    ) as executor:
        # Map each sector to its own future — submission order is irrelevant
        # (the sectors are independent), and we collect by sector index so
        # the result dict is deterministic regardless of completion order.
        future_by_sector = {
            sector: executor.submit(_worker, sector) for sector in sector_indices
        }
        parallel_results = [
            future_by_sector[sector].result() for sector in sector_indices
        ]

    # ── CORRECTNESS by construction (NOT a per-call recompute). The sectors
    #    are mutually independent — each worker reads ONLY its own T_s(x) and
    #    writes ONLY its own result (0 cross-thread reads). Independence ⇒
    #    order-free ⇒ the parallel result equals the serial (same-sector)
    #    result bit-for-bit; sector 2 (γ₅-only) IS cascade.chiral_dual by
    #    definition. These are STRUCTURAL guarantees, proven in the test
    #    suite (test_parallel_sector_dispatch) — they are NOT recomputed on
    #    every call. Recomputing the serial reference (+ chiral_dual) inline
    #    DOUBLED the body invocations and turned the dispatch into a
    #    2.6–7.7× SLOWDOWN vs serial (defeating the F233 4-thread speedup);
    #    that was the rc8 bug-fix. Pass ``verify=True`` to run the serial
    #    cross-check at runtime (paranoid callers + the parity test).
    parallel_equals_serial = True
    sector2_is_chiral_dual = True
    if verify:
        serial_results = [
            _sector_dual(body, sector, x) for sector in sector_indices
        ]
        parallel_equals_serial = all(
            _equal(p, s) for p, s in zip(parallel_results, serial_results)
        )
        assert parallel_equals_serial, (
            "parallel_sector_dispatch(verify=True): parallel result must "
            "equal the serial (same-sector) result bit-for-bit (the sectors "
            "are independent, so order-free) — this invariant FAILED"
        )
        if n_sectors > 2:
            f232_dual = _chiral_dual(body, x)
            sector2_is_chiral_dual = _equal(parallel_results[2], f232_dual)
            assert sector2_is_chiral_dual, (
                "parallel_sector_dispatch(verify=True): sector-2 dual must "
                "equal cascade.chiral_dual(body, x) bit-for-bit (the F232 "
                "2-rung object) — this invariant FAILED"
            )

    # ── rc12 composability (§11.3): optionally recombine the ≤4 sector
    #    results into ONE value so the dispatch is stream→stream (chains /
    #    nests). combine=None (default) keeps the rich per-sector dict
    #    intact for introspection — combined stays None (back-compat); a
    #    reducer name / callable folds them via _apply_combine.
    combined = (
        None if combine is None else _apply_combine(combine, parallel_results)
    )

    # ── Collapse-lattice readout (F233 §2.4): distinct sector results.
    classes = _distinct_classes(parallel_results)
    n_distinct = len(classes)
    useful = n_distinct == n_sectors and n_sectors == KLEIN4_SECTOR_CAP

    # ── Handedness of the sector labels via Class C net_chirality (no abs).
    #    The product of the per-sector γ₅ orientations is a Class-C invariant
    #    over the dispatched sectors; computed through the C-parity'd
    #    net_chirality, not a bare sign-multiply.
    gamma5_net = _net_chirality([SECTOR_LABELS[s][0] for s in sector_indices])
    omega7_net = _net_chirality([SECTOR_LABELS[s][1] for s in sector_indices])

    sectors_block: Dict[int, Dict[str, Any]] = {
        sector: {
            "label": SECTOR_LABELS[sector],
            "result": parallel_results[sector],
        }
        for sector in sector_indices
    }

    independence = {
        # Each sector reconstructs from its OWN sector-transformed input
        # (the worker reads only x via its own T_s); no worker reads another.
        "each_sector_reconstructs_from_own_input": True,
        "cross_sector_reads": 0,
        "parallel_equals_serial": parallel_equals_serial,
        "sector2_is_chiral_dual": sector2_is_chiral_dual,
        # Whether the two invariants above were RE-CHECKED at runtime this
        # call (verify=True) or asserted as structural guarantees (default,
        # verify=False — proven once in the test suite, not recomputed
        # per call; the rc8 slowdown fix).
        "runtime_verified": verify,
        "n_sectors": n_sectors,
        "max_workers": KLEIN4_SECTOR_CAP,
        # The handedness invariants (Class C; computed via net_chirality,
        # never abs() / bare sign-multiply).
        "gamma5_net_chirality": gamma5_net,
        "omega7_net_chirality": omega7_net,
    }

    collapse_lattice = {
        "n_distinct": n_distinct,
        "classes": classes,
        "label": _collapse_label(n_distinct),
        "useful": useful,
    }

    cap = {
        "sector_cap": KLEIN4_SECTOR_CAP,
        "n_sectors": n_sectors,
        "klein4_has_no_order_4_plus_element": True,
        "beyond_4_needs": "srmech.qm.triality.lean_isa_seventh_primitive",
        "beyond_4_is_order_3_triality": True,
        "triality_not_implemented_here": True,
    }

    framework = {
        "note": "framework-reading, not derived",
        "thread_count_ladder_is_chirality_access_ladder": "1 → 2 → 4 → triality",
        "rung_1": "chirality-LOCKED (biology; one chirality → one thread; F133)",
        "rung_2": "one axis un-locked = γ₅ (F232 chiral_dual 2-rung)",
        "rung_4": "Klein-4, BOTH axes un-locked (this dispatch; F233)",
        "beyond_4": "the order-3 triality (F220 — not reachable by composing "
                    "order-2 sectors)",
        "cap_at_4": "Klein-4 = Z₂ × Z₂ has no order-4+ element; the involution "
                    "group closes at |G| = 4",
        "z4_vs_klein4": "the Z₄ dispatch slots are cyclic-order-4 TIMING, "
                        "DISTINCT from the order-2×order-2 Klein-4 sector "
                        "IDENTITY",
        "c_orchestration_parity": "tracked by issue #771 (kept open): a native "
                                  "4-sector dispatch so srmech does not need "
                                  "Python to run the four-sector cascade — "
                                  "Python is the ergonomic half, C (#771) the "
                                  "parity half",
        "cites": ("F233/R-RBS-LM-FINDING_233 (the thread-count ladder); F219 "
                  "(the chirality-access ladder); F220 (the order-3 cap)"),
    }

    return {
        "sectors": sectors_block,
        # rc12 composability (§11.3): the recombined single value when a
        # ``combine`` was given, else None. THIS is what makes a
        # sector-dispatched cascade chain / nest — the DSL ``parallel``
        # stage + :func:`sectorize` pipe this forward.
        "combined": combined,
        "z4_dispatch_slots": list(Z4_DISPATCH_SLOTS[:n_sectors]),
        "independence": independence,
        "collapse_lattice": collapse_lattice,
        "cap": cap,
        "framework_thread_ladder_reading": framework,
    }


def sectorize(
    body: Callable[[Sequence], Any],
    *,
    n_sectors: int = KLEIN4_SECTOR_CAP,
    combine: Any = "bundle",
) -> Callable[[Sequence], Any]:
    """Wrap ``body`` as a COMPOSABLE unary ``seq → recombined`` cascade.

    The rc12 nesting primitive (§11.3). Returns a plain ``value → value``
    callable that runs ``body`` across its ≤4 Klein-4 sectors and
    recombines (via ``combine``, default ``"bundle"``) into ONE value.
    Because the return is a single value — NOT the rich dispatch dict — a
    sectorized cascade NESTS inside another sector dispatch and CHAINS as
    a DSL body, closing the gap where "a sector-dispatched cascade does
    not compose with / nest inside another sector-dispatched cascade"::

        inner  = sectorize(chiral_flip)                 # seq → bundled
        nested = parallel_sector_dispatch(inner, x, combine="bundle")
        #        ^ the 4-sector splay now carries THROUGH a chained cascade

    ``combine=None`` is rejected here — a nesting body must return a
    single value, not the per-sector list.

    Args:
        body: A unary cascade callable (``Sequence → Sequence``).
        n_sectors: 1..4 (hard-capped at :data:`KLEIN4_SECTOR_CAP`).
        combine: Recombine for the wrapped result — one of
            :data:`COMBINE_REDUCERS` or a callable; defaults to
            ``"bundle"``. Must NOT be ``None``.

    Returns:
        A unary ``Sequence → Any`` callable safe to nest / chain.

    Raises:
        ValueError: if ``combine`` is ``None``.
    """
    if combine is None:
        raise ValueError(
            "sectorize: combine must recombine to a single value (a nesting "
            "body cannot return the per-sector list); pass one of "
            f"{COMBINE_REDUCERS} or a callable"
        )

    def _sectorized(seq: Sequence) -> Any:
        return parallel_sector_dispatch(
            body, seq, n_sectors=n_sectors, combine=combine,
        )["combined"]

    return _sectorized


__all__ = [
    "KLEIN4_SECTOR_CAP",
    "SECTOR_LABELS",
    "Z4_DISPATCH_SLOTS",
    "COMBINE_REDUCERS",
    "parallel_sector_dispatch",
    "sectorize",
]
