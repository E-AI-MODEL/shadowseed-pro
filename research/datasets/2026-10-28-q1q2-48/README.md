# Original research records: 48-call Q1/Q2 pilot (28 October 2026)

This folder contains readable, original, **unaltered** source files from the 48-completed-answer, 24-two-turn-track pilot. The study contains two checkpoints within a single fictional case and does not imply two independent cases, proof of novelty, or completed independent human reviews.

## Where to start

- [Original model answers, 24 two-turn tracks](original-author-kit/OWNER/observed-owner.json) (48 model responses with provider receipts).
- [Exact original source observations](original-author-kit/SOURCE/original-observed_sha256_0a5094e3.json) (prior raw detector and host records, pinned SHA-256).
- [Experimental plan and arm order](original-author-kit/OWNER/plan.json).
- [Original blinded reviewer packet](original-author-kit/OWNER/blind-human-review.json) and [individual reviewer packets](original-author-kit/REVIEW/).
- [Analysis scripts](original-author-kit/CODE/), [mechanical outputs](original-author-kit/ANALYSIS/), and [read-only HTML explorer](original-author-kit/RAW_EXPLORER_AUTHOR_ONLY.html).

These are *original file bytes* from the owner research archive. One original helper runner, `CODE/runner_local_two_point_pilot.py`, is kept with the complete owner ZIP rather than mirrored in this public folder. The executed source runner is separately available on PR #260. Inferences and researcher interpretations should be placed in separate dated files, not written back into these source records. The historical terms `accepted`, `rejected`, `not_atomic` and `surfaced` belong to the original pipeline; they are not evaluations of the underlying text.

## Provenance and checksums

- GitHub Actions completed run: https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40616375653 .
- Original owner artifact ID: `12786191379`; historic filename `q1q2-48-encrypted-owner-40616375653`.
- Original encrypted artifact SHA-256: `587c582f40af5e7cab9639bef3938b4b57650f0c878af8bf1e1a1b8749cd1d2b`. The unchanged encrypted ZIP is separately backed up, but is **not** a Git-tracked file in this directory.
- Full unchanged original author ZIP SHA-256: `aecf3bc94987b685e6348437af5a815c39a7f6bd3417d686f44c7c5234592475`. Its unaltered, complete source remains backed up outside this public repository.
- Source `observed.json` SHA-256: `0a5094e38ab2fdcf8c68dc8d6a3c75d29eeffd49e1f6c8e138589ed73ca36bbf`.
- The [SHA256SUMS](SHA256SUMS) file lists all source files actually included in this directory (excluding this README and the checksum file itself).
- Git commits preserve content history. The 7-day retention on the original GitHub Actions artifact does not govern these Git-tracked readable research files.

## Scope and access

The original author ZIP also includes the one-off RSA private key, an owner-to-arm unblinding map, and a reviewer identity map. Those **three files** are preserved intact with the owner archive but not part of this public collection. The incomplete blinded review must not be silently relabeled as independently assessed. This publication does **not** publish model API credentials, the RSA private key, or the unblinding identity.

No model calls have been rerun to reconstruct missing content. This is a faithful byte-level preservation of 22 source files and two new documentation files, not a generated substitute for the originals.

See [PR #260](https://github.com/E-AI-MODEL/shadowseed-pro/pull/260) and [archive issue #266](https://github.com/E-AI-MODEL/shadowseed-pro/issues/266).
