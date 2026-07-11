r"""R-RBS-LM-IPAKERNEL (#226) — the IPA (phonetic) notation as its own genome-encoded sublanguage kernel: COMPREHEND a
`{{IPA|…}}` transcription into a PHONEME SEQUENCE + prosody, never strip it.

WHY it's the same comprehend-not-strip pattern but a THINNER structure: IPA is a phonetic NOTATION for PRONUNCIATION —
a SEQUENCE of discrete sound-slots (phonemes), the substrate's discrete-cyclic-slot view of phonology, modulated by
SUPRASEGMENTALS (primary/secondary stress ˈˌ, length ː, syllable breaks). So it is more sequence than graph, but it is
still structure to comprehend, not noise: it contributes (word) --pronounced_as--> /ipa/, and the phoneme inventory +
stress pattern + C/V skeleton let downstream compute phonetic similarity (rhyme / alliteration / homophony) — the
phonological layer of a word's identity (and the ADA/speech surface). The transcription TYPE (phonemic /…/ vs phonetic
[…]) is itself a precision determinative.

Class-B/F FORM grammar (a notation parser, no numeric primitive), sibling to understand_markup / understand_latex /
understand_chem / understand_convert. srmech 0.9.0rc209. No numpy, no Python abs builtin, no Counter, no CAD. The `ipa`
chromosome's gene labels are the phoneme classes (vowel/consonant/suprasegmental). Run:
  /tmp/srmech_v/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-IPAKERNEL_...py
"""
import re
import unicodedata

# IPA vowel base symbols (a segment starting with one of these is a vowel nucleus).
IPA_VOWELS = set("i y ɨ ʉ ɯ u ɪ ʏ ʊ e ø ɘ ɵ ɤ o ə ɛ œ ɜ ɞ ʌ ɔ æ ɐ a ɶ ɑ ɒ ᵻ ɚ ɝ".split())
# suprasegmentals -> feature label (they are NOT phonemes; ː/ˑ attach to the preceding segment as length).
SUPRA = {"ˈ": "primary_stress", "ˌ": "secondary_stress", ".": "syllable_break", "‿": "linking",
         "|": "minor_break", "‖": "major_break", "↗": "rising", "↘": "falling"}
LENGTH = {"ː", "ˑ"}
_DELIMS = "/[]()⟨⟩ \t"


def understand_ipa(src):
    r"""Comprehend an IPA transcription into a pronunciation sequence. Returns:
        ipa        : the normalized phoneme string
        type       : 'phonemic' (/…/) | 'phonetic' ([…]) | 'unspecified'
        phonemes   : ordered segments (base + attached length/diacritics)
        vowels / consonants : the phoneme inventory split
        syllables  : estimated syllable count (vowel GROUPS — adjacent vowels = one diphthong nucleus)
        stress     : the suprasegmental sequence (primary/secondary stress, breaks)
        cv         : the consonant/vowel skeleton (e.g. 'CVCVC')
        edge       : ('__entity__', 'pronounced_as', ipa) — the pronunciation relationship
    COMPREHEND, not strip: the phoneme sequence + prosody survive as structure, not deleted as noise.
    """
    s = src.strip()
    typ = "phonemic" if s.startswith("/") else "phonetic" if s.startswith("[") else "unspecified"
    parts = [p for p in s.split("|") if "=" not in p]        # drop audio=…/lang=… args; join pipe-separated phonemes
    s = "".join(parts)
    s = s.strip(_DELIMS)

    phonemes, stress, cur = [], [], ""
    for ch in s:
        if ch in SUPRA:
            if cur:
                phonemes.append(cur); cur = ""
            stress.append(SUPRA[ch])
        elif ch in LENGTH:
            if cur:
                cur += ch                                    # length attaches to the current segment
            elif phonemes:
                phonemes[-1] += ch
        elif unicodedata.combining(ch) or ch in "ʰʷʲˠˤ̃ⁿˡ":     # diacritic / secondary articulation attaches
            if not cur and phonemes:
                phonemes[-1] += ch
            else:
                cur += ch
        elif ch.isspace():
            if cur:
                phonemes.append(cur); cur = ""
        else:
            if cur:
                phonemes.append(cur)
            cur = ch
    if cur:
        phonemes.append(cur)

    def _is_vowel(p):
        return bool(p) and p[0] in IPA_VOWELS
    vowels = [p for p in phonemes if _is_vowel(p)]
    consonants = [p for p in phonemes if p and not _is_vowel(p)]
    # syllable estimate = number of vowel GROUPS (merge adjacent vowels into one diphthong nucleus)
    syllables, prev_v = 0, False
    cv = []
    for p in phonemes:
        v = _is_vowel(p)
        cv.append("V" if v else "C")
        if v and not prev_v:
            syllables += 1
        prev_v = v
    ipa = "".join(phonemes)
    return {"ipa": ipa, "type": typ, "phonemes": phonemes, "vowels": vowels, "consonants": consonants,
            "syllables": max(syllables, 1 if phonemes else 0), "stress": stress, "cv": "".join(cv),
            "edge": ("__entity__", "pronounced_as", ipa) if ipa else None}


if __name__ == "__main__":
    SAMPLES = ["/əˈlbiːdoʊ/", "[eɪ]", "oː", "/aː/", "[ʔ]", "ɑː", "/tʃiːz/", "[ˈbʊk]",
               "æ|l|ˈ|b|iː|d|oʊ|audio=LL-Q1860.wav", "/ˌɛləˈveɪʃən/"]
    print("=== IPAKERNEL — comprehend {{IPA}} into a pronunciation sequence (not strip) ===\n")
    for s in SAMPLES:
        r = understand_ipa(s)
        print(f"  {s}")
        print(f"     type={r['type']}  phonemes={r['phonemes']}  cv={r['cv']}  syllables={r['syllables']}"
              f"  stress={r['stress']}")
        print(f"     vowels={r['vowels']}  consonants={r['consonants']}\n")
