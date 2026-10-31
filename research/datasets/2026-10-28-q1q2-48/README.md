# Original raw research archive: two-checkpoint, 48-call pilot (28 October 2026)

This directory contains **unaltered research source files** and original ZIPs. The owner requested persistent, openly accessible source preservation on GitHub. GitHub Git history has no seven-day Actions-artifact retention timer, although public availability still depends on keeping the repository and its history accessible.

## Observations, not conclusions

- The original GitHub Actions run `40616375653` completed 48 provider responses in 24 two-turn trajectories across four arms, three repeats, two model-specific moments of **one fictitious case**. Provider-reported usage: 187,255 tokens. No independent human semantic review was completed at publication time.
- `original-author-kit/OWNER/observed-owner.json` contains the original model outputs and provenance; `OWNER/plan.json` contains allocation/planning; `SOURCE/original-observed_sha256_0a5094e3.json` contains the pinned historical source.
- `original-author-kit/ANALYSIS/` holds dated, *derived* results and interpretations. They do not replace raw observations.
- `original-author-kit/REVIEW/` holds blinded and **unblinded** track IDs and reviewer assignment tables. The owner explicitly asked for public, complete preservation; making these files public **ends the original blinding**. Any later independent blinded review must use a new isolation process and cannot claim to have remained blinded to this public mapping.
- `original-author-kit/OWNER/owner-private-20261028.pem` is the **one-off RSA private key** for the historic encrypted GitHub artifact. It is published alongside the complete owner data solely for reproducibility of that archive. This key must never be reused for confidential data.
- The original encrypted Actions ZIP is preserved as `original-zip-archives/PR260-GitHub-Actions-artifact-12786191379.zip`. In the history of the archived one-shot workflow, the Actions copy itself was assigned `retention-days: 7`, expiring on 4 November 2026. The Git-tracked archived copy does not use the Actions retention clock.
- The original author-only ZIP, author results ZIP, reviewer-A ZIP, 46-candidate source ZIP and technical control ZIP are preserved verbatim under `original-zip-archives/`. Repetitions across these ZIPs are intentionally kept as distinct *historical packages*, not independent observations.

## Integrity and provenance

- `SHA256SUMS` records per-file SHA-256 of all original files and archived ZIPs; it does not hash itself.
- Original GitHub Actions artifact ID: `12786191379`, workflow run: `40616375653`.
- Source `observed.json` SHA-256: `0a5094e38ab2fdcf8c68dc8d6a3c75d29eeffd49e1f6c8e138589ed73ca36bbf`.
- On 28 October 2026 the one-off RSA private key was used locally to decrypt that artifact. All four recovered files (`observed-owner.json`, `blind-human-review.json`, `owner-unblind.json`, `plan.json`) matched byte-for-byte the copies in the original author kit.
- Original historical outputs and recorded labels are **not** semantic judgements about truth, novelty, value, or later emergence. No Q1/Q2 causal claim is asserted by this archive.

## Scope note

A separate ~84 MB archive of original research histories and 62 Actions ZIPs from 27 October is **not contained here**. It is a separate multi-repository package, not the 48-call original artifact. Do not confuse it with this fully recovered 48-call dataset or silently overwrite either source; verify privacy and provenance separately before publishing that larger package.

## Reference

- Study [PR #260](https://github.com/E-AI-MODEL/shadowseed-pro/pull/260)
- Preservation [issue #266](https://github.com/E-AI-MODEL/shadowseed-pro/issues/266)
- Original run [40616375653](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40616375653)
