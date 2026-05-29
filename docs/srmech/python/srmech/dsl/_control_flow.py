"""Control-flow primitives for the cascade DSL runner: loop / fold / reduce.

ADR-0002 Phase 2-v2 (task #235) — adds the three composition primitives
that turn a flat ``chain().then(...).then(...)`` pipeline into a real
DSL with iteration + accumulation. Each helper returns a closure that
takes one input value and produces one output value, matching the
``Chain._stages`` per-stage callable contract.

Design notes
------------
* **No new srmech-level primitive class.** Loop / fold / reduce are
  *composition operators* — they sequence existing A–N primitives;
  they don't introduce a new class. ``loop`` IS Class I (cyclic
  repetition); ``fold`` and ``reduce`` are Class M (cross-class bind:
  accumulator + element each step).
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


__all__ = [
    "make_loop_stage",
    "make_fold_stage",
    "make_reduce_stage",
]
