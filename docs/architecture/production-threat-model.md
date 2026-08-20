# Production Threat Model

**Status:** Accepted  
**Original implementation baseline:** `v0.6.0` at `02b8d2f505c837c88e5cc6654c7f864b751480f5`  
**Governance review:** refreshed 2026-08-20 after issue #66 protection enforcement; the architecture remains intentionally based on the v0.6.0 runtime contract until later phases change implementation.  
**Scope:** Phase 0 architecture for `production-ready/local`; hosted deltas are explicitly identified.

## Assets to protect

- seed authority state and Gate decision history;
- point-of-use authorization records;
- prompts, answers, seed text, evidence references/notes and feedback;
- stable workspace identity;
- workspace database, backups and exports;
- local actor identity, protected live audit anchor and private integrity/signing material;
- hosted provider credentials and provider configuration;
- release provenance, build artifacts and repository history;
- availability and resource budgets for model-backed operations.

## Trust boundaries

1. **Product boundary:** UI/CLI input is untrusted. The application layer validates trusted actor context, workspace scope and capability before authority-bearing operator operations.
2. **Runtime boundary:** detector/model output is untrusted content. It may create weightless candidates but may not grant authority.
3. **Gate boundary:** typed signals/actions may propose authority changes; only the Gate applies Gate-controlled authority effects.
4. **Point-of-use boundary:** promoted/current authority is necessary but not sufficient for influence.
5. **Persistence boundary:** current snapshots are mutable application state; the production ledger plus protected external live anchor form the local integrity boundary.
6. **Provider boundary:** local or hosted model/embedding providers are external dependencies. Their responses are data, not evidence authority.
7. **Import/export boundary:** backups and ZIP/report artifacts are untrusted until structural and integrity validation succeeds.
8. **Build/release boundary:** dependencies, Actions and artifacts are supply-chain inputs requiring provenance and integrity validation.

## Principals

### Local profile

- local workspace owner;
- stable local product actor/install identity;
- stable logical `workspace_id`;
- local OS account and platform secure storage;
- local model process;
- hosted model/embedding provider when explicitly selected.

### Hosted extension

Adds authenticated tenant users, evidence verifiers, tenant administrators, service identities and platform administrators. ADR-007 governs those boundaries.

## Threats and required controls

| Threat | Example | Required control |
|---|---|---|
| Unauthorized verified support | forged `operator_verified=true` | trusted ActorContext + `evidence.verify` before verified signal construction |
| Unauthorized negative authority action | untrusted UI invokes falsification | `contradiction.submit` + actor/scope attribution before canonical contradiction/Gate path |
| Unauthorized contradiction recovery | user closes blocking contradiction to regain eligibility | `contradiction.resolve` + recorded basis + existing Gate/revalidation sequencing |
| Evidence replay/double counting | same source through several channels | stable `source_ref` identity and ADR-004 deduplication |
| Artificial evidence identities | mint many refs for one source | actor attribution, audit visibility, later richer provenance where needed |
| Prompt injection via seed/evidence | instruction-like candidate text | structural prompt boundary, bounded surfacing, point-of-use checks, adversarial tests |
| SSL self-reinforcement | model sees seed then detector repeats it | same-turn contamination rule; exposed output cannot count as independent recurrence |
| Stale authorization | old Gate event reused after authority changes | authority versioning and current Gate-event link |
| Contradiction bypass | influence despite unresolved contradiction | Gate/point-of-use blocking invariant |
| Audit event tampering | edit/delete/reorder authority history | append-only workspace-wide hash chain + protected live anchor + verifier |
| Valid-history rollback | replace current DB with older valid backup and matching old internal chain | protected live anchor outside ordinary workspace; old head fails closed unless explicit restore creates new epoch |
| Snapshot forgery | edit mutable state only | snapshot-to-ledger consistency verification |
| Workspace identity confusion | copied DB treated as unrelated healthy workspace | stable `workspace_id`; explicit fork/import semantics |
| Protected key/anchor loss | secure-store entry deleted and product silently recreates it | fail-closed/degraded recovery; new actor/integrity epoch; no silent continuity claim |
| Crash between DB and anchor commit | authority ledger advances but external anchor does not | same-DB authority+ledger transaction plus recoverable anchor-update protocol |
| Malicious restore | crafted DB replaces workspace | schema/session-state/ledger validation before atomic replacement |
| Old backup restore as hidden rollback | valid old backup overwrites current state | compare with protected live anchor; explicit restore epoch referencing prior head and backup digest |
| Migration corruption | upgrade partially rewrites data | ordered migrations, backup preflight, transaction where possible, post-migration verification |
| Retroactive audit claim | imported v0.6 records described as historically tamper-evident | explicit pre-production genesis/import boundary |
| Secret disclosure | key appears in state/export/log | secret-source abstraction, persistence rejection, redaction and negative tests |
| Provider exfiltration | arbitrary base URL receives credentials/content | endpoint allow policy; explicit hosted-provider confirmation; no arbitrary production target by default |
| Provider semantic fallback | outage silently changes model/policy | explicit failure; no silent model/Gate/evidence fallback |
| Resource exhaustion | huge prompt/export/seed flood | bounded sizes/counts/concurrency/timeouts with atomic failure |
| Local remote exposure | production launcher binds LAN/WAN | loopback enforcement for production-local profile |
| Export/archive attack | traversal, bomb, symlink | retain defensive ZIP verification and size/compression limits |
| Dependency compromise | mutable Actions/dependency drift | immutable Action SHAs, lock/constraints, scanning, SBOM, artifact signing/provenance |
| Repository bypass | direct push or force push to main | issue #66 ruleset/branch protection and break-glass policy |
| Privacy leakage in telemetry | prompt text becomes log label | content-minimized structured telemetry; no raw content labels |
| Hash privacy leakage | raw low-entropy evidence text is naively hashed into permanent ledger | minimize ledger payload; hash structured identities/commitments rather than arbitrary raw user text |
| Deletion/audit conflict | session delete leaves raw evidence or prompt data in append-only history | content-minimized ledger design + explicit tombstone; full workspace erase ends local ledger continuity |
| Backup lifecycle confusion | session delete claimed to remove exported backup | explicit deletion semantics and separate backup/export lifecycle |

## Security properties we do claim for production-local

Subject to accepted implementation and tests, the local profile may claim:

- ordinary network exposure is restricted to loopback;
- authority-bearing product actions are attributable to a trusted local actor context and stable workspace scope;
- a client boolean alone cannot produce verified authority support;
- operator falsification and contradiction-resolution actions cannot bypass the production capability boundary;
- Gate and point-of-use contracts remain the only supported authority/influence path;
- historical production authority event tampering and rollback to an older valid live state are detectable relative to protected local integrity material;
- production audit claims begin at an explicit genesis/import boundary rather than being retroactively applied to v0.6.0 history;
- supported database upgrades and restore operations are validated and recoverable;
- normal operational telemetry is content-minimized;
- released artifacts are tied to an exact source revision with declared integrity/provenance controls.

## Security properties we do not claim for production-local

- defense against a fully compromised operating system or malicious machine administrator who can replace both workspace and protected integrity material;
- uninterrupted audit continuity after protected integrity material is irrecoverably lost; recovery creates an explicit new epoch;
- multi-user or tenant isolation;
- hostile-network service security;
- factual truth of operator-verified evidence;
- universal prompt-injection prevention;
- universal model correctness or answer-quality improvement;
- anonymity of support/research artifacts;
- secure physical-media erasure beyond the underlying platform;
- commercial-use rights.

## Validation requirements

Before `production-ready/local`:

- every table threat above that applies to local has a corresponding implementation control;
- critical controls have negative/adversarial tests;
- authority/audit integrity failure is fail-closed for authority-bearing operations where consistency cannot be established;
- valid-old-backup rollback and database/anchor crash windows are tested, not merely documented;
- v0.6.0 import proves the pre-production/production audit boundary;
- release acceptance cites the exact tested commit and no unresolved P0/P1 production finding remains.
