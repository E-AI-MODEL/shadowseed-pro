# Shadowseed Workbench 0.12.3

0.12.3 is a Research Preview candidate. The published download remains
`v0.12.2` until the exact-SHA Release Workbench workflow publishes this version.

## Changes since the download

- Native role-structured chat for supported backends, with the same transport
  for treatment and the same-turn SSL-off control. Completion-only backends
  retain their compatibility path. Fixture output does not expose instructions.
- Bounded generation history: at most six previous turns and approximately
  12,000 characters. The current user message is retained in full. Detection
  keeps its separate bounded clean context and 220-token default ceiling.
- At most one surfaced seed by default in new product sessions. Explicit
  session settings remain authoritative; this is not a universal hard limit.
- Automatic model-role routing requires evidence for the exact model ID and
  role. Family names alone do not establish detector or revision suitability.
- All new web and Gradio chats check the selected Ollama embedding model
  before persistence. A missing model returns `ollama pull <model>`; an
  unreachable server returns startup guidance. Explicit model tags must match.
  Endpoint and consent validation happen before this read-only preflight.
- The chat form shows local setup instructions and keeps creation errors visible
  inside the mobile conversation drawer. Doctor guidance includes the normal
  Ollama embedding setup.
- Whole-candidate Markdown wrappers are removed before detector filtering and
  deduplication. Internal formatting and code identifiers are preserved. Raw
  detector output and parser diagnostics remain available in the existing audit.

The remaining setup and parser fixes from PR #196 are carried onto current
`main`; its older chat implementation must not overwrite the later #198 fixes.

## What is retained from the GLM comparison

The product uses the canonical Python runtime. Detection records a possible
atomic gap with unspecified type and zero weight. The historical 18-word rule
does not decide atomicity. Conversation context helps interpretation but is not
evidence. Recurrence, external evidence, authority, current relevance and
point-of-use permission remain separate. Research remains a separate package.

The current Gate, evidence, contradiction, promotion and authority rules are
unchanged. No new schema, decision-model authority or automatic promotion path
is introduced. Same-turn revision still depends on same-turn promotion and is
inactive in ordinary evidence-backed sessions without that event.

## Candidate acceptance

| Check | Required evidence |
| --- | --- |
| Deterministic mechanics | Full pytest, branch coverage, Ruff and web contract checks on the candidate |
| Distribution | Clean wheel and standalone self-tests, supported-platform CI, provenance and checksums |
| Missing local dependency | No persisted chat; exact installation guidance; retry after installation succeeds |
| Real conversation | Native Ollama chat, a correction in a later turn, bounded history and clean detector input |
| SSL behavior | Weightless birth; evidence through the existing Gate; current relevance and point-of-use checks |
| Paired comparison | One additional no-SSL generation with matching transport and no state mutation |
| Continuity | Close and reopen the chat, preserve messages/audit state, and run `shadowseed doctor` |
| Production claim | Independent assurance, no open P0/P1 finding and the documented unchanged-candidate soak |

Deterministic backend doubles and HTTP fixtures do not establish live-model
quality or latency. A successful build does not substitute for the real Ollama
use cycle. The minimum published Ollama requirement remains v0.11.10 for
EmbeddingGemma; the thin client does not download models automatically.

## Local use after publication

Start Ollama and install a chat model of your choice plus the embedding model:

```bash
ollama pull embeddinggemma
```

Open Shadowseed, select the exact installed chat model and create a conversation.
Fixture remains available without Ollama for deterministic mechanism inspection.

Run Release Workbench only after merge and successful CI on the exact protected
`main` SHA. Production Release Assurance and the unchanged-candidate use period
remain separate from publishing a Research Preview.
