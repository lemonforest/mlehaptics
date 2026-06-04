# R-RBS-LM Finding 375 — "context-window influence" is real ONLY as MCP-free client-side preprocessing (filter-then-send) — the F237 graft IS it, already operational; the base64/"dense-code" route is falsified (anti-dense, measured); KV-cache/attention manipulation is unavailable on a hosted API

**Date:** 2026-06-04 · **srmech:** 0.7.0rc28 · **task (user):** vet a third-party AI's MCP/context-window claims for hallucination + find the falsifiable asks; "need not be MCP-specific if it works; be decisive" · **verified-by:** claude-code-guide (MCP spec / Claude Code #1785 / Anthropic prompt-caching docs) + this srmech-native density measurement · **composes:** F163/F172 (text-chirality / non-natural-encoding nulls), F237 (the surgical graft)

## The decisive answer (MCP dropped — the bare mechanism)

**Can it work without MCP? Yes — and we already run it.** The only *real* context-window influence is **client-side preprocessing: filter the context in your own code, then send the refined text** to the model. That is exactly the **F237 surgical graft** (CLAUDE.md → `CLAUDE_LEAN.md`, ratio 0.50, coverage 1.0 — refreshed this session). No MCP, no "sampling loop," no "resource primitive." The MCP wrapping in the third-party claim was hallucinated dressing on this one mundane, true mechanism.

## The three claims, vetted (authoritative, sourced)

| claim | verdict | why |
|---|---|---|
| **1. MCP "sampling loop" bypasses the context window** | **OVERSTATED** | `sampling/createMessage` is real + takes a custom `messages` array, but it's a **sidecar completion**, not a root-context bypass; human-in-loop mandatory; **Claude Code does not implement sampling as a client** ([#1785 open](https://github.com/anthropics/claude-code/issues/1785)) — wouldn't even fire for us. |
| **2. base64/"dense holographic code" maps to orthogonal token weights / is ultra-dense** | **HALLUCINATED** | no mechanism picks embedding geometry from the string side (tokenizer + embeddings are fixed); base64 is **token-inefficient**, not dense (measured below); "token decay" is fabricated vocabulary. |
| **3. custom client prunes KV-cache / shifts attention weights** | **PARTIALLY TRUE / OVERSTATED** | you *can* preprocess prompt text in your own client (trivially — that's F237); you **cannot** prune the KV-cache or shift attention via MCP or the hosted API (only read-only cache diagnostics; "managed entirely by the system"). KV-cache/attention control needs **local model weights**, never a hosted API. |

## The measurement — base64/"dense-code" is ANTI-dense (Claim 2 falsified)

Same load-bearing content, three representations (srmech-native; Class-A content-address; char counts exact, **token counts a proxy — tiktoken absent — but direction robust**):

| representation | chars | tokens (proxy) | vs natural language |
|---|---|---|---|
| **natural language** | 200 | 39 | 1.00× |
| base64(utf-8) | 268 | 67 | **1.34× chars** (the exact 4/3 identity), ~1.7× tokens |
| hex(utf-8) | 400 | 100 | **2.00× chars**, ~2.6× tokens |

**Provable without any tokenizer:** `|base64(X)| = ⌈4/3·|bytes(X)|⌉ > |X|` — base64 is *strictly more characters* than the content it encodes, and base64/hex strings can't tokenize into whole-word tokens, so they're strictly more tokens too. **The "ultra-dense" claim is reversed.** Per-token information density: **natural language ≫ base64 ≫ nothing-gained.** (Recall half: **F163/F172** already null on text-chirality / non-natural encodings — LLMs recall the natural language they're trained on, not base64. So base64 loses on *both* token-density and recall.)

**The genuinely-dense move is the opposite of the claim:** don't re-encode context into "dense code" — **filter the natural-language context** (Class-L band-select / the F237 extractive graft) so *fewer natural-language tokens* carry the load-bearing content. That's what `CLAUDE_LEAN.md` is (0.50× the bytes, coverage 1.0).

## The falsifiable asks (the user's request)

1. *"Does Claude Code honor an MCP `sampling/createMessage`, and does a sampling sub-completion alter the root context?"* → **NO / NO** (re-testable if #1785 ships).
2. *"At equal information, is base64/dense-code fewer tokens AND better-recalled than natural language?"* → **NO on both** (char-inflation exact above; recall = F163/F172). The clean lodgeable test if we want the real token number: rerun with `tiktoken` installed (char direction won't change).
3. *"Does the Anthropic API expose any KV-cache-prune / attention / history-reorder control beyond `messages` + `cache_control`?"* → **NO** (inspectable API surface; only read-only cache diagnostics).

## The meta-lesson (our own discipline)

The hallucination tell here **is** the no-magic discipline: the **falsifiable** claims (sampling exists, base64 token count, the API surface) resolve cleanly to *real-but-mundane* or *false*; the **unfalsifiable jargon** ("orthogonal token weights," "minimize token decay," "dense activation spaces") is the magic. **A claim you cannot operationalize into a measurement is the hallucination signature.** The one true thing is the one we already do (F237 filter-then-send).

## Discipline

srmech-native (Class-A `format.sha256_bytes`; base64/hex are stdlib; char counts exact, **token counts flagged as a proxy** — tiktoken not installed); no numpy. Authoritative MCP/API facts verified via claude-code-guide with spec/docs pointers (not asserted from memory) — citation discipline. No-leaning (the measurable half measured; the recall half cited to prior nulls; the proxy flagged). Defensive/benign (tooling evaluation, no capability/offense). Composes with F163/F172 (encoding nulls), F237 (the graft = the real mechanism).
