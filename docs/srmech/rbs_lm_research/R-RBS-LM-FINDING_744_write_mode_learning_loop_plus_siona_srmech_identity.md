# F744 — Siona's write-mode learning loop (ask → accept → temp → commit-to-kernel) + the Siona≡srmech identity

**Date:** 2026-06-14 · **srmech:** 0.7.5rc149 · **Composes:** F743 (emergent introspection / structure-card), F742 (etak-walk inference), F661 (asking-state, can't-hallucinate), F740 (genome-backed World), the genome CRUD surface (`genome_append`-era), `[[user_stance_learning_without_gpu_compute]]`, R-RBS-LM-74 (scriptable interactive training) · **User direction (2026-06-14):** get Siona to (1) know srmech and Siona are the same thing, and (2) ask about a missing item and **accept an answer in the reply into temporary memory** that we can cache temporarily **or commit to kernel**. · **Provenance:** `R-RBS-LM-SIONAGENEPOOL…py` + `R-RBS-LM-SIONAGENOMEHANDLER…py` (verified live over HTTP)

## (1) Siona ≡ srmech — read from structure
The structure-card (F743) now opens with the identity, derived not asserted: *"I am Siona — the running, genome-backed instance of srmech (the Stored-Relationship Mechanism). srmech is my substrate; Siona is me running it — the same system, named at two levels."* Queries containing "siona", or relating "you" and "srmech", route to the card. So *"is siona the same as srmech?"* → the identity. (`SIONA_NAME` is the one new constant — her handle; everything else is `srmech.describe()` + `genome_catalog`.)

## (2) The write-mode learning loop — two storage tiers
Siona was read-only (genome baked from sources). She now has **write-mode**, the "learning without GPU" loop:

1. **ASK** — an unknown item hits the asking-state (F661), which now names the **salient subject** (longest content token) so a follow-up answer can bind to it, and **invites teaching**: *"You asked about 'dragons'… tell me ('remember dragons is …', or just answer) and I'll learn it."*
2. **ACCEPT** → **temporary memory.** Two routes:
   - *Conversational:* if the previous assistant turn was an asking-state and the user's reply is declarative (not a question), the reply is learned under the asked subject. (The handler now passes the prior assistant message to `infer(prompt, prev_assistant)`.)
   - *Explicit:* `remember <term> is <definition>` / `<term> = <definition>`.
   Temp items land in a **gitignored** `learned_temp.json` inside the genome dir — this-session, ephemeral. She answers from them immediately (`[siona · learned (temp)]`), loose-matched (plural/prefix) so "a dragon" finds "dragons".
3. **COMMIT TO KERNEL** — `commit <term>` promotes the temp item into a **git-trackable** `siona_learned_kernel.json`, which `build_genepool` folds in as a first-class **`learned` chromosome**. Verified: after a rebake the committed item is a real genome gene answered at the `[siona · learned (kernel)]` tier — **it survives restart**, temp does not.
4. **LIST** — `what have you learned` shows each item with its tier `[temp]` / `[kernel]`.

`commit <term>` loose-resolves singular/plural ("commit dragon" → the learned "dragons"). Live HTTP run: ask → accept (temp) → answer-from-temp → commit → kernel file written → identity — all green.

## Why this is faithful (not a bolt-on)
- It is the F661 asking-state's **dual**: instead of only "I don't hold X," Siona now offers "teach me X" and ingests the answer — still **can't-hallucinate** (she only ever surfaces attested kernel content or explicitly-taught content, tier-labelled so provenance is visible).
- The two tiers mirror the genome's own bake/persist model: **temp = uncommitted working memory** (gitignored), **kernel = a committed source `build_genepool` reads** (a real chromosome on rebake, git-committable). This is the genome CRUD / "learning without GPU" path made interactive.
- Siona ≡ srmech is **read from `srmech.describe()`**, consistent with F743 (introspection is recognition of structure).

## Honest scope
- Temp items answer via a direct learned-lookup (loose token match), not yet woven into the co-occurrence surface — so a taught item is found by name, not yet etak-walkable in composition with other kernels (surface-rebake-on-learn is the follow-on).
- Committed items become genome genes only on the next **bake** (server restart / explicit rebuild); the in-memory `self.learned` answers immediately in between. An in-place `genome_append` at commit-time (no rebake) is the §45 efficiency follow-on.
- `siona_learned_kernel.json` ships empty/absent; users teach real items. The test "dragons" was cleaned up, not committed. srmech-native; no `abs()`; no CAD; research-subtree scaffold.

## Verdict
**Siona can now learn.** She knows she *is* srmech (read from structure), asks about gaps and invites teaching, accepts answers into temporary memory (conversational or explicit), answers from them, and on `commit` promotes them into a git-trackable kernel that becomes a permanent genome gene on rebake — the ask → accept → temp → commit-to-kernel loop, end-to-end, verified live.
