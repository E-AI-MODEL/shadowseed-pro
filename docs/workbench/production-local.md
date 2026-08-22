# Production-local operating boundary

This document describes the bounded single-user `production-ready/local` target from ADR-006. It does not turn the generic Workbench remote-preview mode into a production network service and it does not grant commercial rights beyond `LICENSE`.

## Supported launcher boundary

The standalone product launcher uses `shadowseed.workbench.production_local.launch_production_local_workbench`. Its network host is fixed to `127.0.0.1`; the API has no host override and no remote-allow option.

The generic source command `shadowseed workbench --host ... --allow-remote` remains a trusted-environment/development preview surface. It has no multi-user authentication layer and is outside the `production-ready/local` claim.

## Container boundary

`Dockerfile.workbench` binds the process to `0.0.0.0` *inside the container* so Docker port forwarding works. That internal bind is not a production-host exposure policy. Publish the host port on loopback only:

```bash
docker build -f Dockerfile.workbench -t shadowseed-workbench .
docker run --rm \
  -p 127.0.0.1:7860:7860 \
  -v "$HOME/.shadowseed:/data" \
  shadowseed-workbench
```

Do not use `-p 7860:7860`, host networking, or a public reverse proxy and call that `production-ready/local`. A future hostile-network or multi-user deployment is governed by ADR-007 instead.

## Resource limits

The production-local application boundary rejects oversized or unreasonable integrity-sensitive input before state mutation. Current hard limits are defined in `shadowseed.application.limits` and cover messages, evidence references/notes, feedback notes, session/model configuration and imported backups. Export ZIP verification retains its separate file-count, per-file, aggregate-size and compression-ratio limits.

A limit failure is an explicit operation failure. It may not switch Gate policy, model backend, evidence semantics or persistence mode, and tests must prove authority/session state remains unchanged when a pre-commit limit fails.

## Workspace files and deletion

On POSIX hosts Shadowseed restricts product-managed workspace directories to owner-only access (`0700`) and primary local files to owner read/write (`0600`) where supported. Windows uses the current user/ACL security boundary rather than pretending POSIX mode bits provide the same guarantee.

Session deletion removes content-bearing live state while retaining only the documented content-minimized ledger continuity/tombstone. Full workspace erase removes the live workspace and its workspace-specific protected integrity material. Independently created backups and exports are separate copies and remain untouched until explicitly deleted.

No secure physical-media erasure claim is made beyond the underlying filesystem/platform.

## Operational logs

Production-local operational JSONL logs use an explicit metadata allow-list, bounded rotation and restrictive local file permissions where supported. Raw prompts, answers, messages, seed text, evidence references/notes, credentials and arbitrary exception payloads are not accepted as structured operational fields.

## Recovery

Do not repair a damaged production workspace by deleting its protected anchor/key and relaunching. Integrity continuity fails closed. Use a verified backup through the supported workspace restore/import flow so the recovery transition is explicit and auditable.

`shadowseed doctor` is the supported readiness/diagnostic entry point. Phase 4 acceptance requires it to distinguish usable workspace state, integrity problems and dependency degradation with actionable repair guidance.
