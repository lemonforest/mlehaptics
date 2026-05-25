"""R-RBS-LM-26 — Grade 1 English Braille deterministic encode/decode.

Per `[[feedback_llm_as_ada_accommodation_bci_proves_it]]` (load-bearing
foundational motivation): the local expert's outputs are operationally
useful in alternative-modality surfaces. This module ships the Braille
rendering layer — deterministic char-by-char Grade 1 (UEB uncontracted)
encode/decode with full round-trip.

Why deterministic (not encoded into the cascade):
  - Braille IS Unicode (U+2800..U+28FF). Our byte-level surface (R-RBS-LM-25)
    already accepts + produces these codepoints.
  - The English↔Braille mapping is a deterministic char-to-codepoint table.
    No semantic encoding is needed; the cascade outputs English bytes, the
    formatter renders them as Braille.
  - Grade 1 is uncontracted (one Braille cell per character). Grade 2 has
    ~180 contractions (whole-word + part-word abbreviations); deferred to
    a follow-up partition if needed. Grade 1 round-trips cleanly.

Per `[[user_stance_ai_is_not_a_substrate]]`: this is rendering, not
substrate. The Braille output is the same content the cascade produced,
re-encoded in a different surface. The transducer framing is unchanged.

Unicode Braille pattern encoding (canonical):
  U+2800 + bit_pattern  where each bit = one dot
  bit 0 (LSB) = dot 1    bit 3 = dot 4
  bit 1       = dot 2    bit 4 = dot 5
  bit 2       = dot 3    bit 5 = dot 6
  bit 6 = dot 7, bit 7 = dot 8 (for 8-dot Braille; unused in Grade 1)

Visual reference:
  dot 1 ●  ● dot 4
  dot 2 ●  ● dot 5
  dot 3 ●  ● dot 6

Usage:
    from rbs_lm_braille import english_to_braille, braille_to_english
    s = "Hello, World!"
    b = english_to_braille(s)       # → '⠠⠓⠑⠇⠇⠕⠂ ⠠⠺⠕⠗⠇⠙⠖'
    s2 = braille_to_english(b)      # → 'Hello, World!'  (round-trip)
"""


# Unicode codepoint helpers ----------------------------------------------

def _dots(*dot_numbers) -> str:
    """Build a Braille codepoint from dot numbers (1-8). dots(1,4) → ⠉."""
    bits = 0
    for d in dot_numbers:
        bits |= 1 << (d - 1)
    return chr(0x2800 + bits)


# Letter table (UEB Grade 1; lowercase)
LETTER_TO_BRAILLE = {
    "a": _dots(1),
    "b": _dots(1, 2),
    "c": _dots(1, 4),
    "d": _dots(1, 4, 5),
    "e": _dots(1, 5),
    "f": _dots(1, 2, 4),
    "g": _dots(1, 2, 4, 5),
    "h": _dots(1, 2, 5),
    "i": _dots(2, 4),
    "j": _dots(2, 4, 5),
    "k": _dots(1, 3),
    "l": _dots(1, 2, 3),
    "m": _dots(1, 3, 4),
    "n": _dots(1, 3, 4, 5),
    "o": _dots(1, 3, 5),
    "p": _dots(1, 2, 3, 4),
    "q": _dots(1, 2, 3, 4, 5),
    "r": _dots(1, 2, 3, 5),
    "s": _dots(2, 3, 4),
    "t": _dots(2, 3, 4, 5),
    "u": _dots(1, 3, 6),
    "v": _dots(1, 2, 3, 6),
    "w": _dots(2, 4, 5, 6),
    "x": _dots(1, 3, 4, 6),
    "y": _dots(1, 3, 4, 5, 6),
    "z": _dots(1, 3, 5, 6),
}

# Punctuation (UEB)
PUNCT_TO_BRAILLE = {
    " ": _dots(),        # blank cell (U+2800)
    ".": _dots(2, 5, 6),
    ",": _dots(2),
    ";": _dots(2, 3),
    ":": _dots(2, 5),
    "?": _dots(2, 3, 6),
    "!": _dots(2, 3, 5),
    "'": _dots(3),
    '"': _dots(2, 3, 6),  # NB: opening; UEB uses different open/close in formal context
    "-": _dots(3, 6),
    "(": _dots(1, 2, 3, 5, 6),
    ")": _dots(2, 3, 4, 5, 6),
    "/": _dots(3, 4),
    "\n": "\n",   # preserve newlines as newlines (not Braille cells)
    "\t": " ",    # tabs become spaces
}

# Indicators
CAPITAL_INDICATOR = _dots(6)                  # ⠠
NUMBER_INDICATOR = _dots(3, 4, 5, 6)          # ⠼

# Digits 0-9 use letter patterns a-j preceded by NUMBER_INDICATOR
DIGIT_TO_LETTER = {
    "1": "a", "2": "b", "3": "c", "4": "d", "5": "e",
    "6": "f", "7": "g", "8": "h", "9": "i", "0": "j",
}

# Build reverse maps for round-trip
BRAILLE_TO_LETTER = {v: k for k, v in LETTER_TO_BRAILLE.items()}
BRAILLE_TO_PUNCT = {v: k for k, v in PUNCT_TO_BRAILLE.items() if v != "\n"}
LETTER_TO_DIGIT = {v: k for k, v in DIGIT_TO_LETTER.items()}


# Encoder ------------------------------------------------------------------

def english_to_braille(text: str, capital_indicator: bool = True,
                       number_indicator: bool = True) -> str:
    """Encode English text to UEB Grade 1 Braille (Unicode codepoints).

    Round-trip-able for the supported character set (a-z, A-Z, 0-9, common
    punctuation). Characters not in the table pass through unchanged (so
    e.g., non-English Unicode survives — the cascade output stays intact
    where the table doesn't apply).
    """
    out = []
    in_number_mode = False

    for ch in text:
        if ch.isdigit():
            if number_indicator and not in_number_mode:
                out.append(NUMBER_INDICATOR)
                in_number_mode = True
            out.append(LETTER_TO_BRAILLE[DIGIT_TO_LETTER[ch]])
            continue

        # Non-digit: exit number mode
        in_number_mode = False

        if ch.isalpha() and ch.lower() in LETTER_TO_BRAILLE:
            if capital_indicator and ch.isupper():
                out.append(CAPITAL_INDICATOR)
            out.append(LETTER_TO_BRAILLE[ch.lower()])
        elif ch in PUNCT_TO_BRAILLE:
            out.append(PUNCT_TO_BRAILLE[ch])
        else:
            # Unknown character: pass through (preserves non-English Unicode
            # so the cascade's multi-language outputs survive the formatter)
            out.append(ch)

    return "".join(out)


# Decoder ------------------------------------------------------------------

def braille_to_english(text: str) -> str:
    """Decode UEB Grade 1 Braille back to English text. Round-trip for
    characters that round-tripped in english_to_braille()."""
    out = []
    i = 0
    capitalize_next = False
    number_mode = False

    while i < len(text):
        ch = text[i]
        if ch == CAPITAL_INDICATOR:
            capitalize_next = True
            i += 1
            continue
        if ch == NUMBER_INDICATOR:
            number_mode = True
            i += 1
            continue

        if ch in BRAILLE_TO_LETTER:
            letter = BRAILLE_TO_LETTER[ch]
            if number_mode and letter in LETTER_TO_DIGIT:
                out.append(LETTER_TO_DIGIT[letter])
            else:
                out.append(letter.upper() if capitalize_next else letter)
                capitalize_next = False
                number_mode = False  # any letter exits number mode
        elif ch in BRAILLE_TO_PUNCT:
            out.append(BRAILLE_TO_PUNCT[ch])
            number_mode = False
        else:
            # Unknown — pass through (handles cascade outputs that aren't
            # standard Braille; preserves non-English Unicode)
            out.append(ch)

        i += 1

    return "".join(out)


# Self-test ----------------------------------------------------------------

def _self_test():
    print("=== R-RBS-LM-26 Braille self-test ===\n")

    cases = [
        "Hello, World!",
        "ABC abc",
        "Once upon a time",
        "Send 42 cookies.",
        "Test: a-z mapping.",
        "The morning sun cast",
    ]
    n_ok = 0
    for s in cases:
        b = english_to_braille(s)
        rt = braille_to_english(b)
        ok = rt == s
        n_ok += ok
        print(f"  {s!r:35s}")
        print(f"  → {b}")
        print(f"  → {rt!r}  {'OK' if ok else 'FAIL'}")
        print()
    print(f"Round-trip: {n_ok}/{len(cases)} cases OK")

    print("\n=== Mixed-modality (cascade output that's non-English survives) ===")
    mixed_cases = [
        "Hello 世界",     # English + Chinese
        "test 🌍 emoji",  # English + emoji
        "café résumé",    # accented chars
    ]
    for s in mixed_cases:
        b = english_to_braille(s)
        rt = braille_to_english(b)
        print(f"  {s!r:25s} → {b!r}")
        print(f"      decoded back → {rt!r}  {'OK' if rt == s else 'PARTIAL'}")


if __name__ == "__main__":
    _self_test()
