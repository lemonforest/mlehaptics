"""Fluent cascade-composition builder for the v0.5.0rc8 DSL.

The :class:`Chain` builder composes cascade-catalog ops
(``srmech.amsc.cascade.*``) + control-flow primitives (loop / fold /
reduce) into a single executable pipeline. The runner reads the TOML
cascade-catalog descriptors at construction time and dispatches through
the matching ``srmech.amsc.cascade`` Python entry points (which
themselves route to C peers when ``HAS_NATIVE`` is True).

Per-stage events are emitted to the introspection bus when active
(``srmech.introspect.publish()`` or ``SRMECH_PUBLISH_STATUS=1``) —
observable via ``srmech status`` or ``srmech bus tap``.

Framework reading
-----------------
The DSL is Class M (cross-class bind) ∘ Class F (declarative render of
the cascade structure) ∘ Class E (catalog enumeration of cascade ops).
A chain's stage list IS the chain's spectral spectrum — each stage is
one A–N primitive class instance, the chain is the composition. The
loop / fold / reduce primitives are Class I (cyclic repetition) /
Class M (accumulator bind) respectively; no new primitive class is
introduced.
"""

from __future__ import annotations

import functools
from typing import Any, Callable, Iterable, List, Optional, Tuple

from ._catalog import cascade_op_kind, lookup_cascade_op
from ._control_flow import (
    make_fold_stage,
    make_loop_stage,
    make_parallel_stage,
    make_reduce_stage,
)

# Introspection emit hook — same gating pattern as srmech.amsc.cascade.
# The DSL emits ``dsl.<chain_name>.stage.<N>`` / ``dsl.<chain_name>
# .complete`` events when a publish context is active; otherwise the
# hook is a zero-cost no-op (thread-local check first, then bail).
from srmech.introspect._writer import (
    _is_publishing as _is_pub,
    emit_if_publishing as _emit,
)


def _describe_shape(value: Any) -> str:
    """Best-effort shape descriptor for event payloads.

    Mirrors the cascade-emit shape contract used in
    :mod:`srmech.amsc.cascade`. Returns a short string suitable for the
    ``input_shape`` / ``output_shape`` event fields — avoids
    serialising arbitrary numpy / list payloads through the wire.
    """
    if value is None:
        return "None"
    if hasattr(value, "shape") and hasattr(value, "dtype"):
        # numpy-like
        try:
            return f"{tuple(value.shape)}/{value.dtype}"
        except Exception:
            return "ndarray"
    if isinstance(value, (list, tuple, str, bytes)):
        return f"{type(value).__name__}(len={len(value)})"
    if isinstance(value, dict):
        return f"dict(len={len(value)})"
    if isinstance(value, (int, float, bool, complex)):
        return type(value).__name__
    return type(value).__name__


class Chain:
    """Fluent cascade-composition builder.

    Build a chain by chaining ``.then(...)``, ``.loop(...)``,
    ``.fold(...)``, ``.reduce(...)`` calls; execute it with
    :meth:`run`. Each builder method returns ``self`` so the calls
    chain idiomatically::

        result = (
            chain("my-pipeline")
                .then("pin_slot_at_zero")
                .then("best_rational_signed", max_denominator=100)
                .run(-3.14)
        )

    Parameters
    ----------
    name
        Chain name; used as the event-emit prefix
        (``dsl.<name>.stage.<N>``). Defaults to ``"chain"`` when
        not supplied.
    """

    __slots__ = ("name", "_stages", "_terminal_reason")

    def __init__(self, name: Optional[str] = None) -> None:
        self.name: str = name or "chain"
        # Each stage: (op_name, callable, kwargs-dict).
        self._stages: List[Tuple[str, Callable, dict]] = []
        # Set when a TERMINAL stage is appended (a non-combining
        # ``parallel_sectors`` fan-out, whose output is a list-of-N, not a
        # single composable value). Chaining past it raises a guided error
        # instead of crashing the next stage with the list — the rc12
        # composability guard.
        self._terminal_reason: Optional[str] = None

    # ── builders ───────────────────────────────────────────────────

    def _guard_not_terminal(self) -> None:
        """Raise if the previous stage was a terminal (non-composable) one.

        A ``parallel_sectors(..., combine=None)`` stage yields the
        per-sector LIST, not a single piped value — so a following stage
        would receive a list-of-N and fail. The rc12 guard turns that into
        a clear, actionable error pointing at ``combine=``.
        """
        if self._terminal_reason is not None:
            raise ValueError(self._terminal_reason)

    def then(self, op_name: str, **kwargs: Any) -> "Chain":
        """Append a cascade-catalog op by name.

        ``op_name`` must match a ``[cascade].name`` field in one of the
        on-disk TOML descriptors under
        ``srmech/amsc/_research/cascade_catalog/``.

        Extra ``kwargs`` are passed straight through to the resolved
        callable; cascade ops with keyword-only options
        (``best_rational_signed``'s ``max_denominator`` / ``fine_scale``)
        accept their canonical names.

        A ``combinator``-kind op (the 1→N fan-out
        ``parallel_sector_dispatch``) is **rejected here** with a guided
        error — it is not a plain ``value → value`` stage and must be
        driven by :meth:`parallel_sectors` (the ``parallel`` discriminator),
        the same way loop/fold/reduce have their own builders.
        """
        self._guard_not_terminal()
        if cascade_op_kind(op_name) == "combinator":
            raise ValueError(
                f"'{op_name}' is a fan-out combinator (kind='combinator'), "
                f"not a plain `op` stage: it takes a *body* op + data and "
                f"yields N per-sector results (1→N), so it cannot be a "
                f"`value → value` `.then()` / `op=` stage. Use the "
                f"`parallel` discriminator instead — "
                f"`chain.parallel_sectors(body=<unary-op>, n_sectors=4)` "
                f"in Python, or a `[[stage]]` with "
                f"`parallel_body='<unary-op>'` in a TOML chain spec."
            )
        op_fn = lookup_cascade_op(op_name)
        self._stages.append((op_name, op_fn, dict(kwargs)))
        return self

    def loop(self, n_times: int, sub_chain: "Chain") -> "Chain":
        """Repeat ``sub_chain`` ``n_times`` (value-threaded).

        Each iteration feeds the previous iteration's output as the
        next iteration's input. ``n_times == 0`` is a no-op (input
        passes through unchanged).
        """
        self._guard_not_terminal()
        if not isinstance(sub_chain, Chain):
            raise TypeError(
                f"loop: sub_chain must be a Chain instance; "
                f"got {type(sub_chain).__name__}"
            )
        stage_fn = make_loop_stage(n_times, sub_chain)
        # Encode the meta in the stage tuple so visualize can render it.
        self._stages.append((
            f"loop({n_times}, {sub_chain.name})",
            stage_fn,
            {},
        ))
        return self

    def fold(
        self, init: Any, op_name: str, **kwargs: Any,
    ) -> "Chain":
        """Fold over the input sequence: ``acc = op(acc, elem)`` with seed.

        ``op_name`` resolves to a cascade-catalog op (must be a
        2-argument callable, e.g. ``cyclic_gcd``). ``init`` is the
        seed accumulator; an empty input sequence yields ``init``
        unchanged.
        """
        self._guard_not_terminal()
        op_fn = lookup_cascade_op(op_name)
        stage_fn = make_fold_stage(init, op_fn, dict(kwargs))
        self._stages.append((
            f"fold(init, {op_name})",
            stage_fn,
            {},
        ))
        return self

    def reduce(self, op_name: str, **kwargs: Any) -> "Chain":
        """Reduce over the input sequence: same as fold but no seed.

        Uses the first element of the input as the initial accumulator;
        an empty input sequence raises ``ValueError`` (matches
        ``functools.reduce``).
        """
        self._guard_not_terminal()
        op_fn = lookup_cascade_op(op_name)
        stage_fn = make_reduce_stage(op_fn, dict(kwargs))
        self._stages.append((
            f"reduce({op_name})",
            stage_fn,
            {},
        ))
        return self

    def parallel_sectors(
        self, body: str, *, n_sectors: int = 4, combine: Any = "bundle",
        **body_kwargs: Any,
    ) -> "Chain":
        """Fan a unary ``body`` op across its ≤4 Klein-4 chirality sectors.

        The ``parallel`` special form (v0.6.0rc11; rc12 composability). The
        stage runs the piped value through the ``body`` op across
        ``n_sectors`` (≤ 4) Klein-4 sectors via
        :func:`srmech.amsc.cascade.parallel_sector_dispatch`. A GIL-releasing
        body (native / IO / numpy) lets the ≤4 sectors genuinely overlap —
        the F233 4-thread speedup — instead of running serially. Reach for
        it when you have an independent cascade body to fan out rather than
        getting locked into one thread per cascade cycle.

        ``body`` is the dotted-or-bare NAME of a unary cascade op (e.g.
        ``"chiral_flip"``); it is resolved through the cascade catalog,
        the same as :meth:`then`. ``parallel_sector_dispatch`` itself is a
        *combinator*, not a valid ``body`` (a body must be a plain
        ``value → value`` op).

        Extra ``**body_kwargs`` are bound to the body op (``functools.partial``)
        so an op with keyword-only options can still be a ``parallel_body`` —
        e.g. ``parallel_sectors("reorient", orientation=-1)`` or
        ``parallel_sectors("best_rational_signed", max_denominator=100)``.
        The bound body stays a unary ``value → value`` callable, so the
        per-sector dispatch is unchanged (UPSTREAM_NOTES §16.1).

        ``combine`` (rc12 §11.3) decides the stage's output shape:

        * default ``"bundle"`` (or ``"mean"`` / ``"sector0"`` / ``"concat"``
          / a callable) — RECOMBINE the ≤4 sector results into ONE value,
          so the stage is ``stream → stream`` and **chains / nests** like
          any other stage. This carries the 4-way splay THROUGH a chained
          cascade — e.g. a settling loop runs 4×-per-step::

              chain("settle").parallel_sectors("body").parallel_sectors("body")

        * ``combine=None`` — emit the **ordered per-sector list**
          ``[sector_0, …, sector_{n-1}]`` (the 1→N fan-out, for inspecting
          the four chirality channels). This is a TERMINAL stage: chaining
          a further builder after it raises a guided error (the next stage
          cannot consume a list-of-N).
        """
        self._guard_not_terminal()
        body_fn = lookup_cascade_op(body)
        if body_kwargs:
            # Bind the body op's keyword-only options (e.g. reorient's
            # orientation=-1) so a required-kwarg op can be a parallel_body:
            # the per-sector dispatch calls body_fn(stream) with the kwargs
            # already applied (UPSTREAM_NOTES §16.1 parallel_body= completion).
            body_fn = functools.partial(body_fn, **body_kwargs)
        label_kw = "".join(f", {k}={v}" for k, v in body_kwargs.items())
        stage_fn = make_parallel_stage(body_fn, n_sectors, combine)
        self._stages.append((
            f"parallel_sectors({body}, n={n_sectors}, combine={combine}{label_kw})",
            stage_fn,
            {},
        ))
        if combine is None:
            self._terminal_reason = (
                f"cannot chain past a non-combining parallel_sectors "
                f"('{body}', combine=None): it yields the per-sector LIST "
                f"(a 1→N fan-out), not a single piped value, so the next "
                f"stage cannot consume it. Pass combine='bundle' (or "
                f"'mean'/'sector0'/'concat'/a callable) to recombine into "
                f"one composable stream and keep chaining."
            )
        return self

    # ── execution ──────────────────────────────────────────────────

    def run(self, input_value: Any) -> Any:
        """Execute the chain with ``input_value`` as the seed.

        Each stage receives the previous stage's output. Per-stage
        events are emitted to the introspection bus when a publish
        context is active; otherwise the emit calls are zero-cost.

        Parameters
        ----------
        input_value
            The initial value fed to the first stage.

        Returns
        -------
        Any
            The output of the final stage. An empty chain returns
            ``input_value`` unchanged (the identity chain).
        """
        value = input_value
        for stage_idx, (op_name, op_fn, kwargs) in enumerate(self._stages):
            if _is_pub():
                _emit(
                    f"dsl.{self.name}.stage.{stage_idx}",
                    class_="DSL",
                    input_shape=_describe_shape(value),
                    extra={"op": op_name, "chain": self.name},
                )
            if kwargs:
                value = op_fn(value, **kwargs)
            else:
                value = op_fn(value)
        if _is_pub():
            _emit(
                f"dsl.{self.name}.complete",
                class_="DSL",
                input_shape="",
                output_shape=_describe_shape(value),
                extra={"chain": self.name, "n_stages": len(self._stages)},
            )
        return value

    # ── inspection / dunder helpers ────────────────────────────────

    def stages(self) -> List[Tuple[str, dict]]:
        """Return the chain's stage list as ``[(op_name, kwargs), ...]``.

        Used by ``srmech dsl visualize`` (CLI render) and by tests.
        Callable references are omitted so the return value is purely
        descriptive.
        """
        return [(op_name, dict(kwargs)) for op_name, _fn, kwargs in self._stages]

    def __len__(self) -> int:
        return len(self._stages)

    def __repr__(self) -> str:
        stage_names = ", ".join(op for op, _, _ in self._stages)
        return f"Chain(name={self.name!r}, stages=[{stage_names}])"


def chain(name: Optional[str] = None) -> Chain:
    """Build a new cascade chain.

    The thin factory function the public API hangs on::

        from srmech.dsl import chain

        result = chain("encoder").then("chiral_flip").run([1, 2, 3, 4])

    Parameters
    ----------
    name
        Optional chain name; used as the event-emit prefix
        (``dsl.<name>.stage.<N>``). Defaults to ``"chain"``.
    """
    return Chain(name)


__all__ = ["Chain", "chain"]
