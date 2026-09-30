# Shadowseed Workbench 0.9.1

Shadowseed Workbench 0.9.1 is the packaged release of the new Dutch chat-first
Workbench introduced after 0.8.0. It keeps the same canonical Shadow Seed
Learning runtime, Validation Gate and point-of-use authorization model while
moving the product experience away from a tester-oriented interface.

## What changed

- Chat is now the primary Workbench surface, with **Nieuwe chat** and **Versturen** as the main actions;
- the visible interface is Dutch by default;
- an available local Ollama model is selected automatically, with a safe offline demo fallback when no local model is available;
- model provider, embeddings and relevance settings remain available under technical settings rather than dominating the main workflow;
- Sources, Memory, Control and explanation surfaces are grouped around normal user tasks;
- technical JSON, audit and trace information remain available in collapsible technical sections;
- source upload continues to treat TXT, Markdown, JSON and CSV content as observation input rather than automatically trusted evidence;
- the Workbench now explains Shadow Seed Learning, authority versus relevance, the Validation Gate, source processing, RAG versus fine-tuning and the limits of what SSL can establish;
- paired SSL-on / SSL-off comparison remains available, including the explicit experimental shadow-pressure mode;
- assisted review notices remain bound to the selected session across Chat, Sources and Memory;
- current-Gate revalidation protects point-of-use authorization when Gate settings become stricter;
- production audit commitments now protect authority-relevant Gate configuration and recurrence counts;
- restore/import paths preserve reproducible Gate configuration commitments;
- observation-ledger schema handling fails closed when nested records claim a newer schema than their enclosing ledger.

## Product behavior

The default Workbench stays on the same controller and canonical runtime used by
the technical surfaces. The UI does not introduce a second Gate, a direct
weight editor or an alternate authority path.

The operational path remains:

```text
observe -> seed -> recur/evidence -> Validation Gate -> promote
        -> relevance -> point-of-use decision -> possible influence
```

A promoted seed remains only eligible for later use. Relevance and current
point-of-use authorization are still required before it can influence a turn.

## Local-first chat

The Workbench prefers an available local Ollama model. When no supported local
model is available, the product can open with the safe offline demo path so the
interface remains inspectable without silently sending content to a hosted
provider.

Hosted providers remain explicit opt-in choices. Embedding settings make the
local/online boundary visible in the technical configuration.

## Sources and memory

The Sources workspace supports pasted text and multiple TXT, Markdown, JSON and
CSV files. Source chunks are processed as observations and do not become fake
chat turns or trusted evidence by default.

Memory and review actions refresh their visible state after evidence,
falsification and Gate changes. Historical promotion events remain part of the
audit trail, while current authorization can be revalidated against the Gate
active now.

## Audit and production integrity

0.9.1 strengthens the protected production record around authority decisions:

- Gate configuration used for point-of-use authorization is committed separately from seed authority state;
- restore and import events retain reproducible Gate configuration snapshots;
- recurrence counts used by current-Gate checks are part of protected authority state;
- mixed observation-ledger schema versions fail closed;
- the packaged production controller forwards normal and comparison modes through the same runtime path.

## Distribution and release integrity

Publication requires:

- the exact protected-`main` source SHA;
- required CI and production-local acceptance;
- Linux/macOS/Windows standalone evidence;
- frozen product self-tests;
- `SHA256SUMS`;
- CycloneDX SBOM;
- `PROVENANCE.json`;
- repository license verification;
- dependency-lock verification;
- trusted artifact attestations;
- post-download verification.

The macOS distribution boundary remains unchanged: the app is ad-hoc signed,
not Apple-notarized.

## Claim boundary

Version 0.9.1 does not claim that SSL improves every answer, proves semantic
truth, retrains the base model, or makes the system suitable for high-impact
decisions. A changed answer is not by itself evidence that SSL caused the
difference. The audit trail records the system path needed to inspect those
claims rather than assuming them.
