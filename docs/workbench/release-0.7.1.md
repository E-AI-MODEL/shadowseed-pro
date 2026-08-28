# Shadowseed Workbench 0.7.1 Research Preview

Shadowseed Workbench 0.7.1 is a production-local assurance candidate that repairs the macOS standalone distribution defect discovered while validating 0.7.0 on a real browser-downloaded Mac. It remains a prerelease and does **not** itself complete the `production-ready/local` claim.

## What changed

- The final macOS application bundle is re-sealed only after every required bundle mutation, including installation of `SHADOWSEED_LICENSE.txt`.
- The build fails unless `codesign --verify --deep --strict` accepts the final application bundle.
- The release ZIP is created only after the final seal is valid.
- CI re-extracts the exact distributable ZIP, verifies the extracted app seal again, and runs the packaged frozen self-test from that round-tripped application.
- The standalone manifest records the macOS signature mode and archive round-trip evidence so release verification is tied to the bytes that are actually distributed.

## macOS acceptance boundary

The 0.7.0 ZIP checksum matched the published release exactly, but the extracted application failed strict code-signature verification because resources had been added after the PyInstaller application seal. Version 0.7.1 closes that packaging and CI gap.

This release does **not** claim native Apple Developer ID signing or notarization unless the published release evidence explicitly demonstrates those controls. The default CI path can use an ad-hoc application signature. Therefore the real acceptance test remains a normal Internet-download path on a supported Mac: download the published ZIP, verify its checksum, extract it normally, and open Shadowseed without removing quarantine attributes or bypassing Gatekeeper.

## Production-local status

The live product authority model is unchanged:

```text
runtime_mode = live
Gate policy = evidence_backed
trace > 0 means the seed is present
weight = 0 means the seed does not steer
```

No Gate, contradiction, evidence-provenance, or point-of-use authority semantics are weakened by this packaging repair.

`production-ready/local` remains gated on the repository production acceptance contract. After this exact candidate is published, the required next evidence is:

1. exact-SHA release/provenance/checksum assurance on the protected `main` candidate;
2. a successful normal browser-download/open cycle on supported macOS without a Gatekeeper bypass;
3. a normal local Workbench use cycle and `shadowseed doctor` evidence as required by the Phase 5 runbook;
4. no unresolved P0/P1 findings through the unchanged-candidate soak period;
5. final main/tag/SHA re-verification before the production-local claim.

Because 0.7.1 is a new source SHA and release candidate, the previous 0.7.0 soak does not carry forward.

## Distribution and rights

The release workflow continues to verify exact-source standalone manifests, dependency lock provenance, SBOM, `SHA256SUMS`, the repository license, and GitHub/Sigstore artifact attestations before publication. Model weights remain separate from standalone artifacts.

Software distributed with the repository `LICENSE` is source-available under PolyForm Noncommercial License 1.0.0. Commercial use requires separate permission. Third-party dependencies and model artifacts retain their own applicable terms.
