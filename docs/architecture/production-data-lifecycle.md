# Production Data Lifecycle

**Status:** Proposed  
**Primary profile:** `production-ready/local`

## Data classes

| Data class | Purpose | Sensitivity | Local retention default | Delete behavior | Export/provider behavior |
|---|---|---|---|---|---|
| prompts and answers | conversation | content-bearing | until session/workspace deletion | removed with source session/workspace | full reports may include; hosted model calls transmit relevant content |
| SSL-off controls | product comparison | content-bearing | with source turn/session | removed with source session/workspace | full reports may include; hosted comparison creates an extra provider request |
| seed text | candidate memory | content-bearing | with session | removed with source session/workspace | full reports may include; support bundles omit text |
| Gate/influence records | authority/audit | potentially sensitive metadata | with authority history | follows session/workspace policy and audit contract | minimized support may include structural metadata; full reports may include records |
| evidence `source_ref` | evidence identity | potentially confidential | with evidence history | follows source session/workspace | research/full artifacts may include; avoid secret URLs/credentials |
| evidence notes | operator rationale | content-bearing | with evidence history | follows source session/workspace | never normal telemetry; content-bearing exports only |
| tester feedback | research/product feedback | content-bearing | with session | removed with session/workspace | full reports may include; minimized support omits free text |
| actor id | authority attribution | pseudonymous/security metadata | as required for auditable history | removed on full local erase; session-level behavior follows audit design | may appear in integrity/admin export only when necessary |
| operational logs | product health/security | metadata only by default | bounded/rotated | expiry/rotation policy | no raw prompt/answer/seed/evidence-note content by default |
| backups | user recovery | same sensitivity as source | user-managed | explicit separate deletion | never treated as privacy-minimized |
| full reports | user export | content-bearing | user-managed | explicit separate deletion | share only after inspection |
| support bundles | support diagnostics | minimized but pseudonymous | user-managed | explicit separate deletion | structural/environment metadata only per export contract |
| efficacy/research bundles | research | content-bearing | study policy | study-controlled | not governed by support-bundle minimization assumptions |

## Local production rules

1. No automatic cloud workspace synchronization is part of the default local profile.
2. Workspace files use restrictive permissions available on the host platform where practical.
3. Session deletion removes the declared session-owned primary data from the live workspace.
4. Full workspace deletion removes the live workspace and local production integrity material associated only with that workspace.
5. Backups and exported files are independent copies. Product UI/documentation must not claim they were deleted when only the live source was deleted.
6. Operational logs are bounded/rotated and content-minimized.
7. Raw prompts, answers, seed text and free evidence notes are forbidden as ordinary metric labels or routine operational log fields.
8. Hosted provider transmission remains explicit at configuration/use time and is governed by the provider/account terms outside the local workspace.

## Retention configuration

The first local production implementation may keep primary session data until explicit deletion rather than inventing an automatic retention period. Any future automatic retention must be opt-in or clearly product-defined and tested.

Operational logs require an explicit bounded retention/rotation setting because they are not user conversation storage.

## Deletion verification

Tests must prove that declared primary rows/files are absent after session/workspace deletion and that orphaned normalized records are not left behind. Where the audit contract requires a session deletion record before content removal, documentation must distinguish that minimal audit record from retained conversation content.

## Hosted extension

Hosted production must add enforceable tenant/user retention, deletion requests, access logging, backup-expiry behavior and deletion verification across primary data, caches, indexes and asynchronous jobs. Those requirements are not satisfied by this local policy alone.

## Privacy claim boundary

Data minimization, pseudonymization and integrity verification do not imply anonymity. External evidence truth is not established by storage or verification. Product documentation must keep these claims separate.
