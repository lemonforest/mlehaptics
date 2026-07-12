"""rc79 published-wheel verification (gate 5) — run inside a numpy-ABSENT venv
created OUTSIDE the source tree, after `pip install`ing srmech==0.9.0rc79 from
TestPyPI. Verifies: version, numpy absent, HAS_NATIVE True, next_token_coherence
present, and the F945 BRANCH/COHERENT/STOP trichotomy reproduced through the
published wheel.

This file is a notes-only helper (not packaged, not a test); it is the exact
gate-5 probe so the verification is re-derivable."""
import sys

import srmech
from srmech.amsc import hdc
from srmech.amsc.q import Q
from srmech.rbs_lm import RBSLMInferenceSubstrate, CoherenceReadout

assert srmech.__version__ == "0.9.0rc79", srmech.__version__
assert "numpy" not in sys.modules, "numpy must be absent"
try:
    import numpy  # noqa: F401
    raise SystemExit("FAIL: numpy is importable in this venv")
except ImportError:
    pass
ns = srmech.native_status()
assert ns["has_native"] is True, ns
assert hasattr(RBSLMInferenceSubstrate, "next_token_coherence")

PARAMS = {"substrate": {"D": 8192, "token_seed_hex_chars": 16},
          "inference": {"instrument": {"operating_k": 1, "operating_temperature": 1.0,
                                       "memory_capacity": 1000, "default_max_tokens": 8,
                                       "learn_seed": 1234}}}
VOCAB = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"]
EDGES = [("a", "b"), ("a", "c"), ("b", "d"), ("c", "d"), ("d", "e")]


def tome(src_edges):
    sub = RBSLMInferenceSubstrate.from_params(PARAMS)
    sub.vocab = list(VOCAB)
    sub.vocab_idx = {w: i for i, w in enumerate(VOCAB)}
    sub.vocab_vecs = [sub.ctx.enc(w) for w in VOCAB]
    assoc = [hdc.klein4_bind(sub.ctx.encode_context([p]), sub.ctx.enc(n))
             for p, n in src_edges]
    sub.M = sub.ctx.bundle_odd(assoc)
    sub.n_learned = len(src_edges)
    return sub


bysrc = {}
for p, n in EDGES:
    bysrc.setdefault(p, []).append((p, n))

ra = tome(bysrc["a"]).next_token_coherence(["a"], top_k=3)
assert ra.verdict == "BRANCH", ra.verdict
assert set(ra.branch_candidates) == {"b", "c"}, ra.branch_candidates
for src, nxt in (("b", "d"), ("c", "d"), ("d", "e")):
    r = tome(bysrc[src]).next_token_coherence([src], top_k=3)
    assert r.verdict == "COHERENT", (src, r.verdict)
    assert r.candidates_topk[0] == nxt
rn = tome(bysrc["a"]).next_token_coherence(["zzznoise_unlearned"], top_k=3)
assert rn.verdict == "STOP", rn.verdict

# raw-vs-softmax margin contrast (gate 2) through the published wheel
sub = tome(bysrc["d"])
rc = sub.next_token_coherence(["d"])
_, probs = sub.next_token_distribution(["d"], temperature=1.0)
ps = sorted((float(p) for p in probs), reverse=True)
assert float(rc.collapse_margin) > (ps[0] - ps[1])

# floor no-magic + exact-Q decision path
assert rc.noise_floor == Q(17, 50)
assert isinstance(rc.collapse_margin, Q)

print("rc79 WHEEL VERIFY OK:",
      "version", srmech.__version__, "| has_native", ns["has_native"],
      "| a=BRANCH b/c/d=COHERENT noise=STOP | raw>softmax margin",
      round(float(rc.collapse_margin), 3), ">", round(ps[0] - ps[1], 3),
      "| floor", str(rc.noise_floor))
