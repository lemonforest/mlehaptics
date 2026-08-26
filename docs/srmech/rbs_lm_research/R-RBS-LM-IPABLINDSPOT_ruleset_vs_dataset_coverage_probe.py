r"""R-RBS-LM-IPABLINDSPOT (#226) — the rulesets-vs-dataset blind-spot ratchet for the IPA kernel: run understand_ipa
over real {{IPA…}} template contents from enwiki, measure coverage, and census the chars it cannot classify (the gaps —
expected to surface the IPAc-en ascii-code form: ee/oo/sh/ch that need the code table). Not training; coverage only.

srmech 0.9.0rc209. No numpy, no Python abs builtin, no Counter, no CAD. Run in the background:
  MAX_ARTICLES=12000 /tmp/srmech_v/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-IPABLINDSPOT_...py
"""
import bz2, importlib.util, os, re, sys, time
import xml.etree.ElementTree as ET
from pathlib import Path

DUMP = str(Path.home() / "corpora" / "wikipedia" / "enwiki-latest-pages-articles.xml.bz2")
N = int(os.environ.get("MAX_ARTICLES", "12000"))
_IPA_T = re.compile(r"\{\{\s*(IPA[a-zA-Z-]*)\s*\|([^{}]*?)\}\}", re.I)


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); mod = importlib.util.module_from_spec(spec)
    sv = sys.argv; sys.argv = ["x"]
    try: spec.loader.exec_module(mod)
    except SystemExit: pass
    sys.argv = sv; return mod


K = _load("ipak", "docs/srmech/rbs_lm_research/R-RBS-LM-IPAKERNEL_phonetic_notation_sublanguage_pronunciation_sequence.py")
CLASSIFIED = K.IPA_VOWELS | set(K.SUPRA) | K.LENGTH | set("bdfghjklmnpqrstvwxzθðʃʒŋɡɹɾɫʔʁχħʕ")  # common IPA consonants


def main():
    t0 = time.time()
    blocks = 0; with_ph = 0; with_vowel = 0; pure_ascii = 0
    unclassified = {}; by_template = {}
    n = 0
    with bz2.open(DUMP, "rt", encoding="utf-8") as fh:
        for _e, el in ET.iterparse(fh, events=("end",)):
            if (el.tag.endswith("}text") or el.tag == "text") and el.text:
                n += 1; raw = el.text
                for tmpl, body in _IPA_T.findall(raw):
                    body = body.split("|audio")[0]
                    if not body.strip() or len(body) > 200:
                        continue
                    blocks += 1
                    by_template[tmpl.lower()] = by_template.get(tmpl.lower(), 0) + 1
                    r = K.understand_ipa(body)
                    if r["phonemes"]:
                        with_ph += 1
                    if r["vowels"]:
                        with_vowel += 1
                    core = "".join(p for p in body.split("|") if "=" not in p).strip("/[]() ")
                    if core and all(ord(c) < 128 for c in core):
                        pure_ascii += 1
                    for ph in r["consonants"] + r["vowels"]:
                        for c in ph:
                            if c not in CLASSIFIED and not c.isspace():
                                unclassified[c] = unclassified.get(c, 0) + 1
                if n >= N:
                    el.clear(); break
            el.clear()
    print(f"=== IPABLINDSPOT — ruleset-vs-dataset IPA coverage ({n} articles, {blocks:,} IPA blocks, {time.time()-t0:.0f}s) ===\n")
    print(f"  COVERAGE: >=1 phoneme {with_ph:,}/{blocks:,} = {100*with_ph/max(1,blocks):.0f}%   "
          f">=1 vowel {with_vowel:,} = {100*with_vowel/max(1,blocks):.0f}%   PURE-ASCII (likely IPAc-en code form) "
          f"{pure_ascii:,} = {100*pure_ascii/max(1,blocks):.0f}%")
    print(f"  template mix: " + ", ".join(f"{{{{{t}}}}} {c}" for t, c in sorted(by_template.items(), key=lambda kv: -kv[1])[:8]))
    print("\n  TOP-30 unclassified chars in extracted phonemes (blind spots — rare IPA symbols / IPAc-en code residue):")
    top = sorted(unclassified.items(), key=lambda kv: -kv[1])[:30]
    print("    " + "   ".join(f"{repr(c)} {n}" for c, n in top))


if __name__ == "__main__":
    main()
