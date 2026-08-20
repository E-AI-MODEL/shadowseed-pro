# Production Migration and Recovery Policy

**Status:** Proposed

## Principle

A production schema change is incomplete until supported existing data can be upgraded, verified and recovered. Version numbers alone are not a migration system.

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
- recovery/restore procedure.

The initial support window must include at least the immediately previous production schema. A wider window may be adopted later.

## Upgrade flow

1. inspect database and schema metadata without mutating it;
2. reject a schema newer than the running product;
3. verify the source database and authority ledger before migration;
4. require/create a validated backup for migrations classified as destructive or high-risk;
5. execute each migration exactly once in declared order;
6. update schema metadata only with the corresponding successful migration;
7. run database integrity checks;
8. verify ledger and snapshot consistency;
9. start the product only after the complete target schema verifies.

A failed migration must not be reported as a healthy upgraded workspace.

## Atomicity and recovery

Use one database transaction for a migration where supported and safe. Large or platform-constrained migrations that cannot be fully atomic require an explicit migration journal and restart/recovery state.

Rollback does not mean every migration needs a reverse SQL script. For irreversible transformations, the supported rollback is restoration of the validated pre-migration backup with the previous application version.

## Compatibility

Historical event payloads remain historical. Migrations may add indexes, projections or compatibility metadata, but must not rewrite old Gate events to make them look as though newer policy semantics applied in the past.

Legacy missing runtime metadata retains the repository's documented compatibility interpretation unless a separately accepted ADR changes that contract.

## Tests

Every production schema version retained in the support window requires a fixture or deterministic constructor in tests.

CI must prove:

- upgrade from each supported source version to current;
- second initialization is idempotent after successful migration;
- corrupt/unsupported source fails without replacing good data;
- interrupted migration has the documented recovery result;
- backup made before a high-risk migration restores successfully;
- post-migration session/Gate/audit replay remains consistent;
- a database from a newer unsupported version is rejected.

## Release gate

No production release may change the schema version unless migration and recovery coverage lands in the same change. Release notes must state the schema impact and backup/restore requirement.
