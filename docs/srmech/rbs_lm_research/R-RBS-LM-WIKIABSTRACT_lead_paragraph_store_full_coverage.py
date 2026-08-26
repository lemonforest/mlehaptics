r"""R-RBS-LM-WIKIABSTRACT (F788 — finishing F745's documented scale path) — the lead-PARAGRAPH abstract store:
title -> the first ~3 clean sentences of each simplewiki article (multi-sentence, "what X is + a bit more"). This is
the FULL-COVERAGE version of the F745 wiki·abstract chromosome (which only had a 58-article proof cut), built with the
SAME extractor + markup-understanding + attestation as the F760 lead-sentence gloss store — just N sentences, not 1.

Pairs with the gloss store: "what is X" -> the crisp lead sentence (gloss, F760); "tell me about / explain X" or
"tell me more" (depth=long, F763) -> this fuller abstract. Bounded (≤3 sentences, ≤~500 chars) — not the article body.

srmech 0.7.5rc165. Text-only (no encode); no abs; no CAD; CC-BY-SA simplewiki. Run:
  /tmp/srmech_rc165/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-WIKIABSTRACT_...py
"""
import importlib.util as _U
import json
import os
import re
import time
from pathlib import Path
import srmech
from srmech.amsc.format import sha256_raw

_mk_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "R-RBS-LM-MARKUPGRAMMAR_class_bf_form_layer_understand_not_strip.py")
_mk_spec = _U.spec_from_file_location("markupgrammar", _mk_path)
MK = _U.module_from_spec(_mk_spec); _mk_spec.loader.exec_module(MK)

ART = Path.home() / "corpora" / "wikipedia" / "simplewiki_extracted" / "articles.jsonl"
OUT = Path.home() / "corpora" / "wikipedia" / "simplewiki_abstracts.json"
_SENT = re.compile(r"(?<=[.!?])\s+")
MAX_SENTS = 3


def abstract_of(text):
    """The first ≤MAX_SENTS clean sentences (the lead paragraph), markup UNDERSTOOD (F764). '' if none usable."""
    clean, _edges = MK.understand_markup((text or "")[:2200].replace("\n", " "))
    sents = []
    for sent in _SENT.split(clean)[:12]:
        s = sent.strip()
        if 12 <= len(s) <= 400 and not re.search(r"\bthumb\b|\bpx\b", s, re.I):
            sents.append(s)
            if len(sents) >= MAX_SENTS:
                break
    return " ".join(sents)


def main():
    print(f"=== R-RBS-LM-WIKIABSTRACT — lead-paragraph abstract store (srmech {srmech.__version__}) ===")
    t0 = time.time()
    abstracts = {}
    n = 0
    with open(ART) as f:
        for line in f:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            n += 1
            title = (d.get("title") or "").strip().lower()
            if not title or "(" in title or ":" in title:
                continue
            ab = abstract_of(d.get("text", ""))
            if ab and ab.count(" ") >= 4:                     # need a real abstract, not a stub
                abstracts[title] = ab
    OUT.write_text(json.dumps({"wiki": "simplewiki", "articles": n, "abstracts": len(abstracts),
                               "max_sentences": MAX_SENTS, "store": abstracts,
                               "attestation": {"source_url": "https://dumps.wikimedia.org/simplewiki/latest/",
                                               "license": "CC-BY-SA-4.0",
                                               "response_sha256": sha256_raw(",".join(sorted(abstracts)).encode()).hex(),
                                               "parser_version": f"srmech {srmech.__version__}"}}))
    print(f"  {n} articles -> {len(abstracts)} abstracts ({time.time()-t0:.1f}s); wrote {OUT.name} ({OUT.stat().st_size/1e6:.1f} MB)")
    for w in ("ketchup", "tomato", "volcano", "computer", "music"):
        print(f"    {w:9}: {abstracts.get(w, '(none)')[:240]}")


if __name__ == "__main__":
    main()
