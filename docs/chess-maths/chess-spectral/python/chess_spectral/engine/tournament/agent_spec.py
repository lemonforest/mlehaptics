"""Agent specification parsing for the search / tournament CLIs.

The CLI accepts a per-side string like::

    evaluator=spectral,depth=4,weights=spectral_v1.json

and produces a fully-configured :class:`~.core.Agent`. Same key=value
shape across 2D and 4D — the only difference is the bound
``search_fn`` and the bound evaluator-resolver (which evaluator family
modules to look up by name).

This is the *symmetric per-side configuration* surface §16's tournament
needs: white and black each get their own AgentSpec, parsed from
identical strings, so a CLI invocation like::

    chess_spectral tournament \\
        --white evaluator=spectral,depth=4,weights=sw_v1.json \\
        --black evaluator=qm,depth=3,weights=qw_v1.json \\
        --rounds 10

ships two completely-different engine configurations into the same
single-process tournament loop.

Spec grammar
------------

A spec is a comma-separated sequence of ``key=value`` pairs. Recognized
keys:

  - ``label``                  display name (default: ``<evaluator>@<depth>``)
  - ``evaluator``              ``material`` | ``spectral`` | ``qm``  (required)
  - ``depth``                  integer search depth (default: 4)
  - ``time_budget_ms``         integer milliseconds; 0/unset = no budget
  - ``weights``                path to weights JSON (spectral / qm only)
  - ``no_tt``                  flag, disables transposition table
  - ``no_mvv_lva``             flag, disables MVV-LVA move ordering
  - ``no_quiescence``          flag, disables quiescence search
  - ``quiescence_max_depth``   integer (default: 8)

Boolean flags can be specified as ``key`` alone (sets to True) or
``key=true``/``key=false``. Whitespace around keys/values is stripped.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, Mapping, Optional


_VALID_EVALUATORS_2D = ("material", "spectral", "qm")
_VALID_EVALUATORS_4D = ("material", "spectral", "qm")
_BOOL_KEYS = ("no_tt", "no_mvv_lva", "no_quiescence")
_INT_KEYS = ("depth", "time_budget_ms", "quiescence_max_depth")
_STR_KEYS = ("label", "evaluator", "weights")
_KNOWN_KEYS = set(_BOOL_KEYS + _INT_KEYS + _STR_KEYS)


@dataclass
class AgentSpec:
    """Parsed but not-yet-bound agent configuration.

    ``evaluator`` is the family name (string); the dim-specific
    ``build_agent`` is what binds it to a real callable + search_fn.
    """
    evaluator: str
    label: Optional[str] = None
    depth: int = 4
    time_budget_ms: Optional[int] = None
    weights: Optional[Path] = None
    no_tt: bool = False
    no_mvv_lva: bool = False
    no_quiescence: bool = False
    quiescence_max_depth: int = 8


def parse_spec(text: str) -> AgentSpec:
    """Parse a comma-separated ``key=value`` agent spec.

    Raises ``ValueError`` on unknown keys, missing required ``evaluator``,
    or malformed fragments. The caller is responsible for binding the
    spec to a dim-specific :class:`Agent` via ``build_agent_2d`` or
    ``build_agent_4d``.
    """
    if not text or not text.strip():
        raise ValueError("agent spec is empty")
    pairs: Dict[str, object] = {}
    for raw in text.split(","):
        item = raw.strip()
        if not item:
            continue
        if "=" in item:
            key, _, value = item.partition("=")
            key = key.strip()
            value = value.strip()
        else:
            # Bare flag form: `no_tt` -> no_tt=True
            key = item
            value = "true"
        if key not in _KNOWN_KEYS:
            raise ValueError(
                f"unknown agent spec key {key!r}; valid keys: "
                f"{', '.join(sorted(_KNOWN_KEYS))}"
            )
        if key in _BOOL_KEYS:
            pairs[key] = _parse_bool(value, key)
        elif key in _INT_KEYS:
            try:
                pairs[key] = int(value)
            except ValueError:
                raise ValueError(f"agent spec {key}={value!r}: not an integer")
        elif key == "weights":
            pairs[key] = Path(value)
        else:
            pairs[key] = value

    if "evaluator" not in pairs:
        raise ValueError(
            "agent spec missing required 'evaluator=' (one of material / "
            "spectral / qm)"
        )
    return AgentSpec(**pairs)  # type: ignore[arg-type]


def _parse_bool(value: str, key: str) -> bool:
    v = value.lower()
    if v in ("true", "1", "yes", "on"):
        return True
    if v in ("false", "0", "no", "off"):
        return False
    raise ValueError(f"agent spec {key}={value!r}: expected boolean (true/false)")


def _validate_evaluator(name: str, valid: tuple) -> None:
    if name not in valid:
        raise ValueError(
            f"unknown evaluator {name!r}; expected one of {', '.join(valid)}"
        )


def _build_agent_common(
    spec: AgentSpec,
    valid_evaluators: tuple,
    eval_module_resolver: Callable[[str], object],
    search_fn: Callable,
    SearchOptions,
):
    """Shared body for build_agent_2d / build_agent_4d.

    ``eval_module_resolver(name) -> module`` returns the evaluator
    module (must expose ``evaluate(position, side_to_move)``,
    ``DEFAULT_WEIGHTS``, ``load_weights_json`` for spectral / qm).
    """
    _validate_evaluator(spec.evaluator, valid_evaluators)

    eval_mod = eval_module_resolver(spec.evaluator)

    if spec.weights is not None:
        if not hasattr(eval_mod, "load_weights_json"):
            raise ValueError(
                f"evaluator {spec.evaluator!r} does not accept weights "
                f"(material is unweighted by design)"
            )
        weights = eval_mod.load_weights_json(spec.weights)
        # Bind the evaluator with the loaded weights via a closure.
        evaluator = lambda pos, stm: eval_mod.evaluate(  # noqa: E731
            pos, stm, weights=weights
        )
    else:
        evaluator = eval_mod.evaluate

    options = SearchOptions(
        max_depth=spec.depth,
        time_budget_ms=spec.time_budget_ms,
        use_tt=not spec.no_tt,
        use_mvv_lva=not spec.no_mvv_lva,
        use_quiescence=not spec.no_quiescence,
        quiescence_max_depth=spec.quiescence_max_depth,
    )

    label = spec.label or f"{spec.evaluator}@{spec.depth}"
    return label, evaluator, search_fn, options


def build_agent_2d(spec: AgentSpec):
    """Resolve a 2D :class:`Agent` from a parsed :class:`AgentSpec`.

    Imports of the dim-specific modules are deferred until call time
    so this module remains a leaf with no heavyweight side effects.
    """
    from chess_spectral.engine.tournament.core import Agent
    from chess_spectral.engine.search import search, SearchOptions
    from chess_spectral.engine.eval import material, spectral, qm

    def _resolve(name: str):
        return {"material": material, "spectral": spectral, "qm": qm}[name]

    label, evaluator, sfn, options = _build_agent_common(
        spec, _VALID_EVALUATORS_2D, _resolve, search, SearchOptions,
    )
    return Agent(
        label=label, evaluator=evaluator, search_fn=sfn, search_options=options,
    )


def build_agent_4d(spec: AgentSpec):
    """Resolve a 4D :class:`Agent` from a parsed :class:`AgentSpec`.

    Mirrors ``build_agent_2d`` but binds 4D-side modules.
    """
    from chess_spectral.engine.tournament.core import Agent
    from chess_spectral_4d.engine.search import search, SearchOptions
    from chess_spectral_4d.engine.eval import material, spectral, qm

    def _resolve(name: str):
        return {"material": material, "spectral": spectral, "qm": qm}[name]

    label, evaluator, sfn, options = _build_agent_common(
        spec, _VALID_EVALUATORS_4D, _resolve, search, SearchOptions,
    )
    return Agent(
        label=label, evaluator=evaluator, search_fn=sfn, search_options=options,
    )


__all__ = [
    "AgentSpec", "parse_spec",
    "build_agent_2d", "build_agent_4d",
]
