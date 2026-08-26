#!/usr/bin/env python3
"""R-RBS-SNN-5 — the THREE-KERNEL lean hybrid: a coherent sentence is assembled from
three SEPARABLE, individually-clean kernels bound at query time (NOT one dense matrix).

The user's question: can we keep a lean structure hybrid (instead of a super-dense LLM)
where the structure kernel carries ONLY the unbiased data and a separate layer maps to
the actual sentence-binding words? Answer (this demo, on our OWN findings):

  GRAMMAR kernel   role anchors {SUBJ,VERB,OBJ} + the S-V-O frame — CLOSED, shared,
                   domain-agnostic (the_one's "grammar"/syntax side, F408/F164)
  LEXICON kernel   {word → hypervector} — SOURCED (the words; F408 semantics)
  DOMAIN-lean      the relationship triple (subj, rel, obj) — render-free, from the
                   RBS-SNN store (F426); carries WHICH relationship, no grammar/words

  sentence = bundle( bind(SUBJ,lex[s]), bind(VERB,lex[v]), bind(OBJ,lex[o]) )   (F155/F156)
  read     = for role in frame: cleanup( unbind(sentence, role) ) → word

The dense LLM ENTANGLES all three in one weight matrix; the lean hybrid keeps them
separate and binds at query — so a new sentence adds only a tiny domain-triple, and the
grammar + lexicon kernels are REUSED unchanged (demonstrated by the swap test).

srmech-first: bind/bundle/similarity (Class M); the F155/F156 Klein-4 role-filler
mechanism. numpy-free. Defensive / no-lineage. No new A-N class.
"""
import random
from srmech.amsc import hdc

D = 1024                                   # bytes; large enough for clean cleanup
RNG = random.Random(20260606)


def hv():
    return bytes(RNG.getrandbits(8) for _ in range(D))


def unbind(sent, role):
    return hdc.bind(sent, role)            # XOR self-inverse


def cleanup(noisy, lexicon):
    return max(lexicon, key=lambda w: hdc.similarity(noisy, lexicon[w]))


def main():
    # ---- GRAMMAR kernel (closed, shared, domain-agnostic) ----
    roles = {r: hv() for r in ("SUBJ", "VERB", "OBJ")}
    FRAME = ("SUBJ", "VERB", "OBJ")        # S-V-O; surface render "the {s} {v} the {o}"

    # ---- LEXICON kernel (sourced — the actual words) ----
    words = ["boundary", "bulk", "fusion", "gap", "gate", "duplicate", "lock", "couplings",
             "holds", "resolves", "detects", "recovers", "spectrum", "store"]
    lexicon = {w: hv() for w in words}

    # ---- DOMAIN-lean kernel (the relationships, from the RBS-SNN store / real findings) ----
    domain_triples = [
        ("F425", ("boundary", "holds", "bulk")),       # F425: the boundary holds the bulk
        ("F421", ("fusion", "resolves", "gap")),        # F421: the fusion op resolves the gap
        ("F428", ("gate", "detects", "duplicate")),     # F428: the self-check gate detects a duplicate
        ("F429", ("lock", "recovers", "couplings")),    # F429: the phase-lock recovers the couplings
    ]

    def encode(triple):                    # the bind (F155/F156)
        s, v, o = triple
        return hdc.bundle([hdc.bind(roles["SUBJ"], lexicon[s]),
                           hdc.bind(roles["VERB"], lexicon[v]),
                           hdc.bind(roles["OBJ"], lexicon[o])])

    def read(sent):                        # unbind by role + cleanup, in frame order
        return tuple(cleanup(unbind(sent, roles[r]), lexicon) for r in FRAME)

    print("=== three-kernel lean hybrid — sentences about our own findings ===")
    print("(GRAMMAR frame + LEXICON + DOMAIN-lean, bound via srmech Class-M; F155/F156 mechanism)\n")
    exact = 0
    for fid, triple in domain_triples:
        got = read(encode(triple))
        ok = got == triple
        exact += ok
        s, v, o = got
        print(f"  {fid} domain-lean {triple}")
        print(f"       → bound+read: \"the {s} {v} the {o}\"   [{'exact ✓' if ok else 'DRIFT ✗'}]")
    print(f"\nreadback fidelity: {exact}/{len(domain_triples)} sentences recovered EXACTLY "
          f"(the bind is clean — lean, not lossy)")

    # ---- SWAP TEST: the kernels are separable + reusable ----
    print("\n--- swap test: same GRAMMAR + LEXICON kernels, swap the DOMAIN-lean triple ---")
    novel = ("spectrum", "holds", "store")             # a triple NOT in the list above
    got = read(encode(novel))
    print(f"  new domain triple {novel} (grammar+lexicon UNCHANGED)")
    print(f"       → \"the {got[0]} {got[1]} the {got[2]}\"   "
          f"[{'exact ✓' if got == novel else 'drift'}]")
    print("  ⇒ a NEW sentence added only a tiny domain-triple; grammar + lexicon were REUSED.")

    # ---- the lean-vs-dense ledger ----
    print("\n--- lean hybrid vs dense LLM (what each stores) ---")
    print(f"  GRAMMAR kernel : {len(roles)} role anchors + 1 frame   (CLOSED — shared by ALL sentences)")
    print(f"  LEXICON kernel : {len(lexicon)} word vectors           (SOURCED — shared by ALL sentences)")
    print(f"  DOMAIN-lean    : {len(domain_triples)+1} triples       (the only per-sentence cost)")
    print(f"  dense LLM      : 1 entangled weight matrix holding grammar+lexicon+content FUSED")
    print(f"  ⇒ the lean hybrid pays grammar+lexicon ONCE; each new sentence = one small triple.")
    return 0 if exact == len(domain_triples) else 1


if __name__ == "__main__":
    raise SystemExit(main())
