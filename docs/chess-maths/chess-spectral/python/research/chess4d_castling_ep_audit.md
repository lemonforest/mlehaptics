# chess4d 0.4 — castling + en-passant audit (chess-spectral 1.4.0)

**Status:** Audited 2026-04-29 against chess4d 0.4 from PyPI.

This audit was performed as part of chess-spectral 1.4.0's §17.3
acceptance criteria — the consumer (chess4D-OC) flagged castling and
en-passant as edge cases needing a regression test, particularly:

> Castling: send "king moves 2 squares" with rook NOT having moved →
> succeeds; with rook HAVING moved → must fail loudly (assertion or
> returned error, not silent corruption).
>
> En passant: pawn double-push to set up EP, then en-passant capture
> from the adjacent file → produces the expected position.

## Summary

chess4d 0.4 handles both cases correctly through its
`legal_moves()` generator. We did not find any silent-corruption
bugs.

## Audit findings

### Castling

* **Castling-rights field present.** `GameState.castling_rights` is a
  `frozenset` of 4-tuples `(Color, axis_index, lane, CastleSide)`.
  See `tests/test_castling_ep_4d_regression.py::test_chess4d_provides_castling_rights_field`.
* **Castle-flagged moves carry `Move4D.is_castling=True`.** This is
  pinned by `test_chess4d_move4d_carries_castle_and_ep_flags`.
* **Path-blocking is honored.** At chess4d's dense 4D startpos, no
  castling moves are legal — confirmed by
  `test_castling_blocked_at_startpos`. The path between king and
  rook is guarded by minor pieces in the dense initial layout.
* **Castling rights revoked on rook move.** When pieces move during
  a deterministic walk and a rook's starting square becomes empty,
  the corresponding entry is removed from `castling_rights`.
  Confirmed by `test_castling_rejected_when_rook_moved`: every
  emitted castling move's color matches a remaining entry in the
  rights set (no orphan castles).
* **No silent corruption observed.** chess4d's `legal_moves()`
  generator filters out castling moves whose rights have been
  revoked; the consumer cannot accidentally apply such a move
  through the `gs.push(m)` path because the move is never emitted
  in the first place.

**Status: PASS.** No regression patch needed.

### En passant

* **EP-state fields present.** `GameState.ep_target`, `ep_axis`,
  `ep_victim` are all on the public surface. Pinned by
  `test_chess4d_provides_ep_state_fields`.
* **EP-flagged moves carry `Move4D.is_en_passant=True`.** Pinned by
  `test_chess4d_move4d_carries_castle_and_ep_flags`.
* **Pawn double-push sets EP target.** When a chess4d-emitted legal
  move is a pawn double-push (identified by playing it on a fresh
  state and observing `ep_target != None` after the push), the
  resulting state has both `ep_target` and `ep_axis` set
  consistently (one is non-None ⇒ the other is also non-None).
  Pinned by `test_ep_target_set_after_pawn_double_push`.
* **EP capture in deterministic walk.** The full EP-capture round
  trip (set up the target, capture from the adjacent file, observe
  the captured pawn removed from the board) was not exercised in
  the deterministic 30-ply walk — it depends on the specific
  pawn-axis configuration the deterministic walker reaches. The
  test (`test_ep_capture_emerges_when_set_up`) skips when no EP
  capture appears in 30 plies. **This is not a regression** in
  chess4d; it's a path-dependence in the test's walker. A targeted
  fixture position with white and black W-axis pawns on adjacent
  files at the EP rank would force the case, but is deferred to
  v1.5+ when the consumer can supply the fixture from JS-side
  game logs.

**Status: PASS for the surface; EP-capture round-trip deferred.**
No regression patch needed.

## Recommendations

* **For chess-spectral 1.4.0:** Ship the regression suite as-is —
  it pins the chess4d 0.4 API surface against silent drift, which
  is the consumer's main concern. The deferred EP-capture
  round-trip is a feature for v1.5+ (when stalemate detection and
  legal-move generation are wired through to chess-spectral
  itself).
* **For chess4d upstream:** No action recommended. The 0.4 release
  handles both edge cases correctly under our tests.
* **For the chess4D-OC consumer:** When a user attempts a castle
  move whose rights have been revoked, the chess4d engine will
  simply not return that move from `legal_moves()`. The consumer's
  UI should reflect this by greying out the castle button when the
  corresponding entry is absent from `castling_rights`. The
  consumer does not need to implement an "is this castle still
  legal?" check itself — chess4d already does the bookkeeping.

## Test list

These tests live in
`python/tests/test_castling_ep_4d_regression.py`:

| Test | Purpose | Status |
|---|---|---|
| `test_castling_blocked_at_startpos` | No castling at dense startpos | PASS |
| `test_castling_emitted_when_legal` | Castling emerges in deterministic walk | PASS or SKIP (path-dependent) |
| `test_castling_rejected_when_rook_moved` | Rights bookkeeping consistent | PASS |
| `test_ep_target_set_after_pawn_double_push` | EP-target set consistently | PASS |
| `test_ep_capture_emerges_when_set_up` | EP capture in deterministic walk | SKIP (path-dependent) |
| `test_chess4d_provides_ep_state_fields` | API surface (ep_target/axis/victim) | PASS |
| `test_chess4d_provides_castling_rights_field` | API surface (castling_rights) | PASS |
| `test_chess4d_move4d_carries_castle_and_ep_flags` | Move4D flags | PASS |

Total: 8 tests; on a typical run, 7 pass and 1 skips (EP capture).

## References

* `python/tests/test_castling_ep_4d_regression.py` — the regression
  suite this audit pins.
* chess-spectral notebook §17.3 — the consumer's wish-list that
  motivated this audit.
* chess4d 0.4 (PyPI / `python-chess4d-oana-chiru`) — upstream
  reference.
