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

# ── F1 carrier-FFI (the DSL Chain LINEAR run-loop → C; 0.9.0rc181) ──────────
# ``Chain.run`` value-threads the F1 carrier through the C-backed cascade atoms
# via ``srmech_dsl_chain_run`` (srmech_dsl_chain_run.c) — the leaf-dispatch table
# (``lookup_cascade_op``) + the ``build_chain_from_dict`` stage-IR grammar, both
# in C. Only LINEAR (``.then(...)``) chains over the C-backed unary atoms take the
# native path; a combinator (loop/fold/reduce/parallel) stage, a non-C leaf, or an
# unsupported carrier shape falls through to the pure loop below (rc103 inform-
# don't-limit — never a wrong answer). The F1 value descriptor is shared with the
# #796 F2/F3/F4 carrier extensions:
#   None -> {"k":"n"} ; int -> {"k":"i","v":..} ; float -> {"k":"f","v":..} ;
#   str -> {"k":"s","v":..} ; list -> {"k":"l","v":[..]} ; tuple -> {"k":"t",..}
_NATIVE_MISS = object()
_F1_MAX_DEPTH = 6
_INT64_MIN = -(2 ** 63)
_INT64_MAX = (2 ** 63) - 1


def _value_to_desc(v: Any, depth: int = 0) -> Optional[dict]:
    """Marshal a Python value to the F1 value descriptor; ``None`` → defer to pure.

    Only the F1-representable shapes (None / int64 / float / str / bounded-depth
    list|tuple of those) marshal; anything else (bool, out-of-int64 int, bytes,
    dict, complex, a numpy scalar, over-deep nesting) returns ``None`` so
    ``Chain.run`` keeps the pure path.
    """
    if depth > _F1_MAX_DEPTH:
        return None
    if v is None:
        return {"k": "n"}
    if type(v) is bool:
        return None                      # bool not an F1 carrier kind → pure
    if type(v) is int:
        if _INT64_MIN <= v <= _INT64_MAX:
            return {"k": "i", "v": v}
        return None                      # out-of-int64 → pure
    if type(v) is float:
        return {"k": "f", "v": v}
    if type(v) is str:
        return {"k": "s", "v": v}
    if type(v) is list or type(v) is tuple:
        items: List[dict] = []
        for e in v:
            d = _value_to_desc(e, depth + 1)
            if d is None:
                return None
            items.append(d)
        return {"k": "t" if type(v) is tuple else "l", "v": items}
    return None


def _desc_to_value(desc: Any) -> Any:
    """Rebuild a Python value from the F1 value descriptor (the C output)."""
    k = desc.get("k")
    if k == "n":
        return None
    if k == "i":
        return int(desc["v"])
    if k == "f":
        return float(desc["v"])
    if k == "s":
        return desc["v"]
    if k == "l":
        return [_desc_to_value(e) for e in desc["v"]]
    if k == "t":
        return tuple(_desc_to_value(e) for e in desc["v"])
    raise ValueError(f"unknown F1 value descriptor kind {k!r}")

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

    def _run_native(self, input_value: Any) -> Any:
        """Run this chain in C via ``srmech_dsl_chain_run``; ``_NATIVE_MISS`` → pure.

        Eligible iff the chain is a non-empty LINEAR pipeline (every stage is a
        plain ``op`` stage — no loop/fold/reduce/parallel combinator, whose stage
        labels carry a ``(``), every stage kwarg is a JSON scalar, and the seed is
        an F1-representable value. The C peer decides per-leaf whether it is
        C-backed; a non-C leaf / unsupported carrier returns non-OK → pure.
        """
        from srmech.amsc import _native
        if not (_native.HAS_NATIVE and _native.LIB is not None):
            return _NATIVE_MISS
        lib = _native.LIB
        if not (hasattr(lib, "srmech_dsl_chain_run")
                and hasattr(lib, "srmech_dsl_chain_run_arena_bytes")):
            return _NATIVE_MISS
        if not self._stages:
            return _NATIVE_MISS                      # identity chain → pure
        stage_list: List[dict] = []
        for op_name, _fn, kwargs in self._stages:
            if "(" in op_name:                       # combinator label → rc182
                return _NATIVE_MISS
            stage: dict = {"op": op_name}
            for kk, vv in kwargs.items():
                if type(vv) is bool or type(vv) not in (int, float, str):
                    return _NATIVE_MISS              # non-scalar kwarg → pure
                stage[kk] = vv
            stage_list.append(stage)
        input_desc = _value_to_desc(input_value)
        if input_desc is None:
            return _NATIVE_MISS
        import ctypes
        import json
        chain_dict = {"chain": {"name": self.name}, "stage": stage_list}
        try:
            chain_json = json.dumps(chain_dict, ensure_ascii=False).encode("utf-8")
            input_json = json.dumps(input_desc, ensure_ascii=False).encode("utf-8")
        except (TypeError, ValueError):
            return _NATIVE_MISS
        ws_bytes = int(lib.srmech_dsl_chain_run_arena_bytes(
            len(chain_json), len(input_json)))
        ws = (ctypes.c_char * ws_bytes)()
        out_cap = max(ws_bytes // 2, 16384)
        out = (ctypes.c_char * out_cap)()
        out_len = ctypes.c_size_t()
        rc = lib.srmech_dsl_chain_run(
            chain_json, len(chain_json), input_json, len(input_json),
            ws, ws_bytes, out, out_cap, ctypes.byref(out_len))
        if rc != _native.SRMECH_OK:
            return _NATIVE_MISS
        desc = json.loads(out.raw[:out_len.value].decode("utf-8"))
        return _desc_to_value(desc)

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
        # F1 carrier-FFI: a LINEAR chain over the C-backed atoms runs end-to-end
        # in C (rc181). Skipped while a publish context is active so the per-stage
        # events still fire on the pure path; a non-eligible chain / non-C leaf /
        # unsupported carrier returns _NATIVE_MISS → the pure loop below runs.
        if not _is_pub():
            native = self._run_native(input_value)
            if native is not _NATIVE_MISS:
                return native
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
