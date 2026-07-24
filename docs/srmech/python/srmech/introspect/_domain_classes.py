"""The package's DOMAIN-CLASS surface — what classes srmech actually ships.

rc298 (`#936`). Before this module, ``describe()["classes"]`` enumerated the
``[class]`` TOML catalog and called that "classes". That is an ADR-0009
mechanism-2 defect: an *implementation detail* (which classes happen to be
TOML-declared) reported as if it were the *capability* surface.

The concrete symptom rc297 created: ``CDRegister`` is a shipped public class, a
registered carrier, and has three C peers — and ``describe()`` said srmech had
four classes, none of them it. A caller asking "what classes do you have?" got
an answer shaped by how the classes were WRITTEN rather than by what they ARE.

The fix is capability-first. Every domain class is reported; the declaration
route travels as a FIELD, never as an admission criterion. A consumer that
genuinely wants the TOML-only view reads ``toml_total`` / filters ``routes``.

HOW THE SET IS DERIVED (and why it is not a hand-written list)
-------------------------------------------------------------
A hand-maintained roster is exactly what rots into the bug this module exists
to fix, so the set is derived from two live sources:

  * the ``[class]`` TOML catalog          -> route ``"toml"``
  * public classes in ``srmech.amsc.cascade.__all__``  -> route ``"python"``

``srmech.amsc.cascade`` is the domain-object surface: ``One``,
``SedenionRegister`` and ``CDRegister`` all live there, and any future domain
class lands there too. So a new domain class appears in ``describe()``
AUTOMATICALLY. The only maintenance burden is the reverse direction — a value
RECORD exported alongside them must be named in ``NON_DOMAIN_RECORDS`` below,
with a reason. That asymmetry is deliberate: the failure mode is
over-reporting (loud, caught by the ratchet in tests/test_domain_classes_rc298.py)
rather than the silent under-reporting that produced `#936`.
"""

from __future__ import annotations

from typing import Dict

__all__ = ["NON_DOMAIN_RECORDS", "list_domain_classes"]


#: Classes exported from ``srmech.amsc.cascade`` that are value RECORDS —
#: components OF a domain object rather than domain objects themselves. Each
#: entry carries the reason it is not a class in the capability sense.
#:
#: Adding a name here is a deliberate act. ``tests/test_domain_classes_rc298.py``
#: pins this mapping so a new cascade export cannot be quietly excluded.
NON_DOMAIN_RECORDS: Dict[str, str] = {
    "Block": (
        "a frozen value record of One's Hurwitz block decomposition "
        "(R.1 + sigma e^{I_n theta} Im A_n) — an attribute bag held by "
        "One.blocks, with no cascade-op-chain surface of its own"
    ),
}


def list_domain_classes() -> Dict[str, str]:
    """Every domain class srmech ships, mapped to its declaration route.

    Returns
    -------
    dict
        ``{class_name: "toml" | "python"}``. ``"toml"`` means a ``[class]``
        descriptor drives it (so ``srmech.dsl.describe_class`` resolves it and
        it is compiled into ``srmech_class_registry``); ``"python"`` means it is
        hand-coded (so it has no TOML descriptor, and a bare-C host reaches its
        capability through the class's own C peers rather than through
        ``srmech_run_class_method``).

    The route is DESCRIPTIVE. Both routes are shipped, supported classes; the
    distinction is how the declaration is spelled, not whether the capability
    exists. See ADR-0009 — the capability is the invariant, the projection is
    not.
    """
    routes: Dict[str, str] = {}

    # Guarded imports: this module is reached from ``describe()``, which runs
    # during package warmup, so a hard import of either source could re-enter a
    # partially-initialised module. Both sources are independently optional.
    try:
        from ..dsl import list_classes as _list_classes
        for name in _list_classes():
            routes[name] = "toml"
    except Exception:  # pragma: no cover — class catalog optional / absent
        pass

    try:
        from ..amsc import cascade as _cascade
        for name in getattr(_cascade, "__all__", ()):
            if name in NON_DOMAIN_RECORDS:
                continue
            if not isinstance(getattr(_cascade, name, None), type):
                continue
            # A TOML-declared class also has a Python class object (One /
            # SedenionRegister). The TOML descriptor is the DECLARATION, so it
            # wins the route; don't downgrade it here.
            routes.setdefault(name, "python")
    except Exception:  # pragma: no cover — cascade surface optional
        pass

    return dict(sorted(routes.items()))
