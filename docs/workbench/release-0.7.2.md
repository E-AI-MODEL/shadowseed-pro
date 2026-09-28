# Shadowseed Workbench 0.7.2 Research Preview

Shadowseed Workbench 0.7.2 is a production-local assurance candidate for the credential-free macOS distribution path. It remains a prerelease and does **not** by itself complete the `production-ready/local` claim.

## What changed

- macOS standalone builds require no Apple Developer ID certificate, App Store Connect key, notarization credential, or signing secret;
- the final `Shadowseed.app` is ad-hoc signed and must pass strict `codesign --verify --deep --strict`;
- the distributable ZIP contains `Shadowseed.app`, `Open Shadowseed.command`, and `README_FIRST_START.txt`;
- CI extracts the exact ZIP again, verifies the extracted app seal and first-launch files, and runs the frozen product self-test from the round-tripped app;
- the standalone manifest records the actual platform boundary: ad-hoc signed, not notarized, not Gatekeeper-assessed, first-launch helper present;
- Release Workbench rejects a macOS artifact that claims stronger Apple platform verification than was actually performed.

## Supported macOS first-launch path

A browser download may attach `com.apple.quarantine`. Because 0.7.2 is intentionally not Apple-notarized, a direct first double-click may be blocked.

The supported first-launch path is:

1. download and extract the verified macOS ZIP;
2. keep `Shadowseed.app` and `Open Shadowseed.command` together;
3. open `Open Shadowseed.command` once;
4. if Finder blocks that helper too, Control-click it, choose **Open**, and confirm;
5. after the helper opens Shadowseed, later launches can use `Shadowseed.app` directly.

The helper removes `com.apple.quarantine` recursively only from the adjacent `Shadowseed.app` bundle and then opens that app. It does not use `sudo`, disable Gatekeeper globally, or change system-wide security settings.

This is deliberately different from the 0.7.1 acceptance experiment, which required a normal browser-download launch without quarantine removal. Version 0.7.2 changes the declared distribution contract instead of claiming Apple notarization that the project does not use.

## Release integrity

The credential-free macOS path does not weaken the repository release controls. Publication still requires:

- the exact protected-`main` source SHA;
- frozen standalone self-tests;
- final-bundle and archive-round-trip verification;
- `SHA256SUMS`;
- CycloneDX SBOM;
- `PROVENANCE.json`;
- repository license verification;
- GitHub/Sigstore artifact attestations;
- post-download verification;
- the normal production-local acceptance and unchanged-candidate soak gates.

## Authority model

No Gate, lifecycle, evidence, contradiction, recurrence, point-of-use, engine, or Workbench authority semantics change in 0.7.2.

```text
runtime_mode = live
Gate policy = evidence_backed
trace > 0 means the seed is present
weight = 0 means the seed does not steer
```

## Claim boundary

Version 0.7.2 does not claim Apple Developer ID signing, Apple notarization, automatic Gatekeeper acceptance, Windows Authenticode signing, general answer-quality benefit, semantic truth, hosted/multi-user readiness, or a completed `production-ready/local` status before the repository assurance and soak gates finish.
