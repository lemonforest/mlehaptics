r"""R-RBS-LM-CHESSRULES (the user's question, 2026-06-08): "when it looks so simple now -- this must be exactly like
chess piece move rules. Or it could be. Both?"

THE ANSWER: BOTH -- and the both-ness IS the no-single-truth law (F626). Chess piece move rules are the cleanest instance
of the F631 'we SEE the rules, we don't teach them' realization, AND they carry a second faithful description we already
built in the chess-spectral notebook -- so chess proves a seen rule has TWO languages of math at once:

  (1) EXACTLY LIKE verb forms (the SEEN GENERATOR, Class C): a bishop's moves = a SEEN rule (diagonal slide -- a generating
      rotate over the board lattice), NOT a learned set of (position -> legal-moves) pairs. You don't TEACH chess moves by
      showing a million games; you SEE the rule (it generates every legal move from piece + square, BIT-EXACT, zero games).
      The 'irregular' exceptions -- castling, en passant, promotion, the pawn double-step + diagonal-only capture -- are the
      SEEN-EXCEPTION dictionary (the rule FAILS on them, so they're stored once, content-addressed). This is EXACTLY the
      F629/F631 shape: piece = lemma, legal move = inflection (a rotate over an axis-lattice), exceptions = the small dict.

  (2) AND ALSO a SPECTRAL OBJECT (the Class-L reading, the chess-spectral notebook): the same move rule defines a GRAPH on
      the board (the knight's-move graph), and that graph has a Laplacian eigenspectrum -- a fixed, SEEN, computed object
      (the chess-spectral D_4/B_4 piece-graph spectra). The move rule is BOTH a seen generator (Class C) AND a spectral
      structure (Class L). These are the F626 TWO LANGUAGES OF MATH for one invariant move-rule, neither privileged.

So 'both' is not a hedge -- it's the law: a seen rule is one invariant object with two truths (the generator and the
spectrum). Chess is the case where we have BOTH attested, so it makes the F631 realization concrete in two languages.

srmech 0.7.5rc6: amsc.laplacian.{dense_laplacian, jacobi_eigvals} (Class L -- the move-graph spectrum); amsc.format.
sha256_bytes (the content-addressed exception tomes). The seen generators = integer-lattice cascades (add). No abs();
no CAD; no Workflow; no sub-agents.
"""
import srmech
from srmech.amsc import laplacian, format as fmt

B = 5                                                              # a 5x5 board (keeps the eigendecomp small + native)
def sq(r, c): return r * B + c
def on(r, c): return 0 <= r < B and 0 <= c < B


def knight_moves(r, c):                                            # the SEEN generator (Class C): 8 L-shaped offsets
    offs = [(1, 2), (2, 1), (-1, 2), (-2, 1), (1, -2), (2, -1), (-1, -2), (-2, -1)]
    return [(r + dr, c + dc) for dr, dc in offs if on(r + dr, c + dc)]


def bishop_moves(r, c):                                            # the SEEN generator (Class C): diagonal slides
    out = []
    for dr, dc in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
        nr, nc = r + dr, c + dc
        while on(nr, nc):
            out.append((nr, nc)); nr += dr; nc += dc
    return out


def main():
    print(f"=== R-RBS-LM-CHESSRULES — chess piece moves: a SEEN rule (like verb forms) AND a spectral object -- BOTH  (srmech {srmech.__version__}) ===\n")

    # (1) EXACTLY LIKE verb forms: the SEEN GENERATOR (Class C) -- generates legal moves with ZERO games taught
    print("(1) THE SEEN GENERATOR (Class C) -- like walk->walked, generated zero-corpus (no games taught):")
    print(f"    knight from d-ish center (2,2): {knight_moves(2, 2)}   (8 SEEN L-moves -- a generating rotate)")
    print(f"    knight from corner       (0,0): {knight_moves(0, 0)}   (the SAME rule, fewer on-board)")
    print(f"    bishop from center       (2,2): {bishop_moves(2, 2)}")
    print(f"    -> the rule GENERATES every legal move from piece + square, BIT-EXACT. Not a learned (pos->moves) table.\n")

    # the SEEN-EXCEPTION dictionary (the F629 pattern): the rule FAILS -> stored, content-addressed
    print("(2) THE SEEN-EXCEPTION DICTIONARY (the F629 shape) -- the simple rule FAILS, so it's stored once:")
    EXCEPTIONS = {                                                 # the moves no simple generator derives
        "castling":    "king+rook compound move (not on the king's 1-square generator)",
        "en_passant":  "pawn captures a just-passed pawn (not on the diagonal-capture generator)",
        "promotion":   "pawn reaching the last rank becomes another piece (a type change, not a move)",
        "pawn_double": "pawn's first move may be 2 squares (not on the forward-1 generator)",
    }
    for name, desc in EXCEPTIONS.items():
        addr = fmt.sha256_bytes(f"rule-exception:{name}".encode())[:8]
        print(f"    exception '{name:<11}' -> addr {addr}  ({desc})")
    print(f"    -> EXACTLY go->went / child->children: the generator covers the regular case, the irregulars are SEEN")
    print(f"    exceptions stored once. piece = lemma; legal move = inflection (a rotate); exceptions = the small dict.\n")

    # (3) AND ALSO a SPECTRAL OBJECT (Class L) -- the same move rule's GRAPH has a SEEN Laplacian spectrum
    print("(3) THE SAME RULE, SECOND LANGUAGE -- the SPECTRAL OBJECT (Class L, the chess-spectral notebook reading):")
    edges = set()
    for r in range(B):
        for c in range(B):
            for nr, nc in knight_moves(r, c):
                a, b = sq(r, c), sq(nr, nc)
                edges.add((min(a, b), max(a, b)))                  # undirected knight-move graph
    edges = sorted(edges); weights = [1.0] * len(edges)
    L = laplacian.dense_laplacian(B * B, edges, weights)
    evals = sorted(float(x) for x in laplacian.jacobi_eigvals(L))
    zeros = sum(1 for e in evals if abs(e) < 1e-9)                 # # near-zero eigenvalues = # connected components
    print(f"    knight-move graph on {B}x{B}: {B*B} squares, {len(edges)} edges (all SEEN from the rule, no games)")
    print(f"    Laplacian spectrum (Class L): lambda_min={evals[0]:.4f}  lambda_max={evals[-1]:.4f}  (zero-eigs={zeros} => {zeros} component(s))")
    print(f"    smallest few: {[round(e,3) for e in evals[:4]]}   largest few: {[round(e,3) for e in evals[-4:]]}")
    print(f"    -> the move rule is ALSO an eigen-object: a fixed, SEEN, COMPUTED spectrum (the D_4/B_4 piece-graph")
    print(f"    spectra of the chess-spectral notebook). Same invariant rule -- a second faithful language of math.\n")

    print("VERDICT (exactly like verb forms, or a spectral object -- both?):")
    print(f"  • BOTH -- and 'both' is the LAW (F626), not a hedge. A chess piece move rule is ONE invariant object with TWO")
    print(f"    faithful descriptions: (a) the SEEN GENERATOR (Class C) -- a rotate over the board lattice that produces")
    print(f"    every legal move bit-exact with zero games taught, plus a small SEEN-exception dictionary (castling / en")
    print(f"    passant / promotion / pawn-double = go->went / child->children); and (b) the SPECTRAL OBJECT (Class L) --")
    print(f"    the move-graph's Laplacian eigenspectrum, a fixed computed object (the chess-spectral piece-graph spectra).")
    print(f"  • SO YES, EXACTLY LIKE VERB FORMS: piece = lemma, legal move = inflection (a rotate over an axis-lattice),")
    print(f"    exceptions = the small SEEN-exception store. Conjugation, plurals, AND chess moves are the SAME object")
    print(f"    (F631). You SEE the rule; you don't TEACH it from a corpus of games any more than from a corpus of")
    print(f"    sentences. (AlphaZero LEARNS to PLAY WELL -- strategy, a hard open problem; but the MOVE RULES themselves")
    print(f"    were never learned -- they are SEEN, handed in. The seeable layer and the strategic layer are distinct.)")
    print(f"  • AND THE BOTH-NESS IS THE NO-SINGLE-TRUTH LAW: the two readings (generator + spectrum) are the_one's two")
    print(f"    languages of math for one invariant rule, neither privileged (F398) -- chess is the case where we have BOTH")
    print(f"    attested (the seen generator here + the Class-L spectrum the chess-spectral notebook built), so it makes the")
    print(f"    F631 realization concrete in two languages at once. (The strategy of GOOD play remains the expert's, F282.)")
    print(f"  • Composes F631 (we see the rules) + F629 (the rotate + small exception dict) + F626 (two languages / no single")
    print(f"    truth) + F623/F621 (moves = rotates over a lattice) + the chess-spectral notebook (Class-L piece-graph")
    print(f"    spectra, D_4/B_4) + F172 (the Laplacian eigenspectrum IS the srmech-native structure signature) + F398/F282.")
    print(f"    srmech 0.7.5rc6. Favored not privileged (F398); held open (F394).")


if __name__ == "__main__":
    main()
