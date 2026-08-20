# Production Persistence and Audit Contract

**Status:** Accepted  
**Scope:** `production-ready/local` first; hosted implementations must preserve or strengthen the same integrity properties.

## Goals

Production storage must serve two different needs without confusing them:

- efficient mutable state used to resume a session;
- independently verifiable history of authority-relevant events.

The current v0.6.0 normalized audit tables are useful query projections, but they are rebuilt from session state and therefore are not independent production audit evidence.

Production integrity begins at an explicit production-ledger boundary. Migrating old research-preview state must never retroactively describe mutable historical records as though they had always been append-only or tamper-evident.

## Workspace identity

Every production workspace has a stable opaque `workspace_id` stored in workspace metadata. It is the canonical local authorization/audit scope and is independent of filesystem path, machine hostname or display title.

Rules:

- normal backup/restore of the same logical workspace preserves `workspace_id`;
- moving a backup to a new machine may preserve the logical `workspace_id`, but the import creates a new local actor/integrity epoch and records the transition;
- creating an intentionally independent copy/fork requires a new `workspace_id` and a recorded fork/import provenance event;
- copying database files by hand is not a supported way to mint a second healthy production workspace identity.

## Storage model

Production persistence will separate:

1. **session snapshot**: current resumable runtime state;
2. **normalized projections**: turns, current seeds, feedback and query-friendly records;
3. **authority ledger**: append-only canonical integrity history for authority/influence-relevant events;
4. **workspace metadata**: `workspace_id`, schema, migration and integrity metadata;
5. **protected live anchor**: the current audit epoch/head information stored outside ordinary workspace data;
6. **public verification material**: key identifiers/public keys/checkpoint metadata required to verify retained history without exposing private integrity material.

Snapshots and projections are replaceable derived/application state. The authority ledger is not rewritten during ordinary saves.

## Ledger scope and sequence

The local production profile uses a workspace-wide monotonic ledger sequence. Each event identifies its session and seed where applicable.

A workspace-wide chain gives migrations, restores, actor changes and session authority events one ordered integrity history. Content-bearing session data is not required in the chain: the ledger stores the minimum typed authority/security metadata and cryptographic commitments needed for integrity verification.

Timestamps are audit metadata but are not trusted as the ordering primitive. Ledger sequence and hash linkage define order.

## Authority ledger event

The implementation format may evolve, but each canonical ledger event must carry or canonically commit to:

- `workspace_id`;
- audit epoch;
- ledger event id;
- workspace-wide monotonic sequence;
- session id and seed id where applicable;
- event type;
- canonical minimal event payload;
- payload/event digest;
- previous ledger-event digest;
- actor id/scope for operator actions where applicable;
- request/idempotency/correlation id where applicable;
- Gate policy, verdict, Gate event id and authority version where applicable;
- authority state before/after where applicable;
- typed signal metadata needed to interpret the decision, with content-bearing evidence fields represented by stable cryptographic digests where raw values are unnecessary;
- timestamp;
- schema/event-format version.

Canonical serialization must be deterministic before hashing.

Raw prompts, answers, seed text, evidence notes and ordinary model output are not stored in the integrity ledger merely to make hashing convenient. A ledger event may commit to a digest of a fuller runtime event while retaining only the minimal replay/integrity fields required by the production contract.

## Events that require ledger coverage

At minimum:

- verified evidence attestation/authorization and submission;
- operator-triggered contradiction/falsification and contradiction-resolution actions;
- Gate decisions and authority transitions;
- contradiction lifecycle transitions that affect authority eligibility;
- point-of-use allow/deny decisions linked to current Gate authority;
- production identity/key/actor rotation or reset events relevant to audit interpretation;
- migration, import, restore and integrity-epoch transitions;
- session deletion tombstones and other lifecycle events needed to explain intentional removal of content-bearing state.

Ordinary model text does not automatically belong in the integrity ledger.

## Protected anchor and anti-rollback

A valid hash chain alone does not detect replacement of the workspace with an older, internally valid copy. `production-ready/local` therefore requires a protected live anchor outside the ordinary workspace database.

The protected anchor commits at least to:

- `workspace_id`;
- current audit epoch;
- latest anchored ledger sequence;
- latest anchored ledger head digest;
- integrity key/public-key identifier.

The anchor and private integrity material are stored using the strongest supported local platform protection selected by the implementation. They are never persisted in ordinary session configuration, normal exports or backups.

Verification rules:

- a database whose ledger head is behind the protected live anchor is a rollback/integrity failure and fails closed for authority-bearing operations;
- a database ahead of the anchor is accepted only through the defined crash-recovery protocol when the extra chain is a valid continuation of the anchored head and no conflicting anchored state exists;
- replacing both the database and the protected anchor is outside the production-local threat claim because that implies compromise of the protected local integrity boundary;
- an intentional restore of older state is not treated as an invisible rollback. It must use the supported restore workflow and create a new audit epoch that references the previous live head and the restored backup identity/digest.

## Audit epochs and integrity-key lifecycle

An audit epoch marks a deliberate integrity-continuity transition. Examples include an authorized restore to older state, cross-machine import, or recovery when the previous protected local integrity key/anchor is unavailable.

Normal key rotation should link old and new verification material in the ledger and preserve continuity where the old key remains available.

Loss of protected integrity material must never silently recreate the same actor/key identity or continue the same epoch as though nothing happened. Recovery enters a fail-closed/degraded mode, requires an explicit user recovery action, creates a new actor/integrity epoch, and records the continuity boundary. Historical internally verifiable records remain historical; the product must not claim an anti-rollback guarantee across a continuity break it can no longer prove.

## Tamper evidence

For the local profile, events form a cryptographic hash chain and the product maintains the protected live anchor described above. The implementation may additionally sign each event or checkpoint/head, but the anti-rollback property may not rely only on mutable data stored beside the workspace.

Verification must detect at least:

- event payload modification;
- event deletion from the middle of a chain;
- event reordering;
- chain splicing;
- workspace replacement with an older valid ledger head relative to the protected anchor;
- snapshot authority state inconsistent with ledger history;
- unexpected workspace identity or audit-epoch changes.

The claim is tamper evidence relative to protected local integrity material, not immunity against a fully compromised host administrator.

## Transaction and crash-recovery boundary

For the local SQLite production profile, an authority mutation and its corresponding append-only ledger event **must** commit in the same SQLite transaction. This is not optional while both records live in the same database.

The protected external anchor cannot participate in that SQLite transaction, so implementation must use a recoverable anchor-update protocol. At minimum it must distinguish:

1. database/ledger transaction durably committed;
2. protected anchor update pending;
3. protected anchor updated and verified.

A crash between database commit and anchor update may be recovered only by verifying that the database chain is a unique valid extension of the previously protected head before advancing the anchor. A database behind or conflicting with the protected head fails closed.

No successful production authority transition may be treated as healthy if neither the ledger transaction nor a recoverable anchor state can account for it.

## Replay and verification

Production tooling must support:

- verify workspace identity, audit epoch and protected anchor relation;
- verify ledger chain/checkpoints;
- cross-check current seed authority/version against ledger history;
- verify point-of-use records against current-version Gate event references;
- distinguish historical pre-production imported state from post-boundary production ledger events;
- identify the first integrity failure without silently repairing it;
- produce a content-minimized integrity report suitable for support diagnostics.

Verification may use existing runtime replay semantics but must not rewrite historical event payloads.

## v0.6.0 / pre-production bootstrap boundary

The first production schema must handle the existing v0.6.0 workspace explicitly.

Because v0.6.0 `audit_events` are rebuilt from mutable session state, migration cannot claim that those records were historically append-only. A supported import/migration therefore creates a production-ledger genesis/baseline event that commits to the validated pre-migration workspace/session state and records at least:

- source application/schema version;
- source workspace/database digest or equivalent validated snapshot commitment;
- import timestamp and actor;
- `pre_production_history = true` or equivalent provenance marker;
- first production `workspace_id`/audit epoch/head.

Existing historical Gate/influence records remain readable as migrated historical data, but tamper-evident production-history claims begin at this explicit boundary.

## Backup and restore

A production backup includes the workspace database, ledger, public verification material and metadata needed to verify its internal integrity. It does **not** include private local integrity/signing keys or the mutable protected live anchor used for anti-rollback.

Restore flow:

1. open source read-only;
2. validate format/schema/session-state compatibility;
3. verify structural database integrity;
4. verify ledger and included public verification material;
5. compare backup workspace identity/epoch/head with the current protected live anchor when restoring into an existing workspace;
6. validate migration path if an upgrade is required;
7. restore into a temporary target;
8. run post-restore replay/snapshot consistency checks;
9. create the required restore/import audit-epoch transition;
10. atomically replace the live workspace and advance the protected anchor only after the complete recovery protocol succeeds.

A failed restore leaves the existing live workspace and protected anchor intact.

A cross-machine import with no previous machine anchor available is explicitly recorded as an import/continuity transition; it does not pretend to prove anti-rollback continuity against the unavailable old anchor.

## Deletion

Session/workspace deletion is an intentional product operation, not hidden ledger rewriting.

For the local production profile:

- session deletion removes content-bearing session state, normalized projections, raw evidence references/notes and other data declared session-owned by the data-lifecycle contract;
- the workspace-wide ledger is not rewritten to erase events from the middle of its hash chain;
- only content-minimized authority/security metadata and cryptographic commitments needed for ledger continuity may remain, plus an explicit session-deletion tombstone;
- documentation and UI must disclose that this minimal audit metadata remains until full workspace erasure;
- full workspace deletion removes the live workspace ledger and workspace-specific protected anchor/key association together, subject to platform secure-store cleanup;
- backups and exports remain separate copies and are not deleted automatically.

This is a deliberate local privacy/integrity tradeoff. Hosted deletion requirements remain a separate ADR-007 design problem and may require tenant-specific retention or cryptographic-erasure mechanisms.

## Hosted extension

Hosted persistence must use service-controlled write permissions, tenant-scoped ledger/checkpoint design and a database architecture designed for concurrency and isolation. Shared local SQLite is not a hosted production database.

## Acceptance targets for Phase 3

- stable `workspace_id` is enforced independently of filesystem path;
- historical ledger rows are never deleted/rebuilt during ordinary session save;
- authority mutation and ledger append share one local SQLite transaction;
- mutation/deletion/reordering/rollback tests fail verification;
- current authority snapshot cannot silently diverge from ledger history;
- interrupted database/anchor update has a deterministic recovery outcome;
- old valid backup replacement cannot silently pass as the current live workspace;
- intentional restore creates an explicit new audit epoch;
- key/anchor loss cannot silently recreate continuity;
- backup/restore round trip preserves verifiable internal history without exporting private integrity keys;
- v0.6.0 import creates an explicit pre-production history boundary rather than retroactive tamper-evidence claims;
- session deletion removes content-bearing data while preserving only declared minimal ledger continuity metadata;
- historical Gate payloads remain readable without retroactive semantic rewriting;
- integrity diagnostics avoid leaking ordinary prompt/seed/evidence-note content by default.
