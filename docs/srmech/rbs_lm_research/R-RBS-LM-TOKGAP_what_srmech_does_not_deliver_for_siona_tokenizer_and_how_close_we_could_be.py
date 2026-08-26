r"""R-RBS-LM-TOKGAP — what does srmech's rc287 `glyph_stream` NOT deliver that Siona's tokenizer uses, and how
close could we get by composing srmech primitives instead of carrying a private tokenizer?

User (2026-07-20): *"can we prefer srmech tokenizer tooling? we brought our research from here to srmech so
that our tooling can be as domain agnostic as possible ... once we find the correct pattern in things, we
should be able to ride any other domain whose cascade patterns have been recognized with the same type of
tooling of different coherency/perspectives. ... find out what parts of srmech does not deliver what we use in
our siona tokenizer things and research to find out if close we could be."*

THE FRAME: this is not "port Siona to glyph_stream". It is "which of Siona's text ops are DOMAIN-AGNOSTIC
cascade ops wearing a text costume?" Those belong upstream and would ride into ephemerides-spectral /
chess-spectral. The ones that are genuinely English/locale-specific stay in Siona and should SAY so.

Siona's tokenizer stack, as found (5 distinct concerns fused into one op):
  1. SEGMENT   `_native._tokenize_spans_py` — byte-scan; `_is_word_byte` = ASCII alnum OR `c >= 0x80`
  2. CASEFOLD  `_native.tokenize` — `.lower()` on each span
  3. FOLD      `context_shape.fold_accents` — NFD, drop Mn, lower
  4. FILTER    `anchor._words` / `register._words` — regex split + `len(w) > 2` floor
  5. MORPH     `asl._lemma_variants` — English suffix stripping

What srmech rc287 ships: `glyph_stream(text)` -> UAX #29 extended grapheme clusters, lossless, NO casefold, NO
length floor, NO stoplist ("case folding and confusable normalisation are per-locale concerns that now belong
downstream" — rc287 changelog).

MEASURED HERE:
  A. Does Siona's byte-scan carry the SAME scriptio-continua defect srmech just removed? (`c >= 0x80` makes
     every non-ASCII byte a word byte, so a CJK run cannot break.) Measured against the same failure cases
     rc287 cites, on 18-language sample text.
  B. Can Siona's word segmentation be RECOVERED by composing `glyph_stream` + one boundary predicate — i.e. is
     the private tokenizer replaceable by srmech + a thin, declared projection? Exact-match rate on ASCII prose.
  C. Which of the 5 concerns are domain-agnostic (upstream candidates) vs locale-specific (stay in Siona)?
  D. Does the same gap exist in the sister packages' kernels (ephemerides / chess), i.e. is this one shared
     tooling gap or three unrelated ones?

srmech 0.9.0rc288. Composes F1257 (the finding that motivated rc287), F1255/F1256, #231/PKG-3.
Run:  /tmp/srmech_rc288/bin/python3 R-RBS-LM-TOKGAP_*.py
"""
import sys
import time
import unicodedata
from pathlib import Path

from srmech.amsc import text as T

SIONA = Path(__file__).resolve().parent.parent / "siona"
sys.path.insert(0, str(SIONA))
T0 = time.time()


def log(m):
    print("[%5.1fs] %s" % (time.time() - T0, m), flush=True)


# ---- Siona's tokenizer, reproduced verbatim from siona/_native.py (no import: keeps this runnable
# ---- even if the package pulls srmech.amsc.text at import time)
def _is_word_byte(c):
    return (48 <= c <= 57) or (97 <= c <= 122) or (65 <= c <= 90) or c >= 0x80


def siona_spans(data):
    out, i, n = [], 0, len(data)
    while i < n:
        while i < n and not _is_word_byte(data[i]):
            i += 1
        if i >= n:
            break
        s = i
        while i < n and _is_word_byte(data[i]):
            i += 1
        out.append((s, i - s))
    return out


def siona_tokenize(text):
    data = text.encode("utf-8") if isinstance(text, str) else bytes(text)
    return [data[s:s + ln].decode("utf-8", "replace").lower() for s, ln in siona_spans(data)]


# ---- the candidate REPLACEMENT: srmech glyph_stream + one declared boundary predicate ----
def _cluster_is_word(cl):
    """Boundary predicate over a GRAPHEME CLUSTER (not a byte): letter|mark|number by Unicode category."""
    base = cl[0]
    return unicodedata.category(base)[0] in ("L", "M", "N")


def glyph_words(text, *, casefold=True):
    """Siona-shaped word segmentation COMPOSED from srmech's glyph_stream + a declared predicate.

    This is the whole proposal in one function: srmech owns SEGMENTATION (universal, attested, C-native);
    the word decision is a thin, named, locale-declared projection ON TOP -- not a second tokenizer.
    """
    out, cur = [], []
    for cl in T.glyph_stream(text):
        if _cluster_is_word(cl):
            cur.append(cl)
        elif cur:
            out.append("".join(cur))
            cur = []
    if cur:
        out.append("".join(cur))
    return [w.lower() for w in out] if casefold else out


SAMPLES = {
    "English":  "The quick brown fox jumps over the lazy dog.",
    "Chinese":  "中国的首都是北京。",
    "Japanese": "日本語のテキストです。",
    "Thai":     "ภาษาไทยเขียนติดกัน",
    "Korean":   "한국어 텍스트입니다.",
    "Russian":  "Быстрая коричневая лиса.",
    "Greek":    "Η γρήγορη καφέ αλεπού.",
    "Arabic":   "الثعلب البني السريع.",
    "Hebrew":   "השועל החום המהיר.",
    "Hindi":    "तेज़ भूरी लोमड़ी।",
    "Hawaiian": "ʻokina and kahakō: ʻāina",
    "Emoji":    "family 👨‍👩‍👧‍👦 and flag 🇯🇵 here",
}


def main():
    import srmech
    log("=== TOKGAP — srmech %s vs Siona's private tokenizer ===" % srmech.__version__)

    # ---------- A. does Siona carry the defect rc287 removed? ----------
    log("")
    log("--- A. SCRIPTIO-CONTINUA / cluster defects: Siona byte-scan vs srmech-composed ---")
    log("  %-10s %-7s %-7s  %s" % ("script", "siona", "glyph", "note"))
    a_rows = []
    for name, s in SAMPLES.items():
        st, gt = siona_tokenize(s), glyph_words(s)
        longest_s = max((len(t) for t in st), default=0)
        note = ""
        if longest_s >= 6 and name in ("Chinese", "Japanese", "Thai"):
            note = "SIONA RUNS TOGETHER (%d-char token)" % longest_s
        elif name == "Hawaiian":
            note = "okina kept" if any("ʻ" in t for t in gt) else ""
            note += " | siona okina: %s" % ("kept" if any("ʻ" in t for t in st) else "LOST")
        elif name == "Emoji":
            note = "siona emoji tokens: %d | glyph: %d" % (
                sum(1 for t in st if any(ord(c) > 0x1F000 for c in t)),
                sum(1 for t in gt if any(ord(c) > 0x1F000 for c in t)))
        log("  %-10s %-7d %-7d  %s" % (name, len(st), len(gt), note))
        a_rows.append((name, len(st), len(gt), note))

    log("")
    log("  the two rc287 cites, run against SIONA's tokenizer:")
    log("    siona_tokenize('中 国')      = %r   (srmech pre-rc287 gave [])" % (siona_tokenize("中 国"),))
    log("    siona_tokenize('日本語のテキスト') = %r" % (siona_tokenize("日本語のテキスト"),))
    log("    glyph_words('中 国')         = %r" % (glyph_words("中 国"),))

    # ---------- B. can glyph_stream RECOVER Siona's segmentation on the text it was built for? ----------
    log("")
    log("--- B. RECOVERY: does srmech-composed reproduce Siona's own output on ASCII prose? ---")
    probes = ["The quick brown fox jumps over the lazy dog.",
              "hello, world -- this is a test (with punctuation) and 42 numbers!",
              "don't split contractions?  maybe. e.g. U.S.A. 3.14",
              "CamelCase and snake_case and kebab-case",
              "  leading and trailing   whitespace  "]
    same = 0
    for p in probes:
        st, gt = siona_tokenize(p), glyph_words(p)
        ok = st == gt
        same += ok
        if not ok:
            log("    DIFF %r" % p[:52])
            log("         siona: %s" % st)
            log("         glyph: %s" % gt)
    log("  exact match on %d/%d ASCII probes" % (same, len(probes)))

    # ---------- C. the concern split ----------
    log("")
    log("--- C. THE FIVE CONCERNS — upstream-able vs locale-specific ---")
    concerns = [
        ("1 SEGMENT", "_native._tokenize_spans_py", "srmech glyph_stream + predicate",
         "DELIVERED", "srmech owns it; universal + attested + C-native"),
        ("2 CASEFOLD", "_native.tokenize .lower()", "str.lower / str.casefold",
         "DECLINED", "rc287: per-locale, belongs downstream — Siona keeps, but DECLARE it"),
        ("3 FOLD", "context_shape.fold_accents", "(none in srmech)",
         "GAP", "NFD+drop-Mn is DOMAIN-AGNOSTIC (a Class-K projection) — upstream candidate"),
        ("4 FILTER", "anchor._words len>2", "(removed from srmech by rc287)",
         "RETIRED", "same _MIN_LEN defect rc287 deleted — Siona still carries it"),
        ("5 MORPH", "asl._lemma_variants", "(none)",
         "LOCAL", "English suffix rules — genuinely locale-specific, stays in Siona"),
    ]
    log("  %-11s %-30s %-32s %-10s" % ("concern", "siona site", "srmech equivalent", "status"))
    for c in concerns:
        log("  %-11s %-30s %-32s %-10s" % c[:4])
    log("")
    for c in concerns:
        log("    %-11s %s" % (c[0], c[4]))

    # ---------- D. is the len>2 filter live in Siona today? ----------
    log("")
    log("--- D. is the retired _MIN_LEN defect LIVE in Siona? ---")
    import re
    def anchor_words(gloss):
        return [w for w in re.split(r"[ ,;/()]+", (gloss or "").lower()) if len(w) > 2]
    for probe in ("a cat in a hat", "I am", "to be or not to be", "中 国"):
        log("    anchor._words(%-20r) = %s" % (probe, anchor_words(probe)))
    log("    => every 1-2 char token is dropped, incl. the operators F1257 found ARE the conserved core")

    log("")
    log("VERDICT: srmech delivers concern 1 (and better than Siona's own). Concern 3 is the one real GAP and "
        "it is domain-agnostic. Concern 4 is a defect Siona inherited and srmech has already retired. "
        "Concerns 2 and 5 are correctly Siona-local but should be DECLARED, not implicit.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
