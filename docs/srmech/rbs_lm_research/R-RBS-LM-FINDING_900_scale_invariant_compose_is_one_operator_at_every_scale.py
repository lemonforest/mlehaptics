"""F900 — the byte/glyph scaffolding is ONE scale-invariant operator (role-filler
bundle, C1) repeated at every scale; word-hash is its DUAL (a content-address
atom-mint, scale-invariant in FORM); and the EXISTING L1/L2/L3 ladder breaks
scale-invariance because it uses a DIFFERENT, similarity-destroying operator
(chained bind, no positions).

Composes F899 (the packaged encode is word-hash, byte-blind). The user's 2026-06-21
reframe: don't discard word-hash — see it as "a fractal form of byte-hash" (a
scale-invariance coherency), AND follow the next fractal movement (hash a coherent
string of words BEFORE it becomes a sentence). This probe grounds that reframe with
srmech klein4 (numpy-free, pure-Python OK).

Run from docs/srmech/python:  python ../rbs_lm_research/R-RBS-LM-FINDING_900_*.py

MEASURED (srmech 0.9.0, D=2048, klein4 chance ~= 0.25; rbs_lm + klein4 surfaces are
identical rc13..rc16 so the version is not load-bearing):

(A) atom-mint (word-hash) vs compose (byte/glyph) at the WORD scale -- morphology
      cat/cot      atom=0.250   compose=0.562
      cat/car      atom=0.237   compose=0.588
      walk/walked  atom=0.255   compose=0.708
      run/running  atom=0.250   compose=0.566
      cat/dog      atom=0.248   compose=0.262   (correctly stays at chance)

(B) SCALE-INVARIANCE of the single compose operator C1 -- change ONE part of an
    n-part whole; similarity stays in a graceful, well-above-chance band at EVERY
    scale (the fractal signature):
      byte->word     n=8  sim=0.733
      word->phrase   n=5  sim=0.625
      phrase->sent   n=3  sim=0.698

(C) the EXISTING ladder (encode_bigram_l1 / _skeleton_l2 / _sentence_l3 = chained
    bind, no positions) is NOT scale-invariant -- the same one-part change collapses
    to chance regardless of n:
      bigram_l1   cat/sat vs cat/ran      = 0.249
      skeleton_l2 ...(the,mat) vs (the,dog)= 0.238
      sentence_l3 ...mat vs ...rug (1/5)   = 0.246

READING: C1 (role-filler bundle, what klein4_encode_bytes and ContextSubstrate.
encode_context already use) IS the scale-free fractal compositor; atom-mint
(klein4_random(seed=content_hash)) IS its dual at every scale (the "fractal form of
byte-hash"); the bigram/skeleton/sentence ladder uses a THIRD, non-invariant operator
and should be rebuilt on C1. Coherence == scale-invariance: a coherent word-string
has the same 1-part-change signature as a word and a sentence; an incoherent one
breaks the self-similarity (a native coherence/hallucination detector -- the
introspection the user wants).
"""
import sys
sys.path.insert(0, ".")  # run from docs/srmech/python
from srmech.amsc import hdc
from srmech.amsc import format as amsc_format
from srmech.rbs_lm import substrate as sub

D = 2048
def _fl(q): return float(q.as_float()) if hasattr(q, "as_float") else float(q)
def sim(a, b): return _fl(hdc.klein4_similarity(a, b))

# --- C1: the single scale-invariant compositor (role-filler bundle) ----------
# Same SHAPE as hdc.klein4_encode_bytes and ContextSubstrate.encode_context, but
# over ARBITRARY part-vectors -> it recurses up the ladder unchanged.
_POS = {}
def pos_key(i):
    if i not in _POS:
        _POS[i] = hdc.klein4_random(D, seed=int(amsc_format.sha256_bytes(
            f"__pos_{i}__".encode())[:8], 16))
    return _POS[i]

def compose(parts):
    """C1 -- bundle of position-bound parts; SAME operator at every scale."""
    bound = [hdc.klein4_bind(p, pos_key(i)) for i, p in enumerate(parts)]
    if len(bound) == 1:
        return bound[0]
    if len(bound) % 2 == 0:                  # klein4_bundle needs an odd count
        bound = bound + [pos_key(10_000)]    # fixed neutral pad (never drop a part)
    return hdc.klein4_bundle(*bound)

def atom(content_hash_seed):
    """The DUAL -- a content-addressed random atom. atom(byte) and atom(word) and
    atom(phrase) are the SAME operation at different scales (word-hash = fractal
    form of byte-hash)."""
    return hdc.klein4_random(D, seed=content_hash_seed)

def byte_atom(b):   return atom(b)                                    # ground alphabet (256)
def word_vec(w):    return compose([byte_atom(b) for b in w.encode("utf-8")])  # byte->word
def phrase_vec(ws): return compose([word_vec(w) for w in ws])        # word->phrase (skeleton)
def sent_vec(phrs): return compose([phrase_vec(p) for p in phrs])    # phrase->sentence


def main():
    print("(A) atom-mint (word-hash) vs compose (byte/glyph) at word scale (chance~0.25)")
    for a, b in [("cat","cot"),("cat","car"),("walk","walked"),("run","running"),("cat","dog")]:
        s_atom = sim(sub.encode_word_k4(a, D=D, sector=0, hex_chars=16),
                     sub.encode_word_k4(b, D=D, sector=0, hex_chars=16))
        print(f"   {a+'/'+b:<14} atom={s_atom:.3f}   compose={sim(word_vec(a), word_vec(b)):.3f}")

    print("\n(B) SCALE-INVARIANCE of compose C1 (change ONE part of n)")
    print(f"   byte->word   n=8 sim={sim(word_vec('spectral'), word_vec('specXral')):.3f}")
    ph1=["the","cat","sat","on","mat"]; ph2=["the","cat","zebra","on","mat"]
    print(f"   word->phrase n=5 sim={sim(phrase_vec(ph1), phrase_vec(ph2)):.3f}")
    s1=[["the","cat","sat"],["on","the","mat"],["in","the","sun"]]
    s2=[["the","cat","sat"],["by","the","door"],["in","the","sun"]]
    print(f"   phrase->sent n=3 sim={sim(sent_vec(s1), sent_vec(s2)):.3f}")

    print("\n(C) EXISTING ladder (chained bind, no positions) -- NOT scale-invariant")
    print(f"   bigram_l1   : {sim(sub.encode_bigram_l1('cat','sat',D=D,hex_chars=16), sub.encode_bigram_l1('cat','ran',D=D,hex_chars=16)):.3f}")
    print(f"   skeleton_l2 : {sim(sub.encode_skeleton_l2(('the','cat'),('the','mat'),D=D,hex_chars=16), sub.encode_skeleton_l2(('the','cat'),('the','dog'),D=D,hex_chars=16)):.3f}")
    print(f"   sentence_l3 : {sim(sub.encode_sentence_l3(['the','cat','sat','on','mat'],D=D,hex_chars=16), sub.encode_sentence_l3(['the','cat','sat','on','rug'],D=D,hex_chars=16)):.3f}")


if __name__ == "__main__":
    main()
