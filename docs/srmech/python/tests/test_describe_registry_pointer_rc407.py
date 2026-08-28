"""rc407 (`#T1076`) — ``describe()`` must publish the route to the registry.

THE DEFECT THIS PINS. ``describe()`` is the self-recognition ROOT and, since
v0.5.0rc11, the surface an MCP / JSON-RPC consumer is pointed at first. Through
rc406 its ``tools`` block held exactly four keys — ``total``, ``mcp_callable``,
``handle_pending``, ``by_category`` — all of them COUNTS. Measured on the rc406
tree: ``json.dumps(describe())`` was 20,981 characters and the strings
``get_tool_schema``, ``ToolEntry``, ``registry``, ``find`` and ``lookup``
occurred **zero times** in it. The index said how many ops exist and never how
to reach one.

WHY THAT IS A REAL DEFECT AND NOT A STYLE POINT. It is not a circularity
argument — ``tool_schema`` IS in ``dir(srmech.introspect)`` in a fresh
interpreter, so a Python caller can always find the drill-down by hand. The
consumer that cannot is the one ``describe()`` exists for: **a JSON consumer
has no ``dir()``.** It receives a bare total and, from the payload alone, no
next call. So the route has to be IN the payload.

``covers`` is the second half. The registry indexes module-level ops only;
carrier and class METHODS are not in it. Without a scope statement, a reader
who searches the registry for ``QMat.rank`` and misses learns the wrong thing —
that it does not ship — when the truth is that it is published on a different
surface (``describe()["carriers"]`` / :mod:`srmech.introspect.carrier_schema`).

FAILS BEFORE / PASSES AFTER: reverting the ``tools`` dict in
``srmech/introspect/__init__.py`` to its four count keys makes
``test_tools_block_publishes_the_registry_route`` fail on the first assert.
"""

import importlib
import json

import srmech
from srmech.introspect import describe


def test_tools_block_publishes_the_registry_route():
    """The count block must carry a REACHABLE drill-down route."""
    tools = describe()["tools"]

    assert "registry" in tools, (
        "describe()['tools'] must name the per-op registry; a JSON consumer "
        "has no dir() and otherwise has no next call after the count"
    )
    assert tools["registry"] == "srmech.introspect.tool_schema.get_tool_schema"
    assert "resolve" in tools
    assert tools["resolve"].startswith(tools["registry"])


def test_the_named_registry_route_actually_imports_to_a_callable():
    """A pointer that does not resolve is worse than none — import it."""
    dotted = describe()["tools"]["registry"]
    module_path, _, attr = dotted.rpartition(".")
    obj = getattr(importlib.import_module(module_path), attr)

    assert callable(obj), f"{dotted} is not callable"

    # And it really is the registry the counts were taken from.
    schema = obj()
    assert len(schema.tools) == describe()["tools"]["total"]
    assert callable(schema.resolve), "the 'resolve' route must exist on it"


def test_covers_states_the_scope_including_the_carrier_exclusion():
    """The scope note must name the surface it does NOT index."""
    covers = describe()["tools"]["covers"]

    assert isinstance(covers, str) and covers
    assert "carrier" in covers, (
        "'covers' must say carrier/class methods are not in this registry, "
        "or a missing lookup reads as 'srmech does not ship it'"
    )


def test_the_route_is_discoverable_in_the_serialised_payload():
    """The whole point: the route survives into the JSON an MCP client sees."""
    blob = json.dumps(describe())

    assert "get_tool_schema" in blob
    assert "carrier_schema" in blob


def test_top_level_key_set_is_untouched():
    """The route rides INSIDE 'tools'. The 13-key top level is pinned
    exhaustively HERE and in two peers — ``tests/test_domain_classes_rc298.py``
    and ``tests/test_mcp.py::test_describe_shape`` — and all three must move
    together. (11 -> 12 at rc420: "cascade_catalog", ADR-0012 clause C6 closed;
    12 -> 13 at rc430: "frames", the FRAME axis — local task `#T1127`.)

    The "pinned exhaustively by rc298" phrasing this docstring carried until
    rc430 named ONE peer and read as though this file were the derivative copy.
    There are three peers, none derivative; ``test_describe_key_set_pins_rc430``
    derives the roster so the count cannot go stale silently again.
    """
    d = describe()

    assert set(d) == {
        "srmech_version",
        "tool_schema_version",
        "native",
        "tools",
        "handle_pending",
        "categories",
        "classes",
        "cascade_catalog",
        "carriers",
        "limits",
        "c_claims",
        "lanes",
        "frames",
    }
    assert len(d) == 13


def test_registry_size_is_unchanged_by_this_rc():
    """No public callable was added, removed or renamed here."""
    from srmech.introspect.tool_schema import get_tool_schema, warmup_all

    warmup_all()
    assert len(get_tool_schema().tools) == 679
    assert describe()["tools"]["total"] == 679
    assert describe()["srmech_version"] == srmech.__version__
