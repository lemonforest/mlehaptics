"""rc209 vs rc217 SEAM parity: run the ACTUAL WIKIKERNEL build_edges_topk on a fixed corpus and hash
(vocab, edges, weights). If the hash matches across the two srmech versions, the shard encode is
bit-consistent across the power-outage resume boundary (shard 114). Run under each venv."""
import json, sys, importlib.util
KDIR = "/home/skirklan/GitHub/mlehaptics/.claude/worktrees/strange-elgamal-feac0c/docs/srmech/rbs_lm_research"
sys.path.insert(0, KDIR)
spec = importlib.util.spec_from_file_location(
    "wk", KDIR + "/R-RBS-LM-WIKIKERNEL_big_wiki_word_association_class_l_kernel_reference.py")
wk = importlib.util.module_from_spec(spec); spec.loader.exec_module(wk)
import srmech

# a fixed multi-"article" corpus with the kinds of tokens that stress a tokenizer:
# apostrophes, unicode, digits, casing, punctuation, hyphenation.
CORPUS = [
    "The Victoria and Albert Museum in London holds a's acquisition from South America.",
    "Café society flourished; naïve résumé writers can't spell 'accommodation' well.",
    "E = mc^2 was Einstein's 1905 result — special relativity, published in Annalen der Physik.",
    "Anti-establishment, well-being, and state-of-the-art hyphenations test the boundary rules.",
    "DNA, RNA and ATP are biomolecules; the mitochondria (plural of mitochondrion) make ATP.",
] * 40  # replicate so co-occurrence weights accumulate

vocab, idx, edges, weights, freq, dropped = wk.build_edges_topk(
    wk._ListSource(CORPUS) if hasattr(wk, "_ListSource") else CORPUS, window=4, vocab_cap=None)

ew = sorted(zip([list(e) for e in edges], [float(w) for w in weights]))  # (edge, weight) pairs, edge-sorted
# the DISCRIMINATING hash EXCLUDES the version string (else it always differs)
core = json.dumps({
    "n_vocab": len(vocab), "vocab": list(vocab),
    "n_edges": len(ew), "edges_weights": ew,
    "freq": {k: freq[k] for k in sorted(freq)},
}, sort_keys=True, default=str)
edges_sorted = ew
from srmech.amsc.format import sha256_bytes           # Class-A content hash (discipline: no raw hashlib)
h = sha256_bytes(core.encode())
print("VERSION=%s  n_vocab=%d  n_edges=%d  CORE_SHA256=%s" % (srmech.__version__, len(vocab), len(edges_sorted), h))
