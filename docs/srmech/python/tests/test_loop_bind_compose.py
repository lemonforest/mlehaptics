"""v0.7.0rc3 — the loop-bind family slots into the compose engine (MS #21 #813).

#813 asks HOW the octonion loop-bind composes in srmech's operator-chain surface
(``srmech.amsc.compose.run_chain`` against ``DEFAULT_CLASS_REGISTRY``). The answer:
it is ALREADY reachable — registry ``M`` → ``srmech.amsc.hdc``, and ops resolve
dynamically by name — so ``loop_bind`` / ``loop_conj`` / ``loop_associator`` /
``cross7`` / ``g2_three_form`` run as ``class="M", op="<name>"`` steps with NO new
registration. This test is the worked proof: M (bind) composes, C (loop_conj
ordering) composes after it, and the K associator residue resolves — the
M∘C-with-K-residue cascade #813 describes, runnable end-to-end. The compose-engine
registration #813 also mentions (a shipped cascade-catalog descriptor) carries a C
symbol, so it rides with the C-transpile step at the end of the v0.7.0 arc.

numpy-free: octonion basis vectors are plain length-8 Python lists with a single
1.0 (``_e(i)``); the ops take and return plain lists; equality is an element-wise
``abs(a-b) < tol`` loop.
"""
from srmech.amsc import compose
from srmech.amsc import hdc


def _e(i):
    """The i-th octonion basis vector as a plain length-8 list."""
    v = [0.0] * 8
    v[i] = 1.0
    return v


def _allclose(a, b, atol=1e-9):
    """Element-wise |a - b| < atol over two equal-length octonion vectors."""
    a = list(a)
    b = list(b)
    return len(a) == len(b) and all(abs(x - y) < atol for x, y in zip(a, b))


def _spec(name, *steps):
    return compose.parse_chain_spec({
        "name": name,
        "summary": f"loop-bind compose proof: {name}",
        "returns": "octonion vector",
        "steps": list(steps),
    })


def test_loop_bind_resolves_and_runs_in_compose_engine():
    # M (the octonion loop-bind) reached as class="M", op="loop_bind".
    spec = _spec(
        "loop_bind",
        {"class": "M", "op": "loop_bind",
         "args": {"x": "@input.x", "y": "@input.y"}},
    )
    out = compose.run_chain(spec, inputs={"x": _e(1), "y": _e(2)})
    assert _allclose(out, hdc.loop_bind(_e(1), _e(2)))


def test_loop_associator_K_residue_resolves_in_compose_engine():
    # The Class-K associator residue resolves through the same surface.
    spec = _spec(
        "loop_associator",
        {"class": "M", "op": "loop_associator",
         "args": {"a": "@input.a", "b": "@input.b", "c": "@input.c"}},
    )
    out = compose.run_chain(
        spec, inputs={"a": _e(1), "b": _e(2), "c": _e(4)})
    assert _allclose(out, hdc.loop_associator(_e(1), _e(2), _e(4)))


def test_cross7_and_g2_three_form_resolve_in_compose_engine():
    # The rc2 companions are reachable through the compose engine too.
    cross = compose.run_chain(
        _spec("cross7", {"class": "M", "op": "cross7",
                         "args": {"x": "@input.x", "y": "@input.y"}}),
        inputs={"x": _e(1), "y": _e(2)})
    assert _allclose(cross, hdc.cross7(_e(1), _e(2)))
    phi = compose.run_chain(
        _spec("g2", {"class": "M", "op": "g2_three_form",
                     "args": {"x": "@input.x", "y": "@input.y", "z": "@input.z"}}),
        inputs={"x": _e(1), "y": _e(2), "z": _e(3)})
    assert abs(phi - 1.0) < 1e-9   # φ(e1,e2,e3) = +1


def test_two_step_M_then_C_composition():
    # M (bind) ∘ C (loop_conj ordering flip): step[1] consumes step[0]'s output.
    spec = _spec(
        "bind_then_conj",
        {"class": "M", "op": "loop_bind",
         "args": {"x": "@input.x", "y": "@input.y"}},
        {"class": "M", "op": "loop_conj", "args": {"x": "@step[0]"}},
    )
    out = compose.run_chain(spec, inputs={"x": _e(1), "y": _e(2)})
    assert _allclose(out, hdc.loop_conj(hdc.loop_bind(_e(1), _e(2))))
