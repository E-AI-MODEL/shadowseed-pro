# Shadowseed product UX and authority profiles

## Goal

A first-time user should be able to open Shadowseed and, within five minutes:

1. understand what Shadowseed does;
2. start a run without reading documentation;
3. see which shadow seeds were discovered and why;
4. understand whether a seed is merely observed, validated, promoted, or used;
5. verify whether Shadowseed changed an answer;
6. control how much autonomy Shadowseed receives;
7. inspect the raw JSON and event trail when desired.

The product must preserve the current technical auditability while removing the
need to understand internal implementation details before using it.

## Product principle

The default user experience is not a developer console.

The primary flow is:

**Start -> Run -> Observe -> Understand -> Verify -> Control -> Inspect**

Technical JSON, embeddings, Gate events, traces, and ledger records stay
available through progressive disclosure.

## Authority profiles

Profiles sit above the existing lifecycle. They never bypass the Validation
Gate and do not create an alternative implementation.

### Controlled (default)

- detect: automatic
- evidence validation: manual
- promotion: existing Gate
- surfacing: existing relevance and point-of-use checks
- contradictions: block until manually resolved

This profile must remain behaviorally equivalent to the current production
runtime.

### Assisted

- detect: automatic
- mature recurrence is tracked automatically
- live authority remains evidence-backed
- when recurrence is mature but verified support is still missing, the product
  raises a review request rather than silently granting authority
- promotion still goes through the Gate
- relevant promoted seeds may surface automatically

### Autonomous

- detect and recurrence handling: automatic
- live sessions use the existing exploratory Gate by default, so recurrence can
  raise authority without being relabeled as external evidence
- promotion still happens only through the Gate
- surfacing still requires relevance plus point-of-use safety checks
- user remains able to inspect, override and contradict
- all authority changes remain attributable and auditable

### Open research

- maximum autonomy for exploratory runs
- recurrence uses the same exploratory Gate path as Autonomous
- the profile may permit future unreviewed system evidence only when an explicit,
  auditable producer exists and the selected Gate policy accepts that signal
- Gate, provenance, contradiction and audit events remain active

## Interface structure

### 1. Home / Start

The first screen explains Shadowseed visually in five stages:

1. Input: chat, text, files, corpus
2. Observe: detect possible gaps and recurring perspectives
3. Develop: cluster, recur, validate, contradict
4. Gate: determine whether a seed may gain authority
5. Use: surface only when relevant at point of use

The user chooses an authority profile here. The current profile is always
visible in the header.

### 2. Run

Normal chat or corpus ingestion is the primary workspace.

The interface should show only actions relevant to the current context. Do not
show disabled authority tools as the dominant interaction.

### 3. Shadow

Show seed cards with plain-language status:

- Found
- Recurring
- Supported
- Validated
- Promoted
- Blocked
- Used

Each card answers:

- What did Shadowseed notice?
- Where did it come from?
- Why is it in this state?
- Has it ever influenced an answer?
- What can I do next?

### 4. Verify

Provide a built-in verification flow that can compare:

- answer without Shadowseed influence
- answer with Shadowseed
- which seeds were eligible
- which seeds were selected
- which seeds actually surfaced
- whether observed text differences may be attributed to Shadowseed

The interface should never require the user to infer influence merely from text
differences.

### 5. Control

The current release exposes a run-level Control workspace showing the selected
profile, effective Gate and any seeds asking for review. Profile selection is a
run-level decision; changing authority rules mid-run is deliberately not a
silent UI mutation.

Profile controls use plain language first. A future advanced panel may expose
per-stage behavior:

- Detect
- Validate
- Promote
- Surface
- Contradictions

Where appropriate, each stage may expose Auto / Ask / Manual / Off. Unsupported
combinations must not be offered.

### 6. Inspect

Every human-readable object should have an optional technical drawer:

- lifecycle events
- Gate decision
- authority version
- evidence
- similarity / relevance
- trace
- contradictions
- ledger references
- raw JSON

Raw JSON is a first-class inspection surface, but never the only explanation.

## Contextual actions

Authority-bearing controls appear when relevant.

Examples:

- "Resolve contradiction" appears on a blocked seed.
- "Submit verified support" appears when the current profile requires human
  evidence and the seed can benefit from it.
- A promoted seed that has never surfaced explains why, including relevance
  threshold and point-of-use decision.
- In Autonomous mode, manual controls remain available as overrides but are not
  required for normal operation.

## Large-ingest direction

The same UI must scale from one chat to large corpora.

The product should eventually summarize large runs as:

- items processed
- candidate seeds
- semantic clusters
- active seeds
- validated/promoted seeds
- blocked seeds
- seeds that actually influenced outputs

Each number drills down to seed cards, events, and raw JSON.

## Non-regression contract

Introducing profiles must not alter default production behavior.

- default profile = Controlled / strict
- current Gate semantics remain unchanged
- current point-of-use relevance checks remain unchanged
- current production-local auth and ledger behavior remain unchanged
- research and production boundaries remain intact

New autonomy is opt-in and implemented through profile policy, not by
duplicating the runtime or bypassing existing authority mechanisms.
