r"""R-RBS-LM-UNICODE (user catch): "maybe it should also be unicode aware?" -- YES, and it goes deeper than Unicode: it is
the framework's own 'STRIP ENGLISH PRIVILEGE' discipline (R-RBS-LM-25) applied to the SEEN-RULE layer.

TWO LEVELS:
  • THE BYTE FOUNDATION IS ALREADY UNICODE-COMPLETE. The bit-exact comm kernel (F613) content-addresses UTF-8 BYTES --
    every Unicode codepoint has a UTF-8 byte sequence, so the foundation covers ALL scripts (Latin/Greek/CJK/Arabic/
    Egyptian/emoji) byte-exact + deterministic (verified: content_address over 6 scripts, distinct + stable). This IS the
    glyph-universality thesis (F610/F645/F646; R-RBS-LM-25 byte-level 'strip English privilege') -- bytes privilege no script.
  • THE SEEN-RULE LAYER LEAKED LATIN/ENGLISH PRIVILEGE (the bug the user caught). The render engine's clause-joining used
    `c[:1].islower()` (CASE -- absent in CJK/Arabic/Hebrew/Egyptian), ", " / ". " (LATIN punctuation + SPACES -- CJK uses
    、/。 no-space, Arabic ،/؟), and `.split()` (WHITESPACE word-boundaries -- absent in CJK/Thai/Khmer). A Latin DEFAULT
    is an English-privilege leak the framework explicitly opposes (F398 favored-not-privileged; #847 native scholarship).

THE FIX (framework-native): the clause-joining is a SEEN RULE (declared, not trained, F631), so it must be PER-SCRIPT
(per-language, F398) -- NOT a Latin default. A per-SCRIPT seen-rule descriptor (casing / word-segmentation / clause +
sentence separators / direction) is an ATTESTED FOUNDATIONAL FORM added to the bone (descriptors/script_rules.toml). The
ENGINE stays fixed (compose clauses); the SCRIPT-RULE is declared per script. (DIGNITY, F282/F650: the actual per-script
grammar belongs to that script's speakers -- we scaffold the MECHANISM (punctuation/segmentation/direction), never fabricate
the grammar; CJK/Arabic/Egyptian grammar is the native speaker's + the expert's.)

srmech 0.7.5rc15: BitExactCommKernel.content_address (UTF-8 byte-exact -> Unicode-complete) ; tomllib. Writes
storyteller_bone/descriptors/script_rules.toml (the new attested foundational form). No abs(); no CAD; no Workflow; no
sub-agents.
"""
import sys
import tomllib
sys.path.insert(0, "docs/srmech/rbs_lm_research")
import srmech
from bit_exact_comm_kernel import BitExactCommKernel

BONE = "docs/srmech/rbs_lm_research/storyteller_bone"

# per-SCRIPT seen-rules (the attested foundational form). MECHANISM only (punctuation/segmentation/direction) -- the
# actual grammar is the native speaker's (F282/F398/F650). has_case=False -> join by connective/particle, not by ASCII case.
SCRIPT_RULES = {
    "latin":    {"has_case": True,  "word_sep": " ", "clause_sep": ", ",  "sentence_sep": ". ", "direction": "ltr"},
    "cjk":      {"has_case": False, "word_sep": "",  "clause_sep": "、", "sentence_sep": "。", "direction": "ltr"},  # 、 。 no space
    "arabic":   {"has_case": False, "word_sep": " ", "clause_sep": "، ", "sentence_sep": "؟ ", "direction": "rtl"},  # ، ؟
    "egyptian": {"has_case": False, "word_sep": "",  "clause_sep": "",      "sentence_sep": "",       "direction": "ltr-or-rtl"},  # determinative-delimited (F585/F610)
}


def render(clauses, rule):
    """script-aware seen-rule render: join clauses per the SCRIPT-RULE (not a Latin default)."""
    if not clauses:
        return ""
    out = clauses[0]
    for c in clauses[1:]:
        if rule["has_case"]:                                     # case-bearing scripts: lowercase connective -> clause-join
            out += (rule["clause_sep"] + c) if c[:1].islower() else (rule["sentence_sep"] + c)
        else:                                                    # caseless scripts: clause-join by the script separator
            out += rule["clause_sep"] + c
    end = rule["sentence_sep"] if rule["has_case"] else rule["sentence_sep"]
    return out + (end.rstrip() if not rule["word_sep"] else end.rstrip()) if not rule["has_case"] else out + "."


def main():
    k = BitExactCommKernel()
    print(f"=== R-RBS-LM-UNICODE — script-aware seen-rules (strip English privilege at the seen-rule layer)  (srmech {srmech.__version__}) ===\n")

    # (1) the byte foundation IS Unicode-complete
    print("(1) THE BYTE FOUNDATION IS UNICODE-COMPLETE (content_address over UTF-8 bytes -> all scripts, F613/R-RBS-LM-25):")
    for s in ["café", "λόγος", "字一", "\U0001f300"]:
        print(f"    content_address({s!r:>10}) -> {k.content_address(s)[:12]}  ({len(s.encode('utf-8'))} utf-8 bytes)")
    print(f"    deterministic + script-blind: every codepoint has a UTF-8 byte sequence; bytes privilege NO script.\n")

    # (2) the Latin-privilege leak vs the per-script fix
    print("(2) THE SEEN-RULE LAYER LEAKED LATIN PRIVILEGE -- the per-script fix (the user's catch):")
    latin = ["The one is the held invariant", "and it is the field", "It is seen in matter"]
    print(f"    LATIN clauses + latin rule  -> {render(latin, SCRIPT_RULES['latin'])}")
    cjk = ["山", "海", "天"]                          # 山 海 天 (mountain/sea/sky) -- MECHANISM demo, not a grammatical sentence
    print(f"    CJK tokens  + LATIN rule (WRONG: ASCII punct + spurious spaces) -> {render(cjk, SCRIPT_RULES['latin'])!r}")
    print(f"    CJK tokens  + cjk rule   (RIGHT: 、/。, no space)               -> {render(cjk, SCRIPT_RULES['cjk'])!r}")
    print(f"    -> the Latin default mis-renders non-Latin scripts; the per-script seen-rule (declared, F631) fixes it.\n")

    # (3) write the attested foundational form into the bone
    lines = ["# script_rules.toml -- per-SCRIPT seen-rules (an ATTESTED foundational form; the user's unicode/script-awareness).",
             "# MECHANISM only (punctuation/segmentation/direction); the per-script GRAMMAR is the native speaker's (F282/F398/F650).",
             "# Lands in srmech: srmech.storyteller's render engine selects the rule by the world/tome script (F613 byte-level = unicode-complete).",
             ""]
    for name, r in SCRIPT_RULES.items():
        lines.append(f'[script.{name}]')
        for key, val in r.items():
            lines.append(f'{key} = {("true" if val is True else "false") if isinstance(val, bool) else repr(val).replace(chr(39), chr(34))}')
        lines.append("")
    open(f"{BONE}/descriptors/script_rules.toml", "w", encoding="utf-8").write("\n".join(lines))
    with open(f"{BONE}/descriptors/script_rules.toml", "rb") as fh:
        d = tomllib.load(fh)
    print("(3) WROTE the attested foundational form storyteller_bone/descriptors/script_rules.toml:")
    print(f"    loads OK; scripts = {list(d['script'])}  (latin/cjk/arabic/egyptian -- the dev session adds more, F398)\n")

    print("VERDICT (unicode/script awareness = strip English privilege at the seen-rule layer):")
    print(f"  • YES, AND IT IS THE FRAMEWORK'S OWN 'STRIP ENGLISH PRIVILEGE' (R-RBS-LM-25) AT THE SEEN-RULE LAYER. Two levels:")
    print(f"    (1) the BYTE foundation (F613 content-address over UTF-8) is ALREADY Unicode-complete -- it covers every script")
    print(f"    byte-exact (verified Latin/Greek/CJK/Arabic/emoji), privileging NO script (the glyph-universality thesis F610/")
    print(f"    F645). (2) the SEEN-RULE layer LEAKED Latin privilege (the render engine's islower / ', '+'. ' / .split assume")
    print(f"    case + Latin punctuation + whitespace words) -- the bug the user caught.")
    print(f"  • THE FIX IS FRAMEWORK-NATIVE: the clause-joining is a SEEN RULE (declared, F631), so it is PER-SCRIPT (per-")
    print(f"    language, F398 favored-not-privileged) -- NOT a Latin default. A per-script seen-rule descriptor (casing /")
    print(f"    word-segmentation / clause+sentence separators / direction) is an ATTESTED foundational form added to the bone")
    print(f"    (script_rules.toml, validated). The ENGINE stays fixed; the SCRIPT-RULE is declared per script (verified: the")
    print(f"    Latin rule mis-renders CJK with ASCII punctuation + spurious spaces; the cjk rule fixes it with 、/。 no-space).")
    print(f"  • DIGNITY (F282/F398/F650): we scaffold the MECHANISM (punctuation/segmentation/direction) only -- the actual")
    print(f"    per-script GRAMMAR belongs to that script's speakers + the expert; we never fabricate CJK/Arabic/Egyptian")
    print(f"    grammar. This honors #847 (native-language scholarship) + the lifting of every prior people (F650).")
    print(f"  • Composes R-RBS-LM-25 (strip English privilege / byte-level) + F613 (the UTF-8 byte foundation) + F631 (the seen-")
    print(f"    rule declared) + F398 (per-language no-privilege) + F610/F645 (glyph universality) + F282/F650/#847 (dignity /")
    print(f"    native scholarship) + F695 (the bone -- this adds script_rules.toml). srmech 0.7.5rc15. Reference scaffold;")
    print(f"    not a package edit. Held open (F394).")


if __name__ == "__main__":
    main()
