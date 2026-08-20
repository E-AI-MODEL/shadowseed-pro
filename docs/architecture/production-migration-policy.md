# Production Migration and Recovery Policy

**Status:** Proposed

## Principle

A production schema change is incomplete until supported existing data can be upgraded, verified and recovered. Version numbers alone are not a migration system.

Migration also must not manufacture assurance retroactively. Data created before the production audit boundary remains historical pre-production state even after it is imported into the production schema.

## Migration model

Production storage will use explicit ordered migration identifiers. A migration declares:

- source schema version(s);
- target schema version;
- preconditions;
- data transformation;
- integrity checks;
- whether the migration is transactional;
- backup requirement;
- post-migration verification;
- recovery/restore procedure;
- any audit/bootstrap event it creates;
- whether the source contains pre-production history whose integrity claim begins only at import.

The initial production support window must include the v0.6.0 workspace schema and, after the first production release, at least the immediately previous production schema. A wider window may be adopted later.

## Stable workspace identity

The first production schema introduces a stable opaque `workspace_id`.

Migration rules:

- a v0.6.0 workspace receives its first production `workspace_id` during validated production bootstrap;
- ordinary later upgrades preserve it;
- normal backup/restore of the same logical workspace preserves it;
- explicit fork/copy-as-new creates a new identity through a supported import/fork operation rather than by editing metadata;
- filesystem path, machine hostname and session ids are not substitutes for `workspace_id`.

## v0.6.0 production bootstrap

v0.6.0 has mutable session snapshots, normalized projections and an `audit_events` table that is rebuilt from those snapshots. Those records are useful historical data but are not independent append-only audit evidence.

The first production migration must therefore:

1. validate the v0.6.0 database structurally and load all persisted sessions through the supported runtime restoration path;
2. verify existing Gate/point-of-use replay invariants as far as the v0.6.0 runtime contract permits;
3. create a validated pre-migration backup;
4. assign the production `workspace_id` and initialize the first audit epoch;
5. create a production genesis/import ledger event that cryptographically commits to the validated pre-production workspace state and records the source application/schema version;
6. mark imported historical records as pre-production history rather than rewriting them into new ledger events that imply earlier tamper evidence;
7. initialize the protected local anchor only after the migrated database and genesis event verify;
8. leave the v0.6.0 source/backup recoverable if any step fails.

Production tamper-evidence and anti-rollback claims begin at that explicit genesis/import boundary.

## Upgrade flow

1. inspect database and schema metadata without mutating it;
2. reject a schema newer than the running product;
3. identify whether the source is pre-production bootstrap or an already production-ledgered workspace;
4. verify the source database and, when present, authority ledger/protected-anchor relation before migration;
5. require/create a validated backup before every production schema migration unless an accepted migration explicitly proves that no durable user data can be at risk; the default is backup-first;
6. execute each migration exactly once in declared order;
7. update schema metadata only with the corresponding successful migration;
8. run database integrity checks;
9. verify ledger and snapshot consistency;
10. create/verify any required migration checkpoint event;
11. start the product only after the complete target schema and protected anchor relation verify.

A failed migration must not be reported as a healthy upgraded workspace.

## Atomicity and recovery

Use one SQLite transaction for each local production database migration where supported and safe. Large/platform-constrained migrations that cannot be fully atomic require an explicit migration journal and restart/recovery state defined by that migration.

Updates to protected integrity anchors occur through the persistence contract's recoverable anchor-update protocol. A migration cannot leave the database at a new valid ledger head while silently treating an old protected anchor as healthy.

Rollback does not mean every migration needs a reverse SQL script. For irreversible transformations, the supported rollback is restoration of the validated pre-migration backup with the previous application version, through the explicit restore/audit-epoch workflow.

## Compatibility

Historical event payloads remain historical. Migrations may add indexes, projections or compatibility metadata, but must not rewrite old Gate events to make them look as though newer policy semantics or production integrity guarantees applied in the past.

Legacy missing runtime metadata retains the repository's documented compatibility interpretation unless a separately accepted ADR changes that contract.

## Tests

Every production schema version retained in the support window requires a fixture or deterministic constructor in tests. v0.6.0 remains the required pre-production bootstrap fixture until the product explicitly ends that migration path.

CI must prove:

- v0.6.0 bootstrap creates a stable `workspace_id`, explicit pre-production genesis boundary and verified first production anchor;
- upgrade from each supported production source version to current;
- second initialization is idempotent after successful migration;
- corrupt/unsupported source fails without replacing good data;
- imported historical Gate events remain semantically unchanged;
- interrupted database migration has the documented recovery result;
- interrupted anchor advancement has the documented recovery result;
- pre-migration backup restores successfully;
- post-migration session/Gate/audit replay remains consistent;
- old-but-valid backup cannot silently replace a newer live workspace without an explicit restore epoch;
- a database from a newer unsupported version is rejected.

## Release gate

No production release may change the schema version unless migration and recovery coverage lands in the same change. Release notes must state:

- source schemas supported;
- target schema;
- whether the release creates a new audit epoch or format;
- backup/restore requirements;
- any continuity limitation that prevents a stronger historical integrity claim.
