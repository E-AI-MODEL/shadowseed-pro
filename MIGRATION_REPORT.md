# Shadowseed repository rebuild report

## Result

A new English-language, installable Git repository was built from the supplied archive.

## Verified state

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
- live chat now stores uncontaminated baseline history and applies the same surfacing rules as the session benchmark
- contract-blocked seeds are not recorded as surfaced
- active code, CLI text, workflows, templates, and documentation are English
- historical source material remains under `archive/`

## Claim boundary

The repository is research-ready, not production-ready. Production use still needs durable persistence, migrations, monitoring, privacy and retention controls, operator gates, rollback, and real-world abuse testing.

## Publication note

No source license was present. Select a license before public distribution or third-party reuse.

No GitHub remote is configured in this package. A repository owner and repository name are required before pushing it to GitHub.
