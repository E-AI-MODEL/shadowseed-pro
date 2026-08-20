# Production Threat Model

**Status:** Proposed  
**Baseline:** `main` at `02b8d2f505c837c88e5cc6654c7f864b751480f5`  
**Scope:** Phase 0 architecture for `production-ready/local`; hosted deltas are explicitly identified.

## Assets to protect

- seed authority state and Gate decision history;
- point-of-use authorization records;
- prompts, answers, seed text, evidence references/notes and feedback;
- workspace database, backups and exports;
- local actor identity and any audit-signing/checkpoint material;
- hosted provider credentials and provider configuration;
- release provenance, build artifacts and repository history;
- availability and resource budgets for model-backed operations.

## Trust boundaries

1. **Product boundary:** UI/CLI input is untrusted. The application layer validates identity/scope/capability before authority-bearing operations.
2. **Runtime boundary:** detector/model output is untrusted content. It may create weightless candidates but may not grant authority.
3. **Gate boundary:** typed signals may propose authority changes; only the Gate applies them.
4. **Point-of-use boundary:** promoted/current authority is necessary but not sufficient for influence.
5. **Persistence boundary:** current snapshots are mutable application state; the production audit ledger is independent historical integrity evidence.
6. **Provider boundary:** local or hosted model/embedding providers are external dependencies. Their responses are data, not evidence authority.
7. **Import/export boundary:** backups and ZIP/report artifacts are untrusted until structural and integrity validation succeeds.
8. **Build/release boundary:** dependencies, Actions and artifacts are supply-chain inputs requiring provenance and integrity validation.

## Principals

### Local profile

- local workspace owner;
- stable local product actor/install identity;
- local OS account and platform secure storage;
- local model process;
- hosted model/embedding provider when explicitly selected.

### Hosted extension

Adds authenticated tenant users, evidence verifiers, tenant administrators, service identities and platform administrators. ADR-007 governs those boundaries.

## Threats and required controls

| Threat | Example | Required control |
|---|---|---|
| Unauthorized authority action | forged `operator_verified=true` | trusted ActorContext + capability check before verified signal construction |
| Evidence replay/double counting | same source through several channels | stable `source_ref` identity and ADR-004 deduplication |
| Artificial evidence identities | mint many refs for one source | actor attribution, audit visibility, later richer provenance where needed |
| Prompt injection via seed/evidence | instruction-like candidate text | structural prompt boundary, bounded surfacing, point-of-use checks, adversarial tests |
| SSL self-reinforcement | model sees seed then detector repeats it | same-turn contamination rule; exposed output cannot count as independent recurrence |
| Stale authorization | old Gate event reused after authority changes | authority versioning and current Gate-event link |
| Contradiction bypass | influence despite unresolved contradiction | Gate/point-of-use blocking invariant |
| Audit tampering | edit/delete/reorder authority history | append-only hash-chained ledger + protected signed/checkpoint root + verifier |
| Snapshot forgery | edit mutable state only | snapshot-to-ledger consistency verification |
| Malicious restore | crafted DB replaces workspace | schema/integrity/ledger validation before atomic replacement |
| Migration corruption | upgrade partially rewrites data | ordered migrations, backup preflight, transaction where possible, post-migration verification |
| Secret disclosure | key appears in state/export/log | secret-source abstraction, persistence rejection, redaction and negative tests |
| Provider exfiltration | arbitrary base URL receives credentials/content | endpoint allow policy; explicit hosted-provider confirmation; no arbitrary production target by default |
| Provider semantic fallback | outage silently changes model/policy | explicit failure; no silent model/Gate/evidence fallback |
| Resource exhaustion | huge prompt/export/seed flood | bounded sizes/counts/concurrency/timeouts with atomic failure |
| Local remote exposure | production launcher binds LAN/WAN | loopback enforcement for production-local profile |
| Export/archive attack | traversal, bomb, symlink | retain defensive ZIP verification and size/compression limits |
| Dependency compromise | mutable Actions/dependency drift | immutable Action SHAs, lock/constraints, scanning, SBOM, artifact signing/provenance |
| Repository bypass | direct push or force push to main | issue #66 ruleset/branch protection and break-glass policy |
| Privacy leakage in telemetry | prompt text becomes log label | content-minimized structured telemetry; no raw content labels |
| Backup lifecycle confusion | session delete claimed to remove exported backup | explicit deletion semantics and separate backup/export lifecycle |

## Security properties we do claim for production-local

Subject to accepted implementation and tests, the local profile may claim:

- ordinary network exposure is restricted to loopback;
- authority-bearing product actions are attributable to a trusted local actor context;
- a client boolean alone cannot produce verified authority support;
- Gate and point-of-use contracts remain the only supported authority/influence path;
- historical authority event tampering is detectable relative to protected local integrity material;
- supported database upgrades and restore operations are validated and recoverable;
- normal operational telemetry is content-minimized;
- released artifacts are tied to an exact source revision with declared integrity/provenance controls.

## Security properties we do not claim for production-local

- defense against a fully compromised operating system or malicious machine administrator;
- multi-user or tenant isolation;
- hostile-network service security;
- factual truth of operator-verified evidence;
- universal prompt-injection prevention;
- universal model correctness or answer-quality improvement;
- anonymity of support/research artifacts;
- commercial-use rights.

## Validation requirements

Before `production-ready/local`:

- every table threat above that applies to local has a corresponding implementation control;
- critical controls have negative/adversarial tests;
- authority/audit integrity failure is fail-closed for authority-bearing operations where consistency cannot be established;
- release acceptance cites the exact tested commit and no unresolved P0/P1 production finding remains.
