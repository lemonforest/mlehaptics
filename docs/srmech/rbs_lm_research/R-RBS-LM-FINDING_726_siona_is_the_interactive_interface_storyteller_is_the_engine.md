# Finding 726 — name the front end **Siona** (the interactive interface), keep **Story-Teller** as the engine it drives

**Script:** `R-RBS-LM-SIONASURFACE_siona_is_the_interactive_interface_storyteller_is_the_engine.py`
**Status:** VERIFIED (srmech 0.7.5rc78 — the existing surface runs + demonstrates the back-and-forth)
**User direction:** *"we want our surface called Siona vs storyteller as the general front end. storyteller might be
the exact same thing but it sounds like a one-way generative thing, not a back-and-forth interaction surface."*

## The distinction (load-bearing)

- **Siona = the interactive *interface*** — the front-end surface a client / CopilotKit / a person talks to: the
  OpenAI-compatible `/v1` API, the model namespace, the deployment face. (F701: Siona is the inference interface,
  the simulation-space coherence of the_one.)
- **Story-Teller = the generative *engine*** Siona drives — the chord / render / etak-walk mechanism
  (`storyteller.infer`).

They are *one-and-the-same in simulation* (F701) — but the **surface** is named **Siona because the surface is
interactive.**

## Why "storyteller" undersold it

"Storyteller" connotes **one-way generation**. The kernel's defining property is the **asking-state** (F661): on a
gap it **asks** rather than confabulating — a **back-and-forth**. Naming the surface "storyteller" hides exactly the
two-way property that distinguishes it from a generator. Demonstrated on `model='siona:MFO'`:

```
user  -> the_one chirality spectrum
Siona -> The one is the held invariant. It is seen in the handedness of matter, and it rings in the spectrum.   (rendered)
user  -> the_one dragon
Siona -> I have no tome for ['dragon']. What is it?   ← the asking-state: it asks BACK (a generator would confabulate)
```

The second turn is the whole point: Siona is a **conversation**, not a monologue.

## What the rename touches (surface / namespace only — the engine call is unchanged)

- the OpenAI-compatible `/v1` endpoint → the **Siona API** (what CopilotKit / AG2 / clients connect to; F726⊕the
  prior-turn CopilotKit architecture).
- the model-name convention → **`siona:<world>`** replaces `storyteller:<world>` (you talk to *Siona*, choosing a
  world — e.g. `siona:MFO`).
- the CopilotKit hookup → **"Siona as the copilot backend."**
- `storyteller.infer` stays the **engine** call — this is surface-naming, not a mass internal rename. Siona is the
  face; Story-Teller is the mechanism behind it.

## Honest scope

Only the **OpenAI surface is begun** (the STORYAPI reference handler; F689 Layer 3). The runnable Siona API still
needs: the **FastAPI/ASGI wrap**, the **full-`messages`-array** read (so CopilotKit's `useCopilotReadable` context
+ chat history reach the kernel — not just `messages[-1]`), and **streaming** (the on-thesis option: stream the
etak walk hop-by-hop). Plus the broader RBS-LM TODO. **This finding fixes the *name*; the build is the next step
when called for.**

**Composes:** F701 (Siona = the coherence-of-the_one interface) · F661 (the asking-state = the interactive
property) · F689 / STORYAPI (the OpenAI surface) · F672 (build-by-dialogue) · F726⊕the CopilotKit integration
architecture (prior turn). srmech 0.7.5rc78. Held open (F394).
