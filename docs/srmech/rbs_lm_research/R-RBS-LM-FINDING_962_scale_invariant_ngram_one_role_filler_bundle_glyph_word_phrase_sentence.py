"""F962 — the n-gram is SCALE-INVARIANT (user): the SAME position-keyed role-filler bind+bundle is the n-gram
at EVERY scale -- bytes/glyphs->word (encode_word_byteglyph = klein4_encode_bytes, docstring: 'the
scale-invariant role-filler bundle over the word's UTF-8 bytes'), words->phrase (encode_context), phrases->
sentence (same op). ONE recursive operation, dynamic width (F961: operating_k 1/2/3/4). The byte/glyph,
word, phrase, sentence 'levels' are not separate schemes -- they're one n-gram applied recursively, each
level's output the next level's unit. srmech rc79; no srmech fix needed (already explicit)."""
from srmech.rbs_lm import substrate as S
from srmech.amsc import hdc
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
cs=S.ContextSubstrate(D=8192, hex_chars=16)
def ngram(unit_hvs):                                   # THE scale-invariant n-gram (== encode_context, on HVs)
    return cs.bundle_odd([hdc.klein4_bind(cs.pos_key(p), u) for p,u in enumerate(unit_hvs)])
# LEVEL 0 bytes->word: srmech's own encode_word_byteglyph (the same role-filler bundle over UTF-8 bytes)
w_fourth=cs.enc('fourth'); w_month=cs.enc('month'); w_of=cs.enc('of'); w_year=cs.enc('year')
# LEVEL 1 words->phrase: SAME n-gram on word HVs
ph1=ngram([w_fourth,w_month]); ph2=ngram([w_of,w_year])
# LEVEL 2 phrases->sentence: SAME n-gram on phrase HVs
sent=ngram([ph1,ph2])
print('one ngram() applied recursively:')
print('  L0 bytes->word   : encode_word_byteglyph (srmech, == role-filler bundle over bytes)')
print('  L1 words->phrase : ngram([fourth,month]) -> phrase HV')
print('  L2 phrases->sent : ngram([ph1,ph2]) -> sentence HV ; distinct from its parts?',
      fl(hdc.klein4_similarity(sent,ph1))<0.9 and fl(hdc.klein4_similarity(sent,w_fourth))<0.9)
print('=> SAME position-keyed role-filler bundle at every scale (glyph->word->phrase->sentence) = scale-invariant n-gram')
