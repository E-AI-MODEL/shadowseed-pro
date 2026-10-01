# ADR-008: Reset the Workbench around the Shadow Seed Learning lifecycle

Status: Accepted  
Date: 2026-10-01  
Owners: Shadowseed maintainers

## Context

Shadowseed Workbench 0.9.x moved toward a polished Dutch chat experience, but the product surface accumulated controls and screens that expose implementation mechanics rather than the mental model of Shadow Seed Learning.

The SSL core remains conceptually stable:

```text
observe -> seed -> recur/evidence/contradiction -> Validation Gate
        -> authority -> relevance -> point-of-use -> optional influence
```

The important distinctions are:

- remembered is not believed;
- recurrence is not evidence;
- relevant is not authorized;
- authorized is not necessarily surfaced;
- surfaced is not proof that wording differences were caused by SSL.

Recent Workbench changes blurred these distinctions.

Examples:

- **SSL-invloed** is presented as a percentage of answer influence, while it actually maps mainly to surfacing/relevance settings;
- **Validation Gate** is presented as one continuous percentage even though the mapping changes authority profile, Gate policy and several thresholds;
- self-reinforcement and embedding choices are exposed beside ordinary chat even though they are research/mechanism controls;
- Chat, Overzicht, Bronnen, Geheugen and Controleren maintain partially independent session selectors and refresh paths;
- manual refresh buttons are required to synchronize UI views of one persisted conversation;
- the ordinary A/B path was changed in 0.9.2 into a persistent independent vanilla trajectory, including late replay of earlier user turns;
- that longitudinal control can make an interactive A/B request unexpectedly expensive;
- the vanilla and SSL arms can use different prompt/transport paths, which adds another variable to an experiment intended to isolate SSL context.

ADR-005 remains correct in its main principle: the product is a normal chat first and research harnesses are subordinate. This ADR narrows and updates the Workbench implementation contract after the 0.9.x experience.

## Decision

### 1. Preserve the SSL engine; reset the presentation layer

The canonical lifecycle, Gate, contradiction handling, persistence, audit ledger, embeddings, recurrence and point-of-use authorization are not rewritten as part of the Workbench reset.

The current 0.9.x UI is retained as implementation history/reference while a new product surface is built on the same controller/runtime boundary.

### 2. One active conversation is the UI source of truth

The normal Workbench has one active session state.

Chat, Shadow/memory inspection and source ingestion must refer to that same active session unless the user explicitly switches conversation.

Ordinary UI state changes propagate automatically after:

- sending a message;
- creating or switching chat;
- source ingestion;
- evidence submission;
- contradiction/falsification;
- any other successful session mutation.

The user must not need **Refresh**, **Refresh chats**, **Refresh memory**, **Refresh runs**, or equivalent buttons to synchronize views of persisted state.

Provider/model discovery may still have an explicit re-scan action because an external Ollama installation can change outside Shadowseed.

### 3. The default UI exposes user decisions, not research mechanisms

The ordinary surface starts with:

- model/provider selection;
- chat;
- a compact Shadow view showing what was noticed and whether it may/was used;
- optional source ingestion;
- optional same-turn comparison.

The following are not first-class normal-chat controls:

- SSL influence percentage;
- Gate strictness percentage;
- self-reinforcement toggle;
- raw embedding backend selection;
- shadow-pressure mode;
- raw runtime mode;
- direct authority/Gate policy selection.

These may remain available in a clearly separated Research/Advanced surface where their exact semantics are stated.

The normal product chooses safe documented defaults. Semantic embeddings are the normal real-model default; lexical embeddings remain useful as a research/control mechanism.

### 4. The normal Shadow view mirrors the SSL lifecycle

Plain language must not break the connection with the actual SSL semantics.

Every visible state and action in the normal UI must have a direct, inspectable mapping to one canonical runtime concept or application command. The UI may explain technical language, but it must not replace it with a friendlier phrase that changes the meaning.

Examples:

- **Onthouden** maps to a persisted seed;
- **Toegestaan** maps to current Gate authorization, not to truth;
- **Aangeboden aan antwoord** maps to surfacing / point-of-use context, not to proven causal influence;
- **Tegenspraak registreren** creates a canonical contradiction record and blocks point-of-use influence while open;
- **Geverifieerde ondersteuning toevoegen** submits independently checked support through the existing evidence authorization path;
- **Bron toevoegen** by itself is not equivalent to verified evidence and must not be presented as if it were.

The primary human-readable states answer three questions:

1. **What did Shadowseed notice?**
2. **May it influence an answer?**
3. **Was it offered to this answer as authorized context?**

A seed detail can expose the full lifecycle, for example:

```text
noticed -> seen again -> supported/contradicted -> authorized -> relevant -> used
```

Technical fields such as trace, weight, Gate event IDs, embeddings and raw JSON remain inspectable but are progressively disclosed.

### 5. One UI action maps to one product concept

The Workbench must not compress unrelated backend mechanisms into one button, slider, question or preset.

A normal UI control represents one coherent user intent and maps to one named application-level action. If that action needs several lower-level operations for atomicity, those operations are composed behind the application-service boundary and remain one semantic command. The UI must not directly coordinate unrelated backend functions and present them as one choice.

Examples of what this rule forbids:

- one "SSL influence" slider that simultaneously changes retrieval thresholds, top-k and other surfacing mechanics while sounding like answer authority;
- one "Gate strictness" slider that silently switches authority profile, Gate policy, recurrence requirements, evidence requirements and promotion thresholds;
- one question such as "How much may Shadowseed do?" if the answer changes validation policy, surfacing policy and feedback-loop behavior together;
- one button that both registers contradiction and changes evidence/authority through a separate path.

Examples of acceptable composition:

- **Tegenspraak registreren** may create the canonical contradiction record and persist the resulting blocking state because those are one domain action;
- **Geverifieerde ondersteuning toevoegen** may validate the operator attestation, record the evidence and route it through the Gate because those steps are one authority-bearing command;
- **Vergelijk dit antwoord zonder SSL** may generate one non-mutating control and one real turn because together they implement one clearly named comparison action.

When two backend mechanisms can be changed independently, the UI must either expose them as separate controls with their real meaning or keep them out of the normal product surface.

### 5. Normal same-turn A/B isolates SSL context

The ordinary action **Compare this answer without SSL** follows the original ADR-005/v0.8 contract:

1. use the same model configuration;
2. use the same visible pre-turn conversation history;
3. use the same current user message;
4. generate a non-mutating control with no surfaced Shadow Seeds;
5. execute the real live SSL turn normally;
6. keep the control out of detection, recurrence, Gate state and later conversation history.

The comparison should change one intended variable: availability of SSL seed context.

Where technically possible, both arms use the same provider transport and equivalent prompt framing. A provider-native vanilla arm must not silently be compared with a differently wrapped SSL arm and then described as a pure SSL-context comparison.

The interactive comparison must require at most one additional model generation for the current turn. It must never replay all earlier turns synchronously.

### 6. Longitudinal vanilla trajectory remains research-only

The 0.9.2 independent vanilla conversation is scientifically useful for a different question:

> How does a fully vanilla conversation trajectory diverge over time from a Shadowseed trajectory?

That experiment remains available in Research tooling.

It is not the default Workbench A/B action and must not be labeled as a same-turn causal comparison.

If longitudinal A/B is enabled after a conversation has already started, historical replay must not block the ordinary interactive response path without an explicit research action and cost/latency warning.

### 7. “Controleren” is audit, not a normal workflow step

Users should not have to manually “check” or “retrieve” SSL as part of normal operation.

Retrieval/relevance, Gate authorization and point-of-use checks are automatic runtime responsibilities.

After an answer, the UI may state for example:

- **Geen geheugen gebruikt**
- **2 eerdere inzichten gebruikt · Bekijk**

The detailed audit explains which seeds were authorized, selected, surfaced and used.

### 8. Every normal function has contextual ELI8 help and explicit interaction semantics

Every visible normal-product function must have an adjacent **ⓘ** affordance.

The help content has five fixed layers:

1. **Alsof je 8 bent** — a concrete analogy that explains the function without changing its meaning;
2. **Wat doet dit echt?** — the exact product/runtime action it maps to;
3. **Wat doet dit niet?** — the most likely category error or false expectation;
4. **Samen met andere functies** — dependencies and interactions expressed with explicit relation words;
5. **Huidige combinatie** — what the currently active settings mean together for this session/seed.

Interaction language is standardized:

- **versterkt** — a signal or route can become stronger; this never means “more true”;
- **verslapt** — a signal or route is weakened/suppressed;
- **blokkeert** — a hard stop exists for that route;
- **vereist** — the action cannot proceed without the named condition;
- **mag** — policy permits the action, but it is not required;
- **kan** — the condition makes an outcome possible, not guaranteed;
- **moet niet / hoeft niet** — no dependency exists;
- **onafhankelijk** — changing one does not change the other.

Help must describe real runtime consequences, not generic educational copy. For example:

- Gate authorization + relevance means a seed **kan** be surfaced; it **moet niet** be surfaced;
- an open contradiction **blokkeert** point-of-use even when evidence exists;
- verified support **kan** evidence-backed authority **versterken**, but does not make a seed true;
- self-reinforcement off **blokkeert** SSL-exposed output from strengthening its own recurrence/authority loop;
- same-turn comparison on **vereist** one extra current-turn generation but **verandert** SSL state niet;
- semantic matching can improve retrieval of paraphrases but is **onafhankelijk** from authority.

This help layer is descriptive only. It must never mutate configuration or combine independent mechanisms.

### 8. Workbench tests must cover behavior and latency shape, not only labels

UI contract tests must go beyond checking that button strings and CSS selectors exist.

At minimum they must prove:

- one active session drives the normal views;
- a successful mutation updates dependent views without manual refresh;
- normal chat has no Gate/SSL percentage controls;
- ordinary A/B cannot trigger historical vanilla replay;
- ordinary A/B uses no more than one extra current-turn generation;
- comparison metadata clearly distinguishes same-turn and longitudinal experiments;
- a control generation cannot mutate SSL state;
- legacy/research sessions remain inspectable.

## Consequences

### Positive

- the Workbench becomes understandable from the SSL philosophy rather than from internal implementation knobs;
- fewer controls reduce accidental experiment invalidation;
- normal A/B becomes faster and easier to interpret;
- refresh-related stale-state bugs disappear by design instead of being patched per tab;
- research mechanisms remain available without defining the normal product experience.

### Costs

- part of the 0.9.x UI will be replaced rather than incrementally polished;
- some existing UI tests must be rewritten around the new contract;
- same-turn and longitudinal comparisons must coexist as explicitly different experiment types;
- controller/application boundaries may need small additions to support automatic UI synchronization cleanly.

## Compatibility

This ADR does not delete persisted session data or rewrite the SSL engine.

Existing 0.9.x workspaces remain subject to the production migration/integrity policy. UI reset work must not silently reinterpret legacy runtime metadata.

The 0.9.2 independent `vanilla_history` field may remain readable for research/provenance even when the normal Workbench stops using it.

## Acceptance criteria

1. Opening the Workbench yields a usable chat without operating SSL research controls.
2. There is one active chat state shared by the normal Chat and Shadow views.
3. No ordinary state-refresh button is required after a successful action.
4. The normal UI does not expose SSL/Gate percentage sliders or self-reinforcement.
5. A normal answer says plainly whether prior memory was offered as authorized context.
6. Seed details show remembered/authorized/relevant/used as separate concepts.
7. **Compare this answer without SSL** uses the same pre-turn visible history and adds at most one extra model generation.
8. The same-turn control never enters SSL lifecycle state or later conversation history.
9. Longitudinal vanilla-path comparison is available only as an explicitly labeled research experiment.
10. The existing Gate, audit and point-of-use authority invariants remain unchanged.
11. No normal UI control silently changes more than one independent SSL policy dimension.
12. Every visible normal-product function has contextual ⓘ help with ELI8, exact semantics, non-effects, dependencies and the current combination state.
