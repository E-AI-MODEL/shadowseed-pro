# Shadowseed Tester Workbench

The Workbench is a local-first tester application over the existing Shadowseed
runtime. It does not introduce a second seed lifecycle or Gate implementation.

The implementation plan is maintained in
[`docs/plans/tester-workbench-0.4.md`](../plans/tester-workbench-0.4.md).

## Foundation commands

```bash
shadowseed doctor
shadowseed init
shadowseed workspace info
shadowseed workspace backup
```

The default workspace is `~/.shadowseed`. Override it with `--workspace` for
isolated test runs. Backend credentials stay in environment variables or an
operating-system keyring and are never written as workspace configuration.
Session messages are stored locally, so testers should not paste secrets into
conversations.
