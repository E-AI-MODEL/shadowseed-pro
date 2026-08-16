# Shadowseed repository rebuild report

This report records the initial archive rebuild. Test counts below are historical;
the README, architecture documentation, and current CI describe the active runtime.

## Result

A new English-language, installable Git repository was built from the supplied archive.

## Verified state at rebuild completion

- 506 source files individually mapped in `docs/migration/file-manifest.csv`
- 375 tests passing
- 4 optional-backend tests skipped
- Python compilation passing
- Ruff checks passing
- installed CLI verified from `/tmp`
- fixture chat smoke test passing
- packaged default gap-suite input verified outside the source tree

## Structural changes

- shared surfacing policy extracted to `shadowseed.surfacing`
- recurrence refresh extracted to `shadowseed.recurrence`
- model and embedding backends moved to `shadowseed.adapters`
- model detector moved to `shadowseed.detection`
- retrieval probes, recurrence clustering, and text similarity moved out of the benchmark namespace
- `shadowseed.chat` now exposes a one-generation `live` product path and a separate baseline-isolated `evaluation` path
- contract-blocked seeds are not recorded as surfaced
- active code, CLI text, workflows, templates, and documentation are English
- historical source material remains under `archive/`

## Claim boundary

The repository is research-ready, not production-ready. Production use still needs durable persistence, migrations, monitoring, privacy and retention controls, operator gates, rollback, and real-world abuse testing.

## Publication note

No source license was present in the supplied archive, and the rebuilt repository
still does not declare one. Select a license before third-party reuse.
