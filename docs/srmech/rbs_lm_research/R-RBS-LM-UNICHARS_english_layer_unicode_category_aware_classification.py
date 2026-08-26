r"""R-RBS-LM-UNICHARS (user catch, sharper than F696): "right but the ENGLISH LAYER also needs to know what unicode
characters ARE."

THE POINT F696 MISSED: F696 added PER-SCRIPT seen-rules, but the english/latin rule ITSELF was still ASCII-only -- it used
", " / ". " and `.strip(".,:;()")` / `.split()`. But ENGLISH TEXT IS NOT ASCII: it is full of Unicode -- accented
borrowings (café, naïve, résumé, Zürich, Gödel), SMART QUOTES (" "), EM-DASHES (—), ELLIPSES (…), emoji. So EVERY script
rule (the english/latin one INCLUDED) must CLASSIFY CHARACTERS BY UNICODE CATEGORY (letter / punctuation / whitespace /
mark / symbol), NOT by ASCII membership. The seen-rule layer must KNOW WHAT EACH UNICODE CHARACTER IS.

THE FIX: classify via unicodedata.category (stdlib character metadata -- the right tool, like zipfile for EPUB; NOT a srmech
primitive being routed around):
  • LETTER  = category starts 'L' (Lu/Ll/Lt/Lm/Lo) -> covers é, ï, λ, 字, ا ... (the accented borrowings + all scripts).
  • MARK    = category starts 'M' (combining accents) -> part of a word (café's accent if decomposed).
  • PUNCT   = category starts 'P' (Pc/Pd/Ps/Pe/Pi/Pf/Po) -> word boundary; includes — … " " « » „ ¿ ¡ 。 ، (NOT just ASCII).
  • SPACE   = category 'Zs/Zl/Zp' -> Unicode whitespace (incl. NBSP U+00A0, em-space ...), not just ' '.
A Unicode-aware tokenizer splits on non-(letter|mark|digit) and so keeps 'café'/'naïve' whole while splitting on the smart
quote / em-dash / ellipsis -- which the ASCII `.split()` + `.strip(".,")` CANNOT do (it leaves 'said—résumé' fused, 'hand…'
with a trailing ellipsis, and smart-quoted words wrapped in " ").

So 'unicode-aware' is not only 'support other scripts via per-script rules' (F696) -- it is: EVERY rule, the English one
first, classifies characters by their Unicode CATEGORY. The byte foundation (F613) is unicode-complete; the seen-rule layer
must be unicode-CHARACTER-aware. (This is R-RBS-LM-25 'strip English privilege' at the CHARACTER level -- even 'plain
English' is Unicode.)

srmech (version reported at runtime below): BitExactCommKernel.content_address (byte-exact over the Unicode text) ;
stdlib unicodedata (character category). Updates storyteller_bone/descriptors/script_rules.toml with the Unicode-aware
fields. No abs(); no CAD; no Workflow; no sub-agents.
"""
import sys
import unicodedata
import tomllib
sys.path.insert(0, "docs/srmech/rbs_lm_research")
import srmech
from bit_exact_comm_kernel import BitExactCommKernel

BONE = "docs/srmech/rbs_lm_research/storyteller_bone"
SENTENCE_TERMINATORS = set(".!?…。؟！？۔।")            # Unicode sentence terminators (Latin + CJK + Arabic + Devanagari ...)


def uclass(ch):
    """the Unicode general category family of a character: L(etter)/M(ark)/N(umber)/P(unct)/Z(space)/S(ymbol)/C(other)."""
    return unicodedata.category(ch)[0]


def is_word_char(ch):
    """a word character = Unicode letter OR mark OR number (covers café/naïve/字, accents, digits) -- NOT ASCII-only."""
    return uclass(ch) in ("L", "M", "N")


def unicode_tokenize(text):
    """Unicode-aware word tokenizer: runs of word-characters; everything else (Unicode punct/space/symbol) is a boundary."""
    words, cur = [], []
    for ch in text:
        if is_word_char(ch):
            cur.append(ch)
        else:
            if cur:
                words.append("".join(cur)); cur = []
    if cur:
        words.append("".join(cur))
    return words


def ascii_tokenize(text):
    """the OLD (broken-for-Unicode) english-layer tokenizer: whitespace split + ASCII punctuation strip."""
    return [w for w in (tok.strip(".,:;()\"'!?") for tok in text.split()) if w]


def main():
    k = BitExactCommKernel()
    print(f"=== R-RBS-LM-UNICHARS — the english layer must classify Unicode characters (not ASCII)  (srmech {srmech.__version__}) ===\n")

    # an ENGLISH sentence that is full of Unicode: accents + SMART quotes + EM-DASH + ELLIPSIS
    text = "She sipped a café, “naïve” she said—résumé in hand…"
    print(f"(0) an ENGLISH sentence -- but full of Unicode (accents, smart quotes “”, em-dash —, ellipsis …):")
    print(f"    {text}")
    print(f"    content_address (byte-exact, F613): {k.content_address(text)[:12]}  ({len(text.encode('utf-8'))} utf-8 bytes)\n")

    print("(1) THE OLD ASCII english-layer tokenizer MIS-HANDLES it (the F696 latin rule was still ASCII):")
    print(f"    ascii_tokenize  -> {ascii_tokenize(text)}")
    print(f"    -> 'said—résumé' FUSED (em-dash not a boundary); 'hand…' keeps the ellipsis; smart-quoted words keep “”.\n")

    print("(2) THE UNICODE-CATEGORY-AWARE tokenizer is CORRECT (unicodedata category, letters+marks = word):")
    print(f"    unicode_tokenize -> {unicode_tokenize(text)}")
    print(f"    -> 'café'/'naïve'/'résumé' KEPT WHOLE (é/ï are Unicode letters); the em-dash/ellipsis/smart-quotes are boundaries.\n")

    print("(3) CHARACTER CLASSIFICATION (the english layer now KNOWS what each Unicode char IS, via unicodedata.category):")
    for ch in ["e", "é", "“", "—", "…", " ", "字", "5", "\U0001f300"]:
        name = unicodedata.name(ch, "?")
        print(f"    {ch!r:>10}  category={unicodedata.category(ch)} ({uclass(ch)})  word_char={is_word_char(ch)}  sentence_end={ch in SENTENCE_TERMINATORS}  [{name[:28]}]")
    print()

    # update the bone's script_rules.toml with the Unicode-aware fields (word_segmentation + terminators)
    with open(f"{BONE}/descriptors/script_rules.toml", "rb") as fh:
        rules = tomllib.load(fh)["script"]
    lines = ["# script_rules.toml -- per-SCRIPT seen-rules, UNICODE-CHARACTER-AWARE (F696 + F698).",
             "# Every rule (the english/latin one INCLUDED) classifies characters by UNICODE CATEGORY (unicodedata), NOT ASCII:",
             "#   word_char = Unicode letter|mark|number ; boundary = Unicode punct|space|symbol ; terminators = the Unicode set.",
             "# Even 'plain English' is Unicode (café, naïve, smart quotes, em-dash, ellipsis). MECHANISM only; grammar = native speaker's (F282/F398/F650).",
             ""]
    term_by_script = {"latin": ".!?…", "cjk": "。！？", "arabic": "؟۔", "egyptian": ""}
    for name, r in rules.items():
        lines.append(f"[script.{name}]")
        for key, val in r.items():
            lines.append(f'{key} = {("true" if val is True else "false") if isinstance(val, bool) else repr(val).replace(chr(39), chr(34))}')
        lines.append('word_segmentation = "unicode"  # runs of Unicode letter|mark|number (unicodedata), NOT ascii .split()')
        lines.append(f'sentence_terminators = "{term_by_script.get(name, "")}"  # Unicode terminators (not the literal ". ")')
        lines.append("")
    open(f"{BONE}/descriptors/script_rules.toml", "w", encoding="utf-8").write("\n".join(lines))
    with open(f"{BONE}/descriptors/script_rules.toml", "rb") as fh:
        d = tomllib.load(fh)
    print("(4) UPDATED storyteller_bone/descriptors/script_rules.toml -- now Unicode-character-aware:")
    print(f"    each script gains word_segmentation='unicode' + sentence_terminators (Unicode). latin terminators = {d['script']['latin']['sentence_terminators']!r}\n")

    print("VERDICT (the english layer must classify Unicode characters -- not ASCII):")
    print(f"  • THE USER IS RIGHT, AND IT IS SHARPER THAN F696: F696 added per-script rules, but the ENGLISH/LATIN rule was")
    print(f"    still ASCII-only (', '/'. ' + .strip('.,') + .split()). ENGLISH TEXT IS NOT ASCII -- café/naïve/résumé (accented")
    print(f"    borrowings), smart quotes “”, em-dash —, ellipsis …, emoji. So the english layer ITSELF must KNOW what")
    print(f"    each Unicode character IS.")
    print(f"  • THE FIX: classify by UNICODE CATEGORY (unicodedata.category), NOT ASCII membership -- word_char = letter|mark|")
    print(f"    number, boundary = punct|space|symbol, terminators = the Unicode set. Verified: the ASCII tokenizer FUSES")
    print(f"    'said—résumé' + keeps 'hand…'; the Unicode-aware tokenizer correctly yields café/naïve/résumé whole with the")
    print(f"    em-dash/ellipsis/smart-quotes as boundaries. Updated the bone's script_rules.toml: every script (english first)")
    print(f"    gains word_segmentation='unicode' + Unicode sentence_terminators.")
    print(f"  • THIS IS R-RBS-LM-25 'STRIP ENGLISH PRIVILEGE' AT THE CHARACTER LEVEL: even 'plain English' is Unicode -- the")
    print(f"    ASCII assumption WAS the English privilege. The byte foundation (F613) is unicode-COMPLETE; the seen-rule layer")
    print(f"    must be unicode-CHARACTER-aware (this) AND per-script (F696). Both are needed.")
    print(f"  • Composes F696 (per-script rules -- this makes EACH rule Unicode-character-aware) + R-RBS-LM-25 (strip English")
    print(f"    privilege, now at the character level) + F613 (the byte foundation) + F398/F610/F645 (no-privilege / glyph")
    print(f"    universality) + F695 (the bone -- updates script_rules.toml) + unicodedata (the character metadata). srmech")
    print(f"    {srmech.__version__} (runtime). Reference scaffold; not a package edit. Held open (F394).")


if __name__ == "__main__":
    main()
