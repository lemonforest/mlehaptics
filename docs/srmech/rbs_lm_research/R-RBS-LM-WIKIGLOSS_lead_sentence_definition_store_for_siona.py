r"""R-RBS-LM-WIKIGLOSS (F760 infra) — the real DEFINITION tier: title -> the lead-sentence gloss of each simplewiki
article ("what X IS"), so Siona answers "what is a tomato?" with a definition, not a relations dump (the F759 next-inch).

The lead sentence of a simplewiki article IS a definition (e.g. "The tomato (Solanum lycopersicum) is a … berry."). We
UNDERSTAND the markup (F764: the shared R-RBS-LM-MARKUPGRAMMAR unwraps inline content — a [[linked]] / '''bold''' word
is still content — and removes only pure-form syntax) rather than skipping any sentence that contains markup (the
strip instinct F762 corrected: "you can't just strip things Siona needs to understand"), then take the first clean
sentence. Compact title->gloss side-store (the EXACT definition tier; pairs with the F754/F757 relational side-stores
+ the genome self — F584/F119 two-tier).

srmech 0.7.5rc155. Text-only (no encode); no abs; no CAD; CC-BY-SA simplewiki. Run (background):
  /tmp/srmech_rc155/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-WIKIGLOSS_...py
"""
import importlib.util as _U
import json
import os
import re
import time
from pathlib import Path
import srmech
from srmech.amsc.format import sha256_raw

# F764: the lead is run through the SHARED markup grammar — markup is UNDERSTOOD (unwrapped + edges extracted), not
# stripped/skipped (the F762 correction: "you can't just strip things Siona needs to understand"). __file__-based
# import so it resolves regardless of cwd.
_mk_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "R-RBS-LM-MARKUPGRAMMAR_class_bf_form_layer_understand_not_strip.py")
_mk_spec = _U.spec_from_file_location("markupgrammar", _mk_path)
MK = _U.module_from_spec(_mk_spec); _mk_spec.loader.exec_module(MK)

ART = Path.home() / "corpora" / "wikipedia" / "simplewiki_extracted" / "articles.jsonl"
OUT = Path.home() / "corpora" / "wikipedia" / "simplewiki_glosses.json"
_SENT = re.compile(r"(?<=[.!?])\s+")


def gloss_of(text):
    """The first lead sentence as the definition, with markup UNDERSTOOD (F764) — the unified grammar UNWRAPS inline
    content (a linked/bold word is still content) and removes only pure-form syntax, so sentences that USED to be
    skipped for containing a [[link]] are now kept + clean. (Was: skip any markup sentence — the strip instinct F762
    corrected.) A light thumb/px guard remains for residual image-caption junk. '' if none usable."""
    clean, _edges = MK.understand_markup((text or "")[:1500].replace("\n", " "))
    for sent in _SENT.split(clean)[:8]:
        s = sent.strip()
        if 12 <= len(s) <= 400 and not re.search(r"\bthumb\b|\bpx\b", s, re.I):
            return s
    return ""


def main():
    print(f"=== R-RBS-LM-WIKIGLOSS — lead-sentence definition store (srmech {srmech.__version__}) ===")
    t0 = time.time()
    glosses = {}
    n = 0
    with open(ART) as f:
        for line in f:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            n += 1
            title = (d.get("title") or "").strip().lower()
            if not title or "(" in title or ":" in title:        # skip disambig/namespaced titles
                continue
            gl = gloss_of(d.get("text", ""))
            if gl:
                glosses[title] = gl
    OUT.write_text(json.dumps({"wiki": "simplewiki", "articles": n, "glosses": len(glosses),
                               "store": glosses,
                               "attestation": {"source_url": "https://dumps.wikimedia.org/simplewiki/latest/",
                                               "license": "CC-BY-SA-4.0",
                                               "response_sha256": sha256_raw(",".join(sorted(glosses)).encode()).hex(),
                                               "parser_version": f"srmech {srmech.__version__}"}}))
    print(f"  {n} articles -> {len(glosses)} glosses ({time.time()-t0:.1f}s); wrote {OUT.name} ({OUT.stat().st_size/1e6:.1f} MB)")
    for w in ("tomato", "dragon", "volcano", "computer", "music", "earth"):
        print(f"    {w:9}: {glosses.get(w, '(none)')[:110]}")


if __name__ == "__main__":
    main()
