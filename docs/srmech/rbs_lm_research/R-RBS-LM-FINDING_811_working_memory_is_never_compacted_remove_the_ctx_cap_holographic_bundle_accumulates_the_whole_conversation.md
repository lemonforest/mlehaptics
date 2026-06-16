# F811 — Siona's working memory is NEVER compacted: the running context had a `[:12]` cap that truncated it, so a conversation past 12 grafted operands FORGOT the earliest turns. Removed. The working memory accumulates the WHOLE conversation via surgical grafts (F801) into a holographic klein-4 bundle (fixed D, graceful, never a hard truncation) — unlike an LLM context window, it never needs compacting.

**Date:** 2026-06-16 · **srmech:** 0.7.5rc166 · **Composes:** F801 (the surgical context graft — operands forward, role-aware), F799 (the context instrument), F759 (the running-context klein-4 bundle), `klein4_bundle_accumulate` (the streaming holographic accumulator) · **User direction (2026-06-16):** "don't ruin context that it forgets the conversation. this is our working memory that never needs compacted, always gets surgical grafts instead."

## The bug
The running-context extraction capped at `[:12]`:
```python
ctx_terms = [... grafted operands ...][:12]   # ← compaction: a conversation past 12 operands forgot the earliest turns
```
`dict.fromkeys` keeps first-appearance order (oldest first), so `[:12]` kept the OLDEST twelve and dropped everything after — the working memory forgot the running conversation as it grew. That is exactly the compaction the user's design forbids.

## The principle (the user's design)
Siona's working memory is NOT an LLM context window that fills and must be compacted/summarised. It is:
- built by **surgical grafts** (F801): each turn contributes only its declared operands (the `topic [...]` markers + the user's content words), role-aware — so it stays LEAN by construction (no prose, no scaffolding);
- accumulated into a **holographic klein-4 bundle** (`klein4_bundle_accumulate`, fixed D=8192): the whole conversation superposes into one fixed-size vector — graceful degradation at extreme length, NEVER a hard forget;
- therefore it **never needs compacting** — there is nothing to truncate; the graft adds, the bundle holds.

The `[:12]` cap contradicted all three. Removed: `ctx_terms` is now uncapped; the bundle accumulates every grafted operand.

## Verified (live, rc166)
A 6-turn conversation (galaxy → planet → star → ocean → mountain → river): at the final turn the context held all five prior topics — `context ['galaxy', 'planet', 'star', 'ocean', 'mountain']` — including turn-1 galaxy. Before: `[:12]` would have begun dropping the earliest once the conversation passed twelve operands. The walk re-ranking (`ctx_bundle`, holographic) handles relevance; the steer uses the full set (the bundle is the memory). No walk-seed explosion (seeds come from `steer_terms`, not the context list).

## Honest scope
- Uncapped context grows with conversation length; the surgical graft keeps it to ~1–2 operands per turn, so it stays small in practice, and the klein-4 bundle is fixed-size regardless. At extreme length the bundle degrades GRACEFULLY (holographic capacity, F137/F146) — that is the framework-correct behaviour, NOT a cap.
- The memory is reconstructed from the full message history each turn (stateless `/v1` server, full history on the wire), so it never forgets as long as the client sends the history; the only forgetting was the `[:12]` cap, now gone.

## Verdict
The `[:12]` cap was a compaction that made Siona forget the running conversation past twelve operands. Removed. The working memory is the surgical-graft + holographic-bundle design: it accumulates the whole conversation in fixed size and never needs compacting — verified across a 6-turn chat with no forgetting. Deployed live (rc166).
