# Shadow Seed Learning: small exploratory pilot, 28 October 2026

This is the **private author kit** for the exploratory two-moment pilot. It is not a peer-reviewed claim of Q1 or Q2.

- `two_point_pilot.py`: a fully offline-tested local version of the source-pinned 48-call runner; the canonical GitHub branch uses `research/scripts/q1q2_two_point_48.py`.
- `test_two_point_pilot.py`: mocked, network-free source and arm tests.
- `decrypt_owner_artifact.sh`: decrypts a GitHub Actions artifact.
- `owner-encryption-public-20261028.pem`: the public key, safe to share.
- `owner-private-20261028.pem`: **private key, never put in GitHub or give to reviewers.**
- `plan.json`: a local dry-run showing both moments, source hash and all arms.

The two research moments both come from case DM26-C02. A weightless candidate in a *research inquiry prompt* is not the same as authorisation by Shadowseed's production Gate. Two-turn variation does not prove that the model could never have generated the relation otherwise. Run human-blind semantic review before treating any candidate as useful/novel.

The original raw Actions `observed.json` is SHA-pinned; model outputs and owner mappings are encrypted in the GitHub artifact with a fresh AES key wrapped under RSA-OAEP. To recover data, run `decrypt_owner_artifact.sh artifact.zip owner-private-20261028.pem ./owner-output`.
