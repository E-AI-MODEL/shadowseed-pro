# Production Data Lifecycle

**Status:** Proposed  
**Primary profile:** `production-ready/local`

## Data classes

| Data class | Purpose | Sensitivity | Local retention default | Delete behavior | Export/provider behavior |
|---|---|---|---|---|---|
| prompts and answers | conversation | content-bearing | until session/workspace deletion | removed with source session/workspace | full reports may include; hosted model calls transmit relevant content |
| SSL-off controls | product comparison | content-bearing | with source turn/session | removed with source session/workspace | full reports may include; hosted comparison creates an extra provider request |
| seed text | candidate memory | content-bearing | with session | removed with source session/workspace | full reports may include; support bundles omit text |
| Gate/influence runtime records | runtime authority/audit detail | potentially sensitive metadata/content | with source session unless separately minimized into production ledger | content-bearing copies removed with session; minimal ledger commitments may remain | full reports may include records |
| production authority ledger | integrity/authorization history | security metadata, content-minimized | lifetime of live workspace | session delete keeps only minimum continuity metadata/tombstone; full workspace erase removes ledger | integrity/admin export only as needed; no private integrity keys |
| evidence `source_ref` | evidence identity | potentially confidential/content-bearing | with evidence/session history | raw value removed with session; ledger may retain only stable digest/minimal commitment | research/full artifacts may include; avoid secret URLs/credentials |
| evidence notes | operator rationale | content-bearing | with evidence/session history | removed with source session/workspace | never normal telemetry; content-bearing exports only |
| tester feedback | research/product feedback | content-bearing | with session | removed with session/workspace | full reports may include; minimized support omits free text |
| actor id | authority attribution | pseudonymous/security metadata | as required for auditable workspace history | may remain in content-minimized workspace ledger until full erase | integrity/admin export only when necessary |
| workspace id | logical workspace scope/integrity | pseudonymous/security metadata | lifetime of logical workspace | removed from live product on full workspace erase | may appear in integrity/backup metadata; not a secret |
| protected integrity key/anchor | anti-rollback/integrity | security-sensitive | lifetime of local workspace/epoch | removed/invalidated on full erase or explicit recovery transition | private key/anchor secrets are never ordinary backup/export content |
| operational logs | product health/security | metadata only by default | bounded/rotated | expiry/rotation policy | no raw prompt/answer/seed/evidence-note content by default |
| backups | user recovery | same sensitivity as source | user-managed | explicit separate deletion | never treated as privacy-minimized; no private local integrity key |
| full reports | user export | content-bearing | user-managed | explicit separate deletion | share only after inspection |
| support bundles | support diagnostics | minimized but pseudonymous | user-managed | explicit separate deletion | structural/environment metadata only per export contract |
| efficacy/research bundles | research | content-bearing | study policy | study-controlled | not governed by support-bundle minimization assumptions |

## Local production rules

1. No automatic cloud workspace synchronization is part of the default local profile.
2. Workspace files use restrictive permissions available on the host platform where practical.
3. Session deletion removes the declared session-owned content-bearing primary data from the live workspace.
4. The append-only workspace ledger is not rewritten to remove an event from the middle of its chain. After session deletion it may retain only the minimum typed security/authority metadata, digests and deletion tombstone required for integrity continuity. It must not retain raw prompt, answer, seed, evidence-reference or evidence-note content merely for audit convenience.
5. UI and documentation disclose that session deletion can leave this minimal content-minimized workspace audit metadata until full workspace erase.
6. Full workspace deletion removes the live database/ledger and clears or invalidates the workspace-specific protected integrity key/anchor association from supported platform secure storage.
7. Full workspace erase makes no claim about independently created backups, reports or support/research exports.
8. Backups and exported files are independent copies. Product UI/documentation must not claim they were deleted when only the live source was deleted.
9. Operational logs are bounded/rotated and content-minimized.
10. Raw prompts, answers, seed text, raw evidence source references and free evidence notes are forbidden as ordinary metric labels or routine operational log fields.
11. Hosted provider transmission remains explicit at configuration/use time and is governed by the provider/account terms outside the local workspace.

## Session deletion procedure

A production session deletion must be explicit and atomic with respect to the live database.

At minimum it:

1. verifies actor/scope authorization where the production boundary requires it;
2. creates the content-minimized session deletion/tombstone ledger event needed for continuity;
3. deletes session-owned content-bearing rows/projections and raw evidence metadata in the same durable operation where technically possible;
4. verifies that no orphaned session-owned content-bearing data remains in live tables;
5. advances/verifies the protected integrity anchor using the normal crash-recovery protocol.

A failure cannot be presented as a completed deletion.

## Full workspace erase

Full workspace erase is intentionally stronger than session deletion. It removes the entire local Shadowseed workspace and therefore also ends the local ledger continuity for that workspace.

The supported erase flow must attempt to remove:

- live database and sidecar/journal files;
- workspace-local caches or temporary content under product control;
- workspace-specific protected integrity keys/anchors or references in supported platform secure storage;
- other product-managed files explicitly declared part of the live workspace.

The product must report any component it could not delete. It must not imply secure media erasure beyond guarantees provided by the underlying filesystem/platform.

## Retention configuration

The first local production implementation may keep primary session data until explicit deletion rather than inventing an automatic retention period. Any future automatic retention must be opt-in or clearly product-defined and tested.

Operational logs require an explicit bounded retention/rotation setting because they are not user conversation storage.

The minimal workspace authority ledger persists until full workspace erase because rewriting history would break the production integrity contract. Its schema must therefore remain deliberately content-minimized.

## Deletion verification

Tests must prove:

- declared content-bearing primary rows/files are absent after session/workspace deletion;
- raw `source_ref` and evidence-note values for a deleted session are not retained in the live production ledger when only their digest/minimal commitment is needed;
- orphaned normalized records are not left behind;
- session deletion retains only the documented minimal ledger/tombstone material;
- full workspace erase removes live ledger state and attempts secure-store key/anchor cleanup;
- backups/exports remain untouched unless separately deleted.

## Hosted extension

Hosted production must add enforceable tenant/user retention, deletion requests, access logging, backup-expiry behavior and deletion verification across primary data, caches, indexes and asynchronous jobs. A hosted design must separately resolve integrity-history retention versus legal/user deletion requirements, potentially through tenant-scoped chains, key destruction or other accepted mechanisms. Those requirements are not satisfied by this local policy alone.

## Privacy claim boundary

Data minimization, pseudonymization, hashing and integrity verification do not imply anonymity. A digest of low-entropy or guessable content may still carry privacy risk; therefore the production ledger should commit to structured event identities rather than indiscriminately hash arbitrary raw user text.

External evidence truth is not established by storage or verification. Product documentation must keep these claims separate.
