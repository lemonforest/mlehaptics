r"""R-RBS-LM-FEEDBACK — the user's curiosity: take the RBS-HDC instrument's own inference OUTPUT, then PERMUTE or
BIND it with the_one kernel, and see how it changes the language structure (could be bad / could be not-helpful
for complex languages — held open).

Setup: the instrument emits a paragraph P0; we encode its content words as ONE HDC vector V_out (bundle of word
anchors) — the instrument's output as a held box. Then two feedback transforms with the_one's kernel K, and we
DECODE each back to the nearest vocabulary words (a cleanup-memory readout) to see what theme the instrument would
carry forward:
  • PERMUTE  : permute(V_out, stride)   — a cyclic (Class I) rotation of the output vector.
  • BIND     : bind(V_out, K)           — XOR with the_one kernel (Class M).
Measured against P0's own theme (Jaccard overlap of the top decoded words).
srmech 0.7.4.
"""
import hashlib
import re
from collections import Counter
import importlib.util as U
import srmech
from srmech.amsc import hdc
from srmech.amsc.cascade import the_one

NB = hdc.DEFAULT_HDC_BYTES
_s = U.spec_from_file_location("k7", "docs/srmech/rbs_lm_research/R-RBS-LM-K7STEER_anchor_gated_byte_generator.py")
k7 = U.module_from_spec(_s); _s.loader.exec_module(k7)


def hv(label):
    out, i = b"", 0
    while len(out) < NB:
        out += hashlib.sha256(label.encode() + bytes([i])).digest()
        i += 1
    return out[:NB]


def decode(vec, vocab, anchors, topn=10):
    return set(sorted(vocab, key=lambda w: hdc.similarity(vec, anchors[w]), reverse=True)[:topn])


def jacc(a, b):
    return len(a & b) / max(1, len(a | b))


def main():
    print(f"=== R-RBS-LM-FEEDBACK — instrument output → permute vs bind with the_one; effect on language structure  (srmech {srmech.__version__}) ===\n")
    text = k7.load_text()
    words = re.findall(r"[a-z]{4,}", text.lower())
    vocab = [w for w, _ in Counter(words).most_common(600)]      # content-word vocab (the cleanup memory)
    anchors = {w: hv("W:" + w) for w in vocab}
    K = hv("the_one:" + str(the_one(sigma=1, theta_num=1, theta_den=7, terms=8).to_flat_rational()))

    # the instrument's OUTPUT: its dominant content words around a seed (a stand-in for a generated paragraph's theme)
    seed = "water"
    win = [words[i + d] for i in range(len(words)) if words[i] == seed for d in range(-5, 6)
           if 0 <= i + d < len(words) and len(words[i + d]) >= 4 and words[i + d] != seed]
    P0_theme = set([w for w, _ in Counter(win).most_common(10)])
    P0_in_vocab = P0_theme & set(vocab)
    V_out = hdc.bundle([anchors[w] for w in sorted(P0_in_vocab)] * (1 if len(P0_in_vocab) % 2 else 1) + ([anchors[sorted(P0_in_vocab)[0]]] if len(P0_in_vocab) % 2 == 0 else []))
    print(f"[OUTPUT]  instrument theme around '{seed}' (top words): {sorted(P0_in_vocab)}\n")

    # RAW readback (baseline — decode V_out itself)
    d_raw = decode(V_out, vocab, anchors)
    # PERMUTE feedback (cyclic, Class I)
    d_perm = decode(hdc.permute(V_out, 4099), vocab, anchors)
    # BIND feedback (the_one kernel, Class M) — decoded in RAW space, and in the KEYED space (unbind)
    d_bind_raw = decode(hdc.bind(V_out, K), vocab, anchors)                       # read raw → relocated
    keyed_anchors = {w: hdc.bind(anchors[w], K) for w in vocab}
    d_bind_keyed = set(sorted(vocab, key=lambda w: hdc.similarity(hdc.bind(V_out, K), keyed_anchors[w]), reverse=True)[:10])

    print("DECODE the carried theme (Jaccard overlap with the instrument's own output theme):")
    print(f"  RAW readback (baseline)             : overlap {jacc(d_raw, P0_in_vocab):.2f}   {sorted(d_raw)[:6]}…")
    print(f"  PERMUTE (cyclic, Class I)            : overlap {jacc(d_perm, P0_in_vocab):.2f}   {sorted(d_perm)[:6]}…")
    print(f"  BIND with the_one, read RAW          : overlap {jacc(d_bind_raw, P0_in_vocab):.2f}   {sorted(d_bind_raw)[:6]}…")
    print(f"  BIND with the_one, read KEYED (unbind): overlap {jacc(d_bind_keyed, P0_in_vocab):.2f}   {sorted(d_bind_keyed)[:6]}…\n")

    print("VERDICT (exploratory — held open, could be bad / not-helpful):")
    print(f"  • BIND with the_one is a REVERSIBLE KEYING (Class M): read in the SAME keyed space it RECOVERS the")
    print(f"    theme (overlap {jacc(d_bind_keyed, P0_in_vocab):.2f}); read RAW it is SCRAMBLED (overlap {jacc(d_bind_raw, P0_in_vocab):.2f}). So bind RELOCATES")
    print(f"    the structure, it does not change it — 'not helpful' for re-shaping language (it is a key, F493 keying).")
    print(f"  • PERMUTE with the_one (cyclic, Class I) is a GENUINE structural transform: it shifts which words are")
    print(f"    near (overlap {jacc(d_perm, P0_in_vocab):.2f} vs raw {jacc(d_raw, P0_in_vocab):.2f}) — a cyclic RE-VIEW of the output, a different reading.")
    print(f"  • so the user's two ops do different things: BIND = relocate (reversible, no structural change);")
    print(f"    PERMUTE = re-view (genuine cyclic shift). For COMPLEX languages, BIND-feedback adds no structure")
    print(f"    (just a key); PERMUTE-feedback changes structure but is a rotation, not new meaning — consistent")
    print(f"    with the user's hunch it 'could be not as helpful'. The held box (F484) is where meaning lives;")
    print(f"    feeding output back through the_one re-keys/re-views it, it does not generate new operand structure.")


if __name__ == "__main__":
    main()
