"""rc464 (`#T1188`) — the WORKED-example generator for the fourteen `cdr_*`
[class] CDRegister binding-surface adapters.

COMPUTATIONAL PROVENANCE. Every `# ->` line in the fourteen curated examples
this writes into `srmech/introspect/_tool_docs_curated.py` is a REAL captured
`repr`, produced by executing the expression immediately above it in this
script. Nothing here is typed by hand, and an expression whose repr exceeds the
cap RAISES rather than truncating — a truncated output is a fabricated one.

WHY A WORKED SNIPPET AND NOT JUST AN input/output PAIR. Two gates want
different things and only the snippet satisfies both:

  * `tests/test_worked_examples_strict_zero_rc353.py` wants a non-empty
    captured `output` on every example. A `smoke_test_hint` alone satisfies
    that — `tools/gen_tool_docs.py` executes the hint and banks the real result.
  * `tests/test_frame_scope_rc430.py` carries a DOWN-ONLY `NO_ARG` ceiling, and
    `tools/example_args.py` harvests arguments by EXECUTING `example["worked"]`
    with the op wrapped in a recorder — `example["input"]` is deliberately not
    an argument source (see that module's docstring for why). An op with no
    worked snippet is `no_worked_snippet`, i.e. NO_ARG, and fourteen new ones
    would push that census 280 -> 294 through a ceiling that may only fall.

So the snippet is not decoration; it is what makes these ops MEASURABLE on the
frame axis at all.

Run from `docs/srmech/python`:

    python3 ../notes/_rc464_cdr_worked_examples.py

It merges per-key into the committed CURATED dict — it never rebuilds the file
from this list, which is the rc291 (`#T916`) defect on this side.
"""

from __future__ import annotations

import io
import json
import sys
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

_PY_ROOT = Path(__file__).resolve().parents[1] / "python"
sys.path.insert(0, str(_PY_ROOT))

import srmech  # noqa: E402
from srmech import cascade  # noqa: E402

#: A repr longer than this RAISES. Narrowing the expression is the fix.
_MAX = 200


def _ns():
    """The namespace every snippet line is evaluated in — the same imports the
    snippet itself declares, so what ships is what runs."""
    ns = {"__name__": "__worked__"}
    exec(
        "from srmech.cascade import (\n"
        "    cdr_write, cdr_materialize, cdr_read_unbind, cdr_clean, cdr_slots,\n"
        "    cdr_working_block, cdr_carry_block, cdr_couple_working,\n"
        "    cdr_uncouple_working, cdr_carry, cdr_correct, cdr_element,\n"
        "    cdr_element_of, cdr_navigate)\n",
        ns,
    )
    return ns


# Shared fixtures, built once so the fourteen snippets read as one coherent
# session rather than fourteen unrelated constructions. D=256 keeps every
# captured vector repr inside the cap without narrowing what the call shows.
_SETUP = (
    "from srmech.cascade import (\n"
    "    cdr_write, cdr_materialize, cdr_read_unbind, cdr_clean, cdr_slots,\n"
    "    cdr_working_block, cdr_carry_block, cdr_couple_working,\n"
    "    cdr_uncouple_working, cdr_carry, cdr_correct, cdr_element,\n"
    "    cdr_element_of, cdr_navigate)\n"
    "\n"
    "# the declarative field-state of a dim-4 register holding one value.\n"
    "# D / namespace / both OPT flags are None here on purpose: the [class]\n"
    "# contract has no scalar default, and the adapters resolve None at USE\n"
    "# time to 8192 / f'CD{dim}' / False -- the same rule the Python\n"
    "# constructor applies.\n"
    "_, st = cdr_write(0, 'alpha', 4, 256, None, {}, {})\n"
    "slots, book = st['slots'], st['codebook']\n"
)

# (op name, [source lines], why)
ROWS = [
    ("srmech.cascade.cdr_write", [
        "cdr_write(3, 'beta', 4, 256, None, book, slots)[1]['slots']",
        "sorted(cdr_write(3, 'beta', 4, 256, None, book, slots, sign=-1)[1]['codebook'])",
        "cdr_write(9, 'gamma', 4, 256, None, book, slots)",
    ],
     "The mutates pair in both halves: the slot-map gains the assignment, the "
     "codebook gains the minted value vector, and an out-of-range slot RAISES "
     "rather than silently widening the address space."),

    # The WIRE-FORM operand leads deliberately: a slot map crossing JSON /
    # the srmech_mval_t DICT arrives STR-keyed with LIST pairs, and that is
    # the only spelling of a NON-EMPTY register the harvest can bank (an
    # int key and a tuple pair do not survive a JSON round trip). Leading
    # with it keeps the op measurable on the rc430 frame axis instead of
    # BASE_RAISES, and it documents a real contract point -- _cdr_rehydrate
    # normalises both back.
    ("srmech.cascade.cdr_materialize", [
        "len(cdr_materialize(4, 256, None, {}, {'0': ['alpha', 1]}))",
        "cdr_materialize(4, 256, None, book, slots) == cdr_materialize(4, 256, 'CD4', book, slots)",
        "cdr_materialize(4, 256, None, {}, {})",
    ],
     "D/8 bytes out from the STR-keyed wire form -- the value vector is minted "
     "on demand, so an empty codebook is not an empty register; the explicit "
     "namespace agrees with the resolved default; and an empty register RAISES "
     "instead of returning an empty vector, because an empty bundle is not a "
     "value."),

    ("srmech.cascade.cdr_read_unbind", [
        "cdr_read_unbind(0, 4, 256, None, {}, {})",
        "len(cdr_read_unbind(0, 4, 256, None, book, slots))",
        "cdr_read_unbind(0, 4, 256, None, book, slots) == cdr_read_unbind(1, 4, 256, None, book, slots)",
    ],
     "An empty register short-circuits to None; stage 1 otherwise returns a "
     "full-width noisy vector; and two different slots unbind to different "
     "vectors, which is what makes the address do any work."),

    # The short-circuit call leads DELIBERATELY. tools/example_args.py banks
    # the FIRST returning call, and this op's other two calls pass a minted
    # 32-byte vector and a bytes-valued codebook -- neither of which JSON can
    # carry -- so leading with the real chain answer would harvest nothing and
    # leave the op NO_ARG on the rc430 frame axis, against a ceiling that may
    # only fall. `noisy=None` is JSON-carryable and is a real documented case.
    ("srmech.cascade.cdr_clean", [
        "cdr_clean(None, book)",
        "cdr_clean(cdr_read_unbind(0, 4, 256, None, book, slots), book)",
        "cdr_clean(cdr_read_unbind(0, 4, 256, None, book, slots), {})",
    ],
     "The empty-register short-circuit, the chain's real answer, and an empty "
     "codebook -- which recovers nothing rather than guessing, because cleanup "
     "is a nearest-neighbour decision and an empty neighbourhood has no answer."),

    ("srmech.cascade.cdr_slots", [
        "cdr_slots({'0': ('alpha', 1), '3': ('beta', -1)})",
        "cdr_slots(slots) == slots",
        "cdr_slots({})",
    ],
     "The STR-keyed wire form comes back int-keyed, an already-int map is "
     "unchanged, and an empty map is empty -- a reshape, not a validator."),

    ("srmech.cascade.cdr_working_block", [
        "cdr_working_block(16)",
        "cdr_working_block(256)",
        "cdr_working_block(4)",
    ],
     "The Hurwitz cap in one reading: dim 16 and dim 256 have the SAME "
     "eight-slot reversible block, and dim 4 is truncated to what exists. More "
     "slots buy address space, never a longer reversible word."),

    ("srmech.cascade.cdr_carry_block", [
        "cdr_carry_block(16)",
        "len(cdr_carry_block(256))",
        "cdr_carry_block(8)",
    ],
     "The complement of the working block: everything past the reversibility "
     "horizon, growing with dim, and correctly EMPTY at dim 8 where there is "
     "nothing past it."),

    ("srmech.cascade.cdr_couple_working", [
        "cdr_couple_working([1.5, -2.25, 3.0], 16, True)",
        "len(cdr_couple_working([1.0] * 7, 16, True))",
        "cdr_couple_working([1.5], 16, False)",
    ],
     "One reversible word out; seven streams -- the Hurwitz cap -- still bind "
     "at dim 16, because more slots buy address space and not a longer word; "
     "and the GATE fires on a register built for pure addressing, which is a "
     "refusal rather than a silent no-op."),

    ("srmech.cascade.cdr_uncouple_working", [
        "cdr_uncouple_working(cdr_couple_working([1.5, -2.25, 3.0], 16, True), 16, True)",
        "cdr_uncouple_working(cdr_couple_working([2.0, 4.0], 4, True), 4, True)",
        "cdr_uncouple_working([0.0] * 4, 16, False)",
    ],
     "The round trip recovers the streams at dim 16 and again at dim 4 -- where "
     "the cap is three, not seven, because it is read from dim and never "
     "hardcoded -- and the gate fires on this side too, so an OPT layer cannot "
     "be entered through its exit."),

    ("srmech.cascade.cdr_carry", [
        "cdr_carry([1, 0, 1, 1], 16, True)",
        "len(cdr_carry([1] * 11, 16, True, n=4))",
        "cdr_carry([1, 0, 1, 1], 16, False)",
    ],
     "A 7-bit codeword at the default n=3, a 15-bit one at n=4 -- the EC order "
     "is an axis independent of dim and rides as a keyword -- and the gate "
     "fires on a register built for pure addressing."),

    ("srmech.cascade.cdr_correct", [
        "cdr_correct([0, 1, 1, 0, 0, 1, 1], 16, True)['error_position']",
        "cdr_correct([1, 1, 1, 0, 0, 1, 1], 16, True)",
        "cdr_correct([0, 1, 1, 0, 0, 1, 1], 16, False)",
    ],
     "A clean word reports position 0; a single flipped bit is LOCATED and "
     "repaired and the payload recovered; and the gate fires. The located bit "
     "is a Class-K GF(2) flip, computed by XOR."),

    ("srmech.cascade.cdr_element", [
        "cdr_element({}, 4)",
        "cdr_element({0: ('alpha', 1), 3: ('beta', -1)}, 4)",
        "cdr_element({0: ('alpha', 1), 3: ('beta', -1)}, 4) == cdr_element({0: ('zzz', 1), 3: ('qqq', -1)}, 4)",
    ],
     "An empty register is the zero element rather than an error; occupancy "
     "reads as exact Q coefficients in {-1, 0, +1}; and two registers holding "
     "DIFFERENT names at the same signed slots read as the SAME carrier "
     "element -- the keys are orthogonal to the algebra."),

    # The EMPTY-slots operand leads for the same reason cdr_clean's None does:
    # `{'dim': 4, 'slots': {1: ('beta', -1)}}` has an INT key and a TUPLE value,
    # so a JSON round trip returns it as `{'1': ['beta', -1]}` -- a different
    # object -- and the harvest correctly refuses to bank it. Leading with the
    # empty one keeps `other` synthesizable without weakening the row: the
    # occupied operand is still shown, second.
    ("srmech.cascade.cdr_element_of", [
        "cdr_element_of({'dim': 4, 'slots': {}}, 4)",
        "cdr_element_of({'dim': 4, 'slots': {1: ('beta', -1)}}, 4)",
        "cdr_element_of({'dim': 8, 'slots': {}}, 4, verb='add')",
    ],
     "An empty operand reads as the zero element rather than an error; a bare "
     "state dict with occupancy is accepted off the wire; and an unequal rung "
     "RAISES AHEAD of the algebra, with `verb` naming the operation the caller "
     "actually asked for instead of always saying multiply."),

    ("srmech.cascade.cdr_navigate", [
        "sorted(cdr_navigate(1, 4, 256, None, {}, {}, False, False))",
        "cdr_navigate(1, 4, 256, None, book, slots, False, False)['slots']",
        "cdr_navigate(1, 4, 256, None, book, cdr_navigate(1, 4, 256, None, book, slots, False, False)['slots'], False, False)['slots']",
    ],
     "ALL SEVEN fields come back, which is what stops a routed register "
     "silently losing its D, its namespace and both OPT gates; content routes "
     "by the algebra rather than by a rewrite; and navigating twice along the "
     "same direction returns the slot with the sign flipped -- e_j^2 = -1 "
     "recovered as a Class-C sign, an involution that needs no norm."),
]


def _run(src: str, ns) -> str:
    """Evaluate one snippet line and return its REAL repr — or the exception's
    own type-and-message, which is a real captured outcome too and is how the
    three gate/refusal lines above ship an honest `# ->`."""
    buf = io.StringIO()
    try:
        with redirect_stdout(buf), redirect_stderr(buf):
            res = eval(src, ns)  # noqa: S307 — dev-time provenance tool
        rendered = repr(res)
    except Exception as exc:  # noqa: BLE001 — a refusal IS the captured output
        msg = str(exc)
        head = msg.split(".")[0].split(" -- ")[0].strip()
        rendered = f"{type(exc).__name__}: {head[:110]}"
    if len(rendered) > _MAX:
        raise SystemExit(
            f"output is {len(rendered)} chars (> {_MAX}). NARROW THE "
            f"EXPRESSION — truncating would ship a fabricated output.\n"
            f"  {src}\n  {rendered[:120]}...")
    return rendered


def main() -> int:
    print("srmech :", srmech.__file__)
    print("version:", srmech.__version__)
    print("cascade:", cascade.__name__)
    print()

    # The parameter-name `input` map comes from EXECUTING each entry's own
    # `smoke_test_hint`, via the same `gen_tool_docs._build_example` the
    # generator uses. Two nearby sources are WRONG and both were tried:
    #   * `srmech.introspect._tool_docs` is the MERGED output, so once this
    #     script has run once, reading it back hands you THIS SCRIPT'S OWN
    #     curated example and the parameter names are already gone;
    #   * `gen_tool_docs.build_docs()[1]` is no better, because the seed
    #     PRESERVES a committed executed-I/O example verbatim (the rc294 rule
    #     that stops regeneration destroying real captured output), so it
    #     returns the same thing.
    # Measured the hard way: with either of those,
    # tests/test_tool_example_input_schema_rc355.py's down-only
    # `numeric_call_index` residual went 87 -> 101 on a run that had already
    # "fixed" exactly that. `_build_example` re-EXECUTES the hint, so it is the
    # only source that cannot be contaminated by a previous run of this script.
    import sys as _sys
    _sys.path.insert(0, str(_PY_ROOT / "tools"))
    import gen_tool_docs as _gtd
    from srmech.introspect.tool_schema import get_tool_schema, warmup_all
    warmup_all()
    _SCHEMA = {e.name: e for e in get_tool_schema().tools}

    def _seeded_example(name):
        entry = _SCHEMA[name]
        assert entry.smoke_test_hint, f"{name} has no smoke_test_hint to execute"
        ex, verdict = _gtd._build_example(entry)
        assert verdict == "executed", (
            f"{name}: smoke_test_hint did not EXECUTE (verdict {verdict!r}); a "
            f"signature snippet carries no captured output and would fail the "
            f"strict-zero example gate")
        return ex

    probed = {}
    for name, calls, why in ROWS:
        ns = _ns()
        exec(compile(_SETUP, "<setup>", "exec"), ns)
        inp, outp, lines = {}, {}, []
        for i, src in enumerate(calls, start=1):
            rendered = _run(src, ns)
            inp[str(i)] = src
            outp[str(i)] = rendered
            lines.append(src)
            lines.append(f"# -> {rendered}")
        worked = _SETUP + "\n" + "\n".join(lines) + "\n"
        # Prove the shipped snippet RUNS AS ONE PROGRAM, not merely line by
        # line — otherwise a refusal in the middle would silently strand every
        # later line, and its captured `# ->` would document a call that never
        # happens when the snippet is executed the way tools/example_args.py
        # executes it. A refusal is allowed ONLY on the LAST line (the
        # cyclic_group precedent), which is why every row above orders its
        # refusal last and carries at most one.
        check = _ns()
        try:
            exec(compile(worked, f"<worked:{name}>", "exec"), check)
        except Exception as exc:  # noqa: BLE001
            final = calls[-1]
            if not outp[str(len(calls))].startswith(
                    (type(exc).__name__ + ":",)):
                raise SystemExit(
                    f"{name}: the snippet died at a line that is NOT its last, "
                    f"so every later `# ->` documents a call the shipped "
                    f"snippet never reaches. Move the refusal to the end. "
                    f"last line: {final} | raised: {exc!r}")
        # `input` / `output` are taken from the SEEDED example, whose keys are
        # real PARAMETER NAMES (gen_tool_docs executes the ToolEntry's
        # smoke_test_hint and banks the kwargs it used). They are NOT replaced
        # by this script's numeric call indices: `input` is contractually a
        # kwargs map (srmech/introspect/tool_schema.py:28), and
        # tests/test_tool_example_input_schema_rc355.py carries a DOWN-ONLY
        # ceiling on the `numeric_call_index` residual that fourteen more rows
        # would have pushed 87 -> 101. The numeric transcript belongs in
        # `worked`, which is where a multi-call sequence has always lived.
        seeded = _seeded_example(name)
        assert seeded.get("input") and seeded.get("output"), (
            f"{name}: the executed smoke_test_hint produced no input/output")
        assert all(not k.isdigit() for k in seeded["input"]), (
            f"{name}: the seeded input is numeric-keyed, so it is not the "
            f"executed hint - check the source above")
        probed[name] = {"example": {"input": seeded["input"],
                                    "output": seeded["output"],
                                    "worked": worked, "why": why}}
        print(f"OK  {name}  ({len(calls)} calls worked)")

    dest = _PY_ROOT / "srmech" / "introspect" / "_tool_docs_curated.py"
    src_text = dest.read_text(encoding="utf-8")
    ns2 = {}
    exec(compile(src_text, str(dest), "exec"), ns2)
    cur = ns2["CURATED"]

    # MERGE per key — never rebuild the file from ROWS (rc291 `#T916`).
    out_lines = src_text.splitlines(keepends=True)
    for name in sorted(probed):
        assert name in cur, f"{name} has no curated row to merge into"
        merged = dict(cur[name])
        merged.update(probed[name])
        row = (f'    {json.dumps(name)}: '
               f'{json.dumps(merged, sort_keys=True, ensure_ascii=False)},\n')
        hit = [i for i, ln in enumerate(out_lines)
               if ln.startswith(f'    {json.dumps(name)}:')]
        assert len(hit) == 1, (name, len(hit))
        out_lines[hit[0]] = row
    text = "".join(out_lines)
    compile(text, str(dest), "exec")
    dest.write_bytes(text.encode("utf-8"))
    print(f"\nmerged {len(probed)} worked examples into {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
