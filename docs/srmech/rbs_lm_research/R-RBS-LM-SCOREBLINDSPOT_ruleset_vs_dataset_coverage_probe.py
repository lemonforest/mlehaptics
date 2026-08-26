r"""R-RBS-LM-SCOREBLINDSPOT (#226) — the rulesets-vs-dataset blind-spot ratchet for the SCORE kernel: run
understand_score over real enwiki <score> blocks, measure note-extraction coverage, and census the \commands appearing
(so the ones that carry PITCH meaning we drop — e.g. \ottava octave-shift, chord <>, \transpose — surface as gaps).
Not training; coverage only. <score> is rare so this streams wide.

srmech 0.9.0rc209. No numpy, no Python abs builtin, no Counter, no CAD. Run in the background:
  MAX_ARTICLES=60000 /tmp/srmech_v/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-SCOREBLINDSPOT_...py
"""
import bz2, importlib.util, os, re, sys, time
import xml.etree.ElementTree as ET
from pathlib import Path

DUMP = str(Path.home() / "corpora" / "wikipedia" / "enwiki-latest-pages-articles.xml.bz2")
N = int(os.environ.get("MAX_ARTICLES", "60000"))
_SCORE = re.compile(r"<score\b([^>]*)>(.*?)</score>", re.S | re.I)
_CMD = re.compile(r"\\([a-zA-Z]+)")
# commands that carry PITCH/STRUCTURE meaning (dropping them loses information — the real score blind spots)
PITCH_BEARING = {"ottava", "transpose", "relative", "transposition", "clef", "key"}


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); mod = importlib.util.module_from_spec(spec)
    sv = sys.argv; sys.argv = ["x"]
    try: spec.loader.exec_module(mod)
    except SystemExit: pass
    sys.argv = sv; return mod


K = _load("scorek", "docs/srmech/rbs_lm_research/R-RBS-LM-SCOREKERNEL_music_notation_sublanguage_pitch_class_cycle.py")


def main():
    t0 = time.time()
    blocks = 0; with_note = 0; zero = 0; abc = 0; chords = 0
    cmds = {}; note_hist = []
    n = 0
    with bz2.open(DUMP, "rt", encoding="utf-8") as fh:
        for _e, el in ET.iterparse(fh, events=("end",)):
            if (el.tag.endswith("}text") or el.tag == "text") and el.text:
                n += 1; raw = el.text
                for attr, body in _SCORE.findall(raw):
                    if len(body) > 6000:
                        continue
                    blocks += 1
                    lang = "abc" if re.search(r"lang\s*=\s*\"?abc", attr, re.I) else None
                    r = K.understand_score(body, lang)
                    if r["lang"] == "abc":
                        abc += 1
                    if "<" in body and ">" in body:
                        chords += 1
                    if r["n_notes"]:
                        with_note += 1; note_hist.append(r["n_notes"])
                    else:
                        zero += 1
                    for c in _CMD.findall(body):
                        cmds[c] = cmds.get(c, 0) + 1
                if n >= N:
                    el.clear(); break
            el.clear()
    avg = sum(note_hist) / max(1, len(note_hist))
    print(f"=== SCOREBLINDSPOT — ruleset-vs-dataset <score> coverage ({n} articles, {blocks:,} score blocks, {time.time()-t0:.0f}s) ===\n")
    print(f"  COVERAGE: >=1 note {with_note:,}/{blocks:,} = {100*with_note/max(1,blocks):.0f}%   0-note {zero:,}   "
          f"avg notes/block {avg:.1f}   ABC {abc:,}   chord-bearing <> {chords:,}")
    print("\n  TOP-30 \\commands in score blocks (PITCH-BEARING ones = blind spots we currently drop):")
    top = sorted(cmds.items(), key=lambda kv: -kv[1])[:30]
    for i in range(0, len(top), 3):
        row = top[i:i + 3]
        print("    " + "   ".join(f"{'*' if c in PITCH_BEARING else ' '}\\{c:<14} {n:>5}" for c, n in row))
    print("\n  (* = pitch/structure-bearing: dropping it loses information — the score kernel's real gaps)")


if __name__ == "__main__":
    main()
