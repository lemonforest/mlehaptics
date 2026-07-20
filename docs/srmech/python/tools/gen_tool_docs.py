#!/usr/bin/env python3
"""gen_tool_docs.py — GENERATE the introspection docs floor (rc240, #838).

Emits ``srmech/amsc/_tool_docs.py`` — a generated literal module holding
``TOOL_DOCS: dict[name -> {"explanation": str, "example": dict}]`` — the
auto-seeded EXPLANATION (from each op's docstring) + EXAMPLE (executed where
safe, else an honest signature usage-snippet) for every registered tool.

Curation-preserving: hand-written high-quality entries live in the sibling
``_tool_docs_curated.py`` (``CURATED`` dict); this generator merges them OVER
the auto-seed so regeneration never clobbers curation. Byte-deterministic
(sorted keys) so a codegen-idempotence test can pin drift.

Run:  python tools/gen_tool_docs.py   (from docs/srmech/python)
The auto-seed NEVER fabricates an output — if an op cannot be safely executed
its example is a ``{"call": "..."}`` usage snippet keyed off the signature.

**The un-rederivable-prose guard (rc291, #916).** The merge above only
protects text that lives in ``_tool_docs_curated.py``. Between rc274 and
rc290 twenty genome/plasmid/text explanations were hand-written straight
into the GENERATED ``_tool_docs.py`` instead, so every regeneration
silently replaced four rcs of curation — including native-dispatch notes
and the rc280 quadratic-fix explanation — with a short docstring seed.
That is live damage, because the standing ripple gate says "regenerate
_tool_docs.py".

So before writing, this generator compares the committed file against the
freshly-computed auto-seed. Any field it finds that is NOT in ``CURATED``
and NOT re-derivable from the current docstring is prose it would destroy;
it refuses to write and names the keys. The author then either moves the
text into ``_tool_docs_curated.py`` (the fix, when it is curation) or
re-runs with ``--accept-seed-drift`` (when a docstring legitimately
changed). Silent loss is no longer reachable.
"""

from __future__ import annotations

import io
import json
import importlib
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# ── explanation extraction ────────────────────────────────────────────

_MAX_EXPLANATION = 320


def _clean_doc(doc: Optional[str]) -> Optional[str]:
    """First paragraph of a docstring, whitespace-collapsed, capped. The
    'what/when' hint beyond the one-line summary. None if no docstring."""
    if not doc:
        return None
    # first blank-line-delimited paragraph
    para_lines = []
    for line in doc.strip().splitlines():
        if line.strip() == "":
            if para_lines:
                break
            continue
        para_lines.append(line.strip())
    para = " ".join(para_lines).strip()
    if not para:
        return None
    para = " ".join(para.split())  # collapse internal runs of whitespace
    if len(para) > _MAX_EXPLANATION:
        # cut at a sentence boundary <= cap when possible
        cut = para.rfind(". ", 0, _MAX_EXPLANATION)
        para = (para[: cut + 1] if cut > 40 else para[:_MAX_EXPLANATION].rstrip()) + " …"
    return para


def _resolve_callable(name: str) -> Optional[Any]:
    module, _, attr = name.rpartition(".")
    try:
        m = importlib.import_module(module)
        return getattr(m, attr)
    except Exception:
        return None


# ── example synthesis ─────────────────────────────────────────────────

def _synth_arg(type_str: str) -> Tuple[bool, Any]:
    """A trivially-safe sample value for a scalar/list parameter type, or
    (False, None) if the type is a carrier / opaque / not auto-synthesizable."""
    t = (type_str or "").strip().lower()
    table = {
        "int": (True, 3),
        "float": (True, 1.0),
        "bool": (True, True),
        "str": (True, "abc"),
        "bytes": (True, b"abc"),
        "list[int]": (True, [1, 2, 3]),
        "list[float]": (True, [1.0, 2.0, 3.0]),
        "list[str]": (True, ["a", "b"]),
        "list[bytes]": (True, [b"a", b"b"]),
        "tuple[int, int]": (True, (3, 4)),
    }
    return table.get(t, (False, None))


def _repr_short(v: Any) -> str:
    r = repr(v)
    return r if len(r) <= 200 else r[:197] + "..."


def _signature_snippet(name: str, params, returns) -> Dict[str, Any]:
    args = ", ".join(f"{p.name}=<{p.type}>" for p in params)
    ret = f" -> {returns.type}" if returns is not None else ""
    return {"call": f"{name.rpartition('.')[2]}({args}){ret}"}


def _build_example(entry) -> Dict[str, Any]:
    """Real executed input->output where safe; else an honest usage snippet."""
    fn = _resolve_callable(entry.name)
    # 1) smoke_test_hint gives an attested-safe input — execute it.
    if fn is not None and entry.smoke_test_hint:
        try:
            kwargs = {k: eval(v) if isinstance(v, str) else v  # noqa: S307 dev tool
                      for k, v in entry.smoke_test_hint.items()}
            buf = io.StringIO()
            with redirect_stdout(buf), redirect_stderr(buf):
                out = fn(**kwargs)
            return {"input": {k: _repr_short(v) for k, v in kwargs.items()},
                    "output": _repr_short(out)}
        except Exception:
            pass
    # 2) all-scalar params → synthesize + execute.
    if fn is not None and entry.parameters and entry.mcp_callable:
        synth = {}
        ok = True
        for p in entry.parameters:
            if not p.required:
                continue
            good, val = _synth_arg(p.type)
            if not good:
                ok = False
                break
            synth[p.name] = val
        if ok and synth:
            try:
                buf = io.StringIO()
                with redirect_stdout(buf), redirect_stderr(buf):
                    out = fn(**synth)
                return {"input": {k: _repr_short(v) for k, v in synth.items()},
                        "output": _repr_short(out)}
            except Exception:
                pass
    # 3) honest signature snippet (no fabricated output).
    return _signature_snippet(entry.name, entry.parameters, entry.returns)


# ── emit ──────────────────────────────────────────────────────────────

def build_docs() -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]],
                          Dict[str, Dict[str, Any]]]:
    """``(merged, seed, curated)``.

    ``seed`` is the pure auto-seed BEFORE curation is merged over it — the
    guard in :func:`unrederivable_fields` needs it to answer "could this
    generator have produced the text now on disk?".
    """
    import sys
    python_dir = Path(__file__).resolve().parent.parent
    if str(python_dir) not in sys.path:
        sys.path.insert(0, str(python_dir))
    import srmech  # noqa: F401
    from srmech.amsc.tool_schema import get_tool_schema, warmup_all
    warmup_all()

    try:
        from srmech.amsc._tool_docs_curated import CURATED
    except Exception:
        CURATED = {}

    docs: Dict[str, Dict[str, Any]] = {}
    seed: Dict[str, Dict[str, Any]] = {}
    for t in get_tool_schema().tools:
        fn = _resolve_callable(t.name)
        expl = _clean_doc(getattr(fn, "__doc__", None)) if fn is not None else None
        entry: Dict[str, Any] = {}
        if expl:
            entry["explanation"] = expl
        # A {"call": ...} example is MECHANICALLY derivable from the parameters,
        # so it must ALWAYS be re-derived — never seeded from t.example.
        # t.example is loaded FROM the generated _tool_docs.py (tool_schema.py
        # imports TOOL_DOCS at line 313), so preferring it closes a loop: the
        # generator reads its own output as authoritative and _build_example
        # becomes unreachable for every op that already has an entry. A renamed
        # parameter can then NEVER reach its example. That is how rc290's
        # the_one -> coupling rename left 49 call signatures advertising a
        # kwarg that raises TypeError.
        # Executed-I/O examples ({"input"/"output"}) are NOT derivable — keep those.
        derived = _build_example(t)
        if t.example and set(t.example) != {"call"}:
            ex = t.example          # executed I/O — not re-derivable, preserve
        else:
            ex = derived or t.example
        if ex:
            entry["example"] = ex
        if entry:
            seed[t.name] = dict(entry)
        cur = CURATED.get(t.name)
        if cur:
            entry.update(cur)  # curation wins
        if entry:
            docs[t.name] = entry
    return docs, seed, dict(CURATED)


# ── the un-rederivable-prose guard (rc291, #916) ──────────────────────

def load_committed(path: Path) -> Dict[str, Dict[str, Any]]:
    """``TOOL_DOCS`` from the committed generated module, imported as DATA.

    Imported rather than text-compared on purpose: the committed file has
    historically carried ``\\uXXXX``-escaped prose while this generator emits
    literal UTF-8, and that difference is representation, not content. The
    guard must not fire on it.
    """
    if not path.exists():
        return {}
    import importlib.util
    spec = importlib.util.spec_from_file_location("_tool_docs_committed", path)
    if spec is None or spec.loader is None:
        return {}
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return dict(getattr(mod, "TOOL_DOCS", {}))


def unrederivable_fields(
    committed: Dict[str, Dict[str, Any]],
    seed: Dict[str, Dict[str, Any]],
    curated: Dict[str, Dict[str, Any]],
) -> Dict[str, list]:
    """``{tool_name: [field, ...]}`` for every committed field this generator
    can neither re-derive from a docstring nor read back out of ``CURATED``.

    A non-empty result means regeneration would DESTROY text — the rc274→rc290
    defect. Empty is the healthy state and the round-trip test pins it.
    """
    lost: Dict[str, list] = {}
    for name, entry in committed.items():
        cur = curated.get(name, {})
        sed = seed.get(name, {})
        gone = sorted(
            field for field, value in entry.items()
            if cur.get(field, sed.get(field)) != value
        )
        if gone:
            lost[name] = gone
    return lost


def render(docs: Dict[str, Dict[str, Any]]) -> str:
    lines = [
        '"""_tool_docs.py — GENERATED by tools/gen_tool_docs.py. DO NOT EDIT.',
        "",
        "The rc240 (#838) introspection docs floor: per-tool EXPLANATION",
        "(docstring-seeded) + EXAMPLE (executed input->output where safe, else an",
        "honest signature usage-snippet). Hand-curation lives in",
        "_tool_docs_curated.py (CURATED) and is merged OVER this at generation.",
        "Merged into ToolEntry.explanation/.example at registration, so it flows",
        "through get_tool_schema() -> the C tool registry + tool_schema_sha256.",
        "",
        "TO IMPROVE AN EXPLANATION, EDIT _tool_docs_curated.py, NOT THIS FILE.",
        "Text written here is destroyed by the next generator run — that is what",
        "happened to twenty genome/plasmid/text explanations between rc274 and",
        "rc290 (rc291 migrated them). CURATED is merged over the auto-seed and",
        "therefore survives. Since rc291 the generator refuses to write rather",
        'than clobber prose it cannot re-derive, so this is caught, not silent."""',
        "",
        "from __future__ import annotations",
        "",
        "from typing import Any, Dict",
        "",
        "TOOL_DOCS: Dict[str, Dict[str, Any]] = {",
    ]
    for name in sorted(docs):
        payload = json.dumps(docs[name], sort_keys=True, ensure_ascii=False)
        lines.append(f"    {json.dumps(name)}: {payload},")
    lines.append("}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    import sys
    accept_drift = "--accept-seed-drift" in sys.argv[1:]
    here = Path(__file__).resolve().parent
    out_path = here.parent / "srmech" / "amsc" / "_tool_docs.py"
    docs, seed, curated = build_docs()

    lost = unrederivable_fields(load_committed(out_path), seed, curated)
    if lost and not accept_drift:
        n = sum(len(v) for v in lost.values())
        print(f"REFUSING TO WRITE {out_path}", file=sys.stderr)
        print(f"  {n} field(s) across {len(lost)} tool(s) would be DESTROYED — "
              f"they are neither in _tool_docs_curated.py nor re-derivable "
              f"from the current docstring:", file=sys.stderr)
        for name in sorted(lost):
            print(f"    {name}: {', '.join(lost[name])}", file=sys.stderr)
        print("  If this is hand-written curation (the usual cause): move it "
              "into srmech/amsc/_tool_docs_curated.py, which IS merged over "
              "the auto-seed and therefore survives.", file=sys.stderr)
        print("  If a docstring legitimately changed and the old seed is "
              "simply stale: re-run with --accept-seed-drift.", file=sys.stderr)
        raise SystemExit(1)

    out_path.write_text(render(docs), encoding="utf-8", newline="\n")
    n_expl = sum(1 for d in docs.values() if "explanation" in d)
    n_ex = sum(1 for d in docs.values() if "example" in d)
    n_exec = sum(1 for d in docs.values()
                 if d.get("example", {}).get("output") is not None)
    print(f"wrote {out_path} — {len(docs)} tools, "
          f"{n_expl} explanations, {n_ex} examples ({n_exec} executed I/O)")


if __name__ == "__main__":
    main()
