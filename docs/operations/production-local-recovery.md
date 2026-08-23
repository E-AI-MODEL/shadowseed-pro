# Production-local recovery runbook

This runbook covers the single-user local/workstation profile only. It does not describe hosted disaster recovery or claim continuity after a fully compromised local administrator/OS.

## 1. Diagnose before changing files

Run:

```bash
shadowseed doctor --json
shadowseed workspace info
```

If workspace or production-integrity validation fails, stop normal authority-bearing use. Do not delete `integrity.key`, replace `anchor.json`, edit `production_ledger`, or copy an older database over the live workspace to make the error disappear.

## 2. Preserve the failing state for investigation

If local policy permits, make a filesystem copy of the failing workspace directory for diagnostics. Treat it as content-bearing and sensitive. This diagnostic copy is not a supported live restore action and does not establish integrity.

## 3. Select a known backup

Backups are independent copies and can contain the same sensitive data as the source workspace. Select a backup created by the supported workspace backup flow. The restore path validates the backup size, SQLite integrity, schema, production ledger and logical workspace identity before replacement/import.

## 4. Existing-workspace restore

For a backup from the same logical workspace:

```bash
shadowseed workspace --workspace <workspace-path> restore <backup.db>
```

The application verifies the current live integrity state first, stages the restored mutable state, validates the staged database/ledger/authority snapshot, creates a new audit epoch and only then replaces the live database. The restore event commits both the prior live head and backup head.

After success:

```bash
shadowseed doctor --workspace <workspace-path> --json
shadowseed workspace --workspace <workspace-path> info
```

Confirm `production_integrity` is healthy and the workspace remains the expected logical identity.

## 5. Fresh-machine/import recovery

When the target path has no existing workspace identity/database, the same restore command performs an explicit import recovery. The backup logical workspace ID is preserved, a new local integrity key/anchor is created, and a new audit epoch records that previous protected-anchor continuity is unavailable.

This is a declared continuity break, not silent recreation of the old machine's protected integrity state.

## 6. Protected integrity material loss

If the live workspace ledger exists but its protected key/anchor is missing or cannot be authenticated, normal open/use fails closed. Do not manufacture replacement material for the existing epoch. Recover from a verified backup through the supported import/restore workflow, producing an explicit new recovery boundary.

## 7. Rollback after a bad application update

Application rollback and data rollback are separate:

1. stop Shadowseed;
2. preserve the current workspace and a known backup;
3. install a supported application version whose migration support window includes the workspace schema;
4. run `shadowseed doctor --json` before opening the workspace for normal use;
5. if data restore is necessary, use the supported restore workflow rather than replacing `workspace.db` manually.

An older internally valid database copied over a newer live workspace is expected to fail the protected anti-rollback check.

## 8. Full workspace erase

`shadowseed workspace delete --yes` removes the live workspace and workspace-specific protected integrity material. It does not delete independently created backups or exports. Verify those separately according to local data policy.

## Evidence backing this runbook

The Phase 3/4 test suites exercise same-workspace restore, fresh-machine import, backup integrity, old-valid-history rollback rejection, database/anchor crash recovery, missing integrity material, staged snapshot/ledger consistency, full workspace erase and independent-backup retention. Production publication still requires those tests and clean-machine platform checks to pass on the exact candidate commit.
