# Shadowseed Workbench 0.4.1 Tester Preview

Shadowseed 0.4.1 is a corrective patch for two late P2 review findings that
arrived after the 0.4.0 Workbench pull requests had already merged.

## Fixed

- **Chronological seed audit timelines.** Events from seed, validation, Gate,
  contradiction, probe-feedback, and influence ledgers are now interleaved by
  their actual timestamp instead of being grouped by ledger. ISO-8601 timezone
  offsets are normalized before ordering; missing or malformed timestamps retain
  a deterministic fallback order.
- **Scenario batch failure isolation.** A backend error after earlier scenario
  questions have succeeded now returns a partial, resumable result containing
  the session id, completed count, failure position, and error instead of losing
  the caller's progress context.
- **Safe scenario resume.** The Workbench can retry from the failed question
  without replaying completed calls. Resume validates the persisted turn count,
  the already-completed question prefix, backend, model, and profile before
  continuing, which protects hosted-model testers from stale-state replay or
  accidental skips.
- **Workbench UI status.** Partial scenario runs are shown as paused rather than
  completed and expose a dedicated resume action.

## Release discipline

`v0.4.0` remains unchanged and continues to identify the exact artifact that was
published on 2026-08-08. This patch is released as a new `v0.4.1` tag after the
same full CI, Workbench CI, cross-platform portability, Docker, clean-wheel,
export, and checksum gates succeed on `main`.

The preview remains local-first, single-user, research-ready, and not
production-ready. These fixes improve tester reliability and audit presentation;
they do not constitute new benchmark evidence or a scientific model-benefit
claim.
