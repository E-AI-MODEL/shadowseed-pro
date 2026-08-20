# Production Persistence and Audit Contract

**Status:** Proposed  
**Scope:** `production-ready/local` first; hosted implementations must preserve or strengthen the same integrity properties.

## Goals

Production storage must serve two different needs without confusing them:

- efficient mutable state used to resume a session;
- independently verifiable history of authority-relevant events.

The current v0.6.0 normalized audit tables are useful query projections, but they are rebuilt from session state and therefore are not independent production audit evidence.

## Storage model

Production persistence will separate:

1. **session snapshot**: current resumable runtime state;
2. **normalized projections**: turns, current seeds, feedback and query-friendly records;
3. **authority ledger**: append-only canonical history for authority/influence-relevant events;
4. **workspace metadata**: schema, migration and integrity metadata;
5. **integrity checkpoint material**: chain roots/signatures or references required to verify ledger history.

Snapshots and projections are replaceable derived/application state. The authority ledger is not rewritten during ordinary saves.

## Authority ledger event

The implementation format may evolve, but each canonical ledger event must carry or canonically commit to:

- ledger event id;
- session id;
- seed id where applicable;
- event type;
- monotonic per-scope or per-session sequence;
- canonical payload;
- payload digest;
- previous ledger-event digest or chain root;
- actor id/scope for operator actions where applicable;
- request/correlation id where applicable;
- Gate event id and authority version where applicable;
- timestamp;
- schema/event-format version.

Canonical serialization must be deterministic before hashing.

## Events that require ledger coverage

At minimum:

- verified evidence submission authorization;
- Gate decisions and authority transitions;
- contradiction creation/resolution transitions that affect authority eligibility;
- point-of-use allow/deny decisions linked to current Gate authority;
- production identity reset/change events relevant to audit interpretation;
- migration/restore integrity checkpoints;
- deletion tombstone/checkpoint behavior where needed to explain intentional lifecycle changes.

Ordinary model text does not automatically belong in the integrity ledger. Sensitive content should be represented by stable ids/digests where full content is not required for authority replay.

## Tamper evidence

For the local profile, events will form a cryptographic hash chain and the product will maintain protected checkpoint/signing material outside ordinary session state. Exact key storage/signature technology is selected during implementation based on supported platforms.

Verification must detect at least:

- event payload modification;
- event deletion from the middle of a chain;
- event reordering;
- chain splicing without a valid checkpoint;
- snapshot authority state inconsistent with ledger history.

The claim is tamper evidence relative to protected local integrity material, not immunity against a fully compromised host administrator.

## Transaction boundary

An authority-bearing operation must not commit mutable authority state without committing the corresponding ledger record in the same durable application transaction where technically possible.

Where platform limitations require staged commits, the runtime must have a recoverable journal/state that prevents an unlogged successful authority transition from being treated as healthy production state.

On detection of an authority snapshot/ledger inconsistency, production authority-bearing operations fail closed until verification/recovery succeeds. Read-only recovery/export tooling may remain available where safe.

## Replay and verification

Production tooling must support:

- verify ledger chain/checkpoints;
- cross-check current seed authority/version against ledger history;
- verify point-of-use records against current-version Gate event references;
- identify first integrity failure without silently repairing it;
- produce a content-minimized integrity report suitable for support diagnostics.

Verification may use existing runtime replay semantics but must not rewrite historical event payloads.

## Backup and restore

A production backup includes all state needed to verify the restored workspace, including ledger/checkpoint metadata that is safe and appropriate to export.

Restore flow:

1. open source read-only;
2. validate format/schema compatibility;
3. verify structural database integrity;
4. verify ledger integrity and required checkpoints;
5. validate migration path if an upgrade is required;
6. restore into a temporary target;
7. run post-restore replay/snapshot consistency checks;
8. atomically replace the live workspace only after success.

A failed restore leaves the existing live workspace intact.

## Deletion

Session/workspace deletion is an intentional product operation, not hidden ledger rewriting.

The implementation must define whether the local full-workspace delete removes the complete ledger and integrity material together, while session-level deletion may use a deletion record/tombstone before content removal where audit continuity is required. The final choice must satisfy the data-lifecycle contract and avoid claiming historical audit retention after the user intentionally performs a full local erase.

Backups and exports remain separate copies and are not deleted automatically unless explicitly managed by the product.

## Hosted extension

Hosted persistence must use service-controlled write permissions, tenant-scoped ledger chains/checkpoints and a database architecture designed for concurrency and isolation. Shared local SQLite is not a hosted production database.

## Acceptance targets for Phase 3

- historical ledger rows are never deleted/rebuilt during ordinary session save;
- mutation/deletion/reordering tests fail verification;
- current authority snapshot cannot silently diverge from ledger history;
- interrupted authority write has a deterministic recovery outcome;
- backup/restore round trip preserves and verifies ledger integrity;
- historical Gate payloads remain readable without retroactive semantic rewriting;
- integrity diagnostics avoid leaking ordinary prompt/seed content by default.
