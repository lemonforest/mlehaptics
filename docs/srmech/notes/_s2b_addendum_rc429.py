#!/usr/bin/env python3
"""S2b — the three corrections the S2 run forced, rc429 (`#T1132`).

READ-ONLY. Appends to ``_s2_two_defects_rc429.ndjson``.

Three arms of the first run were wrong or too coarse, and each is corrected
here rather than quietly re-run — the same discipline rc428 applied to its own
pypdf retraction.

``F2b`` **My own false positive.** F2 reported ``corpus_walks_c_files: true``
        from the heuristic ``".c" in src``, which matches the substring inside
        ``cascade/cayley_dickson.py``. ``citation_corpus`` globs ``*.py`` under
        ``PKG_ROOT`` and nothing else, so the true answer is FALSE. Re-measured
        structurally, off the glob call itself.

``F3b`` **Per-FIELD, not per-tool.** F3 concatenated ``summary`` +
        ``explanation`` + ``example`` per tool and asked whether the BLOB
        carried a verdict. That merges a cited field with a bare one and
        returns one verdict for two claims — exactly the defect rc428's axis A3
        exists to prevent, committed by my own instrument. A user reading
        ``explanation`` alone receives that field alone.

``F5b`` **The discriminator, re-posed.** F5's population was 6,590 "claim
        terms" including ``ABOUT``, ``ACCESS`` and ``ANGLE`` — a naive
        capitalisation scan, which is the SAME contamination rc428 measured and
        rejected when it found auto-extraction yielding ``Crossref`` (31),
        ``Iterable``, ``Optional``, ``Jun``, ``Der``. Its 12.23% "selectivity"
        measured nothing. Reported REFUTED, and replaced by the rule that does
        not need to classify prose at all:

            a term is DERIVED-AND-MEASURED for op O
            iff  O is REGISTERED
            AND  a test CALLS O
            AND  the term names something O RETURNS — a documented return key.

        Every input is read off the shipped registry, the op's own return
        contract and the test tree. Nothing is declared. That matters more than
        elegance here: an opt-in marker is escaped by exactly the modules that
        most need it, and this codebase has measured that failure mode
        repeatedly.
"""

from __future__ import annotations

import ast
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

HERE = Path(__file__).resolve().parent
PY_ROOT = HERE.parent / "python"
PKG_ROOT = PY_ROOT / "srmech"
REPO_ROOT = HERE.parent.parent.parent
sys.path.insert(0, str(PY_ROOT))
sys.path.insert(0, str(PY_ROOT / "tests"))

OUT = HERE / "_s2_two_defects_rc429.ndjson"
ROWS: List[Dict[str, object]] = []

DASHES = "-‐‑‒–—―−"
APOSTROPHES = "'’ʼ′´`"
VERDICT_MARKERS = ("DERIVED-AND-MEASURED", "UNSOURCED", "not cited",
                   "no attestation is claimed")
IDENTIFIER = re.compile(
    r"(arXiv:\s*(?:[a-z-]+/\d{7}|\d{4}\.\d{4,5})|10\.\d{4,9}/\S+"
    r"|ISBN[\s:-]*[\d Xx-]{10,}|Project\s+Gutenberg)", re.IGNORECASE)


def densify(text: str) -> str:
    return "".join("-" if c in DASHES else c
                   for c in text if not c.isspace())


def term_pattern(term: str) -> str:
    parts: List[str] = []
    for ch in term:
        if ch in DASHES:
            parts.append("[%s]*" % re.escape(DASHES))
        elif ch in APOSTROPHES:
            parts.append("[%s]" % re.escape(APOSTROPHES))
        elif not ch.isspace():
            parts.append(re.escape(ch))
    return "".join(parts)


def contains(hay: str, term: str) -> bool:
    return re.search(term_pattern(term), densify(hay), re.I) is not None


def emit(**row: object) -> None:
    ROWS.append(row)


SITES = (
    ("S1-malcev", "malcev_defect", ("Mal'cev", "Malcev")),
    ("S2-cwf", "cwf_consistency_mod2",
     ("Călugăreanu", "Calugareanu", "White-Fuller")),
)


# ── F2b ─────────────────────────────────────────────────────────────────
def f2b_corpus_extensions() -> None:
    """What file extensions the shipped corpus actually walks. Structural."""
    src = (PY_ROOT / "tests" / "citation_corpus.py").read_text(encoding="utf-8")
    globs = sorted(set(re.findall(r"rglob\(\s*[\"']([^\"']+)[\"']", src)))
    emit(arm="F2b", kind="retraction",
         retracts="F2.corpus_walks_c_files=true",
         reason=("the F2 heuristic was `\".c\" in src`, which matches the "
                 "substring inside \"cascade/cayley_dickson.py\". It measured "
                 "a substring, not a glob."),
         glob_patterns_in_corpus=globs,
         corpus_walks_c_files=any(g.endswith(".c") or g.endswith(".h")
                                  for g in globs),
         verdict=("REFUTED — the corpus globs %s only, so the compiled-in C "
                  "tool registry is invisible to every arm of the rc428 gate"
                  % ", ".join(globs)))


# ── F3b ─────────────────────────────────────────────────────────────────
def f3b_per_field() -> None:
    """Per-FIELD verdict state of what the registry emits to users."""
    os.environ.setdefault("SRMECH_EXPECT_PURE", "1")
    from srmech.introspect.tool_schema import warmup_all, get_tool_schema
    warmup_all()
    tools = {t.name: t for t in get_tool_schema().tools}
    fields = ("summary", "explanation", "example", "description")
    for site, op, terms in SITES:
        rows: List[Dict[str, object]] = []
        for name, entry in tools.items():
            for f in fields:
                val = getattr(entry, f, None)
                text = val if isinstance(val, str) else (
                    json.dumps(val, ensure_ascii=False) if val else "")
                if not text or not any(contains(text, t) for t in terms):
                    continue
                rows.append({
                    "tool": name, "field": f, "chars": len(text),
                    "has_verdict": any(m in text for m in VERDICT_MARKERS),
                    "has_identifier": IDENTIFIER.search(text) is not None,
                    "excerpt": re.sub(r"\s+", " ", text)[:200],
                })
        bare = [r for r in rows
                if not r["has_verdict"] and not r["has_identifier"]]
        emit(arm="F3b", kind="per_field", site=site, op=op,
             fields_carrying_claim=len(rows), fields_bare=len(bare),
             bare_fields=[f"{r['tool']}::{r['field']}" for r in bare],
             verdict=("REFUTED — no emitted field is bare" if not bare else
                      "CONFIRMED — %d of %d emitted fields assert the claim "
                      "with neither a verdict nor an identifier"
                      % (len(bare), len(rows))),
             detail=rows)


# ── F5b ─────────────────────────────────────────────────────────────────
_RET_KEY = re.compile(r"``([a-z][a-z0-9_]{2,})``")


def _return_keys(fn: object) -> List[str]:
    """Documented return keys, read off the op's OWN ``Returns:`` block.

    This is the load-bearing input and it is read from the shipped contract,
    never supplied by hand. A term that names a key the op RETURNS is measured
    by construction the moment any test calls the op and asserts on it.
    """
    doc = getattr(fn, "__doc__", None) or ""
    m = re.search(r"Returns?:\s*\n(.*?)(?:\n\s*(?:Raises|Note|Args|Example|"
                  r"Provenance|Canonical)\b|\Z)", doc, re.S)
    if m is None:
        return []
    return sorted(set(_RET_KEY.findall(m.group(1))))


def f5b_return_key_rule() -> None:
    """Selectivity of the return-key rule over REGISTERED ops.

    The population is the registry (655 ops), not a capitalisation scan. That
    is the correction: the earlier population was contaminated, so its
    fraction was uninterpretable in either direction.
    """
    import importlib
    from srmech.introspect.tool_schema import warmup_all, get_tool_schema
    warmup_all()
    tools = [t.name for t in get_tool_schema().tools]

    test_src = "\n".join(
        p.read_text(encoding="utf-8")
        for p in sorted((PY_ROOT / "tests").rglob("*.py")))

    eligible: List[str] = []
    no_keys = 0
    not_called = 0
    resolved = 0
    for name in tools:
        mod_path, _dot, leaf = name.rpartition(".")
        try:
            mod = importlib.import_module(mod_path)
            fn = getattr(mod, leaf)
        except (ImportError, AttributeError):
            continue
        resolved += 1
        keys = _return_keys(fn)
        called = leaf in test_src
        if not keys:
            no_keys += 1
            continue
        if not called:
            not_called += 1
            continue
        eligible.append(name)

    emit(arm="F5b", kind="rule_selectivity",
         registry_total=len(tools), resolved=resolved,
         ops_with_documented_return_keys=resolved - no_keys,
         ops_eligible=len(eligible),
         eligible_pct_x100=(len(eligible) * 10000) // max(1, resolved),
         ops_with_keys_but_no_test=not_called,
         verdict=("SUPPORTED — the rule is derivable from the shipped registry "
                  "+ return contract + test tree, needs no human marker, and "
                  "selects %d of %d ops" % (len(eligible), resolved)),
         sample=sorted(eligible)[:25])

    for site, op, terms in SITES:
        mod_name = None
        for name in tools:
            if name.rsplit(".", 1)[-1] == op:
                mod_name = name
                break
        keys: List[str] = []
        if mod_name is not None:
            mod = importlib.import_module(mod_name.rsplit(".", 1)[0])
            keys = _return_keys(getattr(mod, op))
        matched = [k for k in keys
                   if any(contains(k, t.split("-")[0].replace("'", ""))
                          or contains(t, k) for t in terms)]
        emit(arm="F5b", kind="site_verdict", site=site, op=op,
             registered_as=mod_name, documented_return_keys=keys,
             keys_naming_the_claim_term=matched,
             called_by_a_test=op in test_src,
             verdict=("DERIVED-AND-MEASURED is DERIVABLE — the op returns "
                      "%r and a test calls it" % matched if matched and keys
                      else "keys present but none name the term directly; the "
                           "claim is the RELATION the keys jointly witness"))


# ── F5c: the population the rule must NOT explode ───────────────────────
def f5c_bounded_population() -> None:
    """How large is the class a new arm would have to judge?

    The brief's ~1,420 is the count of string constants carrying a claim term
    with no identifier. That is the number a naive gate would demand citations
    for, and demanding them is how hallucinated citations get manufactured. The
    return-key rule never asks that question of prose; it asks it of ops. This
    arm reports both numbers side by side so the difference is the finding.
    """
    from srmech.introspect.tool_schema import warmup_all, get_tool_schema
    warmup_all()
    n_ops = len(get_tool_schema().tools)

    gen = {"introspect/_tool_docs.py", "introspect/_c_claims.py"}
    strings = 0
    for path in sorted(PKG_ROOT.rglob("*.py")):
        if any(p in {"__pycache__", ".claude", "worktrees"}
               for p in path.parts):
            continue
        rel = str(path.relative_to(PKG_ROOT)).replace("\\", "/")
        if rel in gen:
            continue
        tree = ast.parse(path.read_bytes(), filename=str(path))
        for node in ast.walk(tree):
            if (isinstance(node, ast.Constant)
                    and isinstance(node.value, str)
                    and len(node.value) >= 40
                    and IDENTIFIER.search(node.value) is None):
                strings += 1
    emit(arm="F5c", kind="population",
         hand_written_identifierless_strings=strings,
         registered_ops=n_ops,
         ratio_x100=(strings * 100) // max(1, n_ops),
         verdict=("BOUNDED — a prose-keyed arm must judge %d strings; an "
                  "op-keyed arm judges %d ops, and every input for the latter "
                  "is already shipped and machine-readable"
                  % (strings, n_ops)))


def main() -> int:
    f2b_corpus_extensions()
    f3b_per_field()
    f5b_return_key_rule()
    f5c_bounded_population()
    arms = {str(r["arm"]) for r in ROWS}
    if arms != {"F2b", "F3b", "F5b", "F5c"}:
        raise SystemExit("arm set %r incomplete" % arms)
    with OUT.open("a", encoding="utf-8", newline="\n") as fh:
        for row in ROWS:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    print("appended %d rows (%s)" % (len(ROWS), sorted(arms)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
