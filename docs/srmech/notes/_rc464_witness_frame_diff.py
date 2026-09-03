"""rc464 (`#T1188`) — the corpus-witness frame differ, committed as provenance.

`tests/test_search_glyph_tokenizer_rc416.py`'s WITNESS_RC416 note attributes each
move frame by frame. This is the script that produced the rc464 stage-3
attribution (0 added, 2 removed, 12 changed; 763 -> 761). It is committed under
the computational-provenance discipline: a re-pin whose attribution cannot be
reproduced is a reading of the diff, not a measurement.

Usage — dump one tree's corpus, then difference two dumps:

    python3 _rc464_witness_frame_diff.py <package-root> <out.json>

The rc464 run compared a `git archive` of docs/srmech at 3d404205d (the tip
before the removal, which reproduced b213cf4f... exactly) against the working
tree.
"""
import json
import subprocess
import sys

root = sys.argv[1]
out = subprocess.run(
    [sys.executable, "-c",
     "import sys; sys.path.insert(0, %r);\n"
     "from srmech.introspect.search import _build_frames;\n"
     "fr, w = _build_frames('all');\n"
     "import json; print(json.dumps({'witness': w, 'frames': "
     "{f.kind + ':' + f.name: f.blob.hex() for f in fr}}))" % root],
    capture_output=True, text=True, cwd=root)
if out.returncode != 0:
    print(out.stderr[-2000:]); sys.exit(1)
print(out.stdout.strip()[:120] + " ...")
open(sys.argv[2], "w", encoding="utf-8").write(out.stdout)
