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

from typing import Any, Callable, Iterable, List, Optional, Tuple

from ._catalog import lookup_cascade_op
from ._control_flow import (
    make_fold_stage,
    make_loop_stage,
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

    __slots__ = ("name", "_stages")

    def __init__(self, name: Optional[str] = None) -> None:
        self.name: str = name or "chain"
        # Each stage: (op_name, callable, kwargs-dict).
        self._stages: List[Tuple[str, Callable, dict]] = []

    # ── builders ───────────────────────────────────────────────────

    def then(self, op_name: str, **kwargs: Any) -> "Chain":
        """Append a cascade-catalog op by name.

        ``op_name`` must match a ``[cascade].name`` field in one of the
        on-disk TOML descriptors under
        ``srmech/amsc/_research/cascade_catalog/``.

        Extra ``kwargs`` are passed straight through to the resolved
        callable; cascade ops with keyword-only options
        (``best_rational_signed``'s ``max_denominator`` / ``fine_scale``)
        accept their canonical names.
        """
        op_fn = lookup_cascade_op(op_name)
        self._stages.append((op_name, op_fn, dict(kwargs)))
        return self

    def loop(self, n_times: int, sub_chain: "Chain") -> "Chain":
        """Repeat ``sub_chain`` ``n_times`` (value-threaded).

        Each iteration feeds the previous iteration's output as the
        next iteration's input. ``n_times == 0`` is a no-op (input
        passes through unchanged).
        """
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
        op_fn = lookup_cascade_op(op_name)
        stage_fn = make_reduce_stage(op_fn, dict(kwargs))
        self._stages.append((
            f"reduce({op_name})",
            stage_fn,
            {},
        ))
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
