"""Control-flow primitives for the cascade DSL runner: loop / fold / reduce / parallel.

ADR-0002 Phase 2-v2 (task #235) — adds the three composition primitives
that turn a flat ``chain().then(...).then(...)`` pipeline into a real
DSL with iteration + accumulation. v0.6.0rc11 (MS #20) adds the fourth,
``parallel`` (the Klein-4 four-sector fan-out). Each helper returns a
closure that takes one input value and produces one output value,
matching the ``Chain._stages`` per-stage callable contract.

Design notes
------------
* **No new srmech-level primitive class.** Loop / fold / reduce /
  parallel are *composition operators* (control-flow special forms) —
  they sequence existing A–N primitives; they don't introduce a new
  class. ``loop`` IS Class I (cyclic repetition); ``fold`` and
  ``reduce`` are Class M (cross-class bind: accumulator + element each
  step); ``parallel`` is Class C (the Klein-4 chirality-sector fan-out
  of :func:`srmech.amsc.cascade.parallel_sector_dispatch`).
* **Why ``parallel`` is a special form, not a plain ``op``.** A plain
  ``op`` stage is a 1→1 ``value → value`` map. ``parallel`` is a 1→N
  *fan-out*: it runs a caller-named *body* op across the ≤4 Klein-4
  sectors and yields the *list* of per-sector results. Its first
  argument is a *body* (an op name), not the piped value, and its
  natural output is N results — so it cannot be a plain ``op`` stage;
  it gets its own discriminator exactly as loop/fold/reduce do. This is
  why ``parallel_sector_dispatch`` is classified ``kind = "combinator"``
  in its catalog descriptor and rejected as an ``op=`` stage.
* **Sub-chain isolation.** ``loop``'s sub-chain runs its own
  ``Chain.run(value)`` so its event stream is emitted under the
  sub-chain's own name, not the parent's — keeps event-trace
  attribution honest at multiple nesting levels.
* **Reduce on empty sequence raises** per the Python ``functools.reduce``
  convention. ``fold`` with an empty sequence simply returns ``init``
  unchanged (folds over zero elements = the identity = the seed).
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Iterable


def make_loop_stage(n_times: int, sub_chain: "Any") -> Callable[[Any], Any]:
    """Build a stage callable that repeats ``sub_chain`` ``n_times``.

    The sub-chain is run via its own ``run()`` method, so events
    emitted by sub-stages bear the sub-chain's name. Each iteration
    feeds the previous iteration's output as the next iteration's
    input (the value-threaded loop, not a fixed-input loop).

    Parameters
    ----------
    n_times
        Number of repetitions; must be ``>= 0``. ``n_times == 0`` is
        a no-op (returns the input unchanged).
    sub_chain
        A :class:`srmech.dsl.Chain` instance.

    Returns
    -------
    callable
        A unary ``input -> output`` callable matching the
        ``Chain._stages`` contract.

    Raises
    ------
    ValueError
        If ``n_times < 0``.
    """
    if n_times < 0:
        raise ValueError(
            f"loop: n_times must be >= 0; got {n_times}"
        )

    def loop_fn(input_value):
        value = input_value
        for _ in range(n_times):
            value = sub_chain.run(value)
        return value

    return loop_fn


def make_fold_stage(
    init: Any, op_fn: Callable, kwargs: Dict[str, Any],
) -> Callable[[Iterable], Any]:
    """Build a stage callable that folds ``op_fn`` over the input sequence.

    Equivalent to ``functools.reduce(op_fn, input, init)`` with extra
    ``kwargs`` threaded through to each call. Returns ``init`` if the
    input sequence is empty.

    Parameters
    ----------
    init
        Seed accumulator.
    op_fn
        Binary callable: ``(accumulator, element) -> new_accumulator``.
    kwargs
        Static kwargs passed to each ``op_fn`` invocation.

    Returns
    -------
    callable
        A unary ``input -> output`` stage callable.
    """

    def fold_fn(input_seq):
        acc = init
        for elem in input_seq:
            if kwargs:
                acc = op_fn(acc, elem, **kwargs)
            else:
                acc = op_fn(acc, elem)
        return acc

    return fold_fn


def make_reduce_stage(
    op_fn: Callable, kwargs: Dict[str, Any],
) -> Callable[[Iterable], Any]:
    """Build a stage callable that reduces ``op_fn`` over the input sequence.

    Equivalent to ``functools.reduce(op_fn, input)`` (no seed; the first
    element is the seed). Raises ``ValueError`` on an empty input
    sequence — matches both Python's ``functools.reduce`` convention
    and the spec.

    Parameters
    ----------
    op_fn
        Binary callable: ``(accumulator, element) -> new_accumulator``.
    kwargs
        Static kwargs passed to each ``op_fn`` invocation.

    Returns
    -------
    callable
        A unary ``input -> output`` stage callable.
    """

    def reduce_fn(input_seq):
        it = iter(input_seq)
        try:
            acc = next(it)
        except StopIteration:
            raise ValueError(
                "reduce on empty sequence; supply a seed via fold(init, ...) "
                "if an empty sequence should produce a default value"
            )
        for elem in it:
            if kwargs:
                acc = op_fn(acc, elem, **kwargs)
            else:
                acc = op_fn(acc, elem)
        return acc

    return reduce_fn


def make_parallel_stage(
    body_fn: Callable, n_sectors: int = 4,
) -> Callable[[Any], Any]:
    """Build a stage callable that fans ``body_fn`` across the Klein-4 sectors.

    The ``parallel`` special form (v0.6.0rc11): the piped value is run
    through ``body_fn`` across its ``n_sectors`` (≤ 4) Klein-4 chirality
    sectors via :func:`srmech.amsc.cascade.parallel_sector_dispatch`, and
    the stage emits the **ordered list of per-sector results**
    ``[sector_0_result, …, sector_{n-1}_result]``. This is a 1→N fan-out:
    the stage's output is a *list of sequences* (the branch), not a single
    piped value — so a downstream stage receives the N-way bundle, not one
    transformed sequence.

    Parameters
    ----------
    body_fn
        The already-resolved unary cascade callable to fan across sectors
        (the chain builder resolves the body op-name via
        :func:`srmech.dsl._catalog.lookup_cascade_op` before calling here,
        mirroring :func:`make_fold_stage`).
    n_sectors
        How many of the 4 Klein-4 sectors to dispatch (``1..4``; default
        4). Hard-capped at 4 (the Klein-4 ``Z₂ × Z₂`` has no order-4+
        element; 8+ needs the order-3 triality, F220).

    Returns
    -------
    callable
        A unary ``input -> [per-sector results]`` stage callable matching
        the ``Chain._stages`` contract.

    Raises
    ------
    ValueError
        If ``n_sectors`` is not in ``1..4`` (validated at build time so a
        bad chain spec fails fast, not mid-run).
    """
    if not isinstance(n_sectors, int) or isinstance(n_sectors, bool):
        raise ValueError(
            f"parallel: n_sectors must be an int; got {type(n_sectors).__name__}"
        )
    if n_sectors < 1 or n_sectors > 4:
        raise ValueError(
            f"parallel: n_sectors must be in 1..4 (Klein-4 has no order-4+ "
            f"element; 8+ needs the order-3 triality per F220); got {n_sectors}"
        )

    def parallel_fn(input_value):
        # Lazy import (cycle-safe — mirrors _catalog.lookup_cascade_op):
        # srmech.amsc.cascade pulls srmech.introspect which can pull
        # srmech.dsl in some test configurations, so resolve at call time.
        from srmech.amsc.cascade import parallel_sector_dispatch
        result = parallel_sector_dispatch(
            body_fn, input_value, n_sectors=n_sectors,
        )
        sectors = result["sectors"]
        return [sectors[s]["result"] for s in range(n_sectors)]

    return parallel_fn


__all__ = [
    "make_loop_stage",
    "make_fold_stage",
    "make_reduce_stage",
    "make_parallel_stage",
]
