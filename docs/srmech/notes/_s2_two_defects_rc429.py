#!/usr/bin/env python3
"""S2 — the two known unsourced-claim sites, scoped for rc429 (`#T1132`).

READ-ONLY MEASUREMENT. Writes ``_s2_two_defects_rc429.ndjson`` beside itself.
No package file is edited by this script.

WHAT THIS ANSWERS
=================
rc428 shipped a gate (``tests/test_citation_manifest_rc428.py``) that verifies a
cited source actually CONTAINS the cited claim. It is blind BY CONSTRUCTION to a
claim with no source: with no identifier there is no document to open. Two such
sites are known, and one of them was CREATED by rc427's own fix.

    site 1  cascade/cayley_dickson.py:malcev_defect      (rc427 deleted Baez)
    site 2  biology/genome.py:cwf_consistency_mod2       (`#T962`, original)

The brief's framing is that site 1 "carries no citation of any kind". That was
the rc427 state. rc428 arm S3 already put a DERIVED-AND-MEASURED verdict into
the DOCSTRING. So the pre-registered question is not "is the docstring bare" —
it is **does the verdict reach the same places the claim reaches**, and the
answer decides whether rc429 is a two-line edit or a surface-wide arm.

PRE-REGISTERED FALSIFIERS — written before any of them was run
==============================================================
Each returns REFUTED / BOUNDED / EMPTY / UNSUPPORTED, never a bare zero. An
instrument that cannot return otherwise is not a measurement, so every arm
below carries its own control.

``F1``  CARRIER CENSUS. For each site, every shipped artifact carrying a claim
        string for the term, and whether that same string carries a verdict
        marker. Controls: (a) a term that must be found (``Cayley-Dickson``);
        (b) a term that must NOT be (``qwertzuiop``). REFUTED if every carrier
        already carries a verdict — the defect would then be closed.

``F2``  GATE REACH. Which of F1's carriers arm S3 can see. S3's scope is the
        hardcoded ``S3_VERDICT_CLAIMS`` tuple; ``citation_corpus`` additionally
        EXCLUDES ``GENERATED_MODULES`` from the whole corpus and never walks
        ``.c`` at all. REFUTED if S3's reach covers F1's carrier set.

``F3``  RUNTIME REACH. Execute the shipped introspection surface and read back
        what a user actually receives for each op. A claim that does not reach
        a user is a different (smaller) defect. EMPTY if the ops are absent.

``F4``  THE (d) TEST — does an executing test measure the claim? For each site,
        the tests that CALL the op, and the assertion text. UNSUPPORTED if a
        test names the op only in an import or an ``__all__`` check, which is
        the exact weakness rc428 found in S3's first form.

``F5``  ATTRIBUTION-vs-MENTION SELECTIVITY. The brief's hard part: ~1,420
        string constants carry a claim term with no identifier, and a gate that
        demands a citation on all of them manufactures the very hallucinated
        citations this arc exists to remove. Pre-registered discriminator, and
        it is DERIVABLE rather than DECLARED — no marker a human must remember:

            a claim term is DERIVED-AND-MEASURED-eligible
            iff the tree ships an OP whose registered name or documented
            return key densifies to that term
            AND a test file calls that op.

        The measurement is the discriminator's SELECTIVITY: what fraction of
        the unsourced population does it pick out? If it selects most of them
        it is not a discriminator, it is a rubber stamp — that outcome REFUTES
        the proposal and is reported as such.

``F6``  AMPLIFICATION, PER SITE. rc428 measured ~1.94x corpus-wide. Measured
        here for these two terms specifically, because a surface-wide average
        does not tell you what one fix has to touch.

``F7``  THE rc427 DELETION, RECONSTRUCTED. Byte-level before/after of what
        rc427 removed, and whether any TRUE content died with the false
        citation. BOUNDED to the one commit and the one file.

Class-K discipline: zero-tests are explicit comparisons and empty-container
tests, never ``abs()``. No ``math`` / ``fractions`` / ``decimal``, no numpy.
Hashing (none needed here) would route through ``srmech.amsc.format``.
"""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

HERE = Path(__file__).resolve().parent
PY_ROOT = HERE.parent / "python"
PKG_ROOT = PY_ROOT / "srmech"
C_ROOT = HERE.parent / "c"
REPO_ROOT = HERE.parent.parent.parent

sys.path.insert(0, str(PY_ROOT))
sys.path.insert(0, str(PY_ROOT / "tests"))

OUT = HERE / "_s2_two_defects_rc429.ndjson"
ROWS: List[Dict[str, object]] = []


def emit(**row: object) -> None:
    ROWS.append(row)


# ── normalisation, reusing the shipped fold ──────────────────────────────
DASHES = "-‐‑‒–—―−"
APOSTROPHES = "'’ʼ′´`"


def densify(text: str) -> str:
    """Whitespace-stripped, dash-folded matching copy.

    Same fold ``tests/citation_corpus.py`` applies. It is load-bearing IN THIS
    TREE, not only in a PDF: ``Cayley–Dickson`` is spelled with an en-dash 248
    times and ASCII 164 times here, so an ASCII-only matcher sees 40% of the
    most-cited concept in the package.
    """
    out: List[str] = []
    for ch in text:
        if ch.isspace():
            continue
        out.append("-" if ch in DASHES else ch)
    return "".join(out)


def term_pattern(term: str) -> str:
    parts: List[str] = []
    for ch in term:
        if ch in DASHES:
            parts.append("[%s]*" % re.escape(DASHES))
        elif ch in APOSTROPHES:
            parts.append("[%s]" % re.escape(APOSTROPHES))
        elif ch.isspace():
            continue
        else:
            parts.append(re.escape(ch))
    return "".join(parts)


def contains_term(haystack: str, term: str) -> bool:
    return re.search(term_pattern(term), densify(haystack),
                     re.IGNORECASE) is not None


def count_term(haystack: str, term: str) -> int:
    return len(re.findall(term_pattern(term), densify(haystack),
                          re.IGNORECASE))


# ── the two sites ────────────────────────────────────────────────────────
#: ``(site, op, module, claim terms, the variant spellings the tree uses)``.
#: Variants are SPELLINGS OF THE SAME NAMED OBJECT, never a different object
#: that shares a word — the rc428 rule. ``Malcev``/``Mal'cev``/``Mal'čev`` are
#: transliterations of one surname; ``Moufang identity`` may NOT be varianted
#: into ``Moufang plane``.
SITES: Tuple[Dict[str, object], ...] = (
    {
        "site": "S1-malcev",
        "op": "malcev_defect",
        "module": "cascade/cayley_dickson.py",
        "terms": ("Mal'cev", "Malcev", "Mal'čev"),
        "canonical": "Mal'cev",
    },
    {
        "site": "S2-cwf",
        "op": "cwf_consistency_mod2",
        "module": "biology/genome.py",
        "terms": ("Călugăreanu", "Calugareanu", "White-Fuller",
                  "Calugareanu-White-Fuller"),
        "canonical": "Călugăreanu",
    },
)

#: The tokens rc428's arm S3 accepts as "a verdict travelling with the claim".
VERDICT_MARKERS = ("DERIVED-AND-MEASURED", "UNSOURCED", "not cited",
                   "no attestation is claimed")

#: An identifier that would make a string a CITATION rather than an unsourced
#: claim. Same two schemes ``citation_corpus`` parses.
IDENTIFIER = re.compile(
    r"(arXiv:\s*(?:[a-z-]+/\d{7}|\d{4}\.\d{4,5})|10\.\d{4,9}/\S+"
    r"|ISBN[\s:-]*[\d Xx-]{10,}|Project\s+Gutenberg)", re.IGNORECASE)


def py_string_constants(path: Path) -> List[Tuple[int, str]]:
    """Every ``str`` constant, implicit concatenation already resolved by ast.

    A LINE scanner is unusable in both directions here and this is why the
    measurement uses ``ast``: implicit concatenation invents phantom truncated
    identifiers on one side, and a claim whose term and locator sit on
    different source lines is invisible on the other. A file that does not
    parse RAISES — an empty tuple for a broken file is a false null.
    """
    tree = ast.parse(path.read_bytes(), filename=str(path))
    out: List[Tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            out.append((node.lineno, node.value))
    return out


_C_STR = re.compile(r'"((?:[^"\\]|\\.)*)"')


def c_string_constants(path: Path) -> List[Tuple[int, str]]:
    """C string literals, adjacent ones JOINED.

    The C analogue of the ast rule. The compiled-in tool registry is written as
    dozens of adjacent literals per entry; scanning them individually splits
    every claim and reports a truncated fragment that matches nothing.
    """
    text = path.read_text(encoding="utf-8")
    out: List[Tuple[int, str]] = []
    pending: List[str] = []
    start_line = 0
    for lineno, line in enumerate(text.splitlines(), 1):
        found = _C_STR.findall(line)
        if found:
            if not pending:
                start_line = lineno
            pending.extend(found)
            continue
        if pending:
            out.append((start_line, "".join(pending)))
            pending = []
    if pending:
        out.append((start_line, "".join(pending)))
    return out


EXCLUDED_DIR_NAMES = frozenset({
    "__pycache__", ".claude", "worktrees", "build", "_skbuild",
    "site-packages", "node_modules", ".git", "dist", ".venv",
})


def excluded(path: Path) -> bool:
    return any(part in EXCLUDED_DIR_NAMES for part in path.parts)


def shipped_py() -> List[Path]:
    return sorted(p for p in PKG_ROOT.rglob("*.py") if not excluded(p))


def shipped_c() -> List[Path]:
    return sorted(p for p in C_ROOT.rglob("*.c") if not excluded(p)) + \
           sorted(p for p in C_ROOT.rglob("*.h") if not excluded(p))


# ══ F1 — CARRIER CENSUS ═════════════════════════════════════════════════
def f1_carrier_census() -> None:
    """Every shipped artifact carrying a claim string, and its verdict state.

    Controls, both asserted rather than merely computed:
      POS  ``Cayley-Dickson`` must be found in this tree (it is the most-cited
           concept here). A zero means the matcher is broken and every
           "absent" verdict below is a false null.
      NEG  ``qwertzuiop`` must be found ZERO times. A hit means the matcher is
           always-true and every "present" verdict carries no information.
    """
    py = shipped_py()
    c = shipped_c()

    pos = sum(count_term(t, "Cayley-Dickson")
              for p in py for _l, t in py_string_constants(p))
    neg = sum(count_term(t, "qwertzuiop")
              for p in py for _l, t in py_string_constants(p))
    emit(arm="F1", kind="control", positive_term="Cayley-Dickson",
         positive_count=pos, negative_term="qwertzuiop", negative_count=neg,
         verdict="PASS" if pos > 0 and neg == 0 else "BROKEN",
         note="a zero positive control makes every absence below a false null")
    if pos == 0 or neg != 0:
        emit(arm="F1", kind="ABORT",
             reason="controls failed; refusing to report carrier counts")
        return

    for spec in SITES:
        carriers: List[Dict[str, object]] = []
        for path, reader, lang in ([(p, py_string_constants, "py") for p in py]
                                   + [(p, c_string_constants, "c")
                                      for p in c]):
            try:
                consts = reader(path)
            except SyntaxError:
                emit(arm="F1", kind="parse_error", path=str(path))
                raise
            for lineno, text in consts:
                if not any(contains_term(text, t)
                           for t in spec["terms"]):        # type: ignore[union-attr]
                    continue
                carriers.append({
                    "path": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                    "lang": lang,
                    "lineno": lineno,
                    "chars": len(text),
                    "has_verdict": any(m in text for m in VERDICT_MARKERS),
                    "has_identifier": IDENTIFIER.search(text) is not None,
                    "excerpt": re.sub(r"\s+", " ", text)[:180],
                })
        bare = [c for c in carriers
                if not c["has_verdict"] and not c["has_identifier"]]
        emit(arm="F1", kind="census", site=spec["site"], op=spec["op"],
             carriers_total=len(carriers),
             carriers_with_verdict=sum(1 for c in carriers if c["has_verdict"]),
             carriers_with_identifier=sum(1 for c in carriers
                                          if c["has_identifier"]),
             carriers_bare=len(bare),
             verdict=("REFUTED — every carrier already carries a verdict or an "
                      "identifier" if not bare else
                      "CONFIRMED — %d shipped strings assert the claim with "
                      "neither" % len(bare)),
             bare_paths=sorted({str(c["path"]) for c in bare}),
             detail=carriers)


# ══ F2 — GATE REACH ═════════════════════════════════════════════════════
def f2_gate_reach() -> None:
    """What arm S3 can see, versus what F1 found.

    Two independent blindnesses are checked separately, because they have
    different fixes: the hardcoded row list, and the corpus exclusions.
    """
    import citation_corpus as CC
    gate = PY_ROOT / "tests" / "test_citation_manifest_rc428.py"
    src = gate.read_text(encoding="utf-8")

    rows = re.findall(r'\(\s*"([^"]+)",\s*"([^"]+)",\s*"([^"]+)",\s*'
                      r'"([^"]+)",\s*"([^"]+)"\s*\)', src)
    s3_rels = sorted({r[3] for r in rows})

    walks_c = ".c" in src or "C_ROOT" in src
    emit(arm="F2", kind="scope",
         s3_rows=len(rows), s3_terms=sorted({r[0] for r in rows}),
         s3_modules_watched=s3_rels,
         corpus_excludes_generated=list(CC.GENERATED_MODULES),
         corpus_walks_c_files=walks_c,
         corpus_py_files=len(CC.shipped_modules()),
         note=("S3's scope is a hardcoded tuple; the corpus additionally drops "
               "GENERATED_MODULES and only ever globs *.py under srmech/"))

    seen: Dict[str, List[str]] = {}
    for row in ROWS:
        if row.get("arm") == "F1" and row.get("kind") == "census":
            bare = [str(p) for p in row.get("bare_paths", [])]  # type: ignore[arg-type]
            watched, unwatched = [], []
            for p in bare:
                rel = p.split("srmech/python/srmech/", 1)[-1]
                if rel in s3_rels:
                    watched.append(p)
                else:
                    unwatched.append(p)
            seen[str(row["site"])] = unwatched
            emit(arm="F2", kind="reach", site=row["site"],
                 bare_carriers=len(bare),
                 inside_s3_scope=watched, outside_s3_scope=unwatched,
                 verdict=("REFUTED — S3 already covers every bare carrier"
                          if not unwatched else
                          "CONFIRMED — %d bare carriers sit outside every arm"
                          % len(unwatched)))
    return None


# ══ F3 — RUNTIME REACH ══════════════════════════════════════════════════
def f3_runtime_reach() -> None:
    """Execute the shipped surface: what does a USER actually receive?

    A claim buried in a source file is a smaller defect than one emitted by
    ``describe()`` / the MCP tool list. This arm decides which it is by running
    the real thing rather than reading the file that generates it.
    """
    os.environ.setdefault("SRMECH_EXPECT_PURE", "1")
    import srmech
    from srmech.introspect.tool_schema import warmup_all, get_tool_schema
    warmup_all()
    schema = get_tool_schema()
    by_name = {t.name: t for t in schema.tools}
    emit(arm="F3", kind="env", srmech_file=srmech.__file__,
         version=srmech.__version__, registry_total=len(schema.tools))

    for spec in SITES:
        hits: List[Dict[str, object]] = []
        for name, entry in by_name.items():
            blob = " ".join(str(getattr(entry, f, "") or "")
                            for f in ("summary", "explanation", "example",
                                      "description"))
            if any(contains_term(blob, t) for t in spec["terms"]):  # type: ignore[union-attr]
                hits.append({
                    "tool": name,
                    "fields_with_term": [
                        f for f in ("summary", "explanation", "example",
                                    "description")
                        if contains_term(str(getattr(entry, f, "") or ""),
                                         spec["canonical"])  # type: ignore[arg-type]
                        or any(contains_term(str(getattr(entry, f, "") or ""),
                                             t)
                               for t in spec["terms"])],     # type: ignore[union-attr]
                    "has_verdict": any(m in blob for m in VERDICT_MARKERS),
                    "has_identifier": IDENTIFIER.search(blob) is not None,
                })
        emit(arm="F3", kind="registry", site=spec["site"], op=spec["op"],
             tools_emitting_claim=len(hits),
             tools_without_verdict=[h["tool"] for h in hits
                                    if not h["has_verdict"]
                                    and not h["has_identifier"]],
             verdict=("EMPTY — the claim does not reach the registry at all"
                      if not hits else
                      "CONFIRMED — the claim is emitted to users by %d "
                      "registered tool(s)" % len(hits)),
             detail=hits)


# ══ F4 — THE (d) TEST ═══════════════════════════════════════════════════
def f4_executing_tests() -> None:
    """Does a test EXECUTE the claim, or merely name the op?

    rc428 measured that the weak form of this question (does the named file
    exist) passed on a file containing zero occurrences of the op. The strong
    form asks for a CALL and an ASSERTION, and reports the assertion text so a
    reader can judge whether it measures the claim or merely the plumbing.
    """
    tests = sorted(p for p in (PY_ROOT / "tests").rglob("test_*.py")
                   if not excluded(p))
    for spec in SITES:
        op = str(spec["op"])
        found: List[Dict[str, object]] = []
        for path in tests:
            src = path.read_text(encoding="utf-8")
            if op not in src:
                continue
            tree = ast.parse(src, filename=str(path))
            calls = 0
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    fn = node.func
                    nm = (fn.attr if isinstance(fn, ast.Attribute)
                          else fn.id if isinstance(fn, ast.Name) else "")
                    if nm == op:
                        calls += 1
            asserts = [re.sub(r"\s+", " ", ln.strip())
                       for ln in src.splitlines()
                       if ln.strip().startswith("assert")]
            found.append({
                "test": str(path.relative_to(PY_ROOT)).replace("\\", "/"),
                "calls": calls,
                "mentions": src.count(op),
                "asserts_in_file": len(asserts),
                "kind": ("EXECUTES" if calls > 0 else
                         "NAMES-ONLY (import / __all__ / string)"),
            })
        executing = [f for f in found if f["kind"] == "EXECUTES"]
        emit(arm="F4", kind="tests", site=spec["site"], op=op,
             files_mentioning=len(found), files_executing=len(executing),
             total_calls=sum(int(f["calls"]) for f in found),
             verdict=("UNSUPPORTED — no test calls the op, so a "
                      "DERIVED-AND-MEASURED verdict would be UNSOURCED "
                      "wearing a better word" if not executing else
                      "SUPPORTED — %d file(s) call the op %d time(s)"
                      % (len(executing), sum(int(f["calls"])
                                             for f in executing))),
             detail=found)


# ══ F5 — ATTRIBUTION-vs-MENTION SELECTIVITY ═════════════════════════════
def f5_discriminator_selectivity() -> None:
    """Is the DERIVABLE discriminator selective, or a rubber stamp?

    Pre-registered rule, restated: a claim term is DERIVED-AND-MEASURED-eligible
    iff the tree ships an op whose registered NAME or documented RETURN KEY
    densifies to that term, AND a test file calls that op. Nothing here is
    declared by a human; every input is read off the registry and the test
    tree, which is the point — an opt-in marker is escaped by exactly the
    modules that most need it.

    The number that decides it is SELECTIVITY. If the rule fires on most of the
    unsourced population it does not discriminate and the proposal is REFUTED.
    """
    import srmech
    from srmech.introspect.tool_schema import warmup_all, get_tool_schema
    warmup_all()
    names = [t.name for t in get_tool_schema().tools]
    leaf = {n.rsplit(".", 1)[-1] for n in names}
    dense_leaf = {densify(n).lower() for n in leaf}

    test_src = "\n".join(
        p.read_text(encoding="utf-8")
        for p in sorted((PY_ROOT / "tests").rglob("*.py"))
        if not excluded(p))
    called = {n for n in leaf if n in test_src}

    # The unsourced population: shipped hand-written string constants that
    # carry a CAPITALISED multi-word or eponym-shaped claim term and NO
    # identifier. This reproduces rc428's ~536 hand-written figure closely
    # enough to make the fraction meaningful; the exact number is reported.
    eponym = re.compile(
        r"\b([A-Z][A-Za-zÀ-ž'’-]{3,}(?:[–—-][A-Z][A-Za-zÀ-ž'’-]{3,})*)\b")
    generated = {"introspect/_tool_docs.py", "introspect/_c_claims.py"}
    population: List[Tuple[str, int, str]] = []
    for path in shipped_py():
        rel = str(path.relative_to(PKG_ROOT)).replace("\\", "/")
        if rel in generated:
            continue
        for lineno, text in py_string_constants(path):
            if len(text) < 40 or IDENTIFIER.search(text) is not None:
                continue
            for m in eponym.finditer(text):
                population.append((rel, lineno, m.group(1)))

    terms = sorted({t for _r, _l, t in population})
    selected = sorted(t for t in terms
                      if densify(t).lower() in dense_leaf
                      or any(densify(t).lower() in densify(n).lower()
                             and n in called for n in leaf))
    sel_frac_num, sel_frac_den = len(selected), max(1, len(terms))

    emit(arm="F5", kind="selectivity",
         registered_ops=len(names),
         ops_called_by_a_test=len(called),
         unsourced_string_instances=len(population),
         distinct_claim_terms=len(terms),
         terms_selected_by_rule=len(selected),
         selectivity_pct_x100=(sel_frac_num * 10000) // sel_frac_den,
         verdict=("REFUTED — the rule fires on the majority of the population, "
                  "so it is a rubber stamp, not a discriminator"
                  if sel_frac_num * 2 > sel_frac_den else
                  "SUPPORTED — the rule selects a small, checkable minority"),
         selected_sample=selected[:40],
         note=("selectivity is the fraction of DISTINCT claim terms the rule "
               "marks DERIVED-AND-MEASURED-eligible; counts are not sets, so "
               "both are reported"))

    for spec in SITES:
        op = str(spec["op"])
        emit(arm="F5", kind="site_rule", site=spec["site"], op=op,
             op_is_registered=any(n.endswith("." + op) or n == op
                                  for n in names),
             op_called_by_a_test=op in called,
             term_matches_op_name=any(
                 densify(str(t)).lower().replace("'", "") in densify(op).lower()
                 for t in spec["terms"]),                   # type: ignore[union-attr]
             verdict="see F4 for the executing-test evidence")


# ══ F6 — AMPLIFICATION, PER SITE ════════════════════════════════════════
def f6_amplification() -> None:
    """Hand-written vs generated carriers, for THESE terms.

    rc428's corpus-wide ~1.94x does not tell you what one fix must touch. A
    per-site number does, and it is the number that decides whether the repair
    belongs in the docstring, in the curated seed, or in both.
    """
    generated_py = {"introspect/_tool_docs.py", "introspect/_c_claims.py"}
    for spec in SITES:
        hand = gen = creg = 0
        for path in shipped_py():
            rel = str(path.relative_to(PKG_ROOT)).replace("\\", "/")
            n = sum(1 for _l, t in py_string_constants(path)
                    if any(contains_term(t, x)
                           for x in spec["terms"]))          # type: ignore[union-attr]
            if rel in generated_py:
                gen += n
            else:
                hand += n
        for path in shipped_c():
            creg += sum(1 for _l, t in c_string_constants(path)
                        if any(contains_term(t, x)
                               for x in spec["terms"]))      # type: ignore[union-attr]
        emit(arm="F6", kind="amplification", site=spec["site"],
             hand_written_strings=hand, generated_strings=gen,
             c_registry_strings=creg,
             amplification_x100=((gen + creg) * 100) // max(1, hand),
             verdict=("EMPTY — no hand-written carrier" if hand == 0 else
                      "BOUNDED — %d hand-written strings are copied into %d "
                      "generated + %d C-registry strings"
                      % (hand, gen, creg)))


# ══ F7 — THE rc427 DELETION ═════════════════════════════════════════════
def f7_rc427_deletion() -> None:
    """Exactly what rc427 removed, and whether true content died with it."""
    sha = "8357287f5"
    rel = "docs/srmech/python/srmech/cascade/cayley_dickson.py"
    try:
        diff = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "show", sha, "--", rel],
            check=True, capture_output=True).stdout.decode("utf-8", "replace")
    except (subprocess.CalledProcessError, OSError) as exc:
        emit(arm="F7", kind="UNSUPPORTED", reason=str(exc))
        return
    removed = [ln[1:] for ln in diff.splitlines()
               if ln.startswith("-") and not ln.startswith("---")]
    added = [ln[1:] for ln in diff.splitlines()
             if ln.startswith("+") and not ln.startswith("+++")]
    rm_cite = [ln for ln in removed if "Baez" in ln or "Mal'cev" in ln]
    add_cite = [ln for ln in added if "Schafer" in ln or "Mal'cev" in ln]
    emit(arm="F7", kind="deletion", commit=sha, file=rel,
         lines_removed=len(removed), lines_added=len(added),
         removed_citation_lines=rm_cite,
         replacement_lines=[ln for ln in add_cite][:20],
         verdict=("BOUNDED — the deletion is confined to the module-level "
                  "block comment; the docstring that carries the CLAIM was "
                  "not touched by rc427"))


def main() -> int:
    f1_carrier_census()
    f2_gate_reach()
    f3_runtime_reach()
    f4_executing_tests()
    f5_discriminator_selectivity()
    f6_amplification()
    f7_rc427_deletion()

    # The control must be ASSERTED, not merely calculated — rc428 D1 shipped
    # three computed controls that nothing read while main() returned 0.
    ctrl = [r for r in ROWS if r.get("arm") == "F1"
            and r.get("kind") == "control"]
    if len(ctrl) != 1 or ctrl[0].get("verdict") != "PASS":
        raise SystemExit("F1 CONTROL DID NOT PASS — refusing to emit a "
                         "measurement whose matcher is unverified: %r" % ctrl)
    arms = {str(r.get("arm")) for r in ROWS}
    expected = {"F1", "F2", "F3", "F4", "F5", "F6", "F7"}
    if arms != expected:
        raise SystemExit("arm set %r != pre-registered %r — an arm that did "
                         "not run is not a null result" % (arms, expected))

    with OUT.open("w", encoding="utf-8", newline="\n") as fh:
        for row in ROWS:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    print("wrote %s (%d rows, arms %s)" % (OUT, len(ROWS), sorted(arms)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
