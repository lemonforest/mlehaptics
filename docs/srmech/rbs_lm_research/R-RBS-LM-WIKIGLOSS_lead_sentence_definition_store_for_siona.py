r"""R-RBS-LM-WIKIGLOSS (F760 infra) — the real DEFINITION tier: title -> the lead-sentence gloss of each simplewiki
article ("what X IS"), so Siona answers "what is a tomato?" with a definition, not a relations dump (the F759 next-inch).

The lead sentence of a simplewiki article IS a definition (e.g. "The tomato (Solanum lycopersicum) is a … berry."). We
strip a leading image/markup block (thumb|WxHpx|caption.) per the §35/F698 "wiki adapter MUST strip content-bearing
markup" discipline, then take the first sentence. Compact title->gloss side-store (the EXACT definition tier; pairs with
the F754/F757 relational side-stores + the genome self — F584/F119 two-tier).

srmech 0.7.5rc155. Text-only (no encode); no abs; no CAD; CC-BY-SA simplewiki. Run (background):
  /tmp/srmech_rc155/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-WIKIGLOSS_...py
"""
import json
import re
import time
from pathlib import Path
import srmech
from srmech.amsc.format import sha256_raw

ART = Path.home() / "corpora" / "wikipedia" / "simplewiki_extracted" / "articles.jsonl"
OUT = Path.home() / "corpora" / "wikipedia" / "simplewiki_glosses.json"
_MARKUP = re.compile(r"^(thumb|left|right|file:|image:|\[\[|\{\{)", re.I)
_SENT = re.compile(r"(?<=[.!?])\s+")


def gloss_of(text):
    """The first MARKUP-FREE lead sentence = the definition. Skips image-caption junk ('…thumb|right|250px|…')
    that litters some leads (F698 markup discipline). '' if none usable in the first few sentences."""
    lead = (text or "").strip().replace("\n", " ")
    for sent in _SENT.split(lead)[:8]:
        s = sent.strip()
        if 12 <= len(s) <= 400 and "|" not in s and not re.search(r"thumb|\bpx\b|\[\[|\{\{|File:|Image:", s, re.I):
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
